# CADFEM-Bench final: substantive audit

The package payload passes all 1,736 SHA-256 checks. This is an archive-integrity result, not certification of benchmark references or grading behavior. The sealed release has not been modified by this audit.

## Confirmed problems

1. **Four locally calculated targets are scored.** B-FEMCAD-031 uses a locally evaluated capacitor formula; B-FEMCAD-058 uses three locally evaluated pressure-hull formulas. The bundled builder documents and implements those calculations. The statement that all 123 targets are numerical values published by sources is false. Holding both cases under the user's source-only rule leaves 55 primary tasks and 119 outputs.
2. **General rigid rotation fails the rigging geometry gate.** The original source STEP passes. An identical STEP rotated 37 degrees about z and translated fails with “no axis-aligned orientation matches”. See rigging-arbitrary-rotation.json. General rigid registration or a consistently defined drawing frame is needed.
3. **Original FEMCAD numerical evidence is missing offline.** The five tasks link locally compiled tasks, a local builder and hidden reconstructed STEP solids. Their evidence lists do not include the original publisher page/notebook/output assets. Geometry-reference CAD is not FEM numerical evidence. The source claims should be linked to exact original assets with hashes.

The live Wolfram [solid mechanics verification page](https://reference.wolfram.com/language/PDEModels/tutorial/StructuralMechanics/SolidMechanicsVerificationTests.html) explicitly specifies 14.9 for the perforated plate; the [heat-transfer verification page](https://reference.wolfram.com/language/PDEModels/tutorial/HeatTransfer/HeatTransferVerificationTests.html) explicitly specifies 332.97. The claimed 230.197 needs direct inspection of the source output image: a literal search of the fetched SolidMechanics HTML did not find that number. This does not prove it is absent from images. SolidMechanics.html is retained here as a timestamped source snapshot, not added to the sealed benchmark.

## Material limits

- The scored set is 57 tasks /123 outputs, with 51 supplied-CAD and 6 reconstruction tasks. Eleven family labels do not establish 57 distinct engineering problems ; 24 tasks come from three bracket/plate families.
- Fourteen tasks have independent reproduction ; 43 do not. Acceptance bands are still provisional for many tasks.
- Full workflow verification still requires human review. No frontier-model/expert benchmark result is certified by the infrastructure probes.
- Reserved data is public web data and cannot prove absence from model training.
- The full raw library is not embedded. 83 local folders and 6,067 files are indexed; remaining unadmitted raw files stay at external local paths. The package documents this accurately.
- Contact remains held after failed convergence admission; complex physics breadth and mixed source rights remain unresolved.

## What passed

All 1,736 manifested payload files match their SHA-256 hashes. Primary task/reference IDs and output counts match. Forty collection reports are bundled; all 52 PDF-directory entries are classified. The final consolidation preserved the v1.6 scored inputs, references and tooling without admitting extra tasks. Candidate inputs remain separate from the evaluator library.

See audit.json for machine-readable findings. No source-only replacement release or general-rotation correction is claimed by this check.
