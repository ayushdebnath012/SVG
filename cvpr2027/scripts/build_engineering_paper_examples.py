import sys,json,gzip,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
import engsvg_svg_edit as E
import pymupdf as fitz
from svgpatchlab.core.xml import normalized_tree,parse_svg
out=ROOT/'runs/paper-engineering-examples-20261001';fig=ROOT/'paper/network/figures'
records={}
for name in ['truss-section','bridge-load','bridge-topology','plate-holes']:
 old=ROOT/'runs/engsvg-svg2svg-verified-20260925'/name
 saved=json.loads((old/'result.json').read_text())
 result=E.save_edit(old/'source.svg',saved['request'],out/name)
 assert normalized_tree(parse_svg((out/name/'edited.svg').read_text()))==normalized_tree(parse_svg((old/'edited.svg').read_text()))
 records[name]=result
want='engsvg-7ba3ff23a1ece2269757:svg-edit-2'
found=None
for shard in sorted((ROOT/'data/engsvg-dataset-factory-v2').glob('tasks-*.jsonl.gz')):
 with gzip.open(shard,'rt') as f:
  for line in f:
   row=json.loads(line)
   if row['id']==want:found=row;break
 if found:break
assert found
head,source=found['prompt'].split('\nCurrent SVG:\n',1);req=head.split('Request: ',1)[1]
p=out/'plate-violation';p.mkdir(exist_ok=True);(p/'input.svg').write_text(source)
r=E.save_edit(p/'input.svg',req,p);assert r['edit_fidelity_pass'] and not r['engineering_check_pass'];records['plate-violation']=r
(out/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
# Keep complete SVGs as editable assets and vector PDFs for the full examples.
for name in records:
 for state in ['source','edited']:
  s=(out/name/f'{state}.svg').read_text();(fig/f'editor-{name}-{state}.svg').write_text(s)
  d=fitz.open(stream=s.encode(),filetype='svg');(fig/f'editor-{name}-{state}.pdf').write_bytes(d.convert_to_pdf())
# Figure retains actual geometry, normalizes colors and summarizes annotations separately.
ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
def panel(s,x,y,w,h,crop):
 root=ET.fromstring(E._canonical_style(s,E._style(s)))
 a,b,c,d=map(float,crop.split());scale=min(w/c,h/d)
 tx=x+(w-c*scale)/2-scale*a;ty=y+(h-d*scale)/2-scale*b
 ident=f'clip{int(x)}_{int(y)}'
 body=''.join(ET.tostring(ch,encoding='unicode') for ch in root if ch.tag.split('}')[-1] not in ('text','rect') and (ch.tag.split('}')[-1]=='g' or 'mounting plate' not in s))
 return f'<defs><clipPath id="{ident}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs><g clip-path="url(#{ident})"><g transform="translate({tx} {ty}) scale({scale})">{body}</g></g>'

def text(x,y,s,size=22,color='#18364c',weight='normal'):
 from html import escape
 return f'<text x="{x}" y="{y}" font-family="DejaVu Sans" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(s)}</text>'
parts=[f'<svg xmlns="{ns}" viewBox="0 0 1400 630" width="1400" height="630"><rect width="1400" height="630" fill="white"/>']
parts += [text(20,30,'PARSE + PATCH + RE-IMPORT + ENGINEERING CHECK',25,weight='bold'),text(25,69,'Source SVG',21),text(730,69,'Edited SVG',21)]
for name,y,crop in [('bridge-topology',85,'85 425 950 200'),('plate-violation',350,'180 160 660 575')]:
 for j,state in enumerate(['source','edited']):parts.append(panel((out/name/f'{state}.svg').read_text(),15+705*j,y,660,190,crop))
parts += [text(25,291,'Structural patch: 6 to 8 panels; 21 to 29 members.',22,weight='bold'),text(25,321,'FEM re-solve: peak stress 84.38 → 112.50 MPa; equilibrium passes.',20)]
parts += [text(25,580,'Increase hole diameters by 6 mm: edit is faithful; clearance fails.',22,'#ac2733','bold'),text(25,612,'Recovered edge distance: 15 → 12 mm, below the stated 15 mm minimum.',20)]
parts.append('</svg>');svg=''.join(parts);(fig/'editor-overview.svg').write_text(svg)
d=fitz.open(stream=svg.encode(),filetype='svg');(fig/'editor-overview.pdf').write_bytes(d.convert_to_pdf());d[0].get_pixmap().save(str(ROOT/'tmp/editor-overview.png'))
(out/'provenance.json').write_text(json.dumps({'plate_violation_dataset_id':want,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'figure_presentation':'Original geometry; colors normalized and annotations summarized','artifacts':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*/*.svg')}},indent=2)+'\n')
print(json.dumps({n:{k:v[k] for k in ['mode','edit_fidelity_pass','engineering_check_pass']} for n,v in records.items()},indent=2))
