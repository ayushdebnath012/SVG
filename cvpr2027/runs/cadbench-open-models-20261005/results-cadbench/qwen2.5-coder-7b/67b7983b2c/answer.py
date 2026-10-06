import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear blank
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 19.701  # outer_diameter / 2
cylinder.Height = 304.8  # overall_length

# Create a PartDesign Feature to define the gear parameters
gear_params = body.newObject("PartDesign::FeaturePython", "GearParams")
gear_params.addProperty("App::PropertyInteger", "NumberOfTeeth", "Gear", "Number of teeth")
gear_params.addProperty("App::PropertyAngle", "PressureAngle", "Gear", "Pressure angle")
gear_params.addProperty("App::PropertyFloat", "DiametralPitch", "Gear", "Diametral pitch")
gear_params.addProperty("App::PropertyFloat", "PitchDiameter", "Gear", "Pitch diameter")
gear_params.addProperty("App::PropertyFloat", "OuterDiameter", "Gear", "Outer diameter")
gear_params.addProperty("App::PropertyFloat", "OverallLength", "Gear", "Overall length")
gear_params.addProperty("App::PropertyFloat", "GearModule", "Gear", "Gear module")

gear_params.NumberOfTeeth = 24
gear_params.PressureAngle = 20 * FreeCAD.Units.Degree
gear_params.DiametralPitch = 16
gear_params.PitchDiameter = 38.1
gear_params.OuterDiameter = 41.402
gear_params.OverallLength = 304.8
gear_params.GearModule = 25.4 / 16

# Create a PartDesign Feature to generate the gear teeth
gear_teeth = body.newObject("PartDesign::Gear", "GearTeeth")
gear_teeth.Base = cylinder
gear_teeth.NumberOfTeeth = gear_params.NumberOfTeeth
gear_teeth.PressureAngle = gear_params.PressureAngle
gear_teeth.DiametralPitch = gear_params.DiametralPitch
gear_teeth.GearModule = gear_params.GearModule
gear_teeth.PitchDiameter = gear_params.PitchDiameter
gear_teeth.OuterDiameter = gear_params.OuterDiameter
gear_teeth.Height = gear_params.OverallLength

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
