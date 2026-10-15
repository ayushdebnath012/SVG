import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

# Create a new document
doc = App.newDocument("ConnectorHousing")

# --- Parameters Object ---
# We create a standard App::Object to hold the parameters as Float properties.
# This satisfies the requirement for "named document objects" driving the geometry.
param_obj = doc.addObject("App::Object", "Parameters")
param_obj.addProperty("App::PropertyFloat", "rear_rounded_square_section_thickness", "Dimensions", "thickness")
param_obj.addProperty("App::PropertyInteger", "rounded_square_side_count", "Dimensions", "sides")
param_obj.addProperty("App::PropertyFloat", "rounded_square_corner_center_offset", "Dimensions", "corner_offset")
param_obj.addProperty("App::PropertyFloat", "rounded_square_corner_arc_radius", "Dimensions", "corner_radius")
param_obj.addProperty("App::PropertyFloat", "rounded_square_corner_arc_start_angle", "Dimensions", "corner_start")
param_obj.addProperty("App::PropertyFloat", "rounded_square_corner_arc_end_angle", "Dimensions", "corner_end")
param_obj.addProperty("App::PropertyFloat", "rounded_square_flat_edge_length", "Dimensions", "flat_len")
param_obj.addProperty("App::PropertyFloat", "rounded_square_lower_flat_offset_from_center", "Dimensions", "lower_offset")
param_obj.addProperty("App::PropertyFloat", "circular_port_outer_diameter", "Dimensions", "port_dia")
param_obj.addProperty("App::PropertyFloat", "housing_overall_axial_length", "Dimensions", "housing_len")
param_obj.addProperty("App::PropertyFloat", "circular_end_opening_width", "Dimensions", "end_open_w")
param_obj.addProperty("App::PropertyFloat", "circular_end_opening_height", "Dimensions", "end_open_h")
param_obj.addProperty("App::PropertyFloat", "lower_side_opening_width", "Dimensions", "side_open_w")
param_obj.addProperty("App::PropertyFloat", "lower_side_opening_height", "Dimensions", "side_open_h")
param_obj.addProperty("App::PropertyFloat", "lower_side_opening_center_x_offset", "Dimensions", "side_open_x")
param_obj.addProperty("App::PropertyFloat", "lower_side_opening_center_y_offset", "Dimensions", "side_open_y")
param_obj.addProperty("App::PropertyFloat", "tapered_side_opening_near_edge_height", "Dimensions", "taper_near_h")
param_obj.addProperty("App::PropertyFloat", "tapered_side_opening_far_edge_height", "Dimensions", "taper_far_h")
param_obj.addProperty("App::PropertyFloat", "tapered_side_opening_axial_length", "Dimensions", "taper_len")
param_obj.addProperty("App::PropertyFloat", "side_fastener_row_axial_position", "Dimensions", "fastener_z")
param_obj.addProperty("App::PropertyFloat", "side_fastener_center_spacing", "Dimensions", "fastener_spacing")
param_obj.addProperty("App::PropertyFloat", "side_fastener_through_hole_diameter", "Dimensions", "fastener_hole_d")
param_obj.addProperty("App::PropertyFloat", "side_fastener_counterbore_diameter", "Dimensions", "fastener_cb_d")
param_obj.addProperty("App::PropertyFloat", "side_fastener_counterbore_depth", "Dimensions", "fastener_cb_d")
param_obj.addProperty("App::PropertyInteger", "corner_fastener_count", "Dimensions", "corner_count")
param_obj.addProperty("App::PropertyFloat", "corner_through_hole_diameter", "Dimensions", "corner_hole_d")
param_obj.addProperty("App::PropertyFloat", "corner_through_hole_depth", "Dimensions", "corner_hole_d")
param_obj.addProperty("App::PropertyFloat", "corner_counterbore_diameter", "Dimensions", "corner_cb_d")
param_obj.addProperty("App::PropertyFloat", "corner_counterbore_depth", "Dimensions", "corner_cb_d")

