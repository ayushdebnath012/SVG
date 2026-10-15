import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("ConnectorHousing")

# --- Parameters ---
# Define a VarSet to hold all parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "rear_rounded_square_section_thickness", "Dimensions", "Rear thickness")
params.addProperty("App::PropertyLength", "rounded_square_flat_edge_length", "Dimensions", "Side length")
params.addProperty("App::PropertyLength", "rounded_square_corner_arc_radius", "Dimensions", "Corner radius")
params.addProperty("App::PropertyLength", "rounded_square_corner_center_offset", "Dimensions", "Corner offset")
params.addProperty("App::PropertyLength", "rounded_square_lower_flat_offset_from_center", "Dimensions", "Lower offset")
params.addProperty("App::PropertyInteger", "rounded_square_side_count", "Dimensions", "Number of sides")
params.addProperty("App::PropertyLength", "circular_port_outer_diameter", "Dimensions", "Port diameter")
params.addProperty("App::PropertyLength", "housing_overall_axial_length", "Dimensions", "Total length")
params.addProperty("App::PropertyLength", "circular_end_opening_width", "Dimensions", "Opening W")
params.addProperty("App::PropertyLength", "circular_end_opening_height", "Dimensions", "Opening H")
params.addProperty("App::PropertyLength", "lower_side_opening_width", "Dimensions", "Lower Side W")
params.addProperty("App::PropertyLength", "lower_side_opening_height", "Dimensions", "Lower Side H")
params.addProperty("App::PropertyLength", "lower_side_opening_center_x_offset", "Dimensions", "Lower Side X")
params.addProperty("App::PropertyLength", "lower_side_opening_center_y_offset", "Dimensions", "Lower Side Y")
params.addProperty("App::PropertyLength", "tapered_side_opening_near_edge_height", "Dimensions", "Taper Near")
params.addProperty("App::PropertyLength", "tapered_side_opening_far_edge_height", "Dimensions", "Taper Far")
params.addProperty("App::PropertyLength", "tapered_side_opening_axial_length", "Dimensions", "Taper Length")
params.addProperty("App::PropertyLength", "side_fastener_row_axial_position", "Dimensions", "Fastener Z")
params.addProperty("App::PropertyLength", "side_fastener_center_spacing", "Dimensions", "Fastener Spacing")
params.addProperty("App::PropertyLength", "side_fastener_through_hole_diameter", "Dimensions", "Fastener Hole")
params.addProperty("App::PropertyLength", "side_fastener_counterbore_diameter", "Dimensions", "Fastener CB")
params.addProperty("App::PropertyLength", "side_fastener_counterbore_depth", "Dimensions", "Fastener CB Depth")
params.addProperty("App::PropertyInteger", "corner_fastener_count", "Dimensions", "Corner Fasteners")
params.addProperty("App::PropertyLength", "corner_through_hole_diameter", "Dimensions", "Corner Hole")
params.addProperty("App::PropertyLength", "corner_through_hole_depth", "Dimensions", "Corner Hole Depth")
params.addProperty("App::PropertyLength", "corner_counterbore_diameter", "Dimensions", "Corner CB")
params.addProperty("App::PropertyLength", "corner_counterbore_depth", "Dimensions", "Corner CB Depth")

# Set values
params.rear_rounded_square_section_thickness = 10.0
params.rounded_square_flat_edge_length = 52.4592704
params.rounded_square_corner_arc_radius = 7.5
params.rounded_square_corner_center_offset = 31.8198052
params.rounded_square_lower_flat_offset_from_center = -36.8198052
params.rounded_square_side_count = 4
params.circular_port_outer_diameter = 60.0
params.housing_overall_axial_length = 52.52
params.circular_end_opening_width = 24.5
params.circular_end_opening_height = 31.5
params.lower_side_opening_width = 24.05
params.lower_side_opening_height = 30.0
params.lower_side_opening_center_x_offset = -0.225
params.lower_side_opening_center_y_offset = -28.0
params.tapered_side_opening_near_edge_height = 30.0
params.tapered_side_opening_far_edge_height = 25.0
params.tapered_side_opening_axial_length = 15.0
params.side_fastener_row_axial_position = 34.52
params.side_fastener_center_spacing = 24.0
params.side_fastener_through_hole_diameter = 3.7
params.side_fastener_counterbore_diameter = 7.0
params.side_fastener_counterbore_depth = 21.0
params.corner_fastener_count = 4
params.corner_through_hole_diameter = 5.0
params.corner_through_hole_depth = 22.6
params.corner_counterbore_diameter = 8.5
params.corner_counterbore_depth = 12.52

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Base Sketch (Rounded Square Profile) ---
# We need to construct the rounded square profile in the XY plane.
# The profile is centered at (0,0).
# It has N sides. Each side has a flat edge and a corner arc.
# The corner arcs are centered at distance 'rounded_square_corner_center_offset' from origin.
# The flat edges are tangent to these arcs.

