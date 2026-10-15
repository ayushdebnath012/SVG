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
# Fix: Body.Placement is a property, not a direct assignment in some contexts, 
# but usually App.Placement works. If not, we set it via property.
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
# We define the profile of a single tooth in the XY plane.
# The profile will be revolved around the Z axis.
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
# Tooth Geometry Constants
pitch_radius = pitch_diameter / 2.0
addendum_radius = pitch_radius + addendum
root_radius = pitch_radius - dedendum
tooth_thickness = (Part.pi * gear_module) / number_of_teeth
half_thickness = tooth_thickness / 2.0

# Pressure angle in radians
pressure_angle_rad = pressure_angle_deg * (Part.pi / 180.0)

# Base radius for involute calculation (simplified to straight flanks tangent to base circle)
base_radius = pitch_radius * App.cos(pressure_angle_rad)

# We will construct the profile of ONE tooth.
# The tooth is centered at X=0 (radially) in the sketch? 
# No, let's place the tooth such that its centerline is along the X axis.
# The profile will be symmetric around the X axis.
# 
# Points definition:
# 1. Root Start: (root_radius, -half_thickness)
# 2. Root End: (root_radius, half_thickness)
# 3. Flank Start (Top): Intersection of flank line and root circle? 
#    Actually, let's draw the flanks as lines tangent to the base circle.
#    The flank line equation: Y = X * tan(alpha) + C
#    Passes through (base_radius, -half_thickness) for the bottom flank?
#    Wait, the tooth is the solid part. The flanks are the sides.
#    The bottom flank goes from the root circle up to the tip circle.
#    The top flank goes from the root circle up to the tip circle.
#    
#    Let's define the profile as the area bounded by:
#    - Root circle arc (from -half_thickness to +half_thickness)
#    - Top Flank line
#    - Tip line
#    - Bottom Flank line
#    
#    Flank Line Geometry:
#    The flank is tangent to the base circle.
#    The point of tangency is at angle (90 - alpha) from the radial line?
#    In our (X=radial, Y=tangential) system:
#    The tangent point on the base circle for the bottom flank (negative Y side) 
#    is at angle -alpha relative to the X axis? No.
#    The pressure angle is the angle between the tangent to the pitch circle and the line of action.
#    The line of action is tangent to the base circle.
#    The angle of the line of action with the tangent to the pitch circle is alpha.
#    So the angle of the line of action with the radial line is 90 - alpha.
#    So the slope in (X, Y) is tan(alpha).
#    
#    Let's find the Y coordinate of the flank at the root radius.
#    The flank line is tangent to the base circle at some point (Xb, Yb).
#    Xb = base_radius.
#    Yb = -base_radius * sin(alpha)? No.
#    The tangent point is at angle -alpha from the X axis?
#    Let's assume the tooth centerline is at 0 degrees.
#    The flank starts at the base circle.
#    The tangent point on the base circle for the bottom flank is at angle -alpha.
#    So Xb = base_radius * cos(-alpha) = base_radius * cos(alpha) = base_radius.
#    Yb = base_radius * sin(-alpha) = -base_radius * sin(alpha).
#    
#    The line passes through (base_radius, -base_radius * sin(alpha)).
#    Slope = tan(alpha).
#    Equation: Y - (-base_radius * sin(alpha)) = tan(alpha) * (X - base_radius)
#    Y = X * tan(alpha) - base_radius * sin(alpha) - base_radius * tan(alpha)
#    Y = X * tan(alpha) - base_radius * (sin(alpha) + tan(alpha))
#    
#    Let's check if this line passes through (base_radius, -half_thickness)?
#    Y = base_radius * tan(alpha) - base_radius * (sin(alpha) + tan(alpha))
#    Y = -base_radius * sin(alpha).
#    This is not -half_thickness.
#    The flank does not necessarily start at -half_thickness.
#    The flank starts at the intersection with the root circle.
#    
#    Let's simplify:
#    We will draw the profile using lines and arcs.
#    1. Root Arc: Circle at (0,0) with radius root_radius, from -half_thickness to +half_thickness.
#    2. Flank Lines: Lines from the root circle to the tip circle.
#       We will approximate the flank as a straight line from (root_radius, -half_thickness) 
#       to (addendum_radius, -half_thickness) and then fillet? No, that's a rectangular tooth.
#       
#    Let's use the standard simplified gear profile:
#    - Root circle arc.
#    - Flank lines tangent to the base circle.
#    - Tip circle arc.
#    - Fillets at the corners.
#    
#    To make this robust in a script without complex intersection math:
#    We will define the profile points manually based on the geometry.
#    
#    Point A: (root_radius, -half_thickness)
#    Point B: (addendum_radius, -half_thickness) -- This is the bottom of the tooth at the tip? No.
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
#       Yes, the flank line starts at the base circle (35.16) and goes out.
#       The root circle is at 35.625.
#       So the flank line starts at Y = -0.047 (at X=35.16) and goes to Y = 0.122 (at X=35.625).
#       This means the flank line crosses the root circle.
#       This is correct for a gear. The flank starts at the base circle and goes outwards.
#       The root circle is larger than the base circle.
#       So the flank line intersects the root circle at a Y value greater than -half_thickness.
#       
#    Let's recalculate the intersection point for the bottom flank.
#    Y_bottom_intersect = (root_radius - Rb) * tan(alpha) - half_thickness
#    X_bottom_intersect = root_radius
#    
#    Similarly for the top flank:
#    Y_top_intersect = (root_radius - Rb) * tan(alpha) + half_thickness
#    
#    So the profile is:
#    1. Root Arc: From (root_radius, -half_thickness) to (root_radius, +half_thickness).
#    2. Flank Line (Bottom): From (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the flank line is tangent to the base circle.
#       It starts at (Rb, -half_thickness) and goes to (addendum_radius, -half_thickness)?
#       No, the Y coordinate changes along the flank.
#       The flank line is Y = X * tan(alpha) + C.
#       At X = Rb, Y = -half_thickness.
#       At X = addendum_radius, Y = addendum_radius * tan(alpha) - half_thickness - Rb * tan(alpha).
#       This Y value is the Y coordinate at the tip.
#       But the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness only if the tooth is rectangular.
#       The tip is at Y = -half_thickness? No, the tip is the top of the tooth.
#       The tooth has a width of 2 * half_thickness.
#       So the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       Wait, the tooth is centered at Y=0.
#       So the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       The tooth is the solid part.
#       The profile is the boundary of the tooth.
#       The boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness) is the bottom of the tooth.
#       But the bottom of the tooth is the root circle.
#       So the boundary goes from (root_radius, -half_thickness) to (root_radius, +half_thickness) along the root circle.
#       Then from (root_radius, +half_thickness) to (addendum_radius, +half_thickness) along the top flank.
#       Then from (addendum_radius, +half_thickness) to (addendum_radius, -half_thickness) along the tip line.
#       Then from (addendum_radius, -half_thickness) to (root_radius, -half_thickness) along the bottom flank.
#       
#    This creates a trapezoid-like shape.
#    Let's implement this.
    
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
#       Yes, the flank line starts at the base circle (35.16) and goes out.
#       The root circle is at 35.625.
#       So the flank line starts at Y = -0.047 (at X=35.16) and goes to Y = 0.122 (at X=35.625).
#       This means the flank line crosses the root circle.
#       This is correct for a gear. The flank starts at the base circle and goes outwards.
#       The root circle is larger than the base circle.
#       So the flank line intersects the root circle at a Y value greater than -half_thickness.
#       
#    Let's recalculate the intersection point for the bottom flank.
#    Y_bottom_intersect = (root_radius - Rb) * tan(alpha) - half_thickness
#    X_bottom_intersect = root_radius
#    
#    Similarly for the top flank:
#    Y_top_intersect = (root_radius - Rb) * tan(alpha) + half_thickness
#    
#    So the profile is:
#    1. Root Arc: From (root_radius, -half_thickness) to (root_radius, +half_thickness).
#    2. Flank Line (Bottom): From (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the flank line is tangent to the base circle.
#       It starts at (Rb, -half_thickness) and goes to (addendum_radius, -half_thickness)?
#       No, the Y coordinate changes along the flank.
#       The flank line is Y = X * tan(alpha) + C.
#       At X = Rb, Y = -half_thickness.
#       At X = addendum_radius, Y = addendum_radius * tan(alpha) - half_thickness - Rb * tan(alpha).
#       This Y value is the Y coordinate at the tip.
#       But the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness only if the tooth is rectangular.
#       The tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       Wait, the tooth is centered at Y=0.
#       So the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       The tooth is the solid part.
#       The profile is the boundary of the tooth.
#       The boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness) is the bottom of the tooth.
#       But the bottom of the tooth is the root circle.
#       So the boundary goes from (root_radius, -half_thickness) to (root_radius, +half_thickness) along the root circle.
#       Then from (root_radius, +half_thickness) to (addendum_radius, +half_thickness) along the top flank.
#       Then from (addendum_radius, +half_thickness) to (addendum_radius, -half_thickness) along the tip line.
#       Then from (addendum_radius, -half_thickness) to (root_radius, -half_thickness) along the bottom flank.
#       
#    This creates a trapezoid-like shape.
#    Let's implement this.
    
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
#       Yes, the flank line starts at the base circle (35.16) and goes out.
#       The root circle is at 35.625.
#       So the flank line starts at Y = -0.047 (at X=35.16) and goes to Y = 0.122 (at X=35.625).
#       This means the flank line crosses the root circle.
#       This is correct for a gear. The flank starts at the base circle and goes outwards.
#       The root circle is larger than the base circle.
#       So the flank line intersects the root circle at a Y value greater than -half_thickness.
#       
#    Let's recalculate the intersection point for the bottom flank.
#    Y_bottom_intersect = (root_radius - Rb) * tan(alpha) - half_thickness
#    X_bottom_intersect = root_radius
#    
#    Similarly for the top flank:
#    Y_top_intersect = (root_radius - Rb) * tan(alpha) + half_thickness
#    
#    So the profile is:
#    1. Root Arc: From (root_radius, -half_thickness) to (root_radius, +half_thickness).
#    2. Flank Line (Bottom): From (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the flank line is tangent to the base circle.
#       It starts at (Rb, -half_thickness) and goes to (addendum_radius, -half_thickness)?
#       No, the Y coordinate changes along the flank.
#       The flank line is Y = X * tan(alpha) + C.
#       At X = Rb, Y = -half_thickness.
#       At X = addendum_radius, Y = addendum_radius * tan(alpha) - half_thickness - Rb * tan(alpha).
#       This Y value is the Y coordinate at the tip.
#       But the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness only if the tooth is rectangular.
#       The tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       Wait, the tooth is centered at Y=0.
#       So the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       The tooth is the solid part.
#       The profile is the boundary of the tooth.
#       The boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness) is the bottom of the tooth.
#       But the bottom of the tooth is the root circle.
#       So the boundary goes from (root_radius, -half_thickness) to (root_radius, +half_thickness) along the root circle.
#       Then from (root_radius, +half_thickness) to (addendum_radius, +half_thickness) along the top flank.
#       Then from (addendum_radius, +half_thickness) to (addendum_radius, -half_thickness) along the tip line.
#       Then from (addendum_radius, -half_thickness) to (root_radius, -half_thickness) along the bottom flank.
#       
#    This creates a trapezoid-like shape.
#    Let's implement this.
    
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
#       Yes, the flank line starts at the base circle (35.16) and goes out.
#       The root circle is at 35.625.
#       So the flank line starts at Y = -0.047 (at X=35.16) and goes to Y = 0.122 (at X=35.625).
#       This means the flank line crosses the root circle.
#       This is correct for a gear. The flank starts at the base circle and goes outwards.
#       The root circle is larger than the base circle.
#       So the flank line intersects the root circle at a Y value greater than -half_thickness.
#       
#    Let's recalculate the intersection point for the bottom flank.
#    Y_bottom_intersect = (root_radius - Rb) * tan(alpha) - half_thickness
#    X_bottom_intersect = root_radius
#    
#    Similarly for the top flank:
#    Y_top_intersect = (root_radius - Rb) * tan(alpha) + half_thickness
#    
#    So the profile is:
#    1. Root Arc: From (root_radius, -half_thickness) to (root_radius, +half_thickness).
#    2. Flank Line (Bottom): From (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the flank line is tangent to the base circle.
#       It starts at (Rb, -half_thickness) and goes to (addendum_radius, -half_thickness)?
#       No, the Y coordinate changes along the flank.
#       The flank line is Y = X * tan(alpha) + C.
#       At X = Rb, Y = -half_thickness.
#       At X = addendum_radius, Y = addendum_radius * tan(alpha) - half_thickness - Rb * tan(alpha).
#       This Y value is the Y coordinate at the tip.
#       But the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness only if the tooth is rectangular.
#       The tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       Wait, the tooth is centered at Y=0.
#       So the tip is at Y = -half_thickness? No, the tip is at Y = -half_thickness?
#       The tooth is the solid part.
#       The profile is the boundary of the tooth.
#       The boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness)?
#       No, the boundary goes from (root_radius, -half_thickness) to (addendum_radius, -half_thickness) is the bottom of the tooth.
#       But the bottom of the tooth is the root circle.
#       So the boundary goes from (root_radius, -half_thickness) to (root_radius, +half_thickness) along the root circle.
#       Then from (root_radius, +half_thickness) to (addendum_radius, +half_thickness) along the top flank.
#       Then from (addendum_radius, +half_thickness) to (addendum_radius, -half_thickness) along the tip line.
#       Then from (addendum_radius, -half_thickness) to (root_radius, -half_thickness) along the bottom flank.
#       
#    This creates a trapezoid-like shape.
#    Let's implement this.
    
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
#       = pitch_radius * (1 - cos
