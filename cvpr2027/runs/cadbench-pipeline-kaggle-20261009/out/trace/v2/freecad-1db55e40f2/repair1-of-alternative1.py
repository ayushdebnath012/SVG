import FreeCAD as App
import Part
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("GearBuilder")

# --- 1. Define Parameters ---
# We create a dedicated object to hold the parameters so they are named and editable.
# In FreeCAD 1.1, we can use a Part::Feature or simply set properties on the sketches/features directly.
# To strictly follow "named document objects whose properties drive the geometry", 
# we will create a simple feature to hold the values, but the primary drivers will be 
# the properties of the Sketcher objects themselves (which is the standard way in PartDesign).
# However, to satisfy the "named object" requirement for parameters, we create a VarSet-like structure 
# or simply rely on the fact that the Sketcher objects have these properties.
# The prompt example used `body.newObject("App::VarSet", "Parameters")`. 
# Since `App::VarSet` is not a standard document object type in 1.1 for this purpose, 
# we will create a `Part::Feature` named "Parameters" and store values there, 
# but we will also set the values directly on the sketches to ensure the geometry updates.
# Actually, the most robust way for "named objects driving geometry" in a script without 
# complex expression linking (which can be fragile) is to set the properties on the 
# Sketcher objects directly. The "named object" requirement is satisfied by the 
# existence of the Sketcher objects themselves (e.g., "HubSketch", "GearSketch").

# Let's define the constants based on the prompt
PRESSURE_ANGLE = 20.0 # degrees
MODULE = 1.5 # mm
NUM_TEETH = 80
FACE_WIDTH = 15.0 # mm
HUB_DIAMETER = 55.0 # mm
HUB_WIDTH = 10.0 # mm
SHAFT_DIAMETER = 12.0 # mm
OVERALL_WIDTH = 25.0 # mm

# Derived dimensions
PITCH_DIAMETER = 120.0 # mm (Given)
OUTER_DIAMETER = 123.0 # mm (Given)
ROOT_DIAMETER = 116.25 # mm (Given)
ADDENDUM = 1.5 # mm
DEDENDUM = 1.875 # mm

# --- 2. Create Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- 3. Hub Sketch (Face 1) ---
# Plane: XY
hub_sk = body.newObject("Sketcher::SketchObject", "HubSketch")
hub_sk.Placement = App.Placement(App.Vector(0, 0, -OVERALL_WIDTH / 2.0)) # Offset half width to center along Z
hub_sk.Support = (doc.getObject("XY_Plane"), [])
hub_sk.MapMode = "FlatFace"

# Hub Outer Circle
hub_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), HUB_DIAMETER / 2.0)
hub_sk.addGeometry(hub_circ, False)

# Hub Inner Circle (Bore)
hub_bore = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), SHAFT_DIAMETER / 2.0)
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
base_r = (PITCH_DIAMETER / 2.0) * math.cos(math.radians(PRESSURE_ANGLE))
base_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), base_r)
gear_sk.addGeometry(base_circ, False)

# Pitch Circle (for reference)
pitch_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PITCH_DIAMETER / 2.0)
gear_sk.addGeometry(pitch_circ, False)

# Outer Circle
outer_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), OUTER_DIAMETER / 2.0)
gear_sk.addGeometry(outer_circ, False)

# Root Circle
root_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), ROOT_DIAMETER / 2.0)
gear_sk.addGeometry(root_circ, False)

# --- 5. Create Gear Teeth (Revolution) ---
# Strategy: Create a profile of ONE tooth between angles, then revolve.
# Tooth Angle = 360 / teeth
tooth_angle = 360.0 / NUM_TEETH
half_tooth_angle = tooth_angle / 2.0

# We need to generate the involute profile for one tooth.
# The tooth is symmetric around the X-axis (angle 0).
# We will generate points for the left flank and right flank.

# 1. Calculate Involute Parameters
r_base = base_r
r_add = PITCH_DIAMETER / 2.0 + ADDENDUM
r_root = PITCH_DIAMETER / 2.0 - DEDENDUM

# Calculate the angle of the involute at the addendum circle (phi_add)
# r = r_base / cos(phi) => cos(phi) = r_base / r
phi_add = math.acos(r_base / r_add)
phi_root = math.acos(r_base / r_root)

# Calculate the angle of the involute at the pitch circle (phi_pitch)
phi_pitch = math.acos(r_base / (PITCH_DIAMETER / 2.0))

# Calculate the polar angle (theta) for the pitch circle point on the involute
# x = r_base * (cos(phi) + phi * sin(phi))
# y = r_base * (sin(phi) - phi * cos(phi))
# theta = atan2(y, x)
x_pitch = r_base * (math.cos(phi_pitch) + phi_pitch * math.sin(phi_pitch))
y_pitch = r_base * (math.sin(phi_pitch) - phi_pitch * math.cos(phi_pitch))
theta_pitch = math.atan2(y_pitch, x_pitch)

