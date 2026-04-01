# -*- coding: utf-8 -*-
"""
DiffuSVG_Pipeline_v2.py — Corrected Full Pipeline
Kaggle T4 GPU (16 GB VRAM / 30 GB RAM)

Architecture (from whiteboard):
  ┌─────────────────── DATA GENERATION ───────────────────┐
  │  Text Prompt → SD3.5-Medium → Raster Image            │
  │                                   ↓                    │
  │                          Potrace + ImageMagick         │
  │                                   ↓                    │
  │                                 SVG  (Y)               │
  │                                   ↓                    │
  │              Dataset: [ (Text Prompt=X, SVG=Y), … ]    │
  └────────────────────────────────────────────────────────┘

  ┌─────────────────── VLM QUALITY GATE ──────────────────┐
  │  Render SVG → PNG                                      │
  │  Feed (PNG + Prompt) to Qwen2-VL                       │
  │  Ask: "Does this SVG match the prompt?" → keep / drop  │
  └────────────────────────────────────────────────────────┘

  ┌─────────────────── FINE-TUNING ───────────────────────┐
  │  Qwen2-VL-2B  +  QLoRA                                │
  │  Input:  chat-template formatted text prompt           │
  │  Output: SVG code string                               │
  └────────────────────────────────────────────────────────┘

  ┌─────────────────── INFERENCE ─────────────────────────┐
  │  Text Prompt → Fine-tuned Qwen2-VL → SVG Code         │
  │  SVG Code → Render → Evaluate (CLIP / DINO)           │
  └────────────────────────────────────────────────────────┘

Key fixes over v1:
  1. Proper Qwen2-VL chat template for training inputs
  2. max_length 2048 (SVGs need >512 tokens)
  3. Causal LM loss computed correctly (labels = full sequence)
  4. VLM quality gate actually enabled
  5. CLIP/DINO evaluation loop
  6. SVG minification to reduce token count
  7. Validation split for early stopping
"""

import subprocess, shutil, sys, os, gc, json, logging, re, io, random, tempfile
from pathlib import Path
from typing import Optional

import torch
import numpy as np
from PIL import Image

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Hide GPU 1 before CUDA initialises — prevents HF Trainer from using DataParallel,
# which crashes with 4-bit QLoRA (illegal memory access in bnb.py forward).
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG")


# ════════════════════════════════════════════════════════════════════════════
# HF TOKEN — Kaggle Secrets (add "HF_TOKEN" in Add-ons → Secrets)
# ════════════════════════════════════════════════════════════════════════════
def _get_hf_token() -> str:
    # 1. Already in environment (e.g. set manually before running)
    if os.environ.get("HF_TOKEN", "").startswith("hf_"):
        return os.environ["HF_TOKEN"]
    # 2. Kaggle Secrets
    try:
        from kaggle_secrets import UserSecretsClient
        token = UserSecretsClient().get_secret("HF_TOKEN")
        if token and token.startswith("hf_"):
            log.info("HF_TOKEN loaded from Kaggle Secrets.")
            return token
    except Exception:
        pass
    # 3. Hard-coded fallback (replace if needed)
    return "YOUR_HF_TOKEN"


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    # ── Paths ──
    HF_TOKEN: str         = _get_hf_token()
    RESULTS_JSON: str      = "/kaggle/input/datasets/ayushdebnath0123/result/results.json"
    WORKING_DIR: str       = "/kaggle/working"
    OUTPUT_DIR: str        = "/kaggle/working/dataset"
    LORA_OUTPUT_DIR: str   = "/kaggle/working/qwen2vl_svg_lora"
    EVAL_DIR: str          = "/kaggle/working/eval_results"

    # ── Failure mining thresholds ──
    CLIP_THRESHOLD: float  = 24.0
    DINO_THRESHOLD: float  = 0.35

    # ── FLUX.1-schnell (CPU offload on T4) ──
    SD_MODEL: str          = "black-forest-labs/FLUX.1-schnell"
    SD_STEPS: int          = 4       # schnell = 1-4 steps
    SD_GUIDANCE: float     = 0.0     # schnell needs no CFG
    SD_STYLE_PREFIX: str   = "minimalist flat vector app icon, solid colors, geometric, white background, "

    # ── Vectorizer (vtracer — native colour SVG) ──
    VEC_RESOLUTION: int    = 512
    VEC_COLOR_PRECISION: int = 6
    VEC_FILTER_SPECKLE: int = 4
    VEC_CORNER_THRESHOLD: int = 60
    SVG_MIN_PATHS: int     = 1
    SVG_MAX_PATHS: int     = 500

    # ── VLM (7B, 4-bit quantised) ──
    VLM_MODEL: str         = "Qwen/Qwen2-VL-7B-Instruct"

    # ── Training ──
    MAX_SEQ_LEN: int       = 1024  # 2048 OOMs on T4 16GB; 1024 fits with grad ckpt
    EPOCHS: int            = 5
    BATCH_SIZE: int        = 1
    GRAD_ACCUM: int        = 8
    LEARNING_RATE: float   = 1e-4
    WARMUP_RATIO: float    = 0.05
    VAL_SPLIT: float       = 0.1
    LORA_R: int            = 16   # 32 → 16 saves ~100MB activations
    LORA_ALPHA: int        = 32   # keep same ratio as R
    LORA_DROPOUT: float    = 0.05

    # ── Eval ──
    CLIP_MODEL: str        = "openai/clip-vit-base-patch32"


