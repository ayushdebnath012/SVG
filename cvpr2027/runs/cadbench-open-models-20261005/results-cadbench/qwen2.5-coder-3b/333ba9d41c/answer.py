import FreeCAD
import PartDesign

# Define the parameters
pressure_angle = 20
gear_module = 1
number_of_teeth = 48
pitch_diameter = 48
outer_diameter = 50
face_width = 6
hub_diameter = 16
hub_width = 8
shaft_diameter = 8
overall_width = 14
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module
root_diameter = pitch_diameter - 2 * dedendum

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"
gear_tooth_profile.Shape = Part.makeCircle(face_width / 2)

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"
gear_tooth.Shape = gear_tooth_profile.Shape
gear_tooth.Shape = gear_tooth.Shape.extrude(Part.makeVector(0, 0, pitch_diameter))

# Create the gear body with teeth
gear_body.addFeature(gear_tooth)

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"
hub.Shape = Part.makeCylinder(hub_diameter / 2, overall_width)

# Create the round bore
round_bore = PartDesign.Feature(doc)
round_bore.Label = "Round Bore"
round_bore.Shape = Part.makeCylinder(shaft_diameter / 2, overall_width)

# Create the gear body with hub and round bore
gear_body.addFeature(hub)
gear_body.addFeature(round_bore)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
