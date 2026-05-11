# -*- coding: utf-8 -*-
"""
OmniSVG_Kaggle.py  —  OmniSVG text-to-SVG inference on Kaggle T4 GPU
======================================================================

Pipeline:
  1. Install system + Python dependencies
  2. Load OmniSVG 4B model (Qwen2.5-VL-3B-Instruct backbone)
     with 4-bit NF4 quantization to fit on T4 16 GB
  3. Run text-to-SVG on eval_prompts.json (50 held-out prompts)
  4. CLIP ViT-B/32 evaluation (score >= 21.5 = success)
  5. Save SVGs, PNGs, results JSON, and HTML gallery to /kaggle/working

Kaggle setup:
  - Accelerator : GPU T4 x1
  - Internet    : ON
  - Secrets     : HF_TOKEN  (required)
  - Add dataset : (optional) your prior eval_prompts.json as a Kaggle dataset

Local testing:
  - Set HF_TOKEN env var or edit HF_TOKEN below
  - Run: python OmniSVG_Kaggle.py
"""

import subprocess, sys, os, gc, json, logging, re, io, time
from pathlib import Path
from typing import Optional, List

# ── Detect environment ──────────────────────────────────────────────────────
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
WORKING_DIR = {"kaggle": "/kaggle/working", "colab": "/content", "local": "/tmp/omnisvg"}[_ENV]
OMNISVG_DIR = str(Path(__file__).parent / "OmniSVG")
os.makedirs(WORKING_DIR, exist_ok=True)

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# Redirect HF cache so large downloads don't fill the system disk on Kaggle
_HF_CACHE = os.path.join(WORKING_DIR, "hf_cache")
os.makedirs(_HF_CACHE, exist_ok=True)
for _k in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE"):
    os.environ[_k] = _HF_CACHE

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("OmniSVG-Kaggle")
log.info(f"Environment: {_ENV}  |  Working dir: {WORKING_DIR}")
log.info(f"OmniSVG source: {OMNISVG_DIR}")


# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
class Config:
    # Model
    MODEL_SIZE: str = "4B"          # "4B" (needs ~8 GB) or "8B" (needs ~12 GB) — both fit T4 w/ 4-bit
    HF_TOKEN:   str = ""            # filled from Kaggle Secret / env var in main()

    # Eval prompts (JSON file, relative to this script)
    PROMPTS_JSON: str = str(Path(__file__).parent / "eval_prompts.json")

    # Generation
    NUM_CANDIDATES: int = 2         # candidates per prompt (increase for quality, decrease for speed)
    MAX_LENGTH:     int = 1024      # OmniSVG token budget per candidate
    TEMPERATURE:    float = 0.5
    TOP_P:          float = 0.88
    TOP_K:          int   = 50
    REP_PENALTY:    float = 1.05

    # Evaluation
    CLIP_THRESHOLD: float = 21.5    # scores above blank-image baseline (~20.0)

    # Output
    OUTPUT_DIR:  str = os.path.join(WORKING_DIR, "omnisvg_outputs")
    RESULTS_JSON: str = os.path.join(WORKING_DIR, "omnisvg_results.json")
    GALLERY_HTML: str = os.path.join(WORKING_DIR, "omnisvg_gallery.html")

cfg = Config()


