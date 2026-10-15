"""Geometry gate for this source's open cylindrical shells, in supplied CAD coordinates.
Analytic cylinder axes/radii plus Boolean surface coverage; no volume-based gate.
"""
import argparse,json,math
from pathlib import Path
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepTools import BRepTools
from OCP.Bnd import Bnd_Box
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.GProp import GProp_GProps
from OCP.STEPControl import STEPControl_Reader,STEPControl_Writer,STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopAbs import TopAbs_FACE,TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS,TopoDS_Shape,TopoDS_Compound

def read(p):
 if p.suffix.lower() in ['.stp','.step']:
  r=STEPControl_Reader();assert r.ReadFile(str(p))==IFSelect_RetDone;r.TransferRoots();return r.OneShape()
 s=TopoDS_Shape();assert BRepTools.Read_s(s,str(p),BRep_Builder());return s

def compound(shapes):
 s=TopoDS_Compound();b=BRep_Builder();b.MakeCompound(s)
 for sh in shapes:b.Add(s,sh)
 return s

def area(s):
 p=GProp_GProps();BRepGProp.SurfaceProperties_s(s,p);return p.Mass()

def signatures(s):
 sig=[];exp=TopExp_Explorer(s,TopAbs_FACE)
 while exp.More():
  face=TopoDS.Face_s(exp.Current());a=BRepAdaptor_Surface(face);assert a.GetType()==GeomAbs_Cylinder,'all faces must retain analytic cylindrical surfaces'
  c=a.Cylinder();ax=c.Axis();d=[ax.Direction().X(),ax.Direction().Y(),ax.Direction().Z()];o=[ax.Location().X(),ax.Location().Y(),ax.Location().Z()]
  if next(v for v in d if abs(v)>1e-7)<0:d=[-v for v in d]
  along=sum(x*y for x,y in zip(o,d));o=[x-along*y for x,y in zip(o,d)];sig.append({'radius':c.Radius(),'axis':d,'axis_origin':o});exp.Next()
 return sig

def validate(sub,refs):
 assert BRepCheck_Analyzer(sub).IsValid(),'invalid submitted shape';assert not TopExp_Explorer(sub,TopAbs_SOLID).More(),'expected open shells, no solids'
 ref=compound([read(x) for x in refs]);a,b=area(ref),area(sub);expected=signatures(ref);actual=signatures(sub)
 def match(x,y):return abs(x['radius']-y['radius'])<=.01 and math.dist(x['axis'],y['axis'])<1e-7 and math.dist(x['axis_origin'],y['axis_origin'])<=.01
 assert all(any(match(x,y) for y in expected) for x in actual),'cylinder radius or axis mismatch';assert all(any(match(x,y) for y in actual) for x in expected),'missing source cylinder'
 co=BRepAlgoAPI_Common(ref,sub);co.Build();assert co.IsDone(),'surface Boolean failed';overlap=area(co.Shape());diff=(a+b-2*overlap)/a
 passed=abs(a-b)/a<=.001 and -1e-8<=diff<=.001
 return {'geometry_passed':bool(passed),'reference_area_mm2':a,'submitted_area_mm2':b,'overlap_area_mm2':overlap,'relative_symmetric_surface_difference':diff,'maximum_difference':.001,'analytic_radius_and_axis_tolerance_mm':.01,'coordinate_frame':'supplied source CAD; alignment not inferred','scope':'source cylindrical open-shell geometry only; not setup, mesh, shell normals, fields or convergence approval'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--submitted',type=Path,required=True);a.add_argument('--reference',type=Path,nargs='+',required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args()
 try:r=validate(read(x.submitted),x.reference)
 except Exception as e:r={'geometry_passed':False,'error':str(e)}
 x.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
