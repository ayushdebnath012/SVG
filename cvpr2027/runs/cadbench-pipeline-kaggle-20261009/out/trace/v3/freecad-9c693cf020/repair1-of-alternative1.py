import FreeCAD as App
import Part
import math
from pathlib import Path

# Initialize Document
doc = App.newDocument("SpringClip")

# Create PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define Named Parameters in a VarSet for easy editing
params = body.newObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "bridge_outer_radius")
params.addProperty("App::PropertyLength", "bridge_wall_thickness")
params.addProperty("App::PropertyLength", "bridge_to_tip_fillet_center_length")
params.addProperty("App::PropertyLength", "tip_fillet_radius")
params.addProperty("App::PropertyLength", "lobe_to_inner_connector_transition_radius")
params.addProperty("App::PropertyLength", "bridge_to_retention_lobe_center_distance")
params.addProperty("App::PropertyAngle", "retention_lobe_arc_sweep_angle")
params.addProperty("App::PropertyLength", "clip_width")
params.addProperty("App::PropertyAngle", "bridge_inner_arc_half_sweep_angle")
params.addProperty("App::PropertyAngle", "tip_fillet_exit_radius_angle_from_negative_x")

# Set Values
params.bridge_outer_radius = 6.50
params.bridge_wall_thickness = 2.60
params.bridge_to_tip_fillet_center_length = 26.00
params.tip_fillet_radius = 1.10
params.lobe_to_inner_connector_transition_radius = 1.95
params.bridge_to_retention_lobe_center_distance = 19.20
params.retention_lobe_arc_sweep_angle = 82.145694714
params.clip_width = 2.20
params.bridge_inner_arc_half_sweep_angle = 86.0
params.tip_fillet_exit_radius_angle_from_negative_x = 45.0

# --- Geometry Calculation ---
# Coordinate System:
# Origin: Halfway between Outer Bridge Center and Shared Retention Lobe Center.
# X: Runs from Open Tips (Left) to Closed Bridge (Right).
# Y: Runs between the two legs (Upper is +Y, Lower is -Y).
# Z: Normal to the sketch plane (Thickness direction).

# Reference Points relative to Bridge Center (X=0, Y=0):
# Retention Lobe Center X = +bridge_to_retention_lobe_center_distance
# Sketch Origin X = Retention Lobe Center X / 2

bridge_center_x = 0.0
lobe_center_x_rel = params.bridge_to_retention_lobe_center_distance.Value
origin_x = lobe_center_x_rel / 2.0

# Helper to get absolute X
def get_abs_x(rel_x):
    return origin_x + rel_x

# 1. Outer Bridge
# Center: (0, 0)
# Radius: R_outer
R_outer = params.bridge_outer_radius.Value
# Upper Leg Start (Tip of arc): (0, R_outer)
# Lower Leg Start (Tip of arc): (0, -R_outer)

# 2. Straight Outer Legs
# Length to Fillet Center: L_fillet
L_fillet = params.bridge_to_tip_fillet_center_length.Value
# Upper Leg End (before fillet): (L_fillet, R_outer)
# Lower Leg End (before fillet): (L_fillet, -R_outer)

