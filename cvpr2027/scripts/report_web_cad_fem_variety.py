from pathlib import Path
import json,re,hashlib,zipfile
import cadquery as cq,resvg_py,pymupdf as fitz
from OCP.IGESControl import IGESControl_Reader
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/web-cad-fem-variety';OUT=ROOT/'output';TMP=ROOT/'tmp/cad-variety-report';TMP.mkdir(exist_ok=True)
styles=getSampleStyleSheet();styles['Normal'].fontSize=10;styles['Normal'].leading=14;styles['Title'].textColor=colors.HexColor('#153956');styles['Heading1'].fontSize=20
story=[]
def p(t,style='Normal'):story.append(Paragraph(t,styles[style]));story.append(Spacer(1,8))
def img(path,w=500,h=255):
 from PIL import Image as PI
 im=PI.open(path);scale=min(w/im.width,h/im.height);story.append(Image(str(path),width=im.width*scale,height=im.height*scale));story.append(Spacer(1,8))
def table(rows,widths=None):
 t=Table([[Paragraph(str(v),styles['Normal']) for v in r] for r in rows],colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eef3')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#bbc9d3')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t);story.append(Spacer(1,12))
def cad(file,name):
 if file.suffix.lower()=='.igs':
  r=IGESControl_Reader();r.ReadFile(str(file));r.TransferRoots();shape=cq.Shape.cast(r.OneShape())
 else:shape=cq.importers.importStep(str(file)).val()
 svg=cq.exporters.getSVG(shape,opts=dict(width=1200,height=620,showHidden=False,showAxes=False,projectionDir=(1,-1,.7),marginLeft=25,marginTop=25,strokeWidth=-1))
 svg=re.sub(r'stroke-width="([0-9.eE+-]+)"',lambda m:f'stroke-width="{float(m.group(1))*1.6}"',svg,count=1);path=TMP/(name+'.png');path.write_bytes(resvg_py.svg_to_bytes(svg_string=svg,dpi=96,background='white'));return path
