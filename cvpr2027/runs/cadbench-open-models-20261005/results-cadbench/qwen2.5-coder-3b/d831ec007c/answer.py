import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 24
pitch_diameter = 24  # mm
outer_diameter = 26  # mm
face_width = 10  # mm
hub_diameter = 20  # mm
hub_width = 10  # mm
shaft_diameter = 8  # mm
overall_width = 20  # mm
addendum = gear_module  # ISO 54 / DIN 867
dedendum = 1.25 * gear_module  # ISO 54 / DIN 867
whole_depth = addendum + dedendum  # ISO 54 / DIN 867
root_diameter = pitch_diameter - 2 * dedendum  # ISO 54 / DIN 867
circular_pitch = math.pi * gear_module  # ISO 54
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 54 / involute gear geometry
bore_diameter = shaft_diameter  # inferred from geometry standard table + given parameters

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
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"
gear_tooth_profile.Shape = Part.makeCylinder(face_width / 2, whole_depth, 0, 360)

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"
gear_tooth.Shape = gear_tooth_profile.Shape

# Create the gear body with teeth
gear_body.addFeature(gear_tooth)

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"
hub.Shape = Part.makeCylinder(hub_diameter / 2, overall_width, 0, 360)

# Create the central bore
bore = PartDesign.Feature(doc)
bore.Label = "Bore"
bore.Shape = Part.makeCylinder(bore_diameter / 2, shaft_diameter, 0, 360)

# Create the gear body with hub and bore
gear_body.addFeature(hub)
gear_body.addFeature(bore)

# Save the document
doc.saveAs(os.path.join(os.path.dirname(__file__), "answer.FCStd"))
