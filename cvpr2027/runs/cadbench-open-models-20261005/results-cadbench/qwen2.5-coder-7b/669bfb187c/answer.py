import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define key parameters
overall_height = 16
flange_diameter = 34.5
flange_thickness = 7
hub_width = 24
inner_diameter = 16

# Create a hexagonal nut body
hex_nut = body.newObject("PartDesign::Pad", "HexNut")
hex_nut.Profile = doc.addObject("Part::Circle", "HexNutProfile")
hex_nut.Profile.Radius = hub_width / 2
hex_nut.Length = overall_height
hex_nut.BaseOffset = 0

# Create a circular flange
flange = body.newObject("PartDesign::Pocket", "Flange")
flange.Profile = doc.addObject("Part::Circle", "FlangeProfile")
flange.Profile.Radius = flange_diameter / 2
flange.Length = flange_thickness
flange.BaseOffset = overall_height - flange_thickness

# Create a central through-hole
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Profile = doc.addObject("Part::Circle", "ThroughHoleProfile")
through_hole.Profile.Radius = inner_diameter / 2
through_hole.Length = overall_height
through_hole.BaseOffset = 0

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
