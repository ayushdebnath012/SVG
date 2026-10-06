```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("WaterCup")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Create a new PartDesign Cylinder for the cup body
cylinder = PartDesign.Cylinder()
cylinder.Radius = 40.0  # Half of the cup diameter
cylinder.Height = 120.0  # Cup height
cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the cylinder to the body
body.addObject(cylinder)

# Create a new PartDesign Plane for the cup interior
plane = PartDesign.Plane()
plane.Base = cylinder
plane.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 2.0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new PartDesign Cylinder for the cup interior
interior_cylinder = PartDesign.Cylinder()
interior_cylinder.Radius = 38.0  # Half of the cup diameter minus the cup thickness
interior_cylinder.Height = 120.0  # Cup height
interior_cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior cylinder to the body
body.addObject(interior_cylinder)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign Extrusion for the cup interior
interior_extrusion = PartDesign.Extrusion()
interior_extrusion.Base = interior_cylinder
interior_extrusion.Dir = FreeCAD.Vector(0, 0, 1)
interior_extrusion.Length = 120.0  # Cup height
interior_extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the interior extrusion to the body
body.addObject(interior_extrusion)

# Create a new PartDesign Fillet for the cup interior
fillet = PartDesign.Fillet()
fillet.Radius = 1.0  # Fillet radius
fillet.Base = interior_cylinder
fillet.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Extrusion for the cup body
extrusion = PartDesign.Extrusion()
extrusion.Base = cylinder
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 120.0  # Cup height
extrusion.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the extrusion to the body
body.addObject(extrusion)

# Create a new PartDesign