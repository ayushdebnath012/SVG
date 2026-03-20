#!/usr/bin/env python3
"""
dataset_pipeline.py — Hard-failure dataset builder for Qwen2VL fine-tuning
===========================================================================

The dataset consists of prompts that gave BAD results in the main pipeline
(Qwen2VL failed to produce valid/good SVGs for them).

For each such prompt we generate a BETTER SVG via:
    SD 3.5 Medium  →  Potrace + ImageMagick  →  clean SVG

These (bad-prompt, good-svg) pairs become the fine-tuning dataset so
Qwen2VL learns to handle the hard cases.

Full workflow
─────────────
1. Run DiffuSVG_v4.ipynb  →  results.json   (contains per-prompt scores)
2. Run this script          →  dataset.jsonl  (hard-prompt → potrace SVG pairs)
3. Run finetune_qwen2vl.py  →  fine-tuned adapter

Failure criteria (configurable):
  - success == False  (SVG extraction / validation failed)
  - CLIP score  < clip_threshold   (default 24.0)
  - DINO score  < dino_threshold   (default 0.35)

Requirements:
    pip install diffusers transformers accelerate torch pillow tqdm
    System: potrace  (+ imagemagick for --colour mode)

Usage:
    # Mine bad prompts from results.json, build corrective dataset
    python dataset_pipeline.py \\
        --results results.json \\
        --output_dir ./dataset \\
        --hf_token YOUR_HF_TOKEN

    # Override thresholds
    python dataset_pipeline.py \\
        --results results.json \\
        --clip_threshold 26 --dino_threshold 0.40 \\
        --output_dir ./dataset --hf_token YOUR_HF_TOKEN

    # Dry-run (no GPU — checks Potrace is installed)
    python dataset_pipeline.py --dry_run
"""

import csv
import gc
import io
import json
import logging
import os
import random
import re
from pathlib import Path
from typing import List, Optional, Tuple

import torch
from PIL import Image, ImageDraw
from tqdm import tqdm

from vectorize import ColourVectorizer, Vectorizer, is_good_svg

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Diffusion loader
# ---------------------------------------------------------------------------

SVG_STYLE = {
    "low":    "simple vector art, ",
    "medium": "flat vector illustration, minimal design, clean shapes, ",
    "high":   "ultra-simple flat vector, geometric shapes only, solid colors, icon style, minimalist, ",
}

NEG_PROMPT = (
    "gradient, shadow, texture, 3d, realistic, photograph, "
    "complex details, noise, grain, watermark"
)


def load_sd35(hf_token: str, simplification: str = "high"):
    """Load SD 3.5 Medium and return a generate_image() callable."""
    from diffusers import StableDiffusion3Pipeline

    logger.info("Loading SD 3.5 Medium…")
    pipe = StableDiffusion3Pipeline.from_pretrained(
        "stabilityai/stable-diffusion-3.5-medium",
        torch_dtype=torch.float16,
        token=hf_token,
    )
    pipe.enable_model_cpu_offload()
    logger.info("SD 3.5 Medium loaded (CPU-offloaded)")

    style_prefix = SVG_STYLE.get(simplification, SVG_STYLE["high"])

    @torch.inference_mode()
    def generate_image(
        prompt: str,
        seed: Optional[int] = None,
        steps: int = 30,
        guidance: float = 5.0,
    ) -> Image.Image:
        gen = torch.Generator("cuda").manual_seed(seed) if seed is not None else None
        return pipe(
            style_prefix + prompt,
            negative_prompt=NEG_PROMPT,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=gen,
        ).images[0]

    return generate_image


# ---------------------------------------------------------------------------
# Failure mining
# ---------------------------------------------------------------------------

