"""
FreeCAD 1.1 Script: Parametric Spur Gear Generation
Generates a spur gear with hub and bore inside a single PartDesign Body.
"""

from pathlib import Path
import FreeCAD as App
import Part
import PartDesign
import Sketcher
import math

# -----------------------------------------------------------------------------
# 1. Initialize Document and Body
# -----------------------------------------------------------------------------
doc = App.newDocument("SpurGear")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")
doc.add(body)

# -----------------------------------------------------------------------------
# 2. Define Named Parameters
# -----------------------------------------------------------------------------
# We create a Feature to hold our variables so they are editable in the tree
params = body.newObject("PartDesign::Feature", "Parameters")
params.Type = "PartDesign::VariableSet" # Ensure it acts as a variable set container

# Base Geometry Parameters
params.addProperty("App::PropertyFloat", "gear_module", "Dimensions", "Module (m)")
params.gear_module = 1.0

params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Count")
params.number_of_teeth = 60

params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = 20.0

params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Width")
params.face_width = 6.0

params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub D")
params.hub_diameter = 18.0

params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub W")
params.hub_width = 8.0

params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Bore")
params.shaft_diameter = 8.0

params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Total L")
params.overall_width = 14.0

# Derived Dimensions (Calculated in script, but could be expressions if preferred)
# Derived values based on ISO/DIN standards provided in prompt
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "D_p")
params.pitch_diameter = params.gear_module * params.number_of_teeth # 60 mm

params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "D_a")
params.outer_diameter = params.pitch_diameter + 2 * params.gear_module # 62 mm

params.addProperty("App::PropertyLength", "root_diameter", "Dimensions", "D_f")
params.root_diameter = params.pitch_diameter - 2 * (1.25 * params.gear_module) # 57.5 mm

params.addProperty("App::PropertyLength", "base_diameter", "Dimensions", "D_b")
params.base_diameter = params.pitch_diameter * math.cos(math.radians(params.pressure_angle)) # ~56.382 mm

params.addProperty("App::PropertyLength", "circular_pitch", "Dimensions", "p")
params.circular_pitch = math.pi * params.gear_module # ~3.142 mm

params.addProperty("App::PropertyLength", "addendum", "Dimensions", "ha")
params.addendum = params.gear_module # 1.0 mm

params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "hf")
params.dedendum = 1.25 * params.gear_module # 1.25 mm

params.addProperty("App::PropertyLength", "whole_depth", "Dimensions", "h")
params.whole_depth = params.addendum + params.dedendum # 2.25 mm

# Helper to get base diameter in expression format for later use
base_d_expr = f"{params.base_diameter}" 

# -----------------------------------------------------------------------------
# 3. Create the Main Gear Profile Sketch
# -----------------------------------------------------------------------------
# We will sketch on the XY plane (Z=0), extrude along Z for face_width.
# The profile needs to be a closed loop representing the toothed cylinder.
# Since we can't easily draw a continuous involute spline in standard Sketcher lines,
# we will generate the profile as a TopoShape and import it into the sketch.
# However, to strictly follow "sketches and PartDesign features", we will construct
# the profile geometry using Part commands and add them to the sketch.

sk1 = body.newObject("Sketcher::SketchObject", "GearProfile")
sk1.Placement = App.Placement(App.Vector(0, 0, 0))
sk1.Constraints = Sketcher.Array() # Clear default
sk1.Support = [
    (doc.getObject("XY_Plane"), [""]), 
    (doc.getObject("Z_Axis"), [""])
]
sk1.MapMode = "FlatFace"

# Generate the involute profile segments
# We need a continuous path. We will generate N+1 points (closing the loop)
# and connect them.
profile_points = []
num_points = 100 # Resolution of the involute

# Start at the base diameter angle
start_angle = 0
# End angle: roughly where the tooth tip is. 
# Tooth width at pitch circle = pi / N
tooth_width = math.pi / params.number_of_teeth
# Half tooth width
half_tooth = tooth_width / 2
# Approximate tip angle: Base angle + half tooth width (roughly)
# More precise: The involute angle increases with radius.
# Let's just sweep from -half_tooth to +half_tooth relative to the tooth center line.
# Actually, for a gear, we usually generate one tooth and pattern it.
# But for a single solid body via sketch, we need the full external contour.
# The contour is: Base circle segment + Involute arc + Tip circle segment.

# Let's generate points for the right half of one tooth and the root circle.
# Actually, the easiest way to get a valid sketch for the whole gear is:
# 1. Define the involute curve function.
# 2. Generate points along the involute from base radius to outer radius.
# 3. Connect them.

