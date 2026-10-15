# Astra on SFEM: direct stress prediction pilot

**Run status: BLOCKED_PROVIDER.** No accuracy claim is possible for cases without a generated prediction.

Six distinct geometries from the published validation archive, selected in archive order without inspecting stress labels. Two small, two medium and two large load cases. This is a convenience pilot, not an estimate of full-dataset accuracy.

Astra received full vertex coordinates (rounded to six decimals), tetrahedral connectivity, fixed-node IDs, material and load class, two geometry-only views, and the published simulation source. VonMises, displacement and stress-tensor labels were withheld. Each completed case used one gpt-6-astra call, with no solver tools or repair feedback. OpenAI requests specify low reasoning effort; the configured Experiential Labs route uses its default effort. Provider attempts and rejected calls are retained separately.

Completed predictions: 0/6. Complete 32-vertex predictions: 0/6. API calls: 2. Estimated cost at the runner's configured rates: $0.0000 (cap $5.0).

| Geometry / load | Sample relative L2 error | Queries within ×2 | Archived field max | Astra field max |
|---|---:|---:|---:|---:|
| 02530_001_final_medium_Load | no_prediction / abstention | — | — | — |
| 12430_001_final_small_Load | no_prediction / abstention | — | — | — |
| 00034_003_final_large_Load | no_prediction / abstention | — | — | — |
| 03017_001_final_small_Load | no_prediction / abstention | — | — | — |
| 03797_002_final_large_Load | no_prediction / abstention | — | — | — |
| 00121_005_final_medium_Load | no_prediction / abstention | — | — | — |

Relative L2 = ‖prediction − archived stress‖₂ / ‖archived stress‖₂ over 32 preselected vertex IDs. Summary targets are statistics of the saved median VonMises field over all vertices, not maxima across random simulations. Stress values retain raw dataset units (Pa under an SI-consistent interpretation).

## Interpretation limits

- No new FEniCSx solve was run. Comparisons use the released raw H5 labels.
- H5 input features omit realized stochastic load facets and random seeds; exact reconstruction is not identifiable from these features alone.
- The current simulation source applies normal surface traction using the load parameter, despite the README describing forces in N.
- The current source overwrites each iteration’s result inside the impact-zone loop, leaving the last zone before taking medians. The exact code revision that generated the archive is unknown, so this is a source audit observation rather than proof about every archived label.
- Source material constants are E = 2.303e9 and ν = 0.4002. No remeshing, unit rescaling, training or target normalization was performed.

## Reproduce / inspect

Run from repository root:

```sh
.venv/bin/python cvpr2027/scripts/sfem_astra_stress.py report --out cvpr2027/runs/sfem-astra-20261010
```

`dataset_manifest.json` pins the dataset revision, repository commit, archive members and file hashes. `protocol.json` records the label exclusion and evaluation metrics. Per-case folders contain input JSON, geometry image, saved API request/response/usage; completed cases additionally contain parsed predictions and scores. `run` skips existing attempts and never automatically retries billable calls.

## Provider blockers

- openai: HTTP 429. See `02530_001_final_medium_Load/api/call-001-stress.json` for the recorded error.
- explabs: HTTP 429. See `02530_001_final_medium_Load/api-explabs/call-001-stress.json` for the recorded error.

After funding/unlocking the desired provider, resume with:

```sh
.venv/bin/python cvpr2027/scripts/sfem_astra_stress.py run --out cvpr2027/runs/sfem-astra-20261010 --budget 5 --provider openai --retry-rejected
.venv/bin/python cvpr2027/scripts/sfem_astra_stress.py report --out cvpr2027/runs/sfem-astra-20261010
```

Use `--provider explabs` for the alternate route. `--retry-rejected` archives only confirmed zero-cost rejected attempts before retrying; successful or uncertain dispatches are never retried by this flag.
