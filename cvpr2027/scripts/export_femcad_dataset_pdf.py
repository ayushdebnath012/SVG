"""Export all 100 source-bound FEMCAD tasks as an illustrated PDF catalog."""
import json,re,html,hashlib
from pathlib import Path
from collections import Counter
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[2]; PROJECT=ROOT/'cvpr2027'; DATA=PROJECT/'data/femcad-source-v2'
OUT=ROOT/'output/pdf/femcad-100-task-catalog.pdf'
TMP=ROOT/'tmp/pdfs';TMP.mkdir(parents=True,exist_ok=True)
rows=[json.loads(s) for s in (DATA/'tasks.jsonl').read_text().splitlines()]
pages=json.loads((DATA/'sources.json').read_text())['pages']; refs={p['url']:i+1 for i,p in enumerate(pages)}
for name,file in [('Body','Arial.ttf'),('Bold','Arial Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,'/System/Library/Fonts/Supplemental/'+file))
W,H=595.276,841.89; M=43; IW=W-2*M
NAVY=HexColor('#142B3D');BLUE=HexColor('#086D89');GRAY=HexColor('#52616D');PALE=HexColor('#EDF3F6');LINE=HexColor('#CFDCE3')
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
c.setTitle('FEMCAD Source v2 - 100 CAD + FEM Tasks');c.setAuthor('FEMCAD dataset catalog; sources: Wolfram Research and MFEM crawl')
page_no=0; bottoms=[]
def esc(t):return html.escape(str(t).replace('–','-').replace('—','-').replace('‑','-').replace('→','->'))
def para(text,x,y,width=IW,size=10.5,leading=15,color=NAVY,bold=False,markup=False):
 st=ParagraphStyle('p',fontName='Bold' if bold else 'Body',fontSize=size,leading=leading,textColor=color,splitLongWords=True)
 p=Paragraph(text if markup else esc(text),st);_,h=p.wrap(width,800)
 assert y-h>=43,(page_no,text[:80],y,h)
 p.drawOn(c,x,y-h);bottoms.append((page_no,y-h));return y-h

def newpage(kicker='DATASET CATALOG',title=None):
 global page_no
 if page_no:c.showPage()
 page_no+=1
 c.setFillColor(NAVY);c.rect(0,H-10,W,10,fill=1,stroke=0)
 c.setFont('Bold',8);c.setFillColor(BLUE);c.drawString(M,H-36,kicker)
 c.setStrokeColor(LINE);c.line(M,39,W-M,39)
 c.setFont('Body',8);c.setFillColor(GRAY);c.drawString(M,26,'FEMCAD Source v2  |  Official-source CAD + FEM tasks');c.drawRightString(W-M,26,str(page_no))
 y=H-60
 if title:y=para(title,M,y,size=24,leading=28,bold=True)-20
 return y

def image_box(f,x,y,w,h):
 im=Image.open(PROJECT/f['local']).convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im)
 c.setFillColor(white);c.setStrokeColor(LINE);c.roundRect(x,y-h,w,h,5,stroke=1,fill=1)
 iw,ih=im.size;scale=min((w-16)/iw,(h-16)/ih)
 c.drawImage(ImageReader(bg.convert('RGB')),x+(w-iw*scale)/2,y-h+(h-ih*scale)/2,iw*scale,ih*scale)
 c.linkURL(f['url'],(x,y-h,x+w,y),relative=0,thickness=0)

def heading(label,y):return para(label.upper(),M,y,size=8.5,leading=12,bold=True,color=BLUE)-5

def ranges(indices):
 out=[]
 for n in indices:
  if not out or n>out[-1][-1]+1:out.append([n])
  else:out[-1].append(n)
 return ', '.join(str(a[0]) if len(a)==1 else f'{a[0]}-{a[-1]}' for a in out)

# Cover / overview.
y=newpage('ILLUSTRATED RESEARCH DATASET','100 tasks in CAD + FEM')
y=para('Engineering geometry. Source-defined physics.',M,y,size=17,leading=23,color=BLUE)-16
y=para('100 cases  /  25 geometry families  /  9 covered categories',M,y,size=11,bold=True)-15
y=para('13 hard  |  55 complex  |  32 hardest',M,y,size=11,color=GRAY)-24
for j,r in enumerate([rows[4],rows[14],rows[20],rows[23]]):image_box(r['figures'][-1],M+(j%2)*(IW/2+6),y-(j//2)*150,IW/2-6,140)
y-=310
y=heading('What this catalog contains',y)
y=para('All 100 task specifications, source geometry images, case selectors, expected outputs and clickable references. Parameter variants share parts: this is not a collection of 100 distinct CAD geometries.',M,y)-16
y=heading('Status and scope',y)
y=para('These are open-book reproduction and generation tasks. Difficulty labels are proposed. No gold answers or model failures have been validated. Accepted cases currently come from Wolfram; the MFEM crawl yielded no selected qualifying case. System Physics remains uncovered.',M,y,size=10,leading=14)-10
para('The drawings are source geometry views, engineering cross-sections or part meshes. Solution-field images and graph plots are excluded. Source images belong to their respective owners.',M,y,size=9,leading=13,color=GRAY)

# Shared instructions - referenced on every task page.
y=newpage('READ BEFORE USING THE TASKS','Shared task requirements')
for title,body in [
 ('1. Reconstruct the CAD','Deliver a reproducible CAD construction and STEP geometry, or planar CAD where the source is 2D. Include the boundary/material region map. Preserve source dimensions, units, fillets and model dimensionality.'),
 ('2. Reproduce the FEM problem','Deliver a mesh, FEM implementation and results.json. Preserve the constitutive law, loads, boundary and initial conditions. The individual task page specifies the analysis and required results.'),
 ('3. Resolve the source inputs','Use the full downloadable code-cell URLs in sources.json, not abbreviated screen-reader captions. Cell indices in this catalog are zero-based HTML input order, not Mathematica In[] labels. Resolve prerequisite definitions from the same page.'),
 ('4. Record dependencies','Resolve and record material-entity values, runtime defaults and installation support files. Report missing dependencies instead of guessing. Examples include the muffler STL files, bracket WXF geometry and condenser meteorological data. These assets are not bundled as solved task inputs.'),
 ('5. Verify the prediction','Include mesh convergence and appropriate balance/residual checks. CAD export and verification requirements are evaluation instructions authored for this dataset, not measurements claimed from the source.'),
 ('6. Avoid evaluation leakage','Split by split_group, not by individual row. The 21 conservative split groups keep related hooks, mufflers, perforated plates and all bracket variants together. Source tutorials contain worked solutions; an image-only evaluation requires a separate input/reference split.'),
 ('Source and validation record','28 unique source images and 1,003 full source-code cells were traced and checked. Structural/provenance checks passed; no FEM solve was performed. The JSONL remains the machine-readable source of record. Legacy numerical assumptions were replaced by official-source bindings.')]:
 y=para(title,M,y,size=12,leading=16,bold=True)-5;y=para(body,M,y,size=10.5,leading=15)-19

# Complete clickable task index, 25 per page.
for start in range(0,100,25):
 y=newpage('CLICKABLE CONTENTS',f'Task index {start+1}-{min(start+25,100)}')
 y=para('Select any task title to jump to its illustrated specification.',M,y,size=10,color=GRAY)-20
 for r in rows[start:start+25]:
  label=f'{r["id"][-3:]}  {r["title"]}'
  y=para(f'<link href="#{r["id"]}" color="#086D89">{esc(label)}</link>',M,y,width=IW-68,size=9.4,leading=12,markup=True)-8
  c.setFont('Body',8);c.setFillColor(GRAY);c.drawRightString(W-M,y+8,r['tier'])

# One full case per page.
for r in rows:
 y=newpage(f'{r["id"]}  /  {r["category"].upper()}',r['title'])
 c.bookmarkPage(r['id']);c.addOutlineEntry(r['id']+' '+r['title'],r['id'],level=0,closed=True)
 y=para(f'{r["tier"].upper()} (proposed)   |   Family: {r["geometry_family"]}   |   Split: {r["split_group"]}',M,y,size=8.5,leading=12,color=GRAY)-14
 figs=r['figures'][:2];gap=12;fw=(IW-gap*(len(figs)-1))/len(figs)
 for j,f in enumerate(figs):image_box(f,M+j*(fw+gap),y,fw,167)
 y-=181
 y=para('Source engineering geometry. Click an image to open its original.',M,y,size=8,leading=11,color=GRAY)-14
 y=heading('CAD + FEM task',y)
 y=para(r['prompt'].split('\n\n')[0],M,y,size=11,leading=16)-16
 y=heading('Case selection',y)
 case=r['source_case'];kind=case['type']
 if kind=='published_sweep_member':
  value=case.get('exact_expression',str(case['value']))
  select=f'{case.get("model", "").capitalize()+": " if case.get("model") else ""}{case["parameter"]} = {value} {case["unit"]}. Source sweep: {case["source_expression"]}.'
 elif kind=='published_sweep':select=f'{case["parameter"]}: {", ".join(map(str,case["values"]))} ({case["unit"]}). Run the complete listed comparison.'
 else:select=case.get('name','Documented analysis identified by the source cells below; preserve all prerequisites and any loading history.')
 y=para(select,M,y,size=10.5,leading=15)-15
 y=heading('Required results',y)
 y=para(r['required_results'],M,y,size=10.5,leading=15)-16
 y=heading('Source binding',y)
 u=r['source']['url'];g=r['source']['geometry_url']
 ref=refs[u];title=next(p['title'] for p in pages if p['url']==u)
 y=para(f'<link href="{html.escape(u,quote=True)}" color="#086D89">[{ref:02}] {esc(title)}</link>',M,y,size=9.5,leading=13,markup=True)-4
 y=para('Input cells: '+ranges(r['source']['focus_cell_indices'])+'.',M,y,size=9,leading=12,color=GRAY)-4
 if g!=u:
  y=para(f'<link href="{html.escape(g,quote=True)}" color="#086D89">Geometry construction: source [{refs[g]:02}]</link>',M,y,size=9.5,leading=13,markup=True)-4
 y-=11
 para('Apply all shared requirements on page 2. Dependency resolution, solver validation and model-failure testing remain pending.',M,y,size=8.5,leading=12,color=GRAY)

# Full reference addresses; images individually link to their original files.
for start in range(0,len(pages),7):
 y=newpage('OFFICIAL SOURCE REFERENCES',f'Sources {start+1}-{min(start+7,len(pages))}')
 for i,p in enumerate(pages[start:start+7],start+1):
  y=para(f'[{i:02}] {p["title"]}',M,y,size=11,leading=15,bold=True)-5
  y=para(f'<link href="{html.escape(p["url"],quote=True)}" color="#086D89">{esc(p["url"])}</link>',M,y,size=8.5,leading=12,markup=True)-7
  y=para('Full code cells and cached-page SHA256: sources.json.',M,y,size=8,leading=11,color=GRAY)-22
 para('Scope note: mfem.org was crawled (150 pages), but no case from that crawl met the selected combined CAD/FEM/engineering-drawing criteria. This catalog does not add physical setups to geometry-only examples.',M,y,size=9,leading=13,color=GRAY)
c.save()
(TMP/'pdf-build.json').write_text(json.dumps({'pdf':str(OUT),'pages':page_no,'tasks':len(rows),'minimum_text_bottom_pt':min(y for _,y in bottoms)},indent=2))
print(OUT);print('Pages:',page_no)
