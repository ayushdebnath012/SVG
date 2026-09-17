"""Prepare, launch, inspect and fetch the Serveo compute batch using SSH.

Authentication stays in SSH. No passwords, local .env, or private keys are
included in the archive. Run `prepare`, then `connect`, then `launch`.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'tmp/remote-compute'
SOCKET = STATE / 'ssh.sock'


def ssh_options(identity=None):
    options = ['-o', 'StrictHostKeyChecking=accept-new', '-o', 'ConnectTimeout=20',
               '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
               '-o', 'ProxyCommand=ssh -o StrictHostKeyChecking=accept-new '
                     '-o ConnectTimeout=20 -W sn4622130673:22 serveo.net',
               '-o', f'ControlPath={SOCKET}']
    if identity:
        options += ['-i', str(identity.resolve()), '-o', 'IdentitiesOnly=yes']
    return options


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'connect', 'launch', 'status', 'fetch'])
    parser.add_argument('--identity', type=Path)
    parser.add_argument('--gpu', help='CUDA_VISIBLE_DEVICES for the job; bypasses the idle-GPU heuristic '
                        '(needed when a display session holds a little memory on the only device)')
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    state_path = STATE / 'latest.json'
    host = 'iit@sn4622130673'
    ssh = ['ssh', *ssh_options(args.identity)]
    if args.action == 'connect':
        # Foreground authentication, then a reusable master socket for file transfer.
        subprocess.run([*ssh, '-M', '-o', 'ControlPersist=4h', '-fN', host], check=True)
        subprocess.run([*ssh, host, 'hostname; nvidia-smi; df -h .; command -v python3'], check=True)
        return
    if args.action == 'prepare':
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        archive = STATE / f'source-{stamp}.tar.gz'
        prefixes = ('scripts/', 'src/', 'tests/', 'vendor/', 'experiments/', 'configs/',
                    'data/controlled-editing/', 'runs/a100/', 'runs/reference-v3/')
        files = []
        for path in sorted(ROOT.rglob('*')):
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part.startswith('.') or part in ('__pycache__', 'checkpoints') for part in relative.parts):
                continue
            if str(relative).startswith(prefixes) or str(relative) in ('requirements-local.txt', 'requirements-colab.txt'):
                if path.suffix not in ('.pyc', '.zip'):
                    files.append(path)
        hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        manifest = STATE / f'source-{stamp}.json'
        manifest.write_text(json.dumps(hashes, indent=2) + '\n')
        with tarfile.open(archive, 'w:gz') as tar:
            for path in files:
                tar.add(path, arcname=str(Path('cvpr2027') / path.relative_to(ROOT)), recursive=False)
            tar.add(manifest, arcname='cvpr2027/source-manifest.json')
        state = {'created_utc': stamp, 'archive': str(archive),
                 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                 'remote': f'svg-compute/{stamp}', 'host': host, 'status': 'prepared'}
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        print(json.dumps(state, indent=2))
        print(f'{len(files)} files; {archive.stat().st_size / 1024**2:.1f} MiB')
        return
    state = json.loads(state_path.read_text())
    remote = state['remote']
    quote = shlex.quote
    # Require an authenticated master; never leave unattended transfers at a password prompt.
    subprocess.run([*ssh, '-O', 'check', host], check=True)
    scp = ['scp', *ssh_options(args.identity)]
    if args.action == 'launch':
        if state['status'] != 'prepared':
            parser.error('This bundle has already been launched; use status or prepare a new bundle')
        subprocess.run([*ssh, host, f'mkdir -p {quote(remote)}'], check=True)
        subprocess.run([*scp, state['archive'], f'{host}:{remote}/source.tar.gz'], check=True)
        verify = f"printf '%s  source.tar.gz\\n' {quote(state['archive_sha256'])} | sha256sum -c -"
        subprocess.run([*ssh, host, f'cd {quote(remote)} && {verify} && tar -xzf source.tar.gz'], check=True)
        job = f'cd {quote(remote + "/cvpr2027")} && bash scripts/bootstrap_remote.sh && '
        if args.gpu is not None:
            job += f'export CUDA_VISIBLE_DEVICES={quote(args.gpu)} && '
        job += 'exec .venv-remote/bin/python scripts/remote_batch.py --output results'
        command = f'nohup bash -c {quote(job)} > {quote(remote + "/launch.log")} 2>&1 < /dev/null & echo $!'
        pid = subprocess.check_output([*ssh, host, command], text=True).strip()
        state.update(status='launched', remote_pid=pid)
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        print(f'Launched remote PID {pid} in {remote}; use status to monitor bootstrap and stages')
    elif args.action == 'status':
        command = f'tail -n 25 {quote(remote + "/launch.log")}; '
        command += f'cat {quote(remote + "/cvpr2027/results/status.json")} 2>/dev/null || true'
        subprocess.run([*ssh, host, command], check=True)
    elif args.action == 'fetch':
        subprocess.run([*ssh, host, f'cd {quote(remote)} && '
            "tar --exclude='*/checkpoints' -czf results.tar.gz launch.log cvpr2027/results"], check=True)
        destination = STATE / f'results-{state["created_utc"]}.tar.gz'
        subprocess.run([*scp, f'{host}:{remote}/results.tar.gz', str(destination)], check=True)
        print(f'Downloaded {destination}; intermediate optimizer checkpoints remain on the host')


if __name__ == '__main__':
    main()
