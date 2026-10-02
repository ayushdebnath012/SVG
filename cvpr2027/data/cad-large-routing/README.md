# Twenty-four-net PCB routing discovery fixture

Connect all 24 pad pairs, A–X, on one copper layer while avoiding keepouts, foreign pads, trace contacts and board boundaries. Routes use the integer grid and horizontal/vertical segments. Every feasible route set passes; no length optimum or hidden reference shape is required. This is an abstract routing CAD task, not a complete electrical circuit.

The frozen manifest contains an original, constructively feasible board with 41 × 31 sites and 240 keepouts. Seed 3333 was selected before Astra testing: the first generated 24-net board whose reference passes, but none of 150 randomly ordered sequential BFS runs completes all nets. This measures sensitivity of that simple classical heuristic; it is not an impossibility proof. Reference SVG clearance and connectivity also pass an independent continuous-distance audit.

The source image and exact JSON coordinates are supplied to Astra. Hidden reference routes and the generation seed are omitted. The model is `gpt-6-astra` with high effort, up to four geometric-checker calls and 16,000 output tokens per turn. The model chooses routes; the harness exports them as SVG polylines. No general code execution or automatic router is supplied. Checker feedback contains only constraint violations.

A hard-case admission requires three independent fresh-context completed responses with actual geometric violations. A malformed response, API error, truncation or unfinished response does not qualify. A repaired intermediate mistake does not qualify. An admitted case would establish repeatable failure on this exact configuration, not inability to solve the board with different tools, nor failure across a shape family.

Run from the repository root, using a new output directory:

```sh
.venv/bin/python cvpr2027/scripts/cad_large_routing.py run --output cvpr2027/runs/NEW-RUN/trial-1 --sample 1
```

`sample` is a run identifier, not a random seed sent to the API. The existing local credential loader is used. The experiment directory preserves API requests, responses and checker outputs. `code-snapshot` records implementation hashes; the wrapper hash supplements the core script hash in each API protocol.

The initial 16,000-token screen was incomplete and is excluded. A fresh-context retry uses `--max-output-tokens 32000`; its protocol is distinct, and any repeats must use that same larger allowance. No completed failure is inferred from the smaller-budget run.

PCB routing benchmarks and tool-feedback methods are already covered by [OmniRouting](https://arxiv.org/abs/2608.04434) and [PCBWorld](https://arxiv.org/abs/2607.05915). This local pilot does not establish novelty. No model has been trained on this fixture.
