import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Define parameters
number_gear_tooth = 30
gear_module = 2
gear_height = 30
pressure_angle = 20
gear_pitch_diameter = number_gear_tooth * gear_module

gear_recessed_hub_diameter = 50
gear_recessed_hub_depth = 5
gear_web_thickness = 20
number_of_web_lightening_holes = 4
web_lightening_hole_diameter = 10
web_lightening_hole_circle_diameter = 34

protruding_hub_diameter = 22
protruding_hub_height = 30
inner_hole_diameter = 12

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the spur gear
spur_gear = body.newObject("PartDesign::Pad", "SpurGear")
spur_gear.Profile = Part.makeCircle(gear_pitch_diameter / 2)
spur_gear.Length = gear_height
spur_gear.LengthFilletRadius = 0

# Create the recessed hub
recessed_hub = body.newObject("PartDesign::Pocket", "RecessedHub")
recessed_hub.Profile = Part.makeCircle(gear_recessed_hub_diameter / 2)
recessed_hub.Length = gear_recessed_hub_depth
recessed_hub.LengthFilletRadius = 0

# Create the web
web = body.newObject("PartDesign::Pocket", "Web")
web.Profile = Part.makeBox(gear_recessed_hub_diameter, gear_web_thickness, gear_height)
web.Length = gear_recessed_hub_depth
web.LengthFilletRadius = 0

# Create the web lightening holes
for i in range(number_of_web_lightening_holes):
    angle = 2 * i * 3.14159 / number_of_web_lightening_holes
    x = web_lightening_hole_circle_diameter / 2 * FreeCAD.sin(angle)
    y = web_lightening_hole_circle_diameter / 2 * FreeCAD.cos(angle)
    hole = body.newObject("PartDesign::Pocket", f"WebLighteningHole{i}")
    hole.Profile = Part.makeCircle(web_lightening_hole_diameter / 2)
    hole.Length = gear_recessed_hub_depth
    hole.LengthFilletRadius = 0
    hole.Placement.Base = FreeCAD.Vector(x, y, 0)

# Create the protruding hub
protruding_hub = body.newObject("PartDesign::Pad", "ProtrudingHub")
protruding_hub.Profile = Part.makeCircle(protruding_hub_diameter / 2)
protruding_hub.Length = protruding_hub_height
protruding_hub.LengthFilletRadius = 0

# Create the inner hole
inner_hole = body.newObject("PartDesign::Pocket", "InnerHole")
inner_hole.Profile = Part.makeCircle(inner_hole_diameter / 2)
inner_hole.Length = protruding_hub_height
inner_hole.LengthFilletRadius = 0

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
