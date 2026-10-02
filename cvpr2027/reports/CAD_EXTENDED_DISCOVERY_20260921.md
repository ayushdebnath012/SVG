# Extended engineering drawing discovery and novelty audit

Date: 21 September 2026. This is an evidence log, not a claim that all novelty or benchmark gates have been met.

## Completed custom screens

| Screen | Distinct cases | Astra result | Reported API tokens |
|---|---:|---|---:|
| Rolled neutral-surface sheet patterns with oblique drilled openings and a trimmed cone | 3 | 3 geometry passes | 15,678 |
| Detached top/front/right machining drawings, with blind-to-through hole edits | 2 plate layouts | 2 geometry passes; equivalent wording adjudicated as correct | 19,210 |

All runs used `gpt-6-astra` with high reasoning effort. They are excluded from the hard subset. The five conditions are not five independent engineering families. No training was started on them.

The [pattern runs](../runs/astra-cad-development-20260921/screen/summary.json) retain prompts, responses, tool executions, SVGs and reference comparisons. The generic numerical contour helper provided no task-specific geometry or target comparison. The evaluator maps points on the flat pattern back to the 3D neutral surface and tests bore/trim membership. All three outputs had zero residual mismatch area outside the stated tolerance, and maximum raster boundary intrusion of 0.1 mm. This is a sampled check with 0.15 mm physical tolerance plus a 0.1414 mm raster allowance. It does not establish finite-thickness sheet-metal manufacturability, bend compensation or springback accuracy.

The [machining runs](../runs/astra-cad-multiview-20260921/screen/summary.json) moved four selected holes in each plate, enlarged them, changed their depths and updated all views, hidden edges and annotations. The original evaluator incorrectly treated `THROUGH` as different from `THRU`. Original scores remain intact; [separate adjudications](../runs/astra-cad-multiview-20260921/screen/adjudicated-summary.json) fix that flag without changing geometry checks or model outputs. Five meaningful grader tests cover the oracle, equivalent wording, a wrong diameter, retained blind ends and an incorrect right-view translation. Six pattern-evaluator tests also pass.

The [rendered gallery](../runs/astra-cad-development-20260921/combined-gallery.png) was visually inspected. Empty selection records are saved for [patterns](../runs/astra-cad-development-20260921/hard_selection.json) and [machining edits](../runs/astra-cad-multiview-20260921/hard_selection.json). Passing cases are not rerun to search for an accidental failure.

## Released drawing experiment

