# FEMCAD-Hard v1

## Joint CAD+FEM benchmark

The current intended benchmark is **one end-to-end CAD-to-FEM task**. See [joint-benchmark.md](joint-benchmark.md) for the strict candidate inputs, submission contract, checker and per-study blockers. All 50 are preparation drafts; none is certified for scoring. The older source-assisted packages below supply geometry/recipes and measure a different task.

## Isolated candidate inputs (50-study edition)

Use the [input packaging report](input-packaging-report.md) for the separate candidate and held-out packages. The combined JSONL and illustrated PDF contain answers and must not be passed to a candidate. The new exporter supplies one isolated task at a time and refuses known blocked tasks. No scoring-readiness claim is made.

The illustrated PDF also includes 50 advanced COMSOL source studies in
`advanced-source-studies.json`, beginning with rubber boot self-contact, a piezoelectric valve,
turbine stator creep, compound gear-train vibration and a perforated muffler. These entries carry
original source drawings, source-page hashes and published-analysis summaries. They are
not validated grading tasks and are kept outside `tasks.jsonl`; published curves and
approximate observations are explicitly distinguished from benchmark reference values.
"Super hard" is an editorial difficulty assessment. Fetch them with
`python scripts/fetch_femcad_advanced_sources.py`. The broader bounded crawl is
`python scripts/crawl_femcad_comsol.py discover`, then `inspect`, then `collect`.
The selected existing studies and their source-analysis summaries are recorded in
`comsol-crawl-selection.json`. Unavailable source drawings are omitted. Rebuild the PDF
with `python scripts/export_femcad_hard_pdf.py`.

5 CAD + FEM tasks on engineering parts, built only from pages crawled on Wolfram's FEM documentation and mfem.org. Each asks a model to build an FEM-ready CAD model of the part (CadQuery -> part.step) and run the finite-element analysis set out on the source page (fem.py -> results.json). Every task's part is drawn on its source page (CAD render, dimensioned drawing or part mesh; see `figures`). Prompts are self-contained; values the scraped code does not contain are set in the task and listed in `provenance_notes`.

## Categories (from https://www.wolfram.com/language/core-areas/fem/)

| Category | Tasks |
|---|---|
| Geometric Modeling | 0 |
| Mesh Generation | 0 |
| Heat Transfer | 1 |
| Fluid Dynamics | 0 |
| Mass Transport | 0 |
| Solid Mechanics | 3 |
| Acoustics | 0 |
| Electromagnetics | 1 |
| Multiphysics | 0 |
| System Physics | 0 |
| Seamless Workflow | 0 |

Mass Transport and System Physics are empty: the crawled pages model those physics only on plain domains (rectangles, rooms), not on engineering parts.

Tiers: hard 5, complex 0, hardest 0. Sources: Wolfram 5, mfem.org 0. 3-D solids 5, 2-D domains 0.

## FEM problems

5 tasks pose the FEM problem their source page solves (when the part is built on a companion page, e.g. the OpenCascadeLink Book Shelf Bracket analysed in the Solid Mechanics tutorial, `source.geometry_page` names it). 0 () take their part from a CAD-only page and state an analysis set here (`analysis_source`).

## Sources and scraping

* Wolfram: crawled from the FEM core-area page into the PDE-model collection and tutorials, the FEMDocumentation tutorials and the OpenCascadeLink tutorials it links (robots.txt honoured): `scripts/scrape_wolfram_fem.py`, manifest `wolfram-sources.json`.
* MFEM: crawl of mfem.org (no robots.txt served): `scripts/scrape_mfem_site.py`, manifest `mfem-sources.json`.
* Raw pages stay in git-ignored `tmp/`; only URLs, hashes, dates and extracted parameters are kept here. Each task records its page URL and the hash of the page it was built from.

## References

