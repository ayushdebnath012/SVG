import FreeCAD
import Part
import PartDesign
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 32
pitch_diameter = 32  # mm
outer_diameter = 34  # mm
face_width = 10  # mm
hub_diameter = 26  # mm
hub_width = 10  # mm
shaft_diameter = 8  # mm
overall_width = 20  # mm

# Calculate derived parameters
addendum = pitch_diameter / number_of_teeth  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
whole_depth = addendum + dedendum  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the toothed gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Profile = Part.makeCircle(outer_diameter / 2)
gear_body.Length = face_width
gear_body.LengthFilletRadius = 0

# Create the central hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = Part.makeCircle(hub_diameter / 2)
hub.Length = hub_width
hub.LengthFilletRadius = 0

# Create the round through bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = Part.makeCircle(shaft_diameter / 2)
bore.Length = overall_width
bore.LengthFilletRadius = 0

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
FreeCAD.closeDocument(doc.Name)
