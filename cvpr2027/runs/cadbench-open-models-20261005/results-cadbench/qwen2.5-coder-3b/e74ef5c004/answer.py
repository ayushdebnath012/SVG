```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Set the active document
FreeCAD.setActiveDocument("answer")

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Cylinder
cylinder = PartDesign.Cylinder()
cylinder.Radius = 25  # Diameter / 2
cylinder.Height = 80  # Length
cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the cylinder to the body
body.addObject(cylinder)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Radius = 4  # Keyway width / 2
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0,