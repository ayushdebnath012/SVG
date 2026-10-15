from pathlib import Path
import json,csv
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import pymupdf
D=Path('cvpr2027/data/web-cad-fem-multiphysics');T=Path('cvpr2027/tmp/cad-fem-fracture-search');O=Path('cvpr2027/output/pdf/web-fem-multiphysics-candidates.pdf');cat=json.loads((D/'catalog.json').read_text())
p=D/'capriccio-fracture/MD1e6/output/fe-md-simulation-400.vtu';r=vtk.vtkXMLUnstructuredGridReader();r.SetFileName(str(p));r.Update();g=r.GetOutput();pts=vtk_to_numpy(g.GetPoints().GetData());u=vtk_to_numpy(g.GetPointData().GetArray('u'));val=np.linalg.norm(u,axis=1);ok=np.isfinite(val)
fig,ax=plt.subplots(figsize=(7,3));ax.scatter(pts[~ok,0],pts[~ok,1],s=2,c='#cbd5e1',label='Nonfinite field entries');im=ax.scatter(pts[ok,0],pts[ok,1],c=val[ok],s=4,cmap='viridis');fig.colorbar(im,ax=ax,label='|u|, original source units');ax.set_aspect('equal');ax.set_xlabel('Source x coordinate');ax.set_ylabel('Source y coordinate');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(T/'fracture-reference.png',dpi=180);plt.close(fig)
a=np.genfromtxt(D/'digimat-thermomechanical/30C14hr_80C10hr_FEA_data.csv',delimiter=',',names=True)
fig,axs=plt.subplots(1,2,figsize=(7,2.7));axs[0].plot(a['Time']/3600,a['DoC']);axs[0].set_ylabel('Degree of cure');axs[1].plot(a['Time']/3600,a['Etot'],label='Total strain');axs[1].plot(a['Time']/3600,a['ECH11'],label='Chemical shrinkage');axs[1].legend(fontsize=7)
for ax in axs:ax.set_xlabel('Source time / 3600');ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(T/'cure-history.png',dpi=180);plt.close(fig)
styles=getSampleStyleSheet();styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;story=[]
def P(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,6))
def H(t):story.append(Paragraph(t,styles['Heading1']));story.append(Spacer(1,6))
def table(rows,widths):
 tb=Table([[Paragraph(str(c),styles['BodyText']) for c in row] for row in rows],colWidths=widths);tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#cbd5e1'))]));story.append(tb);story.append(Spacer(1,12))
H('New published multiphysics source candidates')
P('12 October 2026 | Original web downloads only | No local CAD creation, FEM solves or model trials')
P('<b>Admission result:</b> three native Abaqus CAE / published numerical-reference candidates downloaded. No newly verified, redistributable native CAD/BREP + FEM pair. One additional native FreeCAD + FEM case verified locally but excluded from source redistribution due to its file license metadata. No original dimensioned engineering drawings verified.')
H('Coupled FEM / MD polymer fracture')
P('Felix Weber, Zenodo 18355528, CC BY 4.0. Two cases: MD1e6 and MD4e6. Native GTPm.cae, input deck, Julia/LAMMPS inputs and 54 saved coupled FE/MD VTU frames downloaded as original archive members, each source CRC verified. Native CAE geometric parts have not been independently inspected; no STEP/BREP is verified.')
story.append(Image(str(T/'fracture-reference.png'),width=490,height=210));P('<b>Published FEM reference visualization, not a CAD drawing:</b> original coordinates and displacement values from MD1e6 increment 400. Grey points have nonfinite field values. No deformation or reference solution generated locally.')
table([['Case','Frames / points','Saved point fields'],['MD1e6','20 / 2868','u: 3 components; uforces: 3; stress: 9'],['MD4e6','34 / 20109','u: 3 components; uforces: 3; stress: 9']],[105,135,250])
P('All frames contain nonfinite field entries at 1086 or 4566 points respectively. Source region masks and units need review; do not silently replace these entries or score all nodes. MD initial data and potentials are not in this selected package. Increment filenames are not certified physical times. These are two cases in one family, not 54 independent tasks.')
P('Source: <link href="https://zenodo.org/records/18355528" color="blue">https://zenodo.org/records/18355528</link>')
story.append(PageBreak());H('Resin curing and thermomechanical strain')
P('Jesper Kjaer Jorgensen / Technical University of Denmark, Zenodo 10025292, CC BY 4.0. Eight original files with publisher MD5 checks, including native Box3D_TE.cae, journal, material files, temperature schedule and published FEA CSV. Complex cure/material physics on a simple box specimen, not a complex CAD drawing.')
story.append(Image(str(T/'cure-history.png'),width=465,height=170));P('Plots show unchanged published CSV values. 1910 finite rows; reference strain history is sampled at the source X1Y1 set, not a full nodal solution.')
r=cat['records'][2];table([['Published reference','Final value'],['Degree of cure','0.994059324265'],['Total strain','-0.004613536'],['Chemical shrinkage strain','-0.00388499489054']],[280,210])
P('Native CAE/journal naming (TE versus TVE) and material-state correspondence need inspection. Replay requires Abaqus and Digimat material coupling. The extraction script contains an apparent endpoint error and has not been executed locally.')
P('Source: <link href="https://zenodo.org/records/10025292" color="blue">https://zenodo.org/records/10025292</link>')
H('Verified local example and held leads')
P('<b>Bimetal strip:</b> native FreeCAD geometry imports as two valid solids; 21 published transient VTU frames contain finite displacement, stress and temperature fields at 4072 points. Simple geometry, one coupled thermal/mechanical case. Original FCStd license field says All rights reserved. Data files are omitted from the shared ZIP; source links and audit summaries remain.')
P('<b>Tapered springs:</b> original ODB and CAD-building scripts downloaded; no prebuilt CAD supplied. Experimental CSV is kept distinct from FEM results. <b>SOFA soft actuator:</b> OBJ geometry and scripts downloaded, but no saved numerical FEM fields; not counted.')
P('Sources: FreeCAD documentation Macro_export_transient_FEM_results; Zenodo 14998785 (tapered springs); Zenodo 7838026 (soft actuator). Exact links and inventories are in the catalog and README.')
P('<b>Benchmark use:</b> keep candidates separate from admitted cases. Drawing-to-CAD-to-FEM receives no new qualified drawing; supplied-CAD-to-FEM admission awaits native geometry, source correspondence, region/unit and replay checks. No model accuracy scores have been measured.')
def footer(c,d):c.setFont('Helvetica',8);c.setFillColor(colors.grey);c.drawString(45,25,'Web-sourced originals; reference diagnostics are not certified model scores');c.drawRightString(550,25,str(d.page))
SimpleDocTemplate(str(O),pagesize=(595,842),leftMargin=45,rightMargin=45,topMargin=35,bottomMargin=45).build(story,onFirstPage=footer,onLaterPages=footer)
d=pymupdf.open(O);print('PDF',len(d),'pages')
for i,page in enumerate(d):page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(T/f'report-{i+1}.png')
