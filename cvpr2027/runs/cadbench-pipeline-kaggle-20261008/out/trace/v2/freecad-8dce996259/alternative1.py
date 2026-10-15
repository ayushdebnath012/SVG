from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

# Determine output path based on script location
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Create new document
doc = App.newDocument("GearConstruction")

# --- Create Reference Planes ---
# We need XY, XZ, and YZ planes to sketch on.
# PartDesign Body sketches usually default to XY, but we can be explicit or rely on standard defaults.
# Standard FreeCAD documents often come with XY_Plane, XZ_Plane, YZ_Plane.
# If not, we create them. In a headless script, we assume standard defaults or create them.
# Let's assume standard defaults exist (XY_Plane, Z_Axis, etc.) or create them if missing.
# However, PartDesign::SketchObject typically attaches to existing planes.
# We will create the necessary planes if they don't exist to ensure robustness.

def create_plane_if_missing(plane_name):
    if doc.getObject(plane_name) is None:
        if "XY" in plane_name:
            p = doc.addObject("Part::Plane", plane_name)
            p.Placement = App.Placement(App.Vector(0, 0, 0))
        elif "XZ" in plane_name:
            p = doc.addObject("Part::Plane", plane_name)
            p.Placement = App.Placement(App.Vector(0, 0, 0))
            # Rotate 90 deg around X to get XZ? No, standard is usually:
            # XY: Z=0
            # XZ: Y=0
            # YZ: X=0
            # FreeCAD standard planes are usually already there.
            # If not, we create them manually.
        elif "YZ" in plane_name:
            p = doc.addObject("Part::Plane", plane_name)
            p.Placement = App.Placement(App.Vector(0, 0, 0))
        # Let's rely on the fact that App.newDocument usually creates XY_Plane.
        # We will explicitly create the others if needed, or just use the standard ones.
        # Actually, let's just create them to be safe for the script logic.
        if "XY" in plane_name:
             p = doc.addObject("Part::Plane", plane_name)
             p.Placement = App.Placement()
        elif "XZ" in plane_name:
             p = doc.addObject("Part::Plane", plane_name)
             p.Placement = App.Placement()
             # Rotate to align with XZ plane (Normal Y)
             rot = App.Rotation(App.Vector(1, 0, 0), App.Vector(0, 0, 1), 90)
             p.Placement = p.Placement * App.Placement(rot)
        elif "YZ" in plane_name:
             p = doc.addObject("Part::Plane", plane_name)
             p.Placement = App.Placement()
             # Rotate to align with YZ plane (Normal X)
             rot = App.Rotation(App.Vector(0, 1, 0), App.Vector(0, 0, 1), 90)
             p.Placement = p.Placement * App.Placement(rot)
        return p
    return doc.getObject(plane_name)

# Standard planes usually exist. If not, we create them.
# Let's try to get them, if fail create.
try:
    xy_plane = doc.getObject("XY_Plane")
    xz_plane = doc.getObject("XZ_Plane")
    yz_plane = doc.getObject("YZ_Plane")
    z_axis = doc.getObject("Z_Axis")
except:
    # Fallback creation if not standard
    xy_plane = create_plane_if_missing("XY_Plane")
    xz_plane = create_plane_if_missing("XZ_Plane")
    yz_plane = create_plane_if_missing("YZ_Plane")
    z_axis = doc.addObject("App::Axis", "Z_Axis")
    z_axis.Placement = App.Placement(App.Vector(0,0,0))
    z_axis.XAxis = App.Vector(1,0,0)
    z_axis.YAxis = App.Vector(0,1,0)
    z_axis.ZAxis = App.Vector(0,0,1)

# --- Parameters ---
# We will store key values in the Body's properties or a Parameter object.
# Using a Parameter object for cleaner separation.
params = doc.addObject("App::Parameter", "GearParams")
params.addProperty("App::PropertyLength", "gear_module", "GearParams", "Module")
params.addProperty("App::PropertyInteger", "number_of_teeth", "GearParams", "Teeth")
params.addProperty("App::PropertyLength", "pressure_angle_deg", "GearParams", "PressureAngleDeg")
params.addProperty("App::PropertyLength", "face_width", "GearParams", "FaceWidth")
params.addProperty("App::PropertyLength", "hub_diameter", "GearParams", "HubDia")
params.addProperty("App::PropertyLength", "hub_width", "GearParams", "HubWidth")
params.addProperty("App::PropertyLength", "shaft_diameter", "GearParams", "ShaftDia")
params.addProperty("App::PropertyLength", "overall_width", "GearParams", "OverallWidth")
# ISO standard constants
params.addProperty("App::PropertyLength", "dedendum", "GearParams", "Dedendum")
params.addProperty("App::PropertyLength", "addendum", "GearParams", "Addendum")
params.addProperty("App::PropertyLength", "pitch_diameter", "GearParams", "PitchDia")
params.addProperty("App::PropertyLength", "root_diameter", "GearParams", "RootDia")
params.addProperty("App::PropertyLength", "outer_diameter", "GearParams", "OuterDia")

