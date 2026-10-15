"""Prepare, replay and compare the audited, web-sourced FEM pilot.

No model API calls. Only the six admitted track tasks can be prepared. Numerical
errors are diagnostics; no unsupported tolerance or self-reported physics pass.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, shutil, subprocess, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'cvpr2027/data/published-fem-pilot-v1'


def load(p):
    def reject(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(p.read_text(), parse_constant=reject)


def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def asset_inventory(folder):
    result = []
    for p in sorted(folder.rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlink artifact not permitted: ' + str(p.relative_to(folder)))
        if p.is_file():
            result.append(dict(path=str(p.relative_to(folder)), sha256=sha(p), bytes=p.stat().st_size))
    return result


def inventory_hash(items):
    return hashlib.sha256(json.dumps(items, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def choose(case, track):
    rows = [r for r in load(DATA / 'catalog.json')['records'] if r['case_id'] == case and r['track'] == track]
    if len(rows) != 1:
        raise ValueError('Case/track was not admitted by the audit: ' + case + '/' + track)
    return rows[0]


def prepare(case, track, out, model, attempt):
    row = choose(case, track)
    src = ROOT / row['candidate_manifest']; task = load(src)
    if out.exists():
        raise ValueError('Run directory already exists; attempts must not overwrite each other')
    if not out.resolve().is_relative_to((ROOT / 'cvpr2027/tmp').resolve()):
        raise ValueError('Run workspaces must be under cvpr2027/tmp')
    for f in task['files']:
        p = src.parent / f['path']
        if p.is_symlink() or sha(p) != f['sha256']:
            raise ValueError('Candidate input changed')
    out.mkdir(parents=True); inputs = out / 'inputs'; inputs.mkdir(); (out / 'submission').mkdir(); (out / 'outputs').mkdir()
    for f in task['files']:
        shutil.copy2(src.parent / f['path'], inputs / f['path'])
    protocol = dict(case_id=case, track=track, family=row['family'], model=model, attempt=attempt,
                    candidate_manifest_sha256=sha(src), evaluator_contract_sha256=sha(ROOT / row['private_contract']),
                    private_contract=row['private_contract'], input_inventory=asset_inventory(inputs), required_artifacts=task['required_artifacts'],
                    harness='one-shot-code-submission; isolated no-network replay', model_called=False,
                    status='prepared', certified_scored_release=False, public_training_contamination='possible')
    save(out / 'protocol.json', protocol)
    (out / 'model-instructions.md').write_text(
        'Use only the attached candidate input files. Solve the published engineering problem with FEM. '
        'Return a JSON object {"files": {"main.py": "<executable Python source>", ...}}. '
        'The replay mounts inputs read-only at /work/inputs and code read-only at /work/submission; '
        'write outputs in the current directory /work/outputs. main.py must execute the workflow, not echo reference answers. '
        'Do not fetch tutorials or reference results. No package installation or network. '
        'Report missing runtime capabilities explicitly.\n\n' + (inputs / 'task.md').read_text())
    print('Prepared', case, track, 'for', model, '(no API request).')


def ingest(out, response):
    if (out / 'submission-manifest.json').exists():
        raise ValueError('Submission already frozen; use a new attempt directory')
    obj = load(response); files = obj.get('files')
    if not isinstance(files, dict) or not isinstance(files.get('main.py'), str) or not files['main.py'].strip():
        raise ValueError('Expected nonempty files.main.py')
    if not 1 <= len(files) <= 20:
        raise ValueError('Invalid file count')
    for name, content in files.items():
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*\.(py|txt|json)', name):
            raise ValueError('Invalid generated filename')
        if not isinstance(content, str) or len(content.encode()) > 2_000_000:
            raise ValueError('Invalid generated file content')
    for name, content in files.items():
        (out / 'submission' / name).write_text(content)
    save(out / 'submission-manifest.json', asset_inventory(out / 'submission'))
    protocol = load(out / 'protocol.json'); protocol['status'] = 'submission_frozen'; save(out / 'protocol.json', protocol)
    print('Frozen submission; no code executed.')


def replay(out, image, timeout):
    if (out / 'execution.json').exists():
        raise ValueError('Execution already recorded; use a new attempt directory')
    if not (out / 'submission-manifest.json').exists():
        raise ValueError('Freeze a model submission first')
    if asset_inventory(out / 'submission') != load(out / 'submission-manifest.json'):
        raise ValueError('Frozen submission changed')
    protocol = load(out / 'protocol.json')
    if asset_inventory(out / 'inputs') != protocol['input_inventory']:
        raise ValueError('Frozen inputs changed')
    if not shutil.which('docker'):
        save(out / 'execution.json', dict(status='infrastructure_blocked', reason='Docker unavailable; candidate code was not executed.'))
        print('Infrastructure blocked: Docker unavailable.'); return
    identity = subprocess.run(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], capture_output=True, text=True, timeout=30)
    if identity.returncode or not re.fullmatch(r'sha256:[0-9a-f]{64}', identity.stdout.strip()):
        save(out / 'execution.json', dict(status='infrastructure_blocked', reason='Configured solver runtime image unavailable.'))
        print('Infrastructure blocked: runtime image unavailable.'); return
    runtime = identity.stdout.strip(); name = 'published-fem-' + hashlib.sha256(str(out.resolve()).encode()).hexdigest()[:16]
    cmd = ['docker', 'run', '--rm', '--name', name, '--pull=never', '--network=none', '--read-only', '--cap-drop=ALL',
           '--security-opt=no-new-privileges', '--pids-limit=128', '--memory=8g', '--memory-swap=8g', '--cpus=2',
           '--user', f'{os.getuid()}:{os.getgid()}', '--tmpfs', '/tmp:rw,nosuid,nodev,size=512m',
           '--env', 'HOME=/tmp', '--env', 'OMP_NUM_THREADS=1', '--env', 'OPENBLAS_NUM_THREADS=1']
    for folder in ['inputs', 'submission', 'outputs']:
        suffix = ',readonly' if folder != 'outputs' else ''
        cmd += ['--mount', f'type=bind,src={(out/folder).resolve()},dst=/work/{folder}{suffix}']
    cmd += ['--workdir', '/work/outputs', runtime, 'python3', '/work/submission/main.py']
    started = time.monotonic(); process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    expired = False
    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        expired = True; subprocess.run(['docker', 'kill', name], capture_output=True, timeout=20)
        process.kill(); stdout, _ = process.communicate()
    (out / 'replay.log').write_bytes(stdout)
    assets = asset_inventory(out / 'outputs')
    save(out / 'execution.json', dict(status='timeout' if expired else 'executed' if process.returncode == 0 else 'execution_error',
         returncode=process.returncode, runtime_image=runtime, wall_seconds=time.monotonic()-started, network='none',
         inputs_sha256=inventory_hash(protocol['input_inventory']), submission_sha256=inventory_hash(load(out / 'submission-manifest.json')),
         output_inventory=assets, output_inventory_sha256=inventory_hash(assets)))
    print('Replay recorded.')


STRESS_FACTORS = {'Pa': 1, 'kPa': 1000, 'MPa': 1e6, 'GPa': 1e9}


def finite_number(value):
    try:
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        return False


def compare(contract, results):
    qois = results.get('qois') if isinstance(results, dict) else None
    qois = qois if isinstance(qois, dict) else {}
    rows = []
    for ref in contract['qois']:
        pred = qois.get(ref['key']); row = dict(key=ref['key'], reference=ref['value'], unit=ref['unit'], status='missing')
        if not isinstance(pred, dict):
            rows.append(row); continue
        value, unit = pred.get('value'), pred.get('unit')
        if not finite_number(value):
            row['status'] = 'invalid_number'
        elif unit == ref['unit']:
            row.update(status='compared', prediction=value)
        elif isinstance(unit, str) and unit in STRESS_FACTORS and ref['unit'] in STRESS_FACTORS:
            row.update(status='compared', prediction=value * STRESS_FACTORS[unit] / STRESS_FACTORS[ref['unit']],
                       original_prediction=value, original_unit=unit, converted=True)
        else:
            row.update(status='unit_mismatch', original_unit=unit)
        if row['status'] == 'compared' and not math.isfinite(row['prediction']):
            row['status'] = 'invalid_number'
            row.pop('prediction', None)
        if row['status'] == 'compared':
            err = abs(row['prediction'] - ref['value'])
            row.update(absolute_error=err, relative_error=err/abs(ref['value']) if ref['value'] else None,
                       numerical_pass=None)
        rows.append(row)
    return rows


def score(out, review=None):
    protocol = load(out / 'protocol.json'); row = choose(protocol['case_id'], protocol['track'])
    src = ROOT / row['candidate_manifest']; private = ROOT / row['private_contract']
    if sha(src) != protocol['candidate_manifest_sha256'] or sha(private) != protocol['evaluator_contract_sha256']:
        raise ValueError('Benchmark contract changed after prepare')
    if asset_inventory(out / 'inputs') != protocol['input_inventory']:
        raise ValueError('Frozen inputs changed')
    contract = load(private); assets = asset_inventory(out / 'outputs'); names = {a['path'] for a in assets if a['bytes']}
    result_path = out / 'outputs/results.json'
    try:
        values = load(result_path) if result_path.exists() else {}
        qois = compare(contract, values)
    except (ValueError, TypeError):
        qois = [dict(key=q['key'], status='invalid_results') for q in contract['qois']]
    execution = load(out / 'execution.json') if (out / 'execution.json').exists() else {'status': 'not_executed'}
    verified = execution.get('status') == 'executed'
    if verified:
        verified = (execution.get('output_inventory') == assets and
                    execution.get('submission_sha256') == inventory_hash(asset_inventory(out / 'submission')) and
                    execution.get('inputs_sha256') == inventory_hash(protocol['input_inventory']))
    required = [x for x in protocol['required_artifacts'] if x not in ['main.py']]
    missing = [x for x in required if x not in names]
    if not (out / 'submission/main.py').is_file():
        missing.append('main.py')
    fields = [x for x in names if Path(x).suffix.lower() in ['.vtu', '.vtk', '.xdmf', '.npz']]
    if not fields:
        missing.append('field_output')
    review_status = 'pending'; valid_physics = None
    if review is not None:
        review = review.resolve()
        if review.is_relative_to((out / 'outputs').resolve()) or review.is_relative_to((out / 'submission').resolve()) or review.is_relative_to((out / 'inputs').resolve()):
            raise ValueError('Review must be evaluator-authored outside candidate-visible mounts')
        r = load(review)
        if (r.get('output_inventory_sha256') != inventory_hash(assets) or
                r.get('submission_sha256') != inventory_hash(asset_inventory(out / 'submission')) or
                r.get('candidate_manifest_sha256') != protocol['candidate_manifest_sha256']):
            raise ValueError('Review does not bind to these exact inputs, code and output artifacts')
        keys = ['geometry', 'physics', 'cad_mesh_correspondence', 'actual_fem_execution', 'convergence_and_recovery']
        checks = r.get('checks', {})
        if not r.get('reviewer') or not all(isinstance(checks.get(k), dict) and isinstance(checks[k].get('passed'), bool)
                                           and checks[k].get('evidence') for k in keys):
            raise ValueError('Incomplete trusted review')
        valid_physics = all(checks[k]['passed'] for k in keys)
        review_status = 'accepted' if valid_physics else 'failed'
    if execution.get('status') == 'infrastructure_blocked':
        status = 'infrastructure_blocked'
    elif not verified:
        status = 'execution_unverified'
    elif missing:
        status = 'missing_required_artifacts'
    elif valid_physics is False:
        status = 'physical_setup_failed'
    elif valid_physics is None:
        status = 'trusted_review_pending'
    elif not all(q['status'] == 'compared' for q in qois):
        status = 'invalid_or_missing_numerical_results'
    else:
        status = 'reviewed_diagnostic_comparison'
    report = dict(case_id=protocol['case_id'], track=protocol['track'], family=protocol['family'], model=protocol['model'], attempt=protocol['attempt'],
                  status=status, execution_verified=verified, execution_status=execution.get('status'), missing_artifacts=missing,
                  trusted_review_status=review_status, physical_validity=valid_physics, qois=qois, joint_pass=None,
                  certified_scored_release=False, note='No validated numeric acceptance tolerance or independent baseline; errors are diagnostic only.')
    save(out / 'score.json', report); print(json.dumps(dict(status=status, joint_pass=None)))


def summarize(files):
    reports = [load(p) for p in files]; groups = defaultdict(list)
    identifiers = set()
    for r in reports:
        ident = (r['model'], r['track'], r['case_id'], r['attempt'])
        if ident in identifiers:
            raise ValueError('Duplicate attempt in report')
        identifiers.add(ident); groups[(r['model'], r['track'])].append(r)
    rows = []
    for (model, track), runs in groups.items():
        families = defaultdict(list)
        for r in runs:
            if r['status'] == 'reviewed_diagnostic_comparison':
                errors = [q['relative_error'] for q in r['qois'] if q.get('relative_error') is not None]
                if errors:
                    families[r['family']].append(sum(errors)/len(errors))
        means = {f: sum(e)/len(e) for f, e in families.items()}
        rows.append(dict(model=model, track=track, attempts=len(runs), status_counts=dict(Counter(r['status'] for r in runs)),
                         reviewed_numeric_attempts=sum(len(e) for e in families.values()), family_mean_relative_errors=means,
                         macro_family_relative_error=sum(means.values())/len(means) if means else None,
                         note='Errors exclude unverified/failed attempts; report coverage and failures alongside errors, never as a success rate.'))
    return dict(separate_tracks=True, reports=rows, certified_scored_release=False, model_success_rate=None)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'ingest', 'replay', 'score', 'report'])
    p.add_argument('--case', default='NAFEMS-LE10'); p.add_argument('--track', choices=['cad_fem', 'analysis_fem'], default='analysis_fem')
    p.add_argument('--out', type=Path); p.add_argument('--model', default='unconfigured'); p.add_argument('--attempt', type=int, default=1)
    p.add_argument('--response', type=Path); p.add_argument('--review', type=Path); p.add_argument('--scores', nargs='+', type=Path)
    p.add_argument('--image', default='engineering-fem-runtime:0.9.0-gmsh4.15.2'); p.add_argument('--timeout', type=int, default=900)
    a = p.parse_args()
    if a.action == 'report':
        if not a.scores: p.error('--scores is required')
        report = summarize(a.scores)
        if a.out: save(a.out, report)
        else: print(json.dumps(report, indent=2))
    elif a.out is None: p.error('--out is required')
    elif a.action == 'prepare': prepare(a.case, a.track, a.out, a.model, a.attempt)
    elif a.action == 'ingest':
        if a.response is None: p.error('--response is required')
        ingest(a.out, a.response)
    elif a.action == 'replay': replay(a.out, a.image, a.timeout)
    else: score(a.out, a.review)
