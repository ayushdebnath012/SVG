import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Washer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a square plate
square_plate = body.newObject("PartDesign::Pad", "SquarePlate")
square_plate.Profile = doc.addObject("Part::Box", "SquareProfile")
square_plate.Profile.Length = 40
square_plate.Profile.Width = 40
square_plate.Profile.Height = 5
square_plate.Length = 5

# Create a central hole
central_hole = body.newObject("PartDesign::Pocket", "CentralHole")
central_hole.Profile = doc.addObject("Part::Cylinder", "HoleProfile")
central_hole.Profile.Radius = 7.5 / 2
central_hole.Profile.Height = 5
central_hole.Length = 5

# Save the document
doc.saveAs("/app/answer.FCStd")
FreeCAD.closeDocument(doc.Name)
