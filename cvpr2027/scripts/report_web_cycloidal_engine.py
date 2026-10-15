"""Evidence PDF and local research package; no CAD creation or FEM solves."""
from pathlib import Path
import json,zipfile,hashlib
import pymupdf
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
D=Path('cvpr2027/data');T=Path('cvpr2027/tmp/cad-fem-machine-parts-search');roots=[D/x for x in ['web-cad-fem-cycloidal-drive','web-cad-fem-engine-tbc','web-cad-fem-piston-drawing','web-cad-fem-held-machine-leads']];C,E,P,H=roots;cc,ec,pc,hc=[json.loads((r/'catalog.json').read_text()) for r in roots];V=json.loads((T/'source-verification.json').read_text());O=Path('cvpr2027/output/pdf/web-cad-fem-cycloidal-engine.pdf');Z=Path('cvpr2027/output/datasets/web-cad-fem-cycloidal-engine.zip');sty=getSampleStyleSheet();sty['BodyText'].fontSize=9.5;sty['BodyText'].leading=12.4;sty['Heading1'].fontSize=18;sty['Heading1'].leading=22;story=[]
def p(t):story.extend([Paragraph(t,sty['BodyText']),Spacer(1,5)])
def h(t):story.extend([Paragraph(t,sty['Heading1']),Spacer(1,7)])
def img(path,width=475,maxheight=260):
 im=PILImage.open(path);hh=width*im.height/im.width
 if hh>maxheight:width*=maxheight/hh;hh=maxheight
 story.extend([Image(str(path),width=width,height=hh),Spacer(1,6)])
def table(rows,widths):
 t=Table([[Paragraph(str(v),sty['BodyText']) for v in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey)]));story.extend([t,Spacer(1,6)])
def source(c):p(f'Source: <link href="{c["source"]}" color="blue">original publisher repository</link>. Revision, original URLs and file hashes are retained in the catalog and download manifest.')
def nxt():story.append(PageBreak())
h('Cycloidal gearbox: original complex CAD')
p('12 October 2026. Published CAD and existing FEM from three source projects: cycloidal gearbox component studies, coated piston thermal/structural studies and piston-pin-rod assembly plots. Two broad mechanical families: geared transmission and engine piston systems. No new geometry or FEM solution was generated.')
img(T/'cycloidal-assembly-cad.png',490,265)
p('<b>Read-only CAD inspection:</b> the original assembly STEP independently imports as a valid BREP with 198 solids and 3,455 faces. Its envelope is approximately 109 x 115 x 115 mm. This image tessellates the original CAD for display; the triangle edges are display facets, not a FEM mesh or a dimensioned drawing.')
img(T/'cycloidal-disk-cad.png',320,180)
p('<b>Original disk geometry:</b> one valid solid with 20 faces, imported from native FreeCAD BREP. All 28 supplied component FreeCAD models import as valid single solids. Housing has 191 faces; lid 129; flanges 45/48; coupler 33. Pins, spacers and simple rings add setup variety, not equivalent complex drawings.')
p('The source has 15 primary component-study groups, with 15 PLA/steel references and 13 PETG-CF references. Purchased steel pins are reused in the material comparison. This is a component-static study, not an assembled gearbox contact/dynamic result.')
source(cc)
nxt();h('Gearbox: original published FEM comparisons')
img(C/'fem/compare/side_by_side/01_disk.png',495,215)
p('<b>Original publisher Fig. 01:</b> PLA and PETG-CF disk stress contours at nominal 200 N tangential loading. Source legend uses Pa; raw corrected CalculiX values use the N-mm-MPa convention supported by native material/deck data. Derived peak averaged nodal stress is 5.69916 / 5.70073 MPa; max U is 0.0496606 / 0.0579329 mm.')
img(C/'fem/compare/side_by_side/09_cam_p2.png',495,215)
p('<b>Original publisher Fig. 09:</b> input cam P2 radial bending at nominal 300 N. Both source material studies give peak 18.44698 MPa. Max U is 0.0279490 mm for PLA and 0.0326072 mm for PETG-CF. Earlier axial cam solutions are retained as secondary cases and not included in the 28 primary references.')
p('Original FRD files contain displacement, stress, total strain and nodal ERROR fields, source IDs, coordinates and elements. Exact saved decimal arrays are copied to NPZ; no missing values are filled and no solve is run. Von Mises is labeled as derived from the saved averaged nodal tensor.')
p('Isotropic material assumptions, fixed-face stress peaks, no mesh convergence study and absence of fatigue/wear/creep/contact limit physical interpretation. These are numerical source-reference candidates; zero certified benchmark admissions.')
source(cc)
nxt();h('Gearbox: numerical reference inventory')
primary=[r for r in cc['records'] if r.get('primary_component_candidate')];pla=[r for r in primary if '/pla/' in r['file']];pet=[r for r in primary if '/petg_cf/' in r['file']]
def name(r):return Path(r['file']).stem.replace('DiskPLA','Disk').replace('_lin','').replace('_radial','').replace('_fixed','')
p('28 primary native CAD / saved-solution candidates across 15 component groups. The assembly remains one broad family; the 13 material reruns are variants. Other original results: one 1000x underloaded disk, two earlier axial cam solves and one mesh-only housing file, all excluded from primary counting.')
rows=[['Component','PLA/steel max U mm','PETG-CF max U mm','Peak VM MPa (PLA/steel)']]
for r in pla:
 q=next((x for x in pet if name(x)==name(r)),None);rows.append([name(r),f"{r['max_translation_mm']:.6g}",f"{q['max_translation_mm']:.6g}" if q else 'same steel; no rerun',f"{r['derived_max_averaged_nodal_vm_MPa']:.6g}"])
