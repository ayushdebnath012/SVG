"""Report source-published drawings and FEM figures, package originals with audits."""
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

R = Path('cvpr2027/data/web-cad-fem-rigging-plate')
D = Path('cvpr2027/data/web-cad-fem-turbine-design')
T = Path('cvpr2027/tmp/cad-fem-new-complex-search')
O = Path('cvpr2027/output/pdf/web-cad-fem-rigging-turbine.pdf')
Z = Path('cvpr2027/output/datasets/web-cad-fem-rigging-turbine.zip')
cat = json.loads((R / 'catalog.json').read_text())
styles = getSampleStyleSheet()
styles['BodyText'].fontSize = 9.5
styles['BodyText'].leading = 13
story = []


def p(text):
    story.extend([Paragraph(text, styles['BodyText']), Spacer(1, 8)])


def h(text):
    story.extend([Paragraph(text, styles['Heading1']), Spacer(1, 8)])


def img(path, width=500):
    im = PILImage.open(path)
    story.extend([Image(str(path), width=width, height=width * im.height / im.width), Spacer(1, 8)])


def table(rows, widths):
    tab = Table([[Paragraph(str(x), styles['BodyText']) for x in row] for row in rows], colWidths=widths)
    tab.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), .3, colors.lightgrey),
    ]))
    story.extend([tab, Spacer(1, 10)])


h('Original drawing + native CAD: rigging plate')
p('12 October 2026. One new mechanical geometry family with seven published FEM loading variants. Dimensioned source drawing and native CAD included. No locally created geometry, FEM solution or frontier-model trial.')
img(T / 'rigging-drawing-1.png')
p('<b>Original engineering drawing:</b> physical page 1 of the publisher manufacturing-notes PDF, rendered for inspection. Source dimensions, material and tolerance are preserved. Pages 2-3 contain source manufacturing illustrations and remain in the original PDF.')
table([
    ['CAD audit', 'Read-only result'],
    ['Original STEP / SolidWorks', 'riggingplate-14mar2024.step and .sldprt retained. STEP imports as one valid solid with 145 faces.'],
    ['STEP units and bounding dimensions', 'Millimetres, approximately 235.579 x 111.904 x 12.000 mm, consistent with the source drawing.'],
    ['Material and data provenance', 'Source specifies 7075-T6 aluminium. Pinned Git revision, original LICENSE and SHA256 download manifest retained.'],
], [190, 315])
p('Primary source: <link href="https://github.com/mpangch/OpenRiggingPlate" color="blue">mpangch / OpenRiggingPlate</link>, revision 7b0bdc155c648940279e337230fb99f9aee7d25f. CERN-OHL-S-2.0. CAD validity establishes geometry integrity, not simulation accuracy or a certified breaking load.')

story.append(PageBreak())
h('Seven original FEM loading directions')
img(R / 'FEA Analysis/Test 1 (2697.7 lbf)/Stress.png')
p('<b>Original FEM result:</b> Test1 equivalent von Mises stress, MPa. This unchanged publisher image is one of 28 retained boundary-condition, stress, deformation and safety-factor plots.')
rows = [['Load variant', 'Peak stress MPa', 'Peak total deformation mm', 'Minimum safety factor']]
for rec in cat['records']:
    rows.append([rec['id'].split('-')[-1], *[target['value'] for target in rec['targets']]])
table(rows, [100, 125, 160, 120])
p('<b>Numerical reference provenance:</b> 21 rounded source legend values. Stress and deformation maxima were checked visually, with OCR crosschecks. catalog.json records the original file and hash for every target. These are published FEM reference values, not frontier-model accuracy scores.')
p('<b>Reference scope:</b> no raw .rst, nodal field table or input deck found in the inspected repository. Plot references can support candidate scalar comparisons after setup review. They cannot support nodal displacement/stress error metrics.')
p('All seven variants share one native CAD geometry. Preserve the geometry group across future train/test splits. A static result label of 1 is not interpreted as a transient simulation time.')

story.append(PageBreak())
h('Source inconsistencies and benchmark admission')
img(R / 'FEA Analysis/Test 4 (2225.4 lbf)/Boundary Conditions.png')
p('<b>Original loading illustration:</b> Test4 shows a remote displacement and a 9899.5 N force. Source files preserve the application location and loading direction. Full remote support settings remain unavailable in the downloaded evidence.')
table([
    ['Source evidence', 'Consequence for benchmarking'],
    ['Test4 force label discrepancy', 'README says 2222.5 lbf; folder says 2225.4 lbf; image says 9899.5 N. Keep all originals and resolve the intended load.'],
    ['Source claims analyses passed', 'Tests1/4/7 plot minimum safety factors below one. Do not infer a certified safe design or experimental breaking strength.'],
    ['Tests1/5 total deformation', 'Minimum displacement is nonzero. Remote support rotation and rigid-motion contribution require review.'],
    ['Mesh, material, contact and solver scope', 'Native solution archive and convergence evidence not found. Peak-stress tolerances and replay have not been established.'],
], [190, 315])
p('<b>Track status:</b> drawing-to-CAD-to-FEM has an original dimensioned drawing and valid native CAD, but FEM reproduction is pending. Supplied-CAD-to-FEM has scalar plot candidates with the same limits. Report the two tracks separately when evaluating models.')
p('<b>Count:</b> one CAD/plot-reference candidate, seven loading variants, 21 reference scalars, zero new raw-field cases and zero newly certified benchmark admissions. No COMSOL used.')

