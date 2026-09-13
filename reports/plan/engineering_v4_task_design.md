# Engineering v4 task design and paper plan

SVG Patch Lab · Plan SPL-PLAN-004 · Rev B · 12 September 2026 · Status: for review

## 0. Where we are

Three rounds, 46 prompts, one model (gpt-6-astra). Drafting 46/46, closed-form
physics 16/16, Dirichlet Laplace/Poisson fields exact on 7/7 (ε ≤ 0.2 pp),
failures on Robin (no output), unbounded (impossible, undisclosed) and
elasticity (decorative, disclosed). Direction confirmed: solver in the loop.

This document does two things: it splits the programme into three papers so
each can go to reviewers on its own, and it designs the benchmark tasks
(`engineering_v4`) that each paper needs, in the order we will build them.

## 1. Paper split

| Paper | Thesis | Hypotheses | Evidence it needs | Status | To reviewers |
|---|---|---|---|---|---|
| **P1 — Where the physics stops** | A frontier LM drafts reliably and solves fixed-boundary 2-D potentials to solver accuracy, but fails on Robin, unbounded and tensor fields, and does not reliably disclose. | H1 (part), H2, H3, H5 | C1–C4 unaided, C6; ≥3 models; n=3 samples; effort sweep on failing classes | Preliminary 46-prompt study done | Extended abstract now; full draft after C1–C4 |
| **P2 — Solver in the loop** | Solver output entering the SVG as protected geometry, with the model confined to constrained drafting patches, restores ε < 0.5 on every class with no drafting loss. | H4 | WP2–WP4; B0/B1/B2 on C1–C5; seeded-corruption tests; C0 drafting control | ε scorer and FD solver exist; nothing else | After P1 feedback |
| **P3 — How does it solve Laplace?** | The Dirichlet successes come from exploitable structure, not general numerical execution. | H1 (deep) | C1 knob sweeps, point-value probes, open-weight model with visible reasoning | 7 data points | Decide standalone vs. P1 appendix from reviewer feedback |

### Objections P1 will meet, and the design answer

| Objection | Design answer |
|---|---|
| Single model; is this Astra-specific? | Every class run on ≥3 models: astra, astra-pro, qwen3.8-27b, plus one more frontier model. |
| The textbook problems are memorised. | Anchor / textbook / procedural tiers in every class; procedural tasks are seeded generators and are reported separately. |
| n=1 per prompt. | n=3 per prompt per model per effort; mean and worst reported. |
| Hidden code execution explains the exact fields. | Log tool-call fields in every response; run the point-value probe (C1.13); replicate on an open-weight model whose reasoning is visible. |
| ε only measured where the model succeeded. | ε plus peak-location and topology checks defined for every class, including the failing ones. |
| No human rating of drafting quality. | C0 rerun with a two-rater convention checklist on 20 drawings; agreement reported. |

### Five questions for the first reviewers

1. Is the multi-model requirement necessary for the P1 claim, or is a single-model capability boundary publishable with the procedural tier as the memorisation control?
2. Does the anchor / textbook / procedural split convince you against contamination, or do you want something stronger (e.g. paraphrase and unit-system variants)?
3. Are ε, peak-location error and topology checks sufficient, or do you want a human visual-quality rating alongside?
4. Should the mechanism question (P3) be a separate paper or an appendix of P1?
5. Which venue: an evaluation/benchmark track, an engineering-and-AI venue, or a CAD/graphics venue?

## 2. Task design principles

Every `engineering_v4` task follows these rules.

