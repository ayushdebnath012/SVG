from pathlib import Path
import json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,white
from reportlab.lib.utils import ImageReader
import pymupdf
w=Path(__file__).resolve().parents[1];p=w.parent/'cadfem-contact-followup-20261014';a=json.loads((p/'assessment.json').read_text());tmp=w/'tmp/contact-followup-report';tmp.mkdir(exist_ok=True)
sys.path.insert(0,str(w/'scripts/cadfem_bench'));import common as C;from render import triangles
s=p/'original-sources/extracted-original';T=np.array([t for n in ['Lower_tube','Upper_tube'] for _,t in triangles(C.read_shape(s/(n+'.brep')))])
f=np.load(p/'validation/comparison/source-original-nodal-fields.npz');x=f['coords_mm'];vm=f['VM_MPa'];lo=x.min(0);hi=x.max(0);center=(lo+hi)/2;r=max(hi-lo)/2
fig=plt.figure(figsize=(10,4.5));axs=[fig.add_subplot(121,projection='3d'),fig.add_subplot(122,projection='3d')]
axs[0].add_collection3d(Poly3DCollection(T,facecolor='#6d90a2',edgecolor='none'));sc=axs[1].scatter(*x.T,c=vm,s=1,cmap='inferno',vmin=0,vmax=vm.max(),rasterized=True);fig.colorbar(sc,ax=axs[1],shrink=.62,pad=.09,label='Published von Mises (MPa)')
for ax,title in zip(axs,['Original CAD surfaces','Original saved FEM results']):
 for k,fn in enumerate([ax.set_xlim,ax.set_ylim,ax.set_zlim]):fn(center[k]-r,center[k]+r)
 ax.set_box_aspect((1,1,1));ax.view_init(elev=17,azim=-63);ax.set_title(title,fontsize=11);ax.set_xlabel('x (mm)',fontsize=8);ax.set_ylabel('y (mm)',fontsize=8);ax.set_zlabel('z (mm)',fontsize=8);ax.tick_params(labelsize=7)
fig.subplots_adjust(left=.01,right=.93,bottom=.05,top=.92,wspace=.17);fig.savefig(tmp/'original-cad-and-fields.png',dpi=180);plt.close(fig)
rows=a['mesh_refinement'];fig,ax=plt.subplots(figsize=(7,3.2));ax.plot([v['shell_elements'] for v in rows],[v['max_displacement_mm'] for v in rows],marker='o',label='Actual validation solves');ax.axhline(a['source_correspondence']['source_max_displacement_mm'],color='#bb6049',linestyle='--',label='Original saved source value');ax.set(xlabel='S3 shell elements',ylabel='Maximum displacement (mm)');ax.grid(alpha=.18);ax.legend(frameon=False,fontsize=9);fig.tight_layout();fig.savefig(tmp/'refinement.png',dpi=170);plt.close(fig)
PDF=w/'output/pdf/cadfem-contact-followup-20261014.pdf';c=canvas.Canvas(str(PDF),pagesize=(595,842));c.setTitle('CADFEM contact source validation follow-up');style=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=15,textColor=HexColor('#253c47'))
def para(txt,y):
 q=Paragraph(txt,style);ww,hh=q.wrap(511,700);q.drawOn(c,42,y-hh);return y-hh

def page(title,n):
 c.setFillColor(HexColor('#132f40'));c.rect(0,779,595,63,fill=1,stroke=0);c.setFillColor(white);c.setFont('Helvetica-Bold',18);c.drawString(42,803,title);c.setFont('Helvetica',9);c.setFillColor(HexColor('#6a7e89'));c.drawString(42,24,'CADFEM source validation | 14 October 2026 | local research');c.drawRightString(552,24,str(n))