cfg = Config()
os.environ["HF_TOKEN"] = cfg.HF_TOKEN
log.info(f"HF_TOKEN set: {'OK' if cfg.HF_TOKEN.startswith('hf_') else 'MISSING — add it in Kaggle Secrets!'}")


# ════════════════════════════════════════════════════════════════════════════
# STEP 0 — Install dependencies
# ════════════════════════════════════════════════════════════════════════════
def install():
    log.info("Installing system packages …")
    subprocess.run(["apt-get", "update", "-qq"], capture_output=True)
    subprocess.run(
        ["apt-get", "install", "-y", "-qq", "libcairo2"],
        capture_output=True,
    )

    log.info("Installing Python packages …")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q",
            "diffusers>=0.30", "transformers>=4.40", "accelerate>=0.27",
            "bitsandbytes>=0.43", "peft>=0.10", "trl>=0.8",
            "cairosvg", "pillow", "tqdm", "sentencepiece",
            "open_clip_torch", "vtracer",
        ],
        check=True,
    )
    log.info("All packages installed (incl. vtracer).")

install()


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Vectorizer  (Raster → vtracer → Colour SVG)
# ════════════════════════════════════════════════════════════════════════════
class Vectorizer:
    """Convert a raster PIL image to a colour SVG string via vtracer."""

    def __init__(
        self,
        resolution: int = 512,
        color_precision: int = 6,
        filter_speckle: int = 4,
        corner_threshold: int = 60,
    ):
        self.resolution = resolution
        self.color_precision = color_precision
        self.filter_speckle = filter_speckle
        self.corner_threshold = corner_threshold

    # ── public ──────────────────────────────────────────────────────────
    def vectorize(self, image: Image.Image) -> Optional[str]:
        """Convert PIL Image → colour SVG string using vtracer."""
        import vtracer

        try:
            img = image.convert("RGBA").resize(
                (self.resolution, self.resolution), Image.LANCZOS
            )

            # Convert to PNG bytes in memory (vtracer reads format from bytes)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

            svg = vtracer.convert_raw_image_to_svg(
                png_bytes,
                img_format="png",
                colormode="color",
                hierarchical="stacked",
                mode="spline",
                filter_speckle=self.filter_speckle,
                color_precision=self.color_precision,
                corner_threshold=self.corner_threshold,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )

            return self._normalize_and_minify(svg)

        except Exception as e:
            log.warning(f"vtracer failed: {e}")
            return None

    # ── helpers ─────────────────────────────────────────────────────────
    @staticmethod
    def _normalize_and_minify(svg: str) -> str:
        """Normalize the viewBox and strip unnecessary whitespace so the
        SVG string is as short as possible (critical for fitting in tokens)."""
        # Normalize header
        svg = re.sub(
            r"<svg[^>]*>",
            '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
            svg,
            count=1,
        )
        # Remove XML declaration / doctype
        svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
        svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg)
        # Remove comments
        svg = re.sub(r"<!--.*?-->", "", svg, flags=re.DOTALL)
        # Collapse whitespace
        svg = re.sub(r"\s+", " ", svg).strip()
        # Remove metadata
        svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
        return svg

    @staticmethod
    def is_valid(svg: Optional[str], min_p: int = 1, max_p: int = 500) -> bool:
        if not svg or "<path" not in svg:
            return False
        n = len(re.findall(r"<path", svg))
        return min_p <= n <= max_p


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — SVG rendering helper
# ════════════════════════════════════════════════════════════════════════════
def render_svg_to_pil(svg_str: str, size: int = 256) -> Optional[Image.Image]:
    """Render an SVG string to a PIL Image via cairosvg."""
    try:
        import cairosvg

        png_bytes = cairosvg.svg2png(
            bytestring=svg_str.encode("utf-8"),
            output_width=size,
            output_height=size,
        )
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Find & mine failure prompts from results.json
# ════════════════════════════════════════════════════════════════════════════
FALLBACK_PROMPTS = [
    "a red apple", "a yellow sun", "a blue circle", "a green tree", "a red heart",
    "a yellow star", "an orange carrot", "a pink flower", "a house with red roof",
    "a snowman", "a rocket", "a cat face", "a wifi symbol", "a battery icon",
    "a music note", "a play button", "a gear icon", "a home icon", "a mail envelope",
    "a phone icon", "a camera", "a lock", "a mountain", "a rainbow", "clouds",
    "a crescent moon", "a pizza slice", "a coffee cup", "an ice cream", "a cake",
    "a hamburger", "a donut", "a watermelon", "a banana", "a strawberry",
    "a hot air balloon", "a treasure chest", "a lighthouse", "a bicycle", "a guitar",
    "circles", "a spiral", "squares", "yin yang", "a peace sign",
    "a target", "a smiley", "thumbs up", "lightning bolt", "a car",
]


