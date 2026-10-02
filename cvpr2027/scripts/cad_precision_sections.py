"""Separately specified precision inspection templates; never rescore coarse tasks."""
import argparse,copy,hashlib,json,tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
import cad_torus_sections as t
import cad_hard_geometry as h
import cad_astra_benchmark as core
from render_svg_gallery import render
SIZE=4000;SCALE=32.;ORIGIN=2000.

def mask(task):
 result=np.zeros((SIZE,SIZE),dtype=bool);x=(np.arange(SIZE)+.5-ORIGIN)/SCALE
 for start in range(0,SIZE,100):
  y=(ORIGIN-np.arange(start,min(start+100,SIZE))-.5)/SCALE;xx,yy=np.meshgrid(x,y)
  result[start:start+len(y)]=t.field(task['spec'],xx,yy)>=0
 return result

def raster(svg):
 root=ET.fromstring(svg);root.set('viewBox','250 250 500 500');root.set('width',str(SIZE));root.set('height',str(SIZE))
 with tempfile.TemporaryDirectory(prefix='cad-precision-') as d:
  p=Path(d)/'shape.svg';png=Path(d)/'shape.png';p.write_text(ET.tostring(root,encoding='unicode'));render(p,png,SIZE)
  im=Image.open(png).convert('L');a=np.asarray(im)<128
 if a.shape!=(SIZE,SIZE):raise ValueError('renderer size mismatch')
 return a

def compare(actual,target):
 missing=target&~actual;extra=actual&~target
 tolerance=.05+1/SCALE  # Explicit one-pixel raster allowance, frozen before calls.
 interior=distance_transform_edt(target);residual=missing&(interior>SCALE*tolerance);maxmissing=float(np.max(interior[missing],initial=0));del interior
 exterior=distance_transform_edt(~target);residual|=extra&(exterior>SCALE*tolerance);maxextra=float(np.max(exterior[extra],initial=0));del exterior
 return dict(iou=float((target&actual).sum()/max(1,(target|actual).sum())),symmetric_difference_mm2=float((target^actual).sum()/SCALE**2),residual_mismatch_mm2=float(residual.sum()/SCALE**2),max_intrusion_mm=max(maxmissing,maxextra)/SCALE,physical_tolerance_mm=.05,raster_allowance_mm=1/SCALE)

def score(task,text):return h.score(task,text,reference=mask(task),render_fn=raster,compare_fn=compare)

def build(out):
 if (out/'tasks.json').exists():raise ValueError('Frozen pool exists')
 source=json.loads((core.ROOT/'data/cad-torus-sections/tasks.json').read_text());tasks=[]
 for old in source['tasks']:
  task=copy.deepcopy(old);task.update(id='precision_'+old['id'],kind='precision_torus',family='precision_toroidal_pipe_section',residual_area_tolerance_mm2=.05)
  task['prompt']='PRECISION INSPECTION TEMPLATE: this SVG will be used as a section-profile template. Maximum permitted contour deviation is 0.05 mm. A symbolic or coarse illustrative drawing is insufficient. Use sufficiently accurate native SVG curves or samples; no raster image or script.\n'+task['prompt']
  task['reference_mask_sha256']=hashlib.sha256(mask(task).tobytes()).hexdigest();tasks.append(task)
 source.update(version='cad-precision-torus-v1',system=h.SYSTEM.replace('accurate within 0.5 mm','accurate within 0.05 mm'),scope='Precision (0.05 mm) inspection template of a toroidal pipe section. Distinct requirement/interface from earlier 0.5 mm discovery tasks.',tasks=tasks,
   criteria=dict(boundary_tolerance_mm=.05,raster_allowance_mm=1/SCALE,residual_mismatch_area_mm2=.05,resolution_pixels_per_mm=SCALE,evaluation_window_mm=[-62.5,62.5,-62.5,62.5],selection='Three evaluable independent samples including two high-effort; at least two drawing failures including a high-effort failure; identified review. Operational/truncation/format excluded.'))
 out.mkdir(parents=True,exist_ok=True);core.write_json(out/'tasks.json',source)
 core.write_json(out/'selection_policy.json',dict(rule=source['criteria']['selection'],screen=dict(effort='medium',cap=16000,samples=1),confirmation=dict(effort='high',cap=32000,samples=2),adaptive_discovery='New explicit 0.05 mm precision inspection requirement; old 0.5 mm results remain passes, never retroactively reclassified.'))
 for task in tasks:(out/(task['id']+'.reference.svg')).write_text(t.oracle(task))
 print('Built',len(tasks))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=core.ROOT/'data/cad-precision-sections');build(p.parse_args().output)
