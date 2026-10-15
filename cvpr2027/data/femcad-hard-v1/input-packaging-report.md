# Candidate inputs and private references

The 50 source studies now have separate candidate and held-out preparation packages under
`tmp/femcad-evaluation/`. No engineering task, drawing, FEM solution, numerical reference, or acceptance tolerance was generated. Source images and binary dependencies are copied unchanged, with SHA-256 provenance. HTML is an extract of the published tutorial with answer content removed.

## Files to use

- `tmp/femcad-evaluation/model-inputs/FEMCAD-ADV-NNN/task.json`: candidate instructions, requested outputs, asset inventory, hashes, status and runtime requirements.
- `problem.html` in that directory: extracted model definition, setup and geometry instructions, with local original figures and equation images. GUI toolbar icons are omitted.
- `assets/`: geometry, material, parameter, loading and other input files. Filenames match the tutorial. Study 040 also receives the original material library from study 039.
- `tmp/femcad-evaluation/held-out/FEMCAD-ADV-NNN/reference.json`: full administrative row, source URLs and hashes, removal log and candidate provenance.
- `reference.html`: offline reference tutorial including published result figures; `original-tutorial.html` preserves the original source bytes.
- Held-out `assets/`: locally downloaded solved models, numerical reference tables and supplementary slides. The reference manifest identifies remote solver files explicitly; they are not represented as downloaded numerical arrays.
- `tmp/femcad-evaluation/candidate-archives/`: 42 individual input ZIP files, each containing one unblocked task only. [Archive index and hashes](candidate-archives.json). Rebuilding the preparation directory requires exporting these archives again.
- [Machine-readable packaging report](input-packaging-report.json) and [validation results](input-packaging-validation.json).

**Do not send `advanced-tasks.jsonl`, the illustrated dataset PDF, the original tutorials, or the parent evaluation directory to a candidate.** These remain administrative/reference artifacts containing answers. The legacy five-row `tasks.jsonl` is a different edition and was not changed.

## Separation rules

All tutorial Results/Results and Discussion sections, result/postprocessing instruction sections, solved models and four standalone output tables are held out. Additional exclusions handle reference imports and answers placed outside the results sections: experimental forming angles, muffler and tweeter reference interpolations, the pressure-vessel stress-location coordinates, a car-door load-result figure, a loudspeaker deformation figure, and numerical resonance statements. Optional shortcuts that load a solved model were removed where the source supplies the geometry construction instructions.

Parameters, constitutive curves, prescribed loads, meshes, solver settings and pure geometry/material models remain inputs. The snap-hook displacement table is a prescribed load, not an answer. Vented-enclosure impedance tables are prescribed upstream inputs, although they originate from the separate loudspeaker-driver study. **Use a fresh candidate context and isolated filesystem per task** so those inputs cannot leak answers to another task.

This protocol evaluates **source-assisted FEM reproduction with supplied geometry**. It does not measure unaided reconstruction from a drawing, independent selection of numerical methods, or discovery of sampling locations. Source solver shifts and design frequencies are supplied settings; they must not be confused with withheld predictions.

## Remaining blocked packages

Six tutorials require an additional base model that has not been supplied as a verified answer-free input:

| Task | Required companion |
|---|---|
| 003 | `turbine_stator` |
| 018 | `comb_drive_tuning_fork_gyroscope` |
| 026 | `composite_dome_tweeter_eigen`, including homogenized materials |
| 029 | `cohesive_zone_debonding` |
| 030 | `sports_car`, including LES forcing |
| 031 | `motherboard_shock_response` |

Their geometry/supporting files are packaged where available, but the tasks remain blocked. Loading a full solved base or target model without inspecting/exporting its required inputs could expose answers. No compatible COMSOL execution/export workflow is configured here, so those inputs have not been fabricated or inferred from plots.

Two further source ambiguities block evaluation:

- **002:** reported operating voltage differs between the results narrative and figure caption (60 V versus 50 V).
- **017:** initial void fraction is 0.4 in the model-definition table but 0.6 in the material setup table.

Thus **42 packages have no known dependency/settings blocker; eight are blocked**. This is a packaging status, not a FEM pass rate or certification of complete reproducibility.

## Export and isolation

From `cvpr2027/`:

```sh
python3 scripts/validate_fem_evaluation_inputs.py
python3 scripts/export_fem_candidate_bundle.py FEMCAD-ADV-001 --output tmp/fem-task-001-inputs.zip
```

The exporter checks hashes and local image references, rejects known blocked tasks, and includes exactly one task's allowlisted files. It refuses to overwrite an existing output. It makes no model/API calls.

Extract that archive into a new isolated candidate workspace. Disable network access and mount no other task, original catalog, reference directory or project filesystem. Directory separation inside this shared project alone is not an access-control boundary. The old `fem_open_model_pilot.py` now stops before credentials or network access because its full-tutorial prompt leaks answers and its delivery path omits dependencies.

Rebuild using `python3 scripts/package_fem_evaluation_inputs.py`. Downloads use the existing exact-version asset inventory and original tutorial image URLs; downloads are cached. The previous build is retained as `tmp/femcad-evaluation-previous/`.

## Validation and limits

Structural checks cover all 50 package inventories and hashes, source provenance, resolution of local images, exclusion of active HTML/source hyperlinks, known reference tables, solution entries in supplied MPH archives, targeted answer-leak cases, and the required geometry/material assets. Original candidate figures were also inspected as contact sheets. These checks do not replace an independent semantic review, a licensed solver compatibility check, or a study-by-study reproducibility run.

Model definition and setup sections can depend on quantities computed in earlier stages. Removing results/postprocessing instructions is conservative and may remove an operation later needed by a multi-stage workflow. Such workflow completeness still needs verification before scoring; no missing operations, parameters or FEM values were invented to make these tutorials appear runnable.

Numerical evaluation remains unready: per-output scoring contracts, validated target exports, externally justified tolerances and solver execution are still missing. No paid inference or FEM solve was performed.
