"""Verify packaged file hashes, or refresh the manifest from non-ignored Git files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'SHA256SUMS.json'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return {'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write', action='store_true', help='Refresh after intentional changes; requires Git')
    a = p.parse_args()
    if a.write:
        raw = subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z','.'], cwd=ROOT)
        paths = sorted(set(x for x in raw.decode().split('\0') if x))
        manifest = {name: digest(ROOT/name) for name in paths
                    if name != MANIFEST.name and (ROOT/name).is_file()}
        MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n')
        print(f'Wrote hashes for {len(manifest)} packaged files')
    else:
        manifest = json.loads(MANIFEST.read_text())
        errors = []
        for name, expected in manifest.items():
            path = (ROOT/name).resolve()
            if ROOT not in path.parents:
                errors.append(name+': outside project'); continue
            if not path.is_file() or digest(path) != expected:
                errors.append(name+': missing or changed')
        if errors:
            raise SystemExit('\n'.join(errors))
        print(f'Verified {len(manifest)} packaged files')


if __name__ == '__main__':
    main()