# Set default values per prompt
params.gear_module = 1.0
params.number_of_teeth = 50
params.pressure_angle_deg = 20.0
params.face_width = 6.0
params.hub_diameter = 16.0
params.hub_width = 8.0
params.shaft_diameter = 8.0
params.overall_width = 14.0

# Calculate ISO dimensions
params.dedendum = 1.25 * params.gear_module
params.addendum = params.gear_module
params.pitch_diameter = params.gear_module * params.number_of_teeth
params.root_diameter = params.pitch_diameter - 2 * params.dedendum
params.outer_diameter = params.pitch_diameter + 2 * params.addendum

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Sketch 1: Gear Teeth (on XY Plane) ---
sketch_gear = body.newObject("Sketcher::SketchObject", "SketchGearProfile")
sketch_gear.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_gear.AttachmentSupport = (xy_plane, [])
sketch_gear.ConstrainToCurrentPlane = True
sketch_gear.MapMode = "FlatFace"

# Gear Geometry Calculation
# Pressure angle alpha = 20 deg
# Base circle radius = m * z * cos(alpha)
# Addendum circle radius = m * (z/2 + 1)
# Dedendum circle radius = m * (z/2 - 1.25)
# Pitch circle radius = m * z / 2
# Tooth thickness at pitch circle = pi * m / 2
# Tip width calculation involves involute geometry.
# Simplified approach: Construct profile points.

import math
alpha = math.radians(params.pressure_angle_deg)
m = params.gear_module
z = params.number_of_teeth

r_base = m * z * math.cos(alpha)
r_addendum = m * (z / 2 + 1)
r_dedendum = m * (z / 2 - 1.25)
r_pitch = m * z / 2
pitch_t = math.pi * m / 2
tip_angle = 2 * math.asin((r_addendum - r_base) / r_base) # Approximation for tip width angle?
# Exact tip width formula: s_t = m * z * (pi/2 + 2 * tan(alpha) * (inv(a) - inv(alpha)))
# Where inv is inverse involute.
# For simplicity in scripting without external libraries, we approximate or use a point-based sketch.
# We will construct the tooth profile using vertices and curves.

# Number of teeth to model = 12 (symmetry), then pattern
teeth_to_model = 12

# Start point: Angle = -90 deg (bottom of pitch circle relative to vertical, but let's align with X axis)
# Let's start at angle 0 (Right) and go clockwise? Or start at -90 (Bottom) and go CCW?
# Let's start at angle -90 (Bottom) and go CCW to distribute evenly.
start_angle = -math.pi / 2

# Function to get point on involute
def get_involute_point(angle_rad, r_base, r_c):
    # angle_rad is the rolling angle of the base circle.
    # The point on the involute is at radius r_c.
    # inv(u) = u - tan(u). r_c = r_base * sec(u).
    # tan(u) = sqrt((r_c/r_base)^2 - 1)
    # phi = arctan(sqrt((r_c/r_base)^2 - 1))
    # theta (rolling angle) = phi + alpha
    # Wait, the angle we pass is the polar angle of the point.
    # Let's use the standard parametric form:
    # x = r_base * (cos(t) + t*sin(t))
    # y = r_base * (sin(t) - t*cos(t))
    # r = r_base * sqrt(1+t^2)
    # We need to solve for t given r_c.
    t = math.sqrt((r_c/r_base)**2 - 1)
    x = r_base * (math.cos(t) + t * math.sin(t))
    y = r_base * (math.sin(t) - t * math.cos(t))
    return App.Vector(x, y, 0)

# Define points for one tooth segment
# We need: Base circle start, Base circle end, Addendum circle end, Addendum circle start.
# Tooth thickness at pitch circle = pitch_t
# Half tooth thickness at pitch circle = pitch_t / 2
# Angle corresponding to half tooth thickness at pitch circle:
# s = r * (theta - theta_base) ... actually simpler:
# The angle subtended by half tooth at pitch circle:
# delta_phi = pitch_t / r_pitch = (pi * m / 2) / (m * z / 2) = pi / z
# So half tooth angle = pi / (2*z)

half_tooth_angle = math.pi / (2 * z)

# We need the involute angles.
# Let's define the key points for one tooth in the middle of a tooth.
# Point 1: Intersection of Base Circle and Flank (Start of involute)
# We need to find the angle on the base circle that corresponds to the addendum radius.
# tan(theta_base) = sqrt((r_add/r_base)^2 - 1)
theta_add_inv = math.sqrt((r_addendum/r_base)**2 - 1)
# Angle of the point on the circle relative to the start of the involute generation?
# The polar angle of the point on the involute is theta_polar = theta_base + theta_add_inv - alpha ??
# Standard formula:
# Theta_polar = theta_base + phi, where phi = inv(theta_base) + alpha?
# Let's use the direct construction:
# We need the angle of the line from center to the tip of the tooth.
# The tooth is symmetric around its centerline.
# Centerline angle = start_angle + (tooth_index * 2*pi/z) + pi/z

