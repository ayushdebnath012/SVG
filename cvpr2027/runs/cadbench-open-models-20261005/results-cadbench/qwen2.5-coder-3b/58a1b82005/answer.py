import FreeCAD
import PartDesign
import Part

# Create a new document
doc = FreeCAD.newDocument("Shaft")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Create the external spline section
spline = PartDesign.Spline(doc, "Spline")
spline.NumberOfTeeth = 15
spline.Module = 2
spline.PitchDiameter = 30
spline.PressureAngle = 30
spline.Height = 10
spline.addVertex(0, 0, 0)
spline.addVertex(30, 0, 0)
spline.addVertex(30, 10, 0)
spline.addVertex(0, 10, 0)
spline.addVertex(0, 0, 0)
spline.generate()

# Create the smooth shaft section
shaft = PartDesign.Shaft(doc, "Shaft")
shaft.Diameter = 24
shaft.Length = 20
shaft.addVertex(0, 0, 0)
shaft.addVertex(0, 0, 20)
shaft.generate()

# Connect the two sections coaxially
body.addObject(spline)
body.addObject(shaft)
body.connectFeatures(spline, shaft)

# Save the document
doc.saveAs("/app/answer.FCStd")
