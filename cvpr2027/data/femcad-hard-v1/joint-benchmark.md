# One end-to-end CAD+FEM benchmark

The intended task is one chain: **published drawings/specifications → candidate-built CAD → mesh from that CAD → FEM on that mesh → computed results**. There are no separate CAD and FEM leaderboards in this protocol. Stage diagnostics help identify why a joint attempt fails.

## Current release status

**50 joint task drafts are prepared; zero are certified for scored release.** The earlier 42 unblocked packages measured source-assisted reproduction with geometry files and recipes supplied. That count does not transfer to this stricter task.

The new candidate files contain 177 original source images/equations and 32 source specification files. They contain no STEP, MPH, MPHBIN, imported CAD, airfoil coordinate files, published solution files, numerical answer tables, or step-by-step construction instructions. Source model-definition sections, constitutive equations, original drawings and allowed parameter/material/load tables are retained. Study 030 additionally uses a reviewed original geometry-only image from the setup section, with all surrounding instructions removed. No dimensions, engineering tasks, drawings, numerical solutions or thresholds were invented.

This remains a public-source collection. Removing local answers does not demonstrate that a model has never encountered the source tutorials during training.

## Artifacts

- [Per-study audit and provenance](joint-benchmark.json): all 50 studies, retained source blocks, original asset hashes, individual notes and blockers. Evaluator-only; do not send this catalog to candidates.
- `tmp/femcad-joint-benchmark/candidate-inputs/FEMCAD-ADV-NNN/`: one candidate directory containing `task.json`, `problem.html`, source images and permitted specification tables. The task manifest embeds the submission schema.
- `tmp/femcad-joint-benchmark/evaluator-only/FEMCAD-ADV-NNN/contract.json`: private reference/acceptance contract. Missing targets and tolerances are explicitly null, and release approval is false.
- Existing `tmp/femcad-evaluation/held-out/`: the original published references, numerical tables and solver-model inventories. Original CAD assets remain in the source-assisted collection for evaluators; they are not copied into the joint candidate inputs.
- [Validation report](joint-benchmark-validation.json).
- [Submission schema](joint-submission.schema.json).

Supply only one candidate directory to a fresh isolated model context, with network and access to the project, other tasks and evaluator files disabled. Some inputs of study 040 are outputs of study 039, so sharing task context would leak information.

## Candidate submission

`submission.json` identifies six distinct, nonempty artifacts and their SHA-256 hashes:

| Artifact key | Required content |
|---|---|
| `cad_source` | Editable CAD or complete construction code |
| `cad` | STEP geometry, declared units and dimensional formulation |
| `mesh` | Solver-readable mesh built from that CAD |
| `solver_input` | Reproducible FEM model/code using that mesh |
| `results` | Computed numerical fields/curves/scalars with units, coordinates and load/time/frequency steps |
| `solver_log` | Unedited solver log, version, convergence and failure information |

Declare named physical regions with CAD entity IDs and corresponding mesh group IDs. Record CAD→mesh, mesh→solver and solver→results parent hashes, plus reproducible build/mesh/solve instructions. Preserve plane-strain, axisymmetric, shell or mixed formulations where the published task uses them; do not replace them with an invented 3D problem.

Hashes detect inconsistent files. They **do not prove execution or correct geometry-to-mesh association**. A trusted isolated runner must independently replay the submitted construction/meshing/solution process, record the actual inputs consumed at each stage and check the physical-region mapping. The current checker does not execute candidate code and does not claim to supply that runner.

## Joint scoring rule

A joint pass requires all of the following on the same replayed artifact chain:

1. Geometry matches the published task within source-supported, validated criteria: relevant dimensions, features, connectivity, gaps/contact surfaces and physical regions. Import success or a similar-looking image alone is insufficient.
2. FEM preserves the specified materials, units, loads, supports, contacts, couplings and dimensional assumptions.
3. Solver execution converges, with problem-appropriate equilibrium/conservation checks and validated discretization/time-step evidence.
4. Numerical outputs agree with the appropriate held-out reference under validated acceptance criteria at the specified locations and operating points.

No weighted average allows good-looking CAD to compensate for incorrect physics. Missing references, incomplete inputs and unavailable runtime are benchmark infrastructure blocks, not model failures. A candidate crash or invalid submission is recorded separately from a validated numerical mismatch. Report pass@1 only over a frozen, fully eligible task set with declared solver tools, budgets, limits and retry policy.

The four downloaded reference tables are insufficient to validate every output in all 50 studies. Some are experiments: notably the muffler source explains model/experiment differences. Experimental agreement must not be treated as exact solver ground truth. Published plots can support visual diagnostics, but cannot replace field/curve data and validated comparison tolerances.

## What still blocks scoring

Every study needs an audit that its permitted inputs fully determine both geometry and physics. Studies 005, 010, 011, 021, 034 and 048 are prioritized for drawing review because of dimension/scale information; this is not an eligibility certification. Other entries often show rendered geometry rather than sufficient engineering drawings. Exact airfoil coordinates and imported assembly detail cannot be recovered uniquely from illustrations.

The six companion-model dependencies and two conflicting source settings identified in the earlier packaging audit remain unresolved. Removing binary material libraries also exposes additional missing-input questions in the loudspeaker studies. Each is recorded in the joint audit. Missing fields are not filled by guessing.

Reference geometry exports, per-output numerical targets, externally justified tolerances and a compatible trusted solver runner are still required. Source MPH archives containing solutions do not by themselves satisfy those requirements. The final semantic review must also check that the retained problem-definition text contains no answer clues and that all required physical specifications survived filtering.

## Commands

From `cvpr2027/`:

```sh
python3 scripts/build_femcad_joint_benchmark.py
python3 scripts/validate_femcad_joint_benchmark.py
python3 -m unittest discover -s tests -p test_femcad_joint_benchmark.py
```

Inspect an actual candidate submission without executing its code:

```sh
python3 scripts/inspect_femcad_joint_submission.py /path/to/submission \
  --task-id FEMCAD-ADV-011 --output tmp/submission-inspection.json
```

For optional STEP import/entity/area/volume/bounding-box diagnostics, use the installed Gmsh environment:

```sh
tmp/fem-model-pilot-venv/bin/python scripts/inspect_femcad_joint_submission.py \
  /path/to/submission --task-id FEMCAD-ADV-011 --inspect-cad \
  --output tmp/submission-inspection.json
```

The inspector normalizes STEP import to metres and uses documented [Gmsh OpenCASCADE APIs](https://gmsh.info/doc/texinfo/#Namespace-gmsh_002fmodel_002focc). These diagnostics do not certify topology or source agreement. `joint_pass` stays null until independently validated execution and task-specific scoring exist. No model/API request or new FEM solve is part of these preparation/inspection commands.
