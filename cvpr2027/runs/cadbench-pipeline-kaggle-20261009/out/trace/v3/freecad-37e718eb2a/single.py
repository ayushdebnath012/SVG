import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("MountingBracket")

# --- Parameters ---
# Define a VarSet to hold all parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "corner_arc_radius", "Dimensions", "corner_arc_radius")
params.corner_arc_radius = 63.50
params.addProperty("App::PropertyLength", "plate_thickness", "Dimensions", "plate_thickness")
params.plate_thickness = 482.60
params.addProperty("App::PropertyLength", "cross_section_length", "Dimensions", "cross_section_length")
params.cross_section_length = 255.93
params.addProperty("App::PropertyLength", "cross_section_width", "Dimensions", "cross_section_width")
params.cross_section_width = 255.94
params.addProperty("App::PropertyLength", "support_profile_inner_wall_top_y", "Dimensions", "support_profile_inner_wall_top_y")
params.support_profile_inner_wall_top_y = 175.36
params.addProperty("App::PropertyLength", "support_profile_upper_shoulder_x", "Dimensions", "support_profile_upper_shoulder_x")
params.support_profile_upper_shoulder_x = 58.62
params.addProperty("App::PropertyLength", "support_profile_upper_apex_x", "Dimensions", "support_profile_upper_apex_x")
params.support_profile_upper_apex_x = 139.19
params.addProperty("App::PropertyLength", "support_profile_outer_diagonal_y", "Dimensions", "support_profile_outer_diagonal_y")
params.support_profile_outer_diagonal_y = 139.19
params.addProperty("App::PropertyLength", "support_profile_neck_x", "Dimensions", "support_profile_neck_x")
params.support_profile_neck_x = 165.10
params.addProperty("App::PropertyLength", "support_profile_neck_y", "Dimensions", "support_profile_neck_y")
params.support_profile_neck_y = 48.36
params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "number_of_mounting_holes")
params.number_of_mounting_holes = 3
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "mounting_hole_diameter")
params.mounting_hole_diameter = 127.00
params.addProperty("App::PropertyLength", "adjacent_hole_center_spacing", "Dimensions", "adjacent_hole_center_spacing")
params.adjacent_hole_center_spacing = 146.05
params.addProperty("App::PropertyLength", "shaped_opening_depth", "Dimensions", "shaped_opening_depth")
params.shaped_opening_depth = 120.65
params.addProperty("App::PropertyLength", "concave_profile_arc_radius", "Dimensions", "concave_profile_arc_radius")
params.concave_profile_arc_radius = 76.20
params.addProperty("App::PropertyLength", "mounting_lobe_arc_radius", "Dimensions", "mounting_lobe_arc_radius")
params.mounting_lobe_arc_radius = 12.70
params.addProperty("App::PropertyLength", "profile_mounting_hole_diameter", "Dimensions", "profile_mounting_hole_diameter")
params.profile_mounting_hole_diameter = 25.40
params.addProperty("App::PropertyLength", "inner_lobe_center_x", "Dimensions", "inner_lobe_center_x")
params.inner_lobe_center_x = -73.03
params.addProperty("App::PropertyLength", "outer_lobe_center_x", "Dimensions", "outer_lobe_center_x")
params.outer_lobe_center_x = -219.07
params.addProperty("App::PropertyLength", "lobe_center_y", "Dimensions", "lobe_center_y")
params.lobe_center_y = 55.88
params.addProperty("App::PropertyLength", "secondary_concave_center_y", "Dimensions", "secondary_concave_center_y")
params.secondary_concave_center_y = 0.01
params.addProperty("App::PropertyLength", "outer_loop_upper_inner_x", "Dimensions", "outer_loop_upper_inner_x")
params.outer_loop_upper_inner_x = -176.49
params.addProperty("App::PropertyLength", "outer_loop_lower_inner_x", "Dimensions", "outer_loop_lower_inner_x")
params.outer_loop_lower_inner_x = -176.52
params.addProperty("App::PropertyLength", "outer_loop_outer_x", "Dimensions", "outer_loop_outer_x")
params.outer_loop_outer_x = -228.60
params.addProperty("App::PropertyLength", "outer_loop_upper_y", "Dimensions", "outer_loop_upper_y")
params.outer_loop_upper_y = 69.86
params.addProperty("App::PropertyLength", "outer_loop_lower_y", "Dimensions", "outer_loop_lower_y")
params.outer_loop_lower_y = -69.84
params.addProperty("App::PropertyLength", "outer_loop_lobe_join_offset_y", "Dimensions", "outer_loop_lobe_join_offset_y")
params.outer_loop_lobe_join_offset_y = 64.28
params.addProperty("App::PropertyLength", "outer_loop_lobe_inner_offset_y", "Dimensions", "outer_loop_lobe_inner_offset_y")
params.outer_loop_lobe_inner_offset_y = 47.48
params.addProperty("App::PropertyLength", "lens_outer_x", "Dimensions", "lens_outer_x")
params.lens_outer_x = -30.45
params.addProperty("App::PropertyLength", "upper_lens_inner_x", "Dimensions", "upper_lens_inner_x")
params.upper_lens_inner_x = -115.61
params.addProperty("App::PropertyLength", "lower_lens_inner_x", "Dimensions", "lower_lens_inner_x")
params.lower_lens_inner_x = -115.58
params.addProperty("App::PropertyInteger", "number_of_secondary_mounting_holes", "Dimensions", "number_of_secondary_mounting_holes")
params.number_of_secondary_mounting_holes = 2
params.addProperty("App::PropertyLength", "small_mounting_hole_diameter", "Dimensions", "small_mounting_hole_diameter")
params.small_mounting_hole_diameter = 9.52
params.addProperty("App::PropertyLength", "small_hole_depth", "Dimensions", "small_hole_depth")
params.small_hole_depth = 76.00
params.addProperty("App::PropertyLength", "bracket_plate_thickness", "Dimensions", "bracket_plate_thickness")
params.bracket_plate_thickness = 25.40
params.addProperty("App::PropertyLength", "blind_recess_depth", "Dimensions", "blind_recess_depth")
params.blind_recess_depth = 22.00
params.addProperty("App::PropertyInteger", "opposed_flange_count", "Dimensions", "opposed_flange_count")
params.opposed_flange_count = 2
params.addProperty("App::PropertyLength", "flange_recess_root_x", "Dimensions", "flange_recess_root_x")
params.flange_recess_root_x = -152.40
params.addProperty("App::PropertyLength", "flange_recess_root_outer_y", "Dimensions", "flange_recess_root_outer_y")
params.flange_recess_root_outer_y = 53.62
params.addProperty("App::PropertyLength", "flange_recess_root_inner_y", "Dimensions", "flange_recess_root_inner_y")
params.flange_recess_root_inner_y = 48.62
params.addProperty("App::PropertyLength", "flange_recess_upper_inner_x", "Dimensions", "flange_recess_upper_inner_x")
params.flange_recess_upper_inner_x = -38.36
params.addProperty("App::PropertyLength", "flange_recess_upper_edge_y", "Dimensions", "flange_recess_upper_edge_y")
params.flange_recess_upper_edge_y = 162.66
params.addProperty("App::PropertyLength", "flange_recess_mid_x", "Dimensions", "flange_recess_mid_x")
params.flange_recess_mid_x = -63.88
params.addProperty("App::PropertyLength", "flange_recess_apex_x", "Dimensions", "flange_recess_apex_x")
params.flange_recess_apex_x = -139.19
params.addProperty("App::PropertyLength", "flange_recess_apex_y", "Dimensions", "flange_recess_apex_y")
params.flange_recess_apex_y = 237.98
params.addProperty("App::PropertyLength", "flange_recess_outer_x", "Dimensions", "flange_recess_outer_x")
params.flange_recess_outer_x = -237.97
params.addProperty("App::PropertyLength", "flange_recess_outer_y", "Dimensions", "flange_recess_outer_y")
params.flange_recess_outer_y = 139.20

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Main Profile Sketch (XY Plane) ---
# This sketch defines the cross-section of the supporting body.
# Origin is at the center of the quarter-round.
sketch_main = body.newObject("Sketcher::SketchObject", "MainProfileSketch")
sketch_main.Plane = "XY_Plane"
sketch_main.ConstrainAuto = True
sketch_main.Locked = False
sketch_main.AddGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.cross_section_length, 0, 0)), False)
sketch_main.AddGeometry(Part.LineSegment(App.Vector(params.cross_section_length, 0, 0), App.Vector(params.cross_section_length, params.cross_section_width, 0)), False)
sketch_main.AddGeometry(Part.LineSegment(App.Vector(params.cross_section_length, params.cross_section_width, 0), App.Vector(0, params.cross_section_width, 0)), False)
sketch_main.AddGeometry(Part.LineSegment(App.Vector(0, params.cross_section_width, 0), App.Vector(0, 0, 0)), False)
# Add the quarter round at the origin (0,0)
sketch_main.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.corner_arc_radius), False)

