"""Persistent frozen-verifier RPC over SSH standard streams, target-free input."""
import json,sys,torch
from train_agentic_cad_grpo import load_model,encode,distribution
torch.set_num_threads(4)
model,tok,ids=load_model(sys.argv[1])
print(json.dumps({'ready':True}),flush=True)
for line in sys.stdin:
    request=json.loads(line)
    if request.get('close'):break
    results=[]
    for row in request['rows']:
        # Whitelist before any model input is constructed.
        row={k:row[k] for k in ['code','instruction','candidate','tools']}
        try:
            with torch.no_grad():p=distribution(model,encode(tok,row),ids).exp().cpu().tolist()
            terminal=p[3][2]/(p[3][2]+p[3][3])
            results.append({'p_accept':terminal,'probabilities':p})
        except Exception as e:results.append({'p_accept':0.,'error_type':type(e).__name__})
    print(json.dumps({'results':results}),flush=True)
