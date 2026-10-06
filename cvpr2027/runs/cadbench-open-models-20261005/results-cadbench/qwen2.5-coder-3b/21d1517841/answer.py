import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("LargeWasher")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a new PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a new PartDesign Hole
hole = PartDesign.Hole()

# Set the parameters for the hole
hole.Radius = 1.6  # Inner diameter / 2
hole.Diameter = 3.2  # Inner diameter
hole.Depth = 0.8  # Thickness

# Add the hole to the body
body.addObject(hole)

# Create a new PartDesign Plane
plane = PartDesign.Plane()

# Set the parameters for the plane
plane.Base = doc.ActiveObject  # Use the hole as the base
plane.Normal = FreeCAD.Vector(0, 0, 1)  # Normal vector

# Add the plane to the body
body.addObject(plane)

# Create a new PartDesign Extrusion
extrusion = PartDesign.Extrusion()

# Set the parameters for the extrusion
extrusion.Base = plane
extrusion.Dir = FreeCAD.Vector(0, 0, 1)
extrusion.Length = 9.0  # Outer diameter

# Add the extrusion to the body
body.addObject(extrusion)

# Save the document
doc.saveAs("/app/answer.FCStd")
