"""Package downloaded source CAD and published FEM tables; never solve or build CAD."""
import hashlib
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import cadquery as cq
import openpyxl
import resvg_py
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'tmp/cad-paired-search/frontistr'
OUT = ROOT / 'data/native-cad-fem-findings'
OUT.mkdir(parents=True, exist_ok=True)
REV = 'da45c381d3c70343dce3838e53463f9b2e602e24'
records = []
previews = []
for folder in sorted((CACHE / 'sample/benchmarks').iterdir()):
    cad = next(folder.glob('*.FCStd'))
    dest = OUT / folder.name
    dest.mkdir(exist_ok=True)
    for f in folder.iterdir():
        if f.suffix in ['.FCStd', '.xlsx', '.md', '.png']:
            shutil.copy2(f, dest / f.name)
    with zipfile.ZipFile(cad) as z:
        xml = ET.fromstring(z.read('Document.xml'))
        geometry = z.read('PartShape.brp')
        (dest / 'source-embedded-shape.brep').write_bytes(geometry)
        constraints = []
        materials = []
        types = {o.attrib['name']: o.attrib['type'] for o in xml.findall('./Objects/Object')}
        for o in xml.findall('./ObjectData/Object'):
            typ = types[o.attrib['name']]
            if typ.startswith('Fem::Constraint'):
                constraints.append({'name': o.attrib['name'], 'type': typ,
                                    'original_properties_xml': ET.tostring(o, encoding='unicode')})
            for m in o.findall("./Properties/Property[@name='Material']/Map"):
                materials.append({i.attrib['key']: i.attrib['value'] for i in m})
    shape = cq.importers.importBrep(str(dest / 'source-embedded-shape.brep')).val()
    assert shape.isValid() and len(shape.Solids()) == 1
    svg = cq.exporters.getSVG(shape, opts={'width': 650, 'height': 420,
                                          'showHidden': False, 'showAxes': False,
                                          'projectionDir': (1, -1, 0.8),
                                          'marginLeft': 20, 'marginTop': 20,
                                          'strokeWidth': 0.7})
    (dest / 'cad-view.svg').write_text(svg)
    (dest / 'cad-view.png').write_bytes(resvg_py.svg_to_bytes(svg_string=svg, dpi=96,
                                                          background='white'))
    previews.append((cad.stem, dest / 'cad-view.png'))
    sheet = openpyxl.load_workbook(dest / 'data_sheet.xlsx', data_only=True).active
    rows = []
    mesh = None
    for row_number, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if len(row) < 9 or row[2] not in ['Calculix', 'FrontISTR']:
            continue
        mesh = row[1] or mesh
        stress = row[8]
        if stress is None:
            continue
        flag = ((folder.name == '03_bikeframe' and row[3] == 'iterativecholesky') or
                (folder.name == '04_spring' and mesh == '2. middle' and row[3] == 'spooles'))
        rows.append({'mesh': mesh, 'solver': row[2], 'matrix_solver': row[3],
                     'max_von_mises_MPa': stress, 'source_cell': f'Sheet1!I{row_number}',
                     'source_flags_inaccurate': flag,
                     'usable_as_published_baseline': isinstance(stress, (int, float)) and not flag})
    record = {'id': folder.name, 'cad_file': str(dest / cad.name),
              'source': f'https://github.com/FrontISTR/FEM_FrontISTR/tree/{REV}/sample/benchmarks/{folder.name}',
              'source_revision': REV, 'cad_validation': {'valid': True, 'solids': 1, 'faces': len(shape.Faces())},
              'materials': materials, 'boundary_conditions': constraints,
              'published_fem_results': rows,
              'dimensioned_drawing_available': False,
              'cad_view_note': 'Inspection render of the original embedded B-Rep; no geometry generated.',
              'benchmark_status': 'Source CAD/FEM pair verified; not yet admitted. Mesh-sensitive peaks, source units, selectors and replay need review.',
              'no_local_fem_solve': True}
    (dest / 'record.json').write_text(json.dumps(record, indent=2))
    records.append(record)

shutil.copy2(CACHE / 'LICENSE', OUT / 'LICENSE-source')
(OUT / 'download-manifest.json').write_text((CACHE / 'download-manifest.json').read_text())
(OUT / 'catalog.json').write_text(json.dumps({'distinct_cad_models': 4, 'new_benchmark_admissions': 0,
                                            'records': records}, indent=2))
(OUT / 'README.md').write_text('''# Four newly found native CAD / published FEM pairs

Original FreeCAD models, embedded B-Reps, numerical Excel results, source stress contours,
material cards and face-based boundary conditions. Source: FrontISTR/FEM_FrontISTR,
revision da45c381d3c70343dce3838e53463f9b2e602e24.

Four distinct models: gear, pressure can, motorcycle frame, spring. Three mesh settings
and multiple solvers are repeated measurements, not additional engineering cases.
No COMSOL dependency. No locally generated engineering geometry or FEM reference results.
CAD views are inspection renders of the original source B-Reps, not dimensioned drawings.

These are source pairs, not certified benchmark cases. Peak stress changes with mesh size.
Published inaccurate solver rows are explicitly flagged in record.json. Original tables
are preserved unmodified. Review units, source face selectors and mesh correspondence
before scoring model submissions. No solver replay or model trial was run.
''')
canvas = Image.new('RGB', (1300, 940), 'white')
draw = ImageDraw.Draw(canvas)
for i, (name, f) in enumerate(previews):
    x, y = (i % 2) * 650, (i // 2) * 470
    draw.text((x + 20, y + 12), name + ' - original CAD', fill='black')
    canvas.paste(Image.open(f).convert('RGB'), (x, y + 40))
preview = ROOT / 'output/native-cad-fem-found-4.png'
canvas.save(preview)
archive = ROOT / 'output/datasets/native-cad-fem-found-4.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in OUT.rglob('*'):
        if f.is_file():
            z.write(f, f.relative_to(OUT))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
print(json.dumps({'catalog': str(OUT / 'catalog.json'), 'archive': str(archive),
                  'preview': str(preview), 'models': len(records),
                  'published_result_rows': sum(len(r['published_fem_results']) for r in records)}, indent=2))
