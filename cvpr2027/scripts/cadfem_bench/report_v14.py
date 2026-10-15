from pathlib import Path
import argparse,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import pymupdf

ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--pdf',type=Path,required=True);a=ap.parse_args();p=a.package;v=json.loads((p/'evaluator/validation.json').read_text());tmp=p.parent/'cvpr2027/tmp/v1.4-report';tmp.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(__file__).parent));import common as C;from render import triangles
# Inspect original shell surfaces directly, never generate/export benchmark CAD.
src=p/'evaluator/source-review/freecad-contact/extracted-original';T=np.array([t for n in ['Lower_tube','Upper_tube'] for _,t in triangles(C.read_shape(src/(n+'.brep')))])
fig=plt.figure(figsize=(5.5,3.4));ax=fig.add_subplot(111,projection='3d');ax.add_collection3d(Poly3DCollection(T,facecolor='#60849a',edgecolor='none'));pts=T.reshape(-1,3);lo=pts.min(0);hi=pts.max(0);center=(lo+hi)/2;r=max(hi-lo)/2
for k,fn in enumerate([ax.set_xlim,ax.set_ylim,ax.set_zlim]):fn(center[k]-r,center[k]+r)
ax.set_box_aspect((1,1,1));ax.view_init(20,-56);ax.set_axis_off();fig.subplots_adjust(0,0,1,1);fig.savefig(tmp/'contact.png',dpi=170);plt.close(fig)
records=json.loads((p/'evaluator/runtime-validation/solver-job-002/outputs/refinement.json').read_text())['meshes'];fig,ax=plt.subplots(figsize=(6,2.7),layout='constrained');ax.plot([r['elements'] for r in records],[r['outputs']['max_displacement_mm'] for r in records],'o-');ax.set_xlabel('Tetrahedral elements');ax.set_ylabel('Maximum displacement (mm)');ax.set_title('Actual sandboxed serial-solver replay');ax.grid(alpha=.2);fig.savefig(tmp/'baseline.png',dpi=170);plt.close(fig)
a.pdf.parent.mkdir(parents=True,exist_ok=True);c=canvas.Canvas(str(a.pdf),pagesize=(595,842));st=ParagraphStyle('p',fontName='Helvetica',fontSize=10,leading=14,textColor=HexColor('#253a4d'))
def text(s,x,y,w=505,size=10):
 q=Paragraph(s,ParagraphStyle('p',parent=st,fontSize=size,leading=size*1.38));_,h=q.wrap(w,750);q.drawOn(c,x,y-h);return y-h

def page(title,n):
 c.setFillColor(HexColor('#18364d'));c.rect(0,785,595,57,fill=1,stroke=0);c.setFillColor(HexColor('#ffffff'));c.setFont('Helvetica-Bold',18);c.drawString(42,807,title);c.setFillColor(HexColor('#5f7180'));c.setFont('Helvetica',8);c.drawString(42,23,'CADFEM-Bench v1.4 | 14 October 2026 | local research pilot');c.drawRightString(553,23,str(n))
def pic(f,x,y,w,h):
 im=ImageReader(str(f));iw,ih=im.getSize();scale=min(w/iw,h/ih);c.drawImage(im,x+(w-iw*scale)/2,y+(h-ih*scale)/2,iw*scale,ih*scale)
