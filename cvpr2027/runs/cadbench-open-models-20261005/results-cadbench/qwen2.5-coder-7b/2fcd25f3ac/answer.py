import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Define parameters
pressure_angle = 20 * math.pi / 180  # Convert to radians
gear_module = 1
number_of_teeth = 18
pitch_diameter = 18
outer_diameter = 20
face_width = 10
hub_diameter = 14
hub_width = 10
shaft_diameter = 6
overall_width = 20

# Calculate derived parameters
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
root_diameter = pitch_diameter - 2 * dedendum
circular_pitch = math.pi * gear_module
base_diameter = pitch_diameter * math.cos(pressure_angle)

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Profile = Part.makeCircle(pitch_diameter / 2)
gear_body.Length = whole_depth
gear_body.LengthFilletRadius = 0.5

# Create the hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = Part.makeCircle(hub_diameter / 2)
hub.Length = whole_depth
hub.LengthFilletRadius = 0.5

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(shaft_diameter / 2)
bore.Length = overall_width
bore.LengthFilletRadius = 0.5

# Position the hub and bore
hub.Placement.Base = FreeCAD.Vector(-hub_width / 2, 0, 0)
bore.Placement.Base = FreeCAD.Vector(-overall_width / 2, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
