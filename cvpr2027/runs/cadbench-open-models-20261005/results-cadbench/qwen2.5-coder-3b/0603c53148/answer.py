import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
outer_diameter = 107.156
flange_thickness = 21.034
bolt_circle_diameter = 87.312
bolt_hole_diameter = 9.922
number_bolt_holes = 4
bore_diameter = 49.213

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create the flange body
flange_body = PartDesign.Cylinder(doc, "FlangeBody", outer_diameter / 2, flange_thickness, 0, 360)
body.addObject(flange_body)

# Create the through bore
bore = PartDesign.Cylinder(doc, "Bore", bore_diameter / 2, flange_thickness, 0, 360)
bore.Placement.Base = FreeCAD.Vector(0, 0, flange_thickness / 2)
body.addObject(bore)

# Create the bolt holes
angle_between_holes = 360 / number_bolt_holes
for i in range(number_bolt_holes):
    hole = PartDesign.Cylinder(doc, f"BoltHole_{i+1}", bolt_hole_diameter / 2, flange_thickness, 0, 360)
    hole.Placement.Base = FreeCAD.Vector(
        outer_diameter / 2 * math.cos(math.radians(i * angle_between_holes)),
        outer_diameter / 2 * math.sin(math.radians(i * angle_between_holes)),
        flange_thickness / 2
    )
    body.addObject(hole)

# Save the document
doc.saveAs("/app/answer.FCStd")
