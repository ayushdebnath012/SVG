import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
overall_height = 14.0
flange_diameter = 29.9
flange_thickness = 6.2
hub_width = 21.0
through_hole_diameter = 14.0
hex_head_width_across_flats = hub_width
hex_head_width_across_corners = hex_head_width_across_flats / math.cos(math.radians(30))
hex_head_angle = 30
hex_height_above_flange = overall_height - flange_thickness

# Create the flange
flange = body.newObject("PartDesign::Pad", "Flange")
flange.Profile = Part.makeCircle(flange_diameter / 2)
flange.Length = flange_thickness
flange.LengthFilletRadius = 0

# Create the hex hub
hex_hub = body.newObject("PartDesign::Pocket", "HexHub")
hex_hub.Profile = Part.makePolygon([
    FreeCAD.Vector(-hub_width / 2, 0, 0),
    FreeCAD.Vector(-hub_width / 4, hex_head_width_across_flats / 2, 0),
    FreeCAD.Vector(hub_width / 4, hex_head_width_across_flats / 2, 0),
    FreeCAD.Vector(hub_width / 2, 0, 0),
    FreeCAD.Vector(hub_width / 4, -hex_head_width_across_flats / 2, 0),
    FreeCAD.Vector(-hub_width / 4, -hex_head_width_across_flats / 2, 0)
])
hex_hub.Length = hex_height_above_flange
hex_hub.LengthFilletRadius = 0

# Create the through hole
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Profile = Part.makeCircle(through_hole_diameter / 2)
through_hole.Length = overall_height
through_hole.LengthFilletRadius = 0

# Position the features
hex_hub.Placement.Base = FreeCAD.Vector(0, 0, flange_thickness)
through_hole.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
