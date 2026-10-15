"""Render existing source CAD and report existing FEM values; no geometry or FEM generation."""
from pathlib import Path
import json,zipfile,hashlib,re
import cadquery as cq,resvg_py
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from PIL import Image,ImageDraw,ImageFont
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/web-cad-fem-additions';j=json.loads((DATA/'catalog.json').read_text());records=j['records'];pd=ROOT/'output/pdf';pd.mkdir(exist_ok=True,parents=True);pdf=pd/'web-cad-fem-additions-169.pdf';thumbs=DATA/'cad-views';thumbs.mkdir(exist_ok=True)
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
style=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=14,textColor=colors.HexColor('#243546'))
c=canvas.Canvas(str(pdf),pagesize=(595,842));c.setTitle('Published CAD and FEM source collection - 169 additions');c.setAuthor('Source assets credited per case')
page=0
def para(t,y,size=10,width=505):
 ps=ParagraphStyle('p',parent=style,fontSize=size,leading=size*1.4);p=Paragraph(escape(t),ps);w,h=p.wrap(width,750);p.drawOn(c,45,y-h);return y-h-10
def top(title,sub):
 global page
 page+=1;c.setFillColor(colors.HexColor('#102e49'));c.rect(0,757,595,85,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Helvetica-Bold',17);c.drawString(45,805,title);c.setFont('Helvetica',10);c.drawString(45,780,sub);c.setFillColor(colors.HexColor('#243546'))
 c.setFont('Helvetica',8);c.drawString(45,24,'Published source assets | No local CAD or FEM reference generation');c.drawRightString(550,24,str(page))
def table(rows,y,widths):
 t=Table(rows,colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eff5')),('TEXTCOLOR',(0,0),(-1,-1),colors.HexColor('#243546')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#ccd5de'))]));w,h=t.wrap(505,700);t.drawOn(c,45,y-h);return y-h-14
def pic(p,x,y,w,h):c.drawImage(ImageReader(str(p)),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
top('Published CAD + FEM: 169 additions','Collected from original web sources | 11 October 2026')
y=para('169 downloaded source pairs across seven problem families. The 160 GeoPINONet instances are parameter variations in two families; they are not 160 different types of complex engineering problem.',719,13)
y=table([['Collection','CAD instances','Published FEM output'],['GeoPINONet: lug','80','Stress tensor + displacement CSV'],['GeoPINONet: holed plate','80','Stress tensor + displacement CSV'],['UCSM: four sheet-metal families','8','Major/minor true-strain JSON + mesh'],['Nonlinear tricuspid valve','1','Stress/strain, displacement, VTK, ODB']],y,[210,85,210])
for t in ['All original source CAD and result files are included in the accompanying package. CAD/result locators appear on each page and in catalog.json. Source licenses are CC BY 4.0; retain original author attribution.','The CAD pictures are inspection renders of downloaded CAD. They are not dimensioned engineering drawings. The valve case includes the original published dimensioned geometry figures.','No new certified benchmark admissions or frontier-model trials are claimed. Units, load mapping, mesh behavior, solver replay and numerical tolerances still require review.','Source discrepancy: GeoPINONet plate README says thickness 20 mm, while the downloaded CAD and corresponding FEM coordinate bounds agree on 10 mm. One UCSM mesh face is missing a strain row; no value was filled.']:
 y=para(t,y)
y=para('Sources: zenodo.org/records/21483341 | zenodo.org/records/15327950 | doi.org/10.1016/j.dib.2021.107664',y,9)
c.showPage()
for i,r in enumerate(records,1):
 name=r['id'];top(f'{i:03d} / 169  |  '+('Nonlinear valve' if name.startswith('tricuspid') else r['family'].replace('Plate_with_a_hole','Holed plate').replace('Lug_3D','3D lug')),name)
 if name.startswith('tricuspid'):
  image=DATA/'valve/figure-1.jpg';pic(image,45,469,505,245);y=para('Original published dimensioned geometry and boundary conditions (article Fig. 1). Native IGES surface geometry and Rhino model included.',457,10)
  f=r['fem']['frames'][-1];y=table([['Final published frame 4','Value'],['Nodal result rows',str(f['node_rows'])],['Stress / strain rows',str(f['stress_rows'])+' each'],['Max nodal displacement [mm]',f"{f['max_displacement_mm']:.6g}"],['Max published von Mises stress [MPa]',f"{f['max_published_von_mises_MPa']:.6g}"]],y,[340,165]);y=para('Five frames belong to one source simulation. Summary maxima are extracted from original ASCII results, not a new solver run.',y)
 elif name.startswith('geopinonet'):
  cp=DATA/r['cad'];shape=cq.importers.importStep(str(cp)).val();svg=cq.exporters.getSVG(shape,opts=dict(width=950,height=520,showHidden=False,showAxes=False,projectionDir=(1,-1,.8),marginLeft=25,marginTop=25,strokeWidth=.7));image=thumbs/(name+'.png');image.write_bytes(resvg_py.svg_to_bytes(svg_string=svg,dpi=96,background='white'));pic(image,45,448,505,280);y=para('Inspection view of the original STEP CAD. No source dimensioned drawing verified.',437,9)
  rows=[['Original ANSYS reference CSV','Compression','Lateral bending'],['Nodal rows']+[str(f['rows']) for f in r['fem']],['Max displacement [m]']+[f"{f['max_displacement_m']:.6g}" for f in r['fem']],['Max full 3D von Mises [Pa]']+[f"{f['max_von_mises_Pa']:.6g}" for f in r['fem']]];y=table(rows,y,[255,125,125]);y=para('Numeric fields: x, y, z, ux, uy, uz, sxx, syy, szz, sxy, syz, sxz. Summary maxima are calculated from the published reference fields. They are not model performance scores.',y,9)
 else:
  cp=DATA/r['cad'];shape=cq.importers.importStep(str(cp)).val();svg=cq.exporters.getSVG(shape,opts=dict(width=950,height=520,showHidden=False,showAxes=False,projectionDir=(1,-1,.8),marginLeft=25,marginTop=25,strokeWidth=-1));svg=re.sub(r'stroke-width="([0-9.eE+-]+)"',lambda m:f'stroke-width="{float(m.group(1))*1.8}"',svg,count=1);image=thumbs/(name+'.png');image.write_bytes(resvg_py.svg_to_bytes(svg_string=svg,dpi=96,background='white'));pic(image,45,448,505,280);y=para('Inspection view of the original STEP CAD. LS-DYNA static implicit inverse forming results; no source dimensioned drawing verified.',437,9)
  f=r['fem'];y=table([['Original strain JSON','Value'],['Strain rows / mesh faces',f"{f['strain_rows']} / {f['mesh_faces']}"],['Minor true strain range',f"{f['minor_range'][0]:.6g} to {f['minor_range'][1]:.6g}"],['Major true strain range',f"{f['major_range'][0]:.6g} to {f['major_range'][1]:.6g}"],['Missing face values',str(f['missing_face_ids'])]],y,[300,205]);y=para('Strains are dimensionless. Original STEP, OFF mesh and strain JSON are provided together. Mesh IDs are in range; solver mapping is not independently replayed.',y,9)
 y=para('CAD file: '+r['cad'],y,8)
 if name.startswith('geopinonet'):y=para('FEM files: '+r['cad_archive']+' -> '+r['source_split']+'/'+r['source_case']+'/*_compression.csv and *_lateral_bending.csv (full ZIP-member locators in catalog.json).',y,8)
 elif name.startswith('ucsm'):y=para('FEM file: '+r['strains']+' | mesh: '+r['mesh'],y,8)
 else:y=para('FEM archive: valve/original-supplement.zip -> Text_Files/ and ParaView_Visualization/',y,8)
 y=para('Source: '+r['source'],y,8);y=para('Status: collected source pair; not a certified benchmark task.',y,8)
 if name.startswith('geopinonet-Plate'):y=para('Source discrepancy: README thickness 20 mm; this CAD and FEM pair is 10 mm.',y,8)
 assert y>42,(name,y)
 c.linkURL(r['source'],(45,30,550,50),relative=0,thickness=0);c.showPage()
 if i%25==0:print('PDF cases',i,flush=True)
top('Valve: original drawing and FEM view','Published article figures 2 and 4; source assets preserved')
pic(DATA/'valve/figure-2.jpg',45,434,505,290);para('Figure 2: original geometry control points, chordae insertion coordinates and dimensions in millimeters.',422,10)
pic(DATA/'valve/figure-4.jpg',75,153,445,220);para('Figure 4: published nonlinear closure result. Numerical stress, strain and displacement results are in the original supplement; this figure itself is a geometry visualization.',140,10);para('Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8668829/',82,9);c.showPage();c.save();print('PDF',pdf,'pages',page,flush=True)
# Readme makes archive locators and source qualification explicit.
(DATA/'README.md').write_text('''# Published CAD and FEM source collection: 169 additions

Downloaded original web assets. No local engineering geometry, problems, physics assumptions or FEM reference results were generated. CAD PNGs are inspection renders of original CAD; numerical summary maxima are read/calculated from original reference fields.

- 80 GeoPINONet lug STEP instances, each with two ANSYS reference CSVs.
- 80 GeoPINONet holed-plate STEP instances, each with two ANSYS reference CSVs.
- 8 UCSM STEP/mesh/LS-DYNA strain pairs, two examples from each of four families.
- 1 nonlinear anisotropic tricuspid-valve IGES/Rhino geometry + Abaqus model/results, original dimensioned figures, ASCII/VTK/ODB files.

These are 169 CAD/reference pairs in seven families, not 169 different complex engineering task types. Zero new certified benchmark admissions; no frontier model calls or solver replay were run. Only the valve has verified original dimensioned figures in this addition. Other CAD views are not dimensioned drawings.

## Where are CAD and FEM?

`catalog.json` links every source pair to its CAD file and its results. `geopinonet/cad/` contains extracted unmodified STEP members. Original full ZIP archives under `geopinonet/` hold reference CSVs and fixed/loaded surface STL files. Exact CSV ZIP-member names are in each catalog record. CSV fields: x,y,z,ux,uy,uz,sxx,syy,szz,sxy,syz,sxz. CAD bounds (mm) and FEM coordinates (m) agree in all 160 pairs. All 320 reference CSVs contain finite values (17,376,822 total rows).

`ucsm/` contains eight original STEP, OFF mesh and major/minor true-strain JSON triplets. Download manifest includes source archive, exact member, verified member CRC32 and local SHA256. Large source archives were fetched selectively via standard HTTP ranges. One face in 1119_uc3 lacks a strain row (21,632 of 21,633); no missing value is filled. Original solver input/material cards are not supplied here; do not claim deterministic replay readiness.

`valve/Idealized_Geometry/` contains original IGES (a shell surface and curves, not a solid) and Rhino geometry. Original complete `valve/original-supplement.zip` contains five result frames, source VUMAT, solver decks, postprocessing code, ASCII fields, VTK fields and ODB. Five frames are one source problem. Original dimensioned figures 1/2 are included. Original replay requires Abaqus; reading TXT/VTK does not.

## Qualification issues

GeoPINONet source README says holed-plate thickness 20 mm; all downloaded plate STEP and FEM bounds agree on 10 mm. This discrepancy is flagged per record. Source config uses steel E=2e11 Pa, nu=0.3, and demo source documents a 1000 N reference load, but force/BC semantics still need task-by-task benchmark review. Avoid mesh-dependent peak stress scoring without tolerances and convergence evidence.

Published FEM values are reference outputs, not frontier-model scores. Keep supplied-CAD-to-FEM and drawing-to-CAD-to-FEM evaluations separate. Do not expose reference CSV/strain/result fields to a model attempting a held-out FEM task. Source training/validation partitions are preserved; public-data contamination remains possible.

## Source attribution and licenses

All three source collections specify CC BY 4.0. Preserve author attribution and source URLs.

- Vicente Urrutia Valdes, Ivan La Fe-Perdomo, Angel Rodriguez Soto. GeoPINONet. https://zenodo.org/records/21483341 ; https://github.com/v-urrutiav/GeoPINONet . Original source archive and Zenodo metadata preserved.
- Tobias Lehrer, Philipp Stocker, Fabian Duddeck, Marcus Wagner. UCSM. https://zenodo.org/records/15327950 . Publication https://doi.org/10.1016/j.cad.2025.103924 . Published static implicit inverse analysis estimates strain, not a full contact/forming trajectory.
- Devin W. Laurence, Chung-Hao Lee, et al. An in-silico benchmark for the tricuspid heart valve. https://doi.org/10.1016/j.dib.2021.107664 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC8668829/ . Source supplementary CC BY 4.0 statement preserved in article.xml.
''')
# Visual overview: original published valve drawing plus renders from three CAD sources.
can=Image.new('RGB',(1500,1020),'white');d=ImageDraw.Draw(can);font=ImageFont.truetype(FONT,23)
items=[('Original valve drawing (published Fig. 1)',DATA/'valve/figure-1.jpg'),('Lug: downloaded STEP + ANSYS fields',thumbs/'geopinonet-Lug_3D-model_train-1.png'),('Sheet-metal UC3: STEP + strain JSON',thumbs/'ucsm-1119_uc3.png'),('Sheet-metal UC4: STEP + strain JSON',thumbs/'ucsm-1813_uc4.png')]
for i,(title,p) in enumerate(items):
 x=(i%2)*750;y=(i//2)*510;d.text((x+24,y+18),title,font=font,fill='#102e49');im=Image.open(p).convert('RGB');im.thumbnail((700,440));can.paste(im,(x+(750-im.width)//2,y+65+(440-im.height)//2))
can.save(ROOT/'output/web-cad-fem-additions-preview.png')
arc=ROOT/'output/datasets/web-cad-fem-additions-169.zip'
with zipfile.ZipFile(arc,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for f in DATA.rglob('*'):
  if f.is_file():z.write(f,f.relative_to(DATA),compress_type=zipfile.ZIP_STORED if f.suffix=='.zip' else zipfile.ZIP_DEFLATED)
 z.write(pdf,'web-cad-fem-additions-169.pdf')
print('PACKAGE',arc,arc.stat().st_size,flush=True)
