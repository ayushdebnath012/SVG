from __future__ import annotations

import json

from svgpatchlab.core import (
    PatchPolicy,
    apply_patch,
    build_scene,
    derive_patch,
    parse_patch,
    validate_patch,
)
from svgpatchlab.core.patch import extract_json_object
from svgpatchlab.models import ModelAdapter
from svgpatchlab.types import ArchitectureResult, BenchmarkCase, ModelRequest

from .base import Architecture
from .prompts import patch_prompt


class OraclePatchArchitecture(Architecture):
    name = "oracle_patch"
    requires_model = False

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        try:
            patch = derive_patch(case.source_svg, case.answer_svg)
            scene = build_scene(case.source_svg)
            validate_patch(patch, scene, task=case.task)
            return ArchitectureResult(output_svg=apply_patch(case.source_svg, patch), patch=patch)
        except Exception as exc:
            return ArchitectureResult(error=f"{type(exc).__name__}: {exc}")


class OracleTargetArchitecture(Architecture):
    name = "oracle_target_patch"

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        result = ArchitectureResult(model_calls=1)
        try:
            scene = build_scene(case.source_svg)
            gold = derive_patch(case.source_svg, case.answer_svg)
            targets = sorted({target for operation in gold.operations for target in operation.targets})
            context = {
                "known_correct_targets": targets,
                "scene": scene,
            }
            response = model.generate(
                ModelRequest(
                    patch_prompt(
                        case.instruction,
                        "SVG skeleton with oracle target IDs",
                        json.dumps(context, indent=2, sort_keys=True),
                    ),
                    metadata={"request_id": case.case_id},
                )
            )
            result.raw_responses.append(response.text)
            result.patch = parse_patch(response.text)
            validate_patch(result.patch, scene, PatchPolicy(), task=case.task)
            result.output_svg = apply_patch(case.source_svg, result.patch)
        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
        return result


class TwoStagePatchArchitecture(Architecture):
    name = "two_stage_patch"

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        result = ArchitectureResult(model_calls=2)
        try:
            scene = build_scene(case.source_svg)
            scene_text = json.dumps(scene, indent=2, sort_keys=True)
            selection_prompt = f"""Identify the smallest SVG patch intent and target nodes.
Return only JSON with keys `operation`, `targets`, and `attributes`.
Do not emit SVG. Do not modify path geometry.

Instruction:
{case.instruction}

SVG skeleton:
{scene_text}
"""
            selection_response = model.generate(
                ModelRequest(
                    selection_prompt,
                    metadata={"request_id": f"{case.case_id}:select"},
                )
            )
            result.raw_responses.append(selection_response.text)
            selection = extract_json_object(selection_response.text)

            final_context = json.dumps(
                {"scene": scene, "stage_one_selection": selection},
                indent=2,
                sort_keys=True,
            )
            patch_response = model.generate(
                ModelRequest(
                    patch_prompt(case.instruction, "Stage-one selection and SVG skeleton", final_context),
                    metadata={"request_id": f"{case.case_id}:patch"},
                )
            )
            result.raw_responses.append(patch_response.text)
            result.patch = parse_patch(patch_response.text)
            validate_patch(result.patch, scene, PatchPolicy(), task=case.task)
            result.output_svg = apply_patch(case.source_svg, result.patch)
        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
        return result
