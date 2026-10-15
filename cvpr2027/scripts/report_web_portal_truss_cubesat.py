"""Package source CAD/drawings and existing FEM evidence; no generated engineering data."""
from pathlib import Path
import json, zipfile, hashlib, html
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-machine-variety-search')
names=['web-cad-fem-portal-frame','web-cad-fem-bolted-truss','web-cad-fem-cubesat-frame'];roots=[D/n for n in names]
cats=[json.loads((r/'catalog.json').read_text()) for r in roots];v=json.loads((T/'source-verification.json').read_text())
O=Path('cvpr2027/output/pdf/web-cad-fem-portal-truss.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-portal-truss.zip')
styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.5;styles['BodyText'].leading=12.7;styles['Heading1'].fontSize=18;styles['Heading1'].leading=22
story=[]
def p(s):story.extend([Paragraph(s,styles['BodyText']),Spacer(1,6)])
def h(s):story.extend([Paragraph(s,styles['Heading1']),Spacer(1,9)])
def pic(f,w=490,mh=260):
    im=PILImage.open(f);hh=w*im.height/im.width
    if hh>mh:w*=mh/hh;hh=mh
    story.extend([Image(str(f),width=w,height=hh),Spacer(1,7)])
def table(rows,widths):
    t=Table([[Paragraph(html.escape(str(x)),styles['BodyText']) for x in row] for row in rows],colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,7)])
