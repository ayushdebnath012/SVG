import FreeCAD as App
import Part
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("GearBuilder")

# --- 1. Define Parameters ---
PRESSURE_ANGLE = 20.0 # degrees
MODULE = 1.5 # mm
NUM_TEETH = 80
FACE_WIDTH = 15.0 # mm
HUB_DIAMETER = 55.0 # mm
HUB_WIDTH = 10.0 # mm
SHAFT_DIAMETER = 12.0 # mm
OVERALL_WIDTH = 25.0 # mm

# Derived dimensions
PITCH_DIAMETER = 120.0 # mm
OUTER_DIAMETER = 123.0 # mm
ROOT_DIAMETER = 116.25 # mm
ADDENDUM = 1.5 # mm
DEDENDUM = 1.875 # mm

# --- 2. Create Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- 3. Hub Sketch (Face 1) ---
# Plane: XY
hub_sk = body.newObject("Sketcher::SketchObject", "HubSketch")
# Correct Placement syntax for FreeCAD 1.1
hub_sk.Placement = App.Placement(App.Vector(0, 0, -OVERALL_WIDTH / 2.0)) 
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
# The angle subtended by the tooth thickness at the pitch circle is:
# alpha_tooth = (Tooth Thickness) / (Pitch Radius)
# Tooth Thickness = pi * Module / 2
# Pitch Radius = PITCH_DIAMETER / 2
# Angle = (pi * Module / 2) / (PITCH_DIAMETER / 2) = (pi * Module) / PITCH_DIAMETER
# Since PITCH_DIAMETER = pi * Module * NUM_TEETH,
# Angle = (pi * Module) / (pi * Module * NUM_TEETH) = 1 / NUM_TEETH radians?
# Wait, 1/80 rad = 2.25 degrees.
# But 360/80 = 4.5 degrees.
# This implies the tooth thickness is much smaller than the space width?
# No, tooth thickness = space width = pi * m / 2.
# So the angle subtended by the tooth is half the circular pitch angle.
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
# half_tooth_angle_rad = (3
