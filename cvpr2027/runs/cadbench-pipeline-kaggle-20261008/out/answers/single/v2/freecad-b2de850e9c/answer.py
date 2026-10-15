import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# --- Parameters ---
# Gear Geometry
pressure_angle_deg = 20.0
gear_module = 1.5
number_of_teeth = 50
pitch_diameter = 75.0
outer_diameter = 78.0
face_width = 15.0
hub_diameter = 45.0
hub_width = 10.0
shaft_diameter = 10.0
overall_width = 25.0

# Calculated ISO/DIN values
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
root_diameter = pitch_diameter - (2 * dedendum)

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create Parameter Set for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.gear_module = gear_module
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.face_width = face_width
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Diameter")
params.hub_diameter = hub_diameter
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.hub_width = hub_width
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
params.shaft_diameter = shaft_diameter
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.overall_width = overall_width
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Teeth Count")
params.number_of_teeth = number_of_teeth
params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "Pressure Angle")
params.pressure_angle_deg = pressure_angle_deg

# --- Sketch 1: Gear Tooth Profile ---
# We define the profile in the XY plane. 
# The gear will be created by revolving this profile around the Z axis.
# Coordinate system: Origin at center of pitch circle.
# X axis points to the right (tangent to pitch circle at 0 deg).
# Y axis points up (radial direction).

sketch_gear = body.newObject("Sketcher::SketchObject", "Sketch_GearProfile")
sketch_gear.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_gear.ConstrainToCurrentPlane = True
sketch_gear.Plane = "XY_Plane"
sketch_gear.MapMode = "FlatFace"

# Helper to add geometry
def add_line(p1, p2, is_constraint=False):
    sketch_gear.addGeometry(Part.LineSegment(p1, p2), is_constraint)

def add_circle(center, radius, is_constraint=False):
    sketch_gear.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constraint)

# --- Define Tooth Profile Points ---
# We will construct one tooth profile and then use a Polar Pattern to create the gear.
# The profile will be defined relative to the center of the tooth.
# However, for a clean revolution, it's often easier to define the profile 
# starting from the center of the gear and going out, or define the tooth 
# relative to the pitch circle and use a specific placement.
# 
# Strategy: Define the profile of ONE tooth relative to the center of the gear,
# but shifted so the revolution works correctly. 
# Actually, the standard way in PartDesign for gears is to sketch the profile 
# of a single tooth, place it at the correct angle (usually 0 or 90), and pattern it.
# 
# Let's define the profile of a single tooth.
# Tooth thickness at pitch circle = pi * module / number_of_teeth
# Tooth thickness = 3.14159 * 1.5 / 50 = 0.0942 mm
# Half thickness = 0.0471 mm
# Pitch Radius = 37.5 mm
# Addendum Radius = 37.5 + 1.5 = 39.0 mm
# Root Radius = 37.5 - 1.875 = 35.625 mm

# Let's place the tooth such that its centerline is at 0 degrees (along X axis).
# The profile will be symmetric around the X axis.
# Points:
# 1. Root start (inner radius, -half_thickness)
# 2. Root end (inner radius, +half_thickness)
# 3. Fillet start (inner radius, +half_thickness) -> Fillet to addendum
# 4. Fillet end (addendum radius, +half_thickness)
# 5. Tip end (addendum radius, +half_thickness)
# 6. Tip start (addendum radius, -half_thickness)
# 7. Fillet start (addendum radius, -half_thickness) -> Fillet to root
# 8. Fillet end (inner radius, -half_thickness)
# 9. Root start (inner radius, -half_thickness) - Close loop

# Wait, standard gear tooth profile involves:
# - Root fillet (concave)
# - Flank (straight line at pressure angle)
# - Tip (straight line)
# - Tip fillet (concave)
# 
# Let's simplify for a robust script:
# 1. Draw the involute/flank lines.
# 2. Draw the tip line.
# 3. Draw the root line.
# 4. Add fillets.

# Tooth Geometry Constants
pitch_radius = pitch_diameter / 2.0
addendum_radius = pitch_radius + addendum
root_radius = pitch_radius - dedendum
tooth_thickness = (Part.pi * gear_module) / number_of_teeth
half_thickness = tooth_thickness / 2.0

# Pressure angle in radians
pressure_angle_rad = pressure_angle_deg * (Part.pi / 180.0)

