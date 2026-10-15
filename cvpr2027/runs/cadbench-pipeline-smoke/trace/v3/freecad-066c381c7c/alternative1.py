import os
import FreeCAD
import PartDesign

def create_part():
    doc = FreeCAD.newDocument("CoaxialConnectorHousing")
    
    body = doc.addObject("PartDesign::Body", "Body")
    
    # 1. Base block: 10 x 10 x 8 (Width x Length x Height roughly)
    # Let's inspect the drawing:
    # Top view shows width = 10, length of main block = 10, total length = 19.
    # Side/Front view shows height = 8, with an angled top (225 deg or similar, height 4 on one side).
    # Let's create a sketch on XY plane for the main block profile (length 10, height 8 with slope).
    
    sketch_base = doc.addObject("Sketcher::SketchObject", "BaseSketch")
    sketch_base.Support = (doc.XY_Plane, [""])
    doc.recompute()
    
    # Draw a polygon for the side profile (XZ plane or XY? Let's use XZ plane for side view profile)
    sketch_base.Support = (doc.XZ_Plane, [""])
    doc.recompute()
    
    # Profile in XZ: length along X (10), height along Z (8).
    # Let's use point coordinates: (0,0), (10,0), (10, 4), (0, 8) -> wait, angle 225 deg or slope from height 8 down to 4 over length 10.
    # Looking at right view: bottom length 10, left height 8, right height 4. Top edge slopes down.
    geo_list = [
        Part.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(10, 0, 0)),
        Part.LineSegment(FreeCAD.Vector(10, 0, 0), FreeCAD.Vector(10, 4, 0)),
        Part.LineSegment(FreeCAD.Vector(10, 4, 0), FreeCAD.Vector(0, 8, 0)),
        Part.LineSegment(FreeCAD.Vector(0, 8, 0), FreeCAD.Vector(0, 0, 0))
    ]
    # Actually, better to use Sketcher geometry API properly or just create standard shapes via Pad.
    # Let's use standard Sketcher lines:
    geom = [
        Part.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(10, 0, 0)),
        Part.LineSegment(FreeCAD.Vector(10, 0, 0), FreeCAD.Vector(10, 4, 0)),
        Part.LineSegment(FreeCAD.Vector(10, 4, 0), FreeCAD.Vector(0, 8, 0)),
        Part.LineSegment(FreeCAD.Vector(0, 8, 0), FreeCAD.Vector(0, 0, 0))
    ]
    for seg in geom:
        sketch_base.addGeometry(seg, False)
    doc.recompute()
    
    pad = doc.addObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_base
    pad.Length = 10.0  # width = 10
    pad.TaperAngle = 0.0
    doc.recompute()
    
    # 2. Cylindrical extension on the right: diameter 6, length 9 (total 19 - 10 = 9).
    # Attached to the right face (X=10 face).
    # Let's create a sketch on the right face or YZ plane.
    sketch_cyl = doc.addObject("Sketcher::SketchObject", "CylSketch")
    # map to face or plane. Let's use YZ plane offset by 10.
    sketch_cyl.Support = (doc.YZ_Plane, [""])
    sketch_cyl.MapMode = "Offset"
    sketch_cyl.MapPathParameter = 0.0
    sketch_cyl.Placement = FreeCAD.Placement(FreeCAD.Vector(10, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))
    doc.recompute()
    
    # Circle of diameter 6 (radius 3) centered at Y=4, Z=4 (relative to block center, or local sketch origin)
    # Let's draw circle at origin (0,0) with radius 3
    sketch_cyl.addGeometry(Part.Circle(FreeCAD.Vector(0, 4, 0), FreeCAD.Vector(0,0,1), 3.0), False)
    doc.recompute()
    
    pad_cyl = doc.addObject("PartDesign::Pad", "PadCyl")
    pad_cyl.Profile = sketch_cyl
    pad_cyl.Length = 9.0
    doc.recompute()
    
    # 3. Pocket / Hole in the cylindrical part: diameter 4.4 through, and a slot/recess with diameter 2.4 and angle 278°.
    sketch_hole = doc.addObject("Sketcher::SketchObject", "HoleSketch")
    sketch_hole.Support = (doc.YZ_Plane, [""])
    sketch_hole.Placement = FreeCAD.Placement(FreeCAD.Vector(19, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))
    doc.recompute()
    
    sketch_hole.addGeometry(Part.Circle(FreeCAD.Vector(0, 4, 0), FreeCAD.Vector(0,0,1), 2.2), False) # dia 4.4
    doc.recompute()
    
    pocket = doc.addObject("PartDesign::Pocket", "PocketCyl")
    pocket.Profile = sketch_hole
    pocket.Length = 19.0
    doc.recompute()

    body.addObjects([pad, pad_cyl, pocket])
    doc.recompute()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, "answer.FCStd")
    doc.saveAs(out_path)
    print(f"Successfully saved to {out_path}")

if __name__ == "__main__":
    create_part()
