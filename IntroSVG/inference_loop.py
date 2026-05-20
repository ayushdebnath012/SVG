"""
IntroSVG — Official Inference Loop
====================================
Matches the official repo interface:

    python inference_loop.py \
        --MODEL_NAME Models/IntroSVG-Qwen2.5-VL-7B \
        --CSV_FILE example/test.csv \
        --OUTPUT_DIR your_output_folder

CSV must have a 'prompt' column (or the first column is used).

────────────────────────────────────────────────────────────────
4-GPU production (lmdeploy server — recommended):

    lmdeploy serve api_server Models/IntroSVG-Qwen2.5-VL-7B \\
        --tp 4 --server-port 23333

    python inference_loop.py \\
        --MODEL_NAME IntroSVG-Qwen2.5-VL-7B \\
        --BASE_URL   http://localhost:23333/v1 \\
        --CSV_FILE   example/test.csv \\
        --OUTPUT_DIR results/

Single GPU (no server, 8-bit quantized transformers):

    python inference_loop.py \\
        --MODEL_NAME Models/IntroSVG-Qwen2.5-VL-7B \\
        --CSV_FILE   example/test.csv \\
        --OUTPUT_DIR results/
────────────────────────────────────────────────────────────────
"""

import argparse
import base64
import csv
import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

log = logging.getLogger("inference")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

N_MAX = 3      # max refinement iterations (paper: N_max = 3)
TAU   = 9.5    # score threshold to stop early (paper: τ = 9.5)


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders — must match training data format exactly
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Backend: lmdeploy / vLLM OpenAI-compatible server (official approach)
# ─────────────────────────────────────────────────────────────────────────────

class LMDeployBackend:
    """Sends requests to a running lmdeploy or vLLM OpenAI-compatible server."""

    def __init__(self, model_name: str, base_url: str):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key="EMPTY")
        self.model  = model_name
        log.info(f"LMDeploy backend: model={model_name}  url={base_url}")

    def generate_text(
        self,
        user_text: str,
        max_new_tokens: int = 2048,
        temperature: float  = 0.5,
        do_sample: bool     = True,
    ) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": user_text}],
            max_tokens=max_new_tokens,
            temperature=temperature if do_sample else 0.0,
        )
        return resp.choices[0].message.content or ""

    def generate_vision(
        self,
        user_text: str,
        png_bytes: bytes,
        max_new_tokens: int = 512,
    ) -> str:
        b64 = base64.b64encode(png_bytes).decode()
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "low"}},
                    {"type": "text", "text": user_text},
                ],
            }],
            max_tokens=max_new_tokens,
            temperature=0.0,
        )
        return resp.choices[0].message.content or ""


# ─────────────────────────────────────────────────────────────────────────────
# Backend: transformers (single-GPU fallback, 8-bit quantized)
# ─────────────────────────────────────────────────────────────────────────────

class TransformersBackend:
    """Single-GPU 8-bit quantized fallback — no server required."""

    def __init__(self, model_name: str):
        import torch
        from transformers import (
            Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig,
        )

        log.info(f"Loading model (8-bit): {model_name}")
        quant = BitsAndBytesConfig(load_in_8bit=True, llm_int8_skip_modules=["visual"])
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_name, quantization_config=quant, device_map="auto",
        )
        self.model.eval()
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.device = next(self.model.parameters()).device

    def _run(self, messages, images=None, max_new_tokens=2048,
             temperature=0.5, do_sample=True) -> str:
        import torch

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        inputs = self.processor(
            text=[text], images=images, return_tensors="pt",
        ).to(self.device)

        gen_kwargs: Dict[str, Any] = dict(
            max_new_tokens=max_new_tokens,
            repetition_penalty=1.3,
            pad_token_id=self.processor.tokenizer.eos_token_id,
        )
        if do_sample:
            gen_kwargs.update(do_sample=True, temperature=temperature, top_p=0.95)
        else:
            gen_kwargs.update(do_sample=False)

        with torch.inference_mode():
            ids = self.model.generate(**inputs, **gen_kwargs)
        n   = inputs["input_ids"].shape[1]
        return self.processor.tokenizer.decode(ids[0][n:], skip_special_tokens=True).strip()

    def generate_text(self, user_text: str, max_new_tokens=2048,
                      temperature=0.5, do_sample=True) -> str:
        messages = [{"role": "user", "content": user_text}]
        return self._run(messages, images=None,
                         max_new_tokens=max_new_tokens,
                         temperature=temperature, do_sample=do_sample)

    def generate_vision(self, user_text: str, png_bytes: bytes,
                        max_new_tokens=512) -> str:
        from PIL import Image
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        messages = [{"role": "user", "content": [
            {"type": "image"},
            {"type": "text", "text": user_text},
        ]}]
        return self._run(messages, images=[img],
                         max_new_tokens=max_new_tokens,
                         temperature=1.0, do_sample=False)


