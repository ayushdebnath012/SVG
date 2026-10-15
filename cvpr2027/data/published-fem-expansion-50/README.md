# 50 published mechanical FEM source problems

The minimum requested size is **50 distinct engineering problems**. This expansion supplies **50 new source records**, across eight physics families, for benchmark preparation. It does **not** promote them automatically to the executable pilot: that still has three admitted physical cases and zero certified scored cases.

The source is [EDF's official Code_Aster validation library](https://codeaster.gitlab.io/doc/docaster/manuals/man_v/other_pages/list/index.html). The original solver files are pinned to official source commit `4ce70ac7b16b8d88243badd5b83f76f86254e47c`. No physical problem, CAD model or FEM reference was generated locally, and no solver or model API was run. Code_Aster does not require COMSOL.

## Included data

- 50 publisher problem records, counted once per selected physical case, rather than once per mesh, output quantity or benchmark track.
- 62 original publisher geometry illustrations. These include technical sketches and model illustrations; they are not all manufacturing drawings.
- 50 original solver command files and their run manifests, with all data files declared by those manifests downloaded.
- Original FE meshes. MED containers were opened as HDF5 and checked for their mesh groups; this is container integrity verification, not geometry validation.
- 28 cases with a separate original GIBI geometry/preprocessor definition. **Zero native STEP files** are verified in this expansion. A MED mesh must not be described as native CAD.
- 761 published literal FEM baseline assertion blocks, with source line numbers and output selectors. Some assertions contain multiple numerical values. These are source solver baselines, not frontier-model accuracy scores or raw full-field result exports.
- SHA-256 verification of all 245 packaged solver, geometry and illustration assets.

The cases cover compressor and fan blades, piping systems, gyroscopic rotors, submerged cables, fluid-structure vibration, beam and shell buckling, helicoidal shells, layered composites, cracks and fracture, frictional contact, notched plastic specimens, sheet forming, indentation and thermomechanics. Some are calibration examples; this is not a claim that all 50 are complex industrial assemblies or that all mechanical engineering domains are covered.

## Numerical references

Each case JSON contains `published_fem_checks`. Values are copied from the original solver test's **`VALE_CALC`** baseline, preserving its selector and line locator. An accompanying `VALE_REFE` may be analytical, experimental or another solver's reference; it is not substituted for the published FEM baseline.

Values remain in original source units. A column or component name alone can be misleading: for example, a table column named `DY` may contain a reaction-force sum, depending on the original extraction operation. The original command file must be reviewed to establish quantity, units, location, time/load step and stress recovery. `PRECISION` in a publisher regression test is **not** an adopted model acceptance tolerance.

## Benchmark admission remains separate

Before any new case enters `cad_fem` or `analysis_fem`, review drawing completeness, document/source version correspondence, physical inputs, units, geometry-to-mesh mapping, source output extraction and independent convergence. Prepare separate answer-free candidate inputs and evaluator references. Do not expose this release's full solver decks, numerical JSONs or review PDF to a candidate model: they contain answers and solver recipes.

None of these 50 cases is silently added to [the executable pilot](../published-fem-pilot-v1/README.md). Lack of native CAD and a verified import route remains a limitation for the supplied-CAD track. The three earlier admitted pilot cases are separate from these new source records.

## Artifacts

- [catalog.json](catalog.json): exactly 50 case IDs, English labels, families, source links and per-case record paths.
- [records/](records/): original-source provenance, files, hashes, published numerical assertions and pending review items.
- [validation.json](validation.json): integrity checks, counts and MED-container checks.
- [crawl-audit.json](crawl-audit.json): outcomes for 98 discovered candidate documents, including exclusions.
- `cvpr2027/output/pdf/published-mechanical-fem-50-source-review.pdf`: 51-page evaluator review, one page per problem plus a cover.
- `cvpr2027/output/datasets/published-mechanical-fem-50-sources.zip`: the review, records and original source assets. Extract into the repository root to preserve paths.

The ZIP contains original diagrams, commands, meshes and geometry scripts, with publisher documentation links. Full scraped documentation HTML remains in the local acquisition cache. The acquisition/build scripts reflect that cache; rebuilding the entire crawl additionally requires its discovery metadata. Original solver assets retain their GPL notices and [source license](LICENSE-Code_Aster); publisher illustrations retain their original attribution. No new blanket license is asserted over third-party artwork.
