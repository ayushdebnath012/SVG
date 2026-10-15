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
pl = FreeCAD.Placement()
pl.Rotation.setYawPitchRoll(0, 0, 0)
sketch.Placement = pl

# Parameters
left_axial_tip = -11.75
right_axial_tip = 188.25
shaft_radius = 6.00
housing_outer_radius = 60.00
housing_left_axial_station = 60.75
housing_right_axial_station = 101.75
right_shaft_shoulder_axial_station = 155.75
right_bearing_shoulder_radius = 17.00

# Geometry for the revolution sketch (half cross-section in XZ plane, X=radius, Z=axial)
geom = [
    # 0: Axis line along Z
    Sketcher.LineSegment(FreeCAD.Vector(0, left_axial_tip, 0), FreeCAD.Vector(0, right_axial_tip, 0)),
    # 1: Right end face
    Sketcher.LineSegment(FreeCAD.Vector(0, right_axial_tip, 0), FreeCAD.Vector(shaft_radius, right_axial_tip, 0)),
    # 2: Shaft segment
    Sketcher.LineSegment(FreeCAD.Vector(shaft_radius, right_axial_tip, 0), FreeCAD.Vector(shaft_radius, right_shaft_shoulder_axial_station, 0)),
    # 3: Bearing shoulder step
    Sketcher.LineSegment(FreeCAD.Vector(shaft_radius, right_shaft_shoulder_axial_station, 0), FreeCAD.Vector(right_bearing_shoulder_radius, right_shaft_shoulder_axial_station, 0)),
    # 4: Transition to housing right
    Sketcher.LineSegment(FreeCAD.Vector(right_bearing_shoulder_radius, right_shaft_shoulder_axial_station, 0), FreeCAD.Vector(housing_outer_radius, housing_right_axial_station, 0)),
    # 5: Housing outer cylinder
    Sketcher.LineSegment(FreeCAD.Vector(housing_outer_radius, housing_right_axial_station, 0), FreeCAD.Vector(housing_outer_radius, housing_left_axial_station, 0)),
    # 6: Transition to left tip
    Sketcher.LineSegment(FreeCAD.Vector(housing_outer_radius, housing_left_axial_station, 0), FreeCAD.Vector(shaft_radius, left_axial_tip, 0)),
    # 7: Left end face
    Sketcher.LineSegment(FreeCAD.Vector(shaft_radius, left_axial_tip, 0), FreeCAD.Vector(0, left_axial_tip, 0))
]

for g in geom:
    sketch.addGeometry(g, False)

doc.recompute()

# Create Revolution feature
rev = doc.addObject("PartDesign::Revolution", "Revolution")
rev.Profile = sketch
# Reference axis: use the first line (index 1 in 1-based indexing for sketch axes or explicit edge)
rev.ReferenceAxis = (sketch, ['Line1'])
rev.Angle = 360.0
body.addObject(rev)

doc.recompute()

# Save document next to script / absolute path /app/answer.FCStd
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/app'
output_path = os.path.join(script_dir, "answer.FCStd")
doc.saveAs(output_path)
print("Successfully saved to", output_path)
