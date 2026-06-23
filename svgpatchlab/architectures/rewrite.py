from __future__ import annotations

import re

from svgpatchlab.core.xml import parse_svg
from svgpatchlab.models import ModelAdapter
from svgpatchlab.types import ArchitectureResult, BenchmarkCase, ModelRequest

from .base import Architecture
from .prompts import rewrite_prompt


_SVG_FENCE = re.compile(r"```svg\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_svg(text: str) -> str:
    matches = _SVG_FENCE.findall(text)
    if len(matches) == 1:
        svg = matches[0].strip()
    else:
        start = text.find("<svg")
        end = text.rfind("</svg>")
        if start < 0 or end < 0:
            raise ValueError("response does not contain an SVG")
        svg = text[start : end + len("</svg>")].strip()
    parse_svg(svg)
    return svg


class FullRewriteArchitecture(Architecture):
    name = "full_rewrite"

    def run(self, case: BenchmarkCase, model: ModelAdapter) -> ArchitectureResult:
        result = ArchitectureResult(model_calls=1)
        try:
            response = model.generate(
                ModelRequest(
                    rewrite_prompt(case.instruction, case.source_svg),
                    metadata={"request_id": case.case_id},
                )
            )
            result.raw_responses.append(response.text)
            result.output_svg = extract_svg(response.text)
        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
        return result

