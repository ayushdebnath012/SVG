import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Key")

# Set the active document
FreeCAD.setActiveDocument("Key")

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Cylinder
cylinder = PartDesign.Cylinder()

# Set the parameters for the cylinder
cylinder.Radius = 2.5  # Diameter / 2
cylinder.Height = 3.0  # Height
cylinder.Length = 10.0  # Length

# Add the cylinder to the body
body.addObject(cylinder)

# Save the document
doc.saveAs("/app/answer.FCStd")
