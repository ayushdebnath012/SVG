import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the parameters
outer_diameter = 125.4125  # mm
flange_thickness = 23.01875  # mm
bore_diameter = 64.690625  # mm
bolt_circle_diameter = 103.1875  # mm
bolt_hole_diameter = 13.49375  # mm
number_of_bolt_holes = 4

# Create a cylindrical flange body
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = outer_diameter / 2
cylinder.Height = flange_thickness
cylinder.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a through bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = bore_diameter / 2
bore.Height = flange_thickness
bore.Placement.Base = FreeCAD.Vector(0, 0, 0)
bore.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)

# Create a bolt circle
bolt_circle = body.newObject("PartDesign::Circle", "BoltCircle")
bolt_circle.Radius = bolt_circle_diameter / 2
bolt_circle.Placement.Base = FreeCAD.Vector(0, 0, 0)
bolt_circle.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)

# Create bolt holes
bolt_hole_radius = bolt_hole_diameter / 2
for i in range(number_of_bolt_holes):
    angle = 360 * i / number_of_bolt_holes
    x = bolt_circle_diameter / 2 * FreeCAD.sin(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Degree))
    y = bolt_circle_diameter / 2 * FreeCAD.cos(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Degree))
    bolt_hole = body.newObject("PartDesign::Cylinder", f"BoltHole_{i}")
    bolt_hole.Radius = bolt_hole_radius
    bolt_hole.Height = flange_thickness
    bolt_hole.Placement.Base = FreeCAD.Vector(x, y, 0)
    bolt_hole.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)

# Finalize the body
body.finish()

# Save the document
doc.saveAs("/app/answer.FCStd")
