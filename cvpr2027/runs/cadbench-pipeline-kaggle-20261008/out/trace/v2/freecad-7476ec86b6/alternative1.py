import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("GearStock")

# --- Parameters ---
# Define parameters as document variables to keep them editable
params = doc.addObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of teeth")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module (m)")
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face width")
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure angle (deg)")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter")

params.number_of_teeth = 20
params.gear_module = 25.4 / 32.0 # mm
params.face_width = 304.8        # mm
params.pressure_angle = 20.0     # degrees
params.outer_diameter = 17.526   # mm

# Derived dimensions based on standard spur gear geometry
# Diametral Pitch (DP) = 1 / Module
# Pitch Diameter (Dp) = Number of Teeth (N) / DP = N * Module
# Outer Diameter (Do) = Dp + 2 * Module (Standard full depth teeth)
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Calculated Pitch Diameter")
params.pitch_diameter = params.number_of_teeth * params.gear_module

# Create the Body
body = doc.addObject("PartDesign::Body", "GearBody")

# --- Base Cylinder (Blank Stock) ---
# We will create a large cylinder first to act as the "stock" which is then cut or trimmed.
# However, the prompt asks for "spur gear stock ... cylindrical gear body with external involute gear teeth".
# Usually, this implies the final shape is the gear itself. 
# To make it parametric and robust, we build the involute profile and pad it.
# The "stock" description with a 1ft face width suggests a very wide gear blank.

# 1. Create Sketch for the Involute Tooth Profile
sketch_profile = body.newObject("Sketcher::SketchObject", "GearProfileSketch")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.ConstrainToCurrentPlane = True
# Attach to XY plane (Standard is usually XY, but we need to ensure we are on a known plane)
# In FreeCAD 1.1, standard planes are often accessible. Let's use XY.
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0)) 
# Actually, let's explicitly attach to the XY plane of the body's coordinate system if possible,
# or just assume standard XY at origin for the first sketch.
# To be safe and explicit:
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# Add Circle for Pitch Circle (Center of gear)
# Radius = Pitch Diameter / 2
pitch_radius = params.pitch_diameter / 2.0
sketch_profile.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), pitch_radius), False)

# Add Circle for Outer Diameter Circle
outer_radius = params.outer_diameter / 2.0
sketch_profile.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), outer_radius), False)

# Add Line for Base Diameter (for involute generation reference)
# Base Diameter = Pitch Diameter * Cos(Pressure Angle)
base_radius = pitch_radius * (App.Quantity(params.pressure_angle).toDegrees()) # Wait, App.Quantity is for units, need math.cos
import math
base_radius = pitch_radius * math.cos(math.radians(params.pressure_angle.value))
sketch_profile.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), base_radius), False)

# --- Involute Tooth Generation ---
# Since FreeCAD PartDesign doesn't have a native "Gear Generator" feature that creates the involute curve directly 
# from a sketch constraint in a simple way, we will generate the geometry points and create a closed loop sketch.
# We will create a series of LineSegments and Arcs to form one tooth profile, then pattern it.

def generate_involute_points(base_r, face_angle_deg, steps=100):
    """Generates points along an involute curve."""
    points = []
    angle_rad = 0
    # We need to generate points from the Base Circle out to the Outer Circle
    # Involute equation: x = r_base * (cos(theta) + theta*sin(theta))
    #                      y = r_base * (sin(theta) - theta*cos(theta))
    # theta is the angle of unwrapping.
    # r = r_base * sqrt(1 + theta^2)
    # We need r to go from base_r to outer_radius.
    # Let's iterate theta until r >= outer_radius.
    
    theta = 0
    step = 0.001
    max_theta = 10.0 # Safety break
    
    current_r = base_r
    while current_r < outer_radius and theta < max_theta:
        theta += step
        r = base_r * math.sqrt(1 + theta**2)
        if r > outer_radius:
            r = outer_radius
            theta = math.sqrt((r/base_r)**2 - 1)
        
        x = r * (math.cos(theta) + theta * math.sin(theta))
        y = r * (math.sin(theta) - theta * math.cos(theta))
        points.append(App.Vector(x, y, 0))
        
        if r >= outer_radius:
            break
            
    return points

# Generate one full tooth profile
# Tooth thickness at pitch circle = Pi * Module / 2 (Standard)
# Tooth space at pitch circle = Pi * Module / 2
# Angle subtended by one tooth at pitch circle = 360 / N
# Half angle = 180 / N
half_tooth_angle_deg = 180.0 / params.number_of_teeth.value
full_tooth_angle_deg = 2 * half_tooth_angle_deg

