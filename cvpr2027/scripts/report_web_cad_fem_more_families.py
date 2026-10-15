from pathlib import Path
import json,pymupdf as fitz
from PIL import Image as PI,ImageDraw
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parents[1];D=R/'data/web-cad-fem-more-families';T=R/'tmp/cad-more-families-search';O=R/'output';a=json.loads((D/'deepwheel/catalog.json').read_text());styles=getSampleStyleSheet();styles['Normal'].fontSize=10;styles['Normal'].leading=14;styles['Heading1'].textColor=colors.HexColor('#153956');styles['Title'].fontSize=23;story=[]
def p(t,style='Normal'):story.append(Paragraph(t,styles[style]));story.append(Spacer(1,7))
def im(path,h=210):
 x=PI.open(path);sc=min(495/x.width,h/x.height);story.append(Image(str(path),width=x.width*sc,height=x.height*sc));story.append(Spacer(1,7))
def table(rows,widths=[220,275]):
 t=Table([[Paragraph(str(x),styles['Normal']) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef4')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b9c9d3')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t);story.append(Spacer(1,9))
p('New wheel and e-bike CAD/FEM sources','Title');p('12 October 2026 | Downloaded original published geometry and references')
table([['New family / source','Collected content'],['Wheel free-free vibration / DeepWheel','10 original STEP solid CAD models and paired FEM modal frequency labels. Full 904-row source CSV retained.'],['E-bike frame / TU Wien MBSE','1 native SolidWorks part with original displacement contour PDF and systems requirements. Plot-only reference.']])
p('11 new CAD/reference candidates from two sources. Ten wheel variants represent one engineering family, not ten different task families. E-bike adds a second source/design case. No geometry or FEM solve was generated locally.')
im(T/'epsilon_0285_2-cad-view.png',h=215)
p('Inspection render of original epsilon_0285_2 STEP: valid single solid, 9,268 faces. The publisher reconstructed this geometry from images and converted it to BREP; it is not human-authored parametric CAD or an original dimensioned drawing.')
r=next(x for x in a['records'] if x['id']=='epsilon_0285_2');table([['Published scalar FEM reference','Value'],['Mode 7 / rim frequency',str(r['reference']['mode_7_frequency_Hz'])+' Hz'],['Mode 11 / spoke frequency',str(r['reference']['mode_11_frequency_Hz'])+' Hz']])
p('Source: <link href="https://dataset.narnia.ai/deepwheel.html">DeepWheel / KAIST SmartDesignLab and Narnia Labs</link>. Soyoung Yoo and Namwoo Kang; dataset CC BY-NC 4.0. Original files and source documentation are preserved.')
story.append(PageBreak());p('Wheel modal reference table','Heading1');im(T/'beta_0451_0-cad-view.png',h=175)
p('Inspection render of original beta_0451_0 STEP. All ten imported models are valid single solids with 7,928-9,774 faces. Original filenames and checksums are indexed in the catalog.')
rows=[['ID (full original ID in catalog)','Mass kg','Mode 7 Hz','Mode 11 Hz']]
for i,r in enumerate(a['records']):rows.append([f"W{i+1:02d}: "+r['id'].split('_c1_')[0],r['reference']['mass_kg'],r['reference']['mode_7_frequency_Hz'],r['reference']['mode_11_frequency_Hz']])
table(rows,[210,75,100,110])
p('Selection: ten evenly spaced cases in sorted Mode 7 frequency order. This spans the 366.0754-479.6003 Hz source range; it is not a blind or random test split. 904 exact CSV-to-STEP filename matches verified; only ten CAD files downloaded.')
p('Publisher setup: OptiStruct via SimLab, free-free normal modes, Tet10 volume mesh with average size 6 mm. Stated A356-T6 material: E = 72 GPa, nu = 0.33, density = 2680 kg/m3. Mode 7 is after the six rigid-body modes; detailed mode-family matching needs eigenvectors.')
p('CONSISTENCY FLAG: CAD mass at stated density is about 3.25% below the CSV mass in every selected case. Published masses imply approximately 2770 kg/m3. This suggests a density/setup discrepancy; the actual solver input was not verified. Do not silently change density to fit labels.')
story.append(PageBreak());p('E-bike frame static loading','Heading1');im(T/'simulation.png',h=390)
p('Original publisher simulation.pdf, reproduced as an unmodified page view: frame CAD above and SolidWorks resultant displacement contour below. Native ebike-frame.SLDPRT is included.')
table([['Published contour legend','Reading'],['Resultant displacement URES','Displayed maximum 0.2545 mm'],['Reference precision','Rounded image legend, four significant digits; not a full nodal output file']])
p('Eight original source files downloaded; all publisher MD5 checksums pass. Requirements, architecture and user-needs PDFs accompany the CAD and simulation image.')
p('Scoring gaps: force magnitude and full material/boundary setup are not readable in the supplied PDF; no raw nodal result array or neutral STEP export verified. Native geometry validity and analysis state need a SolidWorks-compatible reader. This remains a plot-reference candidate, not an automatically scored case.')
p('Source: <link href="https://researchdata.tuwien.ac.at/records/npj9z-j2c96">TU Wien Research Data, DOI 10.48436/npj9z-j2c96</link>. Authors listed in original metadata; CC BY 4.0. Requirements diagrams do not replace dimensioned drawings.')
story.append(PageBreak());p('Benchmark preparation and rejected leads','Heading1')
table([['Reference category','Current use'],['10 wheel frequency pairs','Scalar modal prediction / supplied-CAD solver workflow candidates. Relative frequency errors can be reported after resolving setup discrepancy.'],['E-bike contour reference','CAD inspection and source-task audit candidate; precise automatic displacement scoring is not ready.'],['Drawing-to-CAD-to-FEM track','No new verified original dimensioned drawings. STEP inspection views and source pictures are not counted as engineering drawings.']])
p('Zero new certified admissions, zero model trials and zero local solver runs. Do not combine scalar frequencies with stress-field scores or treat all variants as independent task families. Public-data contamination, mesh convergence, mode ordering and replay tolerances remain to audit.')
table([['Other source crawled','Reason not added as a solved CAD/FEM pair'],['Composite thermal damage / Mendeley xjf5cmkjm3','Three ANSYS Workbench archives downloaded (about 100 MB). They contain DesignModeler CAD and Mechanical databases, but .skipped_files_on_archive explicitly lists the omitted .rth thermal result files and solver outputs. No solved temperature arrays verified.'],['Nominal tetrachiral compression / Zenodo 21669226','STEP + Abaqus CAE + experimental force-displacement records. No numerical FEM output file verified; experiments kept distinct.'],['Ocular adduction / Zenodo 7306040','Complex STEP assembly and Abaqus INP cases, but no published solved field/reference file verified in inspected repository.'],['CarHoods10k / Dryad','Structural scalars and STL geometry available; native BREP CAD not verified.'],['Antmicro thermal example','Native FCStd and workflow scripts found, but no saved original solved fields verified.']])
p('Package contains qualified candidate-source originals, catalogs, provenance, SHA-256 checksums, validation reports and audit scripts. The three unqualified composite archives remain in the local research cache and are excluded from the paired-source ZIP.')
p('Earlier published CAD/FEM collections remain linked in selected-dataset.json. The new source subset is an incremental addition, not a replacement.')
pdf=O/'pdf/web-cad-fem-wheel-ebike.pdf';SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=38).build(story)
doc=fitz.open(pdf);thumbs=[]
for i,page in enumerate(doc):
 path=T/f'new-report-page-{i+1}.png';page.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(path);x=PI.open(path).convert('RGB');x.thumbnail((350,495));thumbs.append(x)
contact=PI.new('RGB',(350*2,530*((len(thumbs)+1)//2)),'#dce4eb');dr=ImageDraw.Draw(contact)
for i,x in enumerate(thumbs):contact.paste(x,((i%2)*350,(i//2)*530));dr.text(((i%2)*350+8,(i//2)*530+500),f'Page {i+1}',fill='black')
contact.save(O/'web-cad-fem-wheel-ebike-preview.png');print('PDF',len(doc),'pages',pdf)
