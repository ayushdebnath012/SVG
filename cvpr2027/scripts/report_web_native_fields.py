"""Illustrate and package original native CAD and existing FEM fields."""
from pathlib import Path
import json,hashlib,zipfile,re
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-native-fields-search');roots=[D/n for n in ['web-cad-fem-elmer-cooling','web-cad-fem-wheel-rim-fields','web-cad-fem-testbench-fields']];A,W,B=roots;cats=[json.loads((r/'catalog.json').read_text()) for r in roots];v=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-native-fields.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-native-fields.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.4;sty['BodyText'].leading=12.3;sty['Heading1'].fontSize=18;sty['Heading1'].leading=22;story=[]
def fmt(t):
 chunks=re.split(r'(<[^>]+>)',t)
 for i,t in enumerate(chunks):
  if t.startswith('<'):continue
  t=re.sub(r'\b(to|within|is|temperature|velocity|powers|total|three|imply|maximum|minimum|envelope|E|nu|rho|k|mu|mean|Source|source|report|label|mode|Mode|modes|of|about|all|All|from|below|prescribed|four|first|each|case|cases|inlet|ambient|around|across|a|near|reader|these|gives|giving|for|with|count|nodes|points|cells|Native|native|full|model|including|and|solid|pressure|SYS|The|FreeCAD|coordinates|recovered|yield|frequencies|not|converged|Its|CalculiX|bounds|x|adds)(?=\d)',r'\1 ',t)
  t=re.sub(r'(?<=\d)(modes|nodes|faces|solids|Hz|K|Pa|MPa|mm|micrometers|GPa|W|N|s)\b',r' \1',t)
  t=re.sub(r'(?<=[;:])(?=\S)',' ',t)
  t=re.sub(r'/(?=\d)','/ ',t)
  chunks[i]=re.sub(r'=(?=[0-9-])','= ',t).replace('andm/s','and m/s')
 return ''.join(chunks)
