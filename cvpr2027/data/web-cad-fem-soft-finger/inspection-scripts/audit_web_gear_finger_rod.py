"""Read published CAD/RST and preserve exact saved fields. No solves or CAD creation."""
from pathlib import Path
import hashlib
import json
import re
import shutil

import cadquery as cq
import h5py
import numpy as np
from ansys.mapdl import reader

D = Path('cvpr2027/data')
T = Path('cvpr2027/tmp/cad-fem-kirigami-search')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def audit_cad(path):
    s = cq.importers.importStep(str(path)).val()
    b = s.BoundingBox()
    return dict(valid=s.isValid(), solids=len(s.Solids()), faces=len(s.Faces()),
                bbox_mm=[b.xlen, b.ylen, b.zlen], volume_mm3=s.Volume())


def metadata(root):
    m = json.loads((root / 'download-manifest.json').read_text())
    return dict(source=m['source'], revision=m['revision'], license=m['license'],
                date='2026-10-12', solver_runs=0, model_calls=0, locally_generated_cad=0, certified_cases=0)


F = D / 'web-cad-fem-soft-finger'
records = []
for case in ['Part1', 'Part2_1', 'Part2_2']:
    rst = F / case / 'dp0/SYS/MECH/file.rst'
    native = F / case / 'dp0/SYS/DM/SYS.agdb'
    inp = F / case / 'dp0/SYS/MECH/ds.dat'
    text = inp.read_text()
    assert '/units,MPA' in text
    assert 'MP,EX,1,200000,' in text and 'MP,NUXY,1,0.3,' in text
    assert 'sf,all,pres,0.18' in text
    with h5py.File(native) as h:
        datasets = {k: dict(shape=list(h[k].shape), bytes=h[k].size*h[k].dtype.itemsize) for k in h}
    assert datasets['AGP Parasolid Data']['bytes'] > 40000
    r = reader.read_binary(str(rst))
    states = []
    for i, label in enumerate(r.time_values):
        ids, u = r.nodal_displacement(i)
        sid, s = r.nodal_stress(i)
        meshids, coordinates = r.mesh.nnum, r.mesh.nodes
        assert np.array_equal(ids, sid) and np.array_equal(ids, meshids)
        assert len(np.unique(ids)) == len(ids)
        assert np.isfinite(coordinates).all() and np.isfinite(u).all()
        mask = np.isfinite(s).all(axis=1)
        a = s[mask]
        vm = np.sqrt(.5*((a[:,0]-a[:,1])**2 + (a[:,1]-a[:,2])**2 + (a[:,2]-a[:,0])**2)
                     + 3*(a[:,3]**2 + a[:,4]**2 + a[:,5]**2))
        out = F / f'{case}-saved-result-{i}.npz'
        np.savez_compressed(out, displacement_node_ids=ids, displacement=u,
                            stress_node_ids=sid, stress=s, mesh_node_ids=meshids, mesh_coordinates=coordinates)
        z = np.load(out)
        assert np.array_equal(z['displacement'], u)
        assert np.array_equal(z['stress'], s, equal_nan=True)
        states.append(dict(reader_index=i, static_load_label=float(label), npz=out.name, npz_sha256=sha(out),
                           nodes=len(ids), displacement_dofs=u.shape[1], finite_stress_rows=int(mask.sum()),
                           missing_stress_rows=int((~mask).sum()), nonfinite_displacement=0,
                           maximum_translation_mm=float(np.linalg.norm(u[:,:3], axis=1).max()),
                           finite_subset_maximum_von_mises_MPa=float(vm.max())))
    log = (F / case / 'dp0/SYS/MECH/solve.out').read_text(errors='replace')
    assert 'DISTRIBUTED ANSYS RUN COMPLETED' in log
    assert 'NUMBER OF ERROR   MESSAGES ENCOUNTERED=          0' in log
    records.append(dict(id=case, native_cad=str(native.relative_to(F)), native_cad_sha256=sha(native),
                        native_geometry_container='Ansys DesignModeler HDF5; serialized Parasolid/object data',
                        native_geometry_datasets=datasets, independent_brep_import=False,
                        rst=str(rst.relative_to(F)), rst_sha256=sha(rst), input_deck=str(inp.relative_to(F)),
                        reader='ansys-mapdl-reader 0.56.0', reader_summary=str(r), mesh_elements=r.mesh.n_elem,
                        stress_recovery='reader.nodal_stress averages stored element-nodal stresses at common corner nodes; NPZ preserves reader output including NaNs. Not an unaveraged integration-point stress field.',
                        stress_component_order=['X','Y','Z','XY','YZ','XZ'],
                        recovery_documentation='https://reader.docs.pyansys.com/version/stable/api/rst.html#ansys.mapdl.reader.rst.Result.nodal_stress',
                        solver_units='N, mm, tonne, second; MPa from /units,MPA and input comments',
                        declared_input_youngs_modulus_MPa=200000, declared_input_poisson=.3,
                        declared_input_pressure_MPa=.18, source_log_completed=True, source_log_warnings=2,
                        states=states))
