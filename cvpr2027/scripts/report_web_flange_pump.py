"""Report original CAD/FEM evidence and package the local research collection."""
from pathlib import Path
import json,hashlib,zipfile
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
D=Path('cvpr2027/data');F=D/'web-cad-fem-flange-contact';P=D/'web-cad-fem-gear-pump';T=Path('cvpr2027/tmp/cad-fem-machinery-search');fc=json.loads((F/'catalog.json').read_text());pc=json.loads((P/'catalog.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-flange-pump.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-flange-pump.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.3;sty['BodyText'].leading=12.2;sty['Heading1'].fontSize=18;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width,maxheight=290):
 im=PILImage.open(path);height=width*im.height/im.width
 if height>maxheight:width*=maxheight/height;height=maxheight
 story.extend([Image(str(path),width=width,height=height),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(x),sty['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,7)])
def nxt():story.append(PageBreak())
def source(url):p(f'Source: <link href="{url}" color="blue">original publisher repository</link>. Original source notices, revision and file hashes retained.')
h('Bolted flange: original native CAD and FEM')
p('12 October 2026. Two new geometry families collected: bolted nozzle-flange sector and external gear-pump housing. Four flange saved solutions from three publishers are grouped within one family; a pump plot-reference candidate adds a second family. Zero certified admissions.')
img(F/'spsvision/boltedFlange_files/user_files/simulating_contact.png',450,240)
p('<b>Original publisher CAD/contact view:</b> upper and lower flange sectors, bolt and nut. Native DesignModeler AGDB files contain nonempty serialized Parasolid geometry, including upstream geometry and analysis-system CAD. No original neutral STEP or independent native BREP import is claimed.')
img(F/'spsvision/boltedFlange_files/user_files/displacement_3s.png',450,245)
p('<b>Original published FEM figure:</b> final-stage deformation for the spsvision project. Actual RST, source input, materials, Mechanical database and logs are retained. Saved arrays were read without launching ANSYS or executing source code.')
p('The source deck uses static contact/nonlinear stages with imposed body temperatures. Labels 1, 2 and 3 do not establish a transient rocket launch. Repositories use different descriptions and mesh/setup variants; matching assembly dimensions are evidence for one common geometry family, not independent industries.')
source('https://github.com/spsvision/BoltedFlangeAnalysis')
nxt();h('Four saved solutions: numerical inventory')
rows=[['Original saved case','Nodes / elements','Sets','Final translation inch','Final recovered VM psi']]
for r in fc['records']:
 s=r['states'][-1];rows.append([r['id'],f"{r['mesh_nodes']:,} / {r['mesh_elements']:,}",len(r['states']),f"{s['maximum_translation_inch']:.9f}",f"{s['finite_recovered_peak_vm_psi']:.3f}"])
table(rows,[107,111,32,112,123])
p('<b>Read-only fields:</b> all 18 saved result sets were extracted to NPZ with original node IDs, mesh coordinates, displacements, nodal temperatures, recovered stresses and finite masks. These are four original solutions, not 18 separate CAD tasks. Exact output arrays were compared back to the reader.')
rows=[['Saved case','Finite stress rows / total','Final translation mm (converted)']]
for r in fc['records']:
 s=r['states'][-1];rows.append([r['id'],f"{s['finite_stress_rows']:,} / {r['mesh_nodes']:,}",f"{s['maximum_translation_mm_readonly_conversion']:.6f}"])
table(rows,[155,160,170])
p('<b>Unit evidence:</b> every inspected deck declares /units,BIN with inch, psi, lbf and Fahrenheit conventions. Reference temperature is 70 degrees F; final stored temperatures are 700 degrees F. NPZ retains source scales. Converted summaries use 25.4 mm/inch and 0.006894757293168361 MPa/psi.')
p('<b>Stress scope:</b> ansys-mapdl-reader 0.56.0 averages saved element-nodal stress at shared corner nodes. Peaks use finite six-component rows; missing entries remain NaN. The local peaks can be affected by contact singularities and output recovery. Numerical finiteness or a completed run does not establish correct material failure behavior.')
p('Source logs report zero errors and six to eight warnings across these cases. Full warning, convergence, contact, pretension and geometry/state correspondence reviews remain required. The two Sornanathan systems contain identical native CAD data but different saved solution histories.')
source('https://github.com/Sornanathan/Ansys.Bolted_Nozzle_Flange')
nxt();h('Source labeled Saturn V: preserve actual setup')
img(F/'saturn-nozzle/images/ansys_model_closeup.png',185,120)
p('<b>Original publisher CAD illustration:</b> circular flange with fasteners. Saved analysis CAD and mesh are a narrow sector. The full-ring view is not a dimensioned manufacturing drawing or a validated full-engine solution.')
img(F/'saturn-nozzle/images/Equivalent_Stress.png',460,245)
p('<b>Original FEM contour:</b> final equivalent stress legend 5.4558e5 psi. Reader finite-subset peak is 545,582.102 psi, agreeing at displayed precision. The standalone RST is byte-identical to its archive RST and counted once.')
table([['README description','Saved source evidence'],['SI, 500 degrees C and Inconel 718 bolts','BIN imperial units; 70 to 700 degrees F; 300-series stainless/A286 material names'],['Transient progression and 2.31 mm maximum','antype,0 static stages; final translation 1.099026 inch (27.915266 mm)'],['26,134 nodes / 4,255 elements','RST mesh: 26,278 nodes / 6,605 elements']],[240,245])
p('This is retained as a source-specific flange-sector reference with explicit conflicts. It is not admitted as independently validated Saturn V hardware. Static stage values, material scope and geometry must follow the actual deck; the README cannot replace those inputs.')
source('https://github.com/Prashantsk45/Saturn-V-F1-Nozzle-Joint-FEA')
nxt();h('External gear pump: native CAD and FEM plots')
img(P/'original-report-evidence/pump-original-p5-image1.png',465,265)
p('<b>Original CAD parameter view:</b> pump housing with ports, flange holes and gear chamber. Native SolidWorks housing and gear SLDPRT files are downloaded. The README says SolidWorks files are omitted, but the original repository tree contains both. No original assembly or neutral STEP located.')
img(P/'StaticFigure133.png',470,235)
p('<b>Original FEM figure:</b> equivalent-stress maximum 1.9542e8 Pa, or 195.42 MPa, matching report physical page 16. This is original scalar/contour evidence, not a saved nodal-field archive. No RST or full mechanical model is present in the source tree.')
p('The report identifies static analysis, local 0.003 m face sizing, 102,736 nodes and 59,255 elements, with port-region fixed support and segmented pressure loads. Complete load magnitudes, native CAD state matching and convergence still require verification.')
source(pc['source'])
nxt();h('Pump design table: auxiliary reference data')
img(P/'original-report-evidence/pump-original-p19-image0.jpeg',480,250)
p('<b>Original embedded source table:</b> nine design points with wall thickness, bolt-hole diameter, mass, stress and displacement. Physical page 19. Nine rows are not nine CAD/result pairs because original exports for each design are unavailable.')
table([['Original scalar reference','Source value / interpretation'],['StaticFigure130 stress','5.2696e8 Pa = 526.96 MPa, different plotted configuration'],['StaticFigure133 stress','1.9542e8 Pa = 195.42 MPa, matches report prose'],['StaticFigure66 stress','2.0569e8 Pa = 205.69 MPa'],['StaticFigure57 displacement','4.9194e-5 m = 0.049194 mm'],['Report page 14 displacement','0.00010515 m = 0.10515 mm, another source reference']],[245,240])
p('<b>Unresolved units:</b> DOE table column labels displacement in mm, whereas original contour labels use m. Retain the table values as written until setup/author evidence resolves the scale. Design 2 image table gives 3.58e-05, while the prose summary gives 3.57e-05; no silent correction was made.')
p('<b>Revision scope:</b> several stress/displacement figures show different dates, meshes and peaks. The native housing and gear files are real CAD, but the precise geometry/load configuration for each scalar has not been verified. This remains one plot-reference family candidate.')
p('CAD screenshots show parametric dimensions and equations. They do not provide a verified complete dimensioned engineering drawing with all necessary views, thicknesses and tolerances.')
source(pc['source'])
nxt();h('Collection counts and frontier-benchmark status')
table([['Collected evidence','Count / status'],['Engineering geometry families','2: one common flange-sector family, one gear-pump housing family'],['Publisher repositories','4, grouped by geometry/setup evidence'],['Native CAD + original saved solution candidates','4 flange solutions'],['Saved static result sets','18 within those four solutions'],['Native CAD + published scalar/plot candidate','1 gear-pump family'],['Auxiliary pump design table','9 rows; exact CAD variants and displacement scale unresolved'],['Independent native BREP imports / complete dimensioned drawings','0 / 0 newly verified'],['Certified admissions / frontier-model scores','0 / not measured']],[240,245])
p('<b>Included:</b> native DesignModeler and SolidWorks CAD; original Workbench archives/RST; material/setup/log files; exact read-only NPZ extractions; original CAD/FEM views; pump report and design-table figures; source URLs, revisions and SHA-256 hashes.')
p('<b>Required admission checks:</b> geometry/state/load correspondence, constitutive material scope, unit consistency, contact and pretension behavior, mesh convergence, output recovery, and tolerances. Original unusually large stresses and README discrepancies are preserved for audit, not labeled as certified physical performance.')
p('<b>Separate tasks:</b> supplied-CAD FEM can use admitted cases. Drawing reconstruction needs complete original drawing evidence; native CAD thumbnails and parameter screens do not automatically satisfy that track. Never inflate counts with static stages, plies, source mirrors or table rows.')
p('<b>Local research:</b> MIT notices retained for pump and Saturn source. Other flange-source data licenses unresolved. No public redistribution. Original uploaded source code and solver inputs were read as text and never executed.')
p('This extension uses published assets only. No new CAD, new FEM solve, COMSOL dependency or frontier-model call was introduced. Detailed machine-readable status is registered in the master collection index.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Published CAD + FEM | original assets and read-only reference audits');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'flange-pump-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True)
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in [F,P]:
  for f in sorted(root.rglob('*')):
   if f.is_file():z.write(f,root.name+'/'+str(f.relative_to(root)))
 z.write(O,O.name)
 for name in ['collect_web_flange_pump.py','audit_web_flange_pump.py','report_web_flange_pump.py']:z.write(Path('cvpr2027/scripts')/name,'inspection-scripts/'+name)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));count=len(z.namelist())
v={'zip':str(Z),'bytes':Z.stat().st_size,'members':count,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest(),'crc_verified':True,'pdf_pages':len(doc)};(T/'package-validation.json').write_text(json.dumps(v,indent=2));print(v,flush=True)
