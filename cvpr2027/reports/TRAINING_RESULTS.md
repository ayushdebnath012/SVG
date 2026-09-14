# Verified A100 training results

Three Qwen2.5-Coder-1.5B-Instruct LoRA runs completed on an NVIDIA A100-SXM4-40GB: seeds 17, 29 and 41, three full epochs and 90 optimizer steps each. Adapter weights, final/previous optimizer checkpoints, exact data, raw predictions, package versions and source hashes are saved locally in `runs/a100/`. Final adapters, predictions and manifests are versioned in this branch; intermediate optimizer checkpoints and ZIP downloads remain local ignored files. The original downloaded archive is `runs/a100-completed.zip` (350,830,393 bytes).

`scripts/summarize_training.py` verified completion, data and source hashes, case-disjoint splits, all 720 raw base/final predictions, and the three safetensors adapter structures. Each adapter contains 4,358,144 parameters. Model revision: `2e1fd397ee46e1388853d2af2c993145b0f1098a`. The separate saved-adapter inference reload check was prepared but was **not run** before Colab disconnected; no reload result is claimed.

| Model / policy | Test strict exact action | Annulus strict exact action | Test fence-normalized | Annulus fence-normalized |
|---|---:|---:|---:|---:|
| Base Qwen, each seed | 0/60 | 0/60 | 26/60 | 25/60 |
| Final LoRA, seed 17 | 60/60 | 60/60 | 60/60 | 60/60 |
| Final LoRA, seed 29 | 60/60 | 60/60 | 60/60 | 60/60 |
| Final LoRA, seed 41 | 60/60 | 60/60 | 60/60 | 60/60 |
| Deterministic template parser | 60/60 | 60/60 | 60/60 | 60/60 |

Training plus adapter-save times were 94.94, 98.61 and 99.42 seconds respectively; these exclude base/final evaluation and environment/model setup. The live notebook and logs retain the complete execution record. No cost estimate is inferred from these timings.

The strict base score is heavily affected by Markdown JSON fences. The separate normalization measure removes only one enclosing fence; it does not choose a convenient object from malformed or multiple-object responses. The base also makes action errors, so normalization does not make it perfect.

This is a compact-DOM, shared-template action policy, not a trained FEM solver or vision model. Each evaluation split contains only ten independent physical cases, with six edits each. Repeated seeds do not increase the number of independent test cases. The perfect rule baseline makes the result pipeline validation, not evidence that learning is needed. The next engineering study is described in the [FEM literature and extension report](FEM_LITERATURE_AND_EXTENSION.md).

## Provenance and recovery

An initial three-seed A100 run finished but lost its temporary weights before download. Its notebook/console logs are preserved as `runs/a100-first-run-*`; those logs are not counted as three additional independent experiments. The recovery run repeated the same configuration and downloaded automatically on completion. The verified results above refer only to the recovered, locally saved artifacts. An earlier T4 attempt was interrupted and is retained separately.

The GPU-generated JSONL bytes differ from the original local data because numerical-library serialization differs. Every model input and target matches the local splits; all three GPU runs have identical split hashes. Use the exact data inside each GPU run to reproduce hashes and executor scoring.

Recheck from `cvpr2027/`:

```sh
../.venv/bin/python scripts/summarize_training.py --runs runs/a100 --output reports/training_verified.json
```

Machine-readable evidence: `reports/training_verified.json`. Completed notebook: `notebooks/A100_completed_runs.ipynb`. The Colab runtime is disconnected; no GPU training remains active.
