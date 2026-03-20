# -*- coding: utf-8 -*-
"""
DiffuSVG_Pipeline_v3.py
Kaggle T4 x2 GPU  /  Google Colab T4

Pipeline:
  Prompt → FLUX.1-schnell → Raster PNG
         → vtracer → Colour SVG          (Stage 1)
         → Gemini-1.5-flash gate          (Stage 2)
         → Qwen2-VL-7B QLoRA fine-tune   (Stage 3)
         → Inference + correction         (Stage 4)
         → CLIP evaluation                (Stage 5)

Changes over v2:
  - FLUX.1-schnell replaces SD3.5-Medium  (4 steps, no gated token needed)
  - vtracer replaces Potrace              (clean Bezier curves, colour-native)
  - Gemini-1.5-flash replaces local VLM gate  (frees VRAM for 7B fine-tune)
  - Qwen2-VL-7B replaces 2B everywhere
  - Per-stage output dirs saved throughout
  - No-truncation policy in SVGCausalDataset  (prevents mode collapse)
  - MAX_SEQ_LEN raised to 2048
  - Comprehensive zip of all stages at end
"""

import subprocess, shutil, sys, os, gc, json, logging, re, io, random, tempfile, zipfile
from pathlib import Path
from typing import Optional

import torch
import numpy as np
from PIL import Image

os.environ["PYTORCH_ALLOC_CONF"]   = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["CUDA_VISIBLE_DEVICES"]  = "0"   # single GPU — prevents DataParallel + QLoRA crash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG")


# ════════════════════════════════════════════════════════════════════════════
# PLATFORM DETECTION
# ════════════════════════════════════════════════════════════════════════════
IN_KAGGLE = os.path.exists("/kaggle/working")
IN_COLAB  = "google.colab" in sys.modules or os.path.exists("/content")
if IN_COLAB:
    IN_KAGGLE = False


# ════════════════════════════════════════════════════════════════════════════
# SECRETS
# ════════════════════════════════════════════════════════════════════════════
def _get_secret(name: str) -> str:
    """Load a secret from env → Kaggle Secrets → Colab Secrets."""
    val = os.environ.get(name, "")
    if val and "YOUR_" not in val:
        return val
    if IN_KAGGLE:
        try:
            from kaggle_secrets import UserSecretsClient
            val = UserSecretsClient().get_secret(name)
            if val:
                log.info(f"{name} loaded from Kaggle Secrets.")
                return val
        except Exception:
            pass
    if IN_COLAB:
        try:
            from google.colab import userdata
            val = userdata.get(name)
            if val:
                log.info(f"{name} loaded from Colab Secrets.")
                return val
        except Exception:
            pass
    return f"MISSING_{name}"


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    # ── Secrets ──
    HF_TOKEN:      str = _get_secret("HF_TOKEN")       # only needed if using gated models
    GEMINI_API_KEY: str = _get_secret("GEMINI_API_KEY") # Gemini quality gate

    # ── Paths ──
    if IN_KAGGLE:
        WORKING_DIR:  str = "/kaggle/working"
        INPUT_DIR:    str = "/kaggle/input"
        RESULTS_JSON: str = "/kaggle/input/datasets/ayushdebnath0123/result/results.json"
    elif IN_COLAB:
        WORKING_DIR:  str = "/content/diffusvg_outputs"
        INPUT_DIR:    str = "/content/input"
        RESULTS_JSON: str = "/content/input/results.json"
    else:
        WORKING_DIR:  str = str(Path.cwd() / "outputs")
        INPUT_DIR:    str = str(Path.cwd() / "input")
        RESULTS_JSON: str = str(Path.cwd() / "results.json")

    OUTPUT_DIR:     str = os.path.join(WORKING_DIR, "dataset")
    LORA_OUTPUT_DIR: str = os.path.join(WORKING_DIR, "qwen2vl_svg_lora")
    EVAL_DIR:       str = os.path.join(WORKING_DIR, "eval_results")

    # ── Failure mining ──
    CLIP_THRESHOLD: float = 24.0
    DINO_THRESHOLD: float = 0.35

    # ── FLUX.1-schnell ──
    SD_MODEL:        str   = "black-forest-labs/FLUX.1-schnell"
    SD_STEPS:        int   = 4      # schnell = 1-4 steps, no CFG
    SD_GUIDANCE:     float = 0.0
    SD_STYLE_PREFIX: str   = (
        "minimalist flat vector app icon, solid colors, "
        "geometric shapes, white background, clean lines, "
    )

    # ── vtracer ──
    VEC_RESOLUTION:      int = 512
    VEC_COLOR_PRECISION: int = 6
    VEC_FILTER_SPECKLE:  int = 4
    VEC_CORNER_THRESHOLD: int = 60
    SVG_MIN_PATHS:       int = 1
    SVG_MAX_PATHS:       int = 500

    # ── Gemini gate ──
    GEMINI_GATE_MODEL: str = "gemini-1.5-flash"

    # ── VLM (fine-tune) ──
    VLM_MODEL: str = "Qwen/Qwen2-VL-7B-Instruct"

    # ── Training ──
    MAX_SEQ_LEN:    int   = 2048   # vtracer SVGs tokenise to 800-1500
    EPOCHS:         int   = 5
    BATCH_SIZE:     int   = 1
    GRAD_ACCUM:     int   = 8
    LEARNING_RATE:  float = 1e-4
    WARMUP_RATIO:   float = 0.05
    VAL_SPLIT:      float = 0.1
    LORA_R:         int   = 16
    LORA_ALPHA:     int   = 32
    LORA_DROPOUT:   float = 0.05

    # ── Eval ──
    CLIP_MODEL: str = "ViT-B-32"


