"""Post-hoc multi-view audit of the fixed six previously illustrated CAD edit cases."""
from pathlib import Path
import json,hashlib
import numpy as np
import cadquery as cq
from PIL import Image,ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'runs/cad-multiview-audit-20261003';OUT.mkdir(parents=True,exist_ok=True)
OLD=ROOT/'runs/mechanical-cad-fem-20261002';NEW=ROOT/'runs/multisource-cad-colab-20261002/results-final/fem-examples'
ids=['mounting_angle_box_x_f130','locator_block_box_y_f130','t3medplus_stepped_shaft_rot_diag60','propeller_bore_widen_compute','t5hard_pan_head_screw_U_a','t5hard_round_flange_V_a']
u=np.array([1,1,0])/np.sqrt(2);n=np.array([1,-1,1])/np.sqrt(3);w=np.cross(n,u)
views={'front':np.array([[1,0,0],[0,0,1]]),'top':np.array([[1,0,0],[0,1,0]]),'right':np.array([[0,1,0],[0,0,1]]),'isometric':np.array([u,w])}
records=[];saved={};provenance={};availability=[]
def tess(p):
 v,f=cq.importers.importStep(str(p)).val().tessellate(.3);provenance[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return np.array([x.toTuple() for x in v]),np.array(f)
def mask(pts,faces,basis,bounds,size):
 xy=pts@basis.T;lo,hi=bounds;scale=(size-20)/max(hi-lo);xy=(xy-(lo+hi)/2)*scale+(size-1)/2;xy[:,1]=(size-1)-xy[:,1];im=Image.new('1',(size,size));draw=ImageDraw.Draw(im)
 for triangle in xy[faces]:draw.polygon([tuple(p) for p in triangle],fill=1)
 return np.array(im,bool)
def iou(a,b):
 union=(a|b).sum();return float((a&b).sum()/union) if union else None
for rid in ids:
 solids={'source':tess(OLD/rid/'source.step'),'target':tess(OLD/rid/'target.step'),'H100':tess(OLD/rid/'prediction.step')}
 p=NEW/rid/'verification/prediction.step';verification=NEW/rid/'verification/verification.json'
 # Only completed outputs enter this visual audit; failed pipeline attempts remain unscored.
 eligible=p.exists() and verification.exists() and json.loads(verification.read_text()).get('status')=='completed'
 availability.append({'case':rid,'H100':'saved_solid_available','Colab3B':'completed_output_available' if eligible else 'unavailable_no_completed_verification'})
 if eligible:solids['Colab3B']=tess(p)
 allpts=np.concatenate([d[0] for d in solids.values()]);bounds={k:((allpts@b.T).min(0),(allpts@b.T).max(0)) for k,b in views.items()}
 for size in [512,1024]:
  masks={name:{view:mask(pts,faces,b,bounds[view],size) for view,b in views.items()} for name,(pts,faces) in solids.items()}
  for model in ['H100','Colab3B']:
   if model not in solids:continue
   results=[]
   for view in views:
    src=masks['source'][view];target=masks['target'][view];pred=masks[model][view];expected=src^target;actual=src^pred
    results.append({'view':view,'silhouette_iou':iou(pred,target),'edit_mask_iou':iou(expected,actual),'reference_change_pixels':int(expected.sum())})
   records.append({'case':rid,'model':model,'resolution':size,'views':results,'mean_silhouette_iou':float(np.mean([x['silhouette_iou'] for x in results])),'mean_visible_edit_iou':float(np.mean([x['edit_mask_iou'] for x in results if x['edit_mask_iou'] is not None]))})
  if size==512:saved[rid]=masks
summary={}
for model in ['H100','Colab3B']:
 rs=[x for x in records if x['model']==model and x['resolution']==512];fine={x['case']:x for x in records if x['model']==model and x['resolution']==1024}
 summary[model]={'n_available':len(rs),'n_fixed_cases':6,'mean_silhouette_iou':float(np.mean([x['mean_silhouette_iou'] for x in rs])),'mean_visible_edit_iou':float(np.mean([x['mean_visible_edit_iou'] for x in rs])),'mean_abs_edit_iou_resolution_change':float(np.mean([abs(x['mean_visible_edit_iou']-fine[x['case']]['mean_visible_edit_iou']) for x in rs]))}
report={'scope':'Fixed previously illustrated six held-out cases, selected before this visual audit; diagnostic subset, not full benchmark accuracy or fair cross-model comparison','contract':{'views':list(views),'resolutions':[512,1024],'tessellation_tolerance_mm':.3,'camera':'Per-case shared source/target/all-available-prediction bounds; common orthographic bases and equal scaling; no per-shape recentering','metric':'Silhouette IoU and XOR source-to-target versus source-to-prediction change-mask IoU; unchanged-view unions are undefined and excluded from visible-edit mean','limitations':'Occluded/internal edits may be invisible; triangulation/raster effects; no instruction compliance or feature-tolerance certificate'},'summary':summary,'availability':availability,'records':records,'step_hashes':provenance}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
# A feature-change figure: exactly the same flange request for both actual adapters.
m=saved['t5hard_round_flange_V_a'];view='top';source=m['source'][view];target=m['target'][view]
fig,axs=plt.subplots(1,4,figsize=(9,3.15));titles=['Source: 4 holes','Released target: 6 holes','H100 prediction','Colab 3B prediction']
for ax,name,title in zip(axs,['source','target','H100','Colab3B'],titles):
 mask_=m[name][view];rgb=np.ones((*mask_.shape,3));rgb[mask_]=[.63,.51,.76]
 if name in ['H100','Colab3B']:
  rgb[target&~mask_]=[.93,.29,.35];rgb[mask_&~target]=[1,.65,.18]
 ax.imshow(rgb);ax.set_title(title,fontsize=11);ax.axis('off')
 if name in ['H100','Colab3B']:
  rec=next(x for x in records if x['case']=='t5hard_round_flange_V_a' and x['model']==name and x['resolution']==512);vr=next(v for v in rec['views'] if v['view']=='top');fig.text(.625 if name=='H100' else .875,.125,f"Top silhouette IoU: {vr['silhouette_iou']:.3f}\nVisible edit IoU: {vr['edit_mask_iou']:.3f}",ha='center',fontsize=9)
fig.text(.5,.018,'Common top-view camera. Red: target-only silhouette; orange: prediction-only silhouette. Actual saved solids.',ha='center',fontsize=9);fig.subplots_adjust(top=.85,bottom=.28,left=.01,right=.99,wspace=.04)
for ext in ['pdf','svg','png']:fig.savefig(ROOT/'paper/network/figures'/f'cad-edit-localization.{ext}',dpi=220)
plt.close(fig)
print(json.dumps(summary,indent=2))
