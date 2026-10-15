"""Hierarchical verification; unknown checks never become required passes."""
import hashlib,json,subprocess,tempfile,time,math
from pathlib import Path
from .core import digest
ROOT=Path(__file__).resolve().parents[2]

class Verifier:
    def __init__(self,python=None,semantic=None,timeout=180,max_jobs=100):
        self.python=str(python or ROOT/'tmp/cad-runtime/bin/python')
        self.semantic=semantic;self.timeout=timeout;self.max_jobs=max_jobs;self.jobs=0
        self.cache={};self.deadline=float('inf')
        self.version=digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__),Path(__file__).with_name('worker.py'),ROOT/'scripts/cad_edit_contracts.py',ROOT/'scripts/verify_mechanical_cad_edits.py',ROOT/'scripts/mechanical_cad_fem.py']})

    def native(self,task,candidate,phase,stage,export_path=None):
        remaining=self.deadline-time.monotonic()
        if self.jobs>=self.max_jobs or remaining<=0:
            return {'geometry':{'status':'UNKNOWN','reason':'Execution budget exhausted'}}
        self.jobs+=1
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'input.json';dst=Path(d)/'result.json'
            payload=dict(task=task,candidate=candidate,phase=phase,stage=stage)
            if export_path:payload['export_path']=str(Path(export_path).resolve())
            src.write_text(json.dumps(payload))
            try:
                subprocess.run([self.python,str(Path(__file__).with_name('worker.py')),str(src),str(dst)],
                    timeout=min(self.timeout,remaining),capture_output=True,check=True)
                return json.loads(dst.read_text())
            except Exception as e:return {'geometry':{'status':'UNKNOWN','reason':type(e).__name__}}

    def __call__(self,task,candidate,phase='search'):
        key=digest([task,candidate,phase,self.version])
        if phase!='final' and key in self.cache:return self.cache[key]
        stages={k:{'status':'UNKNOWN','reason':'Not evaluated'} for k in ['geometry','constraints','semantics','fem','robustness']}
        raw=self.native(task,candidate,phase,'geometry')
        stages.update({k:raw[k] for k in stages if k in raw})
        if stages['geometry']['status']=='PASS' and stages['constraints']['status']=='PASS':
            spec=task.get('semantics',{})
            if spec.get('mode')=='explicit_constraints' and spec.get('complete') is True and task['constraints']:
                stages['semantics']={'status':'PASS','confidence':1.,'basis':'Caller-declared complete measurable task contract'}
            elif self.semantic and time.monotonic()<self.deadline:
                try:
                    tools={'execute':{'gates':True,'error':None,'volume':raw['geometry']['metrics']['volume'],'changed':raw.get('changed')},'numbers':raw.get('numbers',[])}
                    if hasattr(self.semantic,'timeout'):self.semantic.timeout=min(self.timeout,self.deadline-time.monotonic())
                    stages['semantics']=self.semantic({k:task[k] for k in ['code','instruction']},candidate,tools)
                except Exception as e:stages['semantics']={'status':'UNKNOWN','reason':type(e).__name__}
        if all(stages[k]['status']=='PASS' for k in ('geometry','constraints','semantics')) and (task.get('fem') or task.get('robustness')):
            physics=self.native(task,candidate,phase,'physics')
            for k in ['geometry','constraints','fem','robustness']:
                if k in physics:stages[k]=physics[k]
        required=task['required'];statuses=[stages[k]['status'] for k in required]
        status='FAIL' if 'FAIL' in statuses else ('PASS' if all(s=='PASS' for s in statuses) else 'UNKNOWN')
        confidence=float(stages['semantics'].get('confidence',0))
        if not math.isfinite(confidence) or not 0<=confidence<=1:confidence=0;status='UNKNOWN'
        robustness=1. if stages['robustness']['status']=='PASS' else 0.
        edits=raw.get('edited_lines',1000);objectives=[confidence,robustness,-float(edits)]
        score=(1 if status=='PASS' else 0)+confidence+.1*robustness-.001*edits
        verdict=dict(status=status,stages=stages,objectives=objectives,score=score,
            diagnosis=[{'stage':k,**v} for k,v in stages.items() if k in required and v['status']!='PASS'],
            tool_version=self.version,phase=phase)
        self.cache[key]=verdict
        return verdict

    def export(self,task,candidate,path):
        result=self.native(task,candidate,'export','geometry',export_path=path)
        if result.get('exported') and Path(path).exists():return {'status':'PASS','path':str(path)}
        return {'status':'UNKNOWN','reason':result.get('geometry',{}).get('reason','CAD export failed')}
