import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__ to ensure the script is self-contained and portable
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Parameters
bridge_outer_radius = 6.50
bridge_wall_thickness = 2.60
bridge_to_tip_fillet_center_length = 26.00
tip_fillet_radius = 1.10
lobe_to_inner_connector_transition_radius = 1.95
bridge_to_retention_lobe_center_distance = 19.20
retention_lobe_arc_sweep_angle = 82.145694714
clip_width = 2.20
bridge_inner_arc_half_sweep_angle = 86.0
tip_fillet_exit_radius_angle_from_negative_x = 45.0

# --- Document Setup ---
doc = App.newDocument("SpringClip")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
# In FreeCAD 1.1, Body.Placement is a PropertyPlacement, not a direct assignment in some contexts, 
# but usually App.Placement works. If not, we set it via the property.
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create Parameters
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "bridge_outer_radius", "Dimensions", "bridge_outer_radius")
params.addProperty("App::PropertyLength", "bridge_wall_thickness", "Dimensions", "bridge_wall_thickness")
params.addProperty("App::PropertyLength", "bridge_to_tip_fillet_center_length", "Dimensions", "bridge_to_tip_fillet_center_length")
params.addProperty("App::PropertyLength", "tip_fillet_radius", "Dimensions", "tip_fillet_radius")
params.addProperty("App::PropertyLength", "lobe_to_inner_connector_transition_radius", "Dimensions", "lobe_to_inner_connector_transition_radius")
params.addProperty("App::PropertyLength", "bridge_to_retention_lobe_center_distance", "Dimensions", "bridge_to_retention_lobe_center_distance")
params.addProperty("App::PropertyLength", "retention_lobe_arc_sweep_angle", "Dimensions", "retention_lobe_arc_sweep_angle")
params.addProperty("App::PropertyLength", "clip_width", "Dimensions", "clip_width")
params.addProperty("App::PropertyLength", "bridge_inner_arc_half_sweep_angle", "Dimensions", "bridge_inner_arc_half_sweep_angle")
params.addProperty("App::PropertyLength", "tip_fillet_exit_radius_angle_from_negative_x", "Dimensions", "tip_fillet_exit_radius_angle_from_negative_x")

# Set initial values
params.bridge_outer_radius = bridge_outer_radius
params.bridge_wall_thickness = bridge_wall_thickness
params.bridge_to_tip_fillet_center_length = bridge_to_tip_fillet_center_length
params.tip_fillet_radius = tip_fillet_radius
params.lobe_to_inner_connector_transition_radius = lobe_to_inner_connector_transition_radius
params.bridge_to_retention_lobe_center_distance = bridge_to_retention_lobe_center_distance
params.retention_lobe_arc_sweep_angle = retention_lobe_arc_sweep_angle
params.clip_width = clip_width
params.bridge_inner_arc_half_sweep_angle = bridge_inner_arc_half_sweep_angle
params.tip_fillet_exit_radius_angle_from_negative_x = tip_fillet_exit_radius_angle_from_negative_x

# --- Geometry Calculation ---
# Inner bridge radius
inner_bridge_radius = bridge_outer_radius - bridge_wall_thickness

# Bridge center is at (0,0) in the sketch frame.
# Retention lobe center is at (bridge_to_retention_lobe_center_distance, 0).
# Tip fillet center is at (-bridge_to_tip_fillet_center_length, 0).

# 1. Retention Lobe Geometry
# The lobe center is at X = +19.20.
# The lobe radius is the inner bridge radius.
# The sweep angle is 82.145... degrees.
# The lobe connects to the inner connector.
# The inner bridge arc starts at angle 0 (positive X) and goes to bridge_inner_arc_half_sweep_angle (86 deg).
# Wait, the problem says: "bridge_inner_arc_half_sweep_angle is measured from the bridge's positive x radial direction to either inner-bridge endpoint."
# So the inner bridge arc goes from +86 deg to -86 deg.
# The paired retention-lobe arcs share one center on the longitudinal profile centerline.
# bridge_to_retention_lobe_center_distance is the full x-direction distance from the bridge center to that shared lobe center.
# retention_lobe_arc_sweep_angle is the full sweep of either mirrored lobe.
# The lobe radius and each inner-connector radius equal the inner bridge radius implied by the bridge wall.
# Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends.
# bridge_inner_arc_half_sweep_angle is measured from the bridge's positive x radial direction to either inner-bridge endpoint.
# Symmetry, external tangency, common radii, and profile closure determine all transition centers and contact points.