page('Balanced primary evaluation',1)
y=text('<b>41 tasks / 86 published outputs / 10 family labels.</b> Each family contributes at most five tasks. The three bracket/holed-plate families contribute 15/41 tasks (36.6%), compared with 84/126 (66.7%) in v1.3.',42,757)
y=text('<b>35 supplied-CAD tasks and 6 reconstruction tasks.</b> Six NAFEMS calibration tasks are separate. The complete 126-task source pool is retained for provenance; it is not the primary leaderboard.',42,y-14)
for fam,n in v['by_family'].items():y=text(f"{fam}: <b>{n}</b>",48,y-8,size=10)
y=text('<b>Reservation:</b> 78 public-source cases are outside candidate inputs; one additional task shares primary CAD and is listed as related. Exact CAD hashes are disjoint between primary and reserved suites, but related designs and public training exposure remain possible.',42,y-23)
y=text('<b>Readiness:</b> 10/41 primary tasks are independently reproduced; 31 are not. The full pool has 16 reproduced tasks. No new model trial or human expert baseline is claimed.',42,y-15)
text('Forty-one tasks are not forty-one independent mechanical problems. Family labels, CAD variants, load cases and tracks are reported separately. Source-specific licences remain in force; do not publish the full package.',42,92,size=9);c.showPage()
page('Tested sandbox and field checks',2)
y=text('<b>Kernel restrictions tested:</b> evaluator reads, another-release reads, writes outside the job, input changes and outbound network are denied. A nonterminating program is killed at the wall-time limit. Inputs/source are frozen and all run/artifact identities are recorded.',42,757)
y=text('<b>Real software baseline:</b> original coupler CAD was remeshed and solved on three meshes inside the macOS sandbox using Gmsh, scikit-fem and SciPy. Final displacement 0.007705541 mm is about 1.16% from the published 0.007617466 mm, within its existing 6% band.',42,y-15)
pic(tmp/'baseline.png',55,379,485,210)
y=text('<b>Independent field check:</b> rebuilding the elasticity operator gives a weak residual of 9.15e-13. Multiplying the field by 1.001 gives approximately 9.99e-4 and fails. This checks actual submitted arrays, not a claimed residual in a log.',42,362)
y=text('<b>Limits:</b> boundary tags are not yet fully checked against CAD faces; geometry/setup and convergence approval still require review. The three-mesh baseline is an execution/consistency test, not a new convergence certification. Correct answers alone remain insufficient for an end-to-end pass.',42,y-15)
y=text('<b>Backend scope:</b> local macOS mode denies home/package data, network and out-of-job writes, but permits system data outside home. Docker mode requires a preinstalled digest-pinned image and is prepared, not tested on this machine. Neither missing backend falls back to unrestricted execution.',42,y-15)
text('Standard replay budget: 600 s wall time, 600 s CPU per process, observed process-group RAM 8192 MB, two numerical threads, one attempt and no automatic retry. Exact model/provider/version and generation costs must be recorded outside the sandbox.',42,80,size=9);c.showPage()
page('New contact source data, held for review',3)
pic(tmp/'contact.png',55,440,485,305)
y=text('<b>Original FreeCAD shell-contact example.</b> Two native cylindrical-shell BREP surfaces, an original CalculiX deck and saved native result arrays for 15,404 nodes. The geometry above is a read-only tessellation of those source surfaces, not a generated engineering problem.',42,425)
y=text('The pinned creation script and deck specify 5000 N, E = 72000 MPa and 0.5 mm shell thickness. Contact is frictionless, surface-to-surface, with a linear normal penalty. The source static step does not enable large-deformation geometry.',42,y-15)
y=text('<b>Not admitted:</b> legacy serialized force units and exact saved-output correspondence need verification; the solid-only scorer needs a shell-specific geometry gate; no independent contact replay or convergence study is established. Large displacement/high stress do not establish physical validity.',42,y-15)
y=text('The solid-to-solid companion provides CAD/setup but no saved result arrays. It is not counted as a CAD+FEM result pair. Original files, Git blob hashes, SHA-256, input decks and read-only extracted arrays are retained under source-review.',42,y-15)
text('Primary source: github.com/FreeCAD/FreeCAD, pinned tree 406063b1116a6cb872bbd92ec27c6f425a8d1f98. No third-party macros or source programs were executed.',42,79,size=9);c.showPage()
page('Precise status of the remaining limitations',4)
y=756
for title,body in [('Balance','Fixed: capped primary suite, separate calibration and family macro-averages.'),('Release labels','Fixed: current scorer reports 1.4; readiness distinguishes primary and full-pool counts.'),('Execution sandbox','Tested for the local serial CAD/FEM runtime; portable Docker backend still needs a validated image/runtime.'),('Automatic physics','Partial: equilibrium/extraction checker for cycloidal quadratic-tet fields; complete geometry/setup/convergence verification remains unfinished.'),('Trustworthy targets','Partial: 10 primary tasks have independent reproduction evidence; 31 still need it. Most bands remain provisional or empirical.'),('Complex physics','Research pending: contact source pair added but held. Plasticity, fracture, forming, crash and fatigue are not independently admitted primary cases.'),('Hold-out contamination','Public-source cases are reserved from prompts. Web crawling cannot establish an unpublished private hold-out or exclude pretraining exposure.'),('Model/expert pilots','No API model runs or human expert study performed. A real trusted software solver replay is provided separately.')]:
 y=text('<b>'+title+':</b> '+body,42,y)-18
text('The release fixes concrete packaging and execution weaknesses without fabricating validation. It remains a research pilot. v1.3 is preserved, source targets are unchanged, and held/unsupported cases cannot silently become automatic workflow passes.',42,95,size=9)
c.save();(p/'report').mkdir(exist_ok=True)
import shutil;shutil.copy2(a.pdf,p/'report'/a.pdf.name)
d=pymupdf.open(a.pdf)
for i,pg in enumerate(d):pg.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(tmp/f'page-{i+1}.png')
print(a.pdf,len(d),'pages')
