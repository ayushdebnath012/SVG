import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a hexagonal nut body
hex_nut_width_across_flats = 16.0
hex_nut_width_across_corners = hex_nut_width_across_flats / math.cos(math.radians(30))
hex_nut_half_angle = 30.0

hex_nut = PartDesign.makeCylinder(hex_nut_width_across_flats / 2, hex_nut_width_across_flats / 2 * math.sqrt(3))
hex_nut.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), hex_nut_half_angle))
body.addObject(hex_nut)

# Create a circular flange
flange_diameter = 22.0
flange_thickness = 4.0

flange = PartDesign.makeCylinder(flange_diameter / 2, flange_thickness)
flange.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, -flange_thickness / 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
body.addObject(flange)

# Create a through hole
inner_diameter = 10.0
overall_height = 15.0

through_hole = PartDesign.makeCylinder(inner_diameter / 2, overall_height)
through_hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
body.addObject(through_hole)

# Fuse the features to create the final solid
final_shape = PartDesign.makeFusion([hex_nut, flange, through_hole])

# Add the final shape to the body
body.addObject(final_shape)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument("answer")
