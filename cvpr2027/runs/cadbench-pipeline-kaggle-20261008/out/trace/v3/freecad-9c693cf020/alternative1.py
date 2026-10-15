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

# Get reference axes (XY plane origin)
# FreeCAD 1.1 standard axes: X_Axis, Y_Axis, Z_Axis, XY_Plane, XZ_Plane, YZ_Plane
# We will create a local sketch on the XY_Plane.
# Coordinate System:
# X: Bridge center (0,0) to Tips (positive x)
# Y: Between legs (positive y is upper leg, negative y is lower leg)
# Z: Out of plane (normal to sketch)

# 1. Create Main Profile Sketch (Side View)
sketch_main = body.newObject("Sketcher::SketchObject", "MainProfileSketch")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch_main.ConstrainToCurrentView = False
sketch_main.UseInternalConstraints = False

# Calculations based on geometry description:
# Origin: Halfway between Outer Bridge Center and Shared Retention Lobe Center.
# Let Outer Bridge Center be at x=0.
# Retention Lobe Center is at x = +bridge_to_retention_lobe_center_distance.
# Sketch Origin x = bridge_to_retention_lobe_center_distance / 2.

bridge_center_x = 0.0
lobe_center_x = params.bridge_to_retention_lobe_center_distance.Value
origin_x = lobe_center_x / 2.0

# Y coordinates:
# clip_width is the full solid width normal to the profile.
# The profile is the centerline of the clip (x-z plane equivalent in 3D, but here we are in x-y plane sketch).
# Wait, "clip_width is the full solid width normal to this profile".
# If the profile is in the X-Y plane, the "width" of the spring (the length of the strip) is usually along Z in the 3D model.
# However, the prompt says "x runs from the open tips toward the closed bridge and y runs between the two legs".
# This implies the sketch is the cross-section of the spring material itself.
# So the "solid width" mentioned in the prompt description likely refers to the distance between the two legs in the Y direction of this sketch.
# Let's re-read carefully: "A U-shaped spring clip... clip_width is the full solid width normal to this profile."
# If the profile is the cross-section, then the "width" of the strip is the Z-dimension of the final extrusion.
# BUT, the prompt also says "y runs between the two legs". This implies the Y-axis in the sketch is the width of the U-shape opening.
# And "clip_width" is defined as 2.20 mm.
# If the sketch is the cross-section (thickness of the metal), then Y would be the thickness? No, Y runs between legs.
# This is a standard Spring Clip.
# Shape: A strip bent into a U.
# The "Profile" described (Bridge, Legs, Lobes) is the shape of the *strip cross-section*? No, that would be a simple rectangle.
# The description describes the *shape of the clip itself* as seen from the front (the hook shape).
# So the Sketch is the Front View (the shape of the hook).
# The "Width" of the material (thickness of the strip) is the "clip_width" = 2.20 mm.
# This thickness is usually extruded along the Z-axis (normal to the sketch plane) in FreeCAD to create the 3D body.
# So:
# Sketch Plane: XY.
# X: Horizontal (Bridge center to tips).
# Y: Vertical (Between legs).
# The thickness of the metal strip is `clip_width`.
# We will extrude the sketch along Z (using Pad) with Length = clip_width.

# Let's verify the "y runs between the two legs" part.
# Yes, in the front view sketch, Y separates the upper and lower legs.
# The thickness of the material is the dimension perpendicular to this plane (Z).

# --- Geometry Construction for Front View Sketch ---

# 1. Outer Bridge Arc
# Center: (0, 0)
# Radius: params.bridge_outer_radius
bridge_outer_arc = Part.makeArc(
    App.Vector(bridge_center_x, 0, 0),
    App.Vector(0, params.bridge_outer_radius, 0),
    App.Vector(bridge_center_x, 0, 0), # Start/End logic handled by angles usually, or 3 points
    # Let's use 3 points or angle. 
    # Upper leg end (start of arc): (0, bridge_outer_radius)
    # Lower leg end (end of arc): (0, -bridge_outer_radius)
    # But the arc connects to straight legs.
    pass
)

# Define points for sketch geometry
# Bridge Center: C_bridge = (0, 0)
# Upper Leg Start (Tip of arc): P_bridge_top = (0, bridge_outer_radius)
# Lower Leg Start (Tip of arc): P_bridge_bot = (0, -bridge_outer_radius)

# 2. Straight Outer Legs
# Extend from bridge center towards tips (Positive X).
# Length: bridge_to_tip_fillet_center_length (distance to fillet center)
# Upper Leg Line: From (0, bridge_outer_radius) to (L, bridge_outer_radius)
# Lower Leg Line: From (0, -bridge_outer_radius) to (L, -bridge_outer_radius)
L_fillet = params.bridge_to_tip_fillet_center_length.Value

