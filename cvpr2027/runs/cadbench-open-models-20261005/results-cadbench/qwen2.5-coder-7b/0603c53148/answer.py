import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
outer_diameter = 107.156
flange_thickness = 21.034
bolt_circle_diameter = 87.312
bolt_hole_diameter = 9.922
number_bolt_holes = 4
bore_diameter = 49.213

# Create a circular flange body
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = Part.makeCircle(outer_diameter / 2)
flange.Length = flange_thickness
flange.LengthFilletRadius = 0

# Create a through bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(bore_diameter / 2)
bore.Length = flange_thickness
bore.LengthFilletRadius = 0
bore.Base = flange.Pad

# Create bolt holes
bolt_radius = bolt_hole_diameter / 2
bolt_circle_radius = bolt_circle_diameter / 2
angle_step = 2 * 3.14159 / number_bolt_holes

for i in range(number_bolt_holes):
    angle = i * angle_step
    x = bolt_circle_radius * FreeCAD.sin(angle)
    y = bolt_circle_radius * FreeCAD.cos(angle)
    hole = body.newObject("PartDesign::Pocket", f"BoltHole_{i}")
    hole.Profile = Part.makeCircle(bolt_radius)
    hole.Length = flange_thickness
    hole.LengthFilletRadius = 0
    hole.Base = flange.Pad
    hole.Placement.Base = FreeCAD.Vector(x, y, 0)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
FreeCAD.closeDocument(doc.Name)
