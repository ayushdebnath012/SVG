# Twelve-net PCB routing discovery fixture

This is an original, abstract CAD layout task, not a full circuit design. Connect the twelve pairs of pads using one layer of orthogonal traces. Every net must be present. Traces must avoid keepouts, foreign pads and each other. Any feasible layout passes; the reference route and its length are not the answer key.

The frozen `tasks.json` includes a feasible reference, seed and selection protocol. Only board dimensions, blocked sites, net endpoints and the source image are sent to Astra. `reference-audit.json` verifies the exported reference SVG using both grid occupancy and independent continuous distances. The reference is never provided to the model or its checker.

Configuration: requested model `gpt-6-astra`, high reasoning effort, up to four calls to `check_routes`, and 16,000 output tokens per API turn. The checker can evaluate partial or complete candidates. It reports violations, not routing suggestions. No general code execution or routing solver is exposed. This configuration measures planning with geometric feedback, not capability when equipped with an automatic router.

Before testing Astra, the generator constructs feasible paths, shuffles net identities, and retains the first seeded board for which only 1–3 of 150 sampled sequential BFS routing orders succeed. These are classical screening results, not Astra trials. An earlier random-pair generator found no certified feasible candidate and made no model calls. The chosen board has 31 × 21 grid sites, 95 keepouts and 12 nets. Grid pitch is 2 mm, trace width 0.6 mm, pad diameter 1 mm, keepout side 1.2 mm and minimum clearance 0.4 mm.

A hard-case admission requires three fresh-context, completed Astra outputs that violate geometric constraints. API errors, malformed interfaces, truncation and unfinished responses are excluded. Intermediate checker errors that Astra subsequently repairs are not failures. The result applies only to this fixture and configuration; it does not demonstrate a new research contribution or generalize to unseen boards.

From the repository root, using a fresh output directory:

```sh
.venv/bin/python cvpr2027/scripts/cad_dense_routing.py run --output cvpr2027/runs/NEW-RUN/trial-1 --sample 1
.venv/bin/python -m unittest discover -s cvpr2027/tests -p test_cad_trace_routing.py
```

API credentials are read through the existing local configuration. `sample` labels a fresh call; it is not an API random seed. Original prompts, responses, checker outputs and final SVGs are retained. See `runs/astra-dense-routing-20260922` for actual results, rather than inferring outcomes from this prospective protocol.
