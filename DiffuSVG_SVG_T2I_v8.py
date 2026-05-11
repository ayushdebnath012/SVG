# -*- coding: utf-8 -*-
"""
DiffuSVG_SVG_T2I_v8.py
=======================
Adapts SVG-T2I (arXiv:2512.11749v1, Shi et al. 2025) to the OmniSVG model
(Qwen2.5-VL backbone) for high-quality text-to-SVG generation.

Key adaptations from the paper, mapped to SVG generation:

  Paper concept                   →  SVG adaptation here
  ─────────────────────────────── ─────────────────────────────────────────────
  VFM Autoencoder-P (Table 7)    →  VFMAutoencoder: frozen DINOv2 encoder +
                                     lightweight CNN decoder; encodes rendered
                                     SVGs into VFM feature space for quality
                                     assessment.

  Multi-res VFM analysis (Fig 4)  →  MultiResolutionVFMGate: tests rendered SVGs
                                     at 224 / 448 / 896 px (3 scales vs v7's 2);
                                     cross-scale cosine similarity identifies
                                     degenerate / semantically unstable SVGs.

  Flow matching objective (Eq 1-2)→  FlowMatchingScorer: uses the linear
                                     interpolation trajectory between a reference
                                     feature distribution and Gaussian noise to
                                     score how "on-manifold" a generated SVG is.

  4-stage progressive training    →  SVGProgressiveCurriculum: stages by SVG
  (Table 4)                          complexity (char count + VFM quality):
                                     simple (224px) → medium (448px) →
                                     complex (896px) → aesthetic HQ (896px).

  Dual scoring (Tables 5-6)      →  VFM consistency × CLIP score product;
                                     GenEval-category evaluation (single_obj,
                                     two_obj, counting, colors, position).

  N-best reranking               →  VFMGuidedOmniSVG: generates N candidates
                                     from OmniSVG, reranks by VFM×CLIP, returns
                                     best.

Architecture: OmniSVG SketchDecoder (Qwen2.5-VL-3B, 4-bit NF4, Kaggle T4)

Usage:
  # Kaggle / Colab
  python DiffuSVG_SVG_T2I_v8.py          # full pipeline
  python DiffuSVG_SVG_T2I_v8.py --stage 1  # single stage only
"""

import subprocess, sys, os, gc, json, logging, re, random, shutil, io, math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_NO_TORCHVISION"] = "1"
os.environ["USE_TORCHVISION"] = "0"
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_FLAX"] = "0"
os.environ["USE_JAX"] = "0"
os.environ["TRANSFORMERS_NO_FLAX"] = "1"
os.environ["TRANSFORMERS_NO_JAX"] = "1"
os.environ["USE_TORCHAO"] = "0"
os.environ["TRANSFORMERS_NO_TORCHAO"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"


# ─── Dependency bootstrap ──────────────────────────────────────────────────────
def _ensure_deps():
    # ── Numpy 2.2.x / old-scipy compat monkeypatch ───────────────────────────
    # Root cause: old scipy (<1.14) bundles array_api_compat which does
    # `from numpy import *`, triggering numpy.core → numpy.strings, which
    # imports several private string helpers from `numpy._core.umath`.
    # In some Kaggle images those helpers are missing from the Python shim.
    #
    # pip install of a new scipy goes into user site-packages but Kaggle's
    # system scipy at /usr/local/lib/python3.12/dist-packages/ takes priority,
    # so the updated files on disk are never reached by the running kernel.
    #
    # Definitive fix: stub the private helpers directly into the already-loaded
    # umath module. `numpy._core.strings` only needs the names to exist at import
    # time; they are never actually called in our pipeline or by sklearn/
    # transformers.
    import numpy as _np
    import numpy._core.umath as _ncu

    # Old scipy.array_api_compat does `from numpy import *`; with NumPy 2.2 on
    # some Kaggle images that star import pulls in `numpy.char` / `numpy.strings`,
    # whose module init is incompatible with the bundled NumPy ufunc objects. We
    # do not use those namespaces, so keep them out of star-import expansion.
    if hasattr(_np, "__all__"):
        _np.__all__ = [
            name for name in _np.__all__
            if name not in {"char", "strings"}
        ]

    _numpy_string_private_helpers = (
        "_lstrip_whitespace", "_lstrip_chars",
        "_rstrip_whitespace", "_rstrip_chars",
        "_strip_whitespace",  "_strip_chars",
        "_replace", "_expandtabs_length", "_expandtabs",
        "_center", "_ljust", "_rjust", "_zfill",
        "_partition", "_partition_index",
        "_rpartition", "_rpartition_index",
    )
    for _name in _numpy_string_private_helpers:
        if not hasattr(_ncu, _name):
            setattr(_ncu, _name, None)  # import-only stub

    # Also install scipy>=1.14 so future kernel sessions get the proper fix
    # (scipy 1.14 ships an updated array_api_compat that is numpy-2.2-safe).
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                           "scipy>=1.14"])

    pkgs = [
        "bitsandbytes>=0.46.1", "peft>=0.13.0", "accelerate>=0.26.0",
        "cairosvg", "open_clip_torch", "transformers>=4.45.0", "einops",
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + pkgs)

    # Clear any partially imported optional stacks left by a previous failed
    # notebook run before Transformers checks availability again.
    for _prefix in (
        "torchvision", "timm", "tensorflow", "tensorflow_probability",
        "tensorflow_text", "keras", "torchao",
    ):
        for _mod_name in [m for m in list(sys.modules) if m == _prefix or m.startswith(_prefix + ".")]:
            sys.modules.pop(_mod_name, None)

    # Transformers only uses sklearn/torchvision/timm/TF/Flax/torchao for optional helpers here.
    # Marking them unavailable prevents fragile Kaggle imports:
    #   sklearn -> scipy -> numpy.strings
    #   torchvision -> custom C++ ops such as torchvision::nms
    #   timm -> torchvision feature extraction wrappers
    #   tensorflow -> scipy -> numpy.char -> numpy.strings
    #   torchao -> mismatched Torch private APIs such as torch._dynamo.warn_once
    try:
        import importlib
        import importlib.metadata as _metadata
        import transformers.utils.import_utils as _tf_import_utils
        import transformers.utils as _tf_utils

        def _pkg_version(pkg: str, default: str = "unavailable") -> str:
            try:
                return _metadata.version(pkg)
            except Exception:
                return default

        # Mixed Kaggle Transformers installs can have newer integration files
        # importing private version globals from an older import_utils module.
        _private_versions = {
            "_torch_version": _pkg_version("torch", "0.0.0"),
            "_torchvision_version": "unavailable",
            "_timm_version": "unavailable",
            "_torchao_version": "unavailable",
            "_tf_version": "unavailable",
            "_flax_version": "unavailable",
            "_jax_version": "unavailable",
        }
        for _name, _version in _private_versions.items():
            if not hasattr(_tf_import_utils, _name):
                setattr(_tf_import_utils, _name, _version)

        def _torch_version_cmp(library_version: str, op, accept_dev: bool = False) -> bool:
            try:
                from packaging import version as _version
                current = _version.parse(str(_tf_import_utils._torch_version).split("+")[0])
                target = _version.parse(str(library_version).split("+")[0])
                return op(current, target)
            except Exception:
                return False

        if not hasattr(_tf_import_utils, "is_torch_less_or_equal"):
            _tf_import_utils.is_torch_less_or_equal = (
                lambda library_version, accept_dev=False:
                    _torch_version_cmp(library_version, lambda a, b: a <= b, accept_dev)
            )
        if not hasattr(_tf_import_utils, "is_torch_greater_or_equal"):
            _tf_import_utils.is_torch_greater_or_equal = (
                lambda library_version, accept_dev=False:
                    _torch_version_cmp(library_version, lambda a, b: a >= b, accept_dev)
            )
        if not hasattr(_tf_import_utils, "is_torchdynamo_compiling"):
            _tf_import_utils.is_torchdynamo_compiling = lambda: False
        if not hasattr(_tf_import_utils, "get_torch_version"):
            _tf_import_utils.get_torch_version = (
                lambda: str(_tf_import_utils._torch_version)
            )
        if not hasattr(_tf_utils, "is_torchdynamo_compiling"):
            _tf_utils.is_torchdynamo_compiling = (
                _tf_import_utils.is_torchdynamo_compiling
            )

        def _false_available(*args, **kwargs):
            return False

        def _true_available(*args, **kwargs):
            return True

        _import_utils_helper_defaults = {
            # Core framework availability
            "is_torch_available": _true_available,
            "is_vision_available": _true_available,
            "requires_backends": lambda obj, backends: None,
            # Always-false optional backends
            "is_av_available": _false_available,
            "is_flash_attn_available": _false_available,
            "is_flax_available": _false_available,
            "is_jax_available": _false_available,
            "is_scipy_available": _false_available,
            "is_sklearn_available": _false_available,
            "is_tf_available": _false_available,
            "is_timm_available": _false_available,
            "is_torch_flex_attn_available": _false_available,
            "is_torchao_available": _false_available,
            "is_torchvision_available": _false_available,
            # Quantizer availability helpers — mixed Transformers install has
            # quantization_config.py from a newer version that imports these from
            # transformers.utils, but the old system import_utils.py doesn't define them.
            "is_auto_awq_available": _false_available,
            "is_auto_gptq_available": _false_available,
            "is_auto_eetq_available": _false_available,
            "is_auto_hqq_available": _false_available,
            "is_aqlm_available": _false_available,
            "is_compressed_tensors_available": _false_available,
            "is_eetq_available": _false_available,
            "is_fbgemm_gpu_available": _false_available,
            "is_gptq_available": _false_available,
            "is_hqq_available": _false_available,
            "is_marlin_available": _false_available,
            "is_optimum_quanto_available": _false_available,
            "is_quanto_available": _false_available,
            "is_quip_available": _false_available,
            "is_vptq_available": _false_available,
            "is_fp8_available": _false_available,
            "is_gguf_available": _false_available,
        }
        for _name, _fn in _import_utils_helper_defaults.items():
            if not hasattr(_tf_import_utils, _name):
                setattr(_tf_import_utils, _name, _fn)
            # Also force-set on utils directly so quantization_config.py can import them
            if not hasattr(_tf_utils, _name):
                setattr(_tf_utils, _name, _fn)

        # Some Kaggle images can end up with a mixed Transformers install where
        # transformers.models.auto expects availability helpers to be exported
        # from transformers.utils, but __init__.py does not expose all of them.
        # Copy the canonical helpers back from import_utils before any model
        # class import triggers the lazy auto-module machinery.
        _availability_helpers = (
            "is_accelerate_available", "is_bitsandbytes_available",
            "is_av_available", "is_datasets_available",
            "is_flash_attn_available",
            "is_flax_available", "is_jax_available", "is_peft_available",
            "is_safetensors_available", "is_scipy_available",
            "is_sentencepiece_available",
            "is_sklearn_available", "is_tf_available", "is_timm_available",
            "is_tokenizers_available", "is_torch_available",
            "is_torch_cuda_available", "is_torch_flex_attn_available",
            "is_torchao_available",
            "is_torchvision_available", "is_vision_available",
        )
        for _name in _availability_helpers:
            if hasattr(_tf_import_utils, _name):
                setattr(_tf_utils, _name, getattr(_tf_import_utils, _name))
        for _name in dir(_tf_import_utils):
            if not _name.startswith("_") and not hasattr(_tf_utils, _name):
                setattr(_tf_utils, _name, getattr(_tf_import_utils, _name))

        # The same mixed-install state can leave transformers.utils missing
        # regular helpers that newer modules import from it. Re-export any
        # public helper already present in the real utility submodules.
        for _submodule in ("doc", "generic", "hub"):
            try:
                _mod = importlib.import_module(f"transformers.utils.{_submodule}")
                for _name in dir(_mod):
                    if not _name.startswith("_") and not hasattr(_tf_utils, _name):
                        setattr(_tf_utils, _name, getattr(_mod, _name))
            except Exception:
                pass

        def _is_torch_tensor(x):
            _torch = sys.modules.get("torch")
            return bool(_torch is not None and getattr(_torch, "is_tensor", lambda _: False)(x))

        def _is_numpy_array(x):
            return isinstance(x, _np.ndarray)

        def _to_numpy(x):
            if _is_numpy_array(x):
                return x
            if _is_torch_tensor(x):
                return x.detach().cpu().numpy()
            if hasattr(x, "numpy"):
                return x.numpy()
            return _np.asarray(x)

        for _name, _fn in {
            "is_jax_tensor": _false_available,
            "is_tf_tensor": _false_available,
            "is_torch_tensor": _is_torch_tensor,
            "is_numpy_array": _is_numpy_array,
            "to_numpy": _to_numpy,
            "is_av_available": _false_available,
        }.items():
            if not hasattr(_tf_utils, _name):
                setattr(_tf_utils, _name, _fn)

        if not hasattr(_tf_utils, "ExplicitEnum"):
            from enum import Enum

            class _ExplicitEnum(str, Enum):
                @classmethod
                def _missing_(cls, value):
                    raise ValueError(
                        f"{value!r} is not a valid {cls.__name__}; "
                        f"choose one of {[x.value for x in cls]}"
                    )

            _tf_utils.ExplicitEnum = _ExplicitEnum
        if not hasattr(_tf_utils, "TensorType"):
            _ExplicitEnumBase = getattr(_tf_utils, "ExplicitEnum", str)

            class _TensorType(_ExplicitEnumBase):
                PYTORCH = "pt"
                TENSORFLOW = "tf"
                NUMPY = "np"
                JAX = "jax"
                MLX = "mlx"

            _tf_utils.TensorType = _TensorType
        if not hasattr(_tf_utils, "requires_backends"):
            _tf_utils.requires_backends = lambda obj, backends: None
        if not hasattr(_tf_utils, "logging"):
            try:
                _tf_utils.logging = importlib.import_module("transformers.utils.logging")
            except Exception:
                pass

        def _download_url(url, proxies=None):
            """Small fallback for Transformers mixed installs missing this export."""
            import tempfile
            from urllib.parse import urlparse

            import requests

            name = os.path.basename(urlparse(url).path) or "downloaded_file"
            dst = os.path.join(tempfile.mkdtemp(), name)
            response = requests.get(url, proxies=proxies, timeout=60)
            response.raise_for_status()
            with open(dst, "wb") as f:
                f.write(response.content)
            return dst

        def _add_model_info_to_auto_map(auto_map, repo_id):
            """Compatibility copy for newer Transformers save helpers."""
            if auto_map is None or repo_id in (None, ""):
                return auto_map

            def _with_repo(value):
                if isinstance(value, str) and "--" not in value:
                    return f"{repo_id}--{value}"
                return value

            if isinstance(auto_map, dict):
                return {k: _add_model_info_to_auto_map(v, repo_id)
                        for k, v in auto_map.items()}
            if isinstance(auto_map, tuple):
                return tuple(_with_repo(v) for v in auto_map)
            if isinstance(auto_map, list):
                return [_with_repo(v) for v in auto_map]
            return _with_repo(auto_map)

        def _add_model_info_to_custom_pipelines(custom_pipelines, repo_id):
            """Compatibility copy for newer Transformers save helpers."""
            if custom_pipelines is None or repo_id in (None, ""):
                return custom_pipelines
            if not isinstance(custom_pipelines, dict):
                return custom_pipelines
            out = {}
            for task, value in custom_pipelines.items():
                if isinstance(value, dict):
                    value = dict(value)
                    impl = value.get("impl")
                    if isinstance(impl, str) and "--" not in impl:
                        value["impl"] = f"{repo_id}--{impl}"
                out[task] = value
            return out

        if not hasattr(_tf_utils, "add_model_info_to_auto_map"):
            _tf_utils.add_model_info_to_auto_map = _add_model_info_to_auto_map
        if not hasattr(_tf_utils, "add_model_info_to_custom_pipelines"):
            _tf_utils.add_model_info_to_custom_pipelines = (
                _add_model_info_to_custom_pipelines
            )
        if not hasattr(_tf_utils, "download_url"):
            _tf_utils.download_url = _download_url

        # ── transformers.file_utils stub ──────────────────────────────────
        # Newer quantizers/auto.py imports quantizer_quark.py which does
        #   from ..file_utils import is_torch_available
        # The real file_utils.py re-exports ~50 names from transformers.utils
        # via `from .utils import (CLOUDFRONT_DISTRIB_PREFIX, ...,
        # FLAX_WEIGHTS_NAME, ...)`. The old system utils/__init__.py is missing
        # newer constants so the whole file_utils import crashes. Pre-install a
        # populated stub so none of the quantizer files ever execute the real
        # file_utils.py.
        import types as _types_mod
        _tf_file_utils = sys.modules.get("transformers.file_utils")
        if _tf_file_utils is None:
            _tf_file_utils = _types_mod.ModuleType("transformers.file_utils")
            sys.modules["transformers.file_utils"] = _tf_file_utils

        # Missing string constants (Flax/TF names were removed from newer
        # utils/__init__.py but old file_utils.py still re-exports them)
        _file_utils_constants = {
            "FLAX_WEIGHTS_NAME": "flax_model.msgpack",
            "FLAX_WEIGHTS_INDEX_NAME": "flax_model.msgpack.index.json",
            "TF2_WEIGHTS_NAME": "tf_model.h5",
            "TF2_WEIGHTS_INDEX_NAME": "tf_model.h5.index.json",
            "TF_WEIGHTS_NAME": "pytorch_model.bin",
            "WEIGHTS_NAME": "pytorch_model.bin",
            "WEIGHTS_INDEX_NAME": "pytorch_model.bin.index.json",
            "SAFE_WEIGHTS_NAME": "model.safetensors",
            "SAFE_WEIGHTS_INDEX_NAME": "model.safetensors.index.json",
            "CONFIG_NAME": "config.json",
            "FEATURE_EXTRACTOR_NAME": "preprocessor_config.json",
            "IMAGE_PROCESSOR_NAME": "preprocessor_config.json",
            "TOKENIZER_CONFIG_FILE": "tokenizer_config.json",
            "MODEL_CARD_NAME": "modelcard.json",
            "FULL_CONFIGURATION_FILE": "config.json",
            "CLOUDFRONT_DISTRIB_PREFIX": "https://cdn.huggingface.co",
            "PYTORCH_PRETRAINED_BERT_WEIGHTS_URL": "https://cdn.huggingface.co",
            "PYTORCH_TRANSFORMERS_CACHE": os.environ.get(
                "PYTORCH_TRANSFORMERS_CACHE",
                os.environ.get("TRANSFORMERS_CACHE", ""),
            ),
            "TRANSFORMERS_CACHE": os.environ.get("TRANSFORMERS_CACHE", ""),
            "TRANSFORMERS_DYNAMIC_MODULE_NAME": "transformers_modules",
            "SENTENCEPIECE_UNDERLINE": "▁",
            "DUMMY_INPUTS": [[7, 6, 0, 0, 1], [1, 2, 3, 0, 0], [0, 0, 0, 4, 5]],
            "DUMMY_MASK": [[1, 1, 1, 1, 1], [1, 1, 1, 0, 0], [0, 0, 0, 1, 1]],
            "ENV_VARS_TRUE_VALUES": {"1", "ON", "YES", "TRUE"},
            "ENV_VARS_TRUE_AND_AUTO_VALUES": {"1", "ON", "YES", "TRUE", "AUTO"},
        }
        for _name, _val in _file_utils_constants.items():
            if not hasattr(_tf_utils, _name):
                setattr(_tf_utils, _name, _val)
            if not hasattr(_tf_file_utils, _name):
                setattr(_tf_file_utils, _name, _val)

        # Copy all public helpers from import_utils and utils into the stub
        for _src_mod in (_tf_import_utils, _tf_utils):
            for _name in dir(_src_mod):
                if not _name.startswith("__") and not hasattr(_tf_file_utils, _name):
                    try:
                        setattr(_tf_file_utils, _name, getattr(_src_mod, _name))
                    except Exception:
                        pass

        for _mod_name in (
            "transformers.feature_extraction_utils",
            "transformers.image_processing_base",
            "transformers.image_processing_utils",
            "transformers.image_processing_utils_fast",
            "transformers.modeling_utils",
            "transformers.models.auto.image_processing_auto",
            "transformers.models.dinov2.modeling_dinov2",
        ):
            sys.modules.pop(_mod_name, None)

        for _name in ("is_flax_available", "is_jax_available",
                      "is_tf_available", "is_torchvision_available",
                      "is_timm_available", "is_sklearn_available",
                      "is_torchao_available", "is_torch_flex_attn_available",
                      "is_flash_attn_available", "is_av_available",
                      "is_scipy_available"):
            setattr(_tf_utils, _name, _false_available)
        if not hasattr(_tf_utils, "is_torch_available"):
            setattr(_tf_utils, "is_torch_available", _true_available)

        _tf_import_utils._sklearn_available = False
        _tf_import_utils._torchvision_available = False
        _tf_import_utils._torchvision_version = "unavailable"
        _tf_import_utils._timm_available = False
        _tf_import_utils._torchao_available = False
        _tf_import_utils._torchao_version = "unavailable"
        _tf_utils._torchao_available = False
        _tf_utils._torchao_version = "unavailable"
        _tf_import_utils._tf_available = False
        _tf_import_utils._flax_available = False
        _tf_import_utils._jax_available = False
        _tf_import_utils._tensorflow_text_available = False
        _tf_import_utils._tensorflow_probability_available = False
    except Exception:
        pass

