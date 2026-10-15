import FreeCAD as App
import Part
from Part import Shape
from pathlib import Path

# Create Document
doc = App.newDocument("MainBody")

# --- 1. Parameters ---
params = doc.addObject("App::Variations", "Parameters")
params.addProperty("App::PropertyLength", "main_body_thickness", "Dimensions", "Plate thickness")
params.addProperty("App::PropertyLength", "main_body_upper_edge_height", "Dimensions", "Top frame height")
params.addProperty("App::PropertyLength", "main_body_upper_shoulder_height", "Dimensions", "Rib attachment height")
params.addProperty("App::PropertyLength", "main_body_lower_shoulder_height", "Dimensions", "Rib bottom height")
params.addProperty("App::PropertyLength", "main_body_lower_edge_height", "Dimensions", "Bottom frame height")
params.addProperty("App::PropertyLength", "main_body_cutout_cross_section_length", "Dimensions", "Rear recess width")
params.addProperty("App::PropertyLength", "rectangular_cutout_length", "Dimensions", "Rear recess width (alternative)")
params.addProperty("App::PropertyLength", "main_body_cross_section_length", "Dimensions", "Rear pad width")
params.addProperty("App::PropertyLength", "main_body_cross_section_width", "Dimensions", "Rear pad height")
params.addProperty("App::PropertyLength", "secondary_body_thickness", "Dimensions", "Rear pad depth")
params.addProperty("App::PropertyLength", "lug_cross_section_width", "Dimensions", "Lug lateral width")
params.addProperty("App::PropertyLength", "upper_lug_cross_section_length", "Dimensions", "Upper lug height")
params.addProperty("App::PropertyLength", "lower_lug_cross_section_length", "Dimensions", "Lower lug height")
params.addProperty("App::PropertyLength", "upper_lug_lower_edge_height", "Dimensions", "Upper lug bottom Y")
params.addProperty("App::PropertyLength", "lower_lug_lower_edge_height", "Dimensions", "Lower lug bottom Y")
params.addProperty("App::PropertyLength", "main_body_cutout_cross_section_width", "Dimensions", "Rear recess height")
params.addProperty("App::PropertyLength", "main_body_cutout_corner_radius", "Dimensions", "Rear recess corner radius")
params.addProperty("App::PropertyLength", "main_body_cutout_depth", "Dimensions", "Rear recess depth")
params.addProperty("App::PropertyLength", "main_recess_lower_edge_height", "Dimensions", "Rear recess bottom Y")
params.addProperty("App::PropertyLength", "cutout_depth", "Dimensions", "Side chamfered cutout depth")
params.addProperty("App::PropertyLength", "side_chamfered_cutout_center_x", "Dimensions", "Side cutout X from mid-plane")
params.addProperty("App::PropertyLength", "side_chamfered_cutout_center_y", "Dimensions", "Side cutout Y")
params.addProperty("App::PropertyLength", "side_chamfered_cutout_flat_width", "Dimensions", "Side cutout flat width")
params.addProperty("App::PropertyLength", "side_chamfered_cutout_flat_height", "Dimensions", "Side cutout flat height")
params.addProperty("App::PropertyLength", "side_chamfer_size", "Dimensions", "Side chamfer size")
params.addProperty("App::PropertyLength", "main_body_extrusion_length", "Dimensions", "Rib length")
params.addProperty("App::PropertyLength", "small_rectangular_cutout_length", "Dimensions", "Rib base width")
params.addProperty("App::PropertyLength", "cap_baseline_frontward_offset", "Dimensions", "Rib base offset")
params.addProperty("App::PropertyLength", "cap_rise", "Dimensions", "Rib tip rise")
params.addProperty("App::PropertyLength", "rectangular_cutout_width", "Dimensions", "Rear recess width")
params.addProperty("App::PropertyLength", "shallow_rectangular_cutout_depth", "Dimensions", "Rear recess depth")
params.addProperty("App::PropertyLength", "shallow_rectangular_cutout_lower_edge_height", "Dimensions", "Rear recess bottom Y")
params.addProperty("App::PropertyLength", "cutout_half_width", "Dimensions", "Front window half width")
params.addProperty("App::PropertyLength", "front_window_lower_edge_height", "Dimensions", "Front window bottom Y")
params.addProperty("App::PropertyLength", "front_window_upper_edge_height", "Dimensions", "Front window top Y")
params.addProperty("App::PropertyLength", "side_through_hole_diameter", "Dimensions", "Side hole diameter")
params.addProperty("App::PropertyLength", "side_hole_a_center_x", "Dimensions", "Side hole A X")
params.addProperty("App::PropertyLength", "side_hole_a_center_y", "Dimensions", "Side hole A Y")
params.addProperty("App::PropertyLength", "side_hole_b_center_x", "Dimensions", "Side hole B X")
params.addProperty("App::PropertyLength", "side_hole_b_center_y", "Dimensions", "Side hole B Y")
params.addProperty("App::PropertyLength", "dual_body_through_hole_diameter", "Dimensions", "Bottom hole diameter")
params.addProperty("App::PropertyLength", "bottom_hole_pair_center_height", "Dimensions", "Bottom hole pair center Y")
params.addProperty("App::PropertyLength", "bottom_hole_pair_spacing", "Dimensions", "Bottom hole pair spacing")
params.addProperty("App::PropertyLength", "common_cutout_length", "Dimensions", "Square/Short cutout length")
params.addProperty("App::PropertyLength", "square_main_body_cutout_depth", "Dimensions", "Square cutout depth")
params.addProperty("App::PropertyLength", "square_cutout_lower_edge_height", "Dimensions", "Square cutout bottom Y")
params.addProperty("App::PropertyLength", "short_rectangular_cutout_length", "Dimensions", "Short cutout length")
params.addProperty("App::PropertyLength", "short_rectangular_cutout_width", "Dimensions", "Short cutout width")
params.addProperty("App::PropertyLength", "short_rectangular_cutout_depth", "Dimensions", "Short cutout depth")
params.addProperty("App::PropertyLength", "short_cutout_lower_edge_height", "Dimensions", "Short cutout bottom Y")
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "Mounting hole diameter")
params.addProperty("App::PropertyLength", "hole_cut_depth", "Dimensions", "Mounting hole depth")
params.addProperty("App::PropertyLength", "mounting_hole_column_center_offset", "Dimensions", "Mounting hole column offset")
params.addProperty("App::PropertyLength", "mounting_hole_upper_row_center_height", "Dimensions", "Mounting hole upper Y")
params.addProperty("App::PropertyLength", "mounting_hole_lower_row_center_height", "Dimensions", "Mounting hole lower Y")
params.addProperty("App::PropertyLength", "triangular_cutout_width", "Dimensions", "Triangular cutout width")
params.addProperty("App::PropertyLength", "triangular_cutout_lower_vertex_height", "Dimensions", "Triangular cutout bottom Y")
params.addProperty("App::PropertyLength", "rectangular_cutout_depth", "Dimensions", "Lug pocket depth")
params.addProperty("App::PropertyLength", "repeated_cutout_column_center_offset", "Dimensions", "Lug pocket column offset")
params.addProperty("App::PropertyLength", "repeated_cutout_lower_row_center_height", "Dimensions", "Lug pocket lower Y")
params.addProperty("App::PropertyLength", "repeated_cutout_upper_row_center_height", "Dimensions", "Lug pocket upper Y")
params.addProperty("App::PropertyLength", "narrow_rectangular_cutout_width", "Dimensions", "Top narrow cutout width")
params.addProperty("App::PropertyLength", "top_narrow_cutout_lower_edge_height", "Dimensions", "Top narrow cutout bottom Y")

