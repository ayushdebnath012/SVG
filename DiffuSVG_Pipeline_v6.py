# -*- coding: utf-8 -*-
"""
DiffuSVG_Pipeline_v6.py — Dataset + LoRA Training Pipeline
Runs on Kaggle T4 GPU (16 GB VRAM).

Stages:
  1. Load existing training_pairs.json, classify by complexity, augment
  2. QLoRA fine-tune Qwen2-VL-7B-Instruct on prompt → SVG
  3. Inference on held-out test prompts
  4. CLIP evaluation + HTML gallery
"""

import subprocess, sys, os, gc, json, logging, re, random, shutil
from pathlib import Path
from typing import List, Optional

# Must be set BEFORE any torch/CUDA import
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# ── Ensure bitsandbytes >= 0.46.1 (Kaggle ships an older version) ─────────
def _ensure_deps():
    """Check bitsandbytes version; upgrade + restart kernel if needed."""
    need_restart = False
    try:
        import bitsandbytes
        from packaging.version import Version
        if Version(bitsandbytes.__version__) < Version("0.46.1"):
            print(f"⚠️  bitsandbytes {bitsandbytes.__version__} is too old, upgrading...")
            need_restart = True
    except ImportError:
        need_restart = True

    if need_restart:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U",
            "bitsandbytes>=0.46.1", "peft>=0.13.0", "accelerate>=0.26.0"])
        # Also install other deps while we're at it
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
            "cairosvg", "open_clip_torch"])
        print("✅ Dependencies upgraded. Restarting kernel...")
        # Auto-restart on Kaggle/Colab
        import IPython
        IPython.Application.instance().kernel.do_shutdown(True)
        # If we reach here, restart didn't work — tell user
        raise SystemExit("Please restart the kernel and re-run this cell.")

    # Install non-restart deps quietly
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
        "cairosvg", "open_clip_torch", "peft>=0.13.0"])

_ensure_deps()

import torch, numpy as np
from PIL import Image
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ── Detect environment ───────────────────────────────────────────────────────
def _detect_env() -> str:
    if Path("/kaggle").exists():
        return "kaggle"
    try:
        import google.colab
        return "colab"
    except ImportError:
        pass
    return "local"

