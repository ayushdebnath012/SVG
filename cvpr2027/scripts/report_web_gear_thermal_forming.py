"""Illustrated catalog of original web CAD and published FEM references."""
from pathlib import Path
import json,zipfile,hashlib,re
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-transmission-search');roots=[D/n for n in ['web-cad-fem-spur-gear-pair','web-cad-fem-ventilated-rotor','web-cad-fem-finned-heatsink','web-cad-fem-nx-heatsink','web-cad-fem-titanium-forming-held','web-cad-fem-crane-drawings-held']];G,R,H,N,F,C=roots
cats=[json.loads((r/'catalog.json').read_text()) for r in roots];v=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-gear-thermal-forming.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-gear-thermal-forming.zip');styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.4;styles['BodyText'].leading=12.3;styles['Heading1'].fontSize=18;styles['Heading1'].leading=22;story=[]
def fmt(t):
 t=re.sub(r'\b(ANSYS|Aluminium|is|and|with|on|maximum|minimum|mean|Max|Min|max|min|label|E|nu|k|alpha|ambient|Prescribed|rotation|objects|its|stress|README|h|Projected|count|prescribed|simulated|rigid|Job|Jobs|time|around|pages|thickness|approximately|Heated|friction|uniform|admission|Rotor|Zenodo|x)(?=\d)',r'\1 ',t)
 t=re.sub(r'(?<=\d)(MPa|mm|GPa)\b',r' \1',t)
 return re.sub(r'=(?=[0-9-])','= ',t)
