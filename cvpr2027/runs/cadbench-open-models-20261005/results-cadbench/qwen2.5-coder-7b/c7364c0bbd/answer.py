import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define key parameters
outer_diameter = 69.453
flange_thickness = 13.097
pitch_circle_diameter = 57.944
bolt_hole_diameter = 6.747
number_bolt_holes = 4
bore_diameter = 34.925

# Create a circular flange body
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = doc.addObject("Part::Circle", "FlangeProfile")
flange.Profile.Radius = outer_diameter / 2
flange.Length = flange_thickness
flange.Base = FreeCAD.Vector(0, 0, 0)

# Create a central through bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = doc.addObject("Part::Circle", "BoreProfile")
bore.Profile.Radius = bore_diameter / 2
bore.Length = flange_thickness
bore.Base = FreeCAD.Vector(0, 0, 0)

# Create bolt hole pattern
bolt_hole_radius = bolt_hole_diameter / 2
bolt_circle_radius = pitch_circle_diameter / 2
angle_step = 360 / number_bolt_holes

for i in range(number_bolt_holes):
    angle = i * angle_step
    x = bolt_circle_radius * FreeCAD.sin(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Angle))
    y = bolt_circle_radius * FreeCAD.cos(FreeCAD.Units.Quantity(angle, FreeCAD.Units.Angle))
    bolt_hole = body.newObject("PartDesign::Pocket", f"BoltHole{i}")
    bolt_hole.Profile = doc.addObject("Part::Circle", f"BoltHoleProfile{i}")
    bolt_hole.Profile.Radius = bolt_hole_radius
    bolt_hole.Length = flange_thickness
    bolt_hole.Base = FreeCAD.Vector(x, y, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
