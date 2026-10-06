import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define key parameters
inner_diameter = 34.925
outer_diameter = 69.454
flange_thickness = 26.194
pitch_circle_diameter = 57.547
bolt_hole_diameter = 6.747
number_bolt_holes = 4

# Create a circular flange body
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = doc.addObject("Part::Circle", "FlangeProfile")
flange.Profile.Radius = outer_diameter / 2
flange.Length = flange_thickness
flange.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Create a central through bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = doc.addObject("Part::Circle", "BoreProfile")
bore.Profile.Radius = inner_diameter / 2
bore.Length = flange_thickness
bore.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Create a bolt circle
bolt_circle = body.newObject("PartDesign::Circle", "BoltCircle")
bolt_circle.Radius = pitch_circle_diameter / 2
bolt_circle.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Create bolt holes
bolt_hole_radius = bolt_hole_diameter / 2
bolt_hole_distance = pitch_circle_diameter / number_bolt_holes
for i in range(number_bolt_holes):
    angle = 2 * i * 3.141592653589793 / number_bolt_holes
    x = bolt_hole_distance * 0.5 * (1 + 0.5 * (i % 2))
    y = bolt_hole_distance * 0.5 * (1 + 0.5 * (i % 2))
    z = 0
    bolt_hole = body.newObject("PartDesign::Pocket", f"BoltHole{i}")
    bolt_hole.Profile = doc.addObject("Part::Circle", f"BoltHoleProfile{i}")
    bolt_hole.Profile.Radius = bolt_hole_radius
    bolt_hole.Length = flange_thickness
    bolt_hole.Base = FreeCAD.Placement(FreeCAD.Vector(x, y, z), FreeCAD.Rotation())

# Save the document
doc.saveAs("/app/answer.FCStd")
