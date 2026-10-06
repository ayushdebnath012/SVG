import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Profile = doc.addObject("Part::Circle", "GearProfile")
gear_body.Profile.Radius = 25  # Half of the pitch diameter
gear_body.Length = 50  # Pitch diameter

# Create a hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = doc.addObject("Part::Circle", "HubProfile")
hub.Profile.Radius = 20  # Half of the hub diameter
hub.Length = 10  # Hub width

# Create a central bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = doc.addObject("Part::Circle", "BoreProfile")
bore.Profile.Radius = 5  # Half of the shaft diameter
bore.Length = 50  # Pitch diameter

# Set properties
pressure_angle = 20 * math.pi / 180  # Convert to radians
gear_module = 2
number_of_teeth = 25
pitch_diameter = 50
outer_diameter = 54
face_width = 20
hub_diameter = 40
hub_width = 10
shaft_diameter = 10
overall_width = 30
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
root_diameter = pitch_diameter - 2 * dedendum
base_diameter = pitch_diameter * math.cos(pressure_angle)
circular_pitch = math.pi * gear_module
tooth_thickness = circular_pitch / 2

# Set the properties of the objects
gear_body.Profile.Radius = pitch_diameter / 2
gear_body.Length = pitch_diameter
hub.Profile.Radius = hub_diameter / 2
hub.Length = hub_width
bore.Profile.Radius = shaft_diameter / 2
bore.Length = pitch_diameter

# Save the document
doc.saveAs("/app/answer.FCStd")