# Set values
params.main_body_thickness = 28.00
params.main_body_upper_edge_height = 70.50
params.main_body_upper_shoulder_height = 28.50
params.main_body_lower_shoulder_height = -43.50
params.main_body_lower_edge_height = -70.50
params.main_body_cutout_cross_section_length = 32.00
params.rectangular_cutout_length = 50.80
params.main_body_cross_section_length = 26.00
params.main_body_cross_section_width = 5.00
params.secondary_body_thickness = 12.00
params.lug_cross_section_width = 11.00
params.upper_lug_cross_section_length = 31.80
params.lower_lug_cross_section_length = 14.40
params.upper_lug_lower_edge_height = 28.50
params.lower_lug_lower_edge_height = -57.90
params.main_body_cutout_cross_section_width = 105.00
params.main_body_cutout_corner_radius = 3.00
params.main_body_cutout_depth = 22.00
params.main_recess_lower_edge_height = -65.50
params.cutout_depth = 4.00
params.side_chamfered_cutout_center_x = 1.00
params.side_chamfered_cutout_center_y = 14.65
params.side_chamfered_cutout_flat_width = 17.00
params.side_chamfered_cutout_flat_height = 27.70
params.side_chamfer_size = 1.00
params.main_body_extrusion_length = 27.70
params.small_rectangular_cutout_length = 4.00
params.cap_baseline_frontward_offset = -10.50
params.cap_rise = 2.31
params.rectangular_cutout_width = 6.00
params.shallow_rectangular_cutout_depth = 1.90
params.shallow_rectangular_cutout_lower_edge_height = 22.50
params.cutout_half_width = 8.00
params.front_window_lower_edge_height = 2.50
params.front_window_upper_edge_height = 26.50
params.side_through_hole_diameter = 2.80
params.side_hole_a_center_x = -7.98
params.side_hole_a_center_y = -6.50
params.side_hole_b_center_x = 0.72
params.side_hole_b_center_y = -41.00
params.dual_body_through_hole_diameter = 3.00
params.bottom_hole_pair_center_height = -9.00
params.bottom_hole_pair_spacing = 15.00
params.common_cutout_length = 15.00
params.square_main_body_cutout_depth = 14.00
params.square_cutout_lower_edge_height = 45.30
params.short_rectangular_cutout_length = 15.00
params.short_rectangular_cutout_width = 10.00
params.short_rectangular_cutout_depth = 14.00
params.short_cutout_lower_edge_height = -57.90
params.mounting_hole_diameter = 7.00
params.hole_cut_depth = 7.50
params.mounting_hole_column_center_offset = 24.50
params.mounting_hole_upper_row_center_height = 65.70
params.mounting_hole_lower_row_center_height = -62.90
params.triangular_cutout_width = 15.00
params.triangular_cutout_lower_vertex_height = 60.30
params.rectangular_cutout_depth = 5.00
params.repeated_cutout_column_center_offset = 36.00
params.repeated_cutout_lower_row_center_height = -50.55
params.repeated_cutout_upper_row_center_height = 39.45
params.narrow_rectangular_cutout_width = 5.00
params.top_narrow_cutout_lower_edge_height = 62.50

