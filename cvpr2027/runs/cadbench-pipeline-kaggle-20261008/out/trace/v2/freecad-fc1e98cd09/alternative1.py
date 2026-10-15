import FreeCAD as App
import Part
from pathlib import Path
import math

# Initialize document
doc = App.newDocument("GearStock")

# --- Parameters ---
# Define a parameter set to drive dimensions
params = doc.addObject("App::PropertyGroupProxy", "Parameters")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter (mm)")
params.pitch_diameter = 12.7 # 1/2 inch
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter (mm)")
params.outer_diameter = 14.732 # 0.58 inch
params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Axial Length (mm)")
params.overall_length = 304.8 # 1 ft
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.number_of_teeth = 12
params.addProperty("App::PropertyLength", "module", "Dimensions", "Calculated Module (mm)")
# Module = Pitch Diameter / Number of Teeth
params.module = params.pitch_diameter / params.number_of_teeth
params.addProperty("App::PropertyLength", "base_radius", "Dimensions", "Calculated Base Radius (mm)")
params.base_radius = params.pitch_diameter / 2 * math.cos(math.radians(20))
params.addProperty("App::PropertyLength", "addendum", "Dimensions", "Calculated Addendum (mm)")
params.addendum = params.module
params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "Calculated Dedendum (mm)")
params.dedendum = 1.25 * params.module
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle (deg)")
params.pressure_angle = 20.0

# --- Create Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject(body)

# --- Create Planes ---
# Plane 1: Origin (XY) for Top Sketch (Profile)
plane_xy = body.newObject("PartDesign::Plane", "XY_Plane")
plane_xy.Placement = App.Placement(App.Vector(0, 0, 0))

# Plane 2: XZ for Side Profile (optional, but we'll use XY for everything to keep it simple and robust)
# Actually, let's create a plane offset along Z to hold the axial length sketch if needed, 
# but usually a Pad along Z from a XY sketch is easiest.

# --- Step 1: Main Body (Blank) ---
# Sketch 1: Outer Cylinder Profile
sketch_main = body.newObject("Sketcher::SketchObject", "MainProfile")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.AttachmentSupport = [(doc.getObject("XY_Plane"), [""])]
sketch_main.ConstrainAuto = False
sketch_main.MapMode = "FlatFace"

# Line for outer diameter
line_outer = sketch_main.addGeometry(Part.LineSegment(App.Vector(-params.outer_diameter / 2, 0, 0), App.Vector(params.outer_diameter / 2, 0, 0)))
# Line for pitch diameter (reference)
line_pitch = sketch_main.addGeometry(Part.LineSegment(App.Vector(-params.pitch_diameter / 2, 0, 0), App.Vector(params.pitch_diameter / 2, 0, 0)))
# Line for root diameter (inside)
line_root = sketch_main.addGeometry(Part.LineSegment(App.Vector(-((params.outer_diameter - 2*params.addendum) - 2*params.dedendum)/2), 0, 0), App.Vector(((params.outer_diameter - 2*params.addendum) - 2*params.dedendum)/2), 0, 0))
# Line for base diameter (inside)
line_base = sketch_main.addGeometry(Part.LineSegment(App.Vector(-params.base_radius, 0, 0), App.Vector(params.base_radius, 0, 0)))

# Constraints: Close the profile
# Center all lines at X=0
sketch_main.addConstraint(Sketcher.Constraint("CenterX", 0, 1))
sketch_main.addConstraint(Sketcher.Constraint("CenterX", 0, 2))
sketch_main.addConstraint(Sketcher.Constraint("CenterX", 0, 3))
sketch_main.addConstraint(Sketcher.Constraint("CenterX", 0, 4))

# Horizontal segments
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 0, 3))
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 0, 4))

# Coincident start/end to close loop
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 0, 4))
# Coincident inner ends
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 0, 3))

# Addendum/Root dimensions from parameters
# Note: Sketcher constraints cannot directly reference parameters for lengths easily without expressions in the sketcher or using the Body's parameters.
# However, for robustness in a script, we set the geometry manually using the calculated values derived from params.
# To make it truly parametric via the sketcher, we would need to add "Length" constraints referencing the parameters object.
# Let's do that for the outer diameter.
sketch_main.addConstraint(Sketcher.Constraint("Length", "Parameters.outer_diameter", 0, 1))
sketch_main.addConstraint(Sketcher.Constraint("Length", "Parameters.pitch_diameter", 0, 2))
# Calculate root diameter: OD - 2*Addendum - 2*Dedendum
root_diam = params.outer_diameter - 2*params.addendum - 2*params.dedendum
sketch_main.addConstraint(Sketcher.Constraint("Length", root_diam, 0, 3))
# Base diameter
sketch_main.addConstraint(Sketcher.Constraint("Length", 2*params.base_radius, 0, 4))

