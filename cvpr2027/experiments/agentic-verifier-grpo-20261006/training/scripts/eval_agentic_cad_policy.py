"""Frozen verifier evaluation. Ground-truth labels affect reporting only, not action selection."""
import argparse,json
from pathlib import Path
import torch
from train_agentic_cad_grpo import load_model,encode,distribution
from agentic_cad_policy import rollout

p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--adapter',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
torch.set_num_threads(4)
model,tok,ids=load_model(str(a.adapter) if a.adapter else None)
rows=[json.loads(l) for l in a.data.read_text().splitlines()]
a.out.parent.mkdir(parents=True,exist_ok=True)
with torch.no_grad(),a.out.open('w') as f:
 for row in rows:
  probabilities=distribution(model,encode(tok,row),ids).exp().cpu().tolist()
  r=rollout(probabilities,False) # ground-truth label deliberately unavailable to policy
  r.pop('reward')
  r.update(id=row['id'],category=row['category'],probabilities=probabilities)
  f.write(json.dumps(r)+'\n');f.flush()
print(json.dumps({'evaluated':len(rows),'out':str(a.out)}))