# We need to construct the profile starting from the valley (root), going up the flank, over the top, and down.
# However, generating the exact involute from the base circle to the outer circle for a specific tooth position is complex 
# to do purely with lines in a sketch without a CAD kernel native command.
# 
# Alternative Approach for FreeCAD 1.1 Scripting:
# Use a "Gear" object? No, must be PartDesign features.
# We can approximate the involute using a spline or many small line segments.
# Given the constraints, we will generate a spline representing one tooth flank from the base circle to the outer circle.
# Then we will create a closed loop: Outer Arc -> Flank 2 -> Base -> Flank 1 -> Outer Arc (start).

# Let's refine the profile construction:
# 1. Start at the intersection of the Base Circle and the flank line (angle - half_tooth_angle).
#    Actually, involutes start at the base circle.
# 2. Generate points for the flank from Base Circle to Outer Circle.
# 3. Generate points for the opposite flank.
# 4. Close the loop.

# Let's create the points for ONE side of a tooth.
# The tooth is centered at angle 0.
# The flank starts at angle: -half_tooth_angle - (addendum angle correction)
# But for simplicity in a script without a dedicated gear module, we will use the standard approach:
# Generate the involute curve for the full rotation, then slice it.
# OR: Generate the specific points for one tooth.

# Let's use the method of generating the involute curve and then extracting the segment.
# Tooth thickness at pitch circle = Pi * M / 2.
# Arc length at pitch circle = Radius * Angle.
# Angle subtended by half tooth at pitch circle = (Pi * M / 2) / PitchRadius = (Pi/2) / (N*M) * (1/M) ? 
# No. Arc = R * theta. Theta = Arc / R = (Pi * M / 2) / (N * M / 2) = Pi / N.
# So half tooth angle at pitch circle = 180 / N degrees. Correct.

# The involute profile starts at the base circle.
# We need to find the angle of the involute at the base circle relative to the tooth center.
# This requires solving the involute angle equation.
# Let's simplify: We will generate a spline from the Base Circle point to the Outer Circle point.
# We define the start point on the Base Circle at angle (180/N + addendum_angle_correction).
# And end point at Outer Circle.

# Actually, the most robust way in a script without external libraries is to generate the full involute 
# for one sector and then create the sketch geometry.
# But to keep it "script-only" and fast, let's generate the points for one tooth profile directly.

# Parameters for one tooth
N = params.number_of_teeth.value
M = params.gear_module.value
PA = math.radians(params.pressure_angle.value)
Pd = N * M
Od = Pd + 2 * M # Approximation, prompt gave specific Od, let's use prompt's Od but adjust profile to fit.
# Prompt says: outer_diameter = 17.526 mm. 
# Calculated: Pd + 2M = 15.875 + 2*0.79375 = 17.4625 mm.
# There is a slight discrepancy (17.526 vs 17.4625). We will use the Prompt's Outer Diameter as the limit.
# The involute will extend to this radius.

BaseRadius = Pd * math.cos(PA)
PitchRadius = Pd / 2.0
OuterRadius = params.outer_diameter / 2.0

# Generate involute points for the full circle to define the curve mathematically
# We need to generate points for the angle range corresponding to one tooth.
# Let's generate a dense set of points for the involute curve and then filter/select the relevant segment.
# We will generate points for a full revolution of the involute generation parameter (theta).
# Then we will rotate them to align with the tooth position.

def get_involute_point(theta):
    r = BaseRadius * math.sqrt(1 + theta**2)
    if r > OuterRadius:
        r = OuterRadius
        theta = math.sqrt((r/BaseRadius)**2 - 1)
    
    x = r * (math.cos(theta) + theta * math.sin(theta))
    y = r * (math.sin(theta) - theta * math.cos(theta))
    return App.Vector(x, y, 0)

# We need to determine the range of theta for one tooth.
# The tooth starts at the base circle (theta=0 relative to the tooth center? No, theta=0 is the start of the involute).
# The tooth is centered.
# Let's calculate the "involute angle" (theta) for the outer radius.
theta_max = math.sqrt((OuterRadius/BaseRadius)**2 - 1)

# Tooth geometry:
# Angle between tooth center and the start of the involute (where it leaves the base circle) depends on the tooth thickness.
# Let's approximate the tooth profile by generating the involute curve for the full extent and then placing it.
# Actually, simpler: Create a spline that follows the involute equation.
# We need the starting angle of the tooth center.
# Angle between tooth center and the point where the involute starts (Base Circle) is:
# alpha_start = (angle subtended by half tooth at pitch circle) + (angle correction for base circle)
# alpha_pitch = math.pi / N
# alpha_base = ... this is complex to derive exactly without iterative solving in a script.
# 
# Heuristic: 
# The tooth occupies an angle of 2 * alpha_pitch at the pitch circle.
# The involute curve starts at Base Circle.
# Let's generate points for the involute from theta=0 to theta_max.
# Then we rotate this curve so that the "middle" of the curve (at Pitch Radius) aligns with angle 0.
# Then we reflect one side and connect.

