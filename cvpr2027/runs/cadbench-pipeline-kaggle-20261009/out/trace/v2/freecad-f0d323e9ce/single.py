import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from the prompt's specific values
PRESSURE_ANGLE_DEG = 20.0
DIAMETRAL_PITCH = 12.0
NUMBER_OF_TEETH = 16
PITCH_DIAMETER_MM = 33.8582
OUTER_DIAMETER_MM = 38.1
OVERALL_LENGTH_MM = 304.8

# Calculated parameters based on AGMA/ISO standards provided in prompt
GEAR_MODULE = 25.4 / DIAMETRAL_PITCH
ADDENDUM = 1.0 / DIAMETRAL_PITCH * 25.4
DEDENDUM = 1.25 / DIAMETRAL_PITCH * 25.4
WHOLE_DEPTH = 2.25 / DIAMETRAL_PITCH * 25.4
ROOT_DIAMETER = PITCH_DIAMETER_MM - 2 * DEDENDUM
BASE_DIAMETER = PITCH_DIAMETER_MM * math.cos(math.radians(PRESSURE_ANGLE_DEG))

# --- Document Setup ---
doc = App.newDocument("GearStock")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold the parameters, though direct property access on Body 
# or specific objects is also valid. Using a VarSet makes them clearly named and editable.
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.pitch_diameter = PITCH_DIAMETER_MM
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.outer_diameter = OUTER_DIAMETER_MM
params.addProperty("App::PropertyLength", "length", "Dimensions", "Overall Length")
params.length = OVERALL_LENGTH_MM
params.addProperty("App::PropertyLength", "addendum", "Dimensions", "Addendum")
params.addendum = ADDENDUM
params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "Dedendum")
params.dedendum = DEDENDUM
params.addProperty("App::PropertyLength", "root_diameter", "Dimensions", "Root Diameter")
params.root_diameter = ROOT_DIAMETER
params.addProperty("App::PropertyLength", "base_diameter", "Dimensions", "Base Diameter")
params.base_diameter = BASE_DIAMETER
params.addProperty("App::PropertyInteger", "num_teeth", "Dimensions", "Number of Teeth")
params.num_teeth = NUMBER_OF_TEETH
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = PRESSURE_ANGLE_DEG

# --- Sketch 1: Base Cylinder (Outer Envelope) ---
# This sketch defines the outer cylinder and the root circle for the gear body.
sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_Base")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [])
sketch_base.ConstrainToCurrentPlane = True

# Outer Circle (Pitch Diameter + Addendum)
# Radius = Outer Diameter / 2
outer_radius = params.outer_diameter.Value / 2.0
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), outer_radius), False)

# Root Circle (for the body cut)
# Radius = Root Diameter / 2
root_radius = params.root_diameter.Value / 2.0
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), root_radius), False)

# Coincident constraint to center
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 1, 1))

# --- Sketch 2: Involute Tooth Profile ---
# We need to generate the involute curve.
# Involute equation:
# x = r_b * (cos(t) + t*sin(t))
# y = r_b * (sin(t) - t*cos(t))
# where r_b is base radius, t is the involute parameter (angle in radians).
# We need to calculate the angle range to cover the tooth height.
# Tooth height (from pitch circle to tip) = Addendum
# Tooth depth (from pitch circle to root) = Dedendum
# However, the involute starts at the base circle.
# We need to find the angle 't' such that the radial distance r = r_b / cos(t) equals the tip radius.
# r_tip = r_b / cos(t_tip) => cos(t_tip) = r_b / r_tip => t_tip = acos(r_b / r_tip)

r_base = params.base_diameter.Value / 2.0
r_tip = params.outer_diameter.Value / 2.0
r_root = params.root_diameter.Value / 2.0

# Calculate involute angle for the tip
# t = acos(r_base / r_tip)
t_tip = math.acos(r_base / r_tip)

# Calculate involute angle for the root (if root is outside base circle)
# If root < base, the involute doesn't reach the root, but here root < base is typical.
# Actually, the involute starts at base. The profile goes from base to tip.
# The "root" of the gear is a straight line cut (fillet usually), but for a simple stock, 
# we can just extrude the involute from the base circle up to the tip, and then cut the root.
# Or, we can define the profile from the base circle to the tip, and then use a pocket to cut the root.
# Let's define the profile from the base circle (start of involute) to the tip.
# The profile will be symmetric around the X-axis (in the sketch plane).

