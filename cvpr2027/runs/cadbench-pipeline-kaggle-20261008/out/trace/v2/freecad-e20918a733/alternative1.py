import FreeCAD as App
import Part
from pathlib import Path
from math import cos, pi, sqrt

# --- Configuration & Parameters ---
# Derived from the prompt requirements
params = {
    "pressure_angle": 20.0,      # degrees
    "gear_module": 1.0,          # mm
    "number_of_teeth": 70,       # teeth
    "face_width": 6.0,           # mm
    "hub_diameter": 18.0,        # mm
    "hub_width": 8.0,            # mm
    "shaft_diameter": 8.0,       # mm
    "overall_width": 14.0,       # mm
    "addendum": 1.0,             # mm
    "dedendum": 1.25,            # mm
}

# Calculated parameters based on ISO 21771 / AGMA standards
params["whole_depth"] = params["addendum"] + params["dedendum"]
params["root_diameter"] = params["gear_module"] * params["number_of_teeth"] - 2 * params["dedendum"]
params["base_diameter"] = params["gear_module"] * params["number_of_teeth"] * cos(params["pressure_angle"] * pi / 180)
params["circular_pitch"] = pi * params["gear_module"]
params["pitch_diameter"] = params["gear_module"] * params["number_of_teeth"]
params["outer_diameter"] = params["gear_module"] * params["number_of_teeth"] + 2 * params["addendum"]

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# 1. Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.ViewObject.Transparency = 50 # Make it semi-transparent for visualization
doc.setActiveObject(body)

# 2. Define Reference Planes (XY, XZ, YZ)
# These are standard FreeCAD reference planes. We will use them for attachments.
# Note: In a headless script, we assume XY_Plane exists or we define our own coordinate system.
# For robustness in PartDesign, we usually attach to the Body's origin planes.
# FreeCAD 1.0+ PartDesign Body has implicit planes. Let's create explicit planes if needed, 
# but standard practice is to attach sketches to the Body's internal planes (XY, XZ, YZ).
# However, the API provided in the prompt suggests creating explicit planes. 
# Let's create them to be safe and explicit.

# XY Plane (X, Y, Z)
plane_xy = doc.addObject("Part::Plane", "XY_Plane")
plane_xy.Placement = App.Placement(App.Vector(0, 0, 0))
doc.recompute()

# XZ Plane
plane_xz = doc.addObject("Part::Plane", "XZ_Plane")
plane_xz.Placement = App.Placement(App.Vector(0, 0, 0))
# Rotate 90 deg around Y to get XZ from XY
plane_xz.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(App.Vector(0, 1, 0), 90))
doc.recompute()

# YZ Plane
plane_yz = doc.addObject("Part::Plane", "YZ_Plane")
plane_yz.Placement = App.Placement(App.Vector(0, 0, 0))
# Rotate 90 deg around X to get YZ from XY
plane_yz.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(App.Vector(1, 0, 0), 90))
doc.recompute()

# Reference Axes (Standard in FreeCAD: X_Axis, Y_Axis, Z_Axis)
# These are usually available, but let's ensure we reference them correctly.
# We will rely on the sketch's local axis definitions or global axes.
# Standard convention: Z is the rotation axis for the gear.

# 3. Create Sketches and Features
doc.setActiveObject(body)

# --- Step 1: Hub Bore (Inner Cylinder) ---
# We need a hole. Let's create it first or last? 
# Usually, we build the body outwards. Let's create the Hub Cylinder, then the Gear Teeth, then the Bore?
# Or: Gear Body -> Hub -> Bore. 
# Let's do: 
# 1. Gear Outer Body (Teeth)
# 2. Hub (Cylinder inside)
# 3. Bore (Hole through center)
# Actually, for a single solid, order doesn't matter for the final shape, but topology might.
# Let's create the gear teeth first.

# --- Step 2: Gear Teeth Profile Sketch ---
sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0)) # Center on XY plane
sketch_teeth.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
sketch_teeth.MapMode = "FlatFace"
sketch_teeth.ConstrainAuto = False
sketch_teeth.OuterSketch = False
sketch_teeth.ConstrainAuto = False

# We need to draw the gear profile.
# Coordinate system: Center at (0,0). X axis along the radius.
# We need a closed profile.
# Points:
# 1. Base of tooth (root) on one side
# 2. Tip of tooth
# 3. Base of tooth on other side
# 4. Bottom of root (pitch circle minus dedendum)

# Calculations for one tooth half (symmetric)
# Center at (0,0)
# Root radius: root_diameter / 2
# Tip radius: outer_diameter / 2
# We need the transition angle (fillet radius).
# Standard fillet radius r_f = 0.38 * m (approx). Let's use a standard value or calculate based on pressure angle.
# Common practice: r_f = 0.38 * m.
r_f = 0.38 * params["gear_module"]

