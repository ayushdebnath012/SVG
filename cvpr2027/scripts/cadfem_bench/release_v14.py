"""Assemble v1.4 from the immutable v1.3 release plus locally validated replay evidence.
Run from the original SVG workspace. Source data and targets are not regenerated.
"""
import argparse,json,shutil,sys
from pathlib import Path
from suites import apply

def augment(p,workspace):
 ev=p/'evaluator';pool=ev/'task-pool'
 # Preserve historical docs as history, not current release claims.
 if (ev/'DATASET_CARD.md').exists():shutil.copy2(ev/'DATASET_CARD.md',pool/'v1.3-DATASET_CARD.md')
 old=p/'report/cadfem-bench-v1.3.pdf'
 if old.exists():shutil.move(str(old),str(pool/'v1.3-report.pdf'))
 extras=ev/'runtime-validation';extras.mkdir(parents=True,exist_ok=True)
 src=workspace/'cvpr2027/tmp/frontier-fixes'
 for name in ['probe-job','solver-job-002','timeout-job','probe-job-hardened-003','solver-job-hardened']:
  shutil.copytree(src/name,extras/name,dirs_exist_ok=True)
 # Include failed attempt as a failure, never as a successful solve.
 shutil.copytree(src/'solver-job',extras/'solver-job-failed-import',dirs_exist_ok=True)
 shutil.copy2(src/'tampered-field-check.json',extras/'tampered-field-check.json')
 shutil.copy2(src/'fair-protocol.json',ev/'evaluation-protocol.json')
 shutil.copytree(workspace/'cvpr2027/data/web-cad-fem-freecad-contact',ev/'source-review/freecad-contact',dirs_exist_ok=True)
 for name in ['suites.py','sandbox_runner.py','verify_static_fields.py','release_v14.py','score_v14.py','report_v14.py','verify_v14.py','finish_v14.py']:
  shutil.copy2(Path(__file__).parent/name,p/'scripts/cadfem_bench'/name)
 shutil.copy2(Path(__file__).parent/'sandbox_runner.py',ev/'sandbox_runner.py');shutil.copy2(Path(__file__).parent/'verify_static_fields.py',ev/'verify_static_fields.py')
 shutil.copy2(Path(__file__).parent/'score_v14.py',ev/'score.py')
 shutil.copy2(Path(__file__).parent/'score_v14.py',p/'scripts/cadfem_bench/score.py')
 rows=[json.loads(x) for x in (ev/'references.jsonl').read_text().splitlines()]
 for r in rows:
  if r['family']=='femcad-hard':r['geometry_check']['analytic_radius_tolerance_mm']=.01
 text=''.join(json.dumps(r)+'\n' for r in rows)
 (ev/'references.jsonl').write_text(text);(ev/'suites/primary/references.jsonl').write_text(text)
 # Qualification is a reported subset. It does not hide unreproduced tasks.
 tasks=[json.loads(x) for x in (p/'candidate/tasks.jsonl').read_text().splitlines()]
 qualified=[t['task_id'] for t in tasks if t.get('readiness',{}).get('independently_reproduced')]
 (ev/'reproduced-task-ids.txt').write_text('\n'.join(qualified)+'\n')
 status={'balance':'fixed: primary capped at five tasks per family','release_labels':'fixed in active scorer/review protocol','sandbox_execution':'tested macOS file/network isolation and serial CAD/FEM replay; Docker backend prepared but not tested here','automatic_physics':'partial: cycloidal equilibrium/extraction check; CAD-face scope and convergence review still required','reproduction':'partial: 10 of 41 primary tasks / 16 of 126 full-pool tasks; no new tasks counted from repeat solves','complex_physics':'research pending: new original shell-contact CAD+fields pair collected but held for source/output correspondence, shell validators and independent replay','holdout':'78 public-source cases reserved outside candidate inputs; genuine private contamination-resistant holdout cannot be obtained by web crawling alone','frontier_trials':'not run; prior user preference was benchmark/runner preparation','human_expert_baseline':'not run; trusted software solver replay is provided and labeled separately'}
 (ev/'limitations-status.json').write_text(json.dumps(status,indent=2)+'\n')
 shutil.copy2(src/'geometry-checks-v14.json',extras/'geometry-checks-v14.json')
 assets=Path(__file__).parent/'assets_v14'
 for f in assets.rglob('*'):
  if f.is_file():
   dest=p/f.relative_to(assets);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
 shutil.copytree(assets,p/'scripts/cadfem_bench/assets_v14',dirs_exist_ok=True)
 return status

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--workspace',type=Path,required=True);x=a.parse_args()
 if x.out.exists():a.error('output already exists; preserve previous attempts')
 shutil.copytree(x.source,x.out);apply(x.out);print(json.dumps(augment(x.out,x.workspace.resolve()),indent=2))
