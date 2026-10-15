# CADFEM contact validation follow-up - 2026-10-14

This add-on contains original web-sourced CAD/FEM data and actual validation evidence. It changes no v1.4 or v1.5 task, reference, tolerance or release file. **No new task is admitted or scored.**

The source is FreeCAD's native shell-to-shell contact example, pinned to Git tree 406063b1116a6cb872bbd92ec27c6f425a8d1f98. Native CAD with saved results, original CalculiX input deck, creation script, source writer convention and extracted original BREP/fields are retained. No third-party source program was executed. The creation script is evidence only. Four writer-convention files match the Git tree's original blob hashes.

## What was resolved

- The serialized force 5,000,000 is 5,000 N: FreeCAD's Quantity.cpp defines 1 N as 1,000 internal units; meshtools.py converts the force to N before deck writing.
- All 7,702 original deck node IDs/coordinates match the native mesh (maximum coordinate gap 7.04e-11 mm).
- All 15,404 thickness-expanded source output nodes match the replay coordinates. Original source maximum displacement is 69.691101907 mm; actual CalculiX 2.23 replay is 69.773735893 mm (0.119% gap). Full displacement-field L2 gap is 0.182%; stress-field L2 gap is 2.666%.
- A shell geometry validator checks analytic cylinder axes/radii and Boolean surface coverage, rather than solid volume. An unchanged original STEP export passes; a 3% scaled test-only copy fails. It does not validate physical setup, normals, mesh, fields or convergence.

## Why the case remains held

Five actual remeshed solves use the unchanged source cylindrical surfaces, radius 25 mm, length 500 mm, thickness 0.5 mm, E=72,000 MPa, nu=0.3, 5,000 N point load and source frictionless penalty-contact configuration. The upper cylindrical face is partitioned in topology to make Gmsh accept the load vertex; original surface area is asserted unchanged. Lower z=0 and upper x=475 translations are constrained exactly as in the source deck. Shell element order/orientation matches the source's S3/S2 convention.

| nominal mesh h (mm) | shell elements | maximum displacement (mm) | maximum von Mises (MPa) |
|---:|---:|---:|---:|
| 6.4 | 9236 | 65.541154 | 1275.420 |
| 5.12 | 14224 | 69.123307 | 1288.850 |
| 4.096 | 22402 | 74.323073 | 1626.581 |
| 3.2768 | 34432 | 79.733876 | 2214.690 |
| 2.6214 | 53882 | 83.948853 | 2533.757 |

The last displacement change is **5.02%**, the previous change 6.79%, and the finest result differs from the saved source by **20.46%**. This fails the existing admission rule (last <1%, previous <2%, reference band <=10%). Peak stress also grows substantially. Do not widen a tolerance to turn these failures into passes. These solves check mesh sensitivity in the same solver family; they do not establish independent-formulation reproduction.

Original source Stats already contain the reference extrema; no locally solved value becomes a reference. This is an elastic, small-displacement computational example with contact. Large displacements and stress do not establish physically valid material strength.

## Use and separation

original-sources/ contains saved source results and is **evaluator-only**: giving the native FCStd to a model would expose the answers. validation/geometry/original-source-shells.step is an unchanged CAD-only export and contains no FEM answers. Keep original input-deck output units (mm, N, MPa). The original solid-contact companion is retained for provenance but has no saved results and is not a CAD+FEM result pair.

The shell validator is standalone and is not automatically wired into the release scorer. Trusted review is still required. Replay and refinement scripts are reproducible with the pinned CalculiX 2.23 conda runtime and the existing CadQuery/Gmsh environment. Original source notices apply; this package is for local research and is not automatically cleared for redistribution.
