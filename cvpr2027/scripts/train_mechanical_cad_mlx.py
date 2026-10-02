"""Reproducible local QLoRA pilot, with base/final held-out patch evaluation."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import sys
import time


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--iters', type=int, default=100)
    p.add_argument('--eval-count', type=int, default=12)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Use a fresh output directory')
    import mlx.core as mx
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    a.output.mkdir(parents=True)
    source = json.loads((a.data / 'manifest.json').read_text())
    model, tokenizer = load(a.model)
    def messages(r):
        return [dict(role='system', content=source['system']), dict(role='user', content=r['input'])]
    filtered = {}
    omissions = []
    mlxpath = a.output / 'data'
    mlxpath.mkdir()
    for split in ('train', 'validation', 'test'):
        content = (a.data / f'{split}.jsonl').read_bytes()
        assert hashlib.sha256(content).hexdigest() == source['files'][split]
        filtered[split] = []
        for line in content.decode().splitlines():
            r = json.loads(line)
            chat = messages(r) + [dict(role='assistant', content=r['target'])]
            tokens = tokenizer.apply_chat_template(chat, tokenize=True)
            if len(tokens) > 3072:
                omissions.append(dict(id=r['id'], split=split, tokens=len(tokens)))
                continue
            filtered[split].append(r)
        if not filtered[split]:
            raise ValueError(f'No retained {split} rows')
        name = 'valid' if split == 'validation' else split
        (mlxpath / f'{name}.jsonl').write_text(''.join(json.dumps(dict(messages=messages(r) + [dict(role='assistant', content=r['target'])])) + '\n' for r in filtered[split]))
    families = [{r['family'] for r in rs} for rs in filtered.values()]
    assert all(not x & y for i, x in enumerate(families) for y in families[i+1:])
    manifest = dict(status='started', model=a.model, model_repo='mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit',
                    model_revision=Path(a.model).name, source_manifest=source,
                    packages={k: importlib.metadata.version(k) for k in ('mlx', 'mlx-lm', 'transformers')},
                    iterations=a.iters, seed=17, max_sequence_length=3072,
                    batch_size=1, learning_rate=1e-4, lora_layers=8,
                    counts={s: len(rs) for s, rs in filtered.items()}, omissions=omissions,
                    evaluation='First fixed held-out family test rows; exact JSON patch and source-line validity. CAD correctness assessed separately.',
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    dump(a.output / 'run_manifest.json', manifest)
    def evaluate(label, m, tok):
        results = []
        for r in filtered['test'][:a.eval_count]:
            prompt = tok.apply_chat_template(messages(r), tokenize=False, add_generation_prompt=True)
            prediction = generate(m, tok, prompt=prompt, max_tokens=256, sampler=make_sampler(temp=0), verbose=False)
            patch = None
            error = None
            try:
                clean = prediction.strip()
                if clean.startswith('```'):
                    clean = '\n'.join(clean.splitlines()[1:-1])
                patch = json.loads(clean)
                if not isinstance(patch, dict) or set(patch) != {'line', 'old', 'new'}:
                    raise ValueError('Wrong patch schema')
                if type(patch['line']) is not int or not isinstance(patch['old'], str) or not isinstance(patch['new'], str) or '\n' in patch['new']:
                    raise ValueError('Invalid field types')
                lines = r['code'].splitlines()
                if not 1 <= patch['line'] <= len(lines) or lines[patch['line'] - 1] != patch['old']:
                    raise ValueError('Patch does not match original line')
                lines[patch['line'] - 1] = patch['new']
                predicted_code = '\n'.join(lines)
            except Exception as e:
                error = str(e)
                predicted_code = None
            results.append(dict(id=r['id'], family=r['family'], prediction=prediction,
                                exact=patch == json.loads(r['target']), applicable=error is None,
                                error=error, predicted_code=predicted_code, reference_code=r['edited_code']))
            print(label, len(results), '/', min(a.eval_count, len(filtered['test'])), flush=True)
        (a.output / f'{label}-predictions.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in results))
        metrics = dict(n=len(results), exact=sum(r['exact'] for r in results), applicable=sum(r['applicable'] for r in results))
        dump(a.output / f'{label}-metrics.json', metrics)
        print(label, metrics, flush=True)
    evaluate('base', model, tokenizer)
    del model, tokenizer
    mx.clear_cache()
    command = [sys.executable, '-m', 'mlx_lm', 'lora', '--model', a.model,
               '--train', '--mask-prompt', '--data', str(mlxpath), '--adapter-path', str(a.output / 'adapter'),
               '--iters', str(a.iters), '--batch-size', '1', '--num-layers', '8', '--learning-rate', '0.0001',
               '--max-seq-length', '3072', '--grad-checkpoint', '--steps-per-report', '10',
               '--steps-per-eval', '50', '--val-batches', '4', '--save-every', '50', '--seed', '17']
    manifest['command'] = command
    dump(a.output / 'run_manifest.json', manifest)
    start = time.monotonic()
    result = subprocess.run(command)
    if result.returncode:
        manifest.update(status='failed', returncode=result.returncode)
        dump(a.output / 'run_manifest.json', manifest)
        raise SystemExit(result.returncode)
    model, tokenizer = load(a.model, adapter_path=str(a.output / 'adapter'))
    evaluate('trained', model, tokenizer)
    manifest.update(status='completed', training_and_final_eval_seconds=time.monotonic() - start,
                    adapter_sha256=hashlib.sha256((a.output / 'adapter' / 'adapters.safetensors').read_bytes()).hexdigest())
    dump(a.output / 'run_manifest.json', manifest)


if __name__ == '__main__':
    main()