# Coordinates for the tooth profile (symmetric around X axis)
# We define the profile from the center of the tooth (X=0, Y=0) outwards? 
# No, let's define the profile of the TOOTH itself.
# The tooth occupies X from -half_thickness to +half_thickness at the pitch circle.
# But the profile is curved.
# 
# Let's define the profile points explicitly:
# Point A: Root corner (root_radius, -half_thickness)
# Point B: Root corner (root_radius, +half_thickness)
# Point C: Fillet start (root_radius, +half_thickness)
# Point D: Fillet end (addendum_radius, +half_thickness)
# Point E: Tip corner (addendum_radius, +half_thickness)
# Point F: Tip corner (addendum_radius, -half_thickness)
# Point G: Fillet start (addendum_radius, -half_thickness)
# Point H: Fillet end (root_radius, -half_thickness)
# Point I: Root corner (root_radius, -half_thickness)

# Actually, the flanks are straight lines at the pressure angle.
# The pressure angle is measured from the tangent to the pitch circle.
# So the flank line makes an angle of (90 - pressure_angle) with the radial line?
# No, the pressure angle is the angle between the line of action and the tangent.
# The flank line is tangent to the base circle.
# Base radius = pitch_radius * cos(pressure_angle)
# Base radius = 37.5 * cos(20) = 35.16 mm
# 
# Let's construct the profile using lines and arcs.
# 1. Line from Root (root_radius, -half_thickness) to (BaseRadius, -half_thickness)? No.
# The standard simplified profile:
# - Root circle arc (concave)
# - Flank line (straight)
# - Tip line (straight)
# - Tip fillet (convex)
# - Root fillet (concave)

# Let's try a simpler approach often used in CAD for gears:
# Define the profile of the tooth space (the gap) or the tooth.
# Let's define the TOOTH profile.
# 
# Start at the bottom of the tooth (root level, left side of tooth).
# X = -half_thickness, Y = -root_radius? No, Y is radial.
# Let's use a coordinate system where X is radial (outward) and Y is tangential.
# This is confusing. Let's stick to standard XY plane where X is horizontal, Y is vertical.
# We will rotate the sketch later or place it correctly.
# 
# Let's define the profile of ONE tooth centered at (0,0) in the sketch plane?
# No, if we revolve a profile centered at (0,0), we get a solid of revolution.
# If the profile is the tooth shape, we need to position it correctly.
# 
# Correct Approach:
# 1. Create a sketch.
# 2. Draw the profile of a single tooth.
# 3. Place the profile such that its centerline is at 0 degrees (along X axis).
# 4. Revolve 360 degrees.
# 
# Tooth Profile Points (X, Y) where X is radial distance from center, Y is tangential offset.
# Wait, if we revolve around Z, the profile must be in the XZ or XY plane.
# If we use XY plane, X is radial, Y is tangential.
# 
# Tooth Profile:
# - Root Circle: Radius = root_radius. Arc from -half_thickness to +half_thickness.
# - Flank: Line from (root_radius, -half_thickness) to (base_radius, -half_thickness)? 
#   Actually, the flank is tangent to the base circle.
#   The base circle radius is Rb = pitch_radius * cos(alpha).
#   The flank line starts at the base circle and goes outwards.
#   The angle of the flank line with the radial line is alpha (pressure angle).
#   So the slope in (X, Y) coordinates (X=radial, Y=tangential):
#   dy/dx = tan(alpha).
#   So Y = X * tan(alpha) + C.
#   At the base circle (X=Rb), Y = -half_thickness (for the bottom flank).
#   So -half_thickness = Rb * tan(alpha) + C => C = -half_thickness - Rb * tan(alpha).
#   Equation: Y = X * tan(alpha) - half_thickness - Rb * tan(alpha).
#   This line goes from X=Rb to X=addendum_radius.
# 
# - Tip: Line from (addendum_radius, -half_thickness) to (addendum_radius, +half_thickness).
# 
# - Top Fillet: Connects (addendum_radius, +half_thickness) to (root_radius, +half_thickness)?
#   No, usually there is a fillet at the tip and root.
#   Let's add a fillet at the tip corner (addendum_radius, +half_thickness) with radius = 0.2*module?
#   And a fillet at the root corner (root_radius, -half_thickness).
# 
# Let's refine the points:
# P1: (root_radius, -half_thickness)
# P2: (addendum_radius, -half_thickness) -> This is the end of the flank?
#    No, the flank ends at the base circle? No, the flank is the side of the tooth.
#    The flank goes from the root fillet to the tip fillet.
#    The flank is a straight line.
#    It starts at the intersection of the root fillet and the root circle?
#    Or does it start at the base circle?
#    Ideally, the flank is tangent to the base circle.
#    So the flank line starts at (Rb, Y_base).
#    But for a simple sketch, we can just draw the line from (root_radius, -half_thickness) 
#    to (addendum_radius, -half_thickness) and then fillet the corners?
#    That creates a rectangular tooth, not a gear.
#    
#    Let's do the proper geometry:
#    1. Draw the base circle (Rb).
#    2. Draw the flank line tangent to the base circle at the correct angle.
#       Angle of tangent: 90 - alpha (relative to radial).
#       In (X, Y) coords: slope = tan(alpha).
#       Line: Y = X * tan(alpha) + C.
#       Passes through (Rb, -half_thickness).
#    3. Draw the tip line at X = addendum_radius.
#    4. Draw the root line at Y = -half_thickness? No, root is an arc.
#    
#    Let's simplify:
#    We will draw the profile of the tooth.
#    Points:
#    A: (root_radius, -half_thickness)
#    B: (addendum_radius, -half_thickness) -- This is the bottom of the tooth at the tip? No.
#       The tooth has a width.
#       The bottom of the tooth (root) is at Y = -half_thickness.
#       The top of the tooth (tip) is at Y = +half_thickness.
#       The sides are the flanks.
#       
#    Let's define the profile as the area between the two flanks and the tip/root circles.
#    Actually, let's just draw the outline of the tooth.
#    
#    Start at (root_radius, -half_thickness).
#    Go to (addendum_radius, -half_thickness) -> This is the bottom of the tooth? No.
#    The tooth is the solid part.
#    The profile is the boundary of the tooth.
#    
#    Boundary:
#    1. Root Arc: From (root_radius, -half_thickness) to (root_radius, +half_thickness).
#       Wait, the root is a circle. The tooth sits on the root circle.
#       So the bottom of the tooth is the root circle arc.
#       But the tooth has thickness.
#       So the root of the tooth is the arc of the root circle from -half_thickness to +half_thickness.
#    2. Flank: From (root_radius, +half_thickness) to (addendum_radius, +half_thickness).
#       This is the side of the tooth.
#       It should be a straight line tangent to the base circle.
#    3. Tip: From (addendum_radius, +half_thickness) to (addendum_radius, -half_thickness).
#    4. Flank: From (addendum_radius, -half_thickness) to (root_radius, -half_thickness).
#    
#    This creates a trapezoid-like shape with rounded corners.
#    Let's implement this.
    
