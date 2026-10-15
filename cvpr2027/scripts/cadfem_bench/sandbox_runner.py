"""Provider-neutral offline replay; executes only explicitly submitted main.py.

macOS: kernel-enforced restrictions on home data, evaluator paths, writes and network.
Docker: preferred portable backend; pinned image, no network, readonly root, pids/resource limits.
Execution evidence alone never auto-approves FEM setup or field correctness.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,re,resource,shutil,signal,subprocess,tempfile,time
from pathlib import Path


def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def inventory(p):
 out={}
 for f in sorted(p.rglob('*')):
  if f.is_symlink():raise ValueError('symlink artifacts rejected: '+str(f))
  if f.is_file():out[str(f.relative_to(p))]={'sha256':sha(f),'bytes':f.stat().st_size}
 return out

def prepare(package,task_id,submission,job,suite,model_id,run_id):
 if job.exists():raise ValueError('new attempt directory required')
 if suite=='primary':tasks=jl(package/'candidate/tasks.jsonl');base=package/'candidate/tasks'
 else:tasks=jl(package/'evaluator/suites'/suite/'tasks.jsonl');base=package/'evaluator/suites'/suite/'inputs'
 t=next((x for x in tasks if x['task_id']==task_id),None)
 if t is None:raise ValueError('task not in requested suite')
 code=inventory(submission)
 if 'main.py' not in code or not code['main.py']['bytes']:raise ValueError('nonempty submitted main.py required')
 if sum(v['bytes'] for v in code.values())>10_000_000:raise ValueError('submission source exceeds 10 MB')
 job.mkdir(parents=True);(job/'outputs').mkdir();(job/'cache').mkdir();(job/'tmp').mkdir();(job/'inputs').mkdir()
 shutil.copytree(submission,job/'submission')
 for i in t['inputs']:
  rel=Path(i['path']).relative_to(Path('tasks')/task_id);src=base/task_id/rel
  if src.is_symlink() or sha(src)!=i['sha256']:raise ValueError('input hash mismatch')
  dst=job/'inputs'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 write(job/'inputs/task.json',t)
 rec={'release':'1.4','suite':suite,'task_id':task_id,'task_sha256':hashlib.sha256(json.dumps(t,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'run_id':run_id,'model_id':model_id,'inputs':inventory(job/'inputs'),'submission':inventory(job/'submission'),'status':'prepared','model_api_called':False,'public_source_contamination':'possible'}
 write(job/'protocol.json',rec);return rec


def mac_profile(job,runtime,package):
 base=subprocess.run([str(runtime),'-I','-c','import sys; print(sys.base_prefix)'],capture_output=True,text=True,check=True).stdout.strip()
 bases={runtime.parent.parent.resolve(),Path(base).resolve(),Path(base),runtime.resolve().parent.parent}
 # Allow rules more specific than /Users permit only runtime and this job.
 # System paths outside /Users remain readable; writes and network are denied.
 esc=lambda p:json.dumps(str(p))
 allowed=' '.join('(subpath '+esc(p)+')' for p in sorted(bases,key=str))
 s='(version 1)\n(allow default)\n(deny network*)\n(deny file-link)\n(deny appleevent-send)\n(deny mach-lookup)\n(allow mach-lookup (global-name "com.apple.system.opendirectoryd.libinfo"))\n(deny process-info*)\n(allow process-info* (target self))\n(deny file-read* (subpath "/Users"))\n'
 s+='(allow file-read* '+allowed+' (subpath '+esc(job)+'))\n'
 s+='(deny file-read* (subpath '+esc(package)+'))\n(allow file-read-metadata)\n'
 s+='(deny file-write*)\n(allow file-write* (subpath '+esc(job/'outputs')+') (subpath '+esc(job/'tmp')+') (subpath '+esc(job/'cache')+') (literal "/dev/null"))\n'
 return s,base


def replay(package,job,backend,runtime,image,wall,cpu,ram_mb):
 rec=json.loads((job/'protocol.json').read_text())
 if (job/'execution.json').exists():raise ValueError('attempt already executed')
 if inventory(job/'inputs')!=rec['inputs'] or inventory(job/'submission')!=rec['submission']:raise ValueError('frozen inputs or code changed')
 env={'PATH':str(runtime.parent)+':/usr/bin:/bin','TZ':'UTC','LANG':'en_US.UTF-8','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','VECLIB_MAXIMUM_THREADS':'2','TMPDIR':str(job/'tmp'),'XDG_CACHE_HOME':str(job/'cache'),'CADFEM_INPUT_DIR':str(job/'inputs'),'CADFEM_OUTPUT_DIR':str(job/'outputs')}
 sandbox_info={};profile=None;name=None
 if backend=='macos':
  if platform.system()!='Darwin' or not Path('/usr/bin/sandbox-exec').exists():raise RuntimeError('macOS sandbox unavailable; refusing unsandboxed execution')
  profile,base=mac_profile(job,runtime,package);(job/'profile.sb').write_text(profile)
  cmd=['/usr/bin/sandbox-exec','-f',str(job/'profile.sb'),str(runtime),'-I','-B',str(job/'submission/main.py')]
  sandbox_info={'backend':'macos-seatbelt','python_sha256':sha(runtime.resolve()),'runtime_prefix':str(runtime.parent.parent),'base_prefix':base,'network':'denied','write_access':'outputs/tmp/cache only','data_read_policy':'home data denied except runtime/job; package explicitly denied; system data outside home readable','profile_sha256':hashlib.sha256(profile.encode()).hexdigest()}
 elif backend=='docker':
  if not shutil.which('docker'):raise RuntimeError('Docker unavailable; refusing unsandboxed execution')
  if not image or not re.fullmatch(r'[^\s]+@sha256:[a-f0-9]{64}',image):raise ValueError('pinned image name@sha256:digest required')
  check=subprocess.run(['docker','image','inspect',image,'--format','{{.Id}}'],capture_output=True,text=True,timeout=20)
  if check.returncode:raise RuntimeError('pinned runtime image must already be installed; no automatic pull')
  name='cadfem-'+hashlib.sha256(str(job).encode()).hexdigest()[:16]
  cmd=['docker','run','--rm','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','128','--memory',str(ram_mb)+'m','--cpus','2','--user',str(os.getuid())+':'+str(os.getgid()),'--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--mount','type=bind,src='+str(job/'inputs')+',dst=/work/inputs,readonly','--mount','type=bind,src='+str(job/'submission')+',dst=/work/submission,readonly','--mount','type=bind,src='+str(job/'outputs')+',dst=/work/outputs','--workdir','/work/outputs','--env','CADFEM_INPUT_DIR=/work/inputs','--env','CADFEM_OUTPUT_DIR=/work/outputs',image,'python','-I','-B','/work/submission/main.py']
  sandbox_info={'backend':'docker','image':image,'image_id':check.stdout.strip(),'network':'none','root':'readonly','memory_mb':ram_mb,'pids':128}
 else:raise ValueError('unsupported sandbox backend')
 def limits():
  resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu+1));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_NOFILE,(512,512))
 start=time.monotonic();why=None;maxrss=0
 with (job/'sandbox.log').open('wb') as log:
  process=subprocess.Popen(cmd,cwd=job/'outputs',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=limits)
  while process.poll() is None:
   if time.monotonic()-start>wall:why='wall_time_limit'
   if backend=='macos':
    ps=subprocess.run(['/bin/ps','-axo','pgid=,rss='],capture_output=True,text=True)
    rss=sum(int(line.split()[1]) for line in ps.stdout.splitlines() if len(line.split())==2 and line.split()[0]==str(process.pid));maxrss=max(maxrss,rss)
    if rss>ram_mb*1024:why='process_group_memory_limit'
   if why:
    if name:subprocess.run(['docker','kill',name],capture_output=True)
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    break
   time.sleep(.2)
  code=process.wait()
 try:outputs=inventory(job/'outputs');error=None
 except Exception as e:outputs={};error=str(e)
 frozen=inventory(job/'inputs')==rec['inputs'] and inventory(job/'submission')==rec['submission']
 result={'release':'1.4','run_id':rec['run_id'],'task_id':rec['task_id'],'model_id':rec['model_id'],'task_sha256':rec['task_sha256'],'sandbox':sandbox_info,'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'wall_limit_seconds':wall,'cpu_limit_seconds_per_process':cpu,'ram_limit_mb':ram_mb,'peak_process_group_rss_kb':maxrss,'termination_reason':why,'outputs':outputs,'output_inventory_error':error,'frozen_inputs_unchanged':frozen,'execution_verified':code==0 and not why and not error and frozen,'physics_verified':False,'workflow_verified':False,'note':'Sandbox execution is evidence only; setup/mesh/field/convergence need trusted validators. No review is automatically fabricated.'}
 write(job/'execution.json',result);return result


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','replay']);ap.add_argument('--package',type=Path,required=True);ap.add_argument('--job',type=Path,required=True);ap.add_argument('--task-id');ap.add_argument('--submission',type=Path);ap.add_argument('--suite',choices=['primary','calibration','reserved-public','related-public'],default='primary');ap.add_argument('--model-id');ap.add_argument('--run-id');ap.add_argument('--backend',choices=['macos','docker'],default='macos');ap.add_argument('--python',type=Path,default=Path(os.sys.executable));ap.add_argument('--image');ap.add_argument('--wall-seconds',type=int,default=600);ap.add_argument('--cpu-seconds',type=int,default=600);ap.add_argument('--ram-mb',type=int,default=8192);a=ap.parse_args()
 p=a.package.resolve();job=a.job.resolve();runtime=a.python.absolute()
 if not runtime.is_file() or job.is_relative_to(p):ap.error('trusted runtime required and job must be outside package')
 try:
  if a.action=='prepare':
   if not all([a.task_id,a.submission,a.model_id,a.run_id]):ap.error('prepare requires task, submission, model-id and run-id')
   r=prepare(p,a.task_id,a.submission.resolve(),job,a.suite,a.model_id,a.run_id)
  else:r=replay(p,job,a.backend,runtime,a.image,a.wall_seconds,a.cpu_seconds,a.ram_mb)
  print(json.dumps(r,indent=2))
 except Exception as e:
  if a.action=='replay':write(job/'execution.json',{'status':'infrastructure_blocked','error':str(e),'execution_verified':False,'physics_verified':False})
  ap.exit(1,str(e)+'\n')
if __name__=='__main__':main()
