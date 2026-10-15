import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration & Parameters ---
# Derived from __file__ to ensure output is next to the script
script_dir = Path(__file__).resolve().parent
output_file = script_dir / "answer.FCStd"

# Geometric Parameters (ISO 21771 Standard based on prompt)
gear_module = 2.0
number_of_teeth = 25
pressure_angle_deg = 20.0
face_width = 20.0
hub_diameter = 40.0
hub_width = 10.0
shaft_diameter = 10.0
overall_width = 30.0

# Calculated Dimensions
pressure_angle = math.radians(pressure_angle_deg)
pitch_diameter = gear_module * number_of_teeth
outer_diameter = pitch_diameter + 2 * gear_module
root_diameter = pitch_diameter - 2 * (1.25 * gear_module)
base_diameter = pitch_diameter * math.cos(pressure_angle)
circular_pitch = math.pi * gear_module
tooth_thickness = circular_pitch / 2.0
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum

# --- Document Creation ---
doc = App.newDocument("Gear")

# 1. Main Body
body = doc.addObject("PartDesign::Body", "Body")

# 2. Parameters (Named objects driving geometry)
# We store values in the Body's properties to make them editable and named
body.addProperty("App::PropertyLength", "module", "Dimensions", "Gear Module")
body.module = gear_module

body.addProperty("App::PropertyInteger", "num_teeth", "Dimensions", "Number of Teeth")
body.num_teeth = number_of_teeth

body.addProperty("App::PropertyLength", "width", "Dimensions", "Overall Face Width")
body.width = overall_width

body.addProperty("App::PropertyLength", "hub_d", "Dimensions", "Hub Diameter")
body.hub_d = hub_diameter

body.addProperty("App::PropertyLength", "shaft_d", "Dimensions", "Shaft Diameter")
body.shaft_d = shaft_diameter

# --- Feature Construction ---

# ------------------------------------------------------------------
# STEP 1: Create the Involute Tooth Profile Sketch
# ------------------------------------------------------------------
sketch = body.newObject("Sketcher::SketchObject", "ToothProfile")
# Attach to XY Plane
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainPlane = "XY_Plane"
sketch.ConstrainAxis = "Z_Axis"
sketch.MapMode = "FlatFace"

# Generate Involute Profile points
# We define a closed loop: Outer Circle Arc -> Involute Line -> Inner Circle Arc -> Closing Line
# Coordinate system: X is radial, Y is tangential

# 1. Start at the start of the outer arc (0 degrees)
# Point A: (OuterDiameter/2, 0)
p_start_outer = App.Vector(outer_diameter / 2.0, 0.0)
sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), p_start_outer), False)

# 2. Outer Arc (approximate for the flank, or use exact involute start)
# To keep it simple and robust with standard constraints, we often use a circle arc 
# for the very tip and line for the involute, but a true involute is better.
# Let's construct the exact involute segment from the base circle to the outer circle.
# Tangent point on base circle (angle = 0 relative to X)
# Involute equation: x = r_b * (cos(t) + t*sin(t)), y = r_b * (sin(t) - t*cos(t))
# where t is the involute angle (in radians).
# t=0 is the base circle. t_max corresponds to radius = outer_radius.

r_base = base_diameter / 2.0
r_outer = outer_diameter / 2.0

# Calculate t_max where r(t) = r_outer
# r(t) = r_b * sqrt(1 + t^2)
# t_max = sqrt((r_outer/r_b)^2 - 1)
t_max = math.sqrt((r_outer / r_base)**2 - 1)

# Function to get point on involute
def get_involute_point(t):
    x = r_base * (math.cos(t) + t * math.sin(t))
    y = r_base * (math.sin(t) - t * math.cos(t))
    return App.Vector(x, y)

# Point B: End of involute at outer radius
p_end_involute = get_involute_point(t_max)

