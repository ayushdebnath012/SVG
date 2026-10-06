"""Illustrated CAD-edit/FEM architecture using actual saved solids and solver fields."""
from pathlib import Path
import json,hashlib
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import Normalize
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'paper/network/figures'
r=ROOT/'runs/multisource-cad-colab-20261002/results-final/fem-examples/t5hard_round_flange_V_a'
source=ROOT/'runs/mechanical-cad-fem-20261002/t5hard_round_flange_V_a/source.step'
sol=r/'verification/prediction-mesh-1/solution.npz';d=np.load(sol);m=json.loads((sol.parent/'metrics.json').read_text());v=json.loads((r/'verification/verification.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'pdf.fonttype':42,'svg.fonttype':'none'})
purple='#7b2894';lavender='#f5eef9';yellow='#fff2d5';green='#e8f4e9';ink='#242331'
f=plt.figure(figsize=(11,6.2));a=f.add_axes([.015,.015,.97,.97]);a.set_xlim(0,100);a.set_ylim(0,100);a.axis('off')
def box(x,y,w,h,color=lavender,lw=1.3):a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.25,rounding_size=1.7',facecolor=color,edgecolor=purple,lw=lw))
def text(x,y,s,size=13,bold=False,color=ink):a.text(x,y,s,ha='center',va='center',fontsize=size,fontweight='bold' if bold else 'normal',color=color,linespacing=1.25)
def arrow(x0,y0,x1,y1,style='-'):a.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=15,lw=1.4,color=ink,linestyle=style))
for x,w in [(1,15),(20,19),(43,16),(63,18),(85,14)]:box(x,21,w,75)
text(8.5,91,'CAD input',16,True,purple);text(29.5,91,'Trained editor',16,True,purple);text(51,91,'Apply edit',16,True,purple);text(72,91,'FEM check',16,True,purple);text(92,91,'Verification',14,True,purple)
# Actual tessellated solid views. No learned or invented geometry is shown.
def geometry(bounds,points,faces,colors,wire=False,fixtures=False):
 ax=f.add_axes(bounds,projection='3d');ax.add_collection3d(Poly3DCollection(points[faces],facecolors=colors,edgecolors='#816692' if wire else (colors if not fixtures else 'none'),linewidths=.18 if wire else 0,shade=(not fixtures and not wire)));mid=(points.max(0)+points.min(0))/2;rad=np.ptp(points,axis=0).max()*.52
 for setter,c in zip([ax.set_xlim,ax.set_ylim,ax.set_zlim],mid):setter(c-rad,c+rad)
 ax.set_box_aspect((1,1,1));ax.view_init(48,-55);ax.set_axis_off();ax.set_facecolor('none')
 if fixtures:
  axis=np.array(m['axis']);q=points@axis;nodes=np.unique(faces);fixed=nodes[q[nodes]<=q.min()+.05*np.ptp(q)];ax.scatter(*points[fixed[::max(1,len(fixed)//65)]].T,s=5,color='#2255b5',depthshade=False);centre=points[q>=q.max()-.05*np.ptp(q)].mean(0);ax.quiver(*centre,*(axis*rad*.7),color='#bd2727',linewidth=2,arrow_length_ratio=.3)
 return ax
solid=cq.importers.importStep(str(source)).val();pts,tris=solid.tessellate(.3);xyz=np.array([p.toTuple() for p in pts]);tris=np.array(tris)
geometry([.025,.54,.145,.29],xyz,tris,'#ae7ccc',False);text(8.5,55,'4 mounting holes',10,True,purple)
box(2.5,31,12,18,'#ffffff');text(8.5,44,'Instruction',12,True,purple);text(8.5,37,'4 → 6 holes\nSame radius / Ø',10)
text(8.5,26,'Source program\nSolid illustrated',11)
# Model internals represented as modules, not an unimplemented algorithm.
box(21.5,72,16,10,'#fff');text(29.5,77,'Source + request\nTokenized context',10)
for y in [56,58,60]:box(23,y,13,8,'#e6d5f1',.8)
text(29.5,64,'Transformer',12,True,purple)
box(23,41,13,11,yellow);text(29.5,46.5,'QLoRA\nrank-16 adapter',11,True,purple)
arrow(29.5,72,29.5,68);arrow(29.5,55,29.5,52)
text(29.5,30,'Qwen2.5-Coder-3B\nNF4 backbone\nCompletion-only loss',11)
# Exact saved patch summarized rather than printing tiny program text.
patch=json.loads((r/'patch.json').read_text());box(44.5,65,13,18,'#fff');text(51,79,'JSON line patch',11,True,purple)
text(51,71,'polarArray(..., 6)\nOriginal line 10\nKeep radius 60.8',9)
box(44.5,53,13,8,yellow);text(51,57,'Validate / execute',9,True)
arrow(51,65,51,61)
t=d['tetrahedra'];faces=np.concatenate([t[:,[0,1,2]],t[:,[0,1,3]],t[:,[0,2,3]],t[:,[1,2,3]]]);owners=np.tile(np.arange(len(t)),4);surf,ix,count=np.unique(np.sort(faces,axis=1),axis=0,return_index=True,return_counts=True);owner=owners[ix[count==1]];surf=surf[count==1];xyz=d['points']
edited=cq.importers.importStep(str(r/'verification/prediction.step')).val();ep,ef=edited.tessellate(.3);geometry([.438,.25,.145,.255],np.array([p.toTuple() for p in ep]),np.array(ef),'#ae7ccc')
text(51,25,'6 mounting holes',11,True,purple)
geometry([.632,.60,.175,.245],xyz,surf,'#ece9f0',True,True)
text(72,60,'Mesh + fixtures + 1 N load',10)
cap=m['vm_p95_MPa'];geometry([.632,.31,.175,.245],xyz,surf,plt.cm.turbo(Normalize(0,cap)(d['vm_MPa'][owner])),False,True)
text(72,29,'Actual stress field',11)
cax=f.add_axes([.675,.235,.09,.01]);bar=f.colorbar(plt.cm.ScalarMappable(norm=Normalize(0,cap),cmap='turbo'),cax=cax,orientation='horizontal');bar.set_ticks([0,cap]);bar.set_ticklabels(['0',f'{cap:.4f}']);bar.ax.tick_params(labelsize=8,pad=1)
# Checks retain a failure branch, avoiding the impression of unconditional acceptance.
for y,title,detail in [(70,'Solid match','IoU ≥ 0.99999'),(51,'FEM checks','Forces + energy'),(32,'Response','Mesh + compliance')]:
 box(86.5,y,11,14,'#fff');text(92,y+10,title,11,True,purple);text(92,y+4,detail,9)
arrow(92,70,92,65);arrow(92,51,92,46)
for x0,x1 in [(16,20),(39,43),(59,63),(81,85)]:arrow(x0,57,x1,57)
# Bottom strip: evidence and pass/failure accounting, rather than fabricated feedback loops.
box(1,1,55,15,'#fff');text(28.5,11,'Example evidence: actual 4-to-6-hole flange edit',13,True,purple)
err=v['relative_target_compliance_error']*100
text(28.5,5,f"IoU ≈ 1.00000   |   compliance discrepancy = {err:.4f}%",11)
box(60,1,18,15,green);text(69,11,'Checks pass',12,True);text(69,5,'Record a diagnostic pass',9)
box(82,1,17,15,yellow);text(90.5,11,'Any failure',12,True);text(90.5,5,'Keep case unverified',10)
arrow(92,21,90.5,16,style='--');arrow(88,21,69,16);text(78,19,'all pass',8);text(96,18,'fail',8)
for ext in ['pdf','svg','png']:f.savefig(FIG/f'cad-fem-illustrated-architecture.{ext}',dpi=260)
plt.close(f)
out=ROOT/'runs/paper-mechanical-diagrams-20261003/illustrated-provenance.json';out.write_text(json.dumps({'example':'actual final 3B six-hole flange prediction','illustration':'actual source tessellation, predicted FEM mesh and stress; abstract model modules','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,sol,r/'patch.json',r/'verification/verification.json']}},indent=2)+'\n')
print('Illustrated CAD/FEM architecture exported.')