# Generate points for one flank from Base to Outer
theta_vals = []
r_vals = []
x_vals = []
y_vals = []
step = 0.001
current_theta = 0.0
while current_theta <= theta_max + 0.01:
    theta_vals.append(current_theta)
    r = BaseRadius * math.sqrt(1 + current_theta**2)
    if r > OuterRadius: r = OuterRadius
    current_theta = math.sqrt((r/BaseRadius)**2 - 1)
    r_vals.append(r)
    x_vals.append(r * (math.cos(current_theta) + current_theta * math.sin(current_theta)))
    y_vals.append(r * (math.sin(current_theta) - current_theta * math.cos(current_theta)))
    current_theta += step

# Now we have a list of points for a curve starting at Base Circle and ending at Outer Circle.
# We need to position this curve.
# The "start" of our list is at Base Circle (theta=0).
# The "end" is at Outer Circle.
# We need to find the rotation angle that places the midpoint of the arc at the Pitch Circle at Angle 0.
# But our list is linear in theta, not arc length.
# Let's just pick the point where r = PitchRadius.
target_r = PitchRadius
# Interpolate to find theta_target
theta_target = math.sqrt((target_r/BaseRadius)**2 - 1)
idx_target = theta_vals.index(theta_target) # This is approximate due to step, but close enough
# Actually, let's just use the calculated theta_target directly for rotation logic.

# The point at theta_target in our list corresponds to the Pitch Circle.
# Its coordinates in local space are (0,0) rotated? No.
# At theta_target, the point is at distance PitchRadius.
# Its angle in the local coordinate system of the generated curve is 0 (because we built it from scratch).
# Wait, the involute equation generates points relative to the Base Circle center.
# The angle of the point (x,y) relative to the x-axis is: phi = atan2(y, x).
# For the involute generation, the parameter 'theta' is the angle of the tangent point on the base circle.
# The angle of the point itself is phi = theta + atan(theta).
# Let's verify:
# x = r(cos(theta) + theta sin(theta))
# y = r(sin(theta) - theta cos(theta))
# tan(phi) = y/x = (sin - th cos) / (cos + th sin) = tan(alpha - th) where alpha = atan(1/th)? No.
# It is known that phi = theta + atan(theta).
# So the angle of the point relative to the X-axis is theta + atan(theta).

# We want the tooth to be symmetric around Y-axis (in our sketch) or X-axis?
# Let's place the tooth center at Y-axis (Angle 90 deg) or X-axis?
# Standard is usually X-axis. Let's place the tooth center at Angle 0 (X-axis).
# The profile is symmetric around the X-axis.
# So we need the point at Pitch Radius to be at (PitchRadius, 0).
# Our generated points are at angle phi = theta + atan(theta).
# We need to rotate the generated curve by -phi_target so that this point lands on the X-axis.

# Let's create the profile for one half-tooth (from Base to Outer).
# We will create two segments:
# 1. From Base (theta=0) to Pitch (theta_target).
# 2. From Pitch (theta_target) to Outer (theta_max).
# Actually, we need the full tooth.
# The tooth consists of:
# - Flank 1 (Outer to Pitch to Base)
# - Valley (Arc at Base Radius)
# - Flank 2 (Base to Pitch to Outer)
# - Top (Arc at Outer Radius)

# Let's generate the points for the full curve (theta=0 to theta_max) and rotate it.
# Then we will duplicate and flip to make the second flank.
# But wait, the involute is continuous.
# We need the profile of ONE tooth.
# The tooth starts at some angle, goes up the flank, over the top, down the other flank.
# The "start" of the involute generation (theta=0) is on the Base Circle.
# This point corresponds to the beginning of the tooth space or the beginning of the tooth?
# The involute starts at the base circle. The tooth profile exists from Base to Outer.
# So the flank starts at Base Circle.
# The angle of this start point relative to the tooth center line is:
# alpha_start = alpha_pitch + alpha_addendum_correction.
# Since we are generating the curve from theta=0 (Base) to theta_max (Outer),
# and we want the tooth center to be at Angle 0,
# we need to rotate the curve such that the point at theta=0 is at Angle -(alpha_pitch + correction).
# And the point at theta=0 (on the other side) is at +(alpha_pitch + correction).

# Let's simplify. We will generate the curve for theta in [0, theta_max].
# We will calculate the angle of the point at theta=0. It is 0.
# We will calculate the angle of the point at theta=theta_max.
# We need to rotate the whole curve by an offset so that the midpoint of the tooth is at 0.
# The midpoint of the tooth is at Pitch Radius.
# The angle of the point at theta_target is phi_target = theta_target + atan(theta_target).
# We want this point to be at Angle 0.
# So we rotate by -phi_target.
# The point at theta=
