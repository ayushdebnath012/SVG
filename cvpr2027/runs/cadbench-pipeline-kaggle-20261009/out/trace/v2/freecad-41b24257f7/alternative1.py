"""
FreeCAD 1.1 Script: Parametric Spur Gear Generator
Generates a spur gear with involute teeth, hub, and bore.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Draft
import Math
from math import cos, sin, pi, sqrt, atan2, radians, degrees

# -----------------------------------------------------------------------------
# 1. Configuration & Derived Parameters
# -----------------------------------------------------------------------------
# User Inputs
P = 20.0          # Pressure Angle [degrees]
m = 2.0           # Module [mm]
z = 24            # Number of Teeth
b = 20.0          # Face Width [mm]
d_hub = 38.0      # Hub Outer Diameter [mm]
b_hub = 10.0      # Hub Width [mm]
d_shaft = 10.0    # Bore Diameter [mm]
w_total = 30.0    # Overall Width [mm]

# Derived Parameters (ISO Standards based on prompt)
pressure_angle_rad = radians(P)
pitch_diameter = m * z
outer_diameter = (m * z) + (2 * m) # Pitch + 2*Addendum
root_diameter = (m * z) - (2.5 * m) # Pitch - 2*Dedendum
base_diameter = pitch_diameter * cos(pressure_angle_rad)
circular_pitch = pi * m
tooth_thickness = circular_pitch / 2
addendum = m
dedendum = 1.25 * m
whole_depth = addendum + dedendum

# -----------------------------------------------------------------------------
# 2. Document Setup
# -----------------------------------------------------------------------------
doc = App.newDocument("SpurGear")

# Create standard XY, XZ, YZ planes
XY_Plane = doc.addObject("Part::Plane", "XY_Plane")
XY_Plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
XZ_Plane = doc.addObject("Part::Plane", "XZ_Plane")
XZ_Plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(90, 0, 0))
YZ_Plane = doc.addObject("Part::Plane", "YZ_Plane")
YZ_Plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 90, 0))
# Create Axes for easy reference
X_Axis = doc.addObject("Part::Line", "X_Axis")
X_Axis.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0))
X_Axis.Line = App.Vector(1, 0, 0)
Z_Axis = doc.addObject("Part::Line", "Z_Axis")
Z_Axis.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0))
Z_Axis.Line = App.Vector(0, 0, 1)

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))

# Add parameters to Body for editing
params = body.newObject("App::Property", "Parameters")
params.addProperty("App::PropertyInteger", "z", "Parameters", "Number of Teeth")
params.z = z
params.addProperty("App::PropertyLength", "m", "Parameters", "Module")
params.m = m
params.addProperty("App::PropertyLength", "b", "Parameters", "Face Width")
params.b = b
params.addProperty("App::PropertyLength", "hub_d", "Parameters", "Hub Diameter")
params.hub_d = d_hub
params.addProperty("App::PropertyLength", "hub_b", "Parameters", "Hub Width")
params.hub_b = b_hub
params.addProperty("App::PropertyLength", "shaft_d", "Parameters", "Shaft Diameter")
params.shaft_d = d_shaft
params.addProperty("App::PropertyLength", "w_total", "Parameters", "Total Width")
params.w_total = w_total
params.addProperty("App::PropertyLength", "pressure_angle", "Parameters", "Pressure Angle")
params.pressure_angle = P

# Helper to link expressions
def link_expr(obj, prop, source_name, source_prop):
    try:
        obj[prop] = f"= {source_name}.{source_prop}"
    except:
        pass

# -----------------------------------------------------------------------------
# 3. Feature Construction
# -----------------------------------------------------------------------------

# --- Step 1: Base Cylinder (The Hub/Body core) ---
# We start with a cylinder of outer_diameter and total_width.
# Sketch on XY_Plane, extruded along Z.
sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_Base")
sketch_base.Placement = App.Placement(App.Vector(0, 0, w_total / 2), App.Rotation())
sketch_base.ConstraintTypes = ["Horizontal", "Vertical", "Radius", "Coincident", "Equal", "Perpendicular", "Parallel"]
sketch_base.MapMode = "FlatFace"
sketch_base.AttachmentSupport = (XY_Plane, [])
sketch_base.TangentSupport = (YZ_Plane, [])
sketch_base.AddToBody = body

# Outer Circle for base
c_base = sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), outer_diameter / 2))
# Center Coincident
c_base.Constraint = sketch_base.addConstraint(Sketcher.Constraint("Point", "XY_Plane", 0.5, 0.5))
# Diameter constraint (optional, but good for visibility)
c_base.Expression = str(outer_diameter / 2)

# Pad Base
pad_base = body.newObject("PartDesign::Pad", "Pad_Base")
pad_base.Profile = sketch_base
pad_base.Length = w_total
pad_base.Type = "Solid"
pad_base.MidPlane1 = False
pad_base.MidPlane2 = False
# Link dimensions
link_expr(pad_base, "Length", "Parameters", "w_total")
# Recalculate
doc.recompute()

# --- Step 2: Hub ---
# Cut a cylinder for the hub
sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, w_total / 2), App.Rotation())
sketch_hub.AttachmentSupport = (XY_Plane, [])
sketch_hub.MapMode = "FlatFace"
c_hub = sketch_hub.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), d_hub / 2))
c_hub.Constraint = sketch_hub.addConstraint(Sketcher.Constraint("Point", "XY_Plane", 0.5, 0.5))
link_expr(c_hub, "Radius", "Parameters", "hub_d")

pocket_hub = body.newObject("PartDesign::Pocket", "Pocket_Hub")
pocket_hub.Profile = sketch_hub
pocket_hub.Type = "Solid"
pocket_hub.Length = w_total
pocket_hub.MidPlane1 = False
pocket_hub.MidPlane2 = False
link_expr(pocket_hub, "Length", "Parameters", "w_total")
doc.recompute()

# --- Step 3: Bore ---
sketch_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, w_total / 2), App.Rotation())
sketch_bore.AttachmentSupport = (XY_Plane, [])
sketch_bore.MapMode = "FlatFace"
c_bore = sketch_bore.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), d_shaft / 2))
c_bore.Constraint = sketch_bore.addConstraint(Sketcher.Constraint("Point", "XY_Plane", 0.5, 0.5))
link_expr(c_bore, "Radius", "Parameters", "shaft_d")

pocket_bore = body.newObject("PartDesign::Pocket", "Pocket_Bore")
pocket_bore.Profile = sketch_bore
pocket_bore.Type = "Solid"
pocket_bore.Length = w_total
pocket_bore.MidPlane1 = False
pocket_bore.MidPlane2 = False
link_expr(pocket_bore, "Length", "Parameters", "w_total")
doc.recompute()

# --- Step 4: Tooth Profile Generation ---
# We need to calculate the involute curve points.
# Function to generate involute points
def get_involute_points(N=200, d_base_val=base_diameter):
    r_base = d_base_val / 2.0
    points = []
    t = 0.0
    # Generate enough points for a full circle
    while t <= 2 * pi:
        r = r_base * (t + 1) # Involute radius grows with t
        # Involute angle phi = tan(t) - t (Wait, standard formula: phi = tan(t) - t? No.)
        # Parametric eq of involute:
        # x = r_base * (cos(t) + t*sin(t))
        # y = r_base * (sin(t) - t*cos(t))
        # where t is the roll angle (unwrapped angle).
        
        x = r_base * (cos(t) + t * sin(t))
        y = r_base * (sin(t) - t * cos(t))
        
        # Normalize to radius r_base for the base circle start
        # Actually, the standard parametric form uses the base circle radius directly.
        # Let's verify limits. At t=0, x=r_base, y=0.
        # We need to stop when radius reaches outer_diameter/2
        
        if r > outer_diameter / 2 + 0.1:
            break
            
        points.append((x, y))
        t += 0.01 # Step size
    return points

# Create the tooth sketch
sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, w_total / 2), App.Rotation())
sketch_teeth.AttachmentSupport = (XY_Plane, [])
sketch_teeth.MapMode = "FlatFace"
sketch_teeth.ConstrainType = ["Horizontal", "Vertical", "Radius", "Coincident", "Equal", "Perpendicular", "Parallel", "Tangent", "Parallel", "Angle"]
sketch_teeth.TangentSupport = (YZ_Plane, [])

# We will construct one tooth profile and use a Polar Pattern.
# Tooth Profile:
# 1. Center line at x=0.
# 2. Root circle arc at bottom.
# 3. Base circle arc (tangent to involute).
# 4. Involute curve.
# 5. Top land circle arc.
# 6. Addendum circle.

# We need to calculate the angle of the tooth half-width at the pitch circle.
# Pitch Radius
rp = pitch_diameter / 2.0
# Tooth Thickness at Pitch Circle
# s = pi * m / 2 = circular_pitch / 2
# The angle subtended by half-tooth at pitch circle: theta_half = s / rp
theta_half_pitch = (pi * m / 2) / rp

# Calculate involute points relative to the center of the tooth (which will be on the X axis initially)
# The tooth is symmetric around X axis? No, usually we draw the half-tooth on the X axis and mirror, 
# or draw the full tooth and rotate. Let's draw the half-tooth on the X axis (0 to 180 deg sweep)
# and use a linear pattern or just mirror? 
# Better: Draw the full tooth profile (left side to right side) and use Polar Pattern.
# But generating the involute requires knowing the exact start and end angles.

# Let's generate points for the right flank of the tooth starting from the base circle.
# The tooth starts at the root radius.
# We need the angle of the involute start point (root radius).
# r = r_base / cos(phi) => phi = acos(r_base / r)
# But we don't know the exact root involute angle easily without iteration or solving.
# Alternative: Generate a dense cloud of involute points and filter by radius.

inv_points = get_involute_points(N=300, d_base_val=base_diameter)

# We need to place these points such that they form a tooth.
# The tooth is centered on the Y-axis in the sketch? 
# Let's draw the tooth such that the Y-axis is the centerline of the tooth.
# So we need points where x is negative (left flank) and positive (right flank).
# Actually, standard parameterization: 
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# This creates an involute starting at (r_base, 0) and spiraling out counter-clockwise.
# We want the tooth profile.
# Let's calculate the t value corresponding to the root radius (root_diameter/2).
r_root = root_diameter / 2.0
r_outer = outer_diameter / 2.0

# Solve for t_root: r = r_base * sqrt(1 + t^2)
# t = sqrt((r/r_base)^2 - 1)
t_root = sqrt((r_root / (base_diameter/2.0))**2 - 1)
t_outer = sqrt((r_outer / (base_diameter/2.0))**2 - 1)

# Calculate the angle of the tooth centerline relative to the base circle tangent.
# The tooth center angle (theta) = t - sin(t) / cos(t) ? No.
# Let's just use the property that the tooth is symmetric about the Y-axis in the sketch.
# We will generate points for the Right Flank (t from 0 to t_outer) and Left Flank (mirror).
# But the Involute formula gives points relative to the base circle center.
# If we align the base circle center with the sketch origin:
# Right Flank: We want the curve that goes from Root to Outer.
# The angle of the tangent to the base circle at the start of the involute is 0.
# As t increases, the angle increases.
# We need to shift the points so the tooth is centered on the Y axis.

# Let's define the tooth center angle (alpha).
# alpha = atan2(tooth_thickness_at_pitch, pitch_radius)
# theta_half_pitch = (pi * m / 2) / rp
# alpha = theta_half_pitch
# The tooth center is at angle alpha.
# The flank starts at angle (alpha - theta_half_pitch) and ends at (alpha + theta_half_pitch).
# Wait, the involute starts at the base circle.
# The angle of the involute point P(t) is: psi = t + atan(t) ? No.
# The angle of the radius vector OP(t) is: theta = t - sin(t)/cos(t)? No.
# Correct Parametric:
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# Angle of point = atan2(y, x) = atan2(sin(t)-t*cos(t), cos(t)+t*sin(t)) = t - atan(t).
# Wait, atan(t) is the pressure angle at radius r.
# So the polar angle theta = t - atan(t).
# We need to find t_start such that r(t_start) = r_root.
# We already calculated t_root.
# We need to find t_end such that r(t_end) = r_outer.

# The tooth occupies an angular sector.
# The sector angle of the tooth at the pitch circle is 2 * theta_half_pitch.
# The involute curve must span from the root to the outer.
# We need to calculate the t values for the left and right flanks.
# This is complex because the root and outer circles intersect the involute at specific t values.
# Let's assume the tooth is generated by rotating a single profile segment.

# Profile Segment Construction:
# 1. Line from (0, -r_root) to (0, r_root) -> No, that's the root circle.
# We need the profile:
# - Arc at bottom: r = r_root
# - Arc at top: r = r_outer
# - Involute connecting them.

# Let's calculate the t values for the "Start" and "End" of the involute flank on the RIGHT side.
# The right flank is the one with positive x (if centered on Y).
# Actually, let's just generate a full set of points for one tooth and then use a polar pattern.
# One tooth profile:
# Start point: Angle = -theta_half_pitch, Radius = r_root (approx, intersection of root circle and flank)
# End point: Angle = +theta_half_pitch, Radius = r_outer
# This is tricky. Let's use a simpler method:
# Generate involute points. Filter them by radius [r_root, r_outer].
# Then sort by angle.
# We want a segment of length 2 * theta_half_pitch centered at 0? No, centered at some angle.
# Let's generate the profile such that the Y-axis is the centerline of the tooth.
# So we need points where the angle (atan2(y,x)) ranges from -theta_half_pitch to +theta_half_pitch.
# AND the radius ranges from r_root to r_outer.
# But the involute doesn't start at r_root exactly at the centerline.
# The involute starts at the base circle.
# The base circle is inside the root circle.
# So the involute starts at some angle, goes outwards, and hits the outer circle.
# We need to clip the involute to the ring between r_root and r_outer.

# Let's generate points for the right flank (t from t_root to t
