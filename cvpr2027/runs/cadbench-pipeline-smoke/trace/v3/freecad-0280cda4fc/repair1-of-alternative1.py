import os
import FreeCAD
import Part
import Sketcher
import PartDesign

def create_base_document(filename):
    doc = FreeCAD.newDocument("CameraMountBase")
    body = doc.addObject("PartDesign::Body", "Body")
    
    sketch = doc.addObject("Sketcher::SketchObject", "BaseSketch")
    body.addObject(sketch)
    sketch.MapMode = "FlatFace"
    sketch.AttachmentSupport = [(doc.XY_Plane, "")]
    
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, -30, 0), FreeCAD.Vector(30, -30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, -30, 0), FreeCAD.Vector(30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, 30, 0), FreeCAD.Vector(-30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, 30, 0), FreeCAD.Vector(-30, -30, 0)), False)
    
    pad = doc.addObject("PartDesign::Pad", "BasePad")
    pad.Profile = sketch
    pad.Length = 80.0
    body.addObject(pad)
    
    doc.recompute()
    doc.saveAs(filename)
    FreeCAD.closeDocument(doc.Name)

def create_target_document(target_filename):
    doc = FreeCAD.newDocument("CameraMountTarget")
    body = doc.addObject("PartDesign::Body", "Body")
    
    sketch = doc.addObject("Sketcher::SketchObject", "BaseSketch")
    body.addObject(sketch)
    sketch.MapMode = "FlatFace"
    sketch.AttachmentSupport = [(doc.XY_Plane, "")]
    
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, -30, 0), FreeCAD.Vector(30, -30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, -30, 0), FreeCAD.Vector(30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(30, 30, 0), FreeCAD.Vector(-30, 30, 0)), False)
    sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-30, 30, 0), FreeCAD.Vector(-30, -30, 0)), False)
    
    pad = doc.addObject("PartDesign::Pad", "BasePad")
    pad.Profile = sketch
    pad.Length = 80.0
    body.addObject(pad)
    
    doc.recompute()
    doc.saveAs(target_filename)
    FreeCAD.closeDocument(doc.Name)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stem = os.path.splitext(os.path.basename(__file__))[0]
    
    base_file = os.path.join(script_dir, f"{stem}_base.FCStd")
    edit_file = os.path.join(script_dir, f"{stem}_edit.FCStd")
    
    create_base_document(base_file)
    create_target_document(edit_file)
