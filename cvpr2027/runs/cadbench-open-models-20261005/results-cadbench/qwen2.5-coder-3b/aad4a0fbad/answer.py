import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
hole_diameter = 8  # mm
nut_thickness = 10  # mm
hole_cut_depth = 30  # mm

# Calculate across_flats if not provided
if 'across_flats' not in locals():
    across_flats = hole_diameter * 13 / 100  # ISO default proportion

# Calculate across_corners
across_corners = across_flats / math.cos(math.radians(30))

# Create the nut body
nut_body = PartDesign.Body()
nut_body.addObject(PartDesign.Extrusion())
nut_body.Extrusion.Base = Part.makeBox(hole_diameter, nut_thickness, nut_thickness)
nut_body.Extrusion.Dir = (0, 0, 1)
nut_body.Extrusion.Solid = True

# Create the through hole
through_hole = PartDesign.Body()
through_hole.addObject(PartDesign.Extrusion())
through_hole.Extrusion.Base = Part.makeCylinder(hole_diameter / 2, hole_cut_depth)
through_hole.Extrusion.Dir = (0, 0, 1)
through_hole.Extrusion.Solid = True

# Subtract the through hole from the nut body
nut_body.addObject(PartDesign.Subtractive())
nut_body.Subtractive.Base = nut_body
nut_body.Subtractive.Tool = through_hole

# Create a PartDesign body to hold the nut body
body = PartDesign.Body()
body.addObject(nut_body)

# Save the model
output_path = FreeCAD.getHomePath() + '/app/answer.FCStd'
body.saveAs(output_path)
