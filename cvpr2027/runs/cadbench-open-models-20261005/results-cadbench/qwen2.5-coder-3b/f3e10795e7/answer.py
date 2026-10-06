import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Frustum")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new PartDesign frustum feature
frustum = PartDesign.Frustum(body)

# Set the parameters for the frustum
frustum.TopDiameter = 15.0
frustum.BottomDiameter = 25.0
frustum.Height = 30.0

# Add the frustum to the body
body.addObject(frustum)

# Save the document
doc.saveAs("/app/answer.FCStd")