# Pad the blank
pad_blank = body.newObject("PartDesign::Pad", "Pad_Blank")
pad_blank.Profile = sketch_main
pad_blank.Length = params.overall_length
pad_blank.MidPlane = False
pad_blank.Reverse = False

# --- Step 2: Teeth Geometry ---
# We need to create the tooth profile and pattern it.
# Approach: Create a sketch for one tooth sector or a simplified involute, then Polar Pattern.
# Given the constraints of a simple script, we will construct an approximate involute profile 
# using a sketch relative to the center, then pattern it.

# Sketch 2: Tooth Profile (on the XY plane, centered)
sketch_tooth = body.newObject("Sketcher::SketchObject", "ToothProfile")
sketch_tooth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_tooth.AttachmentSupport = [(doc.getObject("XY_Plane"), [""])]
sketch_tooth.MapMode = "FlatFace"

# We will draw the full profile of one tooth (from root to tip) on the Right side (X > 0).
# Then we will pattern this around the center.
# Coordinates:
# Center of gear: (0,0)
# Root Radius: r_root = (params.outer_diameter - 2*params.addendum - 2*params.dedendum) / 2
# Pitch Radius: r_pitch = params.pitch_diameter / 2
# Base Radius: r_base = params.base_radius
# Tip Radius: r_tip = params.outer_diameter / 2

r_root = (params.outer_diameter - 2*params.addendum - 2*params.dedendum) / 2
r_tip = params.outer_diameter / 2
r_pitch = params.pitch_diameter / 2
r_base = params.base_radius

# Tooth angle (half angle between teeth)
tooth_angle = (2 * math.pi / params.number_of_teeth) / 2

# Approximate Involute Points:
# 1. Start at Root (Vertical line up)
p1 = App.Vector(r_root, 0, 0)
# 2. Base Circle contact point? No, we draw the curve.
# Let's calculate 3 points for a spline approximation of the involute.
# Point at Base Radius (start of involute)
p_base = App.Vector(r_base, 0, 0)
# Point at Pitch Radius
# Tangent angle at pitch radius: inv(alpha) = tan(alpha) - alpha
# alpha_p = 20 deg
# alpha_t = atan(r_base / r_pitch)
alpha_t = math.atan(r_base / r_pitch)
# Involute function: r * (sec(theta) - theta) ... standard formula is complex.
# Let's use a simplified spline passing through:
# A: Base circle point (r_base, 0)
# B: Pitch circle point
# C: Tip circle point

# Parametric calculation for Involute:
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# where t = angle from base circle tangent.
# At base circle, t=0.
# At pitch circle: tan(t) = r_pitch / r_base - 1? No.
# The pressure angle at pitch circle is 20 deg.
# The tangent angle of the involute at pitch circle is 20 deg relative to the radius? 
# Yes, the pressure angle IS the angle between the line of action and the tangent to the pitch circle.
# So t_pitch = 20 deg in radians.
t_pitch = math.radians(20.0)
# At tip circle, pressure angle is larger.
# r_tip = r_base / cos(t_tip)
t_tip = math.acos(r_base / r_tip)

# Calculate points
x_base = r_base * (math.cos(0) + 0*math.sin(0))
y_base = r_base * (math.sin(0) - 0*math.cos(0))
# Point 1 (Base)
p_start = App.Vector(x_base, y_base, 0)

x_pitch = r_base * (math.cos(t_pitch) + t_pitch*math.sin(t_pitch))
y_pitch = r_base * (math.sin(t_pitch) - t_pitch*math.cos(t_pitch))
p_mid = App.Vector(x_pitch, y_pitch, 0)

x_tip = r_base * (math.cos(t_tip) + t_tip*math.sin(t_tip))
y_tip = r_base * (math.sin(t_tip) - t_tip*math.cos(t_tip))
p_end = App.Vector(x_tip, y_tip, 0)

# Also need the fillet/transition at the root to the vertical side of the tooth?
# Standard gears have a fillet at the root. Let's add a small circle at the root.
# Let's define the tooth profile as:
# Line from Root to Base (Vertical-ish) -> Spline (Involute) -> Line from Tip to Tip (Vertical-ish) -> Line back to start.
# Actually, the tooth space is between teeth.
# We need to draw ONE TOOTH profile.
# Tooth profile consists of:
# 1. Root fillet arc (approx)
# 2. Involute from Base to Tip
# 3. Tip relief (often omitted for stock, but we'll stop at the tip circle)
# 4. Side flank (Vertical line for simplicity in stock, or close to vertical)

# Let's construct the profile of ONE TOOTH (Right side of the space? No, Right side of the tooth).
# Wait, the tooth is the material.
# Profile of the tooth:
# Left flank: Involute curve (approximated by spline through Base, Pitch, Tip points calculated above, shifted to center of tooth)
# Right flank: Vertical line? Or another involute? 
# Tooth flanks are symmetric.
# The space between teeth is the inverse.
# Let's draw the profile of the tooth flank on the RIGHT side of the tooth (the side facing the next tooth).
# This flank goes from Root to Tip.
# It is an involute curve.
# The other side is a mirror image.

