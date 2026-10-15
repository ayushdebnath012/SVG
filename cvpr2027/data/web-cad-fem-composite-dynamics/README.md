# Published CAD + FEM: composite and dynamic examples

Five publisher projects downloaded at the pinned Ansys example-data revision. One ribbed composite-wing assembly adds complex geometry. PCB, curved cyclic sector, sandwich panel and flat laminate add physics variety using simpler geometry.

Original SpaceClaim CAD with serialized ACIS geometry, Workbench archives, solver results, ACP HDF5 definitions and MatML materials are included. Cyclic geometry also has an independently imported valid STEP. Original CAD thumbnails are views, not dimensioned engineering drawings. No CAD creation, source-code execution, new solve or frontier-model call occurred.

Read catalog.json first. Three static RST projects have read-only extracted arrays. The vibration reader NPZs and the LS-DYNA parser NPZ are explicitly UNVERIFIED and must not enter scoring. Vibration displacement decoding is invalid; LS-DYNA shell layout decoding reported warnings. Preserve original binaries for a compatible independent decoder. Fatigue data provide a static stress basis; published synthetic load series and dummy S-N curve are not physical fatigue-life ground truth.

Before admission: establish exact CAD/result revision matching, source units, loads/constraints, material and layup mappings, stress recovery and mesh convergence. Zero certified admissions. Drawing reconstruction and supplied-CAD FEM tracks remain separate. No model scores have been measured.

Download-manifest.json pins original assets and hashes, including four real Git LFS HDF5 objects (not pointer text). Documentation-manifest.json identifies original publisher figures and URLs. Source assets: repository MIT; retain LICENSE. Official documentation/figures retain their separate copyright, local research copies only. No public release has been made.
