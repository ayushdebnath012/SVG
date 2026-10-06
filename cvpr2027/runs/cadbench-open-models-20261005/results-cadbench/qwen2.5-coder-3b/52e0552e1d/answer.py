import FreeCAD
import PartDesign

# Define the parameters
pressure_angle = 20
gear_module = 1
number_of_teeth = 40
pitch_diameter = 40
outer_diameter = 42
face_width = 10
hub_diameter = 35
hub_width = 10
shaft_diameter = 10
overall_width = 20
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
gear_tooth_profile.Shape = Part.makeCircle(pitch_diameter / 2)

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"
gear_tooth.Shape = gear_tooth_profile.Shape
gear_tooth.Shape = gear_tooth.Shape.extrude(FreeCAD.Vector(0, 0, outer_diameter / 2))

# Create the gear body
gear_body.Shape = gear_tooth.Shape

# Create the hub section
hub_section = PartDesign.Feature(doc)
hub_section.Label = "Hub Section"
hub_section.Shape = Part.makeBox(hub_diameter, hub_width, overall_width)
hub_section.Shape = hub_section.Shape.translate(FreeCAD.Vector(0, 0, outer_diameter / 2))

# Create the round bore
round_bore = PartDesign.Feature(doc)
round_bore.Label = "Round Bore"
round_bore.Shape = Part.makeCylinder(shaft_diameter / 2, overall_width)
round_bore.Shape = round_bore.Shape.translate(FreeCAD.Vector(0, 0, outer_diameter / 2))

# Create the gear body with hub and bore
gear_body.Shape = gear_body.Shape.fuse(hub_section.Shape)
gear_body.Shape = gear_body.Shape.fuse(round_bore.Shape)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