# Involute function:
# r = rb / cos(phi)
# theta = phi + tan(phi) (where phi is the involute angle in radians)
# x = r * cos(theta), y = r * sin(theta)
# But we need to stitch multiple teeth.
# Simpler approach: Generate the profile of ONE tooth, then use Polar Pattern?
# No, the pattern creates instances. We need a single sketch of the whole gear to Pad it.
# OR: We can Pad a single tooth sketch, then use a Linear/Polar pattern on the Pad?
# The prompt asks for "exactly one solid body".
# Approach: Create a sketch of the FULL gear profile (teeth + root) -> Pad.
# To draw the full profile:
# 1. Draw the Root Circle (D_root / 2).
# 2. Draw the Involute curves for N teeth.
# 3. Draw the Outer Circle (D_outer / 2).
# 4. Close the loop.

# Let's generate a list of points that form the perimeter.
# Start at angle - (pi/N) on the root circle, go to + (pi/N), then follow involutes.
# Actually, let's just generate the involute arcs for all teeth and connect them.

points = []

# Function to get involute coordinates
def get_involute(r, phi):
    # phi is the angle of the tangent to the base circle (involute angle)
    # r_base = rb
    # r = r_base / cos(phi)
    # theta = phi + tan(phi)
    # x = r * cos(theta)
    # y = r * sin(theta)
    if math.cos(phi) == 0:
        return None
    r_val = params.base_diameter / 2.0 / math.cos(phi)
    theta = phi + math.tan(phi)
    x = r_val * math.cos(theta)
    y = r_val * math.sin(theta)
    return (x, y)

# Generate points for the full gear profile
# We step through angles.
# Start from the start of the first tooth flank (left side)
# The gear profile consists of:
# - Root circle arc between tooth flanks
# - Involute flank
# - Tip circle arc
# - Involute flank
# - Root circle arc... repeat

# Let's calculate the angle of the tooth center line relative to the start.
# We'll generate points from theta = -pi/2 - (pi/N) to theta = -pi/2 + (pi/N) ... wait.
# Let's just iterate 360 degrees.
# We will create a list of (x,y) that traces the boundary.

# We need to switch between Root Circle, Involute, and Tip Circle.
# Transition points:
# 1. Root to Involute: Occurs at the intersection of the root circle and the tooth flank.
#    We can approximate this or calculate exactly.
#    Exact: The tooth flank is tangent to the base circle. The root is a circle.
#    We can define the "cut" points.
#    Simplified: Just generate enough points on the involute and the root circle to close.

# Strategy: 
# 1. Define the "Tooth Center Angle" step = 2*pi / N.
# 2. For each tooth, generate the profile segment.
# 3. Concatenate.

total_points = []
tooth_angle_step = 2 * math.pi / params.number_of_teeth

# We start at the beginning of the first tooth (left flank).
# Let's assume the gear is symmetric and we start at angle -pi/2 (negative Y axis) 
# and move clockwise? Let's stick to standard math counter-clockwise.
# Let's start at the root circle at the start of the first tooth.
# Tooth 1 starts at angle: - (pi/N) relative to its center?
# Let's just generate points for the full 360 degrees by stepping.

current_angle = - (math.pi / params.number_of_teeth) # Start slightly inside the first tooth valley
# We will trace the perimeter.
# Actually, constructing the full closed loop programmatically is robust.

# Let's build the point list by iterating over each tooth.
# For each tooth, we add:
# - Left flank (Involute)
# - Top (Tip Circle arc)
# - Right flank (Involute)
# - Valley (Root Circle arc)

# But we need to be careful about the transition points.
# A simple heuristic that works for visualization:
# Generate points on the Involute from Base Radius to Outer Radius.
# Generate points on Root Circle.
# Generate points on Outer Circle.
# Stitch them.

# Better: Generate the vertices of the profile.
# We know the involute starts at the base circle (r = D_base/2).
# We know the tooth tip is at r = D_outer/2.
# We know the root is at r = D_root/2.

# Let's create the profile by generating points for the "Right" side of the gear and mirroring?
# No, let's just generate the full chain.

# Start point: Intersection of Root Circle and the first tooth flank (left side).
# We approximate the start of the involute segment.
# The involute segment for a tooth starts at some angle and ends at another.
# Let's define the "Tooth Center Angle" as 0.
# Left flank goes from (root_radius, angle_start) to (outer_radius, angle_end).
# Right flank goes from (outer_radius, angle_end_right) to (root_radius, angle_start_right).

# This is getting complex to do purely geometric without a CAD kernel call.
# Alternative: Use `Part.makeSpindle` or similar? No, must be sketch.
# Alternative: Generate the involute spline points.

# Let's try a robust point generation:
# We will generate points along the involute curve for N teeth, and fill the valleys with root circle arcs.
# We define the "Tooth Start Angle" for the left flank of tooth i.
# Angle_i = - (pi/N) + i * (2*pi/N)
# The left flank starts at the root circle at Angle_i? 
# Actually, the root circle cuts the involute.
# We can just assume the root circle is the bottom, and the involutes are the sides.
# We will generate points on the involute from Base Radius to Outer Radius.
# And we will generate points on the Root Circle.
# And we will generate points on the Outer Circle.

