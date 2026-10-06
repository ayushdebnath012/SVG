import FreeCAD
import Part
import PartDesign
import math

# Define the parameters
pressure_angle = 20
gear_module = 1
number_of_teeth = 80
pitch_diameter = 80
outer_diameter = 82
face_width = 6
hub_diameter = 18
hub_width = 8
shaft_diameter = 8
overall_width = 14

# Calculate derived parameters
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
root_diameter = pitch_diameter - 2 * dedendum
circular_pitch = math.pi * gear_module
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
tooth_thickness = circular_pitch / 2

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Profile = Part.makeCircle(pitch_diameter / 2)
gear_body.Length = whole_depth
gear_body.LengthFilletRadius = 0.5

# Create the teeth
teeth = body.newObject("PartDesign::Pocket", "Teeth")
teeth.Profile = Part.makeCircle(root_diameter / 2)
teeth.Length = whole_depth
teeth.LengthFilletRadius = 0.5

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(shaft_diameter / 2)
bore.Length = overall_width
bore.LengthFilletRadius = 0.5

# Create the hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = Part.makeCircle(hub_diameter / 2)
hub.Length = overall_width
hub.LengthFilletRadius = 0.5

# Position the hub
hub.Placement.Base = FreeCAD.Vector(0, 0, whole_depth - overall_width / 2)

# Save the document
doc.saveAs("/app/answer.FCStd")
