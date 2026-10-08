"""Export completed MCTS outcomes to LaTeX and a matched comparison figure."""
from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/mcts-astra-20261007-final'
PAPER=ROOT/'paper/network'
c=json.loads((EXP/'comparison.json').read_text())
search=json.loads((EXP/'search-summary.json').read_text())
cal=json.loads((EXP/'calibration.json').read_text())
gate=json.loads((EXP/'gate-diagnostics.json').read_text())
s=c['all_tasks'];v=c['valid_references'];old=c['versus_single_repair_all']
pre=json.loads((EXP/'api-preflight.json').read_text())
m={'mctsN':s['n'],'mctsBefore':s['before'],'mctsAfter':s['after'],'mctsPrior':old['before'],
   'mctsRecovered':s['recovered'],'mctsRegressed':s['regressed'],
   'mctsPriorGained':old['recovered'],'mctsPriorLost':old['regressed'],
   'mctsRate':f"{100*s['after']/s['n']:.1f}",'mctsDelta':f"{s['delta_pp']:.2f}",
   'mctsP':f"{v['exact_mcnemar_p']:.2f}",'mctsPriorP':f"{c['versus_single_repair_valid']['exact_mcnemar_p']:.2f}",
   'mctsCalls':c['api_attempts'],'mctsCompleted':search['api_completed'],
   'mctsCost':f"{c['api_cost_estimate_usd']+pre['estimated_cost_usd']:.2f}",
   'mctsReplaced':c['replacements'],'mctsSeconds':f"{search['seconds']:.0f}",
   'mctsThreshold':f"{cal['threshold']:.4f}",'mctsNumericWeight':cal['numeric_weight'],
   'mctsValidN':v['n'],'mctsValidAfter':v['after'],
   'mctsMaxFreshP':f"{gate['calibrated_probability_max']:.4f}",
   'mctsGatePassing':gate['passing_probability_threshold']}
(PAPER/'mcts-results.tex').write_text('% Generated from frozen MCTS selections and offline reference scores.\n'+''.join(f'\\newcommand{{\\{k}}}{{{value}}}\n' for k,value in m.items()))
rows=list(csv.DictReader((EXP/'per-task.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'svg.fonttype':'none','text.color':'#203047','axes.labelcolor':'#203047'})
fig,axes=plt.subplots(1,2,figsize=(7.2,2.9),gridspec_kw={'width_ratios':[.9,1.4]})
ax=axes[0]
counts=[s['before'],old['before'],s['after']]
colors=['#4c83e3','#10a58c','#8b5cf6']
ax.bar(range(3),[100*n/s['n'] for n in counts],color=colors,width=.6)
for i,n in enumerate(counts):ax.text(i,100*n/s['n']+2,f'{n}/{s["n"]}',ha='center',fontsize=9,weight='bold')
ax.set(ylim=(0,100),xticks=range(3),xticklabels=['Astra','One repair','MCTS'],ylabel='Strict geometry agreement (%)')
ax.set_title('All 124 tasks',weight='bold',fontsize=10)
ax=axes[1]
groups=[('Easy',{'T1','T2'}),('Moderate',{'T3','T4'}),('Hard',{'T5'})]
for i,(label,cats) in enumerate(groups):
    rr=[r for r in rows if r['reference_valid']=='True' and r['category'] in cats]
    ax.axhspan(i-.42,i+.42,color=['#f3f7fd','#f8f6fd','#f1faf8'][i],zorder=0)
    for off,key,color,name in [(-.22,'without',colors[0],'Astra'),(0,'with_single_repair',colors[1],'One repair'),(.22,'with_mcts',colors[2],'MCTS')]:
        count=sum(r[key]=='True' for r in rr);rate=100*count/len(rr)
        ax.barh(i+off,rate,height=.18,color=color,label=name if i==0 else None)
        ax.text(rate+1,i+off,f'{count}/{len(rr)}',va='center',fontsize=8)
ax.set(yticks=range(3),yticklabels=[g[0] for g in groups],xlim=(0,115),xticks=[0,25,50,75,100],xlabel='Strict agreement (%)')
ax.invert_yaxis();ax.set_title('Edit tiers: 123 valid references',weight='bold',fontsize=10)
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.31),ncol=3,frameon=False,fontsize=8)
for ax in axes:
    ax.spines[['top','right']].set_visible(False);ax.spines['bottom'].set_color('#cbd5e1');ax.spines['left'].set_color('#cbd5e1')
    ax.grid(axis='y' if ax is axes[0] else 'x',alpha=.1);ax.set_axisbelow(True)
fig.subplots_adjust(left=.09,right=.98,bottom=.21,top=.76,wspace=.5)
for ext in ('pdf','svg','png'):fig.savefig(PAPER/f'figures/mcts-astra-comparison.{ext}',dpi=240)
plt.close(fig)
