import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SteppedShaft")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Define the parameters for each shaft section
shaft_sections = [
    (10, 20),
    (15, 30),
    (20, 40),
    (40, 10),
    (30, 20),
    (25, 25),
    (20, 20),
    (50, 20),
    (30, 10)
]

# Create the stepped shaft
for i, (diameter, length) in enumerate(shaft_sections):
    # Create a cylindrical feature
    cylinder = PartDesign.Cylinder(doc, "Cylinder" + str(i + 1))
    cylinder.Radius = diameter / 2
    cylinder.Height = length
    cylinder.Placement.Base = FreeCAD.Vector(0, 0, i * length)
    cylinder.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

    # Add the cylinder to the body
    body.addObject(cylinder)

# Create a solid body from the body
solid_body = PartDesign.Solid(doc, "SolidBody")
solid_body.Base = body

# Save the document
doc.saveAs("/app/answer.FCStd")
