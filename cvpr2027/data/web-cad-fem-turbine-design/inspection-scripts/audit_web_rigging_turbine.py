"""Read original CAD and transcribe publisher plot labels; never solve or generate CAD."""
from pathlib import Path
import hashlib
import json
import re
import shutil

import cadquery as cq

T = Path('cvpr2027/tmp/cad-fem-new-complex-search')
R = Path('cvpr2027/data/web-cad-fem-rigging-plate')
D = Path('cvpr2027/data/web-cad-fem-turbine-design')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def shape_audit(path):
    s = cq.importers.importStep(str(path)).val()
    b = s.BoundingBox()
    return dict(valid=s.isValid(), solids=len(s.Solids()), shells=len(s.Shells()),
                faces=len(s.Faces()), bbox_mm=[b.xlen, b.ylen, b.zlen], volume_mm3=s.Volume())


ocr = json.loads((T / 'rigging-original-legend-ocr.json').read_text())
rows = []
# Exact labels checked visually in the original Stress.png and Deformation.png.
stress = [526.74, 477.42, 494.7, 504.34, 499.57, 497.77, 507.92]
deformation = [1.5883, .6062, .76743, 1.6968, .58854, 2.9133, 1.6823]
sf = [.95494, 1.0536, 1.0168, .99734, 1.0069, 1.0105, .9903]
readme_lbf = [2697.7, 2384.5, 4768.8, 2222.5, 2810.1, 3372.1, 3034.9]
for i in range(1, 8):
    folder = next((R / 'FEA Analysis').glob(f'Test {i} (*)'))
    targets = []
    for name, quantity, value, unit in [
        ('Stress.png', 'maximum_equivalent_von_mises_stress', stress[i-1], 'MPa'),
        ('Deformation.png', 'maximum_total_deformation', deformation[i-1], 'mm'),
        ('Safety Factor.png', 'minimum_safety_factor', sf[i-1], 'dimensionless'),
    ]:
        path = folder / name
        original = next(x for x in ocr if Path(x['path']) == path)
        suffix = 'Min' if name == 'Safety Factor.png' else 'Max'
        text = next(s for s in original['text'] if s.endswith(suffix))
        assert float(text.split()[0]) == value, (i, name, text, value)
        targets.append(dict(quantity=quantity, value=value, unit=unit, original_image=str(path.relative_to(R)),
                            image_sha256=sha(path), extraction='Original legend label, OCR crosscheck; stress and deformation visually checked',
                            source_legend=text, raw_field_available=False))
    boundary = next(x for x in ocr if Path(x['path']) == folder / 'Boundary Conditions.png')
    rows.append(dict(id=f'rigging-plate-load-{i}', geometry_id='riggingplate-14mar2024',
                     source_folder=str(folder.relative_to(R)), targets=targets,
                     source_readme_strength_label_lbf=readme_lbf[i-1],
                     source_folder_strength_label_lbf=float(re.search(r'\(([\d.]+) lbf', folder.name)[1]),
                     boundary_condition_image=str((folder / 'Boundary Conditions.png').relative_to(R)),
                     boundary_legend_ocr=boundary['text'], certified=False))

