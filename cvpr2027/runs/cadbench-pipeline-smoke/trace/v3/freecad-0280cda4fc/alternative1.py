import os
import FreeCAD
import Part
import Sketcher
import PartDesign

def create_base_document(filename):
    doc = FreeCAD.newDocument("CameraMountBase")
    
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Base extrusion: square 60x60, depth 80
    # Let's create sketch on XY plane
    sketch = doc.addObject("Sketcher::SketchObject", "BaseSketch")
    sketch.Support = (doc.XY_Plane, [""])
    sketch.MapMode = "FlatFace"
    
    # Square centered or at origin? Description says "square width-height section of base_side_length"
    # Let's center it on origin: -30 to 30
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, -30, 0), FreeCAD.Vector(30, -30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, -30, 0), FreeCAD.Vector(30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, 30, 0), FreeCAD.Vector(-30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, 30, 0), FreeCAD.Vector(-30, -30, 0)), False)
    
    pad = doc.addObject("PartDesign::Pad", "BasePad")
    pad.Profile = sketch
    pad.Length = 80.0
    
    doc.recompute()
    doc.saveAs(filename)
    return doc

def create_target_document(base_filename, target_filename):
    # For the sake of a complete self-contained script, we build the target directly
    doc = FreeCAD.newDocument("CameraMountTarget")
    body = doc.addObject("PartDesign::Body", "Body")
    
    sketch = doc.addObject("Sketcher::SketchObject", "BaseSketch")
    sketch.Support = (doc.XY_Plane, [""])
    sketch.MapMode = "FlatFace"
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, -30, 0), FreeCAD.Vector(30, -30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, -30, 0), FreeCAD.Vector(30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, 30, 0), FreeCAD.Vector(-30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, 30, 0), FreeCAD.Vector(-30, -30, 0)), False)
    
    pad = doc.addObject("PartDesign::Pad", "BasePad")
    pad.Profile = sketch
    pad.Length = 80.0
    
    doc.recompute()
    doc.saveAs(target_filename)
    return doc

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stem = os.path.splitext(os.path.basename(__file__))[0]
    
    base_file = os.path.join(script_dir, f"{stem}_base.FCStd")
    edit_file = os.path.join(script_dir, f"{stem}_edit.FCStd")
    
    create_base_document(base_file)
    create_target_document(base_file, edit_file)
