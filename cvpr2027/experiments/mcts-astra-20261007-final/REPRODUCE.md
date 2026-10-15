# Reproduction and audit

The completed run is frozen; replaying paid generation requires a new budget authorization. Credentials are entered through hidden interactive prompts and are not included in this archive.

From the repository root, inspect `run_mcts_astra.py --help`. The completed configuration used `--budget 5 --calls-per-task 4 --prompt-api-key` and the saved development-only calibration (`--calibration .../calibration.json`). The worker requires the pinned original verifier adapter and an SSH connection to the experiment server. Task order is seeded at 17; API generation itself is not seeded.

Audit selections using `audit_mcts_astra.py`; score using `score_mcts_astra.py`; export paper macros and figures using `mcts_paper_results.py`. These scripts use the repository's original baseline/development artifact locations. Reference scores are offline only. All final prediction strings matched the saved baseline, so final native-geometry scores were reused.

The selected prediction digest and audit precede reference scoring. See `selection-audit.json`, `implementation-sha256.json`, `PROTOCOL.md`, and `RESULTS.md`. Pricing is an estimate, not an invoice. The total including preflight is $3.258853.
