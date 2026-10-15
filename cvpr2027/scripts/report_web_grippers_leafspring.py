"""Report original web CAD/FEM evidence and package original research files."""
from pathlib import Path
import json,zipfile,hashlib,csv
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-additional-systems-search');roots=[D/x for x in ['web-cad-fem-pneumatic-gripper','web-cad-fem-finray-contact','web-cad-fem-leafspring-modal','web-cad-fem-bistable-gripper-held']];P,F,L,H=roots;pc,fc,lc,hc=[json.loads((r/'catalog.json').read_text()) for r in roots];v=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-grippers-leafspring.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-grippers-leafspring.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.4;sty['BodyText'].leading=12.3;sty['Heading1'].fontSize=18;sty['Heading1'].leading=22;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width=485,maxheight=240):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(x),sty['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def source(c):p(f'Source: <link href="{c["source"]}" color="blue">original publisher project</link>. Original source revision, filenames and download hashes retained.')
def nxt():story.append(PageBreak())
h('Pneumatic gripper: complex assembly CAD + FEM')
p('12 October 2026. New collection includes a multi-link pneumatic gripper, three-finger compliant contact model and curved leaf-spring modal source. Original CAD and existing FEM evidence were downloaded from publishers. No CAD model, engineering problem or FEM solution was generated locally.')
img(P/'assets/baseline/baseline_gripper_cad.png',485,185)
p('<b>Original publisher baseline CAD view:</b> Independently inspected final_a2_gripper.STEP is a valid native BREP, 26 solids and 598 faces; envelope 288.73 x150 x407.32 mm. Baseline STEP also imports valid with 26 solids / 538 faces. Render triangles are CAD display tessellation, not a new FEM mesh or a dimensioned manufacturing drawing.')
img(P/'assets/final-a2/final_a2_equivalent_stress.png',470,245)
p('<b>Original publisher ANSYS result figure:</b> final A2 assembly equivalent-stress peak 11.485 MPa at full prescribed closure. The rigid target cube obscures some linkage parts in the original view. Source contact figure and full original Workbench archive are included.')
p('One gripper family with baseline, contact-interface correction A1 and jaw lightweighting A2. The final A2 raw-result candidate has full assembly STEP plus the original saved RST. Baseline has CAD plus plots/tables; A1 provides corrected-block CAD and plots but no separate complete A1 assembly STEP.')
source(pc)
nxt();h('Pneumatic gripper: numerical references and archive')
img(P/'assets/final-a2/final_a2_contact_pressure.png',430,215)
p('<b>Original contact-pressure FEM figure:</b> maximum 0.57908 MPa. Source summary.csv and workbook Comparison / Final Validation sheets agree on the final validation values below.')
table([['Published quantity','Baseline','A1','Final A2'],['Reaction force N','256.67','48.561','49.848'],['Contact pressure MPa','19.779','1.1391','0.57908'],['Contact area mm2','32.3784','122.72','287.179'],['Global equivalent stress MPa','48.007','16.782','11.485'],['Global principal stress MPa','57.06','27.354','14.537'],['Jaw mass g','40.10','40.10','31.198']],[205,92,92,96])
p('<b>Saved result:</b> public v1.0 WBPZ is 942,827,583 bytes, with publisher SHA-256 verified. It contains file.rst (1,430,388,736 bytes), original ds.dat, solve.out, Mechanical database, native SLDASM and original figures. Metadata indicates 201,463 result nodes, 145,736 elements and 24 static substeps. Static labels 0.01-1 are not physical time histories. Source log reports ANSYS 2026 R1 completed.')
p('<b>Physics:</b> actuator displacement -28.8mm, large deflection, frictionless contact with rigid 150 mm cube, revolute pivots and translational actuator joint; homogenized PLA E 2000 MPa, nu 0.35, rho 1240 kg/m3. Read-only final jaw CAD volume gives 31.19849 g, agreeing with source rounded 31.198 g.')
p('<b>Scope limits:</b> no legacy nodal-field decoding of 2026 R1 RST. Compatible extraction and geometry/figure matching are pending. Baseline convergence M2-to-M3 differences are ~0.15% reaction and ~3.45% stress, not proof of final A2 convergence. Load Study endpoint 257.73 N / 48.026 MPa / 62.051 MPa differs from production summary 256.67 N / 48.007 MPa / 57.06 MPa; retain separate source scopes. Reaction under prescribed closure is not a measured cylinder-force rating.')
source(pc)
nxt();h('Fin Ray gripper: component CAD + assembled FEM')
img(T/'finray-original-finger-ball-cad.png',475,145)
p('<b>Read-only original real15.step:</b> valid two-solid CAD with 33 faces, comprising one finger and a truncated sphere. Finger volume 15,363.67 mm3; ball volume 245,042.51 mm3. Using a full sphere would overstate ball volume/mass by ~8.6%. No complete native three-finger assembly STEP was uploaded.')
img(F/'06_image/figures/3finger_closed.png',420,205)
p('<b>Original author FEM displacement figure:</b> three fingers closed 5.7 mm, source frame 4 of 44. Reported reaction 2.83 N per finger and 8.490418 N total. The original pre-generated three-finger mesh and native-reader displacement cache are included; no local rotation, mesh creation or solve was performed.')
table([['Original saved reference','Verified inventory'],['Mesh','26,469 finger nodes; 95,307 SOLID285 elements; ANSYS NBLOCK/EBLOCK'],['Cache','44 sets x 26,470 IDs x 3 displacement components; all finite'],['Extra node','26470 is rigid-ball pilot; coordinate 40,30,-9 mm from author source'],['Stored set labels','Steps 1-4 closing; 40 sets in step 5 pull; time 1-5 are static labels'],['Displacement magnitude','Largest absolute component 6.989506 mm; not a gravity capacity score']],[160,325])
p('Author extracted the cache with native MAPDL POST1. Source warns ansys-mapdl-reader 0.56 misreads 2026 R1 result fields. Original post-processing scripts are retained as text and never executed. No source RST or full nodal stress array is uploaded. Cache case_3finger is not automatically the gravity-ramp reference.')
source(fc)
nxt();h('Fin Ray: original histories and model limitations')
img(F/'06_image/plot/3finger_gravity.png',495,305)
p('<b>Original publisher plot:</b> includes grip force, load-deflection, directional pull and contact pressure. Plot title indicates a 10 degree tilt; tilt10 and nominal gravity CSV files are byte-identical, so this does not establish two independent solved configurations.')
g=fc['near_1kg_gravity_source_row']
table([['Near 1 kg original gravity CSV row','Value / unit'],['Mass / applied weight',f'{float(g["mass_kg"]):.8g} kg / {float(g["weight_N"]):.8g} N'],['Ball Y displacement',f'{float(g["uy_mm"]):.9f} mm'],['Peak equivalent stress',f'{float(g["svm_max_MPa"]):.9f} MPa'],['Peak contact pressure',f'{float(g["pres_max_MPa"]):.9f} MPa'],['Closed contact nodes',g['n_closed']]],[255,230])
p('Twelve CSV filenames reduce to eight byte-unique files. Three grip files are identical, two base-pull files are identical, and both nominal/tilt gravity ramps are identical. Original labels are preserved, with duplicate groups recorded in catalog.json.')
p('Published model uses hyperelastic TPU Mooney-Rivlin c10=.385, c01=1.47 MPa, friction 0.6, mixed-u/P SOLID285 and augmented-Lagrange contact. Closing 3/4/5/5.7 mm precedes pulling. Source notes omitted self-contact, contact-mesh sensitivity and numeric breakdown at larger closure. Exact geometry/rotation/setup matching remains pending.')
p('The source model supports ~1 kg with ~0.315 mm ball deflection but does not reproduce measured release near 1 kg. Holding beyond 3.2 kg is an unvalidated model outcome. Tip+Y pull and gravity-Y pull differ strongly; the source corrects an earlier directional conclusion. No predicted load is endorsed as a validated mechanical capacity.')
source(fc)
nxt();h('Leaf spring: original CAD and modal-result evidence')
img(L/'original-presentation-evidence/image2.JPG',440,160)
p('<b>Original source CATIA view:</b> curved multi-leaf spring. Independently imported leafspring.igs is a valid surface BREP with 16 faces and 0 solids, envelope 527.5 x202.93 x80 mm. Presentation describes 1020 mm full spring with five leaves; half/full model, boundary and material matching require review.')
img(L/'original-presentation-evidence/image5.png',485,255)
p('<b>Original ANSYS 2023 R2 screenshot:</b> mode 1 frequency 40.104 Hz. Screenshot tabular frequencies are 40.104, 429.45, 1388.6, 1871.9, 2922.3 and 4821.3 Hz. Modal deformation is normalization-dependent; its meter legend is not a static displacement prediction or a valid static error target.')
p('<b>Conflicting auxiliary table:</b> the same presentation lists steel 65.479/79.548 Hz, carbon-glass 113.39/137.61 Hz, aluminum 63.276/76.34 Hz and Kevlar 91.469/96.297 Hz as first modes in a separate comparison. Those 24 numbers do not match the six screenshot modes; configuration/material mapping is unassigned. They are held, not treated as 24 validated CAD/FEM pairs.')
p('Rayleigh-Ritz validation values are analytical references, not FEM. Native WBPJ is supplied, but no associated saved RST/dependency directory is uploaded. This adds one surface-CAD/modal-plot candidate held for matching. The original schematic is not a verified dimensioned manufacturing drawing. Geometry complexity is moderate.')
source(lc)
nxt();h('Dataset additions and benchmark preparation')
table([['Source / role','What is included'],['Pneumatic linkage gripper','Valid baseline/final full assembly STEP; 1 final raw-result candidate; baseline CAD/plots; A1 partial component/plots'],['Fin Ray compliant gripper','Valid component STEP, original assembled mesh, 44-set displacement cache and 8 unique CSVs; assembly matching pending'],['Leaf-spring modal study','Original IGES surface, native project and PPTX/modal figures; configuration held'],['Bistable-gripper source held','Native STEP/SLDPRT and 5 WBPZ setup archives; 0 located numerical-result pairs'],['Certified admissions / model scores','0 / none'],['New dimensioned drawing files','0 verified in this extension']],[165,320])
p('<b>Verification:</b> 97 selected original repository files passed pinned Git blob SHA-1, byte-size and SHA-256 checks; the additional original public release passed publisher SHA-256 and archive CRC. Pneumatic CSV/workbook copies match exact source values/cells. Fin Ray cache is finite, its 26,469 finger IDs match original mesh IDs, and pilot 26470 is explicitly separated. Original PPT media round-trip byte equality verified.')
p('<b>Supplied CAD to FEM track:</b> register the final pneumatic gripper as a raw-source candidate. Freeze exact CAD/CAE transforms, contacts, joints, material/unit cards, converged output definitions and compatible RST extraction before scoring. Fin Ray needs component-to-assembly mapping and exact case alignment. Leaf-spring modal source needs configuration identification.')
p('<b>Drawing to CAD to FEM track:</b> no new dimensioned manufacturing drawing is verified in this batch. CAD screenshots and generic spring schematics do not qualify for independent drawing reconstruction scoring.')
p('<b>Held bistable source:</b> five WBPZ files contain model/material databases and journals, with no located RST/RTH, numerical history, solver log or result figure. A Mechanical database alone is insufficient to claim saved numerical FEM references. It remains outside paired-result counts.')
p('<b>Archive policy:</b> original pneumatic WBPZ is included intact. The separately extracted 1.43 GB RST is omitted from the outer ZIP to avoid duplicating it; it is fully available inside the WBPZ and locally in extracted-original. Smaller decks, logs, figures and metadata are included for review. Original source programs are text-only research assets; collection scripts do not execute them.')
p('<b>Reuse:</b> no explicit data license found for these four repositories; original notices retained for local research. No public release or redistribution permission is implied. These source projects extend gripper/contact and vibration coverage; variants, nodes, frames, CSV rows and mirrored outputs are not additional engineering families.')
p('Three CAD/FEM evidence projects plus one excluded setup-only source. No CAD synthesis, fresh FEM solve, COMSOL dependency or frontier-model call. Models have not been evaluated; source numerical results are references, not model scores.')
source(hc)
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | original published evidence and numerical references');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'grippers-leafspring-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True)
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if f.is_file() and not (root==P and f.suffix.lower()=='.rst'):
    z.write(f,root.name+'/'+str(f.relative_to(root)),compress_type=zipfile.ZIP_STORED if root==P and f.name=='pneumatic_gripper_case_A2_final.wbpz' else zipfile.ZIP_DEFLATED)
 z.write(O,O.name);z.write(T/'source-verification.json','verification/source-verification.json');z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
 for f in ['pneumatic-final-original-cad.png','finray-original-finger-ball-cad.png']:z.write(T/f,'inspection-views/'+f)
 for f in ['collect_web_grippers_leafspring.py','audit_web_grippers_leafspring.py','verify_web_grippers_leafspring.py','report_web_grippers_leafspring.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));members=len(z.namelist());assert any(x.endswith('pneumatic_gripper_case_A2_final.wbpz') for x in z.namelist());assert not any(x.endswith('/file.rst') for x in z.namelist())
hh=hashlib.sha256()
with Z.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):hh.update(b)
q={'zip':str(Z),'bytes':Z.stat().st_size,'sha256':hh.hexdigest(),'members':members,'crc_verified':True,'pdf_pages':len(doc),'raw_RST_preserved_inside_original_WBPZ':True,'separately_extracted_RST_omitted_to_avoid_duplication':True};(T/'package-validation.json').write_text(json.dumps(q,indent=2)+'\n');print(q,flush=True)