# --- 2. Body & Sketches ---
body = doc.addObject("PartDesign::Body", "Body")
body.PartName = "Body"

# Helper to create sketch on a plane
def create_sketch(name, plane_obj):
    s = body.newObject("Sketcher::SketchObject", name)
    s.Placement = App.Placement(plane_obj, App.Rotation())
    s.ConstraintType = "NoConstraint"
    return s

# Base Sketch: Front Face (XZ plane, centered on plate)
# Origin at (0,0,0) -> Mid-thickness plane intersection
sketch_base = create_sketch("sketch_base", doc.getObject("XY_Plane")) # X=Right, Z=Up
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))

# Define Frame Profile on Front Face (XZ)
# Thickness is along Y. Width is Z (height). Length is X.
# The plate is symmetric about X=0.
# Main body outer width (Z) = main_body_cross_section_length = 26
# Main body height (X) = main_body_upper_edge_height to main_body_lower_edge_height (70.5 to -70.5)
# Lugs are lateral (along Y). They will be defined in a separate sketch on a side plane.

# Frame Outer Rectangle
sketch_base.addGeometry(Part.LineSegment(App.Vector(-13, 13, -70.5), App.Vector(-13, 13, 70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(-13, 13, 70.5), App.Vector(13, 13, 70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(13, 13, 70.5), App.Vector(13, 13, -70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(13, 13, -70.5), App.Vector(13, -13, -70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(13, -13, -70.5), App.Vector(-13, -13, -70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(-13, -13, -70.5), App.Vector(-13, -13, 70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(-13, -13, 70.5), App.Vector(-13, 13, 70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(13, -13, -70.5), App.Vector(13, 13, -70.5)), True)
sketch_base.addGeometry(Part.LineSegment(App.Vector(13, 13, 70.5), App.Vector(13, -13, 70.5)), True)

# Constraints for Frame Base
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1)) # Top-Left corner
sketch_base.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 13, -13))
sketch_base.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_base.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, -70.5, 13, -70.5))
sketch_base.recompute()

# --- 3. Features ---

# 3.1 Main Body Block (Pad)
# This creates the base plate thickness.
pad_main = body.newObject("PartDesign::Pad", "Pad_Main")
pad_main.Profile = sketch_base
pad_main.Length = params.main_body_thickness
pad_main.Type = "Full"
pad_main.Reversed = False
pad_main.Thickness = params.main_body_thickness
pad_main.setExpression("Length", "Parameters.main_body_thickness")
body.addFeature(pad_main)
doc.recompute()

# 3.2 Upper Crosspiece (Pad)
# Located at top (Z = main_body_upper_edge_height)
sketch_upper = create_sketch("sketch_upper", doc.getObject("XZ_Plane"))
sketch_upper.Placement = App.Placement(App.Vector(0, 0, params.main_body_upper_edge_height), App.Rotation())
# Rectangle: Width X main_body_cross_section_length, Height params.main_body_cross_section_width (wait, height is Z)
# The crosspiece is a block on top.
# X range: -13 to 13 (same as base width)
# Z range: params.main_body_cross_section_width (5.0)
# Y range: -13 to 13 (same as base width)
sketch_upper.addGeometry(Part.LineSegment(App.Vector(-13, 13, 0), App.Vector(-13, 13, 5)), True)
sketch_upper.addGeometry(Part.LineSegment(App.Vector(-13, 13, 5), App.Vector(13, 13, 5)), True)
sketch_upper.addGeometry(Part.LineSegment(App.Vector(13, 13, 5), App.Vector(13, 13, 0)), True)
sketch_upper.addGeometry(Part.LineSegment(App.Vector(13, 13, 0), App.Vector(-13, 13, 0)), True)
sketch_upper.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_upper.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 13, -13))
sketch_upper.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_upper.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 5, 13, 0))
sketch_upper.recompute()