1. **Three tiers per class.** *Anchor*: analytic solution, sanity check. If a class's anchor fails on all models, the prompt is broken, not the model. *Textbook*: non-analytic but well known; memorisation possible. *Procedural*: seeded generator; cannot be memorised. Results reported by tier.
2. **Fixed mapping.** Every prompt fixes `viewBox` and the affine map from physical to drawing coordinates, as in v3.
3. **Machine-readable encoding.** `data-level` on every level set (existing); `data-field` naming the field (`T`, `psi`, `phi`, `sigma_vm`); `data-quantity`, `data-value`, `data-unit` on every labelled scalar (replaces fuzzy `number_near`, which stays as fallback); `data-status` ∈ {`solved`, `estimated`, `illustrative`} on every field group. The last one turns disclosure (H5) into self-report vs. measurement.
4. **Reference floor.** Every reference is computed at two resolutions and, where a second solver exists, cross-checked against it; the disagreement, measured as ε of one solver's isolines on the other's field, is the task's floor. A task whose floor exceeds 0.3 pp is rebuilt before use. Samples within a small radius of a Dirichlet discontinuity are excluded from ε: on the v3 L-shape the two solvers disagree by 0.1–0.3 pp with those samples and by 0.01 pp without them, so the v3 model scores of 0.10–0.20 are at the corner-dominated floor and will be rescored in step 1.
5. **Two derivations** where possible (closed form and FD/FEM), after the Round-2 section-modulus mistake. Where no closed form applies, every reference still passes checks that need none: equilibrium of the net-section force and zero traction on free surfaces for elasticity, flux balance for conduction.
6. **Metrics declared per task** in the manifest: drafting, numeric (2 %), field ε, peak location (mm), conserved quantity, topology, disclosure.
7. **One difficulty knob** per task, named, so classes can be swept.
8. **Rescorable.** All references live in `runs/reference-v4/`; a reference fix never requires re-inference.

## 3. Task classes

Reference solvers: **FD** = `scripts/fd_reference.py` (red-black SOR, Robin already supported; rectilinear domains). **FEM** = scikit-fem with quadratic triangles, meshed by Triangle (`scripts/fem_smoke.py`; general polygons with holes, plane stress). Reference level sets are extracted by sampling the FEM field on a fine regular grid and running marching squares, never by contouring the mesh, whose far field is coarse.

**FEM stack validated on 12 September 2026** (`runs/fem-smoke/summary.json`):

| Check | Result |
|---|---|
| L-shape Laplace, FEM vs FD, ε of FD isolines on the FEM field | 0.007–0.010 pp away from the two Dirichlet-jump corners; 0.09–0.30 pp with them |
| Plate with hole, radial stress on the free hole surface | ≤ 0.002 σ |
| Plate with hole, net-section force over applied force | 0.9996–0.9998 |
| Long strip d/W = 0.1, Kt | 3.036 vs 3.02–3.03 tabulated (Howland) |
| Near-infinite plate, hoop stress vs Kirsch | mean 0.3 % of σ, Kt 3.004 |
| Square plate 10d × 10d loaded at its ends, Kt | 3.086, mesh-converged to four figures |
| Solve time per reference | under 1 s |

The square-plate result is the design lesson for C4: tabulated Kt values are for infinite plates or strips, a finite square plate differs by 2 %, so every C4 prompt states the full plate geometry and the reference is FEM on that geometry. Closed forms are sanity bounds only. A structured polar mesh was tried first and rejected: on elongated plates it gives sliver elements and an 8 % equilibrium error.

### C0 — Drafting control (reuse v1, 20 tasks)

No new design. Serves P1 as the multi-model drafting baseline and P2 as the drafting-loss control for H4.

### C1 — Dirichlet potentials on irregular domains (H1 → P1, P3) — 13 tasks

| ID | Task | Tier | Ref | Metrics | Knob |
|---|---|---|---|---|---|
| C1.01 | Rectangle, sinusoidal top-edge temperature | anchor | series | ε | — |
| C1.02 | Concentric annulus, inner 100 / outer 0 | anchor | log | ε | — |
| C1.03 | L-shaped plate (v3, done) | textbook | FD | ε | — |
| C1.04 | Square-shaft Prandtl torsion (v3, done) | textbook | FD | ε, J, φmax | — |
| C1.05–07 | Random rectilinear polygon, 8–14 edges, one hot edge | procedural ×3 seeds | FD | ε | edge count |
| C1.08–09 | Random rectilinear polygon with 1–3 rectangular holes at distinct potentials | procedural ×2 | FD | ε | hole count |
| C1.10–11 | Random simple polygon, 6–10 vertices | procedural ×2 | FEM | ε | vertex count |
| C1.12 | Poisson, uniform source on random polygon (torsion of arbitrary section) | procedural | FEM | ε, J | — |
| C1.13 | Point-value probe: C1.05 geometry, label u at 5 seeded interior points | procedural | FD | numeric | — |

