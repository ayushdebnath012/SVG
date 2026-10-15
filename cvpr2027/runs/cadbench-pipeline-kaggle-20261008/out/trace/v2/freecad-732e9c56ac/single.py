import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Part Parameters (Metric)
# pressure_angle = 20 degrees
# diametral_pitch = 12
# number_of_teeth = 24
# pitch_diameter = 50.8 mm
# outer_diameter = 55.118 mm
# overall_length = 304.8 mm
# gear_module = 2.1166666667 mm

# We will store these in a VarSet for easy editing in the tree
params = App.VarSet()
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.pitch_diameter = 50.8
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.outer_diameter = 55.118
params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Overall Length")
params.overall_length = 304.8
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.number_of_teeth = 24
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = 20.0
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Gear Module")
params.gear_module = 25.4 / 12.0 # Derived value

# --- Document Setup ---
doc = App.newDocument("GearStock")
doc.Label = "GearStock"

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Add Parameters to Body
body.addObject(params)

# --- Feature Tree Construction ---

# 1. Base Sketch (Pitch Circle & Outer Circle)
# We define the profile on the XY plane.
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.ConstrainFully = True
sketch.MapMode = "FlatFace"
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add Geometry: Pitch Circle
pitch_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_diameter / 2.0)
sketch.addGeometry(pitch_circle, False)

# Add Geometry: Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
sketch.addGeometry(outer_circle, False)

# Add Geometry: Base Line (for reference)
base_line = Part.LineSegment(App.Vector(-params.pitch_diameter/2 - 10, 0, 0), App.Vector(params.pitch_diameter/2 + 10, 0, 0))
sketch.addGeometry(base_line, False)

# Constraints: Concentric circles
sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1)) # Equal radii? No, concentric centers.
# Actually, Sketcher constraints work on geometry indices.
# 0 is pitch_circle, 1 is outer_circle.
# We need to constrain their centers to be coincident (they are both at 0,0,0 by default, but let's be explicit)
# And we need to ensure they are concentric.
# Since both are centered at 0,0,0, they are already concentric.
# Let's add a constraint to ensure the centers are coincident just in case.
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Center of 0 coincident with Center of 1

# 2. Pad the Base (The Gear Blank)
pad = body.newObject("PartDesign::Pad", "GearBlank")
pad.Profile = sketch
pad.Length = params.overall_length
pad.Type = "Solid"
# Drive length from parameter
pad.setExpression("Length", "Parameters.overall_length")

# 3. Tooth Profile Sketch
# We need to generate an involute tooth profile.
# The profile will be drawn on the XY plane, centered on the pitch circle.
# We will create a sketch that contains the tooth profile relative to the pitch circle.
# Then we will use a Polar Pattern to distribute it.

# Calculate Tooth Geometry
# Circular Pitch (p) = pi * pitch_diameter / number_of_teeth
# Tooth Thickness at pitch circle = p / 2
# Addendum = gear_module
# Dedendum = 1.25 * gear_module (Standard)
# Clearance = 0.25 * gear_module

p = 3.141592653589793 * params.pitch_diameter / params.number_of_teeth
tooth_thickness = p / 2.0
addendum = params.gear_module
dedendum = 1.25 * params.gear_module
clearance = 0.25 * params.gear_module
base_radius = params.pitch_diameter * (1 - 1.0 / params.diametral_pitch) # Standard: base dia = pitch dia * cos(pressure angle)
# Wait, standard formula: Base Diameter = Pitch Diameter * cos(Pressure Angle)
base_radius = (params.pitch_diameter / 2.0) * (App.Vector(0, 0, 1).getAngle(App.Vector(1, 0, 0)) if False else 0) # Placeholder
import math
base_radius = (params.pitch_diameter / 2.0) * math.cos(math.radians(params.pressure_angle))
outer_radius = (params.pitch_diameter / 2.0) + addendum
root_radius = (params.pitch_diameter / 2.0) - dedendum

