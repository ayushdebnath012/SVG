import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SteppedShaft")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Define the parameters for each shaft section
shaft_sections = [
    {"diameter": 10, "length": 40},
    {"diameter": 15, "length": 30},
    {"diameter": 20, "length": 40},
    {"diameter": 40, "length": 10},
    {"diameter": 30, "length": 20}
]

# Create the stepped shaft
for i, section in enumerate(shaft_sections):
    # Create a cylindrical feature for the current section
    cylinder = PartDesign.Cylinder(doc, "Cylinder" + str(i + 1))
    cylinder.Radius = section["diameter"] / 2
    cylinder.Height = section["length"]
    
    # Add the cylinder to the body
    body.addObject(cylinder)

# Join the cylinders end-to-end
body.JoinFeatures()

# Save the document
doc.saveAs("/app/answer.FCStd")
