# Direct Astra baseline on the controlled-editing pilot

17 September 2026. The prompt-only control that the experiment protocol (P04/P05)
requires was run: `gpt-6-astra` was given the controlled-editing pilot's exact
system prompt and compact-DOM input, with no examples, no image and no
fine-tuning, one sample per example, and was scored by the same
`score_action` evaluator as the LoRA runs and the rule parser.

**Result: 60/60 strict exact actions on the test split and 60/60 on the
held-out annulus split.** Every response was a bare JSON object (no Markdown
fences), every call finished with `finish_reason=stop`, there were no API
errors or retries, and the model reported zero reasoning tokens at
`reasoning_effort=low`. Median wall time 1.98 s per call (1.35–4.99 s).
Usage: 48,831 input and 2,373 completion tokens, about **$0.61** at the
documented $10/$50 per million list prices.

| Model / policy | Test strict exact action | Annulus strict exact action |
|---|---:|---:|
| Base Qwen2.5-Coder-1.5B, each seed | 0/60 | 0/60 |
| Final LoRA, seeds 17 / 29 / 41 | 60/60 | 60/60 |
| Deterministic template parser | 60/60 | 60/60 |
| **Direct Astra, zero-shot (this run)** | **60/60** | **60/60** |

Per-task exact rates are 1.0 for all six actions on both splits
(`recompute`, `style:stroke`, `style:stroke-width`, `move_label`,
`reject:numerical_claim`, `reject:missing_required_contour`); `unsafe_edit`
is 0.0 on both splits.

## What this establishes

This is the benchmark reference point for the pilot task: a frontier model
solves it completely with a prompt alone. Together with the perfect rule
parser, it closes the question the protocol asked before any training study
(P05): on the shared-template pilot there is **no gap for learning to fill**,
and hypothesis H4 ("learning helps on context-dependent, visually grounded
edits") cannot be tested here. The LoRA pilot therefore remains pipeline
validation, and the next training study must wait for the harder collection
of P03, where instructions require context beyond keyword routing and where
templates, geometry families and honest counterfactuals are held out.

Limits of this run: ten independent physical cases per split; one sample per
example; a single effort setting and model alias on one day; no image input
and no full SVG (the compact-DOM input hides the geometry, so this measures
instruction routing, not drawing understanding). A repeat on a later date may
resolve the alias differently.

## Records

- `runs/astra-controlled-editing-20260918/protocol.json`: model, endpoint,
  effort, token cap, system-prompt SHA-256, scorer.
- `runs/astra-controlled-editing-20260918/generations.jsonl`: all 120
  predictions with targets, metrics, usage, response IDs and timing.
- `runs/astra-controlled-editing-20260918/responses/*.json`: raw API responses.
- `runs/astra-controlled-editing-20260918/summary.json`: per-split metrics,
  per-task rates, usage and cost estimate.

Repeat (billable; use a fresh output directory so no evidence is overwritten):

```sh
../.venv/bin/python scripts/eval_controlled_astra_api.py --output runs/astra-controlled-editing-<date>
```

The script resumes an interrupted run without re-billing completed examples
and refuses to continue into a directory whose protocol differs.