# 3. Tip Fillets
# Radius: R_fil
R_fil = params.tip_fillet_radius.Value
# Center: (L_fillet, 0)
# Tangent to outer leg (Horizontal).
# Exit angle from negative X: 45 deg.
# This defines the tangent direction at the exit point relative to the bridge (negative X direction).
# For the upper tip, the connector goes towards the lobe (Left and Down).
# Angle from -X (180 deg) downwards by 45 deg -> 225 deg (or -135 deg).
# The fillet connects the horizontal leg (0 deg) to the connector (225 deg).
# The arc must turn 225 degrees? No, the fillet is on the "inside" of the corner formed by the leg and the connector.
# The leg is moving Right. The connector is moving Left-Down.
# The material is "above" the leg and "above" the connector? No, the clip is the material.
# The outer contour follows the leg, then the fillet, then the connector.
# The tangent at the start of the fillet (at the leg) is 0 deg (East).
# The tangent at the end of the fillet (at the connector) is 225 deg (South-West).
# The angle swept by the normal? Or the tangent?
# Tangent change: 0 -> 225. This is a 225 degree turn.
# However, a fillet usually implies a convex rounding.
# If we go from East to South-West, we are turning "Left" (Counter-Clockwise) by 225 degrees?
# Or "Right" (Clockwise) by 135 degrees?
# Let's visualize the corner.
# Leg: Top edge. Connector: Inner edge?
# If the connector is the inner edge, the material is between them.
# The outer contour goes Leg -> Fillet -> Connector.
# The corner is "convex" relative to the outside world? No, the clip is the object.
# The corner is the tip of the leg.
# If the connector goes to the lobe (inwards), the corner is "pointy" if not filleted.
# The fillet rounds it.
# The tangent at the leg is East (0).
# The tangent at the connector is South-West (225).
# To go from East to South-West smoothly, we turn 135 degrees Clockwise (Right) or 225 Counter-Clockwise (Left).
# Since the connector goes "in" (towards the center of the clip), and the leg is "out", the turn is likely 135 degrees (Right turn) if we consider the path along the outer surface?
# Wait, if I walk along the outer surface:
# 1. Walk East along the leg.
# 2. Turn to walk South-West along the connector.
# The turn is 135 degrees to the Right.
# So the fillet arc is 135 degrees.
# Center of fillet:
# Start point P1 = (L_fillet, R_outer). Tangent = (1, 0). Normal = (0, -1) (inwards).
# End point P2. Tangent = (-1/sqrt(2), -1/sqrt(2)). Normal = (1/sqrt(2), -1/sqrt(2)) (inwards).
# Center C = P1 + R_fil * Normal_start = (L_fillet, R_outer - R_fil).
# Let's check if P2 is at distance R_fil from C.
# P2 is at angle 225 deg from C?
# Vector C->P1 is (0, R_fil). Angle 90 deg.
# Vector C->P2 should be at 90 + 135 = 225 deg?
# If the tangent rotates 135 deg clockwise, the normal rotates 135 deg clockwise.
# Normal at start: (0, -1) (270 deg).
# Normal at end: 270 - 135 = 135 deg.
# Vector at 135 deg is (-1, 1).
# So P2 = C + R_fil * (-1, 1) = (L_fillet - R_fil, R_outer - R_fil + R_fil) = (L_fillet - R_fil, R_outer).
# This P2 has Y = R_outer. But the connector must go down.
# My normal calculation might be flipped.
# Let's restart the fillet geometry logic.
# Path: Leg (East) -> Fillet -> Connector (South-West).
# The corner is "outside" the material? No, the material is the clip.
# The outer boundary is the path.
# The corner is the tip.
# If I trace the boundary:
# Start at (0, R_outer). Go East to (L_fillet, R_outer).
# Then curve to the connector.
# The connector goes to the lobe (Left and Down).
# So the curve must turn "Left" (Counter-Clockwise) to face South-West?
# If I turn Left from East (0), I go North. That's wrong.
# I must turn Right (Clockwise).
# East (0) -> South (270/-90) -> South-West (225/-135).
# Turn is 135 degrees Clockwise.
# Center of fillet:
# Start Point P1 = (L_fillet, R_outer).
# Tangent T1 = (1, 0).
# Normal N1 (pointing to center of curvature) = (0, -1) (Down).
# Center C = P1 + R_fil * N1 = (L_fillet, R_outer - R_fil).
# End Point P2:
# Tangent T2 direction: 225 deg (-135 deg).
# Normal N2 direction: 225 - 90 = 135 deg.
# N2 = (-cos(45), sin(45)) = (-0.707, 0.707).
# P2 = C + R_fil * N2 = (L_fillet - R_fil*0.707, R_outer - R_fil + R_fil*0.707).
# This P2 is at Y > R_outer? No, R_fil*0.707 < R_fil. So Y < R_outer.
# This seems correct. The connector starts at P2 and goes South-West.
# So the fillet center is (L_fillet, R_outer - R_fil).
# The arc goes from Angle 270 (South) to Angle 135 (North-West)?
# Wait.
# Vector C->P1 = (0, R_fil). Angle 90 deg.
# Vector C->P2 = (-R_fil*cos(45), R_fil*sin(45)). Angle 135 deg.
# The arc goes from 90 to 135? That's 45 degrees.
# But the tangent change is 135 degrees.
# There is a mismatch.
# Let's re-evaluate the "Exit Angle".
# "tip_fillet_exit_radius_angle_from_negative_x" = 45.0 degrees.
# This is the angle of the *radius*? Or the *tangent*?
# "exit radius angle" usually means the angle of the line from the center to the exit point.
# If the exit radius is at 45 deg from Negative X:
# Negative X is 180 deg.
# 45 deg from it could be 180-45=135 or 180+45=225.
# If it's 135 deg (North-West):
# Then the exit point is at 135 deg from the center.
# The tangent at the exit point is perpendicular to the radius.
# Radius angle 135 -> Tangent angle 45 or 225.
# If the connector goes to the lobe (Left and Down), the tangent must be 225 (South-West).
# This matches!
# So:
# Exit Radius Angle = 135 deg.
# Exit Tangent Angle = 225 deg.
# Start Radius Angle:
# The fillet is tangent to the outer leg (Horizontal, East).
# Radius must be Vertical.
# Since the center is below the leg (to round the corner inwards), the start radius is pointing Up (90 deg).
# So Start Radius Angle = 90 deg.
# End Radius Angle = 135 deg.
# Sweep = 135 - 90 = 45 degrees.
# This seems too small for a "fillet" connecting a leg to a connector.
# Let's re-read: "tangent to its outer leg".
# If the fillet is 45 degrees, the connector would be very short or the geometry is tight.
# Is it possible the "exit radius angle" is measured differently?
# Or maybe the "exit radius" is the tangent?
# "tip_fillet_exit_radius_angle_from_negative_x" -> "radius angle".
# If the radius is at 45 deg from -X, then the radius is at 135 deg (NW) or 225 deg (SW).
# If it's 225 deg (SW):
# Radius points SW. Tangent points NW (45 deg) or SE (135 deg).
# Neither points to the lobe (which is Left/Down).
# So it must be 135 deg (NW).
# Radius points NW. Tangent points SW (225 deg) or NE (45 deg).
# SW (225 deg) points to the lobe. Correct.
# So the geometry is:
# Start Radius: 90 deg (Up).
# End Radius: 135 deg (NW).
# Sweep: 45 deg.
# This implies the connector starts at an angle of 135 deg from the fillet center.
# And the connector is tangent to the fillet at that point.
# This seems consistent.

