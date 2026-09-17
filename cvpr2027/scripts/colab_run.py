"""Paste into a Colab GPU cell: numerical references and three-seed LoRA pilot."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import time
import urllib.request

from IPython.display import clear_output
from google.colab import files

REVISION = 'cb3ab448ea0bca1e0c7b43db3a9e1d7f24270f1a'
WORK = Path('/content/svg-colab-' + REVISION[:10])
WORK.mkdir(exist_ok=True)
subprocess.run(['nvidia-smi'], check=True)
archive = WORK / 'source.tar.gz'
if not archive.exists():
    urllib.request.urlretrieve('https://codeload.github.com/ayushdebnath012/SVG/tar.gz/' + REVISION, archive)
ROOT = WORK / ('SVG-' + REVISION) / 'cvpr2027'
if not ROOT.exists():
    with tarfile.open(archive) as tar:
        tar.extractall(WORK, filter='data')
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(ROOT/'requirements-local.txt'), '-r', str(ROOT/'requirements-colab.txt')], check=True)
subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'bitsandbytes'], check=True)
if 'OUT' not in globals():
    OUT = WORK / ('results-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
OUT.mkdir(exist_ok=True)
(OUT/'logs').mkdir(exist_ok=True)
(OUT/'packages.txt').write_text(subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True))
state_path = OUT/'status.json'
state = json.loads(state_path.read_text()) if state_path.exists() else {'git_revision': REVISION, 'scope': 'FEM and shared-template LoRA pipeline reproduction; no learned advantage established', 'stages': {}}
env = os.environ.copy()
env.update(CUDA_VISIBLE_DEVICES='0', PYTHONUNBUFFERED='1', PYTHONPATH=str(ROOT/'src'), MPLBACKEND='Agg', OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', TOKENIZERS_PARALLELISM='false')

def run(name, command):
    if state['stages'].get(name, {}).get('returncode') == 0:
        return
    state.update(status='running', current_stage=name)
    state_path.write_text(json.dumps(state, indent=2))
    start = time.monotonic()
    logfile = OUT/'logs'/f'{name}.log'
    with logfile.open('a') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        while process.poll() is None:
            clear_output(wait=True)
            print('COLAB:', OUT.name, 'STAGE:', name, 'elapsed:', round(time.monotonic()-start), 'seconds', flush=True)
            print('Completed:', ', '.join(k for k,v in state['stages'].items() if v['returncode']==0), flush=True)
            print(logfile.read_text()[-3000:], flush=True)
            time.sleep(20)
    state['stages'][name] = {'command': command, 'returncode': process.returncode, 'seconds': time.monotonic()-start}
    state.update(status='failed' if process.returncode else 'running')
    state_path.write_text(json.dumps(state, indent=2))
    print(logfile.read_text()[-3000:])
    assert process.returncode == 0, f'{name} failed; see {logfile}. Rerun this cell to resume.'

def script(name, *args):
    return [sys.executable, '-u', str(ROOT/'scripts'/name), *map(str,args)]

run('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT/'tests'), '-v'])
run('saved-adapter-reload', script('check_adapter_reload.py', '--runs', ROOT/'runs/a100', '--output', OUT/'saved-adapter-reload.json'))
for seed in (17,29,41):
    directory = OUT/'training'/f'seed-{seed}'
    command = script('train_controlled_editing.py', '--seed', seed, '--epochs', 3, '--output', directory)
    if (directory/'run_manifest.json').exists():
        command.append('--resume')
    run(f'train-{seed}', command)
run('new-adapter-reload', script('check_adapter_reload.py', '--runs', OUT/'training', '--output', OUT/'new-adapter-reload.json'))
run('fem-bar', script('fem_bench_svg_extension.py', '--output', OUT/'fem-bar'))
run('robin-reference', script('robin_fem_reference.py', '--output', OUT/'robin-reference', '--fd-reference', ROOT/'runs/reference-v3/plate_convective_edges.npz'))
run('rule-baseline', script('eval_controlled_rule_baseline.py', '--data', ROOT/'data/controlled-editing', '--output', OUT/'rule-baseline'))
summary = {'scope': state['scope'], 'git_revision': REVISION,
           'saved_reload': json.loads((OUT/'saved-adapter-reload.json').read_text()),
           'new_reload': json.loads((OUT/'new-adapter-reload.json').read_text()),
           'fem': json.loads((OUT/'fem-bar/summary.json').read_text()),
           'robin': json.loads((OUT/'robin-reference/summary.json').read_text()),
           'training': [{key:json.loads((OUT/'training'/f'seed-{seed}'/filename).read_text()) for key,filename in [('manifest','run_manifest.json'),('base','base_metrics.json'),('sft','sft_metrics.json')]} for seed in (17,29,41)]}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
state.update(status='completed', finished_utc=datetime.now(timezone.utc).isoformat())
state.pop('current_stage',None)
state_path.write_text(json.dumps(state,indent=2))
export = WORK/(OUT.name+'.tar.gz')
with tarfile.open(export,'w:gz') as tar:
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and 'checkpoints' not in path.parts:
            tar.add(path,arcname=str(Path(OUT.name)/path.relative_to(OUT)),recursive=False)
print('BATCH COMPLETE', export, 'sha256:', hashlib.sha256(export.read_bytes()).hexdigest())
for entry in summary['training']:
    print('Seed',entry['manifest']['seed'],'test',entry['sft']['test']['exact_action'],'OOD',entry['sft']['ood']['exact_action'])
files.download(str(export))
