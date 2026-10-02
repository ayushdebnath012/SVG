"""Format-relaxed diagnostic: uniquely replace a fragment on the declared line."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--predictions', type=Path, required=True)
    a = p.parse_args()
    sources = {r['id']: r for r in map(json.loads, (a.data / 'test.jsonl').read_text().splitlines())}
    out = []
    for r in map(json.loads, a.predictions.read_text().splitlines()):
        item = dict(r)
        item['control'] = 'Unique substring patch on the declared source line; transport diagnostic.'
        try:
            text = r['prediction'].strip()
            if text.startswith('```'):
                text = '\n'.join(text.splitlines()[1:-1])
            patch = json.loads(text)
            lines = sources[r['id']]['code'].splitlines()
            if type(patch['line']) is not int or not 1 <= patch['line'] <= len(lines):
                raise ValueError('Invalid line number')
            line = lines[patch['line'] - 1]
            if not isinstance(patch['old'], str) or not patch['old'] or line.count(patch['old']) != 1:
                raise ValueError('Fragment not unique on declared line')
            if not isinstance(patch['new'], str) or '\n' in patch['new']:
                raise ValueError('Invalid replacement')
            lines[patch['line'] - 1] = line.replace(patch['old'], patch['new'], 1)
            item.update(predicted_code='\n'.join(lines), applicable=True, error=None)
        except Exception as e:
            item.update(predicted_code=None, applicable=False, error=str(e))
        out.append(item)
    dest = a.predictions.with_name(a.predictions.name.replace('-predictions', '-fragment-control-predictions'))
    dest.write_text(''.join(json.dumps(r) + '\n' for r in out))
    print(dest)


if __name__ == '__main__':
    main()
