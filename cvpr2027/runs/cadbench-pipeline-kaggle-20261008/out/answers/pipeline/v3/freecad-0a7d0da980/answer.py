import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("PowerStrip")

# --- Parameters ---
# Base dimensions
block_length = 34.75
block_width = 98.6
block_thickness = 3.2
base_x_min = -17.38
base_y_min = -96.79

# Outer Wall
block_extrude_depth = 17.46
outer_profile_top_y = -0.05
outer_profile_bottom_y = -95.04
outer_profile_left_side_x = -15.92
outer_profile_right_side_x = 15.9
top_edge_width = 19.87
top_edge_left_x = -9.99
top_edge_right_x = 9.88

# Top Terminals
top_terminal_arc_left_center_x = -10.05
top_terminal_arc_left_center_y = -8.36
top_terminal_arc_left_radius = 5.85
top_terminal_arc_left_start_angle = 140.1317284
top_terminal_arc_left_end_angle = -179.9020586

top_terminal_arc_right_center_x = 9.95
top_terminal_arc_right_center_y = -8.56
top_terminal_arc_right_radius = 5.94
top_terminal_arc_right_start_angle = 2.217415716
top_terminal_arc_right_end_angle = 41.38540326

# Transition Seed
transition_seed_upper_left_arc_center_x = -10.14
transition_seed_upper_left_arc_center_y = -17.59
transition_seed_upper_left_arc_radius = 5.74
transition_seed_upper_left_arc_start_angle = -179.7005474
transition_seed_upper_left_arc_end_angle = -107.6458007

transition_seed_upper_right_arc_center_x = 10.08
transition_seed_upper_right_arc_center_y = -17.74
transition_seed_upper_right_arc_radius = 5.81
transition_seed_upper_right_arc_start_angle = -71.1286391
transition_seed_upper_right_arc_end_angle = -3.748504046

transition_seed_lower_left_arc_center_x = -10.05
transition_seed_lower_left_arc_center_y = -32.23
transition_seed_lower_left_arc_radius = 5.82
transition_seed_lower_left_arc_start_angle = 134.2342454
transition_seed_lower_left_arc_end_angle = -180.0984463

transition_seed_lower_right_arc_center_x = 10.41
transition_seed_lower_right_arc_center_y = -32.12
transition_seed_lower_right_arc_radius = 5.46
transition_seed_lower_right_arc_start_angle = 0.2098737116
transition_seed_lower_right_arc_end_angle = 46.18730732

transition_seed_left_elbow_x = -11.91
transition_seed_left_elbow_y = -25.85
transition_seed_right_elbow_x = 11.97
transition_seed_right_elbow_y = -26.0

number_of_inter_socket_transitions = 3

# Bottom Connecting Arcs
bottom_connecting_arc_left_center_x = -10.87
bottom_connecting_arc_left_center_y = -89.98
bottom_connecting_arc_left_radius = 5.05
bottom_connecting_arc_left_start_angle = -180
bottom_connecting_arc_left_end_angle = -90

bottom_connecting_arc_right_center_x = 10.74
bottom_connecting_arc_right_center_y = -89.88
bottom_connecting_arc_right_radius = 5.16
bottom_connecting_arc_right_start_angle = -90
bottom_connecting_arc_right_end_angle = 0

bottom_straight_span = 21.61

# Stepped Inner Wall
stepped_profile_extrude_depth = 3.73
stepped_profile_center_x = 0.0
stepped_profile_top_y = -3.58
stepped_profile_bottom_y = -91.36
cavity_profile_overall_width = 23.19
cavity_profile_overall_height = 87.78
bottom_flat_width = 12.5

