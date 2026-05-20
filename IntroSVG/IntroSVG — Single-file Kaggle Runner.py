"""
IntroSVG — Single-file Kaggle Runner
=====================================
Implements the full generate → critique → refine loop from:
  "IntroSVG: Learning from Rendering Feedback for Text-to-SVG Generation
   via an Introspective Generator-Critic Framework" (CVPR 2026)
   https://arxiv.org/abs/2603.09312

Model : gitcat404/IntroSVG-Qwen2.5-VL-7B (HuggingFace)
GPU   : Kaggle T4 (16 GB)

HOW TO RUN ON KAGGLE
---------------------
1. New notebook → Accelerator: GPU T4 x1
2. Settings → Secrets → add HF_TOKEN  (optional but removes rate-limit warnings)
3. Upload this file or paste its entire contents into one code cell
4. Run the cell — everything else is automatic

CUSTOMISE
---------
Edit the USER CONFIG section below (PROMPTS, MAX_ITERATIONS, etc.)
"""

# ═══════════════════════════════════════════════════════════════════════════
# 0.  INSTALL  (runs once; safe to re-run)
# ═══════════════════════════════════════════════════════════════════════════
import subprocess, sys

def _pip(*pkgs):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *pkgs])

# transformers ≥ 4.49 has Qwen2_5_VLForConditionalGeneration
_pip(
    "transformers>=4.49.0",
    "accelerate>=0.26.0",
    "bitsandbytes>=0.43.0",
    "qwen-vl-utils>=0.0.8",
    "cairosvg",
    "Pillow",
)

# ═══════════════════════════════════════════════════════════════════════════
# 1.  USER CONFIG  ← edit here
# ═══════════════════════════════════════════════════════════════════════════

MODEL_NAME      = "gitcat404/IntroSVG-Qwen2.5-VL-7B"
MAX_ITERATIONS  = 3       # max generate → critique → refine rounds per prompt
SCORE_THRESHOLD = 9.5     # stop early if critic gives score ≥ this
RENDER_SIZE     = 512     # PNG size sent to the critic (pixels)
OUTPUT_DIR      = "/kaggle/working/introsvg_output"

PROMPTS = [
    "a red apple with a green leaf",
    "a blue butterfly on a flower",
    "a golden star with sparkles",
    "a coffee cup with rising steam",
    "a crescent moon and three stars",
    "a house with a red roof and yellow windows",
    "a rocket launching into space",
    "a sunflower in a green field",
    "a colorful hot air balloon",
    "a crown decorated with jewels",
]

# ═══════════════════════════════════════════════════════════════════════════
# 2.  IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
import gc
import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("IntroSVG")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# 3.  PROMPT BUILDERS
#
#  Prompts match the training data format from gitcat404/IntroSVG-train.
#  The model has no system-role training — all instruction text lives in
#  the user message, exactly as the SFT data was constructed.
# ═══════════════════════════════════════════════════════════════════════════

def _gen_user_text(prompt: str) -> str:
    return f"Please generate an SVG icon that meets the following description: {prompt}"

def _critic_user_text(prompt: str) -> str:
    return (
        f'You are a professional SVG design critic. Please analyze the input '
        f'AI-generated SVG draft according to the "Original Design Prompt".\n\n'
        f'**Original Design Prompt**: "{prompt}"\n\n'
        f'Your task is to output a structured critique report, strictly following '
        f'the JSON format: {{"score": <0-10>, "critique": "<issues>", "suggestions": "<fixes>"}}'
    )

def _correction_user_text(prompt: str, svg: str, critique: Dict[str, Any]) -> str:
    return (
        f"Please analyze all the information provided below and generate a final, "
        f"high-quality SVG code.\n\n"
        f"The original design prompt was: {prompt}\n\n"
        f"A draft SVG code is:\n{svg}\n\n"
        f"An expert critique and suggestions of this draft is:\n"
        f"{json.dumps(critique, ensure_ascii=False)}"
    )

# ═══════════════════════════════════════════════════════════════════════════
# 4.  MODEL LOADING
#
#  8-bit LLM.int8() quantization on T4 16 GB:
#  • LLM weights ~7 GB at int8; vision encoder kept in fp16 via skip list
#  • Total VRAM ~9–10 GB — fits the T4 with headroom for KV cache
#  • 4-bit NF4 was used previously but destroys the fine-tuning signal;
#    the model card specifies BF16 / torch_dtype="auto" for correct inference
# ═══════════════════════════════════════════════════════════════════════════

