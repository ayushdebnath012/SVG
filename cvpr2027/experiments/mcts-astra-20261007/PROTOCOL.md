# Bounded Astra MCTS pilot

Approved incremental API cap: $5. Same 124 held-out BenchCAD tasks and same frozen Qwen 1.5B GRPO-verifier adapter as the completed 89/124 to 91/124 experiment. Search is gated on the same 60 initial verifier rejections; the 64 accepted initial answers are unchanged.

Search: seed-17 task order, four new API attempts per searched task, branching width two, maximum depth two, UCT exploration 0.7. A root contains the saved initial Astra patch. Each new child is an alternative complete patch against the original source; no reference geometry, reference code or correctness label reaches Astra or the policy. Terminal rollout value comes from live target-free tools and the frozen verifier after both observations. A deterministic terminal value can be replayed; backup changes only the traversed tree path. Identical candidate observations can be cached, but tree statistics remain separate.

Calibration is fixed using the 238 component-disjoint development candidates before paid held-out sampling. L2 Platt calibration maps terminal accept probability to a correctness proxy. Numeric-check weight in {0, 0.1, 0.2} and the eligibility threshold maximize development balanced accuracy with deterministic ties. CAD execution validity is required. Each depth incurs a fixed 0.005 proxy penalty. A child replaces the root only if eligible and strictly higher-scored; otherwise the original is retained. This classifier is imperfect and is not a certificate of target agreement.

API: gpt-6-astra, low reasoning, maximum 2,500 completion tokens, three concurrent calls, four round-robin passes over search tasks. Budget reservation uses request bytes plus the maximum completion allowance at the existing recorded $10/$50 per-million price estimates. Any uncertain failed attempt reserves its worst-case estimate. No failed attempts are silently retried.

Selections are saved before released STEP references are opened by the separate scoring script. Report all 124 tasks and 123 valid references, gains and losses against Astra and the previous one-repair experiment, category/edit tiers, p-values, API errors, cost and candidate counts. One seed only. Comparisons are not equal-compute; no claim that MCTS itself causes a gain without equal-budget sampling/tree/graph controls.

Preparation issue: the first model-worker launch used a cache directory missing the pinned 1.5B weights; it was corrected to the existing user cache before calibration or any API call.
