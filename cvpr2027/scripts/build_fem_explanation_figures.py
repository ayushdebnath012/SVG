"""Large explanatory figure from saved mechanical FEM audit artifacts."""
from pathlib import Path
import json, hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'paper/network/figures'
OUT=ROOT/'runs/paper-fem-explanations-20261003';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','pdf.fonttype':42,'svg.fonttype':'none'})
INK='#193345';BLUE='#e7f0f8';GREEN='#e9f3ed';ORANGE='#fff0dd'
files=[]
def read(path):
 files.append(path);return json.loads(path.read_text())
def box(ax,x,y,w,h,title,detail,color=BLUE):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.3,rounding_size=1.1',facecolor=color,edgecolor=INK,lw=1))
 ax.text(x+w/2,y+h*.73,title,ha='center',va='center',fontsize=10,fontweight='bold',color=INK)
 ax.text(x+w/2,y+h*.32,detail,ha='center',va='center',fontsize=9,color=INK)
def arrow(ax,x0,y0,x1,y1):ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=12,color=INK,lw=1.2))
def surface(d):
 t=d['tetrahedra'];f=np.concatenate([t[:,[0,1,2]],t[:,[0,1,3]],t[:,[0,2,3]],t[:,[1,2,3]]]);owners=np.tile(np.arange(len(t)),4);unique,ix,count=np.unique(np.sort(f,axis=1),axis=0,return_index=True,return_counts=True);return unique[count==1],owners[ix[count==1]]
def draw(ax,d,mode,axis):
 xyz=d['points'];surf,owner=surface(d);span=np.ptp(xyz,axis=0).max()
 if mode=='mesh':colors='#e7edf2';ec='#607988';values=None
 elif mode=='displacement':values=np.linalg.norm(d['displacement'],axis=1)[surf].mean(axis=1);colors=plt.cm.viridis(Normalize(0,np.linalg.norm(d['displacement'],axis=1).max())(values));ec='none'
 else:values=d['vm_MPa'][owner];colors=plt.cm.turbo(Normalize(0,np.percentile(d['vm_MPa'],95))(values));ec='none'
 ax.add_collection3d(Poly3DCollection(xyz[surf],facecolors=colors,edgecolors=ec,linewidths=.23))
 q=xyz@axis;nodes=np.unique(surf);fixed=nodes[q[nodes]<=q.min()+.05*np.ptp(q)];fixed=fixed[::max(1,len(fixed)//100)];ax.scatter(*xyz[fixed].T,color='#1852b0',s=4,depthshade=False)
 centre=xyz[q>=q.max()-.05*np.ptp(q)].mean(axis=0);ax.quiver(*centre,*(axis*span*.27),color='#c42d26',linewidth=2,arrow_length_ratio=.3)
 mid=(xyz.max(axis=0)+xyz.min(axis=0))/2;radius=span*.63
 ax.set_xlim(mid[0]-radius,mid[0]+radius);ax.set_ylim(mid[1]-radius,mid[1]+radius);ax.set_zlim(mid[2]-radius,mid[2]+radius);ax.set_box_aspect((1,1,1));ax.view_init(elev=24,azim=-58);ax.set_axis_off()
 if values is not None:
  cap=np.linalg.norm(d['displacement'],axis=1).max() if mode=='displacement' else np.percentile(d['vm_MPa'],95)
  scale=1e6 if mode=='displacement' else 1
  pos=ax.get_position();cax=ax.figure.add_axes([pos.x0+.035,pos.y0-.013,pos.width-.07,.010])
  sm=plt.cm.ScalarMappable(norm=Normalize(0,cap*scale),cmap='viridis' if mode=='displacement' else 'turbo');bar=ax.figure.colorbar(sm,cax=cax,orientation='horizontal');bar.ax.tick_params(labelsize=7,pad=2);bar.ax.xaxis.get_offset_text().set_visible(False)
  ticks=np.linspace(0,cap*scale,3 if mode=='stress' and cap < .001 else 4);bar.set_ticks(ticks);bar.set_ticklabels([f'{v:.2f}' if mode=='displacement' else (f'{v:.1e}' if cap < .001 else f'{v:.4f}') for v in ticks])
  ax.figure.text(pos.x0+pos.width/2,pos.y0-.045,r'|q| [$10^{-6}$ mm]' if mode=='displacement' else 'von Mises [MPa]; clipped p95',ha='center',fontsize=8)

def save(fig,name):
 for ext in ['pdf','svg','png']:fig.savefig(FIG/f'{name}.{ext}',dpi=260)
 plt.close(fig)

f=plt.figure(figsize=(7.2,8.2));f.suptitle('FEM: from an edited CAD solid to a checked response',fontsize=14,y=.984,fontweight='bold',color=INK)
a=f.add_axes([.035,.83,.93,.12]);a.set_xlim(0,100);a.set_ylim(0,30);a.axis('off')
box(a,1,7,29,21,'1. Define the scenario','Solid + material\nFixed band + loaded band')
box(a,36,7,28,21,'2. Assemble and solve',r'$Kq=f$'+'\nLinear tetrahedral elasticity',GREEN)
box(a,70,7,29,21,'3. Check the solution','Forces, energy, mesh change\nCompare edited vs. target',GREEN)
arrow(a,30,17,36,17);arrow(a,64,17,70,17)
f.text(.5,.802,'Blue: fixed nodes     Red arrow: resultant load direction     All surfaces are undeformed.',ha='center',fontsize=9,color=INK)
cases=[('mounting_angle_box_x_f130','Mounting-angle width edit'),('t5hard_round_flange_V_a','Flange: 4-to-6 mounting-hole edit')]
for row,(rid,label) in enumerate(cases):
 r=ROOT/'runs/multisource-cad-colab-20261002/results-final/fem-examples'/rid/'verification';v=read(r/'verification.json');levels=sorted(r.glob('prediction-mesh-*/solution.npz'));p=levels[-1];files.append(p);d=np.load(p);m=read(p.parent/'metrics.json');axis=np.array(m['axis']);top=.768-row*.325
 f.text(.045,top,label+' | actual final 3B prediction',fontsize=11,fontweight='bold',color=INK)
 for col,mode in enumerate(['mesh','displacement','stress']):
  ax=f.add_axes([.012+col*.327,top-.260,.30,.204],projection='3d');draw(ax,d,mode,axis);ax.set_title(['Tetrahedral surface mesh','Displacement magnitude','Diagnostic stress field'][col],fontsize=9,pad=0)
 f.text(.05,top-.026,f"{m['nodes']:,} nodes; {m['tetrahedra']:,} tets   |   C = {m['compliance_N_mm']:.3e} N mm   |   max |q| = {m['max_displacement_mm']:.3e} mm",fontsize=9,color=INK)
f.text(.05,.110,'Worked-example interpretation',fontsize=11,fontweight='bold',color=INK)
f.text(.05,.072,'The same solid supplies the mesh and both field plots. A color change is a solver response,\nnot proof that the edit is correct: independent solid and target-response checks are still required.',fontsize=9,linespacing=1.5,color=INK)
f.text(.05,.025,'Assumed E = 210,000 MPa, nu = 0.3; static 1 N test. Stress convergence / operating safety\nare not established. Surface edges display the tetrahedral boundary, not every interior element.',fontsize=8.5,color=INK)
save(f,'fem-method-worked-examples-large')

(OUT/'provenance.json').write_text(json.dumps({'figure_data':'saved actual solver fields; no new training or FEM run','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
print('Exported the large FEM worked-example figure (PDF/SVG/PNG).')