# Create Tooth Sketch
tooth_sketch = body.newObject("Sketcher::SketchObject", "ToothSketch")
tooth_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
tooth_sketch.ConstrainAuto = True
tooth_sketch.ConstrainFully = True
tooth_sketch.MapMode = "FlatFace"
tooth_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# We need to draw the involute curve.
# Involute equation:
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# where t is the involute parameter (angle in radians).
# We need to find the t values for the start and end of the tooth flank.
# Start of tooth (root): r = root_radius
# End of tooth (tip): r = outer_radius
# However, the involute starts at the base circle.
# If root_radius < base_radius, the root is a fillet or straight line, not involute.
# Let's check: base_radius = 50.8/2 * cos(20) = 25.4 * 0.9397 = 23.87 mm.
# root_radius = 25.4 - 3.125 = 22.275 mm.
# Since root_radius < base_radius, the root is below the base circle.
# Standard spur gears usually have a fillet at the root if it goes below base circle, 
# or the involute starts at base circle and the root is a straight line tangent to base circle?
# Actually, the involute exists only for r >= base_radius.
# For r < base_radius, the profile is typically a fillet or a straight line.
# To keep it simple and robust for a "stock" gear, we will:
# 1. Draw the involute from base_radius to outer_radius.
# 2. Draw a straight line from base_radius to root_radius (tangent to base circle).
# 3. Draw a straight line from root_radius to the other side.
# 4. Close the loop.

# Let's calculate the involute points.
# We need the angle of the tooth centerline.
# Tooth centerline angle = 0 (for the first tooth).
# Tooth half-width angle (pressure angle at pitch circle) = pressure_angle.
# So the tooth flanks are at +/- pressure_angle relative to the radial line?
# No, the pressure angle is the angle between the line of action and the tangent to the pitch circle.
# The tooth profile is symmetric about the radial line passing through the tooth center.
# The flank angle at the pitch circle is exactly the pressure angle.

# Let's generate points for the left flank (from root to tip).
# We need to solve for the involute angle t such that r = r_base * sqrt(1 + t^2).
# t = sqrt((r/r_base)^2 - 1)

def get_involute_point(r, r_base):
    if r <= r_base:
        return None
    t = math.sqrt((r / r_base)**2 - 1)
    theta = t + math.atan(t) # Angle of the point on the pitch circle relative to base circle start?
    # Actually, the parametric equation uses theta as the angle of the tangent point on the base circle.
    # The point coordinates are:
    # x = r_base * (cos(theta) + t * sin(theta))
    # y = r_base * (sin(theta) - t * cos(theta))
    # where theta is the angle of the tangent point.
    # The angle of the point itself is theta + atan(t).
    # We need to rotate this by the tooth centerline angle.
    
    # Let's assume the tooth centerline is at angle 0.
    # The flank is at angle -pressure_angle at the pitch circle.
    # The involute starts at base circle.
    # The angle of the tangent point on the base circle for the flank is:
    # alpha_base = atan(t) - pressure_angle? No.
    # Let's simplify. We know the point at pitch circle (r_p, alpha_p) where alpha_p = pressure_angle.
    # We can calculate the corresponding t_p.
    # t_p = sqrt((r_p/r_base)^2 - 1)
    # Then for any r, we can find t.
    # The angle of the point on the base circle (theta) is related to the point angle (phi) by phi = theta + atan(t).
    # At pitch circle: phi_p = pressure_angle.
    # So theta_p = pressure_angle - atan(t_p).
    # For any other r, we find t, then theta = theta_p + (t - t_p).
    # Then calculate x, y.
    
    t_p = math.sqrt((params.pitch_diameter / 2.0 / r_base)**2 - 1)
    theta_p = math.radians(params.pressure_angle) - math.atan(t_p)
    
    t = math.sqrt((r / r_base)**2 - 1)
    theta = theta_p + (t - t_p)
    
    x = r_base * (math.cos(theta) + t * math.sin(theta))
    y = r_base * (math.sin(theta) - t * math.cos(theta))
    return App.Vector(x, y, 0)

