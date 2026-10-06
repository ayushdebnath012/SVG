import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 60
pitch_diameter = 60  # mm
outer_diameter = 62  # mm
face_width = 6  # mm
hub_diameter = 18  # mm
hub_width = 8  # mm
shaft_diameter = 8  # mm
overall_width = 14  # mm
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
root_diameter = pitch_diameter - 2 * dedendum
circular_pitch = math.pi * gear_module
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear teeth
gear_teeth = PartDesign.Tooth(doc, gear_body, number_of_teeth, gear_module, pressure_angle, pitch_diameter, outer_diameter, face_width, whole_depth, root_diameter, base_diameter, circular_pitch)
gear_teeth.Label = "Gear Teeth"

# Create the hub
hub = PartDesign.Hub(doc, gear_body, hub_diameter, hub_width, overall_width)
hub.Label = "Hub"

# Create the shaft
shaft = PartDesign.Shaft(doc, gear_body, shaft_diameter)
shaft.Label = "Shaft"

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
