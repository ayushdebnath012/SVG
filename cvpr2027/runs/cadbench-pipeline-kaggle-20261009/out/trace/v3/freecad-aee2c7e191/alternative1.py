from pathlib import Path
import FreeCAD as App
import Part
from Part import Shape, Plane, Vector, Rotation
import Sketcher
from Sketcher import Constraint

def create_param_group(body, name, parent="Parameters"):
    return body.newObject("App::VarSet", name, parent)

def create_sketch(body, name, plane_obj):
    s = body.newObject("Sketcher::SketchObject", name)
    s.Placement = App.Placement(plane_obj.ToPnt(), plane_obj.Rot)
    s.AttachmentSupport = (plane_obj, [""])
    s.MapMode = "FlatFace"
    s.Constrain = False
    return s

def add_constrained_line(sketch, p1, p2, visible=True):
    l = Part.LineSegment(p1, p2)
    sketch.addGeometry(l, visible)

def add_constrained_circle(sketch, center, axis, radius, visible=True):
    c = Part.Circle(center, axis, radius)
    sketch.addGeometry(c, visible)

def add_constraint(sketch, c_type, ref1, ref2, val=0.0):
    sketch.addConstraint(Sketcher.Constraint(c_type, ref1, ref2, val))

# Initialize Document
doc = App.newDocument("ClampModel")
App.setLastInputPosition()

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Define Parameters Group
params = create_param_group(body, "Dimensions", "Parameters")
params.addProperty("App::PropertyLength", "clamp_body_thickness", "Dimensions", "Body thickness")
params.clamp_body_thickness = 12.0
params.addProperty("App::PropertyLength", "side_profile_overall_height", "Dimensions", "Side height")
params.side_profile_overall_height = 11.1
params.addProperty("App::PropertyLength", "top_plate_outer_width", "Dimensions", "Top width")
params.top_plate_outer_width = 31.0
params.addProperty("App::PropertyLength", "top_corner_radius", "Dimensions", "Corner radius")
params.top_corner_radius = 2.22
params.addProperty("App::PropertyLength", "routing_channel_opening_diameter", "Dimensions", "Channel dia")
params.routing_channel_opening_diameter = 3.2
params.addProperty("App::PropertyLength", "routing_channel_center_spacing", "Dimensions", "Channel spacing")
params.routing_channel_center_spacing = 18.0
params.addProperty("App::PropertyLength", "routing_channel_center_vertical_offset", "Dimensions", "Channel V offset")
params.routing_channel_center_vertical_offset = -1.95
params.addProperty("App::PropertyLength", "base_flange_thickness", "Dimensions", "Flange thick")
params.base_flange_thickness = 2.14
params.addProperty("App::PropertyLength", "base_inner_surface_height_above_bottom", "Dimensions", "Inner base height")
params.base_inner_surface_height_above_bottom = 2.0
params.addProperty("App::PropertyLength", "right_mounting_tab_horizontal_extension", "Dimensions", "Tab ext")
params.right_mounting_tab_horizontal_extension = 2.0
params.addProperty("App::PropertyLength", "right_mounting_tab_height", "Dimensions", "Tab height")
params.right_mounting_tab_height = 4.0
params.addProperty("App::PropertyLength", "left_base_transition_radius", "Dimensions", "Left base rad")
params.left_base_transition_radius = 0.89
params.addProperty("App::PropertyLength", "left_base_transition_sweep_angle", "Dimensions", "Left base sweep")
params.left_base_transition_sweep_angle = 9.2068962
params.addProperty("App::PropertyLength", "right_mounting_tab_inner_wall_offset", "Dimensions", "Tab inner offset")
params.right_mounting_tab_inner_wall_offset = 0.14
params.addProperty("App::PropertyLength", "rear_routing_bore_diameter", "Dimensions", "Rear bore dia")
params.rear_routing_bore_diameter = 6.8
params.addProperty("App::PropertyLength", "rear_routing_bore_blind_depth", "Dimensions", "Rear bore depth")
params.rear_routing_bore_blind_depth = 9.1
params.addProperty("App::PropertyLength", "front_routing_bore_diameter", "Dimensions", "Front bore dia")
params.front_routing_bore_diameter = 7.0
params.addProperty("App::PropertyLength", "side_cutout_depth", "Dimensions", "Cutout depth")
params.side_cutout_depth = 4.22
params.addProperty("App::PropertyLength", "side_cutout_start_offset_from_midplane", "Dimensions", "Cutout offset")
params.side_cutout_start_offset_from_midplane = 3.55
params.addProperty("App::PropertyLength", "side_cutout_pair_outer_span", "Dimensions", "Cutout span")
params.side_cutout_pair_outer_span = 8.02
params.addProperty("App::PropertyLength", "side_cutout_end_width", "Dimensions", "Cutout end width")
params.side_cutout_end_width = 2.02
params.addProperty("App::PropertyLength", "side_cutout_end_height", "Dimensions", "Cutout end height")
params.side_cutout_end_height = 1.9
params.addProperty("App::PropertyLength", "side_cutout_row_center_spacing", "Dimensions", "Cutout row spacing")
params.side_cutout_row_center_spacing = 16.06
params.addProperty("App::PropertyLength", "side_cutout_transition_width", "Dimensions", "Cutout trans width")
params.side_cutout_transition_width = 0.26
params.addProperty("App::PropertyLength", "side_cutout_boundary_radius", "Dimensions", "Cutout boundary rad")
params.side_cutout_boundary_radius = 7.36
params.addProperty("App::PropertyAngle", "side_cutout_inner_contact_angle", "Dimensions", "Inner contact angle")
params.side_cutout_inner_contact_angle = 74.2714907
params.addProperty("App::PropertyAngle", "side_cutout_outer_contact_angle", "Dimensions", "Outer contact angle")
params.side_cutout_outer_contact_angle = 59.3285489
params.addProperty("App::PropertyLength", "triangular_access_slot_max_width", "Dimensions", "Tri slot max")
params.triangular_access_slot_max_width = 0.47
params.addProperty("App::PropertyLength", "access_slot_divider_width", "Dimensions", "Slot divider")
params.access_slot_divider_width = 0.46
params.addProperty("App::PropertyLength", "hourglass_access_slot_max_width", "Dimensions", "Hourglass max")
params.hourglass_access_slot_max_width = 0.93
params.addProperty("App::PropertyLength", "hourglass_access_slot_waist_inset", "Dimensions", "Hourglass waist")
params.hourglass_access_slot_waist_inset = 0.46
params.addProperty("App::PropertyAngle", "profile_positive_transverse_angle", "Dimensions", "Pos transv angle")
params.profile_positive_transverse_angle = 0.0
params.addProperty("App::PropertyAngle", "profile_positive_vertical_angle", "Dimensions", "Pos vert angle")
params.profile_positive_vertical_angle = 90.0
params.addProperty("App::PropertyAngle", "profile_negative_transverse_angle", "Dimensions", "Neg transv angle")
params.profile_negative_transverse_angle = 180.0
params.addProperty("App::PropertyAngle", "profile_negative_vertical_angle", "Dimensions", "Neg vert angle")
params.profile_negative_vertical_angle = -90.0
params.addProperty("App::PropertyLength", "triangular_access_slot_tip_station", "Dimensions", "Tri tip station")
params.triangular_access_slot_tip_station = 16.11

