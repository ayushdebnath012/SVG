import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration and Parameters ---
# Define parameters directly to ensure exact values for the task
params = {
    "tapered_clevis_pin_length": 103.88,
    "tapered_clevis_pin_outer_diameter": 23.88,
    "tapered_clevis_pin_inner_diameter": 7.12,
    "tapered_clevis_pin_end_diameter": 12.7,
    "tapered_clevis_pin_taper_length": 15.35,
    "outer_fork_cutouts_radius": 12.7,
    "outer_fork_cutouts_width": 59.7,
    "outer_fork_cutouts_spacing": 7.88,
    "outer_fork_cutouts_arc_angle": 70.0, # degrees
    "outer_fork_cutouts_center_x_offset": 8.35,
    "outer_fork_cutouts_center_y_offset": -5.8,
    "central_fork_slot_length": 76.45,
    "central_fork_slot_width": 13.2,
    "central_fork_slot_center_x_offset": 13.73
}

# Calculate derived values
L_total = params["tapered_clevis_pin_length"]
D_outer = params["tapered_clevis_pin_outer_diameter"]
D_inner = params["tapered_clevis_pin_inner_diameter"]
D_end = params["tapered_clevis_pin_end_diameter"]
T_taper = params["tapered_clevis_pin_taper_length"]

