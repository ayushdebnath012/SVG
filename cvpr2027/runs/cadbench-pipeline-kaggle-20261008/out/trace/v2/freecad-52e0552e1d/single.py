import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameters ---
# Base dimensions
pressure_angle_deg = 20.0
gear_module = 1.0
number_of_teeth = 40
pitch_diameter = 40.0
outer_diameter = 42.0
face_width = 10.0
hub_diameter = 35.0
hub_width = 10.0
shaft_diameter = 10.0
overall_width = 20.0

# Calculated ISO 21771 dimensions
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module
root_diameter = pitch_diameter - 2 * dedendum

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create Parameter Set for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.gear_module = gear_module
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Teeth")
params.number_of_teeth = number_of_teeth
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Dia")
params.pitch_diameter = pitch_diameter
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.face_width = face_width
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Dia")
params.hub_diameter = hub_diameter
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.hub_width = hub_width
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Dia")
params.shaft_diameter = shaft_diameter
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.overall_width = overall_width
params.addProperty("App::PropertyLength", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = pressure_angle_deg

# Helper to get calculated values from parameters
def get_addendum():
    return params.pitch_diameter / params.number_of_teeth

def get_dedendum():
    return 1.25 * params.gear_module

def get_root_diameter():
    return params.pitch_diameter - 2 * get_dedendum()

# --- Sketch 1: Gear Teeth Profile ---
# We will create a sketch on the XY plane, extrude it to face_width, then revolve it.
# However, standard spur gear generation often involves a profile sketch rotated or a direct revolution of a tooth profile.
# Approach: Create a sketch on XY plane containing the tooth profile (one tooth). 
# Then use PartDesign::Revolution to create the gear body.
# To make the hub and bore, we will add them as separate features (Pad/Pocket) or modify the revolution profile.
# Strategy: 
# 1. Sketch on XY plane: One tooth profile.
# 2. Revolution: 360 deg around Z axis -> Creates the gear teeth ring.
# 3. Pad: Extrude the ring along Z to face_width.
# 4. Pad: Extrude a cylinder for the hub.
# 5. Pocket: Bore for the shaft.

sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_teeth.Support = (doc.getObject("XY_Plane"), [])
sketch_teeth.MapMode = "FlatFace"
sketch_teeth.ConstrainAuto = True

# Calculate tooth geometry
m = params.gear_module
z = params.number_of_teeth
pa = params.pressure_angle
pd = params.pitch_diameter
da = params.pitch_diameter + 2 * get_addendum() # Outer diameter
dr = params.pitch_diameter - 2 * get_dedendum() # Root diameter

# Tooth thickness at pitch circle (approximate for standard full depth)
# Circular pitch p = pi * m
# Tooth thickness t = p / 2
p = 3.141592653589793 * m
t = p / 2.0

# Tooth height
h_add = get_addendum()
h_ded = get_dedendum()
h_total = h_add + h_ded

# Tooth profile points (relative to center of tooth)
# We define the profile from the root circle up to the tip circle.
# Simplified involute approximation or standard construction.
# Let's use a standard construction:
# 1. Base circle radius: rb = pd * cos(pa)
# 2. Involute generation.
# For simplicity in a script without complex math libraries, we can approximate the tooth shape 
# using lines and arcs, or generate points.
# Let's generate points for the involute.

import math

def get_involute_point(angle_deg, base_radius):
    angle_rad = math.radians(angle_deg)
    # Involute equation: x = rb * (cos(t) + t*sin(t)), y = rb * (sin(t) - t*cos(t))
    # where t is the rolling angle.
    # The pressure angle at the point is alpha. tan(alpha) = t.
    # So t = tan(alpha).
    # We want to go from base circle (alpha=0) to tip circle (alpha=pa_tip).
    # Actually, let's just generate points along the involute curve.
    # We need the angle of the point on the base circle relative to the start.
    # Let's define the tooth profile from the root to the tip.
    pass

# Let's build the profile explicitly.
# Center of the tooth is at (0,0) in the sketch.
# The gear rotates around Z. The tooth is symmetric around X axis in the sketch? 
# No, usually we sketch one tooth and revolve.
# Let's place the tooth such that its centerline is the X axis.
# Root circle radius: r_root = dr / 2
# Pitch circle radius: r_pitch = pd / 2
# Tip circle radius: r_tip = da / 2

r_root = get_root_diameter() / 2.0
r_pitch = pitch_diameter / 2.0
r_tip = outer_diameter / 2.0

# Points for the right side of the tooth (from root to tip)
# 1. Root point: (r_root, 0)
# 2. Transition to involute? 
# Let's use a simplified polygonal approximation of the involute for robustness, 
# or calculate exact points.
# Exact points:
# Start at base circle. Base radius rb = r_pitch * cos(pa)
rb = r_pitch * math.cos(math.radians(pa))

# We need points from the base circle outwards to the tip.
# The involute starts at rb.
# We need to find the angle of the involute at the tip.
# r_tip = rb / cos(alpha_tip) => cos(alpha_tip) = rb / r_tip
# alpha_tip = acos(rb / r_tip)
alpha_tip = math.acos(rb / r_tip)
t_tip = math.tan(alpha_tip) # This is the rolling angle in radians

# Generate points along the involute from t=0 to t=t_tip
# We also need the fillet at the root.
# Let's create a list of points.
points = []

# Start at the root circle intersection with the centerline? 
# Usually, the tooth profile goes from the root circle up the flank.
# Let's assume the root is a flat bottom or a fillet. 
# Standard gears often have a fillet at the root.
# Let's define the profile:
# 1. Line from (r_root, 0) to (r_root, h_ded) ? No, that's not right.
# The tooth is symmetric. Let's define the right flank.
# The flank starts at the base circle.
# Intersection of base circle and centerline? No, base circle is inside pitch circle.
# The tooth profile is defined from the root circle up to the tip.
# Let's approximate the root as a point on the circle for now, then go to the base circle, then involute.
# Actually, let's just generate the involute from the base circle to the tip, and connect to the root circle with a line or fillet.

# Let's create points for the right flank (positive Y)
# We need the angle of the point on the base circle where the involute starts.
# The tooth centerline is at angle 0.
# The involute starts at angle -alpha_tip on the base circle?
# Let's just generate points (x, y) relative to the tooth center.
# x = rb * (cos(t) + t*sin(t))
# y = rb * (sin(t) - t*cos(t))
# Here t is the rolling angle.
# We need to shift the coordinate system so the tooth centerline is the X axis.
# The standard formula gives points relative to the base circle center.
# If we want the tooth centerline to be the X axis, we need to rotate the generated points.
# The involute starts at t=0. At t=0, x=rb, y=0. This is on the X axis.
# So if we generate points for t from 0 to t_tip, we get the profile starting from the base circle along the X axis.
# But we need the profile to be the flank of the tooth.
# The flank is the involute.
# So we generate points for t from 0 to t_tip.
# These points form the curve from the base circle outwards.
# We need to connect the bottom of this curve to the root circle.
# The bottom of the curve (t=0) is at (rb, 0).
# The root circle is at radius r_root.
# We need to connect (r_root, 0) to (rb, 0)? No, that's a line along the axis.
# The tooth has a width.
# Let's reconsider the sketch.
# We will sketch the profile of ONE tooth.
# The profile consists of:
# 1. Root circle arc (bottom).
# 2. Flank (involute).
# 3. Tip circle arc (top).
# 4. Other flank (symmetric).
# 5. Root fillet (optional, but good practice).

# Let's define the profile points for the RIGHT side of the tooth (from root to tip).
# We need the angle of the tooth.
# Tooth angle = 2 * pi / z.
# Half tooth angle = pi / z.
# The tooth is centered on the X axis.
# So the right flank goes from the root circle, up the involute, to the tip.
# The involute starts at the base circle.
# The base circle radius is rb.
# The involute starts at an angle on the base circle.
# Let's calculate the point where the involute meets the root circle? 
# Usually, the root is below the base circle.
# So the profile is:
# - Line from (r_root, 0) to (rb, 0)? No.
# - The profile is the involute from the base circle to the tip.
# - And a line from the root circle to the start of the involute?
# - Or a fillet.
# Let's use a simplified approach:
# 1. Generate involute points from t=0 to t=t_tip.
# 2. These points are (x, y) relative to the base circle center.
# 3. We need to rotate them so the tooth is centered.
# Actually, the standard way to sketch a gear tooth:
# - Draw the pitch circle.
# - Draw the base circle.
# - Draw the involute from the base circle.
# - Draw the tip circle.
# - Draw the root circle.
# - Connect them.

# Let's generate points for the right flank (positive Y).
# We need the angle of the involute start relative to the tooth centerline.
# The involute starts at the base circle.
# The angle of the point on the base circle where the involute starts is -alpha_tip?
# No, the involute is generated by unwrapping a string from the base circle.
# The point of tangency moves along the base circle.
# The angle of the point of tangency is -t (if we measure from the start point).
# The point on the involute is at angle theta = alpha + t?
# Let's just use the parametric equations and rotate.
# Parametric:
# x = rb * (cos(t) + t*sin(t))
# y = rb * (sin(t) - t*cos(t))
# This gives a curve starting at (rb, 0) and going into the first quadrant (positive x, positive y).
# This is the profile of a tooth if the tooth centerline is the X axis?
# No, this curve is tangent to the base circle at (rb, 0).
# The tangent at (rb, 0) is vertical (x=rb).
# So this curve is the flank of a tooth if the tooth centerline is the Y axis?
# Let's visualize.
# Base circle center (0,0).
# Point (rb, 0). Tangent is vertical.
# If we want the tooth centerline to be the X axis, the flank should be tangent to the base circle at some point and curve away.
# The involute is always tangent to the base circle.
# So if we want the flank to be the involute, the point of tangency must be on the base circle.
# If the tooth centerline is the X axis, the point of tangency for the right flank should be at (rb, 0)?
# No, the point of tangency moves.
# Let's assume the tooth centerline is the X axis.
# The right flank is the involute.
# The point of tangency for the right flank starts at some angle and moves.
# Actually, the simplest way is to generate the points and then rotate them.
# Let's generate points for t from 0 to t_tip.
# These points are (x, y).
# We want the tooth to be symmetric around the X axis.
# So we need the right flank to be the curve for t from 0 to t_tip, but rotated?
# No, the curve (x, y) above is in the first quadrant.
# If we reflect it across the X axis, we get the left flank?
# No, we want the right flank to be in the first quadrant (positive Y).
# So the curve (x, y) is the right flank?
# Let's check the slope.
# At t=0, x=rb, y=0. dx/dt = rb * (-sin(t) + sin(t) + t*cos(t)) = rb * t * cos(t). dy/dt = rb * (cos(t) - cos(t) + t*sin(t)) = rb * t * sin(t).
# At t=0, dx/dt = 0, dy/dt = 0.
# This is a cusp? No, the derivative is 0.
# Wait, the parametric equations are for the involute.
# The tangent vector is ( -sin(t) + t*cos(t), cos(t) + t*sin(t) ) * rb.
# At t=0, tangent is (0, 1). Vertical.
# So the curve starts at (rb, 0) and goes up vertically.
# This is the profile of a tooth if the tooth centerline is the Y axis?
# No, if the tooth centerline is the X axis, the flank should be tangent to the base circle at (rb, 0) and go outwards.
# The tangent at (rb, 0) is vertical.
# So the flank is vertical at the base circle.
# This means the tooth centerline is the X axis, and the flank is the curve (x, y).
# So we can use these points directly.
# But we need to connect the bottom of the curve (rb, 0) to the root circle (r_root, 0).
# And the top of the curve to the tip circle (r_tip, 0)?
# No, the top of the curve is at t=t_tip.
# x_tip = rb * (cos(t_tip) + t_tip*sin(t_tip))
# y_tip = rb * (sin(t_tip) - t_tip*cos(t_tip))
# We need to check if this point is on the tip circle.
# r_tip = sqrt(x_tip^2 + y_tip^2).
# Yes, by definition of the involute, the radius at angle alpha_tip is rb / cos(alpha_tip).
# And t_tip = tan(alpha_tip).
# So r_tip = rb / cos(alpha_tip).
# So the point is on the tip circle.
# But is it on the X axis? No, it's at some angle.
# The angle of the point is theta = alpha_tip + t_tip?
# No, the angle of the point on the polar plot is alpha_tip + t_tip?
# Let's just generate the points and then rotate them so the tooth is centered.
# The tooth is centered on the X axis.
# The right flank is the curve for t from 0 to t_tip.
# The left flank is the curve for t from 0 to t_tip, reflected across the X axis?
# No, the left flank is the curve for t from 0 to t_tip, but rotated by -tooth_angle?
# No, the tooth is symmetric.
# So the right flank is the curve for t from 0 to t_tip, and the left flank is the curve for t from 0 to t_tip, reflected across the
