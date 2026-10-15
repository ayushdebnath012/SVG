"""Execute downloaded mechanical CAD in restricted, timeout-bounded workers.

AST/builtin restriction is defense in depth, not a general Python sandbox.
Only known CadQuery programs from the pinned corpus are accepted.
"""
import ast
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def white_background(path):
    root = ET.fromstring(path.read_text())
    ns = '{http://www.w3.org/2000/svg}'
    root.insert(0, ET.Element(ns + 'rect', {'width': '100%', 'height': '100%', 'fill': 'white'}))
    ET.ElementTree(root).write(path, encoding='unicode')


def execute(code):
    import cadquery as cq
    import math
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(x.name not in {'cadquery', 'math'} for x in node.names):
            raise ValueError('Unexpected import')
        if isinstance(node, (ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.While, ast.With, ast.Try)):
            raise ValueError('Unsupported Python construct')
        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
            raise ValueError('Private attribute access')
        if isinstance(node, ast.Name) and (node.id.startswith('__') or node.id in {'open', 'eval', 'exec', 'compile', 'getattr', 'setattr', 'globals', 'locals', 'input', 'breakpoint'}):
            raise ValueError('Forbidden name')
    tree.body = [n for n in tree.body if not isinstance(n, ast.Import)]
    env = {'cq': cq, 'math': math, 'show_object': lambda *a, **k: None,
           '__builtins__': {'range': range, 'abs': abs, 'min': min, 'max': max, 'len': len,
                            'float': float, 'int': int, 'list': list, 'tuple': tuple, 'enumerate': enumerate, 'zip': zip}}
    exec(compile(tree, '<pinned-benchcad>', 'exec'), env)
    solid = env['result'].val()
    if not solid.isValid() or not solid.Solids() or solid.Volume() <= 0:
        raise ValueError('Invalid or empty solid')
    return solid


def verify_part(row, out):
    import cadquery as cq
    parent = out / 'artifacts' / row['stem']
    parent.mkdir(parents=True, exist_ok=True)
    source = execute(row['code'])
    cq.exporters.export(source, str(parent / 'original.step'))
    directions = {'front': (0, -1, 0), 'top': (0, 0, 1), 'right': (1, 0, 0), 'iso': (1, -1, 1)}
    for view, direction in directions.items():
        dest = parent / f'original-{view}.svg'
        cq.exporters.export(source, str(dest), opt={'projectionDir': direction, 'showHidden': False})
        white_background(dest)
    accepted = []
    for i, edit in enumerate(row['edits']):
        try:
            after = execute(edit['edited_code'])
            if abs(after.Volume() - source.Volume()) <= max(1e-7, source.Volume() * 1e-8):
                raise ValueError('Edit has no measurable volume change')
            cq.exporters.export(after, str(parent / f'edited-{i}.step'))
            paths = {}
            for view, direction in directions.items():
                dest = parent / f'edited-{i}-{view}.svg'
                cq.exporters.export(after, str(dest), opt={'projectionDir': direction, 'showHidden': False})
                white_background(dest)
                paths[view] = str(dest.relative_to(out))
            item = {k: v for k, v in row.items() if k != 'edits'}
            item.update(edit)
            item.update(id=hashlib.sha256((row['stem'] + edit['target']).encode()).hexdigest(),
                        verification=dict(original_valid=True, edited_valid=True, original_volume=source.Volume(),
                                          edited_volume=after.Volume(), fem='not_evaluated_missing_physical_specification'),
                        original_views={v: str((parent / f'original-{v}.svg').relative_to(out)) for v in directions},
                        edited_views=paths)
            accepted.append(item)
        except Exception as e:
            print('Rejected edit', row['stem'], i, type(e).__name__, str(e)[:200], flush=True)
    (parent / 'records.json').write_text(json.dumps(accepted))


def main():
    out = Path(sys.argv[1])
    rows = json.loads((out / 'candidates.json').read_text())
    if len(sys.argv) == 3:
        verify_part(rows[int(sys.argv[2])], out)
        return
    def task(i):
        try:
            r = subprocess.run([sys.executable, __file__, str(out), str(i)], capture_output=True, text=True, timeout=90)
            return i, r.returncode, r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            return i, -1, 'CAD execution timeout'
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool, (out / 'verified.jsonl').open('w') as f:
        for i, status, log in pool.map(task, range(len(rows))):
            print(i + 1, '/', len(rows), rows[i]['stem'], 'exit', status, log[-500:], flush=True)
            records = out / 'artifacts' / rows[i]['stem'] / 'records.json'
            if status == 0 and records.exists():
                for row in json.loads(records.read_text()):
                    f.write(json.dumps(row) + '\n')
                f.flush()


if __name__ == '__main__':
    main()