_ensure_deps()

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from PIL import Image


def _patch_torch_compiler_for_kaggle():
    """
    Some Kaggle images have a mismatched torch / torch._dynamo stack. Recent
    Transformers imports `torch.compiler.disable` while defining optional
    attention helpers; the real decorator imports Dynamo and can crash before
    any model loads. We do not use torch.compile here, so make the decorator
    an identity function.
    """
    def _identity_disable(fn=None, recursive=True, reason=None):
        if fn is None:
            return lambda f: f
        return fn

    try:
        import types
        if not hasattr(torch, "compiler"):
            torch.compiler = types.SimpleNamespace()
        torch.compiler.disable = _identity_disable
        if not hasattr(torch.compiler, "is_compiling"):
            torch.compiler.is_compiling = lambda: False
    except Exception:
        pass


_patch_torch_compiler_for_kaggle()


def _patch_transformers_fsdp_for_kaggle():
    """
    Transformers generation probes FSDP status on every generate() call. That
    probe imports torch.distributed.fsdp, which pulls in torch._dynamo on some
    Kaggle images and crashes due to mismatched private GuardSource symbols.
    This pipeline never uses FSDP, so make every reachable copy of the probe a
    cheap False.  Transformers imports this helper into generation.utils, and
    torch.no_grad wraps generate(), so patch both module globals and any stale
    function object already captured by the decorator/import machinery.
    """
    def _not_fsdp_managed(*args, **kwargs):
        return False

    def _install_fsdp_stub():
        try:
            import types
            import torch.distributed as _dist

            for _name in [m for m in list(sys.modules)
                          if m == "torch.distributed.fsdp"
                          or m.startswith("torch.distributed.fsdp.")]:
                sys.modules.pop(_name, None)

            _fsdp_mod = types.ModuleType("torch.distributed.fsdp")
            _fsdp_mod.__path__ = []

            class _UnavailableFSDP:
                pass

            _fsdp_mod.FullyShardedDataParallel = _UnavailableFSDP
            _fsdp_mod.FlatParameter = _UnavailableFSDP
            _fsdp_fully_mod = types.ModuleType(
                "torch.distributed.fsdp.fully_sharded_data_parallel"
            )
            _fsdp_fully_mod.FullyShardedDataParallel = _UnavailableFSDP
            _fsdp_flat_mod = types.ModuleType(
                "torch.distributed.fsdp.flat_param"
            )
            _fsdp_flat_mod.FlatParameter = _UnavailableFSDP
            sys.modules["torch.distributed.fsdp"] = _fsdp_mod
            sys.modules[
                "torch.distributed.fsdp.fully_sharded_data_parallel"
            ] = _fsdp_fully_mod
            sys.modules["torch.distributed.fsdp.flat_param"] = _fsdp_flat_mod
            _fsdp_mod.fully_sharded_data_parallel = _fsdp_fully_mod
            _fsdp_mod.flat_param = _fsdp_flat_mod
            setattr(_dist, "fsdp", _fsdp_mod)
        except Exception:
            pass

    def _mutate_function_in_place(fn):
        if not callable(fn):
            return
        try:
            fn.__code__ = _not_fsdp_managed.__code__
            fn.__defaults__ = _not_fsdp_managed.__defaults__
            fn.__kwdefaults__ = _not_fsdp_managed.__kwdefaults__
        except Exception:
            pass

    _install_fsdp_stub()

    for _mod_name in (
        "transformers.integrations.fsdp",
        "transformers.generation.utils",
    ):
        try:
            if _mod_name in sys.modules:
                _mod = sys.modules[_mod_name]
                _mutate_function_in_place(
                    getattr(_mod, "is_fsdp_managed_module", None)
                )
                setattr(_mod, "is_fsdp_managed_module", _not_fsdp_managed)
        except Exception:
            pass

    try:
        import transformers.integrations.fsdp as _tf_fsdp
        _mutate_function_in_place(
            getattr(_tf_fsdp, "is_fsdp_managed_module", None)
        )
        _tf_fsdp.is_fsdp_managed_module = _not_fsdp_managed
    except Exception:
        pass

    try:
        import transformers.generation.utils as _gen_utils
        _mutate_function_in_place(
            getattr(_gen_utils, "is_fsdp_managed_module", None)
        )
        _gen_utils.is_fsdp_managed_module = _not_fsdp_managed

        _gen_mixin = getattr(_gen_utils, "GenerationMixin", None)
        _generate = getattr(_gen_mixin, "generate", None)
        for _fn in (_generate, getattr(_generate, "__wrapped__", None)):
            if hasattr(_fn, "__globals__"):
                _fn.__globals__["is_fsdp_managed_module"] = _not_fsdp_managed
    except Exception:
        pass


_patch_transformers_fsdp_for_kaggle()


def _install_qwen_torchvision_stub():
    """
    qwen_vl_utils imports torchvision at module import time even for text-only
    SVG generation. Kaggle's torchvision binary is mismatched with torch, so
    provide the tiny surface qwen_vl_utils expects and fail clearly for video.
    """
    import types

    for _mod_name in [m for m in list(sys.modules)
                      if m == "torchvision" or m.startswith("torchvision.")]:
        sys.modules.pop(_mod_name, None)

    tv = types.ModuleType("torchvision")
    tv.__version__ = "0.19.0"

    io_mod = types.ModuleType("torchvision.io")

    def _read_video_unavailable(*args, **kwargs):
        raise RuntimeError(
            "torchvision video decoding is unavailable in this Kaggle runtime; "
            "text-to-SVG generation does not require it."
        )

    io_mod.read_video = _read_video_unavailable

    transforms_mod = types.ModuleType("torchvision.transforms")
    functional_mod = types.ModuleType("torchvision.transforms.functional")

    class _InterpolationMode:
        NEAREST = "nearest"
        BILINEAR = "bilinear"
        BICUBIC = "bicubic"

    def _resize(img, size, interpolation=None, antialias=True):
        if not isinstance(img, torch.Tensor):
            return img.resize(tuple(reversed(size)) if isinstance(size, list) else size)
        mode = interpolation or "bilinear"
        if mode == _InterpolationMode.BICUBIC:
            mode = "bicubic"
        elif mode == _InterpolationMode.NEAREST:
            mode = "nearest"
        else:
            mode = "bilinear"
        x = img.float()
        squeeze = False
        if x.ndim == 3:
            x = x.unsqueeze(0)
            squeeze = True
        kwargs = {"size": size, "mode": mode}
        if mode in {"bilinear", "bicubic"}:
            kwargs["align_corners"] = False
            kwargs["antialias"] = antialias
        out = F.interpolate(x, **kwargs)
        return out.squeeze(0) if squeeze else out

    functional_mod.resize = _resize
    transforms_mod.functional = functional_mod
    transforms_mod.InterpolationMode = _InterpolationMode
    tv.io = io_mod
    tv.transforms = transforms_mod

    sys.modules["torchvision"] = tv
    sys.modules["torchvision.io"] = io_mod
    sys.modules["torchvision.transforms"] = transforms_mod
    sys.modules["torchvision.transforms.functional"] = functional_mod
    return tv


def _patch_transformers_resize_embeddings_for_kaggle():
    """
    OmniSVG adds SVG tokens to Qwen with resize_token_embeddings(). Newer
    Transformers defaults to mean/covariance initialisation for added tokens,
    which calls CUDA linalg. On a 16 GB T4, the default resize also allocates
    the new 197k-token embedding table on GPU while the old table is still
    resident, causing an avoidable OOM. Force the older random-init path and do
    the duplicate-table allocation on CPU, then move the final tables back.
    """
    # Ensure pytorch_utils is patched before importing modeling_utils so that
    # the `from .pytorch_utils import (...)` inside modeling_utils succeeds even
    # if this function is called before VFMAutoencoder has been constructed.
    _patch_transformers_pytorch_utils_for_kaggle()
    try:
        from transformers.modeling_utils import PreTrainedModel

        current = PreTrainedModel.resize_token_embeddings
        if getattr(current, "_diffusvg_no_mean_resizing", False):
            return

        def _resize_token_embeddings_no_mean(self, *args, **kwargs):
            args = list(args)
            if len(args) >= 3:
                args[2] = False
                kwargs.pop("mean_resizing", None)
            else:
                kwargs["mean_resizing"] = False

            input_emb = self.get_input_embeddings()
            output_emb = self.get_output_embeddings()
            input_device = input_emb.weight.device if input_emb is not None else None
            output_device = (
                output_emb.weight.device
                if output_emb is not None and output_emb is not input_emb
                else None
            )
            should_stage_on_cpu = (
                torch.cuda.is_available()
                and input_device is not None
                and input_device.type == "cuda"
            )

            if should_stage_on_cpu:
                input_emb.to("cpu")
                if output_emb is not None and output_emb is not input_emb:
                    output_emb.to("cpu")
                gc.collect()
                torch.cuda.empty_cache()

            result = current(self, *args, **kwargs)

            if should_stage_on_cpu:
                new_input_emb = self.get_input_embeddings()
                if new_input_emb is not None:
                    new_input_emb.to(input_device)
                new_output_emb = self.get_output_embeddings()
                if (
                    new_output_emb is not None
                    and new_output_emb is not new_input_emb
                    and output_device is not None
                ):
                    new_output_emb.to(output_device)
                gc.collect()
                torch.cuda.empty_cache()

            return result

        _resize_token_embeddings_no_mean._diffusvg_no_mean_resizing = True
        PreTrainedModel.resize_token_embeddings = _resize_token_embeddings_no_mean
    except Exception:
        pass


