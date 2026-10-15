import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("SteeringKnuckle")

# --- Parameters ---
# Define parameters as App::PropertyLength or similar in a VarSet or directly on the Body
# For simplicity and robustness in 1.1, we will use App::PropertyLength on the Body directly 
# or create a VarSet. Let's use a VarSet for clean separation.

params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "body_depth", "Dimensions", "Thickness of the part")
params.body_depth = 15.0

params.addProperty("App::PropertyLength", "spindle_bore_diameter", "Dimensions", "Bore in spindle")
params.spindle_bore_diameter = 15.0

params.addProperty("App::PropertyLength", "spindle_boss_diameter", "Dimensions", "Diameter of spindle boss")
params.spindle_boss_diameter = 24.0

params.addProperty("App::PropertyLength", "spindle_center_offset_x", "Dimensions", "X offset of spindle boss center")
params.spindle_center_offset_x = -100.0

params.addProperty("App::PropertyLength", "hub_outer_arc_radius", "Dimensions", "Radius of outer hub arc")
params.hub_outer_arc_radius = 26.9

params.addProperty("App::PropertyLength", "hub_inner_diameter", "Dimensions", "Diameter of inner hub ring")
params.hub_inner_diameter = 41.7

params.addProperty("App::PropertyLength", "bracket_arm_outer_fillet_radius", "Dimensions", "Fillet radius outer arm")
params.bracket_arm_outer_fillet_radius = 26.9

params.addProperty("App::PropertyLength", "bracket_arm_inner_fillet_radius", "Dimensions", "Fillet radius inner arm")
params.bracket_arm_inner_fillet_radius = 24.0

params.addProperty("App::PropertyLength", "bracket_arm_outer_width", "Dimensions", "Width of the arm section")
params.bracket_arm_outer_width = 18.0

params.addProperty("App::PropertyLength", "bracket_arm_slot_end_arc_radius", "Dimensions", "Radius of slot end arcs")
params.bracket_arm_slot_end_arc_radius = 5.0

params.addProperty("App::PropertyLength", "bracket_arm_slot_width", "Dimensions", "Width of the slot")
params.bracket_arm_slot_width = 10.0

params.addProperty("App::PropertyLength", "bracket_arm_slot_left_center_x", "Dimensions", "X center of left slot")
params.bracket_arm_slot_left_center_x = -77.8

params.addProperty("App::PropertyLength", "bracket_arm_slot_right_center_x", "Dimensions", "X center of right slot")
params.bracket_arm_slot_right_center_x = -41.8

params.addProperty("App::PropertyLength", "bracket_tab_width", "Dimensions", "Width of bracket tabs")
params.bracket_tab_width = 16.0

params.addProperty("App::PropertyLength", "bracket_tab_outer_extent_y", "Dimensions", "Outer Y extent of tabs")
params.bracket_tab_outer_extent_y = 47.0

params.addProperty("App::PropertyLength", "bracket_tab_inner_extent_y", "Dimensions", "Inner Y extent of tabs")
params.bracket_tab_inner_extent_y = 25.6828737

params.addProperty("App::PropertyLength", "arm_inner_fillet_center_left_x", "Dimensions", "X center of inner fillet left")
params.arm_inner_fillet_center_left_x = -85.6125054

params.addProperty("App::PropertyLength", "arm_inner_fillet_center_left_y", "Dimensions", "Y center of inner fillet left")
params.arm_inner_fillet_center_left_y = 33.0

params.addProperty("App::PropertyLength", "arm_outer_fillet_center_right_x", "Dimensions", "X center of outer fillet right")
params.arm_outer_fillet_center_right_x = -40.0703132

params.addProperty("App::PropertyLength", "arm_outer_fillet_center_right_y", "Dimensions", "Y center of outer fillet right")
params.arm_outer_fillet_center_right_y = 35.9

params.addProperty("App::PropertyLength", "center_bore_diameter", "Dimensions", "Diameter of cross bore")
params.center_bore_diameter = 10.0

params.addProperty("App::PropertyLength", "center_bore_y_offset", "Dimensions", "Y offset of cross bore center")
params.center_bore_y_offset = 7.5

# Angles (stored as floats, will be used in expressions or calculated)
params.addProperty("App::PropertyFloat", "hub_outer_arc_lower_start_angle", "Angles", "Start angle lower outer hub")
params.hub_outer_arc_lower_start_angle = -138.1420401

params.addProperty("App::PropertyFloat", "hub_outer_arc_lower_end_angle", "Angles", "End angle lower outer hub")
params.hub_outer_arc_lower_end_angle = -107.301374

params.addProperty("App::PropertyFloat", "hub_outer_arc_upper_start_angle", "Angles", "Start angle upper outer hub")
params.hub_outer_arc_upper_start_angle = 107.301374

