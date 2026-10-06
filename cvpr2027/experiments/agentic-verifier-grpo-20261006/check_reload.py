import sys,json,torch
sys.path.insert(0,'scripts')
from train_agentic_cad_grpo import load_model,encode,distribution
m,t,i=load_model('run-v1/adapter')
r=json.loads(open('data/dev.jsonl').readline());x=encode(t,r)
with torch.no_grad():a=distribution(m,x,i)
m.load_adapter('run-v1/adapter',adapter_name='second');m.set_adapter('second');m.eval()
with torch.no_grad():b=distribution(m,x,i)
print('first',a.tolist(),'second',b.tolist(),'maxdiff',(a-b).abs().max().item())
for name,p in m.named_parameters():
 if '.default.' in name:
  q=dict(m.named_parameters())[name.replace('.default.','.second.')]
  if not torch.equal(p,q):print('MISMATCH',name,p.dtype,q.dtype,(p-q).abs().max().item())
