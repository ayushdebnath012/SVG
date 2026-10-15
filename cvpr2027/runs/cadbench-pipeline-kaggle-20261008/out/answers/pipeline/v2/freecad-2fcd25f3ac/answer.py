import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from the prompt requirements
PRESSURE_ANGLE_DEG = 20.0
GEAR_MODULE = 1.0
NUMBER_OF_TEETH = 18
PITCH_DIAMETER = 18.0
OUTER_DIAMETER = 20.0
FACE_WIDTH = 10.0
HUB_DIAMETER = 14.0
HUB_WIDTH = 10.0
SHAFT_DIAMETER = 6.0
OVERALL_WIDTH = 20.0

# Calculated parameters based on ISO/DIN standards provided in prompt
PRESSURE_ANGLE = math.radians(PRESSURE_ANGLE_DEG)
ADDENDUM = PITCH_DIAMETER / NUMBER_OF_TEETH
DEDENDUM = 1.25 * GEAR_MODULE
WHOLE_DEPTH = ADDENDUM + DEDENDUM
ROOT_DIAMETER = PITCH_DIAMETER - 2 * DEDENDUM
CIRCULAR_PITCH = math.pi * GEAR_MODULE
BASE_DIAMETER = PITCH_DIAMETER * math.cos(PRESSURE_ANGLE)

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold our named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "gear module")
params.module = GEAR_MODULE
params.addProperty("App::PropertyInteger", "teeth", "Dimensions", "number of teeth")
params.teeth = NUMBER_OF_TEETH
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "gear face width")
params.face_width = FACE_WIDTH
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "hub diameter")
params.hub_diameter = HUB_DIAMETER
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "hub width")
params.hub_width = HUB_WIDTH
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "bore diameter")
params.shaft_diameter = SHAFT_DIAMETER
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "total width")
params.overall_width = OVERALL_WIDTH
params.addProperty("App::PropertyLength", "pressure_angle", "Dimensions", "pressure angle (deg)")
params.pressure_angle = PRESSURE_ANGLE_DEG

# --- Sketch 1: Gear Profile (Side View) ---
# This sketch defines the cross-section of the gear teeth, hub, and bore.
sketch_profile = body.newObject("Sketcher::SketchObject", "Sketch_Profile")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Support = [App.getDocument("SpurGear").getObject("XY_Plane")]
sketch_profile.MapMode = "FlatFace"

# Define key points for the profile (X, Y)
# Center is (0,0). Y is vertical (height), X is horizontal (width).
# We will draw a closed loop.
# Points:
# 1. Bottom of bore
# 2. Top of bore
# 3. Top of hub (inner)
# 4. Top of hub (outer)
# 5. Top of gear (outer)
# 6. Top of gear (inner)
# 7. Top of gear (outer) - wait, let's trace the perimeter carefully.

# Let's define the profile as a series of lines and circles.
# The profile is symmetric about the X-axis (horizontal).
# We will draw the top half and close it, or draw the full loop.
# Let's draw the full loop starting from bottom-left of bore.

# Coordinates:
# Bore Radius = shaft_diameter / 2
# Hub Inner Radius = hub_diameter / 2
# Hub Outer Radius = hub_diameter / 2 (Wait, hub is a cylinder, so inner and outer radii are same? No.)
# Hub is a cylinder of diameter hub_diameter. The gear teeth sit on top of this cylinder.
# So the profile goes:
# - Up from bore bottom to bore top (Circle)
# - Up from bore top to hub top (Line)
# - Out from hub top to gear top (Line)
# - Down the gear tooth flank (Line)
# - Down the gear tooth root (Line)
# - In to the other side...

# Actually, standard gear profile generation in 2D sketch:
# 1. Base circle arc? No, usually involute is approximated or generated via spline/lines.
# For a simple script, we can use the standard ISO tooth profile approximation with lines and arcs.
# However, to keep it robust and editable, we will construct the profile using:
# - A circle for the bore.
# - A circle for the root diameter (if we treat it as a fillet, but it's a sharp root usually).
# - Lines for the addendum and dedendum.
# - Lines for the pressure angle flanks.

# Let's define the profile points explicitly.
# Origin (0,0) is center.
# We draw the right half and mirror it, or draw the full loop.
# Let's draw the full loop.

# 1. Bore Circle
sketch_profile.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaft_diameter / 2), False)

# 2. Hub Top Line (from bore top to hub outer edge)
# Hub is a cylinder. The profile goes up the bore, then up the hub side?
# No, the hub is a cylinder of diameter HUB_DIAMETER. The bore is inside it.
# The gear teeth are on the outside of the hub.
# So the profile goes:
# - Up the bore (Circle)
# - Up the hub side wall? No, the hub is solid. The profile is the outer boundary.
# - The outer boundary goes up the hub side (radius = hub_diameter/2) until it hits the gear face.
# - Then it goes out to the gear outer diameter.
# - Then down the gear tooth.

