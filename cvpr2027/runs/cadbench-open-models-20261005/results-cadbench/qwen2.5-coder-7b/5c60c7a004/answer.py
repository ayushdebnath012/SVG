import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the shaft section parameters
sections = [
    {"diameter": 10, "length": 20},
    {"diameter": 15, "length": 30},
    {"diameter": 20, "length": 40},
    {"diameter": 40, "length": 10},
    {"diameter": 30, "length": 20},
    {"diameter": 25, "length": 25},
    {"diameter": 20, "length": 20},
    {"diameter": 50, "length": 20},
    {"diameter": 30, "length": 10}
]

# Create the shaft sections
for i, section in enumerate(sections):
    # Create a new shaft section
    shaft = body.newObject("PartDesign::Cylinder", f"Shaft_{i+1}")
    shaft.Radius = section["diameter"] / 2
    shaft.Height = section["length"]
    shaft.Placement.Base = FreeCAD.Vector(0, 0, sum(s["length"] for s in sections[:i]))

# Finalize the body
body.Tip = body[-1]
body.recompute()

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
