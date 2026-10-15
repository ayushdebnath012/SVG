"""Read published MPH ZIP directories using HTTP ranges; no FEM computation."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import io,json,re,requests,zipfile
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'data/femcad-hard-v1/reference-assets.json'
class RemoteFile:
 def __init__(self,url):
  self.url=url;self.pos=0;self.session=requests.Session()
  r=self.session.get(url,headers={'Range':'bytes=-65536'},stream=True,timeout=30)
  if r.status_code!=206:r.close();raise ValueError('Range request unsupported')
  self.size=int(r.headers['Content-Range'].split('/')[-1]);self.tail=r.content;self.tailstart=self.size-len(self.tail);r.close()
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
  return self.pos
 def tell(self):return self.pos
 def read(self,n=-1):
  n=min(self.size-self.pos,n if n>=0 else self.size-self.pos)
  if n<=0:return b''
  if n>10_000_000:raise ValueError('Bounded archive metadata read exceeded')
  if self.pos>=self.tailstart:b=self.tail[self.pos-self.tailstart:self.pos-self.tailstart+n]
  else:
   r=self.session.get(self.url,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'},stream=True,timeout=30)
   if r.status_code!=206:r.close();raise ValueError('Range request unsupported')
   b=r.content;r.close()
  self.pos+=len(b);return b
 def seekable(self):return True
 def close(self):self.session.close()
def one(t):
 for f in t['files']:
  if f['role']!='solver_model' or f['name'].endswith('_materials.mph'):continue
  remote=None
  try:
   if f.get('local'):z=zipfile.ZipFile(ROOT/f['local'])
   else:remote=RemoteFile(f['url']);z=zipfile.ZipFile(remote)
   with z:
    entries=[{'name':a.filename,'bytes':a.file_size,'compressed_bytes':a.compress_size} for a in z.infolist()]
   if remote:remote.close()
   solutions=[a for a in entries if re.search(r'(^|/)solution\w*\.mphbin$',a['name'],re.I)]
   meshes=[a for a in entries if re.search(r'(^|/)(?:x?mesh)\w*\.mphbin$',a['name'],re.I)]
   f.update(archive_entry_count=len(entries),solution_binary_entries=solutions,mesh_binary_entries=meshes,
     solution_storage_status='Published binary solution entries verified' if solutions else 'No solution binary entries found',
     solution_contents_validation='Archive entries verified; solution values, convergence and numerical correctness not validated; COMSOL needed to interpret/export fields.')
   f.pop('solution_named_entries',None);f.pop('mesh_named_entries',None)
   p=ROOT/'tmp/femcad-reference-assets'/t['id']/(f['name']+'.archive-index.json');p.write_text(json.dumps(entries,indent=2)+'\n')
   f['archive_inventory_local']=str(p.relative_to(ROOT))
   print(t['id'],len(solutions),'solution entries',flush=True)
  except Exception as e:
   if remote:remote.close()
   f['archive_inspection_error']=type(e).__name__+': '+str(e)
   print(t['id'],f['archive_inspection_error'],flush=True)
 return t
if __name__=='__main__':
 d=json.loads(PATH.read_text())
 with ThreadPoolExecutor(max_workers=6) as pool:d['studies']=list(pool.map(one,d['studies']))
 PATH.write_text(json.dumps(d,indent=2)+'\n')
