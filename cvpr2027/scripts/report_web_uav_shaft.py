"""Create original-source evidence report and local collection archive."""
from pathlib import Path
import json,zipfile,hashlib,re
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-rotating-machinery-search');names=['web-cad-fem-uav-assembly','web-cad-fem-quadcopter-dynamics','web-cad-fem-composite-pipe','web-cad-fem-differential-shaft','web-cad-fem-rear-axle'];roots=[D/n for n in names];U,Q,P,S,A=roots;uc,qc,pc,sc,ac=[json.loads((r/'catalog.json').read_text()) for r in roots];check=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-uav-pipe-shaft.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-uav-pipe-shaft.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.4;sty['BodyText'].leading=12.3;sty['Heading1'].fontSize=18;sty['Heading1'].leading=22;story=[]
def readable(t):
 # Format only visible prose; source href URLs remain exact.
 parts=re.split(r'(<[^>]+>)',str(t))
 for i,s in enumerate(parts):
  if s.startswith('<'):continue
  s=re.sub(r'(?<=\d)(?=(?:MPa|Pa|Hz|Nmm|N|mm|MB|GB|bytes|nodes|elements|DOF|static|sets|frequencies|simulations|face|times|degrees|spline|part|pages|modes|force|s2|R1|R2|solid|kg|mm3|face|validated|located|qualified|mm/s2)\b)', ' ',s)
  s=re.sub(r'\b(ANSYS|Workbench|valid|archive|Archived|loose|Loose|with|has|RSTis|at|not|four|two|of|sections|material|deck|pipe|length|is|about|uses|claims|report|than|pages|load|repetition|document|file|total|and|plus|contains|original|to|peak|moment|force)(?=\d)',r'\1 ',s)
  s=re.sub(r';(?=\d)', '; ',s)
  parts[i]=s
 return ''.join(parts)
