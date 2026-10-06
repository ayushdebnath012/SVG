import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the shaft sections
sections = [
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
    {"diameter": 30, "length": 10}
]

# Create the shaft sections
current_position = 0
for section in sections:
    # Create a cylinder for the current section
    cylinder = doc.addObject("PartDesign::Cylinder", f"Cylinder_{current_position+1}")
    cylinder.Radius = section["diameter"] / 2
    cylinder.Height = section["length"]
    cylinder.Placement.Base = FreeCAD.Vector(0, 0, current_position)
    
    # Add the cylinder to the body
    body.addObject(cylinder)
    
    # Update the current position
    current_position += section["length"]

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
