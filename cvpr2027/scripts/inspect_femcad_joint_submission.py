#!/usr/bin/env python3
"""Check CAD->mesh->FEM artifact consistency. Never execute candidate code or grant a physics pass."""
import argparse
import hashlib
import json
import math
from pathlib import Path

REQUIRED=('cad_source','cad','mesh','solver_input','results','solver_log')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def artifact(root,record):
    if not isinstance(record,dict):raise ValueError('Artifact record must be an object')
    rel=record.get('path')
    if not isinstance(rel,str) or Path(rel).is_absolute():raise ValueError('Artifact path must be relative')
    if '..' in Path(rel).parts:raise ValueError('Parent path traversal forbidden')
    p=root/rel
    if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Artifact escapes submission')
    parts=Path(rel).parts
    if any(root.joinpath(*parts[:i]).is_symlink() for i in range(1,len(parts)+1)):raise ValueError('Symlink artifact')
    if not p.is_file() or not p.stat().st_size:raise ValueError('Artifact missing or empty: '+rel)
    actual=digest(p)
    if record.get('sha256')!=actual:raise ValueError('Artifact hash mismatch: '+rel)
    return p,actual


def inspect_step(path):
    if path.suffix.lower() not in {'.step','.stp'}:raise ValueError('CAD must be STEP')
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.option.setString('Geometry.OCCTargetUnit','M')
        gmsh.model.add('submission-inspection')
        gmsh.model.occ.importShapes(str(path),format='step')
        gmsh.model.occ.synchronize()
        entities=gmsh.model.getEntities()
        if not entities:raise ValueError('STEP contains no imported entities')
        counts={str(dim):len(gmsh.model.getEntities(dim)) for dim in range(4)}
        measures={str(dim):sum(gmsh.model.occ.getMass(dim,tag) for _,tag in gmsh.model.getEntities(dim)) for dim in (1,2,3)}
        return {'imported':True,'units':'m','entity_counts_by_dimension':counts,
                'summed_length_area_volume':measures,'bounding_box_m':list(gmsh.model.getBoundingBox(-1,-1)),
                'limitations':'Import and geometric measures do not certify correct topology, absence of overlaps, manifold validity or agreement with source geometry.'}
    finally:gmsh.finalize()


def inspect(root,task_id=None,cad_inspection=False):
    root=Path(root);errors=[];checks={};paths={};hashes={}
    try:submission=json.loads((root/'submission.json').read_text())
    except (OSError,ValueError) as e:return {'status':'invalid_submission','errors':[str(e)],'joint_pass':None}
    if not isinstance(submission,dict):return {'status':'invalid_submission','errors':['Submission must be an object'],'joint_pass':None}
    for field in ('artifacts','lineage','solver','units'):
        if not isinstance(submission.get(field),dict):
            errors.append(field+' must be an object');submission[field]={}
    if task_id and submission.get('task_id')!=task_id:errors.append('Task ID mismatch')
    for name in REQUIRED:
        try:
            p,h=artifact(root,submission.get('artifacts',{}).get(name,{}));paths[name]=p;hashes[name]=h;checks[name]='hash_verified'
        except (OSError,ValueError,TypeError) as e:errors.append(name+': '+str(e))
    if len(set(paths.values()))!=len(paths):errors.append('Distinct required artifacts must have distinct paths')
    lineage=submission.get('lineage',{})
    for field,parent in [('mesh_parent_cad_sha256','cad'),('solver_parent_mesh_sha256','mesh'),('results_parent_solver_input_sha256','solver_input')]:
        if parent not in hashes or lineage.get(field)!=hashes[parent]:errors.append('Lineage mismatch: '+field)
    formulation=submission.get('formulation')
    if formulation not in {'2d-plane-strain','2d-plane-stress','axisymmetric','shell','3d','mixed'}:errors.append('Missing/invalid formulation')
    if not submission.get('units'):errors.append('Missing unit declarations')
    if not submission.get('solver',{}).get('name') or not submission.get('solver',{}).get('version'):errors.append('Missing solver name/version')
    if not isinstance(submission.get('physical_regions'),list) or not submission['physical_regions']:errors.append('Missing CAD-to-mesh physical-region mapping')
    else:
        for region in submission['physical_regions']:
            if not isinstance(region,dict) or not region.get('name') or not all(isinstance(region.get(k),list) and region[k] for k in ('cad_entity_ids','mesh_group_ids')):
                errors.append('Incomplete CAD-to-mesh region mapping')
    if not isinstance(submission.get('reproduction_steps'),list) or not submission['reproduction_steps']:errors.append('Missing reproducible build/mesh/solve instructions')
    metrics=None
    if cad_inspection and 'cad' in paths:
        try:metrics=inspect_step(paths['cad'])
        except Exception as e:errors.append('CAD import inspection: '+str(e))
    return {'task_id':submission.get('task_id'),'status':'invalid_submission' if errors else 'artifact_consistency_verified',
      'artifact_checks':checks,'cad_diagnostics':metrics,'errors':errors,
      'execution_chain':'unverified: hashes are candidate claims; trusted isolated replay is required',
      'cad_correctness':None,'physics_correctness':None,'solver_convergence':None,'numerical_agreement':None,'joint_pass':None,
      'reason':'No validated task reference/acceptance contract or independent CAD-to-mesh-to-solver replay. Artifact consistency is not a benchmark pass.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('submission_directory');p.add_argument('--task-id');p.add_argument('--inspect-cad',action='store_true');p.add_argument('--output',required=True)
    a=p.parse_args();result=inspect(a.submission_directory,a.task_id,a.inspect_cad)
    Path(a.output).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2,allow_nan=False))
