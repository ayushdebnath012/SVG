from pathlib import Path
import json,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
root=Path(__file__).resolve().parents[2];p=root/'cvpr2027/output/datasets/cadfem-bench-v1.1-followup';src=root/'cvpr2027/data/web-cad-fem-fcvm-breadth';cat=json.loads((src/'catalog.json').read_text());rep=json.loads((p/'independent-reproduction/comparison.json').read_text())
for r in cat['records']:
 import numpy as np
 a=np.load(src/'extracted-original'/r['name']/'published-table.npz',allow_pickle=False)['table']
 if len(a)<2:continue
 fig,ax=plt.subplots(figsize=(4.1,2.2),layout='constrained');ax.plot(a[:,5],a[:,4],lw=1.7,color='#246187');ax.set_xlabel('Source reported displacement');ax.set_ylabel('Source load factor');ax.grid(alpha=.2);fig.savefig(src/'inspection'/(r['name']+'-published-curve.png'),dpi=160);plt.close(fig)
shutil.copytree(src,p/'published-source-expansion',dirs_exist_ok=True)
pdf=root/'cvpr2027/output/pdf/cadfem-bench-v1.1-followup.pdf';pdf.parent.mkdir(exist_ok=True,parents=True);c=canvas.Canvas(str(pdf),pagesize=(595,842));style=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=14,textColor=HexColor('#263647'))
def txt(s,x,y,w=495,size=10):
 st=ParagraphStyle('p',parent=style,fontSize=size,leading=size*1.38);a=Paragraph(s,st);_,h=a.wrap(w,800);a.drawOn(c,x,y-h);return y-h

def page(title,n):
 c.setFillColor(HexColor('#132b40'));c.rect(0,786,595,56,fill=1,stroke=0);c.setFillColor(HexColor('#ffffff'));c.setFont('Helvetica-Bold',17);c.drawString(42,810,title);c.setFillColor(HexColor('#5a6875'));c.setFont('Helvetica',8);c.drawString(42,24,'CADFEM-Bench v1.1 follow-up | 14 October 2026');c.drawRightString(553,24,str(n))
def pic(path,x,y,w,h):
 im=ImageReader(str(path));iw,ih=im.getSize();s=min(w/iw,h/ih);c.drawImage(im,x+(w-iw*s)/2,y+(h-ih*s)/2,iw*s,ih*s,mask='auto')
page('Release check and independent reproduction',1)
y=txt('<b>Baseline verified:</b> all 588 files listed in the v1.1 checksum manifest match. The frozen release still contains 118 active tasks and 298 published targets. This supplement adds independent validation evidence and 14 unscored source pairs.',42,763)
y=txt('<b>Two displacement tasks reproduced:</b> independent Gmsh remeshing and FEniCSx quadratic-displacement solves on 11 meshes. Reference values were read only by the comparison stage; none were replaced by new solver outputs.',42,y-14)
for i,r in enumerate(rep['records']):
 yy=640-i*295;txt(r['task_id'],42,yy,size=12)
 for j,(k,v) in enumerate(r['checks'].items()):
  txt(f"{k}: published {v['published_reference']:.8g} mm; independent {v['independent_fine_mesh_value']:.8g} mm; difference {100*v['relative_reference_error']:.3f}%; last refinement change {100*v['last_refinement_relative_change']:.3f}%.",42,yy-25-j*44,size=9)
 prefix='agentfem' if 'AGENT' in r['task_id'] else 'coupler';pic(p/'independent-reproduction'/(prefix+'-convergence.png'),60,yy-250,465,155)
