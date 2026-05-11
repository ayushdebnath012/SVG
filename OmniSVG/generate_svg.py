"""
OmniSVG Text-to-SVG Generator
==============================
Simple API and CLI for generating SVG from text prompts using the OmniSVG model.

Usage as a module:
    from generate_svg import OmniSVGGenerator
    gen = OmniSVGGenerator()          # loads 4B model by default
    svg_str = gen.generate("a red heart icon")
    print(svg_str)

Usage as a CLI:
    python generate_svg.py "a red heart icon"
    python generate_svg.py "a red heart icon" --output heart.svg --model-size 4B
    python generate_svg.py "a red heart icon" --output heart.svg --save-png
"""

import os
import sys
import gc
import io
import yaml
import torch
import numpy as np
import tempfile
from pathlib import Path
from PIL import Image

os.environ["TOKENIZERS_PARALLELISM"] = "false"

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

with open(CONFIG_PATH, "r") as f:
    _config = yaml.safe_load(f)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Generate precise, valid SVG path commands that accurately represent the described scene or object. "
    "Focus on capturing key shapes, spatial relationships, and visual composition."
)

_model_cfg   = _config.get("model", {})
BOS_TOKEN_ID = _model_cfg.get("bos_token_id", 196998)
EOS_TOKEN_ID = _model_cfg.get("eos_token_id", 196999)
PAD_TOKEN_ID = _model_cfg.get("pad_token_id", 151643)

_colors_cfg      = _config.get("colors", {})
BLACK_COLOR_TOKEN = _colors_cfg.get("black_color_token", _colors_cfg.get("color_token_start", 40010) + 2)

_image_cfg          = _config.get("image", {})
TARGET_IMAGE_SIZE   = _image_cfg.get("target_size", 448)
RENDER_SIZE         = _image_cfg.get("render_size", 1024)
EMPTY_THRESHOLD_IL  = _image_cfg.get("empty_threshold_illustration", 250)
EMPTY_THRESHOLD_IC  = _image_cfg.get("empty_threshold_icon", 252)

TASK_CONFIGS = {
    "text-to-svg-icon": {
        "temperature": 0.5,
        "top_p": 0.88,
        "top_k": 50,
        "repetition_penalty": 1.05,
    },
    "text-to-svg-illustration": {
        "temperature": 0.6,
        "top_p": 0.90,
        "top_k": 60,
        "repetition_penalty": 1.03,
    },
}

