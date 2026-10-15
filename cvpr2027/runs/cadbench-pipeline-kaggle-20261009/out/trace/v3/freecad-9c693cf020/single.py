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
# The lobe connects to the inner bridge.
# The inner bridge arc starts at angle 0 (positive X) and goes to bridge_inner_arc_half_sweep_angle (86 deg).
# Wait, the problem says: "bridge_inner_arc_half_sweep_angle is measured from the bridge's positive x radial direction to either inner-bridge endpoint."
# So the inner bridge arc goes from +86 deg to -86 deg? Or just one side?
# "The paired retention-lobe arcs share one center... The lobe radius and each inner-connector radius equal the inner bridge radius implied by the bridge wall."
# "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
# This implies the inner bridge arc ends where the inner connector begins.
# Let's assume the inner bridge arc is symmetric around the X-axis.
# So the inner bridge arc goes from +86 deg to -86 deg.
# The retention lobe must connect to this.
# The retention lobe center is at X = 19.20.
# The inner bridge center is at (0,0).
# Distance between centers = 19.20.
# Sum of radii = inner_bridge_radius + inner_bridge_radius = 2 * inner_bridge_radius.
# If they are tangent externally, distance = sum of radii.
# Let's check: 2 * 5.9 = 11.8. Distance is 19.2. They are not tangent.
# Re-reading: "The lobe radius and each inner-connector radius equal the inner bridge radius".
# "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
# This suggests the inner bridge arc does NOT go all the way to the lobe center.
# The inner bridge arc ends at angle `bridge_inner_arc_half_sweep_angle` (86 deg).
# The inner connector starts there.
# The inner connector is an arc of radius `inner_bridge_radius`.
# The inner connector connects to the retention lobe.
# The retention lobe is an arc of radius `inner_bridge_radius`.
# The retention lobe center is at (19.20, 0).
# The retention lobe sweep is 82.145... degrees.
# The retention lobe must connect to the inner connector.
# The inner connector must connect to the retention lobe.
# The transition between inner connector and retention lobe is a fillet of radius `lobe_to_inner_connector_transition_radius`.

# Let's refine the geometry logic:
# 1. Inner Bridge Arc: Center (0,0), Radius R_in. Starts at angle 0 (positive X), goes to +86 deg and -86 deg.
#    Wait, "bridge_inner_arc_half_sweep_angle is measured from the bridge's positive x radial direction to either inner-bridge endpoint."
#    So the arc is from -86 to +86.
# 2. Inner Connector: Radius R_in. Connects the inner bridge endpoint to the retention lobe.
#    The retention lobe center is at (D_lobe, 0) where D_lobe = 19.20.
#    The retention lobe radius is R_in.
#    The retention lobe sweep is S_lobe = 82.145... deg.
#    The retention lobe must connect to the inner connector.
#    The connection point on the retention lobe is likely at the start/end of its sweep.
#    Let's assume the retention lobe starts at angle 0 relative to its center? Or some other angle?
#    "The paired retention-lobe arcs share one center on the longitudinal profile centerline."
#    "bridge_to_retention_lobe_center_distance is the full x-direction distance from the bridge center to that shared lobe center."
#    So Lobe Center = (19.20, 0).
#    The lobe connects to the inner connector.
#    The inner connector connects to the inner bridge.
#    There is a transition radius R_trans = 1.95 between the inner connector and the retention lobe.
#    This transition is externally tangent to both.
#    We need to find the center of this transition arc.
#    Let C_trans be the center of the transition arc.
#    Distance(C_trans, LobeCenter) = R_in + R_trans.
#    Distance(C_trans, InnerConnectorCenter) = R_in + R_trans.
#    We need to find the InnerConnectorCenter.
#    The inner connector is an arc of radius R_in.
#    It connects the inner bridge endpoint (at angle 86 deg from (0,0)) to the retention lobe.
#    Let's assume the inner connector is tangent to the inner bridge at the endpoint.
#    So the inner connector starts at the point P_bridge = (R_in * cos(86), R_in * sin(86)).
#    The inner connector is tangent to the inner bridge at P_bridge.
#    The tangent vector at P_bridge is perpendicular to the radius vector (cos(86), sin(86)).
#    So the tangent direction is (-sin(86), cos(86)) or (sin(86), -cos(86)).
#    Since the inner connector goes towards the lobe (positive X), and the bridge is at (0,0), the tangent must point generally right.
#    At 86 deg, the radius is almost vertical. The tangent is almost horizontal.
#    The vector from (0,0) to P_bridge is (small, large). Tangent is (-large, small) or (large, -small).
#    We want to go towards positive X. So we need the component of the tangent to be positive.
#    Actually, let's just use the geometry of the transition.

