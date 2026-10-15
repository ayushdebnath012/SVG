# More published CAD + FEM engineering sources

11 downloaded CAD/reference candidates from two sources. Ten wheel geometries represent one modal-vibration family; one e-bike frame has a plot-only displacement reference. No new geometry or FEM solutions were generated locally. No COMSOL source is used. Zero new certified benchmark admissions; no model calls or local solver runs.

## DeepWheel: ten CAD + numerical frequency pairs

Original STEP BREP solids were fetched as selected ZIP members by HTTP ranges from the publisher-linked 7.6GB CAD archive. Each selected member passes the original ZIP CRC and has a recorded SHA-256. All ten import as valid single solids (7,928-9,774 faces). These are publisher-generated, mesh-reconstructed BREP geometries, not human-authored parametric CAD or original dimensioned drawings.

The complete original `deepwheel_sim_results.csv` contains 904 finite, positive mass / Mode7 / Mode11 reference rows. All 904 IDs match original STEP base filenames exactly, corroborated by the publisher's file-matching documentation. Only ten STEP files have been downloaded. Their full IDs, physical metadata, original archive members, scalar references, validity and mass checks are in `deepwheel/catalog.json`. Selection spans the Mode7 frequency range using evenly spaced sorted indices; it is not a blind random holdout.

Material values from publisher paper: A356-T6, E=72GPa, nu=0.33, density=2680kg/m3. Free-free modes, OptiStruct via SimLab, Tet10 mesh, average 6mm. Mode7 follows six rigid-body modes; Mode11 is a publisher-selected spoke mode. No full eigenvectors, nodal stress fields or executable solver decks downloaded.

Important discrepancy: every selected CAD mass computed at stated 2680kg/m3 is approximately 3.25% below published CSV mass; implied density is 2769.89-2769.95kg/m3. This suggests different density/setup, but is an inference without the actual solver deck. Do not silently replace density or claim reference certification. No independent replay, mesh convergence or engineering tolerance certified. Keep public-label contamination and mode reordering in the benchmark audit.

Source: https://dataset.narnia.ai/deepwheel.html and https://huggingface.co/datasets/KAIST-SmartDesignLab/DeepWheel . Soyoung Yoo and Namwoo Kang / KAIST SmartDesignLab and Narnia Labs. Dataset CC BY-NC4.0; noncommercial use with attribution. Original publisher documentation, metadata, source paper and license included. CSV/documentation match the pinned Hugging Face revision recorded in the manifest; full 7.6GB CAD ZIP SHA was not checked because only selected original members were downloaded.

## TU Wien e-bike frame: native CAD + plot reference

Original `ebike-frame.SLDPRT`, `simulation.pdf`, architecture/requirement PDFs and Enterprise Architect file; all eight publisher MD5 checksums verified. The source simulation image displays resultant displacement URES maximum 0.2545mm. This is a rounded image-legend bound, not a full nodal array or independently verified precise maximum. Load magnitude and complete material/BC setup are unreadable in supplied PDF. Native geometric validity and analysis state require a SolidWorks-compatible reader; no neutral STEP export verified. Not ready for automatic engineering accuracy scoring.

Source: https://researchdata.tuwien.ac.at/records/npj9z-j2c96 ; DOI 10.48436/npj9z-j2c96 ; CC BY4.0. Original author metadata preserved.

## Other leads kept separate

Three original ANSYS Workbench composite thermal archives were downloaded into `composite-thermal/`. They contain native DesignModeler `.agdb` geometry and Mechanical databases, but `.skipped_files_on_archive` lists omitted `.rth` result files. No solved temperature arrays verified. They are excluded from paired-case counts and the paired-source ZIP. Archive member inventories and provenance remain in the search log.

Tetrachiral compression (STEP + CAE + experiments), ocular adduction (STEP + INP), CarHoods10k (STL + FEA scalar labels), and Antmicro thermal (FCStd + scripts) are leads with explicit missing-result or missing-native-CAD blockers, not newly counted pairs.

## Benchmark tracks and numerical scoring

Supplied-CAD-to-FEM track gains modal scalar candidates; drawing-to-CAD-to-FEM gains no newly verified dimensioned drawings. PDF CAD views are inspection renders of original solids and the e-bike image is the original publisher page.

`scoring-protocol.json` defines proposed per-mode relative frequency errors; these are scoring rules, not FEM results or measured model scores. Certification remains disabled pending source density/material, replay and convergence review. Keep plot-only e-bike work separate. Earlier source collections are preserved and linked in the main selected-dataset manifest.
