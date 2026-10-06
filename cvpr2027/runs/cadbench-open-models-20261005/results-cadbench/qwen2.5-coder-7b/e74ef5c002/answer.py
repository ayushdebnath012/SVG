import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical shaft
shaft = body.newObject("PartDesign::Cylinder", "SmoothShaft")
shaft.Radius = 25  # half of the diameter
shaft.Height = 80
shaft.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create keyway features
keyway_width = 5
keyway_depth = 5
keyway_height = 20
num_keyways = 2

for i in range(num_keyways):
    keyway = body.newObject("PartDesign::Pocket", f"Keyway{i+1}")
    keyway.Base = shaft
    keyway.Length = keyway_height
    keyway.LengthFuzz = 0
    keyway.BaseOffset = keyway_width * i + keyway_width / 2
    keyway.BaseOffsetFuzz = 0
    keyway.Radius = keyway_depth / 2
    keyway.RadiusFuzz = 0
    keyway.Reversed = True

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
