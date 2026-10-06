import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical shaft
smooth_shaft_diameter = 50
smooth_shaft_length = 80
cylinder = body.newObject("PartDesign::Cylinder", "SmoothShaft")
cylinder.Radius = smooth_shaft_diameter / 2
cylinder.Height = smooth_shaft_length
cylinder.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create keyway parameters
keyway_width = 8
keyway_depth = 4
keyway_height = 50
num_keyway = 1

# Create keyways
for i in range(num_keyway):
    keyway = body.newObject("PartDesign::Pocket", f"Keyway{i+1}")
    keyway.Base = cylinder.Shape
    keyway.Length = keyway_height
    keyway.LengthFilletRadius = keyway_width / 2
    keyway.BaseOffset = keyway_depth / 2
    keyway.BaseAngle = 360 / num_keyway
    keyway.BaseAxis = FreeCAD.Vector(0, 0, 1)
    keyway.BaseOffsetMode = 0
    keyway.BaseOffsetAxis = FreeCAD.Vector(1, 0, 0)
    keyway.BaseOffsetAngle = 0

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))

# Close the document
FreeCAD.closeDocument(doc.Name)
