import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear stock
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 19.05 / 2  # pitch diameter / 2
cylinder.Height = 304.8  # overall length

# Create a PartDesign Feature to define the gear parameters
gear_params = body.newObject("PartDesign::FeaturePython", "GearParams")
gear_params.addProperty("App::PropertyInteger", "NumberOfTeeth", "Gear", "Number of teeth")
gear_params.addProperty("App::PropertyAngle", "PressureAngle", "Gear", "Pressure angle")
gear_params.addProperty("App::PropertyLength", "GearModule", "Gear", "Gear module")
gear_params.addProperty("App::PropertyLength", "PitchDiameter", "Gear", "Pitch diameter")
gear_params.addProperty("App::PropertyLength", "OuterDiameter", "Gear", "Outer diameter")
gear_params.addProperty("App::PropertyLength", "OverallLength", "Gear", "Overall length")

gear_params.NumberOfTeeth = 12
gear_params.PressureAngle = 20 * FreeCAD.Units.Degree
gear_params.GearModule = 1.5875 * FreeCAD.Units.Length
gear_params.PitchDiameter = 19.05 * FreeCAD.Units.Length
gear_params.OuterDiameter = 22.352 * FreeCAD.Units.Length
gear_params.OverallLength = 304.8 * FreeCAD.Units.Length

# Create a PartDesign Feature to create the gear teeth
gear_teeth = body.newObject("PartDesign::Gear", "GearTeeth")
gear_teeth.Base = cylinder
gear_teeth.NumberOfTeeth = gear_params.NumberOfTeeth
gear_teeth.PressureAngle = gear_params.PressureAngle
gear_teeth.GearModule = gear_params.GearModule
gear_teeth.PitchDiameter = gear_params.PitchDiameter
gear_teeth.OuterDiameter = gear_params.OuterDiameter

# Create a PartDesign Feature to cut the gear teeth into the cylinder
cutter = body.newObject("PartDesign::Pocket", "Cutter")
cutter.Base = cylinder
cutter.Profile = gear_teeth
cutter.Length = gear_params.OverallLength

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
