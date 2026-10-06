"""Reproducible vector diagrams and actual-solid drawing views for the paper."""
from pathlib import Path
import json, hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import cadquery as cq
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'paper/network/figures'
OUT=ROOT/'runs/paper-mechanical-diagrams-20261003'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none','pdf.fonttype':42})
BLUE='#e7f0f8'; GREEN='#e9f3ed'; AMBER='#fff2df'; INK='#193345'

def canvas(height):
 f,a=plt.subplots(figsize=(7.2,height));a.set_xlim(0,100);a.set_ylim(0,100);a.axis('off');f.subplots_adjust(left=.015,right=.985,bottom=.025,top=.98);return f,a

def box(a,x,y,w,h,title,detail='',color=BLUE,fs=9):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.35,rounding_size=1.4',edgecolor=INK,facecolor=color,lw=.85))
 a.text(x+w/2,y+h*.70 if detail else y+h/2,title,ha='center',va='center',fontsize=fs,fontweight='bold',color=INK)
 if detail:a.text(x+w/2,y+h*.31,detail,ha='center',va='center',fontsize=fs-1,color=INK,linespacing=1.35)

def arrow(a,start,end,style='-',color=INK):
 a.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=11,lw=1.1,color=color,linestyle=style))

def save(f,name):
 for ext in ['pdf','svg','png']:f.savefig(FIG/f'{name}.{ext}',dpi=220)
 plt.close(f)

f,a=canvas(3.65)
a.text(1,96,'(a) Edit generation and geometry evaluation',fontweight='bold',color=INK)
box(a,1,69,21,19,'CAD + instruction','Original native program\nMechanical edit request')
box(a,27,69,20,19,'Trained CAD editor','Qwen 3B + QLoRA\nJSON line patch')
box(a,52,69,21,19,'Validate + execute','Patch schema / syntax\nCAD / sequence execution')
box(a,78,69,21,19,'Compare solids','STEP / decoded reference\nVolume IoU + failures',GREEN)
for x,y in [(22,27),(47,52),(73,78)]:arrow(a,(x,78.5),(y,78.5))
a.text(52,61,'Invalid patch, execution or mesh failure: retain an unverified record.',fontsize=8,color='#975422',ha='center')
a.text(1,52,'(b) Optional physical audit with an explicit test contract',fontweight='bold',color=INK)
box(a,1,24,21,20,'Contract + solid','Units, material, fixtures\nExplicit test load')
box(a,27,24,20,20,'Independent FEM','Target and prediction\nMesh, forces and energy',GREEN)
box(a,52,24,21,20,'Response checks','Mesh / compliance change\nCompare target response',GREEN)
box(a,78,24,21,20,'Recorded outcome','Geometry + FEM checks\nRecord passes and failures',GREEN)
for x,y in [(22,27),(47,52),(73,78)]:arrow(a,(x,34),(y,34))
arrow(a,(62.5,69),(62.5,64));arrow(a,(88.5,69),(88.5,44),style='--')
a.text(50,12,'Physical checks apply to contracted examples; they are external to CAD token training.',ha='center',fontsize=8,color=INK)
a.text(50,4,'A numerical diagnostic pass is conditional on the disclosed scenario.',ha='center',fontsize=8,color=INK)
save(f,'mechanical-edit-verification-flow')

f,a=canvas(2.15)
a.text(1,93,'CAD patch model: multi-source supervised training',fontweight='bold',color=INK)
box(a,1,35,24,40,'Online CAD edit pairs','BenchCAD + CAD-Editor\nTrain 2,540; val 172; test 252')
box(a,31,35,30,40,'Qwen2.5-Coder-3B','NF4 backbone + rank-16 QLoRA\nCompletion-only token loss\nT4: 1,270 updates / 2 epochs')
box(a,68,35,31,40,'Native JSON line patch','Apply to source, execute, score\nHeld-out strict geometry: 39/252',GREEN)
arrow(a,(25,55),(31,55));arrow(a,(61,55),(68,55))
a.text(50,13,'FEM is an external post-edit check; its solver outputs do not supervise token training.',ha='center',fontsize=8,color=INK)
save(f,'mechanical-trained-models')

# Four orthographic/isometric projections of real source and final 3B predicted solids.
NS='{http://www.w3.org/2000/svg}';ET.register_namespace('',NS[1:-1])
root=ET.Element(NS+'svg',width='1200',height='930',viewBox='0 0 1200 930')
ET.SubElement(root,NS+'rect',width='1200',height='930',fill='white')
def text(x,y,s,size=20):
 ET.SubElement(root,NS+'text',x=str(x),y=str(y),fill=INK,**{'font-family':'Arial','font-size':str(size)}).text=s
text(18,28,'Actual CAD-derived drawings: source and final 3B edited prediction',24)
views=[('Front',(0,-1,0)),('Top',(0,0,1)),('Right',(1,0,0)),('Isometric',(1,-1,1))]
for i,(label,_) in enumerate(views):text(25+i*300,65,label,21)
cases=[('mounting_angle_box_x_f130','Mounting angle: requested base-width change'),('t5hard_round_flange_V_a','Flange: 4 to 6 mounting holes; same diameter and bolt-circle radius')]
manifest=[]
for ci,(rid,title) in enumerate(cases):
 source=ROOT/'runs/mechanical-cad-fem-20261002'/rid/'source.step'
 pred=ROOT/'runs/multisource-cad-colab-20261002/results-final/fem-examples'/rid/'verification/prediction.step'
 y0=85+ci*405;text(18,y0+20,title,22)
 for ri,(role,path) in enumerate([('SOURCE',source),('EDITED PREDICTION',pred)]):
  y=y0+38+ri*172;text(18,y+17,role,16);solid=cq.importers.importStep(str(path)).val()
  for vi,(view,direction) in enumerate(views):
   raw=OUT/f'{rid}-{role.replace(" ","-").lower()}-{view.lower()}.svg'
   cq.exporters.export(solid,str(raw),opt={'projectionDir':direction,'showHidden':False,'width':285,'height':142,'marginLeft':10,'marginTop':10})
   svg=ET.fromstring(raw.read_text());group=ET.SubElement(root,NS+'g',transform=f'translate({12+300*vi},{y+23})');group.extend(list(svg))
  manifest.append({'case':rid,'role':role,'step':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
text(18,915,'Projected views are autoscaled; dimensions and response must be read from CAD / solver artifacts.',17)
ET.ElementTree(root).write(FIG/'mechanical-linked-drawings.svg',encoding='unicode')
(OUT/'drawing-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Generated flowchart, architecture, and 16 actual CAD drawing views.')
