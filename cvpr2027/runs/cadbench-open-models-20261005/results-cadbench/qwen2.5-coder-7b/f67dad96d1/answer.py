import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
outer_diameter = 66.675
flange_thickness = 13.49375
pitch_circle_diameter = 53.18125
bolt_hole_diameter = 6.746875
number_bolt_holes = 4
inner_diameter = 25.4

# Create the flange body
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = Part.makeCircle(outer_diameter / 2)
flange.Length = flange_thickness
flange.LengthFilletRadius = 0

# Create the central through hole
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Profile = Part.makeCircle(inner_diameter / 2)
through_hole.Length = flange_thickness
through_hole.LengthFilletRadius = 0

# Create the bolt holes
bolt_circle_radius = pitch_circle_diameter / 2
angle_step = 360 / number_bolt_holes
for i in range(number_bolt_holes):
    angle = i * angle_step
    x = bolt_circle_radius * FreeCAD.sin(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Angle))
    y = bolt_circle_radius * FreeCAD.cos(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Angle))
    bolt_hole = body.newObject("PartDesign::Pocket", f"BoltHole_{i}")
    bolt_hole.Profile = Part.makeCircle(bolt_hole_diameter / 2)
    bolt_hole.Length = flange_thickness
    bolt_hole.LengthFilletRadius = 0
    bolt_hole.Placement.Base = FreeCAD.Vector(x, y, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
