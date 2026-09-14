"""List research jobs or reproduce a completed CPU check in a fresh directory."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('list')
    run = sub.add_parser('run')
    run.add_argument('id')
    run.add_argument('--output-root', type=Path, default=ROOT/'tmp/reproduction')
    run.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    jobs = json.loads((ROOT/'experiments/registry.json').read_text())['experiments']
    if a.action == 'list':
        for j in jobs:
            print(f"{j['id']:4} {j['status']:12} {'CPU command' if j.get('command') else 'record/plan':12} {j['title']}")
        return
    matches = [j for j in jobs if j['id'] == a.id.upper()]
    if not matches:
        p.error('Unknown experiment ID; use list')
    job = matches[0]
    if not job.get('command'):
        p.error('No executable reproduction for this job. See its evidence or protocol; no experiment was launched.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = a.output_root.resolve()/f"{job['id']}-{stamp}"
    values = dict(python=sys.executable, root=str(ROOT), out=str(out))
    command = [arg.format(**values) for arg in job['command']]
    print(shlex.join(command), flush=True)
    if a.dry_run:
        return
    out.mkdir(parents=True, exist_ok=False)
    for source, target in job.get('copy_inputs', []):
        shutil.copytree(ROOT/source, out/target)
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT/'src') + os.pathsep + env.get('PYTHONPATH', '')
    env['MPLBACKEND'] = 'Agg'
    with (out/'console.txt').open('w') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
    (out/'execution.json').write_text(json.dumps(dict(id=job['id'], command=command,
        utc=stamp, returncode=result.returncode, purpose='CPU reproduction; original evidence preserved'), indent=2)+'\n')
    print(f"Exit {result.returncode}; results: {out}")
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