p('More engineering varieties<br/>Original web CAD + FEM references','Title')
p('Collected 12 October 2026 | Four source collections | No new CAD or FEM solutions generated')
table([['Engineering family','Available original reference'],['Hip implant contact and fixation','IGES components + Abaqus deck + numerical stress/pressure CSV'],['Aircraft wing vibration','IGES wing surfaces + NASTRAN decks + ten nodal mode-shape fields'],['Turbine blade dovetail dynamics','STEP assembly + published reduced mass and stiffness matrices'],['Aircraft fuselage crashworthiness','STEP shell CAD + Abaqus decks + numerical acceleration/DRI plots']],[205,295])
p('The reference types are different. Hip scalars and wing modal fields are solved numerical references. Blade matrices are FE operators; crash results are published plots requiring digitization for automatic scoring.')
p('Four problem families. Four hip wear states, ten wing modes, sixteen blade preloads and three fuselage frame-count variants do not constitute 33 independent engineering task families.')
p('Benchmark status: zero new certified admissions. Source CAD views follow; these are inspection renders of downloaded geometry, not verified dimensioned engineering drawings. The CAD-input track gains candidates; the drawing-input track remains incomplete.')
p('All original assets, checksums, sources, reference types and limitations are in the accompanying dataset package. COMSOL sources are excluded. No model trials or solver runs were performed.')
story.append(PageBreak())
p('Hip implant contact and cement fixation','Heading1');img(cad(DATA/'hip-contact/Solid_model_pelvis.igs','hip'),h=225)
p('Inspection view of original pelvic IGES surfaces. Six original IGES files include pelvis, cement mantle and four cup wear states. Cups are solids; pelvis and cement import as valid surfaces.')
refs=json.loads((DATA/'hip-contact/matched-reference-values.json').read_text());table([['Wear mm','Cup VM MPa','Bearing p MPa','Cement VM MPa','Cement max principal MPa','Cement shear MPa']]+[[r['wear_penetration_mm'],r['cup_peak_von_mises_MPa'],r['bearing_peak_contact_pressure_MPa'],r['cement_peak_von_mises_MPa'],r['cement_peak_max_principal_MPa'],r['cement_peak_shear_MPa']] for r in refs],[55,75,80,80,120,90])
p('Published values copied from Results.csv for the CAD-matched 40 mm cup at 45 degrees. Other cup sizes/angles in the CSV lack matching CAD here. Input deck applies a 2500 N load with contact and nonlinear geometry; wear-state/deck mapping remains to verify.')
p('No separate native head CAD was verified; it remains represented in the solver deck. Numerical replay and tolerances are not certified.')
p('Source: Hua and Jin, University of Leeds. DOI 10.5518/13. CC BY 4.0.<br/><link href="https://archive.researchdata.leeds.ac.uk/15/">archive.researchdata.leeds.ac.uk/15/</link>')
story.append(PageBreak())
p('HIRENASD aircraft wing vibration','Heading1');img(cad(DATA/'hirenasd/hirenasd_AePW_DLR.igs','wing'),h=240)
p('Inspection view of original IGES surface CAD: 14 valid faces. NASTRAN BDF archives and the original coordinate-system PDF are included.')
table([['Published content','Verified extent'],['Mode-shape fields','10 modes; 159,841 nodes per mode; all nodal values finite'],['Columns','X, Y, Z, node ID, f1, f2, f3'],['Units / geometry','CAD in mm; field coordinates in m. Extents agree after conversion.'],['Coordinate excerpt, mode 1','First node coordinates: (0.7818463135, 0.8, 0.0003451690376) m. Complete original rows included as an excerpt.']],[155,345])
p('Fields are structural mode shapes interpolated onto a Centaur grid, not static displacements or stress fields. Sign, normalization, node mapping and frame conventions must be audited before mode-shape scoring. Frequency references are not included; the separate resource currently reports private access.')
p('Source: NASA DASHlink HIRENASD / Aeroelastic Prediction Workshop distribution.<br/><link href="https://c3.ndc.nasa.gov/dashlink/resources/354/">c3.ndc.nasa.gov/dashlink/resources/354/</link><br/>Public download; dataset-specific license was not stated on inspected pages.')
story.append(PageBreak())
p('Turbine blade dovetail contact dynamics','Heading1');img(cad(DATA/'turbine-blade/Assembly.STEP','blade'),h=240)
p('Inspection view of original mock-blade and two-slot STEP assembly: three valid solids, 102 faces. Separate blade and slot STEP/IGES files are included.')
table([['Published FEM object','Contents'],['M_GLOB','1968 x 1968 reduced mass matrix; finite and symmetric'],['K_GLOB_SE','1968 x 1968 x 16 reduced stiffness array; finite'],['CONNECTIVITY','132 x 6 contact-connectivity array'],['Preloads F_ax','1 N, then 2, 4, ... 30 kN'],['Source units','Mass: tons; stiffness: N/mm; positions: mm; load: N (Structures.xlsx).']],[155,345])
p('These are published FE reduced operators, not solved stress/displacement fields. Useful for reduction/operator tasks; they do not yet supply a full response ground truth. Experimental free-decay, frequency and damping data are separate and are not labeled as FEM results.')
p('Source: Botto and Glorioso, Politecnico di Torino. DOI 10.17632/xkssd7gr92.1. CC BY 4.0.<br/><link href="https://data.mendeley.com/datasets/xkssd7gr92/1">data.mendeley.com/datasets/xkssd7gr92/1</link>')
story.append(PageBreak())
p('Fokker F28 fuselage crashworthiness','Heading1');img(DATA/'fokker-f28/F28_CADmodel_vs_real.png',h=200)
p('Original publisher image comparing CAD and physical fuselage. Downloaded STEP surface models have 978, 1142 and 1306 valid faces for 4-, 5- and 6-frame sections. Each has its original no-friction/no-damage Abaqus input deck.')
f=fitz.open(DATA/'fokker-f28/FIG_mean_accelerations_N_frames.pdf');path=TMP/'f28-result.png';f[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(path);img(path,h=230)
p('Original published mean acceleration plot: positions 1-12, vertical acceleration in g, with FEM curves and NASA experimental comparisons. Other original PDFs contain mesh-sensitivity acceleration and dynamic-response-index plots.')
p('No raw CSV, ODB, full-field or time-history references verified in this subset. Plot digitization must distinguish FEM curves from experiments and carry uncertainty before numerical scoring.')
p('Source: Desiderio et al., TU Delft. DOI 10.5281/zenodo.7724227. CC BY 4.0.<br/><link href="https://zenodo.org/records/7724227">zenodo.org/records/7724227</link>')
pdf=OUT/'pdf/web-cad-fem-variety-4.pdf';pdf.parent.mkdir(exist_ok=True)
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#526374'));c.drawString(45,23,'Original web assets | Inspection views and copied references | No solver runs');c.drawRightString(A4[0]-45,23,str(d.page))
SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
d=fitz.open(pdf);print('PDF',len(d),'pages')
from PIL import Image as PI,ImageOps,ImageDraw
thumbs=[]
for i,page in enumerate(d):
 path=TMP/f'page-{i+1}.png';page.get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(path);im=PI.open(path).convert('RGB');im.thumbnail((350,495));thumbs.append(im)
preview=PI.new('RGB',(350*len(thumbs),515),'#d7e1e8')
for i,im in enumerate(thumbs):preview.paste(im,(i*350,10))
preview.save(OUT/'web-cad-fem-variety-preview.png')
archive=OUT/'datasets/web-cad-fem-variety-4.zip';archive.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for f in sorted(DATA.rglob('*')):
  if f.is_file():z.write(f,'web-cad-fem-variety/'+str(f.relative_to(DATA)))
 z.write(pdf,'web-cad-fem-variety/illustrated-review.pdf')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()))
print('ZIP',archive.stat().st_size,'bytes, CRC passed')
