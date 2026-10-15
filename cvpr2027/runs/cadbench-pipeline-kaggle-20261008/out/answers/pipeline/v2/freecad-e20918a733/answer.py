import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# --- Parameters ---
# Gear Geometry
pressure_angle_deg = 20.0
gear_module = 1.0
number_of_teeth = 70
face_width = 6.0
hub_diameter = 18.0
hub_width = 8.0
shaft_diameter = 8.0
overall_width = 14.0

# Calculated Dimensions (ISO 21771)
pressure_angle = math.radians(pressure_angle_deg)
pitch_diameter = gear_module * number_of_teeth
outer_diameter = pitch_diameter + 2 * gear_module
root_diameter = pitch_diameter - 2 * (1.25 * gear_module)
base_diameter = pitch_diameter * math.cos(pressure_angle)
circular_pitch = math.pi * gear_module
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We create a VarSet to hold the named parameters requested in the prompt
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "gear module")
params.gear_module = gear_module
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "face width")
params.face_width = face_width
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "hub diameter")
params.hub_diameter = hub_diameter
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "hub width")
params.hub_width = hub_width
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "shaft diameter")
params.shaft_diameter = shaft_diameter
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "overall width")
params.overall_width = overall_width
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "number of teeth")
params.number_of_teeth = number_of_teeth
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "pressure angle")
params.pressure_angle = pressure_angle_deg

# --- Sketch 1: Gear Tooth Profile ---
# We define the profile on the XY plane. 
# The gear will be extruded along Z.
sketch_gear = body.newObject("Sketcher::SketchObject", "Sketch_GearProfile")
sketch_gear.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_gear.ConstrainToCurrentPlane = True
sketch_gear.Plane = "XY_Plane"

# We will construct the profile using a single closed loop of lines and arcs.
# Coordinate system: Origin at center. X axis points to 0 degrees.
# Pitch Circle Radius (PR) = pitch_diameter / 2
# Base Circle Radius (BR) = base_diameter / 2
# Addendum Circle Radius (AR) = outer_diameter / 2
# Dedendum Circle Radius (DR) = root_diameter / 2

PR = pitch_diameter / 2.0
BR = base_diameter / 2.0
AR = outer_diameter / 2.0
DR = root_diameter / 2.0

# Helper to add geometry
def add_line(p1, p2, is_constraint=False):
    sketch_gear.addGeometry(Part.LineSegment(p1, p2), is_constraint)

def add_circle(center, radius, is_constraint=False):
    sketch_gear.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constraint)

def add_arc(center, radius, start_angle, end_angle, is_constraint=False):
    # FreeCAD Part.Circle expects (center, normal, radius)
    # We create an arc by adding a circle and constraining points, 
    # OR we can use Part.Arc if available, but Sketcher prefers Line/Circle constraints.
    # To keep it robust in headless mode without complex constraint solving for arcs:
    # We will use a sequence of lines and circles to approximate or use Part.Arc directly in geometry.
    # However, Sketcher::SketchObject.addGeometry accepts Part.Arc.
    start_point = App.Vector(center.X + radius * math.cos(math.radians(start_angle)), 
                             center.Y + radius * math.sin(math.radians(start_angle)), 0)
    end_point = App.Vector(center.X + radius * math.cos(math.radians(end_angle)), 
                           center.Y + radius * math.sin(math.radians(end_angle)), 0)
    sketch_gear.addGeometry(Part.Arc(start_point, end_point, center, radius), is_constraint)

# --- Constructing the Tooth Profile ---
# We will draw ONE tooth and use a Polar Pattern later.
# Tooth geometry logic:
# 1. Start at Dedendum Circle (DR) at angle -half_tooth_angle.
# 2. Line to Base Circle (BR) at angle -half_tooth_angle (Root fillet start).
#    Actually, standard spur gear drawing:
#    - Root is arc on DR.
#    - Flank is line tangent to Base Circle.
#    - Tip is arc on AR.
#    - Top is line on AR.
#
# Let's define angles relative to the tooth center line (0 degrees).
# Half tooth angle = 180 / number_of_teeth
half_tooth_angle = 180.0 / number_of_teeth

# Points for the profile (Counter-Clockwise from bottom right of tooth to top right)
# 1. Start at Root (Dedendum Circle) at angle: -half_tooth_angle
p1 = App.Vector(DR * math.cos(math.radians(-half_tooth_angle)), 
                DR * math.sin(math.radians(-half_tooth_angle)), 0)

# 2. Move along Root Circle to angle: +half_tooth_angle
# We add the arc for the root
add_arc(p1, DR, -half_tooth_angle, half_tooth_angle, is_constraint=False)

