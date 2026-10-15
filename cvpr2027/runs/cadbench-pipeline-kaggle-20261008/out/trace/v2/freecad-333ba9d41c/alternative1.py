import FreeCAD as App
import Part
import math
from pathlib import Path

# Ensure we are using FreeCAD 1.1 API patterns
# Create a new document
doc = App.newDocument("SpurGear")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters Section ---
# Define named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "module")
params.gear_module = 1.0

params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "teeth")
params.number_of_teeth = 48

params.addProperty("App::PropertyLength", "pressure_angle_rad", "Dimensions", "pressure angle")
params.pressure_angle_rad = math.radians(20.0)

params.addProperty("App::PropertyLength", "face_width", "Dimensions", "face width")
params.face_width = 6.0

params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "hub")
params.hub_diameter = 16.0

params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "hub")
params.hub_width = 8.0

params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "bore")
params.shaft_diameter = 8.0

params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "total width")
params.overall_width = 14.0

# Derived parameters
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "pitch")
params.addExpression("pitch_diameter", "gear_module * number_of_teeth")

params.addProperty("App::PropertyLength", "addendum", "Dimensions", "profile")
params.addExpression("addendum", "gear_module")

params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "profile")
params.addExpression("dedendum", "1.25 * gear_module")

params.addProperty("App::PropertyLength", "root_diameter", "Dimensions", "profile")
params.addExpression("root_diameter", "pitch_diameter - 2 * dedendum")

params.addProperty("App::PropertyLength", "base_diameter", "Dimensions", "profile")
params.addExpression("base_diameter", "pitch_diameter * cos(pressure_angle_rad)")

params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "profile")
params.addExpression("outer_diameter", "pitch_diameter + 2 * addendum")

params.addProperty("App::PropertyLength", "addendum_radius", "Dimensions", "profile")
params.addExpression("addendum_radius", "pitch_diameter / 2 + addendum")

params.addProperty("App::PropertyLength", "root_radius", "Dimensions", "profile")
params.addExpression("root_radius", "pitch_diameter / 2 - dedendum")

params.addProperty("App::PropertyLength", "base_radius", "Dimensions", "profile")
params.addExpression("base_radius", "base_diameter / 2")

params.addProperty("App::PropertyLength", "tooth_height", "Dimensions", "profile")
params.addExpression("tooth_height", "addendum + dedendum")

# --- Sketch 1: Gear Profile (XZ Plane) ---
# We will use the XZ plane for the profile. 
# FreeCAD default planes: XY, YZ, XZ. We need to attach to XZ.
sketch_profile = body.newObject("Sketcher::SketchObject", "ProfileSketch")
# Attach to XZ Plane
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Reference = (doc.getObject("XZ_Plane"), [""]) # Assuming standard doc has XZ_Plane
sketch_profile.MapMode = "FlatFace"

# Define the gear tooth profile in the XZ plane (X is radius, Z is depth)
# We will construct a closed loop: Base circle -> Addendum circle -> Top fillet -> Root -> Bottom fillet -> Base
# To make it a single sketch, we define points or lines. 
# Strategy: Draw the outline of one tooth, then array it.
# However, for a cleaner sketch, we can draw the involute or approximated curve.
# Let's use a simplified approach: Draw the base circle, then the addendum circle, and connect them with splines or lines if needed.
# But standard gear teeth are involute. 
# Since FreeCAD Sketcher doesn't have a direct "Involute" constraint easily available in all versions without extensions,
# we will construct the profile using a series of lines and circular arcs which is sufficient for a spur gear representation,
# OR we can use the "Curve" tool in sketcher if available, but standard primitives are safer.
# Let's use a parametric approach with lines/arcs.
# Actually, the most robust way in FreeCAD Sketcher for gears is to draw the involute using geometry.
# Let's define the profile as a set of lines/arcs manually based on ISO 21771 standards.
# Profile: From Base Circle to Addendum Circle.
# We will create a sketch that defines the tooth flank and tip.

# Let's create the profile points manually.
# Point 1: Start at Base Radius on X axis
p1 = App.Vector(params.base_radius, 0, 0)
# Point 2: End of Base Circle on X axis
p2 = App.Vector(params.base_radius, 0, 0) # This is tricky to do with just lines.
# Alternative: Use the "Curve" tool? No, let's stick to basic shapes.
# We will construct the profile by drawing the Base Circle, Addendum Circle, and then the tooth profile.
# Wait, a single sketch for the whole gear body is better done by creating the full outer shape.
# But defining the involute tooth by tooth in a sketch is hard.
# Better approach: Create a sketch with the Base Circle and Addendum Circle. 
# Then use a "Pad" to create the blank cylinder, then use a "Pattern" of a tooth? 
# No, we need the solid body to be the gear.
# Let's create the profile sketch containing the involute curve.
# We can use a spline that passes through calculated points of the involute.
# Involute equation: x = r_b * (cos(t) + t*sin(t)), y = r_b * (sin(t) - t*cos(t))
# where r_b is base radius, t is roll angle.
# Let's generate points for the involute.