cat = dict(**metadata(F), collection='Chambered finger geometry with original linear-static saved FEM',
           engineering_families=1, native_cad_saved_solution_candidates=3, raw_result_files=3,
           strict_independently_imported_brep_pairs=0, source_report='Report_ANSYS_FEA_PDMS_Finger.pdf',
           original_dimensioned_engineering_drawing_verified=False,
           material_scope='Report calls geometry a PDMS finger; saved input decks use steel-like E=200000 MPa, nu=0.3, density=7.85e-9 tonne/mm^3. These are not verified PDMS constitutive references.',
           records=records, limitations=[
               'One chambered finger family. Part1 is the single-row source configuration; Part2_1/Part2_2 are two-row pressure-scope variants, not three engineering families.',
               'Saved input material conflicts with the intended PDMS description. Preserve the source physics; do not rescale fields to fabricate PDMS results.',
               'Native AGDB contains serialized CAD; no original neutral STEP was located and no independent native BREP import completed.',
               'Displacements are finite at every recorded node; nodal stresses are missing for most mesh nodes. Preserve NaN mask, report coverage and verify element/output support before stress scoring.',
               'All saved runs are static, one result set each; no nonlinear/hyperelastic/dynamic characterization claimed.',
               'Source completed with two warnings and zero errors; completion alone does not establish physical validity or mesh convergence.',
               'Source license unresolved. Assets retained locally for research; no public redistribution performed.',
           ])
(F / 'catalog.json').write_text(json.dumps(cat, indent=2) + '\n')

G = D / 'web-cad-fem-landing-gear'
shape = audit_cad(G / 'CAD/Assembly/Assembly.STEP')
assert shape['valid'] and shape['solids'] == 15 and shape['faces'] == 500
dxf = (G / 'Assembly Drawing/Assembly.DXF').read_text(errors='replace')
dim_count = len(re.findall(r'\nDIMENSION\s*\n', dxf))
gear = dict(**metadata(G), collection='Twin-wheel nose landing gear: native assembly, drawing and FEM report',
            engineering_families=1, native_cad_plot_scalar_candidates=1, raw_saved_field_files=0,
            cad='CAD/Assembly/Assembly.STEP', native_assembly='CAD/Assembly/Assembly.SLDASM', cad_audit=shape,
            native_part_files=[str(p.relative_to(G)) for p in sorted((G / 'CAD/Parts').glob('*.SLDPRT'))],
            source_drawing=['Assembly Drawing/Assembly.DXF', 'Assembly Drawing/Assembly.SLDDRW', 'Assembly Drawing/Assembly.JPG'],
            dxf_dimension_entities=dim_count, original_dimensioned_drawing_verified=False,
            source_report='Report/Landing_Gear_FEA_Report.pdf',
            targets=[dict(quantity='minimum_static_safety_factor', value=.66716, unit='dimensionless',
                          provenance='Original report physical page4 Figure11 image legend; report rounds to0.667'),
                     dict(quantity='average_static_safety_factor', value=13.63, unit='dimensionless',
                          provenance='Original report physical page5 TableII')],
            capped_plot_maximum_safety_factor=15, capped_value_is_exact_strength_target=False,
            simultaneous_loads_N=[[0,0,7062],[0,-2119,0],[0,0,15696]],
            fixed_support='Single trunnion face at top of strut, source report page4 Figure7',
            limitations=[
                'Only standalone .wbpj pointer is published; dependent Workbench model/results tree is absent. Do not label it a solved result archive.',
                'FEM reference is a report scalar and contour; no nodal fields or stress/displacement magnitudes verified.',
                'Native source drawing includes orthographic/isometric assembly views, but inspected DXF has zero DIMENSION entities and raster has no visible dimension callouts.',
                'Source baseline has minimum safety factor below one; source acknowledges mesh/material/dynamic validation limitations.',
                'Report states structural steel defaults and a Nickel wheel-hub assignment. Source materials, contacts and exact load scoping require replay review.',
                'Buckling/fatigue mentioned in repository overview are not counted as verified numerical result cases.',
            ])
(G / 'catalog.json').write_text(json.dumps(gear, indent=2) + '\n')

