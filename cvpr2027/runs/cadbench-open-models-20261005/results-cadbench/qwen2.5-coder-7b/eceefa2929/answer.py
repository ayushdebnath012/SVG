import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the key parameters
outer_diameter = 66.675
flange_thickness = 13.49375
bore_diameter = 23.8125
bolt_circle_diameter = 53.18125
bolt_hole_diameter = 6.746875
number_bolt_holes = 4

# Create the flange body
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = doc.addObject("Part::Circle", "FlangeProfile")
flange.Profile.Radius = outer_diameter / 2
flange.Length = flange_thickness
flange.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Create the through hole
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Profile = doc.addObject("Part::Circle", "ThroughHoleProfile")
through_hole.Profile.Radius = bore_diameter / 2
through_hole.Length = flange_thickness
through_hole.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Create the bolt circle
bolt_circle = body.newObject("PartDesign::Circle", "BoltCircle")
bolt_circle.Radius = bolt_circle_diameter / 2
bolt_circle.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Create the bolt holes
bolt_holes = []
for i in range(number_bolt_holes):
    angle = 2 * i * 3.141592653589793 / number_bolt_holes
    x = bolt_circle.Radius * FreeCAD.sin(angle)
    y = bolt_circle.Radius * FreeCAD.cos(angle)
    bolt_hole = body.newObject("PartDesign::Pocket", f"BoltHole{i}")
    bolt_hole.Profile = doc.addObject("Part::Circle", f"BoltHoleProfile{i}")
    bolt_hole.Profile.Radius = bolt_hole_diameter / 2
    bolt_hole.Length = flange_thickness
    bolt_hole.Base = FreeCAD.Placement(FreeCAD.Vector(x, y, 0), FreeCAD.Rotation())

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
