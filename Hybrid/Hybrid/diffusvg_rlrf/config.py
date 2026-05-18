from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Dict, List, Optional


HYBRID_DIR = Path(__file__).resolve().parents[1]
DEFAULT_WORK_DIR = HYBRID_DIR / "kaggle_rlrf_run"


@dataclass
class RuntimeConfig:
    seed: int = 42
    device: str = "cuda"
    dtype: str = "float16"
    profile: str = "legacy_t4_diffusvg_rlrf"
    output_dir: str = str(DEFAULT_WORK_DIR / "outputs")
    cache_dir: str = str(DEFAULT_WORK_DIR / "cache")
    num_workers: int = 2


@dataclass
class DiffuSVGConfig:
    """Policy model settings.

    T4 profile target from the legacy architecture:
    DiffuSVG is maintained with OmniSVG as the base generator. RLRF attaches
    LoRA to that existing OmniSVG-backed policy instead of creating a custom SFT
    base unless SFT is explicitly enabled as a bootstrap fallback.
    """

    model_name_or_path: str = os.environ.get(
        "DIFFUSVG_POLICY_MODEL", "Qwen/Qwen2.5-VL-3B-Instruct"
    )
    tokenizer_name_or_path: Optional[str] = None
    adapter_name_or_path: Optional[str] = os.environ.get("DIFFUSVG_ADAPTER") or None
    backend: str = "omnisvg"
    base_architecture: str = "omnisvg_4b_sketchdecoder_nf4"
    trust_remote_code: bool = True
    load_in_4bit: bool = True
    gradient_checkpointing: bool = True
    attn_implementation: Optional[str] = None
    max_new_tokens: int = 1200
    max_prompt_tokens: int = 512
    temperature: float = 0.9
    top_p: float = 0.90
    repetition_penalty: float = 1.05
    use_think_trace: bool = False


@dataclass
class OmniSVGConfig:
    enabled: bool = True
    repo_dir: str = os.environ.get("OMNISVG_DIR", "")
    model_size: str = "4B"
    model_path: str = os.environ.get("OMNISVG_QWEN_MODEL", "")
    weight_path: str = os.environ.get("OMNISVG_WEIGHTS", "")
    auto_find_repo: bool = True
    use_repo_inference: bool = True
    pix_len: int = 2048
    text_len: int = 200
    top_k: int = 50


@dataclass
class LoRAConfig:
    enabled: bool = True
    r: int = 8
    alpha: int = 32
    dropout: float = 0.10
    target_modules: List[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )
    output_dir: str = str(DEFAULT_WORK_DIR / "rlrf_adapter")


@dataclass
class SVGConfig:
    canvas_size: int = 384
    viewbox_size: int = 200
    min_svg_chars: int = 80
    max_svg_chars: int = 12000
    min_visible_elements: int = 2
    strip_text_elements: bool = True
    reject_external_refs: bool = True
    reject_scripts: bool = True


@dataclass
class CurriculumStageConfig:
    id: int
    name: str
    min_chars: int
    max_chars: int
    max_samples: int
    epochs: float
    learning_rate: float
    min_vfm: float
    max_length: int
    render_size: int = 384


@dataclass
class SFTConfig:
    """Optional bootstrap curriculum SFT.

    This is intentionally disabled by default because the main DiffuSVG path
    uses the already fine-tuned OmniSVG weights as the base model.
    """

    enabled: bool = False
    pairs_path: str = ""
    output_dir: str = str(DEFAULT_WORK_DIR / "diffusvg_sft_adapter")
    max_raw_pairs: int = 512
    scored_cache: str = str(DEFAULT_WORK_DIR / "scored_pairs.json")
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    max_grad_norm: float = 0.3
    weight_decay: float = 0.01
    warmup_ratio: float = 0.10
    optim: str = "paged_adamw_8bit"
    save_each_stage: bool = True
    stages: List[CurriculumStageConfig] = field(
        default_factory=lambda: [
            CurriculumStageConfig(1, "Low Complexity", 50, 500, 128, 1.0, 2e-4, 0.00, 768, 224),
            CurriculumStageConfig(2, "Medium Complexity", 50, 2000, 128, 1.0, 1e-4, 0.30, 768, 448),
            CurriculumStageConfig(3, "High Resolution", 50, 4000, 96, 1.0, 5e-5, 0.50, 1024, 896),
            CurriculumStageConfig(4, "Aesthetic HQ", 100, 4000, 64, 1.0, 2e-5, 0.70, 1024, 896),
        ]
    )


