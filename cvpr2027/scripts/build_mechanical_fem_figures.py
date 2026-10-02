"""Scientific FEM surface-stress figures; actual solver fields, not generated illustrations."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[1];run=ROOT/'runs/mechanical-cad-fem-20261002';rs=json.loads((run/'results.json').read_text());cs={c['id']:c for c in json.loads((run/'contracts.json').read_text())};figures=ROOT/'paper/network/figures'
for group in range(2):
 fig=plt.figure(figsize=(10,10.5));fig.suptitle('Scenario-defined FEM: target and actual H100 output',fontsize=15,y=.99)
 for row,r in enumerate(rs[group*3:group*3+3]):
  models={}
  for role in ['target','prediction']:
   v=r['roles'][role]
   if v['final']:
    level=len(v['history'])-1;d=np.load(run/r['source_record_id']/f'{role}-mesh-{level}/solution.npz');models[role]=d
  cap=max([float(r['roles'][role]['final']['vm_p95_MPa']) for role in models] or [1]);norm=Normalize(0,cap);cmap=plt.get_cmap('turbo')
  for col,role in enumerate(['target','prediction']):
   ax=fig.add_subplot(3,2,row*2+col+1,projection='3d');ax.set_title(r['source_record_id'].replace('_',' ')+'\n'+('Released target' if role=='target' else 'Actual final-adapter prediction'),fontsize=9,pad=0)
   if role not in models:
    ax.text2D(.12,.48,'NO FEM RESPONSE\nBoundary meshing failed\nNo contact or shape repair assumed',transform=ax.transAxes,color='#9b2226',fontsize=12);ax.set_axis_off();continue
   d=models[role];xyz=d['points'];tet=d['tetrahedra'];vm=d['vm_MPa'];faces=np.concatenate([tet[:,[0,1,2]],tet[:,[0,1,3]],tet[:,[0,2,3]],tet[:,[1,2,3]]]);owners=np.tile(np.arange(len(tet)),4);unique,ix,count=np.unique(np.sort(faces,axis=1),axis=0,return_index=True,return_counts=True);surf=unique[count==1];stress=vm[owners[ix[count==1]]]
   collection=Poly3DCollection(xyz[surf],facecolors=cmap(norm(stress)),edgecolors='none',linewidths=0);ax.add_collection3d(collection)
   m=r['roles'][role]['final'];axis=np.array(cs[r['id']][role+'_axis']);q=xyz@axis;fixed=np.unique(surf);fixed=fixed[q[fixed]<=q.min()+.05*np.ptp(q)];sample=fixed[::max(1,len(fixed)//120)];ax.scatter(*xyz[sample].T,color='#234c9e',s=2,depthshade=False)
   centre=xyz[q>=q.max()-.05*np.ptp(q)].mean(axis=0);span=np.ptp(xyz,axis=0).max();ax.quiver(*centre,*(axis*span*.17),color='#b22222',arrow_length_ratio=.3,linewidth=2)
   allpoints=np.concatenate([model['points'] for model in models.values()]);mid=(allpoints.max(axis=0)+allpoints.min(axis=0))/2;radius=np.ptp(allpoints,axis=0).max()/2
   ax.set_xlim(mid[0]-radius,mid[0]+radius);ax.set_ylim(mid[1]-radius,mid[1]+radius);ax.set_zlim(mid[2]-radius,mid[2]+radius);ax.set_box_aspect((1,1,1));ax.view_init(elev=22,azim=-55);ax.set_axis_off()
   ax.text2D(.05,.04,f"C = {m['compliance_N_mm']:.3e} N mm; {m['tetrahedra']:,} tets",transform=ax.transAxes,fontsize=8)
  if models:
   cax=fig.add_axes([.91,.70-row*.295,.012,.15]);bar=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,extend='max');bar.ax.tick_params(labelsize=7);bar.set_label('von Mises [MPa]\nclipped at common p95',fontsize=7)
 fig.text(.07,.015,'Assumed E = 210,000 MPa, nu = 0.3; 1 N test load. Blue: fixed nodes; red: load direction.\nUndeformed meshes; compliance mesh check only. Stress fields are diagnostic, not a strength/safety verdict.',fontsize=9)
 fig.subplots_adjust(left=.03,right=.88,bottom=.07,top=.94,hspace=.13,wspace=.02);fig.savefig(figures/f'mechanical-fem-examples-{group+1}.pdf',dpi=200);fig.savefig(figures/f'mechanical-fem-examples-{group+1}.png',dpi=160);plt.close(fig)
print('FEM figures exported')
