"""Build a bounded, family-disjoint mechanical CAD edit dataset from BenchCAD.

Run with the MLX training environment (pyarrow). CAD execution is delegated to
the existing cad-runtime interpreter. No external benchmark answers are trained.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

SYSTEM = ('Edit the supplied mechanical CadQuery program. Return only a JSON object '
          'with line (1-based), old (exact source line), and new (replacement line). '
          'Change only the requested numeric feature argument. Preserve all other lines.')
EXCLUDE = ('pipe', 'duct', 'fitting', 'manifold', 'valve', 'hose', 'resistor', 'circuit', 'pcb')


def digest(x):
    return hashlib.sha256(x.encode()).hexdigest()


def normalized(code):
    return ast.dump(ast.parse(code), include_attributes=False)


def candidates(row):
    tree = ast.parse(row['code'])
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    operations = [n.func.attr for n in calls]
    if row['difficulty'] != 'hard' or len(calls) < 8:
        return []
    # Require compositional geometry, rather than just a decorated primitive.
    if not set(operations) & {'union', 'cut', 'sweep', 'loft', 'revolve'}:
        return []
    lines = row['code'].splitlines()
    edits = []
    for n in sorted(calls, key=lambda n: (n.lineno, n.col_offset)):
        if n.func.attr not in {'hole', 'fillet', 'chamfer', 'extrude'} or not n.args:
            continue
        arg = n.args[0]
        if not isinstance(arg, ast.Constant) or type(arg.value) not in (float, int) or arg.value <= 0:
            continue
        if arg.lineno != arg.end_lineno:
            continue
        old = lines[arg.lineno - 1]
        # AST offsets are byte offsets, not Unicode character offsets.
        raw = old.encode()
        for factor in (0.85, 1.15):
            value = round(arg.value * factor, 4)
            new = (raw[:arg.col_offset] + str(value).encode() + raw[arg.end_col_offset:]).decode()
            changed = lines.copy()
            changed[arg.lineno - 1] = new
            target = dict(line=arg.lineno, old=old, new=new)
            instruction = (f'At line {arg.lineno}, change the first numeric argument of '
                           f'{n.func.attr} from {arg.value} to {value}. Keep every other '
                           'feature, location, orientation and argument unchanged.')
            edits.append(dict(operation=n.func.attr, instruction=instruction,
                              target=json.dumps(target, separators=(',', ':')),
                              edited_code='\n'.join(changed), **target))
        # Two edits per source part, kept in the same family partition.
        break
    return edits


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cad-python', type=Path, required=True)
    p.add_argument('--parts', type=int, default=80)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Use a fresh output directory')
    import pyarrow.parquet as pq
    benchmark = pq.read_table(a.source / 'edit-bench.parquet', columns=['family', 'orig_code', 'gt_code']).to_pylist()
    heldout = {digest(normalized(r[k])) for r in benchmark for k in ('orig_code', 'gt_code')}
    # Mask literal values too, to exclude benchmark program-template variants.
    def skeleton(code):
        t = ast.parse(code)
        for n in ast.walk(t):
            if isinstance(n, ast.Constant) and type(n.value) in (int, float):
                n.value = 0
        return digest(ast.dump(t, include_attributes=False))
    heldout_templates = {skeleton(r[k]) for r in benchmark for k in ('orig_code', 'gt_code')}
    source_rows = []
    files = sorted(a.source.glob('code-gen*.parquet'))
    for f in files:
        source_rows.extend(pq.read_table(f, columns=['stem', 'family', 'difficulty', 'standard', 'code']).to_pylist())
    families = sorted({r['family'] for r in source_rows if not any(x in r['family'].lower() for x in EXCLUDE)}, key=digest)
    family_split = {f: ('test' if i % 10 == 0 else 'validation' if i % 10 == 1 else 'train') for i, f in enumerate(families)}
    a.output.mkdir(parents=True)
    selected = []
    excluded = Counter()
    counts = Counter()
    seen = set()
    for r in sorted(source_rows, key=lambda r: digest(r['stem'])):
        if any(x in r['family'].lower() for x in EXCLUDE):
            excluded['out_of_scope'] += 1
            continue
        h = digest(normalized(r['code']))
        if h in heldout or skeleton(r['code']) in heldout_templates:
            excluded['external_benchmark_template_overlap'] += 1
            continue
        if h in seen:
            excluded['duplicate_code'] += 1
            continue
        edits = candidates(r)
        if not edits:
            excluded['complexity_or_edit_filter'] += 1
            continue
        split = family_split[r['family']]
        cap = a.parts if split == 'train' else max(12, a.parts // 5)
        if counts[split] >= cap or counts[r['family']] >= 4:
            continue
        seen.add(h)
        counts[split] += 1
        counts[r['family']] += 1
        selected.append(dict(**r, component_id=h, split=split, edits=edits))
    (a.output / 'candidates.json').write_text(json.dumps(selected, indent=2))
    worker = Path(__file__).with_name('verify_mechanical_cad_edits.py')
    with (a.output / 'verification.log').open('w') as log:
        result = subprocess.run([str(a.cad_python), str(worker), str(a.output)], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'CAD verification failed: {a.output}/verification.log')
    verified = [json.loads(line) for line in (a.output / 'verified.jsonl').read_text().splitlines()]
    split_rows = {s: [] for s in ('train', 'validation', 'test')}
    for r in verified:
        r['input'] = 'Original CAD program:\n' + r['code'] + '\nEdit instruction:\n' + r['instruction']
        split_rows[r['split']].append(r)
    mlxpath = a.output / 'mlx'
    mlxpath.mkdir()
    for split, rows in split_rows.items():
        if not rows:
            raise ValueError(f'Empty {split} after verification')
        (a.output / f'{split}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        chats = [dict(messages=[dict(role='system', content=SYSTEM), dict(role='user', content=r['input']),
                                dict(role='assistant', content=r['target'])]) for r in rows]
        name = 'valid' if split == 'validation' else split
        (mlxpath / f'{name}.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in chats))
    meta = json.loads((a.source / 'hub-metadata.json').read_text())
    manifest = dict(source='BenchCAD/BenchCAD', revision=meta['sha'], license='CC-BY-4.0',
                    attribution='BenchCAD: Zhang et al., 2026, https://huggingface.co/datasets/BenchCAD/BenchCAD',
                    system=SYSTEM, source_rows=len(source_rows), excluded=dict(excluded),
                    counts={s: len(rs) for s, rs in split_rows.items()},
                    families={s: sorted({r['family'] for r in rs}) for s, rs in split_rows.items()},
                    split_policy='Whole family holdout before edit augmentation; exact AST deduplication; external BenchCAD edit program templates excluded regardless of literal values.',
                    verification='Both solids valid and positive volume; changed volume; original and edited STEP plus four linked SVG projections. This checks executable geometry, not engineering strength.',
                    fem_status='not_evaluated_missing_material_loads_supports_and_units_contract',
                    limitations=['Synthetic single-feature numeric edits with explicit source-line localization.',
                                 'Training input is CAD code linked to SVG views, not image or SVG perception.',
                                 'Geometric equivalence across different program templates and external benchmark ancestry not proven.',
                                 'Family holdout can still share operation patterns; standards compliance not independently certified.'],
                    files={s: hashlib.sha256((a.output / f'{s}.jsonl').read_bytes()).hexdigest() for s in split_rows},
                    source_files={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files + [a.source / 'edit-bench.parquet']})
    (a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ('counts', 'families', 'excluded')}, indent=2))


if __name__ == '__main__':
    main()