pad_upper = body.newObject("PartDesign::Pad", "Pad_Upper")
pad_upper.Profile = sketch_upper
pad_upper.Length = params.main_body_thickness
pad_upper.Type = "Full"
pad_upper.Reversed = False
pad_upper.Thickness = params.main_body_thickness
pad_upper.setExpression("Length", "Parameters.main_body_thickness")
body.addFeature(pad_upper)
doc.recompute()

# 3.3 Lower Foot (Pad)
# Located at bottom (Z = main_body_lower_edge_height)
sketch_lower = create_sketch("sketch_lower", doc.getObject("XZ_Plane"))
sketch_lower.Placement = App.Placement(App.Vector(0, 0, params.main_body_lower_edge_height), App.Rotation())
# Rectangle: Width X main_body_cross_section_length, Height params.main_body_cross_section_width (5.0)
sketch_lower.addGeometry(Part.LineSegment(App.Vector(-13, 13, 0), App.Vector(-13, 13, 5)), True)
sketch_lower.addGeometry(Part.LineSegment(App.Vector(-13, 13, 5), App.Vector(13, 13, 5)), True)
sketch_lower.addGeometry(Part.LineSegment(App.Vector(13, 13, 5), App.Vector(13, 13, 0)), True)
sketch_lower.addGeometry(Part.LineSegment(App.Vector(13, 13, 0), App.Vector(-13, 13, 0)), True)
sketch_lower.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_lower.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 13, -13))
sketch_lower.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_lower.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 5, 13, 0))
sketch_lower.recompute()