C = D / 'web-cad-fem-connecting-rod'
shape = audit_cad(C / 'Connecting Rod.STEP')
assert shape['valid'] and shape['solids'] == 1 and shape['faces'] == 63
rod = dict(**metadata(C), collection='Connecting rod: STEP/SolidWorks and published static FEM plots',
           engineering_families=1, native_cad_plot_scalar_candidates=1, raw_saved_field_files=0,
           cad='Connecting Rod.STEP', native_cad='Connecting Rod.SLDPRT', cad_audit=shape,
           step_unit_declaration='Conversion-based INCH', source_report='Connecting Rod Design&Analysis Project Report.pdf',
           original_dimensioned_engineering_drawing_verified=False, original_dimensioned_cad_sketch_images=True,
           targets=[dict(quantity='maximum_equivalent_von_mises_stress', source_value=1.4017e8,
                         source_unit='dyne/cm^2', normalized_value_MPa=14.017,
                         normalization='1 dyne/cm^2 = 0.1 Pa; divide original value by1e7 for MPa',
                         image='Equivalent Stress.png', report_value_MPa=14.02, report_physical_page=16),
                    dict(quantity='maximum_total_deformation', source_value=.031969, source_unit='cm',
                         normalized_value_mm=.31969, normalization='1 cm = 10 mm',
                         image='Total Deformation.png', report_value_mm=.3197, report_physical_page=15)],
           safety_factor_plot_cap=15, source_report_safety_factor=15,
           safety_factor_interpretation='Capped display, not an exact uncensored strength target',
           report_material=dict(youngs_modulus_GPa=200,poisson=.3,yield_MPa=250),
           report_applied_force_N=[-5000,0,-750],
           limitations=[
               'Original STEP uses INCH and imports with4.98m maximum extent. Source FEM screenshot uses cm/CGS and a200cm scale bar. Geometry dimensions/intent must be reviewed, never silently rescaled.',
               'No .rst or dependent Workbench files provided. Standalone .wbpj is a pointer, not saved-field evidence.',
               'Source CGS plot units differ from report units; exact original labels and explicit conversions are retained.',
               'Source safety factor15 is display-capped; do not score as an exact uncensored minimum.',
               'Linear static educational model, no mesh-convergence/fatigue/contact validation established.',
               'Source README says educational and portfolio purposes only, no standard license found. Kept locally for research; no public redistribution performed.',
           ])
(C / 'catalog.json').write_text(json.dumps(rod, indent=2) + '\n')
for root in [F, G, C]:
    (root / 'COLLECTION_NOTES.md').write_text('# Published CAD and FEM collection\n\nOriginal source README and files remain unchanged. See catalog.json for asset types, exact numerical references, units, provenance and admission limits. No source code executed, CAD generated, FEM solution produced or frontier model called. No COMSOL required. Local research collection; retain source license scope before public redistribution.\n')
    (root / 'inspection-scripts').mkdir(exist_ok=True)
    shutil.copyfile('cvpr2027/scripts/audit_web_gear_finger_rod.py', root / 'inspection-scripts/audit_web_gear_finger_rod.py')
leads = dict(kirigami=dict(source='https://datadryad.org/dataset/doi:10.5061/dryad.9zw3r22st',
                          metadata_verified=True, source_archive_bytes=50234658342,
                          status='Public metadata/README inspected; web download403 and API requires bearer token401. No dataset assets downloaded or pairs counted.'),
             sliding_mechanism=dict(source='https://onlinelibrary.wiley.com/doi/10.1155/adce/3694226',
                                    status='Data available from author upon request; no downloadable native CAD verified. Not counted.'),
             cadengbench=dict(source='https://arxiv.org/abs/2608.09296',
                              status='Benchmark paper inspected; no downloadable native CAD/reference-results repository located. Not counted.'),
             openam=dict(source='https://doi.org/10.6084/m9.figshare.c.8086513',
                         status='Paper link found; cited collection API404. No CAD/result assets downloaded. Not counted.'))
(T / 'screened-leads.json').write_text(json.dumps(leads, indent=2) + '\n')
index = D / 'web-complex-fem/selected-dataset.json'
j = json.loads(index.read_text())
j['ansys_nodal_stress_recovery'] = dict(method='ansys-mapdl-reader nodal_stress averages stored element-nodal stresses at common corner nodes, with NaNs where output is unavailable',
                                        applies_to=['marine_anchor_web_extension','gear_finger_rod_web_extension'],
                                        scoring_rule='Match recovered averaged corner-node stress scope; never compare directly with unaveraged integration-point stresses or fill missing nodes with zero',
                                        documentation='https://reader.docs.pyansys.com/version/stable/api/rst.html#ansys.mapdl.reader.rst.Result.nodal_stress')
j['gear_finger_rod_web_extension'] = dict(catalogs=[str(p / 'catalog.json') for p in [F,G,C]],
                                          pdf='cvpr2027/output/pdf/web-cad-fem-gear-finger-rod.pdf',
                                          zip='cvpr2027/output/datasets/web-cad-fem-gear-finger-rod.zip',
                                          engineering_families=3, native_cad_saved_solution_candidates=3,
                                          native_step_plot_scalar_candidates=2, numerical_plot_targets=4,
                                          verified_new_dimensioned_engineering_drawings=0, certified_cases=0,
                                          important_limit='Chambered-finger report says PDMS, saved decks use steel-like linear material. References require explicit source-physics interpretation.')
index.write_text(json.dumps(j, indent=2) + '\n')
print('3 engineering families; 3 original RST solutions; 2 STEP/plot candidates; 0 certified cases.')
