import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the first section: external spline
spline = body.newObject("PartDesign::Spline", "Spline")
spline.NumberOfPoints = 100
spline.StartPoint = FreeCAD.Vector(0, 0, 0)
spline.EndPoint = FreeCAD.Vector(0, 0, 10)
spline.Radius = 15
spline.Height = 10
spline.Profile = "Spline"
spline.ProfileParameters = [15, 2, 30, 30, 10]

# Create the second section: smooth shaft
shaft = body.newObject("PartDesign::Cylinder", "Shaft")
shaft.Radius = 12
shaft.Height = 20
shaft.Placement.Base = FreeCAD.Vector(0, 0, 10)

# Add a fillet to connect the two sections
fillet = body.newObject("PartDesign::Fillet", "Fillet")
fillet.Base = shaft
fillet.Radius = 12
fillet.Edges = [shaft.Shape.Edges[0]]

# Finalize the body
body.Tip = fillet

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