# Let's refine the geometry logic:
# 1. Inner Bridge Arc: Center (0,0), Radius R_in. Starts at angle 0 (positive X), goes to +86 deg and -86 deg.
#    Wait, "bridge_inner_arc_half_sweep_angle is measured from the bridge's positive x radial direction to either inner-bridge endpoint."
#    So the inner bridge arc goes from -86 to +86.
# 2. Inner Connector: Radius R_in. Connects the inner bridge endpoint to the retention lobe.
#    The retention lobe center is at (D_lobe, 0) where D_lobe = 19.20.
#    The retention lobe radius is R_in.
#    The retention lobe sweep is S_lobe = 82.145... degrees.
#    The retention lobe must connect to the inner connector.
#    The inner connector must connect to the retention lobe.
#    There is a transition radius R_trans = 1.95 between the inner connector and the retention lobe.
#    This transition is externally tangent to both.
#    We need to find the center of this transition arc.
#    Let C_trans be the center of the transition arc.
#    Distance(C_trans, LobeCenter) = R_in + R_trans.
#    Distance(C_trans, InnerConnectorCenter) = R_in + R_trans.
#    Also, the Inner Connector is tangent to the Inner Bridge at the endpoint.
#    So the inner connector starts at the point P_bridge = (R_in * cos(86), R_in * sin(86)).
#    The inner connector is tangent to the inner bridge at P_bridge.
#    So the inner connector center C_ic lies on the line passing through P_bridge and perpendicular to the radius vector (cos(86), sin(86)).
#    This line is the tangent line to the inner bridge at P_bridge.
#    So C_ic is on the line: x * cos(86) + y * sin(86) = R_in. (Normal form)
#    Wait, the line equation for the tangent at angle theta is x*cos(theta) + y*sin(theta) = R.
#    Yes.
#    So C_ic is on this line.
#    Also, the Inner Connector is tangent to the Retention Lobe? No, there is a transition.
#    The Inner Connector connects to the Retention Lobe via the transition.
#    So the Inner Connector must be tangent to the transition arc.
#    And the Retention Lobe must be tangent to the transition arc.
#    This implies the Inner Connector and the Retention Lobe are not directly tangent.
#    But the Inner Connector must connect to the Retention Lobe.
#    The problem says: "The transition is externally tangent to both neighboring arcs."
#    Neighboring arcs of the transition are the Inner Connector and the Retention Lobe.
#    So the transition is tangent to the Inner Connector and the Retention Lobe.
#    So the sequence is: Inner Bridge -> Transition -> Inner Connector -> Retention Lobe?
#    Or: Inner Bridge -> Inner Connector -> Transition -> Retention Lobe?
#    "The transition is externally tangent to both neighboring arcs."
#    "On the upper half, select the transition center on the bridge side of the lobe center and above the longitudinal centerline; select the inner-connector center farther toward the bridge and closer to the centerline."
#    This implies the order is: Bridge -> Inner Connector -> Transition -> Lobe.
#    Let's check the distances.
#    Bridge Center (0,0). Lobe Center (19.20, 0).
#    Inner Connector Center C_ic. Transition Center C_trans.
#    C_ic is "farther toward the bridge" than C_trans. So C_ic is closer to (0,0) than C_trans.
#    C_trans is "above the longitudinal centerline" (y > 0).
#    C_ic is "closer to the centerline" (y < C_trans.y).
#    This implies the order along the path is: Bridge -> Inner Connector -> Transition -> Lobe.
#    So:
#    1. Inner Bridge Arc (R_in) ends at P_bridge_end.
#    2. Inner Connector Arc (R_in) starts at P_bridge_end?
#       "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
#       If the "sloped inner wall" is the transition, then the inner connector is tangent to the transition.
#       And the inner bridge is tangent to the transition.
#       This would mean the inner bridge and inner connector are NOT tangent to each other.
#       They are both tangent to the transition.
#       But the inner bridge ends at P_bridge_end.
#       So the transition must be tangent to the inner bridge at P_bridge_end.
#       And the inner connector must be tangent to the transition.
#       And the inner connector must connect to the retention lobe.
#       Is the inner connector tangent to the retention lobe?
#       "The transition is externally tangent to both neighboring arcs."
#       Neighbors of the transition are the Inner Connector and the Retention Lobe.
#       So the transition is tangent to the Inner Connector and the Retention Lobe.
#       So the sequence is: Inner Bridge -> Transition -> Inner Connector -> Retention Lobe?
#       But the text says "select the inner-connector center farther toward the bridge".
#       If the order is Bridge -> Transition -> Inner Connector -> Lobe, then the transition is closer to the bridge.
#       But the text says "select the inner-connector center farther toward the bridge".
#       This implies the inner connector is farther from the lobe than the transition.
#       So: Lobe ... Transition ... Inner Connector ... Bridge.
#       This matches "inner-connector center farther toward the bridge".
#       So the order is: Bridge -> Inner Connector -> Transition -> Lobe.
#       This means the Inner Connector is tangent to the Inner Bridge?
#       "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
#       This could mean the Inner Connector and the Inner Bridge are tangent to the Transition?
#       If so, the order is Bridge -> Transition -> Inner Connector -> Lobe.
#       But then the transition is closer to the bridge.
#       The text says "select the inner-connector center farther toward the bridge".
#       This implies the inner connector is farther from the lobe than the transition.
#       So: Lobe ... Transition ... Inner Connector ... Bridge.
#       This means the Inner Connector is between the Transition and the Bridge.
#       So the order is: Bridge -> Inner Connector -> Transition -> Lobe.
#       This means the Inner Connector is tangent to the Inner Bridge.
#       And the Transition is tangent to the Inner Connector.
#       And the Transition is tangent to the Retention Lobe.
#       This seems the most logical interpretation.
#       Let's assume:
#       1. Inner Bridge Arc (R_in) ends at P_bridge_end.
#       2. Inner Connector Arc (R_in) starts at P_bridge_end.
#          So C_ic is on the tangent line at P_bridge_end.
#          And distance(C_ic, P_bridge_end) = R_in.
#          Since the inner connector goes towards the lobe (positive X), and the tangent at 86 deg is almost horizontal,
#          the center C_ic must be "below" the tangent line if we go right?
#          Actually, the tangent line is x*cos(86) + y*sin(86) = R_in.
#          The center C_ic is at distance R_in from P_bridge_end along the normal? No, along the radius.
#          The radius vector is (cos(86), sin(86)).
#          The center C_ic is at P_bridge_end - R_in * (cos(86), sin(86))? No, that would be at (0,0).
#          The center C_ic is at P_bridge_end + R_in * (-cos(86), -sin(86))? No, that's also (0,0).
#          Wait, the inner bridge is centered at (0,0). The radius vector is from (0,0) to P_bridge_end.
#          The inner connector is tangent to the inner bridge at P_bridge_end.
#          So the radius of the inner connector at P_bridge_end is perpendicular to the radius of the inner bridge.
#          So the center C_ic lies on the line passing through P_bridge_end and perpendicular to the radius vector (cos(86), sin(86)).
#          This line is the tangent line.
#          So C_ic is on the line: x*cos(86) + y*sin(86) = R_in.
#          And distance(C_ic, P_bridge_end) = R_in.
#          So C_ic is at distance R_in from P_bridge_end along the tangent line.
#          There are two such points. One towards positive X, one towards negative X.
#          We want towards positive X.
#          The tangent vector at 86 deg is (-sin(86), cos(86)) or (sin(86), -cos(86)).
#          At 86 deg, sin(86) is close to 1, cos(86) is close to 0.
#          So the tangent vector is roughly (-1, 0) or (1, 0).
#          We want to go towards positive X, so we choose (sin(86), -cos(86)) which is roughly (1, 0).
#          So C_ic = P_bridge_end + R_in * (sin(86), -cos(86)).
#          Let's verify: P_bridge_end = (R_in * cos(86), R_in * sin(86)).
#          C_ic = (R_in * cos(86) + R_in * sin(86), R_in * sin(86) - R_in * cos(86)).
#          Distance from (0,0) to C_ic: sqrt((R_in(cos+sin))^2 + (R_in(sin-cos))^2) = R_in * sqrt(cos^2+sin^2+2sin cos + sin^2+cos^2-2sin cos) = R_in * sqrt(2).
#          This is not R_in.
#          Wait, the distance from C_ic to P_bridge_end is R_in.
#          The distance from C_ic to (0,0) is not necessarily R_in.
#          The inner connector is an arc of radius R_in.
#          So the distance from C_ic to any point on the inner connector is R_in.
#          So distance(C_ic, P_bridge_end) = R_in.
#          This is correct.
#          Now, the inner connector must connect to the transition.
#          The transition is tangent to the inner connector.
#          So the distance between C_ic and C_trans is R_in + R_trans.
#          And the transition is tangent to the retention lobe.
#          So the distance between C_trans and LobeCenter is R_in + R_trans.
#          We have C_ic = (R_in * cos(86) + R_in * sin(86), R_in * sin(86) - R_in * cos(86)).
#          LobeCenter = (19.20, 0).
#          We need to find C_trans = (x_t, y_t) such that:
#          1. (x_t - C_ic.x)^2 + (y_t - C_ic.y)^2 = (R_in + R_trans)^2
#          2. (x_t - 19.20)^2 + y_t^2 = (R_in + R_trans)^2
#          3. y_t > 0 (above centerline)
#          4. C_ic is "farther toward the bridge" than C_trans.
#             Bridge is at (0,0). Lobe is at (19.20, 0).
#             "Farther toward the bridge" means closer to (0,0) than C_trans.
#             So distance(C_ic, (0,0)) < distance(C_trans, (0,0))?
#             Or x-coordinate?
#             Let's assume x-coordinate. C_ic.x < C_trans.x.
#          5. C_ic is "closer to the centerline" than C_trans.
#             So |C_ic.y| < |C_trans.y|. Since y_t > 0, C_ic.y < y_t.
#             But C_ic.y = R_in * (sin(86) - cos(86)) which is positive (sin(86) > cos(86)).
#             So C_ic.y > 0.
#             So we need C_ic.y < y_t.
#          This gives us a system of equations to solve for C_trans.

