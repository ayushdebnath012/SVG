from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from svgpatchlab.models.base import ModelAdapter
from svgpatchlab.types import ArchitectureResult, BenchmarkCase


@dataclass
class ChainResult:
    output_svg: str | None
    step_results: list[ArchitectureResult] = field(default_factory=list)
    errors: list[str | None] = field(default_factory=list)
    steps_attempted: int = 0
    steps_succeeded: int = 0


class ChainExecutor:
    """Executes a decomposed plan step by step, feeding each output to the next.

    Plan C Stage 2: the chain executor. Each step uses the existing
    skeleton_patch architecture (or any registered architecture). If a step
    fails validation or the model returns invalid JSON, the step is skipped
    and execution continues with the remaining steps using the last valid SVG.

    Usage::

        executor = ChainExecutor(model=patch_model)
        result = executor.execute(svg, steps=[
            {"task": "change_color", "instruction": "Change red to blue"},
            {"task": "transparency", "instruction": "Make it 50% opaque"},
        ])
    """

    def __init__(self, model: ModelAdapter, architecture_name: str = "skeleton_patch"):
        self.model = model
        self.architecture_name = architecture_name

    def execute(self, svg: str, steps: list[dict[str, str]]) -> ChainResult:
        from svgpatchlab.architectures.factory import create_architecture
        from svgpatchlab.types import BenchmarkCase
        from pathlib import Path

        result = ChainResult(output_svg=svg, steps_attempted=len(steps))
        current_svg = svg

        for step in steps:
            architecture = create_architecture(self.architecture_name)
            # Wrap step as a minimal BenchmarkCase (no answer_svg needed for execution)
            case = BenchmarkCase(
                task=step["task"],
                emoji_id="chain",
                instruction=step["instruction"],
                source_svg=current_svg,
                answer_svg=current_svg,
                query_path=Path("."),
                answer_path=Path("."),
            )
            step_result = architecture.run(case, self.model)
            result.step_results.append(step_result)
            result.errors.append(step_result.error)

            if step_result.output_svg is not None:
                current_svg = step_result.output_svg
                result.steps_succeeded += 1
            # On failure: keep current_svg unchanged and continue

        result.output_svg = current_svg if result.steps_succeeded > 0 else None
        return result

    def session_execute(
        self,
        svg: str,
        steps: list[dict[str, str]],
        on_step: Any = None,
    ) -> ChainResult:
        """Like execute() but calls on_step(step_index, step_result, current_svg) after each step."""
        from svgpatchlab.architectures.factory import create_architecture
        from svgpatchlab.types import BenchmarkCase
        from pathlib import Path

        result = ChainResult(output_svg=svg, steps_attempted=len(steps))
        current_svg = svg

        for i, step in enumerate(steps):
            architecture = create_architecture(self.architecture_name)
            case = BenchmarkCase(
                task=step["task"],
                emoji_id="chain",
                instruction=step["instruction"],
                source_svg=current_svg,
                answer_svg=current_svg,
                query_path=Path("."),
                answer_path=Path("."),
            )
            step_result = architecture.run(case, self.model)
            result.step_results.append(step_result)
            result.errors.append(step_result.error)

            if step_result.output_svg is not None:
                current_svg = step_result.output_svg
                result.steps_succeeded += 1

            if on_step is not None:
                on_step(i, step_result, current_svg)

        result.output_svg = current_svg if result.steps_succeeded > 0 else None
        return result
