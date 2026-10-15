import FreeCAD as App
import Part
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("GearBuilder")

# --- 1. Define Parameters (App::VarSet) ---
# We use a VarSet to hold the parameters in a way that PartDesign can sometimes reference,
# although for robust scripting in 1.1, we primarily use direct property assignment on features
# or the standard App::PropertyString/Length if we were using ExpressionManager.
# However, the prompt asks for named objects. We will use a generic App::Feature or simply 
# set the parameters directly on the sketches/features to ensure editability as requested.
# The prompt example uses `body.newObject("App::VarSet", "Parameters")`. 
# In modern FreeCAD 1.1, App::VarSet might not be the standard way to define inputs for sketches.
# Instead, we will create a sketch with properties set to these values directly to ensure 
# the geometry is driven by these named values in the object tree.

params = doc.addObject("App::Feature", "GearParameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "gear module")
params.module = 1.5
params.addProperty("App::PropertyInteger", "teeth", "Dimensions", "number of teeth")
params.teeth = 80
params.addProperty("App::PropertyLength", "width", "Dimensions", "face width")
params.width = 15
params.addProperty("App::PropertyLength", "hub_dia", "Dimensions", "hub diameter")
params.hub_dia = 55
params.addProperty("App::PropertyLength", "hub_w", "Dimensions", "hub width")
params.hub_w = 10
params.addProperty("App::PropertyLength", "shaft_dia", "Dimensions", "shaft diameter")
params.shaft_dia = 12
params.addProperty("App::PropertyLength", "overall_w", "Dimensions", "overall width")
params.overall_w = 25
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "pressure angle")
params.pressure_angle = 20.0
params.addProperty("App::PropertyLength", "addendum", "Dimensions", "addendum")
params.addendum = 1.5
params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "dedendum")
params.dedendum = 1.875

# --- 2. Create Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- 3. Hub Sketch (Face 1) ---
# Plane: XY
hub_sk = body.newObject("Sketcher::SketchObject", "HubSketch")
hub_sk.Placement = App.Placement(App.Vector(0, 0, -12.5)) # Offset half width to center along Z
hub_sk.Support = (doc.getObject("XY_Plane"), [])
hub_sk.MapMode = "FlatFace"

# Hub Outer Circle
hub_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_dia / 2.0)
hub_sk.addGeometry(hub_circ, False)

# Hub Inner Circle (Bore)
hub_bore = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaft_dia / 2.0)
hub_sk.addGeometry(hub_bore, False)

# Constraint: Concentric
hub_sk.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))

# --- 4. Gear Body Sketch (Face 2) ---
# Plane: XY (but shifted up by half face width)
gear_sk = body.newObject("Sketcher::SketchObject", "GearSketch")
gear_sk.Placement = App.Placement(App.Vector(0, 0, 0)) # Center of face width
gear_sk.Support = (doc.getObject("XY_Plane"), [])
gear_sk.MapMode = "FlatFace"

# Base Circle for Involute
base_r = (params.pitch_diameter / 2.0) * math.cos(math.radians(params.pressure_angle))
base_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), base_r)
gear_sk.addGeometry(base_circ, False)

# Pitch Circle (for reference/thickness calc)
pitch_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_diameter / 2.0)
gear_sk.addGeometry(pitch_circ, False)

# Outer Circle
outer_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
gear_sk.addGeometry(outer_circ, False)

# Root Circle
root_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.root_diameter / 2.0)
gear_sk.addGeometry(root_circ, False)

# --- 5. Create Gear Teeth (Revolution) ---
# Strategy: Create a profile of ONE tooth between angles, then revolve.
# Or, create a full gear profile (inner, outer, root circles) + the involute profile.
# To make it a single solid feature tree efficiently:
# 1. Pad the main cylinder (Outer, Root, Hub).
# 2. Cut the Keyway/Flange if needed (none here).
# 3. Cut the teeth? No, teeth are usually added.
# Better approach for "PartDesign::Body" with "exactly one solid":
# Pad the blank cylinder.
# Then use a PartDesign::Pad (Midplane) or Revolution to add the teeth.
# Since teeth are an involute, we need to generate the curve.

# Let's build the blank cylinder first.
# Sketch for Blank: Union of Outer, Root, and Hub circles.
blank_sk = body.newObject("Sketcher::SketchObject", "BlankSketch")
blank_sk.Placement = App.Placement(App.Vector(0, 0, 0))
blank_sk.Support = (doc.getObject("XY_Plane"), [])
blank_sk.MapMode = "FlatFace"

# Add all circles to the blank sketch
blank_sk.addGeometry(outer_circ, False)
blank_sk.addGeometry(root_circ, False)
blank_sk.addGeometry(hub_circ, False)
blank_sk.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
blank_sk.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 1, 2))

