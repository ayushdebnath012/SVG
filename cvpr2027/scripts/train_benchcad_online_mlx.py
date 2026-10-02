"""Fresh-base online edit-pair QLoRA and full retained family-holdout evaluation."""
import argparse
import ast
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

from benchcad_online_edit_dataset import apply


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def main():
    sys.setrecursionlimit(10000)
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--iters', type=int)
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
            total = len(tokenizer.apply_chat_template(chat, tokenize=True))
            answer = len(tokenizer.encode(r['target']))
            if total > 3072 or answer > 512:
                omissions.append(dict(id=r['id'], split=split, tokens=total, answer_tokens=answer,
                                      category=r['category'], family=r['family']))
                continue
            filtered[split].append(r)
        if not filtered[split]:
            raise ValueError(f'No retained {split} rows')
        name = 'valid' if split == 'validation' else split
        chats = [dict(messages=messages(r) + [dict(role='assistant', content=r['target'])]) for r in filtered[split]]
        (mlxpath / f'{name}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in chats))
    groups = [{r['component_id'] for r in rs} for rs in filtered.values()]
    assert all(not x & y for i, x in enumerate(groups) for y in groups[i+1:])
    iters = a.iters or len(filtered['train'])
    manifest = dict(status='started', model=a.model, model_repo='mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit',
                    model_revision=Path(a.model).name, source_manifest=source,
                    packages={k: importlib.metadata.version(k) for k in ('mlx', 'mlx-lm', 'transformers')},
                    iterations=iters, seed=17, max_sequence_length=3072, max_generation_tokens=512,
                    batch_size=1, learning_rate=1e-4, lora_layers=8,
                    counts={s: len(rs) for s, rs in filtered.items()}, omissions=omissions,
                    categories={s:dict(Counter(r['category'] for r in rs)) for s,rs in filtered.items()},
                    families={s:sorted({r['family'] for r in rs}) for s,rs in filtered.items()},
                    evaluation='All retained held-out records, fixed once before training. Greedy decoding, exact patches, AST equality, then separate CAD/STEP scoring.',
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    dump(a.output / 'run_manifest.json', manifest)
    dump(a.output / 'test-records.json', filtered['test'])
    def evaluate(label, m, tok):
        results = []
        for r in filtered['test']:
            prompt = tok.apply_chat_template(messages(r), tokenize=False, add_generation_prompt=True)
            prediction = generate(m, tok, prompt=prompt, max_tokens=512, sampler=make_sampler(temp=0), verbose=False)
            patch = None
            error = None
            ast_match = False
            try:
                text = prediction.strip()
                if text.startswith('```'):
                    text = '\n'.join(text.splitlines()[1:-1])
                patch = json.loads(text)
                predicted_code = apply(r['code'], patch)
                ast_match = ast.dump(ast.parse(predicted_code)) == ast.dump(ast.parse(r['edited_code']))
            except Exception as e:
                error = str(e)[:250]
                predicted_code = None
            results.append(dict(id=r['id'], source_record_id=r['source_record_id'], family=r['family'],
                                category=r['category'], prediction=prediction,
                                exact=patch == json.loads(r['target']), applicable=error is None,
                                ast_match=ast_match, error=error, predicted_code=predicted_code,
                                reference_code=r['edited_code'], reference_step=str((a.data/r['reference_step']).resolve()),
                                reference_step_sha256=r['reference_step_sha256']))
            # Preserve completed outputs if an operational interruption occurs.
            with (a.output / f'{label}-predictions.jsonl').open('a') as f:
                f.write(json.dumps(results[-1]) + '\n')
            print(label, len(results), '/', len(filtered['test']), flush=True)
        metrics = dict(n=len(results), exact=sum(r['exact'] for r in results),
                       applicable=sum(r['applicable'] for r in results), ast_match=sum(r['ast_match'] for r in results),
                       categories={c:dict(n=sum(r['category']==c for r in results),
                                          exact=sum(r['exact'] and r['category']==c for r in results),
                                          ast_match=sum(r['ast_match'] and r['category']==c for r in results)) for c in sorted({r['category'] for r in results})})
        dump(a.output / f'{label}-metrics.json', metrics)
        print(label, metrics, flush=True)
    evaluate('base', model, tokenizer)
    del model, tokenizer
    mx.clear_cache()
    command = [sys.executable, '-m', 'mlx_lm', 'lora', '--model', a.model,
               '--train', '--mask-prompt', '--data', str(mlxpath), '--adapter-path', str(a.output/'adapter'),
               '--iters', str(iters), '--batch-size', '1', '--num-layers', '8', '--learning-rate', '0.0001',
               '--max-seq-length', '3072', '--grad-checkpoint', '--steps-per-report', '25',
               '--steps-per-eval', '100', '--val-batches', '8', '--save-every', '100', '--seed', '17']
    manifest['command'] = command
    dump(a.output/'run_manifest.json', manifest)
    start = time.monotonic()
    result = subprocess.run(command)
    if result.returncode:
        manifest.update(status='failed', returncode=result.returncode)
        dump(a.output/'run_manifest.json', manifest)
        raise SystemExit(result.returncode)
    model, tokenizer = load(a.model, adapter_path=str(a.output/'adapter'))
    evaluate('trained', model, tokenizer)
    manifest.update(status='completed', training_and_final_eval_seconds=time.monotonic()-start,
                    adapter_sha256=hashlib.sha256((a.output/'adapter/adapters.safetensors').read_bytes()).hexdigest())
    dump(a.output/'run_manifest.json', manifest)


if __name__ == '__main__':
    main()