# Let's calculate the coordinates for the sketch.
# We will construct the Outer Path and the Inner Path.
# Outer Path:
# 1. Outer Bridge Arc: (0, R_outer) to (0, -R_outer) via (R_outer, 0)?
#    No, "semicircular". Usually means the top half? Or the whole bridge?
#    "outer bridge is semicircular... straight outer legs extend".
#    This implies the bridge is the top part (semicircle) and legs go down?
#    Or the bridge is the curved part connecting the legs.
#    Given "x runs from open tips toward the closed bridge", the bridge is at the right (positive X).
#    The legs are at the left (negative X relative to bridge? No, tips are at the ends).
#    "x runs from the open tips toward the closed bridge".
#    So Tips are at Left (Low X), Bridge is at Right (High X).
#    My previous setup: Bridge Center at 0. Tips at L_fillet (Positive X).
#    This contradicts "x runs from tips toward bridge".
#    If Tips are at Low X and Bridge at High X:
#    Bridge Center X = 0.
#    Tips X = -L_fillet.
#    Let's re-orient.
#    Origin: Halfway between Bridge Center and Lobe Center.
#    Bridge Center is at +X relative to Origin?
#    "bridge_to_retention_lobe_center_distance is the full x-direction distance from the bridge center to that shared lobe center."
#    If Bridge is at 0, Lobe is at +D.
#    Origin is at +D/2.
#    Tips are "toward the open tips" from the bridge.
#    So Tips are at -L_fillet relative to Bridge Center.
#    So Tips X = -L_fillet.
#    This makes sense. Tips are far left. Bridge is center. Lobe is right.
#    Wait, "bridge_to_tip_fillet_center_length" is measured along x from the bridge center to either mirrored tip-fillet center.
#    So distance is L_fillet.
#    Direction: Tips are away from the bridge.
#    So if Bridge is at 0, Tips are at -L_fillet.
#    Let's adjust coordinates.
#    Bridge Center: (0, 0).
#    Tips (Fillet Centers): (-L_fillet, 0).
#    Retention Lobe Center: (+D, 0).
#    Origin (Sketch): (+D/2, 0).

