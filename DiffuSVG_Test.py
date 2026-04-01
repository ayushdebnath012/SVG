#!/usr/bin/env python3
"""
DiffuSVG_Test.py
================
Test the fine-tuned Qwen2VL LoRA adapter from DiffuSVG_Dataset_Finetune.py.

Usage (Kaggle / Colab with GPU):
    # 1. Unzip the adapter
    import zipfile
    with zipfile.ZipFile("tractor_svg_lora.zip") as z:
        z.extractall("tractor_svg_lora")

    # 2. Run
    python DiffuSVG_Test.py --adapter tractor_svg_lora/final_adapter --prompt "a red apple"

Usage (CPU, slow):
    python DiffuSVG_Test.py --adapter ./final_adapter --prompt "a sun" --device cpu
"""

import argparse
import re
import sys
from pathlib import Path


SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Given a text description, output ONLY valid SVG code. "
    "Rules:\n"
    '- Start with: <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n'
    '- Use simple shapes: <rect>, <circle>, <ellipse>, <polygon>, <path>\n'
    '- Use solid hex fill colours (e.g., fill="#FF0000")\n'
    "- Keep it minimal: 5-20 elements\n- End with: </svg>\n"
    "Output the SVG code directly, no explanation."
)


def load_model(adapter_path: str, device: str, load_in_4bit: bool):
    import torch
    from transformers import AutoTokenizer, Qwen2VLForConditionalGeneration, BitsAndBytesConfig
    from peft import PeftModel

    print(f"Loading base model + adapter from {adapter_path} ...")
    tok = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)

    quant = None
    if load_in_4bit and device != "cpu":
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )

    # The adapter folder contains both base-model config and LoRA weights.
    # If save_pretrained was called on the PEFT model, load it directly.
    try:
        from peft import AutoPeftModelForCausalLM
        model = AutoPeftModelForCausalLM.from_pretrained(
            adapter_path,
            quantization_config=quant,
            device_map=device if device != "cpu" else None,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            trust_remote_code=True,
        )
        print("Loaded via AutoPeftModelForCausalLM.")
    except Exception:
        # Fallback: load base model then attach adapter
        base = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2-VL-2B-Instruct",
            quantization_config=quant,
            device_map=device if device != "cpu" else None,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            trust_remote_code=True,
        )
        model = PeftModel.from_pretrained(base, adapter_path)
        print("Loaded via base + PeftModel.from_pretrained.")

    model.eval()
    return model, tok


def generate_svg(model, tok, prompt: str, device: str,
                 max_new_tokens: int = 800, temperature: float = 0.7) -> str:
    import torch

    messages = [
        {"role": "system",    "content": SYSTEM_PROMPT},
        {"role": "user",      "content": f"Generate SVG for: {prompt}"},
    ]
    text = tok.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tok(text, return_tensors="pt")
    if device != "cpu":
        inputs = {k: v.cuda() for k, v in inputs.items()}

    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tok.eos_token_id,
        )

    new_tokens = out[0][inputs["input_ids"].shape[1]:]
    return tok.decode(new_tokens, skip_special_tokens=True).strip()


def extract_svg(raw: str) -> str | None:
    """Pull <svg ...>...</svg> out of raw model output."""
    m = re.search(r'(<svg[\s\S]*?</svg>)', raw, re.IGNORECASE)
    return m.group(1).strip() if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter",        required=True,
                    help="Path to the adapter folder (unzipped tractor_svg_lora/final_adapter)")
    ap.add_argument("--prompt",         default="a red tractor",
                    help="Text prompt to generate SVG for")
    ap.add_argument("--prompts_file",   default="",
                    help="Optional .txt file with one prompt per line (overrides --prompt)")
    ap.add_argument("--output_dir",     default="./test_outputs")
    ap.add_argument("--device",         default="cuda",
                    help="'cuda' (default) or 'cpu'")
    ap.add_argument("--no_4bit",        action="store_true",
                    help="Disable 4-bit quantisation (needed on CPU or without bitsandbytes)")
    ap.add_argument("--max_new_tokens", type=int, default=800)
    ap.add_argument("--temperature",    type=float, default=0.7)
    args = ap.parse_args()

    load_in_4bit = not args.no_4bit and args.device != "cpu"
    model, tok = load_model(args.adapter, args.device, load_in_4bit)

    # Build prompt list
    if args.prompts_file and Path(args.prompts_file).exists():
        prompts = [l.strip() for l in open(args.prompts_file) if l.strip()]
    else:
        prompts = [args.prompt]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, prompt in enumerate(prompts):
        print(f"\n[{i+1}/{len(prompts)}] Prompt: {prompt}")
        raw = generate_svg(model, tok, prompt, args.device,
                           args.max_new_tokens, args.temperature)
        svg = extract_svg(raw)

        if svg:
            slug = re.sub(r'[^\w]+', '_', prompt)[:40]
            svg_path = out_dir / f"{i:03d}_{slug}.svg"
            svg_path.write_text(svg, encoding="utf-8")
            print(f"  Saved: {svg_path}")
            print(f"  Preview (first 200 chars): {svg[:200]}")
        else:
            print(f"  WARNING: no <svg> found in output.")
            print(f"  Raw output: {raw[:300]}")
            (out_dir / f"{i:03d}_raw.txt").write_text(raw, encoding="utf-8")

    print(f"\nDone. SVGs written to {out_dir}/")


if __name__ == "__main__":
    main()
