"""Run existing numerical and GPU experiments with durable stage logs.

This reproduces the shared-template pilot; it is not a new learning benchmark.
Run from an isolated copy of cvpr2027. No hosted model APIs are called.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def stages(out, cpu_only=False):
    def script(name, *args):
        return [sys.executable, str(ROOT / 'scripts' / name), *map(str, args)]
    jobs = [
        ('tests', [sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-v']),
        ('fem-bar', script('fem_bench_svg_extension.py', '--output', out / 'fem-bar')),
        ('robin-reference', script('robin_fem_reference.py', '--output', out / 'robin-reference',
                                 '--fd-reference', ROOT / 'runs/reference-v3/plate_convective_edges.npz')),
        ('rule-baseline', script('eval_controlled_rule_baseline.py', '--data',
                                ROOT / 'data/controlled-editing', '--output', out / 'rule-baseline')),
    ]
    if not cpu_only:
        jobs.append(('saved-adapter-reload', script('check_adapter_reload.py', '--runs',
                     ROOT / 'runs/a100', '--output', out / 'saved-adapter-reload.json')))
        for seed in (17, 29, 41):
            run = out / 'training' / f'seed-{seed}'
            command = script('train_controlled_editing.py', '--seed', seed, '--epochs', 3, '--output', run)
            if (run / 'run_manifest.json').exists():
                command.append('--resume')
            jobs.append((f'train-{seed}', command))
        jobs.append(('new-adapter-reload', script('check_adapter_reload.py', '--runs',
                     out / 'training', '--output', out / 'new-adapter-reload.json')))
    return jobs


def select_gpu(env):
    # Explicit selection is supported for scheduler-assigned devices. Otherwise
    # only choose a currently idle device, without touching other users' jobs.
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA PyTorch and a visible GPU are required for the GPU stages')
    if not env.get('CUDA_VISIBLE_DEVICES'):
        query = subprocess.check_output(['nvidia-smi',
            '--query-gpu=index,memory.free,memory.used,utilization.gpu',
            '--format=csv,noheader,nounits'], text=True)
        candidates = []
        for line in query.splitlines():
            index, free, used, utilization = map(int, line.split(','))
            if free >= 12000 and used < 1024 and utilization <= 5:
                candidates.append((free, index))
        if not candidates:
            raise RuntimeError('No idle GPU with 12 GB free; retry later or set CUDA_VISIBLE_DEVICES')
        env['CUDA_VISIBLE_DEVICES'] = str(max(candidates)[1])
    return env['CUDA_VISIBLE_DEVICES']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cpu-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    jobs = stages(out, args.cpu_only)
    if args.dry_run:
        for name, command in jobs:
            print(name + ': ' + shlex.join(command))
        return
    out.mkdir(parents=True, exist_ok=True)
    # flock prevents two launchers from writing the same run concurrently.
    import fcntl
    lock = (out / '.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise
    status_path = out / 'status.json'
    configuration = {'cpu_only': args.cpu_only, 'seeds': [] if args.cpu_only else [17, 29, 41], 'epochs': 3}
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for folder in ('scripts', 'src', 'tests', 'vendor', 'data', 'runs/a100', 'runs/reference-v3')
               for p in sorted((ROOT / folder).rglob('*'))
               if p.is_file() and '__pycache__' not in p.parts and 'checkpoints' not in p.parts}
    if status_path.exists():
        if not args.resume:
            lock.close()
            parser.error('Output exists; choose a fresh directory or --resume')
        report = json.loads(status_path.read_text())
        if report['configuration'] != configuration or report['source_sha256'] != sources:
            lock.close()
            parser.error('Resume requires identical configuration and source files')
    else:
        report = {'started_utc': datetime.now(timezone.utc).isoformat(),
                  'host': platform.node(), 'python': sys.version, 'configuration': configuration,
                  'source_sha256': sources, 'stages': {},
                  'scope': 'FEM reference reproduction and shared-template LoRA pipeline validation; no learned advantage established'}
    env = os.environ.copy()
    env.update(PYTHONPATH=str(ROOT / 'src'), MPLBACKEND='Agg', PYTHONUNBUFFERED='1',
               OMP_NUM_THREADS=env.get('OMP_NUM_THREADS', '4'),
               OPENBLAS_NUM_THREADS=env.get('OPENBLAS_NUM_THREADS', '4'),
               WANDB_DISABLED='true', TOKENIZERS_PARALLELISM='false')
    (out / 'logs').mkdir(exist_ok=True)
    report.update(status='running', pid=os.getpid())
    save(status_path, report)
    gpu_selected = False
    try:
        for name, command in jobs:
            if report['stages'].get(name, {}).get('returncode') == 0:
                continue
            if not args.cpu_only and (name.endswith('adapter-reload') or name.startswith('train-')):
                if not gpu_selected:
                    report['cuda_visible_devices'] = select_gpu(env)
                    gpu_selected = True
            entry = {'command': command, 'started_utc': datetime.now(timezone.utc).isoformat()}
            report['stages'][name] = entry
            report['current_stage'] = name
            save(status_path, report)
            print('START', name, flush=True)
            start = time.monotonic()
            with (out / 'logs' / f'{name}.log').open('a') as log:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            entry.update(returncode=result.returncode, seconds=time.monotonic() - start)
            save(status_path, report)
            if result.returncode:
                raise RuntimeError(f'{name} exited {result.returncode}; see logs/{name}.log')
            print('DONE', name, flush=True)
        summaries = {}
        for name, path in [('fem', out / 'fem-bar/summary.json'),
                           ('robin', out / 'robin-reference/summary.json'),
                           ('saved_reload', out / 'saved-adapter-reload.json'),
                           ('new_reload', out / 'new-adapter-reload.json')]:
            if path.exists():
                summaries[name] = json.loads(path.read_text())
        summaries['training'] = [
            {'seed': seed, **{name: json.loads((out / 'training' / f'seed-{seed}' / filename).read_text())
             for name, filename in [('manifest', 'run_manifest.json'), ('base', 'base_metrics.json'), ('sft', 'sft_metrics.json')]}}
            for seed in configuration['seeds']]
        save(out / 'summary.json', {'scope': report['scope'], **summaries})
        report.update(status='completed', finished_utc=datetime.now(timezone.utc).isoformat())
        report.pop('current_stage', None)
    except BaseException as error:
        report.update(status='failed', error=str(error))
        raise
    finally:
        save(status_path, report)
        lock.close()


if __name__ == '__main__':
    main()