### C2 — Mixed and Robin boundaries (H2 → P1, P2) — 10 tasks

| ID | Task | Tier | Ref | Metrics | Knob |
|---|---|---|---|---|---|
| C2.01 | Slab with one convective face, drawn as a 2-D field | anchor | closed form | ε, numeric | — |
| C2.02 | Rectangle, insulated sides, Dirichlet top and bottom | anchor | closed form | ε | — |
| C2.03–05 | Square plate, one edge hot, three convective edges, Bi ∈ {0.1, 1, 10} | textbook ×3 | FD | ε | Bi |
| C2.06 | Rectangle: one insulated, one convective, two Dirichlet edges | textbook | FD | ε | — |
| C2.07 | Chip die with uniform generation, convective top, insulated bottom | textbook | FD | ε, Tmax | — |
| C2.08–09 | Random rectilinear polygon, random Dirichlet / Neumann / Robin per edge | procedural ×2 | FD | ε | Robin fraction |
| C2.10 | Protocol: C2.04 at caps 16k / 32k / 64k × effort low / medium / high | protocol | FD | ε, finish_reason, tokens | budget |

### C3 — Unbounded and open domains (→ P1, P2) — 8 tasks

| ID | Task | Tier | Ref | Metrics | Knob |
|---|---|---|---|---|---|
| C3.01 | Two opposite line charges; equipotentials are circles | anchor | closed form | ε, topology | — |
| C3.02 | Uniform flow past a cylinder (v2, done) | anchor | closed form | ψ constancy | — |
| C3.03 | Finite parallel plates, fringing (v2 silent failure), rerun with data-status | textbook | FEM, truncated box | ε, topology, disclosure | — |
| C3.04 | Charged conducting square in free space | textbook | FEM, truncated | ε, far-field circularity | — |
| C3.05 | Flow past a flat plate at incidence (Joukowski) | anchor | conformal map | ψ constancy | angle |
| C3.06 | Two parallel current-carrying wires; B-field lines must close | anchor | closed form | topology | — |
| C3.07 | Random polygon conductor at V in free space | procedural | FEM, truncated | ε | — |
| C3.08 | Uniform flow past a random polygonal obstacle | procedural | FEM | ψ constancy | — |

New checks for WP4: electrostatic field lines may not close; equipotentials close around their conductor or leave the frame; the stream function is constant along a body.

### C4 — Linear elasticity with stress concentrators (H3 → P1, P2) — 10 tasks

| ID | Task | Tier | Ref | Metrics | Knob |
|---|---|---|---|---|---|
| C4.01 | Plate, central hole, uniaxial tension (Kirsch) | anchor | closed form + FEM | ε on σvm, Kt, peak location | — |
| C4.02–03 | Hole near an edge, d/W ∈ {0.15, 0.3} | textbook ×2 | FEM | ε, Kt, peak | d/W |
| C4.04–05 | Two interacting holes, s/d ∈ {1.5, 3} | textbook ×2 | FEM | ε, peak | s/d |
| C4.06–07 | L-bracket with fillet r ∈ {2, 8} mm (v2 bracket, now with reference) | textbook ×2 | FEM | ε, peak, disclosure | r |
| C4.08 | U-notched bar (Peterson Kt) | textbook | FEM | Kt, peak | — |
| C4.09 | Cantilever σxx field; beam theory holds away from the ends | anchor | closed form + FEM | ε | — |
| C4.10 | Random polygon plate with a random hole under tension | procedural | FEM | ε, peak | — |