sh = shape_audit(R / 'riggingplate-14mar2024.step')
assert sh['valid'] and sh['solids'] == 1 and sh['faces'] == 145
cat = dict(collection='Published rigging plate: dimensioned drawing, native CAD and FEM plot references',
           date='2026-10-12', source='https://github.com/mpangch/OpenRiggingPlate',
           revision=json.loads((R / 'download-manifest.json').read_text())['revision'],
           license='CERN-OHL-S-2.0; original license retained', engineering_families=1,
           unique_native_cad_cases=1, published_load_variants=7, scalar_reference_targets=21,
           native_cad_plot_reference_candidates=1, raw_saved_field_cases=0, certified_cases=0,
           cad='riggingplate-14mar2024.step', native_solidworks='riggingplate-14mar2024.sldprt',
           cad_audit=sh, step_units='millimetre from SI_UNIT(.MILLI.,.METRE.)',
           original_dimensioned_drawing='riggingplate-14mar2024-manufacturingnotes.pdf',
           drawing_physical_page=1, drawing_dimensions_verified=True,
           source_material='7075-T6 aluminium', solver='ANSYS static structural, publisher declaration',
           model_calls=0, solver_runs=0, locally_generated_cad=0, records=rows,
           limitations=[
               'FEM references are rounded legends in original images; no .rst, solver deck or nodal arrays found in repository.',
               'Seven load directions use one CAD geometry. They are not seven independent mechanical families.',
               'Source README labels loads as minimum breaking strength; no destructive test or nonlinear failure simulation evidence verified.',
               'Test4 README says 2222.5 lbf, folder says 2225.4 lbf, original force legend says 9899.5 N. Preserve the discrepancy.',
               'Source README says analyses passed, but plotted minimum safety factors for Tests 1,4,7 are below one. No safety certification inferred.',
               'Tests 1 and 5 show nonzero minimum total displacement. Remote support/rotation and rigid-motion contribution must be checked before scoring.',
               'Test5 OCR reads TEST-5R in some legends. Native solution revision correspondence remains unverified.',
               'Mesh convergence, material strength criterion, contact/load application and full remote-displacement settings not established.',
               'Drawing supports the drawing-to-CAD track, but numerical reproduction, tolerances and reference-blind model trials remain pending.',
           ])
(R / 'catalog.json').write_text(json.dumps(cat, indent=2) + '\n')
shutil.copyfile(T / 'rigging-original-legend-ocr.json', R / 'original-legend-ocr.json')
(R / 'COLLECTION_NOTES.md').write_text('''# Published rigging plate collection

One original geometry with seven published loading variants. Original source README.md and LICENSE are untouched. STEP imports as one valid solid with 145 faces; millimetre extents agree with the original drawing. Original drawing PDF, SolidWorks source, STEP, all 28 load/result PNGs and overview retained. No original raw saved result file or solver input deck found.

catalog.json records 21 original plot scalar labels (seven peak von Mises stress, seven peak total deformation, seven minimum safety factor) with file/hash provenance. They are FEM reference values, not frontier-model scores. Images and rounded labels cannot support nodal field-error scoring. No CAD generation, solver execution or model call performed.

Known source discrepancies: Test4 load differs between README and folder; plotted Tests1/4/7 safety factors fall below one despite README's passed statement; nonzero minimum total displacement in Tests1/5 needs support/rotation review. Source strength labels are not verified experimental breaking loads. Seven variants count as one geometry family. Zero certified benchmark admissions. No COMSOL required.

Original source: https://github.com/mpangch/OpenRiggingPlate, pinned revision in download-manifest.json. CERN-OHL-S-2.0 source license retained. CAD validity does not establish physical correctness of the reference simulation.
''')

files = []
for path in sorted(p for p in D.iterdir() if p.suffix.lower() in {'.step', '.pptx'}):
    import requests
    source = 'https://mhkdr.openei.org/files/5/' + requests.utils.quote(path.name)
    files.append(dict(path=path.name, bytes=path.stat().st_size, sha256=sha(path), source=source))
(D / 'download-manifest.json').write_text(json.dumps(dict(source='https://mhkdr.openei.org/submissions/5',
                                                       license='CC BY 4.0 per repository public metadata; embedded proprietary notices retained', files=files), indent=2) + '\n')
audits = [dict(file='Item_26_45m Preliminary CAD Model.STEP', **shape_audit(D / 'Item_26_45m Preliminary CAD Model.STEP'))]
for name in ['Aquantis Model_R1(WET).STEP', '425 INTERNALS.STEP']:
    path = T / (name + '.audit.json')
    audits.append(json.loads(path.read_text()) if path.exists() else dict(file=name, status='collected, independent import pending'))