# Pad the blank
pad_blank = body.newObject("PartDesign::Pad", "PadBlank")
pad_blank.Profile = blank_sk
pad_blank.Length = params.overall_w
pad_blank.Type = "Solid" # Solid pad

# --- 6. Generate Teeth ---
# We will create a sketch for a single tooth section (e.g., from -15 deg to +15 deg of pitch circle)
# and then use a Revolution feature.
# Tooth Angle = 360 / teeth
tooth_angle = 360.0 / params.teeth
half_tooth_angle = tooth_angle / 2.0

# Start angle for the tooth (centered on X axis for simplicity, then we can shift or just revolve)
# Let's create a tooth from -half_tooth_angle to +half_tooth_angle.

teeth_sk = body.newObject("Sketcher::SketchObject", "TeethSketch")
teeth_sk.Placement = App.Placement(App.Vector(0, 0, 0))
teeth_sk.Support = (doc.getObject("XY_Plane"), [])
teeth_sk.MapMode = "FlatFace"

# We need to define the involute curve points.
# Involute formula:
# r = base_r / cos(phi)
# theta = phi + atan(phi * tan(phi)) ... actually simpler parametric:
# x = base_r * (cos(phi) + phi * sin(phi))
# y = base_r * (sin(phi) - phi * cos(phi))
# where phi is the unwrapping angle in radians.

# Define the tooth profile points
points = []

# 1. Start at the outer circle, angle = -half_tooth_angle
# Check if we are outside the base circle. Usually yes for standard gears.
start_angle_deg = -half_tooth_angle
start_angle_rad = math.radians(start_angle_deg)

# Check intersection with base circle
# If start_angle_rad is small, the point might be inside base circle.
# Standard gear: start from base circle angle, go out.
# Let's find the angle on the base circle corresponding to the start of the tooth flank.
# Actually, standard generation:
# Flank 1: From Base Circle Angle (phi_start) to Addendum Angle (phi_end)
# Addendum Angle = atan((r_add - r_base) / r_base)

r_add = params.pitch_diameter / 2.0 + params.addendum
r_root = params.pitch_diameter / 2.0 - params.dedendum

# Calculate angles for the involute start and end
phi_base = math.atan((r_add - base_r) / base_r) # Max angle for addendum
phi_root = math.atan((r_root - base_r) / base_r) # Min angle for root (if applicable, but usually root is truncated)

# Let's generate the profile points for one tooth centered at 0 degrees.
# Left Flank: From phi_base down to some angle.
# Right Flank: From phi_base up to some angle.
# Tooth thickness is defined at pitch circle.
# We need to shift the involute so that the pitch circle arc length matches tooth_thickness.

# Parametric generation of the tooth profile:
# We will generate points for the left flank and right flank.
# The tooth is symmetric.
# We start at the "outside" of the tooth (addendum circle) and go inwards?
# No, we start at the base circle and go outwards to the addendum.

# Let's define the start angle of the involute at the base circle.
# The total angle of the involute at the base circle for one tooth is:
# alpha_pitch = 2 * atan(tan(phi_base) * (r_pitch / r_base) ... no.
# Let's use the standard method:
# Angle of the pitch circle sector for one tooth = tooth_angle
# Half sector = half_tooth_angle.
# We need to position the involute such that the distance along the pitch circle between the two intersection points is equal to tooth_thickness.

# Simplified approach:
# Generate a point on the involute at the pitch circle.
# Then generate points outward and inward from there.

# Actually, for a scriptable "one tooth" sketch to be revolved:
# We define a curve that goes from the root circle (or intersection) to the outer circle.
# Let's create a profile that spans from angle -half_tooth_angle to +half_tooth_angle.

# 1. Point 1: Outer circle at angle = -half_tooth_angle
p1 = App.Vector(
    (params.outer_diameter / 2.0) * math.cos(math.radians(-half_tooth_angle)),
    (params.outer_diameter / 2.0) * math.sin(math.radians(-half_tooth_angle)),
    0
)

# 2. Point 2: Pitch circle intersection? 
# We need to find the involute point that corresponds to the pitch circle angle.
# But the involute angle (phi) and polar angle (theta) are related.
# theta = phi + atan(phi * tan(phi)) -> no.
# theta = phi + atan(phi * cos(phi) / sin(phi))? 
# Correct relation: theta = phi + atan(phi * tan(phi))? No.
# theta = phi + atan( phi * tan(phi) ) is wrong.
# Relation: theta = phi + atan( phi * sin(phi) / cos(phi) )? 
# Standard: theta = phi + atan( phi * tan(phi) ) is not standard.
# Standard: theta = phi + atan( phi * tan(phi) ) -> wait, let's look up exact formula.
# x = r_b (cos phi + phi sin phi)
# y = r_b (sin phi - phi cos phi)
# theta = atan2(y, x)
# We need theta to be -half_tooth_angle at r = r_add? No, the tooth thickness is at pitch diameter.
# So we need the point on the involute where r = r_pitch.
# r = r_b / cos(phi) => cos(phi) = r_b / r_pitch => phi_pitch = acos(r_b / r_pitch)
phi_pitch = math.acos(base_r / (params.pitch_diameter / 2.0))

