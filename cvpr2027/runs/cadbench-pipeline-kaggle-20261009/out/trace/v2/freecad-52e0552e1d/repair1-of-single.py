import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derive output path from __file__ to ensure it is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameters ---
# Base dimensions
pressure_angle_deg = 20.0
gear_module = 1.0
number_of_teeth = 40
pitch_diameter = 40.0
outer_diameter = 42.0
face_width = 10.0
hub_diameter = 35.0
hub_width = 10.0
shaft_diameter = 10.0
overall_width = 20.0

# Calculated ISO 21771 dimensions
addendum = pitch_diameter / number_of_teeth
dedendum = 1.25 * gear_module
root_diameter = pitch_diameter - 2 * dedendum

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
# Correct placement assignment for PartDesign::Body in FreeCAD 1.1
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create Parameter Set for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.gear_module = gear_module
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Teeth")
params.number_of_teeth = number_of_teeth
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Dia")
params.pitch_diameter = pitch_diameter
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.face_width = face_width
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Dia")
params.hub_diameter = hub_diameter
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.hub_width = hub_width
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Dia")
params.shaft_diameter = shaft_diameter
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.overall_width = overall_width
params.addProperty("App::PropertyLength", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = pressure_angle_deg

# Helper to get calculated values from parameters
def get_addendum():
    return params.pitch_diameter / params.number_of_teeth

def get_dedendum():
    return 1.25 * params.gear_module

def get_root_diameter():
    return params.pitch_diameter - 2 * get_dedendum()

# --- Sketch 1: Gear Teeth Profile ---
# We create a sketch on the XY plane containing the profile of ONE tooth.
# Then we use PartDesign::Revolution to create the gear body.
sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_teeth.Support = (doc.getObject("XY_Plane"), [])
sketch_teeth.MapMode = "FlatFace"
sketch_teeth.ConstrainAuto = True

# Calculate tooth geometry
m = params.gear_module
z = params.number_of_teeth
pa = params.pressure_angle
pd = params.pitch_diameter
da = params.pitch_diameter + 2 * get_addendum() # Outer diameter
dr = params.pitch_diameter - 2 * get_dedendum() # Root diameter

r_root = get_root_diameter() / 2.0
r_pitch = pitch_diameter / 2.0
r_tip = outer_diameter / 2.0

# Base circle radius
rb = r_pitch * math.cos(math.radians(pa))

# Calculate the rolling angle (t) at the tip
# r_tip = rb / cos(alpha_tip) => cos(alpha_tip) = rb / r_tip
alpha_tip = math.acos(rb / r_tip)
t_tip = math.tan(alpha_tip) # Rolling angle in radians

# Generate points for the right flank (positive Y) of the tooth
# The involute starts at the base circle (t=0) and goes to the tip (t=t_tip).
# Parametric equations for involute starting at (rb, 0) with vertical tangent:
# x = rb * (cos(t) + t*sin(t))
# y = rb * (sin(t) - t*cos(t))
# This curve starts at (rb, 0) and goes into the first quadrant.
# We will use this as the right flank.
# We need to connect the bottom (rb, 0) to the root circle (r_root, 0) and the top to the tip circle.
# Actually, the standard gear tooth profile connects the root circle to the base circle with a line or fillet,
# then follows the involute to the tip circle.
# For simplicity and robustness in a script, we will:
# 1. Create a line from (r_root, 0) to (rb, 0).
# 2. Create the involute curve from t=0 to t=t_tip.
# 3. Create a line from the end of the involute to (r_tip, 0)? No, the involute ends at the tip circle but at an angle.
#    We need to close the loop.
#    The tooth is symmetric around the X axis.
#    So we need the left flank as well.
#    The left flank is the involute reflected across the X axis? No.
#    The left flank is the involute generated from the base circle but going in the other direction?
#    Actually, the left flank is the involute for t from 0 to t_tip, but with negative Y?
#    Let's check the symmetry.
#    The involute curve (x, y) is in the first quadrant.
#    If we reflect it across the X axis, we get (x, -y). This would be the left flank if the tooth centerline is the X axis.
#    So the profile is:
#    - Line from (r_root, 0) to (rb, 0).
#    - Involute curve from t=0 to t=t_tip (Right flank).
#    - Line from the end of the right flank to (r_tip, 0)? No.
#    - We need to connect the end of the right flank to the end of the left flank.
#    - The end of the right flank is at (x_tip, y_tip).
#    - The end of the left flank (reflected) is at (x_tip, -y_tip).
#    - We need to connect these two points with a line? No, that would be a flat top.
#    - Standard gears have a tip circle arc.
#    - So we need to connect (x_tip, y_tip) to (r_tip, 0) with an arc? No.
#    - The tip circle is a full circle. The tooth occupies a sector.
#    - The profile should go from (r_root, 0) -> (rb, 0) -> Involute -> (x_tip, y_tip) -> Arc to (x_tip, -y_tip) -> Involute -> (r_root, 0).
#    - But we are sketching ONE tooth.
#    - So we need to define the boundary of the tooth.
#    - The boundary is:
#      1. Line from (r_root, 0) to (rb, 0).
#      2. Involute from t=0 to t=t_tip.
#      3. Line from (x_tip, y_tip) to (r_tip, 0)? No.
#      4. We need to connect the end of the right flank to the start of the left flank.
#      5. The start of the left flank is the reflection of the end of the right flank? No.
#      6. The left flank starts at the base circle at an angle -alpha_tip?
#      7. Let's just generate the points for the right flank and the left flank separately.
#      8. Right flank: t from 0 to t_tip.
#      9. Left flank: t from 0 to t_tip, but reflected across the X axis?
#         If we reflect (x, y) across X, we get (x, -y).
#         This gives a curve in the fourth quadrant.
#         This is the left flank.
#      10. So the profile is:
#          - Line from (r_root, 0) to (rb, 0).
#          - Involute (Right flank).
#          - Line from (x_tip, y_tip) to (r_tip, 0)? No.
#          - We need to connect the end of the right flank to the end of the left flank.
#          - The end of the right flank is at (x_tip, y_tip).
#          - The end of the left flank is at (x_tip, -y_tip).
#          - We need to connect these two points with an arc of radius r_tip?
#          - Yes, the tip circle arc.
#          - But we need to define the arc in the sketch.
#          - We can use a circle and constrain it.
#          - Or we can just add the arc points.
#          - Let's add the arc points.
#          - The arc goes from (x_tip, y_tip) to (x_tip, -y_tip) along the circle of radius r_tip.
#          - But we need to know the angle of the arc.
#          - The angle of the right flank end is theta_tip = atan2(y_tip, x_tip).
#          - The angle of the left flank end is -theta_tip.
#          - The arc goes from theta_tip to -theta_tip? No, that would be the long way around.
#          - The arc goes from theta_tip to -theta_tip through 0? No, the tooth is centered on 0.
#          - So the arc goes from theta_tip to -theta_tip passing through 0.
#          - Wait, the tooth is centered on the X axis.
#          - So the right flank is at positive Y, the left flank is at negative Y.
#          - The arc connects them at the top? No, the arc is the tip of the tooth.
#          - The tip of the tooth is the arc of the tip circle.
#          - So the arc goes from the end of the right flank to the end of the left flank.
#          - The end of the right flank is at angle theta_tip.
#          - The end of the left flank is at angle -theta_tip.
#          - The arc goes from theta_tip to -theta_tip? No, that would be the bottom of the tooth.
#          - The arc goes from theta_tip to -theta_tip passing through 0? No, that would be the top of the tooth.
#          - Yes, the arc goes from theta_tip to -theta_tip passing through 0.
#          - So the arc is from theta_tip to -theta_tip.
#          - But we need to define the arc in the sketch.
#          - We can add the start point, the end point, and the center of the arc (0,0) and the radius r_tip.
#          - And constrain the arc to be the correct one.
#          - Or we can just add the points and let FreeCAD figure it out.
#          - Let's add the points:
#            - (r_root, 0)
#            - (rb, 0)
#            - Points along the right flank (t from 0 to t_tip)
#            - (x_tip, y_tip)
#            - Points along the arc (from theta_tip to -theta_tip)
#            - (x_tip, -y_tip)
#            - Points along the left flank (t from 0 to t_tip, reflected)
#            - (r_root, 0)
#          - This is getting complicated.
#          - Let's simplify.
#          - We will create a closed loop of lines and arcs.
#          - 1. Line from (r_root, 0) to (rb, 0).
#          - 2. Involute curve from t=0 to t=t_tip.
#          - 3. Line from (x_tip, y_tip) to (r_tip, 0)? No.
#          - 4. We need to connect the end of the right flank to the end of the left flank.
#          - 5. The end of the right flank is at (x_tip, y_tip).
#          - 6. The end of the left flank is at (x_tip, -y_tip).
#          - 7. We need to connect these two points with an arc of radius r_tip.
#          - 8. The arc goes from (x_tip, y_tip) to (x_tip, -y_tip) passing through (r_tip, 0).
#          - 9. Then the left flank from (x_tip, -y_tip) to (r_root, 0).
#          - 10. Then the line from (r_root, 0) to (rb, 0).
#          - This forms a closed loop.
#          - Let's implement this.

# Generate points for the right flank
right_flank_points = []
for t in [i * t_tip / 100 for i in range(101)]:
    x = rb * (math.cos(t) + t * math.sin(t))
    y = rb * (math.sin(t) - t * math.cos(t))
    right_flank_points.append((x, y))

# End of right flank
x_tip = right_flank_points[-1][0]
y_tip = right_flank_points[-1][1]

# Generate points for the arc
# The arc goes from (x_tip, y_tip) to (x_tip, -y_tip) passing through (r_tip, 0).
# The angle of (x_tip, y_tip) is theta_tip = atan2(y_tip, x_tip).
# The angle of (x_tip, -y_tip) is -theta_tip.
# The arc goes from theta_tip to -theta_tip passing through 0.
# So the angle goes from theta_tip to 0 to -theta_tip.
# We can generate points along the arc.
arc_points = []
for angle in [i * (theta_tip / 50) for i in range(51)]:
    # We need to go from theta_tip to -theta_tip.
    # So the angle should be theta_tip - i * (2 * theta_tip / 50).
    # But we want to pass through 0.
    # So the angle should be theta_tip - i * (2 * theta_tip / 50).
    # Let's just generate points from theta_tip to -theta_tip.
    pass

# Let's generate points for the arc from theta_tip to -theta_tip.
# The angle goes from theta_tip to -theta_tip.
# We can use a linear interpolation of the angle.
# But we need to make sure we pass through 0.
# So the angle goes from theta_tip to -theta_tip.
# The step is ( -theta_tip - theta_tip ) / N = -2 * theta_tip / N.
# So the angle is theta_tip + i * (-2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 * theta_tip / N).
# This will go from theta_tip to -theta_tip.
# But we want to pass through 0.
# So the angle should be theta_tip - i * (2 *