def _install_torch_legacy_serialization_shim():
    """
    Older PyTorch checkpoints can reference torch.utils.serialization during
    unpickling. Newer PyTorch no longer exposes that module, but torch.load only
    needs the import target to exist for these legacy tensor pickles.
    """
    try:
        import types
        import torch.serialization as _torch_serialization

        mod = sys.modules.get("torch.utils.serialization")
        if mod is None:
            mod = types.ModuleType("torch.utils.serialization")
            sys.modules["torch.utils.serialization"] = mod
        mod.__path__ = []  # allow legacy "from torch.utils.serialization import config"

        for _name in dir(_torch_serialization):
            if not hasattr(mod, _name):
                setattr(mod, _name, getattr(_torch_serialization, _name))

        config_mod = sys.modules.get("torch.utils.serialization.config")
        if config_mod is None:
            config_mod = types.ModuleType("torch.utils.serialization.config")
            sys.modules["torch.utils.serialization.config"] = config_mod
        if not hasattr(config_mod, "load"):
            config_mod.load = types.SimpleNamespace()
        if not hasattr(config_mod, "save"):
            config_mod.save = types.SimpleNamespace()

        _load_endianness = getattr(_torch_serialization, "LoadEndianness", None)
        _native_endianness = (
            getattr(_load_endianness, "NATIVE", None)
            if _load_endianness is not None else None
        )
        _load_defaults = {
            "mmap": False,
            "endianness": _native_endianness,
            "mmap_flags": getattr(__import__("mmap"), "MAP_PRIVATE", None),
            "calculate_storage_offsets": False,
        }
        for _name, _value in _load_defaults.items():
            if not hasattr(config_mod.load, _name):
                setattr(config_mod.load, _name, _value)

        _save_defaults = {
            "compute_crc32": True,
            "use_pinned_memory_for_d2h": False,
            "storage_alignment": 64,
        }
        for _name, _value in _save_defaults.items():
            if not hasattr(config_mod.save, _name):
                setattr(config_mod.save, _name, _value)

        mod.config = config_mod

        def _legacy_getattr(name):
            if name == "config":
                return config_mod
            return getattr(_torch_serialization, name)

        mod.__getattr__ = _legacy_getattr
        if hasattr(torch, "utils"):
            torch.utils.serialization = mod
    except Exception:
        pass


def _patch_torch_load_for_legacy_omnisvg():
    """
    OmniSVG's published pytorch_model.bin can be a legacy pickle on some Kaggle
    images. Install the removed torch.utils.serialization import target and
    retry legacy checkpoints with weights_only=False when PyTorch's safe loader
    cannot read them.
    """
    _install_torch_legacy_serialization_shim()
    try:
        import pickle

        current = torch.load
        if getattr(current, "_diffusvg_legacy_omnisvg", False):
            return

        def _torch_load_legacy_omnisvg(*args, **kwargs):
            _install_torch_legacy_serialization_shim()
            try:
                return current(*args, **kwargs)
            except ModuleNotFoundError as e:
                if "torch.utils.serialization" not in str(e):
                    raise
            except ImportError as e:
                msg = str(e)
                if (
                    "torch.utils.serialization" not in msg
                    and "serialization" not in msg
                    and "config" not in msg
                ):
                    raise
            except pickle.UnpicklingError as e:
                msg = str(e)
                if "weights_only" not in msg and "Weights only" not in msg:
                    raise

            retry_kwargs = dict(kwargs)
            retry_kwargs["weights_only"] = False
            _install_torch_legacy_serialization_shim()
            return current(*args, **retry_kwargs)

        _torch_load_legacy_omnisvg._diffusvg_legacy_omnisvg = True
        torch.load = _torch_load_legacy_omnisvg
    except Exception:
        pass

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG-v8")


# ─── Environment detection ─────────────────────────────────────────────────────
def _detect_env() -> str:
    if Path("/kaggle").exists():
        return "kaggle"
    try:
        import google.colab; return "colab"
    except ImportError:
        pass
    return "local"

_ENV = _detect_env()
WORKING_DIR = {"kaggle": "/kaggle/working", "colab": "/content",
               "local": "/tmp/diffusvg_v8"}[_ENV]
os.makedirs(WORKING_DIR, exist_ok=True)


def _score_on_cpu() -> bool:
    """Keep reranking models off the T4 by default so OmniSVG has VRAM headroom."""
    default = "1" if _ENV == "kaggle" else "0"
    return os.environ.get("DIFFUSVG_SCORE_ON_CPU", default).lower() in {
        "1", "true", "yes", "on"
    }

# ─── Repo URLs ────────────────────────────────────────────────────────────────
# Two separate repos, two separate roles:
#   shiml20/SVG    → SVG diffusion framework (VFM feature space, paper backbone)
#   OmniSVG/OmniSVG → token-based SVG generator (SketchDecoder + Qwen2.5-VL)
_SVG_DIFFUSION_REPO = "https://github.com/shiml20/SVG.git"
_OMNISVG_REPO       = "https://github.com/OmniSVG/OmniSVG.git"

try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()          # Kaggle / Colab notebook — no __file__
_OMNISVG_DIR = _SCRIPT_DIR / "OmniSVG"   # updated by _setup_omnisvg()
_SVG_DIR     = _SCRIPT_DIR               # updated by _setup_svg_diffusion()


def _git_clone(repo: str, target: Path, label: str) -> bool:
    """Shallow-clone repo into target. Returns True on success."""
    if target.exists() and any(target.iterdir()):
        log.info(f"[{label}] Already present at {target}")
        return True
    log.info(f"[{label}] Cloning {repo} → {target} …")
    r = subprocess.run(
        ["git", "clone", "--depth", "1", repo, str(target)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        log.error(f"[{label}] git clone failed:\n{r.stderr[-600:]}")
        return False
    log.info(f"[{label}] Clone complete.")
    return True


def _pip_req(req_file: Path, label: str):
    if req_file.exists():
        log.info(f"[{label}] pip install -r {req_file.name} …")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)]
        )


# ── 1. SVG diffusion framework (shiml20/SVG) ──────────────────────────────────
def _setup_svg_diffusion() -> Path:
    """
    Ensure the SVG diffusion framework (shiml20/SVG) is available.
    Used for: VFMAutoencoder weights, diffusion backbone, reference generation.

    Resolution order:
      1. Already next to this script (local dev)
      2. WORKING_DIR/shiml20_SVG/ (previously cloned)
      3. Clone from GitHub
    """
    # 1. Script is inside the repo (local dev)
    if (_SCRIPT_DIR / "svg_t2i").exists() or (_SCRIPT_DIR / "train.py").exists():
        log.info(f"[SVG-Diffusion] Found locally at {_SCRIPT_DIR}")
        return _SCRIPT_DIR

    # 2. Previously cloned
    cached = Path(WORKING_DIR) / "shiml20_SVG"
    if cached.exists() and any(cached.iterdir()):
        log.info(f"[SVG-Diffusion] Already cloned at {cached}")
        return cached

    # 3. Clone
    ok = _git_clone(_SVG_DIFFUSION_REPO, cached, "SVG-Diffusion")
    if not ok:
        log.warning("[SVG-Diffusion] Clone failed — VFM diffusion features unavailable.")
        return cached   # may be empty; callers must guard
    _pip_req(cached / "requirements.txt", "SVG-Diffusion")
    return cached


# ── 2. OmniSVG token generator (OmniSVG/OmniSVG) ─────────────────────────────
def _setup_omnisvg() -> Path:
    """
    Ensure OmniSVG/ (SketchDecoder + Qwen2.5-VL) is available.
    inference.py loads config.yaml with a relative path, so the caller must
    os.chdir(omnisvg_dir) before importing it.

    Resolution order:
      1. OmniSVG/ next to this script  (local dev / Colab)
      2. /kaggle/input/**/OmniSVG/     (Kaggle dataset mount)
      3. WORKING_DIR/OmniSVG/          (previously cloned)
      4. Clone from GitHub
    """
    # 1. Local
    local = _SCRIPT_DIR / "OmniSVG"
    if (local / "inference.py").exists():
        log.info(f"[OmniSVG] Found locally at {local}")
        return local

    # 2. Kaggle dataset mount
    if _ENV == "kaggle":
        for candidate in Path("/kaggle/input").rglob("OmniSVG/inference.py"):
            log.info(f"[OmniSVG] Found in Kaggle input: {candidate.parent}")
            return candidate.parent

    # 3. Previously cloned
    cached = Path(WORKING_DIR) / "OmniSVG"
    if (cached / "inference.py").exists():
        log.info(f"[OmniSVG] Already cloned at {cached}")
        return cached

    # 4. Clone
    ok = _git_clone(_OMNISVG_REPO, cached, "OmniSVG")
    if not ok:
        raise RuntimeError("[OmniSVG] Clone failed — SVG generation unavailable.")
    _pip_req(cached / "requirements.txt", "OmniSVG")
    return cached


_SVG_DIR     = _setup_svg_diffusion()
_OMNISVG_DIR = _setup_omnisvg()

if str(_OMNISVG_DIR) not in sys.path:
    sys.path.insert(0, str(_OMNISVG_DIR))

# ─── Kaggle HuggingFace token ─────────────────────────────────────────────────
if _ENV == "kaggle" and "HF_TOKEN" not in os.environ:
    try:
        from kaggle_secrets import UserSecretsClient
        os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
        log.info("[Setup] HF_TOKEN loaded from Kaggle secrets.")
    except Exception:
        log.warning("[Setup] HF_TOKEN not found in Kaggle secrets. "
                    "Private model downloads may fail.")

log.info(f"Env={_ENV}  WorkDir={WORKING_DIR}  SVG-Diffusion={_SVG_DIR}  OmniSVG={_OMNISVG_DIR}")


# ════════════════════════════════════════════════════════════════════════════════
# SVG DIFFUSION BACKEND  (shiml20/SVG — reference image generation)
# ════════════════════════════════════════════════════════════════════════════════

class SVGDiffusionBackend:
    """
    Optional wrapper around the shiml20/SVG diffusion framework.

    Role in the pipeline:
      1. Generate reference raster images from text prompts using the
         VFM-feature-space DiT model (SVG-T2I paper backbone).
         These reference images are compared against OmniSVG candidates
         via VFM cosine similarity in VFMGuidedOmniSVG.generate().
      2. Load pre-trained VFM decoder weights (if present in _SVG_DIR)
         into VFMAutoencoder to skip random initialisation.

    Gracefully falls back (available=False) when:
      - _SVG_DIR was not cloned or is empty
      - The repo has no recognised inference entry point
      - Any import error occurs
    """

    # Entry-point probes: (module_name, callable_attr) pairs, in priority order
    _ENTRY_POINTS = [
        ("inference",   "generate"),
        ("inference",   "sample"),
        ("generate",    "generate"),
        ("sample",      "sample"),
        ("infer",       "infer"),
        ("t2i",         "generate"),
        ("pipeline",    "generate"),
    ]

    # Candidate paths for pre-trained VFM decoder weights inside _SVG_DIR
    _DECODER_WEIGHT_PATHS = [
        "pretrained/vfm_decoder.pt",
        "checkpoints/vfm_decoder.pt",
        "weights/vfm_decoder.pt",
        "vfm_decoder.pt",
        "pretrained/autoencoder_decoder.pt",
    ]

    def __init__(self, svg_dir: Path):
        self.svg_dir = svg_dir
        self._ready: bool = False
        self._generate_fn = None
        self._setup()

    def _setup(self):
        if not self.svg_dir.exists() or not any(self.svg_dir.iterdir()):
            log.info("[SVGDiffusion] Directory absent or empty — reference generation disabled.")
            return

        svg_dir_str = str(self.svg_dir)
        if svg_dir_str not in sys.path:
            sys.path.insert(0, svg_dir_str)

        _prev_cwd = os.getcwd()
        try:
            os.chdir(svg_dir_str)
            for mod_name, fn_name in self._ENTRY_POINTS:
                try:
                    mod = __import__(mod_name)
                    fn = getattr(mod, fn_name, None)
                    if callable(fn):
                        self._generate_fn = fn
                        self._ready = True
                        log.info(f"[SVGDiffusion] Inference API: {mod_name}.{fn_name}()")
                        break
                except (ImportError, AttributeError):
                    continue
        except Exception as e:
            log.warning(f"[SVGDiffusion] Setup error: {e}")
        finally:
            os.chdir(_prev_cwd)

        if not self._ready:
            log.info("[SVGDiffusion] No inference API found — "
                     "VFM decoder weight loading still available.")

    @property
    def available(self) -> bool:
        return self._ready

    def generate(self, prompt: str, size: int = 512) -> Optional[Image.Image]:
        """
        Generate a reference raster image for the given text prompt using the
        shiml20/SVG DiT model.  Returns None on any failure.
        """
        if not self._ready:
            return None
        _prev_cwd = os.getcwd()
        try:
            os.chdir(str(self.svg_dir))
            result = self._generate_fn(prompt=prompt, size=size)
            # Handle various return shapes
            if isinstance(result, Image.Image):
                return result.convert("RGB")
            if isinstance(result, (list, tuple)) and result:
                r = result[0]
                if isinstance(r, Image.Image):
                    return r.convert("RGB")
                if isinstance(r, np.ndarray):
                    return Image.fromarray(r).convert("RGB")
            if isinstance(result, np.ndarray):
                return Image.fromarray(result).convert("RGB")
        except Exception as e:
            log.warning(f"[SVGDiffusion] generate() failed for '{prompt[:50]}': {e}")
        finally:
            os.chdir(_prev_cwd)
        return None

    def load_vfm_decoder_weights(self, decoder: "nn.Module") -> bool:
        """
        Try to load pre-trained VFM decoder weights from the shiml20/SVG
        checkpoint directory into the provided decoder nn.Module.
        Returns True if weights were loaded, False otherwise.
        """
        for rel_path in self._DECODER_WEIGHT_PATHS:
            candidate = self.svg_dir / rel_path
            if candidate.exists():
                log.info(f"[SVGDiffusion] Loading VFM decoder weights: {candidate}")
                try:
                    state = torch.load(str(candidate), map_location="cpu",
                                       weights_only=True)
                    # state might be raw state_dict or {'state_dict': ...}
                    if isinstance(state, dict) and "state_dict" in state:
                        state = state["state_dict"]
                    decoder.load_state_dict(state, strict=False)
                    log.info("[SVGDiffusion] Decoder weights loaded.")
                    return True
                except Exception as e:
                    log.warning(f"[SVGDiffusion] Weight load failed: {e}")
        return False


# Initialise once at module level — used by VFMAutoencoder and VFMGuidedOmniSVG
_svg_diffusion_backend = SVGDiffusionBackend(_SVG_DIR)


# ════════════════════════════════════════════════════════════════════════════════
# PAPER-INSPIRED CONFIGURATION  (Tables 7 & 8)
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class VFMConfig:
    """
    VFM encoder/decoder config — mirrors SVG-T2I autoencoder-P (Table 7).

    Paper (autoencoder-P):
      Encoder: DINOv3-s16p, frozen, 29M params, latent_dim=384
      Decoder: CNN [512,256,256,128,128]→3ch, 43M params
      Optimizer: Adam, lr=1e-4, β=(0.5,0.9)
    """
    encoder_model: str = "facebook/dinov2-small"   # DINOv3-s16p proxy (22M)
    patch_size: int = 16                            # 16×16 patch tokens
    latent_dim: int = 384                           # DINOv3-ViT-S/16+ output dim
    resolutions: Tuple = (224, 448, 896)            # 3-scale analysis (vs v7's 2)
    frozen_encoder: bool = True                     # Paper: "Frozen"
    # Decoder channel progression (paper Table 7)
    decoder_channels: Tuple = (512, 256, 256, 128, 128)
    decoder_out_channels: int = 3
    # Quality thresholds (calibrated from paper Fig 4 DINO numbers)
    threshold_high: float = 0.88   # good SVG (paper DINO: ~0.88-0.96)
    threshold_medium: float = 0.70 # acceptable  (paper DINO: ~0.68-0.79)
    threshold_reject: float = 0.40 # degenerate  (paper: below this → bad)


