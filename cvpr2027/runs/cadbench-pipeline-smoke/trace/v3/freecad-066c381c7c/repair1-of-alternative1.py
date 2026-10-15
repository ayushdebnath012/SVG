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
    sketch_base.mapToSupport()
    
    # Use attachments or plane mapping properly in FreeCAD 1.1
    # In PartDesign, sketches are usually added to Body first, then mapped.
    # Alternatively, set MapMode and Support via attachment properties:
    sketch_base.Support = [(doc.XZ_Plane, "")]
    sketch_base.MapMode = "FlatFace"
    doc.recompute()
    
    # Add geometry to sketch_base: rectangle/polygon with sloped top
    # Dimensions from drawing: length = 10, left height = 8, right height = 4 (225 deg angle or height 4 at right)
    # Let's check drawing: left height 8, right height is 4 (implied by 225 deg or total height / slope).
    # Wait, looking at the right view: total height 8, left side vertical 4, top slopes up to 8? 
    # Ah: left side has height 4 (bottom to shoulder), total height 8. Wait, 225° angle from horizontal?
    # Let's carefully read dimensions: width = 10, length = 10, height = 8.
    # Left vertical = 4, then slope to right height = 8? Or vice versa?
    # Right view: height on right is 8, height on left is 4. Top edge goes up from left (4) to right (8)? No, angle 225 degrees (which is 180 + 45).
    # Let's draw: (0,0) to (10,0) [length 10], up to (10, 8), left to (0, 4), down to (0,0).
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
    # Map to the right face of the pad, or YZ plane with offset X=10
    sketch_cyl.Support = [(doc.YZ_Plane, "")]
    sketch_cyl.MapMode = "Offset"
    sketch_cyl.Placement = FreeCAD.Placement(FreeCAD.Vector(10, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))
    doc.recompute()
    
    # Center of cylinder is at Z = 3.99 (or 4), Y = 5 (middle of width 10)
    # In XZ sketch of pad, origin was bottom-left. So cylinder center is at Y=5, Z=4 relative to body.
    sketch_cyl.addGeometry(Part.Circle(FreeCAD.Vector(5, 4, 0), FreeCAD.Vector(0,0,1), 3.0), False)
    doc.recompute()
    
    pad_cyl = doc.addObject("PartDesign::Pad", "PadCyl")
    pad_cyl.Profile = sketch_cyl
    pad_cyl.Length = 9.0
    body.addObject(pad_cyl)
    doc.recompute()
    
    # Hole through the cylinder and main body: dia 4.4 through, plus counterbore/slot.
    sketch_hole = doc.addObject("Sketcher::SketchObject", "HoleSketch")
    body.addObject(sketch_hole)
    sketch_hole.Support = [(doc.YZ_Plane, "")]
    sketch_hole.MapMode = "Offset"
    sketch_hole.Placement = FreeCAD.Placement(FreeCAD.Vector(19, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))
    doc.recompute()
    
    sketch_hole.addGeometry(Part.Circle(FreeCAD.Vector(5, 4, 0), FreeCAD.Vector(0,0,1), 2.2), False)
    doc.recompute()
    
    pocket = doc.addObject("PartDesign::Pocket", "PocketCyl")
    pocket.Profile = sketch_hole
    pocket.Length = 19.0
    body.addObject(pocket)
    doc.recompute()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, "answer.FCStd")
    doc.saveAs(out_path)
    print(f"Successfully saved to {out_path}")

if __name__ == "__main__":
    create_part()
