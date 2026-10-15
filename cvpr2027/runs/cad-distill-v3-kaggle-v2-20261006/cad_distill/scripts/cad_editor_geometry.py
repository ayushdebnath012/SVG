"""CAD-Editor 6-bit sketch/extrude decoding into CadQuery/OCP solids.

Conventions follow Microsoft's MIT CAD-Editor utils/parse_seq2obj.py and
obj_reconverter.py: 6-bit dequantization; ext_v/T range [-1,1]; sketch scale
[0,1.4], offset [-.9,.9]; R stores x,y,z basis vectors. No model code executes.
This adapter does not establish physical units for the normalized dataset.
"""
import numpy as np
import cadquery as cq
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec
from cad_edit_contracts import validate_sequence

def dq(v,lo,hi):return np.asarray(v,dtype=np.float32)*(hi-lo)/63+lo

def execute_sequence(sequence):
 sequence=' '.join(sequence.split());validate_sequence(sequence);result=None
 for feature in sequence.split('<extrude_end>'):
  if not feature.strip():continue
  sketch,ext=feature.split('<sketch_end>');parts=ext.strip().split(',');op=parts[0];p=list(map(int,parts[1:]));bounds=dq(p[:2],-1,1);origin=dq(p[2:5],-1,1);R=np.array(p[5:14],dtype=float).reshape(3,3).T
  if not np.allclose(R.T@R,np.eye(3)) or np.linalg.det(R)<.999:raise ValueError('Nonorthonormal frame')
  if bounds[1]<=bounds[0]:raise ValueError('Invalid extrusion interval')
  scale=float(dq(p[14],0,1.4));offset=dq(p[15:17],-.9,.9);normal=R[:,2]
  def point(xy):
   xy=dq(xy,-1,1)*scale+offset;return cq.Vector(*(R@np.r_[xy,0]+origin))
  bodies=[]
  for face in sketch.split('<face_end>'):
   if not face.strip():continue
   wires=[]
   for loop in face.split('<loop_end>'):
    if not loop.strip():continue
    curves=[c.strip().split(',') for c in loop.split('<curve_end>') if c.strip()];edges=[]
    for i,c in enumerate(curves):
     nums=list(map(int,c[1:]));nxt=curves[(i+1)%len(curves)]
     if c[0]=='line':edges.append(cq.Edge.makeLine(point(nums[:2]),point(list(map(int,nxt[1:3])))))
     elif c[0]=='arc':edges.append(cq.Edge.makeThreePointArc(point(nums[:2]),point(nums[2:4]),point(list(map(int,nxt[1:3])))))
     elif c[0]=='circle':
      if len(curves)!=1:raise ValueError('Circle mixed with other loop curves')
      pts=dq(np.array(nums).reshape(4,2),-1,1);centre=np.array([(pts[0,0]+pts[1,0])/2,(pts[2,1]+pts[3,1])/2]);rad=(np.linalg.norm(pts[0]-pts[1])+np.linalg.norm(pts[2]-pts[3]))/4*scale
      centre=R@np.r_[centre*scale+offset,0]+origin;edges.append(cq.Edge.makeCircle(float(rad),cq.Vector(*centre),cq.Vector(*normal)))
    wires.append(cq.Wire.assembleEdges(edges))
   f=cq.Face.makeFromWires(wires[0],wires[1:]).translate(cq.Vector(*(normal*float(bounds[0]))))
   prism=BRepPrimAPI_MakePrism(f.wrapped,gp_Vec(*(normal*float(bounds[1]-bounds[0])))).Shape();bodies.append(cq.Shape.cast(prism))
  body=bodies[0]
  for b in bodies[1:]:body=body.fuse(b,tol=1e-5)
  if result is None:
   if op!='add':raise ValueError('First feature must add material')
   result=body
  elif op=='add':result=result.fuse(body,tol=1e-5)
  elif op=='cut':result=result.cut(body,tol=1e-5)
  else:result=result.intersect(body,tol=1e-5)
  if not result.isValid():raise ValueError('Invalid construction solid')
 if result is None or not result.Solids() or result.Volume()<=0:raise ValueError('Empty or invalid solid')
 return result