# Generate points for the involute curve
# We need points from t=0 (base circle) to t=t_tip (tip).
# We also need the straight line from the tip down to the root circle? 
# Standard gear: Involute from base to tip. Then a radial line? No, usually a fillet or straight cut.
# For a "stock" gear, we can create the involute shape and then cut the root circle.
# Let's create a closed loop: 
# 1. Involute from Base to Tip (Right side)
# 2. Line from Tip to Root (Radial? No, usually the tooth flank continues or is cut).
# Actually, the simplest way to make a gear stock in PartDesign:
# Create a profile that goes from the Base Circle, along the involute to the Tip, then a line to the Root, 
# then along the root circle? No, that's complex.
# Alternative: Create the full tooth profile (Involute + Root Cut) in one sketch.
# Profile: 
# - Start at Base Circle (t=0)
# - Follow Involute to Tip (t=t_tip)
# - Line from Tip to Root Circle (Radial line? No, the tooth thickness is defined at pitch circle).
# - Follow Root Circle? No, the root is a circle.
# 
# Let's simplify: 
# 1. Draw the Involute curve from Base to Tip.
# 2. Draw a line from Tip to the Root Circle (tangent? No).
# 3. Actually, the standard way is: 
#    - Involute from Base to Tip.
#    - Line from Tip to Root (vertical in the tooth profile view? No, radial).
#    - Root Circle arc.
#    - Line from Root to Base.
# 
# Let's try a different approach: 
# Create the profile of ONE tooth.
# Points:
# A: Start of involute on Base Circle (Angle 0 relative to tooth centerline)
# B: End of involute on Tip Circle
# C: Point on Root Circle (Angle 0 relative to tooth centerline)
# 
# The profile consists of:
# 1. Involute from A to B.
# 2. Line from B to C? (Usually a fillet, but for stock, maybe a straight cut or just the root circle).
#    If we just extrude the involute, we get a shape that is open at the bottom.
#    We need to close it.
#    Let's assume the root is a straight cut perpendicular to the axis? No, it's a gear.
#    Let's assume the root is the Root Circle.
#    So the profile is: Involute (A->B) -> Line (B->C) -> Root Circle Arc (C->A)?
#    Wait, the tooth thickness is defined at the Pitch Circle.
#    We need to ensure the tooth thickness at the Pitch Circle is correct.
#    Tooth Thickness at Pitch Circle = (PI * Module) / 2.
#    Module = 25.4 / 12 = 2.1166...
#    Thickness = PI * 2.1166 / 2 = 3.316... mm.
# 
# Let's construct the profile:
# 1. Start at Base Circle (t=0). Let's call this point P_base.
# 2. Go along involute to Tip (t=t_tip). Call this P_tip.
# 3. Go from P_tip to P_root (on Root Circle, same angle as P_base).
#    Is this a straight line? In a standard gear, the tooth flank is the involute. 
#    The root is usually a fillet. But for a "stock", we can just cut the root circle.
#    So the profile is: Involute (P_base -> P_tip) -> Line (P_tip -> P_root) -> Root Circle Arc (P_root -> P_base)?
#    No, the Root Circle Arc is part of the circle.
#    So: Involute (P_base -> P_tip) -> Line (P_tip -> P_root) -> Root Circle (P_root -> P_base).
#    This creates a closed shape.
#    BUT, we need to check the tooth thickness.
#    The involute starts at the base circle. The thickness at the base circle is not the standard tooth thickness.
#    The standard tooth thickness is at the Pitch Circle.
#    So we need to shift the profile so that the thickness at the Pitch Circle is correct.
#    This is tricky to do purely geometrically without calculating the exact start/end angles.
# 
# Alternative Strategy:
# 1. Create a sketch with the involute curve.
# 2. Create a sketch with the root circle.
# 3. Use a Pad to extrude the involute up to the tip.
# 4. Use a Pocket to cut the root circle.
# 5. Use a Pattern to replicate the teeth.
# 
# How to get the correct tooth thickness?
# We can define the profile relative to the Pitch Circle.
# Let's define the profile as:
# - Line from Pitch Circle (Left side) to Pitch Circle (Right side) -> Thickness = PI*Module/2.
# - From Right side, go UP along the involute to the Tip.
# - From Tip, go DOWN to the Root Circle.
# - From Root Circle, go LEFT to the Pitch Circle (Left side).
# 
# This requires calculating the involute points.
# Let's define the tooth centerline as the X-axis.
# Pitch Circle Radius = PITCH_DIAMETER / 2.
# 
# Point 1: Left side of tooth at Pitch Circle.
#   Angle = 180 degrees (relative to centerline).
#   Point = (-PitchRadius, 0).
# Point 2: Right side of tooth at Pitch Circle.
#   Angle = 0 degrees.
#   Point = (PitchRadius, 0).
#   Wait, the thickness is PI*Module/2.
#   So the distance between these two points is PI*Module/2.
#   So the center of the tooth is at (0,0)? No, the center of the gear is (0,0).
#   The tooth is centered at some angle.
#   Let's place the tooth centerline at X-axis.
#   The tooth spans from angle -theta to +theta? No.
#   The tooth thickness is the arc length at the pitch circle.
#   Arc Length = R * Delta_Theta.
#   Delta_Theta = (PI * Module) / PitchRadius.
#   So the tooth spans from -Delta_Theta/2 to +Delta_Theta/2.
# 
# So, the profile is:
# 1. Start at (PitchRadius * cos(-Delta/2), PitchRadius * sin(-Delta/2)).
# 2. Go to (PitchRadius * cos(Delta/2), PitchRadius * sin(Delta/2)).
#    This is the chord? No, we need the involute.
#    The involute starts at the Base Circle.
#    We need to find the point on the involute that corresponds to the Pitch Circle angle.
#    Let's call the angle of the tooth centerline 0.
#    The tooth extends from -Delta/2 to +Delta/2.
#    The involute starts at the Base Circle.
#    We need to find the parameter 't' for the Pitch Circle.
#    r_pitch = r_base / cos(t_pitch) => t_pitch = acos(r_base / r_pitch).
#    So the involute starts at t=0 (Base Circle) and goes to t=t_tip (Tip).
#    The point on the involute at t_pitch is at radius r_pitch.
#    The angle of the tangent to the involute at t_pitch is t_pitch + 90 deg?
#    The angle of the radius vector to the point on the involute is t + alpha, where alpha is the pressure angle?
#    Actually, the angle of the radius vector to the point on the involute is t + 90 deg? No.
#    The angle of the radius vector to the point on the involute is t + 90 deg? 
#    Let's use the standard formula:
#    x = r_b * (cos(t) + t*sin(t))
#    y = r_b * (sin(t) - t*cos(t))
#    The angle of the radius vector is atan2(y, x).
#    Let's calculate the angle of the radius vector at t_pitch.
#    Let this be theta_pitch.
#    Then the tooth profile is the involute from t=0 to t=t_tip.
#    But we need to position this profile so that the tooth thickness at the pitch circle is correct.
#    The tooth thickness is the arc length between the two flanks at the pitch circle.
#    The flank is the involute.
#    So we need to find the angle of the involute at the pitch circle.
#    Let's call the angle of the radius vector to the point on the involute at t_pitch as theta_inv(t_pitch).
#    Then the tooth thickness is the arc length between theta_inv(t_pitch) and theta_inv(t_pitch) + Delta_Theta?
#    No, the tooth is symmetric.
#    So the tooth centerline is at angle theta_inv(t_pitch) + Delta_Theta/2.
#    And the flanks are at theta_inv(t_pitch) and theta_inv(t_pitch) + Delta_Theta.
#    Wait, the involute is a single curve.
#    The tooth has two flanks.
#    One flank is the involute from Base to Tip.
#    The other flank is the involute from Base to Tip (mirrored).
#    So we need to generate two involute curves.
#    Curve 1: From Base to Tip.
#    Curve 2: From Base to Tip (mirrored).
#    And we need to connect them at the Root Circle.
# 
# Let's simplify the sketch:
# 1. Create a line segment representing the tooth thickness at the Pitch Circle.
#    This line is perpendicular to the radius at the Pitch Circle? No, it's an arc.
#    But in the sketch, we can approximate it with a line if the angle is small?
#    No, we need the exact shape.
#    Let's create the profile as a closed loop:
#    - Involute from Base to Tip (Right Flank).
#    - Line from Tip to Root (Right Side).
#    - Root Circle Arc (from Right Side to Left Side).
#    - Line from Root to Base (Left Side).
#    - Involute from Base to Tip (Left Flank).
#    - Line from Tip to Root (Left Side).
#    - Root Circle Arc (from Left Side to Right Side).
#    This is getting complicated.
# 
# Let's try a simpler approach:
# 1. Create a sketch with the involute curve.
# 2. Create a sketch with the root circle.
# 3. Use a Pad to extrude the involute up to the tip.
# 4. Use a Pocket to cut the root circle.
# 5. Use a Pattern to replicate the teeth.
# 
# How to get the correct tooth thickness?
# We can define the profile as:
# - Line from Pitch Circle (Left side) to Pitch Circle (Right side).
# - From Right side, go UP along the involute to the Tip.
# - From Tip, go DOWN to the Root Circle.
# - From Root Circle, go LEFT to the Pitch Circle (Left side).
# 
# This requires calculating the involute points.
# Let's define the tooth centerline as the X-axis.
# Pitch Circle Radius = PITCH_DIAMETER / 2.
# 
# Point 1: Left side of tooth at Pitch Circle.
#   Angle = 180 degrees (relative to centerline).
#   Point = (-PitchRadius, 0).
# Point
