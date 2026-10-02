# Strongest current prompt: dense serpentine routing edit

Complete nineteen routes around five locked existing traces. All twenty-four nets must meet exact specified geometric centerline lengths, avoid 240 keepouts and foreign copper, preserve the locked traces, and avoid retracing or self-contact. The board has 41 × 31 sites at 2 mm pitch. Trace width is 0.6 mm and minimum clearance is 0.4 mm. The longest required route is 236 mm.

The reference uses 830 of 1,031 available grid sites (80.5%). This is site occupancy, not physical copper coverage. It was generated constructively by inserting two-cell detours into valid routes, checking every insertion against occupied and blocked sites. The completed SVG passes the independent continuous-clearance and length auditor. Consequently the prompt is jointly feasible. There is no hidden preferred routing: every routing that meets the visible constraints passes.

`prompt.txt` contains the exact text input, and `source.png` contains the drawing. The model sees the five locked traces, endpoints, obstacles and length targets. The other nineteen reference routes are hidden. `reference.svg` and `reference-audit.json` are evaluator evidence and must not be supplied with the prompt.

The requested model is `gpt-6-astra`, high effort, with 32,000 output tokens per turn and four calls to a checker that reports constraint violations. It is allowed to check partial candidates. No general code executor or router is provided. Three fresh-context completed failures are required for a repeatable case. API problems, malformed interfaces, truncation and incomplete responses are excluded, as are intermediate errors repaired before the final drawing.

```sh
.venv/bin/python cvpr2027/scripts/cad_serpentine_routing.py run --output cvpr2027/runs/NEW-RUN/trial-1 --sample 1
```

This shares the board and locked copper with the simpler length-constrained fixture; it is a paired constraint variant, not an independent layout family. Failure would establish only configuration-specific routing difficulty. It would not show that Astra cannot solve the board with a routing program, or that this is the hardest possible engineering task.

This is geometric routing research, not electrical simulation or a fabrication-approved PCB. [OmniRouting](https://arxiv.org/abs/2608.04434) and [PCBWorld](https://arxiv.org/abs/2607.05915) already cover closely related benchmarks and feedback methods. No novelty or new training is claimed.
