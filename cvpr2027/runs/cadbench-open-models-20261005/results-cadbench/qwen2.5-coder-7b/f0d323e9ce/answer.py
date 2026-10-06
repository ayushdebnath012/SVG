import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear stock
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 16.9291  # pitch_diameter / 2
cylinder.Height = 304.8  # overall_length

# Create a PartDesign Feature to define the tooth geometry
tooth_feature = body.newObject("PartDesign::Pocket", "ToothFeature")
tooth_feature.Base = cylinder
tooth_feature.Placement.Base = FreeCAD.Vector(0, 0, 0)
tooth_feature.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0)

# Create a PartDesign Feature to define the tooth profile
tooth_profile = body.newObject("PartDesign::Pocket", "ToothProfile")
tooth_profile.Base = tooth_feature
tooth_profile.Length = 4.7625  # whole_depth
tooth_profile.Direction = FreeCAD.Vector(0, 0, 1)

# Create a PartDesign Feature to define the tooth spacing
tooth_spacing = body.newObject("PartDesign::Pad", "ToothSpacing")
tooth_spacing.Base = tooth_profile
tooth_spacing.Length = 304.8  # overall_length
tooth_spacing.Direction = FreeCAD.Vector(0, 0, 1)

# Create a PartDesign Feature to define the gear teeth
gear_teeth = body.newObject("PartDesign::Pocket", "GearTeeth")
gear_teeth.Base = tooth_spacing
gear_teeth.Length = 4.7625  # whole_depth
gear_teeth.Direction = FreeCAD.Vector(0, 0, 1)

# Create a PartDesign Feature to define the gear root
gear_root = body.newObject("PartDesign::Pocket", "GearRoot")
gear_root.Base = gear_teeth
gear_root.Length = 28.5665333334  # root_diameter / 2
gear_root.Direction = FreeCAD.Vector(0, 0, 1)

# Create a PartDesign Feature to define the gear base
gear_base = body.newObject("PartDesign::Pocket", "GearBase")
gear_base.Base = gear_root
gear_base.Length = 31.8164882848  # base_diameter / 2
gear_base.Direction = FreeCAD.Vector(0, 0, 1)

# Save the document
doc.saveAs("/app/answer.FCStd")
