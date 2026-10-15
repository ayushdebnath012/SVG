"""Complete evaluator atlas: actual CAD/source drawings, published results and provenance.
Visualize original saved fields only. No benchmark geometry, target or simulated field is synthesized.
"""
import argparse,collections,hashlib,json,shutil,struct,sys,zipfile,xml.etree.ElementTree as E
from pathlib import Path
from html import escape
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pymupdf
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,white
from reportlab.lib.utils import ImageReader
import common as C
from render import render

ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--pdf',type=Path,required=True);a=ap.parse_args();p=a.package.resolve();ev=p/'evaluator';figs=p/'report/figures';figs.mkdir(parents=True,exist_ok=True);tmp=p.parent/'cvpr2027/tmp/v17-atlas';tmp.mkdir(parents=True,exist_ok=True)
tasks=[json.loads(l) for l in (p/'candidate/tasks.jsonl').read_text().splitlines()];refs={r['task_id']:r for r in [json.loads(l) for l in (ev/'references.jsonl').read_text().splitlines()]};v=json.loads((ev/'validation.json').read_text());review=json.loads((ev/'source-review/complex-engineering/index.json').read_text());log={}
style=ParagraphStyle('body',fontName='Helvetica',fontSize=9,leading=13,textColor=HexColor('#253b47'));small=ParagraphStyle('small',parent=style,fontSize=8,leading=11)

def unv(text):
 lines=text.splitlines();j=next(i for i in range(len(lines)-1) if lines[i].strip()=='-1' and lines[i+1].strip()=='2411')+2;d={}
 while lines[j].strip()!='-1':d[int(lines[j].split()[0])]=[float(x.replace('D','E')) for x in lines[j+1].split()];j+=2
 return d

