import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SmoothShaft")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Define the parameters
section_diameters = [10, 15, 20, 40, 30, 25, 20]
section_lengths = [20, 30, 40, 10, 20, 25, 20]

# Create the stepped shaft
for i in range(7):
    # Create a cylindrical section
    cylinder = PartDesign.Cylinder(doc, "Cylinder" + str(i+1))
    cylinder.Radius = section_diameters[i] / 2
    cylinder.Height = section_lengths[i]
    
    # Add the cylinder to the body
    body.addObject(cylinder)

# Save the document
doc.saveAs("/app/answer.FCStd")