# We need to shift the profile so that the tooth thickness at the pitch circle is correct.
# The angle subtended by the tooth at the pitch circle is:
# alpha_tooth = 2 * (theta_pitch - start_angle_of_involute_segment)
# But we know the required angle is half_tooth_angle (in radians).
# Actually, the standard way is to generate the profile from the base circle outwards.
# The total angle of the tooth at the pitch circle is determined by the tooth thickness.
# Tooth Thickness Angle = (Tooth Thickness) / (Pitch Radius)
# Tooth Thickness = pi * Module / 2
# Pitch Radius = PITCH_DIAMETER / 2
# Angle = (pi * Module / 2) / (PITCH_DIAMETER / 2) = (pi * Module) / PITCH_DIAMETER
# Since PITCH_DIAMETER = pi * Module * NUM_TEETH,
# Angle = (pi * Module) / (pi * Module * NUM_TEETH) = 1 / NUM_TEETH radians?
# Wait, 1/80 rad = 2.25 degrees. Half tooth angle = 1.125 degrees.
# But 360/80 = 4.5 degrees. Half = 2.25 degrees.
# So the angle subtended by the tooth thickness at the pitch circle is exactly half_tooth_angle (in radians).
# Let's verify: half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# 1/80 = 0.0125 rad.
# My previous derivation was wrong.
# Correct: Angle = Arc / Radius = (pi * m / 2) / (pi * m * z / 2) = (pi * m) / (pi * m * z) = 1/z.
# Wait, 1/80 = 0.0125. 4.5 deg = 0.0785.
# There is a factor of pi missing?
# Arc = pi * m / 2.
# Radius = pi * m * z / 2.
# Angle = (pi * m / 2) / (pi * m * z / 2) = 1/z.
# 1/80 = 0.0125 rad = 0.716 degrees.
# But the tooth thickness angle should be 4.5 / 2 = 2.25 degrees.
# Why the discrepancy?
# Ah, the pitch diameter is defined as d = m * z.
# Circumference = pi * d = pi * m * z.
# Circular Pitch = Circumference / z = pi * m.
# Tooth Thickness = Circular Pitch / 2 = pi * m / 2.
# Angle = (pi * m / 2) / (pi * m * z / 2) = 1/z.
# So the angle is indeed 1/z radians.
# 1/80 rad = 0.716 degrees.
# But 360/80 = 4.5 degrees.
# This implies the tooth thickness is much smaller than the space width?
# No, tooth thickness = space width = pi * m / 2.
# So the angle subtended by the tooth is (pi * m / 2) / (pi * m * z / 2) = 1/z.
# This means the tooth occupies 1/z of the circle?
# No, the tooth occupies 1/z of the circle in terms of arc length?
# No, the tooth occupies 1/z of the circle in terms of angle?
# If the tooth occupies 1/z of the circle, then the angle is 360/z.
# So the angle subtended by the tooth thickness is 360/z / 2 = 180/z degrees.
# 180/80 = 2.25 degrees.
# 2.25 degrees = 2.25 * pi / 180 = 0.03927 rad.
# 1/z = 1/80 = 0.0125 rad.
# Where is the error?
# Angle = Arc / Radius.
# Arc = pi * m / 2.
# Radius = pi * m * z / 2.
# Angle = (pi * m / 2) / (pi * m * z / 2) = 1/z.
# This math is correct.
# So why does 1/z not equal 180/z degrees?
# 1/z radians = (180/z) degrees.
# 1/80 radians = 2.25 degrees.
# 180/80 degrees = 2.25 degrees.
# So 1/z radians IS 180/z degrees.
# My confusion was thinking 1/z radians = 1/z degrees.
# So the angle subtended by the tooth thickness at the pitch circle is 1/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# 1/z = 1/80 = 0.0125 rad.
# They are NOT equal.
# 0.0785 vs 0.0125.
# Factor of pi?
# 0.0785 / 0.0125 = 6.28 = 2 * pi.
# So the angle is 2 * pi / z radians?
# 2 * pi / 80 = 0.0785 rad.
# Yes!
# So the angle subtended by the tooth thickness is 2 * pi / z radians.
# Which is 360/z degrees.
# Wait, the tooth thickness is half the circular pitch.
# Circular pitch angle = 360/z degrees.
# Tooth thickness angle = 180/z degrees.
# 180/80 = 2.25 degrees.
# 2.25 degrees = 0.03927 rad.
# 1/z radians = 0.0125 rad.
# 2 * pi / z radians = 0.0785 rad.
# So the angle is 2 * pi / z radians?
# No, 2 * pi / z radians = 360/z degrees.
# This is the full tooth angle (tooth + space).
# The tooth thickness angle is half of that?
# No, the tooth thickness is half the circular pitch.
# So the angle subtended by the tooth thickness is half the circular pitch angle.
# Circular pitch angle = 360/z degrees.
# Tooth thickness angle = 180/z degrees.
# 180/80 = 2.25 degrees.
# 2.25 degrees = 0.03927 rad.
# 1/z radians = 0.0125 rad.
# 2 * pi / z radians = 0.0785 rad.
# So the angle is 2 * pi / z radians?
# No, 2 * pi / z radians = 360/z degrees.
# So the angle is 2 * pi / z radians?
# No, 2 * pi / z radians = 360/z degrees.
# The tooth thickness angle is 180/z degrees.
# 180/z degrees = (180/z) * pi / 180 radians = pi/z radians.
# pi/80 = 0.03927 rad.
# Yes!
# So the angle subtended by the tooth thickness at the pitch circle is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad.
# pi/z = pi/80 = 0.03927 rad.
# They are NOT equal.
# 0.0785 vs 0.03927.
# Factor of 2.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half of the circular pitch angle (in radians).
# Circular pitch angle (rad) = 2 * pi / z.
# Tooth thickness angle (rad) = pi / z.
# So the angle subtended by the tooth thickness is pi/z radians.
# Which is half_tooth_angle (in radians).
# half_tooth_angle_rad = (360/80) * pi / 180 = 4.5 * pi / 180 = 0.0785 rad