media = T / 'turbine-original-media/Item_29_Pass through spar analysis review -13 Feb 2012 Rev A'
(D / 'source-figures').mkdir(exist_ok=True)
for name in ['image5.png', 'image29.png', 'image31.png', 'image33.png']:
    shutil.copyfile(media / name, D / 'source-figures' / name)
catalog = dict(collection='Aquantis complex turbine assemblies and published structural FEM review',
               source='https://mhkdr.openei.org/submissions/5', doi='10.15473/1417292', date='2026-10-12',
               publisher='Dehlsen Associates LLC / Naval Surface Warfare Center / Penn State ARL',
               license='Public repository metadata CC BY 4.0; source slides retain Company Confidential and Proprietary markings',
               native_step_files=3, cad_audits=audits, raw_saved_field_files=0,
               paired_native_cad_reference_cases=0, certified_cases=0, status='held from numerical CAD/FEM benchmark pair count',
               published_fem_evidence=dict(presentation='Item_29_Pass through spar analysis review -13 Feb 2012 Rev A.pptx',
                                          slides=[5,6,8,13,14,15,16,17], model_diameter_m=41.5,
                                          source_element_count=139000, source_dofs=450000,
                                          solver_declaration='Abaqus and I-DEAS',
                                          partial_clamp_restraint_spar_E11_text_max=.00402,
                                          partial_clamp_restraint_spar_E11_text_min=-.00387,
                                          partial_clamp_restraint_foam_von_mises_text_max_ksi=1.04),
               limitations=[
                   'Selected blade STEP is titled 45m; source beam validation discusses 47.5m and 45.5m designs; pass-through spar FEM is 41.5m. Same submission does not certify exact pairing.',
                   'Full wet assembly and internals STEP are original detailed designs, not automatically the geometry solved in the 2012 spar review.',
                   'Structural review plots and source scalar text are available, but no raw ODB/RST or input deck is listed for these FEM runs.',
                   'Simple spreadsheet sandwich-beam outputs in the other presentations are not mislabeled as FEM.',
                   'Source has embedded proprietary notices despite public repository CC BY metadata; retain notices and attribution, no public redistribution performed.',
               ], locally_generated_cad=0, solver_runs=0, model_calls=0)
(D / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
(D / 'COLLECTION_NOTES.md').write_text('''# Aquantis complex design source, pairing held

Three original STEP files and four original design-review presentations collected from https://mhkdr.openei.org/submissions/5 (DOI 10.15473/1417292). The pass-through spar review contains actual Abaqus/I-DEAS FEM figures, scalar results, loads and restraint descriptions. Other presentations use spreadsheet beam approximations, which are not additional FEM fields.

Different design revisions and sizes prevent exact native CAD/result pairing: preliminary STEP is titled 45m, beam validation refers to 47.5m/45.5m, pass-through spar FEM refers to 41.5m. Original raw field/result files are not listed. Count zero verified CAD/FEM pairs from this source. Do not use the various pictures as several independent certified tasks.

Public MHKDR metadata gives CC BY 4.0, while source slides retain proprietary markings. Both are recorded and original notices preserved. Local research download only; no public publication or upload. No source script executed, CAD created, FEM solved or model trial performed. See catalog.json for independent import status and original figure provenance.
''')
index = Path('cvpr2027/data/web-complex-fem/selected-dataset.json')
ix = json.loads(index.read_text())
ix['rigging_turbine_web_extension'] = dict(
    catalogs=[str(R / 'catalog.json'), str(D / 'catalog.json')],
    pdf='cvpr2027/output/pdf/web-cad-fem-rigging-turbine.pdf',
    zip='cvpr2027/output/datasets/web-cad-fem-rigging-turbine.zip',
    unique_native_cad_plot_reference_candidates=1, verified_original_dimensioned_drawings=1,
    published_load_variants=7, scalar_reference_targets=21, raw_saved_field_cases=0,
    complex_turbine_source_held=1, certified_cases=0)
index.write_text(json.dumps(ix, indent=2) + '\n')
print('One drawing/CAD/plot-reference candidate; seven loads; 21 scalar references; one turbine source held.')