# Create Reference Planes
# Main profile sketch on XY plane
xy_plane = doc.addObject("Part::PlanarObject", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))

# Base flange sketch plane offset Z (for the flange cut)
z_offset = params.clamp_body_thickness
xz_plane = doc.addObject("Part::PlanarObject", "XZ_Plane")
xz_plane.Placement = App.Placement(App.Vector(0, 0, z_offset))

# Right side plane for mounting tab and access slots
right_side_x = params.top_plate_outer_width / 2 + params.right_mounting_tab_horizontal_extension
yz_plane = doc.addObject("Part::PlanarObject", "YZ_Plane")
yz_plane.Placement = App.Placement(App.Vector(right_side_x, 0, 0))

# Create Main Profile Sketch (Side View)
# This sketch defines the cross-section of the clamp body.
main_sketch = create_sketch(body, "MainProfileSketch", xy_plane)

# Coordinates for the main profile sketch (Y is vertical, X is horizontal)
# Origin at bottom-left corner of the bounding box of the side profile
# However, the description says "The base flange starts flush with the left outer wall".
# Let's define the profile relative to the bottom-left of the main body thickness area.
# Thickness is in Z (out of this sketch). Width is X, Height is Y.

# Dimensions:
# Overall Height: params.side_profile_overall_height
# Top Plate Width: params.top_plate_outer_width
# Corner Radius: params.top_corner_radius

