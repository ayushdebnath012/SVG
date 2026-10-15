"""Evidence report and local dataset archive with original CAD and existing FEM."""
from pathlib import Path
import json,zipfile,hashlib
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-new-machinery-search');roots=[D/x for x in ['web-cad-fem-kresling-origami','web-cad-fem-valve-transient','web-cad-fem-engine-rod-drawing','web-drawing-fem-mounting-flange','web-cad-fem-rocket-turbopump']];K,V,R,F,H=roots;kc,vc,rc,fc,hc=[json.loads((r/'catalog.json').read_text()) for r in roots];check=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-origami-valve-rod.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-origami-valve-rod.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.4;sty['BodyText'].leading=12.3;sty['Heading1'].fontSize=18;sty['Heading1'].leading=22;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width=475,maxheight=270):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(v),sty['BodyText']) for v in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def source(c):p(f'Source: <link href="{c["source"]}" color="blue">original publisher project / dataset</link>. Original URLs, revisions and SHA-256 provenance retained.')
def nxt():story.append(PageBreak())
h('Kresling origami: native CAD and nonlinear FEM')
p('12 October 2026. Three CAD/FEM source projects added: compliant origami, power-plant valve thermal conduction and two connecting-rod load cases. An additional mounting-flange drawing/scalar source is held for drawing reconstruction. New broad families are origami mechanisms and industrial valve thermal analysis; rod/flange extend existing mechanical families.')
img(K/'original-Inventor-thumbnail.png',160,160)
p('<b>Original stored CAD preview:</b> PNG extracted unchanged from the Inventor thumbnail property. Original native IPT and binary Parasolid X_B are retained. This small source preview is not an independently imported STEP view or a dimensioned drawing. Inventor template filename says n8; selected Parasolid/deck names identify n6. Exact template parameters need review.')
img(T/'kresling-original-FEM-curve-values.png',495,210)
p('<b>Read-only plot of existing FEM cell values:</b> workbook RF 0.80 DM60, A7:C217 and E7:G107. Displacement, force and stored energy are copied from source FEA columns; EXP data is excluded. RF 0.80 has 211 samples, peak force 12.604324 N and minimum -1.401440 N. The AD-labeled curve has 101 samples and peak 13.505147 N. No new FEM values or energy integration.')
p('36 published FEM curves are retained across two workbooks with exact cell columns and row IDs. They cover reduction/material/time variants, not 36 downloadable CAD pairs. One RF0.80 CAD-linked design candidate is registered; exact curve/deck mapping remains pending.')
p('Example Abaqus deck uses geometric nonlinearity, viscoelastic creases, elastic-plastic panels, a quasistatic VISCO step of 18 s and imposed -18 mm Y displacement. CAD is scale x1; source example mesh is x3. No CAD scaling or source program was executed. No ODB/full nodal fields located.')
p('Credit: Samantha Mora, Nicola Pugno and Diego Misseroni, University of Trento; DOI 10.5281/zenodo.15118000, CC BY 4.0. Native geometry import, exact material/amplitude mapping and convergence need validation.')
source(kc)
nxt();h('Industrial valve: original BREP and thermal setup')
img(T/'valve-original-cad.png',490,180)
p('<b>Read-only source CAD inspection:</b> original valve.brep independently imports as a valid BREP with four solids and 112 faces. It represents the symmetric valve/nozzle/pipe region. Display triangles are CAD tessellation, not a newly generated FEM mesh. No dimensioned manufacturing drawing is claimed.')
img(V/'valve-materials.png',410,180)
p('<b>Original publisher material view:</b> stainless valve joined to carbon-steel piping. Source .geo defines volume and boundary labels; .fee defines nonlinear conductivity/diffusivity and transient thermal conditions. Scripts are retained as text and were never executed.')
table([['Model evidence','Published setup'],['Internal boundary','40 C at 0 s, 250 C at 100/500 s, 40 C at 600/1000 s; linear interpolation'],['External / symmetry','Convection h=1e-6 W/(mm2 K) to 50 C; symmetry adiabatic'],['Materials','Carbon steel and stainless, temperature-dependent source property tables'],['Initial state','Source solver starts with the steady-state solution at t=0']],[160,325])
p('This is one complex valve thermal candidate. Six sampled locations and 192 time steps remain one geometry task. Source BREP-to-volume/surface/SCL mapping, original mesh correspondence and mesh/time convergence require review.')
source(vc)
nxt();h('Valve: existing numerical FEM temperature histories')
img(T/'valve-1.png',495,305)
p('<b>Original published FEM plot:</b> rasterized from source SVG. Source CSV has 192 rows, 0-1000 s. Column 2 is imposed internal temperature and is excluded as a solved reference target. Columns3-8 are the six published FEM temperatures on carbon/stainless stress-classification lines (SCL).')
rows=[['Source FEM location','CSV column','Peak C','Final C at 1000 s']]
for r in vc['FEM_history']['fields']:rows.append([r['label'],r['column_1_based'],r['maximum_C'],r['final_C']])
table(rows,[210,75,90,110])
p('Original-temperature-history.npz preserves the original time vector, imposed boundary table/values and all six sampled FEM temperature columns. Source coordinates: SCL2 x=+3 mm and SCL4 x=-3 mm, y=0, from z=48.5 to 57 mm with center at 52.75 mm. Coordinates and physical material sides require explicit topology matching.')
p('Values are source-rounded to 0.001 C. Original full nodal mesh/valve-1.msh result file is not included in this source repository. The CSV supplies real FEM trajectories; it is not a complete nodal-field benchmark. No fresh mesh or solve was created.')
p('Compare model trajectories at the same source points and times after resolving mesh and units. Reproducing the imposed boundary is not a measure of solving the interior thermal problem. Zero certified admissions or measured frontier-model scores.')
source(vc)
nxt();h('Connecting rod: original CAD and two saved results')
img(T/'rod-original-cad.png',440,160)
p('<b>Read-only original neutral CAD:</b> connecting_rod.STEP is valid, with two solids and 76 faces, approximately 94 x 283.7 x 38 mm. Archive contains native SolidWorks rod CAD, two SpaceClaim documents, complete source decks/logs and two original RST files. Full engine native assemblies/parts and Sheet-1.SLDDRW are also preserved; their dependencies and drawing dimensions are unverified.')
S=R/'extracted-original/ANSYS_CONNECTINGROD/ConnectingRod_FEA_files/session_files'
img(S/'Total_Deformation(Tensile).png',440,180)
p('<b>Original ANSYS FEM deformation:</b> peak 2.2623e-7 m. Reader extraction matches 2.2623073e-7 m =0.000226231 mm. Companion original stress plots show 5.2316e5 Pa, consistent with recovered peak523,163.39 Pa =0.523163 MPa.')
table([['Saved source case','Nodes / elements','Max U mm','Peak averaged VM MPa'],['Tensile','27,646 /17,170','0.000226231','0.523163'],['Opposite signed loading','27,646 /17,170','0.000226231','0.523163']],[145,135,105,100])
p('Full source displacement and stress arrays are negatives of each other after matching IDs, with identical missing-stress masks. Two opposite linear-static cases remain one rod geometry; they do not establish nonlinear compression/buckling or a solved full-engine assembly.')
p('Source decks use /units,MKS and steel E=200 GPa, nu=0.3. Applied surface-traction card component 2 is +/-12,391.413196 Pa. Saved stresses are finite at 4,238 nodes and missing at 23,408; NaNs/masks are preserved. Exact neutral/native transform matching and convergence remain pending.')
source(rc)
nxt();h('Mounting flange: original dimensioned CAD drawing')
img(T/'mounting-flange-original-drawing.png',495,360)
p('<b>Original publisher engineering drawing:</b> one-page AutoCAD-exported PDF, with top/front views, section A-A and a title block specifying millimeters, alloy steel and scale 1:2. This is downloaded drawing evidence. No drawing or flange CAD was created locally.')
table([['Visible/source dimension','Review finding'],['Flange OD 160; thickness 15; hub OD 55','Dimensioned on original drawing'],['Bore','Plan labels 25 mm; section labels 26 mm; README says 26 mm'],['Hub height','Front 80 mm; section 95 mm needs interpretation'],['Bolt pattern / ribs / fillets','README supplies Ø130 mm PCD and 8 mm ribs; drawing lacks complete variable-fillet specification']],[180,305])
p('One drawing-based FEM candidate is held. No SLDPRT/STEP model or full saved SolidWorks result binary was uploaded. Drawing alone is insufficient to certify all geometric details. It does not provide 55 original CAD models for the 55 scalar simulation rows.')
p('The original native engine SLDDRW from the rod project is also retained, but has not been independently rendered or dimension-verified. One newly verified dimensioned engineering drawing file in this extension; zero complete manufacturing packages verified.')
source(fc)
nxt();h('Mounting flange: published FEM scalars and limits')
img(F/'fea-stress-plot.png',485,335)
p('<b>Original source SolidWorks Simulation figure:</b> source applied load 3000 N, peak stress 2.994e7 Pa =29.94 MPa and URES 0.002606 mm. Source deformation display scale 6,142.26 exaggerates shape. The screenshot is preserved unchanged.')
rows=[['Fillet mm, load 3000 N','CSV stress MPa','CSV U mm']]
for radius in range(1,6):
 import csv
 r=next(r for r in csv.DictReader((F/'fea-results.csv').open()) if float(r['load_N'])==3000 and float(r['fillet_radius_mm'])==radius);rows.append([radius,r['max_stress_MPa'],r['max_displacement_mm']])