# ════════════════════════════════════════════════════════════════════════════
# STEP 0 — Install dependencies
# ════════════════════════════════════════════════════════════════════════════
def _install():
    log.info("Installing system dependencies (libcairo2) ...")
    subprocess.run(["apt-get", "update", "-q"], capture_output=True)
    subprocess.run(["apt-get", "install", "-y", "-q",
                    "libcairo2", "libcairo2-dev"], capture_output=True)

    log.info("Installing Python dependencies ...")
    pkgs = [
        "transformers>=4.51.0",
        "accelerate>=0.26.0",
        "bitsandbytes>=0.43.0",
        "qwen-vl-utils==0.0.11",
        "cairosvg==2.7.1",
        "einops==0.4.1",
        "shapely>=2.0.0",
        "open_clip_torch",
        "pillow>=10.0.0",
        "pyyaml",
        "huggingface-hub",
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + pkgs)
    log.info("Dependencies installed.")


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — HF token
# ════════════════════════════════════════════════════════════════════════════
def _get_hf_token() -> str:
    if os.environ.get("HF_TOKEN", "").startswith("hf_"):
        return os.environ["HF_TOKEN"]
    try:
        from kaggle_secrets import UserSecretsClient
        tok = UserSecretsClient().get_secret("HF_TOKEN")
        if tok and tok.startswith("hf_"):
            log.info("HF_TOKEN loaded from Kaggle Secrets.")
            return tok
    except Exception:
        pass
    tok = cfg.HF_TOKEN
    if not tok:
        raise RuntimeError(
            "HF_TOKEN not set. Add it as a Kaggle Secret named HF_TOKEN "
            "or set the HF_TOKEN environment variable."
        )
    return tok


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Load OmniSVG model
# ════════════════════════════════════════════════════════════════════════════
_omnisvg_loaded = False
_inference_mod  = None


def _load_omnisvg():
    """Import OmniSVG inference module and load models."""
    global _omnisvg_loaded, _inference_mod

    if _omnisvg_loaded:
        return

    # Make OmniSVG importable
    if OMNISVG_DIR not in sys.path:
        sys.path.insert(0, OMNISVG_DIR)

    # inference.py uses CONFIG_PATH = './config.yaml' — must cd to OmniSVG dir
    os.chdir(OMNISVG_DIR)

    import importlib
    _inference_mod = importlib.import_module("inference")

    log.info(f"Loading OmniSVG {cfg.MODEL_SIZE} model ...")
    _inference_mod.load_models(
        model_size=cfg.MODEL_SIZE,
        weight_path=None,   # auto-downloads OmniSVG weights from HF
        model_path=None,    # auto-downloads Qwen base from HF
    )
    _omnisvg_loaded = True
    log.info("OmniSVG model loaded.")


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Generate SVG for a single prompt
# ════════════════════════════════════════════════════════════════════════════
def generate_svg(prompt: str) -> Optional[str]:
    """Run OmniSVG text-to-SVG for one prompt. Returns best SVG string or None."""
    inf = _inference_mod

    subtype = inf.detect_text_subtype(prompt)
    inputs  = inf.prepare_inputs("text-to-svg", prompt)

    candidates = inf.generate_candidates(
        inputs       = inputs,
        task_type    = "text-to-svg",
        subtype      = subtype,
        temperature  = cfg.TEMPERATURE,
        top_p        = cfg.TOP_P,
        top_k        = cfg.TOP_K,
        repetition_penalty = cfg.REP_PENALTY,
        max_length   = cfg.MAX_LENGTH,
        num_samples  = cfg.NUM_CANDIDATES,
        verbose      = False,
    )

    if not candidates:
        return None
    return candidates[0]["svg"]


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — CLIP evaluation
# ════════════════════════════════════════════════════════════════════════════
_clip_model  = None
_clip_preproc = None
_clip_tokenize = None


def _load_clip():
    global _clip_model, _clip_preproc, _clip_tokenize
    if _clip_model is not None:
        return
    import open_clip, torch
    log.info("Loading CLIP ViT-B-32 ...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    _clip_model, _, _clip_preproc = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    _clip_tokenize = open_clip.get_tokenizer("ViT-B-32")
    _clip_model = _clip_model.to(device).eval()
    log.info("CLIP loaded.")


def clip_score(svg_str: str, prompt: str) -> float:
    """CLIP ViT-B/32 cosine similarity * 100 between rendered SVG and prompt."""
    import torch, cairosvg
    from PIL import Image

    _load_clip()
    device = next(_clip_model.parameters()).device

    # Render SVG → PIL
    try:
        png = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"),
                               output_width=224, output_height=224)
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        bg  = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img_t = _clip_preproc(bg).unsqueeze(0).to(device)
    except Exception as e:
        log.warning(f"CLIP render error: {e}")
        return 0.0

    txt_t = _clip_tokenize([prompt]).to(device)

    with torch.no_grad():
        img_f = _clip_model.encode_image(img_t)
        txt_f = _clip_model.encode_text(txt_t)
        img_f = img_f / img_f.norm(dim=-1, keepdim=True)
        txt_f = txt_f / txt_f.norm(dim=-1, keepdim=True)
        score = (img_f @ txt_f.T).item() * 100.0

    return round(score, 3)


# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — Save outputs
# ════════════════════════════════════════════════════════════════════════════
def save_svg_and_png(svg_str: str, stem: str) -> str:
    """Save SVG and PNG to OUTPUT_DIR. Returns SVG path."""
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
    svg_path = os.path.join(cfg.OUTPUT_DIR, f"{stem}.svg")
    png_path = os.path.join(cfg.OUTPUT_DIR, f"{stem}.png")

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_str)

    try:
        import cairosvg
        from PIL import Image
        png = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"),
                               output_width=512, output_height=512)
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        bg  = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        bg.save(png_path)
    except Exception as e:
        log.warning(f"PNG save failed for {stem}: {e}")

    return svg_path


def build_html_gallery(results: list) -> str:
    """Build an HTML gallery from results list."""
    rows = ""
    for r in results:
        color  = "#2ecc71" if r["success"] else "#e74c3c"
        label  = "PASS" if r["success"] else "FAIL"
        img_src = ""
        png = os.path.join(cfg.OUTPUT_DIR, f"{r['stem']}.png")
        if os.path.exists(png):
            import base64
            with open(png, "rb") as f:
                img_src = "data:image/png;base64," + base64.b64encode(f.read()).decode()
        rows += f"""
<div style="display:inline-block;margin:8px;text-align:center;width:180px;
            font-family:sans-serif;border:1px solid #ddd;border-radius:6px;padding:8px">
  {'<img src="' + img_src + '" width="160" height="160" style="border:1px solid #eee">' if img_src else '<div style="width:160px;height:160px;background:#f5f5f5;line-height:160px;text-align:center;color:#aaa">no render</div>'}
  <div style="font-size:11px;margin-top:4px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis"
       title="{r['prompt']}">{r['prompt']}</div>
  <div style="font-size:10px;color:{color};font-weight:bold">{label} · CLIP {r['clip']:.1f}</div>
</div>"""

    total   = len(results)
    n_pass  = sum(1 for r in results if r["success"])
    clip_vals = [r["clip"] for r in results if r["clip"] > 0]
    clip_avg  = round(sum(clip_vals) / len(clip_vals), 2) if clip_vals else 0

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>OmniSVG Results</title></head>
<body style="background:#fafafa;padding:20px;font-family:sans-serif">
<h2>OmniSVG Text-to-SVG — Evaluation Gallery</h2>
<p>Model: OmniSVG {cfg.MODEL_SIZE} &nbsp;|&nbsp;
   Prompts: {total} &nbsp;|&nbsp;
   Pass: {n_pass}/{total} ({100*n_pass//total if total else 0}%) &nbsp;|&nbsp;
   CLIP mean: {clip_avg} &nbsp;|&nbsp;
   Threshold: {cfg.CLIP_THRESHOLD}</p>
<hr>
{rows}
</body></html>"""


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    # ── 0. deps ──────────────────────────────────────────────────────────────
    _install()

    # ── 1. auth ──────────────────────────────────────────────────────────────
    hf_token = _get_hf_token()
    os.environ["HF_TOKEN"] = hf_token
    try:
        from huggingface_hub import login
        login(token=hf_token, add_to_git_credential=False)
        log.info("Logged in to HuggingFace.")
    except Exception as e:
        log.warning(f"HF login skipped: {e}")

    # ── 2. load model ────────────────────────────────────────────────────────
    _load_omnisvg()
    _load_clip()

    # ── 3. load prompts ──────────────────────────────────────────────────────
    prompts_path = cfg.PROMPTS_JSON
    if not os.path.exists(prompts_path):
        # fall back to built-in short list
        prompts = [
            {"id": 0, "prompt": "a red apple",        "category": "nature"},
            {"id": 1, "prompt": "a blue circle",       "category": "geometric"},
            {"id": 2, "prompt": "a yellow star",       "category": "geometric"},
            {"id": 3, "prompt": "a green tree",        "category": "nature"},
            {"id": 4, "prompt": "a house with red roof","category": "icon"},
            {"id": 5, "prompt": "a rocket",            "category": "icon"},
            {"id": 6, "prompt": "a music note",        "category": "icon"},
            {"id": 7, "prompt": "a heart",             "category": "icon"},
        ]
        log.warning(f"Prompts file not found at {prompts_path}, using built-in list.")
    else:
        with open(prompts_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        prompts = data.get("prompts", data) if isinstance(data, dict) else data

    log.info(f"Running on {len(prompts)} prompts ...")

    # ── 4. generate + evaluate ───────────────────────────────────────────────
    results = []
    n_success = 0

    for entry in prompts:
        pid    = entry.get("id", len(results))
        prompt = entry["prompt"]
        cat    = entry.get("category", "")
        stem   = f"{pid:03d}_{re.sub(r'[^a-z0-9]+', '_', prompt.lower())[:40]}"

        log.info(f"[{pid+1}/{len(prompts)}] {prompt}")
        t0 = time.time()

        svg = generate_svg(prompt)
        elapsed = round(time.time() - t0, 1)

        if svg is None:
            log.warning(f"  → no valid SVG generated ({elapsed}s)")
            results.append({
                "id": pid, "prompt": prompt, "category": cat, "stem": stem,
                "clip": 0.0, "success": False, "error": "no_svg", "time_s": elapsed,
            })
            continue

        # Save
        save_svg_and_png(svg, stem)

        # CLIP
        score   = clip_score(svg, prompt)
        success = score >= cfg.CLIP_THRESHOLD
        if success:
            n_success += 1

        log.info(f"  → CLIP {score:.1f}  {'PASS' if success else 'FAIL'}  ({elapsed}s)")

        results.append({
            "id": pid, "prompt": prompt, "category": cat, "stem": stem,
            "clip": score, "success": success, "time_s": elapsed,
        })

        # Free GPU cache between prompts
        import torch
        torch.cuda.empty_cache()
        gc.collect()

    # ── 5. summary ───────────────────────────────────────────────────────────
    clips = [r["clip"] for r in results if r["clip"] > 0]
    summary = {
        "model": f"OmniSVG {cfg.MODEL_SIZE}",
        "n_total":   len(results),
        "n_success": n_success,
        "clip_mean": round(sum(clips) / len(clips), 3) if clips else 0.0,
        "clip_median": round(sorted(clips)[len(clips) // 2], 3) if clips else 0.0,
        "clip_std":  round((sum((c - sum(clips)/len(clips))**2 for c in clips)
                            / len(clips)) ** 0.5, 3) if clips else 0.0,
        "threshold": cfg.CLIP_THRESHOLD,
        "results": results,
    }

    with open(cfg.RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    html = build_html_gallery(results)
    with open(cfg.GALLERY_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    log.info("=" * 60)
    log.info(f"OmniSVG Evaluation Complete")
    log.info(f"  Model       : OmniSVG {cfg.MODEL_SIZE}")
    log.info(f"  Total       : {len(results)}")
    log.info(f"  Success     : {n_success} / {len(results)}"
             f" ({100*n_success//len(results) if results else 0}%)")
    log.info(f"  CLIP mean   : {summary['clip_mean']}")
    log.info(f"  Results JSON: {cfg.RESULTS_JSON}")
    log.info(f"  Gallery     : {cfg.GALLERY_HTML}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
