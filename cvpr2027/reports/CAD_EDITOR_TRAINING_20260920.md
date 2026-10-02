# Released CAD-Editor data: completed training pilot

**One-epoch LoRA training completed on the supplied server.** On 32 fixed held-out
CAD edit requests, exact target-sequence matches improved from **1/32 (3.125%)**
to **6/32 (18.75%)**. Five cases improved and none lost an exact match. This is a
small feasibility result; 26 of 32 targets still do not match exactly. Neither
geometric correctness nor SVG/engineering correctness has been measured here.

| Same 32 test requests | Copy original sequence | Base Qwen | Trained Qwen |
|---|---:|---:|---:|
| Exact normalized target match | 0/32 | 1/32 | 6/32 |
| Mean character-sequence similarity | 0.7053 | 0.4849 | 0.8304 |
| Generation token-limit hits | Not applicable | 3 | 0 |

Similarity can reward copying unchanged geometry and is not a CAD-validity
metric. The copy baseline makes this limitation visible. All base/final cases,
including truncated base predictions, are included in the denominator. Final
checkpoint selection is fixed to one epoch, not chosen using test scores.

## Data and lineage

The training source is the released [CAD-Editor, ICML 2025](https://github.com/microsoft/CAD-Editor)
`data/processed.zip`, not hand-written task templates. The archive contains
120,000 training and 2,000 test records. Its SHA256 is
`98d01e2b1881f44f38518e43cad7796904ce4a795785569f3e48b87160107f4f`.

The bounded subset uses 2,048 train / 128 validation / 128 test pairs. All exact
normalized source/target sequences are grouped into connected components across
the full archive before splitting. Any component touching official test is
excluded from train and validation. Remaining components are assigned to train
or validation by stable hash, then subsampled with seed 17. Train/validation/test
have 1,504 / 111 / 121 selected components respectively, with no shared component.
The source lacks native design IDs; equivalent geometry with different sequences
may overlap. These splits do not establish geometric generalization.

Inputs are original construction sequences plus edit instructions; targets are
complete edited sequences. They cover add, modify and delete operations. All
2,304 selected examples fit the runner's length limits; none were omitted or
truncated for training. The generation check uses the first 32 test examples in
the previously shuffled manifest. No Astra discovery task enters training.

## Run configuration and evidence

- GPU: NVIDIA RTX PRO 6000 Blackwell on the user-supplied training server.
- Model: Qwen/Qwen2.5-Coder-1.5B-Instruct, cached revision
  `2e1fd397ee46e1388853d2af2c993145b0f1098a`.
- One epoch, 128 optimizer steps, seed 17, BF16, completion-only loss; LoRA rank
  16, alpha 32, dropout 0.05 on q/k/v/o projections; learning rate 0.0002,
  cosine schedule, effective batch size 16. Maximum sequence length 3,072 tokens.
- Greedy before/after generation, identical prompts and 1,536-token output cap.
- Training runtime: 78.27 seconds; training plus final evaluation: 98.35 seconds.
  Validation completion loss: 0.11448. Single seed; no uncertainty estimate.
- Runtime: PyTorch 2.11.0+cu130, Transformers 4.51.3, PEFT 0.15.2. Full package
  versions and runtime warnings are retained in the saved logs.

The final adapter, tokenizer, manifest, metrics, raw predictions, training log,
exact runner snapshot and artifact hashes were retrieved locally. The remote
run is `svg-compute/cad-editor-20260920`; the optimizer checkpoint also remains
there. No API credential was transferred for this local-model training.

- [Local run artifacts](../runs/cad-editor-20260920/)
- [Final LoRA adapter](../runs/cad-editor-20260920/run/adapter/)
- [Run manifest](../runs/cad-editor-20260920/run/run_manifest.json)
- [Paired evaluation and copy-baseline audit](../runs/cad-editor-20260920/run/evaluation_audit.json)
- [Data provenance](../data/cad-editor-pilot/manifest.json)
- [Training runner](../scripts/train_cad_editor_pilot.py)

The next required link is to execute source/edited CAD, export corresponding
SVG views and attach task-appropriate checks. Only then can training improvements
be assessed on the requested CAD drawing and physical-editing objective. This
pilot does not replace that work or produce a populated Astra-failure benchmark.
