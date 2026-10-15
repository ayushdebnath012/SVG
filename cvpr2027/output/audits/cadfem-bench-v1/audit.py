"""Read-only package audit; no FEM solves, CAD generation or source execution.

Run with cvpr2027/tmp/cq-env/bin/python from the workspace root.
Only the inspected package's numeric scorer is run, in temporary directories.
"""
import collections
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PKG = ROOT / 'cadfem-bench-v1'
OUT = Path(__file__).resolve().parent

def readlines(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

tasks = readlines(PKG / 'candidate/tasks.jsonl')
refs = readlines(PKG / 'evaluator/references.jsonl')
registry = readlines(PKG / 'evaluator/registry.jsonl')
result = {'scope': 'Package integrity, CAD import, composition and scorer behavior; no independent FEM reruns',
          'tasks': len(tasks), 'tracks': dict(collections.Counter(t['track'] for t in tasks)),
          'families': dict(collections.Counter(t['family'] for t in tasks)),
          'registry': dict(collections.Counter(r['status'] for r in registry)),
          'graded_reference_classes': dict(collections.Counter(v['ref_class'] for r in refs for v in r['references'].values() if v.get('graded', True)))}
result['id_alignment'] = [t['task_id'] for t in tasks] == [r['task_id'] for r in refs]
result['unique_task_ids'] = len(set(t['task_id'] for t in tasks))
bad, n = [], 0
for line in (PKG / 'SHA256SUMS.txt').read_text().splitlines():
    h, name = line.split('  ', 1)
    p = PKG / name
    n += 1
    if not p.is_file() or sha(p) != h:
        bad.append(name)
result['package_hashes'] = {'checked': n, 'failed': bad}
bad, n = [], 0
cadgroups = collections.defaultdict(list)
for t in tasks:
    for i in t['inputs']:
        p = PKG / 'candidate' / i['path']
        n += 1
        if not p.is_file() or sha(p) != i['sha256'] or p.stat().st_size != i['bytes']:
            bad.append(i['path'])
        if i['role'] == 'cad':
            cadgroups[i['sha256']].append({'task_id': t['task_id'], 'path': i['path'], 'track': t['track']})
result['input_hashes'] = {'checked': n, 'failed': bad}
result['cad_file_instances'] = sum(map(len, cadgroups.values()))
result['unique_cad_file_hashes'] = len(cadgroups)
result['exact_cad_duplicates'] = [v for v in cadgroups.values() if len(v) > 1]
result['assemblies_declared'] = [t['task_id'] for t in tasks if t.get('complexity', {}).get('assembly')]
result['geometry_checks'] = [r['task_id'] for r in refs if r.get('geometry_check')]
result['source_urls'] = sorted(set(t['source']['url'] for t in tasks))
result['raw_solver_file_extensions'] = dict(collections.Counter(p.suffix.lower() for p in PKG.rglob('*') if p.is_file() and p.suffix.lower() in {'.rst','.rth','.frd','.odb','.vtu','.vtk','.h5','.hdf5','.npz'}))

# Regression probe: only exact scalar answers, with no CAD, code, mesh, fields or solver log.
with tempfile.TemporaryDirectory(prefix='cadfem-audit-') as td:
    td = Path(td)
    sub = td / 'answers'
    for r in refs:
        if r['grader'] != 'numeric':
            continue
        p = sub / r['task_id'] / 'results.json'
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'outputs': {k: v['value'] for k,v in r['references'].items()}}))
    o = td / 'score.json'
    run = subprocess.run([sys.executable, str(PKG/'evaluator/score.py'), '--refs',str(PKG/'evaluator/references.jsonl'), '--submissions',str(sub),'--out',str(o)],capture_output=True,text=True,check=True)
    scored = json.loads(o.read_text())
    result['answers_only_probe'] = {'summary': scored['summary'], 'passed_without_any_workflow_artifacts': [r['task_id'] for r in scored['tasks'] if r['passed']],
                                   'track_B_passed_without_CAD': [r['task_id'] for r in scored['tasks'] if r['track']=='B' and r['passed']]}
    (OUT / 'answers-only-score.json').write_text(json.dumps(scored,indent=2)+'\n')
    # Valid JSON but schema-invalid payload: the current grader should reject per task, not crash a run.
    p = sub / refs[0]['task_id'] / 'results.json'
    p.write_text('{"outputs": null}')
    run = subprocess.run([sys.executable,str(PKG/'evaluator/score.py'),'--refs',str(PKG/'evaluator/references.jsonl'),'--submissions',str(sub)],capture_output=True,text=True)
    result['invalid_outputs_null_probe'] = {'exit_code':run.returncode,'stderr_tail':run.stderr.splitlines()[-4:]}

(OUT/'audit-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('answers_only_probe','exact_cad_duplicates','source_urls')},indent=2),flush=True)

# Parse every byte-distinct supplied STEP/BREP with OpenCASCADE; never execute .geo definitions.
from OCP.STEPControl import STEPControl_Reader
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopExp import TopExp
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
cad = []
for h, instances in cadgroups.items():
    p = PKG / 'candidate' / instances[0]['path']
    if p.suffix.lower() == '.geo':
        cad.append({'sha256':h,'instances':instances,'status':'text_geometry_definition_not_executed'})
        continue
    rec = {'sha256':h,'instances':instances}
    try:
        if p.suffix.lower() == '.step':
            reader=STEPControl_Reader()
            assert int(reader.ReadFile(str(p))) == 1
            reader.TransferRoots()
            shape=reader.OneShape()
        else:
            shape=TopoDS_Shape()
            assert BRepTools.Read_s(shape,str(p),BRep_Builder())
        rec['valid']=BRepCheck_Analyzer(shape).IsValid()
        for key,typ in [('solids',TopAbs_SOLID),('faces',TopAbs_FACE)]:
            m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(shape,typ,m); rec[key]=m.Extent()
        g=GProp_GProps(); BRepGProp.VolumeProperties_s(shape,g); rec['volume_mm3']=g.Mass()
        rec['status']='imported'
    except Exception as e:
        rec['status']='error';rec['error']=str(e)
    cad.append(rec)
    (OUT/'cad-inspection.json').write_text(json.dumps(cad,indent=2)+'\n')
    print('CAD',len(cad),len(cadgroups),p.name,rec.get('valid'),flush=True)
result['cad_import_summary']={'checked':sum(x['status']=='imported' for x in cad), 'invalid':[x['instances'] for x in cad if x.get('valid') is False], 'errors':[x for x in cad if x['status']=='error'], 'geometry_definitions_not_executed':sum(x['status']=='text_geometry_definition_not_executed' for x in cad)}
(OUT/'audit-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['cad_import_summary']),flush=True)
