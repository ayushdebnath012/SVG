"""Audit selection provenance and budget before opening any held-out reference."""
import argparse,hashlib,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--experiment',type=Path,required=True);a=ap.parse_args();p=a.experiment
    manifest=json.loads((p/'manifest.json').read_text());summary=json.loads((p/'search-summary.json').read_text())
    initial={r['id']:r for r in map(json.loads,(p/'heldout-target-free.jsonl').read_text().splitlines())}
    selected=list(map(json.loads,(p/'selected.jsonl').read_text().splitlines()))
    assert len(selected)==124 and set(initial)=={r['id'] for r in selected}
    forbidden={'label','reference_valid','reference_code','reference_step','target','audit_reference_iou','audit_selected_strict'}
    calls=[json.loads(f.read_text()) for f in (p/'calls').glob('*/*/result.json')]
    assert len(calls)==summary['api_attempts']
    assert sum(c['estimated_cost_usd'] for c in calls)<=manifest['api_budget_usd']+1e-9
    for folder in (p/'calls').glob('*/*'):
        if not (folder/'result.json').exists():continue
        request=json.loads((folder/'request.json').read_text());body=json.loads(request['messages'][1]['content'])
        assert not forbidden.intersection(body)
        result=json.loads((folder/'result.json').read_text());row=initial[result['id']]
        assert body['original_source']==row['code'] and body['instruction']==row['instruction']
        if (folder/'feature.json').exists():
            feature=json.loads((folder/'feature.json').read_text());assert not forbidden.intersection(feature)
    depths={};replaced=0
    for r in selected:
        tree=r['tree'];assert tree[0]['parent'] is None and tree[0]['depth']==0
        assert r['nodes']==len(tree) and r['selected_depth']==tree[r['selected_node']]['depth']
        for n in tree:
            children=[c for c in tree if c['parent']==n['node']]
            assert len(children)<=2 and n['depth']<=2
            if n['parent'] is not None:assert n['depth']==tree[n['parent']]['depth']+1
            assert n['visits']>=sum(c['visits'] for c in children)
        assert tree[0]['visits']==sum(n['visits'] for n in tree if n['parent']==0)
        chosen=tree[r['selected_node']]
        if r['replace_original']:
            replaced+=1;assert chosen['eligible'] and chosen['metadata']['tools']['execute']['gates']
            assert chosen['value']>tree[0]['value']
            folder=p/chosen['metadata']['origin'];assert (folder/'response.txt').read_text()==r['prediction']
        else:assert r['selected_node']==0 and r['prediction']==initial[r['id']]['candidate']
        depths[r['selected_depth']]=depths.get(r['selected_depth'],0)+1
    assert replaced==summary['replacements']
    report=dict(passed=True,all_tasks=124,api_attempts=len(calls),replacements=replaced,selected_depths=depths,
                references_in_search=False,target_free_request_audit=True,tree_bounds_verified=True,
                selected_prediction_sha256=hashlib.sha256((p/'selected.jsonl').read_bytes()).hexdigest(),
                note='This audit is performed before any new held-out reference scoring.')
    (p/'selection-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