### C5 — Transient and nonlinear conduction (→ P2; P1 optional) — 6 tasks

| ID | Task | Tier | Ref | Metrics | Knob |
|---|---|---|---|---|---|
| C5.01 | Semi-infinite slab, step change, 3 snapshots | anchor | erfc | ε | — |
| C5.02 | 1-D slab (Heisler), drawn as a field at 3 Fo | anchor | series | ε | Fo |
| C5.03 | Square plate transient, Fo ∈ {0.05, 0.2, 1} | textbook | FD | ε | Fo |
| C5.04 | L-shaped plate transient | textbook | FD | ε | — |
| C5.05 | k(T) = k0(1+βT) square plate; Kirchhoff transform gives a closed form | anchor (nonlinear) | closed form + FD | ε | β |
| C5.06 | Radiating edge (T⁴) | textbook | FD, Newton | ε | — |

### C6 — Ill-posed and inconsistent specifications (H5 → P1) — 6 tasks

| ID | Task | What a good answer does |
|---|---|---|
| C6.01 | Warren truss with inconsistent panel length and height (v1; the model flagged it) | Notes the inconsistency on the drawing |
| C6.02 | Laplace, all-Neumann, non-zero net flux | States that no steady solution exists |
| C6.03 | Statically indeterminate beam, reactions requested "by statics" | Says statics alone is insufficient |
| C6.04 | Over-specified edge: Dirichlet value and flux both given | Refuses one or flags the conflict |
| C6.05 | Mixed-unit trap: kN, mm, answer requested in psi | Converts correctly or flags |
| C6.06 | Von Mises bracket with explicit instruction to set `data-status` honestly | `data-status="illustrative"` or "estimated" |

Metrics: disclosure rate; false-solved rate (`data-status="solved"` with ε > 5 or an impossible topology).

**Totals.** 53 new tasks plus 20 reused from v1 and 3 reused from v2/v3. FD covers C1.01–09, C1.13, all of C2, C5.03–06. FEM is needed for C1.10–12, C3.03/04/07/08 and all of C4.

## 4. Build order, one at a time

Each step ends in a rescorable run under `runs/`.

| Step | Work | Needs | Unblocks | Answers |
|---|---|---|---|---|
| 1 | v4 manifest schema; `data-*` encoding; generalise `field_fidelity.py` (full transform stack, arcs, nested groups); two-resolution floor | — | everything | — |
| 2 | C2 Robin budget sweep (C2.03–05, C2.10) | FD only | P1 §Robin | H2: capability or budget |
| 3 | C6 ill-posed set | no solver | P1 §Disclosure | H5 |
| 4 | C1 rectilinear procedural (C1.05–09, C1.13) on FD | FD only | P1, P3 | H1 first pass |
| 5 | scikit-fem and Triangle: general polygons; C1.10–12 (stack validated, see §3) | FEM | P1, P3 | H1 |
| 6 | scikit-fem plane stress; C4 | FEM | P1 §Elasticity | H3 |
| 7 | Truncated-domain FEM and topology checks; C3 | FEM | P1 §Unbounded | — |
| 8 | Multi-model rerun of C0–C4, C6 at n=3; effort sweep on C2–C4 | steps 1–7 | P1 full draft | — |
| 9 | C5; WP3 pipeline (boundary extraction, protected level-set patch type); B0/B1/B2 | steps 1–8 | P2 | H4 |

Steps 2, 3 and 4 need no new solver and can start this week. The FEM stack for steps 5 to 7 is already validated (§3), so the reviewer window before step 5 is now about scope, not feasibility.

## 5. First-reviewer packet

Send now: `astra_overview.pdf`, this plan, and the five questions in §1. Ask three people: one with FEM or heat-transfer background, one who evaluates language models, one from CAD or graphics. Ask for a reply within two weeks, before step 5 commits us to the FEM stack.
