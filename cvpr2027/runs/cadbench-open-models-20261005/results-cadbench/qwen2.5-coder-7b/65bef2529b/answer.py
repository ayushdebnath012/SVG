import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
flange_outer_diameter = 107.156
flange_thickness = 21.034
bolt_circle_diameter = 87.313
bore_diameter = 49.213
bolt_hole_diameter = 9.922
number_of_bolt_holes = 4

# Create a cylindrical flange body
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = flange_outer_diameter / 2
cylinder.Height = flange_thickness
cylinder.Placement.Base = FreeCAD.Vector(0, 0, flange_thickness / 2)

# Create a central through bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = bore_diameter / 2
bore.Height = flange_thickness
bore.Placement.Base = FreeCAD.Vector(0, 0, flange_thickness / 2)

# Create a bolt-hole pattern
bolt_hole_radius = bolt_hole_diameter / 2
bolt_circle_radius = bolt_circle_diameter / 2
angle_step = 2 * math.pi / number_of_bolt_holes

for i in range(number_of_bolt_holes):
    angle = i * angle_step
    x = bolt_circle_radius * math.sin(angle)
    y = bolt_circle_radius * math.cos(angle)
    bolt_hole = body.newObject("PartDesign::Cylinder", f"BoltHole_{i}")
    bolt_hole.Radius = bolt_hole_radius
    bolt_hole.Height = flange_thickness
    bolt_hole.Placement.Base = FreeCAD.Vector(x, y, flange_thickness / 2)

# Finalize the body
body.Touched = True

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