# Calculate key X positions:
# Left wall X = 0
# Right outer wall X = params.top_plate_outer_width
# Right inner wall (tab) X = params.top_plate_outer_width + params.right_mounting_tab_horizontal_extension
# Tab Inner Wall X = Right Outer X + params.right_mounting_tab_inner_wall_offset

left_x = 0.0
right_outer_x = params.top_plate_outer_width
right_inner_x = right_outer_x + params.right_mounting_tab_horizontal_extension
tab_inner_x = right_outer_x + params.right_mounting_tab_inner_wall_offset

bottom_y = 0.0
top_y = params.side_profile_overall_height

# Corner logic:
# "Straight upper edge joins both walls through tangent quarter-round corners of top_corner_radius"
# This implies the top edge is horizontal, and the sides have quarter circles connecting the top edge to the vertical sides.
# Wait, "tangent quarter-round corners" usually means the corner IS a quarter circle.
# If the top edge is straight, and it joins the walls via tangent corners, it implies the vertical walls are NOT the full height, or the corners are fillets.
# Given "straight upper edge joins both walls through tangent quarter-round corners", it sounds like:
# Top edge is horizontal. Vertical walls go up from bottom. At the top, instead of a sharp 90, there is a quarter circle tangent to the top edge and the vertical wall?
# No, a quarter circle tangent to a horizontal line and a vertical line is a standard corner fillet.
# BUT the text says "joins both walls".
# Let's assume standard interpretation: The top of the profile is a rectangle with rounded corners (radius = top_corner_radius).
# So the vertical walls go up to (top_y - top_corner_radius), then a horizontal top edge of length (right_outer_x - left_x - 2*radius)?
# Or does it mean the vertical walls go all the way to top_y, and the "corner" is a fillet of radius top_corner_radius connecting them?
# "Straight upper edge joins both walls through tangent quarter-round corners".
# This phrasing suggests: Top Edge (Straight) -> Tangent Quarter Round -> Wall.
# This is geometrically impossible if the wall is vertical and the top edge is horizontal and they meet at the corner point unless it's a fillet.
# Let's assume the shape is: Vertical wall from (0,0) to (0, top_y - r). Horizontal top from (r, top_y-r) to (W-r, top_y-r). Vertical wall from (W-r, top_y-r) to (W, top_y).
# Actually, simpler: The profile is bounded by x=0, x=W, y=0, y=H. The corners (0,H), (W,H) are replaced by arcs of radius R tangent to the lines x=0, y=H (and x=W, y=H).
# This creates a shape where the top edge is horizontal, length W - 2R. The side walls are vertical, length H - R.
# Let's proceed with this assumption.

r = params.top_corner_radius
h_top_start = top_y - r
w_top_start = right_outer_x - r
h_side_end = h_top_start # Height where top edge starts

# Points for Main Sketch
p0 = App.Vector(left_x, bottom_y, 0) # Bottom-Left
p1 = App.Vector(left_x, h_side_end, 0) # Top-Left Start of Top Edge
p2 = App.Vector(w_top_start, h_side_end, 0) # Top-Right End of Top Edge
p3 = App.Vector(right_outer_x, top_y, 0) # Top-Right
p4 = App.Vector(right_inner_x, top_y, 0) # Tab Top-Right
p5 = App.Vector(right_inner_x, bottom_y, 0) # Tab Bottom-Right
p6 = App.Vector(left_x, bottom_y, 0) # Back to Bottom-Left (closed)

# Add Geometry
add_constrained_line(main_sketch, p0, p1)
add_constrained_line(main_sketch, p1, p2)
add_constrained_line(main_sketch, p2, p3)
add_constrained_line(main_sketch, p3, p4)
add_constrained_line(main_sketch, p4, p5)
add_constrained_line(main_sketch, p5, p0)