# Fork Cutout Geometry
# The cutouts are defined relative to the pin center (0,0).
# Symmetric about outer_fork_cutouts_center_y_offset (which is negative, so below X axis).
# Wait, description says: "centers are symmetric about outer_fork_cutouts_center_y_offset".
# Usually in CAD "symmetric about Y" means the Y coordinate is the axis of symmetry.
# Here, the Y offset is -5.8. This likely means the center of the fork assembly is at Y=-5.8?
# Or the two cutouts are centered at Y = -5.8 and Y = +5.8?
# "two identical opposed openings... symmetric about outer_fork_cutouts_center_y_offset".
# If the offset is -5.8, and they are symmetric about it, then one is at -5.8 - delta and one is at -5.8 + delta.
# BUT, the text also says "The lower opening is the mirror of the upper opening".
# And "centers are symmetric about outer_fork_cutouts_center_y_offset".
# If the symmetry axis is Y = -5.8, then the centers are at Y_c and Y_c - 2*dist.
# Let's re-read carefully: "centers are symmetric about outer_fork_cutouts_center_y_offset".
# This implies the line Y = -5.8 is the axis of symmetry for the pair.
# So Center1_Y = -5.8 + d, Center2_Y = -5.8 - d.
# "clear transverse spacing of outer_fork_cutouts_spacing between the inward arc extrema".
# The inward direction for a Y-centered cutout on the Z-axis is towards Y=0 (if Y is transverse).
# Wait, the pin is along X. The cutouts are in the Z direction (through Z).
# So the cutout faces are roughly in the Y-Z plane? No, "openings through the pin in the Z direction".
# This means the holes go from +Z to -Z. The profile is in the X-Y plane.
# So the "transverse" direction is Y.
# "inward arc extrema": The arcs are at the ends. The straight part is in the middle.
# The "inward" side of the straight part is towards the center of the pin (Y=0)?
# Or is the fork shape like a 'U' or 'H'?
# "capsule-shaped slot... in the orthogonal Y direction". This is the central slot.
# The outer openings: "two equal circular end arcs... straight tangent joins the two arc extrema".
# This describes a shape like a rounded rectangle (capsule) but with arcs at the ends of the X-axis?
# No, "arcs of outer_fork_cutouts_radius".
# Let's construct the profile for one cutout in the X-Y plane.
# It passes completely from one outer tangent surface to the opposite.
# This implies the cutout is a hole through the diameter.
# Profile: Two arcs at the "ends" (longitudinally) and a straight part?
# "Each outer opening has two equal circular end arcs... centers separated longitudinally by outer_fork_cutouts_width".
# So the cutout has a length dimension along X.
# "centers are symmetric about outer_fork_cutouts_center_y_offset".
# Let's assume the "center" of the cutout's longitudinal axis is at Y = -5.8.
# And the two cutouts are symmetric about this line.
# So Cutout 1 Y_center = -5.8 + (spacing/2)?
# "clear transverse spacing of outer_fork_cutouts_spacing between the inward arc extrema".
# The "inward arc extrema" are the points on the arcs closest to the other cutout (or the center).
# If the shape is a hole, the "extrema" are the inner corners.
# Let's assume the standard interpretation:
# Two holes. Their centers are separated by some distance.
# The distance between the closest points of the holes is `outer_fork_cutouts_spacing`.
# The "inward arc extrema" are the points on the arcs that face each other.
# Since the arcs are at the ends of the cutout (longitudinally), the "extrema" are likely the inner endpoints of the arcs.
# Let's define the geometry of one cutout profile.
# It is a shape that removes material.
# It has a length `outer_fork_cutouts_width`.
# It has two circular arcs at the ends.
# The arcs have radius `outer_fork_cutouts_radius`.
# The angle of the arc is `outer_fork_cutouts_arc_angle`.
# "spans ... from its inward transverse direction".
# Inward transverse direction is -Y (if the hole is below) or +Y?
# If the hole is at Y = -5.8, inward is towards Y=0 (up). So angle is measured from -Y axis?
# Or from the vertical? "inward transverse direction" usually means the direction towards the center of the object.
# If the pin is centered at Y=0, and the cutout is at Y=-5.8, inward is +Y.
# So the arc starts at the straight line (which is perpendicular to the tangent?)
# Let's assume the cutout profile is a "stadium" shape (capsule) rotated or modified?
# "straight tangent joins the two arc extrema; an outer straight segment spans the shank taper-transition stations".
# This implies the profile is NOT a simple capsule.
# It has:
# 1. An arc at one end (Left).
# 2. An arc at the other end (Right).
# 3. A straight line connecting the arcs (Top/Inner side).
# 4. A straight line connecting the arcs (Bottom/Outer side)?
# "outer straight segment spans the shank taper-transition stations".
# This suggests the bottom part of the cutout follows the taper of the pin?
# No, the cutout is a hole. The "outer straight segment" might be the part of the cutout boundary that coincides with the pin's outer taper?
# Actually, if it's a hole, the boundary is the intersection of the hole profile and the pin profile.
# But we are defining the hole profile in a sketch.
# If the hole is "through the pin", the profile must be large enough to cut through.
# The description says: "passes completely from one outer tangent surface... to the opposite surface".
# So the profile must span the full width of the pin at that location.
# "outer straight segment spans the shank taper-transition stations".
# This implies the bottom boundary of the hole profile is a line that runs parallel to the pin's taper?
# Or is it a line that connects the two taper stations?
# Let's re-read: "straight tangent connectors close the profile".
# Okay, let's build the profile step-by-step.
# We need to define the vertices of the profile.
# Let's place the cutout at Y = Y_c.
# The cutout has length L_c = `outer_fork_cutouts_width`.
# The arcs are at the ends (X = X_start, X = X_end).
# The arcs have radius R = `outer_fork_cutouts_radius`.
# The arc angle is Alpha = `outer_fork_cutouts_arc_angle`.
# "spans ... from its inward transverse direction".
# If the hole is at Y = -5.8, inward is +Y.
# So the arc starts at the bottom (outer surface) and goes up?
# Or does the arc replace the corner?
# "two equal circular end arcs".
# Let's assume the profile consists of:
# - Top edge: A straight horizontal line? Or an arc?
# - Bottom edge: A straight line?
# The text says "straight tangent joins the two arc extrema".
# This implies the arcs are at the top and bottom? No, "end arcs" usually means along the length.
# So Left Arc and Right Arc.
# "inward arc extrema": The point on the Left Arc closest to the Right Arc? No, the cutout is a single hole.
# "inward arc extrema" of the hole? The points on the arcs closest to the center of the pin (Y=0)?
# If the hole is at Y=-5.8, the "inward" points are the top-most points of the arcs.
# "straight tangent joins the two arc extrema": A line connects the top of Left Arc to the top of Right Arc.
# "an outer straight segment spans the shank taper-transition stations".
# This implies the bottom of the hole is not a simple line, but relates to the taper.
# "straight tangent connectors close the profile".
# Maybe the bottom is composed of lines tangent to the pin's taper?
# Let's assume the hole is a "U" shape or similar that cuts into the side.
# But it says "passes completely".
# Let's try to interpret "outer straight segment spans the shank taper-transition stations".
# The pin tapers from D_outer to D_end.
# The "taper-transition stations" are the points where the taper starts and ends.
# Distance from center to taper start/end = T_taper.
# So at X = -T_taper and X = +T_taper, the diameter changes.
# The "outer straight segment" of the cutout profile might be a line segment that connects the points (X=-T_taper, Y=D_outer/2) and (X=+T_taper, Y=D_outer/2)?
# No, the cutout is at Y=-5.8.
# Maybe the cutout profile's bottom edge is a line that is tangent to the pin's taper curve?
# If the pin tapers, the "outer surface" is a cone.
# A line tangent to the cone at a specific angle?
# Let's assume the bottom of the cutout is a straight line connecting the two "taper stations" on the outer surface?
# No, the cutout is a hole. The profile is the shape of the hole.
# If the hole goes all the way through, the profile must be wider than the pin at the narrowest point.
# The "outer straight segment" might be the part of the profile that lies on the outer surface of the pin?
# This happens if the hole is cut such that its bottom edge is the pin's surface?
# That would mean the hole is open to the surface.
# Let's assume the profile is defined by:
# 1. Top Edge: Straight line connecting the "inward arc extrema".
#    Y_top = Y_center + R? Or Y_center + something?
#    If the arc spans from "inward transverse direction", and the arc is at the end...
#    Let's assume the arc is a quarter circle? No, angle is 70 deg.
#    Let's assume the arc starts at the straight line (top) and goes down to the bottom.
#    Or starts at the bottom (outer surface) and goes to the top.
#    "spans ... from its inward transverse direction".
#    If inward is +Y, and the span is 70 degrees.
#    Does it span from +Y to -Y? No, 70 deg is small.
#    Maybe it spans from the horizontal?
#    Let's assume the arc is at the corner.
#    Common fork shape: The ends are rounded.
#    Let's assume the profile is:
#    - Left Arc: Centered at (X_left, Y_center). Radius R. Angle 70 deg.
#    - Right Arc: Centered at (X_right, Y_center). Radius R. Angle 70 deg.
#    - Top Connector: Straight line connecting the two arcs.
#    - Bottom Connector: "outer straight segment spans the shank taper-transition stations".
#      This suggests the bottom line connects the points where the taper starts/ends on the outer surface?
#      But the cutout is a hole. If the bottom line is on the outer surface, the hole is open.
#      "passes completely".
#      Maybe the bottom line is a line that is tangent to the pin's taper?
#      Let's calculate the geometry.
#      The pin has a taper from D_outer to D_end over length 2*T_taper.
#      The taper slope m = (D_outer - D_end) / (2 * T_taper).
#      The line equation of the outer surface near the cutout:
#      Y_surf(X) = sqrt((D_outer/2)^2 - ((X - X_offset)^2 + (Y - Y_center)^2 ... no).
#      Let's simplify. The pin is a cylinder with conical ends.
#      The "outer straight segment" of the cutout profile is likely a line segment that is tangent to the conical surface?
#      Or simply a line segment connecting the points (X_start_taper, Y_outer) and (X_end_taper, Y_outer)?
#      But the cutout is at Y = -5.8.
#      If the hole is "through", it must go through the full diameter.
#      If the bottom of the profile is the outer surface, then the hole is just a notch?
#      No, "passes completely".
#      Maybe the "outer straight segment" is the top edge?
#      "an outer straight segment spans the shank taper-transition stations".
#      "straight tangent joins the two arc extrema".
#      This implies:
#      - Arc 1 (End)
#      - Arc 2 (End)
#      - Top Line (Joins arc extrema)
#      - Bottom Line (Spans taper stations)
#      If the Bottom Line spans the taper stations, it is at Y = D_outer/2 (at the taper stations)?
#      But the cutout is at Y = -5.8.
#      If D_outer = 23.88, then D_outer/2 = 11.94.
#      If Y_center = -5.8, and R = 12.7.
#      The arc can reach down to -5.8 - 12.7 = -18.5.
#      The pin radius is 11.94.
#      So the arc extends beyond the pin surface?
#      The sketch is in the X-Y plane. The hole is cut from the solid.
#      If the profile extends beyond the pin, the hole will cut into the solid.
#      "outer straight segment spans the shank taper-transition stations".
#      This implies the bottom of the cutout profile is a line segment that connects the points where the taper begins and ends on the OUTSIDE of the pin?
#      This would mean the cutout profile is very large, encompassing the entire pin width at those points?
#      If so, the hole is a full diameter cutout.
#      Let's assume the bottom edge of the profile is the line Y = -D_outer/2 (at the taper stations)?
#      No, the cutout is at Y=-5.8.
#      Let's assume the "outer straight segment" is the part of the profile that lies on the outer surface of the pin?
#      This is confusing. Let's try a different interpretation.
#      Maybe the "fork" is a U-shape attached to the pin?
#      No, "openings through the pin".
#      Okay, let's look at the "clear transverse spacing".
#      Spacing = 7.88.
#      Centers are symmetric about Y = -5.8.
#      So Center1_Y = -5.8 + d, Center2_Y = -5.8 - d.
#      Distance between inward extrema = 7.88.
#      Inward extrema are the points on the arcs closest to the center (Y=0).
#      If the arc is 70 deg, and starts from "inward transverse direction" (towards Y=0).
#      Then the arc starts at the top (closest to Y=0) and goes down?
#      If the arc starts at the top, then the "inward extrema" are the start points.
#      Distance between start points = 7.88.
#      So Center1_Y_start = -5.8 + d. Center2_Y_start = -5.8 - d.
#      Distance = 2d = 7.88 => d = 3.94.
#      So Center1_Y = -5.8 + 3.94 = -1.86.
#      Center2_Y = -
