"""Verify and package an already assembled v1.4 folder; leave earlier releases intact."""
import argparse,hashlib,json,shutil,subprocess,sys,zipfile
from pathlib import Path
from verify_v14 import verify

def finish(p,copy_to=None):
 result=verify(p)
 (p/'evaluator/verification.json').write_text(json.dumps(result,indent=2)+'\n')
 for d in list(p.rglob('__pycache__')):shutil.rmtree(d)
 files=sorted(f for f in p.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt')
 def sha(f):
  h=hashlib.sha256()
  with f.open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block)
  return h.hexdigest()
 lines=[sha(f)+'  '+str(f.relative_to(p)) for f in files]
 (p/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n')
 archive=p.parent/(p.name+'.zip');temp=archive.parent/(archive.name+'.tmp')
 with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for f in sorted(p.rglob('*')):
   if f.is_file():z.write(f,p.name+'/'+str(f.relative_to(p)))
 with zipfile.ZipFile(temp) as z:
  assert z.testzip() is None
  assert len(z.namelist())==len(set(z.namelist()))
  assert z.read(p.name+'/evaluator/verification.json')==(p/'evaluator/verification.json').read_bytes()
 temp.replace(archive)
 for line in lines:
  h,name=line.split('  ',1);assert sha(p/name)==h
 if copy_to:
  dest=copy_to/p.name
  assert dest.resolve()!=p.resolve()
  shutil.copytree(p,dest,dirs_exist_ok=True)
  # Remove stale files only in the matching v1.4 destination, never earlier releases.
  wanted={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file()}
  for f in dest.rglob('*'):
   if f.is_file() and str(f.relative_to(dest)) not in wanted:f.unlink()
  for line in lines:
   h,name=line.split('  ',1);assert sha(dest/name)==h
  shutil.copy2(archive,copy_to/archive.name);assert sha(archive)==sha(copy_to/archive.name)
 report={'version':'1.4','checksummed_files':len(files),'checksum_verification_passed':True,'zip_crc_passed':True,'zip_bytes':archive.stat().st_size,'zip_sha256':sha(archive),'copied_folder_and_zip_verified':bool(copy_to)}
 (p.parent/'cadfem-bench-v1.4-package-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--copy-to',type=Path);x=a.parse_args();finish(x.package.resolve(),x.copy_to.resolve() if x.copy_to else None)
