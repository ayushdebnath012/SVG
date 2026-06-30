from __future__ import annotations

import base64
import io


class RendererUnavailable(RuntimeError):
    pass


def _dependencies():
    try:
        import cairosvg
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise RendererUnavailable(
            "rendering requires the optional dependencies: pip install -e '.[eval]'"
        ) from exc
    return cairosvg, np, Image


def ensure_renderer() -> None:
    _dependencies()


def render_svg_png(
    svg: str,
    size: int = 72,
    background: str | None = "white",
) -> bytes:
    cairosvg, _, _ = _dependencies()
    return cairosvg.svg2png(
        bytestring=svg.encode(),
        output_width=size,
        output_height=size,
        background_color=background,
    )


def render_svg_array(svg: str, size: int = 72, background: str = "white"):
    _, np, Image = _dependencies()
    png = render_svg_png(svg, size=size, background=background)
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB"), dtype=np.float32) / 255.0


def render_svg_data_url(svg: str, size: int = 512) -> str:
    png = render_svg_png(svg, size=size, background="white")
    encoded = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def image_mse(candidate_svg: str, answer_svg: str, size: int = 72) -> float:
    _, np, _ = _dependencies()
    candidate = render_svg_array(candidate_svg, size=size)
    answer = render_svg_array(answer_svg, size=size)
    return float(np.mean((candidate - answer) ** 2))
