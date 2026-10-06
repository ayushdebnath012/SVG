import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("Ladder")

# Define parameters
ladder_side_rails_length = 2400
ladder_side_rail_width = 40
ladder_side_rail_thickness = 90
ladder_number_of_rungs = 7
ladder_rung_length = 400
ladder_rung_width = 40
ladder_rung_thickness = 40
ladder_rung_spacing = 300

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create side rails
side_rail_length = ladder_side_rails_length
side_rail_width = ladder_side_rail_width
side_rail_thickness = ladder_side_rail_thickness

# Left side rail
left_side_rail = body.newObject("PartDesign::Pad", "LeftSideRail")
left_side_rail.Profile = Part.makeBox(side_rail_length, side_rail_width, side_rail_thickness)
left_side_rail.Length = side_rail_length
left_side_rail.LengthFwd = side_rail_length
left_side_rail.LengthRev = 0

# Right side rail
right_side_rail = body.newObject("PartDesign::Pad", "RightSideRail")
right_side_rail.Profile = Part.makeBox(side_rail_length, side_rail_width, side_rail_thickness)
right_side_rail.Length = side_rail_length
right_side_rail.LengthFwd = side_rail_length
right_side_rail.LengthRev = 0

# Create rungs
rung_length = ladder_rung_length
rung_width = ladder_rung_width
rung_thickness = ladder_rung_thickness
rung_spacing = ladder_rung_spacing

# Create rungs
for i in range(ladder_number_of_rungs):
    rung = body.newObject("PartDesign::Pad", f"Rung{i}")
    rung.Profile = Part.makeBox(rung_length, rung_width, rung_thickness)
    rung.Length = rung_length
    rung.LengthFwd = rung_length
    rung.LengthRev = 0
    rung.Placement.Base = FreeCAD.Vector(0, (i * rung_spacing) + (rung_width / 2), 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
