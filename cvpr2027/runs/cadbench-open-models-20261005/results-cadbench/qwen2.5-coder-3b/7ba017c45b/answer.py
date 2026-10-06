import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HexFlangeNut")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a PartDesign Body
body = PartDesign.Body()

# Set the active body
doc.addObject("PartDesign::Body", "Body")
doc.ActiveBody = body

# Create a Hexagonal Hub Section
hex_hub = PartDesign.HexagonalHubSection()
hex_hub.Name = "HexHub"
hex_hub.HubWidth = 10.0
hex_hub.HexHeadWidthAcrossFlats = 10.0
hex_hub.HexHeadWidthAcrossCorners = 11.547005383792516
hex_hub.HexHeadAngle = 30.0
doc.addObject("PartDesign::HexagonalHubSection", "HexHub")
doc.ActiveBody.addObject(hex_hub)

# Create a Circular Flange
flange = PartDesign.CircularFlange()
flange.Name = "Flange"
flange.FlangeDiameter = 14.0
flange.FlangeThickness = 3.0
doc.addObject("PartDesign::CircularFlange", "Flange")
doc.ActiveBody.addObject(flange)

# Create a Plain Through Bore
bore = PartDesign.PlainThroughBore()
bore.Name = "Bore"
bore.BoreDiameter = 6.0
doc.addObject("PartDesign::PlainThroughBore", "Bore")
doc.ActiveBody.addObject(bore)

# Create a PartDesign Body from the features
body = PartDesign.Body()
body.Name = "Body"
doc.addObject("PartDesign::Body", "Body")
doc.ActiveBody = body
doc.ActiveBody.addObject(hex_hub)
doc.ActiveBody.addObject(flange)
doc.ActiveBody.addObject(bore)

# Save the document
doc.saveAs("/app/answer.FCStd")