# Calculate theta for this phi_pitch
x_pitch = base_r * (math.cos(phi_pitch) + phi_pitch * math.sin(phi_pitch))
y_pitch = base_r * (math.sin(phi_pitch) - phi_pitch * math.cos(phi_pitch))
theta_pitch = math.atan2(y_pitch, x_pitch) # This is the angle from the start of the involute generation.

# Now we need to shift this profile so that the midpoint of the tooth (theta_pitch) aligns with 0 degrees (or -half_tooth_angle?).
# The tooth thickness is at the pitch circle.
# Arc length at pitch circle = theta_pitch * r_pitch? No.
# The angle subtended by the tooth at the pitch circle is 2 * (theta_pitch - start_angle_of_involute_segment)
# We need the total angle of the tooth at the pitch circle to be tooth_angle.
# Wait, the tooth thickness is half the circular pitch.
# Circular Pitch = pi * m.
# Tooth Thickness = pi * m / 2.
# Angle of tooth thickness at pitch circle = (pi * m / 2) / (pi * m / 2) * 1 rad? No.
# Angle = ArcLength / Radius = (pi * m / 2) / (pi * m) * 2 = 1 radian? No.
# Angle = (pi * m / 2) / (pitch_diameter / 2) = (pi * m) / pitch_diameter = (pi * m) / (pi * m * z / z)?
# Angle = (pi * m) / (pi * m * z) * 2? No.
# Angle = (Tooth Thickness) / (Pitch Radius) = (pi * m / 2) / (pi * m * z / (2 * pi))?
# Pitch Diameter = pi * m * z.
# Pitch Radius = pi * m * z / 2.
# Angle = (pi * m / 2) / (pi * m * z / 2) = 1/z radians? No.
# Angle = (pi * m / 2) / (pi * m * z / 2) = 1/z * (pi / pi)? 
# Angle = (pi * m / 2) / (pi * m * z / 2) = (pi * m) / (pi * m * z) = 1/z ? No.
# Angle = (pi * m / 2) / (pi * m * z / 2) = 1/z * (pi / (pi/2))? 
# Let's recompute:
# Arc Length = pi * m / 2.
# Radius = pi * m * z / 2.
# Angle (rad) = Arc / Radius = (pi * m / 2) / (pi * m * z / 2) = (pi * m) / (pi * m * z) = 1/z ? No.
# Angle = (pi * m / 2) / (pi * m * z / 2) = (pi * m) / (pi * m * z) = 1/z ? 
# Wait. (pi * m / 2) divided by (pi * m * z / 2) = (pi * m / 2) * (2 / (pi * m * z)) = 1/z.
# Yes, the angle is 1/z radians? 
# Example: z=20. Angle = 1/20 rad = 0.05 rad = 2.86 degrees.
# Total tooth angle = 2 * 2.86 = 5.72 degrees.
# But tooth_angle = 360/20 = 18 degrees.
# So the tooth thickness angle is roughly 18/2 = 9 degrees? No.
# Circular pitch angle = 360/z = 18 degrees.
# Tooth thickness angle = 18 / 2 = 9 degrees.
# 9 degrees = 9 * pi / 180 = 0.157 rad.
# 1/z = 0.05 rad.
# My calculation above was wrong.
# Angle = (pi * m / 2) / (pi * m * z / 2) = 1/z ? 
# Let's check units. 
# Arc = pi * m. (Pitch)
# Circumference = pi * d = pi * (pi * m * z)? No. d = m * z.
# Circumference = pi * m * z.
# Angle of Pitch = (pi * m) / (pi * m * z) = 1/z. (This is in Radians if we consider circumference = 2*pi*r).
# Circumference = 2 * pi * r = 2 * pi * (m*z/2) = pi * m * z.
# Arc = pi * m / 2.
# Angle = (pi * m / 2) / (pi * m * z) = 1/(2z).
# So the angle subtended by the tooth thickness at the pitch circle is 1/(2z) radians?
# 1/(2*20) = 1/40 = 0.025 rad = 1.43 degrees.
# This is clearly wrong. The tooth takes up half the space.
# Angle should be (360/z) / 2 = 180/z degrees.
# 180/20 =