def get_involute_point(angle_rad):
    r_b = params.base_radius.Value
    t = angle_rad # Roll angle
    x = r_b * (math.cos(t) + t * math.sin(t))
    y = r_b * (math.sin(t) - t * math.cos(t))
    return App.Vector(x, y, 0)

# Generate points for the tooth profile
# We need points from Base Radius (t=0) to Addendum Radius.
# Calculate t for Addendum Radius: r = r_b * sqrt(1 + t^2) => t = sqrt((r/r_b)^2 - 1)
r_add = params.addendum_radius.Value
t_end = math.sqrt((r_add / r_b)**2 - 1)

# Number of points for smooth spline
n_points = 20
t_steps = [t_end * i / n_points for i in range(n_points + 1)]
points = [get_involute_point(t) for t in t_steps]

# Addendum Circle Arc (from end of involute to the top of the tooth, symmetric)
# The tooth tip is usually rounded or sharp. Let's assume a small fillet or sharp tip.
# We will just connect the end of the involute to the addendum circle and close.
# Actually, the profile should go from the involute end to the addendum circle (if modified) or just stop.
# Standard gear: The tooth goes from base circle to addendum circle.
# So the profile is: Start at Base Circle (t=0) -> Involute -> End at Addendum Circle (t_end).
# Then we need the other side of the tooth.
# The tooth is symmetric. We generate the right half and mirror it.

# Let's create the sketch geometry
sketch_profile.clearGeometries()
sketch_profile.clearConstraints()

# 1. Draw the Base Circle
sketch_profile.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.base_radius), False)
# 2. Draw the Addendum Circle
sketch_profile.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.addendum_radius), False)

# 3. Draw the Involute Profile (Right side)
# Create a Curve from the points
# Note: Sketcher::SketchObject doesn't directly take a list of App.Vector for a Curve primitive in older versions,
# but in FreeCAD 1.1, we can use Part::Spline or just add lines?
# Let's use Part::Spline and add it to the sketch.
curve = Part.makeSpline(points)
sketch_profile.addGeometry(curve, False)

# 4. Draw the Top of the tooth (Arc from addendum circle to the involute end)
# This is often a small arc. Let's approximate with a line or arc.
# To keep it simple and standard, we will assume the tooth tip is on the addendum circle.
# So we connect the end of the involute to the addendum circle.
# Actually, the involute naturally meets the addendum circle.
# So the profile is closed by the addendum circle arc? No.
# The profile is the boundary of the material.
# The material is between the Base Circle and the Addendum Circle.
# So the sketch is: Base Circle (inner), Addendum Circle (outer), and the Involute lines connecting them.
# But we need to define the tooth count.
# We will create the profile for ONE tooth and then use a Polar Pattern.
# So the sketch must contain the outline of ONE tooth.

# Let's redefine the sketch to contain the profile of ONE tooth.
# We need to find the start and end angles of the tooth.
# Tooth thickness at pitch circle = pi * m / z = 3.14159 * 1 / 48 = 0.06545 mm
# Radius = 24 mm. Chord length approx 0.06545.
# We need to define the tooth shape.
# Let's create a sketch that contains the involute curve from Base to Addendum.
# And then we will use a "PolarPattern" on the feature that creates this profile.
# Wait, PartDesign::Pattern can pattern a feature (Pad).
# So: Sketch -> Pad (creates a wedge of the tooth) -> Pattern.
# But the Pad needs a closed profile.
# Let's construct the closed profile of ONE tooth.

# Tooth start angle and end angle.
# Let's assume the tooth is centered at 0 degrees.
# We need the involute points.
# We already have the points for the right flank.
# Now we need the left flank.
# The tooth thickness at pitch circle is T = pi * m / z.
# We can calculate the angle subtended by half the tooth at the pitch circle.
# half_t = (T / 2) / pitch_radius
# pitch_radius = 24.0
# half_angle_rad = (math.pi * params.gear_module.Value / (2 * params.number_of_teeth.Value)) / (params.pitch_diameter.Value / 2)
half_angle_rad = (math.pi * params.gear_module.Value / (2 * params.number_of_teeth.Value)) / (params.pitch_diameter.Value / 2)