def load_model(model_name: str):
    from transformers import (
        Qwen2_5_VLForConditionalGeneration,
        AutoProcessor,
        BitsAndBytesConfig,
    )

    hf_token = os.environ.get("HF_TOKEN") or None
    log.info(f"Loading {model_name}  (LLM int8, vision encoder skipped → fp16)")

    quant_cfg = BitsAndBytesConfig(
        load_in_8bit=True,
        llm_int8_skip_modules=["visual"],   # keeps ViT in fp16
    )

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name,
        quantization_config=quant_cfg,
        device_map="auto",
        token=hf_token,
    )
    model.eval()

    processor = AutoProcessor.from_pretrained(model_name, token=hf_token)

    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / 1e9
        log.info(f"Model loaded. VRAM used: {alloc:.1f} GB")
    else:
        log.info("Model loaded (CPU mode — inference will be slow).")

    return model, processor


# Lazy singleton — loaded once, reused for all three roles
_model = _processor = None

def get_model():
    global _model, _processor
    if _model is None:
        _model, _processor = load_model(MODEL_NAME)
    return _model, _processor


# ═══════════════════════════════════════════════════════════════════════════
# 5.  SVG UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def render_svg(svg_code: str, size: int = 512) -> Optional[Image.Image]:
    """Render SVG → PIL Image via cairosvg. Returns None on failure."""
    try:
        import cairosvg
    except ImportError:
        log.error("cairosvg not installed — run: pip install cairosvg")
        return None
    svg_code = _fix_svg(svg_code)
    try:
        png = cairosvg.svg2png(
            bytestring=svg_code.encode("utf-8"),
            output_width=size,
            output_height=size,
        )
        return Image.open(io.BytesIO(png)).convert("RGB")
    except Exception as e:
        log.debug(f"render_svg failed: {e}")
        return None


def is_renderable(svg_code: str) -> bool:
    return render_svg(svg_code, size=64) is not None


def _fix_svg(code: str) -> str:
    """Ensure <svg> has xmlns and </svg> tail."""
    code = code.strip()
    if not code.lower().startswith("<svg"):
        m = re.search(r"<svg[\s>]", code, re.IGNORECASE)
        code = code[m.start():] if m else (
            '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n'
            + code + "\n</svg>"
        )
    if "xmlns=" not in code:
        code = code.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    if not code.rstrip().endswith("</svg>"):
        code = code.rstrip()
        code += "\n</svg>" if code.endswith(">") else '"/>\n</svg>'
    return code


def _extract_svg(text: str) -> Optional[str]:
    """Pull SVG out of raw model output (strips markdown fences etc.)."""
    if not text:
        return None
    text = text.strip()
    m = re.search(r"```(?:svg|xml|html)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    m = re.search(r"(<svg[\s>].*?</svg>)", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    if "<svg" in text.lower():
        idx = text.lower().find("<svg")
        return _fix_svg(text[idx:])
    return None


def _parse_critique(text: str) -> Dict[str, Any]:
    """Parse JSON critique from model output."""
    if not text:
        return {"score": 5, "critique": "", "suggestions": ""}
    text = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            p = json.loads(m.group(0))
            return {
                "score":       int(float(p.get("score", 5))),
                "critique":    str(p.get("critique", "")),
                "suggestions": str(p.get("suggestions", "")),
            }
        except (json.JSONDecodeError, ValueError):
            pass
    log.warning(f"Could not parse critique JSON from: {text[:120]!r}")
    return {"score": 5, "critique": text[:200], "suggestions": ""}


# ═══════════════════════════════════════════════════════════════════════════
# 6.  INFERENCE  (three roles using the same model)
# ═══════════════════════════════════════════════════════════════════════════

def _generate_text(
    messages: list,
    temperature: float = 0.5,
    max_new_tokens: int = 2048,
) -> Optional[str]:
    """Text-only forward pass (Generator and Corrector roles)."""
    model, processor = get_model()
    device = next(model.parameters()).device

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = processor(text=[text], return_tensors="pt").to(device)

    gen_kwargs: Dict[str, Any] = dict(
        max_new_tokens=max_new_tokens,
        repetition_penalty=1.3,
        pad_token_id=processor.tokenizer.eos_token_id,
    )
    if temperature > 0:
        gen_kwargs.update(do_sample=True, temperature=temperature, top_p=0.9)
    else:
        gen_kwargs["do_sample"] = False

    with torch.inference_mode():
        out_ids = model.generate(**inputs, **gen_kwargs)

    n_in = inputs["input_ids"].shape[1]
    return processor.tokenizer.decode(out_ids[0][n_in:], skip_special_tokens=True).strip()


def _generate_vision(
    messages: list,
    max_new_tokens: int = 512,
) -> Optional[str]:
    """Vision + text forward pass (Critic role — greedy, temperature=0)."""
    try:
        from qwen_vl_utils import process_vision_info
    except ImportError:
        log.error("qwen-vl-utils missing — pip install qwen-vl-utils")
        return None

    model, processor = get_model()
    device = next(model.parameters()).device

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        return_tensors="pt",
    ).to(device)

    with torch.inference_mode():
        out_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,                        # greedy — no temperature
            repetition_penalty=1.3,
            pad_token_id=processor.tokenizer.eos_token_id,
        )

    n_in = inputs["input_ids"].shape[1]
    return processor.tokenizer.decode(out_ids[0][n_in:], skip_special_tokens=True).strip()