The official [CADGenBench public dataset](https://huggingface.co/datasets/HuggingAI4Engineering/cadgenbench-data) contains 49 drawing-generation and 32 STEP-editing fixtures. Its card identifies ODC-BY licensing and evaluation-only use. All 81 descriptions and 12 selected generation drawings were downloaded; private reference geometry was not accessed. The official code was cloned for inspection. No external submission was made.

The next frozen screen is public drawing **149**, a machined annular part with outer pockets, inner relief features, four through holes, four counterbored holes, eight blind holes, workholding flats and multiple edge treatments. Input consists of the released drawing and enlarged crops of that same drawing. Astra receives a CadQuery execution tool and rendered kernel projections for self-review, with no target or correctness feedback. The output includes a STEP solid and genuine SVG orthographic projections.

The [run protocol](../runs/astra-cad-released-20260921/149/screen/protocol.json) records source image hashes, model settings, allowed tools and necessary dimension/feature checks before the first response. Since official targets are private, any local verdict must cite an explicit public drawing requirement. A passed subset of checks is not an official benchmark pass. Disclosed ambiguity, execution-interface limitations and operational failures cannot establish geometric inability. Fresh confirmation attempts are justified only after an actual final geometry error is audited.

**Drawing 149 result:** completed in 629 seconds, with four execution-tool calls and 102,074 reported tokens across five API turns (including cached/repeated input). The final result is one valid solid. All 38 [local feature and material-occupancy checks](../runs/astra-cad-released-20260921/149/screen/local-audit.json) pass, including bore diameters/depths, retained blind-hole bases, two explicit chamfers and pocket material. This is a partial audit, not a full-shape or official benchmark pass. Astra disclosed inferred bolt-circle diameters and uncertain pocket-length references; those are not counted as errors. The three repaired intermediate kernel failures are also not final shape failures. The case is excluded from the hard subset.

**Drawing 131 result:** the ribbed housing reconstruction completed after resuming one saved request interrupted by an API server error. Five completed API turns reported 223,833 tokens; the failed server request returned no usage. The final object is one valid solid. All 11 [local dimension/surface checks](../runs/astra-cad-released-20260921/131/screen/local-audit.json) pass: 145.32 × 198.85 × 50 mm envelope, main bore and counterbores, mounting bores, and the two projected inclined-plane angles (43.07° and 44.76°). The final SVG was rendered and visually inspected.

The model discloses unresolved rear-pocket boundaries, side-window locations and Detail D dimension associations. Those claims are not accepted as proof of ambiguity; they remain unresolved by this local audit. The initial protocol's shorthand about 5/8/15 mm retained walls also needs annotation-attachment review because depth and retained thickness are different. Those provisional interpretations are explicitly excluded from failure scoring. The case remains **full-shape unscored**, not a demonstrated full pass or a confirmed hard case. No independent failure repeats are justified yet.

[Both released input cases](../data/cad-released-probe/manifest.json) are saved with original drawings, crops, attribution, dataset card and content hashes. The [run summary](../runs/astra-cad-released-20260921/summary.json) and checksums retain all outcomes. Official full-shape scoring requires the public Space's authenticated submission flow and explicit publication consent; there is no local reference target. No external submission or publication occurred. These local tests must not be described as official CADGenBench scores.

**Current decision:** zero admitted hard cases from this batch. Five custom cases pass; two released reconstructions pass limited checks with full-shape verdicts unresolved. No new training and no claim of confirmed novelty. Repeated sampling of these passing or unscored cases would not fix that evidential gap.

## Additional overlap: what we must build on

The registry now contains **62 source records**, with review depth recorded individually. This is not a claim that 59 complete papers were reproduced.

| Primary source | Evidence reviewed | Consequence for this project |
|---|---|---|
| [DrafterBench](https://arxiv.org/abs/2507.11527), [official code](https://github.com/Eason-Li-AIS/DrafterBench) | Primary abstract and README; 1,920 civil drawing-revision tasks across 12 types and 46 tools. Its README evaluates recorded operation chains. | Drawing revision and tool-chain evaluation are existing work. Our proposed comparison must evaluate the resulting drawing and its geometric meaning. |
| [MakerBench-HWE](https://github.com/tonykoop/makerbench-hwe) | Pinned public code, README and selected SVG/DXF fabrication task briefs. Includes engineering artifacts and physical/DFM checks. | Engineering SVG plus verification is already covered. Keep its entire benchmark out of training, as its explicit policy requires. No private oracle inspected. |
| [BenDFM](https://arxiv.org/html/2603.13102v1), [official release](https://github.com/UGent-CVAMO/bendfm) | Full paper and release README; folded/unfolded sheet parts with process-aware manufacturability labels. Current release describes 14,000 BenDFM and 6,000 BenDFM-U parts. | Bending feasibility, collisions and unfolded geometry are useful existing supervision, not new contributions. The official [Zenodo release](https://zenodo.org/records/18622958) and exported metadata were verified: a 3,136,811,782-byte archive, MD5 `230ee3e1e2fc26a0a1dc4358fc8a5298`, declared GPL-3.0-or-later. Metadata is saved; the archive was not downloaded. |
| [Smart Sheet Smith](https://ssrn.com/abstract=7118666) | Primary SSRN abstract via search; full paper and dataset not inspected. Describes multi-view drawing interpretation, bending plans and physics-compensated patterns with iterative checks. | Direct overlap with a broad drawing-to-fabrication-plus-physics proposal. Do not assert that workflow is new or quote its accuracy as reproduced. |
| [ORIGAMISPACE](https://arxiv.org/abs/2511.18450) | Primary abstract only; folding patterns, process and shape reasoning with interactive tasks. | Folding/pattern generation and constraint interaction are also existing benchmark directions. |

Searches also covered engineering SVG ambiguity, drawing edit intent, query-specific verification and constraint evidence. A negative search result does not prove absence of prior art. Existing overlap documented in the [foundation report](PROJECT_FOUNDATION_20260921.md), including CIT-CAD, ProCAD, Drawing2CAD and intent-intervention work, remains applicable.

Two further primary-source checks narrow the method claim: [Chart2SVG](https://arxiv.org/html/2608.26544v1) already recovers a semantic SVG dependency graph and propagates edits across related chart elements; the [2001 constraint-SVG paper](https://constraints.cs.washington.edu/web/csvg-www10/) already links SVG geometry and text through constraints. Thus graph-based SVG consistency is not itself new. The [search log](cad-extended-source-audit-20260921/search-log.json) also records unresolved publisher/patent leads separately; blocked full texts are not represented as fully reviewed.

A particularly close [mechanical-drawing audit reference architecture](https://www.tandfonline.com/doi/full/10.1080/0951192X.2026.2714117) already discusses legacy 2D drawings, typed interfaces, rule gates, uncertainty and traceable findings. Its introduction was available through the primary publisher search result; the complete text was blocked. This further rules out claiming that an evidence/uncertainty architecture for engineering drawings is itself novel. An implemented and evaluated method might still contribute, but the architecture sketch alone does not.

## Defensible research position

The broad proposal is **not novel**. The narrower candidate remains: recover relationships from detached, annotated SVG sheets, apply requested edits consistently across views and annotations, and provide evidence for each engineering claim while distinguishing determined, ambiguous and inconsistent cases.

The contribution would be an empirically useful task and implementation, not the invention of FEM, CAD constraint solving, verification, ambiguity witnesses, drawing associativity or self-correction. It needs all of the following before a strong paper claim: diverse released or independently authored drawings, audited repeatable baseline failures, a method that improves those failures without hidden references, and a comparison with drawing reconstruction, editing, clarification and verification baselines. The existing one-panel linear control and two plate layouts do not establish that result.

For training, reuse CAD-Editor for edit supervision, Drawing2CAD for SVG/CAD correspondence and SketchGraphs for constraints, subject to their source rights and lineage splits. BenDFM is a prospective addition for process checks; its official release declares GPL-3.0-or-later and has not been imported into training. CADGenBench, BenchCAD evaluation records and MakerBench remain evaluation-only. Actual engineering checks should follow the task: geometry and topology for drawing reconstruction; tolerances, fit and collision checks for fabrication; statics, beam theory or FEM only when material, loads and supports are specified. A plausible FEM result cannot rescue the wrong part geometry.