# Let's refine the geometry:
# The "Hub" is a cylinder of diameter HUB_DIAMETER and width HUB_WIDTH.
# The "Gear Body" is a cylinder of diameter OUTER_DIAMETER and width FACE_WIDTH.
# The gear teeth are on the face of the gear body.
# The bore is in the center.

# Profile Path (Right Side):
# Start at bottom of bore: (0, -shaft_diameter/2)
# Go up to top of bore: (0, shaft_diameter/2) -> Circle
# Go up to top of hub: (0, shaft_diameter/2) to (0, hub_diameter/2) -> Line
# Go out to gear outer radius: (0, hub_diameter/2) to (outer_diameter/2, hub_diameter/2) -> Line
# Go down the tooth flank: (outer_diameter/2, hub_diameter/2) to (outer_diameter/2, root_diameter/2) -> Line
# Go in along the root: (outer_diameter/2, root_diameter/2) to (-outer_diameter/2, root_diameter/2) -> Line
# Go up the other tooth flank: (-outer_diameter/2, root_diameter/2) to (-outer_diameter/2, hub_diameter/2) -> Line
# Go in to hub top: (-outer_diameter/2, hub_diameter/2) to (0, hub_diameter/2) -> Line
# Go down hub side: (0, hub_diameter/2) to (0, shaft_diameter/2) -> Line
# Close loop.

# Wait, the gear teeth are distributed around the pitch circle.
# The profile above describes a single tooth or the whole gear?
# The prompt asks for "A spur gear". This implies the full gear with all teeth.
# We cannot draw 18 individual teeth in a single sketch easily without a pattern or complex spline.
# Standard practice in FreeCAD PartDesign for gears:
# 1. Create a sketch of ONE tooth profile.
# 2. Use a Polar Pattern to replicate it.
# 3. Use a Pad to extrude the whole thing.
# BUT, the prompt says "producing exactly one solid body".
# If we pattern the sketch, the Pad will create one solid body containing all teeth.
# This is the correct approach.

# So, Sketch_Profile will contain ONE tooth profile.
# We need to position this tooth correctly.
# Let's define the tooth profile relative to the center of the tooth.
# Tooth Center X = 0.
# Tooth Root extends from -half_tooth_width to +half_tooth_width.
# Tooth Top extends from -half_tooth_width to +half_tooth_width.

# Calculations for ONE tooth:
# Pitch Radius = PITCH_DIAMETER / 2
# Base Radius = BASE_DIAMETER / 2
# Addendum = ADDENDUM
# Dedendum = DEDENDUM
# Whole Depth = WHOLE_DEPTH

# Tooth Geometry (Simplified ISO approximation):
# 1. Root Line: Horizontal line at Y = -Dedendum (relative to pitch circle? No, relative to base).
#    Standard: Root diameter is constant.
#    Let's set the coordinate system such that the Pitch Circle is at Y=0?
#    Or let's set the center of the tooth at (0,0).
#    Let's set the center of the tooth at (0,0).
#    Root Y = -Dedendum.
#    Pitch Y = 0.
#    Top Y = Addendum.

# Tooth Width at Pitch Circle:
# Circular Pitch = pi * module.
# Tooth Width (space) = Circular Pitch / 2.
# Tooth Width (tooth) = Circular Pitch / 2.
# So half-tooth-width = Circular Pitch / 4.

# Let's define the points for the tooth profile (Right Half):
# 1. Top Outer Corner: (half_tooth_width, Addendum)
# 2. Top Inner Corner: (-half_tooth_width, Addendum)
# 3. Root Outer Corner: (half_tooth_width, -Dedendum)
# 4. Root Inner Corner: (-half_tooth_width, -Dedendum)

