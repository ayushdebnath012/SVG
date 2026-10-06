import FreeCAD
import PartDesign
import Part

# Define the parameters
outer_diameter = 125.4125
flange_thickness = 23.01875
bore_diameter = 64.690625
bolt_circle_diameter = 103.1875
bolt_hole_diameter = 13.49375
number_of_bolt_holes = 4

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create a cylindrical flange body
cylinder = PartDesign.Cylinder(doc, "Cylinder", outer_diameter, flange_thickness)
body.addObject(cylinder)

# Create a plain through bore
bore = PartDesign.PlainThroughBore(doc, "Bore", bore_diameter)
bore.Base = cylinder
body.addObject(bore)

# Create a bolt circle
bolt_circle = PartDesign.BoltCircle(doc, "BoltCircle", bolt_circle_diameter)
body.addObject(bolt_circle)

# Create bolt holes
for i in range(number_of_bolt_holes):
    hole = PartDesign.BoltHole(doc, f"BoltHole_{i+1}", bolt_hole_diameter)
    hole.Base = bolt_circle
    body.addObject(hole)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
