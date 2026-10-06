# Agentic CAD verifier + GRPO pilot

Frozen generator: saved GPT-6 Astra first answers, plus at most one new repair per rejected held-out answer. Trainable policy: fresh Qwen2.5-Coder-1.5B-Instruct LoRA. This trains the verifier, not Astra.

The agent chooses among four constrained actions: execute the candidate, check instruction numbers, accept, reject. Tool results are revealed only after the corresponding action; tools cannot repeat. After both tools, only terminal decisions are allowed. This is a small tool-selection/decision policy, not unrestricted generated verifier code.

Training: saved Astra candidates from the local BenchCAD training partition. Group candidate siblings and shared component IDs together in a deterministic training/development split. Original held-out BenchCAD tasks are never training or checkpoint-selection data. Full prompts must fit; no silent truncation.

GRPO: sample eight complete trajectories per candidate from the current policy; normalize terminal rewards within that group; optimize clipped action-probability ratios, averaged by trajectory length, plus exact categorical KL against the frozen initial policy. Two optimization passes per rollout group, clip 0.2, KL coefficient 0.02, seed 17. Correct verdict +1; false acceptance -2; false rejection -1; each tool call costs 0.02. Geometry agreement supplies terminal labels only, never observations. CadQuery validity is not a certificate of instruction satisfaction.

Fixed budget: 120 optimizer groups for a pilot, no test-based tuning. Evaluate fresh and final verifier policies, plus deterministic checks. Report false accept/reject counts and tool calls. Compare Astra alone and Astra with one verifier-guided repair on identical held-out tasks using strict native solid IoU >= 0.99999, with task category breakdown, API failures, reference failures, cost and regressions disclosed. Repair receives only source, instruction, candidate and target-free tool observations. The final verifier chooses repair or original without reference access.

The previous +0.42 pp training-candidate selection result is not this experiment. An existing one-round execution-error-only repair run recovered zero BenchCAD tasks; it is a separate baseline.

## Development-only revision before held-out policy evaluation

Pilot v1 collapsed to unconditional acceptance and its reload check exposed PEFT adapter dtype rounding. Preserve its artifacts as a failed pilot. V2 requires at least one tool before a verdict, balances positive/negative training candidates, uses temperature 1.5 and a 10% uniform mixture over legal actions as part of the optimized policy, and floors reward standard deviation at 0.25 so tiny tool-cost differences do not dominate. Run 600 groups. Restore adapter tensors directly from safetensors after loading to avoid BF16 round-trip loss; verify output equivalence. No held-out verifier scores informed these changes.

V2 stopped at group 14 on a nonfinite gradient with left-padded SDPA batches. V3 uses right padding with the last attended token explicitly gathered, plus nonfinite loss/gradient guards before optimizer updates. Same training/development protocol; no held-out policy evaluation yet.

V3 also stopped on a nonfinite gradient (guard prevented corrupting the optimizer). V4 uses float32 weights/activations and activation checkpointing. These numerical retries do not alter the split or reward. Failed-run logs are retained.

## Evaluation scope and denominators

There are 124 held-out BenchCAD tasks, one with an invalid released reference. Baseline success is 89/124 overall and 89/123 among valid references. Report both. The initial table's description of all 124 as valid references was corrected.

This is a constrained action agent with cached, deterministic target-free tool observations. Training and frozen-policy evaluation replay these observations; they do not measure live tool latency or saved tool computation. Tool-call counts measure observations requested by the policy. New repairs have fresh CAD observations computed in isolated timeout-bounded workers.

Training reward labels use reference-program geometry from the saved teacher audits; held-out success is checked against the pinned author-released STEP solids. Neither kind of reference is passed to the verifier policy or Astra repair requests.

Astra repair calls use the existing Chat Completions interface with external orchestration, not native API tool calls. API request shape checked against https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create . GRPO formulation: https://arxiv.org/abs/2402.03300 .

## Reproduction

- Prepare saved training candidates: `python3 scripts/prepare_agentic_cad_data.py`.
- On a CUDA host with pinned Qwen weights, PyTorch, Transformers, PEFT and safetensors: `python scripts/train_agentic_cad_grpo.py --data DATA_DIR --out FRESH_RUN_DIR --groups 600`.
- Replay held-out target-free observations: `python scripts/eval_agentic_cad_policy.py --data heldout-features.jsonl --adapter FRESH_RUN_DIR/adapter --out decisions.jsonl`.
- With OPENAI_API_KEY configured in the process environment, run `scripts/run_agentic_astra_repairs.py` with explicit data, decisions, output directory and budget arguments. Existing attempt records are not silently retried.
- Evaluate repair features through the same frozen policy; then run `scripts/score_agentic_astra_comparison.py --experiment EXPERIMENT_DIR --repair-decisions REPAIR_DECISIONS_FILE` and `scripts/report_agentic_cad_experiment.py`.

The current implementation is custom action-level GRPO, not a TRL token-generation experiment. Advantages are `(reward - group_mean) / max(group_std, 0.25)`; clipped action ratios use the behavior policy for that group. The 10% uniform exploration mixture is used consistently for behavior sampling and optimized probabilities. Each trajectory averages its action losses; exact categorical KL is computed on each visited state's legal action distribution against the initial frozen policy. Tool outputs are exogenous observations and receive no policy loss.