pad_lower = body.newObject("PartDesign::Pad", "Pad_Lower")
pad_lower.Profile = sketch_lower
pad_lower.Length = params.main_body_thickness
pad_lower.Type = "Full"
pad_lower.Reversed = False
pad_lower.Thickness = params.main_body_thickness
pad_lower.setExpression("Length", "Parameters.main_body_thickness")
body.addFeature(pad_lower)
doc.recompute()

# 3.4 Central Stem (Pad)
# Located between upper and lower shoulders
sketch_stem = create_sketch("sketch_stem", doc.getObject("XZ_Plane"))
sketch_stem.Placement = App.Placement(App.Vector(0, 0, params.main_body_upper_shoulder_height), App.Rotation())
# Rectangle: Width X rectangular_cutout_length (50.8), Height params.main_body_cross_section_width (5.0)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(-25.4, 13, 0), App.Vector(-25.4, 13, 5)), True)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(-25.4, 13, 5), App.Vector(25.4, 13, 5)), True)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(25.4, 13, 5), App.Vector(25.4, 13, 0)), True)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(25.4, 13, 0), App.Vector(-25.4, 13, 0)), True)
sketch_stem.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_stem.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 25.4, -25.4))
sketch_stem.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_stem.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 5, 13, 0))
sketch_stem.recompute()

pad_stem = body.newObject("PartDesign::Pad", "Pad_Stem")
pad_stem.Profile = sketch_stem
pad_stem.Length = params.main_body_thickness
pad_stem.Type = "Full"
pad_stem.Reversed = False
pad_stem.Thickness = params.main_body_thickness
pad_stem.setExpression("Length", "Parameters.main_body_thickness")
body.addFeature(pad_stem)
doc.recompute()

# 3.5 Lugs (Pad)
# Upper Lug
sketch_lug_upper = create_sketch("sketch_lug_upper", doc.getObject("YZ_Plane"))
sketch_lug_upper.Placement = App.Placement(App.Vector(0, params.upper_lug_lower_edge_height, 0), App.Rotation())
# Rectangle: Width Y lug_cross_section_width (11), Height Z upper_lug_cross_section_length (31.8)
sketch_lug_upper.addGeometry(Part.LineSegment(App.Vector(-5.5, 13, 0), App.Vector(-5.5, 13, 31.8)), True)
sketch_lug_upper.addGeometry(Part.LineSegment(App.Vector(-5.5, 13, 31.8), App.Vector(5.5, 13, 31.8)), True)
sketch_lug_upper.addGeometry(Part.LineSegment(App.Vector(5.5, 13, 31.8), App.Vector(5.5, 13, 0)), True)
sketch_lug_upper.addGeometry(Part.LineSegment(App.Vector(5.5, 13, 0), App.Vector(-5.5, 13, 0)), True)
sketch_lug_upper.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_lug_upper.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 5.5, -5.5))
sketch_lug_upper.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_lug_upper.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 31.8, 13, 0))
sketch_lug_upper.recompute()

pad_lug_upper = body.newObject("PartDesign::Pad", "Pad_Lug_Upper")
pad_lug_upper.Profile = sketch_lug_upper
pad_lug_upper.Length = params.main_body_thickness
pad_lug_upper.Type = "Full"
pad_lug_upper.Reversed = False
pad_lug_upper.Thickness = params.main_body_thickness
pad_lug_upper.setExpression("Length", "Parameters.main_body_thickness")
body.addFeature(pad_lug_upper)
doc.recompute()

