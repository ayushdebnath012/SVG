from __future__ import annotations

import json
from string import Template

from svgpatchlab.core import build_scene
from svgpatchlab.models.base import ModelAdapter
from svgpatchlab.types import ModelRequest

DECOMPOSE_PROMPT = Template("""\
You are an SVG edit planner. Break the following complex edit instruction into an
ordered list of simple atomic steps. Each step must be one of these task types:
change_color, set_contour, upside_down, transparency, crop_to_half, rotate, flip, delete.

Return exactly one JSON object with a single key "steps", whose value is an array.
Each element has:
  - "task": one of the task types above
  - "instruction": a self-contained natural-language instruction for that step

Do not include any other keys or explanation.

Complex instruction:
$instruction

Current SVG skeleton:
$skeleton
""")


class DecomposerModel:
    """Converts a complex edit instruction into an ordered list of atomic task steps.

    Plan C Stage 1: the decomposer model. Before training, this uses the base
    language model zero-shot. After SFT + GRPO (train/sft_decomposer.py and
    train/grpo_decomposer.py), the same adapter interface is used with the
    fine-tuned checkpoint.

    Usage::

        decomposer = DecomposerModel(model_adapter)
        steps = decomposer.decompose("make background blue and flip upside down", svg)
        # [{"task": "change_color", "instruction": "..."}, {"task": "upside_down", ...}]
    """

    def __init__(self, model: ModelAdapter, max_steps: int = 4):
        self.model = model
        self.max_steps = max_steps

    def decompose(self, instruction: str, svg: str) -> list[dict[str, str]]:
        """Return list of {"task": task_type, "instruction": sub_instruction}."""
        from svgpatchlab.core.patch import PatchError, extract_json_object

        scene = build_scene(svg)
        skeleton_text = json.dumps(scene, indent=2, sort_keys=True)
        prompt = DECOMPOSE_PROMPT.substitute(
            instruction=instruction,
            skeleton=skeleton_text,
        )
        response = self.model.generate(ModelRequest(prompt, metadata={"role": "decomposer"}))
        try:
            payload = extract_json_object(response.text)
        except PatchError as exc:
            raise ValueError(f"decomposer returned invalid JSON: {exc}") from exc

        steps = payload.get("steps")
        if not isinstance(steps, list):
            raise ValueError("decomposer response missing 'steps' list")
        validated: list[dict[str, str]] = []
        for item in steps[: self.max_steps]:
            if not isinstance(item, dict):
                continue
            task = item.get("task", "")
            instr = item.get("instruction", "")
            if task and instr:
                validated.append({"task": str(task), "instruction": str(instr)})
        return validated
