"""Adaptive discovery round: non-conic sections through toroidal pipe stock."""
import argparse,copy,hashlib,json,math
from pathlib import Path
import numpy as np
import contourpy
import cad_hard_geometry as h
import cad_astra_benchmark as core

DESC='''Make section A-A of a curved hollow pipe (a complete toroidal ring), including the stated drilled access port. Global XYZ units are mm. The torus major circle lies in global XY and is centred at (0,0,0); major_radius is the distance from the origin to the circular tube centreline. The tube has circular outer radius tube_outer and inner radius tube_inner. Thus toroidal stock consists exactly of points where tube_inner^2 <= (sqrt(X^2+Y^2)-major_radius)^2+Z^2 <= tube_outer^2. Subtract each stated infinite through-cylinder whose centre axis is point_mm+t*axis and perpendicular radius is radius_mm. The section plane has origin O and orthonormal vectors u,v: (X,Y,Z)=O+x*u+y*v. Render the actual material intersection with this plane in local x,y mm, including all disconnected regions and voids. Do not substitute ellipses for the generally non-conic torus-plane curves. Follow the common SVG coordinate map. All required dimension labels are true global dimensions: major_diameter, tube_outer_diameter, tube_inner_diameter, port_diameter. No perspective projection, exploded view, flow plot or analysis field is requested.'''

def field(s,x,y):
 O=np.array(s['plane_origin_mm']);u=np.array(s['plane_u']);v=np.array(s['plane_v']);p=O[:,None,None]+u[:,None,None]*x+v[:,None,None]*y
 d=np.sqrt((np.hypot(p[0],p[1])-s['major_radius_mm'])**2+p[2]**2)
 f=np.minimum(s['tube_outer_mm']-d,d-s['tube_inner_mm'])
 for b in s['bores']:
  axis=np.array(b['axis'],float);axis/=np.linalg.norm(axis);delta=p-np.array(b['point_mm'])[:,None,None]
  dist=np.sqrt(np.maximum(0,np.sum(delta*delta,axis=0)-np.einsum('i,ijk->jk',axis,delta)**2));f=np.minimum(f,dist-b['radius_mm'])
 return f

def mask(task):
 x,y=h.grid();return field(task['spec'],x,y)>=0

def simplify(points,tol=.025):
 if len(points)<=2:return points
 a,b=points[0],points[-1];d=b-a
 if np.dot(d,d)<1e-20:distance=np.linalg.norm(points-a,axis=1)
 else:
  t=np.clip(np.einsum('ij,j->i',points-a,d)/np.dot(d,d),0,1);distance=np.linalg.norm(points-(a+t[:,None]*d),axis=1)
 k=int(np.argmax(distance))
 if distance[k]<=tol:return points[[0,-1]]
 return np.vstack([simplify(points[:k+1],tol)[:-1],simplify(points[k:],tol)])

def profile(task,step=.1):
 axis=np.arange(-90,90+step/2,step);x,y=np.meshgrid(axis,axis);f=field(task['spec'],x,y)
 curves=contourpy.contour_generator(x=axis,y=axis,z=f).lines(0)
 return [simplify(p) for p in curves]

def dims(s):return dict(major_diameter=2*s['major_radius_mm'],tube_outer_diameter=2*s['tube_outer_mm'],tube_inner_diameter=2*s['tube_inner_mm'],port_diameter=2*s['bores'][0]['radius_mm'])

def oracle(task):
 d=' '.join(h.poly_path(p) for p in profile(task));labels=''.join(f'<text x="30" y="{65+25*i}" font-size="17" data-dimension="{k}">{k}: {v} mm</text>' for i,(k,v) in enumerate(task['dimensions'].items()))
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000"><rect width="1000" height="1000" fill="white"/><g data-geometry="part" transform="translate(500,500) scale(4,-4)"><path d="{d}" fill="black" fill-rule="evenodd"/></g><text x="30" y="30" font-size="21">Toroidal pipe — oblique section A-A</text>{labels}</svg>'

def build(out):
 if (out/'tasks.json').exists():raise ValueError('Frozen pool exists')
 out.mkdir(parents=True,exist_ok=True)
 base=dict(major_radius_mm=42.,tube_outer_mm=17.,tube_inner_mm=11.,plane_origin_mm=[3,-2,8],plane_u=[.8,.6,0],plane_v=[-.36,.48,.8],bores=[dict(point_mm=[38,8,0],axis=[.25,-.2,1],radius_mm=4.)])
 edit=copy.deepcopy(base);edit.update(tube_inner_mm=12.5,plane_origin_mm=[-4,5,11]);edit['bores'][0].update(point_mm=[33,15,0],radius_mm=5.)
 tasks=[]
 source=dict(spec=base,dimensions=dims(base))
 for mode,spec in [('generate',base),('edit',edit)]:
  task=dict(id='toroidal_pipe_section_'+mode,kind='torus_section',family='toroidal_pipe_section',mode=mode,spec=spec,dimensions=dims(spec))
  prompt=DESC+'\n'
  if mode=='generate':prompt+='Specification:\n'+json.dumps(spec)
  else:prompt+='Original specification:\n'+json.dumps(base)+'\nOriginal SVG:\n'+oracle(source)+'\nEDIT: increase tube_inner from 11 to 12.5, move section plane origin to (-4,5,11), move port axis point to (33,15,0) and radius to 5; preserve all other parameters. Recompute the material section and labels. Target specification:\n'+json.dumps(spec)
  task['prompt']=prompt;task['reference_mask_sha256']=hashlib.sha256(mask(task).tobytes()).hexdigest();tasks.append(task);(out/(task['id']+'.reference.svg')).write_text(oracle(task))
 core.write_json(out/'tasks.json',dict(version='cad-torus-section-v1',system=h.SYSTEM,scope='Oblique section of toroidal hollow pipe with access port; non-conic CAD boundaries, no field plots.',criteria=dict(boundary_tolerance_mm=.5,residual_mismatch_area_mm2=2.,dimension_tolerance_mm=.1,selection='Three evaluable independent samples including two high-effort; at least two drawing failures including a high-effort failure; identified visual/evidence review. Truncation, API and format excluded.'),tasks=tasks))
 core.write_json(out/'selection_policy.json',dict(rule='Three evaluable independent samples including two high-effort; at least two drawing failures including a high-effort failure; identified visual/evidence review. Truncation, API and format excluded.',screen=dict(effort='medium',cap=16000,samples=1),confirmation=dict(effort='high',cap=32000,samples=2),adaptive_discovery='New geometry family after the preceding six-task pool passed; same geometric tolerance, no threshold tuning.'))
 print('Built',len(tasks))

def score(task,text):
 # Pass the family-specific reference explicitly; never change global scorer state.
 return h.score(task,text,reference=mask(task))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=core.ROOT/'data/cad-torus-sections');build(p.parse_args().output)