params.addProperty("App::PropertyFloat", "hub_outer_arc_upper_end_angle", "Angles", "End angle upper outer hub")
params.hub_outer_arc_upper_end_angle = 138.1420401

params.addProperty("App::PropertyFloat", "hub_outer_arc_right_start_angle", "Angles", "Start angle right outer hub")
params.hub_outer_arc_right_start_angle = -72.698626

params.addProperty("App::PropertyFloat", "hub_outer_arc_right_end_angle", "Angles", "End angle right outer hub")
params.hub_outer_arc_right_end_angle = 72.698626

params.addProperty("App::PropertyFloat", "arm_outer_fillet_lower_start_angle", "Angles", "Start angle lower outer fillet")
params.arm_outer_fillet_lower_start_angle = 41.8579599

params.addProperty("App::PropertyFloat", "arm_outer_fillet_upper_end_angle", "Angles", "End angle upper outer fillet")
params.arm_outer_fillet_upper_end_angle = -41.8579599

params.addProperty("App::PropertyFloat", "arm_inner_fillet_lower_end_angle", "Angles", "End angle lower inner fillet")
params.arm_inner_fillet_lower_end_angle = 113.5564643

params.addProperty("App::PropertyFloat", "arm_inner_fillet_upper_start_angle", "Angles", "Start angle upper inner fillet")
params.arm_inner_fillet_upper_start_angle = -113.5564643

params.addProperty("App::PropertyFloat", "spindle_boss_arc_start_angle", "Angles", "Start angle spindle boss arc")
params.spindle_boss_arc_start_angle = 66.4435357

params.addProperty("App::PropertyFloat", "spindle_boss_arc_end_angle", "Angles", "End angle spindle boss arc")
params.spindle_boss_arc_end_angle = -66.4435357

params.addProperty("App::PropertyFloat", "hub_inner_ring_split_angle_1", "Angles", "Split angle 1 inner ring")
params.hub_inner_ring_split_angle_1 = 67.4373731

params.addProperty("App::PropertyFloat", "hub_inner_ring_split_angle_2", "Angles", "Split angle 2 inner ring")
params.hub_inner_ring_split_angle_2 = 112.5626269

params.addProperty("App::PropertyFloat", "hub_inner_ring_split_angle_3", "Angles", "Split angle 3 inner ring")
params.hub_inner_ring_split_angle_3 = 247.4373731

params.addProperty("App::PropertyFloat", "hub_inner_ring_split_angle_4", "Angles", "Split angle 4 inner ring")
params.hub_inner_ring_split_angle_4 = 292.5626269

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Main Profile Sketch ---
# We need to construct the complex 2D profile on the XY plane.
# The profile consists of:
# 1. Hub outer arcs (left and right)
# 2. Arm outer arcs (top and bottom)
# 3. Spindle boss outer arc
# 4. Inner hub ring segments
# 5. Arm inner fillets
# 6. Bracket tabs
# 7. Slot

sketch = body.newObject("Sketcher::SketchObject", "MainProfile")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.LockConstraints = False
sketch.MapMode = "FlatFace"
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Helper to add geometry
def add_line(p1, p2, visible=True):
    sketch.addGeometry(Part.LineSegment(p1, p2), visible)

def add_circle(center, radius, visible=True):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), visible)

def add_arc(center, radius, start_angle, end_angle, visible=True):
    # FreeCAD Sketcher arcs are defined by center, radius, start angle, end angle
    # Angles are in degrees relative to +X axis, counter-clockwise.
    sketch.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), visible)

# --- Constructing the Profile ---

