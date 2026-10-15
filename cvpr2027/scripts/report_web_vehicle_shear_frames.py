"""Evidence report of original CAD/CAE, drawings and existing FEM references."""
from pathlib import Path
import json,hashlib,zipfile
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');roots=[D/x for x in ['web-cad-fem-fsae-chassis','web-cad-fem-gokart-chassis','web-cad-fem-shear-frame','web-cad-fem-workshop-archives']];F,G,S,H=roots;fc,gc,sc,hc=[json.loads((p/'catalog.json').read_text()) for p in roots];T=Path('cvpr2027/tmp/cad-fem-industrial-search');O=Path('cvpr2027/output/pdf/web-cad-fem-vehicle-shear-frames.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-vehicle-shear-frames.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.3;sty['BodyText'].leading=12.2;sty['Heading1'].fontSize=18;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width,maxheight=280):
 im=PILImage.open(path);height=width*im.height/im.width
 if height>maxheight:width*=maxheight/height;height=maxheight
 story.extend([Image(str(path),width=width,height=height),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(v),sty['BodyText']) for v in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def source(d):p(f'Source: <link href="{d["source"]}" color="blue">original publisher dataset/repository</link>. Exact source URLs and hashes retained.')
def nxt():story.append(PageBreak())
h('Formula SAE chassis: original CAD and FEM')
p('12 October 2026. Three published projects added: Formula SAE chassis, go-kart chassis and assembled shear-frame damage study. Vehicle chassis provide two distinct designs within one broad family; laboratory shear frame adds a second family. No generated geometry or new solves.')
img(F/'SYS-original-thumbnail.png',155,155)
p('<b>Original native CAD thumbnail:</b> chassis and suspension representation from SpaceClaim. Two .scdoc documents contain nonempty serialized ACIS geometry. Their main geometry member is 2,447,605 bytes. No independent native solid-BREP validation or neutral STEP export is claimed.')
img(F/'Media/Tortion Test.png',465,245)
p('<b>Original publisher setup figure:</b> beam chassis torsion load case, remote loads, supports and point masses. The downloadable Workbench archive contains four original RST results, complete source decks, Mechanical models, materials and logs.')
p('The source represents tubular members with BEAM188, suspension joints/springs and driver/rear point masses. Four load cases remain one geometry task. The repository static frontal-impact approximation is not a transient crash simulation.')
p('Full-vehicle render is retained as context. The native analysis CAD is the chassis/suspension representation, rather than a verified complete car assembly. No original full dimensioned manufacturing drawing found.')
source(fc)
nxt();h('FSAE fields: preserve binaries, hold extraction')
img(F/'Media/Mesh.png',420,210)
p('<b>Original mesh view:</b> source beam/joint/spring analysis. Saved RSTs are present for torsion, cornering, aero plus cornering and static frontal loading. Each has one static set labeled 1.')
rows=[['System / source case','Mesh nodes / elements','Published max U mm','Legacy max U mm (excluded)']]
for r in fc['records']:rows.append([r['id']+' / '+r['source_load_case'],f"{r['mesh_nodes']:,} / {r['mesh_elements']:,}",r['published_rounded_max_translation_mm'],f"{r['reader_max_translation_mm_excluded']:.3f}"])
table(rows,[135,130,105,115])
p('<b>Extraction hold:</b> ansys-mapdl-reader 0.56.0 returns finite values with unique IDs, but translation maxima differ greatly from source values. Displacement rows number 14,459 or 14,463, versus 21,656 or 21,660 mesh nodes. The cause may involve decoding, field/node scope or source setup mapping. It is unresolved.')
p('All exploratory legacy NPZ arrays are explicitly UNVERIFIED and excluded from scoring. Original RST remains available for a compatible independent decoder. No large values were deleted, missing stresses filled or fields rescaled to force agreement.')
p('BEAM188 direct/combined stress requires its own result convention; a generic averaged six-component stress field is not automatically equivalent. Source decks declare N-mm-tonne-s /units,MPA, E = 200,000 MPa and Poisson ratio 0.3.')
p('Source logs include shape-checking and linearized MPC184 warnings. They report run completion, which does not establish mesh convergence or nonlinear impact accuracy. Zero certified admissions.')
source(fc)
nxt();h('Go-kart chassis: native CAD and modal references')
img(G/'original-report-evidence/original-p5-image0.png',470,220)
p('<b>Original source FEM contour:</b> 17.332 Hz deformation shape. Actual SolidWorks chassis part file is downloaded. Table 2 labels this mode 5 while the ANSYS image title says Total Deformation 6. Frequency/shape pairing needs review; modal displacement amplitude is normalization-dependent.')
img(G/'original-report-evidence/original-p7-image0.png',445,235)
p('<b>Original harmonic FEM contour:</b> maximum deformation 7.9579e-4 m at 40 Hz, equivalent to 0.79579 mm. Source report also lists peak equivalent stress 3.7248e7 Pa (37.248 MPa) at 50 Hz.')
table([['Report evidence','Source scale / limit'],['Modal table','20 frequencies, 0 to 77.771 Hz; physical page 5 Table 2'],['Material and model','Reported AISI 4130; 184,374 nodes, 93,476 SOLID187 elements'],['Saved result coverage','No RST or full Mechanical setup located; figures/tables only']],[215,270])
p('Native CAD remains opaque to this inspection and exact CAD/solver revision matching is unverified. The source fatigue claim of 10^-32 seconds is excluded from physical life ground truth. No model scores or fatigue certification are assigned.')
source(gc)
nxt();h('Shear-frame study: original dimensioned figures')
img(S/'Figures Used/Beam_col_geo.png',475,285)
p('<b>Original publisher engineering figures:</b> beam and column top/side views with 300/350 mm spans, 6 mm sections, 4 mm holes and 200 mm column height. These are downloaded source dimensions, not newly generated drawings.')
img(S/'Figures Used/Top_bottom_view.png',475,195)
p('<b>Original assembly dimension figure:</b> plan arrangement and node/joint reference, including 350 and 412 mm dimensions. Other source component drawings and assembly/mesh/sensor views are retained.')
p('The dataset contains native Abaqus CAE databases for Undamaged and Damage types 1, 2 and 3. Associated journal text records source jobs and assembly/part changes. Files were never executed. CAE geometry has not been independently imported or converted into neutral CAD.')
p('The dimensioned figures support a future drawing reconstruction track. Complete manufacturing views, tolerance/bolt details, damage definitions and exact CAE/drawing correspondence still need verification. Three inspected figure files do not mean three independent benchmark tasks.')
source(sc)
nxt();h('Shear-frame modal FEM: 24 source references')
img(S/'Figures Used/meshed frame.png',350,235)
p('<b>Original source FEM mesh view:</b> assembled laboratory frame. The companion workbook explicitly separates MATLAB, Abaqus and experimental frequency columns. Four native CAE models correspond by source folder names; exact revision matching remains pending.')
rows=[['Source model','First six Abaqus frequencies, Hz','Exact source cells']]
for r in sc['modal_records']:rows.append([r['case'],', '.join(f'{x:g}' for x in r['six_modal_reference_Hz']),', '.join(r['exact_cells'])])
table(rows,[100,265,120])
p('<b>Provenance:</b> Frequencies comparison/comparision.xlsx, Sheet1, cells F3:I8. Units are supported by original Tables Used.docx Tables 3-6, which identify natural frequencies in Hz. Only the 24 Abaqus entries are counted as FEM numerical targets.')
p('Experimental frequencies in columns K:N are measurements and are kept separate. MATLAB values in A:D are another model source. Neither set is silently substituted for Abaqus ground truth. Modal normalization and mode pairing require explicit validation.')
p('Four native model/reference candidates remain one assembled-frame family. No ODB or full saved nodal-field export was located in these source model folders. CAE files and published scalar tables are preserved; zero certified admissions.')
source(sc)
nxt();h('Shear-frame acceleration: preserve source scales')
img(S/'Dynamic Analysis/Acceleration_comparision.png',455,250)
p('<b>Original source comparison plot:</b> experimental and Abaqus acceleration. It is kept as a published result, not locally regenerated. The inspected MATLAB script selects a segment from the workbook and labels the plotted acceleration in g.')
table([['Original workbook column','Interpretation'],['A: Time(sec)','751 finite samples, workbook rows 2:752; monotone time'],['B: Abaqus(ACC)','FEM acceleration in an unspecified raw physical scale'],['C: Experiment(acc in g)','Experimental measurements; not FEM reference values'],['D: Abaqus(Acc in g)','Equals B / 1000 numerically; physical conversion unverified']],[220,265])
p('Read-only original-table-arrays.npz retains all four source columns plus the four-by-six Abaqus frequency table. Values were compared with the workbook cells. No synthetic signals or fresh FEM solutions were created.')
p('<b>Unit hold:</b> the g label cannot establish correct acceleration conversion when raw column B units are unspecified. Sensor, force-location and damage-model mapping for this trajectory also require review. No waveform accuracy score is assigned before resolving them.')
p('The source README refers to three model folders, while version 3 has Undamaged plus three Damage folders. Type 3 journal begins by upgrading a type 1 path. Preserve the actual files and this revision ambiguity instead of assuming four fully validated cases.')
source(sc)
nxt();h('Collection inventory and held source leads')
table([['New source project','CAD/result evidence','Status'],['Formula SAE chassis','Native SpaceClaim + four RSTs, inputs and logs','Four source solution candidates; legacy extraction held'],['Go-kart chassis','Native SolidWorks + modal/harmonic report figures','One plot/table reference candidate'],['Assembled shear frame','Four native CAE databases + dimensioned figures + 24 modal entries','Four native-model/table candidates; mapping review'],['Seven workshop archives','Valve, gear/rack, bolted plates, guitar, heat sink, stand, cap CAD','Held: saved RST/RTH omitted']],[125,220,140])
p('<b>Counting:</b> three source projects with reference evidence within two broad engineering families: vehicle chassis and assembled shear-frame damage modeling. FSAE and go-kart are distinct designs; load cases, modes, frames and spreadsheet rows are not extra geometry families.')
p('<b>Drawings:</b> three original shear-frame dimensioned engineering figure files visually verified. This is useful drawing evidence, not a complete certified manufacturing package. Vehicle CAD/FE views do not become dimensioned drawings.')
p('<b>Benchmark admission:</b> zero newly certified cases. Confirm native geometry, exact CAD/result revisions, load and sensor mapping, material scope, unit conventions, field recovery, modal normalization and convergence. Frontier-model scores are not measured.')
p('<b>Held workshop leads:</b> seven downloaded archives have original CAD/setup but no saved RST/RTH. They are registered separately and excluded from paired-candidate counts. Their textbook/Ansys-training attribution is retained.')
p('<b>Source licenses:</b> shear frame CC BY 4.0; go-kart and workshop repositories MIT notices; FSAE source data license unresolved. Local research collection only, no public release. Original files and SHA-256 provenance are included.')
p('No CAD generation, source-script execution, new solve, COMSOL dependency or model call was introduced. Supplied-CAD FEM and drawing-to-CAD FEM remain separate tracks.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | source evidence, drawings and read-only audits');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'vehicle-shear-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True)
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if f.is_file():z.write(f,root.name+'/'+str(f.relative_to(root)))
 z.write(O,O.name)
 for name in ['collect_web_vehicle_frames.py','collect_web_shear_frame.py','audit_web_vehicle_shear_frames.py','report_web_vehicle_shear_frames.py']:z.write(Path('cvpr2027/scripts')/name,'inspection-scripts/'+name)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));count=len(z.namelist())
v={'zip':str(Z),'bytes':Z.stat().st_size,'members':count,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest(),'crc_verified':True,'pdf_pages':len(doc)};(T/'package-validation.json').write_text(json.dumps(v,indent=2));print(v,flush=True)
