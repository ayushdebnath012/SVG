import FreeCAD
import PartDesign

# Define the parameters
outer_diameter = 40.084
flange_thickness = 10.319
bolt_circle_diameter = 28.575
bolt_hole_diameter = 6.747
number_bolt_holes = 4
inner_diameter = 14.288

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create the flange body
flange_body = PartDesign.Cylinder(doc, "FlangeBody", outer_diameter / 2, flange_thickness, 0, 360)
body.addObject(flange_body)

# Create the central through bore
through_bore = PartDesign.Cylinder(doc, "ThroughBore", inner_diameter / 2, flange_thickness, 0, 360)
body.addObject(through_bore)

# Create the bolt circle
bolt_circle = PartDesign.Circle(doc, "BoltCircle", bolt_circle_diameter / 2, 0, 360)
body.addObject(bolt_circle)

# Create the bolt holes
for i in range(number_bolt_holes):
    angle = 360 / number_bolt_holes * i
    bolt_hole = PartDesign.Cylinder(doc, f"BoltHole_{i}", bolt_hole_diameter / 2, flange_thickness, angle, angle + 360 / number_bolt_holes)
    body.addObject(bolt_hole)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
