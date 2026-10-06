import FreeCAD
import Part

# Define the parameters
inner_diameter = 10.0  # mm
overall_height = 15.0  # mm
flange_diameter = 22.0  # mm
flange_thickness = 4.0  # mm
hex_nut_width_across_flats = 16.0  # mm
hex_nut_width_across_corners = hex_nut_width_across_flats / (2 * 3.141592653589793 / 6)  # mm
hex_nut_half_angle = 30.0  # degrees

# Create a new document
doc = FreeCAD.newDocument("HexFlangeNut")

# Create a Part body
body = Part.Body()

# Create a hexagonal nut body
hex_nut_body = Part.makeHexagonalPrism(hex_nut_width_across_flats, hex_nut_half_angle, overall_height)

# Create a circular flange
flange_body = Part.makeCylinder(flange_diameter / 2, overall_height, FreeCAD.Vector(0, 0, overall_height / 2))

# Create a plain through hole
through_hole_body = Part.makeCylinder(inner_diameter / 2, overall_height, FreeCAD.Vector(0, 0, overall_height / 2))

# Create a union of the hex nut body and the flange body
union_body = hex_nut_body.fuse(flange_body)

# Create a difference between the union body and the through hole body
final_body = union_body.cut(through_hole_body)

# Set the final body as the active body
body.addObject(final_body)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