@dataclass
class TrainingConfig:
    """
    4-stage progressive training — adapted from SVG-T2I Table 4.

    Paper stages (DiT on raster):
      Stage 1: 256² anchor, 60M imgs, 91K steps, bs=1536 → 140M seen
      Stage 2: 512² anchor, 60M imgs, 90K steps, bs=768  →  70M seen
      Stage 3: 1024² anchor, 15M imgs, 44K steps, bs=768 →  34M seen
      Stage 4: 1024² HQ tuning, 1M imgs, 40K steps       →  30M seen

    SVG adaptation: stages by complexity + render resolution.
    """
    # LoRA (adapted from paper DiT optimizer Table 8)
    lora_r: int = 8                 # Higher than v7's 4 for better capacity
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    lora_target_modules: Tuple = (
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    )
    # Optimizer (paper: AdamW, lr=2e-4, β=(0.9,0.95))
    optimizer: str = "paged_adamw_8bit"
    base_lr: float = 2e-4
    betas: Tuple = (0.9, 0.95)
    weight_decay: float = 0.01
    max_grad_norm: float = 0.3
    batch_size: int = 1
    grad_accum: int = 8
    warmup_ratio: float = 0.1

    # Per-stage overrides (lr, render_size, max_chars, quality_threshold)
    STAGES: Tuple = (
        # id, name,                max_chars, render_px, epochs, lr,    vfm_thresh
        (1, "Low Complexity",       500,       224,       1,  2e-4,  0.00),
        (2, "Medium Complexity",   2000,       448,       1,  1e-4,  0.30),
        (3, "High Resolution",     4000,       896,       1,  5e-5,  0.50),
        (4, "Aesthetic HQ Tuning", 4000,       896,       1,  2e-5,  0.70),
    )

    # Text + SVG target length.  Keep enough room after the system/few-shot
    # prompt so SVG output tokens are not entirely masked.
    max_text_len_early: int = 768
    max_text_len_late: int = 1024


@dataclass
class GenerationConfig:
    """OmniSVG generation settings."""
    model_size: str = "4B"          # OmniSVG 4B (Qwen2.5-VL-3B)
    n_candidates: int = 4           # Paper: evaluate multiple, pick best
    temperature_icon: float = 0.5
    temperature_illustration: float = 0.6
    top_p: float = 0.90
    repetition_penalty: float = 1.05
    max_new_tokens: int = 1200


@dataclass
class HierarchicalDiffusionConfig:
    """
    Lightweight first-pass hierarchical latent diffusion trial.

    NeuralField-LDM fits a hierarchical diffusion model to compressed scene
    latents.  For SVGs we use rendered SVG VFM latents instead:
      level 0: 224px CLS latent, global layout
      level 1: 448px CLS latent, object structure conditioned on level 0
      level 2: 896px CLS latent, fine detail conditioned on level 1

    The fitted model is used as a reranking prior for OmniSVG candidates, not
    as a replacement for OmniSVG's SVG token generator.
    """
    enabled: bool = True
    resolutions: Tuple[int, ...] = (224, 448, 896)
    diffusion_steps: int = 64
    train_steps: int = 200
    batch_size: int = 16
    hidden_dim: int = 512
    time_dim: int = 64
    lr: float = 1e-3
    max_fit_samples: int = 256
    score_trials: int = 4
    score_temperature: float = 0.75
    cache_name: str = "hierarchical_latent_diffusion.pt"


