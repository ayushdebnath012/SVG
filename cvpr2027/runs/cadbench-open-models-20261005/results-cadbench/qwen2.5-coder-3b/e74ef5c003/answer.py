import FreeCAD
import PartDesign

# Define the parameters
smooth_shaft_diameter = 30  # mm
smooth_shaft_length = 60  # mm
keyway_width = 6  # mm
keyway_depth = 3  # mm
keyway_height = 30  # mm
num_keyway = 2

# Create a new document
doc = FreeCAD.newDocument("SmoothShaftWithKeyways")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create a cylindrical part
cylinder = PartDesign.Cylinder(doc, "Cylinder", smooth_shaft_diameter / 2, smooth_shaft_length)

# Add the cylinder to the body
body.addObject(cylinder)

# Create keyway features
for i in range(num_keyway):
    keyway = PartDesign.Keyway(doc, f"Keyway_{i+1}", keyway_width, keyway_depth, keyway_height)
    keyway.Base = cylinder
    body.addObject(keyway)

# Save the document
doc.saveAs("/app/answer.FCStd")
