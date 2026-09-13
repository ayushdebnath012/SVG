from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1];out=root/'paper/figures';out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(7.2,3.8),layout='constrained')
names=['Endpoints','Path hashes','Geometric audit','Rigid freeze']
keys=['endpoint_pass','path_hash_pass','numeric_pass','freeze_pass']
stats=json.loads((root/'runs/contour-controls/summary.json').read_text())['methods']
values=[100*stats[k]['corrupt_acceptance'] for k in keys]
bars=ax.barh(names[::-1],values[::-1],color=['#64748b','#2563eb','#94a3b8','#94a3b8'])
for bar,val in zip(bars,values[::-1]):ax.text(val+1,bar.get_y()+bar.get_height()/2,f'{val:.1f}%',va='center')
ax.set_xlim(0,82);ax.set_xlabel('Corrupted drawings accepted (%) — lower is better')
ax.set_title('Manufactured diagnostic controls',loc='left',fontweight='bold',pad=18)
fig.text(.98,.98,'120 corrupt + 40 honest drawings',ha='right',va='top',fontsize=9,color='#475569')
ax.text(.99,.05,'All methods accept 40/40 honest variants.\nThe geometric audit misses wrong text labels.',transform=ax.transAxes,ha='right',fontsize=9,color='#475569')
for ext in ('png','svg'):fig.savefig(out/f'corruption_controls.{ext}',dpi=180)
plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(9,3.2),layout='constrained')
t=np.linspace(0,np.pi/2,200)
for ax,title in zip(axes,['Correct level set','Endpoint-only false pass','Wrong label, correct curve']):
    grid=np.linspace(-.1,1.3,130);xx,yy=np.meshgrid(grid,grid)
    ax.contour(xx,yy,xx*xx+yy*yy,levels=[.5,1,1.5],colors='#cbd5e1',linewidths=.8)
    ax.set(xlim=(-.08,1.25),ylim=(-.08,1.25),aspect='equal');ax.set_title(title,fontsize=10)
    ax.set_xlabel('x');ax.set_ylabel('y')
axes[0].plot(np.cos(t),np.sin(t),color='#2563eb',lw=2);axes[0].text(.6,.88,'u = 1',color='#2563eb')
axes[1].plot([0,1],[1,0],color='#dc2626',lw=2);axes[1].scatter([0,1],[1,0],color='#dc2626',s=20)
axes[1].annotate('midpoint u = 0.5',xy=(.5,.5),xytext=(.12,.15),arrowprops={'arrowstyle':'->'},fontsize=9)
axes[2].plot(np.cos(t),np.sin(t),color='#2563eb',lw=2);axes[2].text(.57,.88,'u = 2',color='#dc2626',fontweight='bold')
fig.suptitle('Numerical geometry and label semantics are separate checks',fontsize=12,fontweight='bold')
for ext in ('png','svg'):fig.savefig(out/f'failure_modes.{ext}',dpi=180)
print(out)
