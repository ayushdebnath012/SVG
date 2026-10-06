import FreeCAD
import PartDesign
import Part
import math

# Define the parameters
pressure_angle = 20  # degrees
gear_module = 2  # mm
number_of_teeth = 30
pitch_diameter = 60  # mm
outer_diameter = 64  # mm
face_width = 20  # mm
hub_diameter = 50  # mm
hub_width = 10  # mm
shaft_diameter = 10  # mm
overall_width = 30  # mm
addendum = pitch_diameter / number_of_teeth  # ISO 21771
dedendum = 1.25 * gear_module  # ISO 21771
whole_depth = addendum + dedendum  # ISO 21771
root_diameter = pitch_diameter - 2 * dedendum  # ISO 21771
base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # ISO 21771
circular_pitch = math.pi * gear_module  # ISO 21771
tooth_thickness = circular_pitch / 2  # ISO 21771

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
gear_tooth.FaceWidth = face_width
gear_tooth.PitchDiameter = pitch_diameter
gear_tooth.OuterDiameter = outer_diameter
gear_tooth.RootDiameter = root_diameter
gear_tooth.BaseDiameter = base_diameter
gear_tooth.Addendum = addendum
gear_tooth.Dedendum = dedendum
gear_tooth.WholeDepth = whole_depth
gear_tooth.CircularPitch = circular_pitch
gear_tooth.ToothThickness = tooth_thickness

# Create the hub
hub = PartDesign.Hub(doc, gear_body)
hub.Label = "Hub"
hub.HubDiameter = hub_diameter
hub.HubWidth = hub_width
hub.OverallWidth = overall_width

# Create the round bore
bore = PartDesign.Bore(doc, gear_body)
bore.Label = "Bore"
bore.Diameter = shaft_diameter
bore.Position = (0, 0, 0)  # Center of the gear and hub

# Save the document
output_path = FreeCAD.getHomePath() + "/app/answer.FCStd"
doc.saveAs(output_path)
