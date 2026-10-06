import FreeCAD
import PartDesign

# Set up the document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the smooth shaft
smooth_shaft_diameter = 50
smooth_shaft_length = 80
cylinder = body.newObject("PartDesign::Cylinder", "SmoothShaft")
cylinder.Radius = smooth_shaft_diameter / 2
cylinder.Height = smooth_shaft_length
cylinder.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the keyways
keyway_width = 5
keyway_depth = 3
keyway_height = 20
num_keyway = 2
keyway_spacing = (smooth_shaft_length - keyway_height) / (num_keyway + 1)

for i in range(num_keyway):
    keyway = body.newObject("PartDesign::Pocket", f"Keyway{i+1}")
    keyway.Base = cylinder
    keyway.Length = keyway_height
    keyway.Width = keyway_width
    keyway.Depth = keyway_depth
    keyway.Placement.Base = FreeCAD.Vector(0, 0, keyway_spacing * (i + 1))

# Save the document
doc.saveAs("/app/answer.FCStd")
FreeCAD.closeDocument(doc.Name)
