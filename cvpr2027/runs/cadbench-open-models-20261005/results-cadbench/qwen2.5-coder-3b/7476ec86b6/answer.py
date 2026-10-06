```python
import FreeCAD
import PartDesign
import Part

# Define the parameters
pressure_angle = 20  # degrees
diametral_pitch = 32
number_of_teeth = 20
pitch_diameter = 15.875  # mm
outer_diameter = 17.526  # mm
face_width = 304.8  # mm
gear_module = 25.4 / diametral_pitch  # mm

# Create a new document
doc = FreeCAD.newDocument("SpurGearStock")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new cylindrical gear body
cylinder = PartDesign.Cylinder(doc, "Cylinder")
cylinder.Radius = outer_diameter / 2
cylinder.Height = face_width
cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a new gear tooth profile
tooth_profile = PartDesign.GearToothProfile(doc, "ToothProfile")
tooth_profile.NumberOfTeeth = number_of_teeth
tooth_profile.PressureAngle = pressure_angle
tooth_profile.GearModule = gear_module
tooth_profile.PitchDiameter = pitch_diameter
tooth_profile.OuterDiameter = outer_diameter

# Create a new gear tooth
tooth = PartDesign.GearTooth(doc, "Tooth")
tooth.Profile = tooth_profile
tooth.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 