# ── Three role wrappers ─────────────────────────────────────────────────────

def generate_svg(prompt: str) -> Optional[str]:
    """Generator: text → SVG (temperature 0.5, matches training prompt format)."""
    raw = _generate_text(
        messages=[
            {"role": "user", "content": _gen_user_text(prompt)},
        ],
        temperature=0.5,
        max_new_tokens=2048,
    )
    return _extract_svg(raw)


def critique_svg(prompt: str, rendered: Image.Image) -> Dict[str, Any]:
    """Critic: rendered image + prompt → JSON score/critique (greedy, matches training)."""
    raw = _generate_vision(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": rendered},
                    {"type": "text", "text": _critic_user_text(prompt)},
                ],
            },
        ],
        max_new_tokens=512,
    )
    return _parse_critique(raw)


def correct_svg(
    prompt: str, flawed_svg: str, critique: Dict[str, Any]
) -> Optional[str]:
    """Corrector: prompt + flawed SVG + critique → improved SVG (greedy, matches training)."""
    raw = _generate_text(
        messages=[
            {"role": "user", "content": _correction_user_text(prompt, flawed_svg, critique)},
        ],
        temperature=0.0,
        max_new_tokens=2048,
    )
    return _extract_svg(raw)


# ═══════════════════════════════════════════════════════════════════════════
# 7.  INFERENCE LOOP
# ═══════════════════════════════════════════════════════════════════════════

