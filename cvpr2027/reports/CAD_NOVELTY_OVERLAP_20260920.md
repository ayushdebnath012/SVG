# Novelty stress test: CAD drawings, editing and engineering verification

20 September 2026, follow-up to the initial 25-source web audit.

**The broad idea is not distinct enough.** CAD generation/editing with geometric
checks, preserved constraints, executable tests or FEA is already covered by
several close works. The expanded primary-source search adds 14 sources. It does
not prove absence of equivalent work, and the narrower proposal below is a
hypothesis that still requires comparative experiments.

## Closest additional overlaps

| Primary source | Existing contribution that overlaps | Consequence for this project |
|---|---|---|
| [CADEngBench](https://arxiv.org/html/2608.09296v1), Aug 2026 | Functional edits, preserved properties, operational parameter families, DFM, matched CalculiX response and assembly grounding | The claim “CAD must work physically, not only look right” is already central prior art. Reuse its evaluation layers; do not present FEM-checked CAD edits as our novelty. |
| [BenchCAD](https://arxiv.org/html/2605.10865v1) / [release](https://benchcad.com/), May 2026 | Industrial programmatic CAD generation and instruction-guided edits across 106 part families | Hard industrial shapes and code-edit training already exist. Reserve official tests; establish an authorized training partition and lineage isolation before any training use. The release labels code MIT/data CC-BY-4.0. |
| [Vector-Bench](https://github.com/yug-space/vector-edit-gym), July 2026 | Deterministic SVG repair scoring plus preservation of unrequested structure; 40 tasks and published model traces | “Fix an SVG without breaking the rest” is not a new task. Our useful addition must concern engineering meaning and dependency changes, not only DOM preservation. Scenic source-asset rights are explicitly unresolved. |
| [CADWorld](https://arxiv.org/html/2609.16251v1), Sept 2026 | 200 FreeCAD GUI tasks covering geometry, constraints, CAM, FEM and technical drawing artifacts | Combining CAD workflows, drawings and downstream checks is also insufficient. Its interface is GUI computer use; ours would need a specifically different representation-level question and matched tool baselines. |
| [BIM-Edit](https://arxiv.org/html/2606.20146v1), June 2026 | Natural-language IFC edits with geometry, semantic and topological evaluation | Building edits and preservation of engineering relationships already have a direct comparator. Do not treat buildings as an automatically novel extension of mechanical CAD. |
| [CADTestBench](https://github.com/dimitrismallis/CADTestBench), May 2026 | Executable geometric/topological predicates tied to prompts, also used to guide generation | Verifier-guided generation and requirement satisfaction cannot be claimed as new. Prefer requirement predicates over a single-reference shape score for underdetermined designs. |
| [Physics-in-the-Loop](https://arxiv.org/abs/2605.19717), May 2026 | Agents plan, generate and revise CAD using explicit engineering tools and load cases | A physical checker in a repair loop is directly anticipated. Code/data were promised in the inspected abstract; no downloaded release was established here. |
| [MUSE](https://arxiv.org/abs/2605.28579), May/June 2026 | Complex editable assemblies evaluated for functionality, manufacturability and assemblability, with design-specific judging | “Beyond geometry” evaluation is established. Distinguish deterministic checks from subjective design rubrics and use both only for appropriate requirements. |
| [IterCAD](https://arxiv.org/abs/2606.13368), current Aug 2026 revision | Drawing/text-to-code and interactive edits with an executable CAD environment, multiview data synthesis, SFT and geometry-aware RL | Iteration, synthetic edit trajectories and solver/execution-informed training are not a sufficient methodological contribution. |
| [OmniMech](https://arxiv.org/abs/2608.05539) / [project](https://omnimech.dev/), Aug 2026 | Dimensioned orthographic drawings paired with native CAD, annotations, cross-view reasoning and tool-augmented reconstruction | Cross-view and annotation-grounded CAD also overlap. The project advertised samples/code, but both tested download links failed; do not treat its full corpus as imported or training-ready. |
| [NIST GD&T implementation testing](https://www.nist.gov/publications/testing-implementations-geometric-dimensioning-and-tolerancing-cad-software), 2020 | Tests semantic representation and graphical presentation of engineering annotations | Model–drawing–annotation consistency predates LLMs. An LLM contribution must solve a new measured failure mode, not rename CAD associativity or PMI verification. |
| [CAD-AG](https://scholars.duke.edu/publication/1703509), 2026 | Geometric feature/rule checks for engineering DXF drawings | Automated drawing geometry grading is prior art; our raster/geometry checker alone is an implementation component. |
| [SVGEditBench V2](https://arxiv.org/abs/2502.19453), 2025 | Instruction-based original/target SVG edit pairs from emoji data | Reuse as a general editing baseline, not as engineering ground truth. |
| [Parametric CAD Bench v2](https://cadbench.ai/), Sept 2026 | Public FreeCAD benchmark with Astra operating through an agent and CAD tools | Existing Astra tool-using results must be acknowledged. Its score is not comparable to our unaided SVG interface; a failure here cannot establish that Astra cannot solve the part using CAD tools. |

The previous audit's HistCAD, EPICCAD, Drawing2CAD, neuralCAD-Edit and
Hephaestus-CCX comparisons still apply. The sources above deepen that overlap;
they do not replace or invalidate those citations.

## Narrower question worth testing, not a confirmed novelty claim

Can a learned editor preserve the **engineering meaning of a linked design
package** when an edit changes a feature whose dependencies cross the object
model, multiple SVG views, dimensions and applicable analysis outputs?

The unit would be an editable package with explicit feature identity and a
measurable dependency graph. Successful edits must update affected geometry and
claims, preserve unrelated constraints, and identify outputs that must be
recomputed when relevant physical inputs change. Count stale dimensions, wrong
section/projection curves, broken feature correspondences and stale analysis
separately from invalid SVG or invalid CAD.

This remains close to associative CAD and existing verified editing work. To
make it scientifically useful, the contribution must be a reproducible benchmark
of failures those existing metrics miss, plus a method with evidence beyond
calling a deterministic CAD exporter. Changing only the file extension to SVG
or filtering on one model's errors does not establish novelty.

## Required comparisons and go/no-go criteria

1. Mine failures under a stated interface, retaining the full discovery pool.
   Only repeatable reviewed drawing failures enter the requested hard subset.
   Do not repeatedly spend calls on the earlier passing examples. Do not label
   token exhaustion, unavailable tools or wrong metadata as geometric inability.
2. Compare unaided Astra, Astra with a general CAD/Python environment, an existing
   iterative CAD agent, deterministic model-edit/export, and the proposed learned
   editor using matched inputs and disclosed compute. If CAD export alone solves
   the task, measure the unresolved language-to-feature edit problem explicitly.
3. Freeze design/family-disjoint test data after discovery. Keep every edit of a
   base model together, and prevent ancestry leakage across derivative datasets.
   A frontier-model-conditioned subset cannot estimate general performance.
4. Require improvements on complete package correctness and collateral-change
   rates, with geometric/constraint/analysis ablations. Text-sequence match from
   the existing 2,048-pair training pilot cannot supply this evidence.
5. If the only remaining errors are long-output transcription or missing tools,
   do not build a main research claim around them. Either target verified editing
   under a motivated deployment constraint or move to a harder source-model task.

## What is implemented during this follow-up

A new frozen six-task discovery pool covers ideal involute gears, roller-offset
cams and oblique sections of intersecting drilled solids, with generation and
editing for each. These are actual mechanical part drawings. Independent
material-membership references check rendered SVGs, accepting equivalent native
SVG constructions including local reuse and clipping. This is procedural
failure discovery, not a claimed import of BenchCAD/OmniMech source models.
Numerical/reference tests passed before screening. Two further curved-pipe tasks and two separately specified precision templates
were added adaptively. All ten new prompt conditions passed and none entered the
hard subset. [Results and evidence](ASTRA_CAD_HARD_DISCOVERY_20260920.md) are
recorded separately.

Primary-source snapshots, retrieval status and SHA256 hashes are in
[cad-overlap-source-audit-20260920/](cad-overlap-source-audit-20260920/).
A source appearing in the registry means it was reviewed, not that its dataset
was downloaded, licensed for training, or used in the training pilot.
