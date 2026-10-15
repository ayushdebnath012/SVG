"""Document original CAD, existing FEM fields and unpaired drawing leads."""
from pathlib import Path
import json,zipfile,hashlib
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-machine-extensions-search');roots=[D/n for n in ['web-cad-fem-cylinder-cover','web-cad-fem-titanium-wing','web-cad-fem-dogbone-control','web-cad-fem-parking-systems']];C,W,B,P=roots;cc,wc,bc,pc=[json.loads((r/'catalog.json').read_text()) for r in roots];check=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-cover-wing-control.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-cover-wing-control.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.4;sty['BodyText'].leading=12.3;sty['Heading1'].fontSize=18;sty['Heading1'].leading=22;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width=485,maxheight=230):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(x),sty['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def src(c):p(f'Source: <link href="{c["source"]}" color="blue">original publisher repository</link>. Original filenames, source tree, Git blob hashes and SHA-256 retained.')
def nxt():story.append(PageBreak())
h('Pneumatic-cylinder cover: original CAD and FEM')
p('13 October 2026. This extension adds a pneumatic-cylinder cover and a titanium wing source with saved FEM data. A simple dogbone source is separated as a buckling/scoring control. Parking/barrier mechanisms add original CAD and drawings but remain held because no numerical FEM reference was located.')
img(T/'cover-original-cad-view.png',485,190)
p('<b>Read-only source STEP view:</b> independently valid BREP, one solid and 102 faces, envelope 62 x62 x34.6 mm. Original native Discovery DSCO is retained. This is a moderately detailed pressure-cover part, not a complex moving assembly. Display tessellation is not a new solver mesh.')
img(T/'cover-original-FEM-stress-points.png',485,225)
p('<b>Read-only visualization of the existing ANSYS result:</b> original finite averaged corner-node stresses shown at their stored coordinates. Derived von-Mises peak is 13.185679 MPa; missing stresses are omitted and preserved as NaN/mask. The point plot is an inspection of downloaded fields, not an original publisher screenshot or a new FEM solve.')
p('Original 2022 R1 static RST has 68,720 nodes, 46,105 elements and one saved set. Source pressure is 0.5 MPa. Native CAD, Discovery model, Workbench project, source deck/log and full original RST are included. One part/one pressure case contributes one candidate, irrespective of node count.')
p('Original archive extraction passed all 23 member CRCs and sizes; STEP validity and native field copies were checked. Geometry/load-face mapping, material plausibility and mesh convergence still need review before benchmark admission.')
src(cc)
nxt();h('Cover: numerical references and source constraints')
img(C/'original-native-thumbnail.png',300,160)
p('<b>Unchanged original Discovery thumbnail:</b> extracted from the native source file; source STEP was independently imported. A thumbnail is not a verified dimensioned drawing.')
table([['Source FEM reference / setup','Value or finding'],['Max translation norm','0.009226294 mm'],['Peak derived averaged von Mises','13.185679 MPa'],['Finite stress nodes','10,655 of 68,720'],['Missing stress nodes','58,065; NaNs and mask retained'],['Pressure / solver units','0.5 MPa; /units,MPA: mm, N, MPa'],['Material definition','Engineering Plastic; deck E22,000 MPa, nu0.3'],['Fixed support','Source component _FIXEDSU contains only node 843, all DOFs fixed'],['Additional restraints','Selected _FRICSUX and _FRICSUZ nodes have UX=0 and UZ=0 respectively']],[210,275])
p('Source deck does not fix every mounting face. Its single-node fixed support and directional frictionless restraints must be matched exactly when recreating boundary conditions. The pressure acts through source surface-element selection; verify its geometric scope rather than assuming the whole exterior is loaded.')
p('Engineering Plastic is the publisher material name. E 22 GPa is kept exactly as supplied; no corrected material value is substituted. The field values reflect those original assumptions and should not be interpreted as a validated operating pressure or product safety rating.')
p('extracted-original-fields.npz retains original node IDs, mesh coordinates, translations, six-component averaged stresses and missing-value mask. Von Mises is derived from the stored tensor, not a separately solved quantity or raw integration-point stress. Field recovery uses ansys-mapdl-reader 0.56.0; repeated reads agree exactly but do not establish independent solver verification.')
p('Supplied-CAD-to-FEM candidate only. No verified dimensioned manufacturing drawing is available for this cover. Required review: CAD/CAE revision and transform, selected support/pressure faces, material card interpretation, convergence and target recovery convention.')
src(cc)
nxt();h('Titanium wing: saved static and modal fields')
img(W/'Resources_/Equivalent Stress.png',495,210)
p('<b>Original publisher static FEM figure:</b> 283.8 Pa equivalent-stress maximum. Recovered averaged tensor gives 283.802497 Pa, consistent with the displayed rounding. Original native DesignModeler FFF.agdb is included; no neutral STEP/IGES was uploaded and proprietary geometry has not been independently imported.')
img(W/'Resources_/5_Natural Frequencies.png',495,145)
p('<b>Original publisher modal/geometry view:</b> five natural frequencies are displayed. Saved RST values are 58.785703, 240.508460, 364.832438, 643.713571 and 1010.110750 Hz. All five normalized mode arrays and exact frequencies are copied to modal-original-fields.npz.')
table([['Existing saved solution','Inventory / reference'],['Static','3,239 nodes /1,863 elements; one set; max U 1.6433948e-8 m; stress finite 565 nodes, missing 2,674'],['Prestressed modal','Same mesh; five frequencies/mode vectors; arbitrary mode normalization'],['Original source cards','MKS titanium E 96 GPa, nu0.36, density4620 kg/m3; two source pressure objects with SFE component 3=0.1 Pa; five fixed-support groups']],[165,320])
p('This is a simple standalone airfoil wing, with static and prestressed modal behavior. Very low 0.1 Pa source pressure explains the small displacement/stress scale; it is not an aircraft flight-load reference. Four distributed partition RST files are not four extra cases.')
p('The publisher title mentions flutter, but these saved results do not provide a coupled aerodynamic flutter eigenproblem or critical airspeed. Natural frequencies alone cannot score flutter prediction. Native CAD import, load/support topology and geometry revision remain pending. No new CAD/mesh or solver run.')
src(wc)
nxt();h('Dogbone: simple buckling control, separate count')
img(B/'original-native-thumbnail.png',280,135)
p('<b>Original stored Discovery geometry preview:</b> native SYS.dsco retained. Source describes 38 mm length, 15 mm end width, 5 mm waist, 3 mm fillet radius and3 mm thickness. No compatible independent solid import or locally synthesized STEP is claimed.')
img(B/'results/static_structural/von_mises.png',470,210)
p('<b>Original publisher static stress figure:</b> maximum 216.89 MPa. Companion fatigue plots report minimum life 19,101 cycles and safety factor 0.39743. These are source plot references; fatigue S-N curve, mean-stress/load-ratio convention and exact case mapping need review.')
table([['Buckling mode','Original dimensionless multiplier','Source rounded'],['1','0.7817336297','0.78173'],['2','2.0094410291','2.0094'],['3','5.7321480567','5.7321']],[95,235,155])
p('Original static and buckling RST files each describe 17,260 nodes /3,030 elements. Source uses 50 MPa compressive pressure and steel E 200,000 MPa. Header multipliers match README rounded values. These are load factors, not Hz; mode deformation is normalized, not actual displacement.')
p('README claims 1 mm static deformation without a supplied static deformation plot. Mode 3 screenshot amplitude 0.88889 mm does not substantiate that claim. No legacy 2025 R2 full-field extraction is used. Static/buckling files are two linked solutions in one simple geometry; fatigue plots are not a third saved RST.')
p('One calibration/control source; zero complex-task count. A stress peak below nominal yield does not establish buckling safety, since the first source multiplier is below 1. Native import and compatible field validation remain pending.')
src(bc)
nxt();h('Parking systems: original drawings, FEM held')
f=P/'extracted-original/parking lock design/parking lock design/pdf/upper arm.PDF';doc=pymupdf.open(f);doc[0].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/'parking-original-upper-arm-drawing.png');img(T/'parking-original-upper-arm-drawing.png',495,365)
p('<b>Original upper-arm engineering drawing:</b> dimensioned orthographic/section/isometric views and title block specifying millimeters. This is one of nine original one-page drawing PDFs for the parking-lock mechanism. Material/tolerance/completeness and matching native parts require review.')
table([['Original CAD archive / evidence','Independent inspection / status'],['Barrier motor/shaft STEP','Valid 25 solids /466 faces; partial mechanism scope'],['Parking upper-assembly STEP','Valid 15 solids /224 faces; full native assembly dependencies pending'],['Parking cap STEP','Valid 1 solid /11 faces; envelope 215 x107.574 x580mm'],['Rotary parking system','Original SolidWorks parts/assemblies; includes third-partyreference/catalogimages'],['Paired numerical FEM candidates','0 located; no RST/RTH, solver history, numerical report or result plot']],[205,280])
p('Publisher describes ANSYS validation and explicitly omits raw result files. The three downloaded archives contain CAD and reference images/drawings, but no located numerical FEM result. CAD complexity does not fill this gap. These sources remain held; neither three projects nor nine drawings increase paired benchmark counts.')
p('Original native assembly/part files and nine dimensional PDFs are included for future matching to a published FEM source. No mechanism was recreated or solved. Repository MIT notice retained; external reference photos/catalog drawings do not automatically inherit that license.')
src(pc)
nxt();h('Collection inventory and benchmark preparation')
table([['Added evidence','Count / qualification'],['Pneumatic-cylinder cover','1 valid neutral CAD / raw static-result candidate'],['Titanium wing','1 native geometry source /2 saved static-modal candidates; proprietary CAD import pending'],['Dogbone control','1 simple geometry /2 linked raw solutions ;0 complex-task count'],['Parking/barrier systems','3 CAD-only projects held ;9 original drawing PDFs unpaired'],['Certified admissions / model scores','0 / none']],[175,310])
p(f'<b>Verification:</b> {check["original_downloads_verified"]} original repository files passed pinned Git blob SHA-1, size and SHA-256 checks. Cylinder RAR extraction passed all 23 original member CRC/size checks. Cover field copies and wing static/five-mode arrays match repeat reads. Buckling multipliers match native headers/source rounding. Missing stresses and original units are retained.')
p('<b>Supplied CAD to FEM:</b> cover is independently valid native STEP. Wing and dogbone have original native CAD files but need compatible import. Freeze exact CAD/CAE transforms, pressure/support scopes, material cards, solver/recovery conventions and tolerances before frontier-model evaluation. Nodal arrays and saved modes are not separate tasks.')
p('<b>Drawing to CAD to FEM:</b> parking-lock drawings supply useful original dimensional information, but no paired numerical FEM reference was located. Keep those assets held until an exact original solve is found. Cover/wing/control previews are not manufacturing drawings. No drawing reconstruction was performed.')
p('<b>Other crawled leads:</b> CarCrashNet publisher says release is pending peer review; advertised 15,567 simulations are not downloaded/admitted. Angled-spar battery wing source ZIP has scripts/notebook and no verified native CAD; its 1.776 GB Results ZIP was not downloaded. Curved post-buckling panel input decks and graphite-foam EnSight meshes are not automatically non-mesh CAD/result pairs.')
p('<b>Provenance / licensing:</b> original source files and archive members remain unchanged. Source programs/macros/journals are retained as text and never executed. Cover, wing and control data-license status unresolved; parking MIT notice has external-image limitations. Local research collection only; no public release or license grant implied.')
p('Two engineering CAD/FEM evidence sources, one separately counted simple control and three unpaired CAD projects. Complexity ranges are stated: cover is a moderate detailed part,wing is a simple standalone component,parking assemblies are complex but unpaired. No locally created CAD/problem, new FEM solve, COMSOL dependency or frontier-model call.')
p('Dataset ZIP includes original CAD/drawings, RSTs, decks/logs, numerical copies, catalogs, source hashes and crawl exclusions. Model benchmark scores have not been measured. Certified admission remains zero; published FEM references are candidates requiring exact problem definition and verification.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | original geometry, saved references and held drawing leads');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer);dd=pymupdf.open(O)
for i,page in enumerate(dd):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'cover-wing-control-report-page-{i+1}.png')
print('PDF pages',len(dd),flush=True);Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if f.is_file():z.write(f,root.name+'/'+str(f.relative_to(root)))
 z.write(O,O.name);z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
 for f in ['source-verification.json','crawl-leads-and-exclusions.json']:z.write(T/f,'verification/'+f)
 for f in ['audit_web_cover_wing_control.py','report_web_cover_wing_control.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
 for f in ['cover-original-cad-view.png','cover-original-FEM-stress-points.png','parking-original-upper-arm-drawing.png']:z.write(T/f,'inspection-views/'+f)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));members=len(z.namelist())
hh=hashlib.sha256()
with Z.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):hh.update(b)
v={'zip':str(Z),'bytes':Z.stat().st_size,'sha256':hh.hexdigest(),'members':members,'CRC_verified':True,'pdf_pages':len(dd)};(T/'package-validation.json').write_text(json.dumps(v,indent=2)+'\n');print(v,flush=True)