table(rows,[100,128,132,125])
p(f'<b>Native/result check:</b> {V["primary_FRD_native_result_matches"]} primary FRD fields match the corresponding native FreeCAD saved displacement and derived von Mises values after matching original node IDs. The PLA disk correct object is CCX_Results001; the first object is the underloaded run. Both cam files also contain earlier axial plus later radial objects.')
disk=next(r for r in pla if name(r)=='Disk');coupler=next(r for r in pla if name(r)=='Coupler')
p(f'<b>Loads:</b> independently summed corrected disk CLOAD resultant {disk["CLOAD_resultant_norm_N"]:.6f} N, versus nominal 200 N. Corrected entries are exactly 1000 times the original deck entries. Coupler applied/reaction norm mismatch is {coupler["reaction_balance_relative_norm"]*100:.3f}%, as the source itself notes. No values were rescaled locally to fit a desired result.')
p('FRD ASCII rounding is preserved. Compare candidate tensors with the same averaged nodal scope and load fixture; these peaks are not integration-point stresses or validated material failure loads. Native assembly-to-component topology matching and convergence review remain pending.')
source(cc)
nxt();h('Coated engine piston: native CAD and FEM')
img(T/'engine-coated-cad.png',480,220)
p('<b>Read-only original CAD inspection:</b> 0.2 mm coating IGES independently imports as two valid solids with 132 faces, approximately 127 x 127 x 82.75 mm. The source publishes 12 IGES files: uncoated plus 11 coating thicknesses. All import as valid BREP; uncoated has one solid and 129 faces. These are supplied CAD, not manufacturing drawings.')
img(E/'Images/IMG-20250608-WA0024.jpg',485,230)
p('<b>Original source structural FEM contour:</b> maximum total deformation 0.054303 mm. Companion stress image WA0022 shows 225.75 MPa. Thicker-configuration images show 716.37 MPa and 0.10778 mm. Exact CAD thickness, thermal-load revision and solver setup matching are not yet certified.')
p('Original ANSYS reports contain thermal setup, material tables, mesh and result tables. Six numerical export files preserve transient temperature/heat-flux minima, maxima and averages. No raw RTH or RST was published in this repository. Three published configuration candidates remain one piston/coating family, rather than 12 proven CAD/result pairs.')
p('The optimizer mock CSV and untraced TBC training CSV are explicitly excluded from FEM ground truth. Python engine-cycle outputs and optimizer predictions are also excluded. No source script or data generator was executed.')
source(ec)
nxt();h('Engine thermal results: time and revision matter')
img(E/'Images/IMG-20250608-WA0011.jpg',485,220)
p('<b>Original temperature contour:</b> source mesh/color result retained unchanged. The ANSYS 0.2 mm report, physical page 14 Table 22, records 2,513.5 C at 37.95 s; its full time-history maximum is 2,526.8 C. The README labels 2,314.3 C as 0.2 mm, but the uncoated report places that number on the uncoated configuration at 37 s.')
rows=[['Numerical export','Samples','Max over saved history','Final maximum at 71.1 s']]
for r in ec['source_thermal_export_tables']:
 label=Path(r['file']).name.replace('.xls','');unit='C' if 'temp' in label else 'W/mm2';rows.append([label,r['rows'],f"{r['highest_saved_maximum']:g} {unit}",f"{r['final_maximum']:g} {unit}"])
