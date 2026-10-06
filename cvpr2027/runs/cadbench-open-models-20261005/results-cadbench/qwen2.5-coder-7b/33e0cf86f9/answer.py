import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HalfMoonKey")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the half moon key
key = body.newObject("PartDesign::Pad", "Key")
key.Length = 1.4  # moon_height
key.Profile = body.newObject("PartDesign::Pocket", "Pocket")
key.Profile.Length = 1.0  # key_thickness
key.Profile.Profile = Part.makeCircle(2.0)  # radius = diameter / 2

# Create a PartDesign Feature for the keyway
keyway = body.newObject("PartDesign::Pocket", "Keyway")
keyway.Length = 1.0  # key_thickness
keyway.Profile = body.newObject("PartDesign::Pocket", "KeywayProfile")
keyway.Profile.Length = 1.0  # key_thickness
keyway.Profile.Profile = Part.makeCircle(2.0)  # radius = diameter / 2

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
