import FreeCAD
import PartDesign

# Define the parameters
outer_diameter = 66.675
flange_thickness = 13.49375
pitch_circle_diameter = 53.18125
bolt_hole_diameter = 6.746875
number_bolt_holes = 4
inner_diameter = 25.4

# Create a new document
doc = FreeCAD.newDocument("Flange")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create a circular flange body
flange_body = PartDesign.CircularFlange(doc, "FlangeBody")
flange_body.OuterDiameter = outer_diameter
flange_body.FlangeThickness = flange_thickness
body.addObject(flange_body)

# Create a central plain through hole
through_hole = PartDesign.PlainThroughHole(doc, "ThroughHole")
through_hole.InnerDiameter = inner_diameter
through_hole.FlangeBody = flange_body
body.addObject(through_hole)

# Create a bolt pattern
bolt_pattern = PartDesign.BoltPattern(doc, "BoltPattern")
bolt_pattern.NumberBoltHoles = number_bolt_holes
bolt_pattern.BoltHoleDiameter = bolt_hole_diameter
bolt_pattern.PitchCircleDiameter = pitch_circle_diameter
bolt_pattern.FlangeBody = flange_body
body.addObject(bolt_pattern)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
