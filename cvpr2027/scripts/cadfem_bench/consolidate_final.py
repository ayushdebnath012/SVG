"""Consolidate the sealed v1.6 benchmark and account for the full local source library.
No case is admitted, no CAD is generated, and no numerical target is changed.
"""
import argparse
import collections
import hashlib
import json
import shutil
from pathlib import Path

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n')

def build(workspace, source, out):
    if out.exists():
        raise FileExistsError(out)
    shutil.copytree(source, out)
    shutil.copy2(out/'README.md', out/'RELEASE_README.md')
    library = out/'evaluator/source-library'
    library.mkdir()
    data = workspace/'cvpr2027/data'
    selected = [d for d in sorted(data.iterdir()) if d.is_dir() and
                (d.name.startswith(('web-', 'published-fem-', 'native-cad-fem', 'femcad-', 'fem-cad-hard'))
                 or d.name in ['simjeb-bench', 'engineering-fem-v1'])]
    tasks = rows(out/'evaluator/task-pool/tasks.jsonl')
    refs = {r['task_id']: r for r in rows(out/'evaluator/task-pool/references.jsonl')}
    evidence = {r['path']: r for r in rows(out/'evaluator/evidence-manifest.jsonl')}
    inventory = []; file_count = 0; byte_count = 0
    with (library/'local-library-files.jsonl').open('w') as stream:
        for d in selected:
            files = [f for f in sorted(d.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and '.git' not in f.parts]
            ext = collections.Counter(f.suffix.lower() or '<none>' for f in files)
            snapshots = []
            for f in files:
                rel = f.relative_to(d)
                row = {'collection': d.name, 'path': str(rel), 'bytes': f.stat().st_size, 'sha256': sha(f), 'origin': 'local collection snapshot; may include source, inspection or historical derived files; not all asserted original'}
                stream.write(json.dumps(row)+'\n');file_count += 1;byte_count += row['bytes']
                if f.name in ['catalog.json', 'download-manifest.json', 'manifest.json', 'source-manifest.json']:
                    dst = library/'metadata'/d.name/rel;dst.parent.mkdir(parents=True, exist_ok=True);shutil.copy2(f, dst);snapshots.append(str(dst.relative_to(library)))
            prefix = 'evidence/data/'+d.name+'/'
            ids = sorted(t['task_id'] for t in tasks if any(e.startswith(prefix) for e in refs[t['task_id']].get('evidence_files', [])))
            primary = {t['task_id'] for t in rows(out/'candidate/tasks.jsonl')}
            inventory.append({'collection': d.name, 'local_raw_data': str(d), 'portable_raw_data': 'cvpr2027/data/'+d.name,
                'file_count': len(files), 'bytes': sum(f.stat().st_size for f in files), 'extensions': dict(sorted(ext.items())),
                'metadata_snapshots': snapshots, 'source_pool_task_ids': ids, 'primary_task_ids': [i for i in ids if i in primary],
                'status': 'contains_admitted_source_evidence' if ids else 'source_library_not_admitted_by_this_inventory',
                'raw_data_storage': 'admitted evidence and selected source-review files are bundled; remaining raw files stay at the indexed local path',
                'admission_policy': 'file presence is not proof of paired CAD/results, complete setup, licensing, convergence or benchmark readiness'})
            print('indexed', d.name, len(files), 'files', flush=True)
    save(library/'collections.json', inventory)
    original = workspace/'cvpr2027/data/cadfem-bench-v1/registry.jsonl'
    shutil.copy2(original, library/'historical-source-registry.jsonl')
    # Preserve historical exclusion reasons without presenting old counts as current.
    save(library/'historical-registry-notice.json', {'role': 'historical source discovery and hold reasons', 'counts_and_readiness_are_current': False,
        'current_task_counts': 'evaluator/validation.json', 'current_held_reasons': 'held/tasks.jsonl', 'current_review_decisions': 'evaluator/source-review/'})
    reports = []
    for pdf in sorted((workspace/'cvpr2027/output/pdf').glob('*.pdf')):
        include = pdf.name.startswith(('cadfem-', 'web-cad-fem-', 'web-fem-', 'published-', 'auxetic-', 'simjeb-','additional-complex-'))
        row = {'filename': pdf.name, 'bytes': pdf.stat().st_size, 'sha256': sha(pdf), 'bundled': include,
               'role': 'historical/source collection report; numerical claims do not automatically become benchmark targets' if include else 'other project report outside CADFEM collection scope'}
        if include:
            dst=library/'reports'/pdf.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pdf,dst)
            row['path']=str(dst.relative_to(out))
        reports.append(row)
    save(library/'report-index.json', reports)
    validation=json.loads((out/'evaluator/validation.json').read_text())
    summary={'release':'CADFEM-Bench final, numerical/scoring version 1.6', 'primary_tasks':validation['tasks'],
        'graded_outputs':validation['graded_outputs'], 'source_pool_tasks':128, 'held_tasks':55,
        'source_collections_indexed':len(inventory), 'local_library_files_indexed':file_count, 'local_library_bytes_indexed':byte_count,
        'collection_reports_bundled':sum(r['bundled'] for r in reports), 'all_pdf_directory_files_accounted_for':len(reports),
        'new_tasks_admitted':0, 'new_CAD_generated':0, 'new_targets_generated':0, 'model_runs_performed_by_this_build':0,
        'unadmitted_raw_library_fully_embedded':False, 'local_raw_library':str(data),
        'distribution':'local research only; source rights vary'}
    save(library/'coverage.json', summary)
    (out/'README.md').write_text('''# CADFEM-Bench final dataset

This is the consolidated final snapshot of CADFEM-Bench v1.6: **57 primary tasks, 123 graded outputs, 11 engineering families**, with 51 supplied-CAD analyses and six drawing/specification-to-CAD tasks. The 128-case source-backed pool is divided into primary, calibration, reserved-public and related-public suites; 55 held tasks are excluded from scoring. See RELEASE_README.md for the full evaluation protocol and limitations.

## What to use

- candidate/: model-visible primary tasks, CAD/drawings/specifications and submission contract.
- evaluator/: hidden references, original source evidence, separate suites, scorer, sandbox runner, geometry validators and verification records.
- held/: inactive tasks and their reasons.
- report/cadfem-bench-v1.6.pdf: 67-page atlas showing each primary CAD/drawing and published numerical results; evaluator-only.
- evaluator/source-review/: six additional complex original CAD/FEM collections and the contact convergence follow-up, unscored.
- evaluator/source-library/: complete inventory of the selected downloaded collection folders, their file hashes, original metadata and collection reports.

The source-library inventory records remaining raw files at their original local paths under cvpr2027/data. Those unadmitted raw files are **not all embedded in this archive**. The inventory also records local inspection and historical derived files; it does not assert that every inventoried file is original web data. Admitted reference evidence and the six reviewed complex collections are embedded. The metadata and historical reports preserve the other leads and limitations without promoting them to scored tasks. Historical counts and claims are superseded by evaluator/validation.json and current held/source-review decisions.

## Running model comparisons

Give a model only candidate/ or an export made by evaluator/export_run.py. The full archive and source-library reports contain answers. Record exact model version, generation settings and resource budgets. Use the same tools and offline replay conditions for each model. Score numerical accuracy, geometry gates and verified workflow separately. Correct numbers alone cannot pass the workflow.

Fourteen primary tasks have independent FEM reproduction; 43 still lack it. Most acceptance bands remain provisional. Human workflow review is still required. Reserved web cases cannot establish a private uncontaminated holdout. Contact remains held because its mesh study failed admission. No new model run is claimed by this consolidation.

Source rights vary. This local research package has no blanket public redistribution license. No CAD or numerical target was created by this consolidation.

## Integrity and rebuilding

SHA256SUMS.txt covers the consolidated package. evaluator/source-library/coverage.json records exact source/report inventory counts. scripts/cadfem_bench/consolidate_final.py rebuilds this final snapshot from a sealed v1.6 and the local source library; finalize_v16.py seals and copies it. The original v1.6 release is preserved.
''')
    script=Path(__file__).resolve();shutil.copy2(script,out/'scripts/cadfem_bench'/script.name)
    return summary

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--workspace',type=Path,required=True);a.add_argument('--source',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args()
    print(json.dumps(build(x.workspace.resolve(),x.source.resolve(),x.out.resolve()),indent=2))
