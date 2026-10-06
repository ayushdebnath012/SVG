import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SlottedHeadlessCylindricalPin")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Cylinder
cylinder = PartDesign.Cylinder()
cylinder.Radius = 0.5  # Diameter / 2
cylinder.Height = 2.5  # Length
cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(0, 0, 0))

# Add the cylinder to the body
body.addObject(cylinder)

# Create a new PartDesign Fillet
fillet = PartDesign.Fillet()
fillet.Radius = 0.04  # Chamfer length / 2
fillet.Shapes = [cylinder.Shape]

# Add the fillet to the body
body.addObject(fillet)

# Create a new PartDesign Slot
slot = PartDesign.Slot()
slot.Width = 0.2  # Slot width
slot.Depth = 0.63  # Slot depth
slot.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(0, 0, 0))

# Add the slot to the body
body.addObject(slot)

# Save the document
doc.saveAs("/app/answer.FCStd")
