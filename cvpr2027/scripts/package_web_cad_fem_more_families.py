from pathlib import Path
import json,hashlib,zipfile,csv,math
R=Path(__file__).resolve().parents[1];D=R/'data/web-cad-fem-more-families';T=R/'tmp/cad-more-families-search';O=R/'output';a=json.loads((D/'deepwheel/catalog.json').read_text());e=json.loads((D/'ebike/catalog.json').read_text())
source_csv=list(csv.DictReader((D/'deepwheel/deepwheel_sim_results.csv').open()));assert len(source_csv)==904 and len({x['file_name'] for x in source_csv})==904;assert all(math.isfinite(float(r[k])) and float(r[k])>0 for r in source_csv for k in ['Mass','Mode7 Freq','Mode11 Freq'])
summary=dict(collection='More original web CAD/FEM engineering sources',collected_date='2026-10-12',source_collections_added=2,engineering_families_represented=2,downloaded_cad_reference_candidates=11,numerical_modal_csv_paired_cad_cases=10,plot_only_native_cad_candidates=1,full_source_modal_reference_rows=904,full_source_modal_cad_pairs_verified_by_exact_filenames=904,full_source_cad_downloaded=False,original_dimensioned_drawing_cases_added=0,certified_benchmark_admissions=0,no_local_geometry_or_fem_generation=True,solver_runs=0,model_calls=0,sources=[dict(source=a['source'],catalog='deepwheel/catalog.json',validation='deepwheel/validation.json',downloaded_paired_cases=10,status='Original STEP BREP + numerical modal frequency scalars; density/mass consistency and replay pending'),dict(source=e['source'],catalog='ebike/catalog.json',validation='ebike/validation.json',downloaded_paired_cases=1,status='Publisher native SLDPRT + contour PDF; plot-only and incomplete solver specification')],earlier_collections_unchanged=True)
(D/'catalog.json').write_text(json.dumps(summary,indent=2))
(D/'README.md').write_text('''# More published CAD + FEM engineering sources

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
''')
held=[dict(source='https://data.mendeley.com/datasets/xjf5cmkjm3/1',status='Held; source archives omit thermal result files explicitly',original_archive_bytes=99615583,download_manifest='composite-thermal/download-manifest.json',archive_inventories=[str(p.relative_to(D)) for p in (D/'composite-thermal').glob('*.members.json')],counted_cases=0),dict(source='https://zenodo.org/records/21669226',status='STEP and Abaqus CAE + experimental records; no numerical FEM results verified',counted_cases=0),dict(source='https://zenodo.org/records/7306040',status='STEP eye assembly and Abaqus decks; no solved output verified',counted_cases=0),dict(source='https://datadryad.org/dataset/doi%3A10.5061/dryad.2fqz612pt',status='STL only verified, no native BREP',counted_cases=0),dict(source='https://github.com/antmicro/thermal-simulation-scripts',status='Native FCStd example and scripts; no saved solved numerical field verified',counted_cases=0)]
(D/'search-log.json').write_text(json.dumps(dict(date='2026-10-12',sources_added=summary['sources'],held_leads=held),indent=2))
(D/'scoring-protocol.json').write_text(json.dumps(dict(status='Prepared proposal, not certified',model_trials_run=0,track='supplied-CAD-to-FEM',drawing_track_status='No new dimensioned source drawings verified',cases=[dict(id=r['id'],cad='deepwheel/'+r['cad'],reference_csv='deepwheel/deepwheel_sim_results.csv',reference_id=r['id'],required_output=['mode_7_frequency_Hz','mode_11_frequency_Hz'],metrics=['100 * abs(predicted_mode7_Hz - reference_mode7_Hz) / reference_mode7_Hz','100 * abs(predicted_mode11_Hz - reference_mode11_Hz) / reference_mode11_Hz'],inputs=r['physics'],certified_scoring_enabled=False,blocker='Stated density and CAD/CSV mass consistency; missing source solver deck and independent replay') for r in a['records']],aggregation='Report each mode and source family separately; do not pool variants as new task types or compare directly with nodal stress scores',no_locally_generated_reference_values=True),indent=2))
selected=R/'data/web-complex-fem/selected-dataset.json';d=json.loads(selected.read_text());d['more_web_engineering_sources']=dict(catalog='cvpr2027/data/web-cad-fem-more-families/catalog.json',pdf='cvpr2027/output/pdf/web-cad-fem-wheel-ebike.pdf',package='cvpr2027/output/datasets/web-cad-fem-wheel-ebike.zip',new_source_collections=2,downloaded_modal_cad_pairs=10,plot_only_native_cad_candidates=1,source_modal_reference_rows=904,source_step_files_downloaded=10,certified_benchmark_admissions=0,status='Original source assets collected; DeepWheel density/mass discrepancy and plot-only e-bike limitations explicit. Unsolved thermal archives excluded from pair count.');selected.write_text(json.dumps(d,indent=2)+'\n')
files=[]
for folder in [D/'deepwheel',D/'ebike']:
 files.extend(p for p in sorted(folder.rglob('*')) if p.is_file())
files.extend(p for p in sorted(D.glob('*')) if p.is_file() and p.name != 'package-manifest.json');files.extend(p for p in sorted((D/'composite-thermal').glob('*.json')) if p.is_file())
assets=[dict(path=str(p.relative_to(R/'data')),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files];manifest=D/'package-manifest.json';manifest.write_text(json.dumps(dict(assets=assets,excluded_original_archives='Composite thermal: no verified solved arrays'),indent=2));files.append(manifest)
zout=O/'datasets/web-cad-fem-wheel-ebike.zip'
with zipfile.ZipFile(zout,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,str(p.relative_to(R/'data')))
 z.write(O/'pdf/web-cad-fem-wheel-ebike.pdf','web-cad-fem-wheel-ebike.pdf')
 for p in [T/'collect_deepwheel.py',T/'audit_deepwheel.py',T/'register_ebike.py',R/'scripts/report_web_cad_fem_more_families.py',R/'scripts/package_web_cad_fem_more_families.py']:z.write(p,'audit-scripts/'+p.name)
with zipfile.ZipFile(zout) as z:assert len(z.namelist())==len(set(z.namelist()));assert z.testzip() is None
print('Package passed ZIP CRC',zout,zout.stat().st_size,'bytes',len(files),'data files')
