import FreeCAD
import Part
import math
import os

# Define the parameters
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

# Create a new document
doc = FreeCAD.newDocument("SpurGearModel")

# Create the spur gear body
spur_gear_body = Part.Body(doc)
spur_gear_body.Label = "Spur Gear Body"

# Create the spur gear profile
spur_gear_profile = Part.makeTorus(gear_pitch_diameter / 2, gear_height / 2, gear_module, gear_height / 2)
spur_gear_body.addObject(spur_gear_profile)

# Create the recessed hub/web profile
recessed_hub_web_profile = Part.makeTorus(gear_recessed_hub_diameter / 2, gear_recessed_hub_depth / 2, gear_web_thickness, gear_recessed_hub_depth / 2)
recessed_hub_web_profile.translate((0, 0, gear_height / 2))
spur_gear_body.addObject(recessed_hub_web_profile)

# Create the web lightening holes
web_lightening_holes = []
for i in range(number_of_web_lightening_holes):
    angle = 360 / number_of_web_lightening_holes * i
    x = gear_web_thickness / 2 * math.cos(math.radians(angle))
    y = gear_web_thickness / 2 * math.sin(math.radians(angle))
    hole = Part.makeCylinder(web_lightening_hole_diameter / 2, web_lightening_hole_circle_diameter / 2)
    hole.translate((x, y, gear_height / 2))
    web_lightening_holes.append(hole)
    spur_gear_body.addObject(hole)

# Create the protruding hub profile
protruding_hub_profile = Part.makeTorus(protruding_hub_diameter / 2, protruding_hub_height / 2, gear_web_thickness, gear_web_thickness)
protruding_hub_profile.translate((0, 0, gear_height / 2))
spur_gear_body.addObject(protruding_hub_profile)

# Create the inner hole for coupling
inner_hole = Part.makeCylinder(inner_hole_diameter / 2, gear_web_thickness / 2)
inner_hole.translate((0, 0, gear_height / 2))
spur_gear_body.addObject(inner_hole)

# Create the final solid body
spur_gear_body.makeSolid()

# Save the document
output_path = os.path.join(os.path.dirname(__file__), "answer.FCStd")
doc.saveAs(output_path)

# Close the document
FreeCAD.closeDocument(doc.Name)