def p(t):story.extend([Paragraph(fmt(t),styles['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,styles['Heading1']),Spacer(1,7)])
def img(path,width=490,maxheight=210):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(fmt(str(x)),styles['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def src(i):p(f'Source: <link href="{cats[i]["source"]}" color="blue">original publisher repository</link>. Original byte hashes and pinned source revision retained.')
def nxt():story.append(PageBreak())
h('Spur gears: original STEP and static FEM')
p('13 October 2026. This extension adds two complex geometry sources (gear pair and ventilated rotor), two separately counted thermal controls, and two held CAD leads. Published scalar/plot references are present; no new raw full-field solution is available in this batch.')
img(T/'gear-source-STEP-inspection.png',490,175)
p('<b>Read-only view of the original source STEP:</b> valid two-solid assembly with 314 faces, envelope 258.945 x174.960 x30 mm. Tessellation displays the downloaded CAD; no new geometry or solver mesh was created. The original AP214 STEP is included.')
img(G/'Stress.jpeg',490,195)
p('<b>Original publisher equivalent-stress figure:</b> 1.2379e7 Pa =12.379 MPa maximum. Original deformation plot gives 6.1668e-6 m =0.0061668 mm. Equivalent elastic strain maximum is7.8558e-5, minimum1.9206e-9. Source ANSYS2026 R1 static results have a load label1 s, not a dynamic rotation history.')
p('One gear pair is one family. Source archive contains byte-identical STEP, WBPJ, report and three result pictures, without the Workbench dependency folder or RST. Exact force/torque, material card, support faces and contact law are not specified in the available report. Forward-solve scoring is held until that problem definition is complete.')
p('Published von Mises stress is not automatically Hertz contact pressure or a gear-fatigue allowable. The report says internal drawings were used but omits their dimensions; no complete dimensioned drawing is uploaded. Supplied-CAD and drawing-reconstruction tracks remain distinct.')
src(0)
nxt();h('Ventilated rotor: CAD and linked thermal stress')
img(R/'file.png',490,140)
p('<b>Original publisher geometry view:</b> perforated/ventilated rotor. Original disk break.IGS imports as 363 valid faces with envelope 180 x180 x21 mm, matching report dimensions. Independent import gives zero solids/shells; ANSYS reports one stitched solid. Exact sewing and face mapping remain pending; no locally constructed solid is substituted.')
img(R/'equivalent stress.png',490,145)
p('<b>Original FEM stress contour:</b> maximum621.02 MPa, minimum1.1227 MPa, mean69.235 MPa; original U maximum0.067061 mm and mean0.045413 mm. The 57-page ANSYS2025 R2 report contains setup and result tables, matching the original image legends.')
table([['Source problem definition','Original report evidence'],['Thermal boundary','Prescribed100 C on one face; convection on one face, ambient22 C; temperature-dependent film coefficient'],['Thermal result','Min99.905 C; max100 C; mean99.991 C. Max100 C is imposed, not an independent prediction'],['Structural transfer / loads','One-way imported thermal field; rotation100 rad/s; two pressure objects0.5 MPa each;10 fixed faces'],['Source material / mesh','StructuralSteel E200,000 MPa, nu0.3, k0.0605 W/mm/K, alpha1.2e-5/K;39,030 nodes /21,095 elements']],[165,320])
p('README describes heat-flux input, but the actual report specifies prescribed temperature. The catalog retains this correction in evidence classification. Source stress621.02 MPa exceeds its250 MPa yield card in a linear elastic solution; this is not validated plastic braking behavior or a transient frictional brake cycle.')
p('Raw thermal/structural files are mentioned in report metadata (8.9375 /15.938 MB) but not uploaded. Full fields and exact boundary-face mapping cannot yet be scored. No verified dimensional drawing available.')
src(1)
nxt();h('Seven-fin conduction: simple thermal control')
img(H/'project3_fusion360.png',490,185)
p('<b>Original Fusion CAD screenshot:</b> original Heat_Sink.step independently imports as one valid solid,55 faces,80 x100 x58 mm. Source base is100 x80 x8 mm with7 fins,50 mm fin height and1.5 mm root fillets. This simple component is a thermal control, excluded from complex-assembly counts.')
img(H/'project3_ansys_temperature.png',490,200)
table([['Original steady-state FEM reference','Value / source scope'],['Temperature','Max31.859 C; min30.196 C. README31.86 /30.20 agrees with figure rounding'],['Total heat flux','Max10,470 W/m2; min126.03 W/m2; mean2,264.5 W/m2'],['Source loading','10 W heat flow at bottom, h25 W/m2/C, ambient22 C; convection on41 faces'],['Source material / mesh','Aluminium6061, approximate README k202 W/m/K;2 mm sizing']],[190,295])
p('Original temperature and heat-flux screenshots, STEP and WBPJ are included. WBPJ lacks dependency/result folders; no RTH or nodal field is uploaded. Exact conductivity card, source-face mapping and mesh convergence remain unverified. This supplies scalar/plot candidates, not certified field targets.')
p('Twenty displayed animation frames and the steady-solution label1 s are not twenty time-dependent cases. No synthesized drawing, local solve or missing-field reconstruction was performed. No verified dimensional manufacturing drawing.')
src(2)
nxt();h('NX heat sink: native CAD and thermal figures')
img(N/'heatsink01.PNG',490,165)
p('<b>Original source NX rendering:</b> native HeatSink1.prt includes the fin-array CAD. No neutral STEP/IGES was uploaded and compatible independent NX import is pending. Images show split fins, rounded base transitions and mounting details, but do not establish complete dimensions.')
img(N/'temperatures2.PNG',490,175)
p('<b>Original ANSYS steady thermal figure:</b> minimum59.123 C and maximum85 C. Two original thermal images show the same result from different viewpoints; they count as one case. Heat input, convection coefficients and full material cards are not supplied, so a possible prescribed85 C peak cannot be classified as a predictive target yet.')
table([['Evidence','Benchmark interpretation'],['Native CAD plus result plots','One geometry family; thermal control, complex-task count0'],['README CFD wording','Figures show solid steady thermal analysis; fluid-flow coupling and transient analyses are future work'],['Projected10-15% improvement','Future optimization claim, not an existing solved reference'],['Copied repository','jatin568 source has byte-identical CAD, mesh and two thermal image assets; counts once']],[160,325])
p('No saved RTH/field arrays, numerical convergence or independently imported geometry. No complete dimensioned drawing. Both supplied-CAD scoring and drawing reconstruction require further evidence. Original bytes are retained unchanged; a copied source does not increase dataset size.')
src(3)
nxt();h('Titanium forming: complex physics, CAD held')
img(F/'original-evidence-images/report-page-13-image-2.jpeg',250,145)
p('<b>Original report SolidWorks view:</b> conical geometry used for CAM trajectory extraction. Three uploaded STEP files are valid solids with7/8/10 faces; they do not provide the simulated150 x150 x1 mm sheet or complete forming assembly. The actual simulated forming tool is an analytically rigid4 mm hemispherical tip.')
img(F/'original-evidence-images/report-page-29-image-2.jpeg',490,170)
p('<b>Original Abaqus Job6 U3 figure:</b> source minimum -59.10, unit not printed, step time301.7. Report narrative says the tool stalls around39.3 mm. Field vs tool-depth scope, units and time mapping are unresolved; no corrected displacement target is created.')
table([['Job','T [C] /angle /target depth [mm]','Peak VM [MPa]','Min thickness [mm]'],['2','600 /20deg /9.5','749.5','0.913'],['3','600 /45deg /39.5','689.1','0.485'],['4','600 /45deg /39.5','810.7','0.575'],['5','600 /60deg /59.5','729.3','0.349'],['6','25 /60deg /59.5','1628','0.370'],['7','25 /60deg /69.5','1687','0.353']],[35,240,100,110])
p('Exact published tables transcribed from pages16,20,21; all six rows held. Job5 thickness0.349 mm contradicts approximately0.50 mm heated-case claims. Heated69.5 mm claim has no matching heated row. Jobs3/4 change mass scaling and differ substantially; they are not new CAD families.')
p('AbaqusExplicit S4R shells, friction0.1 and uniform25/600 C material assumptions are reported; localized coupled heating is future work. CSV/XLSX contain toolpaths/material inputs, not FEM force/displacement outputs. No uploaded INP/CAE/ODB, original sheet CAD or new solve. Complex-task admission0.')
src(4)
nxt();h('Crane hook: original drawing assets, FEM absent')
img(C/'Inventor designs/drawings/Screenshot 2026-01-25 154603.png',350,420)
p('<b>Original exploded assembly drawing:</b> numbered parts, quantities and source material labels. This is an assembly/BOM image, without dimensional constraints. It is not a complete manufacturing drawing or FEM result.')
table([['Downloaded native assets','Qualification'],['Inventor CAD','10 original IPT part files and one IAM assembly; compatible import/dependency completeness pending'],['Original drawing files','3 native DWG files, unrendered. Actual tree has no claimed IDW/PDF drawing exports'],['Existing numerical FEM results','None located; paired-case count0']],[170,315])
p('Original crane hook, support plates, anchor, bushings, spacer, nuts and washer files are retained. BOM includes additional DIN bolt/dowel entries without separate matching native part files; full assembly import is pending. Do not fill missing dependencies with generated parts.')
p('This source adds CAD/drawing variety as a held lead. It does not increase paired CAD/FEM or certified benchmark counts. Source educational/portfolio-use statement is preserved; local research only.')
src(5)
nxt();h('Collection inventory and scoring readiness')
table([['This web extension','Count / status'],['CAD + published FEM evidence','4 geometry sources: gears, rotor, two heat sinks'],['Complex geometry sources','2: meshing gears and perforated ventilated rotor'],['Thermal controls','2: original single-component fin arrays'],['Raw full-field result candidates','0 new RST/RTH/ODB files'],['Held partial/unpaired sources','1 forming CAM source;1 crane CAD source with3 DWG files'],['Certified admissions / frontier scores','0 / no model trials']],[205,280])
p(f'<b>Provenance verified:</b> {v["original_downloads_verified"]} original repository downloads pass pinned Git blob SHA-1, size and SHA-256. Six extracted spur-archive files match their direct originals and archive CRC. Five forming-report embedded images match original PDF streams. Native gear/heat-sink STEP validity checked; rotor IGES faces match the source report envelope.')
p('<b>Supplied CAD to FEM:</b> preserve exact geometric revision and load/material/contact definitions. Gear loading/contact cards are incomplete, rotor stitching/face scopes need verification, heat controls lack full saved fields, and NX needs native import. Published scalar values alone do not certify a reproducible solve.')
p('<b>Drawing to CAD to FEM:</b> no new complete matching dimensioned drawing target is verified in this batch. Original crane DWG files remain unrendered/unpaired; the exploded BOM view and CAD renders do not supply reconstruction constraints. No model was asked to recreate missing geometry.')
p('<b>Numerical references:</b> separate outputs from imposed inputs. Rotor100 C is prescribed; use its computed temperature response and linked structural results only after scope validation. Von Mises is not contact pressure, signed U3 is not total norm, and CAM path coordinates are not FEM solution fields. No scoring tolerance is certified here.')
p('<b>Other web leads:</b> gearbox repositories provide reports/MATLAB/screenshots without native CAD pairs; chiral-lattice Zenodo21669226 has STEP/CAE and experimental curves but no uploaded numerical FEM output; gear/tower modal sources have bare WBPJ/video without dependencies; snap-fit has figures without native CAD. Landing-gear position/acceleration files need rigid-body vs flexible-FEM classification. None adds a paired case here.')
p('<b>Package:</b> original STEP/IGES/NX/Inventor/DWG assets, reports, figures, CAM/material files, six catalogs, master snapshot, exact table transcription and audit script. Original spur ZIP retained; redundant extracted mirrors omitted. Repository notices retained; explicit broad data licenses unresolved or educational-use only. Local research collection, no public release.')
p('Master catalog extended without changing earlier batches. Original FEM figures and numeric tables were collected from the web; no engineering problem, CAD solid, missing FEM data, new solver run or model score was generated. No COMSOL dependency.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | gear, thermal, forming and drawing evidence');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer);doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'gear-thermal-forming-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True);assert len(doc)==7
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if not f.is_file():continue
   rel=f.relative_to(root)
   if root==G and rel.parts[0]=='extracted-original':continue
   z.write(f,root.name+'/'+str(rel))
 z.write(O,O.name);z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
 for f in ['source-verification.json','crawl-leads-and-exclusions.json']:z.write(T/f,'verification/'+f)
 for f in ['audit_web_gear_thermal_forming.py','report_web_gear_thermal_forming.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
 z.write(T/'gear-source-STEP-inspection.png','inspection-views/gear-source-STEP-inspection.png')
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));members=len(z.namelist())
hh=hashlib.sha256()
with Z.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):hh.update(b)
validation={'zip':str(Z),'bytes':Z.stat().st_size,'sha256':hh.hexdigest(),'members':members,'CRC_verified':True,'pdf_pages':len(doc),'redundant_spur_archive_extraction_omitted':True};(T/'package-validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(validation,flush=True)