def mine_bad_prompts(
    results_path: str,
    clip_threshold: float = 24.0,
    dino_threshold: float = 0.35,
) -> Tuple[List[str], dict]:
    """
    Read results.json (or results.csv) and return prompts that failed.

    A result is "bad" if ANY of:
      - success is False
      - CLIP score < clip_threshold
      - DINO score < dino_threshold

    Returns:
        prompts  : list of bad prompt strings
        breakdown: dict with counts per failure reason
    """
    path = Path(results_path)

    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Support both plain list and {"results": [...]} format
        records = data["results"] if isinstance(data, dict) else data

    elif path.suffix == ".csv":
        with open(path, encoding="utf-8", newline="") as f:
            records = list(csv.DictReader(f))
        # CSV stores booleans as strings and numbers as strings
        for r in records:
            r["success"] = r.get("success", "True").lower() in ("true", "1", "yes")
            r["clip"]    = float(r.get("clip", 0) or 0)
            r["dino"]    = float(r.get("dino", 0) or 0)

    else:
        raise ValueError(f"Unsupported results file format: {path.suffix} (use .json or .csv)")

    bad_prompts = []
    breakdown = {"failed": 0, "low_clip": 0, "low_dino": 0, "total": len(records)}

    for r in records:
        prompt = r["prompt"]
        bad = False

        if not r.get("success", True):
            breakdown["failed"] += 1
            bad = True

        if float(r.get("clip", 0)) < clip_threshold:
            if r.get("success", True):  # don't double-count outright failures
                breakdown["low_clip"] += 1
            bad = True

        if float(r.get("dino", 0)) < dino_threshold:
            if r.get("success", True) and float(r.get("clip", 0)) >= clip_threshold:
                breakdown["low_dino"] += 1
            bad = True

        if bad:
            bad_prompts.append(prompt)

    breakdown["bad_total"] = len(bad_prompts)
    return bad_prompts, breakdown


# ---------------------------------------------------------------------------
# VLM quality filter  (whiteboard: Qwen2VL → Y / X decision on each SVG)
# ---------------------------------------------------------------------------

JUDGE_PROMPT = (
    "This is a black vector silhouette traced from an image. "
    "Does the overall shape or outline resemble \"{prompt}\"? "
    "Be lenient — silhouettes lack colour and detail. "
    "Reply with exactly one word: YES or NO."
)


class VLMQualityFilter:
    """
    Uses Qwen2VL to judge whether a Potrace SVG accurately represents the prompt.

    Matches the whiteboard: Qwen2VL acts as the Y/X gatekeeper before SVGs
    enter the (Text Prompt | SVG) training table.

    Accepts a pre-loaded model + processor (e.g. already in GPU memory from the
    notebook), or lazy-loads them itself when model=None.
    """

    def __init__(
        self,
        model=None,
        processor=None,
        model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
        load_in_4bit: bool = True,
        device: str = "cuda",
        render_size: int = 256,
    ):
        self._model = model
        self._processor = processor
        self.model_name = model_name
        self.load_in_4bit = load_in_4bit
        self.device = device
        self.render_size = render_size
        self._owns_model = model is None  # True → we loaded it, we manage it

    # ------------------------------------------------------------------

    def _ensure_loaded(self):
        if self._model is not None:
            return

        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

        logger.info(f"Loading Qwen2VL for quality filtering: {self.model_name}")
        quant = None
        if self.load_in_4bit:
            quant = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
            )
        self._model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_name,
            quantization_config=quant,
            device_map="auto",
            torch_dtype=torch.float16 if quant is None else None,
        )
        self._processor = AutoProcessor.from_pretrained(self.model_name)
        logger.info("Qwen2VL quality filter loaded")

    def _render_svg(self, svg: str) -> Optional[Image.Image]:
        """Render SVG string → PIL Image using cairosvg."""
        try:
            import cairosvg
            png = cairosvg.svg2png(
                bytestring=svg.encode(),
                output_width=self.render_size,
                output_height=self.render_size,
            )
            return Image.open(io.BytesIO(png)).convert("RGB")
        except Exception as e:
            logger.warning(f"SVG render failed: {e}")
            return None

    def is_good(self, svg: str, prompt: str) -> bool:
        """
        Returns True if Qwen2VL judges the SVG as a good match for the prompt.

        Steps:
          1. Render SVG → PIL image
          2. Send (image, prompt) to Qwen2VL with a YES/NO question
          3. Parse answer — YES → keep (Y), NO → discard (X)
        """
        rendered = self._render_svg(svg)
        if rendered is None:
            return False

        self._ensure_loaded()

        question = JUDGE_PROMPT.format(prompt=prompt)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": rendered},
                {"type": "text",  "text": question},
            ],
        }]

        try:
            text = self._processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self._processor(
                text=[text], images=[rendered], return_tensors="pt"
            ).to(self.device)

            with torch.inference_mode():
                out_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=5,   # only need YES/NO
                    do_sample=False,
                )

            generated = out_ids[0][inputs["input_ids"].shape[1]:]
            answer = self._processor.decode(generated, skip_special_tokens=True).strip().upper()
            logger.debug(f"VLM judge for '{prompt}': {answer!r}")
            return answer.startswith("YES")

        except Exception as e:
            logger.warning(f"VLM quality check error for '{prompt}': {e} — defaulting to PASS")
            return True   # on error, don't silently discard

    def move_to_cpu(self):
        """Offload to CPU to free VRAM for SD3.5-M (mirrors notebook pattern)."""
        if self._model is not None:
            self._model.to("cpu")
            torch.cuda.empty_cache()
            gc.collect()

    def move_to_gpu(self):
        """Move back to GPU before judging."""
        if self._model is not None:
            self._model.to(self.device)
            torch.cuda.empty_cache()


