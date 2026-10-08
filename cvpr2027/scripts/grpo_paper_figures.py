"""Build vector explanations of the completed verifier and pending editor GRPO."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper/network/figures'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                     'pdf.fonttype': 42, 'ps.fonttype': 42})
BLUE, GREEN, GRAY = '#4c83e3', '#10a58c', '#64748b'

def box(ax, x, y, w, text, color=BLUE, pending=False):
    ax.add_patch(FancyBboxPatch((x, y), w, .64, boxstyle='round,pad=0.025',
                              linewidth=1, edgecolor=color,
                              facecolor='#f0f5f8' if not pending else '#f3f3f3',
                              linestyle='--' if pending else '-'))
    ax.text(x+w/2, y+.32, text, ha='center', va='center', fontsize=8.3,
            color='#17232d', linespacing=1.25)

def arrow(ax, start, end, color=GRAY, style='-', rad=0):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=10,
                                linewidth=1, color=color, linestyle=style,
                                connectionstyle=f'arc3,rad={rad}'))

# Use the illustrated, saved-geometry architecture rather than text-only boxes.
import runpy
runpy.run_path(str(ROOT / 'scripts/build_grpo_illustrated_figure.py'))
runpy.run_path(str(ROOT / 'scripts/build_mcgot_design_figure.py'))
plt.rcParams.update({'font.size':9,'text.color':'#203047',
                     'axes.labelcolor':'#203047','xtick.color':'#64748b',
                     'ytick.color':'#203047'})
with (ROOT/'experiments/agentic-verifier-grpo-20261006/per-task.csv').open() as f:
    rows=[r for r in csv.DictReader(f) if r['reference_valid']=='True']
groups=[('Easy (T1-T2)',{'T1','T2'}),('Moderate (T3-T4)',{'T3','T4'}),('Hard (T5)',{'T5'}),('All valid',{'T1','T2','T3','T4','T5'})]
fig,ax=plt.subplots(figsize=(3.55,2.9))
for i,(label,cats) in enumerate(groups):
    ax.axhspan(i-.43,i+.43,facecolor=['#f3f7fd','#f8f6fd','#f1faf8','#eef4fa'][i],zorder=0)
    subset=[r for r in rows if r['category'] in cats]; n=len(subset)
    for offset,key,color in [(-.17,'without',BLUE),(.17,'with_agent',GREEN)]:
        count=sum(r[key]=='True' for r in subset); rate=100*count/n
        ax.barh(i+offset,rate,height=.28,color=color,label=('Astra' if key=='without' else '+ verifier / repair') if i==0 else None)
        ax.text(rate+1.2,i+offset,f'{count}/{n}',va='center',fontsize=8)
ax.set(yticks=range(4),yticklabels=[g[0] for g in groups],xlim=(0,112),xticks=[0,25,50,75,100],xlabel='Strict geometry agreement (%)')
ax.invert_yaxis(); ax.spines[['top','right','left']].set_visible(False)
ax.tick_params(axis='y',length=0,labelsize=8); ax.grid(axis='x',alpha=.10); ax.set_axisbelow(True)
ax.spines['bottom'].set_color('#cbd5e1')
ax.legend(loc='upper center',bbox_to_anchor=(.46,1.22),ncol=1,frameon=False,fontsize=8)
fig.subplots_adjust(left=.35,right=.98,bottom=.19,top=.80)
for ext in ('pdf','svg','png'): fig.savefig(OUT/f'grpo-verifier-tier-results.{ext}',dpi=220)
plt.close(fig)
