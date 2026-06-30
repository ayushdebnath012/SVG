from __future__ import annotations

import io
from typing import Any


class EmbedderUnavailable(RuntimeError):
    pass


def _vit_dependencies():
    try:
        import numpy as np
        import torch
        from PIL import Image
        from transformers import ViTFeatureExtractor, ViTModel
    except ImportError as exc:
        raise EmbedderUnavailable(
            "vision embedder requires: pip install torch transformers pillow"
        ) from exc
    return np, torch, Image, ViTFeatureExtractor, ViTModel


class NodeEmbedder:
    """Encodes each SVG node's isolated visual footprint as a ViT embedding vector.

    Plan A Stage 1-2: per-node rasterization then ViT encoding.
    The embedding captures spatial position, shape, and color of the node
    independent of its XML representation.

    Usage::

        embedder = NodeEmbedder()
        scene = build_scene(svg, visual_embeddings=embedder.embed_all(svg, node_ids))
    """

    MODEL_NAME = "google/vit-base-patch16-224"

    def __init__(self, model_name: str = MODEL_NAME, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._extractor: Any = None
        self._model: Any = None

    def _load(self) -> None:
        if self._model is not None:
            return
        _, torch, _, ViTFeatureExtractor, ViTModel = _vit_dependencies()
        self._extractor = ViTFeatureExtractor.from_pretrained(self.model_name)
        self._model = ViTModel.from_pretrained(self.model_name).to(self.device).eval()

    def embed_node(self, svg: str, node_id: str, size: int = 224) -> list[float]:
        """Return a ViT CLS embedding for one node's isolated render."""
        from svgpatchlab.eval.render import render_node_mask

        self._load()
        np, torch, Image, _, _ = _vit_dependencies()

        png_bytes = render_node_mask(svg, node_id, size=size)
        image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        inputs = self._extractor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self._model(**inputs)
        cls_vector = outputs.last_hidden_state[:, 0, :].squeeze(0)
        return cls_vector.cpu().tolist()

    def embed_all(self, svg: str, node_ids: list[str], size: int = 224) -> dict[str, list[float]]:
        """Return ViT embeddings for a list of node IDs."""
        return {nid: self.embed_node(svg, nid, size=size) for nid in node_ids}
