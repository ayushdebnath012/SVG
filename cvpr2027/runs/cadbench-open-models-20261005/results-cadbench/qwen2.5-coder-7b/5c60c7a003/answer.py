import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the shaft sections
sections = [
    {"diameter": 10, "length": 40},
    {"diameter": 15, "length": 30},
    {"diameter": 20, "length": 40},
    {"diameter": 40, "length": 10},
    {"diameter": 30, "length": 20}
]

# Create the shaft sections and join them
previous_feature = None
for section in sections:
    # Create a cylinder for the current section
    cylinder = doc.addObject("PartDesign::Cylinder", f"Cylinder_{section['diameter']}mm")
    cylinder.Radius = section['diameter'] / 2
    cylinder.Height = section['length']
    cylinder.Placement.Base = FreeCAD.Vector(0, 0, 0 if previous_feature is None else previous_feature.Placement.Base.z + previous_feature.Height.Value)
    
    # Add the cylinder to the body
    body.addObject(cylinder)
    
    # Join the current cylinder with the previous one if it exists
    if previous_feature is not None:
        body.addObject(doc.addObject("PartDesign::Fusion", f"Fusion_{section['diameter']}mm"))
        body.Fusion[-1].Base = previous_feature
        body.Fusion[-1].Tool = cylinder
    
    # Update the previous feature to the current one
    previous_feature = cylinder

# Save the document
doc.saveAs("/app/answer.FCStd")