def source(i):p(f'Source: <link href="{cats[i]["source"]}" color="blue">original publisher repository</link>. Pinned revision and original file hashes retained in download-manifest.json.')
def nxt():story.append(PageBreak())
h('Haunched portal frame: CAD and drawing')
p('13 October 2026. This collection adds two sources with native CAD and published FEM evidence: a steel portal frame and an idealized truss control. A third source is held because its CubeSat screenshots do not match the downloadable project. No new engineering geometry, problem, solver run or model prediction was generated.')
pic(T/'portal-dimensioned-drawing.png',490,330)
p('<b>Original fabrication drawing:</b> Drawings/Steel 1.pdf, page 1. Includes front, plan and section views with dimensions, haunched eaves and internal stiffeners. This page is a render of the published PDF, not a reconstructed drawing. The original PDF is included in the ZIP.')
table([['Original CAD / drawings','Files and evidence'],['Native SOLIDWORKS 2024','Steel 1.SLDPRT; steel.SLDASM; M16 nut and bolt parts'],['Dimensioned source PDFs','Steel 1; hexagon nut; hhb(grade a)_is'],['Assembly BOM','One steel component, 12 bolts, 12 nuts across two configurations']],[165,325])
p('<b>Drawing hold:</b> the steel title block says DIMENSIONS ARE IN INCHES, while fastener drawings say millimeters and FEM reports use mm. The drawing is dated 28 November; the final FEM report is dated 5 December. No scale or revision was silently corrected. Compatible native import and exact assembly-to-study mapping remain pending; the README-mentioned STEP folder is absent from the pinned tree.')
p('Original proprietary/confidential drawing notice remains intact. No explicit repository data license was located; collected for local research.')
source(0)
nxt();h('Portal frame: published FEM references')
pic(T/'portal-published-stress.jpeg',490,215)
p('<b>Unchanged embedded source result image:</b> final report, page 15. Published peak nodal von Mises stress is 3.174e8 Pa = <b>317.4 MPa</b>; resultant displacement is <b>5.117 mm</b> on page 15/16; equivalent strain is 1.157e-3. The full original report and displacement image are included.')
table([['Source iteration','Peak VM [MPa]','Peak U [mm]','Status'],['A36 / It1','474.9','5.124','Published, held'],['A992 / It2','474.9','5.124','Published, held'],['It3','463.5','13,100,000','Failed; reject target'],['It4','353.2','5.077','Earlier revision'],['Final','317.4','5.117','Exact native mapping pending']],[125,105,110,150])
p('Final source material: ASTM A992, E = 200 GPa, nu = 0.26, density = 7,850 kg/m3, yield = 345 MPa. Final mesh: 705,930 nodes / 388,199 elements. Report uses a linear elastic solid mesh, large displacement off, two fixed faces, globally bonded interaction, gravity 9.81 m/s2 and force value 10,000 N on two faces.')
p('<b>Load-scope hold:</b> final reaction Y is 20,168.7 N. Total-versus-per-face force scope must be reconciled with the README roof-load claim. Final report has no connector definitions; a bolted CAD assembly does not establish a solved bolt-preload/contact model. No CWR or other full-field result file is uploaded.')
p('Separate source buckling CSV gives multiplier <b>5.0498</b> and “50.5 KN.” Its exact base load and geometry revision are not frozen. Five static iterations and one buckling export remain one geometry family; the disconnected It3 study is retained only as failure evidence. Hand calculations and source “safe” labels are not benchmark certification.')
source(0)
nxt();h('Bolted truss: CAD and original FEM export')
pic(roots[1]/'Results/CAD_design screenshots/Screenshot 2026-04-28 151109.png',490,200)
p('<b>Original publisher CAD screenshot:</b> native Solid Edge FINAL TRUSS ASSEMBLY.asm with 17 .par components is included. Read-only compound-file inspection finds original Parasolid streams in the parts; compatible geometry import is pending. No dimensioned source drawing was located.')
table([['Joint at 1 kg','Original X value','Original Y value'],*[[label,f'{xy[0]:.6f}',f'{xy[1]:.6f}'] for label,xy in zip('ABCDEFGHI',cats[1]['source_XY_at_1kg'])]],[130,180,180])
p('<b>Source result:</b> Abaqus_node_displacement_data.csv contains 9 finite load rows x 9 joints x 2 coordinates. Loads are 0.15, 0.24, 0.30, 0.42, 0.51, 0.61, 0.65, 0.70 and 1.00 kg. Exact numerical copies, original CSV, original CAE and publisher reports are included.')
p('<b>These are deformed joint positions, with unresolved coordinate units:</b> the file does not print XY units or include a zero-load row. No displacement baseline was invented from polynomial fits. The separate experimental plot explicitly uses pixel axes; it is not used as a FEM displacement reference.')
p('Source FEM is a planar pinned-joint T2D2 truss with E = 6 GPa, density = 600 kg/m3, fixed/rolling supports. The physical bolted assembly has 3D eccentricity and experimental failure above about 0.5 kg. Keep this as an idealized truss control; it does not test solved 3D bolt contact. Section area, support/load node mapping and units remain unresolved. No original ODB is present.')
source(1)
nxt();h('Held: CubeSat screenshots / archive mismatch')
pic(roots[2]/'Screenshot 2025-08-12 010120.png',280,195)
p('<b>Original publisher CubeSat CAD screenshot.</b> Separate source directional-deformation figures give Y maximum 0.25521 mm and Z maximum 0.1942 mm. No matching native CubeSat model/result pair is confirmed.')
pic(T/'archive-original-mesh-nodes.png',350,190)
p('<b>Read-only plot of the actual archived mesh nodes, not a CAD reconstruction:</b> Final_Solution.wbpz instead has a 170 x 70 x 100 mm block-like assembly. SYS.agdb contains a native compressed Parasolid stream inside HDF5; its header records DesignModeler 2021 R1. Materials include silicon, copper and aluminum. Archive project and screenshots have incompatible geometry/result evidence.')
table([['Actual saved archive analysis','Recovered values; NOT CubeSat targets'],['Steady thermal / SYS','38.827006 to 40.300339 C'],['Imported-temperature static / SYS-1','U max 0.038040899 mm; averaged VM max 149.622039 MPa'],['Linear buckling / SYS-3','1189.359672 / 1207.052483; dimensionless multipliers'],['Prestressed modal / SYS-4','10 frequencies: 1880.788472 to 4335.841894 Hz']],[170,320])
p('All original archived CAD, decks and parent RTH/RST files are retained, with exact node-ID arrays and all normalized mode vectors. Two worker-partition RSTs add no independent cases. These results add zero verified CubeSat tasks. Original MIT license is retained.')
source(2)
nxt();h('Inventory and limits for frontier benchmarking')
table([['This extension','Verified count / qualification'],['New paired source-evidence families','2: portal frame + idealized 2D truss control'],['Complex FEM family candidate','1: portal frame; raw-field/import checks pending'],['Held mismatched source','1: CubeSat screenshots vs unrelated native archive'],['Original files / archive extraction','78 pinned Git files; 58 original archive files byte-verified'],['New dimensioned PDFs','3 portal-frame/fastener PDFs; steel unit/revision hold'],['Certified new benchmark admissions','0; no frontier-model scores claimed']],[205,285])
p('<b>Integrity:</b> all original downloaded files pass Git blob SHA-1, byte size and SHA-256. The original WBPZ archive passes CRC; each extracted file equals its original archive bytes. The truss NPZ matches every CSV coordinate exactly. Archived nodal solutions and all mode vectors match repeat original-result reads. Native file hash checks find no byte-identical CAD in other previously downloaded manifests; geometric similarity checks remain pending.')
p('<b>Raw-field limits:</b> archived structural stress is finite at 2,021 of 6,871 nodes; 4,850 missing averaged corner-node stress rows remain masked, not set to zero. Von Mises stress is derived from stored averaged tensors, not integration-point truth. Modal vector amplitude is arbitrary; buckling multipliers are not frequencies. Archived temperature uses Celsius with source TOFFST 273.15; structural translation is stored in meters and converted to mm only for display.')
p('<b>Actual archive setup:</b> source convection is 5 W/m2/K to 20 C, source volumetric heat generation is 240,000 W/m3 on _CM58, and structural temperature is imported with reference temperature 22 C plus fixed support. The archive does not establish CubeSat launch loads, fatigue life or validated space thermal conditions.')
p('<b>Two separate tracks:</b> supplied CAD to FEM requires importable geometry, exact native revision, materials, support/load scopes and a frozen numerical reference. Drawing to CAD to FEM also requires matching dimensions and units. Source screenshots can illustrate CAD but do not replace a dimensioned drawing. None of this batch is ready for strict automated grading.')
p('<b>Additional crawl exclusions:</b> Mendeley lattice/resin interlocking has FEM force spreadsheets and figures but no native CAD. Ultrastiff metamaterial has STEP proxies, topology STL and a load figure but no solved outputs; its 22 MPa is an input. Spatial-frame STEP/K/M/mapping data are operator evidence, not a solved field. Biofluids has native CAD and material routines without saved results. The SOLIDWORKS book source has complex chapter CAD but saved CWR only for a simple vase; its mirror adds no new family.')
p('The ZIP includes original CAD, drawings, reports, CAE/WBPZ, all extracted archive bytes, exact existing-field copies, source manifests, catalogs, crawl exclusions and the master-catalog snapshot. No COMSOL dependency, publisher code execution, serialized-proxy deserialization, generated CAD, new FEM solve, model call or public release.')
def footer(c,doc):
    c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | portal frame, truss and archive provenance');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=36,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.45,1.45)).save(T/f'portal-truss-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True);assert len(doc)==5
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for R in roots:
        for f in sorted(R.rglob('*')):
            if f.is_file():z.write(f,R.name+'/'+str(f.relative_to(R)))
    z.write(O,O.name);z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
    for name in ['source-verification.json','crawl-leads-and-exclusions.json','native-file-exact-dedup.json','vkhtwb774t-files.json','k75hh792k9-files.json','6ympzc5rkt-files.json']:z.write(T/name,'verification/'+name)
    for f in ['collect_web_portal_truss_cubesat.py','audit_web_portal_truss_cubesat.py','report_web_portal_truss_cubesat.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
    for f in T.glob('portal-published-*'):z.write(f,'inspection-views/'+f.name)
    z.write(T/'archive-original-mesh-nodes.png','inspection-views/archive-original-mesh-nodes.png')
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));nm=len(z.namelist())
validation=dict(pdf=str(O),pages=len(doc),zip=str(Z),bytes=Z.stat().st_size,sha256=hashlib.sha256(Z.read_bytes()).hexdigest(),members=nm,CRC_passed=True,latest_PDF_visual_QA='Pending page inspection')
(T/'package-validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(validation,flush=True)