sketch_base = body.newObject("Sketcher::SketchObject", "BaseProfile")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.ConstrainToCurrentPlane = True
sketch_base.MapMode = "FlatFace"
sketch_base.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Calculate geometry for the rounded square
n_sides = params.rounded_square_side_count
corner_offset = params.rounded_square_corner_center_offset
flat_len = params.rounded_square_flat_edge_length
corner_radius = params.rounded_square_corner_arc_radius
lower_offset = params.rounded_square_lower_flat_offset_from_center

# The problem description implies a specific orientation where one flat edge is offset vertically.
# Let's assume the standard orientation where the "lower" flat edge is at the bottom.
# The corner centers are distributed around the origin.
# For a 4-sided shape (square), corners are at 45, 135, 225, 315 degrees.
# The "lower" flat edge corresponds to the side between the bottom-left and bottom-right corners.
# The offset of this edge from the center is given.

# Let's define the corner centers explicitly based on the description "equal-magnitude corner-center offsets".
# And "rounded_square_lower_flat_offset_from_center" defines the position of the lower edge.
# If the shape is symmetric, the lower edge is horizontal.
# The distance from center to the lower edge is |lower_offset|.
# The corners of the lower edge are at x = +/- (flat_len/2) relative to the edge center?
# No, the description says "straight segment of rounded_square_flat_edge_length".
# So the flat edge length is fixed.
# The corners are arcs connecting these flat edges.