# Top Right/Left Details
top_right_corner_arc_radius = 2.43
top_right_corner_arc_angle = 45.7064486
top_center_right_arc_radius = 1.7
top_center_left_arc_radius = 2.04
top_center_left_arc_angle = 44.6468796
top_left_corner_arc_radius = 2.08
upper_step_right_arc_radius = 1.49
upper_step_right_arc_angle = 85.4445613
upper_step_left_arc_radius = 1.42
middle_step_left_arc_radius = 1.24
middle_step_right_arc_radius = 1.48
lower_step_left_arc_radius = 1.3
lower_step_right_arc_radius = 1.55
stepped_top_flat_width = 11.23

# Diagonals and Bevels
upper_transition_right_diagonal_angle = 45.1223816
upper_transition_left_diagonal_angle = 45.8308042
middle_transition_right_diagonal_angle = 44.1045136
middle_transition_left_diagonal_angle = 51.9153345
lower_transition_right_diagonal_angle = 50.3628164
lower_transition_left_diagonal_angle = 50.2924765
bottom_right_bevel_angle = 36.6341139
bottom_left_bevel_angle = 42.4362298

top_right_shoulder_length = 5.6
top_left_shoulder_length = 5.59

# Upper Group
upper_outer_vertical_right_length = 8.12
upper_outer_vertical_left_length = 8.21
upper_horizontal_ledge_right_length = 0.78
upper_horizontal_ledge_left_length = 0.79
upper_inner_vertical_right_length = 11.33
upper_inner_vertical_left_length = 11.27
upper_transition_right_diagonal_length = 3.2
upper_transition_left_diagonal_length = 3.27

# Middle Group
middle_outer_vertical_right_length = 8.96
middle_outer_vertical_left_length = 9.18
middle_horizontal_ledge_right_length = 0.72
middle_horizontal_ledge_left_length = 1.05
middle_inner_vertical_right_length = 11.39
middle_inner_vertical_left_length = 10.9
middle_transition_right_diagonal_length = 3.06
middle_transition_left_diagonal_length = 3.7

# Lower Group
lower_outer_vertical_right_length = 8.98
lower_outer_vertical_left_length = 8.91
lower_horizontal_ledge_right_length = 0.68
lower_horizontal_ledge_left_length = 0.99
lower_inner_vertical_right_length = 11.07
lower_inner_vertical_left_length = 11.01
lower_transition_right_diagonal_length = 3.49
lower_transition_left_diagonal_length = 3.59

# Bottom Group
bottom_outer_vertical_right_length = 10.31
bottom_outer_vertical_left_length = 10.31
bottom_outer_ledge_right_length = 4.9
bottom_outer_ledge_left_length = 4.98
bottom_right_bevel_length = 0.48
bottom_left_bevel_length = 0.48

# Ribs
stepped_rib_width = 1.6
stepped_rib_length = 86.7
stepped_rib_height = 3.2
gap_between_ribs = 7.0
number_of_ribs = 2
rib_left_x_min = -4.31
rib_right_x_min = 2.69
rib_y_min = -90.88

# Sockets
stepped_cavity_cut_depth = 18.5
socket_profile_cut_start_z = 0.0
outer_profile_top_width = 12.87
inner_profile_top_width = 10.15
seed_socket_outer_top_right_x = 6.54
seed_socket_inner_top_right_x = 5.12
outer_right_straight_length = 7.62
outer_left_straight_length = 7.63
inner_right_straight_length = 6.06
inner_left_straight_length = 5.81

outer_top_right_arc_radius = 6.29
outer_upper_right_arc_radius = 6.59
outer_lower_right_arc_radius = 5.91
outer_lower_left_arc_radius = 5.99
outer_upper_left_arc_radius = 6.42
outer_top_left_arc_radius = 6.77

inner_top_right_arc_radius = 2.99
inner_top_left_arc_radius = 3.26
inner_upper_left_arc_radius = 3.76
inner_lower_left_arc_radius = 3.46
inner_lower_right_arc_radius = 3.3
inner_upper_right_arc_radius = 3.02