# Let's collect all relevant points:
all_points = []

# 1. Root Circle Arcs (Valleys)
# There are N valleys. Each valley spans from the end of one flank to the start of the next.
# The valley is approximately 1/3 of the tooth space?
# Let's just sample the root circle between the teeth.
for i in range(params.number_of_teeth):
    # Center of tooth i
    theta_center = (i * tooth_angle_step) - (tooth_angle_step / 2)
    
    # Define the range of angles for the tooth flanks relative to the center
    # Flank 1 (Left): from some start angle to tip angle
    # Flank 2 (Right): from tip angle to some end angle
    
    # Let's calculate the involute angles.
    # Involute angle phi is such that r(phi) = r_outer.
    # r_outer = D_outer / 2
    # r_outer = r_base / cos(phi_tip) -> cos(phi_tip) = r_base / r_outer
    phi_tip = math.acos((params.base_diameter / 2.0) / (params.outer_diameter / 2.0))
    
    # The tooth flanks are symmetric around the center line (theta_center).
    # The left flank (outer side) goes from phi = -phi_tip to phi = phi_tip? 
    # No, the flank is the involute.
    # The tooth profile is bounded by the involute curve.
    # The "Left" flank of tooth i (when looking from outside) is the one at theta_center - half_tooth_width?
    
    # Let's simplify: 
    # We will generate the full perimeter by stepping.
    # Start at angle = - (pi/N) (Start of first valley).
    # Move along Root Circle until we hit the start of the first involute.
    # Move along Involute to Outer Radius.
    # Move along Outer Circle (tooth tip).
    # Move along Involute to Root Radius.
    # Repeat.
    
    # Approximate transition:
    # The involute starts at the base circle. The root circle is smaller than base circle (usually).
    # So the root circle is inside the base circle.
    # The flank is tangent to the base circle.
    # The root circle cuts the flank.
    
    # Let's just generate a high resolution set of points for the whole gear.
    # We will define the function for the boundary.
    pass

# Revised Robust Point Generation:
# We will generate points by iterating through 360 degrees.
# At each angle, we determine if we are on a Root Circle, Outer Circle, or Involute.
# But the boundary is not a function of angle (it's multi-valued).
# We must trace the perimeter.

# Let's trace the perimeter of ONE tooth and then replicate? 
# No, we need a single sketch.
# Let's generate the vertices for the full gear.
# Vertices:
# 1. Root circle points between teeth.
# 2. Involute points (flanks).
# 3. Outer circle points (tips).

# We will generate the profile by:
# 1. Start at the beginning of the first tooth valley (Root Circle).
# 2. Traverse Root Circle to the start of the first flank.
# 3. Traverse Flank (Involute) to the tip.
# 4. Traverse Tip (Outer Circle) to the other flank.
# 5. Traverse Flank (Involute) to the next valley.
# 6. Repeat for all teeth.

# Let's calculate the exact angles.
# Tooth pitch angle = 2 * pi / N.
# Center of tooth i = i * pitch_angle.
# The valley center = (i + 0.5) * pitch_angle.
# The flank center line = i * pitch_angle.

# For tooth i:
# Left Flank: Starts at root circle, ends at outer circle.
# Right Flank: Starts at outer circle, ends at root circle.

# We need the intersection of the Root Circle and the Involute Flank.
# This is complex analytically.
# Let's use a simplified approach: 
# The "Start of Involute" is at the Base Circle.
# The "End of Involute" is at the Outer Circle.
# The "Valley" is the Root Circle.
# We can approximate the connection:
# - From Root Circle to Base Circle (short arc) -> Involute -> Outer Circle -> Involute -> Root Circle.
# But the Root Circle is inside the Base Circle (D_root = 57.5, D_base = 56.38... wait).
# D_base = 60 * cos(20) = 56.38. D_root = 57.5.
# ERROR IN PROMPT LOGIC OR MY CALCULATION?
# Prompt: 
# pitch = 60.
# root = 60 - 2*1.25 = 57.5.
# base = 60 * cos(20) = 56.38.
# So D_root > D_base. 
# This means the Root Circle is OUTSIDE the Base Circle.
# This is standard for gears. The tooth flank (involute) starts at Base Circle and goes OUTWARDS to Outer Circle.
# The Root Circle cuts through the involute flank? 
# No, the Root Circle is smaller than the Pitch Circle but larger than the Base Circle?
# Wait. 
# D_base = 56.38.
# D_root = 57.5.
# D_pitch = 60.
# D_outer = 62.
# So the order
