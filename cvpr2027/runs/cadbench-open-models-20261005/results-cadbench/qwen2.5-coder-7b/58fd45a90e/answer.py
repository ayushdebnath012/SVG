import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the key parameters
inner_diameter = 8.0
overall_height = 8.0
flange_diameter = 17.9
flange_thickness = 3.5
hex_head_width_across_flats = 13.0
hex_head_width_across_corners = hex_head_width_across_flats / (2 * 0.8660254037844386)  # cos(30 degrees) = 0.8660254037844386
hex_head_angle = 30.0

# Create a PartDesign Feature for the hexagonal nut body
hex_nut = body.newObject("PartDesign::Pad", "HexNut")
hex_nut.Profile = doc.addObject("Part::Circle", "HexNutProfile")
hex_nut.Profile.Radius = hex_head_width_across_flats / 2
hex_nut.Length = overall_height
hex_nut.BaseOffset = 0

# Create a PartDesign Feature for the through-hole
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Profile = doc.addObject("Part::Circle", "ThroughHoleProfile")
through_hole.Profile.Radius = inner_diameter / 2
through_hole.Length = overall_height
through_hole.BaseOffset = 0

# Create a PartDesign Feature for the flange
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = doc.addObject("Part::Circle", "FlangeProfile")
flange.Profile.Radius = flange_diameter / 2
flange.Length = flange_thickness
flange.BaseOffset = overall_height

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
