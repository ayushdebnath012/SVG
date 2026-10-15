import os
from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# Initialize document
doc = App.newDocument("GearDesign")

# --- 1. Parameters ---
# We create a VarSet to hold the named parameters driven by the task description.
params = doc.addObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Diameter")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "Pressure Angle")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")

# --- Set Values based on Task ---
params.gear_module = 1.0
params.face_width = 10.0
params.hub_diameter = 20.0
params.hub_width = 10.0
params.shaft_diameter = 8.0
params.overall_width = 20.0
params.pressure_angle_deg = 20.0
params.number_of_teeth = 24

# --- Compute Derived Dimensions ---
# Addendum and Dedendum (ISO/DIN)
params.addProperty("App::PropertyLength", "addendum", "Computed", "Addendum")
params.addProperty("App::PropertyLength", "dedendum", "Computed", "Dedendum")
params.addProperty("App::PropertyLength", "whole_depth", "Computed", "Whole Depth")
params.addProperty("App::PropertyLength", "pitch_diameter", "Computed", "Pitch Diameter")
params.addProperty("App::PropertyLength", "outer_diameter", "Computed", "Outer Diameter")
params.addProperty("App::PropertyLength", "root_diameter", "Computed", "Root Diameter")
params.addProperty("App::PropertyLength", "base_diameter", "Computed", "Base Diameter")
params.addProperty("App::PropertyLength", "circular_pitch", "Computed", "Circular Pitch")

# Set Expressions for Derived Values
# addendum = module
params.addProperty("App::PropertyExpression", "addendum_expr", "Computed")
params.addExpression("addendum_expr", "gear_module")

# dedendum = 1.25 * module
params.addProperty("App::PropertyExpression", "dedendum_expr", "Computed")
params.addExpression("dedendum_expr", "1.25 * gear_module")

# whole_depth = addendum + dedendum
params.addProperty("App::PropertyExpression", "whole_depth_expr", "Computed")
params.addExpression("whole_depth_expr", "addendum + dedendum")

# pitch_diameter = module * teeth
params.addProperty("App::PropertyExpression", "pitch_diameter_expr", "Computed")
params.addExpression("pitch_diameter_expr", "gear_module * number_of_teeth")

# outer_diameter = module * (teeth + 2)
params.addProperty("App::PropertyExpression", "outer_diameter_expr", "Computed")
params.addExpression("outer_diameter_expr", "gear_module * (number_of_teeth + 2)")

# root_diameter = pitch_diameter - 2 * dedendum
params.addProperty("App::PropertyExpression", "root_diameter_expr", "Computed")
params.addExpression("root_diameter_expr", "pitch_diameter - 2 * dedendum")

# base_diameter = pitch_diameter * cos(pressure_angle)
params.addProperty("App::PropertyExpression", "base_diameter_expr", "Computed")
params.addExpression("base_diameter_expr", "pitch_diameter * cos(radians(pressure_angle_deg))")

# circular_pitch = pi * module
params.addProperty("App::PropertyExpression", "circular_pitch_expr", "Computed")
params.addExpression("circular_pitch_expr", "pi * gear_module")

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject(body)

# --- Planes ---
# Create XY, XZ, YZ planes manually if not default, but PartDesign usually handles them.
# Let's explicitly create them to be safe and name them.
plane_XY = doc.addObject("PartDesign::Plane", "Plane_XY")
plane_XY.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
plane_XY.Placement.rotate((0, 0, 1), 0) # Normal Z
body.addObject(plane_XY)

plane_XZ = doc.addObject("PartDesign::Plane", "Plane_XZ")
plane_XZ.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
plane_XZ.Placement.rotate((0, 1, 0), 0) # Normal Y
body.addObject(plane_XZ)

plane_YZ = doc.addObject("PartDesign::Plane", "Plane_YZ")
plane_YZ.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
plane_YZ.Placement.rotate((1, 0, 0), 0) # Normal X
body.addObject(plane_YZ)

# Create Axes
axis_Z = doc.addObject("PartDesign::Axis", "Axis_Z")
axis_Z.Placement = App.Placement(App.Vector(0, 0, 0))
body.addObject(axis_Z)

axis_X = doc.addObject("PartDesign::Axis", "Axis_X")
axis_X.Placement = App.Placement(App.Vector(0, 0, 0))
axis_X.Placement.rotate((0, 0, 1), 90) # X axis is rotated 90 deg from Z in XY plane? No, X is (1,0,0).
# In FreeCAD default coordinates: X=(1,0,0), Y=(0,1,0), Z=(0,0,1).
# We need an axis vector.
axis_X.Placement.rotate((0, 0, 1), 0) # Keep it simple, just reference the object
# Actually, let's just use standard XY plane for the main sketch.