# Let's calculate the values.
R_in = inner_bridge_radius
R_trans = lobe_to_inner_connector_transition_radius
D_lobe = bridge_to_retention_lobe_center_distance
theta_bridge = math.radians(bridge_inner_arc_half_sweep_angle)

# P_bridge_end
P_bridge_end = App.Vector(R_in * math.cos(theta_bridge), R_in * math.sin(theta_bridge), 0)

# Tangent vector at P_bridge_end (direction towards positive X)
# The radius vector is (cos, sin). The tangent is (-sin, cos) or (sin, -cos).
# We want to go towards positive X.
# At 86 deg, cos is small positive, sin is large positive.
# (-sin, cos) is (-large, small) -> mostly negative X.
# (sin, -cos) is (large, -small) -> mostly positive X.
# So we choose (sin, -cos).
Tangent_dir = App.Vector(math.sin(theta_bridge), -math.cos(theta_bridge), 0)
# Normalize (it should be unit length)
Tangent_dir.normalize()

# C_ic is at distance R_in from P_bridge_end along the tangent direction.
C_ic = P_bridge_end + R_in * Tangent_dir

# Now solve for C_trans.
# Let D = R_in + R_trans
D = R_in + R_trans

# Equations:
# (x_t - C_ic.x)^2 + (y_t - C_ic.y)^2 = D^2
# (x_t - D_lobe)^2 + y_t^2 = D^2
# Subtract the two equations:
# (x_t - C_ic.x)^2 - (x_t - D_lobe)^2 + (y_t - C_ic.y)^2 - y_t^2 = 0
# (x_t^2 - 2*x_t*C_ic.x + C_ic.x^2) - (x_t^2 - 2*x_t*D_lobe + D_lobe^2) + (y_t^2 - 2*y_t*C_ic.y + C_ic.y^2) - y_t^2 = 0
# -2*x_t*C_ic.x + C_ic.x^2 + 2*x_t*D_lobe - D_lobe^2 - 2*y_t*C_ic.y + C_ic.y^2 = 0
# 2*x_t*(D_lobe - C_ic.x) - 2*y_t*C_ic.y + (C_ic.x^2 + C_ic.y^2 - D_lobe^2) = 0
# 2*x_t*(D_lobe - C_ic.x) - 2*y_t*C_ic.y = D_lobe^2 - C_ic.x^2 - C_ic.y^2
# Let A = 2*(D_lobe - C_ic.x)
# Let B = -2*C_ic.y
# Let C = D_lobe^2 - C_ic.x^2 - C_ic.y^2
# A*x_t + B*y_t = C
# We also have (x_t - D_lobe)^2 + y_t^2 = D^2
# y_t^2 = D^2 - (x_t - D_lobe)^2
# Substitute into the linear equation:
# A*x_t + B*sqrt(D^2 - (x_t - D_lobe)^2) = C
# B*sqrt(...) = C - A*x_t
# Square both sides:
# B^2 * (D^2 - (x_t - D_lobe)^2) = (C - A*x_t)^2
# This is a quadratic equation in x_t.
# Solve for x_t, then find y_t.
# We need y_t > 0 and C_ic.y < y_t.