# ─────────────────────────────────────────────────────────────────────────────
# Inference helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_svg(text: str) -> Optional[str]:
    m = re.search(r'(<svg[\s>].*?</svg>)', text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else None


def _parse_critique(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r'\{.*?\}', text, re.DOTALL)
    if not m:
        return None
    try:
        parsed = json.loads(m.group(0))
        return {
            "score":       int(float(parsed.get("score", 5))),
            "critique":    str(parsed.get("critique", "")),
            "suggestions": str(parsed.get("suggestions", "")),
        }
    except (json.JSONDecodeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main inference loop (§4.3 of the paper)
# ─────────────────────────────────────────────────────────────────────────────

def run_inference_loop(
    prompt: str,
    backend,
    n_max: int  = N_MAX,
    tau: float  = TAU,
) -> Tuple[str, int, float]:
    """
    Generate → Critique → Correct loop.
    Returns (final_svg, iterations_used, final_score).
    """
    from svg_utils import render_to_png, standardize_svg

    # Initial generation
    raw = backend.generate_text(_gen_user_text(prompt), max_new_tokens=2048,
                                temperature=0.5, do_sample=True)
    svg = _extract_svg(raw)
    if svg is None:
        log.warning(f"  No SVG found in initial generation for: {prompt[:60]}")
        return "", 0, 0.0
    svg = standardize_svg(svg) or svg

    score = 0.0
    for iteration in range(1, n_max + 1):
        png = render_to_png(svg, size=224)
        if png is None:
            log.warning(f"  SVG not renderable at iteration {iteration}")
            break

        # Critique
        crit_raw = backend.generate_vision(
            _critic_user_text(prompt), png, max_new_tokens=256,
        )
        critique = _parse_critique(crit_raw)
        if critique is None:
            log.warning(f"  Could not parse critique at iteration {iteration}: {crit_raw[:80]}")
            break

        score = float(critique["score"])
        log.info(f"    iter={iteration}  score={score}  critique={critique['critique'][:60]}")

        if score >= tau or iteration == n_max:
            break

        # Correct
        corr_raw = backend.generate_text(
            _correction_user_text(prompt, svg, critique),
            max_new_tokens=2048, temperature=0.0, do_sample=False,
        )
        new_svg = _extract_svg(corr_raw)
        if new_svg:
            svg = standardize_svg(new_svg) or new_svg

    return svg or "", iteration, score


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main(args):
    out_dir = Path(args.OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pick backend
    base_url = args.BASE_URL or os.environ.get("LMDEPLOY_BASE_URL", "")
    if base_url:
        backend = LMDeployBackend(args.MODEL_NAME, base_url)
    else:
        backend = TransformersBackend(args.MODEL_NAME)

    # Read prompts from CSV
    prompts = []
    with open(args.CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        col = "prompt" if "prompt" in fields else (fields[0] if fields else None)
        if col is None:
            raise ValueError("CSV has no columns")
        for row in reader:
            p = row[col].strip()
            if p:
                prompts.append(p)
    log.info(f"Loaded {len(prompts)} prompts from '{args.CSV_FILE}' (column: '{col}')")

    # Run inference loop for each prompt
    results = []
    for i, prompt in enumerate(prompts):
        log.info(f"[{i+1}/{len(prompts)}] {prompt[:70]}")
        svg, iters, score = run_inference_loop(
            prompt, backend, n_max=args.n_max, tau=args.tau,
        )
        stem     = re.sub(r'[^\w\-]+', '_', prompt[:50]).strip('_') or f"sample_{i:04d}"
        svg_path = out_dir / f"{i:04d}_{stem}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        results.append({
            "prompt":     prompt,
            "svg_file":   str(svg_path),
            "iterations": iters,
            "score":      score,
        })
        log.info(f"  → score={score:.1f}  iters={iters}  file={svg_path.name}")

    # Write summary
    summary = out_dir / "results.jsonl"
    with open(summary, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log.info(f"Done. {len(results)} SVGs → {out_dir}   summary → {summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IntroSVG inference loop")
    parser.add_argument("--MODEL_NAME", required=True,
                        help="Local model path or model name for lmdeploy server")
    parser.add_argument("--CSV_FILE",   required=True,
                        help="CSV file with a 'prompt' column")
    parser.add_argument("--OUTPUT_DIR", required=True,
                        help="Directory to write output SVGs and results.jsonl")
    parser.add_argument("--BASE_URL",   default="",
                        help="lmdeploy/vLLM base URL (e.g. http://localhost:23333/v1). "
                             "Omit to use local transformers backend.")
    parser.add_argument("--n-max",  type=int,   default=N_MAX,
                        help=f"Max refinement iterations (default: {N_MAX})")
    parser.add_argument("--tau",    type=float, default=TAU,
                        help=f"Score threshold for early stopping (default: {TAU})")
    args = parser.parse_args()
    main(args)