# Constraints for Main Profile
# 1. Rectangle constraints (already implicit in lines, but let's ensure closure)
# 2. Quarter circle constraints
# We need to constrain the lines to the circle tangentially or coincidently.
# Let's add points and constraints.
# Point 0: (0,0) - Center of circle
# Point 1: (L, 0)
# Point 2: (L, W)
# Point 3: (0, W)
# Circle Center: (0,0)
# Circle Radius: R
# Line 1-2: x=L
# Line 2-3: y=W
# Line 3-4: x=0
# Line 4-1: y=0
# Circle tangent to Line 1-2 at (R, 0)? No, the description says "inward quarter-round".
# Usually this means the body is the rectangle minus the corner, or the corner is rounded.
# "The transverse outline lies in the positive quadrant about the center of its inward quarter-round"
# This implies the corner at (0,0) is rounded with radius R.
# So the lines should be tangent to the circle at (R, 0) and (0, R).
# Let's add points for tangency.
# Tangent 1: (R, 0)
# Tangent 2: (0, R)
# We will construct the sketch using lines and a circle, then constrain.

# Re-adding geometry for clarity with constraints
sketch_main.clearGeometry()
# Line from (R, 0) to (L, 0)
sketch_main.AddGeometry(Part.LineSegment(App.Vector(params.corner_arc_radius, 0, 0), App.Vector(params.cross_section_length, 0, 0)), False)
# Line from (L, 0) to (L, W)
sketch_main.AddGeometry(Part.LineSegment(App.Vector(params.cross_section_length, 0, 0), App.Vector(params.cross_section_length, params.cross_section_width, 0)), False)
# Line from (L, W) to (0, W)
sketch_main.AddGeometry(Part.LineSegment(App.Vector(params.cross_section_length, params.cross_section_width, 0), App.Vector(0, params.cross_section_width, 0)), False)
# Line from (0, W) to (0, R)
sketch_main.AddGeometry(Part.LineSegment(App.Vector(0, params.cross_section_width, 0), App.Vector(0, params.corner_arc_radius, 0)), False)
# Circle at origin
sketch_main.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.corner_arc_radius), False)

