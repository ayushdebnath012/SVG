import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Feature for the bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = 0.3  # bore_diameter / 2
bore.Height = 0.8  # bearing_width

# Create a PartDesign Feature for the raceway
raceway = body.newObject("PartDesign::Pocket", "Raceway")
raceway.Base = bore
raceway.Length = 0.8 * 0.4  # bearing_width * raceway_depth_ratio
raceway.Direction = FreeCAD.Vector(0, 0, 1)

# Create a PartDesign Feature for the shoulder
shoulder = body.newObject("PartDesign::Pocket", "Shoulder")
shoulder.Base = raceway
shoulder.Length = 0.8  # bearing_width
shoulder.Direction = FreeCAD.Vector(0, 0, 1)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
