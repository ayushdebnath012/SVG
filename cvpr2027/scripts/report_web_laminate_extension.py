from pathlib import Path
import json,zipfile,hashlib
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
import pymupdf
D=Path('cvpr2027/data/web-cad-fem-manufacturing');T=Path('cvpr2027/tmp/cad-fem-manufacturing-search');O=Path('cvpr2027/output/pdf/web-cad-fem-laminate-extension.pdf');cat=json.loads((D/'catalog.json').read_text());styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.5;styles['BodyText'].leading=13;story=[]
def p(s):story.append(Paragraph(s,styles['BodyText']));story.append(Spacer(1,6))
def h(s):story.append(Paragraph(s,styles['Heading1']));story.append(Spacer(1,6))
h('Published composite laminate CAD + FEM')
p('12 October 2026 | Two original native FreeCAD files collected | No local CAD generation, FEM solves or model trials')
p('One new composite physics candidate and one basic solver comparison. Both contain valid native CAD/BREP and saved numerical results. These are not yet admitted benchmark cases. The CAD is a simple rectangular plate, not a complex engineering drawing.')
story.append(Image(str(T/'Scratch-shell-CA-Comp-cad.png'),width=430,height=172));p('<b>CAD inspection render:</b> tessellation of the original Body.Shape.brp, 100 x 50 x 10 mm. The FEM uses an extracted shell surface; its laminate thickness is 2 mm, so the body thickness must not be used as the analysis thickness.')
p('<b>Unbalanced asymmetric laminate:</b> two plies, 0 and 45 degrees, 1 mm each. Source description reports twist under bending. Saved Code_Aster solution contains 77 finite displacement vectors; maximum magnitude 3.9885449105 in original source units.')
story.append(Image(str(T/'Scratch-shell-CA-Comp-CodeAsterResults.png'),width=430,height=172));p('<b>Original saved reference values:</b> colored at original result-mesh coordinates. This is a field visualization, not a newly solved result or an original dimensioned drawing.')
p('Source solver, mesh and result objects are marked Touched. Model/result consistency and solver units need verification before scoring. Original attachment data license is unspecified; native document metadata contains All rights reserved.')
p('Primary source: <link href="https://github.com/FreeCAD/FreeCAD/pull/28380" color="blue">TimSwait-AMRC, FreeCAD Code_Aster integration, PR 28380</link>.')
story.append(PageBreak());h('Isotropic Code_Aster / CalculiX comparison')
p('Original Scratch-shell-CA.FCStd includes CAD, loads, fixed constraints, material properties, shell geometry, meshes and two saved solver result objects. This basic case provides a cross-solver check; it is not an additional complex geometry family.')
story.append(Image(str(T/'Scratch-shell-CA-cad.png'),width=430,height=172));p('Inspection render of the original native CAD. Analysis shell thickness and material setup are retained in the FCStd; no solver was executed.')
story.append(Image(str(T/'Scratch-shell-CA-CCX_Results.png'),width=430,height=172));p('Published CalculiX displacement magnitude at original mesh coordinates. All 631 saved vectors are finite. The Code_Aster result contains 8 finite vectors.')
p('<b>Saved maximum displacement magnitudes:</b> Code_Aster 0.3235794422; CalculiX 0.3278049225. Relative difference: 1.2890%, using the CalculiX maximum as denominator. This compares two source solver outputs; it is not a frontier-model benchmark score or convergence proof.')
p('UNV unit metadata says SI meter while mesh coordinate dimensions match the millimetre CAD values. Retain source values without conversion until the writer conventions are checked. Extracted CSV rows use source array indices, not independently verified node IDs. Native FCStd retains the original mesh node numbers.')
p('Primary source: <link href="https://github.com/FreeCAD/FreeCAD/pull/28380" color="blue">FreeCAD PR 28380, original Scratch-shell-CA.zip attachment</link>.')
story.append(PageBreak());h('Original manufacturing drawing - held lead')
p('Leibniz University Hannover, Niedermeyer et al.; DOI 10.25835/z4qoeq0d; CC BY-NC 4.0. Five original STEP models, an engineering drawing, workbook and analysis-image archive downloaded.')
story.append(Image(str(T/'original-drawing.png'),width=500,height=353));p('<b>Original publisher drawing:</b> Balken fertig bearbeitet, 20 March 2026. Dimensions, tolerances, surface specifications and title block are present. This image renders the downloaded drawing PDF unchanged.')
p('The workbook and comparison images contain coordinate-measurement, CT and scan deviations. No saved numerical FEM output was verified. These measurements must not be used as FEM reference fields; this source is excluded from the two CAD/FEM candidate count.')
p('Primary source: <link href="https://data.uni-hannover.de/de/dataset/shape-errors-and-surface-roughnesses-of-specimens-with-support-and-stiffening-structures" color="blue">Shape errors and surface roughnesses of specimens with support and stiffening structures</link>.')
p('<b>Benchmark status:</b> supplied-CAD-to-FEM has two new candidates awaiting reference consistency and unit checks. Drawing-to-CAD-to-FEM has no newly qualified complete case. Three saved solver outputs belong to two cases; plies, nodes and analysis images are not separate tasks. No model accuracy has been measured.')
def footer(c,d):c.setFont('Helvetica',8);c.drawString(45,25,'Original web sources; candidates remain separate from benchmark admissions');c.drawRightString(550,25,str(d.page))
SimpleDocTemplate(str(O),pagesize=(595,842),leftMargin=45,rightMargin=45,topMargin=30,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
d=pymupdf.open(O);assert len(d)==3
for i,page in enumerate(d):page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(T/f'laminate-report-{i+1}.png')
# Original downloads retained for the user's local research collection; data license limitations in catalog.
files=[D/'catalog.json',D/'README.md']
files.extend(p for p in (D/'hannover-milling').iterdir() if p.is_file())
files.extend(p for p in (D/'codeaster-laminate').iterdir() if p.suffix in ['.zip','.FCStd','.csv'])
manifest=[dict(path=str(p.relative_to(D)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)]
(D/'package-manifest.json').write_text(json.dumps(manifest,indent=2));files.append(D/'package-manifest.json')
out=Path('cvpr2027/output/datasets/web-cad-fem-laminate-extension.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,str(p.relative_to(D)))
with zipfile.ZipFile(out) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()))
print('PDF',len(d),'pages; ZIP',len(files),'files',out.stat().st_size,'bytes')
