import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Washer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a washer body
washer_body = body.newObject("PartDesign::Pad", "WasherBody")
washer_body.Length = FreeCAD.Units.Quantity(10.0, FreeCAD.Units.Length)
washer_body.Profile = body.newObject("PartDesign::Circle", "WasherProfile")
washer_body.Profile.Radius = FreeCAD.Units.Quantity(30.0, FreeCAD.Units.Length)

# Create a square neck hole
square_neck_hole = body.newObject("PartDesign::Pocket", "SquareNeckHole")
square_neck_hole.Length = FreeCAD.Units.Quantity(20.0, FreeCAD.Units.Length)
square_neck_hole.Profile = body.newObject("PartDesign::Rectangle", "SquareNeckProfile")
square_neck_hole.Profile.Length = FreeCAD.Units.Quantity(20.0, FreeCAD.Units.Length)
square_neck_hole.Profile.Width = FreeCAD.Units.Quantity(20.0, FreeCAD.Units.Length)
square_neck_hole.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 5.0), FreeCAD.Rotation())

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
