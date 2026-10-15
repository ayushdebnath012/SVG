"""Show original CAD/results and package source bytes plus read-only field extracts."""
from pathlib import Path
import json,zipfile,hashlib,html
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-machinery-contact-search')
names=['web-cad-fem-shock-absorber','web-cad-fem-screw-jack','web-cad-fem-industrial-thermal','web-cad-fem-piston-pin-assembly'];roots=[D/n for n in names];cats=[json.loads((r/'catalog.json').read_text()) for r in roots];v=json.loads((T/'source-verification.json').read_text())
O=Path('cvpr2027/output/pdf/web-cad-fem-machinery-thermal.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-machinery-thermal.zip');styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.5;styles['BodyText'].leading=12.6;styles['Heading1'].fontSize=18;styles['Heading1'].leading=22;story=[]
def p(s):story.extend([Paragraph(s,styles['BodyText']),Spacer(1,6)])
def h(s):story.extend([Paragraph(s,styles['Heading1']),Spacer(1,8)])
def makepic(f,w,mh):
    im=PILImage.open(f);hh=w*im.height/im.width
    if hh>mh:w*=mh/hh;hh=mh
    return Image(str(f),width=w,height=hh)
def pic(f,w=490,mh=240):story.extend([makepic(f,w,mh),Spacer(1,7)])
def pictures(fs,w=160,mh=245):
    t=Table([[makepic(f,w,mh) for f in fs]],colWidths=[490/len(fs)]*len(fs));t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER')]));story.extend([t,Spacer(1,8)])