# Let's construct the profile for the first tooth (index 0).
# Centerline angle:
# We place the tooth such that its centerline is at angle 0 for simplicity, then rotate later?
# No, let's just build the profile relative to X axis, starting from the valley.
# To make it easy to pattern, let's build the full profile of one tooth from root to tip, centered on angle 0.
# Then we will use a polar pattern.

# Tooth Centerline = 0.
# Half tooth angle at pitch circle = half_tooth_angle.
# Angle of the start of the flank (at pitch circle) relative to centerline = half_tooth_angle.
# Angle of the end of the flank (at pitch circle) = -half_tooth_angle.

# We need the coordinates of the points:
# P_root_start: Intersection of Dedendum circle and Flank?
# Usually, the root is flat or rounded. For a spur gear, root is often defined by the dedendum circle intersecting the tooth space.
# But the prompt asks for a specific root_diameter. We will use the dedendum circle.
# The tooth profile is bounded by the dedendum circle at the root.

# Points:
# 1. Start of Addendum (Tip End)
# 2. End of Addendum (Tip Start)
# 3. End of Flank (Root End)
# 4. Start of Flank (Root Start)
# 5. Center of Root (for symmetry check)

# Let's calculate the involute angles.
# tan(phi) = sqrt((r/r_base)^2 - 1)
# The polar angle of a point on the involute is:
# theta = theta_base + phi - alpha ?? No.
# Let's use the property: The tangent to the involute at any point is perpendicular to the line from the base circle contact point.
# Easier method:
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# where t is the parameter.
# We know r = r_base * sqrt(1+t^2).
# So t = sqrt((r/r_base)^2 - 1).
# This gives the point on the involute curve.
# But we need to know the rotation of this tooth.
# The "angle" of the tooth centerline is fixed.
# The involute starts at the base circle.
# The angle of the point on the circle corresponding to parameter t is:
# theta_circle = t - alpha? No.
# The angle of the radius vector to the point on the involute is:
# theta_point = theta_base + phi.
# And theta_base = phi - alpha?
# Actually, theta_point = t + alpha is not correct.
# Correct relation: The angle of the radius vector is theta = phi + alpha? No.
# Let's use the standard derivation:
# The angle of the tangent to the base circle is theta_base.
# The angle of the radius vector to the point is theta_point.
# theta_point = theta_base + phi.
# And theta_base = phi - alpha?
# Let's just compute the points relative to the tooth centerline.
# We know the tooth is symmetric about angle 0.
# So the centerline is 0.
# The flank extends from the base circle to the addendum circle.
# The angle of the centerline of the tooth is 0.
# The angle of the centerline of the tooth space is pi/z.
# The flank starts at the base circle.
# The angle of the start of the flank (on the base circle) relative to the tooth centerline?
# This is complex. Let's simplify.
# We will define the profile by 6 points for one tooth:
# 1. Tip End (Outer Circle, angle +half_tooth_angle)
# 2. Tip Start (Outer Circle, angle -half_tooth_angle)
# 3. Root End (Root Circle, angle +half_tooth_angle + correction)
# 4. Root Start (Root Circle, angle -half_tooth_angle - correction)
# 5. Center of Root (angle 0, r_dedendum) - optional, for flat bottom? No, standard gear has filleted root or dedendum circle intersection.
#    We will use the dedendum circle.

# Let's calculate the specific angles for the involute points.
# We need the angle of the radius vector to the point on the involute at radius R.
# tan(phi) = sqrt((R/r_base)^2 - 1)
# theta_point = theta_base + phi
# But what is theta_base?
# The involute is generated by unwrapping the base circle.
# The angle of the radius vector to the point P on the involute is:
# theta = phi + alpha_base?
# Let's use the explicit formula for the angle of the radius vector:
# theta = phi + alpha? No.
# The angle of the tangent to the base circle is theta_base.
# The angle of the point is theta = theta_base + phi.
# And theta_base = phi - alpha?
# Actually, the standard formula is:
# theta = phi + alpha?
# Let's verify with a known point.
# If t=0, R=r_base, phi=0. theta = alpha?
# The involute starts at the base circle.
# The angle of the radius vector at the start is alpha?
# Yes, the pressure angle is alpha.
# So theta = phi + alpha.
# Wait, if phi=0, theta=alpha.
# This means the start of the involute is at angle alpha.
# This is relative to the line of centers?
# Yes, relative to the line of action.
# For our sketch, we define the tooth centerline as 0.
# The line of action for this tooth is at angle -alpha? Or +alpha?
# Let's assume the tooth centerline is 0.
# The flank goes "inwards".
# The angle of the radius vector at the addendum circle is:
# phi_add = sqrt((r_add/r_base)^2 - 1)
# theta_add = phi_add + alpha ??
# No, the pressure angle at the addendum is different.
# The pressure angle at radius R is:
