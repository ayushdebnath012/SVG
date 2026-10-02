"""Direct Astra baseline on the controlled-editing pilot: same prompt, same scorer.

Makes billable Chat Completions requests, one sample per example, with the exact
system prompt and compact-DOM input the LoRA pilot used. Every raw response and
its token usage is retained; API failures are recorded as operational outcomes,
separately from model failures. Rerunning with the same --output resumes and
never re-bills a completed example. Set OPENAI_API_KEY, or keep it in the
repository-root .env; the key is never written to results.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import threading
import time
import urllib.error
import urllib.request

from controlled_editing_data import SYSTEM
from train_controlled_editing import load_rows, score_action

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://api.openai.com/v1/chat/completions'
# Documented list prices per million tokens, for an estimate rather than an invoice.
PRICE_INPUT, PRICE_OUTPUT = 10.0, 50.0


def api_key(project):
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    for line in (project / '.env').read_text().splitlines():
        if line.startswith('OPENAI_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"\'')
    raise SystemExit('OPENAI_API_KEY is not set')


def redact(text, key):
    return re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', str(text).replace(key, '[REDACTED]'))


def call(key, payload, attempts):
    """Return (raw response or None, error record or None, attempts used)."""
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                     headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    error = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return json.load(response), None, attempt
        except urllib.error.HTTPError as exc:
            body = redact(exc.read().decode(errors='replace'), key)
            error = {'status': 'api_error', 'http_status': exc.code, 'error': body[:1000]}
            # Rate limits and server errors are worth another attempt; client errors are not.
            if exc.code not in (408, 409, 429) and exc.code < 500:
                return None, error, attempt
            retry_after = exc.headers.get('retry-after') if exc.headers else None
            time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else 5.0 * attempt)
        except Exception as exc:
            error = {'status': 'client_error', 'error_type': type(exc).__name__, 'error': redact(exc, key)[:1000]}
            time.sleep(5.0 * attempt)
    return None, error, attempts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data/controlled-editing')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', default='gpt-6-astra')
    parser.add_argument('--effort', default='low', choices=['none', 'minimal', 'low', 'medium', 'high'])
    parser.add_argument('--max-completion-tokens', type=int, default=4096)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--attempts', type=int, default=3, help='API attempts per example for 429/5xx only')
    parser.add_argument('--limit', type=int, help='Feasibility batch: first N examples per split')
    args = parser.parse_args()
    key = api_key(ROOT.parent)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'responses').mkdir(exist_ok=True)

    protocol = {'model': args.model, 'endpoint': ENDPOINT, 'reasoning_effort': args.effort,
                'max_completion_tokens': args.max_completion_tokens, 'samples_per_example': 1,
                'system_prompt_sha256': __import__('hashlib').sha256(SYSTEM.encode()).hexdigest(),
                'scorer': 'train_controlled_editing.score_action', 'store': False,
                'notes': ['Same system prompt and compact-DOM input as the LoRA pilot; no examples, no images.',
                          'One sample per example; strict JSON exact action is the primary metric.',
                          'API errors are operational outcomes, not model capability failures; they stay in the denominator.']}
    protocol_path = args.output / 'protocol.json'
    if protocol_path.exists():
        previous = json.loads(protocol_path.read_text())
        if {k: previous.get(k) for k in protocol} != protocol:
            raise SystemExit('Existing output used a different protocol; use a fresh --output')
    else:
        protocol['created_utc'] = datetime.now(timezone.utc).isoformat()
        protocol_path.write_text(json.dumps(protocol, indent=2) + '\n')

    data = {split: load_rows(args.data / f'{split}.jsonl') for split in ('test', 'ood')}
    results_path = args.output / 'generations.jsonl'
    existing = {r['id']: r for r in load_rows(results_path)} if results_path.exists() else {}
    lock = threading.Lock()

    def run(row):
        payload = {'model': args.model,
                   'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': row['input']}],
                   'reasoning_effort': args.effort, 'max_completion_tokens': args.max_completion_tokens, 'store': False}
        started = time.perf_counter()
        raw, error, attempts = call(key, payload, args.attempts)
        record = {'id': row['id'], 'case_id': row['case_id'], 'split': row['split'], 'target': row['target'],
                  'attempts': attempts, 'wall_seconds': time.perf_counter() - started,
                  'recorded_utc': datetime.now(timezone.utc).isoformat()}
        if raw is None:
            record.update(status=error['status'], error=error, prediction='', metrics=score_action(row, ''))
        else:
            (args.output / 'responses' / f"{row['id']}.json").write_text(json.dumps(raw, indent=2) + '\n')
            choice = raw['choices'][0]
            text = choice['message'].get('content') or ''
            record.update(status='completed', model=raw.get('model'), response_id=raw.get('id'),
                          finish_reason=choice.get('finish_reason'), usage=raw.get('usage'),
                          refusal=choice['message'].get('refusal'), prediction=text, metrics=score_action(row, text))
        with lock:
            with results_path.open('a') as handle:
                handle.write(json.dumps(record) + '\n')
            existing[row['id']] = record
            done = len(existing)
        print(f"{record['id']} {record['status']} exact={record['metrics']['exact_action']} ({done})", flush=True)

    todo = []
    for split in ('test', 'ood'):
        rows = data[split][:args.limit] if args.limit else data[split]
        todo += [r for r in rows if r['id'] not in existing]
    print(f'{len(todo)} examples to run; {len(existing)} already recorded', flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run, todo))

    summary = {'protocol': protocol, 'scope': 'direct API baseline on the shared-template pilot; one sample per example'}
    usage = defaultdict(int)
    for split in ('test', 'ood'):
        rows = [existing[r['id']] for r in (data[split][:args.limit] if args.limit else data[split]) if r['id'] in existing]
        if not rows:
            continue
        entry = {'n': len(rows), 'attempted': len(rows),
                 'api_errors': sum(r['status'] != 'completed' for r in rows),
                 'finish_length': sum(r.get('finish_reason') == 'length' for r in rows)}
        for metric in ('json_valid', 'action_correct', 'exact_action', 'executor_accepts', 'unsafe_edit',
                       'fence_normalized_exact_action'):
            entry[metric] = sum(r['metrics'][metric] for r in rows) / len(rows)
        groups = defaultdict(list)
        for r in rows:
            kind = r['target']['action']
            if kind == 'style':
                kind += ':' + r['target']['attribute']
            if kind == 'reject':
                kind += ':' + r['target']['reason']
            groups[kind].append(r['metrics']['exact_action'])
        entry['exact_by_task'] = {k: {'n': len(v), 'rate': sum(v) / len(v)} for k, v in groups.items()}
        entry['wall_seconds_total'] = sum(r['wall_seconds'] for r in rows)
        summary[split] = entry
        for r in rows:
            for k, v in (r.get('usage') or {}).items():
                if isinstance(v, int):
                    usage[k] += v
            usage['reasoning_tokens'] += ((r.get('usage') or {}).get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
    summary['usage'] = dict(usage)
    summary['estimated_cost_usd'] = round(usage.get('prompt_tokens', 0) / 1e6 * PRICE_INPUT
                                          + usage.get('completion_tokens', 0) / 1e6 * PRICE_OUTPUT, 4)
    summary['completed_utc'] = datetime.now(timezone.utc).isoformat()
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'protocol'}, indent=2))


if __name__ == '__main__':
    main()