A = 2 * (D_lobe - C_ic.x)
B = -2 * C_ic.y
C_const = D_lobe**2 - C_ic.x**2 - C_ic.y**2

# B^2 * (D^2 - (x_t - D_lobe)^2) = (C - A*x_t)^2
# B^2 * D^2 - B^2 * (x_t^2 - 2*x_t*D_lobe + D_lobe^2) = C^2 - 2*C*A*x_t + A^2*x_t^2
# B^2 * D^2 - B^2 * x_t^2 + 2*B^2*D_lobe*x_t - B^2*D_lobe^2 = C^2 - 2*C*A*x_t + A^2*x_t^2
# (A^2 + B^2) * x_t^2 - (2*B^2*D_lobe + 2*C*A) * x_t + (C^2 + B^2*D_lobe^2 - B^2*D^2) = 0

coeff_a = A**2 + B**2
coeff_b = -(2 * B**2 * D_lobe + 2 * C_const * A)
coeff_c = C_const**2 + B**2 * D_lobe**2 - B**2 * D**2

# Solve quadratic
discriminant = coeff_b**2 - 4 * coeff_a * coeff_c
if discriminant < 0:
    raise ValueError("No solution for transition center")

sqrt_disc = math.sqrt(discriminant)
x_t1 = (-coeff_b + sqrt_disc) / (2 * coeff_a)
x_t2 = (-coeff_b - sqrt_disc) / (2 * coeff_a)

