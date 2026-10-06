import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
outer_diameter = 40.084
flange_thickness = 10.319
bolt_circle_diameter = 28.575
bolt_hole_diameter = 6.747
number_bolt_holes = 4
inner_diameter = 14.288

# Create the flange body
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = Part.makeCircle(outer_diameter / 2)
flange.Length = flange_thickness
flange.LengthFilletRadius = 0

# Create the through bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(inner_diameter / 2)
bore.Length = flange_thickness
bore.LengthFilletRadius = 0

# Create the bolt hole pattern
bolt_circle_radius = bolt_circle_diameter / 2
bolt_hole_radius = bolt_hole_diameter / 2
bolt_hole_positions = [bolt_circle_radius * (i / number_bolt_holes) for i in range(number_bolt_holes)]
bolt_hole_positions = [FreeCAD.Vector(bolt_circle_radius * (i / number_bolt_holes) * FreeCAD.sin(2 * FreeCAD.pi * i / number_bolt_holes), bolt_circle_radius * (i / number_bolt_holes) * FreeCAD.cos(2 * FreeCAD.pi * i / number_bolt_holes), 0) for i in range(number_bolt_holes)]

for pos in bolt_hole_positions:
    hole = body.newObject("PartDesign::Pocket", "BoltHole")
    hole.Profile = Part.makeCircle(bolt_hole_radius)
    hole.Length = flange_thickness
    hole.LengthFilletRadius = 0
    hole.Placement.Base = pos

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
