"""Live benchmark providers: one shared API ledger, a compact Astra planner and an Astra rendered-view semantic check.

The ledger is the hard cap for a whole benchmark run. Every request reserves a worst-case cost before dispatch
(input bytes as a conservative token bound at the cache-write rate, plus the full completion cap) and is settled at the verified list
rates ($10 input, $1 cached input, $12.50 cache-write, $50 output per million tokens), so concurrent tasks can never
exceed the cap. A per-task budget paces spending across tasks. Requests and responses are saved; nothing is retried.
"""
import base64, json, os, threading, time, urllib.error, urllib.request
from pathlib import Path
from .core import Memory
from .providers import AstraPlanner

ENDPOINT = 'https://api.openai.com/v1/chat/completions'
IMAGE_TOKENS = 1500  # reservation per attached image
# A backend fixes the model, sampling and completion caps. Astra is billed; a self-hosted open model costs nothing.
ASTRA = dict(name='gpt-6-astra', endpoint=ENDPOINT, model='gpt-6-astra', params={'reasoning_effort': 'low', 'store': False},
             max_key='max_completion_tokens', tokens={'decompose': 1500, 'generate': 2500, 'semantic': 1000, 'single': 6000},
             priced=True)


def gemini_backend(model, rpm=10):
    """Google Gemini through its OpenAI-compatible endpoint (free tier: throttled, per-minute 429s are retried)."""
    return dict(name=model, endpoint='https://generativelanguage.googleapis.com/v1beta/openai/chat/completions', model=model,
                params={'reasoning_effort': 'low'}, max_key='max_tokens', key_env='GEMINI_API_KEY', rpm=rpm, retry=True,
                tokens={'decompose': 4096, 'generate': 8192, 'semantic': 4096, 'single': 8192}, priced=False)


class ApiRejected(Exception):
    def __init__(self, code, body):
        super().__init__(f'HTTP {code}: {body[:200]}')
        self.code, self.body = code, body


_pace = {'lock': threading.Lock(), 'next': 0.}