# 3. Tip Fillets
# Center: (L_fillet, 0)
# Radius: params.tip_fillet_radius
# The fillet connects the straight leg to the inner curve.
# "tangent to its outer leg" -> Yes.
# "tip_fillet_exit_radius_angle_from_negative_x": 45 degrees.
# Negative X is towards the bridge.
# Angle from Negative X axis.
# Upper tip: The curve starts at the straight leg (angle 0 from positive X? No, straight leg is along X).
# The straight leg is horizontal (angle 0).
# The fillet connects the horizontal leg to the inner curve.
# The exit angle is 45 deg from Negative X.
# So the tangent at the exit point is at 45 deg from -X (i.e., 135 deg standard angle, or 45 deg depression).
# Since it's a fillet, the center of the fillet lies on the normal to the curve.
# Let's trace the path:
# Upper Leg: Horizontal line at y = R_outer. Moving +X.
# Fillet: Arc connecting horizontal line to inner curve.
# Inner curve: Sloped line going down towards the lobe?
# Wait, the description says "A straight connector joins each fillet endpoint to its retention lobe."
# And "The paired retention-lobe arcs share one center...".
# Let's map the sequence:
# 1. Outer Bridge (Semicircle top/bottom).
# 2. Straight Outer Leg (Horizontal).
# 3. Tip Fillet (Curved).
# 4. Straight Connector (Sloped).
# 5. Retention Lobe Arc.
# 6. Inner Connector (Sloped, connecting to inner bridge).
# 7. Inner Bridge (Arc).

# Let's calculate coordinates.
# Origin: (origin_x, 0).
# Bridge Center in Sketch: (origin_x - bridge_to_retention_lobe_center_distance/2, 0).
# Let's shift everything so Bridge Center is at 0 for calculation, then apply offset.
# Actually, let's just use the absolute coordinates derived from `origin_x`.
# Bridge Center X = 0.
# L_fillet X = L_fillet.

# Upper Leg End Point (before fillet): P_leg_end = (L_fillet, bridge_outer_radius)
# Lower Leg End Point (before fillet): P_leg_end_bot = (L_fillet, -bridge_outer_radius)