# 3. Move up the Flank (Tangent to Base Circle)
# The flank is a straight line tangent to the Base Circle.
# The point of tangency is at angle: -half_tooth_angle + pressure_angle
# Wait, the pressure angle is defined at the pitch circle.
# The tangent point on the base circle is at angle: -half_tooth_angle + pressure_angle
# Let's calculate the tangent point.
# The line passes through the origin? No.
# The line is tangent to the base circle.
# The angle of the normal to the tangent line at the point of tangency is the angle of the radius.
# The angle of the radius to the tangent point is: -half_tooth_angle + pressure_angle
tangent_angle = -half_tooth_angle + pressure_angle_deg
tangent_point = App.Vector(BR * math.cos(math.radians(tangent_angle)), 
                            BR * math.sin(math.radians(tangent_angle)), 0)

# The line goes from the root point (p1) to the tangent point? 
# No, the root point is on the dedendum circle. The flank starts at the intersection of the dedendum circle and the tangent line.
# Intersection of Circle(DR) and Line(Tangent).
# This is getting complex for a simple script. 
# Alternative: Use the standard approximation or construct the exact involute.
# For a scriptable solution, we can construct the profile using the known points:
# - Root point (p1)
# - Tangent point on Base Circle (tp)
# - Pitch point (pp)
# - Tip point (tip)
# - Top point (top)
# - Tip point other side (tip2)
# - Root point other side (p2)

# Let's refine the points:
# Angle of the tangent line relative to X axis:
# The tangent line is perpendicular to the radius at tangent_angle.
# So the line angle is tangent_angle + 90.
# We need the intersection of this line with the Dedendum Circle (DR).
# Line equation: (x - tp.x) * cos(tangent_angle) + (y - tp.y) * sin(tangent_angle) = 0
# Circle: x^2 + y^2 = DR^2
# This is solvable, but let's use a simpler geometric construction often used in CAD:
# Define the profile by key points and arcs/lines.

# Key Points:
# A: Root start (-half_tooth_angle)
# B: Root end (+half_tooth_angle)
# C: Tip start (angle corresponding to addendum intersection with tangent)
# D: Tip end
# E: Top left
# F: Top right

# Let's calculate the exact intersection of the tangent line with the Dedendum Circle.
# Tangent Line Vector: (-sin(tangent_angle), cos(tangent_angle))
# Point on line: tp
# Parametric: P = tp + t * (-sin(ta), cos(ta))
# |tp + t*v|^2 = DR^2
# |tp|^2 + 2*t*(tp.v) + t^2 = DR^2
# BR^2 + 2*t*(BR*cos(ta)*(-sin(ta)) + BR*sin(ta)*cos(ta)) + t^2 = DR^2
# BR^2 + 0 + t^2 = DR^2  => t = sqrt(DR^2 - BR^2)
# Since DR > BR, this works.
t_len = math.sqrt(DR**2 - BR**2)
# Direction vector from tp towards the root (inwards)
# The vector (-sin, cos) points "left" of the radius. We need to check direction.
# At -half_tooth_angle + pressure, the radius is in 4th/1st quadrant.
# We want to go towards the center of the tooth (0 deg).
# Let's just compute both intersections and pick the one closer to 0 deg.
v_dir = App.Vector(-math.sin(math.radians(tangent_angle)), math.cos(math.radians(tangent_angle)), 0)
# Check dot product with vector to origin to ensure we go inwards? 
# Actually, we know the geometry. The intersection is at distance t_len from tp.
# There are two intersections. One is the "outer" one (tip side), one is "inner" (root side).
# We want the inner one (root).
# Vector from tp to origin is -tp.
# We want the intersection where the vector from tp points somewhat towards origin.
# Let's try both.
p_root_start = tp + v_dir * t_len
p_root_end = tp - v_dir * t_len

# Determine which is the start (negative angle side) and which is end (positive angle side)
# We defined p1 as the start at -half_tooth_angle.
# Let's just use the calculated points and sort them by angle.
# Actually, let's build the loop:
# 1. Arc on DR from -half_tooth_angle to +half_tooth_angle.
# 2. Line from (+half_tooth_angle, DR) to Tangent Point? No.
# The flank is a straight line. It connects the Root Circle intersection to the Tip Circle intersection.
# Let's find the Tip Circle intersection.
# Same logic, but with AR.
t_len_tip = math.sqrt(AR**2 - BR**2)
p_tip_start = tp + v_dir * t_len_tip
p_tip_end = tp - v_dir * t_len_tip

# Now we have 4 points on the flanks:
# Root Start (RS), Root End (RE)
# Tip Start (TS), Tip End (TE)
# We need to connect them.
# RS is at angle -half_tooth_angle.
# RE is at angle +half_tooth_angle.
# TS is at some angle > -half_tooth_angle.
# TE is at some angle < +half_tooth_angle.
# The profile goes: RS -> Arc(DR) -> RE -> Line(RE, TE) -> Arc(AR) -> TS -> Line(TS, RS).

