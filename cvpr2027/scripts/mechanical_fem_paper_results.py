"""Generate FEM table/disclosure from saved case audits, with failed meshes preserved."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];run=ROOT/'runs/mechanical-cad-fem-20261002';rs=json.loads((run/'results.json').read_text());lines=['% Generated from completed six-case FEM attempt artifacts.']
labels=['Mounting angle','Locator block','Rotated shaft','Propeller','Pan-head screw','Round flange'];rows=[]
for label,r in zip(labels,rs):
 values=[]
 for role in ['source','target','prediction']:
  m=r['roles'][role]['final'];values.append(f"{m['compliance_N_mm']:.3e}" if m else '--')
 err=f"{100*r['relative_prediction_target_compliance_error']:.3f}" if r.get('relative_prediction_target_compliance_error') is not None else '--'
 status={'pass':'Geometry + response agree','fail_geometry_despite_response_agreement':'Geometry fails; response agrees','not_verified_mesh_failure':'Not verified: mesh failure'}[r['combined_edit_check']]
 rows.append(f"{label} & {' & '.join(values)} & {err} & {status} \\\\")
lines.append('\\newcommand{\\femExampleRows}{'+'\n'.join(rows)+'}')
allm=[m for r in rs for v in r['roles'].values() for m in v['history']];maxres=max(max(m['relative_free_residual'],m['relative_force_balance_error'],m['relative_moment_balance_error'],m['relative_energy_error']) for m in allm);maxvol=max(v['final']['relative_mesh_volume_error'] for r in rs for v in r['roles'].values() if v['final'])
lines.append('\\newcommand{\\femAuditSummary}{'+f"Five of six case triples yield 15 solved source/target/prediction configurations with compliance mesh changes below 5\\,\\%. Across their recorded meshes the largest normalized equilibrium/energy error is {maxres:.2e}; final CAD-to-mesh volume error is at most {100*maxvol:.2f}\\,\\%. Three predictions meet both strict geometry agreement and the local 10\\,\\% target-compliance agreement tolerance. The propeller and flange predictions fail geometry while meeting that response tolerance. The screw has no FEM response because its boundary mesh fails; this also affects the source and released target, so it is not attributed solely to the model."+'}')
(ROOT/'paper/network/fem-results.tex').write_text('\n'.join(lines)+'\n')
print('FEM macros saved')