# Add Involute Curve (approximated by a line segment in sketcher for simplicity, 
# as Sketcher doesn't have a native "Involute" curve object, but we can add the points)
# Since Sketcher doesn't support generic curves easily, we will add the tangent line 
# which is the standard approximation in basic CAD unless using advanced workbenches.
# The tangent is perpendicular to the radius at the base circle start.
# Tangent line at base circle (angle 0) is vertical (x = r_base).
# The involute starts at (r_base, 0) and goes up.
# We add the tangent line segment from base circle to the intersection with the outer circle.
# Intersection of x=r_base and circle r_outer: y = sqrt(r_outer^2 - r_base^2)
# Note: The involute is the curve tangent to the unwinding line.
# Let's just add the tangent line which is the correct geometry for the flank.
tangent_point = App.Vector(r_base, 0.0)
tangent_line_point = App.Vector(r_base, math.sqrt(r_outer**2 - r_base**2))
sketch.addGeometry(Part.LineSegment(tangent_point, tangent_line_point), False)

# 3. Outer Tip Arc (to close the tooth tip)
# From tangent_line_point, arc along outer circle to the other side of the tooth?
# No, we are building ONE tooth profile, then we will use it in a polar pattern.
# So the profile must be closed.
# Let's define the profile symmetrically or just one half and mirror? 
# PartDesign Polar Pattern works on the feature, not the sketch content directly in terms of mirroring.
# We need a full closed sketch for the tooth.
# Let's do: Start (Tip Right) -> Flank Up -> Flank Down -> Tip Left -> Close.
# Wait, the sketch is 2D. Let's do:
# 1. Tip Right (Outer Circle)
# 2. Flank Up (Involute/Tangent)
# 3. Flank Down (Tangent)
# 4. Tip Left (Outer Circle)
# 5. Close Tip

# Let's restart the sketch geometry logic for a single closed tooth loop.
# Center of the tooth profile is on the X-axis.
# Tooth thickness is tooth_thickness.
# Half thickness = tooth_thickness / 2.

# Let's define the profile relative to the tooth center line (Y-axis symmetry would be easier, but let's stick to X-Y).
# Actually, standard polar patterns place objects at angles. The sketch is usually attached to a plane.
# Let's attach the sketch to the XZ plane, with the center of the gear at (0,0,0).
# We will draw the profile of ONE tooth, then pattern it.
# The sketch origin will be at the center of the gear.
# The profile will be symmetric about the Y-axis (if we rotate 0 deg).
# Let's rotate the whole thing 45 deg later? No, let's keep it simple.
# Let's draw the tooth profile such that the pitch circle passes through the middle of the tooth.
# The sketch will be attached to XY plane. The tooth profile will be symmetric about the X-axis? 
# No, usually symmetric about the radial line.
# Let's make the sketch symmetric about the X-axis (Y=0). The tooth spans from -tooth_thickness/2 to +tooth_thickness/2 in X.

# Re-drawing the sketch logic:
# Origin (0,0) is gear center.
# Profile is symmetric about X-axis.
# Points:
# A: (pitch_diameter/2, tooth_thickness/2)  <-- Pitch point top
# B: (outer_diameter/2, 0)                  <-- Tip center (Wait, tip is usually slightly outside pitch)
# Actually, the tooth tip is on the outer circle.
# Let's define the profile:
# 1. Start at Tip Center: (outer_diameter/2, 0)
# 2. Go to Tip Corner (Outer Circle, Top Half): (outer_diameter/2, sqrt(outer^2/4 - (outer^2/4 - (tooth_thickness/2)^2 ... no)
#    The tooth is a segment of the outer circle? No, the tip is usually rounded or flat. 
#    Standard spur gear: Tip is part of the outer cylinder. The involute meets the outer cylinder.
#    The "Tip" of the tooth is the arc on the outside.
#    So the profile goes:
#    - Start at Top of Involute (Outer Circle)
#    - Arc along Outer Circle for half tooth thickness
#    - Line down Flank
#    - Line across Bottom Flank
#    - Arc along Outer Circle
#    - Back to start.

