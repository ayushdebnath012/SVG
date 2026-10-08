"""Figure-2-style GRPO architecture with geometry from a saved recovered case.

The rotational surfaces are rendered directly from the exact saved polyline
profiles (not generated images). Reference scores are offline annotations only.
"""
from pathlib import Path
import ast
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'paper/network/figures'
EXP = ROOT / 'experiments/agentic-verifier-grpo-20261006'
CASE = '1bb334960dd158817d9ab53b44a9ebe04a8719e547ebe807e0884c8a38718119'

def record(path):
    return next(json.loads(line) for line in path.open() if json.loads(line)['id'] == CASE)

held = record(EXP / 'heldout.jsonl')
before = record(ROOT / 'runs/multisource-cad-astra-20261004/scored/astra-predictions.jsonl')
after = record(EXP / 'selected-repairs.jsonl')
comparison = json.loads((EXP / 'comparison.json').read_text())
assert not record(EXP / 'grpo-heldout-decisions.jsonl')['accepted']
assert record(EXP / 'grpo-repair-decisions.jsonl')['accepted']

def profile(code):
    node = next(n for n in ast.walk(ast.parse(code))
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == 'polyline')
    return np.array(ast.literal_eval(node.args[0]), dtype=float)

profiles = [profile(held['code']), profile(before['predicted_code']), profile(after['predicted_code'])]
purple, ink = '#7c3aed', '#203047'
lavender, yellow, green = '#f5f3ff', '#fff4d6', '#e8f7ef'
STAGES = [('#2563eb','#eff6ff'), ('#d97706','#fff7ed'),
          ('#7c3aed','#f5f3ff'), ('#0d9488','#f0fdfa'), ('#059669','#ecfdf5')]

def stage(x):
    return STAGES[next((i for i,b in enumerate([20,41,64,84]) if x<b),4)]

def tint(color,amount):
    rgb=np.array(matplotlib.colors.to_rgb(color))
    return tuple((1-amount)*rgb+amount)
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':12,
                     'pdf.fonttype':42, 'svg.fonttype':'none'})
fig = plt.figure(figsize=(11, 6.8))
ax = fig.add_axes([.015,.015,.97,.97]); ax.set(xlim=(0,100),ylim=(0,100)); ax.axis('off')

def box(x,y,w,h,color=None,dashed=False):
    accent,pale=stage(x+w/2)
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.2,rounding_size=1.3',
        edgecolor=tint(accent,.45),facecolor=color or pale,lw=.9,linestyle='--' if dashed else '-'))

def panel(x,y,w,h):
    accent,pale=stage(x+w/2)
    ax.add_patch(FancyBboxPatch((x+.3,y-.6),w,h,boxstyle='round,pad=.2,rounding_size=1.3',
                              facecolor='#e6ebf2',edgecolor='none',zorder=-2))
    box(x,y,w,h,pale)
    ax.add_patch(FancyBboxPatch((x,y+h-8),w,8,boxstyle='round,pad=.2,rounding_size=1.3',
                              facecolor=accent,edgecolor='none'))
    ax.add_patch(Rectangle((x-.2,y+h-8),w+.4,3,facecolor=accent,edgecolor='none'))

def text(x,y,s,size=11,bold=False,color=ink):
    if color==purple:color=stage(x)[0]
    ax.text(x,y,s,ha='center',va='center',fontsize=size,color=color,
            weight='bold' if bold else 'normal',linespacing=1.2)

def arrow(x0,y0,x1,y1,dashed=False):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=14,
        lw=1.3,color='#64748b',linestyle='--' if dashed else '-'))

def transformer(cx,y,label):
    accent,_=stage(cx)
    for dy,amount in [(0,.84),(2,.76),(4,.67)]:box(cx-5.7,y+dy,11.4,6,tint(accent,amount))
    text(cx,y+5,label,9,True,purple)

def solid(bounds,p,color):
    # Exact surface of revolution from the CAD program, rigidly oriented upright.
    theta=np.linspace(0,2*np.pi,73)
    quads=[]
    for v,w in zip(p,np.roll(p,-1,axis=0)):
        for t,u in zip(theta[:-1],theta[1:]):
            quads.append([[v[0]*np.cos(t),v[0]*np.sin(t),v[1]],
                          [v[0]*np.cos(u),v[0]*np.sin(u),v[1]],
                          [w[0]*np.cos(u),w[0]*np.sin(u),w[1]],
                          [w[0]*np.cos(t),w[0]*np.sin(t),w[1]]])
    q=np.asarray(quads)
    normals=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
    lighting=.7+.3*np.sum(normals*np.array([.4,-.5,.768]),axis=1)
    colors=lighting[:,None]*np.array(matplotlib.colors.to_rgb(color))
    a=fig.add_axes(bounds,projection='3d')
    a.add_collection3d(Poly3DCollection(quads,facecolors=colors,edgecolors=colors,linewidths=0))
    a.set(xlim=(-130,130),ylim=(-130,130),zlim=(0,975))
    a.set_box_aspect((260,260,975));a.view_init(18,-58);a.set_axis_off();a.set_facecolor('none')