# Find corresponding y_t
# y_t = (C - A*x_t) / B
# Check which one gives y_t > 0 and C_ic.y < y_t
valid_x = None
valid_y = None

for x_t in [x_t1, x_t2]:
    # Check if x_t is within range for y_t to be real
    if (x_t - D_lobe)**2 > D**2:
        continue
    y_t_sq = D**2 - (x_t - D_lobe)**2
    if y_t_sq < 0:
        continue
    y_t = math.sqrt(y_t_sq)
    # Check condition: y_t > 0 (already true by sqrt)
    # Check condition: C_ic.y < y_t
    if C_ic.y < y_t:
        valid_x = x_t
        valid_y = y_t
        break

if valid_x is None:
    # Try the other root if the first one didn't work (maybe the condition was wrong)
    # Or maybe we need to check the other sign of y_t? No, y_t must be > 0.
    # Maybe the condition C_ic.y < y_t is not required?
    # "select the inner-connector center farther toward the bridge and closer to the centerline."
    # This implies C_ic is closer to the centerline than C_trans.
    # So |C_ic.y| < |C_trans.y|. Since both are positive, C_ic.y < y_t.
    # If no solution, maybe the geometry is impossible with these parameters?
    # Let's assume the first valid solution is correct.
    # If no solution found, we might need to relax the condition or check the other root.
    # Let's try the other root without the condition first to see if it exists.
    for x_t in [x_t1, x_t2]:
        if (x_t - D_lobe)**2 <= D**2:
            y_t_sq = D**2 - (x_t - D_lobe)**2
            y_t = math.sqrt(y_t_sq)
            if y_t > 0:
                valid_x = x_t
                valid_y = y_t
                break

