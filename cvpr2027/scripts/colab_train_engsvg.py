"""Colab GPU cell: LoRA SFT on the eng-svg trainset, evaluated with the real scorer.

Colab preinstalls torchao 0.10, and peft's LoRA dispatch raises on any version below 0.16 rather
than skipping it. Upgrading torchao pulls a newer torch and breaks the pinned 2.11, so the cell
uninstalls torchao first --- the same treatment colab_run.py already gives bitsandbytes.

Paste into a Colab GPU cell after extracting the bundle. Unlike a loss-only pilot, the evaluation
here is the same check the benchmark uses: generated SVGs are parsed, their member centrelines are
reconstructed, and the resulting frame is re-solved with the frame FEM. A drawing counts only if its
geometry, dimensions, claimed analysis and drawn-frame physics all hold.

Reports, for base and trained model on the held-out split: strict pass rate, and the component checks
separately, so a model that draws well but reports badly is not hidden behind one number.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get('ENGSVG_ROOT', '/content/engsvg'))
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))


def load(split, data, arms):
    rows = [json.loads(l) for l in (data / f'{split}.jsonl').read_text().splitlines()]
    return [r for r in rows if r['arm'] in arms]


def evaluate(model, tokenizer, rows, cad, limit, max_new, tag):
    """Generate a drawing per prompt and score it exactly as the benchmark does."""
    import torch
    model.eval()
    out = {'tag': tag, 'n': 0, 'strict_pass': 0, 'geometry_ok': 0, 'dimensions_ok': 0,
           'analysis_ok': 0, 'drawn_fem_ok': 0, 'parsed': 0, 'rows': []}
    for r in rows[:limit]:
        messages = [{'role': 'user', 'content': r['prompt']}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        ids = tokenizer(text, return_tensors='pt', truncation=True, max_length=7000).to(model.device)
        with torch.no_grad():
            gen = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                                 pad_token_id=tokenizer.eos_token_id)
        answer = tokenizer.decode(gen[0][ids['input_ids'].shape[1]:], skip_special_tokens=True)
        import re
        m = re.search(r'<svg\b.*?</svg>', answer, re.DOTALL | re.IGNORECASE)
        rec = {'parsed': bool(m)}
        out['n'] += 1
        if m:
            out['parsed'] += 1
            task = dict(model=r['model'], mapping=r['mapping'], dimensions=r['dimensions'],
                        limits=r['limits'], reference=r['reference_full'])
            row = cad.score(task, json.dumps({'svg': m.group(), 'analysis':
                                              dict(r['reference'], status='calculated')}))
            rec['geometry'] = not row['geometry_errors']
            rec['dimensions'] = not row['dimension_errors']
            rec['analysis'] = not row['analysis_errors']
            drawn = row.get('drawn_geometry_fem')
            ref = r['reference_full']
            rec['drawn_fem'] = bool(drawn) and abs(
                drawn['peak_stress_mpa'] - ref['peak_stress_mpa']) <= 2e-3 * abs(ref['peak_stress_mpa'])
            out['geometry_ok'] += rec['geometry']; out['dimensions_ok'] += rec['dimensions']
            out['analysis_ok'] += rec['analysis']; out['drawn_fem_ok'] += rec['drawn_fem']
            out['strict_pass'] += all((rec['geometry'], rec['dimensions'], rec['analysis'], rec['drawn_fem']))
        out['rows'].append(rec)
        print('.', end='', flush=True)
    print()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', type=Path, default=ROOT / 'data/eng-svg-trainset')
    ap.add_argument('--out', type=Path, default=Path('/content/engsvg-run'))
    ap.add_argument('--model', default='Qwen/Qwen2.5-Coder-1.5B-Instruct')
    ap.add_argument('--arms', default='text2svg', help='comma separated: text2svg,svg2svg')
    ap.add_argument('--epochs', type=float, default=2.0)
    ap.add_argument('--max-len', type=int, default=4096)
    ap.add_argument('--eval-count', type=int, default=24)
    ap.add_argument('--max-new', type=int, default=2600)
    ap.add_argument('--seed', type=int, default=17)
    ap.add_argument('--skip-base', action='store_true',
                    help='skip the pre-training baseline (it is deterministic; reuse an earlier one)')
    a = ap.parse_args()
    arms = tuple(a.arms.split(','))
    a.out.mkdir(parents=True, exist_ok=True)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, set_seed
    from peft import LoraConfig, get_peft_model
    import cad_astra_benchmark as cad

    set_seed(a.seed)
    print(torch.__version__, torch.cuda.get_device_name(0), flush=True)
    train, val, test = (load(s, a.data, arms) for s in ('train', 'validation', 'test'))
    print(f'{len(train)} train / {len(val)} val / {len(test)} test  arms={arms}', flush=True)

    tokenizer = AutoTokenizer.from_pretrained(a.model)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

    def encode(rows):
        feats = []
        for r in rows:
            prompt = tokenizer.apply_chat_template([{'role': 'user', 'content': r['prompt']}],
                                                   tokenize=False, add_generation_prompt=True)
            p = tokenizer(prompt, add_special_tokens=False)['input_ids']
            t = tokenizer(r['target'] + tokenizer.eos_token, add_special_tokens=False)['input_ids']
            ids = (p + t)[:a.max_len]
            labels = ([-100] * len(p) + t)[:a.max_len]
            if len(labels) > len(p):                       # keep only examples with a visible target
                feats.append({'input_ids': ids, 'labels': labels})
        return feats

    enc_train, enc_val = encode(train), encode(val)
    print(f'{len(enc_train)} encoded train examples, max len {a.max_len}', flush=True)

    def collate(batch):
        n = max(len(b['input_ids']) for b in batch)
        pad = tokenizer.pad_token_id
        return {'input_ids': torch.tensor([b['input_ids'] + [pad] * (n - len(b['input_ids'])) for b in batch]),
                'attention_mask': torch.tensor([[1] * len(b['input_ids']) + [0] * (n - len(b['input_ids'])) for b in batch]),
                'labels': torch.tensor([b['labels'] + [-100] * (n - len(b['labels'])) for b in batch])}

    base = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, device_map='cuda')
    if a.skip_base:
        before = {'tag': 'base', 'n': 0, 'strict_pass': 0, 'geometry_ok': 0, 'dimensions_ok': 0,
                  'analysis_ok': 0, 'drawn_fem_ok': 0, 'parsed': 0, 'rows': [],
                  'note': 'skipped; greedy decoding makes this deterministic, so an earlier run stands'}
        print('--- base model evaluation skipped ---', flush=True)
    else:
        print('--- base model, before training ---', flush=True)
        before = evaluate(base, tokenizer, test, cad, a.eval_count, a.max_new, 'base')
        print(json.dumps({k: v for k, v in before.items() if k != 'rows'}, indent=2), flush=True)

    model = get_peft_model(base, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                            target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
                                            task_type='CAUSAL_LM'))
    model.print_trainable_parameters()
    args = TrainingArguments(output_dir=str(a.out / 'checkpoints'), num_train_epochs=a.epochs,
                             per_device_train_batch_size=1, gradient_accumulation_steps=8,
                             per_device_eval_batch_size=1, learning_rate=2e-4, lr_scheduler_type='cosine',
                             warmup_ratio=0.05, logging_steps=10, eval_strategy='epoch',
                             save_strategy='no', bf16=True, report_to=[], seed=a.seed,
                             gradient_checkpointing=True)
    trainer = Trainer(model=model, args=args, train_dataset=enc_train, eval_dataset=enc_val,
                      data_collator=collate)
    started = time.perf_counter()
    history = trainer.train()
    wall = time.perf_counter() - started
    model.save_pretrained(a.out / 'adapter')
    tokenizer.save_pretrained(a.out / 'adapter')

    print('--- trained model ---', flush=True)
    after = evaluate(model, tokenizer, test, cad, a.eval_count, a.max_new, 'trained')
    print(json.dumps({k: v for k, v in after.items() if k != 'rows'}, indent=2), flush=True)

    summary = {'created_utc': datetime.now(timezone.utc).isoformat(), 'model': a.model, 'arms': arms,
               'epochs': a.epochs, 'max_len': a.max_len, 'seed': a.seed,
               'train': len(enc_train), 'validation': len(enc_val), 'test_evaluated': before['n'],
               'train_wall_seconds': wall, 'train_metrics': history.metrics,
               'gpu': torch.cuda.get_device_name(0),
               'scoring': ('cad_astra_benchmark.score plus a 2e-3 gate on the FEM re-solve of the '
                           'reconstructed drawn frame; strict_pass requires all four'),
               'before': before, 'after': after}
    (a.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for tag, r in (('base', before), ('trained', after)):
        n = max(r['n'], 1)
        print(f"{tag:8s} parsed {r['parsed']}/{r['n']}  geometry {r['geometry_ok']}/{n}  "
              f"dimensions {r['dimensions_ok']}/{n}  analysis {r['analysis_ok']}/{n}  "
              f"drawnFEM {r['drawn_fem_ok']}/{n}  STRICT {r['strict_pass']}/{n}")
    print('wrote', a.out / 'summary.json')


if __name__ == '__main__':
    main()