def section(bounds,p,color):
    a=fig.add_axes(bounds)
    a.fill(p[:,0],p[:,1],facecolor=tint(color,.6),edgecolor=color,lw=1.3)
    a.set(xlim=(20,105),ylim=(345,470));a.set_aspect('equal');a.axis('off')
    

for x,w in [(1,16),(21,17),(42,20),(66,17),(87,12)]:panel(x,34,w,63)
for x,t in [(9,'CAD input'),(29.5,'Frozen Astra'),(52,'Trained verifier'),(74.5,'One repair'),(93,'Decision')]:
    text(x,93,t,13 if x!=93 else 11,True,'#ffffff')
solid([.033,.65,.125,.21],profiles[0],'#5996e8')
text(9,64,'Saved source solid',9,True,purple)
box(2.3,43,13.4,17,'#fff');text(9,56,'Instruction',10,True,purple)
text(9,49,'Throat radius\n58.7 -> 40.0 mm',9)
text(9,38,'Code + request',9)

transformer(29.5,78,'Astra')
text(29.5,73,'Generate line patch',9)
solid([.228,.44,.14,.21],profiles[1],'#f49a52')
text(29.5,41,'Initial candidate',9,True,purple)
text(29.5,36.8,'Offline IoU: 0.7936',8.5)

box(43.5,80,17,8,'#fff');text(52,84,'Source + request\n+ candidate',9)
transformer(52,64,'Qwen 1.5B')
box(46,56,12,7,yellow);text(52,59.5,'LoRA rank 8',9,True,purple)
arrow(52,80,52,75);arrow(52,64,52,63)
box(43.5,43,17,10,'#fff')
# Small execution glyph: an executed code sheet, rather than a geometry oracle.
text(46.2,48,'>_',13,True,purple);text(54,48,'Execute CAD\nValid solid',8.5)
arrow(52,56,52,53)
text(52,38,'Learned verdict: REJECT',9,True,color='#a3442c')

transformer(74.5,78,'Same Astra')
text(74.5,73,'Answer + rejection\n+ execution feedback',8.5)
box(67.5,62,14,7,'#fff');text(74.5,65.5,'JSON line patch\nOne bounded retry',9)
solid([.667,.39,.14,.21],profiles[2],'#43b9ac')
text(74.5,36.8,'Repaired candidate',9,True,purple)

ax.add_patch(Circle((93,83),3.5,edgecolor='#27826b',facecolor=green,lw=1.2))
ax.plot([91.3,92.6,95.1],[83,81.5,84.8],color='#27826b',lw=2)
text(93,75,'Same verifier\nACCEPT',9,True,color='#27826b')
box(88,56,10,12,green);text(93,62,'Use repair\nIoU = 1.0*',8.5,True)
box(88,40,10,12,yellow);text(93,46,'If rejected:\nkeep original',8)
for x0,x1 in [(17,21),(38,42),(62,66),(83,87)]:arrow(x0,68,x1,68)

# Actual cross-sections make the otherwise small wall change visible.
box(1,16,39,14,'#fff')
text(20.5,27.8,'Throat sections: inner radius = 40 mm',10,True,purple)
section([.05,.20,.115,.065],profiles[1],'#d97706');text(11,18,'Initial: outer 63.2 mm',8)
section([.225,.20,.115,.065],profiles[2],'#0d9488');text(29,18,'Repair: outer 81.9 mm',8)

box(44,16,55,14,'#fff')
text(71.5,26.8,'Completed verifier GRPO (training only)',11,True,purple)
text(71.5,21.5,'Saved Astra answers -> 8 action trajectories -> verdict reward -> LoRA',9)
text(71.5,17.7,'Reference geometry supplies training labels, never inference observations',8)

