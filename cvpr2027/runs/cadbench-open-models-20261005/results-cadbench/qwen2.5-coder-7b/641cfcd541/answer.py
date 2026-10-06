import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the hexagonal body
hex_body = body.newObject("PartDesign::Pad", "HexBody")
hex_body.Length = 9.525  # overall_length
hex_body.Profile = Part.makePolygon([
    FreeCAD.Vector(-3.175, 0, 0),
    FreeCAD.Vector(-2.588, 3.42, 0),
    FreeCAD.Vector(-0.866, 3.42, 0),
    FreeCAD.Vector(0, 0, 0),
    FreeCAD.Vector(-0.866, -3.42, 0),
    FreeCAD.Vector(-2.588, -3.42, 0),
    FreeCAD.Vector(-3.175, 0, 0)
])

# Create a PartDesign Feature for the through hole
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Length = 9.525  # overall_length
through_hole.Profile = Part.makeCircle(1.4224)  # through_hole_diameter / 2

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