seed_socket_outer_left_x = -14.93
seed_socket_outer_right_x = 14.93
seed_socket_outer_top_y = -72.6
seed_socket_outer_bottom_y = -94.68

seed_socket_inner_left_x = -11.14
seed_socket_inner_right_x = 11.28
seed_socket_inner_top_y = -75.9
seed_socket_inner_bottom_y = -91.27

# Small Cavities
small_cavity_length = 2.47
small_cavity_width = 5.0
cavity_cutout_depth = 8.0
small_cavity_cut_start_z = 0.0
number_of_small_cavities = 3
right_cavity_x_min = 5.79
right_cavity_y_min = -88.15
center_cavity_x_min = -1.19
center_cavity_y_min = -84.04
left_cavity_x_min = -8.2
left_cavity_y_min = -88.15

number_of_socket_modules = 4
socket_module_pitch = 24.0

# --- Build Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Base Sketch ---
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.ConstrainAuto = True
base_sketch.LockConstraints = False
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Base Rectangle
base_rect = Part.makeBox(block_length, block_width, 0)
base_rect = base_rect.moved(App.Placement(App.Vector(base_x_min, base_y_min, 0)))
base_sketch.addGeometry(base_rect, False)

# Base Pad
base_pad = body.newObject("PartDesign::Pad", "BasePad")
base_pad.Profile = base_sketch
base_pad.Length = block_thickness
base_pad.Type = "Solid"
base_pad.Reversed = False
base_pad.Midplane = False
base_pad.makeSolid()

# --- Outer Wall Sketch ---
outer_sketch = body.newObject("Sketcher::SketchObject", "OuterWallSketch")
outer_sketch.Placement = App.Placement(App.Vector(0, 0, block_thickness))
outer_sketch.ConstrainAuto = True
outer_sketch.LockConstraints = False
outer_sketch.MapMode = "FlatFace"
outer_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])

# Helper to add arc
def add_arc(sketch_obj, center, radius, start_angle, end_angle, is_ccw=True):
    # FreeCAD Sketcher arcs are defined by center, radius, start_angle, end_angle
    # Angles are in degrees. CCW is positive.
    # The sketcher constraint system handles the geometry.
    # We use Part.Circle to generate the geometry for the sketch.
    # Note: Part.Circle uses radians.
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    # Create a circle and trim it? No, Sketcher::SketchObject.addGeometry expects Part::Edge or Part::Wire.
    # We can use Part.makeCircle(radius, center, axis) but that creates a full circle.
    # We need an arc. Part::Arc2D or Part::Arc3D.
    # Part::Arc3D(center, radius, start_angle, end_angle, axis)
    # axis must be Z for XY plane.
    
    # However, Sketcher::SketchObject.addGeometry works with Part::Edge.
    # Let's use Part::Arc3D.
    arc = Part.Arc3D(center, radius, start_angle, end_angle, App.Vector(0, 0, 1))
    sketch_obj.addGeometry(arc, False)

# 1. Top Terminal Left
add_arc(outer_sketch, App.Vector(top_terminal_arc_left_center_x, top_terminal_arc_left_center_y, 0), 
        top_terminal_arc_left_radius, top_terminal_arc_left_start_angle, top_terminal_arc_left_end_angle)

# 2. Top Terminal Right
add_arc(outer_sketch, App.Vector(top_terminal_arc_right_center_x, top_terminal_arc_right_center_y, 0), 
        top_terminal_arc_right_radius, top_terminal_arc_right_start_angle, top_terminal_arc_right_end_angle)

# 3. Transition Seed Upper Left
add_arc(outer_sketch, App.Vector(transition_seed_upper_left_arc_center_x, transition_seed_upper_left_arc_center_y, 0), 
        transition_seed_upper_left_arc_radius, transition_seed_upper_left_arc_start_angle, transition_seed_upper_left_arc_end_angle)