# Fillet Geometry (Upper):
# Radius R_fil = params.tip_fillet_radius.Value
# Center C_fil: Distance R_fil from the straight leg (y = bridge_outer_radius).
# Since it connects to an inner curve that goes "inwards" (towards the center of the clip),
# and the clip is symmetric, the fillet center must be inside the corner.
# The straight leg is horizontal. The fillet is tangent to it.
# The "exit" is where it meets the connector.
# "tip_fillet_exit_radius_angle_from_negative_x" = 45 deg.
# This defines the tangent direction at the exit point relative to the bridge (negative x).
# If the tangent is at 45 deg from -X (inwards), then the normal to the curve at that point is at 45 deg from Y (vertical).
# Let's visualize:
# Upper corner: Top-Right.
# Straight leg: Moving Right (0 deg).
# Inner curve: Moving Down-Left?
# The fillet bridges the Rightward motion to the Down-Left motion.
# The tangent at the start of the fillet (at the leg) is Horizontal (0 deg).
# The tangent at the end of the fillet (at the connector) is at 45 deg from -X.
# -X is 180 deg. 45 deg from -X could be 180-45=135 or 180+45=225.
# Since it's the upper tip, it must go down. So the tangent points roughly South-West.
# Angle = 225 deg (-135 deg).
# The change in angle of the tangent is 225 - 0 = 225 deg? No, fillet angle is usually < 180.
# Maybe the tangent is 45 deg *below* the -X axis?
# If the connector goes to the lobe (which is further left, towards the center), the connector must go Left and Down.
# So the tangent at the exit is indeed pointing South-West.
# Angle from -X (West) downwards is 45 deg.
# So the tangent angle is 180 + 45 = 225 degrees.
# The arc of the fillet rotates from 0 deg (East) to 225 deg?
# That's a reflex angle. The fillet is on the "inside" of the corner.
# The corner is "convex" relative to the outside, but "concave" for the material?
# Wait, the leg is straight. The connector is sloped. The fillet rounds the corner.
# The material is "outside" the corner? No, the clip is the material.
# The corner is the corner of the metal strip.
# Leg: Top edge. Connector: Inner edge?
# No, "straight connector joins each fillet endpoint to its retention lobe".
# The fillet is at the "Tip".
# So we have the Outer Leg, then the Fillet, then the Connector.
# The Outer Leg is the top surface.
# The Connector connects the *bottom* of the fillet to the lobe?
# Or does the fillet connect the outer leg to the connector which is on the *inner* side?
# "tangent to its outer leg".
# So the fillet is tangent to the Outer Leg.
# The other side of the fillet is tangent to the Connector.
# The Connector goes to the Retention Lobe.
# The Retention Lobe is "inside" the clip (between the legs).
# So the Connector must go from the Tip area towards the Center.
# So the Connector goes Left and Down (for upper leg).
# Tangent at exit: 225 deg (South-West).
# Tangent at entry: 0 deg (East).
# The fillet arc must turn from East to South-West.
# This is a 225 degree turn? Or 135?
# If the material is continuous, the fillet rounds the "outer" corner of the U-shape?
# No, the U-shape is open. The tip is the end of the leg.
# The "Tip Fillet" is usually at the very end of the leg, rounding it off.
# But the text says "joins each fillet endpoint to its retention lobe".
# This implies the fillet is part of the path from the leg to the lobe.
# So the sequence is Leg -> Fillet -> Connector -> Lobe.
# The Leg is the top edge of the metal.
# The Connector is likely the *inner* edge of the metal strip?
# If so, the thickness of the metal is the distance between Leg and Connector?
# But we have a separate `clip_width` (2.20mm) which is likely the thickness.
# Let's assume the sketch is the Centerline of the strip, and we will use a specific profile?
# No, "The outer bridge is semicircular... straight outer legs extend...".
# This describes the *outer contour* of the clip.
# The "clip_width" is the thickness.
# So we need to construct the Outer Contour and the Inner Contour, then offset?
# OR, construct the outer path and the inner path separately.
# Given the complexity of the "Inner Connector" and "Inner Bridge", it is safer to draw the Outer Path and the Inner Path as two separate sketches or one complex sketch with two loops?
# Usually, for a spring clip, you define the Outer Boundary and the Inner Boundary (with a gap for the thickness) and then use a "Pocket" or "Pad" with a specific profile?
# Actually, the standard way in PartDesign for a strip of constant thickness is to sketch the *centerline* and use a pattern? No.
# The prompt says "producing exactly one solid body".
# If we sketch the outer perimeter and the inner perimeter, we can use a Pad to extrude the difference?
# Yes: Sketch = Outer Path - Inner Path.
# Outer Path: Outer Bridge -> Outer Leg -> Tip Fillet -> Outer Connector?
# Wait, "straight connector joins each fillet endpoint to its retention lobe".
# Does the connector belong to the outer surface or inner?
# "tangent to its outer leg".
# This implies the connector starts from the tip fillet.
# If the connector is on the inner side, it would be tangent to the inner leg?
# Let's assume the "Tip Fillet" is the rounded end of the leg.
# Then "Straight Connector" goes from the end of the fillet to the Lobe.
# Is this connector on the Outer surface or Inner surface?
# "The lobe radius and each inner-connector radius equal the inner bridge radius".
# This implies the inner geometry is defined by these radii.
# So the "Straight Connector" is likely on the *inner* surface?
# But it says "joins each fillet endpoint". The fillet endpoint is on the outer leg.
# Maybe the connector is the *inner* edge of the leg, and the fillet is only on the outer?
# "Each tip has tip_fillet_radius and is tangent to its outer leg."
# This suggests the fillet is at the tip of the outer leg.
# "A straight connector joins each fillet endpoint to its retention lobe."
# If the fillet is at the tip of the outer leg, the endpoint is on the outer surface.
# If the connector joins to the lobe, and the lobe is an inner feature...
# This is confusing. Let's look at the "Inner Bridge" description.
# "Each inner connector and the inner bridge are tangent to the same sloped inner wall at its opposite ends."
# This implies there is an "Inner Bridge" arc and an "Inner Connector".
# So we have:
# 1. Outer Bridge (Semicircle).
# 2. Outer Legs (Straight).
# 3. Tip Fillet (At the end of Outer Legs).
# 4. Inner Connector (Straight, connects to Lobe).
# 5. Retention Lobe (Arc).
# 6. Inner Bridge (Arc).
# Where do the fillet and connector meet?
# "Straight connector joins each fillet endpoint to its retention lobe".
# This implies the sequence: Outer Leg -> Fillet -> Connector -> Lobe.
# But the Fillet is tangent to the Outer Leg.
# Is the Connector tangent to the Fillet? Yes, by definition of a smooth transition.
# So the Connector starts at the end of the Fillet.