# Let's define the profile for the RIGHT flank of a tooth.
# This flank starts at the root radius, goes up the involute to the tip radius.
# The angle of the tooth:
# The tooth is centered at angle = i * tooth_angle.
# Let's build the profile for the tooth at angle 0.
# The right flank of the tooth at 0 starts at angle = -tooth_angle/2 and ends at 0?
# No, the tooth occupies the space between -tooth_angle/2 and +tooth_angle/2.
# The right flank is the boundary at +tooth_angle/2?
# Wait, the tooth is the solid.
# So we need the boundary between Tooth 0 and Tooth 1.
# This boundary is the involute curve.
# We need to generate this curve for ALL teeth.
# Easiest way: Create a sketch of ONE INVOLUTE FLANK relative to the gear center, then use a linear pattern? 
# No, Polar Pattern is better.
# Create a sketch containing ONE TOOTH PROFILE (Left Flank + Right Flank + Top + Bottom).
# Then Polar Pattern.

# Let's build the sketch for ONE TOOTH.
# Center of tooth is at angle 0.
# Left Flank: From Root (angle -tooth_angle/2) to Tip (angle -tooth_angle/2).
# Right Flank: From Root (angle +tooth_angle/2) to Tip (angle +tooth_angle/2).
# Top: Horizontal line at r_tip.
# Bottom: Horizontal line at r_root.
# AND the root fillet connecting them.

# Let's compute points for the Left Flank (involute starting from base).
# The involute starts at base circle.
# The starting point on the involute for the left flank is at angle = -tooth_angle/2.
# But the involute is defined by the unwrapping circle.
# We need to calculate the coordinates of the involute at the specific angles.
# Angle of the involute at the pitch circle is 20 deg.
# The angle of the point on the involute (phi) is related to the polar angle (theta) by:
# tan(theta) = ... complicated.
# Let's use the parametric form:
# x = r_base * (cos(t) + t*sin(t))
# y = r_base * (sin(t) - t*cos(t))
# Here t is the "unwrapped" angle.
# The polar angle theta = t + alpha, where alpha is the pressure angle?
# Actually, theta = t + arcsin(r_base/r)? No.
# Relationship: theta = t + inv(t)? No.
# Relationship: theta = t + arcsin(sin(t)? No.
# Correct relation: theta = t + alpha(t), where alpha(t) is the pressure angle at radius r(t).
# And r(t) = r_base / cos(t).
# So theta = t + arccos(r_base/r). But r is determined by t.
# So theta = t + arccos(r_base / (r_base/cos(t))) = t + arccos(cos(t)) = t + t = 2t?
# Wait, the pressure angle at the pitch circle is 20 deg.
# At pitch circle, r = r_pitch.
# t_pitch = arccos(r_base/r_pitch).
# theta_pitch = t_pitch + 20 deg?
# Let's check: alpha = arcsin(t * r_base / r)? No.
# Standard formula: inv(alpha) = tan(alpha) - alpha.
# The polar angle theta = t + inv(t)? No.
# theta = t + alpha(t).
# Since alpha(t) = arccos(r_base/r(t)) = arccos(cos(t)) = t?
# This implies theta = 2t.
# If theta = 2t, then at pitch circle:
# r = r_pitch. t = arccos(r_base/r_pitch).
# theta = 2 * arccos(r_base/r_pitch).
# But we know the pressure angle at pitch circle is 20 deg.
# Is 2 * arccos(...) == 20 deg?
# r_base = r_pitch * cos(20).
# arccos(cos(20)) = 20 deg.
# So theta = 40 deg?
# The tooth is centered at 0. The flank is at +20 deg (half of 40).
# Yes! The flank is at +20 deg.
# So the parameter t for the tip of the right flank (at +20 deg) corresponds to theta = 20 deg?
# No, the flank is the line of action.
# The line of action is tangent to the base circle.
# The angle of the line of action at the pitch circle is the pressure angle.
# So the flank at the pitch circle is at angle = 20 deg.
# The flank at the root circle is at angle = -tooth_angle/2.
# Wait, the tooth space is symmetric.
# The flank of the tooth at 0 is located at angle +20 deg (Right flank) and -20 deg (Left flank).
# But the tooth is only 360/12 = 30 deg wide.
# So the Right flank is at +15 deg (center of flank)?
# No, the flank is the surface.
# The surface of the tooth is the involute.
# The involute starts at the base circle.
# The angle of the involute at the base circle is 0 deg? No, the base circle is the start of the unwrapping.
# The involute curve exists for angles > 0.
# The polar angle of a point on the involute is theta = t + inv(t)? No.
# Let's just calculate the points for the right flank of the tooth at angle 0.
# This flank
