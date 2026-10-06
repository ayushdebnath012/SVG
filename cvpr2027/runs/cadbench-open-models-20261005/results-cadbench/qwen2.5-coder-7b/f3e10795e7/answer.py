import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the frustum
frustum = body.newObject("PartDesign::Cylinder", "Frustum")
frustum.Radius = 15.0 / 2.0  # top diameter / 2
frustum.Height = 30.0
frustum.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the bottom diameter
bottom_diameter = body.newObject("PartDesign::Cylinder", "BottomDiameter")
bottom_diameter.Radius = 25.0 / 2.0  # bottom diameter / 2
bottom_diameter.Height = 30.0
bottom_diameter.Placement.Base = FreeCAD.Vector(0, 0, -30.0)

# Create a PartDesign Feature for the cutout
cutout = body.newObject("PartDesign::Pocket", "Cutout")
cutout.Base = frustum
cutout.Profile = bottom_diameter
cutout.Length = 30.0

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
