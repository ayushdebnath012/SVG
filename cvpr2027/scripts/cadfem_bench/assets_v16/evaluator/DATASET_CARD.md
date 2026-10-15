# CADFEM-Bench v1.6 - complete source-backed pilot package

**57 primary tasks, 123 published numerical targets, 11 engineering families.** Track A has 51 supplied-CAD tasks; track B has six drawing/specification-to-CAD tasks. The source-backed pool has 128 active tasks across the separately scored suites. Fourteen primary tasks have independent reproduction evidence; scoring reports this subset separately.

This release completes the dataset package and evaluation tooling. It does not establish a fully validated engineering leaderboard: 43 primary tasks still lack independent reproduction, many tolerances remain provisional, and full physics/workflow review remains necessary.

## Dataset composition

| suite | tasks | purpose |
|---|---:|---|
| Primary | 57 | model comparison; no family exceeds eight tasks |
| Calibration | 7 | NAFEMS and tensile-bar controls; separate scores |
| Reserved public | 63 | evaluator-only public-source cases; not guaranteed unseen |
| Related public | 1 | shares primary CAD and cannot serve as independent hold-out |
| Held | 55 | inactive; reasons and original inputs retained |
| Contact source review | 1 CAD/results pair | validated correspondence but failed mesh convergence; not a scored task |

Family labels do not imply independent engineering problems. AgentFEM, GeoPINO and SimJEB bracket/plate families contribute 24/57 tasks (42.1%). The cap changed from five to eight to meet the requested minimum of 50 primary tasks using existing published cases. Macro-averages and per-family results remain available. Selection preserves the earlier primary tasks and adds eligible source cases by reproduction readiness and a fixed task-ID hash, with no model-performance selection.

## Original CAD and results

Candidate inputs contain the original source CAD or its previously documented format/unit conversion. No new supplied-CAD geometry or numerical target is generated in this release. The evaluator's evidence bundle links every scored task to exact source files and checksums. The five existing FEMCAD specification tasks retain hidden geometry reconstructed from the source specification solely for validation; that geometry is explicitly labeled in the atlas and is never described as original published CAD.

The four v1.5 interface-crack tasks were moved to held: their supplied CAD was constructed locally from specifications, and several G targets were derived locally from published factors. Their evidence is preserved, but they are excluded from the original-web-CAD-only active pool. The source-backed plastic-collapse ring remains admitted with its independent convergence evidence.

`report/cadfem-bench-v1.6.pdf` is an evaluator atlas: an overview plus a CAD/drawing view, source numerical results, units and provenance for every primary task. It contains answers; do not supply it to models.

## Additional complex engineering collections

Six additional original source collections are bundled in evaluator/source-review/complex-engineering/: a 26-body nonlinear pneumatic gripper, 15-part landing gear, crank mechanism, connecting rod, finned heatsink and layered composite pipe. CAD, drawings/reports, original plots and available saved FEM/archives are included with source manifests and specific hold reasons. They add no scored task until setup, units, geometry correspondence and solver validation are established. The gripper raw RST is preserved inside the original WBPZ archive, avoiding a duplicate 1.43 GB extraction.

## Model/evaluator separation

Give models only `candidate/` or a task-specific export produced by `export_run.py`. Evaluator references, source solution files, held/source-review data, the report and this full archive contain answers. Public-source CAD and source URLs can still have appeared in training data. A reserved web-source split cannot guarantee an unpublished contamination-resistant hold-out.

Both tracks require the same eight artifacts described in candidate/README.md. Correct scalars alone never count as a workflow pass. The scorer separates numerical accuracy, trusted workflow approval, engineering-family results and the reproduced subset.

## Common offline replay

Each generation attempt is frozen and replayed in a fresh job. Runtime budgets are 600 s wall time, 600 s CPU per process, 8 GiB observed process-group RAM and two numerical threads, with one attempt and no automatic retry. Record exact provider/model version, settings, modalities, tokens, cost and timing in the generation manifest. The package is provider-neutral; model generation is performed outside the solver sandbox. No frontier API call or human expert baseline is claimed.

```sh
python evaluator/export_run.py --package . --out ../model-inputs --model-id YOUR_EXACT_MODEL_ID --run-id trial-001
python evaluator/sandbox_runner.py prepare --package . --job ../job-001 --task-id A-CYC-Coupler-PETGCF --submission ../submission --model-id YOUR_EXACT_MODEL_ID --run-id trial-001
python evaluator/sandbox_runner.py replay --package . --job ../job-001 --backend macos --python /path/to/trusted/python
python evaluator/score.py --refs evaluator/references.jsonl --tasks candidate/tasks.jsonl --submissions ../runs/model --run-id trial-001 --out ../score.json
```

The macOS sandbox denies evaluator/home data reads, outbound network, hard links, input mutation and writes outside output/cache/tmp. System data outside the home directory remains readable; this is not claimed as production-grade arbitrary-code isolation. An optional operator-trusted `--extra-runtime /path/to/calculix-env` grants read-only access to an isolated software prefix and records binary/package hashes. It cannot overlap the package/job. Do not supply private data in a runtime prefix.

Docker requires an already installed digest-pinned image, network disabled and read-only mounts. That backend is prepared but untested on this machine. MPI-based FEniCS runtimes are not certified in the tested macOS mode; serial CalculiX is the available additional solver. Every model in a comparison must receive the same runtime/tool access.

## Validators and actual evidence

The geometry scorer enforces six reconstruction gates, with analytic sphere/cylinder radii for FEMCAD and source-shape overlap for rigging. `verify_static_fields.py` independently reassembles the cycloidal elastic operator and rejects a displacement field perturbed by 0.1%; it does not audit every CAD-face/tag relation or certify convergence. `validate_shell_geometry.py` checks the two original contact cylinders using axes, radii and Boolean surface coverage; it is standalone and not an admitted contact workflow scorer.

The contact follow-up contains original CAD, saved FEM fields, reconciled native force units and a real CalculiX 2.23 deck replay. The source displacement is 69.691102 mm; replay gives 69.773736 mm. Five independent remeshes reach 83.948853 mm, 20.46% above the source, with a 5.02% final mesh change. The case stays held; no new solver value becomes a target and no tolerance is widened to make it pass.

Full geometry/setup/field extraction/convergence approval still follows evaluator/REVIEW_PROTOCOL.md. Neither successful execution nor a few plausible files fabricate a trusted review.

## Files and rebuilding

- candidate/: model-visible primary prompts, CAD/spec inputs, submission schema.
- evaluator/: references, scoring/replay/validators, source evidence, manifests, suites, review protocol and verification.
- held/: inactive cases and explicit reasons.
- report/: complete CAD/results atlas, evaluator-only.
- scripts/cadfem_bench/: build, report, verification and packaging tools; legacy scripts are historical and must not be used to rebuild this release.
- SHA256SUMS.txt: checksums of all package files.

Build from the preserved v1.5 and contact follow-up: `release_v16.py --source <v1.5> --out <fresh-folder> --contact <contact-followup>`, then `finalize_v16.py --package <fresh-folder> --python <trusted-CAD-runtime>`. The original workspace provides the pinned toolchain and source evidence; copying the full archive does not install solver dependencies.

Source rights differ, including local-research-only material. Original notices remain bundled. Do not publish the entire mixed-license archive as though it had a single permissive dataset license. No git commit or external publication is performed.
