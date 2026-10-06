import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SmoothShaft")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Define the sections
sections = [
    (10, 40),  # section_1_diameter/section_1_length
    (15, 30),  # section_2_diameter/section_2_length
    (20, 40),  # section_3_diameter/section_3_length
    (40, 10),  # section_4_diameter/section_4_length
    (30, 20),  # section_5_diameter/section_5_length
    (25, 25)   # section_6_diameter/section_6_length
]

# Create the smooth shaft
for i, (diameter, length) in enumerate(sections):
    # Create a cylindrical feature
    cylinder = PartDesign.Cylinder(doc, diameter, length)
    cylinder.Label = f"Section_{i+1}"
    
    # Add the cylinder to the body
    body.addObject(cylinder)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
