"""Create inspectable before/after CAD drawing sheets from verified records."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('data', type=Path)
    a = p.parse_args()
    rows = [json.loads(x) for x in (a.data / 'verified.jsonl').read_text().splitlines()]
    for r in rows:
        root = ET.Element(NS + 'svg', {'width': '1200', 'height': '720', 'viewBox': '0 0 1200 720'})
        ET.SubElement(root, NS + 'rect', width='1200', height='720', fill='white')
        def label(x, y, text, size=14):
            t = ET.SubElement(root, NS + 'text', x=str(x), y=str(y), fill='#172b40', **{'font-family': 'Arial, sans-serif', 'font-size': str(size)})
            t.text = text
        label(25, 30, r['family'].replace('_', ' ') + ' | verified CAD feature edit', 22)
        label(25, 54, r['instruction'].split(' Keep every other')[0], 14)
        label(25, 78, 'BEFORE', 17)
        label(625, 78, 'AFTER', 17)
        for j, view in enumerate(('front', 'top', 'right', 'iso')):
            y = 100 + j * 140
            for col, key in enumerate(('original_views', 'edited_views')):
                src = ET.fromstring((a.data / r[key][view]).read_text())
                src.attrib.update(x=str(col * 600 + 25), y=str(y), width='550', height='125',
                                  viewBox='0 0 ' + src.get('width', '800') + ' ' + src.get('height', '240'))
                root.append(src)
                label(col * 600 + 25, y + 12, view.upper(), 11)
        label(25, 687, f"Solid volumes: {r['verification']['original_volume']:.5g} → {r['verification']['edited_volume']:.5g} (native CAD units cubed)")
        label(25, 708, 'Geometry verified. FEM not evaluated: physical specification missing. Source: BenchCAD, Zhang et al. 2026, CC-BY-4.0.', 12)
        dest = a.data / 'sheets' / (r['id'] + '.svg')
        dest.parent.mkdir(exist_ok=True)
        ET.ElementTree(root).write(dest, encoding='unicode')
    print('Created', len(rows), 'before/after drawing sheets')


if __name__ == '__main__':
    main()
