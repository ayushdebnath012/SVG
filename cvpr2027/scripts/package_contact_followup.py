"""Package actual source-contact validation without altering any benchmark release."""
import json,hashlib,shutil,zipfile
from pathlib import Path
w=Path(__file__).resolve().parents[1];src=w/'data/web-cad-fem-freecad-contact';out=w/'output/contact-validation/freecad-shell';p=w.parent/'cadfem-contact-followup-20261014';p.mkdir(exist_ok=True)
rows=[json.loads(f.read_text()) for f in out.glob('refinement/h-*/result.json')];rows.sort(key=lambda r:-r['h_mm']);assert len(rows)==5 and all(r['solver_finished'] for r in rows)
a=json.loads((out/'comparison/assessment.json').read_text());pub=a['source_max_displacement_mm'];last=abs(rows[-1]['max_displacement_mm']-rows[-2]['max_displacement_mm'])/rows[-1]['max_displacement_mm'];prev=abs(rows[-2]['max_displacement_mm']-rows[-3]['max_displacement_mm'])/rows[-2]['max_displacement_mm'];gap=abs(rows[-1]['max_displacement_mm']-pub)/pub
assessment={'status':'held_not_scored','new_active_tasks':0,'original_source_revision':'406063b1116a6cb872bbd92ec27c6f425a8d1f98','source_correspondence':a,'mesh_refinement':rows,'last_displacement_relative_change':last,'previous_displacement_relative_change':prev,'finest_vs_source_displacement_relative_gap':gap,'displacement_converged_under_existing_admission_rule':last<.01 and prev<.02,'remaining_blockers':['Maximum displacement has not settled under mesh refinement; published value is mesh-dependent.','Peak stress grows under refinement; no justified continuum tolerance.','Source uses small-displacement elastic shells with contact, despite large displacements and high stresses; no real-strength claim.','No independent solver formulation cross-check or full automatic workflow certification.'],'resolved_blockers':['Native force unit convention reconciled against pinned FreeCAD writer source.','Original input mesh matched to native CAD document and expanded output nodes matched to saved fields.','Actual original-deck replay performed with field comparison.','Open-shell cylindrical geometry validator implemented and tested.'],'task_target_policy':'Only original source Stats/fields can be reference data. Refinement/replay values are validation-only and are never substituted as targets.'}
(out/'assessment.json').write_text(json.dumps(assessment,indent=2)+'\n')
shutil.copytree(src,p/'original-sources',dirs_exist_ok=True)
for name in ['comparison','geometry']:
 shutil.copytree(out/name,p/'validation'/name,dirs_exist_ok=True)
for d in [out/'original-mesh',*sorted((out/'refinement').glob('h-*'))]:
 name='original-mesh' if d.name=='original-mesh' else 'refinement/'+d.name;dest=p/'validation'/name;dest.mkdir(parents=True,exist_ok=True)
 for f in d.iterdir():
  if f.suffix in ['.inp','.frd','.dat','.sta','.cvg','.msh','.json','.log']:shutil.copy2(f,dest/f.name)
shutil.copy2(out/'assessment.json',p/'assessment.json')
(p/'scripts').mkdir(exist_ok=True)
for n in ['audit_freecad_contact.py','converge_freecad_contact.py','validate_shell_geometry.py','package_contact_followup.py','report_contact_followup.py']:
 f=w/'scripts'/n
 if f.exists():shutil.copy2(f,p/'scripts'/n)
(p/'runtime').mkdir(exist_ok=True)
for f in (w/'tmp/calculix-contact-env/conda-meta').glob('*.json'):shutil.copy2(f,p/'runtime'/f.name)
readme=f'''# CADFEM contact validation follow-up - 2026-10-14

This add-on contains original web-sourced CAD/FEM data and actual validation evidence. It changes no v1.4 or v1.5 task, reference, tolerance or release file. **No new task is admitted or scored.**

The source is FreeCAD's native shell-to-shell contact example, pinned to Git tree 406063b1116a6cb872bbd92ec27c6f425a8d1f98. Native CAD with saved results, original CalculiX input deck, creation script, source writer convention and extracted original BREP/fields are retained. No third-party source program was executed. The creation script is evidence only. Four writer-convention files match the Git tree's original blob hashes.

## What was resolved

- The serialized force 5,000,000 is 5,000 N: FreeCAD's Quantity.cpp defines 1 N as 1,000 internal units; meshtools.py converts the force to N before deck writing.
- All 7,702 original deck node IDs/coordinates match the native mesh (maximum coordinate gap {a['original_deck_mesh_max_coordinate_gap_mm']:.3g} mm).
- All 15,404 thickness-expanded source output nodes match the replay coordinates. Original source maximum displacement is {pub:.9f} mm; actual CalculiX 2.23 replay is {a['replay_max_displacement_mm']:.9f} mm (0.119% gap). Full displacement-field L2 gap is {100*a['displacement_field_relative_L2_gap']:.3f}%; stress-field L2 gap is {100*a['stress_field_relative_L2_gap']:.3f}%.
- A shell geometry validator checks analytic cylinder axes/radii and Boolean surface coverage, rather than solid volume. An unchanged original STEP export passes; a 3% scaled test-only copy fails. It does not validate physical setup, normals, mesh, fields or convergence.

## Why the case remains held

Five actual remeshed solves use the unchanged source cylindrical surfaces, radius 25 mm, length 500 mm, thickness 0.5 mm, E=72,000 MPa, nu=0.3, 5,000 N point load and source frictionless penalty-contact configuration. The upper cylindrical face is partitioned in topology to make Gmsh accept the load vertex; original surface area is asserted unchanged. Lower z=0 and upper x=475 translations are constrained exactly as in the source deck. Shell element order/orientation matches the source's S3/S2 convention.

| nominal mesh h (mm) | shell elements | maximum displacement (mm) | maximum von Mises (MPa) |
|---:|---:|---:|---:|
'''
for r in rows:readme+=f"| {r['h_mm']:.5g} | {r['shell_elements']} | {r['max_displacement_mm']:.6f} | {r['max_vonMises_MPa']:.3f} |\n"
readme+=f'''
The last displacement change is **{last*100:.2f}%**, the previous change {prev*100:.2f}%, and the finest result differs from the saved source by **{gap*100:.2f}%**. This fails the existing admission rule (last <1%, previous <2%, reference band <=10%). Peak stress also grows substantially. Do not widen a tolerance to turn these failures into passes. These solves check mesh sensitivity in the same solver family; they do not establish independent-formulation reproduction.

Original source Stats already contain the reference extrema; no locally solved value becomes a reference. This is an elastic, small-displacement computational example with contact. Large displacements and stress do not establish physically valid material strength.

## Use and separation

original-sources/ contains saved source results and is **evaluator-only**: giving the native FCStd to a model would expose the answers. geometry/original-source-shells.step is an unchanged CAD-only export under validation/geometry/ and contains no FEM answers. Keep original input-deck output units (mm, N, MPa). The original solid-contact companion is retained for provenance but has no saved results and is not a CAD+FEM result pair.

The shell validator is standalone and is not automatically wired into the release scorer. Trusted review is still required. Replay and refinement scripts are reproducible with the pinned CalculiX 2.23 conda runtime and the existing CadQuery/Gmsh environment. Original source notices apply; this package is for local research and is not automatically cleared for redistribution.
'''
(p/'README.md').write_text(readme)
print(json.dumps({'folder':str(p),'last_change_percent':last*100,'source_gap_percent':gap*100,'new_active_tasks':0},indent=2))
