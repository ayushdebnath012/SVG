"""Create an UNAPPROVED evaluator review template, never an automatic approval."""
import argparse, json
from pathlib import Path
from score import REQUIRED, REVIEW_CHECKS, digest, canonical_hash, strict_json

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--tasks',required=True);ap.add_argument('--task-id',required=True);ap.add_argument('--submissions',required=True);ap.add_argument('--run-id',required=True);ap.add_argument('--out',required=True)
 a=ap.parse_args();root=Path(a.submissions).resolve();out=Path(a.out).resolve()
 if out.is_relative_to(root):ap.error('review templates must be outside candidate submissions')
 if out.exists():ap.error('refusing to overwrite an existing review')
 ts=[strict_json(x) for x in Path(a.tasks).read_text().splitlines() if x.strip()]
 t=next((x for x in ts if x['task_id']==a.task_id),None)
 if not t:ap.error('unknown task')
 folder=(root/a.task_id).resolve()
 if not folder.is_relative_to(root):ap.error('unsafe submission path')
 hashes={}
 for n in REQUIRED:
  f=folder/n
  if f.is_file() and not f.is_symlink() and f.stat().st_size:hashes[n]=digest(f)
 rec={'task_id':a.task_id,'run_id':a.run_id,'task_sha256':canonical_hash(t),'artifacts':hashes,'reviewer':'',**{k:False for k in REVIEW_CHECKS},'evidence':{k:'' for k in REVIEW_CHECKS}}
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rec)+'\n')
 print('UNAPPROVED template created. Inspect/reproduce the submitted workflow in an isolated environment; fill evidence notes and decisions yourself. No candidate code executed.')
if __name__=='__main__':main()
