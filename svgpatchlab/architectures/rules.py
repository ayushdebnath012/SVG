from __future__ import annotations

import re

from svgpatchlab.core import Patch, PatchOperation, apply_patch, build_scene, validate_patch
from svgpatchlab.models import ModelAdapter
from svgpatchlab.types import ArchitectureResult, BenchmarkCase

from .base import Architecture


_SOURCE_COLOR = re.compile(r"with a (#[0-9A-Fa-f]+) color")
_TARGET_COLOR = re.compile(
    r"\bto (red|green|blue|yellow|cyan|magenta|white|black)\b",
    re.IGNORECASE,
)


class RuleBasedPatchArchitecture(Architecture):
    """Non-LLM baseline for the benchmark's canonical simple instructions."""

    name = "rule_based_patch"
    requires_model = False

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        try:
            scene = build_scene(case.source_svg)
            operation: PatchOperation | None
            if case.task in {"change_color", "set_contour"}:
                source_match = _SOURCE_COLOR.search(case.instruction)
                if not source_match:
                    raise ValueError("instruction does not identify a source color")
                source_color = source_match.group(1)
                targets = tuple(
                    node["id"]
                    for node in scene["nodes"]
                    if node.get("attributes", {}).get("fill") == source_color
                )
                if not targets:
                    raise ValueError(f"no nodes use source color {source_color}")
                if case.task == "change_color":
                    target_match = _TARGET_COLOR.search(case.instruction)
                    if not target_match:
                        raise ValueError("instruction does not identify a target color")
                    attributes = (("fill", target_match.group(1).lower()),)
                else:
                    attributes = (("stroke", "black"), ("stroke-width", "1"))
                operation = PatchOperation("set_attributes", targets, attributes)
            elif case.task == "upside_down":
                operation = PatchOperation(
                    "set_attributes",
                    ("n0",),
                    (("transform", "translate(0,36) scale(1,-1)"),),
                )
            elif case.task == "transparency":
                operation = PatchOperation("set_attributes", ("n0",), (("opacity", "0.5"),))
            elif case.task == "crop_to_half":
                operation = PatchOperation("set_attributes", ("n0",), (("viewBox", "0 0 18 36"),))
            elif case.task == "compression":
                operation = None
            else:
                raise ValueError(f"unsupported task: {case.task}")

            patch = Patch(()) if operation is None else Patch((operation,))
            validate_patch(patch, scene, task=case.task)
            return ArchitectureResult(output_svg=apply_patch(case.source_svg, patch), patch=patch)
        except Exception as exc:
            return ArchitectureResult(error=f"{type(exc).__name__}: {exc}")
