from pathlib import Path
import json,hashlib,zipfile
D=Path('cvpr2027/data/web-cad-fem-multiphysics');R=D.parents[1]
p=D/'catalog.json';d=json.loads(p.read_text())
for r in d['records'][:2]:
 r['limitations']=[v for v in r['limitations'] if not v.startswith('All saved VTU frames')]; r['limitations'].append('All saved VTU frames contain nonfinite field values: 1086 nodes in MD1e6 and 4566 in MD4e6. Their source meaning and region mask require review; do not silently replace NaNs or score all nodes.')
p.write_text(json.dumps(d,indent=2))
(D/'README.md').write_text('''# Published multiphysics source candidates - 12 October 2026

Three downloaded native Abaqus CAE / numerical-reference candidates: two coupled FEM/MD polymer-fracture cases and one resin-cure cycle. Native CAE geometry has not been independently inspected; none is newly admitted as a strict verified CAD/BREP + FEM benchmark pair. No COMSOL, locally generated geometry, solver runs or model trials.

## Coupled polymer fracture

Source: https://zenodo.org/records/18355528 ; Felix Weber; CC BY 4.0. Original selected members downloaded from the 3.986GB source ZIP by checked HTTP byte ranges. Each extracted original member passes source ZIP CRC and has SHA-256 recorded. Entire parent ZIP MD5 not verified because only selected members were downloaded.

Two cases MD1e6 and MD4e6: original GTPm.cae, GTPm.inp, Julia and LAMMPS inputs, plus respectively 20 and 34 published FE/MD coupled VTU frames. Saved point fields u, uforces and stress are real source simulation output. These are two cases in one physical family, not 54 new tasks. Output names are increment identifiers, not certified physical times. Native CAE may contain geometric parts or only a mesh; Abaqus-compatible inspection is required before CAD qualification. No STEP/BREP or dimensioned drawing verified.

All frames have NaNs in the same number of point entries: 1086 nodes in MD1e6, 4566 in MD4e6. Source region-mask meaning remains unverified. Finite-value statistics are diagnostics, not validated scoring references; preserve NaNs and original arrays. The selected package lacks initial MD particle data, potentials and MD-only trajectories; it is not a complete executable replay package. Julia FE/MD coupling, region masks and units require review.

## Resin cure cycle

Source: https://zenodo.org/records/10025292 ; Jesper Kjaer Jorgensen / Technical University of Denmark; CC BY 4.0. Eight original source files, each publisher MD5 verified, including Box3D_TE.cae, Box3D_TVE.jnl, AbqScript.py, Digimat material files, temperature schedule and 30C14hr_80C10hr_FEA_data.csv.

1910 finite CSV rows: Time, Temperature, Etot, DoC, Tg, ETH11, ECH11. These are publisher FEA history values, not experimental data. Final degree of cure = 0.994059324265; total strain = -0.004613536; chemical shrinkage strain = -0.00388499489054. Complex curing constitutive problem on basic box geometry, not a complex drawing. CAE/journal naming and material state need correspondence review. Source script samples X1Y1 and contains an apparent off-by-one endpoint. Preserve original files; do not run its job-submit lines during inspection. Replay requires Abaqus and Digimat material coupling.

## Bimetal source: verified locally, excluded from source redistribution

Source documentation: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Macro_export_transient_FEM_results.md ; author Luftschraube. Publisher-linked ZIP downloaded locally. Original native FreeCAD BREP imports as two valid solids (100 x 10 x 4 mm overall, 2 mm layers); 21 saved VTU frames have 4072 points, 2143 cells and finite displacement, stress, strain and temperature fields. This is one thermomechanical tutorial case with simple geometry, not 21 complex tasks. Original native FCStd metadata says All rights reserved. LGPL declaration for the macro does not license the data. Source archive/models/VTUs are omitted from the share ZIP; audit summaries and links are included. Unit conversion and independent physics replay remain pending.

## Other downloaded leads: not counted

Tapered springs https://zenodo.org/records/14998785 : downloaded one original 11.77MB Abaqus ODB, all five original input scripts and experimental CSV. Scripts build the geometry, but no prebuilt CAD is supplied. Did not execute scripts. ODB needs a compatible reader. Experimental CSV must not be called FEM results.

Soft actuator https://zenodo.org/records/7838026 : original tutorial ZIP has OBJ geometry and SOFA scripts/PDF, but an empty plot directory and no saved solved numerical field. Not counted as CAD/FEM pair.

Catalog includes field dimensions, finite-value diagnostics, source licenses, checksums, limitations and exact original filenames. Both benchmark tracks remain separate: none of these sources adds an original dimensioned engineering drawing. Numerical model scoring remains disabled pending admission checks.
''')
s=R/'data/web-complex-fem/selected-dataset.json';x=json.loads(s.read_text());x['multiphysics_web_candidate_extension']=dict(catalog='cvpr2027/data/web-cad-fem-multiphysics/catalog.json',pdf='cvpr2027/output/pdf/web-fem-multiphysics-candidates.pdf',zip='cvpr2027/output/datasets/web-fem-multiphysics-candidates.zip',native_cae_reference_candidates=3,strict_verified_redistributable_native_cad_pairs=0,local_only_native_cad_fem_case=1,certified_admissions=0);s.write_text(json.dumps(x,indent=2)+'\n')
files=[p for p in D.rglob('*') if p.is_file() and 'bimetal-transient' not in p.parts and p.name!='package-manifest.json']
(D/'package-manifest.json').write_text(json.dumps([dict(path=str(p.relative_to(D)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],indent=2));files.append(D/'package-manifest.json')
zout=R/'output/datasets/web-fem-multiphysics-candidates.zip'
with zipfile.ZipFile(zout,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,'web-cad-fem-multiphysics/'+str(p.relative_to(D)))
 for p in [R/'scripts/audit_web_multiphysics_sources.py',Path('cvpr2027/tmp/cad-fem-fracture-search/collect_fracture.py')]:z.write(p,'audit-scripts/'+p.name)
 z.write(R/'output/pdf/web-fem-multiphysics-candidates.pdf','web-fem-multiphysics-candidates.pdf')
with zipfile.ZipFile(zout) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()))
print(zout,zout.stat().st_size,'CRC passed')