# Let's define the points:
# P_bridge_end = (R_in * cos(86*pi/180), R_in * sin(86*pi/180))
# LobeCenter = (19.20, 0)
# R_in = 5.9
# R_trans = 1.95

# The transition arc is tangent to the Retention Lobe and the Inner Connector.
# The Retention Lobe is an arc of radius R_in centered at LobeCenter.
# The Inner Connector is an arc of radius R_in.
# The transition arc has radius R_trans.
# The transition arc is externally tangent to both.
# So the center of the transition arc, C_trans, is at distance R_in + R_trans from LobeCenter.
# And at distance R_in + R_trans from the center of the Inner Connector, C_ic.
# Also, the Inner Connector is tangent to the Inner Bridge at P_bridge_end.
# So C_ic is at distance R_in from P_bridge_end.
# And the vector C_ic -> P_bridge_end is perpendicular to the tangent of the inner bridge at P_bridge_end.
# The tangent of the inner bridge at P_bridge_end is perpendicular to the radius vector (0,0)->P_bridge_end.
# So C_ic lies on the line passing through P_bridge_end and perpendicular to the radius vector.
# This line is the tangent line to the inner bridge at P_bridge_end.
# So C_ic is on the line: x * cos(86) + y * sin(86) = R_in. (Normal form)
# Wait, the line equation for the tangent at angle theta is x*cos(theta) + y*sin(theta) = R.
# Yes.
# So C_ic is on this line.
# Also, the Inner Connector is tangent to the Retention Lobe? No, there is a transition.
# The Inner Connector connects to the Retention Lobe via the transition.
# So the Inner Connector must be tangent to the transition arc.
# And the Retention Lobe must be tangent to the transition arc.
# This implies the Inner Connector and the Retention Lobe are not directly tangent.
# But the Inner Connector must connect to the Retention Lobe.
# The problem says: "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
# This is confusing. "sloped inner wall" might refer to the transition?
# Let's re-read carefully: "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
# This might mean the inner connector and the inner bridge are tangent to each other?
# "tangent to the same sloped inner wall" -> maybe the transition is the "sloped inner wall"?
# If the transition is the "sloped inner wall", then the inner connector and the inner bridge are tangent to the transition.
# This matches the "externally tangent to both neighboring arcs" description for the transition.
# So:
# 1. Inner Bridge Arc (R_in) ends at P_bridge_end.
# 2. Transition Arc (R_trans) is tangent to Inner Bridge Arc at P_bridge_end.
# 3. Transition Arc (R_trans) is tangent to Retention Lobe Arc (R_in).
# 4. Inner Connector Arc (R_in) is tangent to Transition Arc (R_trans).
# 5. Inner Connector Arc (R_in) is tangent to Retention Lobe Arc (R_in)?
#    "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
#    This sentence is tricky. "sloped inner wall" could be the transition.
#    If the inner connector is tangent to the transition, and the inner bridge is tangent to the transition, that's consistent.
#    But what about the connection between the inner connector and the retention lobe?
#    "The transition is externally tangent to both neighboring arcs."
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
#       But the text says "select the transition center on the bridge side of the lobe center". This is consistent.
#       "select the inner-connector center farther toward the bridge and closer to the centerline."
#       This implies the inner connector is between the transition and the bridge?
#       Or between the transition and the lobe?
#       "farther toward the bridge" than the transition center.
#       So: Bridge ... Inner Connector ... Transition ... Lobe.
#       This means the Inner Connector is tangent to the Inner Bridge?
#       "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
#       This is the confusing part.
#       Maybe "sloped inner wall" refers to the Inner Connector itself? No.
#       Maybe it means the Inner Connector and the Inner Bridge are tangent to each other?
#       If they are tangent to each other, then the transition is between the Inner Connector and the Retention Lobe.
#       Let's assume the standard spring clip geometry:
#       Bridge -> Inner Connector -> Transition -> Retention Lobe.
#       In this case:
#       - Inner Bridge and Inner Connector are tangent at P_bridge_end.
#       - Inner Connector and Transition are tangent.
#       - Transition and Retention Lobe are tangent.
#       Let's check the "sloped inner wall" sentence again.
#       "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
#       This could mean the Inner Connector and the Inner Bridge are tangent to the Transition?
#       If so, the order is Bridge -> Transition -> Inner Connector -> Lobe.
#       But then the transition is closer to the bridge.
#       The text says "select the inner-connector center farther toward the bridge".
#       This implies the inner connector is farther from the lobe than the transition.
#       So: Lobe ... Transition ... Inner Connector ... Bridge.
#       This matches "inner-connector center farther toward the bridge".