# Constraints
# 1. Coincident: (R,0) on Line 1 and Circle
# 2. Coincident: (0,R) on Line 4 and Circle
# 3. Tangent: Line 1 and Circle at (R,0)
# 4. Tangent: Line 4 and Circle at (0,R)
# 5. Horizontal/Vertical lines
# 6. Closed loop

# Helper to get geometry index
def get_geom_idx(obj, geom_type, count):
    # This is tricky in headless without iterating. 
    # We will rely on the order of addition for constraints if we are careful, 
    # but Sketcher constraints are safer with explicit indices.
    # Let's assume the order: 
    # 0: Line (R,0)->(L,0)
    # 1: Line (L,0)->(L,W)
    # 2: Line (L,W)->(0,W)
    # 3: Line (0,W)->(0,R)
    # 4: Circle
    # Points:
    # P0: (R,0) - End of Line 0, Start of Circle? No, Circle is continuous.
    # We need to define points on the sketch.
    # Let's add points explicitly.
    pass

# Let's rebuild the sketch with points to make constraints robust.
sketch_main.clearGeometry()
# Points
p1 = App.Vector(params.corner_arc_radius, 0, 0)
p2 = App.Vector(params.cross_section_length, 0, 0)
p3 = App.Vector(params.cross_section_length, params.cross_section_width, 0)
p4 = App.Vector(0, params.cross_section_width, 0)
p5 = App.Vector(0, params.corner_arc_radius, 0)
c1 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.corner_arc_radius)

# Lines
l1 = Part.LineSegment(p1, p2)
l2 = Part.LineSegment(p2, p3)
l3 = Part.LineSegment(p3, p4)
l4 = Part.LineSegment(p4, p5)

sketch_main.AddGeometry(l1, False)
sketch_main.AddGeometry(l2, False)
sketch_main.AddGeometry(l3, False)
sketch_main.AddGeometry(l4, False)
sketch_main.AddGeometry(c1, False)

# Add Points
sketch_main.AddGeometry(Part.Point(p1), False)
sketch_main.AddGeometry(Part.Point(p2), False)
sketch_main.AddGeometry(Part.Point(p3), False)
sketch_main.AddGeometry(Part.Point(p4), False)
sketch_main.AddGeometry(Part.Point(p5), False)

# Constraints
# 1. Coincident P1 on L1 and C1
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 4, 2)) # L1(0,2) -> P1(4,2) on C1(4,2)? No.
# Indices:
# 0: L1, 1: L2, 2: L3, 3: L4, 4: C1
# 5: P1, 6: P2, 7: P3, 8: P4, 9: P5
# L1 is 0. P1 is 5. C1 is 4.
# Coincident P1 on L1 and C1:
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 5, 2)) # L1(0,2) -> P1(5,2)
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 4, 2, 5, 2)) # C1(4,2) -> P1(5,2)

# Coincident P5 on L4 and C1
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 9, 2)) # L4(3,2) -> P5(9,2)
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 4, 2, 9, 2)) # C1(4,2) -> P5(9,2)

# Tangent L1 and C1 at P1
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 0, 2, 4, 2)) # L1(0,2) tangent to C1(4,2)

# Tangent L4 and C1 at P5
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 3, 2, 4, 2)) # L4(3,2) tangent to C1(4,2)

# Horizontal/Vertical
sketch_main.addConstraint(Sketcher.Constraint("X", 0, 2, 0, 2)) # L1 horizontal
sketch_main.addConstraint(Sketcher.Constraint("Y", 3, 2, 0, 2)) # L4 vertical
sketch_main.addConstraint(S