box(1,1,70,11,'#f3f3f3',True)
text(36,8.5,'Student-editor pipeline: SFT complete; GRPO not yet completed',10,True,color='#68717a')
text(36,3.5,'Astra examples -> SFT Qwen -> generated CAD -> geometry reward -> editor GRPO',9)
box(75,1,24,11,green)
c=comparison['all_tasks']
text(87,8.5,f"All tasks: {c['before']}/{c['n']} -> {c['after']}/{c['n']}",10,True,purple)
text(87,3.5,'2 recovered / 0 regressed',9)

for ext in ('pdf','svg','png'):fig.savefig(FIG/f'grpo-verifier-pipeline.{ext}',dpi=240)
plt.close(fig)
provenance={'case_id':CASE,'geometry':'Exact saved polyline surfaces of revolution, common camera; throat sections cropped at identical bounds',
    'source_code_sha256':hashlib.sha256(held['code'].encode()).hexdigest(),
    'initial_code_sha256':hashlib.sha256(before['predicted_code'].encode()).hexdigest(),
    'repair_code_sha256':hashlib.sha256(after['predicted_code'].encode()).hexdigest(),
    'note':'IoUs are offline reference scores; neither score nor reference geometry enters inference. Model internals are schematic.'}
(FIG/'grpo-verifier-pipeline-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')

# A visual explanation of group-relative learning. These paths are pedagogical
# examples, not a claim about logged trajectories or use of the held-out case.
fig=plt.figure(figsize=(11,4.25))
ax=fig.add_axes([.015,.015,.97,.97]);ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
for x,w in [(1,16),(21,18),(43,18),(65,16),(85,14)]:panel(x,24,w,72)
for x,t in [(9,'Training data'),(30,'8 trajectories'),(52,'Reward'),(73,'Advantages'),(92,'Update')]:
    text(x,92,t,12,True,'#ffffff')
# Stacked code sheets and an instruction strip make the observation contract visible.
for dx,dy in [(2,2),(1,1),(0,0)]:box(3+dx,57+dy,10,23,'#fff')
for y,w in [(75,6),(71,4),(67,7),(63,5)]:ax.plot([5,5+w],[y,y],color=purple,lw=1.3)
text(9,50,'Source + instruction\n+ saved candidate',9)
box(2.3,30,13.4,13,yellow);text(9,36.5,'726 train\n238 dev',10,True,purple)
# Eight paths, each with a required tool before a terminal verdict.
paths=['E -> R','E -> R','E -> A','E -> N -> R','E -> R','E -> N -> A','E -> N -> R','E -> R']
for i,path in enumerate(paths):
    y=78-i*5.2
    box(23,y-2,14,4,'#fff2ed' if path.endswith('A') else '#edf9f3')
    text(30,y,path,8.5,color='#c04d36' if path.endswith('A') else '#087a60')
text(30,29,'E: execute | N: numbers\nA: accept | R: reject',7.5)
rewards=np.array([.98,.98,-2.02,.96,.98,-2.04,.96,.98])
advantages=(rewards-rewards.mean())/max(rewards.std(),.25)
def bars(bounds,values):
    a=fig.add_axes(bounds)
    a.set_facecolor('none')
    a.barh(np.arange(8),values,color=['#16a085' if v>0 else '#e16b50' for v in values],height=.65)
    a.axvline(0,color=ink,lw=.7);a.invert_yaxis()
    a.set(yticks=[],xticks=[-2,0,1],xlim=(-2.5,1.5))
    a.spines[['top','right','left']].set_visible(False);a.tick_params(labelsize=8)
bars([.445,.40,.13,.405],rewards)
bars([.67,.40,.12,.405],advantages)
text(52,30,'Verdict score\nminus tool cost',9)
text(73,33,'(reward - mean) / std',8.5)
text(73,28,'Within the same group',8)
transformer(92,64,'Qwen')
box(87,46,10,12,yellow);text(92,52,'LoRA\nrank 8',9,True,purple)
arrow(92,64,92,58)
text(92,34,'Clipped update\n+ KL penalty',9)
for x0,x1 in [(17,21),(39,43),(61,65),(81,85)]:arrow(x0,60,x1,60)
box(1,1,98,18,'#fff')
text(50,13.5,'Illustrative group, not a logged rollout: candidate is incorrect',11,True,purple)
text(50,7.5,'Correct verdict +1 | false accept -2 | false reject -1 | each tool -0.02',10)
text(50,3,'Reference-derived labels score rewards only. No held-out task is used for training.',8.5)
for ext in ('pdf','svg','png'):fig.savefig(FIG/f'grpo-verifier-learning.{ext}',dpi=240)
plt.close(fig)
