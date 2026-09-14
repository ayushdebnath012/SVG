"""Targeted direct-OpenAI recheck of historical Astra claims; retain every attempt.

Uses the existing local credential without copying it to the research artifacts.
No retries: failed API attempts are retained separately from model failures.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        key = next(line.split('=', 1)[1].strip().strip('\"\'')
                   for line in (a.project / '.env').read_text().splitlines()
                   if line.startswith('OPENAI_API_KEY='))
    template_path = a.project / 'src/svgpatchlab/prompt_templates/generation_v1.txt'
    if not template_path.exists():
        template_path = a.project / 'svgpatchlab/prompt_templates/generation_v1.txt'
    template = template_path.read_text()
    inputs = a.project / 'data/astra_historical_inputs.json'
    previous = {}
    if inputs.exists():
        previous = {row['id']: row for row in json.loads(inputs.read_text())}
    else:
        for name in ('gen-astra-v2-physics', 'gen-astra-v3-fields'):
            path = a.project / 'runs' / name / 'results.jsonl'
            for row in map(json.loads, path.read_text().splitlines()):
                previous[row['id']] = row
    specs = [('plate_convective_edges', 'medium', 16000),
             ('plate_convective_edges', 'medium', 32000),
             ('capacitor_fringe_field', 'low', 16000),
             ('lbracket_von_mises', 'low', 16000)]
    jobs = []
    for case, effort, budget in specs:
        jobs.append({'id': f'{case}-{effort}-{budget}', 'case_id': case,
                     'effort': effort, 'max_completion_tokens': budget,
                     'prompt': template.format(prompt=previous[case]['prompt'])})
    protocol = {'created_utc': datetime.now(timezone.utc).isoformat(),
                'model': 'gpt-6-astra', 'endpoint': 'https://api.openai.com/v1/chat/completions',
                'jobs': jobs, 'workers': 2, 'samples_per_condition': 1,
                'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'notes': ['Targeted diagnostic, not a failure-rate estimate.',
                          'Original task prompts and generation wrapper retained.',
                          'The paired Robin conditions change output-token budget only.',
                          'Old report qualitative claims must be checked against saved SVGs.',
                          'Model alias and service may differ from historical runs.',
                          'API errors are not model capability failures.']}
    protocol_path = a.output / 'protocol.json'
    if protocol_path.exists(): raise ValueError('Use a fresh output folder; no silent reruns')
    protocol_path.write_text(json.dumps(protocol, indent=2) + '\n')

    def run(job):
        out = a.output / job['id']; out.mkdir()
        payload = {'model': 'gpt-6-astra', 'messages': [{'role': 'user', 'content': job['prompt']}],
                   'reasoning_effort': job['effort'],
                   'max_completion_tokens': job['max_completion_tokens'], 'store': False}
        (out / 'request.json').write_text(json.dumps(payload, indent=2) + '\n')
        started = time.perf_counter()
        result = {'id': job['id'], 'case_id': job['case_id'], 'status': 'started',
                  'started_utc': datetime.now(timezone.utc).isoformat()}
        (out / 'result.json').write_text(json.dumps(result, indent=2))
        print('START', job['id'], flush=True)
        request = urllib.request.Request(protocol['endpoint'], data=json.dumps(payload).encode(),
                  headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                raw = json.load(response)
                request_id = response.headers.get('x-request-id')
            (out / 'response.json').write_text(json.dumps(raw, indent=2) + '\n')
            choice = raw['choices'][0]; text = choice['message'].get('content') or ''
            (out / 'response.txt').write_text(text)
            svg = re.search(r'<svg\b.*?</svg>', text, re.DOTALL | re.IGNORECASE)
            if svg: (out / 'output.svg').write_text(svg.group())
            result.update(status='completed', model=raw.get('model'), response_id=raw.get('id'),
                          request_id=request_id, usage=raw.get('usage'),
                          finish_reason=choice.get('finish_reason'), has_svg=bool(svg),
                          output_chars=len(text), refusal=choice['message'].get('refusal'))
        except urllib.error.HTTPError as exc:
            raw_error = exc.read().decode(errors='replace').replace(key, '[REDACTED]')
            raw_error = re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', raw_error)
            result.update(status='api_error', http_status=exc.code, error=raw_error)
        except Exception as exc:
            result.update(status='client_error', error_type=type(exc).__name__,
                          error=str(exc).replace(key, '[REDACTED]'))
        result['wall_seconds'] = time.perf_counter() - started
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('END', job['id'], result['status'], result.get('finish_reason'), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, jobs))
    (a.output / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__': main()