ICON_KEYWORDS = {
    "icon", "logo", "symbol", "badge", "button", "emoji", "glyph",
    "simple", "arrow", "triangle", "circle", "square", "heart", "star", "checkmark",
}
ILLUSTRATION_KEYWORDS = {
    "illustration", "scene", "person", "people", "character", "man", "woman",
    "boy", "girl", "avatar", "portrait", "face", "head", "body", "cat", "dog",
    "bird", "animal", "pet", "fox", "rabbit", "sitting", "standing", "walking",
    "running", "sleeping", "holding", "playing", "house", "building", "tree",
    "garden", "landscape", "mountain", "forest", "city", "ocean", "beach",
    "sunset", "sunrise", "sky",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _detect_subtype(text: str) -> str:
    """Return 'icon' or 'illustration' based on prompt keywords."""
    lower = text.lower()
    if any(k in lower for k in ICON_KEYWORDS):
        return "icon"
    matches = sum(1 for k in ILLUSTRATION_KEYWORDS if k in lower)
    if matches >= 1 or len(text) > 50:
        return "illustration"
    return "icon"


def _render_svg(svg_str: str, size: int = RENDER_SIZE):
    """Render SVG string to a PIL Image; returns None on failure."""
    try:
        import cairosvg
        png_data = cairosvg.svg2png(
            bytestring=svg_str.encode("utf-8"),
            output_width=size,
            output_height=size,
        )
        img_rgba = Image.open(io.BytesIO(png_data)).convert("RGBA")
        bg = Image.new("RGB", img_rgba.size, (255, 255, 255))
        bg.paste(img_rgba, mask=img_rgba.split()[3])
        return bg
    except Exception as e:
        print(f"[render] {e}")
        return None


def _extra_candidate_buffer() -> int:
    """Use extra reranking candidates only when VRAM is above T4 class."""
    if not torch.cuda.is_available():
        return 0
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    return 0 if vram_gb < 20 else 4


def _is_valid(svg_str: str, img, subtype: str = "illustration") -> tuple:
    """Return (bool, reason) indicating whether a candidate is usable."""
    if not svg_str or len(svg_str) < 20:
        return False, "too_short"
    if "<svg" not in svg_str:
        return False, "no_svg_tag"
    if img is None:
        return False, "render_failed"
    threshold = EMPTY_THRESHOLD_IL if subtype == "illustration" else EMPTY_THRESHOLD_IC
    if np.array(img).mean() > threshold:
        return False, "empty_image"
    return True, "ok"


# --------------------------------------------------------------------------- #
# Main generator class
# --------------------------------------------------------------------------- #

class OmniSVGGenerator:
    """
    Loads the OmniSVG model once and exposes `generate(text)` for text-to-SVG.

    Parameters
    ----------
    model_size : str
        "4B" (default, ~7.7 GB) or "8B" (~17 GB).
    model_path : str | None
        Local path or HF repo for the Qwen backbone.
        When None, pulled from config.yaml.
    weight_path : str | None
        Local path or HF repo for OmniSVG pytorch_model.bin.
        When None, pulled from config.yaml.
    max_new_tokens : int
        Maximum SVG tokens to generate per candidate (default 512 for T4).
    num_candidates : int
        How many valid SVGs to attempt; returns the first valid one (default 1 for T4).
    verbose : bool
        Print generation details (default False).
    """

    def __init__(
        self,
        model_size: str = "4B",
        model_path: str | None = None,
        weight_path: str | None = None,
        max_new_tokens: int = 512,
        num_candidates: int = 1,
        verbose: bool = False,
    ):
        self.model_size     = model_size
        self.max_new_tokens = max_new_tokens
        self.num_candidates = num_candidates
        self.verbose        = verbose

        self._dtype = (
            torch.bfloat16
            if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
            else torch.float16
        )

        self._resolve_paths(model_path, weight_path)
        self._load()

    # ------------------------------------------------------------------ #

    def _resolve_paths(self, model_path, weight_path):
        """Fill in paths from config.yaml when not provided."""
        models_cfg = _config.get("models", {}).get(self.model_size, {})
        hf_cfg     = models_cfg.get("huggingface", {})

        self._model_path  = model_path  or hf_cfg.get("qwen_model",    "Qwen/Qwen2.5-VL-3B-Instruct")
        self._weight_path = weight_path or hf_cfg.get("omnisvg_model", "OmniSVG/OmniSVG1.1_4B")

    def _load(self):
        """Download (if needed) and instantiate all model components."""
        from transformers import AutoTokenizer, AutoProcessor
        from decoder import SketchDecoder
        from tokenizer import SVGTokenizer

        print(f"[OmniSVG] Loading {self.model_size} model …")
        print(f"  Qwen backbone : {self._model_path}")
        print(f"  OmniSVG weights: {self._weight_path}")
        print(f"  Precision      : {self._dtype}")

        # ── tokenizer / processor ──────────────────────────────────────
        self.tokenizer = AutoTokenizer.from_pretrained(
            self._model_path, padding_side="left", trust_remote_code=True
        )
        self.processor = AutoProcessor.from_pretrained(
            self._model_path, padding_side="left", trust_remote_code=True
        )
        self.processor.tokenizer.padding_side = "left"

        # ── 4-bit quantization for low-VRAM GPUs ──────────────────────
        use_4bit = False
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            if vram_gb < 20:
                use_4bit = True
                print(f"  Low-VRAM GPU ({vram_gb:.1f} GB) — enabling 4-bit NF4 quantization")

        # ── backbone decoder ───────────────────────────────────────────
        self.decoder = SketchDecoder(
            config_path=CONFIG_PATH,
            model_path=self._model_path,
            model_size=self.model_size,
            pix_len=2048,
            text_len=_config.get("text", {}).get("max_length", 200),
            torch_dtype=self._dtype,
            use_4bit=use_4bit,
        )

        # ── OmniSVG weights ────────────────────────────────────────────
        bin_path = self._resolve_bin_path()
        print(f"  Loading weights from: {bin_path}")
        state_dict = torch.load(bin_path, map_location="cpu")
        self.decoder.load_state_dict(state_dict)
        self.decoder = self.decoder.eval()

        # ── SVG tokenizer ──────────────────────────────────────────────
        self.svg_tok = SVGTokenizer(CONFIG_PATH, model_size=self.model_size)

        print(f"[OmniSVG] Model ready.\n")

    def _resolve_bin_path(self) -> str:
        """Return a local path to pytorch_model.bin, downloading if needed."""
        from huggingface_hub import hf_hub_download

        wp = self._weight_path

        # Local directory
        if os.path.isdir(wp):
            candidate = os.path.join(wp, "pytorch_model.bin")
            if os.path.exists(candidate):
                return candidate
            raise FileNotFoundError(f"pytorch_model.bin not found in {wp}")

        # Local .bin file
        if os.path.isfile(wp) and wp.endswith(".bin"):
            return wp

        # HuggingFace repo
        print(f"  Downloading pytorch_model.bin from HF hub: {wp} …")
        return hf_hub_download(repo_id=wp, filename="pytorch_model.bin", resume_download=True)

    # ------------------------------------------------------------------ #

    def _input_device(self):
        """Return the device where the embedding layer lives."""
        try:
            m = self.decoder.transformer
            if hasattr(m, "model") and hasattr(m.model, "embed_tokens"):
                return next(m.model.embed_tokens.parameters()).device
            if hasattr(m, "embed_tokens"):
                return next(m.embed_tokens.parameters()).device
            return next(m.parameters()).device
        except StopIteration:
            return torch.device("cpu")

    def _build_messages(self, text: str) -> list:
        """Construct the chat messages for a text-to-SVG prompt."""
        instruction = (
            f"Generate an SVG illustration for: {text}\n\n"
            "Requirements:\n"
            "- Create complete SVG path commands\n"
            "- Include proper coordinates and colors\n"
            "- Maintain visual clarity and composition"
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": [{"type": "text", "text": instruction}]},
        ]

    def _prepare_inputs(self, text: str):
        messages   = self._build_messages(text)
        text_input = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        return self.processor(
            text=[text_input], padding=True, truncation=True, return_tensors="pt"
        )

    def _decode_candidate(self, token_ids) -> tuple[str | None, object]:
        """Convert raw generated token IDs to (svg_string, pil_image)."""
        try:
            ids_cpu = token_ids.cpu()
            wrapped = torch.cat([
                torch.full((1, 1), BOS_TOKEN_ID, device="cpu"),
                ids_cpu,
                torch.full((1, 1), EOS_TOKEN_ID, device="cpu"),
            ], dim=1)

            xy = self.svg_tok.process_generated_tokens(wrapped)
            if len(xy) == 0:
                return None, None

            svg_tensors, color_tensors = self.svg_tok.raster_svg(xy)
            if not svg_tensors or not svg_tensors[0]:
                return None, None

            num_paths = len(svg_tensors[0])
            while len(color_tensors) < num_paths:
                color_tensors.append(BLACK_COLOR_TOKEN)

            svg     = self.svg_tok.apply_colors_to_svg(svg_tensors[0], color_tensors)
            svg_str = svg.to_str()

            if "width=" not in svg_str:
                svg_str = svg_str.replace(
                    "<svg", f'<svg width="{TARGET_IMAGE_SIZE}" height="{TARGET_IMAGE_SIZE}"', 1
                )

            img = _render_svg(svg_str, size=RENDER_SIZE)
            return svg_str, img

        except Exception as e:
            if self.verbose:
                print(f"  [decode] {e}")
            return None, None

    # ------------------------------------------------------------------ #

    def generate(
        self,
        text: str,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        repetition_penalty: float | None = None,
    ) -> str | None:
        """
        Generate an SVG string from a text prompt.

        Parameters
        ----------
        text : str
            Natural-language description of the desired SVG.
        temperature / top_p / top_k / repetition_penalty : optional
            Override task-default sampling hyperparameters.

        Returns
        -------
        str | None
            Valid SVG string, or None if generation failed.
        """
        subtype  = _detect_subtype(text)
        task_key = f"text-to-svg-{subtype}"
        defaults = TASK_CONFIGS[task_key]

        temperature        = temperature        or defaults["temperature"]
        top_p              = top_p              or defaults["top_p"]
        top_k              = top_k              or defaults["top_k"]
        repetition_penalty = repetition_penalty or defaults["repetition_penalty"]

        if self.verbose:
            print(f"[generate] subtype={subtype}, temp={temperature}, top_p={top_p}, "
                  f"top_k={top_k}, rep={repetition_penalty}")

        inputs      = self._prepare_inputs(text)
        input_dev   = self._input_device()

        input_ids      = inputs["input_ids"].to(input_dev)
        attention_mask = inputs["attention_mask"].to(input_dev)

        gen_kwargs = dict(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=self.max_new_tokens,
            num_return_sequences=self.num_candidates + _extra_candidate_buffer(),
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            top_k=int(top_k),
            repetition_penalty=repetition_penalty,
            early_stopping=True,
            eos_token_id=EOS_TOKEN_ID,
            pad_token_id=PAD_TOKEN_ID,
            bos_token_id=BOS_TOKEN_ID,
            use_cache=True,
        )

        with torch.no_grad():
            outputs   = self.decoder.transformer.generate(**gen_kwargs)
            input_len = input_ids.shape[1]
            new_ids   = outputs[:, input_len:]

        for i in range(new_ids.shape[0]):
            svg_str, img = self._decode_candidate(new_ids[i : i + 1])
            valid, reason = _is_valid(svg_str, img, subtype)

            if self.verbose:
                print(f"  candidate {i}: {reason}")

            if valid:
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                return svg_str

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("[OmniSVG] Warning: no valid SVG produced.")
        return None

    def generate_to_file(
        self,
        text: str,
        output_path: str,
        save_png: bool = False,
        **kwargs,
    ) -> str | None:
        """
        Generate an SVG and save it to *output_path*.

        Optionally renders and saves a PNG alongside the SVG when save_png=True.

        Returns the saved SVG path, or None on failure.
        """
        svg_str = self.generate(text, **kwargs)
        if svg_str is None:
            return None

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg_str, encoding="utf-8")
        print(f"[OmniSVG] SVG saved → {out}")

        if save_png:
            img = _render_svg(svg_str, size=RENDER_SIZE)
            if img is not None:
                png_path = out.with_suffix(".png")
                img.save(png_path)
                print(f"[OmniSVG] PNG saved → {png_path}")

        return str(out)


