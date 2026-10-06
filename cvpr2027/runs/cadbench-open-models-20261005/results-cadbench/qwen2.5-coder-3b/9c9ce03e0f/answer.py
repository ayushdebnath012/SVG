import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 80
pitch_diameter = 80  # mm
outer_diameter = 82  # mm
face_width = 6  # mm
hub_diameter = 18  # mm
hub_width = 8  # mm
shaft_diameter = 8  # mm
overall_width = 14  # mm
addendum = pitch_diameter / number_of_teeth  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
whole_depth = addendum + dedendum  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771
tooth_thickness = circular_pitch / 2  # ISO 21771

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear profile
gear_profile = PartDesign.Profile(doc)
gear_profile.Label = "Gear Profile"
gear_profile.Shape = Part.makeCylinder(outer_diameter / 2, whole_depth, 0, 360)

# Create the gear tooth profile
tooth_profile = PartDesign.Profile(doc)
tooth_profile.Label = "Tooth Profile"
tooth_profile.Shape = Part.makeCylinder((outer_diameter - face_width) / 2, tooth_thickness, 0, 360)

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"
gear_tooth.Shape = Part.makeCylinder((outer_diameter - face_width) / 2, tooth_thickness, 0, 360)
gear_tooth.Profile = tooth_profile

# Create the gear body with teeth
gear_body_with_teeth = PartDesign.Feature(doc)
gear_body_with_teeth.Label = "Gear Body with Teeth"
gear_body_with_teeth.Shape = gear_body.Shape
gear_body_with_teeth.Profile = gear_profile
gear_body_with_teeth.addFeature(gear_tooth)

# Create the central bore
central_bore = PartDesign.Feature(doc)
central_bore.Label = "Central Bore"
central_bore.Shape = Part.makeCylinder(shaft_diameter / 2, whole_depth, 0, 360)

# Create the rear hub
rear_hub = PartDesign.Feature(doc)
rear_hub.Label = "Rear Hub"
rear_hub.Shape = Part.makeCylinder(hub_diameter / 2, whole_depth, 0, 360)
rear_hub.Profile = Part.makeCylinder(hub_diameter / 2, hub_width, 0, 360)

# Create the gear body with central bore and rear hub
gear_body_with_central_bore_and_rear_hub = PartDesign.Feature(doc)
gear_body_with_central_bore_and_rear_hub.Label = "Gear Body with Central Bore and Rear Hub"
gear_body_with_central_bore_and_rear_hub.Shape = gear_body_with_teeth.Shape
gear_body_with_central_bore_and_rear_hub.Profile = gear_profile
gear_body_with_central_bore_and_rear_hub.addFeature(central_bore)
gear_body_with_central_bore_and_rear_hub.addFeature(rear_hub)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
