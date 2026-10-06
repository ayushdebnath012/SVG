import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a through-hole
through_hole_diameter = 18.0
through_hole = body.newObject("PartDesign::Cylinder", "ThroughHole")
through_hole.Radius = through_hole_diameter / 2
through_hole.Height = 27.0
through_hole.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the external hex drive
drive_style = "external_hex"
hub_width = 27.0
hex_head_height = 22.0
hex_head = body.newObject("PartDesign::Cylinder", "HexHead")
hex_head.Radius = hub_width / 2
hex_head.Height = hex_head_height
hex_head.Placement.Base = FreeCAD.Vector(0, 0, through_hole_diameter / 2)

# Create the flange
flange_diameter = 34.0
flange_thickness = 5.0
flange = body.newObject("PartDesign::Cylinder", "Flange")
flange.Radius = flange_diameter / 2
flange.Height = flange_thickness
flange.Placement.Base = FreeCAD.Vector(0, 0, through_hole_diameter / 2 + hex_head_height)

# Merge the features to create the final shape
body.addFeature(through_hole.BaseFeature)
body.addFeature(hex_head.BaseFeature)
body.addFeature(flange.BaseFeature)

# Save the document
doc.saveAs("/app/answer.FCStd")
