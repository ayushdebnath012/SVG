import FreeCAD
import PartDesign

# Define the parameters
pressure_angle = 20
gear_module = 1
number_of_teeth = 50
pitch_diameter = 50
outer_diameter = 52
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
gear_tooth_profile.Shape = Part.makeCircle(pitch_diameter / 2)

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"
gear_tooth.Shape = gear_tooth_profile.Shape
gear_tooth.Shape = gear_tooth.Shape.extrude(FreeCAD.Vector(0, 0, outer_diameter / 2))

# Create the gear body
gear_body.Shape = gear_tooth.Shape

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"
hub.Shape = Part.makeCylinder(hub_diameter / 2, overall_width)
hub.Shape = hub.Shape.translate(FreeCAD.Vector(0, 0, outer_diameter / 2))

# Create the shaft
shaft = PartDesign.Feature(doc)
shaft.Label = "Shaft"
shaft.Shape = Part.makeCylinder(shaft_diameter / 2, overall_width)
shaft.Shape = shaft.Shape.translate(FreeCAD.Vector(0, 0, outer_diameter / 2))

# Create the round bore
bore = PartDesign.Feature(doc)
bore.Label = "Bore"
bore.Shape = Part.makeCylinder(shaft_diameter / 2, overall_width)
bore.Shape = bore.Shape.translate(FreeCAD.Vector(0, 0, outer_diameter / 2))

# Create the gear body with hub and bore
gear_body.Shape = gear_body.Shape.fuse(hub.Shape)
gear_body.Shape = gear_body.Shape.fuse(bore.Shape)

# Create the gear body with addendum and dedendum
gear_body.Shape = gear_body.Shape.extrude(FreeCAD.Vector(0, 0, addendum))

# Create the gear body with root diameter
gear_body.Shape = gear_body.Shape.extrude(FreeCAD.Vector(0, 0, root_diameter))

# Create the gear body with face width
gear_body.Shape = gear_body.Shape.extrude(FreeCAD.Vector(0, face_width, 0))

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