def post(backend, key, body, timeout):
    """One request: paced to the backend's requests-per-minute; rate-limit and transient errors are retried."""
    for attempt in range(8):
        if backend.get('rpm'):
            with _pace['lock']:
                wait = _pace['next'] - time.monotonic()
                _pace['next'] = max(_pace['next'], time.monotonic()) + 60. / backend['rpm']
            if wait > 0:
                time.sleep(wait)
        req = urllib.request.Request(backend['endpoint'], data=json.dumps(body).encode(),
                                     headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            text = error.read().decode(errors='replace')[:1000]
            daily = any(k in text for k in ('PerDay', 'insufficient_quota', 'credit_balance', 'free_tier_requests')) or 'per day' in text.lower()
            if backend.get('retry') and (error.code in (500, 502, 503, 504) or (error.code == 429 and not daily)) and attempt < 7:
                time.sleep(min(120, 15 * 2 ** attempt))
                continue
            raise ApiRejected(error.code, text)
        except (TimeoutError, OSError) as error:  # socket timeouts and dropped connections on an overloaded service
            if backend.get('retry') and attempt < 7:
                time.sleep(min(120, 15 * 2 ** attempt))
                continue
            raise
    raise ApiRejected(429, 'retries exhausted')


def open_backend(endpoint, model):
    """OpenAI-compatible self-hosted server (vLLM); Qwen thinking-mode sampling, reasoning returned separately."""
    return dict(name=model, endpoint=endpoint, model=model, params={'temperature': 0.6, 'top_p': 0.95, 'top_k': 20},
                max_key='max_tokens', tokens={'decompose': 8192, 'generate': 16384, 'semantic': 12288, 'single': 16384},
                priced=False)


class Ledger:
    def __init__(self, path, cap):
        self.path, self.cap, self.lock = Path(path), float(cap), threading.Lock()
        state = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.spent, self.calls, self.outstanding = float(state.get('spent', 0)), int(state.get('calls', 0)), 0.
        self.dead = None  # set when the account rejects requests for quota; the whole run stops

    def reserve(self, amount):
        with self.lock:
            if self.dead or self.spent + self.outstanding + amount > self.cap:
                return False
            self.outstanding += amount
            return True

    def settle(self, reserved, actual):
        with self.lock:
            self.outstanding -= reserved
            self.spent += actual
            self.calls += 1
            self.path.write_text(json.dumps(dict(spent=self.spent, calls=self.calls, cap=self.cap)))


def cost(usage):
    details = usage.get('prompt_tokens_details') or {}
    cached, writes = details.get('cached_tokens', 0), details.get('cache_write_tokens', details.get('cache_creation_tokens', 0))
    prompt, completion = usage['prompt_tokens'], usage['completion_tokens']
    return (max(0, prompt - cached - writes) * 10 + cached + writes * 12.5 + completion * 50) / 1e6


def parse_object(content):
    text = content.strip()
    start, end = text.find('{'), text.rfind('}')
    result = json.loads(text[start:end + 1])
    if not isinstance(result, dict):
        raise ValueError('Expected JSON object')
    return result


def compact(verdict):
    """Stage statuses, reasons and failed checks only; raw FEM fields stay out of prompts."""
    out = {}
    for stage, v in (verdict.get('stages') or {}).items():
        d = {'status': v.get('status')}
        if v.get('reason'):
            d['reason'] = str(v['reason'])[:200]
        failed = [c for c in v.get('checks', []) if not c.get('ok')]
        if failed:
            d['failed_checks'] = [{k: c[k] for k in ('metric', 'missing', 'value', 'max') if k in c} for c in failed][:5]
        out[stage] = d
    return out


class LivePlanner(AstraPlanner):
    def __init__(self, out, ledger, task_budget, max_calls=12, key=None, timeout=600, backend=None):
        self.backend = backend or ASTRA
        key_env = self.backend.get('key_env', 'OPENAI_API_KEY' if self.backend['priced'] else None)
        self.key = key or (os.environ.get(key_env) if key_env else 'local')
        if not self.key:
            raise ValueError(f'Set {key_env} in the execution environment')
        self.out = Path(out); self.out.mkdir(parents=True, exist_ok=True)
        self.ledger, self.budget, self.max_calls, self.timeout = ledger, task_budget, max_calls, timeout
        self.max_tokens, self.deadline, self.lock = 2500, float('inf'), threading.Lock()
        self.accounting = {'mode': 'live_astra', 'api_calls': 0, 'cost_usd': 0., 'budget_usd': task_budget, 'refused': 0}

    def request(self, kind, messages, max_tokens, images=0):
        if time.monotonic() >= self.deadline:
            raise StopIteration
        b = self.backend
        max_tokens = b['tokens'].get(kind, max_tokens)
        body = {'model': b['model'], 'messages': messages, **b['params'], b['max_key']: max_tokens}
        text_bytes = len(json.dumps([m if isinstance(m.get('content'), str) else
                                     {**m, 'content': [c for c in m['content'] if c.get('type') == 'text']} for m in messages]).encode())
        reserve = ((text_bytes + 512 + images * IMAGE_TOKENS) * 12.5 + max_tokens * 50) / 1e6 if b['priced'] else 0.
        with self.lock:
            if self.accounting['api_calls'] >= self.max_calls or self.accounting['cost_usd'] + reserve > self.budget:
                self.accounting['refused'] += 1
                raise StopIteration
            self.accounting['api_calls'] += 1
            n = self.accounting['api_calls']
        if not self.ledger.reserve(reserve):
            self.accounting['refused'] += 1
            raise StopIteration
        path = self.out / f'call-{n:03d}-{kind}.json'
        saved = {'kind': kind, 'status': 'reserved', 'reserved_usd': reserve,
                 'request': {**body, 'messages': [m if isinstance(m.get('content'), str) else
                             {**m, 'content': [c if c.get('type') == 'text' else {'type': 'image_url', 'image_url': '<png omitted>'}
                                               for c in m['content']]} for m in messages]}}
        path.write_text(json.dumps(saved, indent=1))
        actual = reserve  # an unknown dispatch outcome keeps its worst-case reservation
        try:
            reply = post(b, self.key, body, self.timeout)
            usage = reply.get('usage') or {}
            if not b['priced']:
                actual = 0.
            elif 'prompt_tokens' in usage and 'completion_tokens' in usage:
                actual = cost(usage)
            choice = reply['choices'][0]
            content = choice['message'].get('content') or ''
            saved.update(status='completed', usage=usage, cost_usd=actual, finish_reason=choice.get('finish_reason'), response=content)
            if choice.get('finish_reason') != 'stop':
                raise ValueError('Incomplete model response')
            return content
        except ApiRejected as error:
            saved.update(status='rejected', error_type='HTTPError', http_status=error.code, error=error.body[:500])
            if 400 <= error.code < 500:
                actual = 0.  # the API rejected the request; nothing was generated or billed
            if any(k in error.body for k in ('insufficient_quota', 'credit_balance_exhausted', 'PerDay', 'free_tier_requests')) or error.code in (401, 403):
                self.ledger.dead = 'quota or authorization: ' + error.body[:120]
            raise
        except Exception as error:
            saved.update(status=saved.get('status') if saved.get('status') == 'completed' else 'failed', error_type=type(error).__name__,
                         error=str(error)[:300])
            raise
        finally:
            self.ledger.settle(reserve, actual)
            with self.lock:
                self.accounting['cost_usd'] += actual
            saved['cost_usd'] = actual
            path.write_text(json.dumps(saved, indent=1))

    def call(self, system, body):
        kind = 'decompose' if 'Decompose' in system else 'generate'
        self.last_content = ''
        self.last_content = self.request(kind, [{'role': 'system', 'content': system}, {'role': 'user', 'content': json.dumps(body)}],
                                         self.max_tokens)
        return parse_object(self.last_content)

    def decompose(self, task, experiences):
        try:
            return super().decompose(task, experiences)
        except (ValueError, KeyError, TypeError):  # an unparseable plan falls back to the whole instruction
            return {'steps': [task['instruction']], 'source': 'fallback: unparseable decomposition'}

    def generate(self, task, plan, parent, observations, experiences, repairs, alternatives, strategy, diagnosis):
        try:
            return super().generate(task, plan, parent, compact(observations), experiences, repairs, alternatives, strategy,
                                    [{'stage': d.get('stage'), **compact({'stages': {d.get('stage'): d}})[d.get('stage')]} for d in diagnosis])
        except (ValueError, KeyError, TypeError):  # keep the raw reply as a node; the verifier fails and diagnoses it
            self.last_hypothesis = 'unparseable response'
            return self.last_content or '{}'


class ViewSemantic:
    """Astra judges whether rendered views of the edited solid implement the instruction; cached per candidate."""
    PROMPT = ('Edit instruction: {instruction}\n\nThe image shows the ORIGINAL part (left) and the EDITED part (right), '
              'isometric views (top row) and top views (bottom row). Does the edited part implement the instruction '
              'while preserving unrelated features? Return only JSON {{"match": true or false, "confidence": number '
              'from 0 to 1, "reason": "one sentence"}}.')

    def __init__(self, planner, folder, render):
        self.planner, self.folder, self.render, self.cache = planner, Path(folder), render, {}

    def __call__(self, task, candidate, tools):
        if candidate in self.cache:
            return self.cache[candidate]
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from cad_edit_contracts import apply
        from cad_edit_verifier import extract
        _, patch = extract(candidate)
        code = apply(task['code'], patch, 'cadquery')
        png = self.folder / f'semantic-{len(self.cache):02d}.png'
        if not self.render(task['code'], code, png):
            return {'status': 'UNKNOWN', 'reason': 'Render failed'}
        content = [{'type': 'text', 'text': self.PROMPT.format(instruction=task['instruction'])},
                   {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + base64.b64encode(png.read_bytes()).decode()}}]
        try:
            answer = parse_object(self.planner.request('semantic', [
                {'role': 'system', 'content': 'You verify mechanical CAD edits from rendered views.'},
                {'role': 'user', 'content': content}], 1000, images=1))
        except StopIteration:
            return {'status': 'UNKNOWN', 'reason': 'API budget exhausted'}
        confidence = min(1., max(0., float(answer.get('confidence', 0))))
        verdict = {'status': 'PASS' if answer.get('match') is True and confidence >= .5 else 'FAIL',
                   'confidence': confidence, 'reason': str(answer.get('reason', ''))[:300],
                   'basis': 'Astra rendered-view judgement', 'image': png.name}
        self.cache[candidate] = verdict
        return verdict


class LockedMemory(Memory):
    """Online memory shared by concurrent tasks: each task reads a snapshot at its start; stores are serialized."""
    lock = threading.Lock()

    def __init__(self, path, mode='online'):
        with self.lock:
            super().__init__(path, mode)

    def store(self, task, node, events):
        with self.lock:
            return super().store(task, node, events)
