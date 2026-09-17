"""Compare a fresh GPU batch against the saved A100 run and numerical references.

Exact comparisons cover adapter bytes, every raw prediction and the training
loss record. Numerical references are compared with a relative tolerance
because BLAS reductions differ between hosts. Timing fields are ignored.
"""
import argparse
import hashlib
import json
from pathlib import Path

SEEDS = (17, 29, 41)
TIMING = {'batch_seconds', 'solve_seconds', 'training_seconds', 'train_runtime',
          'train_samples_per_second', 'train_steps_per_second', 'eval_runtime',
          'eval_samples_per_second', 'eval_steps_per_second'}
TEXT_SKIP = {'old_solution_id', 'new_solution_id'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def strip(value, skip):
    if isinstance(value, dict):
        return {k: strip(v, skip) for k, v in value.items() if k not in skip}
    if isinstance(value, list):
        return [strip(v, skip) for v in value]
    return value


def differences(a, b, path=''):
    """Yield (path, absolute gap, relative gap) for numbers; text and structure must match exactly."""
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            raise ValueError(f'{path}: keys differ {sorted(a)} vs {sorted(b)}')
        for k in a:
            yield from differences(a[k], b[k], f'{path}/{k}')
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise ValueError(f'{path}: lengths differ')
        for i, (x, y) in enumerate(zip(a, b)):
            yield from differences(x, y, f'{path}[{i}]')
    elif isinstance(a, (bool, str)) or isinstance(b, (bool, str)) or a is None or b is None:
        if a != b:
            raise ValueError(f'{path}: {a!r} != {b!r}')
    elif a != b:
        yield path, abs(a - b), abs(a - b) / max(abs(a), abs(b))


def compare_reference(new, saved, skip, rel_tol=1e-6, abs_tol=1e-9):
    a, b = (strip(json.loads(p.read_text()), TIMING | skip) for p in (new, saved))
    gaps = list(differences(a, b))
    outside = [(p, x, r) for p, x, r in gaps if x > abs_tol and r > rel_tol]
    # Roundoff-level residuals (1e-13 vs 1e-14) are reported by absolute gap only.
    return {'numbers_compared_differing': len(gaps), 'within_tolerance': not outside,
            'outside_tolerance': [p for p, _, _ in outside][:20],
            'max_absolute_difference': max((x for _, x, _ in gaps), default=0.0),
            'max_relative_difference_above_abs_tol': max((r for _, x, r in gaps if x > abs_tol), default=0.0)}


def compare_training(new, saved):
    report = {}
    for seed in SEEDS:
        n, s = new / f'seed-{seed}', saved / f'seed-{seed}'
        entry = {'adapter_sha256_identical': digest(n / 'adapter/adapter_model.safetensors')
                 == digest(s / 'adapter/adapter_model.safetensors')}
        for name in ('base_generations.jsonl', 'sft_generations.jsonl'):
            a, b = rows(n / name), rows(s / name)
            entry[name] = {'rows': len(a), 'identical_predictions':
                           len(a) == len(b) and all(strip(x, TIMING) == strip(y, TIMING) for x, y in zip(a, b))}
        entry['split_sha256_identical'] = all(digest(n / 'data' / f'{split}.jsonl') == digest(s / 'data' / f'{split}.jsonl')
                                              for split in ('train', 'validation', 'test', 'ood'))
        state = [json.loads((d / 'trainer_state.json').read_text())['log_history'] for d in (n, s)]
        losses = [[strip(e, TIMING) for e in h] for h in state]
        entry['loss_history_identical'] = losses[0] == losses[1]
        manifests = [json.loads((d / 'run_manifest.json').read_text()) for d in (n, s)]
        entry['manifest_identical_except_timing'] = strip(manifests[0], TIMING) == strip(manifests[1], TIMING)
        report[seed] = entry
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new', type=Path, required=True, help='Fresh batch results directory')
    parser.add_argument('--saved-training', type=Path, required=True)
    parser.add_argument('--saved-fem', type=Path, required=True, help='Saved FEM-Bench bar summary.json')
    parser.add_argument('--saved-robin', type=Path, required=True, help='Saved Robin reference summary.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    status = json.loads((args.new / 'status.json').read_text())
    report = {
        'scope': 'reproduction agreement check; identical outputs do not add independent test cases',
        'batch_status': status['status'],
        'stages_passed': sorted(k for k, v in status['stages'].items() if v['returncode'] == 0),
        'training': compare_training(args.new / 'training', args.saved_training),
        'fem_bar': compare_reference(args.new / 'fem-bar/summary.json', args.saved_fem, TEXT_SKIP),
        'robin': compare_reference(args.new / 'robin-reference/summary.json', args.saved_robin, set()),
        'adapter_reload': {name: {k: json.loads((args.new / f'{name}.json').read_text())[k] for k in ('n', 'exact')}
                           for name in ('saved-adapter-reload', 'new-adapter-reload')},
    }
    references_agree = (status['status'] == 'completed'
                        and all(r['n'] == r['exact'] == 18 for r in report['adapter_reload'].values())
                        and report['fem_bar']['within_tolerance'] and report['robin']['within_tolerance'])
    # Bitwise agreement is expected only on the same GPU architecture and library stack;
    # across hardware, kernel rounding changes the weights while the policy's outputs need not change.
    report['all_identical_or_within_tolerance'] = references_agree and all(
        all(v is True or (isinstance(v, dict) and v.get('identical_predictions')) for v in e.values())
        for e in report['training'].values())
    report['functionally_equivalent'] = references_agree and all(
        e['split_sha256_identical'] and e['sft_generations.jsonl']['identical_predictions']
        for e in report['training'].values())
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if report['all_identical_or_within_tolerance']:
        print('bitwise reproduction: adapters, predictions and loss histories identical')
    elif report['functionally_equivalent']:
        print('functional reproduction: every final prediction identical; adapter bytes differ')
    else:
        raise SystemExit('reproduction differs from saved artifacts')


if __name__ == '__main__':
    main()
