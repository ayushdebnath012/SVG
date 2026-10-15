import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Part")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We will use App::PropertyLength and App::PropertyInteger for parameters.
# To make them editable in the tree, we create a VarSet or just add them to the Body directly.
# Adding to Body is standard for simple parametric scripts.

params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "main_body_thickness", "Dimensions", "main_body_thickness")
params.main_body_thickness = 28.00
params.addProperty("App::PropertyLength", "main_body_upper_edge_height", "Dimensions", "main_body_upper_edge_height")
params.main_body_upper_edge_height = 70.50
params.addProperty("App::PropertyLength", "main_body_upper_shoulder_height", "Dimensions", "main_body_upper_shoulder_height")
params.main_body_upper_shoulder_height = 28.50
params.addProperty("App::PropertyLength", "main_body_lower_shoulder_height", "Dimensions", "main_body_lower_shoulder_height")
params.main_body_lower_shoulder_height = -43.50
params.addProperty("App::PropertyLength", "main_body_lower_edge_height", "Dimensions", "main_body_lower_edge_height")
params.main_body_lower_edge_height = -70.50
params.addProperty("App::PropertyLength", "main_body_cutout_cross_section_length", "Dimensions", "main_body_cutout_cross_section_length")
params.main_body_cutout_cross_section_length = 32.00
params.addProperty("App::PropertyLength", "rectangular_cutout_length", "Dimensions", "rectangular_cutout_length")
params.rectangular_cutout_length = 50.80
params.addProperty("App::PropertyLength", "main_body_cross_section_length", "Dimensions", "main_body_cross_section_length")
params.main_body_cross_section_length = 26.00
params.addProperty("App::PropertyLength", "main_body_cross_section_width", "Dimensions", "main_body_cross_section_width")
params.main_body_cross_section_width = 5.00
params.addProperty("App::PropertyLength", "secondary_body_thickness", "Dimensions", "secondary_body_thickness")
params.secondary_body_thickness = 12.00
params.addProperty("App::PropertyLength", "lug_cross_section_width", "Dimensions", "lug_cross_section_width")
params.lug_cross_section_width = 11.00
params.addProperty("App::PropertyLength", "upper_lug_cross_section_length", "Dimensions", "upper_lug_cross_section_length")
params.upper_lug_cross_section_length = 31.80
params.addProperty("App::PropertyLength", "lower_lug_cross_section_length", "Dimensions", "lower_lug_cross_section_length")
params.lower_lug_cross_section_length = 14.40
params.addProperty("App::PropertyLength", "upper_lug_lower_edge_height", "Dimensions", "upper_lug_lower_edge_height")
params.upper_lug_lower_edge_height = 28.50
params.addProperty("App::PropertyLength", "lower_lug_lower_edge_height", "Dimensions", "lower_lug_lower_edge_height")
params.lower_lug_lower_edge_height = -57.90
params.addProperty("App::PropertyLength", "main_body_cutout_cross_section_width", "Dimensions", "main_body_cutout_cross_section_width")
params.main_body_cutout_cross_section_width = 105.00
params.addProperty("App::PropertyLength", "main_body_cutout_corner_radius", "Dimensions", "main_body_cutout_corner_radius")
params.main_body_cutout_corner_radius = 3.00
params.addProperty("App::PropertyLength", "main_body_cutout_depth", "Dimensions", "main_body_cutout_depth")
params.main_body_cutout_depth = 22.00
params.addProperty("App::PropertyLength", "main_recess_lower_edge_height", "Dimensions", "main_recess_lower_edge_height")
params.main_recess_lower_edge_height = -65.50
params.addProperty("App::PropertyLength", "cutout_depth", "Dimensions", "cutout_depth")
params.cutout_depth = 4.00
params.addProperty("App::PropertyLength", "side_chamfered_cutout_center_x", "Dimensions", "side_chamfered_cutout_center_x")
params.side_chamfered_cutout_center_x = 1.00
params.addProperty("App::PropertyLength", "side_chamfered_cutout_center_y", "Dimensions", "side_chamfered_cutout_center_y")
params.side_chamfered_cutout_center_y = 14.65
params.addProperty("App::PropertyLength", "side_chamfered_cutout_flat_width", "Dimensions", "side_chamfered_cutout_flat_width")
params.side_chamfered_cutout_flat_width = 17.00
params.addProperty("App::PropertyLength", "side_chamfered_cutout_flat_height", "Dimensions", "side_chamfered_cutout_flat_height")
params.side_chamfered_cutout_flat_height = 27.70
params.addProperty("App::PropertyLength", "side_chamfer_size", "Dimensions", "side_chamfer_size")
params.side_chamfer_size = 1.00
params.addProperty("App::PropertyLength", "main_body_extrusion_length", "Dimensions", "main_body_extrusion_length")
params.main_body_extrusion_length = 27.70
params.addProperty("App::PropertyLength", "small_rectangular_cutout_length", "Dimensions", "small_rectangular_cutout_length")
params.small_rectangular_cutout_length = 4.00
params.addProperty("App::PropertyLength", "cap_baseline_frontward_offset", "Dimensions", "cap_baseline_frontward_offset")
params.cap_baseline_frontward_offset = -10.50
params.addProperty("App::PropertyLength", "cap_rise", "Dimensions", "cap_rise")
params.cap_rise = 2.31
params.addProperty("App::PropertyLength", "rectangular_cutout_width", "Dimensions", "rectangular_cutout_width")
params.rectangular_cutout_width = 6.00
params.addProperty("App::PropertyLength", "shallow_rectangular_cutout_depth", "Dimensions", "shallow_rectangular_cutout_depth")
params.shallow_rectangular_cutout_depth = 1.90
params.addProperty("App::PropertyLength", "shallow_rectangular_cutout_lower_edge_height", "Dimensions", "shallow_rectangular_cutout_lower_edge_height")
params.shallow_rectangular_cutout_lower_edge_height = 22.50
params.addProperty("App::PropertyLength", "cutout_half_width", "Dimensions", "cutout_half_width")
params.cutout_half_width = 8.00
params.addProperty("App::PropertyLength", "front_window_lower_edge_height", "Dimensions", "front_window_lower_edge_height")
params.front_window_lower_edge_height = 2.50
params.addProperty("App::PropertyLength", "front_window_upper_edge_height", "Dimensions", "front_window_upper_edge_height")
params.front_window_upper_edge_height = 26.50
params.addProperty("App::PropertyLength", "side_through_hole_diameter", "Dimensions", "side_through_hole_diameter")
params.side_through_hole_diameter = 2.80
params.addProperty("App::PropertyLength", "side_hole_a_center_x", "Dimensions", "side_hole_a_center_x")
params.side_hole_a_center_x = -7.98
params.addProperty("App::PropertyLength", "side_hole_a_center_y", "Dimensions", "side_hole_a_center_y")
params.side_hole_a_center_y = -6.50
params.addProperty("App::PropertyLength", "side_hole_b_center_x", "Dimensions", "side_hole_b_center_x")
params.side_hole_b_center_x = 0.72
params.addProperty("App::PropertyLength", "side_hole_b_center_y", "Dimensions", "side_hole_b_center_y")
params.side_hole_b_center_y = -41.00
params.addProperty("App::PropertyLength", "dual_body_through_hole_diameter", "Dimensions", "dual_body_through_hole_diameter")
params.dual_body_through_hole_diameter = 3.00
params.addProperty("App::PropertyLength", "bottom_hole_pair_center_height", "Dimensions", "bottom_hole_pair_center_height")
params.bottom_hole_pair_center_height = -9.00
params.addProperty("App::PropertyLength", "bottom_hole_pair_spacing", "Dimensions", "bottom_hole_pair_spacing")
params.bottom_hole_pair_spacing = 15.00
params.addProperty("App::PropertyLength", "common_cutout_length", "Dimensions", "common_cutout_length")
params.common_cutout_length = 15.00
params.addProperty("App::PropertyLength", "square_main_body_cutout_depth", "Dimensions", "square_main_body_cutout_depth")
params.square_main_body_cutout_depth = 14.00
params.addProperty("App::PropertyLength", "square_cutout_lower_edge_height", "Dimensions", "square_cutout_lower_edge_height")
params.square_cutout_lower_edge_height = 45.30
params.addProperty("App::PropertyLength", "short_rectangular_cutout_length", "Dimensions", "short_rectangular_cutout_length")
params.short_rectangular_cutout_length = 15.00
params.addProperty("App::PropertyLength", "short_rectangular_cutout_width", "Dimensions", "short_rectangular_cutout_width")
params.short_rectangular_cutout_width = 10.00
params.addProperty("App::PropertyLength", "short_rectangular_cutout_depth", "Dimensions", "short_rectangular_cutout_depth")
params.short_rectangular_cutout_depth = 14.00
params.addProperty("App::PropertyLength", "short_cutout_lower_edge_height", "Dimensions", "short_cutout_lower_edge_height")
params.short_cutout_lower_edge_height = -57.90
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "mounting_hole_diameter")
params.mounting_hole_diameter = 7.00
params.addProperty("App::PropertyLength", "hole_cut_depth", "Dimensions", "hole_cut_depth")
params.hole_cut_depth = 7.50
params.addProperty("App::PropertyLength", "mounting_hole_column_center_offset", "Dimensions", "mounting_hole_column_center_offset")
params.mounting_hole_column_center_offset = 24.50
params.addProperty("App::PropertyLength", "mounting_hole_upper_row_center_height", "Dimensions", "mounting_hole_upper_row_center_height")
params.mounting_hole_upper_row_center_height = 65.70
params.addProperty("App::PropertyLength", "mounting_hole_lower_row_center_height", "Dimensions", "mounting_hole_lower_row_center_height")
params.mounting_hole_lower_row_center_height = -62.90
params.addProperty("App::PropertyLength", "triangular_cutout_width", "Dimensions", "triangular_cutout_width")
params.triangular_cutout_width = 15.00
params.addProperty("App::PropertyLength", "triangular_cutout_lower_vertex_height", "Dimensions", "triangular_cutout_lower_vertex_height")
params.triangular_cutout_lower_vertex_height = 60.30
params.addProperty("App::PropertyLength", "rectangular_cutout_depth", "Dimensions", "rectangular_cutout_depth")
params.rectangular_cutout_depth = 5.00
params.addProperty("App::PropertyLength", "repeated_cutout_column_center_offset", "Dimensions", "repeated_cutout_column_center_offset")
params.repeated_cutout_column_center_offset = 36.00
params.addProperty("App::PropertyLength", "repeated_cutout_lower_row_center_height", "Dimensions", "repeated_cutout_lower_row_center_height")
params.repeated_cutout_lower_row_center_height = -50.55
params.addProperty("App::PropertyLength", "repeated_cutout_upper_row_center_height", "Dimensions", "repeated_cutout_upper_row_center_height")
params.repeated_cutout_upper_row_center_height = 39.45
params.addProperty("App::PropertyLength", "narrow_rectangular_cutout_width", "Dimensions", "narrow_rectangular_cutout_width")
params.narrow_rectangular_cutout_width = 5.00
params.addProperty("App::PropertyLength", "top_narrow_cutout_lower_edge_height", "Dimensions", "top_narrow_cutout_lower_edge_height")
params.top_narrow_cutout_lower_edge_height = 62.50

