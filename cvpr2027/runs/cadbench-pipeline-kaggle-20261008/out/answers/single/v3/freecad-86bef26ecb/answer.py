import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Flywheel")

# --- Parameters ---
# Define parameters as App::PropertyLength or similar in a VarSet or directly on the Body
# For simplicity and robustness in this script, we will define them as variables 
# and use expressions in features, or set them on the Body if supported.
# Since PartDesign::Body doesn't natively hold a "Parameters" object in the same way 
# as a generic App::VarSet in older versions without specific setup, we will use 
# App::PropertyLength on the Body if possible, or just hardcode values in expressions 
# if the Body doesn't support the VarSet pattern easily in headless 1.1.
# However, the prompt asks for named document objects driving geometry.
# We will create a "Parameters" object of type App::VarSet.

params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "hub_end_profile_arc_radius", "Dimensions", "hub_end_profile_arc_radius")
params.hub_end_profile_arc_radius = 11.00
params.addProperty("App::PropertyLength", "hub_arc_center_axial_offset", "Dimensions", "hub_arc_center_axial_offset")
params.hub_arc_center_axial_offset = 9.00
params.addProperty("App::PropertyLength", "hub_end_profile_arc_central_angle", "Dimensions", "hub_end_profile_arc_central_angle")
params.hub_end_profile_arc_central_angle = 90.0
params.addProperty("App::PropertyLength", "wheel_circular_angle", "Dimensions", "wheel_circular_angle")
params.wheel_circular_angle = 360.0
params.addProperty("App::PropertyLength", "rim_outer_radius", "Dimensions", "rim_outer_radius")
params.rim_outer_radius = 100.00
params.addProperty("App::PropertyLength", "rim_outer_face_half_width", "Dimensions", "rim_outer_face_half_width")
params.rim_outer_face_half_width = 11.89
params.addProperty("App::PropertyLength", "rim_outer_chamfer_inner_radius", "Dimensions", "rim_outer_chamfer_inner_radius")
params.rim_outer_chamfer_inner_radius = 95.00
params.addProperty("App::PropertyLength", "rim_land_inner_radius", "Dimensions", "rim_land_inner_radius")
params.rim_land_inner_radius = 85.00
params.addProperty("App::PropertyLength", "rim_land_half_width", "Dimensions", "rim_land_half_width")
params.rim_land_half_width = 9.00
params.addProperty("App::PropertyLength", "rim_groove_1_outer_radius", "Dimensions", "rim_groove_1_outer_radius")
params.rim_groove_1_outer_radius = 80.00
params.addProperty("App::PropertyLength", "rim_groove_1_inner_radius", "Dimensions", "rim_groove_1_inner_radius")
params.rim_groove_1_inner_radius = 75.00
params.addProperty("App::PropertyLength", "rim_groove_1_half_width", "Dimensions", "rim_groove_1_half_width")
params.rim_groove_1_half_width = 6.11
params.addProperty("App::PropertyLength", "rim_groove_2_outer_radius", "Dimensions", "rim_groove_2_outer_radius")
params.rim_groove_2_outer_radius = 60.00
params.addProperty("App::PropertyLength", "rim_groove_2_outer_half_width", "Dimensions", "rim_groove_2_outer_half_width")
params.rim_groove_2_outer_half_width = 2.09
params.addProperty("App::PropertyLength", "rim_groove_2_inner_half_width", "Dimensions", "rim_groove_2_inner_half_width")
params.rim_groove_2_inner_half_width = 6.00
params.addProperty("App::PropertyLength", "rim_hub_land_radius", "Dimensions", "rim_hub_land_radius")
params.rim_hub_land_radius = 50.00
params.addProperty("App::PropertyLength", "hub_clearance_arc_radius", "Dimensions", "hub_clearance_arc_radius")
params.hub_clearance_arc_radius = 16.00
params.addProperty("App::PropertyLength", "rim_clearance_arc_radius", "Dimensions", "rim_clearance_arc_radius")
params.rim_clearance_arc_radius = 45.00
params.addProperty("App::PropertyLength", "spoke_cutout_corner_radius", "Dimensions", "spoke_cutout_corner_radius")
params.spoke_cutout_corner_radius = 5.00
params.addProperty("App::PropertyLength", "cutout_inner_upper_fillet_center_x", "Dimensions", "cutout_inner_upper_fillet_center_x")
params.cutout_inner_upper_fillet_center_x = 5.00
params.addProperty("App::PropertyLength", "cutout_inner_lower_fillet_center_x", "Dimensions", "cutout_inner_lower_fillet_center_x")
params.cutout_inner_lower_fillet_center_x = 9.28
params.addProperty("App::PropertyLength", "cutout_inner_lower_fillet_center_y", "Dimensions", "cutout_inner_lower_fillet_center_y")
params.cutout_inner_lower_fillet_center_y = 18.84
params.addProperty("App::PropertyLength", "cutout_outer_lower_fillet_center_x", "Dimensions", "cutout_outer_lower_fillet_center_x")
params.cutout_outer_lower_fillet_center_x = 21.68
params.addProperty("App::PropertyLength", "cutout_outer_lower_fillet_center_y", "Dimensions", "cutout_outer_lower_fillet_center_y")
params.cutout_outer_lower_fillet_center_y = 33.62
params.addProperty("App::PropertyLength", "cutout_outer_upper_fillet_center_x", "Dimensions", "cutout_outer_upper_fillet_center_x")
params.cutout_outer_upper_fillet_center_x = 5.00
params.addProperty("App::PropertyLength", "cutout_inclined_edge_inner_x", "Dimensions", "cutout_inclined_edge_inner_x")
params.cutout_inclined_edge_inner_x = 13.11
params.addProperty("App::PropertyLength", "cutout_inclined_edge_inner_y", "Dimensions", "cutout_inclined_edge_inner_y")
params.cutout_inclined_edge_inner_y = 15.62
params.addProperty("App::PropertyLength", "cutout_inclined_edge_outer_x", "Dimensions", "cutout_inclined_edge_outer_x")
params.cutout_inclined_edge_outer_x = 25.51
params.addProperty("App::PropertyLength", "cutout_inclined_edge_outer_y", "Dimensions", "cutout_inclined_edge_outer_y")
params.cutout_inclined_edge_outer_y = 30.40
params.addProperty("App::PropertyInteger", "spoke_count", "Dimensions", "spoke_count")
params.spoke_count = 7

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the main profile sketch (XY plane)
sketch_profile = body.newObject("Sketcher::SketchObject", "Profile_Sketch")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Support = [doc.getObject("XY_Plane")]
sketch_profile.MapMode = "FlatFace"

