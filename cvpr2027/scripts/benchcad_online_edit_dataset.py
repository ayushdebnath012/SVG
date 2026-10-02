"""Repurpose published BenchCAD edit pairs with an explicit local family split.

This is not the official held-out benchmark protocol. All training starts from a
fresh base model, not the previous source-code-generation adapter.
"""
import argparse
import ast
from collections import Counter
import difflib
import hashlib
import io
import json
from pathlib import Path
import sys
import tokenize

SYSTEM = ('Apply the instruction to the mechanical CadQuery program. Return only JSON '
          'with key edits: a list of objects containing start (zero-based original line '
          'index), delete (number of original lines to remove), and insert (list of '
          'replacement lines). Coordinates refer to the original program. Preserve '
          'unrelated geometry. Do not include Markdown or explanation.')
EXCLUDE = ('pipe', 'duct', 'fitting', 'manifold', 'valve', 'hose', 'resistor', 'circuit', 'pcb')


def sha(x):
    return hashlib.sha256(x.encode()).hexdigest()


def canonical(code):
    ast.parse(code)
    tokens = [t for t in tokenize.generate_tokens(io.StringIO(code).readline) if t.type != tokenize.COMMENT]
    return '\n'.join(line.rstrip() for line in tokenize.untokenize(tokens).splitlines() if line.strip())


def patch(before, after):
    edits = []
    a, b = before.splitlines(), after.splitlines()
    for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != 'equal':
            edits.append(dict(start=i, delete=j-i, insert=b[k:l]))
    return dict(edits=edits)


def apply(before, prediction):
    if not isinstance(prediction, dict) or set(prediction) != {'edits'} or not isinstance(prediction['edits'], list):
        raise ValueError('Invalid patch schema')
    lines = before.splitlines()
    result = []
    cursor = 0
    previous = -1
    for e in prediction['edits']:
        if not isinstance(e, dict) or set(e) != {'start', 'delete', 'insert'}:
            raise ValueError('Invalid edit schema')
        start, delete, insert = e['start'], e['delete'], e['insert']
        if type(start) is not int or type(delete) is not int or delete < 0 or start < cursor or start <= previous or start + delete > len(lines):
            raise ValueError('Overlapping, unordered or out-of-range edit')
        if not isinstance(insert, list) or any(not isinstance(x, str) or '\n' in x or '\r' in x for x in insert):
            raise ValueError('Invalid replacement lines')
        result.extend(lines[cursor:start])
        result.extend(insert)
        cursor = start + delete
        previous = start
    result.extend(lines[cursor:])
    code = '\n'.join(result)
    ast.parse(code)
    return code


def main():
    # Long procedural CAD chains exceed Python's default unparser recursion.
    sys.setrecursionlimit(10000)
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Use a fresh output directory')
    import pyarrow.parquet as pq
    source = pq.read_table(a.source).to_pylist()
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        x, y = find(x), find(y)
        if x != y:
            parent[max(x, y)] = min(x, y)
    # Connect source families sharing either source or target geometry program.
    # Numerical values are masked too, so template variants cannot cross splits.
    owner = {}
    kept = []
    excluded = Counter()
    for r in source:
        if any(x in r['family'].lower() for x in EXCLUDE):
            excluded['out_of_scope'] += 1
            continue
        before, after = canonical(r['orig_code']), canonical(r['gt_code'])
        if before == after:
            excluded['no_ast_edit'] += 1
            continue
        find(r['family'])
        for code in (before, after):
            t = ast.parse(code)
            for n in ast.walk(t):
                if isinstance(n, ast.Constant) and type(n.value) in (int, float):
                    n.value = 0
            key = sha(ast.dump(t, include_attributes=False))
            if key in owner:
                union(r['family'], owner[key])
            owner[key] = r['family']
        kept.append((r, before, after))
    groups = sorted({find(r['family']) for r, _, _ in kept}, key=sha)
    splits = {g: ('test' if i % 10 in (0, 1) else 'validation' if i % 10 == 2 else 'train') for i, g in enumerate(groups)}
    out = {s: [] for s in ('train', 'validation', 'test')}
    seen = set()
    a.output.mkdir(parents=True)
    for r, before, after in kept:
        rid = sha(before + '\n' + r['instruction'] + '\n' + after)
        if rid in seen:
            excluded['duplicate_pair'] += 1
            continue
        seen.add(rid)
        target = patch(before, after)
        assert apply(before, target) == after
        group = find(r['family'])
        split = splits[group]
        item = dict(id=rid, source_record_id=r['record_id'], family=r['family'], component_id=group,
                    category=r['category'], edit_type=r['edit_type'], instruction=r['instruction'],
                    code=before, edited_code=after, target=json.dumps(target, separators=(',', ':')),
                    input='Original CAD program:\n' + before + '\nEdit instruction:\n' + r['instruction'])
        if split == 'test':
            # Use the author's supplied STEP rather than trusting another local
            # reconstruction of the ground-truth program.
            dest = a.output / 'reference-step' / (rid + '.step')
            dest.parent.mkdir(exist_ok=True)
            dest.write_bytes(r['gt_step'])
            item['reference_step'] = str(dest.relative_to(a.output))
            item['reference_step_sha256'] = hashlib.sha256(r['gt_step']).hexdigest()
        out[split].append(item)
    for s, rs in out.items():
        rs.sort(key=lambda r: sha(r['source_record_id']))
        (a.output / f'{s}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rs))
    m = dict(source='https://huggingface.co/datasets/BenchCAD/BenchCAD', upstream_config='edit-bench',
             upstream_split='edit_bench', upstream_rows=len(source), revision='5919f578ab09ec283603a082fab07c7639ab56eb',
             license='CC-BY-4.0', attribution='Zhang et al. 2026, BenchCAD',
             source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(), system=SYSTEM,
             counts={s:len(rs) for s,rs in out.items()}, excluded=dict(excluded),
             families={s:sorted({r['family'] for r in rs}) for s,rs in out.items()},
             categories={s:dict(Counter(r['category'] for r in rs)) for s,rs in out.items()},
             split_policy='70/10/20 family/template-component split. All numeric-masked source/target AST templates linked before assigning groups. Hash-ranked deterministic group split.',
             protocol='Local re-partition of a published benchmark for training and evaluation; NOT official leaderboard protocol. Fresh base weights; prior mechanical adapter not reused.',
             fem='not_evaluated_missing_physical_specification',
             files={s:hashlib.sha256((a.output/f'{s}.jsonl').read_bytes()).hexdigest() for s in out})
    (a.output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(json.dumps({k:m[k] for k in ('counts','excluded','categories')},indent=2))


if __name__ == '__main__':
    main()