# ---------------------------------------------------------------------------
# Dataset pipeline
# ---------------------------------------------------------------------------

class DatasetPipeline:
    """
    For each hard-failure prompt:
        SD 3.5 Medium → raster image → Potrace + ImageMagick → SVG
            → Qwen2VL judge (Y/X) → JSONL dataset

    Matches the full whiteboard data pipeline including the VLM quality gate.
    """

    def __init__(
        self,
        output_dir: str,
        hf_token: str = "",
        simplification: str = "high",
        use_colour_vectorizer: bool = False,
        num_colours: int = 6,
        vectorizer_threshold: float = 0.45,
        vectorizer_resolution: int = 512,
        diffusion_steps: int = 30,
        diffusion_guidance: float = 5.0,
        min_svg_elements: int = 1,
        max_svg_elements: int = 500,
        save_images: bool = False,
        seed: Optional[int] = 42,
        # VLM quality filter
        use_vlm_filter: bool = True,
        vlm_model=None,        # pass pre-loaded Qwen2VL model (e.g. from notebook)
        vlm_processor=None,    # pass pre-loaded processor
        vlm_model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
        vlm_4bit: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.hf_token = hf_token
        self.simplification = simplification
        self.diffusion_steps = diffusion_steps
        self.diffusion_guidance = diffusion_guidance
        self.min_svg_elements = min_svg_elements
        self.max_svg_elements = max_svg_elements
        self.save_images = save_images
        self.seed = seed

        if use_colour_vectorizer:
            self.vectorizer = ColourVectorizer(
                num_colors=num_colours,
                threshold=vectorizer_threshold,
                resolution=vectorizer_resolution,
            )
        else:
            self.vectorizer = Vectorizer(
                threshold=vectorizer_threshold,
                resolution=vectorizer_resolution,
            )

        self.vlm_filter: Optional[VLMQualityFilter] = None
        if use_vlm_filter:
            self.vlm_filter = VLMQualityFilter(
                model=vlm_model,
                processor=vlm_processor,
                model_name=vlm_model_name,
                load_in_4bit=vlm_4bit,
            )

        self._generate_image = None

    def _load_diffusion(self):
        if self._generate_image is None:
            if not self.hf_token:
                raise ValueError(
                    "hf_token required to download SD 3.5 Medium. "
                    "Get one at https://huggingface.co/settings/tokens"
                )
            self._generate_image = load_sd35(self.hf_token, self.simplification)

    # ------------------------------------------------------------------

    def run(
        self,
        prompts: List[str],
        output_filename: str = "dataset.jsonl",
    ) -> Path:
        """
        Generate corrective (text, svg) pairs for the given prompts.

        Each prompt is one that the original pipeline got wrong.
        We produce a better SVG via SD3.5-M + Potrace.

        Returns path to the written JSONL file.
        """
        self._load_diffusion()

        out_path = self.output_dir / output_filename
        if self.save_images:
            (self.output_dir / "images").mkdir(exist_ok=True)

        stats = {
            "total": 0, "valid": 0,
            "failed_diffusion": 0, "failed_vectorize": 0,
            "failed_structural": 0, "failed_vlm": 0,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            for i, prompt in enumerate(tqdm(prompts, desc="Generating corrective SVGs")):
                stats["total"] += 1
                item_seed = (self.seed + i) if self.seed is not None else None

                # ── Step 1: SD3.5-M → raster image ──────────────────────────
                # Move VLM to CPU so SD3.5-M has VRAM (mirrors notebook pattern)
                if self.vlm_filter:
                    self.vlm_filter.move_to_cpu()

                try:
                    image = self._generate_image(
                        prompt,
                        seed=item_seed,
                        steps=self.diffusion_steps,
                        guidance=self.diffusion_guidance,
                    )
                except Exception as e:
                    logger.warning(f"[{i}] Diffusion failed '{prompt}': {e}")
                    stats["failed_diffusion"] += 1
                    continue

                if self.save_images:
                    image.save(self.output_dir / "images" / f"{i:05d}.png")

                # ── Step 2: ImageMagick + Potrace → SVG ──────────────────────
                svg = self.vectorizer.vectorize(image, prompt=prompt)
                if svg is None:
                    logger.warning(f"[{i}] Vectorization failed '{prompt}'")
                    stats["failed_vectorize"] += 1
                    continue

                # ── Step 3a: Structural check (fast, before VLM call) ─────────
                path_count = len(re.findall(r'<path', svg))
                if not is_good_svg(svg, self.min_svg_elements, self.max_svg_elements):
                    logger.info(f"[{i}] Structural check failed '{prompt}' (paths={path_count}, min={self.min_svg_elements}, max={self.max_svg_elements})")
                    stats["failed_structural"] += 1
                    continue

                # ── Step 3b: Qwen2VL quality gate (Y / X) ────────────────────
                if self.vlm_filter:
                    # Give VRAM back to Qwen2VL for the judgement call
                    torch.cuda.empty_cache()
                    gc.collect()
                    self.vlm_filter.move_to_gpu()

                    if not self.vlm_filter.is_good(svg, prompt):
                        logger.info(f"[{i}] VLM judge: X (rejected) '{prompt}' (paths={path_count})")
                        stats["failed_vlm"] += 1
                        continue
                    logger.info(f"[{i}] VLM judge: Y (accepted) '{prompt}' (paths={path_count})")

                # ── Step 4: Write record to dataset ──────────────────────────
                f.write(json.dumps({"text": prompt, "svg": svg}, ensure_ascii=False) + "\n")
                stats["valid"] += 1

                if stats["total"] % 10 == 0:
                    pct = 100 * stats["valid"] / stats["total"]
                    logger.info(
                        f"[{stats['total']}/{len(prompts)}] "
                        f"Y={stats['valid']} ({pct:.0f}%)  "
                        f"X=diff:{stats['failed_diffusion']} "
                        f"vec:{stats['failed_vectorize']} "
                        f"struct:{stats['failed_structural']} "
                        f"vlm:{stats['failed_vlm']}"
                    )

        # Save stats
        with open(self.output_dir / "stats.json", "w") as f:
            json.dump(stats, f, indent=2)

        logger.info(
            f"Done  Y={stats['valid']}  X=diff:{stats['failed_diffusion']} "
            f"vec:{stats['failed_vectorize']} struct:{stats['failed_structural']} "
            f"vlm:{stats['failed_vlm']}  total:{stats['total']}"
        )
        return out_path

    # ------------------------------------------------------------------

    @staticmethod
    def split_dataset(
        jsonl_path: str,
        train_ratio: float = 0.9,
        seed: int = 42,
    ) -> Tuple[Path, Path]:
        """
        Split JSONL into _train.jsonl and _val.jsonl.
        For small datasets (< 20 records) everything goes to train.
        """
        path = Path(jsonl_path)
        with open(path, encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]

        if len(records) < 20:
            logger.warning(
                f"Only {len(records)} records — skipping val split, using all for train"
            )
            train_path = path.with_name(path.stem + "_train.jsonl")
            with open(train_path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            return train_path, None

        random.seed(seed)
        random.shuffle(records)
        split = int(len(records) * train_ratio)
        train, val = records[:split], records[split:]

        train_path = path.with_name(path.stem + "_train.jsonl")
        val_path   = path.with_name(path.stem + "_val.jsonl")

        for subset, out in [(train, train_path), (val, val_path)]:
            with open(out, "w", encoding="utf-8") as f:
                for r in subset:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

        logger.info(f"Train: {len(train)} → {train_path}")
        logger.info(f"Val:   {len(val)}   → {val_path}")
        return train_path, val_path


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------

def dry_run(output_dir: str = "./dataset_dry"):
    """Test the pipeline locally — no GPU or HF token needed."""
    logging.basicConfig(level=logging.INFO)
    logger.info("=== DRY RUN ===")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Synthetic image: white background + black circle (easy to vectorize)
    img = Image.new("RGB", (128, 128), "white")
    draw = ImageDraw.Draw(img)
    draw.ellipse([16, 16, 112, 112], fill="black")

    v = Vectorizer(resolution=128, turdsize=1)
    svg = v.vectorize(img, prompt="a black circle")

    if svg:
        logger.info(f"Vectorization OK — {len(svg)} chars")
        ok = is_good_svg(svg)
        logger.info(f"Quality: {'PASS' if ok else 'WARN (low elements)'}")
        jsonl = out / "dry_run.jsonl"
        with open(jsonl, "w") as f:
            f.write(json.dumps({"text": "a black circle", "svg": svg}) + "\n")
        logger.info(f"Written: {jsonl}")
    else:
        logger.error("Vectorization FAILED — is Potrace installed?")

    logger.info("=== DRY RUN DONE ===")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Build corrective (text, SVG) dataset from bad pipeline results"
    )

    # Source of bad prompts
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--results", type=str,
        help="Path to results.json or results.csv from DiffuSVG_v4.ipynb "
             "(mines prompts with bad scores automatically)"
    )
    src.add_argument(
        "--prompts_file", type=str,
        help="Plain text file with prompts (one per line) — use when you already "
             "know which prompts to fix"
    )

    # Failure thresholds (only used with --results)
    parser.add_argument("--clip_threshold", type=float, default=24.0,
                        help="CLIP score below this = bad result (default 24.0)")
    parser.add_argument("--dino_threshold", type=float, default=0.35,
                        help="DINO score below this = bad result (default 0.35)")

    # Output
    parser.add_argument("--output_dir", type=str, default="./dataset")
    parser.add_argument("--train_split", type=float, default=0.9)

    # HF / model
    parser.add_argument("--hf_token", type=str, default=os.environ.get("HF_TOKEN", ""),
                        help="HuggingFace token (or set HF_TOKEN env var)")
    parser.add_argument("--simplification", choices=["low", "medium", "high"], default="high")
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--guidance", type=float, default=5.0)

    # Vectorizer
    parser.add_argument("--colour", action="store_true",
                        help="Multi-colour vectorizer (requires ImageMagick)")
    parser.add_argument("--num_colours", type=int, default=6)
    parser.add_argument("--threshold", type=float, default=0.45,
                        help="Greyscale binarisation threshold for Potrace")
    parser.add_argument("--resolution", type=int, default=512)

    # Misc
    parser.add_argument("--save_images", action="store_true",
                        help="Save the SD3.5-M raster images alongside SVGs")
    parser.add_argument("--seed", type=int, default=42)
    # VLM quality filter
    parser.add_argument("--no_vlm_filter", action="store_true",
                        help="Skip Qwen2VL Y/X gate — use structural check only")
    parser.add_argument("--vlm_model", type=str, default="Qwen/Qwen2-VL-7B-Instruct")
    parser.add_argument("--vlm_no_4bit", action="store_true",
                        help="Load Qwen2VL in fp16 instead of 4-bit (needs more VRAM)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Validate Potrace setup without GPU")

    args = parser.parse_args()

    # ── Dry-run ──────────────────────────────────────────────────────────────
    if args.dry_run:
        dry_run(args.output_dir)
        raise SystemExit(0)

    # ── Collect prompts ───────────────────────────────────────────────────────
    if args.results:
        prompts, breakdown = mine_bad_prompts(
            args.results,
            clip_threshold=args.clip_threshold,
            dino_threshold=args.dino_threshold,
        )
        logger.info(
            f"Mined {breakdown['bad_total']}/{breakdown['total']} bad prompts from {args.results}"
        )
        logger.info(
            f"  outright failures : {breakdown['failed']}"
        )
        logger.info(
            f"  low CLIP (<{args.clip_threshold}) : {breakdown['low_clip']}"
        )
        logger.info(
            f"  low DINO (<{args.dino_threshold}) : {breakdown['low_dino']}"
        )
        if not prompts:
            logger.info("No bad prompts found — thresholds may be too lenient. Exiting.")
            raise SystemExit(0)

    elif args.prompts_file:
        with open(args.prompts_file, encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(prompts)} prompts from {args.prompts_file}")

    else:
        parser.error("Provide either --results or --prompts_file")

    logger.info(f"Prompts to fix: {prompts}")

    # ── Run pipeline ─────────────────────────────────────────────────────────
    pipeline = DatasetPipeline(
        output_dir=args.output_dir,
        hf_token=args.hf_token,
        simplification=args.simplification,
        use_colour_vectorizer=args.colour,
        num_colours=args.num_colours,
        vectorizer_threshold=args.threshold,
        vectorizer_resolution=args.resolution,
        diffusion_steps=args.steps,
        diffusion_guidance=args.guidance,
        save_images=args.save_images,
        seed=args.seed,
        use_vlm_filter=not args.no_vlm_filter,
        vlm_model_name=args.vlm_model,
        vlm_4bit=not args.vlm_no_4bit,
    )

    jsonl_path = pipeline.run(prompts)

    # ── Split ────────────────────────────────────────────────────────────────
    DatasetPipeline.split_dataset(str(jsonl_path), train_ratio=args.train_split)
