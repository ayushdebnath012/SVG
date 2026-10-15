from pathlib import Path
import json,hashlib,zipfile
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import pymupdf
D=Path('cvpr2027/data/web-cad-fem-assemblies');T=Path('cvpr2027/tmp/cad-fem-assemblies-search');O=Path('cvpr2027/output/pdf/web-cad-fem-frame-kiteboard.pdf');cat=json.loads((D/'catalog.json').read_text());styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.5;styles['BodyText'].leading=13;story=[]
def p(s):story.append(Paragraph(s,styles['BodyText']));story.append(Spacer(1,6))
def h(s):story.append(Paragraph(s,styles['Heading1']));story.append(Spacer(1,8))
h('Published test-bench frame CAD + FEM')
p('12 October 2026 | Web-source collection extension | No local CAD creation, FEM solves or model calls')
p('Added one native CAD case with saved numerical fields and one kiteboard CAD candidate with published FEM plots/scalar. Neither is benchmark-certified. Original dimensioned drawing coverage: zero for these two sources.')
story.append(Image(str(T/'frame-cad.png'),width=390,height=201));p('<b>Original CAD inspection:</b> valid FreeCAD BREP, one solid and 26 faces; bounding dimensions 2000 x 1500 x 100 in native coordinates. The model retains its sketch, pad, pocket and Boolean history.')
story.append(Image(str(T/'frame-fem.png'),width=390,height=201));p('<b>Saved CalculiX reference:</b> stress values at original mesh coordinates. All 2356 nodes have matched source IDs, finite displacement/stress/strain values, and consistent displacement magnitudes. Maximum |u| = 19.0097107742; maximum von Mises = 477.6683112864, in source units.')
p('Von Mises recomputed only as a consistency check on the saved stress tensor: maximum absolute difference 1.14e-13. No FEM solution generated. Steel E = 200000 MPa, Poisson ratio = 0.3. Native setup includes self-weight, a fixed face, and prescribed X displacement -19. Unit/replay and mesh-convergence checks remain before admission.')
p('Primary source: <link href="https://github.com/MarcusAdielsonGuichet/Test-Bench-Digital-Twin" color="blue">MarcusAdielsonGuichet / Test-Bench-Digital-Twin</link>. No explicit data license located. The four external small-mesh FRD test runs are unpaired supporting files, not additional frame cases.')
story.append(PageBreak());h('Composite kiteboard: CAD + published FEM reference')
p('Original Ansys ACP/Mechanical workshop download contains STEP shell geometry, a separate solid core and native Workbench project archives. STEP core: one valid solid, 46 faces. Shell STEP: three faces, zero solids. This adds a shaped composite product and failure-analysis task.')
story.append(Image(str(T/'kiteboard_core-cad.png'),width=400,height=206));p('<b>CAD inspection render:</b> original kiteboard_core.stp from Kiteboard_SOLVED_2025R1. No geometry generated. The shell and core remain separate original files.')
img=D/'kiteboard/acp_tut_tut-7_image_093_01.png';story.append(Image(str(img),width=360,height=275));p('<b>Original published FEM figure:</b> maximum inverse reserve factor 1.0099; shown probe reads 1.009947434 at element 684. This is a dimensionless failure-factor reference, not a frontier-model score.')
p('The download explicitly skips file.rst, ds.dat and solve.out. Keep this as a plot/scalar-reference candidate; no raw nodal fields are present. The reference page is v261 and its linked archive 2025R1: version/setup correspondence and scoring tolerance require review. Replay needs Ansys ACP/Mechanical; no COMSOL dependency.')
p('Sources: <link href="https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/acp_tut/acp_tut7_setup.html" color="blue">original archive setup page</link>; <link href="https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/acp_tut/acp_tut7_postprocess.html" color="blue">published FEM postprocessing references</link>. Publisher copyright retained; no standalone data license asserted.')
story.append(PageBreak());h('Collection inventory and benchmark use')
p('Two new task families: structural frame deformation/stress and composite kiteboard failure. Candidate labels preserve differences in reference completeness. The source files and extracted field table are supplied for local research review.')
rows=[['Source','CAD','FEM reference','Status'],['Test-bench frame','Native FreeCAD BREP','2356 nodal vectors + stress/strain','Candidate, raw fields verified'],['Composite kiteboard','Original STEP shell + solid core','Published plots; IRF scalar 1.0099','Candidate, no raw field file'],['Four other ACP workshops','Native project geometry / auxiliary STEP','No raw fields verified','Held; excluded from count']]
tb=Table([[Paragraph(x,styles['BodyText']) for x in row] for row in rows],colWidths=[110,115,135,145]);tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.append(tb);story.append(Spacer(1,15))
p('<b>Counts:</b> one native CAD + saved numerical-field case; one native CAD + published plot/scalar candidate; zero newly certified benchmark cases. Saved solver outputs, mesh nodes, plies and CAD auxiliary tools are not counted as independent tasks.')
p('<b>Track readiness:</b> supplied-CAD-to-FEM candidates await reproducibility, source consistency and tolerance review. Drawing-to-CAD-to-FEM receives no complete dimensioned-drawing case in this extension. CAD inspection renders do not replace original engineering drawings.')
p('<b>Held sources:</b> bonded T-joint, advanced sandwich panel, composite solid extrusion and cutoff-rule modeling. Their original archives were downloaded and inventoried under web-cad-fem-acp; no raw .rst/.rth fields verified. A modeling tutorial marked SOLVED is not evidence of a saved FEM solution. A fusion graphite-foam heat-exchanger lead has numerical temperature profiles and a hybrid FE mesh, but no native CAD/BREP found in the linked record.')
p('<b>Package:</b> original native CAD/archives, untouched source result files, source links and revisions, source image references, SHA256 manifest, node-ID-preserving extracted frame CSV, and audit catalog. No downloaded code or solver was executed. No frontier-model performance measured.')
p('<b>Source handling:</b> source copyright/data-license status recorded in catalog. Local collection only; no repository commit or public release performed. Original downloads preserved separately from derived inspection figures and extracted values.')
def footer(c,d):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(45,25,'Original web CAD and FEM references; candidates are not certified admissions');c.drawRightString(550,25,str(d.page))
SimpleDocTemplate(str(O),pagesize=(595,842),leftMargin=45,rightMargin=45,topMargin=30,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
d=pymupdf.open(O);assert len(d)==3, len(d)
for i,page in enumerate(d):page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(T/f'frame-kiteboard-report-{i+1}.png')
files=[p for p in D.rglob('*') if p.is_file() and p.name!='package-manifest.json'];manifest=[dict(path=str(p.relative_to(D)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)];(D/'package-manifest.json').write_text(json.dumps(manifest,indent=2));files.append(D/'package-manifest.json');out=Path('cvpr2027/output/datasets/web-cad-fem-frame-kiteboard.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,str(p.relative_to(D)))
with zipfile.ZipFile(out) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()))
print('PDF',len(d),'pages; ZIP',len(files),'files',out.stat().st_size,'bytes')