def run_introsvg(
    prompt: str,
    max_iterations: int = MAX_ITERATIONS,
    score_threshold: float = SCORE_THRESHOLD,
    render_size: int = RENDER_SIZE,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Generate → Render → Critique → Refine loop for one prompt.

    Stops when critique score ≥ score_threshold OR max_iterations reached.
    Returns dict with final svg, score, iterations, success, history.
    """
    history = []
    current_svg: Optional[str] = None
    current_score: float = 0.0
    critique: Optional[Dict] = None

    for iteration in range(1, max_iterations + 1):
        if verbose:
            log.info(f"  ── Iter {iteration}/{max_iterations} ───────────────")

        # ── Generate / Correct ────────────────────────────────────────────
        if iteration == 1 or current_svg is None:
            if verbose:
                log.info("  [GEN] Generating SVG…")
            svg = generate_svg(prompt)
        else:
            if verbose:
                log.info("  [COR] Correcting SVG…")
            svg = correct_svg(prompt, current_svg, critique)

        if svg is None:
            log.warning(f"  Generation returned None (iter {iteration})")
            history.append({"iteration": iteration, "svg": None,
                            "rendered": False, "score": 0.0, "critique": None})
            break

        # ── Render ───────────────────────────────────────────────────────
        rendered_image = render_svg(svg, size=render_size)
        rendered_ok = rendered_image is not None
        if verbose:
            log.info(f"  [RND] {'OK' if rendered_ok else 'FAILED'}")

        if not rendered_ok:
            critique = {
                "score": 0,
                "critique": "SVG failed to render — likely has syntax errors.",
                "suggestions": (
                    'Fix syntax errors. Must start with <svg viewBox="0 0 200 200" '
                    'xmlns="http://www.w3.org/2000/svg"> and end with </svg>. '
                    "Use only <path> with M, L, C, A, Z commands."
                ),
            }
            current_svg, current_score = svg, 0.0
            history.append({"iteration": iteration, "svg": svg,
                            "rendered": False, "score": 0.0, "critique": critique})
            if iteration < max_iterations:
                continue
            break

        # ── Critique ─────────────────────────────────────────────────────
        if verbose:
            log.info("  [CRI] Critiquing…")
        critique = critique_svg(prompt, rendered_image)
        score = float(critique.get("score", 0))
        current_svg, current_score = svg, score

        if verbose:
            log.info(f"  [SCR] Score {score:.1f}/10 — {critique.get('critique','')[:80]}")

        history.append({"iteration": iteration, "svg": svg,
                        "rendered": True, "score": score, "critique": critique})

        # ── Early stop ────────────────────────────────────────────────────
        if score >= score_threshold:
            if verbose:
                log.info(f"  ✓ Score ≥ {score_threshold}, stopping early.")
            break

    success = current_svg is not None and is_renderable(current_svg)
    return {
        "prompt":     prompt,
        "svg":        current_svg or "",
        "score":      current_score,
        "iterations": len(history),
        "success":    success,
        "history":    history,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 8.  DISPLAY & SAVE
# ═══════════════════════════════════════════════════════════════════════════

def _pil_to_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def display_result(result: Dict[str, Any]) -> None:
    """Show the SVG inline in a Kaggle / Jupyter notebook."""
    prompt = result["prompt"]
    svg    = result["svg"]
    score  = result["score"]
    iters  = result["iterations"]
    ok     = result["success"]

    print(f"\n{'─'*60}")
    print(f"Prompt : {prompt}")
    print(f"Score  : {score:.1f}/10  |  Iterations: {iters}  |  Renderable: {ok}")

    if not svg:
        print("  (no SVG generated)")
        return

    try:
        from IPython.display import display as ipy, SVG as IPySVG, Image as IPyImg, HTML
        fixed = _fix_svg(svg)
        try:
            ipy(IPySVG(fixed))
        except Exception:
            img = render_svg(svg, size=400)
            if img:
                ipy(IPyImg(data=_pil_to_png(img), format="png"))
            else:
                ipy(HTML("<pre style='color:red'>Could not render SVG</pre>"))
    except ImportError:
        print(f"  SVG length: {len(svg)} chars")


def save_result(result: Dict[str, Any], out_dir: str) -> str:
    """Save final SVG to disk and return the path."""
    svg = result.get("svg", "")
    if not svg:
        return ""
    slug = re.sub(r"[^\w]+", "_", result["prompt"].lower())[:50].strip("_")
    path = Path(out_dir) / f"{slug}.svg"
    path.write_text(_fix_svg(svg), encoding="utf-8")
    return str(path)


def build_gallery_html(results: List[Dict], out_dir: str) -> str:
    """Generate a side-by-side HTML gallery of all SVGs."""
    cards = []
    for r in results:
        if not r.get("svg"):
            continue
        fixed = _fix_svg(r["svg"])
        card = (
            '<div style="border:1px solid #ccc;border-radius:8px;padding:12px;'
            'width:220px;text-align:center;font-family:sans-serif;display:inline-block;margin:8px">'
            f'<div style="width:200px;height:200px;overflow:hidden">{fixed}</div>'
            f'<p style="font-size:12px;margin:6px 0 2px"><b>{r["prompt"]}</b></p>'
            f'<p style="font-size:11px;color:#666">Score: {r["score"]:.1f}/10 | Iters: {r["iterations"]}</p>'
            "</div>"
        )
        cards.append(card)

    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>IntroSVG Gallery</title></head><body>"
        '<h2 style="font-family:sans-serif">IntroSVG Gallery</h2>'
        '<div style="padding:16px">' + "".join(cards) + "</div>"
        "</body></html>"
    )
    p = Path(out_dir) / "gallery.html"
    p.write_text(html, encoding="utf-8")
    return str(p)


# ═══════════════════════════════════════════════════════════════════════════
# 9.  RUN ALL
# ═══════════════════════════════════════════════════════════════════════════

def run_all(
    prompts: List[str] = PROMPTS,
    output_dir: str = OUTPUT_DIR,
    max_iterations: int = MAX_ITERATIONS,
    score_threshold: float = SCORE_THRESHOLD,
    render_size: int = RENDER_SIZE,
) -> List[Dict]:
    """
    Process every prompt through the IntroSVG loop.
    Displays each result inline, saves SVG files and a gallery.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = []

    log.info(f"Running {len(prompts)} prompts → {output_dir}")
    log.info(f"max_iters={max_iterations}, stop_score={score_threshold}")

    for i, prompt in enumerate(prompts):
        log.info(f"\n{'='*60}")
        log.info(f"[{i+1}/{len(prompts)}] {prompt!r}")

        result = run_introsvg(
            prompt=prompt,
            max_iterations=max_iterations,
            score_threshold=score_threshold,
            render_size=render_size,
            verbose=True,
        )
        results.append(result)
        display_result(result)

        saved = save_result(result, output_dir)
        if saved:
            log.info(f"  Saved → {saved}")

    # ── Summary ───────────────────────────────────────────────────────────
    n_ok    = sum(1 for r in results if r["success"])
    n_total = len(results)
    mean_sc = sum(r["score"]      for r in results) / n_total if n_total else 0
    mean_it = sum(r["iterations"] for r in results) / n_total if n_total else 0

    print(f"\n{'═'*60}")
    print("SUMMARY")
    print(f"{'═'*60}")
    print(f"  Total    : {n_total}")
    print(f"  Success  : {n_ok}/{n_total}  ({n_ok/n_total:.0%})")
    print(f"  Avg score: {mean_sc:.2f}/10")
    print(f"  Avg iters: {mean_it:.2f}")

    gallery = build_gallery_html(results, output_dir)
    print(f"  Gallery  : {gallery}")

    jsonl = Path(output_dir) / "results.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({k: v for k, v in r.items() if k != "history"},
                               ensure_ascii=False) + "\n")
    print(f"  JSONL    : {jsonl}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# 10. ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_all()