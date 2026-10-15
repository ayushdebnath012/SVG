# SimJEB-Bench: CAD generation judged by FEM

A benchmark for models that design or modify mechanical CAD, where every answer is checked by finite element analysis.
It is built on the GE jet engine bracket challenge: one real engineering problem, with fixed interfaces, four load
cases, one material and a mass objective. It also uses the 381 human competition designs collected in
[SimJEB](https://simjeb.github.io) (Whalen, Beyene and Mueller, CGF 2021; doi:10.7910/DVN/XFUWJG).

## Task families

| family | input | the model must | success |
|---|---|---|---|
| `design` | the GE specification only | generate a bracket (CadQuery code or STEP) | valid and passes all four load cases; scored by the share of valid passing human designs it is lighter than |
| `redesign` | a real design that fails | change it so it passes | valid, passes, same bolt and pin diameters, mass at most 1.25 x the original |
| `lighten` | a real design that passes | remove at least 15 % of its mass | valid, passes, same bolt and pin diameters, mass at most 0.85 x the original |
| `analysis` | a real design | report per-case maximum displacement and peak stress, and pass or fail | each value within 10 % (displacement) or 15 % (stress) of the reference, and the verdict right |

`redesign` and `lighten` tasks carry a `witness`: a real valid passing design with the same interface diameters inside
the task's mass limit. It shows that the target is reachable. Tasks without one are marked `feasible: false`.

## The engineering problem (all tasks)

- **Material:** Ti-6Al-4V, E = 113.8 GPa, nu = 0.342, density 4.43 g/cm^3, yield 903 MPa (131 ksi).
- **Bolt holes:** four of diameter 10.3124 mm (0.406 in), vertical, at fixed positions. The walls start at the
  mounting plane z = 0, and the bolts are rigid and fully fixed (RBE2 in SimJEB).
- **Clevis:** two lugs with a 19.1008 mm bore on a fixed pin axis. The gap between the lugs stays empty.
- **Loads:** four separate linear static cases at the pin point, spread over the bores (RBE3):
  - vertical: 35,585.77 N up;
  - horizontal: 37,809.9 N along -x;
  - diagonal: (-28,276.2, 0, 31,403.9) N, 42 degrees from vertical;
  - torsion: 564,924.2 N mm about z.
- **Pass:** in every case, the peak von Mises stress outside 2 mm of the bolt and pin walls is at most 903 MPa. Inside
  that zone, the idealised rigid connections make stress depend on the mesh.

## Validity rules (every submitted part)

- One solid.
- **Bolt holes:** each wall starts within 1 mm of z = 0 and is at least 5.5 mm long.
- **Lug bores:** both present, each at least 5 mm long, with nothing inside the clevis gap.
- **Position:** nothing more than 0.5 mm below z = 0, and inside the design envelope (`envelope.json`). SimJEB does not
  publish the GE design-space model, so the envelope is the union of the bounding boxes of the human designs with
  intact interfaces.
- **Wall thickness:** at most 2 % of the surface thinner than the GE minimum feature size of 1.27 mm. Thickness is
  measured by casting rays along the inward normal against the exact B-rep.

## How answers are checked

- **FEM** ([scripts/simjeb_tasks.py](../../scripts/simjeb_tasks.py)): gmsh first-order tetrahedra (size 1.2 mm),
  FEniCSx linear elasticity, and SimJEB's stress measure (von Mises of the nodal-averaged stress tensor).
  - On SimJEB's own mesh, the same solver ([scripts/simjeb_fem.py](../../scripts/simjeb_fem.py)) reproduces SimJEB's
    published OptiStruct displacements and stresses exactly (design 148, all four cases, every node).
  - On a gmsh mesh made from the STEP, displacements agree with SimJEB to within 3%, and the stress outside the 2 mm
    zone to about 7%.
- **Geometry:** [scripts/cad_checks.py](../../scripts/cad_checks.py) (OpenCASCADE).
- **Harness:** [scripts/simjeb_bench.py](../../scripts/simjeb_bench.py) runs CadQuery code in its own process, then
  the geometry checks, then FEM, then scoring.

A hand-written naive bracket (a flat bolt plate with two upright lugs, 0.657 kg; `naive_bracket_example.py`) is
valid but fails with a safety factor of 0.33. Passing takes real structural design.

## Running it

```bash
python scripts/simjeb_bench.py fetch                         # SimJEB CAD (207 MB) -> tmp/simjeb/cad
python scripts/simjeb_bench.py evaluate --family design --id simjeb-design-ge \
       --cadquery my_bracket.py --results results.jsonl --model my-model
python scripts/simjeb_bench.py evaluate --family redesign --id simjeb-redesign-148 --step fixed.step --results results.jsonl --model my-model
python scripts/simjeb_bench.py score --results results.jsonl
```

Environments: FEniCSx 0.9 with gmsh (FEM) and CadQuery 2.8 (geometry checks and running code). One evaluation takes
about 2 to 5 CPU minutes.

## Files

- `design.jsonl`, `redesign.jsonl`, `lighten.jsonl`, `analysis.jsonl`: task prompts, references, limits, witnesses.
  CAD paths point to `tmp/simjeb/cad/<id>.stp` (fetched, not committed).
- `human_baseline.jsonl`: every human design's FEM results, geometry checks, validity and violations.
- `envelope.json`: the design envelope.

## Limits

- One engineering problem, so the benchmark measures depth, not breadth.
- Linear static analysis only. Rigid bolts and RBE3 load spreading are idealisations; fatigue, buckling and vibration
  are not checked.
- The envelope is derived from the human designs, not GE's own model.
- SimJEB's designs are public on GrabCAD and may be in model training data. The FEM verifier still has to pass whatever
  a model submits.

## Licence and attribution

The SimJEB data is under ODC-By (its README; Harvard Dataverse lists CC0). The CAD comes from the GE jet engine bracket
challenge and is licensed by GrabCAD for non-commercial use, so it is not stored in this repository. Cite Whalen,
Beyene and Mueller, "SimJEB: Simulated Jet Engine Bracket Dataset", Computer Graphics Forum 40(5), 2021.