@dataclass
class RewardConfig:
    """Scaled-down DiffuSVG reward stack.

    The legacy T4 path scored candidates as VFM consistency x CLIP alignment
    x flow score. Here we keep that shape with DINOv2-small and CLIP ViT-B/32.
    """

    use_clip_proxy: bool = True
    clip_model: str = "openai/clip-vit-base-patch32"
    use_vfm_gate: bool = True
    vfm_model: str = "facebook/dinov2-small"
    vfm_resolutions: List[int] = field(default_factory=lambda: [224, 448, 896])
    vfm_threshold_reject: float = 0.40
    vfm_threshold_medium: float = 0.70
    vfm_threshold_high: float = 0.88
    score_device: str = "cuda"
    flow_default: float = 0.5
    use_vlm_judge: bool = False
    vlm_judge_model: str = "Qwen/Qwen2.5-VL-3B-Instruct"
    vlm_weight: float = 0.10
    structure_weight: float = 0.05
    compactness_weight: float = 0.05
    target_svg_chars: int = 4000
    text_copy_penalty: float = 0.5
    blank_penalty: float = 1.0
    render_fail_reward: float = -1.0


@dataclass
class RLRFConfig:
    enabled: bool = True
    prompt_path: str = ""
    max_prompts: int = 64
    train_steps: int = 40
    batch_size: int = 1
    rollouts_per_prompt: int = 4
    learning_rate: float = 5e-6
    weight_decay: float = 1e-2
    max_grad_norm: float = 1.0
    clip_epsilon: float = 0.2
    kl_coef: float = 0.0
    log_every: int = 5
    save_every: int = 40
    gradient_accumulation_steps: int = 1
    # --- Dynamic max-length (paper App. C.3) ---
    # For Text2SVG (no GT SVGs) we derive the budget from the model's own
    # recent output lengths via a rolling window.
    dynamic_max_length: bool = True
    dynamic_len_threshold: int = 200   # extra tokens above observed max chars/chars_per_token
    dynamic_len_min: int = 256         # floor (tokens)
    dynamic_len_max: int = 1200        # T4 ceiling from the legacy v8 profile
    chars_per_token: float = 4.0       # approximate SVG chars per token


@dataclass
class EvalConfig:
    enabled: bool = True
    prompt_path: str = ""
    n_candidates: int = 4
    max_eval_prompts: int = 12
    prompts: List[str] = field(
        default_factory=lambda: [
            "a red apple icon with a green leaf",
            "a yellow emoji wearing a light blue face mask",
            "a purple clipboard with yellow and orange accents",
            "two young girls riding red tricycles",
            "black bars of varying widths arranged like a barcode",
            "a cyberpunk cityscape at sunset with neon signs",
        ]
    )


