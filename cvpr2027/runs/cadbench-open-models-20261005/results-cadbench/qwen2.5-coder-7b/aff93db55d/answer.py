import FreeCAD
import PartDesign
import Part
import math

# Set the document name
doc = FreeCAD.newDocument("answer")

# Define the parameters
pressure_angle = 20  # degrees
diametral_pitch = 20
number_of_teeth = 16
pitch_diameter = 20.32  # mm
outer_diameter = 22.86  # mm
overall_length = 304.8  # mm
gear_module = 1.27  # mm

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical base
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = pitch_diameter / 2
cylinder.Height = overall_length

# Create a PartDesign::Gear feature
gear = body.newObject("PartDesign::Gear", "Gear")
gear.Base = cylinder
gear.NumberOfTeeth = number_of_teeth
gear.Pitch = gear_module
gear.PressureAngle = pressure_angle
gear.DiametralPitch = diametral_pitch
gear.Direction = FreeCAD.Vector(0, 0, 1)

# Create a PartDesign::Pad feature to extrude the gear
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Base = gear
pad.Length = overall_length

# Create a PartDesign::Pocket feature to cut out the teeth
pocket = body.newObject("PartDesign::Pocket", "Pocket")
pocket.Base = pad
pocket.Length = overall_length

# Save the document
doc.saveAs("/app/answer.FCStd")
