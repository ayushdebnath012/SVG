"""Report and package original source assets plus read-only field/CAD audits."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

import pymupdf
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

D = Path('cvpr2027/data')
F, G, C = [D / s for s in ['web-cad-fem-soft-finger','web-cad-fem-landing-gear','web-cad-fem-connecting-rod']]
T = Path('cvpr2027/tmp/cad-fem-kirigami-search')
O = Path('cvpr2027/output/pdf/web-cad-fem-gear-finger-rod.pdf')
Z = Path('cvpr2027/output/datasets/web-cad-fem-gear-finger-rod.zip')
fc = json.loads((F / 'catalog.json').read_text())
gc = json.loads((G / 'catalog.json').read_text())
cc = json.loads((C / 'catalog.json').read_text())
styles = getSampleStyleSheet()
styles['BodyText'].fontSize = 9.4
styles['BodyText'].leading = 13
story = []


def readable(text):
    # Normalize spacing in authored prose only. Original assets and labels stay unchanged.
    for old, new in [
        ('page1', 'page 1'), ('page2', 'page 2'), ('page4', 'page 4'), ('page5', 'page 5'),
        ('Figure1', 'Figure 1'), ('Figure11', 'Figure 11'), ('TableII', 'Table II'),
        ('minimum0.66716', 'minimum 0.66716'), ('to0.667', 'to 0.667'),
        ('E=200,000', 'E = 200,000'), ('E=200 GPa', 'E = 200 GPa'),
        ('ratio0.3', 'ratio 0.3'), ('is0.18', 'is 0.18'),
        ('ansys-mapdl-reader0.56.0', 'ansys-mapdl-reader 0.56.0'),
        ('at54,215', 'at 54,215'), ('and60,624', 'and 60,624'),
        ('labeled1.', 'labeled 1.'), ('solid,63', 'solid, 63'),
        ('x889.00', 'x 889.00'), ('x2286.00', 'x 2286.00'),
        ('is4.98m', 'is 4.98 m'), ('a200cm', 'a 200 cm'),
        ('legend1.4017e8', 'legend 1.4017e8'), ('equals0.1', 'equals 0.1'),
        ('giving14.017', 'giving 14.017'), ('to14.02', 'to 14.02'),
        ('gives0.3197mm', 'gives 0.3197 mm'), ('has15', 'has 15'),
        ('returned404', 'returned 404'),
    ]:
        text = text.replace(old, new)
    return text


def p(text):
    story.extend([Paragraph(readable(text), styles['BodyText']), Spacer(1, 7)])


def h(text):
    story.extend([Paragraph(text, styles['Heading1']), Spacer(1, 8)])


def img(path, width=500):
    im = PILImage.open(path)
    story.extend([Image(str(path), width=width, height=width*im.height/im.width), Spacer(1, 8)])


def table(rows, widths):
    t = Table([[Paragraph(readable(str(v)),styles['BodyText']) for v in row] for row in rows], colWidths=widths)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5), ('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey),
    ]))
    story.extend([t, Spacer(1,9)])


h('Complex assembly: twin-wheel nose landing gear')
p('12 October 2026. Three original source families collected: landing gear, chambered finger and connecting rod. Original CAD and published FEM evidence retained. No locally generated geometry, solver runs or frontier-model calls.')
img(T / 'gear-source-p1-image0.png')
p('<b>Original publisher CAD illustration:</b> assembled nose gear, source report physical page1, Figure1. Downloaded STEP, native SolidWorks assembly and seven source part files provide actual CAD assets.')
img(G / 'Assembly Drawing/Assembly.JPG', 430)
p('<b>Original drawing:</b> publisher orthographic/isometric assembly sheet. Original DXF and SLDDRW retained. The inspected DXF has zero DIMENSION entities and the raster has no visible dimension callouts, so a complete dimensioned engineering drawing is not claimed.')
p('<b>Independent STEP audit:</b> valid shape, 15 solids, 500 faces; approximately 513.33 x 346.95 x 842.21 mm. Component instances, including wheel bodies and fasteners, are not counted as separate FEM tasks.')
p('Source: <link href="https://github.com/aryan-pandharipande/aircraft-nose-landing-gear-design" color="blue">Aryan Pandharipande, aircraft nose landing gear design</link>. MIT source license, original files and pinned revision/download hashes retained.')

story.append(PageBreak())
h('Landing gear: original FEM scalar references')
img(T / 'gear-source-p4-image4.png')
p('<b>Original FEM figure:</b> static safety-factor contour, source report physical page4, Figure11. Image minimum0.66716; report text rounds it to0.667. Source identifies the upper torque-link fillet as the critical location.')
table([
    ['Reference quantity', 'Original value / provenance'],
    ['Minimum static safety factor', '0.66716, original Figure11 legend'],
    ['Average static safety factor', '13.63, physical page5 TableII'],
    ['Maximum plotted safety factor', '15, explicitly capped. Not an exact uncensored strength target.'],
], [200,305])
table([
    ['Simultaneous source loads', 'Magnitude and scope'],
    ['Axle vertical force', '7062 N, +Z, two axle edges'],
    ['Lateral force', '2119 N, -Y, two axle edges'],
    ['Piston axial force', '15696 N, +Z, one piston face'],
], [200,305])
p('<b>Saved-output coverage:</b> only a standalone .wbpj project pointer is published. Dependent Mechanical files, mesh and raw .rst are absent. The numerical references are the report table and original contour, not a saved-field archive.')
p('<b>Admission limits:</b> source uses baseline structural-steel assignments and a Nickel wheel hub. Contacts, actual material scope, mesh convergence and dynamic landing behavior require review. The reference model has safety factor below unity under its source assumptions. Repository mentions of fatigue and buckling do not establish verified result cases.')
p('One native CAD/report-reference candidate. CAD creation from the supplied drawing and FEM from supplied CAD remain separate benchmark tracks, both pending complete reference setup.')

story.append(PageBreak())
h('Chambered finger: native CAD + saved solutions')
img(T / 'finger-source-p2-image0.jpeg')
p('<b>Original publisher CAD screenshot:</b> single-row chambered finger, source report physical page2. Each downloaded source project includes a native DesignModeler SYS.agdb with serialized Parasolid/object data, input ds.dat, Mechanical database and file.rst. Native BREP validity has not been independently imported; no original neutral STEP found.')
img(T / 'finger-saved-displacement.png')
p('<b>Read-only reference plot:</b> saved Part2_1 displacement magnitude at original undeformed mesh coordinates. Every fourth point displayed for legibility; full node arrays retained. These are the stored source solution values, read without launching ANSYS.')
rows = [['Saved project', 'Nodes / elements', 'Maximum translation mm']]
for r in fc['records']:
    s=r['states'][0]
    rows.append([r['id'],f"{s['nodes']:,} / {r['mesh_elements']:,}",f"{s['maximum_translation_mm']:.10g}"])
table(rows,[130,200,175])
p('<b>Material scope:</b> report describes a PDMS finger, but all three saved input decks use E=200,000 MPa, Poisson ratio0.3 and steel-like density. Pressure is0.18 MPa. The saved runs are linear static baselines, not verified PDMS or hyperelastic reference simulations. Preserve this conflict.')
p('Source: <link href="https://github.com/electronjia/Ansys-Finite_Element_Analysis-PDMS_Finger" color="blue">electronjia, ANSYS finger project</link>. One geometry family, three saved solutions. Source-data license unresolved; files retained locally for research. No public redistribution performed.')

story.append(PageBreak())
h('Saved field interpretation and scoring limits')
rows=[['Saved project','Finite stress rows / total nodes','Finite-subset peak VM MPa']]
for r in fc['records']:
    s=r['states'][0]
    rows.append([r['id'],f"{s['finite_stress_rows']:,} / {s['nodes']:,}",f"{s['finite_subset_maximum_von_mises_MPa']:.9f}"])
table(rows,[130,210,165])
p('<b>Displacement:</b> all recorded translations are finite and node IDs are unique. Each NPZ retains the reader-returned displacement arrays, original mesh coordinates and node IDs. Every NPZ was compared back to the reader arrays, with NaNs preserved.')
p('<b>Stress recovery:</b> ansys-mapdl-reader0.56.0 nodal_stress averages stored element-nodal stresses at common corner nodes. It is a recovered averaged field, rather than an unaveraged integration-point field. Component order is X,Y,Z,XY,YZ,XZ. The table maximum is computed from the six finite recovered components.')
p('The reader returns missing stress entries at54,215 nodes for Part1 and60,624 nodes for each Part2 model. Missing output is consistent with the corner-node convention; exact element/output support still requires review. Never replace these NaNs with zero or score them as zero stress.')
p('<b>Units and solution state:</b> binary header says User Defined, while the source input explicitly declares /units,MPA and consistent N-mm units. Three solutions have one static set each, labeled1. This label does not establish a transient time series. Source logs report completion, two warnings and zero errors; this alone does not establish correct physical modeling.')
table([
    ['Potential metric', 'Required interpretation'],
    ['Displacement error', 'Match the declared source material, pressure, support constraints, node mapping and units. Do not compare with a different PDMS model.'],
    ['Recovered stress error', 'Use matching corner-node averaging and a finite reference mask. Report coverage. Do not compare directly against unaveraged element/integration-point stress.'],
    ['Model accuracy scores', 'Not measured. No frontier-model trial or new FEM solve performed.'],
], [200,305])
p('Reader methodology: <link href="https://reader.docs.pyansys.com/version/stable/api/rst.html#ansys.mapdl.reader.rst.Result.nodal_stress" color="blue">official PyMAPDL Legacy Reader documentation</link>. Same averaging convention applies to the earlier marine-anchor reader extraction; the collection index records this shared scoring note.')
p('These are three native CAD/saved-solution candidates with explicit source-physics limits. Zero newly certified benchmark admissions.')

story.append(PageBreak())
h('Connecting rod: CAD sketches and source units')
img(C / 'Connecting Rod Sketch 1.png')
p('<b>Original publisher CAD sketch:</b> dimension labels from the native SolidWorks modeling workflow. Second sketch, final CAD view, STEP and SLDPRT retained. This is a dimensioned modeling sketch, not a verified manufacturing drawing with complete views, units, thickness and tolerances.')
table([
    ['Original CAD audit', 'Result and correspondence limits'],
    ['STEP shape', 'One valid solid,63 faces. STEP explicitly declares conversion-based INCH.'],
    ['Imported dimensions', '4980.94 x889.00 x2286.00 mm. The maximum extent is4.98m. Source geometry dimension intent requires review.'],
    ['Source FEM display', 'Screenshot uses cm and CGS stress units, with a200cm scale bar. No silent rescaling or new geometry applied.'],
], [195,310])
p('<b>Source static setup:</b> report specifies steel E=200 GPa, Poisson ratio0.3, fixed big end and force components(-5000,0,-750)N at the small end. Only a standalone Workbench project pointer is available; no raw .rst or solver mesh/deck found.')
p('Source: <link href="https://github.com/pranavmane7/Connecting-Rod-Design-and-Analysis-Using-SOLIDWORKS-And-ANSYS" color="blue">Pranav Mane, connecting rod design and analysis</link>. Original README says educational/portfolio purposes; no standard license located. Local research inspection only, no public publication.')

story.append(PageBreak())
h('Connecting rod: FEM references with unit provenance')
img(C / 'Equivalent Stress.png')
p('<b>Original FEM screenshot:</b> equivalent stress legend1.4017e8 dyne/cm^2. Preserve the unusual units. One dyne/cm^2 equals0.1 Pa, giving14.017 MPa. Report text rounds the same quantity to14.02 MPa.')
table([
    ['Reference quantity', 'Original label', 'Explicit unit conversion'],
    ['Maximum equivalent stress', '1.4017e8 dyne/cm^2', '14.017 MPa'],
    ['Maximum total deformation', '0.031969 cm', '0.31969 mm'],
    ['Displayed safety factor', '15 minimum and maximum', 'Capped display; excluded as an exact uncensored target'],
], [190,155,160])
p('The report gives0.3197mm deformation, consistent with rounding the screenshot value. Reference labels are taken from original plots; they do not provide nodal field errors. CAD scale, material scope, applied loads and convergence remain scoring checks.')
p('<b>Batch counts:</b> three engineering families; three native finger CAD/saved-solution candidates, two STEP/plot-report candidates. Landing gear has15 imported solids and rod has one; solids and load variants are not additional engineering families. No newly verified complete dimensioned engineering drawings or certified benchmark cases.')
p('<b>Files:</b> original CAD, source drawings/sketches, reports, Workbench data, three raw RST files, three exact reader-output NPZs, source hashes, catalogs and inspection code. License scope is recorded per source. No COMSOL dependency. Reading saved RST files required no ANSYS solve; full replay still needs compatible tooling or validated translation.')
p('<b>Further leads:</b> chiral kirigami CAD/nonlinear FEM archive identified, but download API requires a bearer token. The sliding-mechanism paper supplies data on request. CADEngBench has no verified downloadable reference repository in this search; the cited OpenAM Figshare collection API returned404. None is included in collected pair counts.')


def footer(canvas, doc):
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(45,25,'Published original assets and read-only diagnostics; benchmark admission pending')
    canvas.drawRightString(550,25,str(doc.page))


O.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(str(O), pagesize=(595,842), leftMargin=45, rightMargin=45,
                  topMargin=30,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
assert len(doc)==6,len(doc)
for i,page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'gear-finger-rod-report-{i+1}.png')

for root, names in [(F,['finger-source-p2-image0.jpeg','finger-saved-displacement.png']),
                    (G,['gear-source-p1-image0.png','gear-source-p4-image4.png'])]:
    (root/'inspection-figures').mkdir(exist_ok=True)
    for name in names:shutil.copyfile(T/name,root/'inspection-figures'/name)
for root in [F,G,C]:
    shutil.copyfile('cvpr2027/scripts/report_web_gear_finger_rod.py',root/'inspection-scripts/report_web_gear_finger_rod.py')
shutil.copyfile(T/'screened-leads.json',F/'screened-leads.json')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


files=[(p,str(Path(root.name)/p.relative_to(root))) for root in [F,G,C] for p in sorted(root.rglob('*')) if p.is_file()]
manifest=[dict(path=name,bytes=p.stat().st_size,sha256=sha(p)) for p,name in files]
mp=T/'gear-finger-rod-package-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
    for path,name in files:z.write(path,name)
    z.write(mp,'package-manifest.json')
with zipfile.ZipFile(Z) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
    for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256'],row['path']
validation=dict(pdf_pages=len(doc),zip_files=len(files)+1,zip_bytes=Z.stat().st_size,
                zip_sha256=sha(Z),crc_verified=True,all_manifest_hashes_verified=True)
(T/'gear-finger-rod-package-validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps(validation,indent=2))
