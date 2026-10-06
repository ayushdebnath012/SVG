import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical shaft
shaft = body.newObject("PartDesign::Cylinder", "Shaft")
shaft.Radius = 1.5  # pin_diameter / 2
shaft.Height = 6.0  # pin_length

# Create a cylindrical head
head = body.newObject("PartDesign::Cylinder", "Head")
head.Radius = 2.5  # head_diameter / 2
head.Height = 1.0  # head_thickness

# Position the head on top of the shaft
head.Placement.Base = FreeCAD.Vector(0, 0, 6.0)

# Create a chamfer on the head
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Base = head
chamfer.Length1 = 1.0  # chamfer_length
chamfer.BaseEdge = [head.Edges[0]]  # Chamfer on the top edge of the head

# Position the chamfer on the head
chamfer.Placement.Base = FreeCAD.Vector(0, 0, 6.0 + 1.0)

# Finalize the body
body.finish()

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
