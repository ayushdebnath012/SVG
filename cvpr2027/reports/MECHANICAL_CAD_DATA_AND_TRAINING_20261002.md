# Complex mechanical CAD editing: dataset and completed local training

2 October 2026. Scope: complex mechanical CAD and linked engineering vector views,
with controlled edits. Resistor networks and pipe/circuit families are excluded.
Existing historical circuit experiments remain historical evidence.

## Completed work

Downloaded BenchCAD code-generation shards 0 and 9 (2,000 source parts), pinned
at `5919f578ab09ec283603a082fab07c7639ab56eb`. Downloaded all 748 external
edit-benchmark records only to audit and exclude overlapping programs/templates;
none of those edit answers enters training. Source data is CC-BY-4.0; attribution:
Zhang et al., *BenchCAD*, 2026. The upstream card is retained in the dataset.

Filtered to upstream hard parts with at least eight CadQuery calls and compound
geometry (boolean, sweep, loft or revolve). Excluded pipe, duct, fitting, manifold,
valve, hose, resistor, circuit and PCB family names. Removed 366 source records
whose normalized or numeric-literal-masked AST matched an external edit template.
This conservative check does not prove geometric or source-ancestry isolation
from all other datasets. No official BenchCAD score is claimed after using its
code-generation source as training material.

The bounded selection had 88 candidates from 44 families. After executing the
original and edited programs, 150 pairs from 76 parts and 40 families passed:
108 train, 22 validation, 20 test. Whole families were partitioned before edits.
Edits cover chamfer (62), hole (48), extrusion (24), and fillet (16).
There are 904 referenced SVG views, before/after STEP solids and 150 paired
four-view SVG drawing sheets. Twelve candidate parts have no accepted edit;
failures and timeouts remain in `verification.log`. Invalid edits and edits with
no measurable volume change were excluded. One spline-hub sheet was rendered and
visually inspected; all referenced SVGs passed XML checks. These are CAD-derived
line views with edit annotations, not scanned or fully dimensioned manufacturing
blueprints. Absolute manufacturing units and standards compliance are not certified.

## Training actually completed

Local Apple M5, 16 GB memory, MLX QLoRA on
`mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit`, model revision
`b3252a2f97102b1fb1571fec2c9b27219a8536be`. Seed 17, 100 optimizer iterations,
batch 1, learning rate 1e-4, last 8 layers, prompt-masked loss, 3,072-token cap.
Eight-layer adapters have 2.638 million trainable parameters. The model consumes
CAD code and an explicit feature/line edit request, returning a JSON source-line
patch. Drawings are exported deterministically from the resulting solid.

No example was silently truncated. Token filtering retained 92 train, 22
validation and 12 test examples; 24 longer examples were omitted and their token
counts recorded. This excludes some of the largest propeller/impeller programs.
This is a small localized-edit feasibility pilot; it does not train SVG/image
perception, feature localization, assembly edits or complex free-form redesign.

| Fixed 12 held-out cases | Applicable patches | Executable matching solids |
|---|---:|---:|
| Base, exact source-line contract | 0/12 | 0/12 |
| Base, unique line-fragment diagnostic | 11/12 | 11/12 |
| Trained adapter, exact source-line contract | 12/12 | 12/12 |

Final adapters were reloaded for generation. Both predicted and reference CAD
programs were executed; geometry match requires valid, positive-volume solids
and volumetric IoU >= 0.99999. The relaxed base diagnostic shows that the apparent
strict-contract improvement mainly concerns patch transport/formatting. These
12 cases do not establish a broad engineering-reasoning gain. Base and trained
predictions, geometry scores, training logs, source hashes and adapter checksum
are saved under `runs/mechanical-cad-mlx-20261002/`.

## FEM and source selection

FEM is **not evaluated** for these examples. The geometry source does not declare
material, supports, loads, physical units and an analysis contract. Inventing
those would create synthetic load-case labels rather than validate the original
part's engineering intent. Geometric validity is separately recorded and never
labeled FEM-verified. Add simulation for explicitly specified load-bearing,
stiffness, stress, buckling, contact or thermal edits, with consistent before/after
material/load/support conditions, mesh convergence and solver residual checks.

| Source | Use and verified availability |
|---|---|
| [BenchCAD](https://huggingface.co/datasets/BenchCAD/BenchCAD) | Downloaded executable mechanical programs; local derived edits and views built and trained here. Its external edit benchmark is excluded. |
| [Drawing2CAD](https://github.com/lllssc/Drawing2CAD) | Vector drawing/CAD correspondence and preprocessing; relevant next source for genuine vector-view conditioning. No new Drawing2CAD training completed here. |
| [CAD-Editor](https://github.com/microsoft/CAD-Editor) | Existing repository pilot supplies sequence-edit methodology; this run instead executes mechanical CadQuery solids. |
| [neuralCAD-Edit](https://autodeskailab.github.io/neuralCAD-Edit/) | 192 expert requests and 384 expert edits; reserve for external editing evaluation, not fine-tuning. |
| [HistCAD](https://huggingface.co/datasets/DongXintong/HistCAD) | Released constraint-aware histories and industrial subset; candidate for deeper editable histories. Access/schema/ancestry still require a local audit. |
| [CADEngBench](https://arxiv.org/abs/2608.09296) | Closest inspected functional-edit/FEA benchmark: 300 parts, 600 generation/edit tasks, matched linear-static CalculiX checks, plus 150 assembly pairs. Paper inspected; a public runnable data release was not verified. |

The next meaningful scale-up needs multi-feature edit requests without source-line
answers in the prompt, larger CAD contexts, genuine drawing-conditioned inputs,
and physical cases with declared analysis specifications. Preserve external
benchmarks and source-family splits when expanding.

## Reproduction

Use `scripts/build_mechanical_cad_edits.py` with the pinned parquet downloads and
existing `tmp/cad-runtime/bin/python`. It executes every accepted pair and exports
STEP/SVG; specify a fresh output directory. `scripts/mechanical_cad_sheets.py`
creates inspectable sheets. `scripts/train_mechanical_cad_mlx.py` performs fresh
base evaluation, training, adapter reload and final evaluation; specify a fresh
run directory. `scripts/score_mechanical_cad_predictions.py` runs real CAD and
IoU checks using the CAD environment. `scripts/mechanical_patch_fragment_control.py`
reproduces the format-relaxed diagnostic before geometry scoring.

The MLX environment is isolated in ignored `tmp/mechanical-training/`; package
versions and the exact training command are in the run manifest. Four regression
tests pass for localized patch application, Unicode preservation, complexity
filtering and AST normalization. Additional executed checks cover split hashes,
family isolation, source-line application, scope exclusions, referenced SVG XML
and rejection of unexpected imports, file I/O, private attributes and loops.

The old remote GPU host timed out before banner exchange; no remote training or
remote resource purchase is claimed. The completed adapter is a local MLX model.
