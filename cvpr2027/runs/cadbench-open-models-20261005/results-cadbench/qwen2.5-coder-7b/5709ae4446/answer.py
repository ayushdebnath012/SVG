import FreeCAD
import Part
import PartDesign
import math

# Define the parameters
pressure_angle = 20 * math.pi / 180  # Convert to radians
gear_module = 2  # mm
number_of_teeth = 30
pitch_diameter = 60  # mm
outer_diameter = 64  # mm
face_width = 20  # mm
hub_diameter = 50  # mm
hub_width = 10  # mm
shaft_diameter = 10  # mm
overall_width = 30  # mm

# Calculate derived parameters
addendum = pitch_diameter / number_of_teeth  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
whole_depth = addendum + dedendum  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
base_diameter = pitch_diameter * math.cos(pressure_angle)  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771
tooth_thickness = circular_pitch / 2  # ISO 21771

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Length = pitch_diameter + 2 * whole_depth
gear_body.Profile = Part.makeCylinder(root_diameter / 2, gear_body.Length)

# Create the teeth
tooth_profile = Part.makeCircle(root_diameter / 2)
tooth_profile.translate((0, 0, whole_depth))
tooth_profile.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), tooth_thickness)
gear_body.Profile = Part.makeHelix(tooth_thickness, pitch_diameter, number_of_teeth, 0, 360, 0)
gear_body.Profile = gear_body.Profile.fuse(tooth_profile)

# Create the hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Base = Part.makeCylinder(hub_diameter / 2, gear_body.Length)
hub.Length = hub_diameter / 2

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Base = Part.makeCylinder(shaft_diameter / 2, gear_body.Length)
bore.Length = shaft_diameter / 2

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
