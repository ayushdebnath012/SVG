import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SmoothShaftKeyway")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Cylinder
cylinder = PartDesign.Cylinder()
cylinder.Radius = 15  # Diameter / 2
cylinder.Height = 50  # Length
cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the cylinder to the body
body.addObject(cylinder)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 3.5  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 25), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 3.5  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 25), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 180))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 3.5  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 25), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 3.5  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 25), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 270))

# Add the hole to the body
body.addObject(hole)

# Save the document
doc.saveAs("/app/answer.FCStd")
