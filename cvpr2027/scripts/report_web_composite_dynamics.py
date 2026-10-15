"""Local evidence report: original CAD thumbnails and publisher FEM figures."""
from pathlib import Path
import json,hashlib,zipfile,shutil
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
R=Path('cvpr2027/data/web-cad-fem-composite-dynamics');B=R/'pydpf-composites';T=Path('cvpr2027/tmp/cad-fem-next-search');O=Path('cvpr2027/output/pdf/web-cad-fem-composite-dynamics.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-composite-dynamics.zip')
cat=json.loads((R/'catalog.json').read_text());rec={x['id']:x for x in cat['records']};styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.2;styles['BodyText'].leading=12.2;styles['Heading1'].fontSize=18;story=[]
def p(s):story.extend([Paragraph(s,styles['BodyText']),Spacer(1,5)])
def h(s):story.extend([Paragraph(s,styles['Heading1']),Spacer(1,5)])
def img(path,width,maxheight=350):
 im=PILImage.open(path);height=width*im.height/im.width
 if height>maxheight:width*=maxheight/height;height=maxheight
 story.extend([Image(str(path),width=width,height=height),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(x),styles['BodyText']) for x in row] for row in rows],colWidths=widths)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,5)])
def source(case):p(f'Source: <link href="{rec[case]["documentation"]}" color="blue">official Ansys {case.replace("_"," ")} example</link>. Assets pinned to Ansys example-data revision 8ef505f6; original notices retained.')
def nextpage():story.append(PageBreak())
h('Composite wing: original CAD and impact FEM')
p('12 October 2026. Five new published CAD/result projects collected. The wing provides complex assembly geometry; four other projects add physics variety with simpler geometry. Zero new certified benchmark admissions.')
img(B/'lsdyna_bird_strike/extracted-native/SYS-3-original-thumbnail.png',125,125)
p('<b>Original CAD thumbnail:</b> source SpaceClaim file shows curved wing skin, perforated ribs and impactor. Two nonempty serialized ACIS geometry members are present. Native .scdoc, Workbench .wbpz, ACP layup, material data and input.k are retained. No independent native BREP validity claim.')
img(B/'lsdyna_bird_strike/original-published-fem-1.png',470,280)
p('<b>Original published FEM figure:</b> ply stress contour from the wing-impact example. Original d3plot, d3plot01 and d3plot02 are downloaded. The exploratory reader reports 2,957 nodes, 2,304 shells, 701 SPH particles and three states; these counts are not additional tasks.')
p('<b>Decoder hold:</b> lasso-python 2.0.4 reports shell layout mismatch (260 versus 314 variables) and a plastic-strain reshape failure. All extracted LS-DYNA arrays are UNVERIFIED and excluded from scoring. Preserve original binaries for an independent compatible decoder.')
source('lsdyna_bird_strike')
nextpage();h('PCB-like board: thermal and structural fields')
img(B/'thermal_solid/extracted-native/ACP-Pre-original-thumbnail.png',115,115)
p('<b>Original CAD thumbnail:</b> board surface with mounting holes and local regions. Three native SpaceClaim documents are retained, including downstream solid-model representations. These are source submodels within one project, not three benchmark tasks.')
img(B/'thermal_solid/original-published-fem-1.png',470,280)
p('<b>Original published FEM figure:</b> temperature on a selected board ply. The downloaded file.rst contains a saved static structural state with temperatures. The legacy reader returns 5,240 mesh nodes and 4,310 elements.')
s=rec['thermal_solid']['reader_audit']['states'][0]
table([['Read-only saved result', 'Value in source numeric scale'],['Temperature range, all saved nodes',f"{s['nodal_temperature']['finite_min']:.6f} to {s['nodal_temperature']['finite_max']:.6f}"],['Maximum translation',f"{s['nodal_displacement']['maximum_translation_source_units']:.9f}"],['Finite output coverage','5,240 translations and temperatures; 31,440 recovered stress components']],[260,220])
p('All arrays and node IDs are preserved in saved-reader-state-0.npz and compared with reader output. Binary units say User Defined; physical length, stress and temperature scale require source setup verification. The global temperature minimum can differ from a selected-ply figure minimum. No new solve.')
source('thermal_solid')
nextpage();h('Curved cyclic sector: CAD and structural FEM')
img(B/'cyclic_symmetry/extracted-native/Geom-original-thumbnail.png',120,120)
p('<b>Original CAD thumbnail:</b> layered curved sector. Source Geom.stp independently imports as a valid solid with nine faces, approximately 21.92 x 17.56 x 12.00 mm. Native SpaceClaim and ACP representations are also retained.')
img(B/'cyclic_symmetry/original-published-fem-2.png',470,285)
p('<b>Original published FEM figure:</b> selected-ply stress for the original sector. The raw RST contains one saved static result set. Mesh metadata has 1,272 nodes and 1,012 elements, including cyclic duplicate representation; the default displacement result contains 636 rows for the base sector.')
s=rec['cyclic_symmetry']['reader_audit']['states'][0]
p(f'<b>Read-only scalar:</b> maximum base-sector translation {s["nodal_displacement"]["maximum_translation_source_units"]:.9f} in unconfirmed source length units. Stress has {s["nodal_stress"]["finite_entries"]:,} finite components across its returned rows; preserve missing values and node IDs.')
p('Default cyclic-reader fields represent the original sector. Expanded sectors, duplicate nodes and periodic boundaries require explicit mapping before comparison. Recovered nodal stress averages element-nodal values at common nodes. This is a simpler CAD shape with cyclic and composite modeling complexity.')
source('cyclic_symmetry')
nextpage();h('Sandwich panel: random-vibration references')
img(B/'random_vibration/extracted-native/SYS-1-original-thumbnail.png',115,115)
p('<b>Original CAD thumbnail:</b> simple panel surface, source SpaceClaim serialized ACIS geometry. Native CAD, Workbench project, composite definition HDF5, materials and original file.rst are included.')
img(B/'random_vibration/original-published-fem-1.png',470,290)
p('<b>Original published FEM figure:</b> component-based composite failure result for the stochastic vibration example. This is a statistical PSD workflow, not a deterministic displacement trajectory.')
p('<b>Extraction hold:</b> the legacy reader identified 289 nodes, 512 elements and two zero-labeled sets. One pass returned nonfinite and implausibly large displacements; other inspection passes crashed. All exploratory NPZ arrays are marked UNVERIFIED. Original RST and the observed logs are retained; no numeric score is assigned.')
p('<b>Metric convention:</b> directional PSD/RMS quantities require componentwise statistical comparison. The publisher cautions against ordinary vector/tensor combination and stress-tensor rotation for these results. Positive and negative material-strength directions must be handled explicitly. Different sigma levels do not create independent CAD cases.')
p('Workbench filename mentions 26R1 while internal project names retain 25R1. Confirm source/result revision compatibility rather than assuming the labels match. The native CAD pair remains a candidate pending exact setup verification.')
source('random_vibration')
nextpage();h('Flat laminate: static basis, fatigue caveat')
img(B/'fatigue/extracted-native/ACP-Pre-original-thumbnail.png',115,115)
p('<b>Original CAD thumbnail:</b> flat plate, native SpaceClaim with serialized ACIS geometry. This adds a laminate reference, not complex industrial geometry. Workbench archive, ACP layup, material data and static RST are retained.')
img(B/'fatigue/original-published-fem-3.png',470,280)
p('<b>Original publisher demonstration:</b> fatigue damage contour. The example uses a synthetic random load history and a dummy S-N curve. This demonstration is excluded from physical fatigue-life ground truth; no synthetic series or damage values were generated locally.')
s=rec['fatigue']['reader_audit']['states'][0]
table([['Saved static RST basis', 'Read-only inventory'],['Mesh','85 nodes; 68 elements; one static set'],['Displacement','85 rows, 6 DOFs; first three are translations'],['Maximum translation',f"{s['nodal_displacement']['maximum_translation_source_units']:.9f}, source length units unconfirmed"],['Stress coverage','510 finite recovered components, 85 rows']],[260,220])
p('The provided NPZ retains the static reader output and node mapping. Potential benchmark scope is static laminate response after source setup/units verification. It is not an independently validated fatigue-life case. Published postprocessor code was not executed.')
source('fatigue')
nextpage();h('Collection inventory and admission status')
table([['Source project','Geometry / saved evidence','Current status'],['Composite wing','Curved skin, perforated ribs, impactor; input.k + d3plot sequence','Complex geometry; decoder held'],['PCB-like board','Board CAD + static RST temperatures, translation, stress','Fields readable; units/setup review'],['Cyclic sector','Valid native STEP + RST base-sector fields','Fields readable; cyclic mapping review'],['Sandwich panel','Native CAD + random-vibration RST','Extraction held; PSD conventions'],['Flat laminate','Native CAD + static stress RST','Static only; dummy fatigue excluded']],[115,240,125])
p('<b>Counting:</b> five source projects and five native CAD/saved-result candidates. One provides complex assembly geometry. Four provide simpler geometry and additional physics. Zero newly verified dimensioned engineering drawings and zero certified benchmark admissions. Plies, frames, nodes and submodel files are not extra tasks.')
p('<b>Required before scoring:</b> establish matching CAD/result revisions, geometry scale, complete materials and layups, loads/constraints, units, state alignment, node/element correspondence and convergence. Legacy nodal stresses are recovered averages, not unaveraged integration-point values. Preserve NaNs and report the scored finite subset.')
p('<b>Separate tracks:</b> supplied-CAD-to-FEM can use these candidates once validated. Drawing-to-CAD-to-FEM needs an adequate original drawing; thumbnails and FEM views do not satisfy that requirement. No frontier-model results have been measured.')
p('<b>Included:</b> original Workbench/CAD/result files, real Git LFS HDF5 layup objects, material data, original documentation figures, exact source URLs and SHA-256 hashes, read-only arrays and inspection scripts. UNVERIFIED arrays remain excluded from scoring.')
p('<b>License:</b> example-data assets retain the repository MIT notice. Official documentation and images retain separate publisher copyright. This package is a local research collection; no public redistribution has occurred.')
p('Data source: <link href="https://github.com/ansys/example-data" color="blue">Ansys example-data</link>, pinned revision 8ef505f6ef699eeec68a16001df91ba353342f40. Full machine-readable provenance and limitations are in catalog.json, download-manifest.json and documentation-manifest.json.')
p('No COMSOL files, generated CAD, new solver runs or frontier-model calls were used in this extension.')
def footer(c,doc):
 c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,26,'Published CAD + FEM collection | source evidence and validation notes');c.drawRightString(A4[0]-44,26,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=40,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'composite-report-page-{i+1}.png')
print('PDF pages',len(doc))
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for f in sorted(R.rglob('*')):
  if f.is_file():z.write(f,'web-cad-fem-composite-dynamics/'+str(f.relative_to(R)))
 z.write(O,'web-cad-fem-composite-dynamics.pdf')
 for f in ['audit_web_composite_dynamics.py','enrich_web_composite_dynamics.py','report_web_composite_dynamics.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));count=len(z.namelist())
validation={'zip':str(Z),'bytes':Z.stat().st_size,'members':count,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest(),'crc_verified':True,'pdf_pages':len(doc)};(T/'composite-package-validation.json').write_text(json.dumps(validation,indent=2));print(validation)
