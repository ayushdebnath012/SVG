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
body = doc.addObject("PartDesign::Body", "Body")

# Create a circular flange body
flange_body = PartDesign.Body.createCylinder(body, outer_diameter / 2, flange_thickness)

# Create a through bore
bore = PartDesign.Body.createCylinder(body, bore_diameter / 2, flange_thickness)

# Position the bore inside the flange body
bore.Placement.Base = FreeCAD.Vector(0, 0, -flange_thickness / 2)
bore.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

# Create a bolt circle
bolt_circle_center = FreeCAD.Vector(0, 0, -flange_thickness / 2 + bore_diameter / 2)
bolt_circle_radius = (bolt_circle_diameter - bore_diameter) / 2
bolt_circle_points = []
for i in range(number_bolt_holes):
    angle = 2 * math.pi * i / number_bolt_holes
    x = bolt_circle_center.x + bolt_circle_radius * math.cos(angle)
    y = bolt_circle_center.y + bolt_circle_radius * math.sin(angle)
    bolt_circle_points.append((x, y))

# Create bolt holes
for point in bolt_circle_points:
    hole_center = FreeCAD.Vector(point[0], point[1], -flange_thickness / 2 + bore_diameter / 2)
    hole_radius = bolt_hole_diameter / 2
    hole = PartDesign.Body.createCylinder(body, hole_radius, flange_thickness)
    hole.Placement.Base = hole_center
    hole.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

# Save the document
output_path = __file__.replace(".py", ".FCStd")
doc.saveAs(output_path)

print(f"Model saved to {output_path}")
