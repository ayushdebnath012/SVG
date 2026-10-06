import FreeCAD
import PartDesign
import Part

# Define the parameters
inner_diameter = 8.0  # mm
overall_height = 8.0  # mm
flange_diameter = 17.9  # mm
flange_thickness = 3.5  # mm
hex_head_width_across_flats = 13.0  # mm
hex_head_width_across_corners = hex_head_width_across_flats / (3 ** 0.5)  # mm
hex_head_angle = 30.0  # degrees

# Create a new document
doc = FreeCAD.newDocument("HexFlangeNut")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create a hexagonal nut body
hex_nut_body = PartDesign.Part(doc, "HexNutBody")
hex_nut_body.Shape = Part.makeHexagonalPrism(
    hex_head_width_across_flats,
    hex_head_width_across_corners,
    hex_head_angle,
    overall_height
)

# Create a circular flange
flange = PartDesign.Part(doc, "Flange")
flange.Shape = Part.makeCylinder(
    flange_diameter / 2,
    flange_thickness,
    0,
    0,
    0
)

# Position the flange on top of the hex nut body
flange.Placement.Base = hex_nut_body.Shape.BoundBox.Center
flange.Placement.Rotation = FreeCAD.Placement(
    FreeCAD.Vector(0, 0, 1),
    FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), hex_head_angle)
)

# Create a through-hole
through_hole = PartDesign.Part(doc, "ThroughHole")
through_hole.Shape = Part.makeCylinder(
    inner_diameter / 2,
    overall_height,
    0,
    0,
    0
)

# Position the through-hole in the center of the hex nut body
through_hole.Placement.Base = hex_nut_body.Shape.BoundBox.Center

# Add the hex nut body, flange, and through-hole to the body
body.addObject(hex_nut_body)
body.addObject(flange)
body.addObject(through_hole)

# Save the document
doc.saveAs("/app/answer.FCStd")