# Define the profile points based on the description.
# The description gives stations from outer rim to hub.
# We need to construct a closed loop.
# Let's list the (r, z) coordinates for the positive side (z > 0).
# Note: The description says "From the outer rim toward the hub".
# Stations:
# 1. (rim_outer_radius, rim_outer_face_half_width)
# 2. (rim_outer_chamfer_inner_radius, rim_land_half_width) -> Wait, description says "rim_outer_chamfer_inner_radius" is a radius, but the station is (radius, width). 
#    Actually, looking at the sequence: 
#    (rim_outer_radius, rim_outer_face_half_width) -> (rim_outer_chamfer_inner_radius, rim_land_half_width)
#    This implies a chamfer transition? Or just a step? 
#    "rim_outer_chamfer_inner_radius" is 95.00. "rim_outer_face_half_width" is 11.89.
#    "rim_land_half_width" is 9.00.
#    So at r=95, z=9.00. At r=100, z=11.89.
#    This looks like a chamfer or a fillet between them. The prompt doesn't explicitly say "fillet" here, but "chamfer_inner_radius" suggests a chamfer. 
#    However, later it mentions "rounded inter-spoke opening". 
#    Let's assume linear segments unless specified otherwise, or construct the points exactly as given.
#    The prompt lists "stations". Let's treat them as points.
#    But wait, "rim_outer_chamfer_inner_radius" is 95.00. "rim_outer_face_half_width" is 11.89.
#    "rim_land_inner_radius" is 85.00. "rim_land_half_width" is 9.00.
#    So we have points:
#    P1: (100, 11.89)
#    P2: (95, 9.00)  <-- This is a step down in Z and R.
#    P3: (85, 9.00)  <-- This is a step in R only.
#    P4: (80, 6.11)  <-- Groove 1 outer
#    P5: (75, 6.11)  <-- Groove 1 inner
#    P6: (60, 2.09)  <-- Groove 2 outer (half width)
#    P7: (60, 6.00)  <-- Groove 2 inner (half width) -> Wait, "rim_groove_2_inner_half_width" is 6.00.
#    P8: (50, 6.00)  <-- Hub land radius
#    P9: (50, 9.00)  <-- Hub land half width (same as rim_land_half_width? No, rim_land_half_width is 9.00. 
#                     The station says (rim_hub_land_radius, rim_land_half_width). So (50, 9.00).
#    Then the hub ends: "rounded hub ends are quarter arcs ... centered at equal positive and negative hub_arc_center_axial_offset".
#    Hub arc center is at z = 9.00 (hub_arc_center_axial_offset).
#    Radius is 11.00.
#    The arc connects the hub land (r=50, z=9.00) to the axial closure?
#    "tangent to the axial closure and hub-side land".
#    Axial closure is likely the plane z=0? Or the center of the wheel?
#    "Each rounded inter-spoke opening passes entirely from the outward-facing positive axial end face to the opposite negative axial end face."
#    This implies the wheel has thickness.
#    The profile sketch is on the XY plane (z=0).
#    The "positive axial end face" is at z = +thickness/2.
#    The "negative axial end face" is at z = -thickness/2.
#    The profile sketch defines the shape in the radial-axial plane.
#    Usually, the profile sketch is on the XZ plane (if rotating around Z) or XY plane (if rotating around Y).
#    The prompt says "radial-axial section symmetric about the central axial plane".
#    If we rotate around Z, the profile is in the XZ plane.
#    Let's assume the rotation axis is Z.
#    Then the sketch should be on the XZ plane.
#    The prompt says "sketch.AttachmentSupport = (doc.getObject("XY_Plane"), ...)". 
#    If we use XY plane, the sketch is in XY. Rotating around Z would make a disk.
#    But we need a flywheel with spokes.
#    Standard flywheel: Rotate around Z. Profile is in XZ plane.
#    Let's re-read: "sketch.AttachmentSupport = (doc.getObject("XY_Plane"), ...)". 
#    This is a generic example in the prompt. I should adapt.
#    If I want to rotate around Z, I need the XZ plane.
#    Let's create the sketch on the XZ plane.
#    Points (x, z):
#    x is radius. z is axial position.
#    P1: (100, 11.89)
#    P2: (95, 9.00)
#    P3: (85, 9.00)
#    P4: (80, 6.11)
#    P5: (75, 6.11)
#    P6: (60, 2.09)
#    P7: (60, 6.00)
#    P8: (50, 6.00)
#    P9: (50, 9.00)
#    Then the hub arc. Center at (0, 9.00). Radius 11.00.
#    It connects P9 (50, 9.00) to the axial closure.
#    "tangent to the axial closure". Axial closure is likely the center plane z=0?
#    If the center is at z=9, and radius is 11, the bottom of the arc is at z = 9 - 11 = -2.
#    The top is at z = 9 + 11 = 20.
#    But the hub land is at z=9.
#    The arc is a quarter arc.
#    If it's tangent to the axial closure (z=0 plane?), then the center must be at z=11?
#    Or the "axial closure" is the face of the hub?
#    "rounded hub ends are quarter arcs ... centered at equal positive and negative hub_arc_center_axial_offset".
#    Offset is 9.00. So centers are at z=9 and z=-9.
#    Radius 11.
#    Arc at z=9: From r=50 (hub land) to ... where?
#    "tangent to the axial closure". If the wheel is symmetric about z=0, the closure is z=0.
#    An arc centered at z=9 with radius 11 touches z=0 at x=0? No, distance from (0,9) to (0,0) is 9. Radius is 11.
#    Maybe the "axial closure" refers to the end of the hub land?
#    Let's assume the profile goes from the outer rim (x=100) down to the hub land (x=50, z=9), then curves inwards to the center axis (x=0) at some z.
#    If the arc is centered at (0, 9) with radius 11, it passes through (11, 9) and (0, 20) and (0, -2).
#    This doesn't seem to connect to the hub land at (50, 9).
#    Maybe the "hub_arc_center_axial_offset" is the distance from the center of the wheel to the center of the arc.
#    And the arc connects the hub land to the center of the wheel?
#    Let's reconsider the geometry.
#    Hub land radius = 50. Hub land half width = 9.00. So hub land is a cylinder r=50, z in [0, 18]? Or z in [9-9, 9+9]?
#    If the profile is symmetric about z=0, then the hub land is from z=-9 to z=9?
#    But the stations say "rim_land_half_width = 9.00". And "rim_hub_land_radius = 50.00".
#    Station: (rim_hub_land_radius, rim_land_half_width) -> (50, 9.00).
#    This suggests the hub land ends at z=9.00.
#    Then the arc starts at (50, 9.00).
#    Center of arc is at (0, 9.00)? No, that would be a circle centered on the axis.
#    If center is (0, 9), radius 11. Point (50, 9) is at distance 50. Radius is 11. Mismatch.
#    Maybe the center is at (50, 9)? No, "centered at equal positive and negative hub_arc_center_axial_offset".
#    This implies the center is on the axis (x=0).
#    So center is (0, 9). Radius must be 50 to reach the hub land?
#    But the parameter is "hub_end_profile_arc_radius = 11.00".
#    This is confusing.
#    Alternative interpretation: The "hub land" is the flat part. The "rounded hub end" is the transition from the hub land to the center.
#    Maybe the hub land is at z=9, and the arc connects (50, 9) to (0, 9-11) = (0, -2)?
#    If the arc is centered at (0, 9), radius 11.
#    It passes through (11, 9) and (0, 20) and (0, -2).
#    It does not pass through (50, 9).
#    Perhaps the "hub land" is not at r=50? "rim_hub_land_radius = 50.0