def field_image(t,r):
 dest=figs/(t['task_id']+'-published-field.png')
 fam=t['family'];paths=[ev/x for x in r['evidence_files']]
 if fam=='agentfem-bracket':
  f=next(x for x in paths if x.name=='fields.npz');q=np.load(f,allow_pickle=False);x=q['points']*1000;u=np.linalg.norm(q['displacement'],axis=1)*1000;assert np.isclose(u.max(),r['references']['max_displacement_mm']['value'],rtol=1e-7);label='Published displacement (mm)'
 elif fam=='geopinonet-holed-plate':
  f=next(x for x in paths if x.name.endswith('_lateral_bending.csv'));q=np.loadtxt(f,delimiter=',',skiprows=1);x=q[:,:3]*1000;u=np.linalg.norm(q[:,3:6],axis=1)*1000;assert np.isclose(u.max(),r['references']['max_displacement_lateral_mm']['value'],rtol=1e-7);label='Published lateral displacement (mm)'
 elif fam in ['cycloidal-drive-components','cadworld-freecad-fem']:
  f=next(x for x in paths if x.suffix=='.FCStd' and ('precondition' not in str(x)))
  with zipfile.ZipFile(f) as z:
   root=E.fromstring(z.read('Document.xml'));obj=next(o for o in root.findall('.//ObjectData/Object') if o.find('./Properties/Property[@name="DisplacementLengths"]') is not None)
   name=obj.find('./Properties/Property[@name="DisplacementLengths"]/FloatList').get('file');b=z.read(name);n=struct.unpack('<I',b[:4])[0];u=np.frombuffer(b[4:],'<f8');assert len(u)==n
   ids=[int(i.get('v')) for i in obj.findall('./Properties/Property[@name="NodeNumbers"]/IntegerList/I')];link=obj.find('./Properties/Property[@name="Mesh"]/Link').get('value');m=root.find(f'.//ObjectData/Object[@name="{link}"]/Properties/Property[@name="FemMesh"]/FemMesh').get('file');nodes=unv(z.read(m).decode());x=np.array([nodes[i] for i in ids]);assert len(x)==len(u)
   if 'max_displacement_mm' in r['references']:assert np.isclose(u.max(),r['references']['max_displacement_mm']['value'],rtol=1e-5)
  label='Published displacement (mm)'
 else:
  images=[f for f in paths if f.suffix.lower() in ['.png','.jpg','.jpeg'] and f.is_file()]
  if images:return images[0],'Original published FEM figure'
  return None,'Published numerical results below; no field plot bundled'
 fig=plt.figure(figsize=(4.2,3.2),dpi=160);ax=fig.add_subplot(111,projection='3d');step=max(1,len(u)//30000);q=ax.scatter(*x[::step].T,c=u[::step],s=1.1,cmap='viridis',vmin=0,vmax=u.max(),rasterized=True);lo=x.min(0);hi=x.max(0);c=(lo+hi)/2;rad=(hi-lo).max()/2
 for k,fn in enumerate([ax.set_xlim,ax.set_ylim,ax.set_zlim]):fn(c[k]-rad,c[k]+rad)
 ax.set_box_aspect((1,1,1));ax.view_init(24,-58);ax.set_axis_off();fig.colorbar(q,ax=ax,shrink=.62,pad=.03,label=label);fig.subplots_adjust(0,0,1,.96);fig.savefig(dest,facecolor='white');plt.close(fig);return dest,label

def image_path(f,dest):
 if f.suffix.lower()=='.pdf':
  d=pymupdf.open(f);d[0].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(dest);return dest
 if f.suffix.lower()=='.gif':
  im=Image.open(f);im.seek(0);im.convert('RGB').save(dest);return dest
 return f

c=canvas.Canvas(str(a.pdf),pagesize=(595,842));c.setTitle('CADFEM-Bench v1.7 - complete CAD and published FEM results atlas');pg=0

def para(text,y,sz=9,width=511,x=42):
 st=style if sz==9 else small;q=Paragraph(text,st);_,h=q.wrap(width,760);q.drawOn(c,x,y-h);return y-h

def page(title,subtitle=''):
 global pg;pg+=1;c.setFillColor(HexColor('#153446'));c.rect(0,774,595,68,fill=1,stroke=0);c.setFillColor(white);c.setFont('Helvetica-Bold',16);c.drawString(42,805,title[:65]);c.setFont('Helvetica',8);c.drawString(42,787,subtitle[:110]);c.setFillColor(HexColor('#738691'));c.drawString(42,24,'CADFEM-Bench v1.7 | evaluator-only atlas | 14 October 2026');c.drawRightString(552,24,str(pg))

def img(f,x,y,w,h):
 im=ImageReader(str(f));iw,ih=im.getSize();scale=min(w/iw,h/ih);c.drawImage(im,x+(w-iw*scale)/2,y+(h-ih*scale)/2,width=iw*scale,height=ih*scale,mask='auto')

def table(data,y,widths):
 rows=[[Paragraph(escape(str(x)),small) for x in row] for row in data];t=Table(rows,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e7eef3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.5,HexColor('#a4b7c2'))]));_,h=t.wrap(511,760);t.drawOn(c,42,y-h);return y-h

