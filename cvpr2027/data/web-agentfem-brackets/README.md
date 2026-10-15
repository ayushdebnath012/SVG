---
license: cc-by-4.0
language:
- en
task_categories:
- other
tags:
- finite-element-method
- physics-ai
- neural-operator
- structural-mechanics
- agentfem
size_categories:
- n<1K
pretty_name: AgentFEM Bracket Elasticity
configs:
- config_name: geometry_summary
  data_files:
  - split: train
    path: train.csv
  - split: validation
    path: validation.csv
  - split: test
    path: test.csv
---

# From finite elements to physical AI

![AgentFEM structural family](overview.png)

**176 three-dimensional FEM geometries. Real CAD, meshes and displacement fields.**
An open, reproducible starting point for geometry-conditioned physical learning.

[Interactive lab](https://huggingface.co/spaces/HaomingLuo/AgentFEM-GINO-Structural-Design-Lab) · [Trained model](https://huggingface.co/HaomingLuo/AgentFEM-GINO-Bracket-128) · [AgentFEM](https://github.com/haoming-luo/agentfem) · [AgentFEM-Learning](https://github.com/haoming-luo/agentfem-learning)

## What is inside

A symmetric double-arm support bracket under a uniform downward top-seat load, with fixed foot undersides.
Four parameters vary the arm half-width, half-thickness, waist and bow. Material: linear isotropic elasticity,
E = 70 GPa, nu = 0.33, density = 2700 kg/m³. Height: 189 mm.

**128 training / 16 validation / 32 fresh test geometries.** Nested training prefixes: 32, 64, 128.
The first 64 training cases reuse the existing campaign; 64 new training cases, 4 new validation cases and 32 fresh test cases were computed for this release.

| Files | Contents |
|---|---|
| `train.csv`, `validation.csv`, `test.csv` | Parameters, loads, mass, top-seat displacement, nested prefix order |
| `fields-*.zip` | `fem/<id>/fields.npz` and `summary.json` |
| `geometry-*.zip` | Optional STEP solids and Gmsh tetrahedral meshes |
| `protocol.json` | Frozen split, sampling seeds, bounds and training settings |
| `reproduce.zip` | Geometry generation, AgentFEM campaign, training and evaluation code |
| `evaluation.json`, `learning_curve.csv` | Per-case errors and all three training seeds |

`fields.npz`: `points` (N,3) in metres; `displacement` (N,3) in metres; `stress` (N,) sampled von Mises stress in Pa; `triangles` (F,3) surface connectivity indexing `points`.
**Raw fields retain their physical load**, either 1000 or 10000 N, recorded in each `summary.json`.
Multiply displacement/stress by `target_load_N / physical_load_N` for this linear-elastic problem.
Learning uses a 1000 N reference; the gallery and CSV deflection use 10000 N. Load scaling is not a new independent geometry sample.

## Start with NumPy

```python
from huggingface_hub import hf_hub_download
import io, zipfile, numpy as np
archive = hf_hub_download("HaomingLuo/AgentFEM-Bracket-Elasticity", "fields-test-00.zip", repo_type="dataset")
with zipfile.ZipFile(archive) as z:
    sample = next(n for n in z.namelist() if n.endswith("fields.npz"))
    d = np.load(io.BytesIO(z.read(sample)), allow_pickle=False)
    points, displacement = d["points"], d["displacement"]
```

## Learning curves

![Learning curves](learning_curve.png)

| Training geometries | GINO field error | GINO + correction | Coordinate MLP |
|---:|---:|---:|---:|
| 32 | 30.74% | 7.99% | 6.44% |
| 64 | 30.05% | 5.49% | 4.05% |
| 128 | 24.86% | 3.27% | 2.85% |

Values are mean test surface-node displacement relative L2, averaged over three training seeds.
The same 32 fresh test geometries are used in every row; checkpoints are selected on validation only.
Full per-case, scalar-deflection and baseline results are included. Whiskers show seed range, not confidence bounds.
The inherited 64-case pool mixes inner-domain and wider-domain samples; this is a practical nested expansion, not an iid scaling-law experiment.

## Reproduce or extend

Extract `reproduce.zip`, then extract the field archives into `bracket_lab/study_128/`.
Install a FEniCSx environment (tested: DOLFINx 0.11.0, Gmsh 4.15.2, Python 3.11),
AgentFEM and AgentFEM-Learning; tested source revisions are listed in `environment.json`.
Run `run_study.py prepare`, `run_study.py gino`, `run_study.py correction`, then `evaluate_study.py`.
Missing FEM fields are regenerated from the protocol; existing fields are reused. The example inference in the model repository does not require FEniCSx.

## Numerical scope

AgentFEM solves 3D quadratic displacement elements; exported displacement is sampled at linear mesh nodes.
Reported learning metrics use **all surface nodes**, not a volume/energy norm. Top-seat deflection is a nodal mean.
Every case is checked for finite fields, fixed-face zero displacement, parameter/load consistency and disconnected IDs.
The nominal mesh size is 9 mm; this V1 is not a mesh-converged industrial qualification dataset.
Sharp junction stress values are provided as raw FEM outputs, not validated strength labels.
No bolt contact, plasticity, fracture or experimental measurements are represented.

## Attribution

Data and geometry: **CC BY 4.0**, Haoming Luo (2026). Code: Apache-2.0.
Please cite this repository, its exact revision, AgentFEM, and the relevant model method.
GINO: [Li et al., NeurIPS 2023](https://arxiv.org/abs/2309.00583).
This release is a computational benchmark, not a claim of a new GINO architecture.
