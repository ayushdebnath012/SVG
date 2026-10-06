import FreeCAD
import Part
import PartDesign
import math

# Define parameters
pressure_angle = 20
gear_module = 1
number_of_teeth = 45
pitch_diameter = 45
outer_diameter = 47
face_width = 6
hub_diameter = 16
hub_width = 6
shaft_diameter = 8
overall_width = 12

# Calculate derived parameters
addendum = gear_module
dedendum = 1.25 * gear_module
root_diameter = pitch_diameter - 2 * dedendum
circular_pitch = math.pi * gear_module
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
whole_depth = addendum + dedendum
tooth_thickness = circular_pitch / 2

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Profile = Part.makeCircle(pitch_diameter / 2)
gear_body.Length = outer_diameter / 2
gear_body.LengthFilletRadius = 0

# Create the hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = Part.makeCircle(hub_diameter / 2)
hub.Length = overall_width / 2
hub.LengthFilletRadius = 0

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(shaft_diameter / 2)
bore.Length = overall_width / 2
bore.LengthFilletRadius = 0

# Position the hub and bore
hub.Placement.Base = FreeCAD.Vector(-hub_diameter / 2, 0, 0)
bore.Placement.Base = FreeCAD.Vector(-shaft_diameter / 2, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
FreeCAD.closeDocument(doc.Name)