# 1. Hub Outer Arcs
# Right side: -72.698626 to 72.698626
add_arc(App.Vector(0, 0, 0), params.hub_outer_arc_radius, params.hub_outer_arc_right_start_angle, params.hub_outer_arc_right_end_angle)
# Left side: -138.1420401 to -107.301374 (This is the lower part of the left side)
# Wait, the description says "counter-clockwise from global +X".
# Left side usually goes from ~180-138 to ~180+107.
# Let's trace the perimeter CCW.
# Start at bottom right of right arc? No, let's build segments.
# Right Arc: -72.7 to 72.7
# Top connection to Arm Outer Top?
# Arm Outer Top: 41.86 to -41.86 (This range crosses 0? No, 41 to -41 is CCW if we go 41 -> 0 -> -41? No, that's CW.
# Standard math: 41 to -41 is CW. CCW would be 41 to 360-41 = 318.
# Let's re-read: "arm_outer_fillet_lower_start_angle = 41.8579599", "arm_outer_fillet_upper_end_angle = -41.8579599".
# If we go CCW from 41.8 to -41.8, we pass through 90, 180, 270. That covers the top and left.
# But the arm is on the left (negative X).
# Let's assume the angles define the extent of the arc.
# Arm Outer Top Arc: From 41.86 deg to -41.86 deg? That's a huge span (318 deg).
# Maybe it means the arc is between these angles?
# Let's look at the geometry description: "arm joins the hub and spindle boss... tangent inner and outer blends".
# The arm is on the left.
# Let's assume the arc is centered at some point.
# Actually, the prompt says "measured counter-clockwise from global +X".
# If the arc is on the top of the arm, it should be around 90 deg.
# If the arc is on the bottom, around 270 (-90).
# Let's assume the provided angles define the start and end of the arc segment.
# If start=41.8 and end=-41.8, and we go CCW, we cover 41.8 -> 90 -> 180 -> 270 -> 318 (-41.8).
# This seems to cover the top and left side.
# However, the arm is a specific feature.
# Let's try to interpret "arm_outer_fillet_lower_start_angle" and "arm_outer_fillet_upper_end_angle".
# Maybe "lower" means the bottom of the arm (negative Y) and "upper" means top (positive Y)?
# If lower_start = 41.8 (positive Y, right side) and upper_end = -41.8 (positive Y, right side).
# This is confusing. Let's assume the angles are relative to the arm center or something?
# No, "global +X".
# Let's assume the arc is the top of the arm. Center is likely on the X axis.
# If the arc is from 41.8 to -41.8, and it's the top, it must be going CW? Or the angles are swapped?
# Let's assume the arc is from -41.8 to 41.8 (CCW) for the top? That's small.
# Let's assume the arc is from 41.8 to 360-41.8 (CCW) for the bottom?
# Let's try to construct the shape logically based on typical steering knuckles.
# Hub is center. Arm goes left. Spindle is further left.
# Outer profile:
# Right side: Hub arc (-72 to 72).
# Top: Connects to Arm Top.
# Arm Top: Arc.
# Left: Spindle Boss Arc.
# Bottom: Connects to Arm Bottom.
# Arm Bottom: Arc.
# Inner profile:
# Hub inner ring segments.
# Arm inner fillets.
# Bracket tabs.
# Slot.

# Let's define the points and arcs more carefully.
# We will create a closed loop.

# 1. Right Hub Arc
add_arc(App.Vector(0, 0, 0), params.hub_outer_arc_radius, params.hub_outer_arc_right_start_angle, params.hub_outer_arc_right_end_angle)

# 2. Top Connection to Arm
# The arm outer top arc starts at 41.86 deg?
# If the right hub ends at 72.7 deg, and the arm starts at 41.86 deg, they don't touch.
# Maybe the arm arc is centered elsewhere?
# "bracket_arm_outer_width = 18.0".
# "bracket_arm_outer_fillet_radius = 26.9".
# This radius is the same as the hub outer radius.
# This suggests the arm outer arc is tangent to the hub outer arc?
# If they are tangent, the centers must be collinear with the tangent point.
# If the hub is at (0,0) and arm is at (-100, 0), the tangent point on the right hub is at 0 deg?
# But the angles are +/- 72.
# This implies the arm is not on the X-axis? Or the "arm axis" is the X-axis, but the connection is complex.
# Wait, "spindle_center_offset_x = -100.0". "arm joins the hub and spindle boss".
# Maybe the arm is not a simple rectangle.
# Let's assume the provided angles are correct and we just need to place them.
# Let's assume the arm outer top arc is centered at the spindle center? No, that's the boss.
# Let's assume the arm outer top arc is centered at the hub center? No, that's the hub.
# Maybe the arm outer arc is centered at a point on the X-axis between hub and spindle?
# Let's assume the arm outer arc is centered at the spindle center?
# If center is (-100, 0), radius 26.9.
# Angles 41.8 to -41.8.
# If we go CCW from 41.8 to -41.8, we cover the top and left.
# If we go CW from 41.8 to -41.8, we cover the right.
# The arm is on the left. So the arc should be on the left side of the arm center?
# If the arm center is (-100, 0), the left side is angles 180 +/- something.
# This is getting too speculative.
# Let's try a different interpretation: The angles are relative to the arm's local coordinate system?
# No, "global +X".
# Let's assume the arm outer arc is centered at the hub center?
# If center is (0,0), radius 26.9.
# Angles 41.8 to -41.8.
# If we go CCW, we cover 41.8 -> 90 -> 180 -> 270 -> 318.
# This covers the top, left, and bottom.
# But the hub already covers -72 to 72.
# So there is a gap between 72 and 41.8? No, 72 > 41.8.
# So the hub covers 41.8 to 72.
# The arm arc covers 41.8 to -41.8 (CCW).
# This would overlap.
# Maybe the arm arc is centered at the spindle center (-100, 0)?
# If center is (-100, 0), radius 26.9.
# Angles 41.8 to -41.8.
