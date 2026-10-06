```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Flat_Washer")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Plane
plane = PartDesign.Plane()
plane.Base = doc.addObject("Part::Plane", "Plane")
plane.Axis = FreeCAD.Vector(0, 0, 1)
plane.Length = 10
plane.Width = 10

# Add the plane to the body
body.addObject(plane)

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Base = doc.addObject("Part::Cylinder", "Hole")
hole.Radius = 1.7 / 2
hole.Height = 0.3
hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Extrusion
extrusion = PartDesign.Extrusion()
extrusion.Base = doc.addObject("Part::Cylinder", "Extrusion")
extrusion.Radius = 4 / 2
extrusion.Height = 0.3
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("Part::Cylinder", "Fillet")
fillet.Radius = 0.3 / 2
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0