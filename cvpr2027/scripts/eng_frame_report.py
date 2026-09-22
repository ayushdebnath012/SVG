"""Aggregate every engineering-elevation sample into one table, classified by what actually happened.

`cad_astra_benchmark.score` files a declined analysis (`status: "unavailable"`, null values) under
`format_errors`, which the admission rule then excludes. That discards the most informative outcome
in this study, because declining is a distinct behaviour from computing a wrong number. This report
separates three outcomes:

    computed_correct  every checked quantity within tolerance of the frame FEM
    computed_wrong    a number was printed on the drawing and it is outside tolerance
    declined          the model returned status "unavailable" and no numbers

A unit-only format complaint is withdrawn when the drawing declares its units once, which is normal
drafting practice; see `eng_frame_bench.adjudicate`.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
import cad_astra_benchmark as B  # noqa: E402
from eng_frame_bench import UNITS_NOTE, indeterminacy  # noqa: E402

# Every run of the dimensioned-elevation task, with the manifest it was scored against.
RUNS = [
    ('pilot screen 20 Sep', 'runs/astra-cad-20260920/screen', 'data/cad-astra-pilot'),
    ('pilot confirm building_edit', 'runs/cad-building-edit-confirm-20260922', 'data/cad-astra-pilot'),
    ('EngFrame screen', 'runs/eng-frame-screen-20260922', 'data/eng-frame-bench'),
    ('EngFrame confirm threebay', 'runs/eng-frame-threebay-confirm-20260922', 'data/eng-frame-bench'),
    ('EngFrame XL screen', 'runs/eng-frame-xl-20260922', 'data/eng-frame-bench-xl'),
    ('EngFrame XL confirm deg27', 'runs/eng-frame-xl-confirm-20260922', 'data/eng-frame-bench-xl'),
    ('EngFrame XL confirm 20-member', 'runs/eng-frame-xl-confirm2-20260922', 'data/eng-frame-bench-xl'),
]


def classify(task, folder):
    """One sample -> (outcome, detail). Truncated and errored attempts are excluded, never failed."""
    result = json.loads((folder / 'result.json').read_text())
    if result.get('status') != 'completed':
        return 'excluded_api', result.get('status')
    if result.get('finish_reason') != 'stop':
        return 'excluded_truncated', result.get('finish_reason')
    text = (folder / 'response.txt').read_text() if (folder / 'response.txt').exists() else ''
    try:
        obj = B.read_response(text)
        analysis = obj['analysis']
    except Exception as exc:
        return 'excluded_format', type(exc).__name__
    if analysis.get('status') == 'unavailable' or all(
            analysis.get(k) is None for k in ('ux_mm', 'uy_mm', 'peak_stress_mpa')):
        return 'declined', analysis.get('reason', '')[:160]
    row = B.score(task, text)
    if row.get('analysis_errors'):
        worst = max(row['analysis_errors'], key=lambda e: e['absolute_error'] / max(e['tolerance'], 1e-9))
        return 'computed_wrong', (f"{worst['quantity']} = {worst['actual']} vs {worst['expected']:.4f} "
                                  f"(tolerance {worst['tolerance']:.4f})")
    hard = [k for k in ('geometry_errors', 'dimension_errors', 'visible_result_errors') if row.get(k)]
    if hard:
        return 'computed_wrong', '; '.join(f'{k}={str(row[k])[:80]}' for k in hard)
    others = [e for e in row.get('format_errors', []) if not str(e).startswith('missing mm unit:')]
    units = [e for e in row.get('format_errors', []) if str(e).startswith('missing mm unit:')]
    if others:
        return 'computed_wrong', str(others)[:160]
    if units:
        svg = obj.get('svg', '')
        declared = [t.strip() for t in re.findall(r'>([^<>]*)<', svg) if UNITS_NOTE.search(t)]
        if not declared:
            return 'computed_wrong', 'dimensions carry no units and the drawing declares none'
    return 'computed_correct', ''


def collect():
    rows = []
    for label, run, data in RUNS:
        run_dir, data_dir = ROOT / run, ROOT / data
        if not run_dir.exists():
            print(f'  (missing run {run})', file=sys.stderr)
            continue
        tasks = {t['id']: t for t in json.loads((data_dir / 'tasks.json').read_text())['tasks']}
        for tid, task in tasks.items():
            for folder in sorted((run_dir / tid).glob('sample-*')) if (run_dir / tid).exists() else []:
                if not (folder / 'result.json').exists():
                    continue
                outcome, detail = classify(task, folder)
                model = task['model']
                rows.append({'run': label, 'id': tid, 'sample': folder.name,
                             'mode': task.get('mode', 'edit' if tid.endswith('edit') else 'generate'),
                             'members': len(model['members']),
                             'indeterminacy': task.get('indeterminacy', indeterminacy(model)),
                             'outcome': outcome, 'detail': detail})
    return rows


def main():
    rows = collect()
    scored = [r for r in rows if not r['outcome'].startswith('excluded')]
    print(f"{'run':30s} {'task':26s} {'smp':4s} {'mem':>4s} {'ind':>4s}  outcome")
    for r in rows:
        print(f"{r['run']:30s} {r['id']:26s} {r['sample'][-1]:4s} {r['members']:4d} {r['indeterminacy']:4d}  "
              f"{r['outcome']}{('  ' + r['detail'][:70]) if r['detail'] else ''}")

    print('\nBy frame size (completed samples only):')
    print(f"{'members':>8s} {'samples':>8s} {'correct':>8s} {'wrong':>7s} {'declined':>9s} {'decline rate':>13s}")
    buckets = {}
    for r in scored:
        buckets.setdefault(r['members'], []).append(r['outcome'])
    for members in sorted(buckets):
        got = buckets[members]
        dec = got.count('declined')
        print(f"{members:8d} {len(got):8d} {got.count('computed_correct'):8d} "
              f"{got.count('computed_wrong'):7d} {dec:9d} {dec / len(got) * 100:12.0f}%")

    summary = {
        'samples_total': len(rows),
        'samples_completed': len(scored),
        'excluded': {k: sum(r['outcome'] == k for r in rows)
                     for k in ('excluded_api', 'excluded_truncated', 'excluded_format')},
        'computed_correct': sum(r['outcome'] == 'computed_correct' for r in scored),
        'computed_wrong': sum(r['outcome'] == 'computed_wrong' for r in scored),
        'declined': sum(r['outcome'] == 'declined' for r in scored),
        'by_members': {str(m): {'samples': len(v), 'declined': v.count('declined'),
                                'computed_wrong': v.count('computed_wrong'),
                                'computed_correct': v.count('computed_correct')}
                       for m, v in sorted(buckets.items())},
        'note': ('Declining is reported separately from computing a wrong number: they are different '
                 'behaviours and only the second puts a false engineering claim on a drawing. '
                 'Truncated, errored and unparseable attempts are excluded rather than counted as failures.'),
        'rows': rows,
    }
    out = ROOT / 'runs/eng-frame-aggregate.json'
    out.write_text(json.dumps(summary, indent=2) + '\n')
    print(f"\ncompleted {summary['samples_completed']} | correct {summary['computed_correct']} | "
          f"wrong {summary['computed_wrong']} | declined {summary['declined']}  -> {out}")


if __name__ == '__main__':
    main()
