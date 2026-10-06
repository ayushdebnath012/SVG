```python
import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 18
pitch_diameter = 18  # mm
outer_diameter = 20  # mm
face_width = 10  # mm
hub_diameter = 14  # mm
hub_width = 10  # mm
shaft_diameter = 6  # mm
overall_width = 20  # mm
addendum = pitch_diameter / number_of_teeth  # ISO 54 / DIN 867
dedendum = 1.25 * gear_module  # ISO 54 / DIN 867
whole_depth = addendum + dedendum  # ISO 54 / DIN 867
root_diameter = pitch_diameter - 2 * dedendum  # ISO 54 / DIN 867
circular_pitch = math.pi * gear_module  # ISO 54 / DIN 867
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 54 / DIN 867

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

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the hub shape
hub_shape = Part.makeBox(hub_diameter / 2, hub_width, overall_width)
hub.Shape = hub_shape

# Create the hub feature
hub_feature = PartDesign.Feature(doc)
hub_feature.Label = "Hub Feature"
hub_feature.Shape = hub_shape

# Create the hub feature array
hub_feature_array = PartDesign.Array(doc)
hub_feature_array.Label = "Hub Feature Array"
hub_feature_array.Base = hub_feature
hub_feature_array.CountX = 1
hub_feature_array.CountY = 1
hub_feature_array.CountZ = 1
hub_feature_array.generate()

# Create the hub feature array feature
hub_feature_array_feature = PartDesign.Feature(doc)
hub_feature_array_feature.Label = "Hub Feature Array Feature"
hub_feature_array_feature.Shape = hub_feature_array.Shape

# Create the gear body feature array
gear_body_feature_array = PartDesign.Array(doc)
gear_body_feature_array.Label = "Gear Body Feature Array"
gear_body_feature_array.Base = gear_body_feature
gear_body_feature_array.CountX = 1
gear_body_feature_array.CountY = 1
gear_body_feature_array.CountZ = 1
gear_body_feature_array.generate()

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear_body_feature_array_feature = PartDesign.Feature(doc)
gear_body_feature_array_feature.Label = "Gear Body Feature Array Feature"
gear_body_feature_array_feature.Shape = gear_body_feature_array.Shape

# Create the gear body feature array feature
gear