cfg = Config()
os.environ["HF_TOKEN"] = cfg.HF_TOKEN
log.info(f"HF_TOKEN:       {'OK' if 'hf_' in cfg.HF_TOKEN else 'not set (OK for FLUX)'}")
log.info(f"GEMINI_API_KEY: {'OK' if 'MISSING' not in cfg.GEMINI_API_KEY else 'MISSING — add in Secrets'}")


# ════════════════════════════════════════════════════════════════════════════
# STEP 0 — Install
# ════════════════════════════════════════════════════════════════════════════
def install():
    log.info("Installing system packages …")
    subprocess.run(["apt-get", "update",  "-qq"], capture_output=True)
    subprocess.run(["apt-get", "install", "-y", "-qq", "libcairo2"], capture_output=True)

    log.info("Installing Python packages …")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "diffusers>=0.30", "transformers>=4.40", "accelerate>=0.27",
        "bitsandbytes>=0.43", "peft>=0.10", "trl>=0.8",
        "cairosvg", "pillow", "tqdm", "sentencepiece",
        "open_clip_torch", "vtracer",
        "google-generativeai",
    ], check=True)
    log.info("All packages installed.")

install()


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════
def _slug(text: str, max_len: int = 40) -> str:
    return re.sub(r"[^\w]+", "_", text).strip("_")[:max_len]


def render_svg_to_pil(svg_str: str, size: int = 256) -> Optional[Image.Image]:
    try:
        import cairosvg
        png = cairosvg.svg2png(
            bytestring=svg_str.encode("utf-8"),
            output_width=size, output_height=size,
        )
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Vectorizer  (Raster → vtracer → Colour SVG)
# ════════════════════════════════════════════════════════════════════════════
class Vectorizer:
    def __init__(self, resolution=512, color_precision=6,
                 filter_speckle=4, corner_threshold=60):
        self.resolution       = resolution
        self.color_precision  = color_precision
        self.filter_speckle   = filter_speckle
        self.corner_threshold = corner_threshold

    def vectorize(self, image: Image.Image) -> Optional[str]:
        import vtracer
        try:
            img = image.convert("RGBA").resize(
                (self.resolution, self.resolution), Image.LANCZOS
            )
            buf = io.BytesIO()
            img.save(buf, format="PNG")

            svg = vtracer.convert_raw_image_to_svg(
                buf.getvalue(),
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

    @staticmethod
    def _normalize_and_minify(svg: str) -> str:
        svg = re.sub(r"<svg[^>]*>",
                     '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
                     svg, count=1)
        svg = re.sub(r"<\?xml[^>]*\?>",  "", svg)
        svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg)
        svg = re.sub(r"<!--.*?-->",       "", svg, flags=re.DOTALL)
        svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
        # Round coordinates to 2 d.p. — saves ~30% path data length
        svg = re.sub(r'\d+\.\d{3,}', lambda m: f"{float(m.group()):.2f}", svg)
        svg = re.sub(r"\s+", " ", svg).strip()
        return svg

    @staticmethod
    def is_valid(svg: Optional[str], min_p=1, max_p=500) -> bool:
        if not svg or "<path" not in svg:
            return False
        n = len(re.findall(r"<path", svg))
        return min_p <= n <= max_p


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Failure prompt mining
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
    matches = list(Path(cfg.INPUT_DIR).rglob("results.json")) if Path(cfg.INPUT_DIR).exists() else []
    if matches:
        log.info(f"Auto-found results.json → {matches[0]}")
        return str(matches[0])
    return None


