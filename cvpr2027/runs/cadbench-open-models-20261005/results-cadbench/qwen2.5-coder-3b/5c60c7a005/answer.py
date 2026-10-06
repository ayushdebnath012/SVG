import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SteppedShaft")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Define the sections
sections = [
    (10, 20),  # section_1
    (15, 30),  # section_2
    (20, 40),  # section_3
    (40, 10),  # section_4
    (30, 20),  # section_5
    (25, 25),  # section_6
    (20, 20),  # section_7
    (50, 20)   # section_8
]

# Create the stepped shaft
for i, (diameter, length) in enumerate(sections):
    # Create a cylindrical section
    cylinder = PartDesign.Cylinder(doc, diameter, length)
    cylinder.Label = f"section_{i+1}"
    
    # Add the cylinder to the body
    body.addObject(cylinder)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
