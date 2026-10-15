import os
import FreeCAD
import Part
import PartDesign

def create_part():
    doc = FreeCAD.newDocument("CoaxialConnectorHousing")
    
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Create sketch for main body on XZ plane
    sketch_base = doc.addObject("Sketcher::SketchObject", "BaseSketch")
    body.addObject(sketch_base)
    sketch_base.Support = [(doc.XZ_Plane, "")]
    sketch_base.MapMode = "FlatFace"
    doc.recompute()
    
    # Add geometry to sketch_base: rectangle/polygon with sloped top
    # Dimensions: length 10, left height 4, right height 8, top slope from 4 to 8.
    # Wait, let's check drawing: left side height = 4, right side height = 8.
    geom = [
        Part.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(10, 0, 0)),
        Part.LineSegment(FreeCAD.Vector(10, 0, 0), FreeCAD.Vector(10, 8, 0)),
        Part.LineSegment(FreeCAD.Vector(10, 8, 0), FreeCAD.Vector(0, 4, 0)),
        Part.LineSegment(FreeCAD.Vector(0, 4, 0), FreeCAD.Vector(0, 0, 0))
    ]
    for seg in geom:
        sketch_base.addGeometry(seg, False)
    doc.recompute()
    
    pad = doc.addObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_base
    pad.Length = 10.0  # width = 10
    body.addObject(pad)
    doc.recompute()
    
    # Cylindrical extension on the right: diameter 6, length 19 - 10 = 9.
    sketch_cyl = doc.addObject("Sketcher::SketchObject", "CylSketch")
    body.addObject(sketch_cyl)
    sketch_cyl.Support = [(pad.TypeId, "")] # Use attachment via Plane
    # Better: map to YZ plane with X offset 10
    sketch_cyl.Support = [(doc.YZ_Plane, "")]
    sketch_cyl.MapMode = "Offset"
    sketch_cyl.Placement = FreeCAD.Placement(FreeCAD.Vector(10, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))
    doc.recompute()
    
    sketch_cyl.addGeometry(Part.Circle(FreeCAD.Vector(5, 3.99, 0), FreeCAD.Vector(0,0,1), 3.0), False)
    doc.recompute()
    
    pad_cyl = doc.addObject("PartDesign::Pad", "PadCyl")
    pad_cyl.Profile = sketch_cyl
    pad_cyl.Length = 9.0
    body.addObject(pad_cyl)
    doc.recompute()
    
    # Hole through: dia 4.4
    sketch_hole = doc.addObject("Sketcher::SketchObject", "HoleSketch")
    body.addObject(sketch_hole)
    sketch_hole.Support = [(doc.YZ_Plane, "")]
    sketch_hole.MapMode = "Offset"
    sketch_hole.Placement = FreeCAD.Placement(FreeCAD.Vector(19, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))
    doc.recompute()
    
    sketch_hole.addGeometry(Part.Circle(FreeCAD.Vector(5, 3.99, 0), FreeCAD.Vector(0,0,1), 2.2), False)
    doc.recompute()
    
    pocket = doc.addObject("PartDesign::Pocket", "PocketCyl")
    pocket.Profile = sketch_hole
    pocket.Length = 19.0
    body.addObject(pocket)
    doc.recompute()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, "answer.FCStd")
    doc.recompute()
    doc.saveAs(out_path)
    print(f"Successfully saved to {out_path}")

if __name__ == "__main__":
    create_part()