page('Complete CAD and FEM results atlas','Source-backed pilot; no model ranking or engineering certification claimed')
y=para('<b>54 primary tasks / 118 published targets / 11 family labels.</b> Track A: 51 supplied-CAD tasks. Track B: three drawing/specification tasks. Fourteen primary tasks have independent reproduction evidence; 40 do not.',753)
y=table([['Suite','Tasks','Purpose'],['Primary','54','Comparison; cap eight per family'],['Calibration','7','NAFEMS and tensile controls; separate scoring'],['Reserved public','63','Evaluator-only public cases; possible prior exposure'],['Related public','1','Shares primary CAD; separate score'],['Held','58','Not scored; input data and reasons retained'],['Complex source review','6 collections + contact pair','Original CAD/results with unresolved admission checks']],y-19,[150,60,301])
y=para('<b>Active source-backed pool:</b> 125 tasks across the four active suites. Multiple load branches or mode values are outputs of one task, not additional task counts. Family labels do not imply independent engineering problems.',y-22)
y=table([['Engineering family','Primary tasks'],*[[k,str(n)] for k,n in sorted(v['by_engineering_family'].items())]],y-17,[431,80])
assert y>62,y;para('This atlas contains reference answers and is evaluator-only. Give a model candidate/ or a task-specific export, never this atlas or the full archive.',54,8);c.showPage()
page('What is and is not validated','Artifact contract, data origin and evaluation scope')
y=753
for title,body in [
 ('CAD origin','Track A uses published source CAD or previously documented format/unit conversions. Existing FEMCAD B-task solids are hidden evaluator reconstructions from the source specification, explicitly labeled. No new CAD input or target is synthesized in this release.'),
 ('Source-only correction','Four v1.5 interface-crack tasks are held because their supplied CAD was constructed locally; several G references were locally calculated from published factors. Two analytic-reference tasks and one unresolved publisher-output task are also held. The source-CAD plastic-collapse ring remains admitted.'),
 ('Separate scores','Both task tracks, every family and the fourteen-task reproduced subset are reported separately. Correct numbers alone produce zero workflow passes.'),
 ('Replay runtime','A fresh offline job freezes source and inputs. Default budgets: 600 s wall time, 600 s CPU per process, 8 GiB observed process-group RAM, two threads, one attempt. Serial CalculiX runs inside the tested macOS sandbox with an operator-trusted, read-only software prefix.'),
 ('Scope of automation','CAD reconstruction gates use proper principal-inertia and axis rotations confirmed by exact overlap. A cycloidal field-equilibrium checker are provided. Geometry/setup/fields/convergence still need trusted review where not fully checked. The portable Docker backend is prepared but untested; MPI runtimes are not certified in the macOS mode.'),
 ('Private hold-out','Reserved cases are public-source data with exact-CAD separation. That does not exclude pretraining exposure or related parametric-family overlap.'),
 ('Complex collections','Original gripper, landing-gear, crank, connecting-rod, heatsink and composite-pipe CAD/results are bundled as unscored source review, with explicit unit/setup/correspondence blockers.'),
 ('Trials and rights','Historical v1.5 GPU pilot runs are separate from this corrected release. No v1.7 model ranking or human expert study is claimed. Source notices differ; the full archive is for local research and is not automatically cleared for redistribution.')]:y=para('<b>'+title+':</b> '+body,y)-20
assert y>58,y;c.showPage()
for ix,t in enumerate(tasks):
 r=refs[t['task_id']];page(t['task_id'],t['title']);reproduced=t.get('readiness',{}).get('independently_reproduced',False);y=para('<b>Track '+t['track']+'</b> | '+escape(t['engineering_family'])+' | '+('independent reproduction evidence' if reproduced else 'no independent reproduction; provisional tolerance'),753)
 cad=next((p/'candidate'/i['path'] for i in t['inputs'] if i['role']=='cad'),None);origin='Published CAD / documented conversion'
 if cad is None:
  cad=ev/r['geometry_check']['reference_step'];origin='Hidden validator reconstruction from source spec' if t['family']=='femcad-hard' else 'Original source CAD, hidden geometry reference'
 key=hashlib.sha256(cad.read_bytes()).hexdigest()[:18];view=figs/(key+'-cad.png')
 if not view.exists():render(cad,view)
 img(view,40,487,247,217)
 field=None;caption=''
 if t['track']=='B':
  source=next((p/'candidate'/i['path'] for i in t['inputs'] if i['role'] in ['drawing','figure']),None)
  if source:field=image_path(source,figs/(t['task_id']+'-source-drawing.png'));caption='Original source drawing / diagram'
 else:
  try:field,caption=field_image(t,r)
  except Exception as e:log[t['task_id']]={'field_view_unavailable':str(e)};caption='Published scalars below; source fields not rendered'
 if field:img(field,305,487,250,217)
 else:para(escape(caption),606,8,220,319)
 para(escape(origin),478,8,250,42);para(escape(caption),478,8,240,307)
 data=[['Requested quantity','Published value','Unit','Tolerance']]
 outputs={o['key']:o for o in t['outputs']}
 for k,q in r['references'].items():
  tol=q['tol'];toltext=f"{100*tol['value']:.2g}%" if tol['kind']=='rel' else str(tol['value']);data.append([k,f"{q['value']:.9g}",outputs[k]['unit'],toltext])
 y=table(data,440,[260,110,50,91])
 body=t['prompt'].split('Outputs:')[0].strip();body=body[:690]+(' ...' if len(body)>690 else '')
 y=para('<b>Task setup (abridged):</b> '+escape(body).replace('\n',' '),y-17,8)
 prov=next(iter(r['references'].values()))['provenance'];y=para('<b>Reference provenance:</b> '+escape(prov[:210]),y-15,8)
 y=para('<b>Source:</b> '+escape(t['source']['name'])+'<br/>'+escape(t['source']['url']),y-12,8)
 assert y>45,(t['task_id'],y)
 log.setdefault(t['task_id'],{}).update(page=pg,cad=str(cad.relative_to(p)),CAD_origin=origin,published_field_or_drawing_shown=bool(field),reference_keys=list(r['references']))
 c.showPage()
 if (ix+1)%5==0:print('atlas task pages complete',ix+1,'of',len(tasks),flush=True)