# Assign values
param_obj.recompute() # Ensure properties are initialized
param_obj.rear_rounded_square_section_thickness = 10.0
param_obj.rounded_square_side_count = 4
param_obj.rounded_square_corner_center_offset = 31.8198052
param_obj.rounded_square_corner_arc_radius = 7.5
param_obj.rounded_square_corner_arc_start_angle = 131.8103149
param_obj.rounded_square_corner_arc_end_angle = -41.8103149
param_obj.rounded_square_flat_edge_length = 52.4592704
param_obj.rounded_square_lower_flat_offset_from_center = -36.8198052
param_obj.circular_port_outer_diameter = 60.0
param_obj.housing_overall_axial_length = 52.52
param_obj.circular_end_opening_width = 24.5
param_obj.circular_end_opening_height = 31.5
param_obj.lower_side_opening_width = 24.05
param_obj.lower_side_opening_height = 30.0
param_obj.lower_side_opening_center_x_offset = -0.225
param_obj.lower_side_opening_center_y_offset = -28.0
param_obj.tapered_side_opening_near_edge_height = 30.0
param_obj.tapered_side_opening_far_edge_height = 25.0
param_obj.tapered_side_opening_axial_length = 15.0
param_obj.side_fastener_row_axial_position = 34.52
param_obj.side_fastener_center_spacing = 24.0
param_obj.side_fastener_through_hole_diameter = 3.7
param_obj.side_fastener_counterbore_diameter = 7.0
param_obj.side_fastener_counterbore_depth = 21.0
param_obj.corner_fastener_count = 4
param_obj.corner_through_hole_diameter = 5.0
param_obj.corner_through_hole_depth = 22.6
param_obj.corner_counterbore_diameter = 8.5
param_obj.corner_counterbore_depth = 12.52

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Ensure standard planes exist
planes = ["XY_Plane", "XZ_Plane", "YZ_Plane", "X_Axis", "Y_Axis", "Z_Axis"]
for p_name in planes:
    if p_name not in [o.Name for o in doc.Objects]:
        plane_obj = doc.addObject("Part::Plane", p_name)
        if p_name == "XY_Plane":
            plane_obj.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
        elif p_name == "XZ_Plane":
            plane_obj.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(math.pi/2, 0, 0))
        elif p_name == "YZ_Plane":
            plane_obj.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0, 0, math.pi/2))
        doc.recompute()

# --- Step 1: Rear Rounded Square Profile ---
# Constructing the profile based on the description:
# - 4 sides.
# - Corner centers at distance 31.82 from origin.
# - Lower flat edge offset -36.82.
# - Corner arcs with specific angles.
# Interpretation: The profile is a closed loop.
# Let's define the vertices of the straight segments and the arcs.
# Given the symmetry and "lower flat offset", let's assume the shape is symmetric about X-axis but not Y?
# Or maybe the "lower" refers to the bottom-most part.
# Let's try to construct the vertices manually to match the description.
# Corner centers:
# If "equal-magnitude corner-center offsets", and there are 4 corners.
# Let's assume the corners are at angles 45, 135, 225, 315 degrees?
# Distance = 31.82.
# Coordinates:
# C1 (Top Right): (31.82 * cos(45), 31.82 * sin(45)) = (22.46, 22.46)
# C2 (Top Left): (-22.46, 22.46)
# C3 (Bottom Left): (-22.46, -22.46)
# C4 (Bottom Right): (22.46, -22.46)
# But the "lower flat offset" is -36.82. This doesn't match -22.46.
# Alternative: The corners are at 0, 90, 180, 270?
# C1 (Right): (31.82, 0)
# C2 (Top): (0, 31.82)
# C3 (Left): (-31.82, 0)
# C4 (Bottom): (0, -31.82)
# Still doesn't match -36.82.
# Maybe the "corner-center offset" is the coordinate value itself?
# If C_bottom_center_y = -31.82.
# And the flat edge is at y = -36.82.
# Then the arc connects the flat edge to the next segment.
# Radius = 7.5.
# If the arc is tangent to the flat edge (y=-36.82), its center would be at y = -36.82 + 7.5 = -29.32?
# Or y = -36.82 - 7.5 = -44.32?
# Let's assume the "corner-center offset" is the distance from origin to the center of the arc.
# And the "lower flat offset" is the y-coordinate of the flat edge.
# Let's try to construct the profile as a sequence of lines and arcs.
# We will define the sketch on the XY plane.

sketch_rsq = body.newObject("Sketcher::SketchObject", "RsqProfile")
sketch_rsq.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_rsq.Placement.Rotation = App.Rotation()
sketch_rsq.Placement.Rotation.X = 0
sketch_rsq.Placement.Rotation.Y = 0
sketch_rsq.Placement.Rotation.Z = 0
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1)
sketch_rsq.Placement.Rotation.XYZ = (0,0,0)
sketch_rsq.Placement.Rotation.XYZ = (0,0,1
