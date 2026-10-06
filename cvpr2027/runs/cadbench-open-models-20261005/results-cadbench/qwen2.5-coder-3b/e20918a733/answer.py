import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 70
pitch_diameter = 70  # mm
outer_diameter = 72  # mm
face_width = 6  # mm
hub_diameter = 18  # mm
hub_width = 8  # mm
shaft_diameter = 8  # mm
overall_width = 14  # mm
addendum = gear_module  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
whole_depth = addendum + dedendum  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Part(doc)
gear_body.Label = "Gear Body"

# Create the gear profile
gear_profile = PartDesign.Profile(doc)
gear_profile.Label = "Gear Profile"
gear_profile.Shape = Part.makeCircle(base_diameter / 2)

# Create the gear tooth
gear_tooth = PartDesign.Tooth(doc)
gear_tooth.Label = "Gear Tooth"
gear_tooth.Profile = gear_profile
gear_tooth.NumberOfTeeth = number_of_teeth
gear_tooth.PitchDiameter = pitch_diameter
gear_tooth.OuterDiameter = outer_diameter
gear_tooth.FaceWidth = face_width
gear_tooth.Addendum = addendum
gear_tooth.Dedendum = dedendum
gear_tooth.WholeDepth = whole_depth
gear_tooth.RootDiameter = root_diameter
gear_tooth.BaseDiameter = base_diameter
gear_tooth.CircularPitch = circular_pitch

# Create the gear body feature
gear_body_feature = PartDesign.Feature(doc)
gear_body_feature.Label = "Gear Body Feature"
gear_body_feature.Shape = gear_tooth.Shape

# Create the hub
hub = PartDesign.Hub(doc)
hub.Label = "Hub"
hub.Diameter = hub_diameter
hub.Width = hub_width
hub.OverallWidth = overall_width

# Create the hub feature
hub_feature = PartDesign.Feature(doc)
hub_feature.Label = "Hub Feature"
hub_feature.Shape = hub.Shape

# Create the shaft
shaft = PartDesign.Shaft(doc)
shaft.Label = "Shaft"
shaft.Diameter = shaft_diameter

# Create the shaft feature
shaft_feature = PartDesign.Feature(doc)
shaft_feature.Label = "Shaft Feature"
shaft_feature.Shape = shaft.Shape

# Create the round bore
round_bore = PartDesign.Bore(doc)
round_bore.Label = "Round Bore"
round_bore.Diameter = shaft_diameter
round_bore.Position = (0, 0, 0)
round_bore.Radius = shaft_diameter / 2

# Create the round bore feature
round_bore_feature = PartDesign.Feature(doc)
round_bore_feature.Label = "Round Bore Feature"
round_bore_feature.Shape = round_bore.Shape

# Create the gear body feature in the hub
gear_body_in_hub = PartDesign.Feature(doc)
gear_body_in_hub.Label = "Gear Body in Hub"
gear_body_in_hub.Shape = gear_body_feature.Shape
gear_body_in_hub.Parent = hub_feature

# Create the hub feature in the shaft
hub_in_shaft = PartDesign.Feature(doc)
hub_in_shaft.Label = "Hub in Shaft"
hub_in_shaft.Shape = hub_feature.Shape
hub_in_shaft.Parent = shaft_feature

# Create the round bore feature in the shaft
round_bore_in_shaft = PartDesign.Feature(doc)
round_bore_in_shaft.Label = "Round Bore in Shaft"
round_bore_in_shaft.Shape = round_bore_feature.Shape
round_bore_in_shaft.Parent = shaft_feature

# Create the final solid body
final_solid = PartDesign.Solid(doc)
final_solid.Label = "Final Solid"
final_solid.Shape = gear_body_in_hub.Shape

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