def p(t):story.extend([Paragraph(fmt(t),sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width=490,maxheight=200):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(fmt(str(x)),sty['BodyText']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def src(i):p(f'Source: <link href="{cats[i]["source"]}" color="blue">original publisher repository</link>. Original bytes, source revision and file hashes retained.')
def nxt():story.append(PageBreak())
h('Radiator assembly: native CAD and saved FEM')
p('13 October 2026. This extension adds two repositories with three original CAD geometries and seven saved analysis candidates: two Elmer cooling models and five wheel-rim variants. A previously collected test frame is identified as a duplicate; four unmatched strip restart outputs remain held. No new CAD or solver run.')
img(T/'elmer-original-radiator-CAD-view.png',490,185)
p('<b>Read-only original BREP view:</b> four TO-220 transistor cases on an aluminium radiator. Native full-bridge_on_radiator.FCStd contains a valid 24-solid, 355-face final geometry: 23 physical solids plus an air domain. Display hides only the original air solid; no body was redesigned or reconstructed.')
img(T/'full-bridge_on_radiator-original-temperature-section.png',490,175)
p('<b>Read-only section of the existing saved Elmer field:</b> 137,182 points /130,305 cells. Original global temperature range is 285.954701 to424.355500 K; pressure -0.01161098 to0.05898355 Pa; derived speed maximum0.18218990 m/s. Section displays original points within1.5 mm of the median X plane; full arrays remain unchanged.')
p('Native inlet/ambient temperature is298.15 K and flow velocity50 mm/s =0.05 m/s. The global minimum is below ambient; finite arrays do not establish a physically validated solution. Keep the undershoot unmodified and hold scoring until mesh, stabilization, domain and convergence checks resolve it.')
p('Publisher README heat powers3.04 /1.91 /4 /0 W total8.95 W. Native DFlux values on three9 mm2 faces imply3.4 /4.7 /2.2 W total10.3 W under Elmer SI flux units. This is a read-only derived load check; exact revision/scope disagreement is retained. Radiation is omitted in the source model.')
src(0)
nxt();h('Water cooling: coupled thermal-flow control')
img(T/'elmer-original-tube-CAD-view.png',490,170)
p('<b>Read-only source CAD:</b> native fem-elmer-tube-thermalflow-velocity-3d.FCStd stores two valid solids,29 faces and envelope100 x40 x45.9 mm. Source steel block and water domain are shown, with the original fluid solid transparent. This is a simple coupled-physics control, separate from complex assembly counts.')
img(T/'fem-elmer-tube-thermalflow-velocity-3d-original-temperature-section.png',490,170)
table([['Original saved quantity','Native field / source setup'],['Mesh','41,565 points /36,843 cells; full VTU and exact numerical copies'],['Temperature','284.267569 to600 K; source300 K inlet and600 K imposed heated faces'],['Pressure','0 to101,095.060167 Pa globally; zero solid-point values do not establish minimum fluid pressure'],['Velocity','Derived speed maximum0.49931105 m/s; prescribed inlet50 mm/s =0.05 m/s'],['Material cards','Steel k43 W/m/K; water k0.591 W/m/K, rho998 kg/m3, mu0.001003 kg/m/s']],[155,330])
p('The600 K maximum is prescribed. The284.2676 K minimum falls below the300 K thermal boundary values; do not clip it or treat it as a certified temperature target. Native model, mesh, full stored fields and finished solver log are included, but model convergence and domain-scoped scoring still need review.')
p('FreeCAD0.21.1 Elmer writer uses SI scalar fields and scales mesh coordinates0.001 during solving, reverting coordinates for VTU output. Thus stored coordinates correspond to original CAD millimeters, while temperature, pressure and velocity use K, Pa andm/s. <link href="https://github.com/FreeCAD/FreeCAD/blob/0.21.1/src/Mod/Fem/femsolver/elmer/writer.py" color="blue">Primary unit implementation</link>. VTU lacks body/cell IDs; original UNV groups and native material references are retained for future mapping.')
src(0)
nxt();h('Wheel rim: native CAD and original static results')
img(W/'original-native-thumbnail.png',240,125)
p('<b>Unchanged original SpaceClaim thumbnail:</b> native Rim.SLDPRT and Rim.scdocx included, with three duplicated native CAE imports in the project. Compatible independent solid import is pending. This detailed spoke/flange/hub geometry is one family, irrespective of five analysis variants.')
img(W/'Report/images/Static_Bending_Stress.png',490,190)
p('<b>Original bending FEM figure:</b> displayed von Mises maximum1.3113e8 Pa =131.13 MPa, consistent with the report131.1 MPa. Read-only averaged tensor recovery gives131.132528 MPa. Original radial figure maximum2.0905e7 Pa agrees with recovered20.905141 MPa.')
table([['Source static case','Published U /stress','Saved references'],['Radial load','26.16 micrometers /20.9 MPa','Source remote FY=4000 N'],['Bending moment','244.3 micrometers /131.1 MPa','Source MX=1525, MY=1296, MZ=0 N m'],['Both static files','58,872 nodes /32,734 elements each','9,378 finite stress nodes;49,494 missing, masks retained']],[120,180,185])
p('Source /units,MKS: E71 GPa, rho2770 kg/m3, nu0.33; report yield280 MPa. The report rounds a formula giving1980 N m to2000 N m; source component moment cards are preserved exactly. Static loading is a snapshot, not a measured fatigue life or reproduced qualification test.')
p('<b>Decoder limit:</b> ansys-mapdl-reader0.56.0 returns nonfinite translations and values near1e308 for these2026 R1 RSTs. Displacement arrays are excluded from NPZ. Native RSTs and publisher U plots remain unchanged; averaged stress arrays are exploratory pending compatible independent recovery.')
src(1)
nxt();h('Wheel modal results: three boundary variants')
img(W/'Report/images/Modal_Unconstrained_7.png',490,165)
p('<b>Original free-free Mode7 figure:</b> first flexible mode near381.37 Hz. Six preceding rigid-body modes are retained from native headers, including numerical frequencies0 to0.00251 Hz. Mode deformation normalization is arbitrary; it is not an operating displacement.')
table([['Original saved model','Nodes /elements','Selected header frequencies [Hz]'],['Free-free, SYS','116,074 /63,727','7-8:381.371750 /381.378935;9-10:771.759216 /771.800400'],['Bolt-constrained, SYS-1','58,870 /32,440','1-2:390.017006 /390.215152;3-4:433.718078 /443.721897;7-8:780.500409 /780.550708'],['Tire approximation, SYS-2','58,882 /33,913','5-6:20.843524 /20.843526;7-8:283.770219 /283.953610;9-10:613.176559 /613.213384']],[125,125,235])
p('All12 frequencies per configuration are copied exactly into NPZ. Three original modal RSTs and two static RSTs have distinct SHA-256 values. The36 modes count as three modal cases on one CAD family, not36 new engineering drawings or geometries.')
p('Constrained model fixes five cylindrical bolt-hole faces. Tire extension uses10 kg distributed mass and four50,000 N/m radial springs; it is not a full3D tire/contact model. Source decks, original geometry imports, material cards, plots and report are included.')
p('<b>Mesh discrepancy:</b> report claims a converged116,074-node mesh for all cases, but native constrained/tire/static headers contain about58,870 nodes. Preserve each actual mesh. The published free-free convergence study does not certify all other saved cases. Report wording claims a shift below0.2 Hz for771.8 to780.5 Hz, which does not match those numbers; use original frequencies.')
p('Exact native geometry import, BC/recovery validation and mesh revision mapping remain pending. No verified complete dimensioned manufacturing drawing was located. No model trials or certified scoring tolerances.')
src(1)
nxt();h('Test frame duplicate and unmatched strip outputs')
p('Original Test Frame.FCStd is byte-identical to the frame already collected in the earlier assembly batch. Its2,356-node embedded result is not counted again. The newly inspected test_runs folder supplies four316-node CalculiX2.19 FRD displacement files and corresponding reaction totals.')
table([['Original stage','Applied UX /UZ [mm]','Reaction FX /FZ [N]'],['1','0.008723224 /0.195083992','1532.754 /9.899221'],['2','0.143245675 /0.891315677','25170.38 /45.19469'],['3','0.280735514 /1.653076937','49329.41 /83.81534'],['4','0.156580863 /1.564182474','27513.38 /79.34368']],[75,215,195])
p('<b>Original files:</b> DAT totals are forces at the prescribed-displacement node set. The fixed-set totals oppose them to the stored rounding; XY/Z components and residuals are retained in the JSON audit. All316-node displacement arrays are finite and copied with original node IDs and coordinates.')
p('<b>Geometry mismatch:</b> each FRD has bounds600 x50 x10 mm, while native frame bounds are2000 x1500 x100 mm. The provided CAD is not the matching strip geometry. No native strip CAD was located, and none was constructed locally. Paired new-family count0.')
p('The source decks use sequential *Static restart steps with steel E210,000 MPa, nu0.3. Labels1..4 are load stages, not a dynamic digital-twin trajectory. Only DISP is requested; these files do not contain a stress field. Maximum edge displacement can be prescribed input, so reaction totals are the independent response candidates after geometry matching.')
p('Four stages remain one unmatched strip family/control lead, not four complex CAD/FEM tasks. Original restart and solver-output files are retained; vendored executables, manuals, FMUs and unrelated co-simulation runs were excluded. No source program or solver was executed.')
src(2)
nxt();h('Inventory, provenance and benchmark readiness')
table([['New original paired evidence','Count / qualification'],['New repositories /CAD geometries','2 /3: radiator assembly, water-cooling control, wheel rim'],['Complex geometries /simple controls','2 /1'],['Saved analysis candidates','7:2 Elmer coupled fields +5 wheel static/modal files'],['Held/duplicate testbench','Duplicate frame adds0;4 unmatched strip restart stages'],['New dimensioned drawing targets','0 verified'],['Certified admissions /frontier scores','0 /none']],[195,290])
p(f'<b>Verification:</b> {v["original_downloads_verified"]} original downloaded files pass pinned Git blob SHA-1, byte size and SHA-256. Three FCStd archives pass CRC and byte comparison across701,63 and84 members. Two full Elmer VTU copies match all numerical arrays and cell connectivity exactly. Static wheel stress copies match repeat reads, including NaN masks; five RST hashes are distinct.')
p('<b>Supplied CAD to FEM:</b> original Elmer cached BREPs independently import as valid solids. Native wheel CAD needs compatible import. Geometry/material/body assignments, dimensional scaling, heat-flux scope, fixed/load faces and solver/recovery conventions must be frozen before numerical grading. Finite raw arrays and finished logs alone do not establish physics accuracy.')
p('<b>Drawing to CAD to FEM:</b> keep a separate track. CAD thumbnails, cached BREP views and result figures are included, but no complete matching dimensioned drawing was verified. No source drawing or missing CAD was synthesized. Nodes, time labels, mode numbers and duplicated project imports do not inflate item counts.')
p('<b>Target limits:</b> retain Elmer temperature undershoots and the radiator README/native heat-load disagreement. Do not score prescribed600 K as a prediction, interpret solid-node zeros as fluid pressure minima, use normalized modal shapes as static deformation, or accept invalid legacy displacement decoding. Wheel convergence claims require exact case/mesh mapping.')
p('<b>Other crawled leads:</b> heated Inconel duct repository has reports, CSVs and decks but explicitly omits solver binaries/nativeCAD; CubeSat source has tensile experiments without CAD; robot-dog source has complex CAD without FEM outputs; sector gate has reports/video without native CAD; NIC shroud has analytical tables and generation/solver scripts without uploaded native CAD/full fields. None adds a paired item.')
p('<b>Package policy:</b> original FCStd, native wheel CAD, five RSTs, solver decks/logs, plots/reports, extracted VTUs, exact numerical copies, catalogs and master snapshot included. Original FCStd files contain every cached geometry/mesh member; duplicate extracted history members are omitted. Selected final BREP, Document.xml and native solver text accompany extracted fields.')
p('MIT notice and original material author/CC-BY notices preserved for Elmer examples. Wheel and testbench lack a located explicit data license; local research collection only. Original programs/serialized Python proxies were never executed or deserialized. No COMSOL dependency, new engineering problem, new FEM solve, public release or model call.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | native cooling fields and wheel dynamics');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer);doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'native-fields-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True);assert len(doc)==6
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if not f.is_file():continue
   rel=f.relative_to(root)
   if rel.parts[0]=='extracted-original' and f.name not in ['Data.vtu','Document.xml','original-Elmer-solver-output.txt','PartShape185.brp','PartShape13.brp']:continue
   z.write(f,root.name+'/'+str(rel))
 z.write(O,O.name);z.write(D/'web-complex-fem/selected-dataset.json','catalog/master-catalog-snapshot.json')
 for f in ['source-verification.json','crawl-leads-and-exclusions.json']:z.write(T/f,'verification/'+f)
 for f in ['collect_web_native_fields.py','audit_web_native_fields.py','report_web_native_fields.py']:z.write(Path('cvpr2027/scripts')/f,'inspection-scripts/'+f)
 for f in ['elmer-original-radiator-CAD-view.png','elmer-original-tube-CAD-view.png','full-bridge_on_radiator-original-temperature-section.png','fem-elmer-tube-thermalflow-velocity-3d-original-temperature-section.png']:z.write(T/f,'inspection-views/'+f)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));members=len(z.namelist())
hh=hashlib.sha256()
with Z.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):hh.update(b)
valid={'zip':str(Z),'bytes':Z.stat().st_size,'sha256':hh.hexdigest(),'members':members,'CRC_verified':True,'pdf_pages':len(doc),'redundant_native_extracted_history_omitted':True};(T/'package-validation.json').write_text(json.dumps(valid,indent=2)+'\n');print(valid,flush=True)