# --- Base Sketch (Teeth Profile) ---
# Sketch on XY plane
sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_TeethProfile")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_teeth.Placement.rotate((0, 0, 1), 0) # Ensure normal is Z
sketch_teeth.Constraints = [] # Clear default constraints to avoid conflicts
sketch_teeth.BaseConstraint = "Plane"
sketch_teeth.Plane = "Plane_XY"

# Gear Geometry Calculations for Sketch
m = params.gear_module.value
z = params.number_of_teeth.value
pa_deg = params.pressure_angle_deg.value
pa_rad = math.radians(pa_deg)

# Pitch Radius
r_pitch = m * z / 2.0
# Outer Radius
r_outer = m * (z / 2.0 + 1)
# Root Radius
r_root = r_pitch - 1.25 * m
# Base Radius
r_base = r_pitch * math.cos(pa_rad)

# Pitch Circle Point
P = App.Vector(r_pitch, 0, 0)
# Tangent at Pitch Circle (Vertical line at pitch circle)
TangentLine = Part.LineSegment(P, App.Vector(P.x, P.y + 1000, 0))

# Base Circle (Arc)
BaseCircle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_base)

# Outer Circle
OuterCircle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_outer)

# Root Circle
RootCircle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_root)

# Start Angle for Involute
# We need to generate involute points. 
# t = sqrt((pi*2*z/360 + 0.6366*pa_deg)^2) is not quite right.
# Simple parametric generation of involute:
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# where t is the angle of the tangent relative to the radius.

def get_involute_point(t):
    # t is the angle in radians
    x = r_base * (math.cos(t) + t * math.sin(t))
    y = r_base * (math.sin(t) - t * math.cos(t))
    return App.Vector(x, y, 0)

# Calculate max t for root circle
# r_root^2 = r_base^2 * (1 + t^2)^2  => sqrt(r_root/r_base) = 1 + t^2 => t = sqrt(sqrt(r_root/r_base) - 1)
t_max = math.sqrt(math.sqrt(r_root / r_base) - 1)
t_start = 0

# Generate points for involute curve (one tooth flank)
# We need the flank from Base Circle to Root Circle.
# Then tangent at pitch circle to connect to top.
# Then top to Outer Circle.
# Then symmetrical.

# Point A: Start of involute on base circle (t=0)
P_base = get_involute_point(t_start)
# Point B: End of involute on root circle (t_max)
P_root = get_involute_point(t_max)

# Point C: Tangent at pitch circle
# The tangent line is perpendicular to the radius at the pitch circle? No.
# The tangent to the involute at the pitch circle makes an angle equal to pressure angle with the tangent to the pitch circle.
# Actually, the common tangent between the base circle and the line of action is the pressure angle.
# The involute intersects the pitch circle at a specific angle.
# Let's calculate the intersection of the involute with the pitch circle.
# r_pitch = r_base * sqrt(1 + t_pitch^2) -> t_pitch = sqrt((r_pitch/r_base)^2 - 1)
t_pitch = math.sqrt((r_pitch / r_base)**2 - 1)
P_pitch = get_involute_point(t_pitch)

# Now we have the shape of one tooth flank: BaseCircle -> Involute -> PitchCircleTangent -> OuterCircle -> ...
# But constructing the exact involute geometry in sketcher constraints is hard.
# We will construct the profile using lines and arcs that approximate or define the geometry precisely.
# 1. Base Circle Arc
# 2. Line from Base Circle to Pitch Circle (Involute segment) - Hard to constrain exactly to involute without curve.
#    However, for a standard gear sketch, we often draw the Base Circle, then the tangent lines.
#    The involute is the envelope of these tangents.
#    Standard parametric sketching: Draw the tangent lines at specific angles.
#    Let's use the tangent line at the pitch circle and the tangent line at the base circle (radius).
#    Actually, the most robust way for a script is to create the involute points and create a spline, 
#    OR construct the geometry using the tangent at the pitch circle and the base circle.
#    
#    Let's build the profile using:
#    1. Base Circle (Arc)
#    2. Tangent line at the base circle (radius) -> No, the involute starts at base circle.
#    3. Line segment from Base Circle tangent point to Pitch Circle tangent point? No.
#    
#    Alternative: Create the "Tooth Profile" as a closed loop.
#    We will construct the profile from the Base Circle tangent point to the Root Circle.
#    Since FreeCAD sketcher doesn't have a direct "Involute" constraint, we approximate using a spline or construct the exact points.
#    Let's use the exact points and a B-Spline for the flank.
    
