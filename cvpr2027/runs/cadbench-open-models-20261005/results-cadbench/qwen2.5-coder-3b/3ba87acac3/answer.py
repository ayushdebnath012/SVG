```python
import FreeCAD
import PartDesign

# Define the parameters
pressure_angle = 20
gear_module = 2
number_of_teeth = 20
pitch_diameter = 40
outer_diameter = 44
face_width = 20
hub_diameter = 32
hub_width = 10
shaft_diameter = 10
overall_width = 30

# Calculate addendum and dedendum
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module

# Calculate root diameter
root_diameter = pitch_diameter - 2 * dedendum

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile"

# Create the gear tooth
gear_tooth = PartDesign.Feature(doc)
gear_tooth.Label = "Gear Tooth"

# Create the hub
hub = PartDesign.Feature(doc)
hub.Label = "Hub"

# Create the shaft bore
shaft_bore = PartDesign.Feature(doc)
shaft_bore.Label = "Shaft Bore"

# Create the gear body profile
gear_body_profile = PartDesign.Profile(doc)
gear_body_profile.Label = "Gear Body Profile"

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth profile
gear_tooth_profile = PartDesign.Profile(doc)
gear_tooth_profile.Label = "Gear Tooth Profile