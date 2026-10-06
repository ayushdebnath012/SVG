import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Define parameters
pressure_angle = 20
gear_module = 1
number_of_teeth = 50
pitch_diameter = 50
outer_diameter = 52
face_width = 6
hub_diameter = 16
hub_width = 8
shaft_diameter = 8
overall_width = 14
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module
root_diameter = pitch_diameter - 2 * dedendum

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the gear body
gear_body = body.newObject("PartDesign::Gear", "GearBody")
gear_body.NumberOfTeeth = number_of_teeth
gear_body.Module = gear_module
gear_body.PressureAngle = pressure_angle
gear_body.PitchDiameter = pitch_diameter
gear_body.OuterDiameter = outer_diameter
gear_body.FaceWidth = face_width

# Create the central hub
hub = body.newObject("PartDesign::Cylinder", "Hub")
hub.Radius = hub_diameter / 2
hub.Height = overall_width
hub.Placement.Base = FreeCAD.Vector(0, 0, overall_width / 2)

# Create the round through bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = shaft_diameter / 2
bore.Height = overall_width
bore.Placement.Base = FreeCAD.Vector(0, 0, overall_width / 2)

# Position the hub and bore concentrically with the gear body
gear_body.Placement.Base = FreeCAD.Vector(0, 0, overall_width / 2)
hub.Placement.Base = FreeCAD.Vector(0, 0, overall_width / 2)
bore.Placement.Base = FreeCAD.Vector(0, 0, overall_width / 2)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))

# Close the document
FreeCAD.closeDocument(doc.Name)