_ENV = _detect_env()
WORKING_DIR = {
    "kaggle": "/kaggle/working",
    "colab": "/content",
    "local": "/tmp/diffusvg",
}[_ENV]
os.makedirs(WORKING_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DiffuSVG-v6")
log.info(f"Environment: {_ENV}, Working dir: {WORKING_DIR}")

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    # Dataset
    TRAINING_PAIRS_PATH: str = ""  # set in main()
    MAX_SVG_CHARS: int = 4000     # skip overly complex SVGs
    MIN_SVG_CHARS: int = 50       # skip trivially short SVGs
    VAL_SPLIT: float = 0.1

    # Model — 2B fits comfortably on T4; 7B needs >10GB free
    VLM_MODEL: str = "Qwen/Qwen2-VL-2B-Instruct"
    MAX_SEQ_LEN: int = 1024  # SVGs are short; saves ~50% VRAM vs 2048

    # LoRA
    LORA_R: int = 8
    LORA_ALPHA: int = 16
    LORA_DROPOUT: float = 0.05

    # Training
    EPOCHS: int = 5
    BATCH_SIZE: int = 1
    GRAD_ACCUM: int = 8
    LEARNING_RATE: float = 1e-4
    WARMUP_RATIO: float = 0.1

    # Output
    OUTPUT_DIR: str = ""  # set in main()
    LORA_OUTPUT_DIR: str = ""
    EVAL_DIR: str = ""

cfg = Config()


# ════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT & FEW-SHOT
# ════════════════════════════════════════════════════════════════════════════
_SVG_SYSTEM = """\
You are an SVG code generator. Given a text description, output ONLY the SVG \
element body (rect, circle, polygon, path, ellipse, line, etc.) that would appear \
inside <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">...</svg>.

Rules:
- Output ONLY SVG elements, no <svg> wrapper, no comments, no explanation.
- Always start with a background rect: <rect width="200" height="200" fill="#COLOR"/>
- Use solid fill colors (hex). No gradients, no filters, no blur.
- Keep it simple: aim for 3-25 elements maximum.
- Use geometric primitives: rect, circle, ellipse, polygon, line, path.
- All coordinates within 0-200 range.
"""

# Seed examples for few-shot
_FEW_SHOT_EXAMPLES = [
    ("a blue circle",
     '<rect width="200" height="200" fill="#ffffff"/>\n<circle cx="100" cy="100" r="60" fill="#1565C0"/>'),
    ("a red heart",
     '<rect width="200" height="200" fill="#ffffff"/>\n<circle cx="75" cy="85" r="30" fill="#E53935"/>\n<circle cx="125" cy="85" r="30" fill="#E53935"/>\n<polygon points="45,100 100,165 155,100" fill="#E53935"/>'),
    ("a house with red roof",
     '<rect width="200" height="200" fill="#E3F2FD"/>\n<rect x="50" y="110" width="100" height="80" fill="#FFF9C4"/>\n<polygon points="100,40 50,110 150,110" fill="#C62828"/>\n<rect x="88" y="150" width="25" height="40" fill="#5D4037"/>\n<rect x="60" y="125" width="20" height="20" fill="#81D4FA" stroke="#555" stroke-width="1"/>'),
    ("a rocket",
     '<rect width="200" height="200" fill="#0D1B2A"/>\n<polygon points="100,20 75,90 125,90" fill="#B0BEC5"/>\n<rect x="75" y="90" width="50" height="90" fill="#CFD8DC"/>\n<circle cx="100" cy="115" r="15" fill="#81D4FA"/>\n<polygon points="75,180 55,180 75,140" fill="#E53935"/>\n<polygon points="125,180 145,180 125,140" fill="#E53935"/>\n<polygon points="85,180 100,200 115,180" fill="#FF7043"/>'),
]


def _few_shot_block(prompt: str, n: int = 2) -> str:
    """Build a few-shot prompt with n examples + the actual prompt."""
    examples = random.sample(_FEW_SHOT_EXAMPLES, min(n, len(_FEW_SHOT_EXAMPLES)))
    parts = []
    for ex_prompt, ex_svg in examples:
        parts.append(f"Prompt: {ex_prompt}\nSVG:\n{ex_svg}\n")
    parts.append(f"Prompt: {prompt}\nSVG:")
    return "\n".join(parts)


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1: LOAD & PREPARE DATASET
# ════════════════════════════════════════════════════════════════════════════
def _classify_complexity(svg: str) -> str:
    """Classify SVG complexity based on element count."""
    import re
    tags = re.findall(r"<(rect|circle|ellipse|polygon|polyline|line|path|text)\b", svg)
    n = len(tags)
    if n <= 3:
        return "simple"
    elif n <= 10:
        return "medium"
    else:
        return "complex"


def _wrap_svg(body: str) -> str:
    return f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>'


def _render_svg_to_pil(svg_string: str, size: int = 200) -> Optional[Image.Image]:
    """Render SVG string to PIL image."""
    try:
        import cairosvg, io
        png_data = cairosvg.svg2png(bytestring=svg_string.encode("utf-8"),
                                     output_width=size, output_height=size)
        return Image.open(io.BytesIO(png_data)).convert("RGB")
    except Exception:
        return None


def load_dataset(path: str) -> List[dict]:
    """Load training pairs, filter, and classify by complexity."""
    log.info(f"Loading dataset from {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    dataset = []
    skipped = 0
    for item in raw:
        svg = item.get("svg", "")
        prompt = item.get("prompt", "")
        if not svg or not prompt:
            skipped += 1
            continue
        if len(svg) < cfg.MIN_SVG_CHARS or len(svg) > cfg.MAX_SVG_CHARS:
            skipped += 1
            continue

        complexity = _classify_complexity(svg)
        dataset.append({
            "prompt": prompt,
            "svg": svg,
            "complexity": complexity,
            "is_seed": item.get("is_seed", False),
            "svg_chars": len(svg),
        })

    # Sort by complexity for curriculum ordering
    order = {"simple": 0, "medium": 1, "complex": 2}
    dataset.sort(key=lambda x: (order[x["complexity"]], x["svg_chars"]))

    stats = {}
    for d in dataset:
        c = d["complexity"]
        stats[c] = stats.get(c, 0) + 1

    log.info(f"Dataset: {len(dataset)} usable, {skipped} skipped")
    log.info(f"  Complexity breakdown: {stats}")
    return dataset


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2: QLoRA FINE-TUNING
# ════════════════════════════════════════════════════════════════════════════
def build_chat_pair(prompt: str, svg_body: str, tokenizer) -> str:
    messages = [
        {"role": "system", "content": _SVG_SYSTEM},
        {"role": "user", "content": _few_shot_block(prompt, n=2)},
        {"role": "assistant", "content": svg_body},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False)


class SVGCausalDataset(torch.utils.data.Dataset):
    def __init__(self, data: list, tokenizer, max_len: int):
        self.samples = []
        skipped = 0
        for item in data:
            full_text = build_chat_pair(item["prompt"], item["svg"], tokenizer)
            toks = tokenizer(full_text, truncation=True, max_length=max_len,
                             padding="max_length", return_tensors="pt")
            input_ids = toks["input_ids"].squeeze()
            attn_mask = toks["attention_mask"].squeeze()

            # Mask prompt tokens (only train on SVG output)
            prompt_messages = [
                {"role": "system", "content": _SVG_SYSTEM},
                {"role": "user", "content": _few_shot_block(item["prompt"], n=2)},
            ]
            prompt_only = tokenizer.apply_chat_template(
                prompt_messages, tokenize=False, add_generation_prompt=True)
            prompt_len = len(tokenizer(prompt_only, truncation=True, max_length=max_len)["input_ids"])

            labels = input_ids.clone()
            labels[:prompt_len] = -100
            labels[attn_mask == 0] = -100

            if (labels != -100).sum() < 20:
                skipped += 1
                continue

            self.samples.append({
                "input_ids": input_ids,
                "attention_mask": attn_mask,
                "labels": labels,
            })
        log.info(f"  SVGCausalDataset: {len(self.samples)} usable, {skipped} skipped")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def train_lora(dataset: list):
    """QLoRA fine-tune Qwen2-VL-7B on prompt → SVG pairs."""
    from transformers import (
        AutoTokenizer, Qwen2VLForConditionalGeneration,
        BitsAndBytesConfig, TrainingArguments, Trainer,
    )

    log.info("=" * 70)
    log.info("STAGE 2: QLoRA Fine-Tuning")
    log.info("=" * 70)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(cfg.VLM_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Aggressively free GPU before model load
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    # Check GPU memory
    if torch.cuda.is_available():
        free_gb = torch.cuda.mem_get_info()[0] / 1e9
        total_gb = torch.cuda.mem_get_info()[1] / 1e9
        log.info(f"GPU: {free_gb:.1f} GB free / {total_gb:.1f} GB total")
        if free_gb < 1.0:
            log.error(f"Only {free_gb:.1f} GB free — restart the kernel to free GPU memory.")
            return None, None

    # Load model with 4-bit quantization
    log.info(f"Loading {cfg.VLM_MODEL} with 4-bit NF4 quantization...")
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

    # Apply LoRA
    lora_config = LoraConfig(
        r=cfg.LORA_R, lora_alpha=cfg.LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_dropout=cfg.LORA_DROPOUT, task_type=TaskType.CAUSAL_LM, bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.is_parallelizable = False
    model.model_parallel = False
    model.print_trainable_parameters()

    # Prepare train/val split
    random.shuffle(dataset)
    split = int(len(dataset) * (1 - cfg.VAL_SPLIT))
    train_data, val_data = dataset[:split], dataset[split:]

    train_ds = SVGCausalDataset(train_data, tokenizer, cfg.MAX_SEQ_LEN)
    val_ds = SVGCausalDataset(val_data, tokenizer, cfg.MAX_SEQ_LEN) if val_data else None

    if len(train_ds) == 0:
        log.error("No usable training samples!")
        return None, None

    log.info(f"Train: {len(train_ds)} samples, Val: {len(val_ds) if val_ds else 0} samples")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=cfg.LORA_OUTPUT_DIR,
        per_device_train_batch_size=cfg.BATCH_SIZE,
        per_device_eval_batch_size=cfg.BATCH_SIZE,
        gradient_accumulation_steps=cfg.GRAD_ACCUM,
        num_train_epochs=cfg.EPOCHS,
        learning_rate=cfg.LEARNING_RATE,
        warmup_steps=max(1, int(cfg.WARMUP_RATIO * (len(train_ds) // (cfg.BATCH_SIZE * cfg.GRAD_ACCUM)) * cfg.EPOCHS)),
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
        optim="paged_adamw_8bit",
        max_grad_norm=0.3,
    )

    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=val_ds,
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
# STAGE 3: INFERENCE
# ════════════════════════════════════════════════════════════════════════════
@torch.inference_mode()
def generate_svg(prompt: str, model, tokenizer, max_new_tokens: int = 1500) -> str:
    messages = [
        {"role": "system", "content": _SVG_SYSTEM},
        {"role": "user", "content": _few_shot_block(prompt, n=2)},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    out = model.generate(
        **inputs, max_new_tokens=max_new_tokens,
        do_sample=True, temperature=0.7, top_p=0.9, repetition_penalty=1.1,
    )
    response = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    svg_body = response.strip()
    # Clean markdown fences
    svg_body = re.sub(r"^```(?:svg|xml|html)?\s*\n?", "", svg_body)
    svg_body = re.sub(r"\n?```\s*$", "", svg_body)
    # If model emitted full SVG, extract body
    if "<svg" in svg_body:
        m = re.search(r"<svg[^>]*>(.*?)</svg>", svg_body, re.DOTALL)
        if m:
            svg_body = m.group(1).strip()
    return _wrap_svg(svg_body)


# ════════════════════════════════════════════════════════════════════════════
# STAGE 4: EVALUATION
# ════════════════════════════════════════════════════════════════════════════
_TEST_PROMPTS = [
    "a purple butterfly",
    "a green leaf",
    "a blue diamond",
    "a red car",
    "an orange cat",
    "a yellow flower",
    "a pink umbrella",
    "a brown dog",
    "a gray cloud",
    "a white snowflake on blue background",
    "a gold trophy",
    "a silver key",
    "a black chess piece",
    "a rainbow flag",
    "a green cactus",
    "a blue whale",
    "a red fire truck",
    "an ice cream cone",
    "a smiling sun",
    "a crescent moon with stars",
]


def evaluate_pipeline(model, tokenizer) -> dict:
    """Generate SVGs for test prompts and score with CLIP."""
    log.info("=" * 70)
    log.info("STAGE 4: Evaluation (CLIP scoring)")
    log.info("=" * 70)

    try:
        import open_clip
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "open_clip_torch"])
        import open_clip

    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k")
    clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")
    clip_model = clip_model.float().eval()
    if torch.cuda.is_available():
        clip_model = clip_model.cuda()

    Path(cfg.EVAL_DIR).mkdir(parents=True, exist_ok=True)
    results = []

    for i, prompt in enumerate(_TEST_PROMPTS):
        try:
            svg = generate_svg(prompt, model, tokenizer)
            rendered = _render_svg_to_pil(svg, size=224)
            if rendered is None:
                results.append({"prompt": prompt, "clip": 0.0, "success": False})
                continue

            # Save outputs
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
                img_f = clip_model.encode_image(img_tensor)
                txt_f = clip_model.encode_text(txt_tensor)
                img_f /= img_f.norm(dim=-1, keepdim=True)
                txt_f /= txt_f.norm(dim=-1, keepdim=True)
                score = (img_f @ txt_f.T).item() * 100

            results.append({"prompt": prompt, "clip": score, "success": True})
            log.info(f"  [{i+1}/{len(_TEST_PROMPTS)}] CLIP={score:.2f}  {prompt[:50]}")
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
            "n_total": len(results), "n_success": len(successful),
            "clip_mean": float(np.mean(scores)),
            "clip_median": float(np.median(scores)),
            "clip_std": float(np.std(scores)),
            "results": results,
        }
    else:
        summary = {"n_total": len(results), "n_success": 0, "results": results}

    eval_path = os.path.join(cfg.EVAL_DIR, "eval_summary.json")
    with open(eval_path, "w") as f:
        json.dump(summary, f, indent=2)

    if successful:
        log.info(f"  CLIP: mean={summary['clip_mean']:.2f}, "
                 f"median={summary['clip_median']:.2f}, std={summary['clip_std']:.2f}")
    return summary


# ════════════════════════════════════════════════════════════════════════════
# HTML GALLERY
# ════════════════════════════════════════════════════════════════════════════
def generate_gallery(eval_dir: str):
    """Generate an HTML gallery of evaluation results."""
    html = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
            '<title>DiffuSVG v6 Evaluation Gallery</title>',
            '<style>body{background:#1a1a2e;color:#eee;font-family:Inter,sans-serif;padding:20px}',
            'h1{text-align:center;color:#e94560}',
            '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:20px;padding:20px}',
            '.card{background:#16213e;border-radius:12px;padding:15px;text-align:center;',
            'box-shadow:0 4px 15px rgba(0,0,0,0.3)}',
            '.card img{width:200px;height:200px;border-radius:8px;background:#fff}',
            '.card .prompt{font-size:14px;margin:10px 0 5px;color:#a8d8ea}',
            '.card .score{font-size:18px;font-weight:bold;color:#e94560}',
            '</style></head><body>',
            '<h1>🎨 DiffuSVG v6 — Generated SVGs</h1>',
            '<div class="grid">']

    eval_json = os.path.join(eval_dir, "eval_summary.json")
    if os.path.exists(eval_json):
        with open(eval_json) as f:
            data = json.load(f)
        for i, r in enumerate(data.get("results", [])):
            img_path = f"eval_{i:03d}.png"
            clip_str = f"{r['clip']:.1f}" if r["success"] else "FAIL"
            html.append(f'<div class="card">')
            html.append(f'<img src="{img_path}" alt="{r["prompt"]}">')
            html.append(f'<div class="prompt">{r["prompt"]}</div>')
            html.append(f'<div class="score">CLIP: {clip_str}</div>')
            html.append(f'</div>')

    html.append('</div></body></html>')
    gallery_path = os.path.join(eval_dir, "gallery.html")
    with open(gallery_path, "w") as f:
        f.write("\n".join(html))
    log.info(f"Gallery saved → {gallery_path}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 70)
    log.info("DiffuSVG Pipeline v6 — Dataset + LoRA Training")
    log.info("=" * 70)

    # ── Configure paths ──────────────────────────────────────────────────
    # Look for training_pairs.json in multiple locations
    candidates = [
        # Kaggle dataset input path
        "/kaggle/input/datasets/rkamondal/diffusvg-v5/training_pairs.json",
        "/kaggle/input/diffusvg-v5/training_pairs.json",
        os.path.join(WORKING_DIR, "diffusvg_v5_output", "training_pairs.json"),
        os.path.join(WORKING_DIR, "dataset", "training_pairs.json"),
        os.path.join(WORKING_DIR, "training_pairs.json"),
        # Local dev path
        "f:/SVG-20260310T151742Z-1-001/SVG/diffusvg_v5_output/training_pairs.json",
    ]
    cfg.TRAINING_PAIRS_PATH = ""
    for c in candidates:
        if os.path.exists(c):
            cfg.TRAINING_PAIRS_PATH = c
            break

    if not cfg.TRAINING_PAIRS_PATH:
        log.error("training_pairs.json not found! Expected locations:")
        for c in candidates:
            log.error(f"  {c}")
        log.error("Please upload diffusvg_v5_output/ as a Kaggle dataset or place training_pairs.json in /kaggle/working/")
        return

    cfg.OUTPUT_DIR = os.path.join(WORKING_DIR, "diffusvg_v6_output")
    cfg.LORA_OUTPUT_DIR = os.path.join(cfg.OUTPUT_DIR, "lora_checkpoints")
    cfg.EVAL_DIR = os.path.join(cfg.OUTPUT_DIR, "evaluation")
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    os.makedirs(cfg.LORA_OUTPUT_DIR, exist_ok=True)
    os.makedirs(cfg.EVAL_DIR, exist_ok=True)

    # ── Stage 1: Load Dataset ────────────────────────────────────────────
    log.info("=" * 70)
    log.info("STAGE 1: Loading & Preparing Dataset")
    log.info("=" * 70)

    dataset = load_dataset(cfg.TRAINING_PAIRS_PATH)
    if len(dataset) < 5:
        log.error(f"Only {len(dataset)} samples — need at least 5 to train.")
        return

    # Save processed dataset
    dataset_path = os.path.join(cfg.OUTPUT_DIR, "processed_dataset.json")
    with open(dataset_path, "w") as f:
        json.dump(dataset, f, indent=2)
    log.info(f"Processed dataset saved → {dataset_path}")

    # Log sample details
    log.info("Sample entries:")
    for item in dataset[:5]:
        log.info(f"  [{item['complexity']:7s}] {item['svg_chars']:5d} chars  {item['prompt'][:60]}")
    log.info("  ...")

    # ── Stage 2: Train LoRA ──────────────────────────────────────────────
    model, tokenizer = train_lora(dataset)

    if model is None:
        log.error("Training failed. Exiting.")
        return

    # ── Stage 3+4: Inference & Evaluation ────────────────────────────────
    log.info("=" * 70)
    log.info("STAGE 3: Inference on test prompts")
    log.info("=" * 70)

    eval_summary = evaluate_pipeline(model, tokenizer)

    # ── Generate Gallery ─────────────────────────────────────────────────
    generate_gallery(cfg.EVAL_DIR)

    # ── Zip everything ───────────────────────────────────────────────────
    zip_base = os.path.join(WORKING_DIR, "diffusvg_v6_output")
    shutil.make_archive(zip_base, "zip", cfg.OUTPUT_DIR)
    log.info(f"Zipped → {zip_base}.zip")

    # ── Final Summary ────────────────────────────────────────────────────
    log.info("=" * 70)
    log.info("PIPELINE COMPLETE")
    log.info("=" * 70)
    log.info(f"  Dataset:    {len(dataset)} training pairs")
    log.info(f"  Adapter:    {os.path.join(cfg.LORA_OUTPUT_DIR, 'final_adapter')}")
    log.info(f"  Evaluation: {cfg.EVAL_DIR}")
    if eval_summary.get("n_success", 0) > 0:
        log.info(f"  CLIP mean:  {eval_summary['clip_mean']:.2f}")
    log.info(f"  Output zip: {zip_base}.zip")

    if _ENV == "kaggle":
        log.info("\n📥 Download from Kaggle:")
        log.info("  → Right panel → Output → diffusvg_v6_output.zip")


if __name__ == "__main__":
    main()
