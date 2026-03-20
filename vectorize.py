#!/usr/bin/env python3
"""
vectorize.py — Image → SVG via Potrace + ImageMagick
=====================================================

Implements the vectorization branch from the whiteboard:
    Raster Image → Potrace + ImageMagick → SVG

Requirements (system):
    sudo apt-get install potrace imagemagick   # Linux
    brew install potrace imagemagick           # macOS
    winget install potrace                     # Windows (Potrace)

Requirements (python):
    pip install pillow numpy

Usage:
    from vectorize import Vectorizer
    v = Vectorizer()
    svg = v.vectorize(pil_image, prompt="a red apple")
    print(svg)
"""

import io
import os
import re
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_tool(name: str) -> bool:
    return shutil.which(name) is not None


def _require_tool(name: str, install_hint: str):
    if not _check_tool(name):
        raise EnvironmentError(
            f"'{name}' not found in PATH. Install it: {install_hint}"
        )


# ---------------------------------------------------------------------------
# Core vectorization
# ---------------------------------------------------------------------------

class Vectorizer:
    """
    Converts raster images to SVG using Potrace + ImageMagick.

    Matches the whiteboard pipeline exactly:
        PIL Image → ImageMagick (preprocess: resize, contrast, threshold → BMP)
                  → Potrace (BMP → SVG)
                  → post-process (normalise viewBox)

    ImageMagick is used when available (preferred — matches whiteboard).
    Falls back to PIL-only if ImageMagick is not installed.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        turdsize: int = 2,
        alphamax: float = 1.0,
        opttolerance: float = 0.2,
        resolution: int = 512,
        invert: bool = False,
        contrast_stretch: str = "2%x98%",  # ImageMagick -level arg to boost contrast
    ):
        """
        Args:
            threshold:        Binarization threshold (0–1). Higher = more black.
            turdsize:         Potrace --turdsize: suppress speckles smaller than this px²
            alphamax:         Potrace --alphamax: corner rounding (0=sharp, 1.3=round)
            opttolerance:     Potrace --opttolerance: curve optimisation tolerance
            resolution:       Resize image to this square size before tracing
            invert:           Invert bitmap before tracing (dark subject on light bg)
            contrast_stretch: ImageMagick -level value to stretch contrast before threshold.
                              Set to "" to skip contrast stretching.
        """
        _require_tool("potrace", "https://potrace.sourceforge.net")
        self._has_imagemagick = _check_tool("convert")
        if not self._has_imagemagick:
            logger.warning(
                "ImageMagick ('convert') not found — falling back to PIL for preprocessing. "
                "Install ImageMagick to match the whiteboard pipeline exactly."
            )
        self.threshold = threshold
        self.turdsize = turdsize
        self.alphamax = alphamax
        self.opttolerance = opttolerance
        self.resolution = resolution
        self.invert = invert
        self.contrast_stretch = contrast_stretch

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def vectorize(self, image: Image.Image, prompt: str = "") -> Optional[str]:
        """
        Convert a PIL Image to SVG string.

        Returns SVG code on success, None on failure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            bmp_path = os.path.join(tmpdir, "input.bmp")
            svg_path = os.path.join(tmpdir, "output.svg")

            # Step 1: ImageMagick (preprocess) → 1-bit BMP
            self._to_bmp(image, bmp_path)

            # Step 2: Potrace BMP → SVG
            success = self._run_potrace(bmp_path, svg_path)
            if not success:
                return None

            # Step 3: Read and post-process SVG
            with open(svg_path, "r", encoding="utf-8") as f:
                svg = f.read()

            svg = self._postprocess(svg, prompt)
            return svg

    def vectorize_batch(
        self,
        images: list,
        prompts: list,
    ) -> list:
        """
        Vectorize a list of PIL Images.

        Returns list of (svg_or_None, prompt) tuples.
        """
        results = []
        for img, prompt in zip(images, prompts):
            svg = self.vectorize(img, prompt)
            results.append((svg, prompt))
        return results

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _to_bmp(self, image: Image.Image, path: str):
        """
        Convert PIL Image to 1-bit BMP for Potrace.

        Uses ImageMagick when available (whiteboard: Potrace + ImageMagick):
            convert input.png -resize NxN -colorspace Gray
                    -level 2%x98%       ← contrast stretch
                    -threshold 50%       ← binarize
                    -type Bilevel BMP3 output.bmp

        Falls back to PIL when ImageMagick is not installed.
        """
        if self._has_imagemagick:
            self._to_bmp_imagemagick(image, path)
        else:
            self._to_bmp_pil(image, path)

    def _to_bmp_imagemagick(self, image: Image.Image, path: str):
        """ImageMagick preprocessing → 1-bit BMP (matches whiteboard)."""
        import tempfile as _tf

        # Save input as PNG for ImageMagick to read
        with _tf.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            png_path = tmp.name
        image.convert("RGB").save(png_path)

        threshold_pct = f"{int(self.threshold * 100)}%"
        invert_flag = ["-negate"] if self.invert else []

        cmd = [
            "convert", png_path,
            "-resize", f"{self.resolution}x{self.resolution}!",  # force square
            "-colorspace", "Gray",
        ]
        if self.contrast_stretch:
            cmd += ["-level", self.contrast_stretch]
        cmd += invert_flag
        cmd += [
            "-threshold", threshold_pct,
            "-type", "Bilevel",
            f"BMP3:{path}",           # BMP3 = uncompressed, Potrace-compatible
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.warning(
                    f"ImageMagick preprocessing failed: {result.stderr.strip()} — falling back to PIL"
                )
                self._to_bmp_pil(image, path)
        except Exception as e:
            logger.warning(f"ImageMagick error: {e} — falling back to PIL")
            self._to_bmp_pil(image, path)
        finally:
            os.unlink(png_path)

    def _to_bmp_pil(self, image: Image.Image, path: str):
        """PIL fallback: greyscale + numpy threshold → 1-bit BMP."""
        img = image.convert("RGB").resize(
            (self.resolution, self.resolution), Image.LANCZOS
        )
        grey = np.array(img.convert("L")).astype(np.float32) / 255.0
        binary = (grey < self.threshold).astype(np.uint8)
        if self.invert:
            binary = 1 - binary
        bmp_img = Image.fromarray((binary * 255).astype(np.uint8), mode="L").convert("1")
        bmp_img.save(path, format="BMP")

    def _run_potrace(self, bmp_path: str, svg_path: str) -> bool:
        """Run Potrace to convert BMP → SVG."""
        cmd = [
            "potrace",
            bmp_path,
            "--svg",
            f"--turdsize={self.turdsize}",
            f"--alphamax={self.alphamax}",
            f"--opttolerance={self.opttolerance}",
            "--output", svg_path,
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning(f"Potrace error: {result.stderr.strip()}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("Potrace timed out")
            return False
        except Exception as e:
            logger.error(f"Potrace subprocess error: {e}")
            return False

    def _postprocess(self, svg: str, prompt: str) -> str:
        """
        Clean up Potrace SVG output:
        - Normalize viewBox to 0 0 200 200
        - Strip Potrace metadata comments
        - Ensure xmlns attribute
        """
        # Remove XML declaration and DOCTYPE
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        svg = re.sub(r'<!DOCTYPE[^>]*>', '', svg)

        # Remove Potrace generator comment
        svg = re.sub(r'<!--.*?-->', '', svg, flags=re.DOTALL)

        # Remove <metadata>...</metadata> blocks (Potrace RDF headers)
        svg = re.sub(r'<metadata\b[^>]*>.*?</metadata>', '', svg, flags=re.DOTALL)

        # Extract width/height from existing viewBox or dimensions
        # to compute a normalised viewBox
        vb_match = re.search(r'viewBox="([^"]+)"', svg)
        if vb_match:
            parts = vb_match.group(1).split()
            if len(parts) == 4:
                orig_w = float(parts[2])
                orig_h = float(parts[3])
            else:
                orig_w = orig_h = self.resolution
        else:
            orig_w = orig_h = float(self.resolution)

        # Scale paths from original dimensions to 200x200
        scale_x = 200.0 / orig_w if orig_w > 0 else 1.0
        scale_y = 200.0 / orig_h if orig_h > 0 else 1.0

        # Replace the <svg ...> opening tag with a normalised one
        svg = re.sub(
            r'<svg[^>]*>',
            '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
            svg,
            count=1,
        )

        # Apply scaling transform to the content group
        # Wrap inner content in a <g transform="scale(...)"> if scaling needed
        if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
            svg = svg.replace(
                '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">',
                f'<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
                f'<g transform="scale({scale_x:.4f},{scale_y:.4f})">',
            )
            svg = svg.replace('</svg>', '</g></svg>')

        # Strip blank lines
        svg = "\n".join(line for line in svg.splitlines() if line.strip())

        return svg.strip()


# ---------------------------------------------------------------------------
# Multi-colour variant (uses ImageMagick colour quantisation)
# ---------------------------------------------------------------------------

class ColourVectorizer(Vectorizer):
    """
    Multi-pass colour vectorization:
        Image → colour-quantised layers → per-colour Potrace → merge SVG

    Requires: ImageMagick (`convert` command)
    """

    def __init__(self, num_colors: int = 8, **kwargs):
        super().__init__(**kwargs)
        _require_tool(
            "convert",
            "brew install imagemagick  /  apt install imagemagick",
        )
        self.num_colors = num_colors

    def vectorize(self, image: Image.Image, prompt: str = "") -> Optional[str]:
        """Vectorize with per-colour layers merged into one SVG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "frame")

            # Step 1: Quantise to N colours with ImageMagick
            input_path = os.path.join(tmpdir, "input.png")
            image.convert("RGB").resize(
                (self.resolution, self.resolution), Image.LANCZOS
            ).save(input_path)

            quant_path = os.path.join(tmpdir, "quantised.png")
            subprocess.run(
                [
                    "convert", input_path,
                    "+dither",
                    "-colors", str(self.num_colors),
                    quant_path,
                ],
                capture_output=True,
                timeout=30,
            )

            if not os.path.exists(quant_path):
                # Fallback to single-colour
                logger.warning("ImageMagick quantization failed, using single-pass")
                return super().vectorize(image, prompt)

            # Step 2: Get the palette colours
            result = subprocess.run(
                ["convert", quant_path, "-format", "%c", "histogram:info:-"],
                capture_output=True, text=True, timeout=15,
            )
            colors = self._parse_palette(result.stdout)
            if not colors:
                return super().vectorize(image, prompt)

            # Step 3: Per-colour mask → Potrace → collect paths
            svg_layers = []
            quant_img = Image.open(quant_path).convert("RGB")
            quant_arr = np.array(quant_img)

            for hex_color, rgb in colors:
                # Create binary mask for this colour
                r, g, b = rgb
                tolerance = 20
                mask = (
                    (np.abs(quant_arr[:, :, 0].astype(int) - r) < tolerance) &
                    (np.abs(quant_arr[:, :, 1].astype(int) - g) < tolerance) &
                    (np.abs(quant_arr[:, :, 2].astype(int) - b) < tolerance)
                )

                if mask.sum() < 50:  # skip tiny regions
                    continue

                # Save mask as 1-bit BMP
                bmp_path = os.path.join(tmpdir, f"layer_{hex_color[1:]}.bmp")
                svg_path = os.path.join(tmpdir, f"layer_{hex_color[1:]}.svg")

                mask_img = Image.fromarray((mask * 255).astype(np.uint8)).convert("1")
                mask_img.save(bmp_path, format="BMP")

                if not self._run_potrace(bmp_path, svg_path):
                    continue

                with open(svg_path, "r") as f:
                    layer_svg = f.read()

                paths = self._extract_paths(layer_svg, hex_color)
                svg_layers.extend(paths)

            if not svg_layers:
                return super().vectorize(image, prompt)

            # Step 4: Merge all layers into one SVG (200×200)
            content = "\n".join(svg_layers)
            merged = (
                '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">\n'
                f'{content}\n'
                "</svg>"
            )
            return merged

    # ------------------------------------------------------------------

    def _parse_palette(self, histogram_text: str) -> list:
        """Parse ImageMagick histogram output → list of (hex, (r,g,b))."""
        colors = []
        for line in histogram_text.splitlines():
            m = re.search(r'#([0-9A-Fa-f]{6})', line)
            if m:
                hex_color = "#" + m.group(1).upper()
                r = int(m.group(1)[0:2], 16)
                g = int(m.group(1)[2:4], 16)
                b = int(m.group(1)[4:6], 16)
                colors.append((hex_color, (r, g, b)))
        # Unique colours only
        seen = set()
        unique = []
        for c in colors:
            if c[0] not in seen:
                seen.add(c[0])
                unique.append(c)
        return unique

    def _extract_paths(self, svg: str, fill_color: str) -> list:
        """Extract <path> elements from a Potrace SVG and recolour them."""
        paths = re.findall(r'<path[^>]*/>', svg, re.DOTALL)
        coloured = []
        for p in paths:
            # Remove existing fill, set new fill
            p = re.sub(r'fill="[^"]*"', '', p)
            p = p.replace('<path', f'<path fill="{fill_color}"', 1)
            coloured.append(p)
        return coloured


# ---------------------------------------------------------------------------
# Quality filter
# ---------------------------------------------------------------------------

def is_good_svg(svg: str, min_elements: int = 3, max_elements: int = 200) -> bool:
    """
    Basic quality check for Potrace SVGs.
    Returns True if the SVG seems usable for training.
    """
    if not svg or "<svg" not in svg:
        return False
    paths = len(re.findall(r'<path', svg))
    if paths < min_elements or paths > max_elements:
        return False
    # Must have at least one actual d= attribute with real data
    d_matches = re.findall(r'd="([^"]+)"', svg)
    if not d_matches or max(len(d) for d in d_matches) < 10:
        return False
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Vectorize image to SVG via Potrace")
    parser.add_argument("input", help="Input image file")
    parser.add_argument("output", nargs="?", default="output.svg", help="Output SVG file")
    parser.add_argument("--color", action="store_true", help="Use multi-colour mode (needs ImageMagick)")
    parser.add_argument("--colors", type=int, default=8, help="Number of colours (--color mode)")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--turdsize", type=int, default=2)
    parser.add_argument("--prompt", type=str, default="")
    args = parser.parse_args()

    img = Image.open(args.input)

    if args.color:
        v = ColourVectorizer(
            num_colors=args.colors,
            threshold=args.threshold,
            resolution=args.resolution,
            turdsize=args.turdsize,
        )
    else:
        v = Vectorizer(
            threshold=args.threshold,
            resolution=args.resolution,
            turdsize=args.turdsize,
        )

    svg = v.vectorize(img, prompt=args.prompt)

    if svg:
        Path(args.output).write_text(svg)
        print(f"Saved: {args.output}")
        if is_good_svg(svg):
            print("Quality check: PASS")
        else:
            print("Quality check: WARN (low element count)")
    else:
        print("ERROR: vectorization failed")
