"""Generate a separate CUDA result table from completed, geometry-scored artifacts."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def read(n):return json.loads((a.run/n).read_text())
m=read('run_manifest.json');assert m['status']=='completed'
t=read('trained-metrics.json');b=read('base-metrics.json');n=t['n'];assert n==b['n']==126
lines=['% Generated from completed H100 evaluation artifacts.']
def macro(k,v):lines.append('\\newcommand{\\'+k+'}{'+str(v)+'}')
rows=[]
for label,key,metrics in [('CUDA base','base',b),('CUDA base, list wrapper','base-transport-control',None),('CUDA final LoRA','trained',t)]:
 g=read(key+'-predictions-geometry.json');assert g['n']==n
 if metrics is None:
  rs=list(map(json.loads,(a.run/(key+'-predictions.jsonl')).read_text().splitlines()));app=sum(r['applicable'] for r in rs);ast=sum(r['ast_match'] for r in rs)
 else:app=metrics['applicable'];ast=metrics['ast_match']
 rows.append(f"{label} & {app} & {ast} & {g['match_95']} & {g['match_strict']} \\\\")
macro('cudaRows','\n'.join(rows));g=read('trained-predictions-geometry.json');s=g['statuses']
macro('cudaSummary',f"The final CUDA adapter yields {t['applicable']}/{n} applicable patches and {t['ast_match']}/{n} target AST matches. Against {g['reference_valid']} valid released STEP solids, {g['executable']} predictions execute, {g['match_95']} meet broad IoU and {g['match_strict']} meet strict IoU ({100*g['match_strict']/g['reference_valid']:.1f}\\,\\%). There are {s.get('invalid_patch',0)} invalid patches, {s.get('execution_error',0)} execution errors, {s.get('timeout',0)} timeouts and {s.get('comparison_error',0)} comparison errors; the same invalid released reference is excluded from the geometry denominator.")
macro('cudaAbstract',f"A subsequent three-epoch H100 LoRA run on the same retained split produces {t['applicable']}/{n} applicable patches and {g['match_strict']}/{g['reference_valid']} strict solid matches.")
a.output.write_text('\n'.join(lines)+'\n')