if valid_x is None:
    raise ValueError("Could not find valid transition center")

C_trans = App.Vector(valid_x, valid_y, 0)

# Now we have all centers.
# We need to construct the profile.
# The profile consists of:
# 1. Inner Bridge Arc: Center (0,0), Radius R_in, from -86 deg to +86 deg.
# 2. Inner Connector Arc: Center C_ic, Radius R_in.
#    Starts at P_bridge_end (angle 86 deg from (0,0)).
#    Ends at the point where it meets the transition.
#    The transition is tangent to the inner connector.
#    So the inner connector ends at the point of tangency with the transition.
#    The point of tangency P_ic_trans is on the line connecting C_ic and C_trans.
#    Distance(C_ic, P_ic_trans) = R_in.
#    Direction from C_ic to C_trans.
#    P_ic_trans = C_ic + R_in * (C_trans - C_ic).normalize()
# 3. Transition Arc: Center C_trans, Radius R_trans.
#    Starts at P_ic_trans.
#    Ends at the point of tangency with the retention lobe.
#    The retention lobe center is LobeCenter = (D_lobe, 0).
#    The point of tangency P_trans_lobe is on the line connecting C_trans and LobeCenter.
#    Distance(C_trans, P_trans_lobe) = R_trans.
#    Direction from C_trans to LobeCenter.
#    P_trans_lobe = C_trans + R_trans * (LobeCenter - C_trans).normalize()
# 4. Retention Lobe Arc: Center LobeCenter, Radius R_in.
#    Starts at P_trans_lobe.
#    Sweeps by retention_lobe_arc_sweep_angle.
#    We need to determine the start angle.
#    The retention lobe must connect to the inner connector via the transition.
#    So the start angle is the angle of the vector (LobeCenter -> P_trans_lobe).
#    The sweep is retention_lobe_arc_sweep_angle.
#    The problem says "retention_lobe_arc_sweep_angle is the full sweep of either mirrored lobe."
#    So the arc goes from start_angle to start_angle + sweep_angle (or -sweep_angle).
#    We need to check the direction.
#    The inner connector is on the upper half (y > 0).
#    The transition is on the upper half (y > 0).
#    So the retention lobe must start at the upper side.
#    So the sweep should be clockwise or counter-clockwise?
#    The inner connector comes from the left (negative X relative to lobe center? No, from the bridge).
#    The bridge is at (0,0). The lobe center is at (19.20, 0).
#    The inner connector is between the bridge and the lobe.
#    So the inner connector is to the left of the lobe center.
#    The transition is between the inner connector and the lobe.
#    So the transition is to the left of the lobe center.
#    So the retention lobe starts at the left side (angle 180 deg?) and sweeps?
#    Or starts at some angle and sweeps to the right?
#    Let's calculate the angle of P_trans_lobe relative to LobeCenter.
#    Angle_start = atan2(P_trans_lobe.y - LobeCenter.y, P_trans_lobe.x - LobeCenter.x)
#    The sweep is retention_lobe_arc_sweep_angle.
#    The lobe must connect to the inner connector.
#    The inner connector is on the upper half.
#    So the lobe must start at the upper side.
#    So the sweep should be from Angle_start to Angle_start - sweep_angle (clockwise) or Angle_start + sweep_angle (counter-clockwise)?
#    If the inner connector is on the upper half, and the lobe is on the upper half, then the lobe must start at the upper side.
#    So the start angle is Angle_start.
#    The sweep is retention_lobe_arc_sweep_angle.
#    The direction depends on the geometry.
#    Let's assume the lobe sweeps from the transition point towards the right (positive X).
#    So the angle decreases (clockwise) if we measure from positive X?
#    Or increases?
#    Let's just use the angle of the start point and add/subtract the sweep.
#    We need to check which direction keeps the lobe on the upper half and connects to the inner connector.
#    The inner connector is at P_ic_trans.
#    The transition is at P_trans_lobe.
#    The lobe starts at P_trans_lobe.
#    The lobe must go towards the inner connector? No, the inner connector is already connected via the transition.
#    The lobe must go towards the other side (the other lobe? No, the other side of the same lobe).
#    The lobe is an arc. It has two ends. One end is connected to the transition.
#    The other end is free? Or connected to something else?
#    "The paired retention-lobe arcs share one center... The lobe radius and each inner-connector radius equal the inner bridge radius implied by the bridge wall."
#    "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
#    This implies the lobe is connected to the inner connector at one end.
#    The other end is free? Or connected to the outer leg?
#    "A straight connector joins each fillet endpoint to its retention lobe."
#    Wait, "A straight connector joins each fillet endpoint to its retention lobe."
#    This is for the outer leg?
#    "Each tip has tip_fillet_radius and is tangent to its outer leg. tip_fillet_exit_radius_angle_from_negative_x locates the terminal radius of that fillet relative to the negative x direction. A straight connector joins each fillet endpoint to its retention lobe."
#    This is confusing.
#    Let's re-read the whole description.
#    "A U-shaped spring clip has one closed front profile whose two legs are symmetric about the longitudinal profile centerline."
#    "clip_width is the full solid width normal to this profile."
#    "In the profile frame, x runs from the open tips toward the closed bridge and y runs between the two legs."
#    "The profile origin lies halfway along x between the outer-bridge center and the shared retention-lobe center, with the bridge center on the positive-x side."
#    Wait, "profile origin lies halfway along x between the outer-bridge center and the shared retention-lobe center".
#    So the origin is at (D_lobe / 2, 0)?
#    "with the bridge center on the positive-x side."
#    So Bridge Center is at (D_lobe / 2, 0)?
#    And Lobe Center is at (-D_lobe / 2, 0)?
#    But earlier I assumed Bridge Center at (0,0) and Lobe Center at (D_lobe, 0).
#    Let's re-read: "bridge_to_retention_lobe_center_distance is the full x-direction distance from the bridge center to that shared lobe center."
#    So the distance is D_lobe.
#    "The profile origin lies halfway along x between the outer-bridge center and the shared retention-lobe center".
#    So the origin is at (D_lobe / 2, 0) if Bridge is at (0,0) and Lobe is at (D_lobe, 0).
#    But the problem says "with the bridge center on the positive-x side."
#    This implies the origin is between them, and the bridge is on the positive X side.
#    So if the origin is at (0,0), then Bridge Center is at (D_lobe / 2, 0) and Lobe Center is at (-D_lobe / 2, 0).
#    But the problem says "x runs from the open tips toward the closed bridge".
#    So the open tips are at negative X, and the bridge is at positive X.
#    So the origin is somewhere in the middle.
#    Let's assume the origin is at (0,0).
#    Then Bridge Center is at (D_lobe / 2, 0).
#    Lobe Center is at (-D_lobe / 2, 0).
#    But the problem says "bridge_to_retention_lobe_center_distance is the full x-direction distance from the bridge center to that shared lobe center."
#    So the distance is D_lobe.
#    So if Bridge is at (D_lobe / 2, 0) and Lobe is at (-D_lobe / 2, 0), the distance is D_lobe.
#    This matches.
#    But earlier I calculated the geometry assuming Bridge at (0,0) and Lobe at (D_lobe, 0).
#    This is just a translation.
#    The relative positions are what matters.
#    So let's stick with Bridge at (0,0) and Lobe at (D_lobe, 0) for simplicity, and then translate the whole sketch if needed.
#    But the problem says "The profile origin lies halfway along x between the outer-bridge center and the shared retention-lobe center".
#    So the origin is at (D_lobe / 2, 0) in the Bridge-Lobe frame.
#    So in the sketch frame, we should place the origin at (D_lobe / 2, 0).
#    So Bridge Center = (D_lobe / 2, 0).
#    Lobe Center = (-D_lobe / 2, 0).
#    But the problem says "with the bridge center on the positive-x side."
#    So if the origin is at (0,0), then Bridge Center is at (D_lobe / 2, 0) and Lobe Center is at (-D_lobe / 2, 0).
#    This means the bridge is on the positive X side, and the lobe is on the negative X side.
#    But the problem says "x runs from the open tips toward the closed bridge".
#    So the open tips are at negative X, and the bridge is at positive X.
#    This matches.
#    So the sketch frame origin is at (D_lobe / 2, 0) relative to the Bridge-Lobe frame.
#    So in the sketch, Bridge Center is at (D_lobe / 2, 0).
#    Lobe Center is at