* exact (closed form computed by the build script): FEMCAD-031, FEMCAD-058.
* page (value stated on the source page, e.g. its verification test): FEMCAD-057, FEMCAD-062, FEMCAD-067.
* example (printed by the MFEM example itself, run as shipped from the MFEM 4.10 release): none.

Every task in the dataset has a reference answer for every output (closed form or stated on the source page; nothing is solved here) and a showcase-style picture of its part crawled from the source pages (a CAD render or a meshed-part render, like the FEM page's carousel; schematic line drawings alone do not count). Tasks missing either are left out: FEMCAD-001, FEMCAD-002, FEMCAD-003, FEMCAD-004, FEMCAD-005, FEMCAD-006, FEMCAD-008, FEMCAD-011, FEMCAD-014, FEMCAD-015, FEMCAD-016, FEMCAD-017, FEMCAD-019, FEMCAD-020, FEMCAD-021, FEMCAD-022, FEMCAD-023, FEMCAD-026, FEMCAD-032, FEMCAD-033, FEMCAD-034, FEMCAD-036, FEMCAD-038, FEMCAD-042, FEMCAD-043, FEMCAD-044, FEMCAD-054, FEMCAD-055, FEMCAD-056, FEMCAD-059, FEMCAD-060, FEMCAD-061, FEMCAD-063, FEMCAD-064, FEMCAD-065, FEMCAD-066, FEMCAD-068, FEMCAD-069, FEMCAD-070, FEMCAD-071, FEMCAD-072.

## CAD drawings

`figures` lists the source pages' drawings of the task's part: CAD renders (`cad`), 2-D outlines and dimensioned cross-sections (`drawing`) and meshes of the part (`part-mesh`); `category_showcase` adds the CAD and meshed-part images of the Wolfram FEM page's carousel for the category. Every crawled image was reviewed by eye (`figure-curation.json`): PDE solution plots, graphs, abstract domains, set-up schematics and screenshots were dropped, and images on pages with several parts are assigned to the task whose part they show. Images are Wolfram's / MFEM's: referenced by URL, local copies in git-ignored `tmp/femcad-figures/`.

Draft tasks removed: FEMCAD-007, 009, 010, 012, 013, 018, 024, 025, 027, 028, 029, 030, 035, 037, 039, 040, 041 and 045-053 (domains, eggs, tissue, rooms and textbook spheres without a CAD drawing of an engineering part).

## "Cannot solve" filter

Not yet run (`pilot.status`). Run the available models on every task, keep the ones they fail and report pass rates.

Built by `scripts/build_femcad_hard_dataset.py`.

## Difficult FEM edition

The PDF now contains only the 50 crawled COMSOL source studies; the original five examples remain in `tasks.jsonl` but are excluded from this edition. Four weaker fits were replaced with multiscale composite failure, manufacturing variations in an electromechanical gyroscope, sports-car-door fluid–structure interaction, and two-phase fluid–structure interaction. All retained drawings are original source images. Difficulty is editorial; Astra failure has not been tested.

## Published solver and numerical reference assets

A follow-up crawl verified public solver models with binary mesh and solution archive entries for all 50 advanced studies, matching their tutorial versions. See [reference-assets-report.md](reference-assets-report.md) and [reference-assets.json](reference-assets.json). Four standalone reference tables were downloaded: muffler experimental transmission loss, sheet-forming experimental punch-force data, and tweeter sound-pressure/impedance response tables. Stored assets are under `tmp/femcad-reference-assets/`. Archive evidence is not independent convergence or accuracy validation. No FEM values or grading thresholds were synthesized.

## Combined 50-study dataset

`advanced-tasks.jsonl` contains one row per advanced study with its original task description, figures and complete `published_fem_assets` inventory. Source binaries/supporting files remain at their recorded local paths or verified source download URLs. The PDF includes a source-model link for every study plus a solver inventory and numerical-reference appendix. Grading tolerances remain unvalidated. The legacy `tasks.jsonl` is separate and still contains the original five examples.
