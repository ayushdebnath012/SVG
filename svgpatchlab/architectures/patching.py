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

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        result = ArchitectureResult(model_calls=1)
        try:
            scene = build_scene(case.source_svg)
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