for row in review:
 folder=ev/'source-review/complex-engineering'/row['collection_id'];page('Source review: '+row['collection_id'],'Original CAD/FEM collection; zero scored tasks added')
 y=para(escape(row['title'])+'<br/><b>Status: unscored source review.</b> '+escape(row['hold_reason']),753)
 cad=folder/row['cad_view'];view=figs/(row['collection_id']+'-source-cad.png');render(cad,view);img(view,40,427,515,276)
 y=para('<b>Original CAD:</b> '+escape(row['cad_view'])+'<br/><b>FEM storage:</b> '+escape(row['result_storage']),411)
 cat=json.loads((folder/'catalog.json').read_text());limits=cat.get('limitations') or cat.get('limits') or [];extra=' '.join(str(z) for z in limits)[:1000]
 if extra:y=para('<b>Source inspection notes:</b> '+escape(extra),y-17,8)
 y=para('<b>Bundled files:</b> '+str(row['published_file_count'])+' original/source-inspection files. No macro or author script is executed. Source quantities are retained in the original report/catalog; no derived solver result is admitted as a target.',y-17)
 y=para('<b>Source:</b> '+escape(row['source'] or 'See source manifest')+'<br/>Full original manifests and hold reasons are in evaluator/source-review/complex-engineering/.',y-17,8)
 assert y>50,(row['collection_id'],y);c.showPage();print('atlas source-review page complete',row['collection_id'],flush=True)
c.save()
# Append the already inspected two-page original contact/CAD/refinement report.
d=pymupdf.open(a.pdf);contact=ev/'source-review/contact-validated-followup/report/cadfem-contact-followup-20261014.pdf';d.insert_pdf(pymupdf.open(contact));tmp_pdf=a.pdf.with_name(a.pdf.stem+'-complete.tmp.pdf');d.save(tmp_pdf);d.close();tmp_pdf.replace(a.pdf)
shutil.copy2(a.pdf,p/'report'/a.pdf.name)
log['atlas']={'pages':64,'primary_task_pages':54,'complex_review_pages':6,'contact_review_pages':2,'field_images_are_original_source_data_only':True};(p/'report/atlas-index.json').write_text(json.dumps(log,indent=2)+'\n')
d=pymupdf.open(a.pdf);assert len(d)==64
for i,page in enumerate(d):page.get_pixmap(matrix=pymupdf.Matrix(1,1)).save(tmp/f'page-{i+1:03d}.png')
print('complete atlas',a.pdf,len(d),'pages',flush=True)
