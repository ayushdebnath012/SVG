import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("MountingFlange")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Create a PartDesign Body
body = PartDesign.Body()

# Create a circular flange body
flange_body = PartDesign.CircularFlange()
flange_body.OuterDiameter = 69.454
flange_body.FlangeThickness = 13.097
flange_body.InnerDiameter = 34.925
body.addObject(flange_body)

# Create a bolt circle
bolt_circle = PartDesign.BoltCircle()
bolt_circle.PitchCircleDiameter = 56.356
body.addObject(bolt_circle)

# Create bolt holes
number_bolt_holes = 4
for i in range(number_bolt_holes):
    bolt_hole = PartDesign.BoltHole()
    bolt_hole.BoltDiameter = 6.747
    bolt_hole.PitchCircleDiameter = 56.356
    bolt_hole.Position = (0, 0, 0)  # Adjust position as needed
    body.addObject(bolt_hole)

# Add the body to the document
doc.addObject(body)

# Save the document
output_path = __file__.replace(".py", ".FCStd")
doc.saveAs(output_path)

# Close the document
FreeCAD.closeDocument(doc.Name)
