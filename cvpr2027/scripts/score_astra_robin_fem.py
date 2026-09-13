"""Evaluate saved Astra contours directly in P2 FEM fields at two mesh levels."""
import argparse
import json
from pathlib import Path
import numpy as np
from skfem import Basis, MeshTri, ElementTriP2
from robin_fem_reference import probe
from svgpatchlab.eval.field_fidelity import extract_contours


def main():
    p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True);a=p.parse_args()
    meshes=[]
    for n in (96,192):
        z=np.load(a.reference/f'mesh-{n}.npz')
        basis=Basis(MeshTri(z['points'],z['triangles']),ElementTriP2())
        assert np.array_equal(basis.doflocs,z['doflocs'])
        meshes.append((basis,z['temperature_dofs']))
    matrix=np.array([[1/400,0,-100/400],[0,-1/400,700/400],[0,0,1.]])
    reports=[];drawings=[]
    for path in sorted(a.runs.glob('plate_*/output.svg')):
        contours,issues=extract_contours(path.read_text(),matrix,0.002)
        missing=[level for level in (10,20,40,60,80) if not any(c.level==level for c in contours)]
        all_errors=[];all_weights=[];reference_deltas=[];rows=[]
        for c in contours:
            values=[probe(b,u,c.points.T) for b,u in meshes]
            errors=np.abs(values[-1]-c.level);delta=np.abs(values[-1]-values[-2])
            all_errors.extend(errors);all_weights.extend(c.weights);reference_deltas.extend(delta)
            rows.append({'level':c.level,'samples':len(errors),'issues':c.issues,
                         'mean_error_C':float(np.average(errors,weights=c.weights)),
                         'max_error_C':float(errors.max()),'mesh_difference_max_C':float(delta.max())})
        report={'id':path.parent.name,'metric':'direct P2 FEM evaluation along sampled SVG contours',
                'temperature_range_C':100,'max_sampling_step':.002,'per_level':rows,
                'mean_error_C':float(np.average(all_errors,weights=all_weights)),
                'max_error_C':float(max(all_errors)),
                'reference_mesh_difference_max_C':float(max(reference_deltas)),
                'missing_levels':missing,'issues':issues,'tolerance_C':.5,
                'geometry_pass':not issues and not missing and all(not r['issues'] and r['max_error_C']<=.5 for r in rows),
                'full_drawing_verified':False,
                'limitations':['Finite sampling, not an error certificate.',
                               'Labels, units, occlusion and contour boundary angles are not separately certified.',
                               'Two-mesh differences estimate reference sensitivity, not true error bounds.']}
        (path.parent/'fem_direct_audit.json').write_text(json.dumps(report,indent=2)+'\n')
        reports.append(report);drawings.append(contours)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    z=np.load(a.reference/'plate_convective_edges.npz')
    fig,axes=plt.subplots(1,len(reports),figsize=(12,4),squeeze=False)
    for ax,report,contours in zip(axes[0],reports,drawings):
        ax.contour(z['x'],z['y'],z['field'],levels=[10,20,40,60,80],colors='#2563eb',linewidths=2)
        for c in contours: ax.plot(c.points[:,0],c.points[:,1],color='#dc2626',ls='--',lw=1)
        ax.set(aspect='equal',xlabel='x',ylabel='y',title=report['id'].rsplit('-',1)[-1]+' token budget\nmax sampled error '+f"{report['max_error_C']:.3f} °C")
    fig.suptitle('Astra (red dashed) vs independent FEM (blue): convective plate')
    fig.tight_layout();fig.savefig(a.runs/'robin_fem_comparison.png',dpi=180)
    fig.savefig(a.runs/'robin_fem_comparison.svg');plt.close(fig)
    (a.runs/'fem_comparison.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps([{k:r[k] for k in ['id','mean_error_C','max_error_C','reference_mesh_difference_max_C','geometry_pass']} for r in reports],indent=2))


if __name__=='__main__':main()
