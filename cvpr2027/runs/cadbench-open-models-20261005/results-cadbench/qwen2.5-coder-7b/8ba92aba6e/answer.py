import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the outer circle
outer_circle = body.newObject("PartDesign::Circle", "OuterCircle")
outer_circle.Radius = 2.0  # half of the outer diameter
outer_circle.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the inner circle
inner_circle = body.newObject("PartDesign::Circle", "InnerCircle")
inner_circle.Radius = 0.85  # half of the inner diameter
inner_circle.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the extrusion
extrusion = body.newObject("PartDesign::Pad", "Extrusion")
extrusion.Profile = outer_circle
extrusion.Length = 0.15  # half of the thickness
extrusion.LengthFwd = 0.15
extrusion.LengthRev = 0.15

# Create a PartDesign Feature for the hole
hole = body.newObject("PartDesign::Pocket", "Hole")
hole.Profile = inner_circle
hole.Length = 0.15  # half of the thickness
hole.LengthFwd = 0.15
hole.LengthRev = 0.15

# Save the document
doc.saveAs("/app/answer.FCStd")
