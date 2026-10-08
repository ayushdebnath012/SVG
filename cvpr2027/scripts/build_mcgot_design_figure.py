"""Illustrate a proposed MCTS space over CAD edit thoughts, not results."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OUT=Path(__file__).resolve().parents[1]/'paper/network/figures'
RESULT=OUT.parents[2]/'experiments/mcts-astra-20261007-final/comparison.json'
completed=RESULT.exists()
result=json.loads(RESULT.read_text()) if completed else None
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'pdf.fonttype':42,'svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(11,5.6))
fig.subplots_adjust(left=.015,right=.985,top=.985,bottom=.015)
ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
INK='#203047';BLUE='#2563eb';AMBER='#d97706';PURPLE='#7c3aed';TEAL='#0d9488';GREEN='#059669'

def text(x,y,s,size=10,bold=False,color=INK):
    ax.text(x,y,s,ha='center',va='center',fontsize=size,weight='bold' if bold else 'normal',color=color,linespacing=1.3)

def box(x,y,w,h,title,accent,pale,detail='',dashed=False):
    ax.add_patch(FancyBboxPatch((x+.25,y-.4),w,h,boxstyle='round,pad=.2,rounding_size=1.4',facecolor='#e8edf4',edgecolor='none'))
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.2,rounding_size=1.4',facecolor=pale,edgecolor=accent,lw=1,linestyle='--' if dashed else '-'))
    text(x+w/2,y+h*.68 if detail else y+h/2,title,10,True,accent)
    if detail:text(x+w/2,y+h*.29,detail,8.5)

def arrow(x,y,u,v,color='#94a3b8',dashed=False,rad=0,lw=1.3):
    ax.add_patch(FancyArrowPatch((x,y),(u,v),arrowstyle='-|>',mutation_scale=13,color=color,lw=lw,linestyle='--' if dashed else '-',connectionstyle=f'arc3,rad={rad}'))

text(38,96,'Monte Carlo Tree Search over CAD edit thoughts',17,True)
box(77,91,22,8,'COMPLETED PILOT' if completed else 'PROPOSED / NOT RUN',GREEN if completed else AMBER,'#ecfdf5' if completed else '#fff7ed')
ax.add_patch(FancyBboxPatch((1,29),69,59,boxstyle='round,pad=.3,rounding_size=1.7',facecolor='#f8fafc',edgecolor='#dbe3ee'))
text(35.5,84,'CAD states and edit branches: width 2, maximum depth 2',10,True)
# Explicit tree: each child has one parent; observation caching is separate.
edges=[(14,58,22,69),(14,58,22,45),
       (35,69,43,76),(35,69,43,65),(35,45,43,51),(35,45,43,40),
       (56,76,60,62)]
for coords in edges:arrow(*coords)
for coords in [(14,58,22,69),(35,69,43,76),(56,76,60,62)]:arrow(*coords,color=TEAL,lw=2.4)
box(3,51,11,14,'Root CAD',BLUE,'#eff6ff','Source + request\nInitial Astra patch')
box(22,64,13,10,'Edit A',AMBER,'#fff7ed','Hypothesis 1')
box(22,40,13,10,'Edit B',AMBER,'#fff7ed','Hypothesis 2')
for y,label in [(73,'CAD A1'),(62,'CAD A2'),(48,'CAD B1'),(37,'CAD B2')]:
    box(43,y,13,6,label,PURPLE,'#f5f3ff')
box(60,49,8,14,'Rollout',TEAL,'#f0fdfa','Checks')
text(26,31,'Backup on selected path',8,color=TEAL)
for coords in [(61,64,56,79),(42,79,35,74),(21,76,13,66)]:arrow(*coords,color=TEAL,dashed=True)
box(74,65,25,22,'Target-free verification',PURPLE,'#f5f3ff','Execute / numeric checks\nInstruction consistency\nFrozen GRPO verifier')
if completed and result['replacements']==0:
    box(74,40,25,21,'Gate blocked every candidate',AMBER,'#fff7ed','Max calibrated p: 0.8997 < 0.9016\nAll initial answers retained')
else:
    box(74,40,25,21,'Final selection',GREEN,'#ecfdf5','Choose highest-scored eligible CAD\nNo eligible result: retain original')
arrow(70,64,73.5,75,color=PURPLE)
arrow(86.5,65,86.5,61,color=GREEN)
text(86.5,33,'A proxy score is not proof\nof reference agreement',8.5,color='#64748b')

# Search-control cycle. Every step consumes the fixed experiment budget.
cycle=[(1,21,'1  SELECT',BLUE,'#eff6ff','Value + exploration'),
       (27,22,'2  EXPAND',AMBER,'#fff7ed','Sample Astra patches'),
       (54,21,'3  ROLLOUT',PURPLE,'#f5f3ff','Execute + proxy score'),
       (80,19,'4  BACK UP',TEAL,'#f0fdfa','Update path Q and N')]
for x,w,title,color,pale,detail in cycle:box(x,8,w,16,title,color,pale,detail)
for x,u in [(22,27),(49,54),(75,80)]:arrow(x,16,u,16)
arrow(90,7,11,7,color=TEAL,dashed=True,rad=-.035)
text(50,2,'Repeat until fixed API / token / tool / depth budget is exhausted; reference geometry is used only for final offline scoring.',8.5)
for ext in ('pdf','svg','png'):fig.savefig(OUT/f'monte-carlo-graph-of-thoughts.{ext}',dpi=240)
plt.close(fig)
