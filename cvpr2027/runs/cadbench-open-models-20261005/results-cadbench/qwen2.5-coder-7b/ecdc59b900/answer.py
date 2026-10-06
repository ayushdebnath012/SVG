import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the parameters
section_diameters = [10, 15, 20, 40, 30, 25, 20]
section_lengths = [20, 30, 40, 10, 20, 25, 20]

# Create the stepped cylindrical component
current_length = 0
for i in range(7):
    # Create a cylindrical section
    cylinder = body.newObject("PartDesign::Cylinder", f"Cylinder_{i+1}")
    cylinder.Radius = section_diameters[i] / 2
    cylinder.Height = section_lengths[i]
    cylinder.Placement.Base = FreeCAD.Vector(0, 0, current_length)
    
    # Add the section to the body
    body.addObject(cylinder)
    
    # Update the current length
    current_length += section_lengths[i]

# Finalize the body
body.Tip = body[-1].Name

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))

# Close the document
FreeCAD.closeDocument(doc.Name)
