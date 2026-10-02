# CAD-style SVG generation and editing: fresh web literature and dataset audit

20 September 2026. This is a fresh, broad web search across author repositories,
project pages, arXiv, conference proceedings, publisher pages, and dataset hosts;
it is not limited to this repository's previous literature. It covers engineering
vector drawings, parametric geometry, text/image-conditioned CAD, editing,
constraints, buildings, furniture/assemblies, and engineering validation. It is
not an exhaustive systematic review of every paper on the internet.

**Follow-up:** the [novelty stress test](CAD_NOVELTY_OVERLAP_20260920.md) adds 14
primary sources (39 total in the registry), including closer CAD/FEA, SVG
preservation, building-editing and technical-drawing comparators. The broad
novelty claim is not supported.

## Decision

**Build on existing CAD data and editing methods.** The strongest starting
combination is Drawing2CAD for actual engineering SVGs paired with CAD histories,
SketchGraphs for geometric constraints, and CAD-Editor for instruction-based edit
supervision. Add FloorPlanCAD for building drawings. Use Text2CAD to add language
supervision to compatible DeepCAD-derived records. These are proposed integration
choices based on the sources below. CAD-Editor now has a completed bounded
[training feasibility pilot](CAD_EDITOR_TRAINING_20260920.md); the other integrations
remain proposed.

An SVG-only model should not invent structural truth from appearance. Preserve a
parametric object model behind the drawing, execute edits there, and apply the
appropriate geometric, analytical or numerical checks before exporting linked
SVG views and annotations. Existing datasets supply different pieces of that
pipeline; none of the inspected releases has been verified to provide all of
our required SVG/edit/material/load/validation labels together.

## Highest-priority training sources

