import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical pin
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 0.5  # pin_diameter / 2
cylinder.Height = 3.0  # length

# Create chamfer features
chamfer1 = body.newObject("PartDesign::Chamfer", "Chamfer1")
chamfer1.Base = (cylinder, ["Edge1"])
chamfer1.Length = 0.2  # chamfer_length
chamfer1.Fade = 0.2  # chamfer_length
chamfer1.Angle = 15  # chamfer_angle

chamfer2 = body.newObject("PartDesign::Chamfer", "Chamfer2")
chamfer2.Base = (cylinder, ["Edge2"])
chamfer2.Length = 0.2  # chamfer_length
chamfer2.Fade = 0.2  # chamfer_length
chamfer2.Angle = 15  # chamfer_angle

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
