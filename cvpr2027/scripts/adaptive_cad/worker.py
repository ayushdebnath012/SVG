"""One timeout-bounded native CAD/FEM job. Input and output are JSON files."""
import sys,json,tempfile,math,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cad_edit_contracts import apply
from cad_edit_verifier import extract,numeric_checks,_iou
from verify_mechanical_cad_edits import execute


def metrics(solid):
    bb=solid.BoundingBox()
    return dict(volume=solid.Volume(),area=solid.Area(),solids=len(solid.Solids()),
                faces=len(solid.Faces()),bbox_x=bb.xlen,bbox_y=bb.ylen,bbox_z=bb.zlen)


def measure_constraints(specs,actual,source):
    records=[]
    for c in specs:
        name=c['metric']
        if name not in actual:raise ValueError('Unsupported constraint metric')
        value=actual[name];target=source[name] if c.get('preserve_source') else c.get('equals')
        ok=True
        if target is not None:ok &= abs(value-target)<=c.get('atol',1e-6)+c.get('rtol',1e-5)*abs(target)
        if 'min' in c:ok &= value>=c['min']
        if 'max' in c:ok &= value<=c['max']
        if target is None and 'min' not in c and 'max' not in c:raise ValueError('Constraint has no bound')
        records.append(dict(metric=name,value=value,target=target,ok=bool(ok)))
    return records


def fem(solid,contract,variation=None):
    from mechanical_cad_fem import mesh_step,solve
    import numpy as np
    import cadquery as cq
    required={'young_MPa','poisson','force_N','axis','fixture','band','mesh_size_mm','limits'}
    if not required<=set(contract) or contract['fixture']!='lower_band_fixed_upper_band_axial_load':
        raise ValueError('Incomplete or unsupported FEM contract')
    E=float(contract['young_MPa']);nu=float(contract['poisson']);force=float(contract['force_N'])
    axis=np.asarray(contract['axis'],dtype=float);h=float(contract['mesh_size_mm']);band=float(contract['band'])
    v=variation or {};E*=v.get('young_scale',1);force*=v.get('force_scale',1);h*=v.get('mesh_scale',1)
    if not (E>0 and -1<nu<.5 and force>0 and h>0 and 0<band<.5 and axis.shape==(3,) and np.isfinite(axis).all() and np.linalg.norm(axis)>0):
        raise ValueError('Invalid FEM parameters')
    if not contract['limits']:raise ValueError('FEM requires acceptance limits')
    with tempfile.TemporaryDirectory() as d:
        step=Path(d)/'part.step';cq.exporters.export(solid,str(step))
        xyz,tet=mesh_step(step,Path(d)/'part.msh',h)
        result,_,_=solve(xyz,tet,axis=axis,E=E,nu=nu,force=force,band=band)
    checks=[]
    for name,limit in contract['limits'].items():
        if name not in result or not math.isfinite(result[name]):raise ValueError('Unknown or nonfinite FEM metric')
        checks.append(dict(metric=name,value=result[name],max=limit,ok=result[name]<=limit))
    return dict(status='PASS' if all(c['ok'] for c in checks) else 'FAIL',metrics=result,checks=checks)


NUMBER=re.compile(r"(?<![\w.])(\d+\.\d+|\d+)(?![\w.])")


def perturb(code,source,scale):
    """Scale numeric literals on lines that differ from the source; integers up to 12 are usually counts and stay."""
    src=source.splitlines();out=[]
    def one(m):
        v=float(m.group(1))
        return m.group(1) if v==int(v) and 0<=v<=12 else repr(v*scale)
    for k,line in enumerate(code.splitlines()):
        out.append(NUMBER.sub(one,line) if k>=len(src) or line!=src[k] else line)
    return "\n".join(out)


def geometric_variation(code,source,faces,scale):
    try:return {'status':'PASS' if len(execute(perturb(code,source,scale)).Faces())==faces else 'FAIL','number_scale':scale}
    except Exception as e:return {'status':'FAIL','number_scale':scale,'reason':type(e).__name__}


def run(data):
    task=data['task'];candidate=data['candidate'];phase=data.get('phase','search')
    source=execute(task['code']);_,patch=extract(candidate);code=apply(task['code'],patch,'cadquery');solid=execute(code)
    if data.get('export_path'):
        import cadquery as cq
        cq.exporters.export(solid,data['export_path'])
        return {'geometry':{'status':'PASS'},'exported':data['export_path']}
    actual=metrics(solid);original=metrics(source)
    checks=measure_constraints(task['constraints'],actual,original)
    out=dict(geometry={'status':'PASS','metrics':actual},constraints={'status':'PASS','checks':checks},
             numbers=numeric_checks(task['instruction'],task['code'],patch),code=code,changed=_iou(source,solid)<.99999,
             edited_lines=sum(op['delete']+len(op['insert']) for op in patch['edits']))
    if task.get('instruction_values'):
        # Opt-in instruction contract: requested values appear in inserted lines and the solid changes.
        missing=[n['value'] for n in out['numbers'] if not n['ok']]
        checks.append(dict(metric='instruction_values',missing=missing,ok=not missing))
        checks.append(dict(metric='changed_solid',value=out['changed'],ok=bool(out['changed'])))
    if any(not c['ok'] for c in checks):out['constraints']['status']='FAIL'
    # An empty explicit contract is not a claim of semantic understanding.
    out['fem']={'status':'UNKNOWN','reason':'No physical contract supplied'}
    out['robustness']={'status':'UNKNOWN','reason':'No perturbation contract supplied'}
    if out['constraints']['status']=='FAIL' or data.get('stage')=='geometry':return out
    if task.get('fem'):
        try:out['fem']=fem(solid,task['fem'])
        except Exception as e:out['fem']={'status':'UNKNOWN','reason':type(e).__name__+': '+str(e)[:180]}
    robustness=task.get('robustness')
    if robustness:
        variants=robustness.get('final_variations' if phase=='final' else 'search_variations',[])
        if phase=='final' and variants and all(v in robustness.get('search_variations',[]) for v in variants):
            out['robustness']={'status':'UNKNOWN','reason':'Final check requires a perturbation not used in search'}
            return out
        geometric=[v for v in variants if set(v)=={'number_scale'}]
        physical=[v for v in variants if v not in geometric]
        if variants and (not physical or (task.get('fem') and out['fem']['status']=='PASS')):
            rows=[geometric_variation(code,task['code'],actual['faces'],float(v['number_scale'])) for v in geometric]
            for v in physical:
                if not set(v)<= {'young_scale','force_scale','mesh_scale'}:
                    rows.append({'status':'UNKNOWN','reason':'Unsupported perturbation'});continue
                try:rows.append(fem(solid,task['fem'],v))
                except Exception as e:rows.append({'status':'UNKNOWN','reason':type(e).__name__})
            status='FAIL' if any(r['status']=='FAIL' for r in rows) else ('PASS' if all(r['status']=='PASS' for r in rows) else 'UNKNOWN')
            out['robustness']={'status':status,'variations':variants,'results':rows}
    return out

if __name__=='__main__':
    try:result=run(json.loads(Path(sys.argv[1]).read_text()))
    except Exception as e:result={'geometry':{'status':'FAIL','reason':type(e).__name__+': '+str(e)[:180]}}
    Path(sys.argv[2]).write_text(json.dumps(result,allow_nan=False))
