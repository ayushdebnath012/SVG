from pathlib import Path
import requests,struct,io,zipfile,json,zlib,hashlib,csv
D=Path('cvpr2027/data/web-cad-fem-more-families/deepwheel');D.mkdir(parents=True,exist_ok=True);url='https://drive.usercontent.google.com/download?id=1W4ullba80EpwylUYuSkuqxjkTiwQ06zn&export=download&confirm=t';size=7613228671
sess=requests.Session()
def ran(start,end):
 r=sess.get(url+f'&range_audit={start}_{end}',headers={'Range':f'bytes={start}-{end}'},timeout=180);r.raise_for_status();assert r.status_code==206 and r.headers['Content-Range'].startswith(f'bytes {start}-{end}/'),r.headers;assert len(r.content)==end-start+1;return r.content
b=ran(size-65557,size-1);pos=b.rfind(b'PK\x05\x06');assert pos>=0;e=struct.unpack('<4s4H2IH',b[pos:pos+22]);cdsize,cdoff=e[5:7];print('Central directory',cdsize,cdoff,e[4],flush=True)
if cdoff==0xffffffff or cdsize==0xffffffff:
 loc=struct.unpack('<4sIQI',b[pos-20:pos]);assert loc[0]==b'PK\x06\x07';z64=struct.unpack('<4sQ2H2I4Q',ran(loc[2],loc[2]+55));cdsize,cdoff=z64[-2:];print('ZIP64 directory',cdsize,cdoff,flush=True)
cd=ran(cdoff,cdoff+cdsize-1);entries=[];i=0
while i<len(cd):
 assert cd[i:i+4]==b'PK\x01\x02'
 h=struct.unpack('<4s6H3I5H2I',cd[i:i+46]);nl,el,cl=h[10:13];name=cd[i+46:i+46+nl].decode();entries.append(dict(name=name,method=h[4],crc=h[7],compressed_bytes=h[8],bytes=h[9],local_offset=h[16]));i+=46+nl+el+cl
for e in entries:
 if e['local_offset']==0xffffffff:
  # Resolve ZIP64 extended local offsets in central directory.
  cursor=0
  while cursor<len(cd):
   h=struct.unpack('<4s6H3I5H2I',cd[cursor:cursor+46]);nl,el,cl=h[10:13];name=cd[cursor+46:cursor+46+nl].decode()
   if name==e['name']:
    extra=cd[cursor+46+nl:cursor+46+nl+el];j=0
    while j<len(extra):
     tag,length=struct.unpack('<HH',extra[j:j+4]);data=extra[j+4:j+4+length]
     if tag==1:
      skip=8*(int(e['bytes']==0xffffffff)+int(e['compressed_bytes']==0xffffffff));e['local_offset']=struct.unpack('<Q',data[skip:skip+8])[0];break
     j+=4+length
    break
   cursor+=46+nl+el+cl
(D/'original-cad-archive-members.json').write_text(json.dumps(entries,indent=2))
rows=list(csv.DictReader((D/'deepwheel_sim_results.csv').open()));print('CSV',len(rows),'STEP',len(entries), 'names',[(x['name']) for x in entries[:3]],flush=True)
# Source STL/STEP names are structured; original result ID is the full base stem.
mapping={Path(x['name']).stem:x for x in entries if x['name'].lower().endswith(('.stp','.step'))}
matched=[r for r in rows if r['file_name'] in mapping];print('Exact stem matched',len(matched), 'CSV first',rows[:3],flush=True)
if not matched:
 # Publisher STEP file has CAD process suffix after the original file_name, not a substring guess.
 for r in rows:
  candidates=[e for e in entries if Path(e['name']).name.startswith(r['file_name']+'_')]
  if len(candidates)==1: r['cad_member']=candidates[0]['name'];matched.append(r)
 print('Unique suffix matched',len(matched),flush=True)
else:
 for r in matched:r['cad_member']=mapping[r['file_name']]['name']
(D/'source-result-cad-index.json').write_text(json.dumps(matched,indent=2));assert len(matched)>0
selected=sorted(matched,key=lambda r:float(r['Mode7 Freq']));ids=sorted(set([round(i*(len(selected)-1)/9) for i in range(10)]));manifest=[]
for ix in ids:
 row=selected[ix];ent=next(e for e in entries if e['name']==row['cad_member']);offset=ent['local_offset'];h=ran(offset,offset+29);v=struct.unpack('<4s5H3I2H',h);assert v[0]==b'PK\x03\x04';start=offset+30+v[-2]+v[-1];b=ran(start,start+ent['compressed_bytes']-1);data=zlib.decompress(b,-15) if ent['method']==8 else b;assert len(data)==ent['bytes'] and zlib.crc32(data)&0xffffffff==ent['crc'];out=D/'cad'/Path(ent['name']).name;out.parent.mkdir(exist_ok=True);out.write_bytes(data)
 manifest.append(dict(result=row,cad='cad/'+out.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),source_archive_url=url,archive_member=ent['name'],source_zip_crc=ent['crc'],zip_crc_pass=True));print('Downloaded',out.name,len(data),flush=True)
(D/'selected-pairs.json').write_text(json.dumps(manifest,indent=2));print('Completed selected pairs',len(manifest))
