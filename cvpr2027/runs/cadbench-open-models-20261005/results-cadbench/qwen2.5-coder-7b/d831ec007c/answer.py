import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Parameters
pressure_angle = 20 * math.pi / 180  # Convert to radians
gear_module = 1
number_of_teeth = 24
pitch_diameter = 24
outer_diameter = 26
face_width = 10
hub_diameter = 20
hub_width = 10
shaft_diameter = 8
overall_width = 20
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
root_diameter = pitch_diameter - 2 * dedendum
circular_pitch = math.pi * gear_module
base_diameter = pitch_diameter * math.cos(pressure_angle)
bore_diameter = shaft_diameter

# Create the gear body
gear_body = body.newObject("PartDesign::Gear", "GearBody")
gear_body.NumberOfTeeth = number_of_teeth
gear_body.Module = gear_module
gear_body.PressureAngle = pressure_angle
gear_body.FaceWidth = face_width
gear_body.PitchDiameter = pitch_diameter
gear_body.OuterDiameter = outer_diameter
gear_body.RootDiameter = root_diameter
gear_body.BaseDiameter = base_diameter
gear_body.CircularPitch = circular_pitch
gear_body.WholeDepth = whole_depth

# Create the hub
hub = body.newObject("PartDesign::Cylinder", "Hub")
hub.Radius = hub_diameter / 2
hub.Height = overall_width
hub.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the central bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = bore_diameter / 2
bore.Height = overall_width
bore.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Position the hub and bore concentrically with the gear body
gear_body.Placement.Base = FreeCAD.Vector(0, 0, 0)
hub.Placement.Base = FreeCAD.Vector(0, 0, 0)
bore.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Save the document
doc.saveAs("/app/answer.FCStd")
