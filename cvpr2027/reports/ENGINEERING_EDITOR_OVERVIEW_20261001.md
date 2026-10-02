# Engineering SVG editor and checks — current evidence, 1 October 2026

The current paper is **ReSolve: Parse, Patch, and Check Engineering SVGs**, in [editable LaTeX](../paper/network/main.tex) and [PDF](../paper/network/main.pdf). The retained `network/` directory is the build location; the manuscript now includes structural and mechanical editing implementations and concrete SVG examples.

The workflow is source SVG + request → parse source tree → parse/validate patch → apply to source → re-import the delivered SVG → applicable engineering check. It reports edit fidelity and engineering acceptance separately. The implementations have different input contracts and training histories; a successful check establishes only the quantities and criteria it evaluates.

| Route | Editor and input | Engineering check | Evidence |
|---|---|---|---|
| Circuits and pipes | Learned identifier-addressed patch editor; supported visible SVG grammar | Modified nodal analysis; Newton hydraulic solve cross-checked by Hardy Cross | 1.5B: 1,000/1,000 main edits, 398/400 hard edits; separate 7B opaque-ID control: 154/400 |
| Axial trusses | Bounded deterministic SVG editor; visible geometry, material, section, support and load annotations | Linear axial FEM, stress/displacement reporting and global equilibrium | Saved audit: 20,008/20,008 target matches and equilibrium passes |
| Perforated plates | Bounded deterministic SVG patch editor | Edge distance, ligament, overlap, boundary crossing, net area and volume | Saved audit: 19,992/19,992 target matches; 699 edits violate stated geometric criteria |
| Planar frames | Separate Astra SVG harness, explicit physical model supplied | Member/dimension readback and planar-frame FEM | 21-member edit: all four geometries pass; analysis unavailable in 3/4 attempts, correct in 1/4 |
| Mechanical CAD | Saved Astra generation/editing under task-specific contracts | Geometric shape checks | 10/10 hard-screen outputs pass on re-scoring |
| Functional structural sizing | Astra chooses catalog sections; deterministic SVG export | SVG readback, FEM and stipulated design constraints | 6/6 saved designs pass the repeated audit |
| Broader learned patcher | Separate 7B adapter across plans, circuits, furniture, parts and piping | Target parameters plus geometric consistency | 60/100 intended and consistent drawings; 59/100 exact target trees |

FEM equilibrium passing on a truss does not check material allowables or buckling. Plate geometry checks do not perform plate-stress FEM. The broader learned model's scores cannot be replaced with those of the deterministic structural editor or the better network adapter.

## Replayed examples

The [example run](../runs/paper-engineering-examples-20261001/summary.json) was regenerated from saved inputs and requests on 1 October. Every delivered SVG was imported again and checked.

| Edit | Source → delivered result | Outcome |
|---|---|---|
| Set truss member depth to 40 mm | Peak stress 11.86094 → 5.93047 MPa; displacement 1.52655 → 0.76328 mm | Faithful patch; FEM equilibrium passes |
| Double bridge load | Peak stress 84.375 → 168.750 MPa; displacement 8.94899 → 17.89797 mm | Faithful patch; FEM equilibrium passes |
| Change bridge from 6 to 8 panels | 21 → 29 members; peak stress 112.50 MPa | Parsed structural-tree patch; FEM equilibrium passes; load per node stays fixed |
| Enlarge six plate holes by 4 mm | Edge distance 25 → 23 mm; ligament 58 → 54 mm | Faithful patch; clearance rules pass |
| Enlarge four plate holes by 6 mm | Edge distance 15 → 12 mm, below 15 mm minimum | Faithful patch; violation detected |

[Editable overview SVG](../paper/network/figures/editor-overview.svg) shows the bridge and plate cases. Full source and delivered SVGs are preserved in the example run and figure directory. The overview presents the original geometry with summarized annotations and normalized colors; it is a presentation derivative, not the scoring input.

## Reproduction and evidence

```sh
cd cvpr2027
../.venv/bin/python scripts/build_engineering_paper_examples.py
../.venv/bin/python scripts/validate_astra_crossdomain.py
../.venv/bin/python -m pytest -q tests/test_engsvg_svg_edit.py tests/test_engsvg_truss.py tests/test_engsvg_plate.py
```

The editor/FEM/plate tests pass (21 tests in the initial paper revision). The subsequent parsing/patching revision passes 15 focused edit and generic-correspondence tests, including bridge-panel insertion and removal. All five examples now execute parsed patches; the topology case uses 53 version-3 operations (16 subtree insertions), saved in `bridge-topology/patch.json`. The cross-domain saved-response audit previously passed 27 focused tests and 12 subtests plus the main and XL frame self-checks. The 40,000-edit aggregate is the saved full pipeline audit; this revision replays five examples and does not represent a new 40,000-case learned evaluation.

Read [verified SVG editing](ENGSVG_SVG2SVG_VERIFIED_20260925.md), [Astra cross-domain validation](ASTRA_CROSSDOMAIN_VALIDATION_20261001.md), [learned 7B patcher](ENGSVG_CROSSDOMAIN_7B_A100_20260928.md), and [opaque-ID robustness](NETWORK_ID_BLIND_ROBUSTNESS_20260930.md) for the underlying protocols. The dated earlier discovery reports are historical evidence. The serpentine-routing and nesting attempts ended incomplete or with API errors and supply no confirmed failure claim. No new model training or Astra API call was made for this paper revision.
