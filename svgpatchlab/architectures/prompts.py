from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from string import Template


PATCH_PROMPT_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "prompt_templates"
PATCH_PROMPT_VERSION = 3
PATCH_PROMPT_VERSIONS = (1, 2, 3)

# Active v3 is intentionally zero-shot. Tiny models copied concrete constants
# from v2 examples, especially crop viewBox values, so the baseline prompt now
# uses generic rules and formulas only.
PATCH_EXAMPLES: tuple[dict, ...] = ()

PATCH_V2_EXAMPLES = (
    {
        "instruction": "Add a navy outline two units wide around every shape filled #D97706.",
        "context": (
            'n0 svg viewBox="0 0 48 48"; '
            'n1 path fill="#D97706"; n2 circle fill="#D97706"; '
            'n3 path fill="#1F2937"'
        ),
        "output": {
            "version": 1,
            "operations": [
                {
                    "op": "set_attributes",
                    "targets": ["n1", "n2"],
                    "attributes": {"stroke": "#1E3A8A", "stroke-width": "2"},
                }
            ],
        },
    },
    {
        "instruction": "Make the entire image 40 percent opaque.",
        "context": 'n0 svg viewBox="0 0 64 32"; n1 g; n2 path fill="#14B8A6"',
        "output": {
            "version": 1,
            "operations": [
                {
                    "op": "set_attributes",
                    "targets": ["n0"],
                    "attributes": {"opacity": "0.4"},
                }
            ],
        },
    },
    {
        "instruction": "Flip the whole image upside down.",
        "context": 'n0 svg viewBox="0 0 24 24"; n1 path fill="#A855F7"',
        "output": {
            "version": 1,
            "operations": [
                {
                    "op": "set_attributes",
                    "targets": ["n0"],
                    "attributes": {"transform": "translate(0,24) scale(1,-1)"},
                }
            ],
        },
    },
    {
        "instruction": "Trim the right half and keep the left half.",
        "context": 'n0 svg viewBox="10 5 80 40"; n1 rect fill="#0EA5E9"',
        "output": {
            "version": 1,
            "operations": [
                {
                    "op": "set_attributes",
                    "targets": ["n0"],
                    "attributes": {"viewBox": "10 5 40 40"},
                }
            ],
        },
    },
)


@lru_cache(maxsize=None)
def _load_template(name: str) -> Template:
    return Template((PATCH_PROMPT_TEMPLATE_DIR / name).read_text())


def _format_patch_examples(examples: tuple[dict, ...]) -> str:
    blocks = []
    for index, example in enumerate(examples, start=1):
        blocks.append(
            f"Example {index}\n"
            f"Instruction: {example['instruction']}\n"
            f"Relevant context: {example['context']}\n"
            f"Output: {json.dumps(example['output'], separators=(',', ':'))}"
        )
    return "\n\n".join(blocks)


def patch_prompt(
    instruction: str,
    context_name: str,
    context: str,
    version: int = PATCH_PROMPT_VERSION,
) -> str:
    if version not in PATCH_PROMPT_VERSIONS:
        raise ValueError(f"unknown patch prompt version: {version}")
    examples = _format_patch_examples(PATCH_V2_EXAMPLES) if version == 2 else ""
    return _load_template(f"patch_v{version}.txt").substitute(
        version=version,
        instruction=instruction,
        context_name=context_name,
        context=context,
        examples=examples,
    )


def rewrite_prompt(instruction: str, svg: str) -> str:
    return _load_template("rewrite.txt").substitute(instruction=instruction, svg=svg)