# Coordinates for the profile (drawing from root to tip to root):
# We will draw a polyline and add fillets.
# Point A: Root radius on X axis (Right side of gear) -> (root_r, 0)
# Point B: Tip radius on X axis (Right side of gear) -> (outer_r, 0)
# Point C: Tip radius on Y axis (Top of tooth) -> (0, outer_r)
# Point D: Root radius on Y axis (Top of gear) -> (0, root_r)
# Wait, this is just a circle sector. We need the involute shape.
# Approximating with a 3-point arc for simplicity in script or generating involute points.
# For a robust script, generating involute points is better.

def get_involute_point(pressure_angle_deg, r_b, theta_deg):
    """Returns (x, y) on involute starting from base circle."""
    pa_rad = pressure_angle_deg * pi / 180
    rb = r_b
    theta_rad = theta_deg * pi / 180
    
    # Involute equations:
    # t = sqrt(theta^2 - sin^2(theta)) ... no, simpler parametric form:
    # x = rb * (cos(t) + t*sin(t))
    # y = rb * (sin(t) - t*cos(t))
    # where t is the unwrapping angle.
    # We want the point at a specific angle 'theta_rad' from the base circle normal?
    # Actually, we want the point at polar angle 'theta_rad' on the pitch circle? 
    # No, we want the profile defined by the angle from the base circle tangent point.
    # Let's use the standard parameterization:
    # phi is the angle of the tangent.
    # x = rb * (cos(phi) + phi * sin(phi))
    # y = rb * (sin(phi) - phi * cos(phi))
    # The polar angle alpha of the point is: alpha = phi - sin(phi)/cos(phi)? No.
    # alpha = arctan( (y)/(x) ) = arctan( (sin(phi) - phi*cos(phi)) / (cos(phi) + phi*sin(phi)) )
    # This is complex to invert.
    
    # Alternative: Define the tooth profile by key points.
    # 1. Start at Base Circle (tangent point)
    # 2. Go to Pitch Circle
    # 3. Go to Addendum Circle
    # We will define the profile by a series of points and arcs.
    
    # Let's use a simpler approach: Define the profile by the "Tooth Space" and "Tooth" arcs.
    # Since it's a spur gear, we can generate the points for one tooth and mirror it.
    
    # Let's calculate points for the right half of a tooth (from center X to top Y).
    # Actually, let's just define the full tooth shape using `Part.makePoly` with calculated vertices.
    
    # We need the angle of the tooth half-width.
    # Circular pitch p = pi * m.
    # Tooth thickness at pitch circle = p / 2.
    # Half angle at pitch circle = (p/2) / (pitch_radius).
    half_angle_pitch = (params["circular_pitch"] / 2) / (params["pitch_diameter"] / 2)
    
    # We will generate a path from the center line (Y axis) to the tip (X axis)? 
    # No, let's define the profile relative to the tooth centerline (Y axis).
    # Points:
    # 1. (0, -root_r) -> Bottom of root (on Y axis, below center)
    # 2. (0, root_r) -> Top of root (on Y axis, above center)
    # 3. (outer_r, outer_r) -> Tip corner? No, involute.
    # Let's generate the involute curve for the tooth.
    
    pass

# Let's implement the gear generation logic inside the sketch creation.
# We will create a sketch that defines the profile of ONE tooth, then use a polar pattern.
# Or, we can define the entire gear profile in one sketch? 
# Polar patterning a single tooth is easier to manage dimensions.
# Let's create a sketch "Sketch_ToothProfile" containing just one tooth.
# Then we will use "PartDesign::PolarPattern" to create the gear.
# Wait, the prompt asks for "exactly one solid body". 
# If we pattern the tooth, we get many pads. That's fine, they are in one Body.
# But patterning a sketch *is* a feature. 
# So: Sketch (1 tooth) -> Pad -> PolarPattern.
# This works.

# --- Step 2.1: Single Tooth Sketch ---
sketch_tooth = body.newObject("Sketcher::SketchObject", "Sketch_Tooth")
sketch_tooth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_tooth.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
sketch_tooth.MapMode = "FlatFace"

# We will draw the profile of one tooth.
# Let's define the profile relative to the Y-axis (centerline of tooth).
# We need the involute function.
# Let's create points for the right half of the tooth (from centerline to tip) and mirror it.
# Actually, let's just draw the full closed loop of one tooth.
# We'll use a loop of points: 
# 1. Start at bottom of root (0, -root_r)
# 2. Move up along Y axis to (0, root_r) -> This is the root width/2? 
#    No, the root is flat or rounded. Standard gear has a fillet at the root.
#    Let's assume a fillet at the root.
# 3. Involute from root to tip.
# 4. Top fillet at tip.
# 5. Involute back to other side.