def mine_failures(path: Optional[str]) -> list[str]:
    if path is None:
        log.warning("No results.json — using fallback prompts.")
        return list(FALLBACK_PROMPTS)
    with open(path) as f:
        data = json.load(f)
    records = data["results"] if isinstance(data, dict) else data
    bad = [r["prompt"] for r in records
           if not r.get("success", True)
           or r.get("clip", 0) < cfg.CLIP_THRESHOLD
           or r.get("dino", 0) < cfg.DINO_THRESHOLD]
    if not bad:
        log.warning("No failures in results.json — using fallback prompts.")
        return list(FALLBACK_PROMPTS)
    return bad


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Generate (prompt, SVG) pairs via FLUX.1-schnell + vtracer
# ════════════════════════════════════════════════════════════════════════════
def generate_dataset(prompts: list[str]) -> list[dict]:
    from diffusers import FluxPipeline

    # ── Output dirs ──
    s1_dir  = Path(cfg.WORKING_DIR) / "stage1_generated"
    s1_svgs = s1_dir / "svgs";  s1_svgs.mkdir(parents=True, exist_ok=True)
    s1_pngs = s1_dir / "pngs";  s1_pngs.mkdir(parents=True, exist_ok=True)
    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    img_dir = Path(cfg.OUTPUT_DIR) / "images";  img_dir.mkdir(exist_ok=True)

    log.info("Loading FLUX.1-schnell …")
    flux_token = cfg.HF_TOKEN if "MISSING" not in cfg.HF_TOKEN else None
    pipe = FluxPipeline.from_pretrained(
        cfg.SD_MODEL, torch_dtype=torch.bfloat16,
        token=flux_token,
    )
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
    saved_prompts = []
    svg_char_limit = int((cfg.MAX_SEQ_LEN - 150) * 2.5)

    for i, prompt in enumerate(prompts):
        try:
            torch.cuda.empty_cache()
            img = pipe(
                cfg.SD_STYLE_PREFIX + prompt,
                num_inference_steps=cfg.SD_STEPS,
                guidance_scale=cfg.SD_GUIDANCE,
                width=512, height=512,
            ).images[0]

            img_path = str(img_dir / f"{i:05d}.png")
            img.save(img_path)

            svg = vec.vectorize(img)

            if svg and len(svg) > svg_char_limit:
                log.warning(f"[{i+1}/{len(prompts)}] ✗  SVG too long ({len(svg)} chars): {prompt[:50]}")
                svg = None

            if Vectorizer.is_valid(svg, cfg.SVG_MIN_PATHS, cfg.SVG_MAX_PATHS):
                dataset.append({"prompt": prompt, "svg": svg, "image_path": img_path})
                stem = f"{i:03d}_{_slug(prompt)}"
                (s1_svgs / f"{stem}.svg").write_text(svg, encoding="utf-8")
                img.save(str(s1_pngs / f"{stem}.png"))
                saved_prompts.append(prompt)
                log.info(f"[{i+1}/{len(prompts)}] ✓  {prompt[:60]}  ({len(svg)} chars)")
            else:
                log.warning(f"[{i+1}/{len(prompts)}] ✗  invalid SVG: {prompt[:60]}")
        except Exception as e:
            log.error(f"[{i+1}/{len(prompts)}] error: {e}")

    (s1_dir / "prompts.txt").write_text("\n".join(saved_prompts), encoding="utf-8")
    log.info(f"Stage 1 → {s1_dir}  ({len(dataset)} pairs)")

    del pipe; gc.collect(); torch.cuda.empty_cache()
    return dataset


# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — Gemini Quality Gate
# ════════════════════════════════════════════════════════════════════════════
def vlm_quality_gate(dataset: list[dict]) -> list[dict]:
    """Use Gemini-1.5-flash to verify SVG ↔ prompt alignment.
    Free tier: 15 req/min, 1500 req/day — more than enough."""
    import google.generativeai as genai
    import time

    if "MISSING" in cfg.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY missing — skipping gate, keeping all samples.")
        return dataset

    genai.configure(api_key=cfg.GEMINI_API_KEY)
    gate_model = genai.GenerativeModel(cfg.GEMINI_GATE_MODEL)

    # ── Output dirs ──
    s2_dir      = Path(cfg.WORKING_DIR) / "stage2_filtered"
    s2_svgs     = s2_dir / "svgs";      s2_svgs.mkdir(parents=True, exist_ok=True)
    s2_pngs     = s2_dir / "pngs";      s2_pngs.mkdir(parents=True, exist_ok=True)
    s2_rej_dir  = Path(cfg.WORKING_DIR) / "stage2_rejected"
    s2_rej_svgs = s2_rej_dir / "svgs";  s2_rej_svgs.mkdir(parents=True, exist_ok=True)
    s2_rej_pngs = s2_rej_dir / "pngs";  s2_rej_pngs.mkdir(parents=True, exist_ok=True)

    filtered, saved_prompts = [], []
    pass_idx = rej_idx = 0

    for item in dataset:
        try:
            rendered = render_svg_to_pil(item["svg"], size=256)
            if rendered is None:
                continue

            response = gate_model.generate_content([
                rendered,
                (f"This SVG image was generated for the prompt: \"{item['prompt']}\". "
                 "Does the image accurately represent the prompt? Answer only YES or NO."),
            ])
            answer = response.text.strip().upper()

            if "YES" in answer:
                filtered.append(item)
                stem = f"{pass_idx:03d}_{_slug(item['prompt'])}"
                (s2_svgs / f"{stem}.svg").write_text(item["svg"], encoding="utf-8")
                rendered.save(str(s2_pngs / f"{stem}.png"))
                saved_prompts.append(item["prompt"])
                pass_idx += 1
                log.info(f"  PASS: {item['prompt'][:60]}")
            else:
                rstem = f"{rej_idx:03d}_{_slug(item['prompt'])}"
                (s2_rej_svgs / f"{rstem}.svg").write_text(item["svg"], encoding="utf-8")
                rendered.save(str(s2_rej_pngs / f"{rstem}.png"))
                rej_idx += 1
                log.info(f"  FAIL: {item['prompt'][:60]}  → {answer}")

            time.sleep(1.5)   # stay under 15 req/min free tier limit

        except Exception as e:
            log.warning(f"  Gate error ({e}) — keeping sample conservatively.")
            filtered.append(item)
            stem = f"{pass_idx:03d}_{_slug(item['prompt'])}"
            (s2_svgs / f"{stem}.svg").write_text(item["svg"], encoding="utf-8")
            saved_prompts.append(item["prompt"])
            pass_idx += 1

    (s2_dir / "prompts.txt").write_text("\n".join(saved_prompts), encoding="utf-8")
    log.info(f"Stage 2 → {pass_idx} PASS, {rej_idx} FAIL")
    return filtered


# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Fine-tune Qwen2-VL-7B with QLoRA
# ════════════════════════════════════════════════════════════════════════════
def build_chat_pair(prompt: str, svg: str, tokenizer) -> str:
    messages = [
        {"role": "system",    "content": ("You are an SVG generation assistant. "
                                          "Given a text description of an icon, output clean minimal SVG code. "
                                          "Output ONLY the SVG, no explanation.")},
        {"role": "user",      "content": f"Generate an SVG icon for: {prompt}"},
        {"role": "assistant", "content": svg},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


class SVGCausalDataset(torch.utils.data.Dataset):
    """No-truncation policy: skip any sample whose full token count > max_len.
    Training on truncated SVGs causes mode collapse."""

    def __init__(self, data: list[dict], tokenizer, max_len: int):
        self.samples = []
        skipped = 0

        for item in data:
            full_text = build_chat_pair(item["prompt"], item["svg"], tokenizer)

            # Hard skip — never truncate
            full_len = len(tokenizer.encode(full_text))
            if full_len > max_len:
                log.warning(f"  skip (too long {full_len} > {max_len}): {item['prompt'][:40]}")
                skipped += 1
                continue

            toks = tokenizer(
                full_text, truncation=False, max_length=max_len,
                padding="max_length", return_tensors="pt",
            )
            input_ids = toks["input_ids"].squeeze()
            attn_mask = toks["attention_mask"].squeeze()

            # Mask prompt tokens with -100
            prompt_messages = [
                {"role": "system",    "content": ("You are an SVG generation assistant. "
                                                  "Given a text description of an icon, output clean minimal SVG code. "
                                                  "Output ONLY the SVG, no explanation.")},
                {"role": "user",      "content": f"Generate an SVG icon for: {item['prompt']}"},
            ]
            prompt_only = tokenizer.apply_chat_template(
                prompt_messages, tokenize=False, add_generation_prompt=True
            )
            prompt_len = len(tokenizer(prompt_only, truncation=True, max_length=max_len)["input_ids"])

            labels = input_ids.clone()
            labels[:prompt_len]    = -100
            labels[attn_mask == 0] = -100

            if (labels != -100).sum() < 20:
                skipped += 1
                continue

            self.samples.append({"input_ids": input_ids, "attention_mask": attn_mask, "labels": labels})

        log.info(f"Dataset: {len(self.samples)} usable, {skipped} skipped (too long or empty SVG).")

    def __len__(self):         return len(self.samples)
    def __getitem__(self, i):  return self.samples[i]


def train_lora(dataset: list[dict]):
    from transformers import (AutoTokenizer, Qwen2VLForConditionalGeneration,
                               BitsAndBytesConfig, TrainingArguments, Trainer)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

    if not torch.cuda.is_available():
        log.error("Fine-tuning requires GPU. Aborting.")
        return None, None

    log.info(f"Loading {cfg.VLM_MODEL} for fine-tuning …")
    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Token length check
    lens = [len(tokenizer.encode(build_chat_pair(d["prompt"], d["svg"], tokenizer)))
            for d in dataset[:min(10, len(dataset))]]
    log.info(f"Token lengths (first 10): min={min(lens)} max={max(lens)} mean={np.mean(lens):.0f}")

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
    )
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        cfg.VLM_MODEL, quantization_config=quant_config,
        device_map={"": 0}, trust_remote_code=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_cfg = LoraConfig(
        r=cfg.LORA_R, lora_alpha=cfg.LORA_ALPHA,
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
        lora_dropout=cfg.LORA_DROPOUT, task_type=TaskType.CAUSAL_LM, bias="none",
    )
    model = get_peft_model(model, lora_cfg)
    model.is_parallelizable = False
    model.model_parallel    = False
    model.print_trainable_parameters()

    random.shuffle(dataset)
    split     = int(len(dataset) * (1 - cfg.VAL_SPLIT))
    train_ds  = SVGCausalDataset(dataset[:split],  tokenizer, cfg.MAX_SEQ_LEN)
    val_ds    = SVGCausalDataset(dataset[split:],  tokenizer, cfg.MAX_SEQ_LEN) if dataset[split:] else None

    if len(train_ds) == 0:
        log.error("No usable training samples! All SVGs exceed MAX_SEQ_LEN.")
        return None, None

    warmup = max(1, int(cfg.WARMUP_RATIO
                        * (len(dataset) // (cfg.BATCH_SIZE * cfg.GRAD_ACCUM))
                        * cfg.EPOCHS))
    args = TrainingArguments(
        output_dir=cfg.LORA_OUTPUT_DIR,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        per_device_eval_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        num_train_epochs=cfg.EPOCHS,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=warmup,
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

    trainer = Trainer(model=model, args=args,
                      train_dataset=train_ds, eval_dataset=val_ds)
    log.info(f"Training: {len(train_ds)} train, {len(val_ds) if val_ds else 0} val")
    trainer.train()

    adapter_dir = os.path.join(cfg.LORA_OUTPUT_DIR, "final_adapter")
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    log.info(f"Adapter saved → {adapter_dir}")

    # Stage 3 outputs
    s3_dir = Path(cfg.WORKING_DIR) / "stage3_training"
    s3_dir.mkdir(parents=True, exist_ok=True)
    with open(s3_dir / "training_pairs.json", "w") as f:
        json.dump(dataset, f, indent=2)
    (s3_dir / "prompts.txt").write_text(
        "\n".join(d["prompt"] for d in dataset), encoding="utf-8")
    log.info(f"Stage 3 → {s3_dir}")

    return model, tokenizer


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Inference
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500) -> str:
    messages = [
        {"role": "system",  "content": ("You are an SVG generation assistant. "
                                        "Given a text description of an icon, output clean minimal SVG code. "
                                        "Output ONLY the SVG, no explanation.")},
        {"role": "user",    "content": f"Generate an SVG icon for: {prompt}"},
    ]
    text   = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out    = model.generate(
        **inputs, max_new_tokens=max_new_tokens,
        do_sample=True, temperature=0.7, top_p=0.9, repetition_penalty=1.1,
    )
    resp = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    m = re.search(r"(<svg[\s\S]*?</svg>)", resp)
    return m.group(1) if m else resp


# ════════════════════════════════════════════════════════════════════════════
# STEP 8 — Evaluate
# ════════════════════════════════════════════════════════════════════════════
def evaluate_pipeline(model, tokenizer, test_prompts: list[str], n_samples: int = 20) -> dict:
    import open_clip

    log.info("Loading CLIP …")
    clip_model, _, clip_prep = open_clip.create_model_and_transforms(
        cfg.CLIP_MODEL, pretrained="laion2b_s34b_b79k")
    clip_tok = open_clip.get_tokenizer(cfg.CLIP_MODEL)
    clip_model = clip_model.float().eval()
    if torch.cuda.is_available():
        clip_model = clip_model.cuda()

    Path(cfg.EVAL_DIR).mkdir(parents=True, exist_ok=True)
    s4_dir  = Path(cfg.WORKING_DIR) / "stage4_inference"
    s4_svgs = s4_dir / "svgs";  s4_svgs.mkdir(parents=True, exist_ok=True)
    s4_pngs = s4_dir / "pngs";  s4_pngs.mkdir(parents=True, exist_ok=True)

    results, s4_prompts = [], []

    for i, prompt in enumerate(test_prompts[:n_samples]):
        try:
            svg  = generate_svg(prompt, model, tokenizer)
            stem = f"{i:03d}_{_slug(prompt)}"

            # Always save raw SVG
            (s4_svgs / f"{stem}.svg").write_text(svg, encoding="utf-8")
            with open(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.svg"), "w") as f:
                f.write(svg)
            s4_prompts.append(prompt)

            rendered = render_svg_to_pil(svg, size=224)
            if rendered is None:
                results.append({"prompt": prompt, "clip": 0.0, "success": False})
                continue

            rendered.save(str(s4_pngs / f"{stem}.png"))
            rendered.save(os.path.join(cfg.EVAL_DIR, f"eval_{i:03d}.png"))

            img_t = clip_prep(rendered).unsqueeze(0)
            txt_t = clip_tok([prompt])
            if torch.cuda.is_available():
                img_t = img_t.cuda(); txt_t = txt_t.cuda()

            with torch.no_grad():
                img_f = clip_model.encode_image(img_t)
                txt_f = clip_model.encode_text(txt_t)
                img_f /= img_f.norm(dim=-1, keepdim=True)
                txt_f /= txt_f.norm(dim=-1, keepdim=True)
                score = (img_f @ txt_f.T).item() * 100

            results.append({"prompt": prompt, "clip": score, "success": True})
            log.info(f"  [{i+1}/{n_samples}] CLIP={score:.2f}  {prompt[:50]}")

        except Exception as e:
            log.error(f"  Eval error: {e}")
            results.append({"prompt": prompt, "clip": 0.0, "success": False})

    (s4_dir / "prompts.txt").write_text("\n".join(s4_prompts), encoding="utf-8")

    del clip_model; gc.collect(); torch.cuda.empty_cache()

    ok = [r for r in results if r["success"]]
    summary = {
        "n_total": len(results), "n_success": len(ok),
        "clip_mean":   float(np.mean([r["clip"] for r in ok]))   if ok else 0.0,
        "clip_median": float(np.median([r["clip"] for r in ok])) if ok else 0.0,
        "clip_std":    float(np.std([r["clip"] for r in ok]))    if ok else 0.0,
        "results": results,
    }
    with open(os.path.join(cfg.EVAL_DIR, "eval_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    if ok:
        log.info(f"CLIP mean={summary['clip_mean']:.2f}  median={summary['clip_median']:.2f}")
    return summary


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    # ── Re-read secrets at runtime (Config reads them at import time,
    #    before Kaggle/Colab secrets client is fully ready) ──
    if IN_KAGGLE:
        try:
            from kaggle_secrets import UserSecretsClient
            usc = UserSecretsClient()
            for key in ("GEMINI_API_KEY", "HF_TOKEN"):
                try:
                    val = usc.get_secret(key)
                    if val:
                        setattr(cfg, key, val)
                        os.environ[key] = val
                        log.info(f"{key} reloaded from Kaggle Secrets: OK")
                except Exception as e:
                    log.warning(f"{key} not found in Kaggle Secrets: {e}")
        except ImportError:
            pass
    if IN_COLAB:
        try:
            from google.colab import userdata
            for key in ("GEMINI_API_KEY", "HF_TOKEN"):
                try:
                    val = userdata.get(key)
                    if val:
                        setattr(cfg, key, val)
                        os.environ[key] = val
                        log.info(f"{key} reloaded from Colab Secrets: OK")
                except Exception as e:
                    log.warning(f"{key} not found in Colab Secrets: {e}")
        except ImportError:
            pass

    if not torch.cuda.is_available():
        msg = "No GPU!"
        if IN_KAGGLE: msg += " Kaggle: Settings → Accelerator → GPU T4 x2."
        if IN_COLAB:  msg += " Colab: Runtime → Change runtime type → T4 GPU."
        log.warning(msg)
    else:
        log.info(f"GPU: {torch.cuda.get_device_name(0)}  "
                 f"VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")

    # Mine prompts
    bad_prompts = mine_failures(find_results_json())
    log.info(f"Prompts: {len(bad_prompts)}")

    # Stage 1
    raw_dataset = generate_dataset(bad_prompts)

    # Stage 2 — Gemini gate
    filtered = vlm_quality_gate(raw_dataset)

    Path(cfg.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(cfg.OUTPUT_DIR, "training_pairs.json"), "w") as f:
        json.dump(filtered, f, indent=2)
    log.info(f"{len(filtered)} pairs after gate.")

    if not filtered:
        log.error("No training data. Aborting.")
        return

    # Stage 3 — fine-tune
    model, tokenizer = train_lora(filtered)

    # Stage 4 + 5 — inference + eval
    if model is not None:
        evaluate_pipeline(model, tokenizer, bad_prompts, n_samples=20)

    # Package ALL stages
    archive = os.path.join(cfg.WORKING_DIR, "diffusvg_full_output.zip")
    stage_dirs = [
        ("stage1_generated", Path(cfg.WORKING_DIR) / "stage1_generated"),
        ("stage2_filtered",  Path(cfg.WORKING_DIR) / "stage2_filtered"),
        ("stage2_rejected",  Path(cfg.WORKING_DIR) / "stage2_rejected"),
        ("stage3_training",  Path(cfg.WORKING_DIR) / "stage3_training"),
        ("stage4_inference", Path(cfg.WORKING_DIR) / "stage4_inference"),
        ("eval_results",     Path(cfg.EVAL_DIR)),
        ("final_adapter",    Path(cfg.LORA_OUTPUT_DIR) / "final_adapter"),
    ]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc_root, src in stage_dirs:
            if not src.exists():
                log.warning(f"  skip missing: {src}")
                continue
            for fp in src.rglob("*"):
                if fp.is_file():
                    zf.write(fp, arc_root + "/" + fp.relative_to(src).as_posix())
            log.info(f"  packed {arc_root}/")

    log.info(f"Done. Archive → {archive}")
    log.info("Download from Kaggle Output panel → diffusvg_full_output.zip")


if __name__ == "__main__":
    main()
