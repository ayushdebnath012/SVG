from __future__ import annotations

import json

from svgpatchlab.core import PatchPolicy, apply_patch, build_scene, parse_patch, validate_patch
from svgpatchlab.eval.render import render_svg_data_url
from svgpatchlab.models import ModelAdapter
from svgpatchlab.types import ArchitectureResult, BenchmarkCase, ModelRequest

from .base import Architecture
from .prompts import patch_prompt


class PatchArchitecture(Architecture):
    context_mode = "skeleton"
    include_image = False

    def __init__(self, policy: PatchPolicy | None = None):
        self.policy = policy or PatchPolicy()

    def context(self, case: BenchmarkCase, scene: dict) -> tuple[str, str]:
        if self.context_mode == "full":
            return "Original SVG", case.source_svg
        return "SVG DOM skeleton", json.dumps(scene, indent=2, sort_keys=True)

    def scene_for(self, case: BenchmarkCase) -> dict:
        return build_scene(case.source_svg)

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        result = ArchitectureResult(model_calls=1)
        try:
            scene = self.scene_for(case)
            context_name, context = self.context(case, scene)
            images = (render_svg_data_url(case.source_svg),) if self.include_image else ()
            response = model.generate(
                ModelRequest(
                    patch_prompt(case.instruction, context_name, context),
                    images=images,
                    metadata={"request_id": case.case_id},
                )
            )
            result.raw_responses.append(response.text)
            result.patch = parse_patch(response.text)
            validate_patch(result.patch, scene, self.policy, task=case.task)
            result.output_svg = apply_patch(case.source_svg, result.patch)
        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
        return result


class FullContextPatchArchitecture(PatchArchitecture):
    name = "full_context_patch"
    context_mode = "full"


class SkeletonPatchArchitecture(PatchArchitecture):
    name = "skeleton_patch"
    context_mode = "skeleton"


class VisualSkeletonPatchArchitecture(SkeletonPatchArchitecture):
    name = "visual_skeleton_patch"
    include_image = True


class VisualStatsPatchArchitecture(SkeletonPatchArchitecture):
    """Plan A, cheap path: skeleton plus per-node rendered visual stats.

    Each node gains a compact human-readable "visual" field (bbox in viewBox
    units, area %, position word, dominant color, occlusion flag) computed by
    diffing full vs node-hidden renders. Stats are disk-cached by SVG content,
    so each benchmark input is rasterized once across all runs.
    """

    name = "visual_stats_patch"

    def __init__(
        self,
        policy: PatchPolicy | None = None,
        cache_dir: str = ".cache/visual_stats",
        render_size: int = 64,
    ):
        super().__init__(policy)
        from svgpatchlab.eval.render import VisualStatsCache

        self._cache = VisualStatsCache(cache_dir)
        self.render_size = render_size

    def scene_for(self, case: BenchmarkCase) -> dict:
        stats = self._cache.get_or_compute(case.source_svg, size=self.render_size)
        return build_scene(case.source_svg, visual_stats=stats)


class VisualGNNPatchArchitecture(Architecture):
    """Plan A: skeleton patch guided by GNN-based node pre-selection.

    Requires trained NodeGNN weights and NodeEmbedder (ViT).
    Pass gnn_weights_path to load a trained checkpoint.
    Without weights the GNN scores all nodes equally (no filtering).
    """

    name = "visual_gnn_patch"

    def __init__(
        self,
        gnn_weights_path: str | None = None,
        score_threshold: float = 0.5,
        policy: PatchPolicy | None = None,
    ):
        self.score_threshold = score_threshold
        self.policy = policy or PatchPolicy()
        from svgpatchlab.vision import NodeEmbedder, NodeGNN
        self._embedder = NodeEmbedder()
        self._gnn = NodeGNN()
        if gnn_weights_path:
            self._gnn.load_weights(gnn_weights_path)

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        result = ArchitectureResult(model_calls=1)
        try:
            scene = build_scene(case.source_svg)
            node_ids = [n["id"] for n in scene["nodes"]]

            embeddings = self._embedder.embed_all(case.source_svg, node_ids)
            # Use zero instruction embedding as placeholder until a text encoder is wired in
            instruction_embedding = [0.0] * self._gnn.text_dim
            scores = self._gnn.score_nodes(embeddings, scene, instruction_embedding)
            candidates = self._gnn.select_targets(scores, threshold=self.score_threshold)

            augmented_scene = build_scene(case.source_svg, visual_embeddings=embeddings)
            context = json.dumps(
                {"candidate_targets": candidates, "scene": augmented_scene},
                indent=2,
                sort_keys=True,
            )
            response = model.generate(
                ModelRequest(
                    patch_prompt(case.instruction, "GNN-filtered SVG skeleton", context),
                    metadata={"request_id": case.case_id},
                )
            )
            result.raw_responses.append(response.text)
            result.patch = parse_patch(response.text)
            validate_patch(result.patch, scene, self.policy, task=case.task)
            result.output_svg = apply_patch(case.source_svg, result.patch)
        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
        return result
