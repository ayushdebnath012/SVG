import FreeCAD
import PartDesign
import Part

# Define the parameters
pressure_angle = 20  # degrees
diametral_pitch = 16
number_of_teeth = 12
pitch_diameter = 19.05  # mm
outer_diameter = 22.352  # mm
overall_length = 304.8  # mm
gear_module = 25.4 / diametral_pitch  # AGMA (inch DP to metric module conversion)

# Create a new document
doc = FreeCAD.newDocument("SpurGearStock")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new cylindrical gear body
cylinder = PartDesign.Cylinder(doc, "Cylinder")
cylinder.Radius = outer_diameter / 2
cylinder.Height = overall_length

# Create a new involute tooth profile
tooth_profile = PartDesign.InvoluteToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module

# Create a new gear feature
gear = PartDesign.Gear(doc, "Gear")
gear.Base = cylinder
gear.Profile = tooth_profile

# Add the gear feature to the body
body.addObject(gear)

# Save the document
doc.saveAs("/app/answer.FCStd")