table(rows,[180,55,130,120])
p('The original .xls files are UTF-8 tab-separated ANSYS exports, not binary Excel workbooks. Original-thermal-tables.npz preserves all six tables, including source row number, time, minimum, maximum and average. Each time sequence is finite and increasing from 0.010014 to 71.1 s. A sample is not a separate task.')
p('<b>Reference hold:</b> thicker-coating report Temperature state is Obsolete. Its displayed flux is 19.65 W/mm2 at 40 s, while the downloaded 2 mm history reaches 98.268 W/mm2 elsewhere. Do not mix a displayed-time value, whole-history peak and another report revision.')
p('The modeled temperatures exceed typical aluminum material validity ranges; source material/thermal-load assumptions need engineering review. Fatigue life and real-engine performance are not certified. Preserve the published data while keeping these limits visible.')
source(ec)
nxt();h('Piston assembly: original CAD and drawing files')
img(P/'FILE2.png',425,230)
p('<b>Original publisher assembly/mesh view:</b> piston, pin and connecting rod. Downloaded native files include 3D AutoCAD DWG, a DWG named PISTON DRAWING SHEET AUTOCAD 2D and a SolidWorks assembly. DWG headers identify AC1032. Drawing dimensions and completeness have not been rendered/verified.')
img(P/'FILE3.png',425,230)
p('<b>Original source stress contour:</b> maximum 8.8801e8 Pa = 888.01 MPa. Source displacement contour file.png shows 0.00022122 m = 0.22122 mm. README rounds stress to 880 MPa. Preserve the actual figure legend rather than silently using the prose number.')
p('<b>Conditional candidate:</b> no referenced SolidWorks part files were found in the published tree. Native DWG geometry import is pending. The WBPJ project is present, but its companion solver directory and raw RST are absent. It is not a saved result archive.')
p('README claims a reaction CSV, neutral CAD and convergence study; these assets are absent from the actual uploaded tree. Linear elastic stress above the stated 280 MPa yield does not demonstrate computed plasticity. No manufacturing-drawing or certified supplied-CAD benchmark admission is claimed.')
source(pc)
nxt();h('Collection status and benchmark use')
table([['Source evidence added','Count / meaning'],['Cycloidal drive','15 component groups; 28 primary native CAD / raw-reference candidates; 31 unique saved solutions in total'],['Coated piston','12 valid original IGES exports; 3 published configuration candidates; 6 numerical thermal histories'],['Piston-pin-rod assembly','1 conditional CAD/drawing plus plot candidate; native dependencies and DWG import pending'],['Cooled HPT blade lead','0 pairs: published FEA uses an unpublished second-design CAD revision'],['Broad families','2: geared transmission and engine piston systems'],['Certified admissions / measured model scores','0 / none']],[220,265])
p(f'<b>Provenance:</b> all {V["original_downloads_verified"]} selected original downloads passed source Git blob SHA-1, file size and SHA-256 checks. Original URLs, pinned revisions, native files, reports, figures, decks, solver logs and read-only arrays are retained locally. Local CAD images are explicitly inspection renders of original geometry.')
p('<b>Supplied CAD to FEM:</b> gearbox component references are strongest for preparing static benchmark tasks. Freeze corrected deck, native geometry, original IDs, material and load fixture before evaluating. Separate setup/replay success from scalar/vector/field errors; match stress recovery conventions and mesh mappings.')
p('<b>Drawing to CAD to FEM:</b> retain the original piston DWG drawing as a lead, but do not admit it until dimensioned views, referenced parts, geometry reconstruction and result mapping are verified. No new complete dimensioned manufacturing-drawing package was verified in this extension.')
p('<b>Source rights:</b> cycloidal native FCStd declares All rights reserved and no repository license was found. Coated piston README asserts MIT but no standalone LICENSE is present. Piston assembly license is unresolved. This package is a local research collection, not permission for public redistribution. Original source attribution is preserved.')
p('HPT source permits viewing/downloading to discuss the project but reserves CAD/figure/data reuse. Only its notices and the unpaired-revision evidence are retained; turbine CAD and figures are not packaged. No invented pairing was made.')
p('No generated CAD, source-script execution, new FEM solve, COMSOL dependency or frontier-model call. The master collection now links these new catalogs and keeps primary references, secondary solutions and held leads separate.')
def footer(c,doc):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(44,25,'Web CAD + FEM | original evidence and read-only verification');c.drawRightString(A4[0]-44,25,str(doc.page))
O.parent.mkdir(parents=True,exist_ok=True);SimpleDocTemplate(str(O),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=38,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(O)
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(T/f'cycloidal-engine-report-page-{i+1}.png')
print('PDF pages',len(doc),flush=True)
Z.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for root in roots:
  for f in sorted(root.rglob('*')):
   if f.is_file():z.write(f,root.name+'/'+str(f.relative_to(root)))
 z.write(O,O.name)
 z.write(T/'source-verification.json','verification/source-verification.json')
 for name in ['collect_web_cycloidal_engine.py','audit_web_cycloidal_engine.py','verify_web_cycloidal_engine.py','report_web_cycloidal_engine.py']:z.write(Path('cvpr2027/scripts')/name,'inspection-scripts/'+name)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));count=len(z.namelist())
v={'zip':str(Z),'bytes':Z.stat().st_size,'members':count,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest(),'crc_verified':True,'pdf_pages':len(doc)};(T/'package-validation.json').write_text(json.dumps(v,indent=2)+'\n');print(v,flush=True)