# Lower Lug
sketch_lug_lower = create_sketch("sketch_lug_lower", doc.getObject("YZ_Plane"))
sketch_lug_lower.Placement = App.Placement(App.Vector(0, params.lower_lug_lower_edge_height, 0), App.Rotation())
# Rectangle: Width Y lug_cross_section_width (11), Height Z lower_lug_cross_section_length (14.4)
sketch_lug_lower.addGeometry(Part.LineSegment(App.Vector(-5.5, 13, 0), App.Vector(-5.5, 13, 14.4)), True)
sketch_lug_lower.addGeometry(Part.LineSegment(App.Vector(-5.5, 13, 14.4), App.Vector(5.5, 13, 14.4)), True)
sketch_lug_lower.addGeometry(Part.LineSegment(App.Vector(5.5, 13, 14.4), App.Vector(5.5, 13, 0)), True)
sketch_lug_lower.addGeometry(Part.LineSegment(App.Vector(5.5, 13, 0), App.Vector(-5.5, 13, 0)), True)
sketch_lug_lower.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_lug_lower.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 5.5, -5.5))
sketch_lug_lower.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_lug_lower.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 14.4, 13, 0))
sketch_lug_lower.recompute()

pad_lug_lower = body.newObject("PartDesign::Pad", "Pad_Lug_Lower")
pad_lug_lower.Profile = sketch_lug_lower
pad_lug_lower.Length = params.main_body_thickness
pad_lug_lower.Type = "Full"
pad_lug_lower.Reversed = False
pad_lug_lower.Thickness = params.main_body_thickness
pad_lug_lower.setExpression("Length", "Parameters.main_body_thickness")
body.addFeature(pad_lug_lower)
doc.recompute()

# 3.6 Rear Recess (Pocket)
# Centered on rear face (Y = -14), bottom at main_recess_lower_edge_height
sketch_recess = create_sketch("sketch_recess", doc.getObject("XZ_Plane"))
sketch_recess.Placement = App.Placement(App.Vector(0, -14, params.main_recess_lower_edge_height), App.Rotation())
# Rectangle: Width X main_body_cutout_cross_section_length (32), Height Z main_body_cutout_cross_section_width (105)
sketch_recess.addGeometry(Part.LineSegment(App.Vector(-16, 13, 0), App.Vector(-16, 13, 105)), True)
sketch_recess.addGeometry(Part.LineSegment(App.Vector(-16, 13, 105), App.Vector(16, 13, 105)), True)
sketch_recess.addGeometry(Part.LineSegment(App.Vector(16, 13, 105), App.Vector(16, 13, 0)), True)
sketch_recess.addGeometry(Part.LineSegment(App.Vector(16, 13, 0), App.Vector(-16, 13, 0)), True)
sketch_recess.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_recess.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 16, -16))
sketch_recess.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_recess.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 105, 13, 0))
sketch_recess.recompute()

pocket_recess = body.newObject("PartDesign::Pocket", "Pocket_Recess")
pocket_recess.Profile = sketch_recess
pocket_recess.Length = params.main_body_cutout_depth
pocket_recess.Type = "Blind"
pocket_recess.Reversed = False
pocket_recess.Thickness = params.main_body_cutout_depth
pocket_recess.setExpression("Length", "Parameters.main_body_cutout_depth")
body.addFeature(pocket_recess)
doc.recompute()

# 3.7 Side Chamfered Cutouts (Pocket)
# Right Side (Y = 14)
sketch_side_cutout = create_sketch("sketch_side_cutout", doc.getObject("XZ_Plane"))
sketch_side_cutout.Placement = App.Placement(App.Vector(0, 14, params.side_chamfered_cutout_center_y), App.Rotation())
# Rectangle: Width X side_chamfered_cutout_flat_width (17), Height Z side_chamfered_cutout_flat_height (27.7)
sketch_side_cutout.addGeometry(Part.LineSegment(App.Vector(-8.5, 13, 0), App.Vector(-8.5, 13, 27.7)), True)
sketch_side_cutout.addGeometry(Part.LineSegment(App.Vector(-8.5, 13, 27.7), App.Vector(8.5, 13, 27.7)), True)
sketch_side_cutout.addGeometry(Part.LineSegment(App.Vector(8.5, 13, 27.7), App.Vector(8.5, 13, 0)), True)
sketch_side_cutout.addGeometry(Part.LineSegment(App.Vector(8.5, 13, 0), App.Vector(-8.5, 13, 0)), True)
sketch_side_cutout.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_side_cutout.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 8.5, -8.5))
sketch_side_cutout.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_side_cutout.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 27.7, 13, 0))
sketch_side_cutout.recompute()