def p(t):story.extend([Paragraph(readable(t),sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width=485,maxheight=250):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 tt=Table([[Paragraph(readable(x),sty['BodyText']) for x in row] for row in rows],colWidths=widths);tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([tt,Spacer(1,6)])
def src(c):p(f'Source: <link href="{c["source"]}" color="blue">original publisher project</link>. Original filenames, pinned repository tree, Git blob and SHA-256 provenance retained.')
def nxt():story.append(PageBreak())
h('UAV airframe: 62-body CAD and published FEM')
p('13 October 2026. This extension collects three CAD/FEM evidence projects: two distinct UAV assemblies and a layered composite pipe. A differential shaft is held for contradictory results; a rear axle is excluded because its archive contains setup without located saved numerical FEM results.')
img(T/'uav-original-step-view.png',485,185)
p('<b>Read-only original STEP view:</b> valid native BREP with 62 solids and 5,639 faces. Envelope 400.351 x40.7 x400.351 mm agrees with source report. CAD display triangles do not constitute a newly generated solver mesh.')
img(U/'total deformation.jpg',450,230)
p('<b>Original publisher FEM figure:</b> maximum displacement 0.0023987 m =2.3987 mm. Original report.mht has table-index 35 with the same value. It also records peak principal stress 342.76 MPa, equivalent elastic strain 0.0045572 and total strain energy 0.039066 J. Exact original numeric table rows are preserved in NPZ, without new solves.')
p('Source model: 545,580 nodes, 266,057 elements and 132 bonded contacts; four 10 N thrust forces and one fixed edge. Carbon plates/rods are orthotropic, ABS/steel isotropic. Large deflection is off. This is a constrained structural test rather than free-flight behavior.')
p('One original CAD/report/plot candidate. Report lists a 205.44 MB RST, but that file was not uploaded; WBPJ alone is not a full result archive. Source material orientation, edge/force scope and mesh convergence need review. Peak principal stress at steel hardware exceeds the nominal 250 MPa yield input, so no validated safe capacity is claimed.')
src(uc)
nxt();h('Second UAV: native CAD and dimensioned drawings')
img(Q/'04_Images/01_CAD_Assembly/01_Final_Assembly/01_Final_Drone_Assembly.png',430,135)
p('<b>Original source CAD assembly view:</b> two native SolidWorks assemblies and 17 SLDPRT files are preserved, including structural arms, frame, covers, motors, propellers and fasteners. Compatible native import, dependencies and exact analysis assembly matching remain pending; no neutral STEP assembly was uploaded.')
img(T/'quadcopter-original-drawing-page-6.png',485,320)
p('<b>Original engineering drawing, page 6:</b> arm orthographic views, section A-A, hole sizes, radii, angles and lengths. Visible labels include 300 mm side extent, 325 mm plan extent, three diameter-10 holes and section scale 1:2. The different extents require interpreting the bent geometry, not replacing one dimension with another.')
p('Original drawing PDF has 21 pages: assembly identification/views, bill of materials and 16 dimensioned part pages. All pages were visually inventoried; page 21 adds a detailed main-frame drawing. This is one drawing file for one UAV family, not 21 independent benchmark tasks. Full tolerance/material/manufacturing completeness is not certified.')
p('Drawing-to-CAD-to-FEM candidate can use these original views after checking dimensions against the source native parts and reduced analysis assembly. Source BOM has 16 nomenclature groups; the repository has 17 native part files. File count is not the count of independent engineering systems.')
src(qc)
nxt();h('Second UAV: saved static structural result')
img(Q/'02_ANSYS/01_Static_Structural/03_Results/03_Equivalent_Elastic_Strain/01_Equivalent_Elastic_Strain_0.00066362.png',490,275)
p('<b>Original ANSYS equivalent-stress figure:</b> maximum 1.3927 MPa; source deformation figure gives 0.86549 mm and equivalent elastic strain 0.00066362. Original filenames mislabel three images: the selected strain-named file shows stress; the stress-named file shows deformation; the deformation-named file shows strain. Quantities were checked from visible legends. These are source references, not newly decoded fields.')
table([['Original saved system','Inventory / setup'],['Static RST','49,086,464 bytes; 115,505 result nodes; 80,288 elements; one saved set'],['Prescribed loads','Four separate +Z remote force-node cards, 32 N each; total 128 N'],['Gravity / support','ACEL Z=9806.65 mm/s2; one fixed-face support'],['Material cards','PETG labeled NylonCF: E 2100 MPa, nu 0.35, density 1270 kg/m3'],['Full archive','378,964,300-byte original LFS WBPZ; SHA-256/size/CRC verified']],[165,320])
p('Source log/deck identifies ANSYS 2026 R1. The original file is retained, with metadata-only inspection. Legacy full-field decoding is held because recent ANSYS files can be misread; source images and numerical legends remain available. No source journal was executed or new solve launched.')
p('Source full-CAD mass 4.15 kg includes overridden properties and a detailed propulsion assembly. The finite-element analysis uses an analysis assembly; mass/inertia/material scope must be matched. The report computes a safety factor from 50 MPa yield divided by 1.3927 MPa; that is a source interpretation, not validated certification.')
p('Check actual contact/constraint topology, load distribution, mesh refinement and source revision before scoring displacement or peak stress. This static case and the two dynamic systems remain three solution candidates within one geometry family.')
src(qc)
nxt();h('Second UAV: modal and harmonic source references')
img(Q/'02_ANSYS/02_Modal/04_Natural_Frequencies/01_Natural_Frequencies_1-6.png',485,140)
p('<b>Original cropped modal-result excerpt:</b> the supplied image cuts off the first two modes. All six source-rounded frequencies are listed below and in the full original report. Saved RST header values match the table within 0.0005 Hz; the exact native frequencies are preserved in original-modal-frequency-references.npz.')
rows=[['Mode','Original RST frequency Hz','Source rounded Hz']]
for i,(f,rounded) in enumerate(zip(qc['saved_systems'][1]['set_labels'],[72.582,72.605,72.618,72.620,89.963,89.971]),1):rows.append([i,f'{f:.8f}',rounded])
table(rows,[65,225,195])
p('Modal file has 15,526 result nodes and 9,198 elements. Four 0.105 kg point masses replace detailed motor/propeller geometry. Four partition RST files are distributed-solver pieces and do not represent four extra cases. Mode-vector extraction and compatible native CAD matching remain pending.')
img(Q/'02_ANSYS/03_Harmonic_Response/02_Stress_vs_Frequency/01_Harmonic_Normal_Stress_vs_Frequency.png',485,130)
p('<b>Original harmonic plot:</b> source report approximates a peak near 90 Hz, normal stress amplitude 0.0151 MPa and displacement amplitude 0.186 mm. These plot estimates are held pending exact complex-response extraction. The saved harmonic RST is804,913,152bytes: 300 stored sets, real/imaginary pairs at150 frequencies, not300 simulations.')
p('<b>Load conflict:</b> report describes four32N excitations, but final source harmonic deck has only two excitation-node force cards. Unit-load modal expansion commands are separate from the final force cards. Load mapping, damping, point selection and amplitude/phase conventions must be resolved before harmonic scoring. Static four-force cards are independently verified.')
src(qc)
nxt();h('Composite pipe: native geometry and saved FEM')
img(T/'pipe-original-iges-view.png',485,220)
p('<b>Read-only original IGES view:</b> valid18-face surface BREP, zero solids, envelope 374 x374 x1000mm. Source SolidWorks solid/mid-surface parts and Parasolid files are also retained. Geometry is moderate; the engineering complexity lies in layered orthotropic shells, sections and local fiber orientations.')
table([['Published original file / revision','Review finding'],['Archived Workbench18.1 RST','11,862,016bytes, MPA units: mm/N/MPa;255nodes, 420elements, 1static set'],['Loose Workbench2023R2 RST','10,944,512bytes, MKS units; same mesh count, separate source revision'],['Archived displacement read','255 x 6DOF; finite; max translational norm1.313397mm; rotations kept separate'],['Original applied pressure cards','Archive 1MPa; loose1,000,000Pa; equal physical pressure does not imply equal materials'],['Auxiliary ACP STEP','Valid one solid, 8 faces, 380x380x206mm; different geometry scope from full 1000mm pipe']],[200,285])
p('<b>Decoder limits:</b> archived displacement is exploratory and held from scoring. Loose-source legacy decode returns unphysical values around 1e307; no loose-field NPZ is retained. Legacy shell stress recovery terminated the process; no usable nodal stress or certified ply-failure reference was extracted. Both originals remain intact for a compatible ACP/MAPDL reader.')
p('<b>Material conflict:</b> archived 18.1 deck includes structural-steel cards for sections1-3 and orthotropic material4; loose2023R2 deck has orthotropic cards. Source revisions are not merely unit conversions. Original ACP ply definitions, rosettes, thicknesses and failure criteria are preserved but require exact case mapping. Do not substitute isotropic von-Mises failure scoring for orthotropic ply criteria.')
p('One pipe raw-source candidate, with two source revisions, remains held for numerical/geometry/laminate verification. No new mesh, CAD scaling, source runACP.py execution or FEM solution was generated. Documentation MIT notice does not establish an unrestricted data-license grant for the original CAD/ANSYS project.')
src(pc)
nxt();h('Differential shaft: drawing retained, FEM held')
img(S/'WhatsApp Image 2026-01-07 at 9.35.58 PM.jpeg',495,180)
p('<b>Original dimensioned Fusion revolve sketch:</b> total axial length116.5mm, stepped profile dimensions, reliefs and angle 160degrees. Separate original screenshots document22spline repetitions,1mm fillet and chamfer details. The native F3D is preserved; stored preview extraction passed ZIP CRC. No compatible solid import or CAD reconstruction was attempted.')
img(S/'WhatsApp Image 2026-01-08 at 10.10.57 AM.jpeg',470,190)
p('<b>Original ANSYS deformation figure:</b> the extreme displacement shown corresponds to the problematic 2023R1 report, not the revised values claimed in the presentation. No new values were generated or units silently corrected.')
table([['Source numerical claim','Stress MPa','Displacement mm'],['Presentation / README','152.23','0.11106'],['Original saved report pages16-18','45,764','112,160 max;23,808 min']],[225,100,160])
p('The source report geometry is116.5mm long, but maximum displacement is about963times that length. Report uses183,268nodes/125,453elements, 100 rad/s rotation,15Nmm moment,20 N Y force and frictionless support. Presentation claims ANSYS 2025R2, while the uploaded report is2023R1. Revised 152.23MPa/0.11106mm values have no matched saved RST or corroborating result figure in the upload.')
p('Zero qualified shaft FEM references admitted. Preserve the native CAD, dimensioned sketch and conflicting documents for source review. The sketch is not a complete manufacturing drawing. Claimed analytical +/-5% agreement does not repair contradictory source FEM outputs or prove correct constraints.')
src(sc)
nxt();h('Collection inventory and benchmark readiness')
table([['Added source evidence','Count / status'],['Carbon-fiber UAV','1 valid 62-solid STEP + report/plot candidate; no raw RST uploaded'],['Second quadcopter','1 native CAD family; 3 saved FEMsystems;1 drawing PDF with21pages'],['Layered pipe','1 raw source candidate; 2 source revisions; decoded reference admission held'],['Differential shaft','Native CAD / dimensioned sketch retained; contradictory FEM held,0qualified'],['Rear axle','Native SLDPRT and WBPZ setup-only archive;0located numerical FEM pairs'],['Certified cases / model scores','0 / none']],[175,310])
p(f'<b>Provenance:</b> {check["original_repository_files_verified"]} original repository files passed byte-size, pinned Git blob SHA-1 and SHA-256 checks. An additional publisher LFS archive passed its 378,964,300-byte size, SHA-256 and archive CRC. UAV MHT scalar copies match original rows; quadcopter modal frequencies match the original binary header and source rounding. Pipe archive extraction was checked against unchanged archive bytes.')
p('<b>Supplied CAD to FEM:</b> add source candidates with exact original CAD/CAE scope and references listed in catalogs. Quadcopter static/modal/harmonic are one family; their solver partitions, frequencies and real/imaginary sets are not extra tasks. Resolve harmonic load conflict, compatible field decoding, contact/material scope and convergence before evaluation.')
p('<b>Drawing to CAD to FEM:</b> the original 21-page quadcopter drawing file adds dimensioned views and sections for 16part types. Verify each against native CAD and determine which parts are active in each reduced analysis. The shaft sketch adds geometric evidence but no qualified matched FEM reference. Full manufacturing specifications remain uncertified.')
p('<b>Held rear axle:</b> original Workbench inventory has geometry/material/model databases but no located RST/RTH or numerical FEM output. README directs the reader to clear generated data and re-solve. Handwritten calculations are analytical references; do not count them as FEM results. No solve was performed.')
p('<b>Package policy:</b> retain original378.96MB quadcopter WBPZ intact; omit redundant extracted RST/mode/full/element-matrix files from the outer ZIP. Those raw files remain inside WBPZ and locally. Include extracted source decks/logs and metadata for review. Pipe source RST revisions are included; exploratory displacement NPZ is marked held.')
p('<b>Licenses:</b> quadcopter repository MIT notice retained; composite-pipe documentation is MIT, while source CAD/ANSYS data licensing is narrower/unresolved. Other sources have no explicit data license found. Collection remains local research; no public release or license grant is implied.')
p('Three CAD/FEM evidence projects covering two geometry types, plus two excluded sources. No locally created engineering problem/CAD, new FEM solve, COMSOL dependency, frontier-model call or measured model score. Numerical samples and screenshots are source references, not automatic benchmark admissions.')
src(ac)
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | original geometry, drawings, results and provenance');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'uav-pipe-shaft-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True)
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if not f.is_file():continue
   if root==Q and 'extracted-original' in f.parts and f.suffix.lower() not in ['.dat','.out','.err','.xml','.txt','.wbpj']:continue
   z.write(f,root.name+'/'+str(f.relative_to(root)),compress_type=zipfile.ZIP_STORED if f.name=='original-LFS-archive_DRONE.wbpz' else zipfile.ZIP_DEFLATED)
 z.write(O,O.name);z.write(T/'source-verification.json','verification/source-verification.json');z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
 for f in ['collect_web_uav_shaft.py','fetch_original_quad_archive.py','audit_web_uav_shaft.py','verify_web_uav_shaft.py','report_web_uav_shaft.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
 for f in ['uav-original-step-view.png','pipe-original-iges-view.png','quadcopter-original-drawing-page-6.png','quadcopter-original-drawing-page-21.png']:z.write(T/f,'inspection-views/'+f)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));members=len(z.namelist())
hh=hashlib.sha256()
with Z.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):hh.update(b)
q={'zip':str(Z),'bytes':Z.stat().st_size,'sha256':hh.hexdigest(),'members':members,'CRC_verified':True,'pdf_pages':len(doc),'quadcopter_raw_RSTs_preserved_in_original_WBPZ':True,'redundant_extracted_quadcopter_RSTs_omitted':True};(T/'package-validation.json').write_text(json.dumps(q,indent=2)+'\n');print(q,flush=True)
