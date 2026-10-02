# Void run: prompts omitted the data-level contract

Two samples were collected before this run was stopped. Its prompts lacked the
`STATUS_LINE` clause that `astra_hard_tasks.build_references` appends to every 18 September
prompt, so the model was never asked to put `data-level` on its contours and the scorer found
nothing to measure. The drawings themselves are not evidence of failure and must not be scored.

Recorded usage: 592 input and 17,236 completion tokens across 2 attempts, about $0.87 at list
prices. Kept for provenance only. `polyheat_bench.verify` now checks the manifest prompt against
the 18 September manifest prompt character-for-character, which catches this class of error.