# Recalculating Fillet Geometry with this orientation:
# Upper Leg: From Bridge (0, R_outer) to Fillet Center (-L_fillet, R_outer).
# Direction: West (180 deg).
# Fillet Center: (-L_fillet, R_outer - R_fil). (Center is below the leg to round the corner).
# Start of Fillet (at Leg): Tangent West (180 deg). Radius Up (90 deg).
# End of Fillet (at Connector):
# "tip_fillet_exit_radius_angle_from_negative_x" = 45 deg.
# Negative X is West (180 deg).
# 45 deg from West: 180-45=135 (NW) or 180+45=225 (SW).
# The connector goes to the Lobe (Right and Down? No, Lobe is at +D, which is Right).
# So the connector goes Right and Down.
# Tangent must point South-East (315 deg / -45 deg).
# Radius must be perpendicular to Tangent.
# If Tangent is 315 deg, Radius is 315-90=225 (SW) or 315+90=45 (NE).
# Which one?
# The fillet center is at (-L_fillet, R_outer - R_fil).
# The leg is at Y = R_outer.
# The connector goes to the lobe (Y < R_outer).
# So the connector goes Down.
# The fillet connects the Westward leg to the South-Eastward connector.
# The turn is from 180 (West) to 315 (SE).
# This is a 135 degree turn (Clockwise).
# Center of fillet:
# Start Point P1 = (-L_fillet, R_outer).
# Tangent West. Normal Down (270 deg).
# Center C = P1 + R_fil * (0, -1) = (-L_fillet, R_outer - R_fil).
# End Point P2:
# Radius Angle?
# We need the tangent at P2 to be 315 deg.
# Normal at P2 = 315 - 90 = 225 deg (SW).
# Vector C->P2 = R_fil * (cos(225), sin(225)) = R_fil * (-0.707, -0.707).
# P2 = C + (-0.707*R_fil, -0.707*R_fil) = (-L_fillet - 0.707*R_fil, R_outer - R_fil - 0.707*R_fil).
# This P2 is further Left and Lower.
# But the connector must go to the Lobe (Right).
# This implies the connector starts going Left? That's wrong.
# Maybe the "exit radius angle" defines the radius direction from the *Fillet Center* to the *Exit Point*.
# If the radius is at 45 deg from Negative X (West):
# Angle = 135 deg (NW) or 225 deg (SW).
# If Radius is 135 deg (NW):
# Vector C->P2 = R_fil * (-0.707, 0.707).
# P2 = (-L_fillet - 0.707*R_fil, R_outer - R_fil + 0.707*R_fil).
# Y is still < R_outer. X is more negative.
# Still going Left.
# If Radius is 225 deg (SW):
# Vector C->P2 = R_fil * (-0.707, -0.707).
# P2 = (-L_fillet - 0.707*R_fil, R_outer - R_fil - 0.707*R_fil).
# Still going Left.
# This suggests the fillet center is on the *other* side?
# If the fillet center is *above* the leg?
# C = (-L_fillet, R_outer + R_fil).
# Start Radius: Down (270 deg).
# End Radius: ?
# If we want to turn from West (180) to SE (315), we turn Right (Clockwise).
# Center must be "Right" of the path.
# Path: West -> SE.
# Right of West is North. Right of SE is NW.
# So Center should be North-West of the path?
# If Center is at (-L_fillet, R_outer + R_fil).
# Start Point P1 = (-L_fillet, R_outer). Radius Down (270).
# End Point P2: Radius at 225 (SW)?
# Vector C->P2 = R_fil * (-0.707, -0.707).
# P2 = (-L_fillet - 0.707*R_fil, R_fil - 0.707*R_fil).
# This is still Left.
# Is it possible the "exit radius angle" is from the *Positive* X?
# "from_negative_x" is explicit.
# Maybe the connector goes to the lobe which is *Left* of the bridge?
# "bridge_to_retention_lobe_center_distance is the full x-direction distance from the bridge center to that shared lobe center."
# "x runs from the open tips toward the closed bridge".
# So Tips (Left) -> Bridge (Center) -> Lobe (Right).
# This seems robust.
# Why is the connector going Left?
# Maybe the "Tip Fillet" is at the *inner* corner?
# "Each tip has tip_fillet_radius and is tangent to its outer leg."
# "A straight connector joins each fillet endpoint to its retention lobe."
# If the fillet is at the tip of the outer leg, and the connector goes to the lobe...
# The lobe is "inside" the U.
# The tip is the end of the leg.
# The connector must go from the tip *inwards* to the lobe.
# So the connector goes Right (towards the bridge/lobe).
# My calculation showed the connector going Left.
# This implies the fillet center is on the *Right* of the leg?
# If the leg is moving West, and we want to turn East (towards the lobe), we must turn 180 degrees?
# No, the leg is the outer edge. The connector is the inner edge?
# If the connector is the inner edge, it is parallel to the leg?
# No, "straight connector joins... to its retention lobe".
# The lobe is an arc.
# The connector is a straight line from the tip to the lobe.
# The tip is at (-L_fillet, R_outer).
# The lobe is at (+D, Y_lobe).
# The connector goes from (-L_fillet, R_outer) to (+D, Y_lobe).
# This is a long line going Right and Down.
# The fillet connects the Leg (Westward) to this Connector (South-Eastward).
# The turn is 135 degrees (West to SE).
# The center of the fillet must be such that the arc turns 135 degrees.
# If the leg is West (180) and connector is SE (315).
# The center must be "inside" the turn.
# Turn is Right (Clockwise). Center is to the Right of the path.
# Path: West -> SE.
# Right of West is North. Right of SE is NW.
# So Center is North-West of the path.
# Center Y > R_outer.
# Center X < -L_fillet.
# Let's try Center = (-L_fillet - R_fil, R_outer + R_fil).
# Start Point P1 = (-L_fillet, R_outer).
# Vector C->P1 = (R_fil, -R_fil). Angle -45 (315).
# Tangent at P1: Perpendicular to Radius. 315+90=405=45 (NE) or 315-90=225 (SW).
# We need Tangent West (180).
# This doesn't match.
# Let's try Center = (-L_fillet, R_outer + R_fil).
# Start Point P1 = (-L_fillet, R_outer).
# Vector C->P1 = (0, -R_fil). Angle 270 (South).
# Tangent at P1: 270+90=0 (East) or 270-90=180 (West).
# We need West. So Tangent is 180. Correct.
# End Point P2:
# We need Tangent 315 (SE).
# Radius must be 315-90=225 (SW) or 315+90=45 (NE).
# If Radius is 225 (SW):
# Vector C->P2 = R_fil * (-0.707, -0.707).
# P2 = (-L_fillet - 0.707*R_fil, R_fil - 0.707*R_fil).
# This P2 is Left and Down.
# But the connector must go Right.
# This implies the "exit radius angle" of 45 deg from -X (West) means the radius is at 135 deg (NW) or 225 deg (SW).
# If the radius is at 135 deg (NW):
# Vector C->P2 = R_fil * (-0.707, 0.707).
# P2 = (-L_fillet - 0.707*R_fil, R_fil + 0.707*R_fil).
# This is Left and Up.
# If the radius is at 225 deg (SW):
# P2 is Left and Down.
# In both cases, P2 is Left of the fillet center (-L_fillet).
# This means the connector starts going Left.
# This contradicts the geometry of the clip (Tip -> Lobe).
# UNLESS the "Tip Fillet" is not at the very end of the leg, but somewhere else?
# Or the "exit radius angle" is measured from the *Positive* X?
# Or the "negative x" refers to the local coordinate system of the fillet?
# Let's reconsider the "exit radius angle".
# Maybe it's the angle of the *tangent*?
# "tip_fillet_exit_radius_angle_from_negative_x"
# If it's the tangent angle: 45 deg from -X (West).
# Tangent = 135 (NW) or 225 (SW).
# If Tangent is 225 (SW):
# Then the connector goes Left and Down.
# This would mean the lobe is to the Left of the tip.
# But the lobe is to the Right of the bridge, and the tip is to the Left of the bridge.
# So the lobe is to the Right of the tip.
# So the connector must go Right.
# This implies the tangent must be East-ish.
# 45 deg from -X (West) is 135 or 225. Neither is East.
# 45 deg from +X (East) is 45 or 315.
# If the angle was from +X, then 315 (SE) would work.
# Is it possible "negative_x" is a typo in my interpretation?
# "tip_fillet_exit_radius_angle_from_negative_x"
# Maybe the "negative x" is the direction *from* the tip *to* the bridge?
# Yes, that is the Negative X direction in the global frame (if Bridge is 0, Tip is -L).
# So the angle is measured from the vector pointing to the bridge.
# If the radius is at 45 deg from this vector (West):
# Radius = 135 (NW) or 225 (SW).
# This leads to the same problem.
# What if the "exit radius" is the radius of the *connector*?
# No, "tip_fillet_exit_radius_angle".
# Let's assume the standard interpretation:
# The fillet connects the leg to the connector.
# The connector goes to the lobe.
# The lobe is to the Right.
# The connector goes Right.
# The tangent at the exit must be SE (315).
# The radius at the exit must be 225 (SW) or 45 (NE).
# The angle of this radius from the Negative X (West, 180):
# 225 - 180 = 45 deg.
# 45 - 180 = -135 deg.
# So 225 deg is 45 deg from Negative X.
# So the "exit radius angle" is 45 deg.
# This matches!
# So the Radius is at 225 deg (SW).
# And the Center is such that P2 is at 225 deg from C.
# P2 = C + R_fil * (cos(225), sin(225)).
# We found earlier that if C = (-L_fillet, R_outer + R_fil), then P2 is Left and Up.
# We need P2 to be Right and Down (relative to the leg end).
# This requires the Center to be to the *Right* of the leg end?
# If C = (-L_fillet + R_fil, R_outer + R_fil).
# Start Point P1 = (-L_fillet, R_outer).
# Vector C->P1 = (-R_fil, -R_fil). Angle 225 (SW).
# Tangent at P1: 225+90=315 (SE) or 225-90=135 (NW).
# We need Tangent West (180).
# This doesn't match.
# Let's try C = (-L_fillet, R_outer).
# Start Point P1 = (-L_fillet, R_outer). Radius 0? No.
# Let's try C = (-L_fillet + R_fil, R_outer).
# Start Point P1 = (-L_fillet, R_outer).
# Vector C->P1 = (-R_fil, 0). Angle 180 (West).
# Tangent at P1: 180+90=270 (South) or 180-90=90 (North).
# We need West.
# This is getting complicated.
# Let's use the explicit angles.
# Leg Tangent: 180 (West).
# Connector Tangent: 315 (SE).
# Fillet Radius: R_fil.
# Center C = P1 + R_fil * N1 = P2 - R_fil * N2.
# N1 (Normal at P1) must be perpendicular to 180. So 90 or 270.
# N2 (Normal at P2) must be perpendicular to 315. So 45 or 225.
# We need the arc to go from 180 to 315.
# If we turn Right (Clockwise), the normal rotates Right.
# 90 -> 45 (45 deg turn).
# 270 -> 225 (45 deg turn).
# So the sweep is 45 degrees.
# Case 1: N1 = 90 (North). C = P1 + (0, R_fil) = (-L_fillet, R_outer + R_fil).
# N2 = 45 (NE). P2 = C + R_fil * (0.707, 0.707) = (-L_fillet + 0.707*R_fil, R_outer + R_fil + 0.707*R_fil).
# P2 is Right and Up.
# Connector goes SE (315).
# This works! The connector starts at P2 (Right and Up) and goes SE.
# But P2 is *above* the leg (Y > R_outer).
# The leg is at Y = R_outer.
# The connector goes to the lobe (which is lower).
# So the connector goes Down.
# This seems plausible. The fillet is "outside" the leg?
# No, the leg is the outer edge. The fillet is at the tip.
# If the fillet is outside, the clip is thicker?
# Let's assume this geometry:
# Center C = (-L_fillet, R_outer + R_fil).
# Start P1 = (-L_fillet, R_outer).
# End P2 = (-L_fillet + R_fil*cos(45), R_outer + R_fil + R_fil*sin(45)).
# Connector starts at P2.