# Let's construct the points.
# We need to find the coordinates of the 4 corner centers.
# Let the angle of the lower edge be 0 (horizontal).
# The normal to the lower edge points down (-Y).
# The distance from origin to the line of the lower edge is lower_offset (which is negative, so it's below).
# The corners of the lower edge are at x = +/- flat_len / 2.
# So Corner 3 (bottom right) and Corner 4 (bottom left) are at these x positions?
# Wait, the corner *centers* are at distance 'corner_offset' from the origin.
# Let's assume the corners are arranged symmetrically.
# If the lower edge is horizontal, the two bottom corners have the same Y coordinate.
# Let Y_corner = lower_offset.
# Then X_corner = +/- sqrt(corner_offset^2 - Y_corner^2).
# But we also have the flat edge length.
# The flat edge connects the two bottom corners.
# So the distance between the two bottom corners must be flat_len.
# So 2 * X_corner = flat_len => X_corner = flat_len / 2.
# This implies corner_offset^2 = (flat_len/2)^2 + lower_offset^2.
# Let's check: 31.82^2 = 1012.5. (52.46/2)^2 + (-36.82)^2 = 26.23^2 + 36.82^2 = 688 + 1355 = 2043.
# They don't match. The description says "equal-magnitude corner-center offsets".
# This implies all 4 corners are at distance R = 31.82 from origin.
# And the lower flat edge is at Y = -36.82.
# If the corners are at Y = -36.82, then the flat edge connects them.
# The length of the flat edge would be 2 * sqrt(R^2 - Y^2).
# 2 * sqrt(31.82^2 - 36.82^2) -> Imaginary number.
# This means the "lower flat offset" cannot be the Y-coordinate of the corners if the corners are at that radius.
# Re-reading: "signed offset of the lower straight segment from the profile center".
# Maybe the corners are NOT at the same Y.
# "Each side uses a straight segment ... and a non-tangent corner arc".
# "non-tangent corner arc governed by ... start_angle, end_angle".
# This suggests the arcs are not the standard 90-degree fillets of a rounded square, but specific arcs defined by angles.
# And the "corner-center offset" is the distance from the origin to the center of that arc.
# Let's assume the 4 corners are at angles 45, 135, 225, 315 degrees (standard square rotation).
# Radius = 31.82.
# Corner 1 (45 deg): (22.2, 22.2)
# Corner 2 (135 deg): (-22.2, 22.2)
# Corner 3 (225 deg): (-22.2, -22.2)
# Corner 4 (315 deg): (22.2, -22.2)
# The "lower straight segment" connects Corner 3 and Corner 4.
# Its Y coordinate is -22.2.
# But the parameter says lower_offset = -36.82.
# This contradicts the "equal magnitude offset" if the shape is a standard rotated square.
# Perhaps the "lower straight segment" is NOT the bottom side of the square, but a specific segment defined by the geometry.
# Or maybe the "corner-center offset" is not the radius of the arc center, but the distance to the midpoint of the flat edge? No, "corner-center".
# Let's reconsider the geometry construction.
# Maybe the "lower straight segment" is offset by -36.82 from the center.
# And the corners are at distance 31.82.
# This is geometrically impossible for a convex polygon where the flat edge is a chord of the circle defined by the corner centers, UNLESS the corner centers are not the vertices of the polygon but the centers of the arcs, and the flat edge is tangent to the arcs?
# "non-tangent corner arc". This implies the arc is not tangent to the flat edge.
# So the flat edge and the arc meet at an angle.
# Let's try to construct the points based on the parameters directly.
# We have 4 corners. Let's place them at angles 45, 135, 225, 315 with radius 31.82.
# C1: (22.2, 22.2), C2: (-22.2, 22.2), C3: (-22.2, -22.2), C4: (22.2, -22.2).
# The flat edges connect these.
# Edge 1-2: Top. Y=22.2.
# Edge 2-3: Left. X=-22.2.
# Edge 3-4: Bottom. Y=-22.2.
# Edge 4-1: Right. X=22.2.
# The "lower straight segment" is Edge 3-4. Its Y is -22.2.
# The parameter says -36.82.
# Is it possible the "lower straight segment" refers to something else?
# Or maybe the "corner-center offset" is not 31.82?
# Let's look at the numbers again.
# 31.8198052.
# 36.8198052.
# Difference is 5.0.
# Maybe the corners are shifted?
# What if the "lower straight segment" is defined by the parameter, and the corners are derived?
# "Each side uses a straight segment of rounded_square_flat_edge_length".
# So the length of the bottom edge is 52.4592704.
# If the bottom edge is at Y = -36.8198052, and has length L.
# The corners are at distance R = 31.8198052 from origin.
# Let the corners be at (x1, y1) and (x2, y2).
# y1 = y2 = -36.8198052.
# x2 - x1 = 52.4592704.
# x1^2 + y1^2 = R^2.
# x1^2 + (-36.82)^2 = 31.82^2.
# x1^2 = 31.82^2 - 36.82^2 < 0. Impossible.
# Conclusion: The "lower straight segment" is NOT a horizontal line at Y = -36.82 connecting two points on the circle of radius 31.82.
# Alternative interpretation: The "corner-center offset" is the distance from the origin to the center of the arc.
# The "lower straight segment" is offset from the center by -36.82.
# Maybe the "lower straight segment" is not the bottom edge of the square, but a specific segment in the profile?
# "The profile has rounded_square_side_count identical sides."
# This implies a regular polygon-like shape.
# If it's a regular polygon, all sides are equidistant from the center.
# But the parameters give different offsets for "lower" and "corner".
# This implies the shape is NOT a regular polygon.
# It is a "rounded square" but distorted?
# "rounded_square_side_count identical sides".
# Maybe the "lower straight segment" is one of the sides, and its distance from center is -36.82.
# And the "corner-center offset" is the distance to the arc centers.
# If the shape has 4 sides, and one is at distance -36.82, and the corners are at distance 31.82.
# This is still geometrically tricky.
# Let's try to construct the sketch points manually using the parameters as coordinates.
# Hypothesis: The profile is defined by 4 corner centers and 4 flat edges.
# Corner centers are at angles 45, 135, 225, 315 with radius 31.82.
# Flat edges connect these corners.
# But the "lower straight segment" parameter (-36.82) doesn't match the Y of the bottom edge (-22.2).
# Is it possible the "lower straight segment" is the distance from the center to the *midpoint* of the lower flat edge?
# Midpoint of bottom edge (connecting C3 and C4) is (0, -22.2). Distance is 22.2.
# Still doesn't match -36.82.
# What if the "lower straight segment" is the distance from the center to the *line* containing the lower flat edge?
# That is 22.2.
# What if the "corner-center offset" is not the radius of the corner centers?
# "equal-magnitude corner-center offsets from the profile center are rounded_square_corner_center_offset".
# This seems clear.
# Is it possible the "lower straight segment" is not the bottom edge?
# "signed offset of the lower straight segment from the profile center".
# Maybe the "lower straight segment" is the segment connecting the two bottom corners, but the corners are NOT at 225/315 degrees?
# What if the corners are at angles such that the bottom edge is at Y = -36.82?
# If the bottom edge is at Y = -36.82, and the corners are at distance R = 31.82.
# Then the corners must be at Y = -36.82.
# But then R must be >= 36.82. But R is 31.82.
# This is a contradiction.
# Let's re-read carefully: "rounded_square_lower_flat_offset_from_center".
# Maybe this is the offset of the *flat edge* from the *corner center*? No, "from the profile center".
# Maybe the "profile center" is not (0,0)? No, sketches are usually centered.
# Is it possible the "lower straight segment" is the *vertical* segment on the left or right?
# If the shape is rotated?
# If the "lower" segment is the
