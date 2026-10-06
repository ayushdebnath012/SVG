import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical feature
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 5.0 / 2.0  # Diameter to radius conversion
cylinder.Height = 10.0
cylinder.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Pad feature
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Length = 3.0
pad.BaseFeature = cylinder
pad.BaseOffset = FreeCAD.Vector(0, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