# Points for Left Flank (Counter-Clockwise)
# 1. Start at Base Circle tangent point? No, involute starts at base circle.
#    Let's define the tooth centerline as X axis.
#    Tooth 1 center is at (r_pitch, 0).
#    We need the profile from the gap to the tip.
#    Gap (root) diameter is 2*r_root.
#    Tooth width at pitch circle = pi * m / z.
    
    # Let's define the critical points for one tooth (Right side of centerline, Left side of centerline)
    # Centerline of tooth is at angle 0.
    # Angle between teeth = 360/z.
    # Half angle = 180/z.
    
    half_angle = math.radians(180 / z)
    
    # Point 1: Intersection of Base Circle and Tooth Flank (Start of involute)
    # This is at t=0 relative to the tooth center? No.
    # The involute starts at the base circle.
    # The angle of the tooth centerline relative to the base circle tangent is not simply related.
    
    # Let's generate the profile points for one tooth flank starting from the root.
    # We need the involute curve.
    # Let's create a curve from the root intersection to the tip.
    
    # Point A: Root intersection. 
    # The root circle intersects the involute at t_max.
    # We need the angle of this point.
    # The angle of the involute point (phi) = t + alpha, where alpha is pressure angle?
    # phi = t + atan(t). (Where t is the parameter).
    # At t=0, phi=0. So the base circle point is at angle 0 relative to the reference line.
    # But our tooth center is at angle 0.
    # So the start of the involute is at angle 0?
    # No. The base circle is inside. The tooth center is outside.
    # The involute wraps around the base circle.
    # If we place the tooth center at (r_pitch, 0), the base circle point corresponding to the start of the involute on the "top" of the tooth is at angle 0?
    # Yes, if we define the coordinate system such that the radius to the tooth center is the X-axis.
    # So BaseCircle point is (r_base, 0).
    # The involute goes "inwards" or "outwards"? It goes from base circle (r_base) to tip (r_outer).
    # The parameter t goes from 0 to t_max (for root) and t_pitch (for pitch) to t_tip (for outer).
    
    # Let's calculate the points for the Right Flank (from root to tip, moving away from centerline)
    # Actually, usually we sketch one half and mirror, or the full profile.
    # Let's sketch the Right Flank (from root to tip) and Left Flank.
    
    # Flank points (Right side, moving away from centerline)
    # Start at Root: t_root = t_max. 
    # End at Tip: t_tip = sqrt((r_outer/r_base)^2 - 1)
    
    # We need the angle for each point.
    # Angle of involute point = t + atan(t).
    
    # Let's generate points for the Right Flank (from root to tip)
    # We need to ensure we cover the range from root to tip.
    # t ranges from t_max (root) to t_tip (tip).
    
    # Let's generate 10 points for the flank.
    flank_points = []
    t_vals = [t_max + (t_tip - t_max) * i / 10 for i in range(11)]
    for t in t_vals:
        ang = t + math.atan(t)
        r = r_base * math.sqrt(1 + t**2)
        x = r * math.cos(ang)
        y = r * math.sin(ang)
        flank_points.append(App.Vector(x, y, 0))
        
    # Note: The first point (t_max) is on the root circle.
    # The last point (t_tip) is on the outer circle.
    
    # Now we need the Top of the tooth.
    # From the tip of the flank, go horizontally to the other flank?
    # No, the top is an arc (Outer Circle) or a flat (for some gears).
    # Problem says "spur gear", usually implies filleted top or flat top.
    # Given "outer_diameter", let's assume a flat tip for simplicity unless specified, 
    # but ISO gears often have a fillet. 
    # However, to make it a valid single solid with simple features, a flat top (Outer Circle arc) is safer.
    # We will connect the tip of the flank to the other flank via the Outer Circle arc.
    
    # Mirror the points for the Left Flank (around X axis)
    left_flank_points = [App.Vector(p.x, -p.y, 0) for p in flank_points]
    
    # Close the loop:
    # Start at Left Tip, go to Left Root, go to Center Root? No.
    # The profile is: Left Flank -> Root Circle Arc -> Right Flank -> Outer Circle Arc -> Left Flank?
    # No, the Root Circle is inside. The