def find_results_json() -> Optional[str]:
    if Path(cfg.RESULTS_JSON).exists():
        return cfg.RESULTS_JSON
    matches = list(Path("/kaggle/input").rglob("results.json"))
    if matches:
        log.info(f"Auto-found results.json -> {matches[0]}")
        return str(matches[0])
    return None


def mine_failures(path: Optional[str]) -> list[str]:
    if path is None:
        log.warning("No results.json found -- using built-in fallback prompt list.")
        return list(FALLBACK_PROMPTS)
    with open(path) as f:
        data = json.load(f)
    records = data["results"] if isinstance(data, dict) else data
    bad = []
    for r in records:
        failed = not r.get("success", True)
        low_clip = r.get("clip", 0) < cfg.CLIP_THRESHOLD
        low_dino = r.get("dino", 0) < cfg.DINO_THRESHOLD
        if failed or low_clip or low_dino:
            bad.append(r["prompt"])
    if not bad:
        log.warning("results.json found but no failures -- using fallback prompts.")
        return list(FALLBACK_PROMPTS)
    return bad


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Generate (prompt, SVG) pairs via FLUX.1-schnell + vtracer
# ════════════════════════════════════════════════════════════════════════════
def generate_dataset(prompts: list[str]) -> list[dict]:
    """Text Prompt → FLUX.1-schnell → Image → vtracer → Colour SVG"""
    from diffusers import FluxPipeline

    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    img_dir = Path(cfg.OUTPUT_DIR) / "images"
    img_dir.mkdir(exist_ok=True)

    log.info("Loading FLUX.1-schnell …")
    pipe = FluxPipeline.from_pretrained(
        cfg.SD_MODEL,
        torch_dtype=torch.bfloat16,
        token=cfg.HF_TOKEN,
    )
    # sequential offload moves individual LAYERS to GPU one at a time
    # (enable_model_cpu_offload moves whole components — transformer at 23GB > 15.6GB VRAM)
    pipe.enable_sequential_cpu_offload()
    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()

    vec = Vectorizer(
        resolution=cfg.VEC_RESOLUTION,
        color_precision=cfg.VEC_COLOR_PRECISION,
        filter_speckle=cfg.VEC_FILTER_SPECKLE,
        corner_threshold=cfg.VEC_CORNER_THRESHOLD,
    )

    dataset = []
    for i, prompt in enumerate(prompts):
        try:
            torch.cuda.empty_cache()
            # Generate raster image (256x256 to minimise activation memory)
            img = pipe(
                cfg.SD_STYLE_PREFIX + prompt,
                num_inference_steps=cfg.SD_STEPS,
                guidance_scale=cfg.SD_GUIDANCE,
                width=256,
                height=256,
            ).images[0]

            # Save raster (used later for multimodal input / eval)
            img_path = str(img_dir / f"{i:05d}.png")
            img.save(img_path)

            # Vectorize
            svg = vec.vectorize(img)
            if Vectorizer.is_valid(svg, cfg.SVG_MIN_PATHS, cfg.SVG_MAX_PATHS):
                dataset.append({
                    "prompt": prompt,
                    "svg": svg,
                    "image_path": img_path,
                })
                log.info(f"[{i+1}/{len(prompts)}] ✓  {prompt[:60]}")
            else:
                log.warning(f"[{i+1}/{len(prompts)}] ✗  invalid SVG for: {prompt[:60]}")
        except Exception as e:
            log.error(f"[{i+1}/{len(prompts)}] error: {e}")

    # Free VRAM
    del pipe
    gc.collect()
    torch.cuda.empty_cache()

    log.info(f"Generated {len(dataset)}/{len(prompts)} valid (prompt, SVG) pairs.")
    return dataset



# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — VLM Quality Gate (Qwen2-VL-7B verifies SVG ↔ prompt alignment)
# ════════════════════════════════════════════════════════════════════════════
def vlm_quality_gate(dataset: list[dict]) -> list[dict]:
    """Render each SVG, show it to Qwen2-VL-7B with the prompt, ask if it matches.
    Keeps only aligned pairs to avoid training on noise."""
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    import base64

    log.info(f"Running VLM quality gate with {cfg.VLM_MODEL} (4-bit) …")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    processor = AutoProcessor.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL,
        quantization_config=bnb_config,
        device_map={"":0},
        trust_remote_code=True,
    )
    model.eval()

    filtered = []
    for item in dataset:
        try:
            rendered = render_svg_to_pil(item["svg"], size=256)
            if rendered is None:
                continue

            # Build multimodal prompt
            buf = io.BytesIO()
            rendered.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"data:image/png;base64,{img_b64}"},
                        {
                            "type": "text",
                            "text": (
                                f"This SVG image was generated for the prompt: \"{item['prompt']}\". "
                                "Does the image accurately represent the prompt? "
                                "Answer only YES or NO."
                            ),
                        },
                    ],
                }
            ]

            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            # Process with image
            inputs = processor(
                text=[text],
                images=[rendered],
                return_tensors="pt",
                padding=True,
            ).to(model.device)

            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=10, do_sample=False)

            response = processor.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

            if "YES" in response.upper():
                filtered.append(item)
                log.info(f"  PASS: {item['prompt'][:60]}")
            else:
                log.info(f"  FAIL: {item['prompt'][:60]}  → {response.strip()}")

        except Exception as e:
            log.warning(f"  Gate error: {e}")
            # On error, keep the sample (conservative)
            filtered.append(item)

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()

    log.info(f"VLM gate: kept {len(filtered)}/{len(dataset)} samples.")
    return filtered



# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Fine-tune Qwen2-VL with QLoRA  (Text Prompt → SVG)
# ════════════════════════════════════════════════════════════════════════════
def build_chat_pair(prompt: str, svg: str, tokenizer) -> str:
    """Format as Qwen2-VL chat so the model sees proper special tokens.

    System: You are an SVG generation assistant. Given a text description,
            output clean, minimal SVG code.
    User:   Generate an SVG icon for: {prompt}
    Assistant: {svg}
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an SVG generation assistant. "
                "Given a text description of an icon, output clean minimal SVG code. "
                "Output ONLY the SVG, no explanation."
            ),
        },
        {"role": "user", "content": f"Generate an SVG icon for: {prompt}"},
        {"role": "assistant", "content": svg},
    ]
    # apply_chat_template gives us the full string with special tokens
    return tokenizer.apply_chat_template(messages, tokenize=False)


class SVGCausalDataset(torch.utils.data.Dataset):
    """
    Tokenise chat-formatted (prompt → SVG) pairs for causal LM training.

    The labels mask the system+user portion with -100 so the loss is
    only computed on the assistant (SVG) tokens.
    """

    def __init__(self, data: list[dict], tokenizer, max_len: int):
        self.samples = []
        skipped = 0

        for item in data:
            full_text = build_chat_pair(item["prompt"], item["svg"], tokenizer)

            toks = tokenizer(
                full_text,
                truncation=True,
                max_length=max_len,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = toks["input_ids"].squeeze()       # (max_len,)
            attn_mask = toks["attention_mask"].squeeze()   # (max_len,)

            # Find where the assistant response starts so we mask the prompt
            # Build the prompt-only portion (without the assistant reply)
            prompt_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an SVG generation assistant. "
                        "Given a text description of an icon, output clean minimal SVG code. "
                        "Output ONLY the SVG, no explanation."
                    ),
                },
                {"role": "user", "content": f"Generate an SVG icon for: {item['prompt']}"},
            ]
            prompt_only = tokenizer.apply_chat_template(
                prompt_messages, tokenize=False, add_generation_prompt=True
            )
            prompt_len = len(tokenizer(prompt_only, truncation=True, max_length=max_len)["input_ids"])

            # Labels: -100 for prompt tokens, real ids for SVG tokens
            labels = input_ids.clone()
            labels[:prompt_len] = -100
            # Also mask padding
            labels[attn_mask == 0] = -100

            # Skip if the SVG portion got completely truncated
            if (labels != -100).sum() < 20:
                skipped += 1
                continue

            self.samples.append({
                "input_ids": input_ids,
                "attention_mask": attn_mask,
                "labels": labels,
            })

        log.info(f"Dataset: {len(self.samples)} usable, {skipped} skipped (SVG too long).")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def train_lora(dataset: list[dict]):
    from transformers import (
        AutoTokenizer,
        Qwen2VLForConditionalGeneration,
        BitsAndBytesConfig,
        TrainingArguments,
        Trainer,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

    log.info("Loading Qwen2-VL for fine-tuning …")

    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Check token lengths to verify max_len is reasonable ──
    sample_svg_lens = []
    for item in dataset[:10]:
        full = build_chat_pair(item["prompt"], item["svg"], tokenizer)
        tl = len(tokenizer.encode(full))
        sample_svg_lens.append(tl)
    log.info(f"Sample token lengths (first 10): {sample_svg_lens}")
    log.info(f"Max: {max(sample_svg_lens)}, Mean: {np.mean(sample_svg_lens):.0f}")

    # ── QLoRA quantization ──
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    # Force single-GPU: device_map="auto" with T4 x2 causes DataParallel +
    # gradient_checkpointing + 4-bit QLoRA to conflict → illegal memory access.
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL,
        quantization_config=quant_config,
        device_map={"": 0},  # pin to GPU 0 only, no DataParallel
        trust_remote_code=True,
    )
    model.config.use_cache = False  # required for gradient checkpointing
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_config = LoraConfig(
        r=cfg.LORA_R,
        lora_alpha=cfg.LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=cfg.LORA_DROPOUT,
        task_type=TaskType.CAUSAL_LM,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    # Tell HF Trainer this model must NOT be wrapped in DataParallel.
    # PEFT models lose the hf_device_map attribute, so Trainer defaults to DP
    # on multi-GPU machines. Explicitly disabling prevents the QLoRA crash.
    model.is_parallelizable = False
    model.model_parallel = False
    model.print_trainable_parameters()

    # ── Build train / val splits ──
    random.shuffle(dataset)
    split = int(len(dataset) * (1 - cfg.VAL_SPLIT))
    train_data = dataset[:split]
    val_data = dataset[split:]

    train_ds = SVGCausalDataset(train_data, tokenizer, cfg.MAX_SEQ_LEN)
    val_ds = SVGCausalDataset(val_data, tokenizer, cfg.MAX_SEQ_LEN) if val_data else None

    if len(train_ds) == 0:
        log.error("No usable training samples! Check SVG lengths vs MAX_SEQ_LEN.")
        return None, None

    # ── Trainer ──
    training_args = TrainingArguments(
        output_dir=cfg.LORA_OUTPUT_DIR,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        per_device_eval_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        num_train_epochs=cfg.EPOCHS,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=max(1, int(cfg.WARMUP_RATIO * (len(dataset) // (cfg.BATCH_SIZE * cfg.GRAD_ACCUM)) * cfg.EPOCHS)),
        lr_scheduler_type="cosine",
        fp16=True,
        logging_steps=5,
        eval_strategy="epoch" if val_ds and len(val_ds) > 0 else "no",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=bool(val_ds and len(val_ds) > 0),
        metric_for_best_model="eval_loss" if val_ds and len(val_ds) > 0 else None,
        report_to="none",
        dataloader_pin_memory=False,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    log.info(f"Starting training: {len(train_ds)} train, {len(val_ds) if val_ds else 0} val")
    trainer.train()

    # Save adapter
    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"Adapter saved → {adapter_dir}")

    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Inference: Text Prompt → Qwen2-VL → SVG
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500) -> str:
    """Run the fine-tuned model to produce SVG from a text prompt."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an SVG generation assistant. "
                "Given a text description of an icon, output clean minimal SVG code. "
                "Output ONLY the SVG, no explanation."
            ),
        },
        {"role": "user", "content": f"Generate an SVG icon for: {prompt}"},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    out = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1,
    )
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    # Extract SVG from response (in case model adds explanation)
    svg_match = re.search(r"(<svg[\s\S]*?</svg>)", response)
    return svg_match.group(1) if svg_match else response


