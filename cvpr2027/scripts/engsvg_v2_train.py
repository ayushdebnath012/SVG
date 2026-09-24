"""LoRA SFT on the v2 factory's SVG tasks, scored by comparing drawn geometry.

The v2 families are trusses and plates in the engsvg-ir-v1 schema, not the portal frames that
`cad_astra_benchmark.score` understands, so scoring here uses the factory's own extractor: parse both
the generated and the reference drawing into visible straight segments, then match them.

Reported separately, because they fail for different reasons and a single number hides which:

    parsed        the output is a well-formed SVG the extractor accepts
    count         it drew the right number of members
    geometry      every member endpoint matches the reference within tolerance
    exact         the drawing is byte-identical to the reference

Only SVG-target tasks are used (`text_to_svg`, `svg_edit`); the JSON-target tasks are a different
problem and belong in a different run. Subset with --limit before committing a long session: at 112k
rows with ~2 kB targets this is hours, and the question worth answering first is whether geometry
moves off zero at all.
"""
from __future__ import annotations
import argparse, glob, gzip, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get('ENGSVG_ROOT', Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
import engsvg_svg_geometry as G   # noqa: E402

SVG_TASKS = ('text_to_svg', 'svg_edit')


def load(data, splits, tasks, limit=None):
    out = {s: [] for s in splits}
    for shard in sorted(glob.glob(str(data / 'tasks-*.jsonl.gz'))):
        for line in gzip.open(shard, 'rt'):
            r = json.loads(line)
            if r['split'] in out and r['task'] in tasks:
                out[r['split']].append(r)
        if limit and all(len(v) >= limit for v in out.values()):
            break
    return {k: (v[:limit] if limit else v) for k, v in out.items()}


def compare(generated, reference, tolerance=1.0):
    """Match drawn segments against the reference by endpoint, order-independent."""
    try:
        a = G.extract(generated)
    except Exception as exc:
        return {'parsed': False, 'reason': type(exc).__name__}
    try:
        b = G.extract(reference)
    except Exception:
        return {'parsed': True, 'reason': 'reference unparseable'}
    ga, gb = a['segments'], b['segments']
    used, matched = set(), 0
    for s in gb:
        for i, t in enumerate(ga):
            if i in used:
                continue
            fwd = max(abs(s['a'][0] - t['a'][0]), abs(s['a'][1] - t['a'][1]),
                      abs(s['b'][0] - t['b'][0]), abs(s['b'][1] - t['b'][1]))
            rev = max(abs(s['a'][0] - t['b'][0]), abs(s['a'][1] - t['b'][1]),
                      abs(s['b'][0] - t['a'][0]), abs(s['b'][1] - t['a'][1]))
            if min(fwd, rev) <= tolerance:
                used.add(i); matched += 1
                break
    return {'parsed': True, 'drawn': len(ga), 'expected': len(gb), 'matched': matched,
            'count': len(ga) == len(gb), 'geometry': matched == len(gb) and len(ga) == len(gb),
            'exact': generated.strip() == reference.strip()}


def evaluate(model, tokenizer, rows, limit, max_new, tag, out_dir):
    import torch
    model.eval()
    if hasattr(model, 'gradient_checkpointing_disable'):
        model.gradient_checkpointing_disable()
    if hasattr(model, 'config'):
        model.config.use_cache = True
    agg = {'tag': tag, 'n': 0, 'parsed': 0, 'count': 0, 'geometry': 0, 'exact': 0, 'rows': []}
    for index, r in enumerate(rows[:limit]):
        t0 = time.perf_counter()
        text = tokenizer.apply_chat_template([{'role': 'user', 'content': r['prompt']}],
                                             tokenize=False, add_generation_prompt=True)
        ids = tokenizer(text, return_tensors='pt', truncation=True, max_length=6000).to(model.device)
        with torch.no_grad():
            gen = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                                 pad_token_id=tokenizer.eos_token_id)
        answer = tokenizer.decode(gen[0][ids['input_ids'].shape[1]:], skip_special_tokens=True)
        m = re.search(r'<svg\b.*?</svg>', answer, re.DOTALL | re.IGNORECASE)
        rec = {'task': r['task'], 'family': r['family']}
        if m:
            rec.update(compare(m.group(), r['target']))
        else:
            rec['parsed'] = False
            rec['reason'] = 'no svg in output'
        agg['n'] += 1
        for k in ('parsed', 'count', 'geometry', 'exact'):
            agg[k] += bool(rec.get(k))
        agg['rows'].append(rec)
        flag = ''.join(c if rec.get(k) else '-' for k, c in
                       (('parsed', 'P'), ('count', 'C'), ('geometry', 'G'), ('exact', 'X')))
        extra = (f" {rec.get('matched','?')}/{rec.get('expected','?')} members"
                 if rec.get('parsed') and 'expected' in rec else f" {rec.get('reason','')}")
        print(f'  [{tag} {index + 1}/{min(limit, len(rows))}] {flag} {time.perf_counter() - t0:.0f}s'
              f'{extra}', flush=True)
        if out_dir:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            (Path(out_dir) / f'partial-{tag}.json').write_text(json.dumps(agg, indent=2) + '\n')
            if m:
                (Path(out_dir) / f'svg-{tag}-{index:02d}.svg').write_text(m.group())
    return agg


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=Path, default=ROOT / 'data/engsvg-dataset-factory-v2')
    ap.add_argument('--out', type=Path, default=Path('/content/engsvg-v2-run'))
    ap.add_argument('--model', default='Qwen/Qwen2.5-Coder-1.5B-Instruct')
    ap.add_argument('--tasks', default=','.join(SVG_TASKS))
    ap.add_argument('--limit', type=int, default=4000, help='training rows; 0 uses every row')
    ap.add_argument('--epochs', type=float, default=1.0)
    ap.add_argument('--max-len', type=int, default=3072)
    ap.add_argument('--eval-count', type=int, default=16)
    ap.add_argument('--max-new', type=int, default=2200)
    ap.add_argument('--seed', type=int, default=17)
    ap.add_argument('--skip-base', action='store_true')
    a = ap.parse_args()
    tasks = tuple(a.tasks.split(','))

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, set_seed
    from peft import LoraConfig, get_peft_model
    from colab_train_engsvg import training_arguments

    set_seed(a.seed)
    print(f'torch {torch.__version__} | {torch.cuda.get_device_name(0)}', flush=True)
    data = load(a.data, ('train', 'validation', 'test'), tasks, a.limit or None)
    print({k: len(v) for k, v in data.items()}, 'tasks:', tasks, flush=True)

    tokenizer = AutoTokenizer.from_pretrained(a.model)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

    def encode(rows):
        feats = []
        for r in rows:
            p = tokenizer(tokenizer.apply_chat_template([{'role': 'user', 'content': r['prompt']}],
                                                        tokenize=False, add_generation_prompt=True),
                          add_special_tokens=False)['input_ids']
            t = tokenizer(r['target'] + tokenizer.eos_token, add_special_tokens=False)['input_ids']
            ids, labels = (p + t)[:a.max_len], ([-100] * len(p) + t)[:a.max_len]
            if len(labels) > len(p):
                feats.append({'input_ids': ids, 'labels': labels})
        return feats

    enc_train, enc_val = encode(data['train']), encode(data['validation'][:200])
    print(f'{len(enc_train)} encoded train rows (max_len {a.max_len})', flush=True)

    def collate(batch):
        n = max(len(b['input_ids']) for b in batch); pad = tokenizer.pad_token_id
        return {'input_ids': torch.tensor([b['input_ids'] + [pad] * (n - len(b['input_ids'])) for b in batch]),
                'attention_mask': torch.tensor([[1] * len(b['input_ids']) + [0] * (n - len(b['input_ids'])) for b in batch]),
                'labels': torch.tensor([b['labels'] + [-100] * (n - len(b['labels'])) for b in batch])}

    base = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, device_map='cuda')
    before = ({'tag': 'base', 'n': 0, 'parsed': 0, 'count': 0, 'geometry': 0, 'exact': 0, 'rows': [],
               'note': 'skipped'} if a.skip_base else
              evaluate(base, tokenizer, data['test'], a.eval_count, a.max_new, 'base', a.out))

    if hasattr(base, 'enable_input_require_grads'):
        base.enable_input_require_grads()
    base.config.use_cache = False
    model = get_peft_model(base, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                            target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
                                            task_type='CAUSAL_LM'))
    model.print_trainable_parameters()
    args = training_arguments(TrainingArguments, output_dir=str(a.out / 'checkpoints'),
                              num_train_epochs=a.epochs, per_device_train_batch_size=1,
                              gradient_accumulation_steps=8, per_device_eval_batch_size=1,
                              learning_rate=2e-4, lr_scheduler_type='cosine', logging_steps=20,
                              eval_strategy='epoch', save_strategy='no', bf16=True, report_to=[],
                              seed=a.seed, gradient_checkpointing=True, remove_unused_columns=False)
    trainer = Trainer(model=model, args=args, train_dataset=enc_train, eval_dataset=enc_val,
                      data_collator=collate)
    started = time.perf_counter()
    history = trainer.train()
    model.save_pretrained(a.out / 'adapter'); tokenizer.save_pretrained(a.out / 'adapter')
    try:
        merged = model.merge_and_unload()
    except Exception:
        merged = model
    merged.config.use_cache = True
    after = evaluate(merged, tokenizer, data['test'], a.eval_count, a.max_new, 'trained', a.out)

    summary = {'created_utc': datetime.now(timezone.utc).isoformat(), 'model': a.model,
               'tasks': tasks, 'train_rows': len(enc_train), 'epochs': a.epochs,
               'train_wall_seconds': time.perf_counter() - started,
               'train_metrics': history.metrics, 'gpu': torch.cuda.get_device_name(0),
               'scoring': 'segment-endpoint match against the reference drawing, 1.0 unit tolerance',
               'before': before, 'after': after}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for tag, r in (('base', before), ('trained', after)):
        n = max(r['n'], 1)
        print(f"{tag:8s} parsed {r['parsed']:2d}/{r['n']}  count {r['count']:2d}/{n}  "
              f"geometry {r['geometry']:2d}/{n}  exact {r['exact']:2d}/{n}")
    print('wrote', a.out / 'summary.json')


if __name__ == '__main__':
    main()
