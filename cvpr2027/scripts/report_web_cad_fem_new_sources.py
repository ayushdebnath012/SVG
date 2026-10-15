from pathlib import Path
import json,hashlib,zipfile,cadquery as cq,resvg_py,pymupdf as fitz
from PIL import Image as PILImage,ImageOps,ImageDraw
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parents[1];A=R/'data/web-agentfem-brackets';C=R/'data/web-cadworld-fem';O=R/'output';T=R/'tmp/cad-benchmark-search/report';T.mkdir(exist_ok=True)
a=json.loads((A/'catalog.json').read_text());c=json.loads((C/'catalog.json').read_text());styles=getSampleStyleSheet();styles['Normal'].fontSize=10;styles['Normal'].leading=14;styles['Heading1'].textColor=colors.HexColor('#153956');story=[]
def p(s,style='Normal'):story.append(Paragraph(s,styles[style]));story.append(Spacer(1,8))
def im(path,h=230):
 x=PILImage.open(path);f=min(495/x.width,h/x.height);story.append(Image(str(path),width=x.width*f,height=x.height*f));story.append(Spacer(1,8))
def tab(rows,widths=[220,275]):
 t=Table([[Paragraph(str(x),styles['Normal']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef4')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#bbc9d3')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
def cad(shape,name):
 svg=cq.exporters.getSVG(shape,opts=dict(width=1200,height=580,showHidden=False,showAxes=False,projectionDir=(1,-1,.7),strokeWidth=-1,marginLeft=25,marginTop=25));out=T/(name+'.png');out.write_bytes(resvg_py.svg_to_bytes(svg_string=svg,background='white'));return out
p('More web CAD + FEM pairs','Title');p('Collected 12 October 2026 | Original published assets | No local geometry generation or FEM solves')
tab([['New source','Downloaded and verified'],['AgentFEM bracket elasticity','176 STEP + mesh + displacement/stress pairs; 128 train / 16 validation / 32 test. One parametric family.'],['CADWorld FEM','3 native FreeCAD projects + saved CalculiX results + CSVs + task/evaluator JSON. Two geometry candidates; one basic specimen.']])
p('179 new CAD/result pairs. These are candidates, not 179 distinct complex engineering task types. They extend the collection; earlier aircraft, implant, crash, forming, valve and WAAM sources remain available.')
p('Zero new certified benchmark admissions. Bracket STEP unit metadata conflicts with field coordinates. CADWorld references include very high elastic stress/deformation. Preserve the published data and resolve these issues before judging engineering accuracy.')
p('The supplied-CAD track gains original native geometry and numerical outputs. No new original dimensioned drawing was verified. Inspection renders and task screenshots are labeled accordingly; they do not complete the drawing-to-CAD track.')
p('Checks include publisher SHA-256 hashes where provided, ZIP CRC, native solid validity, finite numerical fields, source load correspondence and cross-checks of reference values. No frontier model trial or independent solver replay was performed.')
p('Sources:<br/><link href="https://huggingface.co/datasets/HaomingLuo/AgentFEM-Bracket-Elasticity">AgentFEM-Bracket-Elasticity</link> (CC BY 4.0, Haoming Luo).<br/><link href="https://github.com/Zdong104/CADWORLD">CADWorld repository</link>; <link href="https://huggingface.co/datasets/Zihan1004/CADWORLD">publisher dataset</link> declares Apache-2.0. Embedded material-card licenses remain intact.')
story.append(PageBreak());p('Bracket elasticity: CAD and FEM references','Heading1')
r=next(x for x in a['records'] if x['id']=='fresh_test_000');shape=cq.importers.importStep(str(A/r['cad'])).val();im(cad(shape,'bracket'))
p('Inspection render of downloaded fresh_test_000 STEP solid. Not an original dimensioned drawing. Geometry has two feet and curved support webs; bonded feet and uniform downward seat traction replace bolt contact.')
tab([['Published result at 10,000 N','Value'],['Mean seat displacement','0.098354836386 mm'],['Maximum displacement','0.175628088556 mm'],['Sampled peak von Mises stress','78.539213022749 MPa'],['Sampled 95th percentile stress','42.922439729845 MPa']])
p('All 176 arrays are finite, fixed-plane displacements are zero, and summary values agree with the original NPZ arrays. Material: E = 70 GPa, nu = 0.33, density = 2700 kg/m3. Feet: z = 0; load seat: z = 0.189 m. Raw references retain their 1000 or 10000 N load.')
p('UNIT BLOCKER: STEP declares millimetres, but its numeric extents are 0.306 x 0.080 x 0.189 and match FEM metres without conversion. That is a factor-1000 scale inconsistency. Source files are retained unchanged; no corrected CAD is substituted.')
p('Publisher states a nominal 9 mm mesh, no industrial convergence qualification, and no plasticity/fracture/contact validation. Sharp-junction stress is a raw sampled output, not a validated strength score.')
for r in c['records']:
 story.append(PageBreak());p(r['task_name'],'Heading1');im(cad(cq.Shape.cast(__import__('OCP.TopoDS',fromlist=['TopoDS_Shape']).TopoDS_Shape()) if False else __import__('cadquery').Shape.importBrep(str(R/'tmp/cad-benchmark-search/cadworld-brep'/(r['id']+'.brp'))),r['id']),h=205)
 p('Inspection render of original native FreeCAD Body BREP. '+r['complexity']+'. This is not an original dimensioned drawing.')
 tab([['Original native project / CSV','Verified content'],['CAD',f"{r['geometry']['solids']} solid; {r['geometry']['faces']} faces; valid BREP; editable FCStd retained"],['Published load',f"{r['loads'][0]['force_N']:g} N"],['Result rows',r['csv_rows']],['Maximum displacement',f"{r['csv_statistics']['Displacement Magnitude']['max']*1000:.6g} mm"],['Peak von Mises stress',f"{r['csv_statistics']['von Mises Stress']['max']/1e6:.6g} MPa"]])
 p('Saved FCStd includes displacement vectors, von Mises arrays, mesh and VTU results. All CSV values are finite. CSV displacement in m agrees with native mm; CSV stress in Pa agrees with native MPa. Source evaluator extrema match the CSV with its stated 5% tolerance.')
 if r['id']=='freecad-fem-001':
  p('Publisher task image identifies the fixed and loaded ends. 200 N Y-axis load, AlMg3F24, Gmsh mesh max 2 mm/min 0.5 mm, CalculiX. Large displacement and 705 MPa stress require checking elastic validity and strength interpretation before benchmark certification.')
 elif r['id']=='freecad-fem-002':
  p('20 kN tension task, Iron-Generic, Gmsh mesh max 1 mm/min 0.5 mm, CalculiX and displacement WarpVector. Peak stress is about 76.6 GPa: this is a saved software-workflow reference, not a credible elastic strength label. No link-link contact solution verified.')
 else:p('20 MN force, AlZn4-5Mg1F35, Gmsh mesh max 5 mm/min 0.5 mm, CalculiX. About 811 mm displacement and 2.72 TPa stress make this unsuitable as validated elastic engineering ground truth. Retained as a basic workflow fixture; excluded from complex task counts.')
 p('Original task/evaluator JSON, precondition project, solved project and full numerical CSV are included. No source evaluator or solver was executed locally. Independent replay, mesh convergence and physical-validity review remain pending.')
pdf=O/'pdf/web-cad-fem-new-sources-179.pdf';SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=38).build(story)
doc=fitz.open(pdf);thumbs=[]
for i,page in enumerate(doc):
 pix=page.get_pixmap(matrix=fitz.Matrix(1,1));path=T/f'page-{i+1}.png';pix.save(path);x=PILImage.open(path).convert('RGB');x.thumbnail((350,495));thumbs.append(x)
contact=PILImage.new('RGB',(350*3,530*2),'#dce3e9')
for i,x in enumerate(thumbs):contact.paste(x,((i%3)*350,(i//3)*530));ImageDraw.Draw(contact).text(((i%3)*350+10,(i//3)*530+500),f'Page {i+1}',fill='black')
contact.save(O/'web-cad-fem-new-sources-preview.png');print('PDF',len(doc),'pages',pdf)
