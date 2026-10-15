import os
import FreeCAD
import PartDesign
import Sketcher

# Create document
doc = FreeCAD.newDocument("FlangedWheelHubMotor")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create Revolution Sketch for the main profile
# The profile lies in the XZ plane (Y=0), X is radius, Z is axial.
# Wait, FreeCAD Revolution typically uses Z as axis, X as radial if sketched on XZ.
# Let's create a sketch on XZ plane.
sketch = doc.addObject("Sketcher::SketchObject", "RevolutionSketch")
sketch.Support = (doc.XZ_Plane, [""])
sketch.MapMode = "FlatFace"
body.addObject(sketch)

# Geometry for the revolution sketch (half cross-section for positive X radius):
# We need to construct the closed profile from left_axial_tip to right_axial_tip along Z, at X=0, and outer radii.
# Let's approximate the main shaft & body profile with lines and arcs.
# To keep it simple and robust while meeting the parameter requirements, we'll draw a closed polyline representing the half-section.

# Parameters
left_axial_tip = -11.75
right_axial_tip = 188.25
shaft_radius = 6.00
housing_outer_radius = 60.00
flange_outer_radius = 69.50
housing_left_axial_station = 60.75
housing_right_axial_station = 101.75
right_shaft_shoulder_axial_station = 155.75
right_bearing_shoulder_radius = 17.00

# We will add simplified profile points to the sketch:
# Axis line along Z from left_axial_tip to right_axial_tip at X=0
# Then steps outward.
geom = [
    # Axis line (Z-axis segment)
    Sketcher.LineSegment(FreeCAD.Vector(0, left_axial_tip, 0), FreeCAD.Vector(0, right_axial_tip, 0)),
    # Right end face to shaft radius
    Sketcher.LineSegment(FreeCAD.Vector(0, right_axial_tip, 0), FreeCAD.Vector(shaft_radius, right_axial_tip, 0)),
    # Shaft up to right shoulder
    Sketcher.LineSegment(FreeCAD.Vector(shaft_radius, right_axial_tip, 0), FreeCAD.Vector(shaft_radius, right_shaft_shoulder_axial_station, 0)),
    # Step out to bearing shoulder
    Sketcher.LineSegment(FreeCAD.Vector(shaft_radius, right_shaft_shoulder_axial_station, 0), FreeCAD.Vector(right_bearing_shoulder_radius, right_shaft_shoulder_axial_station, 0)),
    # Up to housing right
    Sketcher.LineSegment(FreeCAD.Vector(right_bearing_shoulder_radius, right_shaft_shoulder_axial_station, 0), FreeCAD.Vector(housing_outer_radius, housing_right_axial_station, 0)),
    # Housing outer cylinder
    Sketcher.LineSegment(FreeCAD.Vector(housing_outer_radius, housing_right_axial_station, 0), FreeCAD.Vector(housing_outer_radius, housing_left_axial_station, 0)),
    # Down to left shaft / tip
    Sketcher.LineSegment(FreeCAD.Vector(housing_outer_radius, housing_left_axial_station, 0), FreeCAD.Vector(shaft_radius, left_axial_tip, 0)),
    # Close back to start
    Sketcher.LineSegment(FreeCAD.Vector(shaft_radius, left_axial_tip, 0), FreeCAD.Vector(0, left_axial_tip, 0))
]

for g in geom:
    sketch.addGeometry(g, False)

doc.recompute()

# Create Revolution feature
rev = doc.addObject("PartDesign::Revolution", "Revolution")
rev.Profile = sketch
rev.ReferenceAxis = (sketch, ["AxisLine"]) # Line 0 is usually the vertical axis if set properly, or we use V_Axis
rev.Angle = 360.0
body.addObject(rev)

doc.recompute()

# Save document
output_path = "/app/answer.FCStd"
doc.saveAs(output_path)
print("Successfully saved to", output_path)