pocket_side_cutout = body.newObject("PartDesign::Pocket", "Pocket_Side_Cutout")
pocket_side_cutout.Profile = sketch_side_cutout
pocket_side_cutout.Length = params.cutout_depth
pocket_side_cutout.Type = "Blind"
pocket_side_cutout.Reversed = False
pocket_side_cutout.Thickness = params.cutout_depth
pocket_side_cutout.setExpression("Length", "Parameters.cutout_depth")
body.addFeature(pocket_side_cutout)
doc.recompute()

# Left Side (Mirror)
sketch_side_cutout_left = create_sketch("sketch_side_cutout_left", doc.getObject("XZ_Plane"))
sketch_side_cutout_left.Placement = App.Placement(App.Vector(0, -14, params.side_chamfered_cutout_center_y), App.Rotation())
sketch_side_cutout_left.addGeometry(Part.LineSegment(App.Vector(-8.5, 13, 0), App.Vector(-8.5, 13, 27.7)), True)
sketch_side_cutout_left.addGeometry(Part.LineSegment(App.Vector(-8.5, 13, 27.7), App.Vector(8.5, 13, 27.7)), True)
sketch_side_cutout_left.addGeometry(Part.LineSegment(App.Vector(8.5, 13, 27.7), App.Vector(8.5, 13, 0)), True)
sketch_side_cutout_left.addGeometry(Part.LineSegment(App.Vector(8.5, 13, 0), App.Vector(-8.5, 13, 0)), True)
sketch_side_cutout_left.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1))
sketch_side_cutout_left.addConstraint(Sketcher.Constraint("DistanceX", 0, 0, 1, 8.5, -8.5))
sketch_side_cutout_left.addConstraint(Sketcher.Constraint("DistanceY", 0, 0, 1, 13, -13, -13, -13))
sketch_side_cutout_left.addConstraint(Sketcher.Constraint("DistanceZ", 0, 0, 1, 13, 27.7, 13, 0))
sketch_side_cutout_left.recompute()

pocket_side_cutout_left = body.newObject("PartDesign::Pocket", "Pocket_Side_Cutout_Left")
pocket_side_cutout_left.Profile = sketch_side_cutout_left
pocket_side_cutout_left.Length = params.cutout_depth
pocket_side_cutout_left.Type = "Blind"
pocket_side_cutout_left.Reversed = False
pocket_side_cutout_left.Thickness = params.cutout_depth
pocket_side_cutout_left.setExpression("Length", "Parameters.cutout_depth")
body.addFeature(pocket_side_cutout_left)
doc.recompute()

# 3.8 Ribs (Pad)
# Left Rib
sketch_rib_left = create_sketch("sketch_rib_left", doc.getObject("XZ_Plane"))
sketch_rib_left.Placement = App.Placement(App.Vector(0, -14, params.main_body_upper_shoulder_height), App.Rotation())
# Triangle: Base at X = -13 (left edge of stem), tip at X = -13 + small_rectangular_cutout_length (4)
# Base width: small_rectangular_cutout_length (4)
# Height: main_body_extrusion_length (27.7)
# Frontward offset: cap_baseline_frontward_offset (-10.5)
# Rise: cap_rise (2.31)
# The rib is on the underside of the upper crosspiece.
# The upper crosspiece is at Z = 70.5. The rib extends down.
# The rib is on the left side of the stem (X < 0).
# The rib starts at the left stem-side boundary (X = -25.4) and extends toward the frame center (X = 0).
# Wait, the description says "starts at the left stem-side boundary and extends toward the frame center by small_rectangular_cutout_length".
# So
