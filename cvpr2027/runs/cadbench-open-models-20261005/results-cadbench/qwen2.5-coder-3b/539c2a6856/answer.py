import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HexFlangeNut")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Create a new Hexagonal Hub
hex_hub = PartDesign.HexagonalHub()
hex_hub.HubWidth = 46.0
hex_hub.HubHeight = 46.0
body.addObject(hex_hub)

# Create a new Circular Flange
flange = PartDesign.CircularFlange()
flange.FlangeDiameter = 58.0
flange.FlangeThickness = 8.0
body.addObject(flange)

# Create a new Plain Through Hole
through_hole = PartDesign.PlainThroughHole()
through_hole.InnerDiameter = 30.0
through_hole.HoleDepth = 45.0
body.addObject(through_hole)

# Create a new Part::Feature to hold the body
feature = Part.Feature()
feature.Shape = body.Shape
doc.addObject(feature)

# Save the document
doc.saveAs("/app/answer.FCStd")