page('Original contact CAD and FEM results',1)
y=para('<b>Status: held, not scored.</b> Original FreeCAD shell-to-shell contact data are preserved. No new benchmark target or engineering problem is generated. The case uses two cylindrical shell surfaces, radius 25 mm and length 500 mm; shell thickness is 0.5 mm.',753)
c.drawImage(ImageReader(tmp/'original-cad-and-fields.png'),32,428,width=531,height=239)
y=para('<b>Published source extrema:</b> maximum displacement 69.691102 mm; maximum von Mises stress 1282.094663 MPa. These values already occur in the native saved Stats array. The figure displays the original saved stress field at 15,404 thickness-expanded shell nodes.',414)
y=para('<b>Source setup:</b> E=72,000 MPa, Poisson ratio 0.3, 5,000 N downward point load, frictionless surface-to-surface penalty contact (1,000,000), all translations fixed on the lower z=0 and upper x=475 end edges. The deck uses small-displacement elastic shells; no NLGEOM flag is set.',y-17)
y=para('<b>Resolved correspondence:</b> 7,702 input mesh nodes match the native document to 7.04e-11 mm. FreeCAD defines 1 N as 1,000 internal units, so its saved force of 5,000,000 equals the deck load of 5,000 N. Four pinned writer files were verified against their Git blob hashes.',y-17)
y=para('<b>Actual original-deck replay:</b> CalculiX 2.23 gives 69.773736 mm (0.119% above the saved value). Full displacement-field L2 difference is 0.182%; stress-field L2 difference is 2.666%. This is a replay in the same solver family, not independent-formulation validation.',y-17)
para('Source: github.com/FreeCAD/FreeCAD, tree 406063b1116a6cb872bbd92ec27c6f425a8d1f98. Original native CAD, deck, scripts and source notices are bundled for the evaluator. Native FCStd contains answers and must not be exposed to candidates.',108);c.showPage()
page('Mesh sensitivity prevents admission',2)
y=para('Five actual remeshed solves retain the source CAD surfaces and setup. The upper cylinder is partitioned in topology so Gmsh can mesh the load vertex; its surface area is asserted unchanged. These new solutions are validation evidence only.',753)
c.drawImage(ImageReader(tmp/'refinement.png'),54,440,width=487,height=223)
data=[['h (mm)','Shell elements','Max u (mm)','Max stress (MPa)']]+[[f"{v['h_mm']:.5g}",str(v['shell_elements']),f"{v['max_displacement_mm']:.6f}",f"{v['max_vonMises_MPa']:.3f}"] for v in rows]
t=Table(data,colWidths=[85,135,140,151],rowHeights=23);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e5eef3')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),9),('TEXTCOLOR',(0,0),(-1,-1),HexColor('#253c47')),('ALIGN',(0,0),(-1,-1),'RIGHT'),('LINEBELOW',(0,0),(-1,0),.5,HexColor('#a3b6c1'))]));t.wrapOn(c,511,300);t.drawOn(c,42,286)
y=para('<b>Hold decision:</b> the finest displacement is 20.46% above the saved reference. The last mesh change is 5.02%, and the previous change 6.79%. The existing admission rule requires the last change below 1%, previous below 2%, and a justified reference band within 10%. Peak stress also rises substantially. No acceptance band is widened to admit the case.',264)
y=para('<b>Open-shell geometry gate:</b> analytic cylinder axes/radii and Boolean surface coverage replace a solid-volume check. The unchanged original CAD export passes; a 3% scaled test-only copy fails. This standalone validator does not approve normals, setup, mesh, fields or convergence.',y-15)
para('<b>Outcome:</b> force units, mesh/result correspondence and shell-geometry checking are resolved. The source remains evaluator-only and unscored because mesh convergence and physical validity are not established. Existing benchmark releases are unchanged. No frontier-model or human expert run is claimed.',y-15)
c.save();(p/'report').mkdir(exist_ok=True)
import shutil;shutil.copy2(PDF,p/'report'/PDF.name)
d=pymupdf.open(PDF)
for i,pg in enumerate(d):pg.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(tmp/f'page-{i+1}.png')
print(PDF,'pages',len(d))
