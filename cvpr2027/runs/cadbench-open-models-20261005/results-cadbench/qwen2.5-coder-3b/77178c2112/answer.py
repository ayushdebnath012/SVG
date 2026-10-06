import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("CylindricalPin")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new Cylinder
cylinder = PartDesign.Cylinder()
cylinder.Radius = 0.5  # Diameter / 2
cylinder.Height = 3.0  # Length
cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(0, 0, 0))

# Add the cylinder to the body
body.addObject(cylinder)

# Create a new Chamfer
chamfer = PartDesign.Chamfer()
chamfer.Length = 0.2  # Chamfer length
chamfer.Angle = 15  # Chamfer angle in degrees
chamfer.Base = cylinder

# Add the chamfer to the body
body.addObject(chamfer)

# Save the document
doc.saveAs("/app/answer.FCStd")