# We need to connect these with the correct angles.
# Pressure Angle = 20 deg.
# The flank lines should be at 20 deg to the radial line.
# Since we are at the pitch circle (Y=0), the radial line is vertical.
# So the flank lines should be at 20 deg from vertical.
# Slope = tan(90 - 20) = tan(70) ?
# If the tooth is centered at X=0, the flank goes from (0,0) to (half_tooth_width, Addendum)?
# No, the involute starts at the base circle.
# For a simple script, we approximate the flank as a straight line from the Pitch Circle to the Top.
# Angle of the flank relative to the vertical (radial) is the pressure angle.
# So the line goes from (0,0) to (half_tooth_width, Addendum) with an angle of 20 deg from vertical.
# X = r * sin(alpha), Y = r * cos(alpha).
# At Y = Addendum, X = Addendum * tan(alpha).
# Let's check if this matches the tooth width.
# Usually, the tooth width at the pitch circle is defined by the circular pitch.
# Let's stick to the standard dimensions given:
# Tooth Width at Pitch Circle = Circular Pitch / 2.
# So half_width = Circular Pitch / 4.
# The flank line connects (0,0) to (half_width, Addendum).
# The angle of this line is atan(Addendum / half_width).
# Let's calculate the angle: atan(1 / (3.14159/4)) = atan(1.27) = 51 deg.
# This is not 20 deg.
# The 20 deg pressure angle is the angle between the line of action and the tangent to the pitch circle.
# In the tooth profile, the pressure angle is the angle between the tooth flank and the radial line at the pitch point.
# So the flank line should make an angle of 20 deg with the vertical.
# This means at Y=Addendum, the X coordinate would be Addendum * tan(20).
# 1 * tan(20) = 0.364.
# But the required half-width is 3.14159 / 4 = 0.785.
# There is a discrepancy between a simple straight line approximation and the exact circular pitch width if we strictly follow the pressure angle from the center.
# However, the standard ISO gear tooth profile is an involute.
# To keep the script simple and editable, we will construct the profile using:
# - A line for the dedendum (root).
# - A line for the addendum (top).
# - A line for the flank.
# We will force the flank to be at the pressure angle relative to the vertical.
# This will result in a tooth width slightly different from the exact circular pitch, but it's a valid geometric representation for a "spur gear" model in a script.
# Alternatively, we can define the width based on circular pitch and calculate the angle.
# Let's use the Circular Pitch to define the width, and the Pressure Angle to define the shape of the flank.
# We will draw the flank from the Pitch Circle (0,0) to the Top (half_width, Addendum).
# The angle will be atan(Addendum / half_width).
# This is the most robust way to ensure the gear meshes correctly (width-wise).
# The "Pressure Angle" parameter in the prompt is primarily for defining the shape, but if we fix the width, the angle is fixed.
# Let's assume the prompt wants us to use the calculated values.
# We will use the calculated `half_width` and `Addendum` to draw the lines.

# Let's refine the sketch points for ONE tooth:
# Center of tooth at (0,0).
# Pitch Circle Y = 0.
# Root Y = -Dedendum.
# Top Y = Addendum.
# Half Width = Circular Pitch / 4.

# Points:
# A: Top Outer (half_width, Addendum)
# B: Top Inner (-half_width, Addendum)
# C: Root Outer (half_width, -Dedendum)
# D: Root Inner (-half_width, -Dedendum)

# We will draw:
# 1. Line from B to A (Top)
# 2. Line from A to C (Flank)
# 3. Line from C to D (Root)
# 4. Line from D to B (Flank)
# 5. Close loop.

# Wait, the root is usually a fillet or a sharp corner.
# The prompt mentions "root_diameter".
# We will draw a sharp corner for simplicity, or a small fillet.
# Let's draw sharp corners for the profile sketch, then maybe fillet later if needed.
# Actually, the prompt asks for "exactly one solid body".
# We will create the sketch, then pattern it, then pad it.

# Let's create the sketch geometry.
# We need to place the tooth at the correct radius.
# The tooth profile is drawn in the sketch plane.
# We will place the sketch at the center (0,0,0) and the tooth centered at (0,0).
# Then we will use a Polar Pattern on the Pad?
# No, we pattern the Sketch itself?
# If we pattern the sketch, we get multiple sketches.
# We want ONE sketch with ONE tooth, then pattern the PAD.
# Correct workflow:
# 1. Sketch: One tooth profile.
# 2. Pad: Extrude the sketch.
# 3. Polar Pattern: Pattern the Pad.

# Let's define the sketch points again.
# We need to ensure the tooth is centered at (0,0).
# Points:
# P1: (half_width, Addendum)
# P2: (-half_width, Addendum)
# P3: (-half_width, -Dedendum)
# P4: (half_width, -Dedendum)

# We will add these as lines.
# Also, we need to define the base circle?
# The prompt mentions base_diameter.
# We can add a circle for visualization or constraint, but it's not strictly needed for the solid if we use lines.
# Let's just use the lines to define the tooth.

# Coordinates:
# half_width = CIRCULAR_PITCH / 4
# top_y = ADDENDUM
# root_y = -DEDENDUM

# Let's add the geometry to the sketch.
# We need to reference the parameters.
# We can use expressions in the sketch geometry?
# FreeCAD Sketcher supports expressions in coordinates.
# Let's try to use expressions for the points.

# Point 1: (half_width, Addendum)
# Point 2: (-half_width, Addendum)
# Point 3: (-half_width, -Dedendum)
# Point 4: (half_width, -Dedendum)

# We will add 4 LineSegments.
# Line 1: P2 to P1
# Line 2: P1 to P4 (Flank)
# Line 3: P4 to P3 (Root)
# Line 4: P3 to P2 (Flank)

# Wait, the root is usually a flat line at the bottom.
# Yes, P3 to P4 is the root.
# P2 to P3 is the left flank.
# P1 to P4 is the right flank.
# P2 to P1 is the top.

#
