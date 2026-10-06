import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Parameters
pressure_angle = 20 * math.pi / 180  # Convert to radians
gear_module = 1
number_of_teeth = 60
pitch_diameter = 60
outer_diameter = 62
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
base_diameter = pitch_diameter * math.cos(pressure_angle)

# Create the gear body
gear_body = body.newObject("PartDesign::Gear", "GearBody")
gear_body.NumberOfTeeth = number_of_teeth
gear_body.Module = gear_module
gear_body.PressureAngle = pressure_angle
gear_body.PitchDiameter = pitch_diameter
gear_body.OuterDiameter = outer_diameter
gear_body.FaceWidth = face_width

# Create the central hub
hub = body.newObject("PartDesign::Cylinder", "Hub")
hub.Radius = hub_diameter / 2
hub.Height = overall_width
hub.Placement.Base = FreeCAD.Vector(-hub_diameter / 2, 0, 0)

# Create the round through bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = shaft_diameter / 2
bore.Height = overall_width
bore.Placement.Base = FreeCAD.Vector(-outer_diameter / 2, 0, 0)

# Finalize the body
body.finish()

# Save the document
doc.saveAs("/app/answer.FCStd")