@dataclass
class PipelineConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    diffusvg: DiffuSVGConfig = field(default_factory=DiffuSVGConfig)
    omnisvg: OmniSVGConfig = field(default_factory=OmniSVGConfig)
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    svg: SVGConfig = field(default_factory=SVGConfig)
    sft: SFTConfig = field(default_factory=SFTConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    rlrf: RLRFConfig = field(default_factory=RLRFConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)


def apply_a100_profile(cfg: PipelineConfig) -> PipelineConfig:
    """A100/H200 profile: bf16, LoRA r=64, SFT enabled, VLM judge on."""

    cfg.runtime.profile = "a100_diffusvg_full"
    cfg.runtime.dtype = "bfloat16"
    cfg.runtime.num_workers = 4

    # Full precision — no NF4, enable flash-attention-2
    cfg.diffusvg.backend = "omnisvg"
    cfg.diffusvg.base_architecture = "omnisvg_4b_sketchdecoder_bf16"
    cfg.diffusvg.model_name_or_path = os.environ.get(
        "DIFFUSVG_POLICY_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct"
    )
    cfg.diffusvg.load_in_4bit = False
    cfg.diffusvg.gradient_checkpointing = True
    cfg.diffusvg.attn_implementation = "flash_attention_2"
    cfg.diffusvg.max_new_tokens = 2048
    cfg.diffusvg.max_prompt_tokens = 1024
    cfg.diffusvg.temperature = 0.85
    cfg.diffusvg.top_p = 0.92
    cfg.diffusvg.repetition_penalty = 1.15
    cfg.diffusvg.use_think_trace = False

    cfg.omnisvg.enabled = True
    cfg.omnisvg.model_size = "4B"
    cfg.omnisvg.pix_len = 4096
    cfg.omnisvg.text_len = 400
    cfg.omnisvg.top_k = 50

    # LoRA rank 64 — enough capacity for complex scene composition
    cfg.lora.enabled = True
    cfg.lora.r = 64
    cfg.lora.alpha = 128
    cfg.lora.dropout = 0.05

    # 4-stage SFT curriculum — must run before RLRF for complex SVGs
    cfg.sft.enabled = True
    cfg.sft.batch_size = 4
    cfg.sft.gradient_accumulation_steps = 4   # effective batch = 16
    cfg.sft.max_grad_norm = 1.0
    cfg.sft.weight_decay = 0.01
    cfg.sft.warmup_ratio = 0.05
    cfg.sft.optim = "adamw_torch_fused"
    cfg.sft.max_raw_pairs = 4096
    cfg.sft.save_each_stage = True
    cfg.sft.stages = [
        CurriculumStageConfig(1, "Low Complexity",    50,   500,  512, 2.0, 2e-4, 0.00, 1024, 224),
        CurriculumStageConfig(2, "Medium Complexity", 50,  2000,  384, 2.0, 1e-4, 0.30, 1024, 448),
        CurriculumStageConfig(3, "High Resolution",   50,  6000,  256, 2.0, 5e-5, 0.50, 2048, 896),
        CurriculumStageConfig(4, "Aesthetic HQ",     100,  8000,  128, 3.0, 2e-5, 0.70, 2048, 896),
    ]

    # VLM judge on — critical for semantic quality on complex prompts
    cfg.reward.clip_model = "openai/clip-vit-large-patch14"
    cfg.reward.vfm_model = "facebook/dinov2-base"
    cfg.reward.vfm_resolutions = [224, 448, 896]
    cfg.reward.vfm_threshold_reject = 0.35
    cfg.reward.vfm_threshold_medium = 0.65
    cfg.reward.vfm_threshold_high = 0.85
    cfg.reward.score_device = "cuda"
    cfg.reward.flow_default = 1.0
    cfg.reward.use_vlm_judge = True
    cfg.reward.vlm_judge_model = os.environ.get(
        "DIFFUSVG_VLM_JUDGE", "Qwen/Qwen2.5-VL-7B-Instruct"
    )
    cfg.reward.vlm_weight = 0.25
    cfg.reward.structure_weight = 0.10
    cfg.reward.compactness_weight = 0.02
    cfg.reward.target_svg_chars = 6000

    # RLRF: more steps, more rollouts, KL regularisation
    cfg.rlrf.train_steps = 300
    cfg.rlrf.batch_size = 2
    cfg.rlrf.rollouts_per_prompt = 8
    cfg.rlrf.learning_rate = 1e-5
    cfg.rlrf.kl_coef = 0.05
    cfg.rlrf.max_grad_norm = 1.0
    cfg.rlrf.gradient_accumulation_steps = 4
    cfg.rlrf.dynamic_len_max = 2048
    cfg.rlrf.save_every = 50
    cfg.rlrf.log_every = 10
    cfg.rlrf.max_prompts = 256

    cfg.eval.n_candidates = 8
    cfg.eval.max_eval_prompts = 24
    return cfg


def apply_legacy_t4_profile(cfg: PipelineConfig) -> PipelineConfig:
    """Apply the legacy DiffuSVG v8 T4 OmniSVG hardware profile in-place."""

    cfg.runtime.profile = "legacy_t4_diffusvg_rlrf"
    cfg.runtime.dtype = "float16"

    cfg.diffusvg.backend = "omnisvg"
    cfg.diffusvg.base_architecture = "omnisvg_4b_sketchdecoder_nf4"
    cfg.diffusvg.model_name_or_path = "Qwen/Qwen2.5-VL-3B-Instruct"
    cfg.diffusvg.load_in_4bit = True
    cfg.diffusvg.gradient_checkpointing = True
    cfg.diffusvg.attn_implementation = None
    cfg.diffusvg.max_new_tokens = 1200
    cfg.diffusvg.max_prompt_tokens = 512
    cfg.diffusvg.temperature = 0.9
    cfg.diffusvg.top_p = 0.90
    cfg.diffusvg.repetition_penalty = 1.05
    cfg.diffusvg.use_think_trace = False

    cfg.omnisvg.enabled = True
    cfg.omnisvg.model_size = "4B"
    cfg.omnisvg.model_path = ""
    cfg.omnisvg.weight_path = ""
    cfg.omnisvg.use_repo_inference = True
    cfg.omnisvg.pix_len = 2048
    cfg.omnisvg.text_len = 200
    cfg.omnisvg.top_k = 50

    cfg.lora.enabled = True
    cfg.lora.r = 8
    cfg.lora.alpha = 32
    cfg.lora.dropout = 0.10

    cfg.sft.enabled = False
    cfg.sft.max_raw_pairs = 512
    cfg.sft.batch_size = 1
    cfg.sft.gradient_accumulation_steps = 8
    cfg.sft.max_grad_norm = 0.3
    cfg.sft.weight_decay = 0.01
    cfg.sft.warmup_ratio = 0.10
    cfg.sft.optim = "paged_adamw_8bit"
    cfg.sft.stages = [
        CurriculumStageConfig(1, "Low Complexity", 50, 500, 128, 1.0, 2e-4, 0.00, 768, 224),
        CurriculumStageConfig(2, "Medium Complexity", 50, 2000, 128, 1.0, 1e-4, 0.30, 768, 448),
        CurriculumStageConfig(3, "High Resolution", 50, 4000, 96, 1.0, 5e-5, 0.50, 1024, 896),
        CurriculumStageConfig(4, "Aesthetic HQ", 100, 4000, 64, 1.0, 2e-5, 0.70, 1024, 896),
    ]

    cfg.reward.clip_model = "openai/clip-vit-base-patch32"
    cfg.reward.vfm_model = "facebook/dinov2-small"
    cfg.reward.vfm_resolutions = [224, 448, 896]
    cfg.reward.vfm_threshold_reject = 0.40
    cfg.reward.vfm_threshold_medium = 0.70
    cfg.reward.vfm_threshold_high = 0.88
    cfg.reward.score_device = "cuda"
    cfg.reward.use_vlm_judge = False
    cfg.reward.vlm_weight = 0.0
    cfg.reward.target_svg_chars = 4000

    cfg.rlrf.max_prompts = 64
    cfg.rlrf.train_steps = 40
    cfg.rlrf.batch_size = 1
    cfg.rlrf.rollouts_per_prompt = 4
    cfg.rlrf.dynamic_len_max = 1200
    cfg.eval.n_candidates = 4
    cfg.eval.max_eval_prompts = min(cfg.eval.max_eval_prompts, 12)
    return cfg


def _merge_dataclass(obj, values: Dict):
    for key, value in values.items():
        if not hasattr(obj, key):
            raise KeyError(f"Unknown config key: {key}")
        current = getattr(obj, key)
        if is_dataclass(current) and isinstance(value, dict):
            _merge_dataclass(current, value)
        else:
            setattr(obj, key, value)
    return obj


def load_config(path: str = "") -> PipelineConfig:
    cfg = PipelineConfig()
    if path:
        with open(path, "r", encoding="utf-8") as f:
            _merge_dataclass(cfg, json.load(f))
    cfg.sft.stages = [
        stage if isinstance(stage, CurriculumStageConfig) else CurriculumStageConfig(**stage)
        for stage in cfg.sft.stages
    ]
    return cfg


def save_config(cfg: PipelineConfig, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, indent=2)