txt('Limits: requested displacements only; no validation of every stress field or source family. Last-mesh change is an empirical indicator, not a rigorous error bound. The other 116 active tasks still lack independent reproduction.',42,82,size=9);c.showPage()
page('New source CAD and published nonlinear curves',2)
for i,name in enumerate(['Wyk_Rohrstoss_ring','Haltegriff_FEM_RC']):
 y=752-i*331;txt(name.replace('_',' '),42,y,size=13);pic(src/'inspection'/(name+'-CAD.png'),35,y-200,240,183);pic(src/'inspection'/(name+'-published-curve.png'),280,y-196,275,170)
 r=next(r for r in cat['records'] if r['name']==name)
 txt(f"Original FreeCAD model: {r['native_shapes'][0]['solids']} solid regions, {r['native_shapes'][0]['faces']} faces. Published analysis: {r['analysis_type']}; {r['published_table_rows']} printed history rows. Solid regions may be boolean fragments, not separate assembly parts.",42,y-210,size=10)
 txt('CAD view is a read-only tessellation of the original stored BREP. Curve is plotted directly from the original .out table; no new nonlinear FEM solution was generated.',42,y-260,size=9)
txt('Source: github.com/HarryvL/fcVM-workbench. Raw files, pinned Git blob hashes, native properties and exact table copies are included. Source-pair status: held for setup/revision mapping and numerical validation.',42,69,size=9);c.showPage()
page('Additional complex structural candidates',3)
for i,name in enumerate(['IPE400_4','transition']):
 y=752-i*331;txt(name.replace('_',' '),42,y,size=13);pic(src/'inspection'/(name+'-CAD.png'),35,y-200,240,183);pic(src/'inspection'/(name+'-published-curve.png'),280,y-196,275,170)
 r=next(r for r in cat['records'] if r['name']==name)
 txt(f"Original FreeCAD model: {r['native_shapes'][0]['solids']} solid regions, {r['native_shapes'][0]['faces']} faces. Published analysis: {r['analysis_type']}; {r['published_table_rows']} printed history rows. Initial imperfections and control-file material overrides must be matched to this specific output.",42,y-210,size=10)
 txt('The load factor scales a source-defined loading pattern; it is not a force in newtons. Printed stresses are associated with the source-selected critical Gauss point, not automatically global stress maxima.',42,y-260,size=9)
txt('Published CAD and curves are preserved unchanged. These figures are inspection views, not dimensioned manufacturing drawings or newly generated benchmark problems.',42,68,size=9);c.showPage()
page('Inventory, admission limits and remaining work',4)
y=txt('<b>14 native CAD/result pairs:</b> 14 valid extracted analysis BREP shapes; 996 published table rows; five original VTK result files. Named cases are not counted as independent physical families. Beam variants and transition revisions remain grouped for breadth claims.',42,762)
for r in cat['records']:
 y=txt(f"<b>{r['name']}</b> - {r['published_table_rows']} history rows; "+('original VTK available' if r['original_VTK'] else 'original printed result table'),46,y-7,size=9)
y=txt('<b>Admission remains pending.</b> Before scoring these nonlinear cases, match the native analysis and controls to each output, establish the displacement/imperfection convention, verify load and material overrides, and set justified tolerances. A source label or valid CAD file alone is insufficient.',42,y-17)
y=txt('<b>Code_Aster review:</b> the existing 50-case pool provides 761 literal result-check blocks and 28 geometry scripts, but zero native STEP files. It remains a separate source pool; no scripts were executed and no replacement CAD was generated.',42,y-14)
y=txt('<b>What remains:</b> 116 active cases need independent reproduction; these 14 source pairs need admission work; contact, crash, forming and fatigue coverage is still absent from the active scored set. Existing tolerance values remain provisional, with new empirical support only for the two tested displacement tasks.',42,y-14)
txt('All primary references remain source-published. The new FEniCSx fields are clearly labeled validation-only. Candidate-visible benchmark inputs and hidden published answers in the frozen v1.1 release were not modified.',42,83,size=9)
c.save();shutil.copy2(pdf,p/'report.pdf')
import pymupdf
d=pymupdf.open(pdf);render=root/'cvpr2027/tmp/cadfem-followup-report';render.mkdir(exist_ok=True)
for i,pg in enumerate(d):pg.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(render/f'page-{i+1}.png')
print(pdf, len(d),'pages')
