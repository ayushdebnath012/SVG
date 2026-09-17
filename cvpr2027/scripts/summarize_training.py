"""Verify downloaded three-seed pilot artifacts and recompute reported scores.

Does not load pickle checkpoints. Safetensors checks validate file structure,
not inference equivalence. Run from any directory with the local dependencies.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from train_controlled_editing import load_rows, score_action
from eval_controlled_rule_baseline import predict


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
    return sha.hexdigest()


def check_weights(path):
    with path.open('rb') as f:
        header_size = struct.unpack('<Q', f.read(8))[0]
        assert 0 < header_size < path.stat().st_size - 8
        header = json.loads(f.read(header_size))
    tensors = {k: v for k, v in header.items() if k != '__metadata__'}
    assert tensors
    offsets = sorted(v['data_offsets'] for v in tensors.values())
    cursor = 0
    for start, end in offsets:
        assert start == cursor and end > start
        cursor = end
    assert cursor + header_size + 8 == path.stat().st_size
    parameters = sum(math.prod(v['shape']) for v in tensors.values())
    assert parameters == 4358144, parameters
    return {'sha256': digest(path), 'bytes': path.stat().st_size,
            'tensors': len(tensors), 'parameters': parameters}


def verify(root):
    result = {'runs': [], 'limitations': [
        'Shared instruction templates; ten physical cases per evaluation split.',
        'Repeated seeds are not independent evaluation cases.',
        'Compact DOM input; no raster reasoning or actual solver recomputation.',
        'Perfect rule baseline: this is pipeline validation, not a novelty result.']}
    revisions, data_hashes = set(), []
    for seed in (17, 29, 41):
        run = root / f'seed-{seed}'
        manifest = json.loads((run / 'run_manifest.json').read_text())
        assert manifest['status'] == 'completed' and manifest['seed'] == seed
        assert manifest['epochs'] == 3 and manifest['global_steps'] == 90
        # The pilot configuration is fixed; the GPU is recorded per run rather than required.
        assert manifest['effective_batch_size'] == 12 and manifest['gpu']
        for field, filename in [('training_script_sha256', 'train_controlled_editing.py'),
                                ('data_script_sha256', 'controlled_editing_data.py')]:
            assert manifest[field] == digest(Path(__file__).with_name(filename)), field
        state = json.loads((run / 'trainer_state.json').read_text())
        assert state['global_step'] == 90 and state['epoch'] == 3
        revisions.add(manifest['model_revision'])
        data = {}; cases = set(); hashes = {}
        for split, expected in [('train', 360), ('validation', 60), ('test', 60), ('ood', 60)]:
            path = run / 'data' / f'{split}.jsonl'
            hashes[split] = digest(path)
            assert hashes[split] == manifest['data_manifest']['splits'][split]['sha256']
            rows = load_rows(path)
            assert len(rows) == expected and len({r['id'] for r in rows}) == expected
            split_cases = {r['case_id'] for r in rows}
            assert not cases.intersection(split_cases)
            assert len(split_cases) == expected // 6
            cases.update(split_cases); data[split] = {r['id']: r for r in rows}
        data_hashes.append(hashes)
        entry = {'seed': seed, 'manifest': manifest,
                 'adapter': check_weights(run / 'adapter' / 'adapter_model.safetensors'),
                 'scores': {}}
        for label in ('base', 'sft'):
            raw = load_rows(run / f'{label}_generations.jsonl')
            assert len(raw) == 120 and len({r['id'] for r in raw}) == 120
            stored = json.loads((run / f'{label}_metrics.json').read_text())
            entry['scores'][label] = {}
            for split in ('test', 'ood'):
                predictions = [r for r in raw if r['split'] == split]
                assert {r['id'] for r in predictions} == set(data[split])
                recomputed = []
                for pred in predictions:
                    row = data[split][pred['id']]
                    assert pred['target'] == row['target'] and pred['case_id'] == row['case_id']
                    metrics = score_action(row, pred['prediction'])
                    assert metrics == pred['metrics'], pred['id']
                    recomputed.append(metrics)
                scores = {'n': len(predictions)}
                for metric in ('json_valid', 'action_correct', 'exact_action',
                               'executor_accepts', 'unsafe_edit', 'fence_normalized_exact_action'):
                    scores[metric] = sum(r[metric] for r in recomputed) / len(recomputed)
                    assert abs(scores[metric] - stored[split][metric]) < 1e-12
                entry['scores'][label][split] = scores
        entry['scores']['rule'] = {
            split: {'n': len(rows), 'exact_action': sum(
                predict(row['instruction']) == row['target'] for row in rows.values()) / len(rows)}
            for split, rows in data.items() if split in ('test', 'ood')}
        result['runs'].append(entry)
    assert len(revisions) == 1
    assert all(h == data_hashes[0] for h in data_hashes)
    result['model_revision'] = next(iter(revisions))
    result['split_sha256'] = data_hashes[0]
    result['verification'] = 'complete; raw predictions rescored and adapter structure checked'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.runs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(report['verification'])
    for run in report['runs']:
        print(run['seed'], json.dumps(run['scores']))
