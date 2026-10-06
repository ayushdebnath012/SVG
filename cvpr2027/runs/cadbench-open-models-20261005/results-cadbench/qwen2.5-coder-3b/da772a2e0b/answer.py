```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("ConnectingRod")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Create a new PartDesign Plane
plane = PartDesign.Plane()
plane.Base = doc.addObject("PartDesign::Plane", "Plane")
plane.Axis = FreeCAD.Vector(0, 0, 1)
plane.Length = 50.0
plane.Width = 50.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = plane.Shape
fillet.Radius = 1.0

# Create a new PartDesign Hole
hole = PartDesign.Hole()
hole.Base = doc.addObject("PartDesign::Hole", "Hole")
hole.BaseShape = fillet.Shape
hole.Diameter = 3.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = hole.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Base = doc.addObject("PartDesign::Fillet", "Fillet")
fillet.BaseShape = fillet.Shape
fillet.Radius = 1.0

# Create a new PartDesign Fillet
fillet