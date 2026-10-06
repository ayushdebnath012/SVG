import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
diametral_pitch = 20
number_of_teeth = 16
pitch_diameter = 0.8  # in = 20.32 mm
outer_diameter = 0.9  # in = 22.86 mm
overall_length = 1  # ft = 304.8 mm
gear_module = 25.4 / diametral_pitch  # AGMA / ISO gear geometry

# Convert inches to millimeters
pressure_angle_rad = math.radians(pressure_angle)
pitch_diameter_mm = pitch_diameter * 25.4
outer_diameter_mm = outer_diameter * 25.4
overall_length_mm = overall_length * 304.8

# Create a new document
doc = FreeCAD.newDocument("SpurGearStock")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new cylindrical gear body
cylinder = PartDesign.Cylinder(doc, "Cylinder", outer_diameter_mm / 2, overall_length_mm, pitch_diameter_mm / 2)

# Create a new gear profile
gear_profile = PartDesign.GearProfile(doc, "GearProfile", pitch_diameter_mm, number_of_teeth, gear_module, pressure_angle_rad)

# Create a new gear extrusion
gear_extrusion = PartDesign.Extrude(doc, "GearExtrusion", cylinder, gear_profile, overall_length_mm)

# Add the gear extrusion to the body
body.addObject(gear_extrusion)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
