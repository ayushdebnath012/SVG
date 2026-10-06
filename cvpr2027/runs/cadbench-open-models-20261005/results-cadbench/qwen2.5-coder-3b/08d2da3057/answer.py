import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 1  # mm
number_of_teeth = 45
pitch_diameter = 45  # mm
outer_diameter = 47  # mm
face_width = 6  # mm
hub_diameter = 16  # mm
hub_width = 6  # mm
shaft_diameter = 8  # mm
overall_width = 12  # mm
addendum = gear_module  # mm
dedendum = 1.25 * gear_module  # mm
root_diameter = pitch_diameter - 2 * dedendum  # mm
circular_pitch = math.pi * gear_module  # mm
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # mm
whole_depth = addendum + dedendum  # mm
tooth_thickness = circular_pitch / 2  # mm

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create the gear body
gear_body = PartDesign.Body(doc)
gear_body.Label = "Gear Body"

# Create the gear tooth
gear_tooth = PartDesign.Tooth(doc, gear_body)
gear_tooth.Label = "Gear Tooth"
gear_tooth.NumberOfTeeth = number_of_teeth
gear_tooth.GearModule = gear_module
gear_tooth.PressureAngle = pressure_angle
gear_tooth.PitchDiameter = pitch_diameter
gear_tooth.OuterDiameter = outer_diameter
gear_tooth.FaceWidth = face_width
gear_tooth.Addendum = addendum
gear_tooth.Dedendum = dedendum
gear_tooth.WholeDepth = whole_depth
gear_tooth.CircularPitch = circular_pitch
gear_tooth.BaseDiameter = base_diameter
gear_tooth.ToothThickness = tooth_thickness

# Create the hub
hub = PartDesign.Hub(doc, gear_body)
hub.Label = "Hub"
hub.HubDiameter = hub_diameter
hub.HubWidth = hub_width
hub.OverallWidth = overall_width

# Create the round bore
round_bore = PartDesign.Bore(doc, gear_body)
round_bore.Label = "Round Bore"
round_bore.Diameter = shaft_diameter

# Save the document
output_path = FreeCAD.getHomePath() + "/app/answer.FCStd"
doc.saveAs(output_path)