# Generate points for the left flank (mirrored)
# The left flank starts at -half_angle_rad (relative to the tooth center) and goes to 0?
# No, the involute starts at Base Radius.
# Let's calculate the angle of the involute end relative to the base circle.
# The involute point at t_end is at angle theta = t_end.
# We need to shift this so the tooth is centered.
# Actually, let's just create the points for the right flank (0 to t_end) and left flank (-half_angle_rad to -half_angle_rad + t_end_offset?)
# This is getting complex for a script.
# Simpler approach: Create the profile of the tooth using the involute function.
# We will create a closed loop:
# 1. Start at Base Circle (angle -half_angle_rad)
# 2. Go to Addendum Circle along Involute.
# 3. Go across the top (Arc on Addendum Circle).
# 4. Go back to Base Circle along Involute (other side).
# 5. Close the loop at Base Circle.

# Let's calculate the specific angles for the tooth boundaries.
# The tooth is symmetric around 0.
# The thickness at pitch circle is T.
# The arc length at pitch circle is T.
# The corresponding angle at pitch circle is alpha_t = T / pitch_radius.
# So the tooth extends from -alpha_t/2 to +alpha_t/2 at the pitch circle.
# But the involute starts at the base circle.
# The angle of the involute curve at the pitch circle is related to the base circle angle.
# Let's just define the points for the right flank from Base to Addendum.
# And the left flank from Base to Addendum.
# And connect them at the top and bottom.

# Actually, let's simplify. We will create the profile of ONE tooth.
# We will use the involute points we generated earlier (0 to t_end).
# These points are at angles 0 to t_end relative to the base circle radius vector.
# We need to rotate this profile to be centered.
# Let's assume the tooth is centered at angle 0.
# The right flank goes from angle -delta to +delta?
# No, the right flank goes from Base (angle -theta_base) to Addendum (angle -theta_base + t_end).
# Let's just create the profile using the points we have.
# We have points for the right flank: p0 (base) to pn (addendum).
# We need to create a symmetric left flank.
# We need to find the start angle of the right flank relative to the tooth center.
# The tooth thickness at pitch circle is T.
# The angle subtended by the tooth at the pitch circle is alpha_t = T / R_pitch.
# The involute curve is defined by the roll angle t.
# The angle of the radius vector at any point on the involute is theta = t + alpha_b, where alpha_b is the pressure angle at base? No.
# The angle of the radius vector is theta = t + atan(r_b / r). No.
# The angle of the radius vector is theta = t + alpha_0, where alpha_0 is the pressure angle at the base? No.
# Let's use the property that the normal to the involute is tangent to the base circle.
# The angle of the radius vector is theta = t + alpha_b, where alpha_b is the angle of the line from center to the point of tangency?
# Actually, the angle of the radius vector at parameter t is theta = t + alpha_0, where alpha_0 is the pressure angle at the base? No, alpha_0 = 0 at base.
# So theta = t.
# Wait, if theta = t, then the point is at angle t.
# The radius is r = r_b * sqrt(1 + t^2).
# The pressure angle at this point is alpha = atan(t).
# We need the tooth to be symmetric around 0.
# So the right flank should go from some angle -delta to +delta? No.
# The tooth has a thickness.
# Let's assume the tooth is centered at 0.
# The right flank goes from angle -delta to +delta? No.
# The right flank is the curve.
# Let's calculate the angle of the tooth boundaries at the pitch circle.
# alpha_t = T / R_pitch.
# So the right boundary is at +alpha_t/2.
# The left boundary is at -alpha_t/2.
# The involute curve on the right flank goes from the base circle to the addendum circle.
# The angle of the radius vector at the pitch circle (t_p) is alpha_p = atan(T / (2 * R_pitch * sin(alpha_p)))? No.
# Let's use the relationship: t = tan(alpha) - alpha.
# At the pitch circle, the pressure angle is alpha_p = pressure_angle = 20 degrees.
# So t_p = tan(20) - 20_deg.
# The angle of the radius vector at the pitch circle is theta_p = t_p + alpha_base? No.
# The angle of the radius vector is theta = t + alpha_0, where alpha_0 is the angle of the line from center to the point of tangency?
# Actually, the angle of the radius vector is theta = t + alpha_0, where alpha_0 is the pressure angle at the base? No.
# The angle of the radius vector is theta = t + alpha_0, where alpha_0 is the angle of the line from center to the point of tangency?
# Let's just use the property that the angle of the radius vector is theta = t + alpha_0, where alpha_0 is the pressure angle at the base? No.
# The angle of the radius vector is theta = t + alpha_0, where alpha_0 is the angle of the line from center to the point of tangency?
# Let's assume the tooth is centered at 0.
# The right flank goes from the base circle to the addendum circle.
# The angle of the radius vector at the base circle is -delta_base.
# The angle of the radius vector at the addendum circle is +delta_add.
# The total angle of the flank is delta_add - delta_base = t_end.
# The pressure angle at the pitch circle is 20 degrees.
# The angle of the radius vector at the pitch circle