# Let's verify angles.
# RS angle: -half_tooth_angle
# RE angle: +half_tooth_angle
# TS angle: atan2(p_tip_start.Y, p_tip_start.X)
# TE angle: atan2(p_tip_end.Y, p_tip_end.X)

# We need to ensure we pick the correct intersection points (the ones that form the tooth).
# The tooth is between -half_tooth_angle and +half_tooth_angle.
# The tangent point is at tangent_angle.
# The line goes from TS to TE.
# RS is the intersection of the line (extended) with DR.
# RE is the intersection of the line (extended) with DR.
# Wait, the flank is a single line segment from TS to TE.
# The root is an arc from RS to RE.
# The tip is an arc from TS to TE? No, the tip is an arc on AR.
# The top is a line connecting TS and TE? No, the top is usually flat on AR.
# So:
# 1. Arc on DR from RS to RE.
# 2. Line from RE to TE.
# 3. Arc on AR from TE to TS.
# 4. Line from TS to RS.

# Let's calculate the specific points again carefully.
# Tangent Point (TP) is fixed.
# Line L passes through TP with normal vector (cos(ta), sin(ta)).
# Intersections with Circle(R):
# We found p_root_start and p_root_end.
# Which one is RS? The one with angle -half_tooth_angle.
# Which one is RE? The one with angle +half_tooth_angle.
# Actually, the line intersects the circle at two points. One is "before" the tangent point (towards root), one is "after" (towards tip).
# The "before" point is the Root intersection. The "after" point is the Tip intersection.
# Let's check the parameter t.
# t = +t_len -> p_tip_start (further along the line direction)
# t = -t_len -> p_root_start (backwards along the line direction)
# Wait, t_len was sqrt(AR^2 - BR^2).
# If we move from TP by t_len in direction v_dir, we hit AR.
# If we move by -t_len, we hit DR? No, distances are different.
# Let's re-calculate intersections properly.
# Line: P = TP + u * v_dir
# |P|^2 = R^2
# |TP|^2 + 2*u*(TP.v_dir) + u^2 = R^2
# BR^2 + 0 + u^2 = R^2  => u = +/- sqrt(R^2 - BR^2)
# So for DR: u_dr = +/- sqrt(DR^2 - BR^2)
# For AR: u_ar = +/- sqrt(AR^2 - BR^2)
# The point TP is at u=0.
# The "Root" side is towards the center of the gear (smaller radius).
# The "Tip" side is towards the outside (larger radius).
# Since v_dir is (-sin, cos), let's see where it points.
# ta = -half + pressure.
# If we are at the right side of the tooth (positive angle), the tangent is on the "left" side of the radius vector.
# This is getting confusing. Let's use a robust method:
# Define the profile points explicitly based on angles.
# 1. Root Start: Angle = -half_tooth_angle. Radius = DR.
# 2. Root End: Angle = +half_tooth_angle. Radius = DR.
# 3. Tip Start: Intersection of Line(TP, v_dir) and Circle(AR).
# 4. Tip End: Intersection of Line(TP, -v_dir) and Circle(AR).
# 5. Top Left: Intersection of Line(TP, v_dir) and Circle(AR)? No.
# The top is the segment connecting Tip Start and Tip End on the circle AR.
# The flanks connect Root Start/End to Tip Start/End.
# The flank is the line segment between the intersection with DR and the intersection with AR.
# So:
# - Flank 1: Connects (Intersection of Line1 and DR) to (Intersection of Line1 and AR).
# - Flank 2: Connects (Intersection of Line2 and DR) to (Intersection of Line2 and AR).
# - Root: Arc on DR between the two DR intersections.
# - Tip: Arc on AR between the two AR intersections.

# Let's define the two lines.
# Line 1 (Left Flank): Tangent at angle = -half_tooth_angle + pressure_angle_deg
# Line 2 (Right Flank): Tangent at angle = +half_tooth_angle - pressure_angle_deg
# Wait, the pressure angle is symmetric.
# Left Flank Tangent Angle: -half_tooth_angle + pressure_angle_deg
# Right Flank Tangent Angle: +half_tooth_angle - pressure_angle_deg
# These should be symmetric around 0.
# Let's verify: -h + p vs +h - p. Yes, symmetric.

# Line 1 Tangent Point (TP1):
ta1 = -half_tooth_angle + pressure_angle_deg
TP1 = App.Vector(BR * math.cos(math.radians(ta1)), BR * math.sin(math.radians(ta1)), 0)
# Normal vector (points outwards from center):
n1 = App.Vector(math.cos(math.radians(ta1)), math.sin(math.radians(ta1)), 0)
# Line direction (tangent):
d1 = App.Vector(-math.sin(math.radians(ta1)), math.cos(math.radians(ta1)), 0)

# Line 2 Tangent Point (TP2):
ta2
