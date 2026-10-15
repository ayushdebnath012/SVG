import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create Document
doc = App.newDocument("HubMotor")

# --- Parameters ---
# Axial stations and radii
left_axial_tip = -11.75
right_axial_tip = 188.25
shaft_radius = 6.00
shaft_shoulder_radius = 10.00

left_shaft_shoulder_axial_station = 28.25
left_collar_inner_axial_station = 30.75
left_collar_base_radius = 26.58
left_collar_lip_radius = 27.08
left_collar_lip_end_axial_station = 34.25
left_collar_outer_axial_station = 35.25
left_collar_outer_radius = 36.15
left_taper_start_axial_station = 35.40
left_taper_start_radius = 36.50
left_taper_end_axial_station = 46.75
left_taper_end_radius = 47.85
left_housing_neck_radius = 57.00

left_flange_outer_face_axial_station = 54.75
left_flange_inner_face_axial_station = 59.75
housing_left_axial_station = 60.75
housing_right_axial_station = 101.75
right_flange_inner_face_axial_station = 102.75
right_flange_outer_face_axial_station = 107.75
housing_outer_radius = 60.00
flange_outer_radius = 69.50
housing_end_transition_fillet_radius = 3.00
flange_shoulder_fillet_radius = 1.00
flange_outer_corner_fillet_radius = 2.00
flange_inner_corner_fillet_radius = 0.50

right_housing_neck_axial_station = 115.75
right_housing_neck_inner_radius = 22.00
right_housing_neck_outer_radius = 57.00
right_taper_end_axial_station = 117.27
right_taper_end_radius = 20.00
right_land_start_axial_station = 118.75
right_bearing_shoulder_axial_station = 127.75
right_bearing_shoulder_radius = 17.00
right_shaft_shoulder_axial_station = 155.75

number_of_mounting_holes = 18
mounting_hole_diameter = 2.60
mounting_bolt_circle_radius = 63.25

rectangular_cutout_count = 2
right_cutout_width = 2.00
right_cutout_height = 10.28
right_cutout_lower_transverse_coordinate = -5.14
right_cutout_depth = 32.50
left_cutout_width = 2.00
left_cutout_height = 20.00
left_cutout_depth = 40.00

left_flange_outer_rim_axial_station = 56.75
flange_outer_rim_radial_station = 67.50
left_flange_inner_rim_axial_station = 59.25
flange_inner_rim_radial_station = 69.00
flange_rim_transition_entry_angle = 0.0
flange_shoulder_transition_radial_station = 61.00
flange_shoulder_transition_exit_angle = 270.0
left_housing_neck_transition_axial_station = 49.75
left_flange_shoulder_transition_axial_station = 53.75
right_flange_inner_rim_axial_station = 103.25
right_flange_outer_rim_axial_station = 105.75
right_flange_shoulder_transition_axial_station = 108.75
right_housing_neck_transition_axial_station = 112.75
left_collar_lip_transition_radial_station = 28.08
left_collar_outer_transition_axial_station = 35.75
left_collar_outer_transition_angle = 135.0
left_collar_base_transition_axial_station = 31.25
mounting_pattern_axis_offset = 0.00
cutout_pair_negative_edge_offset = -7.00

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject(name="XY_Plane", label="XY_Plane", objType="Part::Plane")
doc.addObject(name="XZ_Plane", label="XZ_Plane", objType="Part::Plane")
doc.addObject(name="YZ_Plane", label="YZ_Plane", objType="Part::Plane")
doc.addObject(name="X_Axis", label="X_Axis", objType="Part::Line")
doc.addObject(name="Y_Axis", label="Y_Axis", objType="Part::Line")
doc.addObject(name="Z_Axis", label="Z_Axis", objType="Part::Line")

# Define Feature Tree Order
# 1. Main Profile Sketch (Half section)
# 2. Main Body (Revolution)
# 3. Mounting Holes (Linear Pattern on main body faces)
# 4. Cutouts (Linear Pattern on main body faces)
# 5. Fillets (Chamfer feature or Fillet feature) - Applying after extrusion

# --- 1. Main Profile Sketch ---
# The profile is a half-section (Z >= 0). 
# X axis is radial (outward), Y axis is axial (up).
# We will construct the profile from left_axial_tip to right_axial_tip.
# Note: In sketch plane XY, let X be radius, Y be axial position.
# Since it's a half section, we draw from Y=left_axial_tip to Y=right_axial_tip.