table(rows,[220,130,135])
p('The figure stress and displacement do not simultaneously match a single table row. CAD/fillet/setup revision and screenshot scope are unresolved. Preserve source figures and CSV values without silently replacing, fitting or rescaling them.')
p('CSV records 55 claimed linear-static runs: 11 loads x 5 fillet radii, with stress, displacement and safety factor. It is one drawing/scalar campaign, not 55 CAD/reference pairs. Original-source-scalar-table.npz exactly retains 55 IDs and numerical rows.')
p('Source fixtures fix the four bolt-hole cylindrical faces and apply distributed normal force to hub top. Exact solver material, mesh, fixture/load mapping and convergence need confirmation. Published surrogate-network accuracy is not a frontier-model benchmark score.')
source(fc)
nxt();h('Collection inventory and benchmark preparation')
table([['New source evidence','Count / role'],['Kresling origami','1 native CAD-linked curve candidate; 36 auxiliary FEM curves; original IPT/X_B and Abaqus deck'],['Power-plant valve','1 valid native BREP with 6 FEM temperature trajectories; 192 source time samples'],['Connecting rod','1 valid STEP geometry with 2 original static RST cases; engine CAD/drawing auxiliary'],['Mounting-flange drawing','1 dimensioned engineering drawing and 55 source scalar rows; no native3D CAD uploaded'],['Rocket turbopump held','Original STEP downloaded, but structural FEA is future work; CFD excluded'],['Certified cases / model scores','0 / none']],[165,320])
p(f'<b>Provenance and checks:</b> all {check["original_downloads_verified"]} selected original downloads passed publisher MD5 or Git blob SHA-1, byte-size and SHA-256 checks. All 36 FEM curve copies, six valve histories and 55 scalar table rows were compared with the original cells/files. Rod opposite signed field consistency is verified. Original source files, labels, notices and unresolved limits remain visible.')
p('<b>Supplied CAD to FEM:</b> valve and rod have independently imported valid CAD. Origami native CAD needs compatible import and the x1/x3 source correspondence resolved. Freeze exact setup, geometry revision, units, output point/mode conventions and mesh/error tolerances before model trials.')
p('<b>Drawing to CAD to FEM:</b> flange adds useful original orthographic/section evidence, with bore and detail conflicts explicitly held. Verify missing dimensions and original 3D model/result mapping before using it for reconstruction scoring. Native rod drawing remains unrendered.')
p('<b>Held turbopump source:</b> Report.pptx slide 10 lists structural/centrifugal FEA as Next Steps. Slide 9 metrics are CFX pressure, torque and efficiency, rather than saved structural FEM. It is excluded from paired counts despite its complex CAD. No result was invented for it.')
p('<b>Licenses:</b> origami CC BY 4.0, credited to Mora/Pugno/Misseroni; FeenoX GPL3 with original notice; flange MIT; rod and turbopump data-license status unresolved. Local research collection only. Original native files are preserved; no public release or license grant is implied.')
p('Three CAD/FEM source projects. Two new broad family candidates: compliant origami and industrial valve thermal conduction. Rod and flange extend already represented families. Samples, scalar rows, material variants and opposite load directions are not extra families.')
p('No locally generated CAD, source program execution, new FEM solve, COMSOL dependency or frontier-model call. Source references are benchmark candidates; certified admission remains zero.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | original source evidence and numerical references');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'origami-valve-rod-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True)
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if f.is_file():z.write(f,root.name+'/'+str(f.relative_to(root)))
 z.write(O,O.name);z.write(T/'source-verification.json','verification/source-verification.json')
 for name in ['collect_web_origami_machinery.py','collect_web_valve_thermal.py','audit_web_origami_machinery.py','verify_web_origami_machinery.py','report_web_origami_valve_rod.py']:z.write(Path('cvpr2027/scripts')/name,'inspection-scripts/'+name)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));n=len(z.namelist())
v={'zip':str(Z),'bytes':Z.stat().st_size,'members':n,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest(),'crc_verified':True,'pdf_pages':len(doc)};(T/'package-validation.json').write_text(json.dumps(v,indent=2)+'\n');print(v,flush=True)
