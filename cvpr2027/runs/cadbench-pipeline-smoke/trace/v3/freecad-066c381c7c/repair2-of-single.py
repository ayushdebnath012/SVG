import os
import FreeCAD
import PartDesign
import Sketcher

doc = FreeCAD.newDocument("CoaxialConnectorHousing")
body = doc.addObject("PartDesign::Body", "Body")

# Base sketch on XY plane using PartDesign origin features
sketch_base = doc.addObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Support = (doc.Origin.XYPlane, [""])
body.addObject(sketch_base)

# Main block: 10 x 10 rectangle
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(10, 0, 0)), False)
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 0, 0), FreeCAD.Vector(10, 8, 0)), False)
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 8, 0), FreeCAD.Vector(0, 8, 0)), False)
sketch_base.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(0, 8, 0), FreeCAD.Vector(0, 0, 0)), False)

pad = doc.addObject("PartDesign::Pad", "Pad")
pad.Profile = sketch_base
pad.Length = 10.0
body.addObject(pad)
doc.recompute()

# Save document next to script
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "answer.FCStd")
doc.saveAs(output_path)