# --- Base Sketch (Main Body Profile) ---
# We define the main body profile on the XY plane.
# The body is symmetric about the YZ plane (x=0).
# Thickness is along Z.
# Height is along Y.
# Width is along X.

sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = [doc.getObject("XY_Plane")]
sketch_base.ConstrainToCurrentPlane = True
sketch_base.MapMode = "FlatFace"

# Define the main body profile (Outer Boundary)
# It's a rectangle centered at (0,0) with width = main_body_cross_section_length and height = main_body_upper_edge_height - main_body_lower_edge_height
# But wait, the description says "main_body_cutout_cross_section_length" for outer side edges?
# Re-reading: "The outer side edges are symmetrically located by main_body_cutout_cross_section_length"
# This phrasing is ambiguous. Usually "located by" implies distance from center.
# However, later it says "central-stem width is rectangular_cutout_length".
# Let's assume the main body width is defined by the cutout length if it's a frame, or the cutout length is the gap.
# "A main body is a single upright plate-like frame... The outer side edges are symmetrically located by main_body_cutout_cross_section_length"
# This likely means the distance from center to outer edge is main_body_cutout_cross_section_length.
# So Total Width = 2 * main_body_cutout_cross_section_length.
# Let's verify with other params. main_body_cross_section_length = 26.00. main_body_cutout_cross_section_length = 32.00.
# If 32 is half-width, total width is 64. If 32 is total width, half is 16.
# Given "outer side edges are symmetrically located by...", it strongly suggests the coordinate of the edge.
# So X_max = 32.0, X_min = -32.0.
# Height: Y_max = 70.5, Y_min = -70.5.
# Thickness: Z = +/- 14.0 (28.0 total).

