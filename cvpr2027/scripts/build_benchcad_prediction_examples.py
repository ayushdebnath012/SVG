"""Export actual held-out H100 predictions alongside sources and released STEP targets."""
import json,textwrap
from pathlib import Path
import xml.etree.ElementTree as ET
import cadquery as cq
from verify_mechanical_cad_edits import execute,white_background
ROOT=Path(__file__).resolve().parents[1];N='{http://www.w3.org/2000/svg}';ET.register_namespace('',N[1:-1])
data=ROOT/'data/benchcad-online-edit-v1';run=ROOT/'runs/benchcad-online-h100-20261002'
rows={r['source_record_id']:r for r in map(json.loads,(data/'test.jsonl').read_text().splitlines())}
pred={r['id']:r for r in map(json.loads,(run/'trained-predictions.jsonl').read_text().splitlines())}
geom={r['id']:r for r in map(json.loads,(run/'trained-predictions-geometry.jsonl').read_text().splitlines())}
groups=[['mounting_angle_box_x_f130','locator_block_box_y_f130','t3medplus_stepped_shaft_rot_diag60'],['propeller_bore_widen_compute','t5hard_pan_head_screw_U_a','t5hard_round_flange_V_a']]
art=ROOT/'runs/benchcad-prediction-figures-20261002';art.mkdir(exist_ok=True);manifest=[]
for page,ids in enumerate(groups,1):
 root=ET.Element(N+'svg',width='1200',height='1000',viewBox='0 0 1200 1000');ET.SubElement(root,N+'rect',width='1200',height='1000',fill='white')
 def text(x,y,s,size=18):
  e=ET.SubElement(root,N+'text',x=str(x),y=str(y),fill='#173044',**{'font-family':'Arial','font-size':str(size)});e.text=s
 text(20,28,'Held-out H100 CAD edits: '+('strict matches' if page==1 else 'partial / failed edits'),25)
 for i,rid in enumerate(ids):
  r=rows[rid];p=pred[r['id']];g=geom[r['id']];y=60+i*300
  text(20,y,rid.replace('_',' ')+' | '+r['category']+' | IoU '+f"{g['volume_iou']:.5f}",20)
  for j,line in enumerate(textwrap.wrap(r['instruction'],width=112)):text(20,y+26+j*21,line,17)
  solids=[execute(r['code']),cq.importers.importStep(str(data/r['reference_step'])).val(),execute(p['predicted_code'])]
  for col,(label,solid) in enumerate(zip(['SOURCE','RELEASED TARGET','H100 PREDICTION'],solids)):
   text(20+col*400,y+83,label,17);path=art/(rid+'-'+str(col)+'.svg')
   cq.exporters.export(solid,str(path),opt={'projectionDir':(1,-1,1),'showHidden':False,'width':380,'height':185,'marginLeft':12,'marginTop':12});white_background(path)
   svg=ET.fromstring(path.read_text());svg.attrib.update(x=str(10+col*400),y=str(y+94),width='380',height='185',viewBox='0 0 380 185');root.append(svg)
  manifest.append(dict(id=r['id'],source_record_id=rid,instruction=r['instruction'],volume_iou=g['volume_iou'],target_ast=p['ast_match'],reference_step_sha256=r['reference_step_sha256'],prediction_role='actual_final_h100_adapter_output'))
 text(20,983,'Views fit independently; use measured IoU, not apparent drawing size. BenchCAD CC-BY-4.0. FEM audit reported separately.',16)
 ET.ElementTree(root).write(ROOT/f'paper/network/figures/benchcad-model-examples-{page}.svg',encoding='unicode')
(art/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