# Generate Left Flank (from root to tip)
# We need to handle the root part (r < base_radius).
# We will draw a line from root to base circle tangent point, then involute.
# Tangent point on base circle for the flank:
# The flank is tangent to the base circle.
# The angle of the tangent point on the base circle is:
# alpha_tangent = -pressure_angle (relative to tooth centerline)?
# Actually, the line of action is tangent to the base circle.
# The angle of the line of action at the pitch circle is the pressure angle.
# So the tangent point on the base circle is at angle -pressure_angle relative to the tooth centerline?
# Let's verify.
# Tooth centerline is at 0.
# Pitch circle point is at angle pressure_angle.
# Base circle tangent point is at angle pressure_angle - 90? No.
# The line connecting the base circle tangent point to the pitch circle point is the line of action.
# The angle of the line of action is constant.
# The angle of the tangent point on the base circle is:
# theta_base = atan(t_p) - pressure_angle.
# Let's calculate the tangent point coordinates.
# theta_base = math.atan(t_p) - math.radians(params.pressure_angle)
# x_t = r_base * cos(theta_base)
# y_t = r_base * sin(theta_base)
# This is the start of the involute.
# The root is at r = root_radius.
# We need to connect the root to the start of the involute.
# Usually, this is a straight line tangent to the base circle?
# Or a fillet. For a stock gear, a straight line tangent to the base circle is common if root < base.
# Let's assume a straight line from root to the tangent point.
# But the root is a circle. The tooth profile must be tangent to the root circle.
# This is getting complex for a script.
# Simplification: 
# 1. Draw the involute from base_radius to outer_radius.
# 2. Draw a straight line from base_radius to root_radius along the radial line? No, that's not a gear.
# 3. Draw a straight line from the end of the involute (at base circle) to the root circle, tangent to the base circle.
#    This creates a "hook" shape.
#    Actually, the standard way is:
#    - Involute from base to tip.
#    - Straight line from base to root, tangent to base circle.
#    - Root circle arc.
#    - Symmetric on other side.
#    - Fillet at root? Often omitted in simple models or done with a small radius.
#    Let's do: Involute + Straight Line to Root + Root Circle Arc + Straight Line + Involute.
#    Wait, the straight line must be tangent to the base circle.
#    The angle of this line is the same as the pressure angle? No.
#    The line of action is tangent to the base circle.
#    The tooth flank is part of the line of action.
#    So the flank is a straight line? No, the involute is curved.
#    The involute is the locus of the end of a taut string unwinding from the base circle.
#    The string is always tangent to the base circle.
#    So the tangent point moves.
#    The line from the tangent point to the point on the involute is the string.
#    The tooth flank IS the involute.
#    So we just need to draw the involute curve.
#    What about the root?
#    If root < base, the involute doesn't exist there.
#    We need to connect the involute start (at base) to the root.
#    Common practice: A straight line tangent to the base circle, extending to the root circle.
#    This line is the extension of the string at the moment it leaves the base circle?
#    No, the string is tangent at the base circle.
#    So the line from the tangent point to the root circle is a straight line.
#    This line is tangent to the base circle.
#    So we draw:
#    1. Point at root circle (intersection with the tangent line).
#    2. Line from root to tangent point on base circle.
#    3. Involute from tangent point to tip.
#    4. Repeat for other side.
#    5. Close with root circle arc.

# Let's calculate the tangent point on the base circle for the left flank.
# The tooth centerline is at 0.
# The pressure angle is at the pitch circle.
# The tangent point on the base circle is at angle:
# theta_tangent = -pressure_angle (relative to the tooth centerline? No).
# Let's use the property that the line of action makes an angle of pressure_angle with the tangent to the pitch circle.
# The tangent to the pitch circle at the pitch point is perpendicular to the radius.
# So the line of action is at angle 90 + pressure_angle?
# Let's use the standard coordinate system.
# Tooth centerline is X-axis.
# Pitch point is at (r_p, 0).
# Tangent to pitch circle at pitch point is vertical (Y-axis).
# Line of action is at angle pressure_angle to the vertical?
# No, pressure angle is the angle between the line of action and the tangent to the pitch circle.
# So the line of action is at angle 90 - pressure_angle from the X-axis?
# Or 90 + pressure_angle?
# Standard: Pressure angle is measured from the tangent to the pitch circle.
# So the line of action is at angle 90 - pressure_angle from the X-axis (if measured from X).
# Wait, if pressure angle is 20, the line of action is 20 degrees from the tangent.
# The tangent is 90 degrees. So the line of action is 70 degrees or 110 degrees.
# Let's assume the tooth is symmetric around X-axis.
# The left flank goes from root to tip.
# The tangent point on the base circle is at angle:
# alpha = atan(t_p) - pressure_angle?
# Let's just calculate the point on the involute at the base circle.
# r = r_base.
# t = 0.
# theta = theta_p - atan(t_p) + atan(0) = theta_p - atan(t_p).
# We know at pitch circle, phi = pressure_angle.
# phi = theta + atan(t).
# So pressure_angle = theta_p + atan(t_p).
# So theta_p = pressure_angle -
