import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Pin")

# Set the active document
FreeCAD.setActiveDocument("Pin")

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new Cylinder feature
cylinder = PartDesign.Cylinder()
cylinder.Radius = 1.5  # Diameter / 2
cylinder.Height = 6.0  # Length
cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(0, 0, 0))

# Add the cylinder to the body
body.addObject(cylinder)

# Create a new Chamfer feature
chamfer = PartDesign.Chamfer()
chamfer.Base = cylinder
chamfer.Length = 1.0  # Chamfer length
chamfer.Angle = 30  # Chamfer angle in degrees

# Add the chamfer to the body
body.addObject(chamfer)

# Save the document
doc.saveAs("/app/answer.FCStd")
