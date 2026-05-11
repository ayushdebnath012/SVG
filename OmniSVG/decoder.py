import torch.nn as nn
import torch
import yaml
import os
from transformers import Qwen2_5_VLForConditionalGeneration, AutoConfig


def load_config(config_path=None):
    """Load configuration from config.yaml"""
    if config_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(current_dir, "config.yaml"),
            os.path.join(current_dir, "..", "config.yaml"),
            "config.yaml"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
        if config_path is None:
            raise FileNotFoundError("config.yaml not found")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


class SketchDecoder(nn.Module):
    """
    Autoregressive generative model.
    Supports optional 4-bit NF4 quantization (use_4bit=True) for low-VRAM GPUs
    such as the Kaggle T4 (16 GB).  When quantized the model uses ~4–6 GB instead
    of the full bfloat16 footprint, leaving headroom for attention activations and
    the expanded token-embedding table (vocab_size=197 000).
    """
    def __init__(self, config_path=None, model_path=None, use_4bit=False,
                 torch_dtype=None, **kwargs):
        super().__init__()

        config_data = load_config(config_path)

        model_config   = config_data.get('model', {})
        hf_config      = config_data.get('huggingface', {})

        self.bos_token_id = model_config['bos_token_id']
        self.eos_token_id = model_config['eos_token_id']
        self.pad_token_id = model_config['pad_token_id']

        self.vocab_size = model_config.get(
            'vocab_size',
            max(self.bos_token_id, self.eos_token_id, self.pad_token_id) + 1
        )

        if model_path is None:
            model_path = hf_config['qwen_model']

        # ── dtype selection ──────────────────────────────────────────────────
        # T4 has no native bfloat16 tensor cores; use float16 there.
        # A100/H100 support bfloat16 natively.
        if torch_dtype is None:
            torch_dtype = (torch.bfloat16
                           if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
                           else torch.float16)

        # ── build from_pretrained kwargs ─────────────────────────────────────
        # Use "auto" (multi-GPU distribution) only when CUDA is available.
        # Without CUDA, "auto" creates meta tensors that break state-dict loading.
        _device_map = "auto" if torch.cuda.is_available() else "cpu"
        load_kwargs = dict(
            attn_implementation="sdpa",
            device_map=_device_map,
        )

        if use_4bit:
            # 4-bit NF4 quantization via bitsandbytes — fits 4B model on T4 16 GB.
            # We keep compute_dtype=float16 because T4 lacks bf16 tensor cores.
            from transformers import BitsAndBytesConfig
            bnb_cfg = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            load_kwargs["quantization_config"] = bnb_cfg
            # torch_dtype must NOT be set when using quantization_config
        else:
            load_kwargs["torch_dtype"] = torch_dtype

        self.transformer = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path, **load_kwargs
        )

        # Resize embedding table to include OmniSVG-specific tokens
        self.transformer.resize_token_embeddings(self.vocab_size)

        # Update special-token ids in the config
        self.transformer.config.bos_token_id = self.bos_token_id
        self.transformer.config.eos_token_id = self.eos_token_id
        self.transformer.config.pad_token_id = self.pad_token_id

    def forward(self, *args, **kwargs):
        raise NotImplementedError("Forward pass not included in open-source version")