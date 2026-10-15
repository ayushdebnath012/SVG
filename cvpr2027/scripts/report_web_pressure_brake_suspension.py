"""Evidence PDF and local archive of published CAD + FEM references."""
from pathlib import Path
import json,hashlib,zipfile
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-pressure-search');roots=[D/x for x in ['web-cad-fem-pressure-vessel','web-cad-fem-brake-thermal','web-cad-fem-active-suspension','web-cad-fem-robot-arm']];V,B,S,R=roots
v,b,s,r=[json.loads((p/'catalog.json').read_text()) for p in roots];O=Path('cvpr2027/output/pdf/web-cad-fem-pressure-brake-suspension.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-pressure-brake-suspension.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.3;sty['BodyText'].leading=12.3;sty['Heading1'].fontSize=18;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def picture(path,width,maxheight=300):
 im=PILImage.open(path);height=width*im.height/im.width
 if height>maxheight:width*=maxheight/height;height=maxheight
 return Image(str(path),width=width,height=height)
def img(path,width,maxheight=300):story.extend([picture(path,width,maxheight),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(x),sty['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,7)])
def source(d):p(f'Source: <link href="{d["source"]}" color="blue">original publisher repository</link>. Pinned revision {d["revision"][:10]}; download hashes and source notices retained.')
def nxt():story.append(PageBreak())
h('Pressure vessel: native CAD and saved FEM')
p('12 October 2026. Three new deformable-FEM families collected: nozzle-and-saddle pressure vessel, perforated brake disc and double-wishbone assembly. A fourth robot-arm archive is retained separately for rigid joint motion. No generated CAD or new solver runs.')
img(V/'1.JPG',465,245)
p('<b>Original publisher CAD views:</b> vessel, nozzle openings, heads and saddle supports. Native CATIA parts and three IGES exports retained. CIRCULAR and CIRCULAR1 have matching imported geometry extents and 66 faces each, but different original hashes. FLAT HEAD imports with 72 faces. None imports as a watertight solid; source native parts remain available.')
img(V/'NIMONIC 75/STRESS.JPG',480,165)
p('<b>Original FEM figure:</b> Nimonic 75 equivalent stress, maximum 22.432 MPa. Raw file.rst and complete static input deck are available. This is one saved material/head case, rather than a solved case for every screenshot folder.')
p('<b>CAD scale:</b> circular-head IGES extent approximately 2400 x 880 x 1239.90 mm. The views have no verified complete dimensioned engineering drawing. Supplied-CAD FEM and drawing reconstruction remain separate benchmark tracks.')
source(v)
nxt();h('Pressure vessel: numerical reference coverage')
img(V/'NIMONIC 75/TD.JPG',480,180)
p('<b>Original deformation figure:</b> maximum 0.031822 mm. Read-only extraction agrees at the printed precision; source arrays are retained unchanged in saved-static-fields.npz.')
table([['Reference audit','Saved result / source setup'],['Mesh and state',f"{v['nodes']:,} nodes; {v['elements']:,} elements; one static state labeled 1"],['Maximum translation',f"{v['maximum_translation_mm']:.12f} mm"],['Finite recovered maximum VM stress',f"{v['finite_recovered_maximum_von_mises_MPa']:.9f} MPa"],['Finite stress rows',f"{v['finite_stress_nodes']:,}; missing rows {v['missing_stress_nodes']:,}"],['Source material','Nimonic 75; E = 207,000 MPa; Poisson ratio 0.34'],['Pressure and units','0.824 MPa; N-mm-tonne-s, original /units,MPA']],[220,265])
p('<b>Stress interpretation:</b> ansys-mapdl-reader 0.56.0 averages saved element-nodal stress at shared corner nodes. The reported VM maximum uses finite six-component recovered rows. Original NaNs, node IDs and coordinates are preserved. Do not compare against a differently recovered or integration-point stress field.')
p('<b>Admission limits:</b> CAD/result head revision and contact/support details need full mapping and mesh-convergence review. README volume claim of 24 liters conflicts with its listed 880 mm outside diameter, 20 mm wall and 1520 mm shell length. The saved case can still support a source-setup benchmark after this mismatch is documented.')
p('The saved RST is a static pressure solution. Published thermal tables/plots do not establish a corresponding saved thermal field. Material and head variants in folders are not additional validated raw cases.')
source(v)
nxt();h('Perforated brake disc: CAD and thermal FEM')
img(T/'brake-original-p3-image0.jpeg',260,165)
p('<b>Original publisher modeling sketch:</b> brake-disc geometry traced from a physical disc. This is a CAD construction view, not a complete dimensioned manufacturing drawing. Native SLDPRT, valid STEP and DesignModeler AGDB retained.')
img(T/'brake-original-p4-image1.png',330,235)
p('<b>Original FEM figure:</b> steady-state temperature, source report physical page 4. Legend 114.22 to 130 degrees C. The saved thermal RTH is finite at all 188,762 mesh nodes; mesh has 119,885 elements.')
table([['Saved thermal reference','Value'],['Minimum temperature',f"{b['minimum_temperature_C']:.9f} degrees C"],['Maximum temperature',f"{b['maximum_temperature_C']:.9f} degrees C"],['Boundary conditions','Prescribed 130 degrees C; ambient 22 degrees C; temperature-dependent convection table']],[240,245])
p('saved-thermal-fields.npz contains node IDs, coordinates and Celsius temperature read from the original RTH. The thermal nodal solution is a scalar temperature, despite the generic reader label. Peak temperature is prescribed; field/interior error is a more useful potential metric.')
p('No raw structural RST found. Structural report and topology outputs are auxiliary references. Fluent CFD assets use finite volume and are excluded from FEM counts. Exact CAD/node mapping and convergence still require review.')
source(b)
nxt();h('Double wishbone: complex assembly and FEA')
img(S/'media/Picture1.png',470,170)
p('<b>Original CAD illustration:</b> wishbones, upright, spring, pins and geared actuator. Native SolidWorks assembly plus nine part files and neutral STEP are retained. Independent STEP import is valid: 10 solids, 549 faces, approximately 257.81 x 324.58 x 220.00 mm.')
t=Table([[picture(S/'original-docx-evidence/image28.png',228,235),picture(S/'original-docx-evidence/image34.png',228,190)]],colWidths=[242,242]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]));story.extend([t,Spacer(1,5)])
p('<b>Original source FEM figures:</b> baseline callout 118 MPa (left); redesigned-region callout 103.1 MPa (right). The report prose rounds the latter to 103 MPa. These are published scalar references; raw mesh and saved simulation fields were explicitly omitted.')
table([['Source setup / reference','Value'],['Applied force components','3675 N vertical; 375 N longitudinal'],['Baseline / redesigned maximum stress','118 MPa / 103.1 MPa (image precision)'],['Connector and fixtures','Pin/hinge constraints; spring replaced by a connector']],[240,245])
p('Before/after CAD revision matching is unresolved. The report contains yield-strength placeholders and an unusual spring-stiffness normalization, so an exact FoS or a fully reproducible setup is not claimed. Simulink/Simscape control results are kept as context and are not FEM cases.')
source(s)
nxt();h('Robot arm: native CAD, rigid-motion archive')
img(R/'original-cad-thumbnail.png',220,220)
p('<b>Original CAD thumbnail:</b> articulated robot arm in source SpaceClaim. The downloaded project ZIP contains a native .scdocx with eight nonempty serialized Parasolid geometry members, source Mechanical database, input deck and saved RST. Independent native BREP validity has not been imported.')
table([['Saved source inventory','Interpretation'],['59 nodes, 43 elements','Reference nodes, masses, targets and joints'],['480 saved states','One trajectory, source labels 1 to 480'],['Element formulations','MASS21, TARGE170, MPC184'],['Source input','All nine bodies sent as rigid; transient, large-motion MKS setup'],['Stored motion array','480 x 59 x 6 generalized displacement, NaNs preserved'],['Continuum stress reference','Absent: no ENS stresses in saved result']],[225,260])
p('<b>Held from deformable-FEM benchmark:</b> the archive supplies actual CAD and saved joint-motion output. Its coarse reference-node representation and lack of solid/shell stress do not support a continuum stress benchmark. The source README stress description is broader than the stored fields.')
p('saved-rigid-motion-only.npz is a read-only extraction for possible future joint/multibody tasks. Rotations, translational coordinates, reference nodes and missing entries need explicit mapping. Never count 480 frames as 480 independent engineering tasks or treat rigid-body motion as elastic deformation.')
p('Input explicitly says antype,4 transient, while the binary header analysis code is 0. Preserve both metadata signals; resolve semantics from source input and output logs before any trajectory scoring.')
source(r)
nxt();h('New collection: counts and benchmark status')
table([['Family','Original CAD + FEM evidence','Candidate status'],['Pressure vessel','CATIA + IGES; RST, input deck, stress/deformation figures','One saved static FEM candidate'],['Brake disc','SLDPRT + valid STEP + AGDB; scalar-temperature RTH','One saved thermal FEM candidate'],['Double wishbone','SolidWorks + valid STEP; original FEM scalar figures','One plot-reference candidate'],['Robot arm','SpaceClaim + saved rigid joint-motion RST','Auxiliary; excluded from continuum stress']],[105,260,120])
p('<b>Counts:</b> three deformable-FEM geometry families: two native-CAD/saved-field candidates and one native-CAD/plot-reference candidate. One additional rigid-motion family is held separately. Two independently imported valid STEP models; pressure IGES has valid faces without closed solids. Zero newly verified complete dimensioned engineering drawings and zero certified admissions.')
p('<b>Before scoring:</b> verify exact CAD/result revision matching, dimensions, material scope, loads/constraints, numerical convergence, node correspondence and field-recovery conventions. Missing stress entries stay missing. Original plotted maxima are engineering reference values, not measured frontier-model scores.')
p('<b>Two task tracks:</b> supplied-CAD-to-FEM can use admitted candidates. Drawing-to-CAD-to-FEM requires sufficient original dimensioned drawings; screenshots, thumbnails and modeling traces do not automatically meet that requirement.')
p('<b>Collection integrity:</b> pinned source revisions, original source paths/URLs, byte lengths and SHA-256 hashes accompany downloads. Source code and input decks were read as text. No new CAD, solver run or model call occurred. No COMSOL files were used.')
p('<b>Local research:</b> explicit source dataset licenses were not found. Original notices retained; no public redistribution. Case-sensitive pressure-vessel folders were stored with a documented alias to preserve distinct originals on this filesystem.')
p('Machine-readable catalogs provide detailed source paths and limitations. The master dataset index registers this extension without counting material screenshots, frames, submodel files or node rows as extra independent cases.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | original source evidence and read-only audits');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(exist_ok=True,parents=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'pressure-brake-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True)
Z.parent.mkdir(exist_ok=True,parents=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if f.is_file():z.write(f,root.name+'/'+str(f.relative_to(root)))
 z.write(O,O.name)
 for name in ['collect_web_pressure_suspension.py','collect_web_brake_robot.py','audit_web_pressure_brake_suspension.py','report_web_pressure_brake_suspension.py']:z.write(Path('cvpr2027/scripts')/name,'inspection-scripts/'+name)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));count=len(z.namelist())
valid={'zip':str(Z),'bytes':Z.stat().st_size,'members':count,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest(),'crc_verified':True,'pdf_pages':len(doc)};(T/'package-validation.json').write_text(json.dumps(valid,indent=2));print(valid,flush=True)
