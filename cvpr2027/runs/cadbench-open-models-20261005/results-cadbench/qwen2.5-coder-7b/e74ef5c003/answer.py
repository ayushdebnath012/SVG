import FreeCAD
import PartDesign

# Set up the document
doc = FreeCAD.newDocument("answer")

# Define the parameters
smooth_shaft_diameter = 30  # mm
smooth_shaft_length = 60  # mm
keyway_width = 6  # mm
keyway_depth = 3  # mm
keyway_height = 30  # mm
num_keyway = 2

# Create the PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the smooth shaft
smooth_shaft = body.newObject("PartDesign::Cylinder", "SmoothShaft")
smooth_shaft.Radius = smooth_shaft_diameter / 2
smooth_shaft.Height = smooth_shaft_length

# Create the keyways
keyway_offset = (smooth_shaft_length - keyway_height) / 2
keyway_positions = [keyway_offset + i * keyway_height for i in range(num_keyway)]

for pos in keyway_positions:
    keyway = body.newObject("PartDesign::Pocket", f"Keyway_{pos}")
    keyway.Base = (FreeCAD.Vector(0, 0, pos), FreeCAD.Vector(0, 0, 1))
    keyway.Length = keyway_height
    keyway.Width = keyway_width
    keyway.Depth = keyway_depth

# Finalize the body
body.Touched()

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