# Constants for sketch
Rb = pitch_radius * (App.Vector(0, 0, 1).Dot(App.Vector(0, 0, 1))) # Just a placeholder, calc below
Rb = pitch_radius * App.cos(pressure_angle_rad)

# Points
P_root_start = App.Vector(root_radius, -half_thickness, 0)
P_root_end = App.Vector(root_radius, half_thickness, 0)
P_flank_start = App.Vector(root_radius, half_thickness, 0)
P_flank_end = App.Vector(addendum_radius, half_thickness, 0)
P_tip_end = App.Vector(addendum_radius, half_thickness, 0)
P_tip_start = App.Vector(addendum_radius, -half_thickness, 0)
P_flank_start_bot = App.Vector(addendum_radius, -half_thickness, 0)
P_flank_end_bot = App.Vector(root_radius, -half_thickness, 0)

# Calculate the intersection of the flank line with the root circle?
# The flank line is tangent to the base circle.
# Line equation: Y = X * tan(alpha) + C
# Passes through (Rb, -half_thickness)
# -half_thickness = Rb * tan(alpha) + C
# C = -half_thickness - Rb * tan(alpha)
# So the line is Y = X * tan(alpha) - half_thickness - Rb * tan(alpha)
# 
# We need to find where this line intersects the root circle (X = root_radius)?
# Y_intersect = root_radius * tan(alpha) - half_thickness - Rb * tan(alpha)
# Y_intersect = (root_radius - Rb) * tan(alpha) - half_thickness
# Note: root_radius - Rb = pitch_radius - dedendum - pitch_radius * cos(alpha)
#       = pitch_radius * (1 - cos(alpha)) - dedendum
#       = pitch_radius * (1 - cos(alpha)) - 1.25 * module
#       This might be negative?
#       Let's check values:
#       pitch_radius = 37.5
#       cos(20) = 0.9397
#       Rb = 35.16
#       root_radius = 35.625
#       root_radius - Rb = 0.465
#       tan(20) = 0.364
#       (0.465 * 0.364) - 0.0471 = 0.169 - 0.047 = 0.122
#       So the flank line intersects the root circle at Y = 0.122.
#       But our root is defined from -0.047 to +0.047.
#       So the flank line is outside the root circle range?
#       Yes, the flank line starts at the base circle (3
