import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Dumbbell")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a PartDesign Body
body = PartDesign.Body()

# Add the body to the document
doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical handle
handle_length = 110.0
handle_diameter = 28.0
handle = PartDesign.Cylinder(doc, "Handle", handle_length, handle_diameter / 2)

# Add the handle to the body
body.addObject(handle)

# Create a hexagonal prism end weight
hex_height = 30.0
cross_flat_width = 80.0
hex_end = PartDesign.HexPrism(doc, "HexEnd", cross_flat_width, hex_height)

# Add the hex end to the body
body.addObject(hex_end)

# Position the hex ends on the handle
hex_end1 = hex_end.copy()
hex_end1.Placement.Base = FreeCAD.Vector(0, 0, handle_length / 2)
body.addObject(hex_end1)

hex_end2 = hex_end.copy()
hex_end2.Placement.Base = FreeCAD.Vector(0, 0, -handle_length / 2)
body.addObject(hex_end2)

# Create a Part::Feature to hold the body
feature = Part.Feature()
feature.Shape = body.Shape
feature.Label = "Dumbbell"
doc.addObject("Part::Feature", "Dumbbell")

# Save the document
doc.saveAs("/app/answer.FCStd")