# --------------------------------------------------------------------------- #
# CLI entry-point
# --------------------------------------------------------------------------- #

def _cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="OmniSVG: generate SVG from a text prompt",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("text", type=str, help="Text prompt describing the SVG to generate")
    parser.add_argument("--output",    "-o", type=str, default=None,
                        help="Output SVG file path (default: print to stdout)")
    parser.add_argument("--model-size", type=str, default="4B", choices=["4B", "8B"],
                        help="OmniSVG model variant to use")
    parser.add_argument("--model-path",  type=str, default=None,
                        help="Local path or HF repo for Qwen backbone (overrides config)")
    parser.add_argument("--weight-path", type=str, default=None,
                        help="Local path or HF repo for OmniSVG weights (overrides config)")
    parser.add_argument("--max-tokens",  type=int, default=512,
                        help="Maximum SVG tokens to generate")
    parser.add_argument("--num-candidates", type=int, default=1,
                        help="Number of candidates to try before giving up")
    parser.add_argument("--temperature",        type=float, default=None)
    parser.add_argument("--top-p",              type=float, default=None)
    parser.add_argument("--top-k",              type=int,   default=None)
    parser.add_argument("--repetition-penalty", type=float, default=None)
    parser.add_argument("--save-png",   action="store_true",
                        help="Also save a rendered PNG next to the SVG")
    parser.add_argument("--verbose",    action="store_true")

    args = parser.parse_args()

    gen = OmniSVGGenerator(
        model_size=args.model_size,
        model_path=args.model_path,
        weight_path=args.weight_path,
        max_new_tokens=args.max_tokens,
        num_candidates=args.num_candidates,
        verbose=args.verbose,
    )

    gen_kwargs = {}
    if args.temperature        is not None: gen_kwargs["temperature"]        = args.temperature
    if args.top_p              is not None: gen_kwargs["top_p"]              = args.top_p
    if args.top_k              is not None: gen_kwargs["top_k"]              = args.top_k
    if args.repetition_penalty is not None: gen_kwargs["repetition_penalty"] = args.repetition_penalty

    if args.output:
        result = gen.generate_to_file(args.text, args.output, save_png=args.save_png, **gen_kwargs)
        if result is None:
            sys.exit(1)
    else:
        svg_str = gen.generate(args.text, **gen_kwargs)
        if svg_str is None:
            sys.exit(1)
        print(svg_str)


if __name__ == "__main__":
    _cli()
