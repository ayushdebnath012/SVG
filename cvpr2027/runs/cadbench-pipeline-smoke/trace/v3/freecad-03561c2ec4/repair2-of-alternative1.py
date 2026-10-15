import os
import FreeCAD
import PartDesign
import Sketcher

# Create document
doc = FreeCAD.newDocument("FlangedWheelHubMotor")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create Revolution Sketch for the main profile on XZ plane
sketch = doc.addObject("Sketcher::SketchObject", "RevolutionSketch")
body.addObject(sketch)

# Map to XZ plane properly in FreeCAD 1.1
sketch.MapMode = "Deactivated"

# Parameters
left_axial_tip = -11.75
right_axial_tip = 188.25
shaft_radius = 6.00
housing_outer_radius = 60.00
housing_left_axial_station = 60.75
housing_right_axial_station = 101.75
right_shaft_shoulder_axial_station = 155.75
right_bearing_shoulder_radius = 17.00

# Geometry using Part.LineSegment / Sketcher geometry constructors
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0, left_axial_tip, 0), FreeCAD.Vector(0, right_axial_tip, 0)), False)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(0, right_axial_tip, 0), FreeCAD.Vector(shaft_radius, right_axial_tip, 0)), False)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(shaft_radius, right_axial_tip, 0), FreeCAD.Vector(shaft_radius, right_shaft_shoulder_axial_station, 0)), False)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(shaft_radius, right_shaft_shoulder_axial_station, 0), FreeCAD.Vector(right_bearing_shoulder_radius, right_shaft_shoulder_axial_station, 0)), False)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(right_bearing_shoulder_radius, right_shaft_shoulder_axial_station, 0), FreeCAD.Vector(housing_outer_radius, housing_right_axial_station, 0)), False)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(housing_outer_radius, housing_right_axial_station, 0), FreeCAD.Vector(housing_outer_radius, housing_left_axial_station, 0)), False)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(housing_outer_radius, housing_left_axial_station, 0), FreeCAD.Vector(shaft_radius, left_axial_tip, 0)), False)
sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(shaft_radius, left_axial_tip, 0), FreeCAD.Vector(0, left_axial_tip, 0)), False)

doc.recompute()

# Create Revolution feature
rev = doc.addObject("PartDesign::Revolution", "Revolution")
rev.Profile = sketch
rev.ReferenceAxis = (sketch, ['AxisLine'])
rev.Angle = 360.0
body.addObject(rev)

doc.recompute()

# Save document to /app/answer.FCStd and next to script
output_path = "/app/answer.FCStd"
doc.saveAs(output_path)
print("Successfully saved to", output_path)
