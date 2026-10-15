"""Package published source assets and report local read-only diagnostics."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

import pymupdf
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

D = Path('cvpr2027/data/web-cad-fem-marine-anchor')
T = Path('cvpr2027/tmp/cad-fem-buckling-search')
O = Path('cvpr2027/output/pdf/web-cad-fem-marine-anchor.pdf')
Z = Path('cvpr2027/output/datasets/web-cad-fem-marine-anchor.zip')
cat = json.loads((D / 'catalog.json').read_text())
styles = getSampleStyleSheet()
styles['BodyText'].fontSize = 9.4
styles['BodyText'].leading = 12.8
story = []


def p(s):
    story.extend([Paragraph(s, styles['BodyText']), Spacer(1, 7)])


def h(s):
    story.extend([Paragraph(s, styles['Heading1']), Spacer(1, 8)])


def img(path, width, height):
    story.extend([Image(str(path), width=width, height=height), Spacer(1, 8)])


def table(rows, widths):
    tab = Table([[Paragraph(str(v), styles['BodyText']) for v in r] for r in rows], colWidths=widths)
    tab.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -1), .3, colors.lightgrey),
    ]))
    story.extend([tab, Spacer(1, 10)])


h('Complex marine anchor: published CAD + FEM')
p('12 October 2026. One modular helical anchor engineering family, one native CAD/saved-FEM candidate and three saved static load sets. No local CAD creation, FEM solve or model trial.')
img(T / 'anchor-source-p19.jpeg', 325, 306)
p('<b>Original publisher CAD figure:</b> baseline anchor template, skirt, mooring lug and cutouts. Unchanged image extracted from the source report, physical PDF page 19, Figure 4. It is a CAD illustration, not a dimensioned manufacturing drawing.')
table([
    ['Original CAD available', 'Evidence and limits'],
    ['Associated DesignModeler SYS.agdb', 'Inside the same baseline Workbench archive as file.rst. HDF5 contains nonempty native object and serialized Parasolid data.'],
    ['SolidWorks .SLDPRT and Parasolid .x_t', 'Original design variants retained. Individual variants are not yet paired to the baseline RST or each DOE row.'],
    ['Independent geometry import', 'Not completed; no original STEP found in these selected files. Native geometry validity remains unverified.'],
], [185, 320])
p('Source: Stress Engineering Services, Carlos Lopez, Hong Zhou and Dilip Maniar, <link href="https://catalog.data.gov/dataset/teamer-modular-group-helical-pile-anchor-structural-analysis" color="blue">TEAMER Modular Group Helical Pile Anchor Structural Analysis</link>; <link href="https://mhkdr.openei.org/submissions/697" color="blue">MHKDR 697</link>. CC BY 4.0. Original report and download hashes included.')

story.append(PageBreak())
h('Saved FEM results: fields, not only pictures')
img(T / 'anchor-source-p22.jpeg', 345, 283)
p('<b>Original publisher FEM figure:</b> equivalent stress, psi, source report physical page 22, Figure 6. Its legend maximum is 41,269 psi. This is a report reference for its particular model/stage; it is not asserted to equal a maximum in the extracted baseline RST.')
p('<b>Raw saved results:</b> Initial Anchor Analysis.wbpz includes file.rst (381,681,664 bytes), ds.dat, native geometry and solve.out. Source log states that the ANSYS run completed. Read-only extraction with ansys-mapdl-reader 0.56.0 found 407,855 nodes, 150,143 elements and three result sets. No ANSYS solver was launched.')
table([
    ['Reader index / static label', 'Maximum translation*', 'Fully finite stress rows'],
    *[[f"{r['reader_result_index']} / {r['static_load_label']:.0f}", f"{r['max_translation_inch']:.9f} inch", f"{r['stress_finite_nodes']:,} / {r['mesh_nodes']:,}"] for r in cat['fem']['states']],
], [185, 155, 165])
p('*Computed from the first three displacement DOFs only. Each saved displacement array has six DOFs and no nonfinite entries. These values are reference diagnostics, not frontier-model accuracy scores.')
p('<b>Units and labels:</b> binary header says User Defined. Input-deck unit comments imply inch, slinch and second, with stress in psi. Labels 1, 2 and 3 are static load-step labels; do not treat them as transient seconds without further evidence.')
p('Each exact NPZ extraction retains node IDs, original mesh coordinates, six displacement DOFs and six nodal stress components. No values interpolated or replaced. Raw RST and input deck remain available inside the original Workbench archive.')

story.append(PageBreak())
h('Benchmark scope and missing-data policy')
img(T / 'anchor-source-p9.png', 250, 235)
p('<b>Original publisher assembly illustration:</b> source report physical PDF page 9 shows the template, skirt, mooring connection and helical piles. The physical pile geometry is idealized in the FEM; this illustration is not an exact finite-element mesh or a dimensioned drawing.')
p('<b>Stress coverage:</b> 89,139 rows have all six finite components; 318,716 rows contain missing stress values in every saved set. Preserve the NaN mask. Never substitute zero. Region, element-support and shell/beam output conventions must be resolved before stress scoring. Coverage is reported alongside any future error metric.')
table([
    ['Potential benchmark track', 'Current admission status'],
    ['Supplied CAD to FEM', 'Candidate only. Confirm native geometry/result correspondence, units, materials, applied loads, constraints, result scope and reference tolerances.'],
    ['Drawing to CAD to FEM', 'No newly verified dimensioned engineering drawing in this source. Publisher illustrations remain visual evidence only.'],
    ['DOE optimization references', '92 finite parameter/stress rows retained in original full_table.csv. Zero individually verified CAD pairs for those rows; do not count them as 92 tasks.'],
], [185, 320])
p('<b>Modeling limits:</b> physical helical piles are idealized as equivalent members in the source FEM. The optimized 2.23 GB Workbench archive has not been downloaded. Source report figures, baseline fields and DOE results concern different design/stage variants.')
p('<b>Package:</b> original baseline Workbench and small source archives, original CAD variants, three exact field NPZs, source report, figure extracts, provenance and inspection scripts. Expanded duplicate file.rst and ds.dat are omitted; their original archive member paths are recorded in catalog.json. SHA256 manifest and ZIP CRC checked.')
p('<b>Admission totals:</b> one new complex family, three load sets, zero newly certified benchmark cases. No COMSOL dependency. Saved fields can be read without an ANSYS solve; full solver replay still requires a compatible ANSYS environment or validated translation.')


def footer(c, doc):
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.grey)
    c.drawString(45, 25, 'Published source assets; read-only audit; benchmark admission pending')
    c.drawRightString(550, 25, str(doc.page))


O.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(str(O), pagesize=(595, 842), leftMargin=45, rightMargin=45,
                  topMargin=30, bottomMargin=42).build(story, onFirstPage=footer, onLaterPages=footer)
doc = pymupdf.open(O)
assert len(doc) == 3, len(doc)
for i, page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(T / f'marine-anchor-report-{i+1}.png')

(D / 'figures').mkdir(exist_ok=True)
for name in ['anchor-source-p9.png', 'anchor-source-p19.jpeg', 'anchor-source-p22.jpeg', 'anchor-stress-mask.png']:
    shutil.copyfile(T / name, D / 'figures' / name)
(D / 'inspection-scripts').mkdir(exist_ok=True)
for name in ['audit_web_marine_anchor.py', 'report_web_marine_anchor.py']:
    shutil.copyfile(Path('cvpr2027/scripts') / name, D / 'inspection-scripts' / name)
excluded = {'file.rst', 'ds.dat', 'package-manifest.json', 'package-validation.json'}
files = sorted(p for p in D.rglob('*') if p.is_file() and p.name not in excluded and not p.name.startswith('~$'))


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


manifest = [{'path': str(p.relative_to(D)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files]
(D / 'package-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
files.append(D / 'package-manifest.json')
Z.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(Z, 'w', zipfile.ZIP_DEFLATED, compresslevel=4) as z:
    for path in files:
        # Already compressed originals and exact NPZ fields do not need a second compression pass.
        compression = zipfile.ZIP_STORED if path.suffix in {'.zip', '.wbpz', '.npz'} else zipfile.ZIP_DEFLATED
        z.write(path, str(path.relative_to(D)), compress_type=compression)
with zipfile.ZipFile(Z) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(set(z.namelist()))
    for row in manifest:
        assert hashlib.sha256(z.read(row['path'])).hexdigest() == row['sha256'], row['path']
validation = {'pdf_pages': len(doc), 'zip_files': len(files), 'zip_bytes': Z.stat().st_size,
              'zip_sha256': sha(Z), 'crc_verified': True, 'manifest_hashes_verified': True}
(D / 'package-validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps(validation, indent=2))
