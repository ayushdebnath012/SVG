import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SmoothShaft")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Define the parameters
smooth_shaft_diameter = 50  # mm
smooth_shaft_length = 80   # mm
keyway_width = 5          # mm
keyway_depth = 3          # mm
keyway_height = 20         # mm
num_keyway = 2

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a Cylinder for the smooth shaft
cylinder = PartDesign.Body.addObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = smooth_shaft_diameter / 2
cylinder.Height = smooth_shaft_length

# Add the cylinder to the body
body.addObject(cylinder)

# Create a Keyway for each keyway
for i in range(num_keyway):
    keyway = PartDesign.Body.addObject("PartDesign::Keyway", f"Keyway_{i+1}")
    keyway.Width = keyway_width
    keyway.Depth = keyway_depth
    keyway.Height = keyway_height
    keyway.Cylinder = cylinder

# Save the document
doc.saveAs("runs/cadbench-qwen3b-pilot-20261005/b0baf87576/answer.FCStd")
