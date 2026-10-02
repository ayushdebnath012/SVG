# Astra drawing and routing failure discovery — 22 September 2026

The user clarified that the task is to find and confirm genuinely hard engineering drawing tasks, rather than correct saved drawings. All original model outputs remain unchanged. No training was started.

## Completed screening

| Task | Completed result | Evidence |
|---|---|---|
| Rotate a 12-hole pattern, enlarge blind bores into through holes, deepen counterbores and update three views | Pass | [Primitive SVG audit](../runs/astra-multiview-rotation-20260922/screen/adjudication.json) |
| The same physical edit, exported as compound SVG paths | Pass | [Compound SVG audit](../runs/astra-multiview-rotation-20260922/compound-screen/adjudication.json) |
| Route six PCB connections around keepouts | Pass, first checker call | [Exported SVG audit](../runs/astra-pcb-routing-20260922/trial-1/audit.json) |
| Route twelve PCB connections around keepouts | Pass, first checker call | [Exported SVG audit](../runs/astra-dense-routing-20260922/trial-1/audit.json) |
| Route 24 PCB connections around keepouts | Pass at 32,000 tokens/turn; first checker call | [Exported SVG audit](../runs/astra-large-routing-20260922/budget32k-trial-1/audit.json) |
| Same 24-net board, exact lengths and five locked traces | Pass, first checker call | [Length and SVG audit](../runs/astra-timed-routing-20260922/trial-1/audit.json) |

The two machining rows are paired representations of one physical task, not two independent shape families. Their geometric boundary errors were below 0.000001 mm. Different but correctly attached radial labels were accepted after annotation review. A reference-label position mismatch is not a drawing failure. These two conditions used 137,634 reported API tokens in total. The six- and twelve-net screens used 8,719 and 22,488 reported tokens respectively, including repeated input context. These are token counts, not dollar costs or account-balance measurements.

The machining task supplies exact source SVG coordinates, transformations and view conventions. Astra can use arithmetic and inspect its edited SVG, with four total tool calls. The routing tasks supply exact pad and obstacle coordinates plus the source image. Astra chooses every route; the harness exports those coordinates into SVG. It may make four calls to a geometry checker. A general code executor or router is not provided. Results therefore describe this specified tool configuration.

## Larger routing candidate

A separately frozen 24-net board has 41 × 31 sites, 240 keepouts, 2 mm grid pitch, 0.6 mm traces and a 0.4 mm minimum clearance. A constructively generated reference passes both checks. None of 150 sampled sequential BFS routing orders solved the selected board, but Astra did solve it. Its first 16,000-token response was entirely reasoning and truncated; that run is excluded (21,440 reported total tokens). A fresh 32,000-token-per-turn run passed and used 52,683 total tokens. [Frozen task and protocol](../data/cad-large-routing/README.md).

The user then explicitly requested harder prompts. The first coupled variant gives five locked traces and specifies exact lengths for all 24 nets. It passed with independent SVG length and clearance checks, using 41,440 reported total tokens. Since the visible locked traces also provide helpful information, adding constraints does not establish empirically greater difficulty. [Exact prompt](../data/cad-timed-routing/prompt.txt).

The strongest running variant inserts feasible serpentine detours into the reference and specifies the resulting lengths, up to 236 mm. All routes together occupy 830 of 1,031 usable grid sites; this percentage describes grid occupancy, not physical copper area. The source exposes only five locked traces and all endpoints, obstacles and target lengths. The other reference paths remain hidden. This shares a board with the previous variants and is not an independent shape family. Its outcome is still pending. [Reference audit](../data/cad-serpentine-routing/reference-audit.json), [exact prompt](../data/cad-serpentine-routing/prompt.txt).

A separate mechanical nesting prompt is also running: fit fourteen unchanged irregular parts into 64 × 48 mm stock using quarter turns and 4 mm lattice translations, with no overlaps and a minimum 0.4 mm gap. It is generated from a connected stock partition with scrambled part orientations. The feasible reference passes both discrete occupancy and continuous SVG polygon checks. No hidden placements are supplied to Astra. [Protocol](../data/cad-part-nesting/README.md), [exact prompt](../data/cad-part-nesting/prompt.txt), [reference audit](../data/cad-part-nesting/reference-audit.json).

Admission requires three fresh-context completed model outputs with actual geometry violations. Truncation, unfinished output, malformed interfaces and API errors are excluded. An intermediate mistake repaired before the final output is excluded. Any valid routing passes, even if different from the reference or longer. A confirmed failure would apply to this exact board and tool budget; it would not establish inability under other tools or generalize across a family.

## How the checks work

The routing checker expands horizontal and vertical segments into grid sites and checks endpoints, bounds, blocked sites, foreign pads, missing nets and cross-net contacts. A separate auditor reads the exported SVG and computes continuous physical distances between axis-aligned segments, square keepouts and pads. It verifies the trace stroke widths as well. These provide connectivity and clearance evidence; they do not provide circuit simulation or fabrication approval. FEM is not an appropriate substitute for these routing checks.

Eight routing tests pass, including crossings hidden between vertices, blocked intermediate sites, missing connections, reversed routes, diagonal rejection and independent SVG-distance checks. Four additional tests cover exact lengths, illegal retracing, locked-route edits and equivalent reversal. Thirteen machining/multiview tests also pass. Hidden solution routes are never exposed to Astra or its checker; explicitly locked existing traces are legitimate visible input in the edit variants.

Five nesting tests pass, including actual SVG coordinate tampering, missing/out-of-bounds parts, overlap and the precise rotation convention. The local nesting geometry dependency is Shapely 2.1.2. The independent SVG auditor checks actual polygon shapes under permitted rigid placements as well as their bounds and gap.

## Literature and novelty

The new routing direction has direct prior art. [OmniRouting](https://arxiv.org/abs/2608.04434) evaluates PCB routing, design-rule compliance, schematic connectivity and agentic tool use. Its [official page](https://www.omnieda.com/routing/) links a five-board sample archive; its contents and reuse rights were not validated locally. [PCBWorld](https://arxiv.org/abs/2607.05915) supplies a KiCad-based routing environment, synthetic generators, real-board data and tool-using agents. Its [official repository](https://github.com/LGAI-Research/PCBWorld) was read, but not installed. [PCB-Bench](https://proceedings.iclr.cc/paper_files/paper/2026/hash/051f3997af1dd65da8e14397b6a72f8e-Abstract-Conference.html) covers PCB reasoning and design comprehension.

The nesting direction also has established prior work: [SVGnest](https://github.com/Jack000/SVGnest), [Sparrow](https://arxiv.org/abs/2509.13329), and [Geometry-Aware Reinforcement Learning for 2D Irregular Nesting](https://arxiv.org/abs/2606.10611). Sparrow describes a heuristic and ten real-world instances. The RL paper describes a polygon encoder, learning framework and contour-derived training data. Their primary abstracts were reviewed; those assets were not downloaded or reproduced.

Five new records were added to the registry, bringing it to 72 records with differentiated review depth; SVGnest was already present. This was an abstract/project-page/README review, not a full-paper reproduction. Routing or nesting plus geometric feedback is not a defensible novelty claim. A local Astra failure would be useful diagnostic evidence, not proof of a new research contribution. No released PCB or nesting dataset was downloaded or used for training in this work.
