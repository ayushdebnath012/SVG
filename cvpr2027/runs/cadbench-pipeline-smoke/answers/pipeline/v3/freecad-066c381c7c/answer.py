import os
import FreeCAD
import PartDesign
import Sketcher

# Create document
doc = FreeCAD.newDocument("CoaxialConnectorHousing")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create Sketch for main block (front view or top view)
# Let's use XY plane for top/bottom view or XZ for front view.
# Looking at drawing: Main block is 10 x 10 x 8 (width x length x height? Let's check:
# Top view shows 10 wide, 10 long for the main block, then a cylindrical/stepped extension to 19 total length.
# Height is 8 (right view).
sketch_base = doc.addObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Support = (doc.XYPlane, [""])
body.addObject(sketch_base)

# Draw main block rectangle 10x10 centered or at origin
# Let's draw from origin: x from 0 to 10, y from -5 to 5 (or 0 to 10)
# Top view: width is 10 (vertical on top view), length is 10 for main block, total 19.
# Let's make it symmetric or quadrant 1.
geom_base = [
    Sketcher.LineSegment(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(10, 0, 0)),
    Sketcher.LineSegment(FreeCAD.Vector(10, 0, 0), FreeCAD.Vector(10, 10, 0)),
    Sketcher.LineSegment(FreeCAD.Vector(10, 10, 0), FreeCAD.Vector(0, 10, 0)),
    Sketcher.LineSegment(FreeCAD.Vector(0, 10, 0), FreeCAD.Vector(0, 0, 0))
]
for g in geom_base:
    sketch_base.addGeometry(g, False)

# Pad the base sketch by height = 8
pad = doc.addObject("PartDesign::Pad", "Pad")
pad.Profile = sketch_base
pad.Length = 8.0
body.addObject(pad)
doc.recompute()

# Add the cylindrical/stepped extension on the right (from x=10 to x=19, length 9)
# Looking at top view, the extension has diameters: 6, then stepped down or up?
# Dia 6 is the main cylinder, and there's a slot or pocket of dia 2.4 and 4.4?
# Let's create a sketch on the right face of the pad (YZ plane offset by 10) or attach to face.
# Alternatively, create a second pad from a sketch on YZ plane or XY plane.
# Let's use XY plane with a sketch for the extension: from x=10 to 19, width 6 centered at y=5.
sketch_ext = doc.addObject("Sketcher::SketchObject", "ExtSketch")
sketch_ext.Support = (doc.XYPlane, [""])
body.addObject(sketch_ext)

geom_ext = [
    Sketcher.LineSegment(FreeCAD.Vector(10, 2, 0), FreeCAD.Vector(19, 2, 0)),
    Sketcher.ArcOfCircle(FreeCAD.Vector(19, 5, 0), FreeCAD.Vector(19, 2, 0), FreeCAD.Vector(19, 8, 0)),
    Sketcher.LineSegment(FreeCAD.Vector(19, 8, 0), FreeCAD.Vector(10, 8, 0)),
]
# Simpler: just a rectangle from x=10 to 19, y=2 to 8 (width 6, centered at y=5) plus semicircular end at x=19? Or is it a full cylinder of dia 6?
# Top view shows parallel lines at y=2 and y=8, so width = 6. At x=19, there is a semicircle of dia 6 (radius 3).
sketch_ext.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 2, 0), FreeCAD.Vector(19, 2, 0)), False)
sketch_ext.addGeometry(Sketcher.ArcOfCircle(FreeCAD.Vector(19, 5, 0), FreeCAD.Vector(19, 2, 0), FreeCAD.Vector(19, 8, 0)), False)
sketch_ext.addGeometry(Sketcher.LineId := Sketcher.LineSegment(FreeCAD.Vector(19, 8, 0), FreeCAD.Vector(10, 8, 0)), False)
sketch_ext.addGeometry(Sketcher.LineSegment(FreeCAD.Vector(10, 8, 0), FreeCAD.Vector(10, 2, 0)), False)

pad_ext = doc.addObject("PartDesign::Pad", "PadExt")
pad_ext.Profile = sketch_ext
pad_ext.Length = 8.0
body.addObject(pad_ext)
doc.recompute()

# Save document
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "answer.FCStd")
doc.saveAs(output_path)