# 4. Transition Seed Upper Right
add_arc(outer_sketch, App.Vector(transition_seed_upper_right_arc_center_x, transition_seed_upper_right_arc_center_y, 0), 
        transition_seed_upper_right_arc_radius, transition_seed_upper_right_arc_start_angle, transition_seed_upper_right_arc_end_angle)

# 5. Transition Seed Lower Left
add_arc(outer_sketch, App.Vector(transition_seed_lower_left_arc_center_x, transition_seed_lower_left_arc_center_y, 0), 
        transition_seed_lower_left_arc_radius, transition_seed_lower_left_arc_start_angle, transition_seed_lower_left_arc_end_angle)

# 6. Transition Seed Lower Right
add_arc(outer_sketch, App.Vector(transition_seed_lower_right_arc_center_x, transition_seed_lower_right_arc_center_y, 0), 
        transition_seed_lower_right_arc_radius, transition_seed_lower_right_arc_start_angle, transition_seed_lower_right_arc_end_angle)

# 7. Bottom Connecting Arc Left
add_arc(outer_sketch, App.Vector(bottom_connecting_arc_left_center_x, bottom_connecting_arc_left_center_y, 0), 
        bottom_connecting_arc_left_radius, bottom_connecting_arc_left_start_angle, bottom_connecting_arc_left_end_angle)

# 8. Bottom Connecting Arc Right
add_arc(outer_sketch, App.Vector(bottom_connecting_arc_right_center_x, bottom_connecting_arc_right_center_y, 0), 
        bottom_connecting_arc_right_radius, bottom_connecting_arc_right_start_angle, bottom_connecting_arc_right_end_angle)

# Straight segments connecting the arcs.
# Based on the description, we need to connect the endpoints of these arcs to form a closed loop.
# The description implies a specific topology. We will construct the wire manually by connecting points.
# Since Sketcher constraints are complex to automate perfectly for arbitrary arcs, we will build the wire from edges.
# We need to identify the endpoints of the arcs and connect them with lines.

# Let's define the points for the outer wall contour.
# We will create a list of points and connect them.
# This is a simplified approach to ensure a valid closed wire.
# We will assume the arcs are placed such that they connect logically based on the provided coordinates.
# To make it robust, we will create the wire from the arcs and lines.

# Let's create the wire explicitly.
# We need to find the endpoints of the arcs.
# Since we can't easily query the sketch object for endpoints before constraints, we will construct the wire from Part edges.

# Define the sequence of points/edges for the outer wall.
# This is a complex shape. We will approximate the connections based on the "shorter exterior sweep" rule.
# We will create a wire from the arcs and lines.

# Let's create the wire manually by defining the edges.
# We will use Part::Edge for lines and Part::Arc3D for arcs.

# Helper to create a line edge
def make_line(p1, p2):
    return Part.LineSegment(p1, p2)

# Helper to create an arc edge
def make_arc(center, radius, start_angle, end_angle):
    return Part.Arc3D(center, radius, start_angle, end_angle, App.Vector(0, 0, 1))

# We need to connect the arcs. Let's assume the order:
# Top Terminal Left -> Top Terminal Right -> Transition Upper Right -> Transition Upper Left -> Transition Lower Left -> Transition Lower Right -> Bottom Right -> Bottom Left -> Close.
# This is a guess at the topology. The prompt says "Two independently dimensioned terminal arcs... One inter-socket transition seed... Two straight side segments connect adjacent terminal, transition, and bottom-arc endpoints."
# This implies:
# Top Left Arc -> Line -> Top Right Arc -> Line -> Transition Upper Right Arc -> Line -> Transition Upper Left Arc -> Line -> Transition Lower Left Arc -> Line -> Transition Lower Right Arc -> Line -> Bottom Right Arc -> Line -> Bottom Left Arc -> Line -> Close.

# Let's extract the endpoints.
# Since we can't easily get endpoints from the sketch object without constraints, we will construct the wire from the arcs and lines directly in the sketch.
# We will add the arcs and lines to
