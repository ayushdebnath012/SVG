# Real CAD editing and novelty audit — 20 September 2026

**Four new tool-enabled Astra tasks passed; no new hard shape was found.**
The literature registry now covers 49 sources. Neither ordinary engineering SVG
generation, CAD editing plus verification, dependency graphs, nor multiview
consistency supports a new contribution by itself. A narrower, explicitly
unconfirmed research hypothesis is described below.

## Actual source-model experiment

Downloaded 110 records from the official
[BenchCAD release](https://huggingface.co/datasets/BenchCAD/BenchCAD), including
source/target CadQuery and STEP. They are held-out edit-benchmark records and
were used only for discovery. Four audited cases were selected before calls;
three retain the upstream target, one has a disclosed reference correction.

| Actual edit | CadQuery tool calls | Final CAD result |
|---|---:|---|
| Handwheel: add three matching spokes between the existing three | 1 | Pass; no missing or added volume versus reference |
| Heat sink: redistribute four fins into six while fixing the outer centres | 1 | Pass; 11.976 mm spacing, preserved fin dimensions and envelope |
| Hinge: replace three cylindrical knuckles with square sections | 1 | Pass; preserved pin bores and mounting geometry |
| Swept elbow: change outer and inner swept circles to squares | 2 | Pass after repair; preserved end flanges and bolt holes |

The endpoint was the Responses API, model `gpt-6-astra`, high reasoning effort,
10,000 output-token cap per turn, maximum three execution-tool calls and one
final answer. Nine successful API turns consumed **23,161 reported tokens**
(17,287 input, 5,874 output). Requests, raw responses including usage, exact
candidate code, execution outputs, final code and SVGs are retained.

The initial four Chat Completions requests and one diagnostic request were
rejected with HTTP 400 before generation: this reasoning/tool combination
requires Responses. They are operational errors, not model failures. The
corrected runner follows the [official function-calling documentation](https://developers.openai.com/api/docs/guides/function-calling).
No token usage was returned for the rejected calls; this is not a billing claim.

Tool feedback exposed validity, solid count, bounding box, volume and geometric
change against the supplied **source only**. The hidden target was used solely
by the final grader. Generated code ran through a limited CAD AST in separate
processes, with a 150-second execution timeout. This is a bounded tool baseline,
not unrestricted Codex, FreeCAD GUI use or an IterCAD reproduction.

The first elbow candidate reused a mutable sweep-path object. Its result was
topologically valid but had two solids and much less volume. Astra then submitted
a version with separate sweep paths and obtained the correct single solid.
This is a retained **repaired intermediate error**, not an unsolved Astra shape.
It demonstrates why execution and connectivity checks matter beyond parsing or
visual plausibility; it does not establish a new verification method.

All final CAD outputs have zero Boolean symmetric-difference volume against the
audited targets. The grader additionally checks CAD validity, solid count and
Boolean volume identities. Equivalent-construction, shifted-geometry, missing-hole,
restricted-execution and STEP-roundtrip controls are in the test suite.

Each final model was exported into real top/front/right SVG projections with
hidden lines and envelope dimensions. The gallery was rendered and inspected.
These are vector inspection sheets with independent view fitting; they lack
complete feature dimensions, GD&T and production drawing approval. No FEM or
physical safety result is claimed for parts without material, load and support
specifications. The earlier frame pilot remains the separate FEM experiment.

Evidence:
- [Frozen cases](../data/cad-native-probe/tasks.json)
- [Results and usage](../runs/astra-cad-native-20260920/screen-responses/summary.json)
- [SVG comparison gallery](../runs/astra-cad-native-20260920/screen-responses/gallery.html)
- [Rendered gallery](../runs/astra-cad-native-20260920/screen-responses/gallery.png)
- [Execution and grading implementation](../scripts/cad_native_probe.py)
- [Verifier tests](../runs/astra-cad-native-20260920/verifier-tests.log)

## Reference audit: avoid manufacturing model failures

Two inspected upstream targets conflict with their instructions:

1. `t2med_torsion_spring` specifies wire radius equal to one quarter of pitch
   4.15 mm; its target uses radius 2 mm instead of 1.0375 mm. Excluded from calls.
2. `t5hard_heat_sink_V_a` asks to retain the span. The source's four centres have
   19.96 mm spacing, spanning 59.88 mm. The upstream six-centre target uses
   13.3 mm spacing, spanning 66.5 mm. The derived probe fixes the reference to
   11.976 mm and explicitly states the fixed centre positions before testing.

These are case-level observations, not an estimated dataset error rate. Candidate
records were not sampled randomly. Other ambiguous examples were not promoted
to the benchmark merely because they looked difficult.

The elbow source's imported STEP and executed code have equal volume and full
intersection, but one subtraction direction incorrectly retains the whole solid.
That contradiction persists across the checked Boolean tolerances. It is an
evaluator/kernel inconsistency; an earlier raw audit difference must not be read
as an actual shape mismatch. The revised grader refuses a geometric verdict if
`V(A\B)+V(A∩B) != V(A)` or its reverse exceeds relative tolerance 1e-6.
All four Astra finals were regraded after this addition and still pass.

## Additional prior art that narrows the claim

The earlier [39-source audit](CAD_NOVELTY_OVERLAP_20260920.md) still applies,
especially CADEngBench, CADWorld, CADTestBench, IterCAD, OmniMech and NIST PMI.
Ten further primary sources were checked, including papers, vendor documentation
and clearly identified non-peer-reviewed projects.

| Source | Existing work | What we cannot claim as new |
|---|---|---|
| [CADIR](https://arxiv.org/html/2608.00891v1) | Construction graphs, dependencies, constraints and persistent topology matching across CAD backends | An editable intermediate representation or dependency-aware CAD edits |
| [SVG360](https://arxiv.org/html/2511.16766v3) | Consistent multiview editable SVG assets and cross-view part identity | Multiview SVG consistency in general; its evaluation concerns appearance/vector stability rather than dimensioned engineering edits |
| [MM-SVGEdit](https://arxiv.org/html/2609.06116v1) | Visual target grounding followed by function-based SVG modification for UI design | A learned locator plus deterministic SVG executor |
| [Round-trip artifact co-evolution](https://www.sciencedirect.com/science/article/pii/S0164121226002475) | Controlled changes between class models and database schemas, edit persistence and repeated consistency | Generic linked-artifact or round-trip evaluation; online source inspected despite its November issue date |
| [RedlineBench](https://redlinebench.benfeicht.com/) | Architectural review across sheets, dimensions, schedules and specifications | Cross-sheet inconsistency detection; this is a public project, not verified peer-reviewed evidence |
| [FMforME](https://www.mdpi.com/2076-3417/16/15/7396) | Engineering runtime predicates, structured correction and CAD execution | A verifier or physical-input checker in the loop |
| [MT-LAPR](https://arxiv.org/abs/2410.07516) | Equivalent program perturbations expose repair instability; readability preprocessing | Metamorphic edit testing or normalization as a general method |
| [LLM metamorphic-testing study](https://arxiv.org/abs/2511.02108) | Broad collection and testing of metamorphic relations | Equivalence-based reliability testing itself |
| [LineWise Design Lab](https://www.linewise.io/designlab.html) | Industrial edit locality, constraints and expert evaluation | “Beyond looking right” as the main novelty claim; no training corpus imported |
| [Classical CAD associativity](https://care.dptlab.com/Content/Help/language/drawing/OVfile/T_OV_associativity.htm) | Model changes propagate into drawing views and associative added geometry | Re-exporting changed views or keeping dimensions attached |

This is a broad targeted internet search, not proof that every relevant source
has been found. Snapshots, retrieval failures and hashes are retained in
[the follow-up source audit](cad-novelty-source-audit-20260920/manifest.json).

## Candidate novelty: recover lost engineering relationships before editing

**Provisional research question:** Can a model edit an exported engineering SVG
whose native CAD history and feature correspondences are absent, recover enough
cross-view and dimension relationships to make the edit correctly, and identify
when the drawing lacks enough information for a requested engineering check?

The hypothesized contribution is **recovery and preservation of engineering
relationships from detached drawings**, evaluated by complete edit correctness.
It is not SVG rendering, ordinary CAD associativity, or another solver wrapper.
The present experiment does not test or establish this hypothesis: it supplies
native source code and lets the exporter regenerate every view.

The distinction from the closest reviewed work would have to be demonstrated:
CADIR starts from executable construction operations; SVG360 generates plausible
multiview assets; MM-SVGEdit targets UI elements; CADEngBench evaluates native CAD
engineering tasks. A detached-drawing experiment must recover geometric feature
identity, dimension attachment and edit scope from the provided SVG itself,
while preserving deliberate sheet layout and unrelated detail.

Concrete method to evaluate, **not yet implemented or claimed novel**:

1. Learn a correspondence model over SVG paths, views, dimensions and feature
   hypotheses. Use released CAD-to-drawing pairs to supervise the relationships;
   do not expose the native program at test time.
2. Solve geometric constraints for an edit and retain all supported alternatives
   when the drawing underdetermines a feature. An arbitrary guessed thickness or
   material must not become an asserted FEM input.
3. Apply a local edit, regenerate only justified geometry, and check the actual
   resulting SVG. Attach evidence to each dimension/analysis claim. This design
   builds on existing constraint and CAD representations rather than replacing them.

Checks must match the object: sketch constraints and dimensions; projection and
section consistency; assembly clearances/interference; interval tolerance checks;
statics/stability or FEM when boundary conditions and materials are specified.
Check a table's tipping or a part's mating clearance when that is the relevant
requirement—do not indiscriminately run FEM on every SVG.

Required baselines receive **the same detached SVG input**: Astra with SVG/geometry
tools; Astra allowed to reconstruct CAD and re-export; a rule-based constraint
recovery/editor; and the proposed learned correspondence model. A separate native
CAD oracle measures the cost of losing source information, not a fair competing
model with privileged input. Include an always-regenerate baseline to expose
whether layout preservation adds meaningful work.

The claim survives only if reviewed, repeated Astra failures remain with those
tools, and recovery improves complete engineering edit correctness beyond the
deterministic baselines on unseen design families. If they solve the tasks, this
direction also fails the research go/no-go test. A negative literature search or
a one-model-filtered benchmark is insufficient evidence of novelty.

## Data and training decision

Keep the completed CAD-Editor LoRA pilot as a feasibility baseline. Do not train
on these four solved tasks or any official BenchCAD edit-test records. For the
candidate direction, Drawing2CAD is the nearest SVG/CAD pairing source;
SketchGraphs contributes constraints, and CAD-Editor contributes edit
instructions. Check their source licenses and design ancestry before combining
them. Split by base design and family, not individual view or edit. BenchCAD's
training-oriented code generation release may supply CAD programs only after
excluding evaluation families and auditing lineage.

No new training run was launched: the necessary failure signal has not been
established. The requested confirmed failure-only shape set remains empty.