# Let's implement this.

# --- Sketch Construction ---

# 1. Outer Path
# - Outer Bridge Arc: From (0, R_outer) to (0, -R_outer) via (R_outer, 0)?
#   "semicircular". Usually means the top half?
#   "outer bridge is semicircular... straight outer legs extend".
#   This implies the bridge is the curved part connecting the legs.
#   If the legs are vertical, the bridge is a semicircle on top?
#   But "x runs from tips toward bridge".
#   So the bridge is at the right.
#   The legs are horizontal?
#   "straight outer legs extend toward the open tips".
#   If the bridge is at the right, and legs extend to the left (tips), then the legs are horizontal.
#   So the bridge is a semicircle connecting the two horizontal legs.
#   Upper Leg: Y = R_outer.
#   Lower Leg: Y = -R_outer.
#   Bridge: Semicircle connecting (0, R_outer) and (0, -R_outer) with center (0,0) and radius R_outer.
#   The arc goes from (0, R_outer) to (0, -R_outer) via (R_outer, 0)?
#   Or via (-R_outer, 0)?
#   "x runs from tips toward bridge".
#   Tips are at Left (-L_fillet). Bridge is at Right (0).
#   So the bridge arc should bulge to the Right (Positive X).
#   So the arc goes from (0, R_outer) to (0, -R_outer) via (R_outer, 0).
#   This is a semicircle in the Right Half Plane.

# - Outer Legs:
#   Upper: From (0, R_outer) to (-L_fillet, R_outer).
#   Lower: From (0, -R_outer) to (-L_fillet, -R_outer).

# - Tip Fillets:
#   Upper: Center (-L_fillet, R_outer + R_fil).
#     Start: (-L_fillet, R_outer).
#     End: (-L_fillet + R_fil*cos(45), R_outer + R_fil + R_fil*sin(45)).
#   Lower: Mirror of Upper.
#     Center (-L_fillet, -R_outer - R_fil).
#     Start: (-L_fillet, -R_outer).
#     End: (-L_fillet + R_fil*cos(45), -R_outer - R_fil - R_fil*sin(45)).
#     Wait, Lower Leg is at Y = -R_outer.
#     Tangent West (180).
#     Connector goes SE (315)?
#     For the lower leg, the connector goes to the lobe (Right and Up? No, lobe is symmetric).
#     Lobe is at Y=0.
#     So connector goes Right and Up (45 deg).
#     Tangent 45 deg.
#     Normal 135 (NW) or 315 (SE).
#     Turn from 180 (West