sketch = body.newObject("Sketcher::SketchObject", "MainProfileSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Support = (doc.getObject("XY_Plane"), [0]) # Attach to XY Plane
sketch.ConstrainAutopilot = False
sketch.ConstrainAutoRotate = False
sketch.AddGeometryConstraint = False
sketch.MapMode = "OnPlane"
sketch.ConstraintSmoothing = 0
sketch.ConstraintSmoothingType = "None"
sketch.AddGeometryConstraint = False
sketch.AddGeometryConstraint = False

# Helper to add line segment
def add_line(p1, p2, auto_constrain=False):
    sketch.addGeometry(Part.LineSegment(p1, p2), auto_constrain)

# --- Profile Geometry Construction (Y = Axial, X = Radius) ---

# Left Shaft
# Start at left_axial_tip, shaft_radius
# P1: (shaft_radius, left_axial_tip)
# P2: (shaft_radius, left_shaft_shoulder_axial_station)
p1 = App.Vector(shaft_radius, left_axial_tip)
p2 = App.Vector(shaft_radius, left_shaft_shoulder_axial_station)
add_line(p1, p2, False)

# Left Shaft Shoulder (Step Up)
# P2: (shaft_shoulder_radius, left_shaft_shoulder_axial_station)
p3 = App.Vector(shaft_shoulder_radius, left_shaft_shoulder_axial_station)
add_line(p2, p3, False)

# Left Collar Base (Inner)
# P4: (left_collar_base_radius, left_collar_inner_axial_station)
p4 = App.Vector(left_collar_base_radius, left_collar_inner_axial_station)
add_line(p3, p4, False)

# Left Collar Lip (Transition)
# Transition from vertical to radial (or vice versa). 
# Description: "collar rises ... through its named lip ... joins a 45-degree tapered web"
# "The collar rises from left_collar_base_radius ... through its named lip"
# This implies a curve or a step. Given "unequal stepped end structures" and "transition radius", 
# we model the lip as a transition.
# Usually: Vertical up to base, then transition to outer radius.
# Let's assume a fillet between the vertical wall and the outer radius at the lip station.
# However, the prompt specifies specific stations for the lip.
# "collar_lip_end_axial_station": 34.25
# "collar_outer_axial_station": 35.25
# "collar_base_transition_axial_station": 31.25
# "collar_lip_transition_radial_station": 28.08
# "collar_outer_transition_axial_station": 35.75
# "collar_outer_transition_angle": 135.0

# Let's simplify the complex transitions into a smooth chain of lines and fillets where possible, 
# or specific arcs if "transition" implies a quadrant.
# "A rounded transition is either a 90-degree quadrant from a radial to an axial tangent..."
# Let's try to place points to match the stations and radii, then fillet.

# Point at base of collar (vertical start)
# Point at start of lip (radial change?)
# Let's define the path:
# 1. Vertical up to left_collar_inner_axial_station (Done)
# 2. Transition to left_collar_base_radius at left_collar_base_transition_axial_station?
#    No, base is usually the start.
# Let's assume the profile goes:
# (shaft_shoulder_radius, left_shaft_shoulder_axial_station) -> (left_collar_base_radius, left_collar_inner_axial_station)
# Then a transition to the outer collar.
# Let's define the lip geometry:
# Start: (left_collar_base_radius, left_collar_inner_axial_station)
# End: (left_collar_outer_radius, left_collar_outer_axial_station)
# Intermediate: Lip end (left_collar_lip_end_axial_station), Lip radius (left_collar_lip_radius)
# And outer transition.

# Simplified Path for Collar:
# 1. Vertical up to lip_end_axial
p5 = App.Vector(left_collar_base_radius, left_collar_lip_end_axial_station)
add_line(p4, p5, False)

# 2. Transition to outer radius. 
# The prompt mentions "lip" and "outer". 
# Let's assume a vertical section at lip radius, then fillet to outer.
# Or a direct fillet.
# Given "collar_lip_radius" = 27.08 and "collar_outer_radius" = 36.15.
# Let's place a point at the lip radius at the lip end station?
# Actually, let's use the "transition" parameters to define the fillet.
# "left_collar_base_transition_axial_station": 31.25
# "left_collar_lip_transition_radial_station": 28.08
# "left_collar_outer_transition_axial_station": 35.75
# "left_collar_outer_transition_angle": 135.0

# This suggests a specific transition geometry. 
# Let's define points:
# A: (left_collar_base_radius, left_collar_base_transition_axial_station) = (26.58, 31.25)
# B: (left_collar_lip_transition_radial_station, left_collar_base_transition_axial_station) = (28.08, 31.25) ? No, radial change.
# Let's assume the path is:
# (26.58, 31.25) -> (28.08, 31.25) [Horizontal] -> (28.08, 34.25) [Vertical] -> (36.15, 35.75) [Diagonal/Fillet] -> (36.15, 35.25) [Vertical Down? No, Up]
# Wait, the profile is a half section.
# Let's try to fit the stations to a smooth curve or chain of lines.
# Since I cannot run the solver, I will create a best-effort representation using lines and fillets that match the general shape and dimensions.
# Path:
# 1. Vertical to (26.58, 31.25)
# 2. Horizontal to (28.08, 31.25)
# 3. Vertical to (28.08, 34.25)
# 4. Fillet to (36.15, 35.25) ? 
# Let's just use lines and fillets between the key radii/stations.

# Revised Collar Path:
# 1. (26.58, 31.25)
# 2. (28.08, 31.25)
# 3. (28.08, 34.25)
# 4. (36.15, 34.25)
# 5. (36.15, 35.25)
# Then fillet the corners.

# Let's restart the segment definition to be robust.
# Segment 1: Shaft Shoulder to Collar Base
# P2: (shaft_shoulder_radius, left_shaft_shoulder_axial_station) -> (shaft_shoulder_radius, left_collar_base_transition_axial_station) ?
# No, let's stick to the main stations.
# P2: (shaft_shoulder_radius, left_shaft_shoulder_axial_station)
# P3: (shaft_shoulder_radius, left_collar_base_transition_axial_station)
# P4: (left_collar_base_radius, left_collar_base_transition_axial_station)
# P5: (left_collar_base_radius, left_collar_lip_end_axial_station)
# P6: (left_collar_lip_radius, left_collar_lip_end_axial_station)
# P7: (left_collar_lip_radius, left_collar_outer_transition_axial_station)
# P8: (left_collar_outer_radius, left_collar_outer_transition_axial_station)
# P9: (left_collar_outer_radius, left_collar_outer_axial_station)

# Let's draw these lines:
# (shaft_shoulder_radius, left_shaft_shoulder_axial_station) -> (shaft_shoulder_radius, left_collar_base_transition_axial_station)
# (shaft_shoulder_radius, left_collar_base_transition_axial_station) -> (left_collar_base_radius, left_collar_base_transition_axial_station)
# (left_collar_base_radius, left_collar_base_transition_axial_station) -> (left_collar_base_radius, left_collar_lip_end_axial_station)
# (left_collar_base_radius, left_collar_lip_end_axial_station) -> (left_collar_lip_radius, left_collar_lip_end_axial_station)
# (left_collar_lip_radius, left_collar_lip_end_axial_station) -> (left_collar_lip_radius, left_collar_outer_transition_axial_station)
# (left_collar_lip_radius, left_collar_outer_transition_axial_station) -> (left_collar_outer_radius, left_collar_outer_transition_axial_station)
# (left_collar_outer_radius, left_collar_outer_transition_axial_station) -> (left_collar_outer_radius, left_collar_outer_axial_station)

# This creates a stepped profile. We will fillet the corners later.

# Let's define the points explicitly for the collar section:
# Start from P3 (shaft_shoulder_radius, left_shaft_shoulder_axial_station)
# 1. Down to (shaft_shoulder_radius, left_collar_base_transition_axial_station)
# 2. Right to (left_collar_base_radius, left_collar_base_transition_axial_station)
# 3. Up to (left_collar_base_radius, left_collar_lip_end_axial_station)
# 4. Right to (left_collar_lip_radius, left_collar_lip_end_axial_station)
# 5. Up to (left_collar_lip_radius, left_collar_outer_transition_axial_station)
# 6. Right to (left_collar_outer_radius, left_collar_outer_transition_axial_station)
# 7. Up to (left_collar_outer_radius, left_collar_outer_axial_station)

# Let's execute these segments.
# Note: The previous P2 was (shaft_shoulder_radius, left_shaft_shoulder_axial_station).
# We need to connect to the new path.
# Let's redefine the points list for the whole profile.

profile_points = []

# Left Shaft
profile_points.append(p1) # (shaft_radius, left_axial_tip)
profile_points.append(App.Vector(shaft_radius, left_shaft_shoulder_axial_station))

# Left Shaft Shoulder
profile_points.append(App.Vector(shaft_shoulder_radius, left_shaft_shoulder_axial_station))

# Left Collar Base
profile_points.append(App.Vector(shaft_shoulder_radius, left_collar_base_transition_axial_station))
profile_points.append(App.Vector(left_collar_base_radius, left_collar_base_transition_axial_station))

# Collar Lip
profile_points.append(App.Vector(left_collar_base_radius, left_collar_lip_end_axial_station))
profile_points.append(App.Vector(left_collar_lip_radius, left_collar_lip_end_axial_station))

# Collar Outer
profile_points.append(App.Vector(left_collar_lip_radius, left_collar_outer_transition_axial_station))
profile_points.append(App.Vector(left_collar_outer_radius, left_collar_outer_transition_axial_station))
profile_points.append(App.Vector(left_collar_outer_radius, left_collar_outer_axial_station))

# Left Taper
# From (left_collar_outer_radius, left_collar_outer_axial_station) to (left_taper_start_radius, left_taper_start_axial_station)
# Check consistency: 36.15 -> 36.50, 35.25 -> 35.40. Close enough.
# Let's assume the taper starts at the
