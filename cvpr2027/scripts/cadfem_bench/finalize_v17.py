"""Seal a verified local v1.7 release, check the archive, and copy it to output/datasets."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def seal(package, datasets):
    check = json.loads((package / 'evaluator/verification.json').read_text())
    assert check['version'] == '1.7' and check['primary_tasks'] == 54
    assert check['complex_source_collections_hash_checked'] == 6
    assert (package / 'report/cadfem-bench-v1.7.pdf').is_file()
    for cache in package.rglob('__pycache__'):
        shutil.rmtree(cache)
    manifest_path = package / 'SHA256SUMS.txt'
    files = sorted(f for f in package.rglob('*') if f.is_file() and f != manifest_path)
    manifest_path.write_text(''.join(f'{digest(f)}  {f.relative_to(package)}\n' for f in files))
    files.append(manifest_path)
    archive = package.with_name(package.name + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as z:
        for f in files:
            z.write(f, f'{package.name}/{f.relative_to(package)}')
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
        assert bad is None, bad
        assert len(z.namelist()) == len(files)
        assert len(z.namelist()) == len(set(z.namelist()))
    datasets.mkdir(parents=True, exist_ok=True)
    target = datasets / package.name
    if target.exists():
        raise FileExistsError(target)
    shutil.copytree(package, target)
    target_archive = datasets / archive.name
    if target_archive.exists():
        raise FileExistsError(target_archive)
    shutil.copy2(archive, target_archive)
    assert digest(archive) == digest(target_archive)
    # The copied manifest covers every copied file and excludes only itself.
    for row in manifest_path.read_text().splitlines():
        sha, rel = row.split('  ', 1)
        assert digest(target / rel) == sha, rel
    return {'package': str(package), 'package_files': len(files),
            'zip': str(archive), 'zip_bytes': archive.stat().st_size,
            'zip_sha256': digest(archive), 'copied_package': str(target),
            'copied_zip': str(target_archive), 'archive_crc_passed': True,
            'copied_file_hashes_passed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--datasets', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(seal(args.package.resolve(), args.datasets.resolve()), indent=2))
