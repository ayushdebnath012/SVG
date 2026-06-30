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


def render_node_mask(svg: str, node_id: str, size: int = 64) -> bytes:
    """Render SVG with only the given node visible, all others transparent.

    Used by Plan A vision module to generate per-node difference images.
    """
    import copy
    from svgpatchlab.core.xml import index_tree, parse_svg, serialize_svg

    root = parse_svg(svg)
    indexed = index_tree(root)
    node_map = {node.node_id: node for node in indexed}
    if node_id not in node_map:
        raise ValueError(f"node {node_id} not found in SVG")

    ancestors: set[str] = set()
    current = node_map[node_id].parent_id
    while current:
        ancestors.add(current)
        current = node_map[current].parent_id

    root_copy = copy.deepcopy(root)
    for node in index_tree(root_copy):
        if node.node_id == node_id:
            pass
        elif node.node_id in ancestors:
            for attr in ("fill", "stroke", "opacity"):
                node.element.attrib.pop(attr, None)
        else:
            node.element.attrib["opacity"] = "0"

    return render_svg_png(serialize_svg(root_copy), size=size, background=None)
