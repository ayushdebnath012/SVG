import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SmoothShaft")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the sections
sections = [
    {"diameter": 10, "length": 40},
    {"diameter": 15, "length": 30},
    {"diameter": 20, "length": 40},
    {"diameter": 40, "length": 10},
    {"diameter": 30, "length": 20},
    {"diameter": 25, "length": 25}
]

# Create the shaft
shaft = PartDesign.Body(body)
for i, section in enumerate(sections):
    # Create a cylindrical feature
    cylinder = PartDesign.Cylinder(shaft, "Cylinder" + str(i+1))
    cylinder.Radius = section["diameter"] / 2
    cylinder.Height = section["length"]

# Save the document
output_path = __file__.replace(".py", ".FCStd")
doc.saveAs(output_path)

print(f"Model saved to {output_path}")
