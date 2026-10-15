"""Package original web CAD/FEM assets and an illustrated evidence catalog."""
from pathlib import Path
import json,zipfile,hashlib
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-complex-assembly-search');roots=[D/n for n in ['web-cad-fem-crank-multiphysics','web-cad-fem-pipe-flange-comparison','web-cad-fem-shelf-pretension','web-cad-fem-knuckle-joint']];C,P,S,K=roots
cats=[json.loads((r/'catalog.json').read_text()) for r in roots];check=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-complex-assemblies.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-complex-assemblies.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.4;sty['BodyText'].leading=12.3;sty['Heading1'].fontSize=18;sty['Heading1'].leading=22;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width=490,maxheight=220):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(x),sty['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def src(i):p(f'Source: <link href="{cats[i]["source"]}" color="blue">original publisher repository</link>. Original file bytes, pinned tree, Git blob hashes and SHA-256 retained.')
def nxt():story.append(PageBreak())
F=C/'original-evidence-frames/Media'
h('Crank assembly: original CAD and static FEM')
p('13 October 2026. This web extension adds four assembly geometries: engine crank, pipe/flanges, bolted shelf support and knuckle joint. All geometry and FEM references are publisher originals. No new engineering problem, CAD model, solver run or frontier-model trial was created.')
img(F/'Assembly+Mesh/Assembly_SP_SW.png',490,165)
p('<b>Original CAD animation, decoded final frame:</b> original Assembly_SP_SW.STEP independently imports as a valid BREP with 5 solids and 186 faces, envelope 136.379 x 329.312 x 152 mm. The original STEP and native Workbench project are included. This CAD view is not a dimensioned manufacturing drawing.')
img(F/'Static_Structural_Analysis/ES.png',490,195)
p('<b>Original static stress figure:</b> equivalent-stress maximum 2.3895e8 Pa = 238.95 MPa. Original deformation figure gives 3.1809e-4 m = 0.31809 mm. Report rounds these to 239 MPa and 0.318 mm. Source applies 6 MPa piston pressure, fixes a crankshaft end and uses 5 mm mesh sizing.')
p('Published figures/tables are available, but no RST or dependency/result directory is uploaded. The WBPJ alone cannot supply full nodal fields. Exact material/contact cards, geometry mapping, stress recovery and convergence must be fixed before using these scalar candidates for scoring.')
p('One crank assembly is one geometry family; component plots and GIF frames do not add benchmark items. Original GIFs are unchanged; PNG copies were verified against the decoded final source frame. Static/thermal/transient references retain their separate scopes.')
src(0)
nxt();h('Crank thermal and jointed-motion conflicts')
img(F/'Steady_State_Analysis/T.png',490,180)
p('<b>Original steady-temperature figure:</b> 294.8 to 660 degrees C. Original heat-flux figure gives maximum 181,900 W/m2 and minimum 2.3781 W/m2; report rounds the maximum to 182,000 W/m2. The temperature report instead claims global minimum 22 C and crankshaft maximum 252.6 C. That disagreement is retained, not reconciled by inventing a corrected field.')
img(F/'Transient_analysis/TD.png',490,180)
p('<b>Original jointed transient total displacement:</b> maximum 0.18111 m at source label 360. README claims 0.00158 m. Revolute/translational joints and prescribed rotation with no external pressure can include rigid-body motion; this total displacement cannot be treated as pure elastic deformation or a validated engine cycle.')
table([['Study / evidence','Benchmark restriction'],['Steady thermal','Ambient 22 C, prescribed piston 660 C, radiation on crankshaft surfaces; report/figure temperature scope or revision conflict held'],['Transient mechanism','Jointed motion; exact rotation/time definition and scalar conflict unresolved; no raw trajectory'],['Multiphysics title','Coupled thermal-structural analysis is future work in the source, not an existing coupled solve']],[155,330])
p('Steady-state GIF display interpolation is not a time-resolved thermal simulation. Animation display labels are not automatically physical time samples. Conflicting temperature and motion values remain excluded from frozen numerical targets until their exact source revisions and scopes are established.')
src(0)
nxt();h('Pipe/flange CAD and original drawing evidence')
img(P/'Images/CAD/05_pipe_flange_assembly_assembled_and_exploded.jpeg',490,160)
p('<b>Original CAD assembled/exploded view:</b> native SolidWorks pipe/flange parts and assembly, two SLDDRW files, native Discovery/SpaceClaim geometry and the Workbench archive are included. No compatible independent solid/drawing import is claimed.')
img(P/'Images/CAD/04_flange_detail_drawing_OD60_bore30_8x4.jpeg',390,285)
p('<b>Original dimensioned flange drawing:</b> diameter 60, bore 30, 8 holes of diameter 4, thickness 7.53 and radial placement 26 are shown. The title block explicitly says <b>dimensions are in inches</b>, while the source CAD/solver setup uses millimeters. This conflict holds the drawing-reconstruction track; original numbers/units are not silently corrected.')
p('The JPEG named 02_pipe_detail_drawing_OD29_80_ID27_00.jpeg is actually a flange 3D model screenshot, without pipe dimensions. It is retained with a corrected evidence classification. This batch has one visually verified dimensioned drawing image, plus two unrendered native SLDDRW files.')
p('Source model dimensions in mm: pipe OD 29.80, ID 27.00, length 225.11; flange OD 60, bore 30, thickness 7.53. Assembly has a reported 0.10 mm radial clearance. Shared-topology and bonded-contact treatments are two variants on the same geometry, not two independent design families.')
src(1)
nxt();h('Pipe/flange: existing solved fields and recovery')
img(P/'Images/Results/21_shared_topology_equivalent_von_mises_stress_20_357MPa.jpeg',490,185)
p('<b>Original shared-topology stress screenshot:</b> maximum 20.357 MPa, averaged display, Average Across Bodies=No. Read-only averaged tensor recovery gives 18.912604 MPa. Recovery convention, exact revision and compatible decoder validation remain unresolved; neither value replaces the other.')
img(P/'Images/Results/39_contact_equivalent_von_mises_stress_19_548MPa.jpeg',490,185)
table([['Same CAD / case','Published U / VM','Recovered U / averaged VM'],['Shared topology','0.01212 mm / 20.357 MPa','0.012119951 mm / 18.912604 MPa'],['Bonded contact','0.011157 mm / 19.548 MPa','0.011156612 mm / 19.548393 MPa']],[125,175,185])
p('Both U peaks and bonded stress agree with source rounding. Original /units,MPA uses mm, N, MPa; steel E 200,000 MPa, nu 0.3. Source bearing force is -500 N along X, with 16 cylindrical bolt-hole faces fixed. Reported total reactions are 500.46 N and 500 N; these remain source scalar references, not independently recovered balances.')
p('Shared RST: 79,219 nodes / 21,384 elements, stress finite 22,077 and missing 57,142 nodes. Bonded: 68,636 / 54,723, finite 19,488 and missing 49,148. NPZ copies retain node IDs, coordinates, translations, averaged stress tensors and NaN masks. These are stored corner-node stresses, not raw integration-point ground truth.')
p('Two original RSTs, each with one saved static set. Direct and archive copies are byte-identical and count once. Source 2026 R1 decoding is exploratory pending compatible independent validation and native CAD import.')
src(1)
nxt();h('Bolted shelf: nonlinear friction and pretension')
img(S/'original-SYS-thumbnail.png',250,150)
p('<b>Unchanged source SpaceClaim thumbnail:</b> bracket, wall and bolted assembly. Native SYS.scdoc is preserved inside the original archive and as an extracted copy. The STEP mentioned in the report was not uploaded; independent native CAD import and complete drawings remain pending.')
img(S/'original-evidence-images/report-page-3-image-1.png',490,210)
p('<b>Original embedded report FEM figure:</b> peak von Mises 396.77 MPa at a bolt. Report deformation is 0.02505 mm. The existing archive decodes to different global peaks; those values are separate held references until the revision/recovery discrepancy is resolved.')
table([['Original stage / source','Max total U [mm]','Max VM [MPa]'],['Archive set 1: pretension','0.028023471','350.096024'],['Archive set 2: locked + load','0.028023471','350.626377'],['Published report','0.02505','396.77']],[235,120,130])
p('Four bolts each receive 5.2 kN pretension, locked in stage 2; external force is -500 N along Y. Friction coefficient 0.15, wall back face fixed, large deflection enabled. Steel bracket/wall E 200 GPa; bolts E 210 GPa, nu 0.3, source yield 550 MPa. These are two quasi-static load stages of one problem, not two geometry cases or dynamic histories.')
p('Original 2024 R1 RST has 91,168 nodes / 72,308 elements and 2 saved sets; averaged stress is finite at 16,247 nodes, missing 74,921. Report describes changing contact mesh from 1.0 to 1.5 mm for upload size; that does not prove the cause of the numerical disagreement. Source safety factor 1.39 is not an independently certified capacity.')
src(2)
nxt();h('Knuckle joint: native assembly and scalar FEM')
img(K/'Knuckle Joint/Images/Assembly.png',490,135)
p('<b>Original CAD view:</b> five Inventor part files and original IAM assembly are included: eye end, fork end, pin, collar and taper pin. The report references a STEP and 4.25 MB RST, but neither is uploaded. This is CAD plus published scalar/plot evidence, not a raw-field benchmark item.')
img(K/'Knuckle Joint/ANSYS/Equivalent stress.png',490,165)
p('<b>Original static stress figure:</b> equivalent-stress maximum 4.9453e7 Pa = 49.453 MPa, minimum 5254.8 Pa. Report average is 11.187 MPa. Source steel E 200 GPa, nu 0.3; 20,000 N force along negative X and one fixed face, linear static with large deflection off.')
table([['Source result / setup','Exact scope'],['Directional deformation','UX minimum -3.2425e-5 m = -0.032425 mm; maximum 0 m; average -1.6776e-5 m'],['Contact formulation','6 bonded contacts; no frictional/slipping pin contact'],['Reported source mesh','11,449 nodes / 5,532 elements'],['Misleading duplicate filename','Total_Deformation.png duplicates Directional deformation.png; legend specifies global X deformation']],[175,310])
p('The signed X displacement is not total displacement magnitude. Original static contact bonding suppresses the articulation that a CAD joint could allow. Use the published loading/contact model, not an inferred real freely rotating mechanism. Five components and mirrored plots count as one family.')
p('Compatible Inventor import, exact support/load face mapping, convergence and recovery remain pending. No dimensioned drawing has been verified for this source. Publisher educational-use statement is retained; local research only.')
src(3)
nxt();h('Inventory, target quality and benchmark use')
table([['New original evidence','Count / status'],['Assembly CAD + FEM source projects','4 distinct geometry families'],['Raw-result sources','2 projects: pipe/flanges and bolted shelf'],['Distinct raw solved cases','3: two pipe connection models, one two-stage shelf problem'],['Plot/scalar-only sources','2: crank assembly and knuckle joint'],['Drawing evidence','1 dimensioned image with unit conflict; 2 native SLDDRW files unrendered'],['Certified admissions / model scores','0 / no model trials']],[205,280])
p(f'<b>Verified provenance:</b> {check["original_downloads_verified"]} original repository files passed source Git blob SHA-1, size and SHA-256 checks. Two Workbench archives passed CRC and extracted-byte comparisons (47 and 28 members). Seven decoded GIF frames match their source pixels. Four embedded shelf-report images match original PDF image streams. Four saved field-set NPZ copies match repeat reads, including NaNs.')
p('<b>Supplied CAD to FEM:</b> crank STEP is independently valid. Pipe, shelf and knuckle native CAD require compatible import. Freeze original geometry revision, transforms, face selection, material cards, units, contact/pretension stages and stress recovery before scoring. Scalar references are distinct from full-field targets; conflicting targets remain held.')
p('<b>Drawing to CAD to FEM:</b> keep a separate admission list. Flange image has explicit inch/mm conflict, alleged pipe drawing is not a drawing, and native SLDDRW files need rendering. CAD screenshots, native thumbnails and deformation plots do not substitute for complete dimensional drawings.')
p('<b>Numerical scoring:</b> these are original FEM reference values, not frontier-model scores. After admission, compare like-for-like units, signed components, spatial fields and stage scopes. Do not score averaged nodal stress against incompatible integration-point peaks, replace missing nodes with zero, or treat total mechanism motion as elastic deformation. No tolerance is certified here.')
p('<b>Other web leads held:</b> co-digester Zenodo record 22210486 contains two spreadsheets without uploaded CAD; scan-based columns provide STL geometry rather than verified non-mesh CAD; complex engine/aircraft SolidWorks models lack matched solved FEM outputs; turbine and steering leads lack verified native CAD/result pairs. None increases the paired count.')
p('<b>Package policy:</b> originals and license notices unchanged. Shelf MIT notice retained; other sources have unresolved or educational-use terms, so this is a local research collection. Source scripts/macros/journals/decks were never executed. Original WBPZ archives retained; redundant extracted pipe archive members are omitted from ZIP because the original archive and direct RSTs are present. Catalog paths identify those archive mirrors.')
p('The master catalog is extended, preserving earlier batches. This PDF shows original CAD and FEM evidence with limitations; the ZIP includes native assets, saved RSTs, original reports/plots, field copies, hashes, catalogs and inspection scripts. No COMSOL dependency, synthesized CAD, new FEM solve or model call was introduced.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | original assemblies and saved numerical references');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer);doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'complex-assemblies-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True);assert len(doc)==7
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if not f.is_file():continue
   rel=f.relative_to(root)
   if root==P and rel.parts[0]=='extracted-original':continue
   z.write(f,root.name+'/'+str(rel))
 z.write(O,O.name);z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
 for f in ['source-verification.json','crawl-leads-and-exclusions.json']:z.write(T/f,'verification/'+f)
 for f in ['collect_web_complex_assemblies.py','audit_web_complex_assemblies.py','report_web_complex_assemblies.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));members=len(z.namelist())
hh=hashlib.sha256()
with Z.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):hh.update(b)
v={'zip':str(Z),'bytes':Z.stat().st_size,'sha256':hh.hexdigest(),'members':members,'CRC_verified':True,'pdf_pages':len(doc),'redundant_pipe_archive_extraction_omitted':True};(T/'package-validation.json').write_text(json.dumps(v,indent=2)+'\n');print(v,flush=True)
