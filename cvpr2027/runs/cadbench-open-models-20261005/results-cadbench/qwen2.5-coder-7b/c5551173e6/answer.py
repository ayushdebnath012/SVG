import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical rod
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 3  # pin_diameter / 2
cylinder.Height = 6.0  # pin_length

# Create a chamfer
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Base = cylinder
chamfer.Length1 = 1.0  # chamfer_length
chamfer.BaseEdge = [cylinder.Shape.Edges[0]]

# Finalize the body
body.addFeature(chamfer)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