# Let's draw the main body profile.
# We need to construct the profile on the XY plane.
# The profile will be a rectangle.
# Points: (-32, -70.5), (32, -70.5), (32, 70.5), (-32, 70.5)

# Helper to add line segments
def add_line(sketch, p1, p2):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

# Main Body Profile
# Bottom edge
add_line(sketch_base, App.Vector(-params.main_body_cutout_cross_section_length, params.main_body_lower_edge_height, 0), 
         App.Vector(params.main_body_cutout_cross_section_length, params.main_body_lower_edge_height, 0))
# Right edge
add_line(sketch_base, App.Vector(params.main_body_cutout_cross_section_length, params.main_body_lower_edge_height, 0), 
         App.Vector(params.main_body_cutout_cross_section_length, params.main_body_upper_edge_height, 0))
# Top edge
add_line(sketch_base, App.Vector(params.main_body_cutout_cross_section_length, params.main_body_upper_edge_height, 0), 
         App.Vector(-params.main_body_cutout_cross_section_length, params.main_body_upper_edge_height, 0))
# Left edge
add_line(sketch_base, App.Vector(-params.main_body_cutout_cross_section_length, params.main_body_upper_edge_height, 0), 
         App.Vector(-params.main_body_cutout_cross_section_length, params.main_body_lower_edge_height, 0))

# Close loop
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 0)) # Close loop constraint logic handled by sketcher usually if closed, but explicit close helps
# Actually, Sketcher needs a closed loop. The last point connects to the first.
# We need to ensure the sketch is closed.
# Let's add a constraint to close the loop.
# Find the last segment index? Easier to just add a constraint between start and end points.
# But we don't have point indices easily.
# Let's just rely on the geometry being a closed loop.
# Wait, Sketcher::SketchObject requires a closed loop for extrusion usually.
# Let's add a constraint: Coincident between point 0 and point 3 (last).
# Actually, let's just use the standard way: add a constraint "Coincident" between the first and last point.
# Since we added 4 lines, we have 4 points.
# Point 0: (-32, -70.5)
# Point 1: (32, -70.5)
# Point 2: (32, 70.5)
# Point 3: (-32, 70.5)
# We need to constrain Point 3 to Point 0.
# Sketcher constraints are tricky to index manually without a loop.
# Let's just add a constraint "Coincident" between the first and last geometry elements? No.
# Let's just assume the sketcher will close it if we add a constraint "Coincident" between the first and last point.
# We can't easily get indices.
# Alternative: Add a constraint "Horizontal" and "Vertical" to all points relative to origin?
# Let's just add a constraint "Coincident