story.append(PageBreak())
h('Complex turbine design source: pairing held')
img(D / 'source-figures/image5.png')
p('<b>Original publisher assembly image:</b> exploded blade shells, continuous spar and hub components. Extracted unchanged from the Aquantis pass-through spar presentation, slide 3. Original three STEP models and four source design presentations are included as a separate held collection.')
img(D / 'source-figures/image33.png', 300)
p('<b>Original FEM reference:</b> clamp-surface von Mises stress along a path, source slide 13. The presentation includes Abaqus and I-DEAS results, loads and restraint descriptions. These are source curves and figures; no raw ODB/RST file was found in the listed resources.')
p('<b>Pairing blocker:</b> the preliminary CAD filename says 45m; beam-model validation discusses 47.5m and 45.5m; the pass-through spar FEM specifies 41.5m. The source submission groups design revisions, so an exact CAD/result pair has not been verified. Spreadsheet sandwich-beam outputs are kept separate from FEM.')
p('<b>CAD audit:</b> preliminary blade imports as two valid solids with ten faces. The internals STEP imports with 290 solids and 19,777 faces, but overall shape validity fails. The 242 MB wet assembly was downloaded; independent import did not complete within a 75-second inspection limit. No geometry repaired or generated.')
p('Source: <link href="https://mhkdr.openei.org/submissions/5" color="blue">Aquantis 2.5 MW Ocean Current Generation Device Design Details</link>, DOI 10.15473/1417292. Public MHKDR metadata gives CC BY 4.0; embedded proprietary markings remain unchanged and recorded. No public upload performed. Count zero additional numerical CAD/FEM pairs from this held source.')


def footer(canvas, doc):
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(45, 25, 'Published original CAD/drawings and FEM references; admission limits recorded')
    canvas.drawRightString(550, 25, str(doc.page))


O.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(str(O), pagesize=(595, 842), leftMargin=45, rightMargin=45,
                  topMargin=30, bottomMargin=42).build(story, onFirstPage=footer, onLaterPages=footer)
doc = pymupdf.open(O)
assert len(doc) == 4, len(doc)
for i, page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(T / f'rigging-turbine-report-{i+1}.png')

# Record screened leads; no unavailable assets counted as collected pairs.
leads = dict(
    viscoelastic=dict(source='https://doi.org/10.5281/zenodo.17537703',
                     status='Paper and DataCite metadata inspected. Paper reports 5000 generated STEP designs and FEM transmissibility curves. Zenodo page/API requests timed out or returned 504; original dataset assets not downloaded, zero collected pairs.',
                     native_cad_download_verified=False),
    ansys_case_studies=dict(source='https://github.com/a-dorgham/FEA_Ansys',
                           revision='b261c7df398c80c5c35ad971c84478163b8c12ee',
                           status='Five original guitar/heatsink/gear/bolt-plate/valve Workbench archives inspected. CAD present, no .rst/.rth saved fields; excluded from pair count.'),
    nexus=dict(source='https://github.com/noahweber1/nexus-agent-benchmark',
               status='Inspected public tree: input/expected artifacts contain .gitkeep only. Task specifications are not available reference data. Excluded.'))
(R / 'screened-leads.json').write_text(json.dumps(leads, indent=2) + '\n')
for root in [R, D]:
    (root / 'inspection-scripts').mkdir(exist_ok=True)
    for name in ['audit_web_rigging_turbine.py', 'report_web_rigging_turbine.py']:
        shutil.copyfile(Path('cvpr2027/scripts') / name, root / 'inspection-scripts' / name)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


files = [(p, str(Path(root.name) / p.relative_to(root)))
         for root in [R, D] for p in sorted(root.rglob('*')) if p.is_file()]
manifest = [dict(path=name, bytes=p.stat().st_size, sha256=sha(p)) for p, name in files]
manifest_path = T / 'rigging-turbine-package-manifest.json'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
Z.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(Z, 'w', zipfile.ZIP_DEFLATED, compresslevel=4) as z:
    for path, name in files:
        z.write(path, name)
    z.write(manifest_path, 'package-manifest.json')
with zipfile.ZipFile(Z) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(set(z.namelist()))
    for row in manifest:
        assert hashlib.sha256(z.read(row['path'])).hexdigest() == row['sha256'], row['path']
validation = dict(pdf_pages=len(doc), files=len(files)+1, zip_bytes=Z.stat().st_size,
                  zip_sha256=sha(Z), crc_verified=True, manifest_hashes_verified=True)
(T / 'rigging-turbine-package-validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps(validation, indent=2))
