"""Verify downloads and compare original native-result arrays with saved FRD fields."""
from pathlib import Path
import json,hashlib,zipfile,struct,xml.etree.ElementTree as E,gc
import numpy as np
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-machine-parts-search');total=0
for name in ['web-cad-fem-cycloidal-drive','web-cad-fem-engine-tbc','web-cad-fem-piston-drawing']:
 R=D/name;m=json.loads((R/'download-manifest.json').read_text())
 for f in m['files']:
  b=(R/f['path']).read_bytes();assert len(b)==f['bytes'];assert hashlib.sha256(b).hexdigest()==f['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['git_blob_sha1'];total+=1
R=D/'web-cad-fem-cycloidal-drive';c=json.loads((R/'catalog.json').read_text());comparisons=[]
for r in c['records']:
 if not r.get('primary_component_candidate'):continue
 f=R/r['file'];fc=(R/'fem/pla/FEM_Disk.FCStd') if f.name=='DiskPLA_fixed.frd' else next(f.parent.glob('*.FCStd'));a=np.load(R/r['exact_ascii_field_copy']);savedU=a['DISP'];savedVM=a['derived_vm'];checks=[]
 with zipfile.ZipFile(fc) as z:
  objects=[];current=None
  for event,element in E.iterparse(z.open('Document.xml'),events=('start','end')):
   if event=='start' and element.tag=='Object':current={'name':element.attrib.get('name'),'properties':{}}
   elif event=='end' and element.tag=='Property':
    if current is not None and element.attrib.get('name') in ['DisplacementVectors','vonMises','NodeNumbers']:current['properties'][element.attrib['name']]=E.tostring(element,encoding='unicode')
    element.clear()
   elif event=='end' and element.tag=='Object':
    if current and 'DisplacementVectors' in current['properties']:objects.append(current)
    current=None;element.clear()
  for object_meta in objects:
   ob=E.Element('Object',{'name':object_meta['name']});props=E.SubElement(ob,'Properties')
   for xml in object_meta['properties'].values():props.append(E.fromstring(xml))
   pr=ob.find('./Properties/Property[@name="DisplacementVectors"]/VectorList');vm=ob.find('./Properties/Property[@name="vonMises"]/FloatList')
   if pr is None or vm is None:continue
   b=z.read(pr.attrib['file']);n=struct.unpack('<I',b[:4])[0];U=np.frombuffer(b,dtype='<f8',offset=4).reshape(n,3);ids=np.array([int(v.attrib['v']) for v in ob.findall('./Properties/Property[@name="NodeNumbers"]/IntegerList/I')]);bi=z.read(vm.attrib['file']);v=np.frombuffer(bi,dtype='<f8',offset=4)
   if len(ids)!=len(a['DISP_node_ids']) or set(ids)!=set(a['DISP_node_ids']):continue
   idx={n:i for i,n in enumerate(a['DISP_node_ids'])};S=np.array([savedU[idx[n]] for n in ids]);idx={n:i for i,n in enumerate(a['STRESS_node_ids'])};sv=np.array([savedVM[idx[n]] for n in ids]);same=np.allclose(U,S,rtol=1e-12,atol=1e-14) and np.allclose(v,sv,rtol=1e-12,atol=1e-14)
   checks.append({'native_result_object':ob.attrib['name'],'exact_saved_displacement_and_derived_vm_match':bool(same),'max_U_diff_mm':float(np.max(abs(U-S))),'max_vm_diff_MPa':float(np.max(abs(v-sv)))})
 assert any(x['exact_saved_displacement_and_derived_vm_match'] for x in checks),str(fc)
 print('Matched',str(fc.relative_to(R)),flush=True);gc.collect();r['native_CAD_file']=str(fc.relative_to(R));r['native_result_object_verification']=checks;comparisons.append({'frd':r['file'],'native_file':str(fc.relative_to(R)),'matches':checks})
(R/'catalog.json').write_text(json.dumps(c,indent=2,allow_nan=False)+'\n');out={'original_downloads_verified':total,'primary_FRD_native_result_matches':len(comparisons),'result_comparisons':comparisons,'policy':'Original scripts never executed; no solve, CAD generation or model calls.'};(T/'source-verification.json').write_text(json.dumps(out,indent=2)+'\n');print('Verified',total,'downloads and',len(comparisons),'native/FRD result matches')
