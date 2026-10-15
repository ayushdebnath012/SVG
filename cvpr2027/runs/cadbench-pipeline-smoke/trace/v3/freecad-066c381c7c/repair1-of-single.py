import os
import FreeCAD
import PartDesign
import Sketcher

doc = FreeCAD.newDocument("CoaxialConnectorHousing")
body = doc.addObject("PartDesign::Body", "Body")

# Base sketch on XY plane
sketch_base = doc.addObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Support = (doc.XYPlane, [""])
body.addObject(sketch_base)

# Main block: 10 x 10 rectangle
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(10, 0, 0)), False)
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 0, 0), FreeCAD.Vector(10, 10, 0)), False)
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 10, 0), FreeCAD.Vector(0, 10, 0)), False)
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(0, 10, 0), FreeCAD.Vector(0, 0, 0)), False)

pad = doc.addObject("PartDesign::Pad", "Pad")
pad.Profile = sketch_base
pad.Length = 8.0
body.addObject(pad)
doc.recompute()

# Extension sketch
sketch_ext = doc.addObject("Sketcher::SketchObject", "ExtSketch")
sketch_ext.Support = (doc.XYPlane, [""])
body.addObject(sketch_ext)

sketch_ext.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 2, 0), FreeCAD.Vector(19, 2, 0)), False)
sketch_ext.addGeometry(Sketcher.ArcOfCircle(FreeCAD.Vector(19, 5, 0), FreeCAD.Vector(19, 2, 0), FreeCAD.Vector(19, 8, 0)), False)
sketch_ext.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(19, 8, 0), FreeCAD.Vector(10, 8, 0)), False)
sketch_ext.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 8, 0), FreeCAD.Vector(10, 2, 0)), False)

pad_ext = doc.addObject("PartDesign::Pad", "PadExt")
pad_ext.Profile = sketch_ext
pad_ext.Length = 8.0
body.addObject(pad_ext)
doc.recompute()

# Save document next to script
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
output_path = os.path.join(script_dir, "answer.FCStd")
doc.saveAs(output_path)
