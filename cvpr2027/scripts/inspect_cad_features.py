"""Read-only kernel surface inventory for a STEP solid, without reference geometry.

Reports evidence, not semantic feature counts: a hole may have several faces and
a fillet may use a non-cylindrical surface. Review topology before grading.
"""
import argparse,json,math
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder,GeomAbs_Plane,GeomAbs_Torus,GeomAbs_Cone
from cad_native_probe import metrics,write

def inventory(shape):
    faces=[]
    for i,f in enumerate(shape.Faces()):
        a=BRepAdaptor_Surface(f.wrapped,True);kind=a.GetType();b=f.BoundingBox()
        r={'index':i,'type':str(kind),'area_mm2':f.Area(),'bbox_mm':{k:getattr(b,k) for k in ['xmin','xmax','ymin','ymax','zmin','zmax']},'orientation':str(f.wrapped.Orientation())}
        if kind in [GeomAbs_Cylinder,GeomAbs_Torus,GeomAbs_Cone]:
            surface=a.Cylinder() if kind==GeomAbs_Cylinder else a.Torus() if kind==GeomAbs_Torus else a.Cone()
            r.update(axis=surface.Axis().Direction().Coord(),location=surface.Location().Coord(),u_range=[a.FirstUParameter(),a.LastUParameter()],v_range=[a.FirstVParameter(),a.LastVParameter()])
            if kind==GeomAbs_Cylinder:r['radius_mm']=surface.Radius()
            if kind==GeomAbs_Torus:r.update(major_radius_mm=surface.MajorRadius(),minor_radius_mm=surface.MinorRadius())
            if kind==GeomAbs_Cone:r.update(reference_radius_mm=surface.RefRadius(),semi_angle_rad=surface.SemiAngle())
        elif kind==GeomAbs_Plane:r.update(normal=a.Plane().Axis().Direction().Coord(),location=a.Plane().Location().Coord())
        faces.append(r)
    return {'metrics':metrics(shape),'surfaces':faces,'scope':'Kernel surface inventory only, not automatic feature recognition or a complete geometry verdict.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('step',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    write(a.output,inventory(cq.importers.importStep(str(a.step)).val()))
