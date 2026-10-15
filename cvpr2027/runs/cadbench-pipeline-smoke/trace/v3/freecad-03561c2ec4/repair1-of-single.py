import os
import FreeCAD
import Part
import PartDesign

# Output paths derived from __file__
script_dir = os.path.dirname(os.path.abspath(__file__))
doc_path = os.path.join(script_dir, "answer.FCStd")

doc = FreeCAD.newDocument("FlangedWheelHubMotor")
body = doc.addObject("PartDesign::Body", "Body")

# Create base sketch for Revolution (axial cross section on XZ plane)
sketch = doc.addObject("Sketcher::SketchObject", "RevolutionSketch")
body.addObject(sketch)

# Map XZ plane: Sketch horizontal is X (radial), vertical is Z (axial)
# Add geometry for a valid symmetric rotationally symmetric hub profile
geoList = [
    # Axis line (Z-axis from -11.75 to 188.25)
    Part.LineSegment(FreeCAD.Vector(0, -11.75, 0), FreeCAD.Vector(0, 188.25, 0)),
    # Bottom inner bore
    Part.LineSegment(FreeCAD.Vector(0, -11.75, 0), FreeCAD.Vector(6.0, -11.75, 0)),
    Part.LineSegment(FreeCAD.Vector(6.0, -11.75, 0), FreeCAD.Vector(6.0, 28.25, 0)),
    # Stepping out to collar/flange profile
    Part.LineSegment(FreeCAD.Vector(6.0, 28.25, 0), FreeCAD.Vector(10.0, 28.25, 0)),
    Part.LineSegment(FreeCAD.Vector(10.0, 28.25, 0), FreeCAD.Vector(69.5, 28.25, 0)),
    Part.LineSegment(FreeCAD.Vector(69.5, 28.25, 0), FreeCAD.Vector(69.5, 107.75, 0)),
    Part.LineSegment(FreeCAD.Vector(69.5, 107.75, 0), FreeCAD.Vector(17.0, 107.75, 0)),
    Part.LineSegment(FreeCAD.Vector(17.0, 107.75, 0), FreeCAD.Vector(17.0, 155.75, 0)),
    Part.LineSegment(FreeCAD.Vector(17.0, 155.75, 0), FreeCAD.Vector(6.0, 155.75, 0)),
    Part.LineSegment(FreeCAD.Vector(6.0, 155.75, 0), FreeCAD.Vector(6.0, 188.25, 0)),
    Part.LineSegment(FreeCAD.Vector(6.0, 188.25, 0), FreeCAD.Vector(0, 188.25, 0)),
]

for g in geoList:
    sketch.addGeometry(g, False)

doc.recompute()

# Revolution feature around the vertical axis (Z axis / line 0)
rev = doc.addObject("PartDesign::Revolution", "Revolution")
rev.Profile = sketch
rev.ReferenceAxis = (sketch, ["Line1"])
rev.Angle = 360.0
body.addObject(rev)

doc.recompute()

# Save document
doc.saveAs(doc_path)
print("Model successfully saved to", doc_path)