@dataclass
class Config:
    """Top-level pipeline config."""
    vfm: VFMConfig = field(default_factory=VFMConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    hierarchical: HierarchicalDiffusionConfig = field(
        default_factory=HierarchicalDiffusionConfig
    )

    training_pairs_path: str = ""
    output_dir: str = os.path.join(WORKING_DIR, "output_v8")
    max_svg_chars: int = 4000
    min_svg_chars: int = 50
    val_split: float = 0.1


cfg = Config()
os.makedirs(cfg.output_dir, exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════════
# SVG UTILITIES
# ════════════════════════════════════════════════════════════════════════════════

_SVG_SYSTEM = """\
You are an SVG code generator. Given a text description, output ONLY the SVG \
elements (rect, circle, ellipse, polygon, path, etc.) that would go inside:
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">…</svg>

Rules:
- Output ONLY SVG elements, no <svg> wrapper, no comments, no explanation.
- Start with a background <rect width="200" height="200" fill="#RRGGBB"/>.
- Use solid hex fill colors only. No gradients, filters, or blur.
- Keep shapes simple: 3–30 elements. All coordinates in the 0–200 range.
- For icons: clean, minimal, single-concept. For illustrations: richer detail.
"""

_FEW_SHOT = [
    ("a blue circle on white",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="100" cy="100" r="65" fill="#1565C0"/>'),
    ("a red heart",
     '<rect width="200" height="200" fill="#ffffff"/>\n'
     '<circle cx="75" cy="85" r="30" fill="#E53935"/>\n'
     '<circle cx="125" cy="85" r="30" fill="#E53935"/>\n'
     '<polygon points="45,100 100,165 155,100" fill="#E53935"/>'),
    ("a green tree",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n'
     '<polygon points="100,20 40,110 160,110" fill="#2E7D32"/>\n'
     '<polygon points="100,50 45,130 155,130" fill="#388E3C"/>\n'
     '<rect x="85" y="140" width="30" height="45" fill="#5D4037"/>'),
    ("a yellow star on dark blue",
     '<rect width="200" height="200" fill="#0D1B2A"/>\n'
     '<polygon points="100,20 112,60 155,60 122,83 133,125 100,100 67,125 '
     '78,83 45,60 88,60" fill="#FFD600"/>'),
    ("a purple butterfly",
     '<rect width="200" height="200" fill="#F8F0FF"/>\n'
     '<ellipse cx="70" cy="90" rx="50" ry="35" fill="#7B1FA2"/>\n'
     '<ellipse cx="130" cy="90" rx="50" ry="35" fill="#7B1FA2"/>\n'
     '<ellipse cx="70" cy="115" rx="30" ry="20" fill="#AB47BC"/>\n'
     '<ellipse cx="130" cy="115" rx="30" ry="20" fill="#AB47BC"/>\n'
     '<rect x="97" y="60" width="6" height="80" rx="3" fill="#4A148C"/>'),
]


def _few_shot_block(prompt: str, n: int = 2) -> str:
    examples = random.sample(_FEW_SHOT, min(n, len(_FEW_SHOT)))
    parts = [f"Prompt: {p}\nSVG:\n{svg}\n" for p, svg in examples]
    parts.append(f"Prompt: {prompt}\nSVG:")
    return "\n".join(parts)


def _wrap_svg(body: str, size: int = 200) -> str:
    return (f'<svg viewBox="0 0 {size} {size}" '
            f'xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>')


def _render_svg(svg_str: str, size: int = 224) -> Optional[Image.Image]:
    try:
        import cairosvg
        png = cairosvg.svg2png(bytestring=svg_str.encode(),
                               output_width=size, output_height=size)
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        return None


def _complexity(svg: str) -> str:
    n = len(re.findall(r"<(rect|circle|ellipse|polygon|polyline|line|path)\b", svg))
    return "simple" if n <= 3 else ("medium" if n <= 10 else "complex")


class _DINOImageProcessorLite:
    """
    Minimal DINOv2 preprocessing to avoid Transformers' fragile AutoImageProcessor
    lazy import path on Kaggle. Images are already resized by callers.
    """
    image_mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    image_std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    def __call__(self, images, return_tensors: str = "pt") -> Dict[str, torch.Tensor]:
        if isinstance(images, Image.Image):
            images = [images]
        tensors = []
        for img in images:
            arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
            tensor = torch.from_numpy(arr).permute(2, 0, 1)
            tensor = (tensor - self.image_mean) / self.image_std
            tensors.append(tensor)
        return {"pixel_values": torch.stack(tensors, dim=0)}


def _disable_torchao_for_transformers():
    """
    Kaggle can ship a torchao build that imports torch._inductor and crashes on
    duplicate decomposition registrations. Transformers only treats torchao as
    optional here, so force all availability probes to False and clear partial
    modules before loading model classes.
    """
    try:
        import transformers.utils as _tf_utils
        import transformers.utils.import_utils as _tf_import_utils

        def _false_available(*args, **kwargs):
            return False

        def _is_torch_tensor(x):
            return bool(getattr(torch, "is_tensor", lambda _: False)(x))

        def _is_numpy_array(x):
            return isinstance(x, np.ndarray)

        def _to_numpy(x):
            if _is_numpy_array(x):
                return x
            if _is_torch_tensor(x):
                return x.detach().cpu().numpy()
            if hasattr(x, "numpy"):
                return x.numpy()
            return np.asarray(x)

        if not hasattr(_tf_import_utils, "_torch_version"):
            _tf_import_utils._torch_version = getattr(torch, "__version__", "0.0.0")
        for _name in (
            "_torchvision_version", "_timm_version", "_torchao_version",
            "_tf_version", "_flax_version", "_jax_version",
        ):
            if not hasattr(_tf_import_utils, _name):
                setattr(_tf_import_utils, _name, "unavailable")

        def _torch_version_cmp(library_version: str, op, accept_dev: bool = False) -> bool:
            try:
                from packaging import version as _version
                current = _version.parse(str(_tf_import_utils._torch_version).split("+")[0])
                target = _version.parse(str(library_version).split("+")[0])
                return op(current, target)
            except Exception:
                return False

        if not hasattr(_tf_import_utils, "is_torch_less_or_equal"):
            _tf_import_utils.is_torch_less_or_equal = (
                lambda library_version, accept_dev=False:
                    _torch_version_cmp(library_version, lambda a, b: a <= b, accept_dev)
            )
        if not hasattr(_tf_import_utils, "is_torch_greater_or_equal"):
            _tf_import_utils.is_torch_greater_or_equal = (
                lambda library_version, accept_dev=False:
                    _torch_version_cmp(library_version, lambda a, b: a >= b, accept_dev)
            )
        if not hasattr(_tf_import_utils, "is_torchdynamo_compiling"):
            _tf_import_utils.is_torchdynamo_compiling = lambda: False
        if not hasattr(_tf_import_utils, "get_torch_version"):
            _tf_import_utils.get_torch_version = (
                lambda: str(_tf_import_utils._torch_version)
            )
        if not hasattr(_tf_utils, "is_torchdynamo_compiling"):
            _tf_utils.is_torchdynamo_compiling = (
                _tf_import_utils.is_torchdynamo_compiling
            )

        _import_utils_helper_defaults = {
            "is_av_available": _false_available,
            "is_flash_attn_available": _false_available,
            "is_flax_available": _false_available,
            "is_jax_available": _false_available,
            "is_scipy_available": _false_available,
            "is_sklearn_available": _false_available,
            "is_tf_available": _false_available,
            "is_timm_available": _false_available,
            "is_torch_flex_attn_available": _false_available,
            "is_torchao_available": _false_available,
            "is_torchvision_available": _false_available,
            "is_torch_available": lambda *args, **kwargs: True,
            "is_vision_available": lambda *args, **kwargs: True,
            "requires_backends": lambda obj, backends: None,
        }
        for _name, _fn in _import_utils_helper_defaults.items():
            if not hasattr(_tf_import_utils, _name):
                setattr(_tf_import_utils, _name, _fn)

        _tf_import_utils._torchao_available = False
        _tf_import_utils._torchao_version = "unavailable"
        _tf_utils._torchao_available = False
        _tf_utils._torchao_version = "unavailable"
        _tf_utils.is_torchao_available = _false_available
        _tf_utils.is_torch_flex_attn_available = _false_available
        _tf_utils.is_flash_attn_available = _false_available
        _tf_utils.is_av_available = _false_available
        _tf_utils.is_scipy_available = _false_available
        for _name, _fn in {
            "is_jax_tensor": _false_available,
            "is_tf_tensor": _false_available,
            "is_torch_tensor": _is_torch_tensor,
            "is_numpy_array": _is_numpy_array,
            "to_numpy": _to_numpy,
        }.items():
            if not hasattr(_tf_utils, _name):
                setattr(_tf_utils, _name, _fn)
        if not hasattr(_tf_utils, "ExplicitEnum"):
            from enum import Enum

            class _ExplicitEnum(str, Enum):
                @classmethod
                def _missing_(cls, value):
                    raise ValueError(
                        f"{value!r} is not a valid {cls.__name__}; "
                        f"choose one of {[x.value for x in cls]}"
                    )

            _tf_utils.ExplicitEnum = _ExplicitEnum
        if not hasattr(_tf_utils, "TensorType"):
            _ExplicitEnumBase = getattr(_tf_utils, "ExplicitEnum", str)

            class _TensorType(_ExplicitEnumBase):
                PYTORCH = "pt"
                TENSORFLOW = "tf"
                NUMPY = "np"
                JAX = "jax"
                MLX = "mlx"

            _tf_utils.TensorType = _TensorType
        if not hasattr(_tf_utils, "requires_backends"):
            _tf_utils.requires_backends = lambda obj, backends: None
    except Exception:
        pass

    for _name in [m for m in list(sys.modules)
                  if m == "torchao" or m.startswith("torchao.")]:
        sys.modules.pop(_name, None)


def _patch_transformers_pytorch_utils_for_kaggle():
    """
    Kaggle's mixed Transformers install has modeling_utils.py from a newer
    version that imports several symbols from pytorch_utils that the older
    system pytorch_utils.py doesn't export.  Add all of them at once.

    Symbols added when missing:
      find_pruneable_heads_and_indices, prune_linear_layer, prune_conv1d_layer,
      id_tensor_storage, isin_mps_friendly, prune_layer
    """
    try:
        import transformers.pytorch_utils as _pu

        if not hasattr(_pu, "find_pruneable_heads_and_indices"):
            def _find_pruneable(heads, n_heads, head_size, already_pruned_heads):
                mask = torch.ones(n_heads, head_size)
                heads = set(heads) - already_pruned_heads
                for head in heads:
                    head = head - sum(1 if h < head else 0 for h in already_pruned_heads)
                    mask[head] = 0
                mask = mask.view(-1).contiguous().eq(1)
                index = torch.arange(len(mask))[mask].long()
                return heads, index
            _pu.find_pruneable_heads_and_indices = _find_pruneable

        if not hasattr(_pu, "prune_linear_layer"):
            def _prune_linear(layer, index, dim=0):
                index = index.to(layer.weight.device)
                W = layer.weight.index_select(dim, index).clone().detach()
                b = None
                if layer.bias is not None:
                    b = (layer.bias.clone().detach() if dim == 1
                         else layer.bias[index].clone().detach())
                new_size = list(layer.weight.size())
                new_size[dim] = len(index)
                new_layer = nn.Linear(
                    new_size[1], new_size[0], bias=layer.bias is not None
                ).to(layer.weight.device)
                new_layer.weight.requires_grad = False
                new_layer.weight.copy_(W.contiguous())
                new_layer.weight.requires_grad = True
                if b is not None:
                    new_layer.bias.requires_grad = False
                    new_layer.bias.copy_(b.contiguous())
                    new_layer.bias.requires_grad = True
                return new_layer
            _pu.prune_linear_layer = _prune_linear

        if not hasattr(_pu, "prune_conv1d_layer"):
            # Conv1D (transformers custom) has weight shape (nx, nf) — transposed
            # compared to nn.Linear. dim=1 (default) selects output features.
            _Conv1D_cls = getattr(_pu, "Conv1D", None)
            def _prune_conv1d(layer, index, dim=1):
                index = index.to(layer.weight.device)
                W = layer.weight.index_select(dim, index).clone().detach()
                b = (layer.bias.clone().detach() if dim == 0
                     else layer.bias[index].clone().detach())
                new_size = list(layer.weight.size())
                new_size[dim] = len(index)
                # Conv1D(nf, nx): arg0=output feats=new_size[1], arg1=input=new_size[0]
                Cls = type(layer) if _Conv1D_cls is None else _Conv1D_cls
                new_layer = Cls(new_size[1], new_size[0]).to(layer.weight.device)
                new_layer.weight.requires_grad = False
                new_layer.weight.copy_(W.contiguous())
                new_layer.weight.requires_grad = True
                new_layer.bias.requires_grad = False
                new_layer.bias.copy_(b.contiguous())
                new_layer.bias.requires_grad = True
                return new_layer
            _pu.prune_conv1d_layer = _prune_conv1d

        if not hasattr(_pu, "id_tensor_storage"):
            def _id_tensor_storage(tensor):
                try:
                    return id(tensor.untyped_storage())
                except AttributeError:
                    return id(tensor.storage())
            _pu.id_tensor_storage = _id_tensor_storage

        if not hasattr(_pu, "isin_mps_friendly"):
            _pu.isin_mps_friendly = torch.isin

        if not hasattr(_pu, "prune_layer"):
            def _prune_layer(layer, index, dim=None):
                if isinstance(layer, nn.Linear):
                    return _pu.prune_linear_layer(layer, index,
                                                  dim=0 if dim is None else dim)
                _Conv1D = getattr(_pu, "Conv1D", None)
                if _Conv1D is not None and isinstance(layer, _Conv1D):
                    return _pu.prune_conv1d_layer(layer, index,
                                                  dim=1 if dim is None else dim)
                raise ValueError(f"Cannot prune layer of type {type(layer)}")
            _pu.prune_layer = _prune_layer

    except Exception:
        pass


def _load_dinov2_model(model_id: str) -> nn.Module:
    """
    Load DINOv2 without importing AutoImageProcessor. The direct module import
    avoids transformers.models.auto.image_processing_auto, which is where the
    Kaggle mixed-install failures have been surfacing.
    """
    _patch_transformers_pytorch_utils_for_kaggle()
    _disable_torchao_for_transformers()
    for _name in (
        "transformers.modeling_utils",
        "transformers.models.dinov2.modeling_dinov2",
    ):
        sys.modules.pop(_name, None)
    from transformers.models.dinov2.modeling_dinov2 import Dinov2Model
    return Dinov2Model.from_pretrained(model_id)


# ════════════════════════════════════════════════════════════════════════════════
# VFM AUTOENCODER  (SVG-T2I Sec. 3.2 + Table 7, autoencoder-P equivalent)
# ════════════════════════════════════════════════════════════════════════════════

class VFMEncoder(nn.Module):
    """
    Frozen DINOv2-small encoder — proxy for SVG-T2I's DINOv3-s16p.

    Paper: "autoencoder-P (Pure) utilises frozen DINOv3 features directly."
    Maps H×W×3 → (H/16)×(W/16)×384.  We expose both CLS and patch tokens.
    """
    def __init__(self, config: VFMConfig):
        super().__init__()
        self.processor = _DINOImageProcessorLite()
        self.backbone = _load_dinov2_model(config.encoder_model)
        if config.frozen_encoder:
            for p in self.backbone.parameters():
                p.requires_grad_(False)
            self.backbone.eval()
        self.latent_dim = config.latent_dim
        self.patch_size = config.patch_size

    @torch.no_grad()
    def forward(self, images: List[Image.Image],
                resolution: int = 224) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
          cls    : (B, latent_dim)        — global representation
          patches: (B, num_patches, D)    — spatial VFM features
        """
        resized = [img.resize((resolution, resolution), Image.LANCZOS)
                   for img in images]
        inputs = self.processor(images=resized, return_tensors="pt")
        device = next(self.backbone.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        out = self.backbone(**inputs)
        tokens = out.last_hidden_state        # (B, 1+num_patches, D)
        return tokens[:, 0, :], tokens[:, 1:, :]


class VFMDecoder(nn.Module):
    """
    Lightweight CNN decoder — mirrors SVG-T2I Table 7 decoder config.
    Channels [512,256,256,128,128]→3ch, ~43M params (paper value).
    Maps (B, D, h, w) patch-feature tensor → (B, 3, H_out, W_out) pixel image.
    """
    def __init__(self, config: VFMConfig):
        super().__init__()
        in_ch, layers = config.latent_dim, []
        for out_ch in config.decoder_channels:
            layers += [
                nn.ConvTranspose2d(in_ch, out_ch, 4, 2, 1),
                nn.GroupNorm(8, out_ch),
                nn.GELU(),
            ]
            in_ch = out_ch
        layers += [nn.Conv2d(in_ch, config.decoder_out_channels, 3, 1, 1),
                   nn.Sigmoid()]
        self.net = nn.Sequential(*layers)

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        """patches: (B, num_patches, D)  →  (B, 3, H_out, W_out)"""
        B, N, D = patches.shape
        h = w = int(math.sqrt(N))
        x = patches.reshape(B, h, w, D).permute(0, 3, 1, 2)
        return self.net(x)


class VFMAutoencoder(nn.Module):
    """
    Full autoencoder-P: frozen DINOv2 encoder + learned CNN decoder.

    Used for:
      1. Reconstructing rendered SVGs through VFM feature space (quality proxy).
      2. Providing normalised patch features for the FlowMatchingScorer.
      3. Training signal: reconstruction loss on training SVGs drives the
         decoder to capture what VFM features encode about SVG appearance.
    """
    def __init__(self, config: VFMConfig):
        super().__init__()
        self.encoder = VFMEncoder(config)
        self.decoder = VFMDecoder(config)
        self.config = config

    def to(self, device):
        self.encoder.backbone = self.encoder.backbone.to(device)
        self.decoder = self.decoder.to(device)
        return self

    def reconstruct(self, images: List[Image.Image],
                    resolution: int = 224) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode images → VFM features → decoded pixel image.
        Returns (reconstructed_tensor (B,3,H,W), patch_features (B,N,D)).
        """
        cls, patches = self.encoder(images, resolution)
        recon = self.decoder(patches)
        return recon, patches

    def reconstruction_loss(self, images: List[Image.Image],
                            resolution: int = 224) -> torch.Tensor:
        """MSE between original and VFM-decoded pixels (training signal)."""
        targets = torch.stack([
            torch.from_numpy(
                np.asarray(
                    img.resize((resolution, resolution), Image.LANCZOS).convert("RGB"),
                    dtype=np.float32,
                ) / 255.0
            ).permute(2, 0, 1)
            for img in images
        ]).to(next(self.decoder.parameters()).device)
        recon, _ = self.reconstruct(images, resolution)
        recon_resized = F.interpolate(recon, size=targets.shape[-2:],
                                      mode="bilinear", align_corners=False)
        return F.mse_loss(recon_resized, targets)

    def load_pretrained_decoder(self) -> bool:
        """
        Try to load pre-trained VFM decoder weights from the shiml20/SVG
        framework (if cloned).  Called once after model construction to
        skip random initialisation when checkpoint exists.
        """
        return _svg_diffusion_backend.load_vfm_decoder_weights(self.decoder)


# ════════════════════════════════════════════════════════════════════════════════
# MULTI-RESOLUTION VFM GATE  (SVG-T2I Sec. 4.3 + Figure 4)
# ════════════════════════════════════════════════════════════════════════════════

class MultiResolutionVFMGate:
    """
    Enhanced quality gate extending v7's VFMQualityGate to 3 scales.

    Paper key finding (Section 4.3 / Fig 4):
      VAE features ≈ resolution-invariant (cosine sim ≈ 1.0 across scales).
      DINOv2 / DINOv3 features shift noticeably across scales:
        High-res pair (448→896): ~0.88–0.96
        Low-res pair  (224→448): ~0.60–0.79
      This scale sensitivity reveals semantic instability in degenerate SVGs
      (blank, noisy, or content-free) — a powerful training-data filter.

    This class:
      • Tests at 224, 448, 896 px (3 scales — paper uses these in Fig 4).
      • Reports per-pair cosine similarity and mean consistency.
      • Rejects SVGs below threshold_reject (default 0.40).
      • Categorises accepted SVGs as "high", "medium", or "low" quality.
    """

    def __init__(self, config: VFMConfig):
        self.config = config
        self._model = None
        self._proc = None

    def _lazy_load(self):
        if self._model is not None:
            return
        log.info(f"[VFMGate] Loading {self.config.encoder_model}…")
        self._proc = _DINOImageProcessorLite()
        self._model = _load_dinov2_model(self.config.encoder_model).eval()
        self._device = torch.device(
            "cuda" if torch.cuda.is_available() and not _score_on_cpu() else "cpu"
        )
        self._model = self._model.to(self._device)
        log.info("[VFMGate] Ready.")

    @torch.no_grad()
    def _cls(self, img: Image.Image, res: int) -> torch.Tensor:
        """Normalised CLS feature at given resolution."""
        self._lazy_load()
        img_r = img.resize((res, res), Image.LANCZOS)
        inputs = self._proc(images=img_r, return_tensors="pt")
        device = getattr(self, "_device", next(self._model.parameters()).device)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        feat = self._model(**inputs).last_hidden_state[:, 0, :]  # (1, D)
        return F.normalize(feat, dim=-1)

    def multi_resolution_scores(self, image: Image.Image) -> Dict[str, float]:
        """
        Cosine similarities between adjacent resolution pairs.
        Returns e.g. {"224→448": 0.74, "448→896": 0.91}.
        """
        feats = {r: self._cls(image, r) for r in self.config.resolutions}
        res_list = list(self.config.resolutions)
        return {
            f"{res_list[i]}→{res_list[i+1]}":
                float((feats[res_list[i]] @ feats[res_list[i+1]].T).item())
            for i in range(len(res_list) - 1)
        }

    def score_svg(self, svg_str: str,
                  reference: Optional[Image.Image] = None) -> Dict[str, Any]:
        """
        Full quality assessment for one SVG string.

        Steps:
          1. Render at 896px (highest fidelity).
          2. Compute 3-scale cross-resolution similarities.
          3. Optionally compare CLS features against a reference image.

        Returns score dict with 'passed' bool and 'tier' string.
        """
        img = _render_svg(svg_str, size=max(self.config.resolutions))
        if img is None:
            return {"passed": False, "mean_consistency": 0.0,
                    "tier": "invalid", "error": "render_failed"}

        sims = self.multi_resolution_scores(img)
        mean_c = float(np.mean(list(sims.values())))

        result: Dict[str, Any] = {
            "passed": mean_c >= self.config.threshold_reject,
            "mean_consistency": mean_c,
            "resolution_sims": sims,
            "tier": (
                "high"   if mean_c >= self.config.threshold_high   else
                "medium" if mean_c >= self.config.threshold_medium else
                "low"
            ),
        }

        if reference is not None:
            ref_feat = self._cls(reference, self.config.resolutions[-1])
            svg_feat = self._cls(img, self.config.resolutions[-1])
            result["svg_ref_sim"] = float((svg_feat @ ref_feat.T).item())

        return result

    def unload(self):
        del self._model, self._proc
        self._model = self._proc = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        log.info("[VFMGate] Unloaded.")


# ════════════════════════════════════════════════════════════════════════════════
# FLOW MATCHING SCORER  (SVG-T2I Eq. 1–2 adapted)
# ════════════════════════════════════════════════════════════════════════════════

class FlowMatchingScorer:
    """
    Adapts SVG-T2I's flow matching objective to score generated SVGs.

    Paper's flow matching (Eq 1-2):
        x_t = (1-t)·x_0 + t·ε,   ε ~ N(0,I),   t ∈ [0,1]
        L_FM = E[ λ(t) ‖v_θ(x_t,t) − (ε − x_0)‖ ]
    where x_0 is the data distribution (VFM features of real images).

    Adaptation (no trained flow model needed):
    We fit the reference distribution μ,σ from training SVG features.
    At inference we measure how far a generated SVG's features are from
    the trajectory midpoint x_{0.5} = 0.5·μ + 0.5·0 (halfway to noise):
        score = sigmoid( cos_sim(generated_feat, μ_norm) × 10 )
    A score near 1.0 means the features are on the data manifold (good SVG).
    A score near 0.5 means ambiguous; near 0.0 means off-manifold (bad).
    """

    def __init__(self):
        self._ref_mean: Optional[torch.Tensor] = None
        self._ref_std:  Optional[torch.Tensor] = None
        self._fitted: bool = False

    def fit(self, gate: MultiResolutionVFMGate,
            images: List[Image.Image], resolution: int = 224):
        """
        Build reference VFM feature distribution from good training examples.
        Call this once after dataset filtering, before scoring candidates.
        """
        log.info(f"[FlowScore] Fitting on {len(images)} reference images…")
        feats = []
        for img in images:
            f = gate._cls(img, resolution)   # (1, D)
            feats.append(f.cpu())
        all_f = torch.cat(feats, dim=0)      # (N, D)
        self._ref_mean = all_f.mean(0)
        self._ref_std  = all_f.std(0) + 1e-8
        self._fitted = True
        log.info("[FlowScore] Reference distribution fitted.")

    def score(self, gate: MultiResolutionVFMGate,
              image: Image.Image, resolution: int = 224) -> float:
        """
        Flow-matching quality score ∈ [0, 1].  Higher = more on-manifold.

        Uses cosine similarity between the image's CLS feature and the
        normalised reference mean — a proxy for the flow trajectory:
            p(x | "data manifold") ∝ exp( cos_sim(x, μ_norm) )
        """
        if not self._fitted:
            return 0.5   # uninformative prior if no reference
        feat = gate._cls(image, resolution).cpu()       # (1, D)
        feat_n = F.normalize(feat, dim=-1)
        mean_n = F.normalize(self._ref_mean.unsqueeze(0), dim=-1)
        cos = float(F.cosine_similarity(feat_n, mean_n).item())
        return float(torch.sigmoid(torch.tensor(cos * 10.0)).item())

    def score_svg(self, svg_str: str, gate: MultiResolutionVFMGate,
                  resolution: int = 224) -> float:
        img = _render_svg(svg_str, size=resolution)
        if img is None:
            return 0.0
        return self.score(gate, img, resolution)


# ════════════════════════════════════════════════════════════════════════════════
# HIERARCHICAL LATENT DIFFUSION SCORER  (NeuralField-LDM adaptation)
# ════════════════════════════════════════════════════════════════════════════════

def _sinusoidal_time_embedding(t: torch.Tensor, dim: int) -> torch.Tensor:
    """DDPM-style timestep embedding."""
    half = dim // 2
    if half == 0:
        return t.float().unsqueeze(-1)
    freqs = torch.exp(
        torch.arange(half, device=t.device, dtype=torch.float32)
        * (-math.log(10000.0) / max(half - 1, 1))
    )
    args = t.float().unsqueeze(1) * freqs.unsqueeze(0)
    emb = torch.cat([torch.sin(args), torch.cos(args)], dim=-1)
    if dim % 2:
        emb = F.pad(emb, (0, 1))
    return emb


class _HierarchicalLatentDenoiser(nn.Module):
    """Small conditional denoiser for one VFM hierarchy level."""

    def __init__(self, latent_dim: int, time_dim: int, hidden_dim: int):
        super().__init__()
        self.time_dim = time_dim
        self.net = nn.Sequential(
            nn.Linear(latent_dim * 2 + time_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, latent_dim),
        )

    def forward(self, x_t: torch.Tensor, t: torch.Tensor,
                parent: Optional[torch.Tensor] = None) -> torch.Tensor:
        if parent is None:
            parent = torch.zeros_like(x_t)
        t_emb = _sinusoidal_time_embedding(t, self.time_dim).to(x_t.dtype)
        return self.net(torch.cat([x_t, parent, t_emb], dim=-1))


class HierarchicalLatentDiffusionScorer:
    """
    Tiny hierarchical DDPM prior over rendered-SVG VFM latents.

    This is the practical "first try" suggested by the hierarchy papers:
      1. Encode accepted training SVG renders at multiple VFM resolutions.
      2. Train one denoiser per level using the DDPM noise-prediction loss.
      3. Condition each finer level on the previous coarser clean latent.
      4. Use denoising error as an on-manifold score for candidate SVGs.

    It is deliberately small enough for Kaggle/T4.  When no training data is
    available, it stays inactive and reranking falls back to VFM x CLIP x flow.
    """

    def __init__(self, config: HierarchicalDiffusionConfig,
                 cache_dir: Optional[str] = None):
        self.config = config
        self.cache_dir = cache_dir
        self.models: List[_HierarchicalLatentDenoiser] = []
        self._latent_dim: Optional[int] = None
        self._fitted = False
        self._device = torch.device(
            "cuda" if torch.cuda.is_available() and not _score_on_cpu() else "cpu"
        )
        betas = torch.linspace(1e-4, 0.02, config.diffusion_steps)
        self._alphas_cumprod = torch.cumprod(1.0 - betas, dim=0)

    @property
    def fitted(self) -> bool:
        return self._fitted

    def cache_path(self) -> Optional[str]:
        if not self.cache_dir:
            return None
        return os.path.join(self.cache_dir, self.config.cache_name)

    def _init_models(self, latent_dim: int):
        self._latent_dim = latent_dim
        self.models = [
            _HierarchicalLatentDenoiser(
                latent_dim=latent_dim,
                time_dim=self.config.time_dim,
                hidden_dim=self.config.hidden_dim,
            ).to(self._device)
            for _ in self.config.resolutions
        ]

    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.cache_path()
        if not path or not os.path.exists(path):
            return False
        try:
            state = torch.load(path, map_location="cpu")
            latent_dim = int(state["latent_dim"])
            self._init_models(latent_dim)
            for model, model_state in zip(self.models, state["models"]):
                model.load_state_dict(model_state)
                model.eval()
            self._alphas_cumprod = state.get(
                "alphas_cumprod", self._alphas_cumprod
            ).float()
            self._fitted = True
            log.info(f"[HierDiff] Loaded cached prior: {path}")
            return True
        except Exception as e:
            log.warning(f"[HierDiff] Cache load failed: {e}")
            return False

    def save(self, path: Optional[str] = None):
        path = path or self.cache_path()
        if not path or not self._fitted:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(
            {
                "latent_dim": self._latent_dim,
                "resolutions": tuple(self.config.resolutions),
                "alphas_cumprod": self._alphas_cumprod.cpu(),
                "models": [m.cpu().state_dict() for m in self.models],
            },
            path,
        )
        self.models = [m.to(self._device) for m in self.models]
        log.info(f"[HierDiff] Saved prior: {path}")

    @torch.no_grad()
    def _extract_latents(self, gate: MultiResolutionVFMGate,
                         images: List[Image.Image]) -> List[torch.Tensor]:
        level_feats: List[List[torch.Tensor]] = [
            [] for _ in self.config.resolutions
        ]
        for img in images:
            for level, res in enumerate(self.config.resolutions):
                feat = gate._cls(img, res).cpu().float()
                level_feats[level].append(feat)
        return [torch.cat(feats, dim=0) for feats in level_feats]

    def fit(self, gate: MultiResolutionVFMGate, images: List[Image.Image]):
        if not self.config.enabled:
            log.info("[HierDiff] Disabled.")
            return
        if not images:
            log.info("[HierDiff] No images available; scorer inactive.")
            return
        if self.load():
            return

        max_n = self.config.max_fit_samples
        if len(images) > max_n:
            rng = random.Random(0)
            images = rng.sample(images, max_n)

        log.info(
            f"[HierDiff] Fitting hierarchical latent DDPM on {len(images)} SVG renders..."
        )
        latents = self._extract_latents(gate, images)
        n, latent_dim = latents[0].shape
        self._init_models(latent_dim)
        latents = [x.to(self._device) for x in latents]
        alphas_cumprod = self._alphas_cumprod.to(self._device)

        params = [p for model in self.models for p in model.parameters()]
        opt = torch.optim.AdamW(params, lr=self.config.lr, weight_decay=1e-4)
        batch_size = min(self.config.batch_size, n)

        for step in range(1, self.config.train_steps + 1):
            idx = torch.randint(0, n, (batch_size,), device=self._device)
            t = torch.randint(
                0, self.config.diffusion_steps, (batch_size,),
                device=self._device,
            )
            a_t = alphas_cumprod[t].view(-1, 1)
            loss = torch.zeros((), device=self._device)

            for level, model in enumerate(self.models):
                x0 = latents[level][idx]
                eps = torch.randn_like(x0)
                x_t = a_t.sqrt() * x0 + (1.0 - a_t).sqrt() * eps
                parent = (
                    torch.zeros_like(x0)
                    if level == 0 else latents[level - 1][idx]
                )
                pred = model(x_t, t, parent)
                loss = loss + F.mse_loss(pred, eps)

            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()

            if step == 1 or step % 50 == 0 or step == self.config.train_steps:
                log.info(
                    f"[HierDiff] step {step:04d}/{self.config.train_steps} "
                    f"loss={float(loss.item()):.4f}"
                )

        for model in self.models:
            model.eval()
        self._fitted = True
        self.save()

    def fit_from_dataset(self, gate: MultiResolutionVFMGate,
                         dataset: List[Dict[str, Any]]):
        if not self.config.enabled:
            return
        if self.load():
            return
        images: List[Image.Image] = []
        max_render = max(self.config.resolutions)
        pool = [x for x in dataset if x.get("svg")]
        if len(pool) > self.config.max_fit_samples:
            pool = random.Random(0).sample(pool, self.config.max_fit_samples)
        for item in pool:
            img = _render_svg(item.get("svg", ""), size=max_render)
            if img is not None:
                images.append(img)
        self.fit(gate, images)

    @torch.no_grad()
    def score(self, gate: MultiResolutionVFMGate,
              image: Image.Image) -> Optional[Dict[str, Any]]:
        if not self._fitted:
            return None

        latents = [
            x.to(self._device)
            for x in self._extract_latents(gate, [image])
        ]
        alphas_cumprod = self._alphas_cumprod.to(self._device)
        t_values = torch.linspace(
            max(1, self.config.diffusion_steps // 4),
            self.config.diffusion_steps - 1,
            steps=max(1, self.config.score_trials),
            device=self._device,
        ).long()

        level_mse: List[float] = []
        level_scores: List[float] = []
        for level, model in enumerate(self.models):
            x0 = latents[level]
            parent = torch.zeros_like(x0) if level == 0 else latents[level - 1]
            losses = []
            gen = torch.Generator(device=self._device)
            gen.manual_seed(1234 + level * 17)
            for t_scalar in t_values:
                t = t_scalar.view(1)
                a_t = alphas_cumprod[t].view(-1, 1)
                eps = torch.randn(
                    x0.shape, generator=gen, device=self._device,
                    dtype=x0.dtype,
                )
                x_t = a_t.sqrt() * x0 + (1.0 - a_t).sqrt() * eps
                pred = model(x_t, t, parent)
                losses.append(float(F.mse_loss(pred, eps).item()))
            mse = float(np.mean(losses))
            level_mse.append(mse)
            level_scores.append(
                float(math.exp(-mse / max(self.config.score_temperature, 1e-6)))
            )

        if len(level_scores) == 3:
            weights = np.asarray([0.35, 0.35, 0.30], dtype=np.float32)
        else:
            weights = np.ones(len(level_scores), dtype=np.float32)
        weights = weights / weights.sum()
        score = float(np.clip(np.dot(weights, level_scores), 0.0, 1.0))
        return {
            "hierarchical_score": score,
            "hierarchical_level_scores": {
                str(res): float(s)
                for res, s in zip(self.config.resolutions, level_scores)
            },
            "hierarchical_level_mse": {
                str(res): float(m)
                for res, m in zip(self.config.resolutions, level_mse)
            },
        }

    def score_svg(self, svg_str: str, gate: MultiResolutionVFMGate
                  ) -> Optional[Dict[str, Any]]:
        if not self._fitted:
            return None
        img = _render_svg(svg_str, size=max(self.config.resolutions))
        if img is None:
            return {
                "hierarchical_score": 0.0,
                "hierarchical_level_scores": {},
                "hierarchical_level_mse": {},
            }
        return self.score(gate, img)


# ════════════════════════════════════════════════════════════════════════════════
# PROGRESSIVE CURRICULUM  (SVG-T2I Table 4 adapted)
# ════════════════════════════════════════════════════════════════════════════════

class SVGProgressiveCurriculum:
    """
    4-stage training curriculum for OmniSVG fine-tuning.

    Mirrors SVG-T2I Table 4's resolution/data progression:
      Stage 1 → simple SVGs, 224px render  (paper: 256² low-res, 60M images)
      Stage 2 → medium SVGs, 448px render  (paper: 512² mid-res, 60M images)
      Stage 3 → complex SVGs, 896px render (paper: 1024² high-res, 15M images)
      Stage 4 → best-quality SVGs, 896px   (paper: 1024² HQ tuning, 1M images)

    For OmniSVG: complexity proxy = SVG char count + VFM consistency score.
    Stage 4 additionally requires a high combined CLIP × VFM score.
    """

    STAGE_DEFS = [
        dict(id=1, name="Low Complexity",     min_c=50,   max_c=500,
             render=224, epochs=1, lr=2e-4,  vfm_min=0.00, max_text=256),
        dict(id=2, name="Medium Complexity",  min_c=50,   max_c=2000,
             render=448, epochs=1, lr=1e-4,  vfm_min=0.30, max_text=256),
        dict(id=3, name="High Resolution",    min_c=50,   max_c=4000,
             render=896, epochs=1, lr=5e-5,  vfm_min=0.50, max_text=256),
        dict(id=4, name="Aesthetic HQ",       min_c=100,  max_c=4000,
             render=896, epochs=1, lr=2e-5,  vfm_min=0.70, max_text=512),
    ]

    def __init__(self, dataset: List[Dict]):
        self.dataset = dataset

    def get_stage_data(self, stage_id: int) -> List[Dict]:
        s = self.STAGE_DEFS[stage_id - 1]
        out = []
        for item in self.dataset:
            svg = item.get("svg", "")
            n = len(svg)
            if not (s["min_c"] <= n <= s["max_c"]):
                continue
            vfm = item.get("vfm_consistency", 0.0)
            if vfm < s["vfm_min"]:
                continue
            if stage_id == 4:
                # Stage 4: also require decent CLIP score
                clip = item.get("clip_score", 0.0)
                if clip * vfm < 15.0:   # product heuristic (~CLIP>20, VFM>0.7)
                    continue
            out.append(item)
        # Curriculum sort: simple → complex within each stage
        out.sort(key=lambda x: len(x.get("svg", "")))
        return out

    def summary(self) -> str:
        lines = ["SVG Progressive Curriculum (SVG-T2I Table 4 adaptation):"]
        for s in self.STAGE_DEFS:
            n = len(self.get_stage_data(s["id"]))
            lines.append(
                f"  Stage {s['id']}: {s['name']:22s} | "
                f"chars {s['min_c']:4d}–{s['max_c']:4d} | "
                f"render {s['render']}px | lr={s['lr']:.0e} | "
                f"vfm≥{s['vfm_min']:.2f} | {n:5d} samples"
            )
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════════
# DATASET  (with VFM scoring + curriculum labels)
# ════════════════════════════════════════════════════════════════════════════════

class SVGCausalDataset(torch.utils.data.Dataset):
    """
    Causal LM dataset for OmniSVG LoRA training.
    Only SVG tokens (not the prompt) contribute to the loss, matching the
    training objective in the OmniSVG/DiffuSVG-v7 convention.
    """
    def __init__(self, pairs: List[Dict], tokenizer, max_len: int = 1024):
        self.pairs = pairs
        self.tok = tokenizer
        self.max_len = max_len

    def __len__(self): return len(self.pairs)

    def __getitem__(self, idx):
        item = self.pairs[idx]
        prompt = item["prompt"]
        svg    = item["svg"]
        few    = _few_shot_block(prompt, n=2)
        prompt_text = f"{_SVG_SYSTEM}\n\n{few}\n"
        text   = f"{prompt_text}{svg}"
        enc    = self.tok(text, truncation=True, max_length=self.max_len,
                          return_tensors="pt")
        input_ids = enc["input_ids"][0]
        labels    = input_ids.clone()
        # Mask prompt tokens from loss (only train on SVG output)
        prompt_enc = self.tok(prompt_text, truncation=True,
                              max_length=self.max_len,
                              return_tensors="pt")["input_ids"][0]
        prompt_len = min(len(prompt_enc), len(labels))
        labels[:prompt_len] = -100
        if torch.all(labels == -100):
            tail = max(1, min(128, len(labels) // 4))
            labels[-tail:] = input_ids[-tail:]
        return {"input_ids": input_ids, "labels": labels,
                "attention_mask": enc["attention_mask"][0]}


def collate_pad(batch, pad_id):
    max_len = max(b["input_ids"].size(0) for b in batch)
    for key in ("input_ids", "labels", "attention_mask"):
        for b in batch:
            t = b[key]; pad = max_len - t.size(0)
            fill = pad_id if key == "input_ids" else (-100 if key == "labels" else 0)
            b[key] = F.pad(t, (0, pad), value=fill)
    return {k: torch.stack([b[k] for b in batch]) for k in batch[0]}


# ════════════════════════════════════════════════════════════════════════════════
# VFM-GUIDED OMNISVG  (N-best reranking via VFM × CLIP dual score)
# ════════════════════════════════════════════════════════════════════════════════

class VFMGuidedOmniSVG:
    """
    Wraps OmniSVG's SketchDecoder inference with SVG-T2I-inspired reranking.

    Generation loop (dual-scoring from paper Tables 5-6):
      1. Generate N candidate SVGs via OmniSVG (OmniSVG/inference.py API).
      2. Render each candidate at 896px (paper: 1024×1024 evaluation).
      3. Score with:
           - VFM consistency (multi-resolution DINOv2, paper Fig 4)
           - CLIP text-image alignment (paper uses GenEval/DPG-Bench)
           - Flow matching score (manifold proximity)
           - optional hierarchical latent diffusion prior
      4. Combined score = VFM × CLIP × flow × hier  (product generalises
         paper's dual-metric comparison in Tables 5–6).
      5. Return best-scoring SVG with full score breakdown.
    """

    def __init__(self, vfm_gate: MultiResolutionVFMGate,
                 flow_scorer: FlowMatchingScorer,
                 gen_cfg: GenerationConfig,
                 svg_diffusion: Optional["SVGDiffusionBackend"] = None,
                 hierarchical_scorer: Optional[
                     HierarchicalLatentDiffusionScorer
                 ] = None):
        self.vfm_gate = vfm_gate
        self.flow_scorer = flow_scorer
        self.gen_cfg = gen_cfg
        # shiml20/SVG diffusion backend — provides reference images for reranking
        self.svg_diffusion = svg_diffusion or _svg_diffusion_backend
        self.hierarchical_scorer = hierarchical_scorer
        self._clip_model = None
        self._omnisvg_loaded = False
        # OmniSVG globals are module-level in inference.py
        self._inf = None

    def _load_clip(self):
        if self._clip_model is not None:
            return
        from transformers import CLIPModel, CLIPProcessor
        model_id = "openai/clip-vit-base-patch32"
        log.info(f"[CLIP] Loading {model_id}…")
        self._clip_processor = CLIPProcessor.from_pretrained(model_id)
        model = CLIPModel.from_pretrained(model_id)
        model.eval()
        device = torch.device(
            "cuda" if torch.cuda.is_available() and not _score_on_cpu() else "cpu"
        )
        model = model.to(device)
        self._clip_model = model
        log.info("[CLIP] Ready.")

    @torch.no_grad()
    def _clip_score(self, image: Image.Image, text: str) -> float:
        self._load_clip()
        device = next(self._clip_model.parameters()).device
        inputs = self._clip_processor(
            text=[text], images=image, return_tensors="pt", padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        out = self._clip_model(**inputs)
        img_f = out.image_embeds
        txt_f = out.text_embeds
        img_f = F.normalize(img_f, dim=-1)
        txt_f = F.normalize(txt_f, dim=-1)
        return float((img_f @ txt_f.T).item() * 100)

    def _load_omnisvg(self):
        if self._omnisvg_loaded:
            return
        if not _OMNISVG_DIR.exists():
            raise RuntimeError(f"OmniSVG directory not found: {_OMNISVG_DIR}")
        log.info(f"[OmniSVG] Loading inference module from {_OMNISVG_DIR}…")
        # inference.py loads config.yaml with a relative path, so we must
        # chdir into OmniSVG/ before importing it.
        _prev_cwd = os.getcwd()
        try:
            os.chdir(str(_OMNISVG_DIR))
            _install_qwen_torchvision_stub()
            _patch_transformers_resize_embeddings_for_kaggle()
            _patch_torch_load_for_legacy_omnisvg()
            import inference as _inf_mod
            _patch_transformers_fsdp_for_kaggle()
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            # Correct API: load_models(model_size, weight_path=None, model_path=None)
            _inf_mod.load_models(self.gen_cfg.model_size)
            _patch_transformers_fsdp_for_kaggle()
            self._inf = _inf_mod
            self._omnisvg_loaded = True
            log.info("[OmniSVG] Model ready.")
        except Exception as e:
            log.error(f"[OmniSVG] Load failed: {e}")
            raise
        finally:
            os.chdir(_prev_cwd)

    def _generate_batch(self, prompt: str) -> List[str]:
        """
        Generate N candidate SVGs using the real OmniSVG API:
          prepare_inputs(task_type, content) → inputs dict
          generate_candidates(inputs, task_type, subtype, ...) → list of {'svg':…}
        Generates all N at once (more efficient than N separate calls).
        """
        _patch_transformers_fsdp_for_kaggle()
        inf = self._inf
        subtype = inf.detect_text_subtype(prompt)
        task_key = f"text-to-svg-{subtype}"
        tc = inf.TASK_CONFIGS.get(task_key, {})

        _prev_cwd = os.getcwd()
        try:
            os.chdir(str(_OMNISVG_DIR))
            inputs = inf.prepare_inputs("text-to-svg", prompt)
            results = inf.generate_candidates(
                inputs=inputs,
                task_type="text-to-svg",
                subtype=subtype,
                temperature=tc.get("default_temperature",
                                   self.gen_cfg.temperature_icon),
                top_p=tc.get("default_top_p", self.gen_cfg.top_p),
                top_k=tc.get("default_top_k", 50),
                repetition_penalty=tc.get("default_repetition_penalty",
                                          self.gen_cfg.repetition_penalty),
                max_length=self.gen_cfg.max_new_tokens,
                num_samples=self.gen_cfg.n_candidates,
            )
        finally:
            os.chdir(_prev_cwd)

        # results is a list of {'svg': str, 'img': PIL.Image, 'path_count': int}
        return [r["svg"] for r in results if r.get("svg")]

    def generate(self, prompt: str,
                 subtype: str = "auto") -> Tuple[Optional[str], Dict]:
        """
        Generate N candidates via OmniSVG, rerank by VFM×CLIP×flow[×hier][×ref_sim].

        When the shiml20/SVG diffusion backend is available, a reference raster
        image is generated first and used as the ground-truth anchor:
          - passed to MultiResolutionVFMGate.score_svg(reference=ref_img) so
            VFM feature similarity vs. the reference is computed (svg_ref_sim)
          - combined score becomes: VFM × CLIP/100 × flow × hier × ref_boost
            where ref_boost = (1 + svg_ref_sim) / 2  ∈ [0, 1]
        Without the backend the formula degrades to the original 3-term product.

        Returns (best_svg, score_dict).
        """
        self._load_omnisvg()
        scored = []

        # ── Optional reference image from shiml20/SVG DiT ───────────────────
        ref_img: Optional[Image.Image] = None
        if self.svg_diffusion is not None and self.svg_diffusion.available:
            log.info(f"[Rerank] Generating reference image via SVG-Diffusion…")
            ref_img = self.svg_diffusion.generate(prompt, size=512)
            if ref_img is not None:
                log.info("[Rerank] Reference image ready.")
            else:
                log.warning("[Rerank] SVG-Diffusion returned None — scoring without reference.")

        try:
            candidates = self._generate_batch(prompt)
        except Exception as e:
            log.error(f"[Rerank] OmniSVG batch generation failed: {e}")
            candidates = []

        candidates = [s for s in candidates if s and len(s) > cfg.min_svg_chars]

        if not candidates:
            log.warning(f"[Rerank] No valid candidates for: {prompt[:60]}")
            return None, {}

        for svg in candidates:
            render_img = _render_svg(svg, size=896)
            if render_img is None:
                scored.append({"svg": svg, "combined": 0.0})
                continue

            # Pass reference image so VFM gate also computes svg_ref_sim
            vfm  = self.vfm_gate.score_svg(svg, reference=ref_img)
            clip = self._clip_score(render_img, prompt)
            flow = self.flow_scorer.score_svg(svg, self.vfm_gate, resolution=224)
            hier = (
                self.hierarchical_scorer.score_svg(svg, self.vfm_gate)
                if self.hierarchical_scorer is not None
                and self.hierarchical_scorer.fitted
                else None
            )

            vfm_val = vfm.get("mean_consistency", 0.0)
            hier_val = hier.get("hierarchical_score", 1.0) if hier else 1.0

            # When a reference image is available, fold in its similarity term
            ref_sim = vfm.get("svg_ref_sim")
            if ref_sim is not None:
                ref_boost = (1.0 + ref_sim) / 2.0   # cosine [-1,1] → [0,1]
                combined  = vfm_val * (clip / 100.0) * flow * hier_val * ref_boost
            else:
                ref_boost = None
                combined  = vfm_val * (clip / 100.0) * flow * hier_val

            entry: Dict[str, Any] = {
                "svg": svg,
                "vfm_consistency": vfm_val,
                "vfm_tier": vfm.get("tier", "low"),
                "resolution_sims": vfm.get("resolution_sims", {}),
                "clip_score": clip,
                "flow_score": flow,
                "hierarchical_score": hier_val if hier else None,
                "combined": combined,
            }
            if hier:
                entry.update(hier)
            if ref_sim is not None:
                entry["svg_ref_sim"]  = ref_sim
                entry["ref_boost"]    = ref_boost
            scored.append(entry)

        best = max(scored, key=lambda x: x["combined"])
        ref_msg = (f" ref_sim={best.get('svg_ref_sim',0):.3f}"
                   if "svg_ref_sim" in best else "")
        log.info(f"[Rerank] Best combined={best['combined']:.4f} "
                 f"vfm={best.get('vfm_consistency',0):.3f} "
                 f"clip={best.get('clip_score',0):.1f} "
                 f"flow={best.get('flow_score',0):.3f} "
                 f"hier={best.get('hierarchical_score') or 0:.3f}{ref_msg}")
        return best["svg"], {k: v for k, v in best.items() if k != "svg"}


# ════════════════════════════════════════════════════════════════════════════════
# DATASET LOADING + VFM SCORING
# ════════════════════════════════════════════════════════════════════════════════

def load_and_score_dataset(path: str, gate: MultiResolutionVFMGate,
                           flow_scorer: FlowMatchingScorer) -> List[Dict]:
    """
    Load training_pairs.json, render each SVG, apply VFM gate, score for
    curriculum assignment.  Saves scored dataset to disk.
    """
    scored_path = os.path.join(cfg.output_dir, "scored_dataset.json")
    if os.path.exists(scored_path):
        log.info(f"[Dataset] Loading cached scored dataset: {scored_path}")
        with open(scored_path) as f:
            cached = json.load(f)
        if cached and not getattr(flow_scorer, "_fitted", False):
            ref_images = []
            for item in cached[:500]:
                img = _render_svg(item.get("svg", ""), size=448)
                if img is not None:
                    ref_images.append(img)
            if ref_images:
                flow_scorer.fit(gate, ref_images, resolution=224)
        return cached

    with open(path) as f:
        raw = json.load(f)
    log.info(f"[Dataset] {len(raw)} raw pairs loaded.")

    keep, ref_images = [], []
    for i, item in enumerate(raw):
        svg = item.get("svg", "")
        if not (cfg.min_svg_chars <= len(svg) <= cfg.max_svg_chars):
            continue
        img = _render_svg(svg, size=448)
        if img is None:
            continue
        scores = gate.score_svg(svg)
        if not scores["passed"]:
            continue
        item = {**item, **scores, "complexity": _complexity(svg)}
        keep.append(item)
        ref_images.append(img)
        if i % 100 == 0:
            log.info(f"[Dataset]  processed {i}/{len(raw)}, kept {len(keep)}")

    # Fit flow scorer on the accepted images
    if ref_images:
        flow_scorer.fit(gate, ref_images[:min(500, len(ref_images))], resolution=224)

    with open(scored_path, "w") as f:
        json.dump(keep, f, indent=2)
    log.info(f"[Dataset] {len(keep)} pairs kept → {scored_path}")
    return keep


# ════════════════════════════════════════════════════════════════════════════════
# LORA TRAINING  (one stage of the 4-stage curriculum)
# ════════════════════════════════════════════════════════════════════════════════

def train_stage(stage_def: Dict, dataset: List[Dict],
                model_name: str = "Qwen/Qwen2.5-VL-3B-Instruct",
                output_dir: Optional[str] = None) -> str:
    """
    Fine-tune OmniSVG (Qwen2.5-VL-3B) for one curriculum stage using QLoRA.

    Follows SVG-T2I Table 8 optimizer config (AdamW, lr=2e-4, β=(0.9,0.95))
    with per-stage learning rate overrides from STAGE_DEFS.

    Returns path to saved LoRA adapter for this stage.
    """
    _patch_transformers_pytorch_utils_for_kaggle()
    from transformers import (AutoTokenizer, AutoModelForCausalLM,
                              BitsAndBytesConfig, TrainingArguments, Trainer,
                              DataCollatorForSeq2Seq)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    tc = cfg.training
    stage_id = stage_def["id"]
    stage_out = output_dir or os.path.join(cfg.output_dir,
                                           f"adapter_stage{stage_id}")

    log.info(f"\n{'='*60}")
    log.info(f"[Train] Stage {stage_id}: {stage_def['name']}")
    log.info(f"[Train] Samples: {len(dataset)}  |  LR: {stage_def['lr']:.0e}"
             f"  |  Render: {stage_def['render']}px")

    if not dataset:
        log.warning(f"[Train] Stage {stage_id} has 0 samples — skipping.")
        return ""

    os.makedirs(stage_out, exist_ok=True)

    max_text_len = (tc.max_text_len_late if stage_id == 4
                    else tc.max_text_len_early)

    # ── 4-bit quantisation (T4 / 16GB) ───────────────────────────────────────
    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    log.info(f"[Train] Loading {model_name} (4-bit NF4)…")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name, quantization_config=bnb_cfg,
            device_map="auto", trust_remote_code=True,
        )
    except ValueError as e:
        if "Qwen2_5_VLConfig" not in str(e):
            raise
        from transformers import Qwen2_5_VLForConditionalGeneration

        log.info("[Train] Falling back to Qwen2_5_VLForConditionalGeneration.")
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_name, quantization_config=bnb_cfg,
            device_map="auto", trust_remote_code=True,
        )
    model = prepare_model_for_kbit_training(model)

    # ── LoRA (SVG-T2I Table 8 architecture spirit) ───────────────────────────
    lora_cfg = LoraConfig(
        r=tc.lora_r, lora_alpha=tc.lora_alpha,
        lora_dropout=tc.lora_dropout,
        target_modules=list(tc.lora_target_modules),
        bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    # ── Dataset ───────────────────────────────────────────────────────────────
    random.shuffle(dataset)
    n_val = max(1, int(len(dataset) * cfg.val_split))
    train_ds = SVGCausalDataset(dataset[n_val:], tokenizer, max_len=max_text_len)
    val_ds   = SVGCausalDataset(dataset[:n_val], tokenizer, max_len=max_text_len)
    pad_id   = tokenizer.pad_token_id

    # ── TrainingArguments (paper optimizer: AdamW, same scheduler shape) ─────
    n_train = max(1, len(train_ds))
    steps_per_epoch = math.ceil(n_train / (tc.batch_size * tc.grad_accum))
    total_steps = steps_per_epoch * stage_def["epochs"]

    train_args = TrainingArguments(
        output_dir=stage_out,
        num_train_epochs=stage_def["epochs"],
        per_device_train_batch_size=tc.batch_size,
        per_device_eval_batch_size=tc.batch_size,
        gradient_accumulation_steps=tc.grad_accum,
        learning_rate=stage_def["lr"],
        weight_decay=tc.weight_decay,
        max_grad_norm=tc.max_grad_norm,
        warmup_ratio=tc.warmup_ratio,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=max(1, total_steps // 20),
        save_steps=max(1, total_steps // 4),
        eval_strategy="steps",
        eval_steps=max(1, total_steps // 4),
        load_best_model_at_end=True,
        report_to="none",
        optim=tc.optimizer,
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=lambda b: collate_pad(b, pad_id),
    )
    trainer.train()
    model.save_pretrained(stage_out)
    tokenizer.save_pretrained(stage_out)
    log.info(f"[Train] Stage {stage_id} adapter saved → {stage_out}")

    del model, trainer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return stage_out


# ════════════════════════════════════════════════════════════════════════════════
# EVALUATION  (GenEval-style categories, Tables 5-6 of the paper)
# ════════════════════════════════════════════════════════════════════════════════

# GenEval-inspired prompt categories (Table 5 of SVG-T2I)
BASIC_EVAL_PROMPTS: Dict[str, List[str]] = {
    "single_obj": [
        "a red apple",
        "a blue star",
        "a green leaf",
        "a yellow sun",
        "a purple diamond",
    ],
    "two_obj": [
        "a cat next to a tree",
        "a moon above clouds",
        "a boat on water",
        "a bird on a branch",
    ],
    "counting": [
        "three blue circles",
        "five red dots",
        "two yellow stars",
    ],
    "colors": [
        "an orange pumpkin",
        "a pink flamingo",
        "a teal wave",
    ],
    "position": [
        "a house with a chimney on top",
        "a fish below a boat",
        "a flag above a pole",
    ],
    "color_attribution": [
        "a red car on a green road",
        "a blue bird with yellow wings",
    ],
}


COMPLEX_EVAL_PROMPTS: Dict[str, List[str]] = {
    "complex_scene": [
        "a beach sunset with palm trees and ocean waves",
        "a medieval castle on a hill under a full moon",
        "a futuristic cityscape with neon lights and flying cars",
        "a forest campsite with a tent, campfire, mountains, and stars",
        "a city street with a bus, traffic light, trees, and people",
    ],
    "complex_composition": [
        "a cozy kitchen table with a fruit bowl, mug, window, and sunlight",
        "a small harbor with boats, lighthouse, clouds, and birds",
        "a garden pond with lily pads, flowers, stones, and a bridge",
    ],
}


EVAL_PROMPTS: Dict[str, List[str]] = {
    **BASIC_EVAL_PROMPTS,
    **COMPLEX_EVAL_PROMPTS,
}


def get_eval_prompts(eval_set: str = "all") -> Dict[str, List[str]]:
    """Return the requested evaluation prompt suite."""
    if eval_set == "geneval":
        return BASIC_EVAL_PROMPTS
    if eval_set == "complex":
        return COMPLEX_EVAL_PROMPTS
    return EVAL_PROMPTS


def evaluate(pipeline: VFMGuidedOmniSVG,
             prompts: Optional[Dict[str, List[str]]] = None,
             output_dir: Optional[str] = None) -> Dict:
    """
    Evaluate SVG quality across GenEval-style categories.

    Metrics:
      - CLIP score (text-image alignment)
      - VFM consistency (cross-resolution semantic stability)
      - Flow manifold score
      - Combined product (VFM × CLIP/100 × flow)
      - Per-category pass rates (CLIP > 20.0 threshold)
    """
    prompts = prompts or EVAL_PROMPTS
    out_dir = output_dir or os.path.join(cfg.output_dir, "eval")
    os.makedirs(out_dir, exist_ok=True)

    all_results, cat_results = [], {}

    for category, cat_prompts in prompts.items():
        cat_scores, cat_pass = [], 0
        for prompt in cat_prompts:
            svg, scores = pipeline.generate(prompt)
            if svg is None:
                all_results.append({"prompt": prompt, "category": category,
                                    "success": False})
                continue

            # Save SVG and rendered PNG
            safe = re.sub(r"[^\w]+", "_", prompt)[:40]
            svg_path = os.path.join(out_dir, f"{safe}.svg")
            png_path = os.path.join(out_dir, f"{safe}.png")
            with open(svg_path, "w") as f:
                f.write(svg)
            img = _render_svg(svg, size=896)
            if img:
                img.save(png_path)

            passed = scores.get("clip_score", 0) >= 20.0
            cat_pass += int(passed)
            cat_scores.append(scores.get("clip_score", 0))

            result = {"prompt": prompt, "category": category,
                      "success": True, "passed": passed, **scores}
            all_results.append(result)

        n = len(cat_prompts)
        cat_results[category] = {
            "pass_rate": cat_pass / n if n else 0.0,
            "clip_mean": float(np.mean(cat_scores)) if cat_scores else 0.0,
            "n": n,
        }
        log.info(f"[Eval] {category:20s}  pass={cat_pass}/{n}  "
                 f"clip_mean={cat_results[category]['clip_mean']:.1f}")

    # Aggregate (mirrors paper Table 5: Overall↑)
    clips = [r.get("clip_score", 0) for r in all_results if r.get("success")]
    vfms  = [r.get("vfm_consistency", 0) for r in all_results if r.get("success")]
    flows = [r.get("flow_score", 0) for r in all_results if r.get("success")]
    hiers = [
        r.get("hierarchical_score") for r in all_results
        if r.get("success") and r.get("hierarchical_score") is not None
    ]
    combined = [
        r.get("combined", 0.0) for r in all_results if r.get("success")
    ]
    n_ok  = sum(r.get("passed", False) for r in all_results)

    summary = {
        "n_total":          len(all_results),
        "n_success":        sum(r.get("success", False) for r in all_results),
        "n_passed":         n_ok,
        "overall_pass_rate": n_ok / len(all_results) if all_results else 0.0,
        "clip_mean":        float(np.mean(clips)) if clips else 0.0,
        "clip_std":         float(np.std(clips))  if clips else 0.0,
        "vfm_mean":         float(np.mean(vfms))  if vfms  else 0.0,
        "flow_mean":        float(np.mean(flows)) if flows else 0.0,
        "hierarchical_mean": float(np.mean(hiers)) if hiers else None,
        "combined_mean":    float(np.mean(combined)) if combined else 0.0,
        "per_category":     cat_results,
        "results":          all_results,
    }

    with open(os.path.join(out_dir, "eval_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    log.info(f"\n[Eval] ══ Summary ══")
    log.info(f"       Overall pass rate : {summary['overall_pass_rate']:.2%}")
    log.info(f"       CLIP mean         : {summary['clip_mean']:.2f}")
    log.info(f"       VFM mean          : {summary['vfm_mean']:.3f}")
    log.info(f"       Flow mean         : {summary['flow_mean']:.3f}")
    if summary["hierarchical_mean"] is not None:
        log.info(f"       Hier diff mean    : {summary['hierarchical_mean']:.3f}")
    log.info(f"       Combined mean     : {summary['combined_mean']:.4f}")
    return summary


# ════════════════════════════════════════════════════════════════════════════════
# HTML GALLERY  (GenEval paper-style visual results)
# ════════════════════════════════════════════════════════════════════════════════

def build_gallery(eval_summary: Dict, out_dir: str) -> str:
    """Generate an HTML gallery grouping results by GenEval category."""
    rows = []
    for cat, meta in eval_summary.get("per_category", {}).items():
        rows.append(
            f"<tr><td colspan='3'><b>{cat}</b> "
            f"pass={meta['pass_rate']:.0%}  clip={meta['clip_mean']:.1f}</td></tr>"
        )
        cat_items = [r for r in eval_summary.get("results", [])
                     if r.get("category") == cat and r.get("success")]
        cat_items.sort(key=lambda x: x.get("combined", 0), reverse=True)
        for r in cat_items[:6]:
            safe = re.sub(r"[^\w]+", "_", r["prompt"])[:40]
            png = f"{safe}.png"
            tick = "✔" if r.get("passed") else "✗"
            hier_line = (
                f"hier={r.get('hierarchical_score',0):.3f}<br>"
                if r.get("hierarchical_score") is not None else ""
            )
            rows.append(
                f"<tr>"
                f"<td><img src='{png}' width='180' height='180' "
                f"style='border:1px solid #ccc'></td>"
                f"<td style='font-size:12px'>{r['prompt'][:60]}</td>"
                f"<td style='font-size:11px'>"
                f"{tick} clip={r.get('clip_score',0):.1f}<br>"
                f"vfm={r.get('vfm_consistency',0):.3f}<br>"
                f"flow={r.get('flow_score',0):.3f}<br>"
                f"{hier_line}"
                f"tier={r.get('vfm_tier','?')}"
                f"</td></tr>"
            )

    hier_mean = eval_summary.get("hierarchical_mean")
    hier_metric = (
        f"<span class='metric'>Hier diff: {hier_mean:.3f}</span>"
        if hier_mean is not None else ""
    )

    html = f"""<!DOCTYPE html><html><head>
<meta charset='utf-8'>
<title>DiffuSVG v8 — SVG-T2I Adaptation Gallery</title>
<style>
  body {{font-family:sans-serif;background:#1a1a2e;color:#eee;padding:20px}}
  h1   {{color:#4fc3f7}}
  h2   {{color:#b39ddb}}
  table{{border-collapse:collapse;width:100%}}
  td   {{padding:8px;vertical-align:top;border-bottom:1px solid #333}}
  .metric{{background:#0d47a1;padding:6px 12px;border-radius:6px;
           display:inline-block;margin:4px;font-size:13px}}
</style></head><body>
<h1>DiffuSVG v8 — SVG-T2I Paper Adaptation</h1>
<p>VFM-guided OmniSVG generation with 3-scale consistency gate,
flow-matching score, hierarchical latent diffusion prior, and 4-stage curriculum.</p>
<div>
  <span class='metric'>CLIP mean: {eval_summary.get('clip_mean',0):.2f}</span>
  <span class='metric'>VFM mean:  {eval_summary.get('vfm_mean',0):.3f}</span>
  <span class='metric'>Flow mean: {eval_summary.get('flow_mean',0):.3f}</span>
  {hier_metric}
  <span class='metric'>Pass rate: {eval_summary.get('overall_pass_rate',0):.1%}</span>
</div>
<br>
<table>
{''.join(rows)}
</table>
</body></html>"""

    path = os.path.join(out_dir, "gallery.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    log.info(f"[Gallery] Saved → {path}")
    return path


# ════════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════════════════════════

def run(training_pairs_path: str = "",
        start_stage: int = 1,
        end_stage:   int = 4,
        skip_train:  bool = False,
        eval_set: str = "all",
        use_hierarchical: bool = True,
        skip_eval: bool = False):
    """
    Full DiffuSVG SVG-T2I v8 pipeline:

      Stage 0: Initialise VFM components
      Stage 1: Load + VFM-score training dataset, build curriculum
      Stages 1-4: Progressive LoRA training on OmniSVG
      Final: Evaluate + build gallery
    """
    log.info("╔══════════════════════════════════════════════╗")
    log.info("║  DiffuSVG SVG-T2I v8  —  OmniSVG Adaptation ║")
    log.info("╚══════════════════════════════════════════════╝")

    # ── SVG diffusion backend status ─────────────────────────────────────────
    if _svg_diffusion_backend.available:
        log.info(f"[Init] SVG-Diffusion backend READY (shiml20/SVG @ {_SVG_DIR})")
        log.info("[Init] Reference-image-guided reranking enabled.")
    else:
        log.info(f"[Init] SVG-Diffusion backend unavailable (no inference API in {_SVG_DIR})")
        log.info("[Init] Reranking will use VFM × CLIP × flow only.")

    # ── Initialise VFM components ────────────────────────────────────────────
    log.info("\n[Init] Building VFM components (SVG-T2I Table 7 + Eq 1-2)…")
    gate = MultiResolutionVFMGate(cfg.vfm)
    flow = FlowMatchingScorer()
    hier = (
        HierarchicalLatentDiffusionScorer(cfg.hierarchical, cfg.output_dir)
        if use_hierarchical and cfg.hierarchical.enabled else None
    )

    # Attempt to warm-start decoder from shiml20/SVG pre-trained weights
    vfm_ae = VFMAutoencoder(cfg.vfm)
    if vfm_ae.load_pretrained_decoder():
        log.info("[Init] VFMAutoencoder decoder initialised from SVG-Diffusion weights.")
    else:
        log.info("[Init] VFMAutoencoder decoder randomly initialised (no pre-trained weights found).")

    # ── Dataset ──────────────────────────────────────────────────────────────
    pairs_path = training_pairs_path or cfg.training_pairs_path
    scored_data: List[Dict] = []
    if pairs_path and os.path.exists(pairs_path):
        log.info(f"\n[Stage 0] Loading + scoring dataset: {pairs_path}")
        scored_data = load_and_score_dataset(pairs_path, gate, flow)
    else:
        log.warning("[Stage 0] No training_pairs.json found — skipping training.")

    curriculum = SVGProgressiveCurriculum(scored_data)
    log.info(f"\n{curriculum.summary()}")

    # Fit/load the hierarchy before the first VFM gate is unloaded.  This is
    # the advisor-requested first-pass hierarchical diffusion trial.
    if hier is not None:
        if scored_data:
            hier.fit_from_dataset(gate, scored_data)
        elif hier.load():
            log.info("[HierDiff] Using cached prior without training pairs.")
        else:
            log.info("[HierDiff] No training pairs/cache; scorer inactive.")

    # ── 4-stage progressive LoRA training ────────────────────────────────────
    last_adapter: Optional[str] = None
    if scored_data and not skip_train:
        for stage_def in SVGProgressiveCurriculum.STAGE_DEFS:
            sid = stage_def["id"]
            if sid < start_stage or sid > end_stage:
                continue
            stage_data = curriculum.get_stage_data(sid)
            log.info(f"\n[Train] Stage {sid}/{len(SVGProgressiveCurriculum.STAGE_DEFS)}"
                     f" → {len(stage_data)} samples")
            adapter_path = train_stage(stage_def, stage_data)
            if adapter_path:
                last_adapter = adapter_path

        # Unload VFM gate before loading OmniSVG to free VRAM
        gate.unload()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # Free every non-OmniSVG model before the large Qwen load. On Kaggle T4,
    # the expanded SVG token tables need the last bit of available VRAM.
    try:
        gate.unload()
    except Exception:
        pass
    del vfm_ae
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if skip_eval:
        log.info(f"\n[Done] Training outputs → {cfg.output_dir}")
        log.info("[Done] Evaluation skipped (--no-eval).")
        if hier is not None:
            status = "fitted" if hier.fitted else "inactive"
            log.info(f"       HierDiff     → {status} ({hier.cache_path()})")
        if last_adapter:
            log.info(f"       Adapter      → {last_adapter}")
        return {
            "skipped_eval": True,
            "output_dir": cfg.output_dir,
            "adapter": last_adapter,
            "hierarchical": bool(hier is not None and hier.fitted),
        }

    # ── Evaluation ────────────────────────────────────────────────────────────
    log.info("\n[Eval] Setting up VFM-guided OmniSVG pipeline…")
    # Reload gate (lighter footprint now that training is done)
    gate2 = MultiResolutionVFMGate(cfg.vfm)
    pipeline = VFMGuidedOmniSVG(gate2, flow, cfg.generation,
                                 svg_diffusion=_svg_diffusion_backend,
                                 hierarchical_scorer=hier)

    eval_out = os.path.join(cfg.output_dir, "eval")
    summary  = evaluate(
        pipeline,
        prompts=get_eval_prompts(eval_set),
        output_dir=eval_out,
    )
    gallery  = build_gallery(summary, eval_out)

    log.info(f"\n[Done] Outputs       → {cfg.output_dir}")
    log.info(f"       Gallery      → {gallery}")
    log.info(f"       SVG-Diffusion→ {_SVG_DIR} (backend={'ready' if _svg_diffusion_backend.available else 'unavailable'})")
    log.info(f"       OmniSVG      → {_OMNISVG_DIR}")
    if hier is not None:
        status = "fitted" if hier.fitted else "inactive"
        log.info(f"       HierDiff     → {status} ({hier.cache_path()})")
    if last_adapter:
        log.info(f"       Adapter      → {last_adapter}")

    return summary


# ════════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="DiffuSVG SVG-T2I v8")
    p.add_argument("--pairs",   default="", help="Path to training_pairs.json")
    p.add_argument("--stage",   type=int,   default=0,
                   help="Run only this stage (1-4).  0 = all stages.")
    p.add_argument("--no-train", action="store_true",
                   help="Skip training; run evaluation only.")
    p.add_argument("--no-eval", action="store_true",
                   help="Skip final OmniSVG evaluation after training.")
    p.add_argument("--output",  default="",
                   help="Override output directory.")
    p.add_argument("--model-size", default="4B", choices=["4B", "8B"],
                   help="OmniSVG model size (default 4B for T4).")
    p.add_argument("--eval-set", default="all",
                   choices=["geneval", "complex", "all"],
                   help="Evaluation prompts: GenEval-style, complex scenes, or both.")
    p.add_argument("--no-hierarchical", action="store_true",
                   help="Disable hierarchical latent diffusion reranking prior.")
    p.add_argument("--hier-steps", type=int, default=0,
                   help="Override hierarchical diffusion prior train steps.")
    p.add_argument("--hier-samples", type=int, default=0,
                   help="Override max SVG renders used to fit the hierarchy.")
    # parse_known_args ignores Jupyter/Kaggle kernel flags like -f kernel.json
    args, _ = p.parse_known_args()

    if args.output:
        cfg.output_dir = args.output
        os.makedirs(cfg.output_dir, exist_ok=True)
    if args.model_size:
        cfg.generation.model_size = args.model_size
    if args.hier_steps > 0:
        cfg.hierarchical.train_steps = args.hier_steps
    if args.hier_samples > 0:
        cfg.hierarchical.max_fit_samples = args.hier_samples

    s = args.stage
    run(
        training_pairs_path=args.pairs,
        start_stage=s if s > 0 else 1,
        end_stage=s   if s > 0 else 4,
        skip_train=args.no_train,
        eval_set=args.eval_set,
        use_hierarchical=not args.no_hierarchical,
        skip_eval=args.no_eval,
    )