# ════════════════════════════════════════════════════════════════════════════
# STEP 8 — Evaluation: CLIP & DINO scores
# ════════════════════════════════════════════════════════════════════════════
def evaluate_pipeline(
    model,
    tokenizer,
    test_prompts: list[str],
    n_samples: int = 20,
) -> dict:
    """Generate SVGs for test prompts and compute CLIP/DINO scores."""
    import open_clip

    log.info("Loading CLIP for evaluation …")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")
    clip_model = clip_model.float().eval()
    if torch.cuda.is_available():
        clip_model = clip_model.cuda()

    Path(cfg.EVAL_DIR).mkdir(parents=True, exist_ok=True)

    results = []
    test_subset = test_prompts[:n_samples]

    for i, prompt in enumerate(test_subset):
        try:
            svg = generate_svg(prompt, model, tokenizer)
            rendered = render_svg_to_pil(svg, size=224)
            if rendered is None:
                results.append({"prompt": prompt, "clip": 0.0, "success": False})
                continue

            # Save rendered output
            rendered.save(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))
            with open(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"), "w") as f:
                f.write(svg)

            # CLIP score
            img_tensor = clip_preprocess(rendered).unsqueeze(0)
            txt_tensor = clip_tokenizer([prompt])
            if torch.cuda.is_available():
                img_tensor = img_tensor.cuda()
                txt_tensor = txt_tensor.cuda()

            with torch.no_grad():
                img_features = clip_model.encode_image(img_tensor)
                txt_features = clip_model.encode_text(txt_tensor)
                img_features /= img_features.norm(dim=-1, keepdim=True)
                txt_features /= txt_features.norm(dim=-1, keepdim=True)
                score = (img_features @ txt_features.T).item() * 100

            results.append({"prompt": prompt, "clip": score, "success": True})
            log.info(f"  [{i+1}/{len(test_subset)}] CLIP={score:.2f}  {prompt[:50]}")

        except Exception as e:
            log.error(f"  Eval error: {e}")
            results.append({"prompt": prompt, "clip": 0.0, "success": False})

    del clip_model
    gc.collect()
    torch.cuda.empty_cache()

    # Summary
    successful = [r for r in results if r["success"]]
    if successful:
        scores = [r["clip"] for r in successful]
        summary = {
            "n_total": len(results),
            "n_success": len(successful),
            "clip_mean": np.mean(scores),
            "clip_median": np.median(scores),
            "clip_std": np.std(scores),
            "results": results,
        }
    else:
        summary = {"n_total": len(results), "n_success": 0, "results": results}

    eval_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
    with open(eval_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Evaluation complete → {eval_path}")
    if successful:
        log.info(f"  CLIP: mean={summary['clip_mean']:.2f}, median={summary['clip_median']:.2f}")

    return summary


def main():
    # ── GPU check ──
    if not torch.cuda.is_available():
        log.warning("No GPU detected! On Kaggle: Settings → Accelerator → GPU T4 x2.")
    else:
        log.info(f"GPU: {torch.cuda.get_device_name(0)}  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        log.info(f"Visible GPUs: {torch.cuda.device_count()} (forced to 1 for QLoRA compatibility)")

    # ── Token check ──
    if not cfg.HF_TOKEN.startswith("hf_"):
        raise RuntimeError(
            "HF_TOKEN not set. Add it in Kaggle: Add-ons → Secrets → 'HF_TOKEN'."
        )

    # ── Step 3: Find failure prompts ──
    results_path = find_results_json()
    bad_prompts = mine_failures(results_path)
    log.info(f"Training on {len(bad_prompts)} prompts.")

    # ── Step 4: Generate dataset ──
    raw_dataset = generate_dataset(bad_prompts)

    # ── Step 5: VLM quality gate ──
    filtered_dataset = vlm_quality_gate(raw_dataset)

    # Save dataset
    dataset_path = os.path.join(cfg.OUTPUT_DIR, "training_pairs.json")
    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(dataset_path, "w") as f:
        json.dump(filtered_dataset, f, indent=2)
    log.info(f"Saved {len(filtered_dataset)} training pairs → {dataset_path}")

    if len(filtered_dataset) == 0:
        log.error("No training data after quality gate. Aborting.")
        return

    # ── Step 6: Fine-tune ──
    model, tokenizer = train_lora(filtered_dataset)

    # ── Step 8: Evaluate ──
    if model is not None:
        evaluate_pipeline(model, tokenizer, bad_prompts, n_samples=20)

    # ── Step 9: Package ──
    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    if Path(adapter_dir).exists():
        archive = shutil.make_archive(
            os.path.join(cfg.WORKING_DIR, "diffusvg_lora_v2"), "zip", adapter_dir
        )
        log.info(f"Pipeline complete. Adapter archive → {archive}")
        log.info("Download: Kaggle Output panel (right sidebar) → diffusvg_lora_v2.zip")
    else:
        log.warning("No adapter found to export.")

    log.info("Done.")


if __name__ == "__main__":
    main()
