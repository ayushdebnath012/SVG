"""CUDA smoke check: reload each saved adapter and run six held-out actions."""
import argparse
import gc
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runs', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from controlled_editing_data import SYSTEM
    from train_controlled_editing import load_rows, score_action
    results = []
    for seed in (17, 29, 41):
        run = args.runs / f'seed-{seed}'
        manifest = json.loads((run / 'run_manifest.json').read_text())
        assert manifest['status'] == 'completed'
        tokenizer = AutoTokenizer.from_pretrained(run / 'adapter')
        base = AutoModelForCausalLM.from_pretrained(
            manifest['model'], revision=manifest['model_revision'],
            device_map={'': 0}, torch_dtype=torch.float16)
        model = PeftModel.from_pretrained(base, run / 'adapter').eval()
        selected = {}
        for row in load_rows(run / 'data' / 'test.jsonl'):
            target = row['target']
            key = (target['action'], target.get('attribute'), target.get('reason'))
            selected.setdefault(key, row)
        assert len(selected) == 6
        for row in selected.values():
            prompt = tokenizer.apply_chat_template([
                {'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': row['input']}],
                tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt, return_tensors='pt').to('cuda')
            with torch.inference_mode():
                generated = model.generate(**inputs, max_new_tokens=128,
                    do_sample=False, pad_token_id=tokenizer.eos_token_id)
            text = tokenizer.decode(generated[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            score = score_action(row, text)
            results.append({'seed': seed, 'id': row['id'], 'prediction': text,
                            'target': row['target'], 'metrics': score})
            print(seed, row['id'], score['exact_action'], flush=True)
        del model, base, inputs, generated
        gc.collect(); torch.cuda.empty_cache()
    report = {'scope': 'saved-adapter reload smoke check; six actions per seed',
              'n': len(results), 'exact': sum(r['metrics']['exact_action'] for r in results),
              'results': results}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    assert report['exact'] == report['n'] == 18, 'Reload predictions require inspection'
    print('ADAPTER RELOAD VERIFIED', flush=True)


if __name__ == '__main__':
    main()
