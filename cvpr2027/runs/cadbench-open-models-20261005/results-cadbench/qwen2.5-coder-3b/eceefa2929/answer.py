import FreeCAD
import PartDesign
import Part

# Define the parameters
bore_diameter = 23.8125
outer_diameter = 66.675
flange_thickness = 13.49375
bolt_circle_diameter = 53.18125
bolt_hole_diameter = 6.746875
number_bolt_holes = 4

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new circular flange body
flange_body = PartDesign.CircularFlange(doc, "FlangeBody")
flange_body.OuterDiameter = outer_diameter
flange_body.FlangeThickness = flange_thickness
flange_body.BoreDiameter = bore_diameter
flange_body.BoltCircleDiameter = bolt_circle_diameter
flange_body.NumberOfBoltHoles = number_bolt_holes
flange_body.BoltHoleDiameter = bolt_hole_diameter

# Add the circular flange body to the body
body.addObject(flange_body)

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new circular flange body
flange_body = PartDesign.CircularFlange(doc, "FlangeBody")
flange_body.OuterDiameter = outer_diameter
flange_body.FlangeThickness = flange_thickness
flange_body.BoreDiameter = bore_diameter
flange_body.BoltCircleDiameter = bolt_circle_diameter
flange_body.NumberOfBoltHoles = number_bolt_holes
flange_body.BoltHoleDiameter = bolt_hole_diameter

# Add the circular flange body to the body
body.addObject(flange_body)

# Save the document
doc.saveAs("/app/answer.FCStd")
