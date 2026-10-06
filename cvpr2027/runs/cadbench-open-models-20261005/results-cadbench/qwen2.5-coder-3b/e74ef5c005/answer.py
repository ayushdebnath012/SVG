import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SmoothShaft")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a PartDesign Body
body = PartDesign.Body()

# Create a PartDesign Cylinder for the smooth shaft
shaft = PartDesign.Cylinder()
shaft.Radius = doc.ParametricObjects["smooth_shaft_diameter"] / 2
shaft.Length = doc.ParametricObjects["smooth_shaft_length"]
shaft.Name = "SmoothShaft"
body.addObject(shaft)

# Create PartDesign Keyway features for each keyway
for i in range(doc.ParametricObjects["num_keyway"]):
    keyway = PartDesign.Keyway()
    keyway.Width = doc.ParametricObjects["keyway_width"]
    keyway.Depth = doc.ParametricObjects["keyway_depth"]
    keyway.Height = doc.ParametricObjects["keyway_height"]
    keyway.Name = f"Keyway_{i+1}"
    body.addObject(keyway)

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")
doc.Body = body

# Save the document
doc.saveAs("/app/answer.FCStd")