| Source | Verified content and release | How we should use it | Main limitation |
|---|---|---|---|
| [Drawing2CAD, ACM MM 2025](https://github.com/lllssc/Drawing2CAD) | Released `svg_raw`, vectorized four-view drawings, CAD sequences and an SVG export/preprocessing pipeline; CAD models originate from DeepCAD. Views are Front, Top, Right and FrontTopRight. | First mechanical-drawing source. Learn geometry-to-SVG and SVG-to-geometry correspondence; derive consistent edit pairs by executing source-model changes. | No verified physical load/material labels. Normalized view boxes do not by themselves preserve real manufacturing scale. MIT repository license is not a blanket statement about underlying source-model rights. |
| [SketchGraphs, 2020](https://github.com/PrincetonLIPS/SketchGraphs) | 15 million CAD sketches with primitives and designer constraints; released raw and processed data, filtered splits, loaders, and baseline models. | Learn primitives, tangency, coincidence, symmetry, dimensions and constraint graphs; deterministic SVG export. | Not dimensioned sheets or physical-analysis data. Original creators retain sketch copyright; the README distinguishes source data from MIT code. |
| [CAD-Editor, ICML 2025](https://github.com/microsoft/CAD-Editor) | Locate-then-infill editing, synthesis scripts, processed data archive, and model links. Pair generation and instruction generation are documented. | Reuse the edit localization/data-generation baseline, execute edited sequences, then add SVG and validation supervision. | CAD sequence edits are not automatically correct SVG edits. Repository is archived as of the inspected page; pin it rather than expect maintenance. |
| [Text2CAD, NeurIPS 2024](https://github.com/SadilKhan/Text2CAD) | Text annotations, preprocessed splits, training/inference code and DeepCAD processing. | Join language with Drawing2CAD/DeepCAD by verified source IDs; train text-to-object specification or CAD-program generation. | Joins and ID coverage need measurement. Project license is CC BY-NC-SA 4.0, not MIT. Do not assume every derived dataset is independently split. |
| [FloorPlanCAD, ICCV 2021](https://floorplancad.github.io/) | Updated release lists 15,663 real building CAD drawings; SVG, PNG and symbol annotations. | Building-plan symbols, wall/opening topology, SVG structure and layout; later add verified edit instructions. | Symbol spotting, not structural validation or native load-bearing BIM. Annotation/site license is CC BY-NC 4.0; authors do not own underlying drawing copyright. |
| [CPTSketchGraphs / DAVINCI, BMVC 2024](https://github.com/cvi2snt/CPTSketchGraphs) | 80 million constraint-preserving transformations derived from SketchGraphs; a 17.1 GB download and FreeCAD-based transformation method. | Train how edits propagate through constraints; derive before/after examples using the original sketch identity. | Not 80 million independent designs or ready-made natural-language edits. Confirm archive-specific terms and recover parent IDs before use. |

## Additional released sources and what they add

| Source | Evidence | Role and caution |
|---|---|---|
| [DeepCAD, ICCV 2021](https://github.com/rundiwu/DeepCAD) | Releases CAD JSON construction sequences, vector representations and processing code; models were parsed from Onshape documents using ABC links. | Shared source-model foundation. Track ancestry across DeepCAD, Drawing2CAD, Text2CAD and other derivatives to prevent leakage. |
| [Fusion 360 Gallery](https://github.com/AutodeskAILab/Fusion360GalleryDataset) | Human design sequences, segmentation, assembly hierarchy and joints. The [reconstruction paper](https://www.research.autodesk.com/publications/fusion-360-gallery/) reports 8,625 sequences; the [joint subset](https://github.com/AutodeskAILab/Fusion360GalleryDataset/blob/master/docs/assembly_joint.md) documents 19,156 joint sets. | Assembly/connection supervision for products and furniture. Custom license permits non-commercial research and restricts redistribution of the full dataset. Joints do not supply joint stiffness or strength automatically. |
| [CAD-Recode, ICCV 2025](https://cad-recode.github.io/) / [released data](https://huggingface.co/datasets/filapro/cad-recode-v1.5) | Procedural CadQuery programs, roughly one million training examples; code and models are linked. | Useful executable-geometry pretraining and procedural generation method; render SVG views from the CAD kernel. It is originally point-cloud-to-CAD, not SVG editing or physical verification. |
| [CAD-Coder / GenCAD-Code, Doris et al., 2025](https://github.com/anniedoris/CAD-Coder) | Author release links 163k image–CadQuery script pairs and training scripts. | Image-to-parametric-code branch. Preserve upstream data provenance and compare against a code-output baseline. |
| [CADFusion, ICML 2025](https://github.com/microsoft/CADFusion) | Text-to-CAD with visual feedback; processed language data and preprocessing from SkexGen. | Baseline for execution/render/feedback training. Its static visual reward does not establish correctness of edited engineering claims. |
| [CubiCasa5K](https://github.com/CubiCasa/CubiCasa5k) | 5,000 floorplan images with polygon annotations in over 80 categories; CC BY-NC 4.0 license. | Raster-plan parsing for an image-input branch. FloorPlanCAD is a more direct fit for native engineering SVG work. |
| [ABC](https://deep-geometry.github.io/abc-dataset/) | One million CAD models with geometric representations; dataset site records source-creator rights and terms. | Geometry diversity and kernel/rendering tests; lacks the required instruction-edit and physical labels. |
| [PartNet](https://partnet.cs.stanford.edu/) | Part hierarchies and furniture categories including tables, chairs and storage furniture. | Furniture decomposition and part identity. Mesh parts alone do not specify manufacturable joints, dimensions, material or loads. Preserve ShapeNet/PartNet provenance and terms. |
| [ViewConsNet data, April 2026](https://data.mendeley.com/datasets/n5w53gtj2r/1) | Released engineering-drawing images, annotations and partial code for cross-view consistency; CC BY 4.0 card; some raw materials restricted. | Auxiliary view-consistency verifier data. Inspect actual released coverage; do not describe it as a complete industrial corpus. |

## Closest prior work that changes the research claim

1. **Constraint-preserving CAD editing is already studied.** Autodesk's
   [Aligning Constraint Generation with Design Intent in Parametric CAD,
   ICCV 2025](https://www.research.autodesk.com/blog/ai-alignment-in-cad-design-teaching-machines-to-understand-design-intent-in-autoconstrain/)
   uses constraint-solver feedback for post-training, including preference and
   reinforcement-learning approaches. Reuse its design-intent question and
   solver-feedback comparison. Merely rewarding valid constraints is not new.
2. **HistCAD explicitly evaluates editability.** The
   [current HistCAD preprint](https://arxiv.org/abs/2602.19171) describes
   170,236 constraint-aware executable sequences and metrics separating edit
   reachability from preserved constraints. Its indexed Hugging Face card was
   found, but direct retrieval returned 401 in this audit. Treat it as a major
   comparator and conditional data source, not a confirmed locally usable corpus.
3. **Engineering validation of generated CAD already has a direct precedent.**
   [Self-Improving CAD Generation Agents with Finite Element Analysis as
   Feedback, May 2026](https://arxiv.org/html/2605.17448v2) introduces
   Hephaestus-CCX: assembled STEP outputs checked using geometry and FEA, plus
   blueprint/render feedback and repair. Appendix H describes an anonymized
   supplemental release and a future public mirror; no ready public repository
   was verified here. Compare task/checker concepts and obtain a runnable release
   before claiming reproduction.
4. **CAD2Program is directly relevant to furniture drawings.** The
   [author project](https://manycore-research.github.io/CAD2Program/) reconstructs
   parametric cabinets from engineering drawing images, including geometry and
   annotation layers. Public bulk training-data access was not verified on the
   inspected project page. Use it as related work, not an assured download.
5. **EPICCAD is recent constraint-aware history work.** The
   [September 2026 journal paper](https://link.springer.com/article/10.1007/s44163-026-01899-5)
   aligns histories, constraints, views and text. Its data/code availability
   section says reasonable request, with restrictions on proprietary NX files.
   It is not an immediately downloadable training dependency.
6. **Two different papers are called CAD-Coder.** The
   [He et al. DXF paper](https://arxiv.org/abs/2505.08686) reports 29,130 editable,
   annotated DXF/script pairs; a public dataset download was not verified.
   The released Doris et al. image-to-CadQuery project above is a separate work.
   The DXF direction is unusually relevant to dimensioned drawings, but do not
   merge their data, authors or results.

The defensible extension to investigate is a **linked object-model/SVG editing
contract**, tested on repeatable Astra failures, that preserves geometry,
constraints, dimensions, multiple views and applicable engineering claims through
edits. This is a research hypothesis, not an established novelty claim. Compare
against a deterministic CAD exporter, a tool-using CAD agent, an unrestricted SVG
editor, and an editor using verified model patches. An unaided Astra baseline
alone is insufficient to establish superiority over existing tool-based methods.

## Benchmarks to reserve, not silently use as training data

| Benchmark | Why it matters | Treatment |
|---|---|---|
| [neuralCAD-Edit, 2026](https://autodeskailab.github.io/neuralCAD-Edit/) | 192 multimodal requests and 384 expert edits, using Fusion Gallery source models. [Dataset card](https://huggingface.co/datasets/autodesk/neuralCAD-Edit) lists CC BY-NC 4.0. | External editing evaluation; exclude its source designs from training even if a host calls its archive split `train`. |
| [CADBench, May/June 2026](https://arxiv.org/abs/2605.10873) / [code](https://github.com/anniedoris/CADBench) | 18,000 multimodal reconstruction evaluation samples, multiple source families and geometry/execution metrics. | External generation test and complexity-stratification reference; audit overlap with DeepCAD/Fusion/ABC training sources. |
| [CADGenBench](https://github.com/huggingface/cadgenbench) | Drawing-to-STEP generation and requested STEP edits, public inputs, private ground truth and a released evaluator/baseline. | External test; public inputs are not licensed training answers or a substitute for local ground truth. |
| [RealCADBench, September 2026](https://arxiv.org/abs/2609.03773) | 12,632 industrial-intent tasks described in the paper, including drawings and assemblies; reported evaluation uses a subset. | Current comparator for realistic shape difficulty. Direct public dataset/code access was not verified in this audit. |
| [Hephaestus-CCX](https://arxiv.org/html/2605.17448v2) | Geometric and physical requirement checks on engineering briefs. | External engineering-validity comparison once the release is accessible. Do not mix its test briefs into fine-tuning. |

## Concrete training-data build plan

Start with **one mechanical-drawing track and one architectural track**, not a
single undifferentiated mix of every dataset.

1. **Import and preserve provenance.** Begin with a small Drawing2CAD sample and
   its DeepCAD records, plus a filtered SketchGraphs sample. Build a separate
   FloorPlanCAD adapter. Store original model/document IDs, source split, source
   URL/version, license record and content hash. Verify real units and scale.
2. **Split before augmenting or joining.** Keep every view, instruction, edit,
   constraint-preserving transform and dataset derivative of a source model in
   the same partition. Deduplicate across source IDs and normalized geometry.
   Exclude external benchmark designs. A random SVG-file split is invalid here.
3. **Execute edits on the source model.** Reuse CAD-Editor's paired-sequence
   approach and CPT-style constraint propagation. Produce before/after CAD,
   before/after SVG views and a factual instruction grounded in the executed
   change. LLM text is a paraphrase candidate, never the geometry reference.
4. **Add typed verification labels.** Check geometric constraints, dimension
   consistency, topology, intersections, clearances and area/mass first. Add
   statics, analytical beam/plate calculations, stability, FEM or other simulation
   only when the case supplies the required physical specification. Missing
   material/support/load information must be explicitly marked unevaluated.
5. **Train model extraction and edits.** Supervise structured object/constraint
   edits and annotation bindings; generate SVG through a deterministic exporter.
   Compare with direct SVG fine-tuning under the same tasks. Retain the base
   model and deterministic edit baseline so another template-routing pilot
   cannot be mistaken for improved CAD understanding.
6. **Mine difficult evaluation cases with Astra.** Screen a reserved, stratified
   pool derived from the imported source families. Repeat failures under fixed
   stronger budgets, verify them independently, and select only confirmed
   failures. Keep drawing failure separate from incorrect physical analysis.
   Discovery results are development evidence. Freeze a disjoint final pool
   before tuning; publish the full screening denominator and selected subset.

Suggested first feasibility batch (a proposal, not a completed dataset): 200
mechanical source designs, 200 constrained sketches and 100 floorplans, with a
small number of executable edits per design. Measure conversion validity, source
ID overlap, constraint coverage, annotation correctness and SVG round-trip
fidelity before scaling. A subsequent training feasibility run uses the official CAD-Editor processed
archive (120,000 training and 2,000 test records). The bounded derived pilot has
2,048 train / 128 validation / 128 test pairs, with exact-sequence connected
components isolated across splits. See `data/cad-editor-pilot/manifest.json`.
This sequence-editing pilot does not yet provide SVG or physical-validation
supervision. Training status and results are recorded separately.

## Provenance and search boundaries

Search themes included engineering SVG datasets, CAD generation and editing,
constraint graphs and transformations, text-to-CAD, drawing-to-CAD, furniture
assemblies, floor plans, CAD verification, and recent 2026 benchmarks. Primary
sources were opened; release claims are distinguished from verified download
entry points, and code licenses from underlying data terms. Public READMEs and
license snapshots for nine repositories, with retrieval times and hashes, are
in [the source audit manifest](cad-source-audit-20260920/manifest.json). The
[machine-readable source registry](../data/cad_sources.json) records proposed
roles and access status. Neither resource claims that all archives were fetched
or all published methods reproduced.
