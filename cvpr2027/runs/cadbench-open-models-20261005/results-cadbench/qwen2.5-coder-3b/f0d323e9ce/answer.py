import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
diametral_pitch = 12
number_of_teeth = 16
pitch_diameter = 1.333  # in
outer_diameter = 1.5  # in
overall_length = 1  # ft
gear_module = 25.4 / diametral_pitch  # mm
addendum = 1 / diametral_pitch  # mm
dedendum = 1.25 / diametral_pitch  # mm
whole_depth = 2.25 / diametral_pitch  # mm
root_diameter = pitch_diameter - 2 * dedendum  # mm
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # mm

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new cylindrical gear body
cylinder = PartDesign.Cylinder(doc, "Cylinder", pitch_diameter / 2, overall_length, 0, 360)

# Create a new involute-tooth ring
involute_tooth_ring = PartDesign.InvoluteToothRing(doc, "InvoluteToothRing", cylinder, number_of_teeth, gear_module, pressure_angle, addendum, dedendum, whole_depth, root_diameter, base_diameter)

# Add the involute-tooth ring to the body
body.addObject(involute_tooth_ring)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