# To keep the script self-contained and robust without complex numerical inversion of involute angles:
# We will use the standard approximation of generating the tooth profile using the Base Circle and Pitch Circle intersections.
# Or, simpler: Use the `Part.makeHelicalWire`? No, that's for helices.
# Let's use a parametric loop to generate the involute points.

# Involute Parameterization:
# x = rb * (cos(phi) + phi * sin(phi))
# y = rb * (sin(phi) - phi * cos(phi))
# Here phi is the angle of the tangent to the base circle.
# The angle of the point from the X-axis (alpha) is:
# alpha = atan2(y, x)
# We need to find phi such that alpha matches our desired tooth angle.
# Alternatively, we can define the profile by specifying the angle of the tooth flank.
# The tooth flank is tangent to the base circle.
# The angle of the tangent is phi.
# The angle of the normal is phi.
# The angle of the radius vector to the point is phi - arcsin(rb/r)? No.
# The angle of the radius vector (alpha) = phi - arcsin(sin(phi)/sqrt(1+phi^2))? No.
# Relationship: alpha = phi - sin(phi) (in radians if phi is the angle of the tangent? No).
# Correct relation: alpha = phi - sin(phi) is for cycloid?
# For involute: The angle subtended by the arc from the base circle start is phi.
# The polar angle alpha of the point is: alpha = phi - sin(phi) ??? No.
# Let's use the formula: 
# x = r_b * (cos(phi) + phi * sin(phi))
# y = r_b * (sin(phi) - phi * cos(phi))
# The angle alpha = atan2(y, x).
# We want to generate points along the tooth.
# Let's iterate phi from 0 to some max value.
# phi = 0 -> x = r_b, y = 0. This is the start of the involute on the X-axis.
# As phi increases, the point moves counter-clockwise.
# We need the tooth to be symmetric around the Y-axis (in our sketch coordinate system where X is the gear rotation axis? No, Z is rotation).
# In our sketch (XY plane), Z is up. Rotation is around Z.
# The tooth centerline will be the Y axis (or X axis). Let's use Y axis.
# So the tooth spans from -angle_tooth to +angle_tooth.

# Let's generate the profile of the tooth.
# We'll create a wire with multiple segments:
# 1. Line from (0, -root_r) to (0, root_r) ? No, root is rounded.
#    Let's use a small fillet at the root.
# 2. Involute from (0, root_r) to (0, outer_r)? No, involute starts at base circle.
#    Base circle radius = base_diameter / 2.
#    Root radius = root_diameter / 2.
#    If root_r < base_r, the root is inside the base circle. The tooth flank is straight (base circle) then involute?
#    No, the tooth flank is involute from base circle.
#    If we cut below the base circle, it's a "hollow tooth" (bad).
#    Usually, root radius is slightly less than base radius, but the flank is still involute from the base circle.
#    Wait, if root_r < base_r, the involute starts at base_r and we have a flat or rounded bottom.
#    So: 
#    - Start at Base Circle (angle 0 relative to tooth centerline).
#    - Go along involute to Pitch Circle.
#    - Go along involute to Addendum Circle.
#    - Top fillet.
#    - Mirror.
#    - Root fillet.

# Let's define the points for the RIGHT HALF of the tooth (from Y-axis to X-axis? No, from Y-axis to the flank).
# Let's assume the tooth centerline is the Y-axis.
# We want to draw from (0, root_r) to (0, outer_r) via the flank.
# Actually, let's draw the profile of the TOOTH SPACE (the gap) and then invert? No, Pad adds material.
# We need the TOOTH profile (solid).
# Profile:
# 1. Start at bottom of root on Y-axis: (0, -root_r)
# 2. Fillet to start of involute.
# 3. Involute up to top of root on Y-axis: (0, root_r).
# 4. Top fillet.
# 5. Involute down to tip? No, we need the outer boundary.
# Let's restart the coordinate system for the sketch.
# Center of gear = (0,0).
# Tooth centerline = Y axis.
# Points to define:
# A: Bottom of root (0, -root_r)
# B: Top of root (0, root_r)
# C: Tip of tooth (outer_r, 0) ? No, the tooth has width.
# The tooth occupies the space between the flanks.
# Flank 1 (Right): From (0, root_r) to (outer_r, 0) roughly.
# Flank 2 (Left): From (0, root_r) to (-outer_r, 0) roughly.
# Wait, the tooth is the material BETWEEN the flanks.
# So the profile is:
# Start at (0, -root_r).
# Go to (0, root_r) via the root fillet? No, the root is the valley.
# The tooth profile is the boundary of the material.
# So we need the profile of the TOOTH.
# The tooth boundary consists of:
# 1. Left Flank
# 2. Right Flank
# 3. Top Fillet
# 4. Bottom Fillet
# AND the connection
