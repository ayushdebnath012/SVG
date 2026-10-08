"""Run the adaptive CAD graph, live or using saved candidates (no reference inputs)."""
import argparse,json
from pathlib import Path
from adaptive_cad.core import Engine,Memory,Config,task_input
from adaptive_cad.providers import ReplayPlanner
from adaptive_cad.live import Ledger,LivePlanner,ViewSemantic
from adaptive_cad.rendering import renderer
from adaptive_cad.verification import Verifier


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--task',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--memory',type=Path,required=True);p.add_argument('--memory-mode',choices=['frozen','online'],default='frozen')
    p.add_argument('--algorithm',choices=['mcts','best-first'],default='mcts')
    p.add_argument('--replay',type=Path,help='JSON list of candidate patch strings; no API calls')
    p.add_argument('--api-budget',type=float,default=0);p.add_argument('--max-api-calls',type=int,default=20)
    p.add_argument('--max-expansions',type=int,default=12);p.add_argument('--max-depth',type=int,default=4)
    p.add_argument('--seconds',type=float,default=1800);p.add_argument('--max-tool-jobs',type=int,default=60)
    p.add_argument('--cad-python',type=Path)
    a=p.parse_args();task=task_input(json.loads(a.task.read_text()))
    if a.out.exists() and any(a.out.iterdir()):p.error('Use a fresh output directory')
    a.out.mkdir(parents=True,exist_ok=True)
    if a.replay:
        planner=ReplayPlanner(json.loads(a.replay.read_text()));semantic=None
    else:
        if a.api_budget<=0:p.error('Live Astra requires a positive --api-budget')
        ledger=Ledger(a.out/'ledger.json',a.api_budget)
        planner=LivePlanner(a.out/'api',ledger,a.api_budget,max_calls=a.max_api_calls)
        semantic=ViewSemantic(planner,a.out,renderer(a.cad_python))
    verifier=Verifier(a.cad_python,semantic,max_jobs=a.max_tool_jobs)
    result=Engine(planner,verifier,Memory(a.memory,a.memory_mode),
        Config(algorithm=a.algorithm,max_expansions=a.max_expansions,max_depth=a.max_depth,seconds=a.seconds)).run(task)

    (a.out/'task.json').write_text(json.dumps(task,indent=2)+'\n')
    if result['status']=='PASS':
        from cad_edit_contracts import apply
        from cad_edit_verifier import extract
        _,patch=extract(result['prediction']);(a.out/'final_cad.py').write_text(apply(task['code'],patch,'cadquery'))
        result['export']=verifier.export(task,result['prediction'],a.out/'final_cad.step')
    result['tool_jobs']=verifier.jobs
    (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['task_id','status','selected_node','bank','pareto','stop','api','tool_jobs']}))

if __name__=='__main__':main()