def table(rows,widths):
    t=Table([[Paragraph(html.escape(str(x)),styles['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,7)])
def src(i):p(f'Source: <link href="{cats[i]["source"]}" color="blue">original publisher repository</link>. Original author notices, pinned revision and file hashes retained.')
def nxt():story.append(PageBreak())
h('Shock absorber: original CAD and FEM plots')
p('13 October 2026. This extension collects two new complex mechanical assemblies and two thermal controls from three source repositories. The existing piston assembly is identified as a duplicate and adds zero items. All engineering CAD and FEM references were published by their sources; no new geometry, problem or solver run was generated.')
pictures([roots[0]/'result references/geometry.png',roots[0]/'result references/stress.png',roots[0]/'result references/deformation.png'],155,255)
p('<b>Unchanged source images, left to right:</b> CAD assembly; equivalent stress; total deformation. The original CATIA parts/products and neutral STEP are included. Source plot maxima are <b>198.44 MPa</b> and <b>8.0874 mm</b>; the stress minimum is 0.00072284 MPa.')
table([['Read-only source STEP inspection','Result'],['Geometry validity / topology','Valid; 12 solids; 207 faces'],['Source CAD envelope','75 x 75 x 388.50 mm; STEP declares millimeter units'],['Original native definitions','13 CATPart files, 2 CATProduct files, 1 STEP'],['Existing FEM reference','One static plot candidate; no uploaded raw RST']],[215,275])
p('<b>Setup hold:</b> the bare WBPJ references missing SpaceClaim and Mechanical databases. Exact applied loads, fixed faces, body materials and contact scope are not documented numerically in the uploaded evidence. Finished result images cannot supply those missing inputs. STEP/native configuration and FEM mesh matching remain pending.')
p('The README also claims modal and PSD random-vibration analysis, but no frequencies, PSD input or response results were found. The source static label 1 s is a load-step label, not an impact or damping history. Complex shock-absorber CAD does not establish simulated hydraulic damping.')
p('No complete dimensioned drawing or explicit data license was located. Original source files are retained for local research; strict numerical grading remains held.')
src(0)
nxt();h('Screw jack: CAD and conflicting FEM references')
pictures([roots[1]/'Screw Jack/Images/Screw_Jack_Assembly/Assem1.PNG',roots[1]/'Screw Jack/FEA/Equivalent Stress.png'],230,265)
p('<b>Unchanged source CAD and equivalent-stress images.</b> The download contains a native SOLIDWORKS assembly plus seven part definitions. Compatible import is pending. The source reports seven bodies, 9.077 kg mass and envelope 242.32 x 365.11 x 262.46 mm; those statistics were not independently recomputed.')
table([['Quantity','Original plot','README'],['Peak von Mises stress [MPa]','5.5054','5.5224'],['Peak total deformation [mm]','0.0022549','0.0014249'],['Peak equivalent elastic strain','5.0912e-5','Not tabulated']],[195,145,150])
p('<b>Revision hold:</b> keep both published references. No average or silent replacement is used. Original stress, displacement, strain, safety-factor and mesh images are included. The displayed safety factor is capped; it does not establish an exact structural margin.')
p('Source setup states FY = +1000 N, structural steel E = 200,000 MPa, nu = 0.3, yield = 250 MPa, eight bonded contact regions and mesh of 58,642 nodes / 33,631 elements. Fixed/load-face scope and the geometry revision corresponding to each result remain unresolved.')
p('The README says STEP, engineering drawings and a complete report are supplied, but the pinned tree has no STEP, SLDDRW, PDF report, MECHDB or RST. A WBPJ index alone is not a saved solution archive. Treat this as one static assembly candidate, not a validated frictional-thread, lifting-cycle or buckling-capacity task.')
src(1)
nxt();h('Curved steam pipe: CAD and saved thermal fields')
pictures([T/'CurvedPipe-203773-original-thumbnail.png',T/'SYS-398752-original-thumbnail.png'],190,155)
p('<b>Original native SpaceClaim thumbnails:</b> bare curved pipe and explicit foam-insulated pipe. Their original SCDOC files and ACIS SAB geometry members are retained; independent BREP/body/face import remains pending. The archived A/B/C models have matching original decks and three RTH result files.')
table([['Part','Recovered outer iron peak [C]','Report peak [C]','Published heat loss [W]'],['A: bare pipe','128.494404','128.5','35.4'],['B: effective insulation','130.782671','130.8','32.3'],['C: explicit foam','128.324369','128.3','35.6']],[125,150,90,125])
p('All three recovered surface maxima round to the published references. A/B have 31,057 temperature nodes each; C has 51,145. Original node IDs and scalar temperatures are copied exactly. Coordinates and surface scopes are copied from the original NBLOCK/EBLOCK deck records; no FEM mesh or solution was generated.')
pic(T/'pipe-C-original-temperature-points.png',430,175)
p('<b>Read-only plot of existing Part C nodal values:</b> every sixth original point is displayed; full arrays remain unchanged. Global temperature is 118.163736 to 128.473561 C. The outer foam maximum is <b>118.774152 C</b>; the reported 128.3 C is the outer cast iron interface, not the foam surface. Separate source masks preserve this distinction.')
p('Native decks use MKS units, cast iron k = 52 W/m/C, inner convection 20 W/m2/C to 155 C, outer ambient 20 C and adiabatic ends. A uses exterior h = 3.8; B uses h = 3.4 without a separate foam body; C models foam k = 0.2 with exterior h = 3.8. Radiation is omitted. Heat-loss magnitudes above come from the report; heat-flow arrays are not claimed as recovered.')
src(2)
nxt();h('Elbow thermal shock: native CAD and published results')
doc=pymupdf.open(roots[2]/'TransientThermalAnalysis/AnalysisReport.pdf')
for x in doc[4].get_images(full=True):
    im=doc.extract_image(x[0])
    if im['width']==348 and im['height']==275:(T/'elbow-original-final-page-FEM.png').write_bytes(im['image'])
pictures([T/'elbow-157622-original-thumbnail.png',T/'elbow-original-final-page-FEM.png'],210,165)
p('<b>Unchanged native CAD thumbnail and original final-page FEM image.</b> This is a second, 90-degree elbow geometry. The source contains its native SCDOC, a two-page task statement and a five-page report; no transient RTH or numerical time-history archive was uploaded.')
table([['Insulation thickness [mm]','Published heat loss [W]'],['1.5 / 2.5 / 5 / 10 / 15','39.835 / 39.921 / 40.070 / 40.147 / 39.997'],['7.5 / 12.5 / 10.5','40.143 / 40.096 / 40.141']],[185,305])
p('Source insulation sweep identifies thickness 10 mm, outer radius 55 mm, as the approximate maximum-heat-loss point. This is one geometry/parameter study, not eight distinct CAD families.')
table([['Source analysis time [min]','Published outer-insulation peak [C]'],['10 / 167 / 90 / 91','29.62 / 113.53 / 106.93 / 107.15'],['92 / 95 / 94','107.39 / 108.01 / 107.79']],[185,305])
p('For thermal shock, the source uses 15 mm insulation, initial uniform temperature 20 C, inner convection 50 W/m2/C to 150 C and exterior h = 3.7 to 20 C. The report uses 200 s time steps. Cast iron density is 7200 kg/m3 and cp = 447 J/kg/C; insulation density is 2500 and cp = 840. Temperature-dependent iron conductivity is in the original statement.')
p('<b>Criterion hold:</b> the report declares 95 minutes to steady state using 0.95 times the steady temperature in Celsius. This is the stated assignment convention; do not silently replace it with 95 percent of temperature rise or absolute Kelvin. No full-field transient verification or certified time-to-steady score is claimed.')
p('Native CAD and source task figures are present, but the figures do not specify every manufacturing dimension. These controls remain in the supplied-CAD track; drawing-to-CAD completeness is not verified.')
src(2)
nxt();h('Counts, provenance and benchmark readiness')
table([['This extension','Count / qualification'],['New source repositories / geometry families','3 / 4'],['New complex assemblies','2: shock absorber and screw jack'],['New thermal controls','2: curved pipe and 90-degree elbow'],['Original saved RTH candidates','3 steady insulation variants of one curved pipe'],['Downloaded original files verified','65 total: 55 new-source files, 10 duplicate-source files'],['Original archive extraction verified','55 files; source archive and five SCDOC CRC checks pass'],['Duplicate piston family increment','0: all CAD, index, README and three images already collected'],['Certified new admissions / model scores','0 / none']],[220,270])
p('<b>Integrity and source mapping:</b> original Git blob SHA-1, byte size and SHA-256 checks pass. Every extracted archive file equals its original bytes. RTH temperature copies match both the unsorted original scalar record after node-ID sorting and repeat safe result reads. Each native deck coordinate matches the preserved node ID. Surface masks match source convection scopes, and all three cast iron peaks round to the report values.')
p('<b>Decoder limit:</b> default legacy VTK mesh decoding exited 139. Safe header/scalar reading with read_mesh=False avoids that reconstruction and scalar vector rotation. Geometry coordinates and contact/convection scope membership are read from original text decks. This recovers stored data; it does not certify every binary quantity or replace independent native CAD import.')
p('<b>Duplicate piston audit:</b> the re-crawl matches eight previous source files byte-for-byte. Only two already-published animation files are new downloads, and they add no numerical targets. Existing piston reference remains 888.01 MPa and 0.22122 mm; no additional CAD family or static case is counted.')
p('<b>Other crawl exclusions:</b> official cooled-turbine archive has native CAD/setup but no RST/RTH output; deep-drawing/cutting dataset has solved mesh/fields but no verified native CAD; cold-plate source uses Fluent finite-volume CFD; engine blower has CAD/drawing without FEM; spring-testing machine and gearbox studies have reports/images without native CAD. None inflates the strict CAD/FEM count.')
p('<b>Next grading requirements:</b> freeze exact CAD revision, unit convention, body/material assignments, load/support faces and result scope. Shock loads are missing; screw-jack README/plot references conflict; thermal CAD kernel import and convergence assessment remain pending. Separate supplied-CAD and dimensioned-drawing tracks. Source extrema are FEM references, not frontier-model performance scores.')
p('Package includes all originals for the three new sources, original archive and extracted files, safe temperature/coordinate/scope copies, manifests/catalogs, original figures and this PDF. Duplicate piston originals are omitted from the ZIP; its audit points to the existing collection. No explicit licenses were located for the three new sources; original author/course notices remain intact. Local research only; no COMSOL, new solver run, source-program execution, model call or public release.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | machinery assemblies and saved thermal fields');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=36,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer);doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.45,1.45)).save(T/f'machinery-thermal-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True);assert len(doc)==5
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for R in roots[:3]:
        for f in sorted(R.rglob('*')):
            if f.is_file():z.write(f,R.name+'/'+str(f.relative_to(R)))
    for f in ['catalog.json','download-manifest.json']:z.write(roots[3]/f,'duplicate-piston-audit/'+f)
    z.write(O,O.name);z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
    for f in ['source-verification.json','crawl-leads-and-exclusions.json','exact-native-CAD-dedup.json','official-cooled-turbine-archive-inventory.json']:z.write(T/f,'verification/'+f)
    for f in ['audit_web_machinery_thermal.py','report_web_machinery_thermal.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
    for f in ['shock-original-STEP-view.png','pipe-C-original-temperature-points.png','elbow-original-final-page-FEM.png']:z.write(T/f,'inspection-views/'+f)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));nm=len(z.namelist())
res=dict(pdf=str(O),pages=len(doc),zip=str(Z),bytes=Z.stat().st_size,sha256=hashlib.sha256(Z.read_bytes()).hexdigest(),members=nm,CRC_passed=True,latest_pdf_visual_QA='Pending latest page inspection');(T/'package-validation.json').write_text(json.dumps(res,indent=2)+'\n');print(res,flush=True)
