```python
import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear stock
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 21.1582 / 2  # pitch_diameter / 2
cylinder.Height = 304.8  # overall_length

# Create a PartDesign Feature to define the tooth geometry
tooth_feature = body.newObject("PartDesign::Feature", "ToothFeature")
tooth_feature.Label = "Tooth Geometry"
tooth_feature.Proxy = None  # This will be set later

# Create a PartDesign Feature to define the tooth profile
tooth_profile = body.newObject("PartDesign::Pocket", "ToothProfile")
tooth_profile.Label = "Tooth Profile"
tooth_profile.Profile = tooth_feature
tooth_profile.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_profile.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth spacing
tooth_spacing = body.newObject("PartDesign::Pocket", "ToothSpacing")
tooth_spacing.Label = "Tooth Spacing"
tooth_spacing.Profile = tooth_feature
tooth_spacing.Length = 21.1582  # pitch_diameter
tooth_spacing.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth depth
tooth_depth = body.newObject("PartDesign::Pocket", "ToothDepth")
tooth_depth.Label = "Tooth Depth"
tooth_depth.Profile = tooth_feature
tooth_depth.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_depth.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth width
tooth_width = body.newObject("PartDesign::Pocket", "ToothWidth")
tooth_width.Label = "Tooth Width"
tooth_width.Profile = tooth_feature
tooth_width.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_width.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth height
tooth_height = body.newObject("PartDesign::Pocket", "ToothHeight")
tooth_height.Label = "Tooth Height"
tooth_height.Profile = tooth_feature
tooth_height.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_height.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth thickness
tooth_thickness = body.newObject("PartDesign::Pocket", "ToothThickness")
tooth_thickness.Label = "Tooth Thickness"
tooth_thickness.Profile = tooth_feature
tooth_thickness.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_thickness.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth clearance
tooth_clearance = body.newObject("PartDesign::Pocket", "ToothClearance")
tooth_clearance.Label = "Tooth Clearance"
tooth_clearance.Profile = tooth_feature
tooth_clearance.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_clearance.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth root
tooth_root = body.newObject("PartDesign::Pocket", "ToothRoot")
tooth_root.Label = "Tooth Root"
tooth_root.Profile = tooth_feature
tooth_root.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_root.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth tip
tooth_tip = body.newObject("PartDesign::Pocket", "ToothTip")
tooth_tip.Label = "Tooth Tip"
tooth_tip.Profile = tooth_feature
tooth_tip.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_tip.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth profile
tooth_profile = body.newObject("PartDesign::Pocket", "ToothProfile")
tooth_profile.Label = "Tooth Profile"
tooth_profile.Profile = tooth_feature
tooth_profile.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_profile.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth spacing
tooth_spacing = body.newObject("PartDesign::Pocket", "ToothSpacing")
tooth_spacing.Label = "Tooth Spacing"
tooth_spacing.Profile = tooth_feature
tooth_spacing.Length = 21.1582  # pitch_diameter
tooth_spacing.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth depth
tooth_depth = body.newObject("PartDesign::Pocket", "ToothDepth")
tooth_depth.Label = "Tooth Depth"
tooth_depth.Profile = tooth_feature
tooth_depth.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_depth.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth width
tooth_width = body.newObject("PartDesign::Pocket", "ToothWidth")
tooth_width.Label = "Tooth Width"
tooth_width.Profile = tooth_feature
tooth_width.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_width.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth height
tooth_height = body.newObject("PartDesign::Pocket", "ToothHeight")
tooth_height.Label = "Tooth Height"
tooth_height.Profile = tooth_feature
tooth_height.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_height.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth thickness
tooth_thickness = body.newObject("PartDesign::Pocket", "ToothThickness")
tooth_thickness.Label = "Tooth Thickness"
tooth_thickness.Profile = tooth_feature
tooth_thickness.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_thickness.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth clearance
tooth_clearance = body.newObject("PartDesign::Pocket", "ToothClearance")
tooth_clearance.Label = "Tooth Clearance"
tooth_clearance.Profile = tooth_feature
tooth_clearance.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_clearance.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth root
tooth_root = body.newObject("PartDesign::Pocket", "ToothRoot")
tooth_root.Label = "Tooth Root"
tooth_root.Profile = tooth_feature
tooth_root.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_root.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth tip
tooth_tip = body.newObject("PartDesign::Pocket", "ToothTip")
tooth_tip.Label = "Tooth Tip"
tooth_tip.Profile = tooth_feature
tooth_tip.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_tip.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth profile
tooth_profile = body.newObject("PartDesign::Pocket", "ToothProfile")
tooth_profile.Label = "Tooth Profile"
tooth_profile.Profile = tooth_feature
tooth_profile.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_profile.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth spacing
tooth_spacing = body.newObject("PartDesign::Pocket", "ToothSpacing")
tooth_spacing.Label = "Tooth Spacing"
tooth_spacing.Profile = tooth_feature
tooth_spacing.Length = 21.1582  # pitch_diameter
tooth_spacing.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth depth
tooth_depth = body.newObject("PartDesign::Pocket", "ToothDepth")
tooth_depth.Label = "Tooth Depth"
tooth_depth.Profile = tooth_feature
tooth_depth.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_depth.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth width
tooth_width = body.newObject("PartDesign::Pocket", "ToothWidth")
tooth_width.Label = "Tooth Width"
tooth_width.Profile = tooth_feature
tooth_width.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_width.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth height
tooth_height = body.newObject("PartDesign::Pocket", "ToothHeight")
tooth_height.Label = "Tooth Height"
tooth_height.Profile = tooth_feature
tooth_height.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_height.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth thickness
tooth_thickness = body.newObject("PartDesign::Pocket", "ToothThickness")
tooth_thickness.Label = "Tooth Thickness"
tooth_thickness.Profile = tooth_feature
tooth_thickness.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_thickness.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth clearance
tooth_clearance = body.newObject("PartDesign::Pocket", "ToothClearance")
tooth_clearance.Label = "Tooth Clearance"
tooth_clearance.Profile = tooth_feature
tooth_clearance.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_clearance.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth root
tooth_root = body.newObject("PartDesign::Pocket", "ToothRoot")
tooth_root.Label = "Tooth Root"
tooth_root.Profile = tooth_feature
tooth_root.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_root.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth tip
tooth_tip = body.newObject("PartDesign::Pocket", "ToothTip")
tooth_tip.Label = "Tooth Tip"
tooth_tip.Profile = tooth_feature
tooth_tip.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_tip.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth profile
tooth_profile = body.newObject("PartDesign::Pocket", "ToothProfile")
tooth_profile.Label = "Tooth Profile"
tooth_profile.Profile = tooth_feature
tooth_profile.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_profile.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth spacing
tooth_spacing = body.newObject("PartDesign::Pocket", "ToothSpacing")
tooth_spacing.Label = "Tooth Spacing"
tooth_spacing.Profile = tooth_feature
tooth_spacing.Length = 21.1582  # pitch_diameter
tooth_spacing.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth depth
tooth_depth = body.newObject("PartDesign::Pocket", "ToothDepth")
tooth_depth.Label = "Tooth Depth"
tooth_depth.Profile = tooth_feature
tooth_depth.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_depth.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth width
tooth_width = body.newObject("PartDesign::Pocket", "ToothWidth")
tooth_width.Label = "Tooth Width"
tooth_width.Profile = tooth_feature
tooth_width.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_width.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth height
tooth_height = body.newObject("PartDesign::Pocket", "ToothHeight")
tooth_height.Label = "Tooth Height"
tooth_height.Profile = tooth_feature
tooth_height.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_height.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth thickness
tooth_thickness = body.newObject("PartDesign::Pocket", "ToothThickness")
tooth_thickness.Label = "Tooth Thickness"
tooth_thickness.Profile = tooth_feature
tooth_thickness.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_thickness.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth clearance
tooth_clearance = body.newObject("PartDesign::Pocket", "ToothClearance")
tooth_clearance.Label = "Tooth Clearance"
tooth_clearance.Profile = tooth_feature
tooth_clearance.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_clearance.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth root
tooth_root = body.newObject("PartDesign::Pocket", "ToothRoot")
tooth_root.Label = "Tooth Root"
tooth_root.Profile = tooth_feature
tooth_root.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_root.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth tip
tooth_tip = body.newObject("PartDesign::Pocket", "ToothTip")
tooth_tip.Label = "Tooth Tip"
tooth_tip.Profile = tooth_feature
tooth_tip.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_tip.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth profile
tooth_profile = body.newObject("PartDesign::Pocket", "ToothProfile")
tooth_profile.Label = "Tooth Profile"
tooth_profile.Profile = tooth_feature
tooth_profile.Length = 23.368 - 21.1582  # outer_diameter - pitch_diameter
tooth_profile.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth spacing
tooth_spacing = body.newObject("PartDesign::Pocket", "ToothSpacing")
tooth_spacing.Label = "Tooth Spacing"
tooth_spacing.Profile = tooth_feature
tooth_spacing.Length = 21.1582  # pitch_diameter
tooth_spacing.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth depth
tooth_depth = body.newObject("PartDesign::Pocket", "ToothDepth")
tooth_depth.Label = "Tooth Depth"
tooth_depth.Profile = tooth_feature
tooth_depth.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_depth.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth width
tooth_width = body.newObject("PartDesign::Pocket", "ToothWidth")
tooth_width.Label = "Tooth Width"
tooth_width.Profile = tooth_feature
tooth_width.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_width.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth height
tooth_height = body.newObject("PartDesign::Pocket", "ToothHeight")
tooth_height.Label = "Tooth Height"
tooth_height.Profile = tooth_feature
tooth_height.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_height.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth thickness
tooth_thickness = body.newObject("PartDesign::Pocket", "ToothThickness")
tooth_thickness.Label = "Tooth Thickness"
tooth_thickness.Profile = tooth_feature
tooth_thickness.Length = 21.1582 / 2  # pitch_diameter / 2
tooth_thickness.LengthFilletRadius = 0.0  # No fillet

# Create a PartDesign Feature to define the tooth clearance
tooth_clearance = body.newObject("PartDesign::Pocket", "ToothClearance")
tooth_clearance.Label = "Tooth Clearance"
tooth_clearance.Profile = tooth_feature
tooth_clearance.Length