# Add constraints to define geometry fully relative to the sketch origin
# Lengths
add_constraint(main_sketch, "FixedSize", 0, 1, params.clamp_body_thickness) # Z thickness? No, sketch is 2D.
# In PartDesign, we often constrain lengths.
# X-lengths
add_constraint(main_sketch, "Length", 0, 3, params.top_plate_outer_width) # Left to Right Outer
add_constraint(main_sketch, "Length", 2, 4, params.right_mounting_tab_horizontal_extension) # Tab width
add_constraint(main_sketch, "Length", 4, 5, params.right_mounting_tab_inner_wall_offset) # Tab inner offset (Wait, 5 is at bottom, 4 at top. This constrains vertical distance if x is same. They are same x.)
# Actually, p4.x == p5.x. So length 4-5 is 0 in Y? No, p4.y=H, p5.y=0. So this constrains height of tab?
# The prompt says "right_mounting_tab_inner_wall_offset" is displacement rightward from outer wall.
# So p5.x should be p4.x? No, p5 is bottom right of tab. p4 is top right of tab.
# The tab extends from Right Outer Wall.
# So Left Wall (p0.x) = 0.
# Right Outer Wall (p3.x) = W.
# Tab Right Wall (p4.x) = W + Ext.
# Tab Inner Wall (p5.x) = W + Ext.
# The offset "right_mounting_tab_inner_wall_offset" is the distance between Tab Inner Wall and Tab Outer Wall?
# "Its inner wall is displaced rightward from that outer wall by right_mounting_tab_inner_wall_offset."
# This implies Tab Inner Wall is NOT at the outer wall edge? That would make the tab U-shaped or have a wall thickness?
# "No corresponding tab exists on the left."
# Maybe the tab has a thickness?
# "extends horizontally beyond the right outer wall by right_mounting_tab_horizontal_extension" -> This defines the outer boundary.
# "inner wall is displaced rightward from that outer wall by right_mounting_tab_inner_wall_offset" -> This defines the inner boundary.
# So the tab is a plate with thickness = offset?
# But the main profile sketch defines the cross section.
# If the tab is part of the main profile, the main profile must include the tab shape.
# If the tab has thickness, the "inner wall" is the boundary facing the main body.
# So p4 (top right outer) -> p6? No.
# Let's trace the perimeter of the main body + tab.
# 0 (BL) -> 1 (TL start) -> 2 (TR start) -> 3 (Top Right Outer) -> 4 (Top Right Tab Outer) -> 5 (Bottom Right Tab Outer) -> 6 (Bottom Right Tab Inner) -> 7 (Bottom Left?) -> ...
# This is getting complicated.
# Re-read: "The right mounting tab extends horizontally beyond the right outer wall... Its inner wall is displaced rightward from that outer wall by right_mounting_tab_inner_wall_offset."
# This implies the tab is a protrusion.
# The "main body" ends at Right Outer Wall. The tab starts there.
# The tab has an "inner wall". This is the face of the tab that joins the main body? No, "displaced rightward from that outer wall".
# If the outer wall is at X=W, and the inner wall is displaced rightward, it is at X = W + offset.
# So the tab is between X=W and X=W+Ext? And the "inner wall" is the one at X=W?
# "displaced rightward from that outer wall by offset".
# If Outer Wall is at X=W. Inner Wall is at X = W + offset.
# Then the material of the tab is between X=W and X=W+offset? No, that would be a thin slice attached to the main body.
# But the tab extends by "horizontal_extension".
# Maybe "outer wall" refers to the left wall of the tab? And "inner wall" refers to the right wall?
# No, "extends beyond... by extension". So Outer Wall is the far edge.
# "Inner wall is displaced rightward from that outer wall".
# This is confusing. Let's assume standard tab geometry:
# Main body ends at X=W.
# Tab extends from X=W to X=W+Ext.
# The tab has a thickness? Or is it a flat plate?
# "inner wall" usually faces the interior. If the tab is on the right, the inner wall is the left face of the tab (at X=W).
# But the text says "displaced rightward from that outer wall".
# If Outer Wall = X=W+Ext. Inner Wall = X=W.
