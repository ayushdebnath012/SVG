"""Package existing drawing/CAD/FEM assets without solving or generating tasks."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/web-complex-fem'
CACHE = ROOT / 'tmp/published-mechanical-cases'


def fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        with requests.get(url, stream=True, timeout=90) as response:
            response.raise_for_status()
            temporary = dest.with_suffix(dest.suffix + '.part')
            with temporary.open('wb') as stream:
                for chunk in response.iter_content(1024 * 1024):
                    stream.write(chunk)
            temporary.replace(dest)
    digest = hashlib.sha256()
    with dest.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'source_url': url, 'local': str(dest.relative_to(ROOT)),
            'bytes': dest.stat().st_size, 'sha256': digest.hexdigest()}


def ingest(source):
    case_dir = CACHE / source['id']
    drawings = []
    for index, figure in enumerate(source['drawings']):
        asset = fetch(figure['url'], case_dir / 'inputs/drawings' / Path(figure['url']).name)
        asset['caption'] = figure.get('original_source_caption', figure['caption'])
        drawings.append(asset)
    geometry, solved = [], []
    for model in source['cad_model_assets']:
        is_reference = model['role'] == 'solver_model'
        dest = case_dir / ('references' if is_reference else 'inputs/cad') / model['name']
        asset = fetch(model['url'], dest)
        (solved if is_reference else geometry).append(asset)
    tutorial = fetch(source['source_url'], case_dir / 'references/source.html')
    soup = BeautifulSoup((ROOT / tutorial['local']).read_bytes(), 'html.parser')
    drawing_urls = {figure['url'] for figure in source['drawings']}
    model_stem = Path(source['source_url']).stem
    result_images = []
    for image in soup.find_all('img', src=True):
        url = urljoin(source['source_url'], image['src'])
        if Path(url).name.startswith(model_stem + '.') and url not in drawing_urls:
            result_images.append(fetch(url, case_dir / 'references/source-images' / Path(url).name))
    import zipfile
    for asset in solved:
        with zipfile.ZipFile(ROOT / asset['local']) as archive:
            names = archive.namelist()
            asset['stored_solution_entries'] = [n for n in names if 'solution' in n.lower() and n.endswith('.mphbin')]
            asset['stored_mesh_entries'] = [n for n in names if 'mesh' in n.lower() and n.endswith('.mphbin')]
            if not asset['stored_solution_entries']:
                raise ValueError(f"No stored solution entries: {asset['local']}")
    record = {'id': source['id'], 'title': source['title'], 'source_url': source['source_url'],
              'source_solver': 'COMSOL', 'drawings': drawings, 'cad_inputs': geometry,
              'published_fem_models': solved, 'source_documentation': tutorial,
              'original_source_images': result_images,
              'published_result_captions': source['source_results_figures'],
              'status': 'Original drawings, native CAD inputs and stored FEM solution assets downloaded',
              'numerical_scoring_ready': False,
              'limitations': ['COMSOL required to interpret/export binary FEM fields.',
                             'Scoring tolerances and convergence have not been established.',
                             'Source tutorial contains results; keep it out of blinded candidate inputs.'],
              'generated_tasks_or_results': False}
    (case_dir / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


if __name__ == '__main__':
    sources = json.loads((DATA / 'drawing-qualified-sources.json').read_text())['sources']
    sources = [s for s in sources if s.get('id') in ['FEMCAD-ADV-005', 'FEMCAD-ADV-010']]
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(ingest, sources))
    (DATA / 'cases.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in records))
    print(json.dumps({'included_cases': len(records), 'ids': [r['id'] for r in records],
                      'drawing_count': sum(len(r['drawings']) for r in records),
                      'solved_model_count': sum(len(r['published_fem_models']) for r in records)}))
