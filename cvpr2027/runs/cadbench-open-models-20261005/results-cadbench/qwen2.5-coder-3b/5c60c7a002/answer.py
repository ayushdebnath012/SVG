import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SmoothShaft")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Define the parameters
shaft_sections = [
    {"diameter": 10, "length": 20},
    {"diameter": 15, "length": 30},
    {"diameter": 20, "length": 40},
    {"diameter": 40, "length": 10},
    {"diameter": 30, "length": 20},
    {"diameter": 25, "length": 25},
    {"diameter": 20, "length": 20},
    {"diameter": 50, "length": 20},
    {"diameter": 30, "length": 10},
    {"diameter": 50, "length": 20},
    {"diameter": 30, "length": 10},
]

# Create the shaft sections
for i, section in enumerate(shaft_sections):
    # Create a cylindrical feature
    cylinder = PartDesign.Cylinder(doc, "Cylinder" + str(i + 1))
    cylinder.Radius = section["diameter"] / 2
    cylinder.Height = section["length"]
    
    # Position the cylinder
    if i > 0:
        cylinder.Placement.Base = body.Shape.Vertexes[-1].Point
    
    # Add the cylinder to the body
    body.addObject(cylinder)

# Save the document
doc.saveAs("/app/answer.FCStd")
