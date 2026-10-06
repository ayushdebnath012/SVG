import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 22
pitch_diameter = 22  # mm
outer_diameter = 24  # mm
face_width = 10  # mm
hub_diameter = 18  # mm
hub_width = 10  # mm
shaft_diameter = 8  # mm
overall_width = 20  # mm
addendum = pitch_diameter / number_of_teeth  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771
bore_diameter = shaft_diameter  # inferred from round bore geometry + given shaft_diameter

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth profile shape
gear_tooth_shape = Part.makeCircle(base_diameter / 2)
gear_tooth_profile.Shape = gear_tooth_shape

# Create the gear tooth feature
gear_tooth_feature = PartDesign.Feature(doc)
gear_tooth_feature.Label = "Gear Tooth Feature"
gear_tooth_feature.Profile = gear_tooth_profile

# Create the gear tooth feature array
gear_tooth_feature_array = PartDesign.Array(doc)
gear_tooth_feature_array.Label = "Gear Tooth Feature Array"
gear_tooth_feature_array.Base = gear_tooth_feature
gear_tooth_feature_array.CountX = number_of_teeth
gear_tooth_feature_array.CountY = 1
gear_tooth_feature_array.CountZ = 1
gear_tooth_feature_array.generate()

# Create the gear body feature
gear_body_feature = PartDesign.Feature(doc)
gear_body_feature.Label = "Gear Body Feature"
gear_body_feature.Shape = gear_tooth_feature_array.Shape

# Create the hub section
hub_section = PartDesign.Feature(doc)
hub_section.Label = "Hub Section"
hub_section.Shape = Part.makeBox(hub_diameter, hub_width, overall_width)

# Create the round bore
round_bore = PartDesign.Feature(doc)
round_bore.Label = "Round Bore"
round_bore.Shape = Part.makeCylinder(bore_diameter / 2, overall_width)

# Create the gear body feature array
gear_body_feature_array = PartDesign.Array(doc)
gear_body_feature_array.Label = "Gear Body Feature Array"
gear_body_feature_array.Base = gear_body_feature
gear_body_feature_array.CountX = 1
gear_body_feature_array.CountY = 1
gear_body_feature_array.CountZ = 1
gear_body_feature_array.generate()

# Create the hub section feature array
hub_section_feature_array = PartDesign.Array(doc)
hub_section_feature_array.Label = "Hub Section Feature Array"
hub_section_feature_array.Base = hub_section
hub_section_feature_array.CountX = 1
hub_section_feature_array.CountY = 1
hub_section_feature_array.CountZ = 1
hub_section_feature_array.generate()

# Create the round bore feature array
round_bore_feature_array = PartDesign.Array(doc)
round_bore_feature_array.Label = "Round Bore Feature Array"
round_bore_feature_array.Base = round_bore
round_bore_feature_array.CountX = 1
hub_section_feature_array.CountY = 1
round_bore_feature_array.CountZ = 1
round_bore_feature_array.generate()

# Create the final solid body
final_solid_body = PartDesign.Feature(doc)
final_solid_body.Label = "Final Solid Body"
final_solid_body.Shape = gear_body_feature_array.Shape

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