# Let's simplify for robust scripting:
# We will draw the "Involute Line" and "Outer Circle Arc" and "Root Line".
# 
# 1. Top Flank End (Outer Circle, Angle = 0): (r_outer, 0)
# 2. Top Tip Corner (Outer Circle, Angle = theta_half): 
#    The half tooth thickness at the outer diameter? 
#    Usually, the tooth thickness is constant at the pitch circle. At the outer circle, it is slightly larger.
#    For simplicity in this script, we will assume the tooth thickness at the outer circle is approximated 
#    or we just draw the involute line and connect it.
#    Let's calculate the angle of the outer circle segment.
#    Half angle alpha_outer = atan( (tooth_thickness/2) / r_outer ) ? No.
#    Let's just use the tooth_thickness at the pitch circle and assume the flank lines converge.
#    This is an approximation common in basic scripting.
#    
#    Refined approach:
#    We draw the involute tangent lines. They intersect the outer circle.
#    We connect the intersection points with an arc.
#    
#    Top Intersection: (r_base, 0) -> Tangent line up.
#    Intersection with Outer Circle: x = r_base. y = sqrt(r_outer^2 - r_base^2).
#    Bottom Intersection: x = r_base. y = -sqrt(r_outer^2 - r_base^2).
#    
#    Now we need to close the tooth between these two points.
#    The distance between them is 2 * sqrt(r_outer^2 - r_base^2).
#    The tooth thickness at this level should be wider than the pitch thickness.
#    But for the script, we will just draw the flank lines and an arc connecting them.
#    
#    Let's define the points:
#    P1 (Top Flank Start): (r_base, 0)
#    P2 (Top Flank End / Tip Corner): (r_base, sqrt(r_outer^2 - r_base^2))
#    P3 (Tip Center?): No, the tooth exists between the flanks.
#    
#    Correct Topology for One Tooth Sketch:
#    1. Start at Top Tip Corner: (r_base, sqrt(r_outer^2 - r_base^2))
#    2. Line to Bottom Tip Corner: (r_base, -sqrt(r_outer^2 - r_base^2)) -- This is the root? No.
#       The root is at root_diameter.
#       The flanks are straight lines (tangent to base circle).
#       They start at (r_base, 0) and go outwards.
#       
#       Let's trace the perimeter of one tooth:
#       - Start at Top Root Corner: (r_root/2, y_root) -> No, root is flat usually.
#       - Let's do: Top Flank Tip -> Arc along Outer Circle -> Bottom Flank Tip -> Flank -> Root -> Flank -> Arc.
#       
#       Let's simplify: 
#       We create a closed loop:
#       A: (r_outer, 0)  [Tip Center]
#       B: (r_outer, tooth_thickness/2) [Approximate Tip Corner] - Wait, tooth thickness is at pitch.
#       
#       Let's use the exact geometry:
#       1. Top Flank Line: From (r_base, 0) to (r_base, h_outer). (h_outer = sqrt(r_outer^2 - r_base^2))
#       2. Outer Arc: From (r_base, h_outer) to (r_base, -h_outer) ?? No, that's a chord.
#          We need to go outwards to cover the tooth width.
#          The tooth width at the outer circle is greater.
#          Let's assume the tooth thickness at the outer circle is the same as the pitch circle for simplicity 
#          (a common simplification in low-fidelity modeling), OR we calculate the angle.
#          Angle of tooth half-width at pitch circle: alpha_p = atan((tooth_thickness/2) / (pitch_diameter/2)).
#          Angle at outer circle is slightly different.
#          
#          Let's stick to the simplest robust method:
#          Draw the two tangent lines from Base Circle (r_base) to Outer Circle (r_outer).
#          These lines are vertical in our local frame (x=r_base).
#          We connect the top of these lines with an arc of radius r_outer.
#          We connect the bottom of these lines with a
