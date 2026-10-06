import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the first section: smooth cylindrical shaft
shaft_diameter = 16
shaft_length = 30
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = shaft_diameter / 2
cylinder.Height = shaft_length
cylinder.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the second section: spur gear
gear_number_tooth = 20
gear_module = 1
gear_height = 20
pressure_angle = 20
gear_pitch_diameter = gear_number_tooth * gear_module

# Create the gear profile
gear_profile = Part.makeCircle(gear_pitch_diameter / 2)
gear_profile = Part.makeHelix(gear_pitch_diameter, gear_height, gear_number_tooth, 0, 360, True)

# Create the gear
gear = body.newObject("PartDesign::Pad", "Gear")
gear.Profile = gear_profile
gear.Length = gear_height
gear.LengthFillet = 0
gear.BaseFeature = cylinder

# Save the document
doc.saveAs("/app/answer.FCStd")
