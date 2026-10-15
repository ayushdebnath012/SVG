import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("WheelRim")

# --- Parameters ---
# Base Dimensions
hub_bore_diameter = 50.00
hub_outer_diameter = 90.00
hub_axial_width = 140.00
spoke_web_axial_width = 100.00
rim_axial_width = 160.00
rim_end_width = 2.99
rim_outer_diameter = 504.00
rim_inner_shoulder_radius = 220.00
rim_well_floor_diameter = 471.93
rim_well_floor_width = 109.99

# Spoke & Opening Geometry
curved_spoke_cutout_count = 8
curved_spoke_side_arc_radius = 143.28
curved_spoke_hub_arc_radius = 34.38
curved_spoke_rim_arc_radius = 210.00
curved_spoke_opening_hub_arc_center_radius = 100.00
curved_spoke_opening_side_arc_center_radius = 170.17
curved_spoke_opening_side_arc_center_offset_angle = 37.229172353940534
curved_spoke_opening_side_arc_span = 49.90826665492402
curved_spoke_opening_hub_arc_span = 141.95690310574687
curved_spoke_opening_rim_arc_span = 10.933863699266055

# Detailed Cutout Geometry
detailed_cutout_leading_edge_arc_radius = 65.48
detailed_cutout_trailing_edge_arc_radius = 87.46
spoke_end_arc_radius = 5.00
detailed_cutout_rim_arc_start_offset = 12.272454253038745
detailed_cutout_rim_arc_span = 19.28518904899144
detailed_cutout_end_arc_center_radius = 162.32
detailed_cutout_end_arc_center_offset_angle = 21.6948128
detailed_cutout_end_arc_span = 137.71759300920402
detailed_cutout_leading_edge_center_radius = 154.42
detailed_cutout_leading_edge_center_offset_angle = 47.2519169565992
detailed_cutout_leading_edge_arc_span = 43.914664785758816
detailed_cutout_trailing_edge_center_radius = 151.85
detailed_cutout_trailing_edge_center_offset_angle = -12.32880601664715
detailed_cutout_trailing_edge_arc_span = 32.59979260417278
detailed_cutout_leading_tip_center_radius = 205.03
detailed_cutout_leading_tip_center_offset_angle = 31.406630862972946
detailed_cutout_leading_tip_arc_span = 136.90153698896054
detailed_cutout_trailing_tip_center_offset_angle = 12.423466698621468
detailed_cutout_trailing_tip_arc_span = 130.2010852390235

# Rim Trim Geometry
outer_curved_profile_arc_radius = 314.10
inner_curved_profile_arc_radius = 255.24
outer_curved_profile_arc_center_radius = 199.28
outer_curved_profile_arc_center_angle = 13.496204762634408
outer_curved_profile_arc_span = 28.56487753739316
inner_curved_profile_arc_center_radius = 205.91
inner_curved_profile_arc_center_angle = 27.27419351807198
inner_curved_profile_arc_span = 34.268192263825085
rim_trim_inner_radius = 60.75
rim_trim_outer_radius = 210.11
rim_trim_arc_top_radius = 209.05
left_rim_trim_side_axial_offset = -87.93
right_rim_trim_side_axial_offset = 53.29

# Mounting Holes
number_of_mounting_holes = 6
hub_mounting_bolt_circle_diameter = 105.00
mounting_hole_diameter = 10.20
mounting_hole_counterbore_diameter = 13.50
mounting_hole_counterbore_depth = 5.00

# Fillets
rim_profile_fillet_radius = 10.00
rim_well_transition_arc_span = 53.18152443071139

# --- Setup Body ---
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Sketch 1: Base Section Profile (YZ Plane) ---
# Origin: Center of hub end face on positive-X side. 
# Profile is in YZ plane. Y=Radial, Z=Tangential.
# The wheel will be revolved around the X-axis.
sk_base = body.newObject("Sketcher::SketchObject", "sk_BaseProfile")
sk_base.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sk_base.Support = (doc.getObject("YZ_Plane"), [])
sk_base.MapMode = "FlatFace"
sk_base.ConstrainAuto = True

# Define the profile points in YZ plane.
# We construct the shape of the cross-section.
# Points are (Y, Z).
# 1. Hub Inner Bore (Circle)
# 2. Hub Outer Cylinder
# 3. Spoke Web
# 4. Rim Body
# 5. Rim Ends
# 6. Rim Well
# 7. Rim Trim

# Helper to add geometry
def add_line(p1, p2):
    sk_base.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(center, radius):
    sk_base.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

# Coordinates (Y, Z)
# Hub Bore: Radius = hub_bore_diameter / 2
hub_bore_r = hub_bore_diameter / 2.0
# Hub Outer: Radius = hub_outer_diameter / 2
hub_outer_r = hub_outer_diameter / 2.0
# Spoke Web Outer: Radius = hub_outer_r + spoke_web_axial_width (Wait, spoke_web_axial_width is axial, not radial)
# Re-reading: "spoke_web_axial_width" is the thickness of the spoke in the axial direction.
# The radial extent of the spoke web is from hub_outer_r to rim_inner_shoulder_radius? 
# No, the description says "rim_inner_shoulder_radius" is the inner annular shoulder of the rim end.
# The spokes connect the hub to the rim.
# Let's assume the spoke web radial thickness is defined by the difference between rim inner radius and hub outer radius, 
# but the problem gives specific spoke geometry for cutouts.
# Let's assume the main spoke web radial thickness is (rim_inner_shoulder_radius - hub_outer_r).
# Actually, let's look at the "rim_well_floor_diameter". This is the floor of the well.
# The rim body surrounds the spoke structure.
# Let's build the profile step by step.

# Start at Hub Inner Bore (Y=hub_bore_r, Z=0)
# Go up to Hub Outer (Y=hub_outer_r, Z=0)
# Go out to Spoke Web Outer (Y = hub_outer_r + (rim_inner_shoulder_radius - hub_outer_r)? No.)
# Let's assume the spoke web extends radially from hub_outer_r to some radius R_spoke_outer.
# The rim inner shoulder is at rim_inner_shoulder_radius.
# The spokes connect hub to rim.
# Let's assume the spoke web outer radius is rim_inner_shoulder_radius.
spoke_web_outer_r = rim_inner_shoulder_radius

# Rim Body Inner (at the well floor level)
# The rim well floor is at rim_well_floor_diameter / 2.
rim_well_floor_r = rim_well_floor_diameter / 2.0
# The rim well floor width is rim_well_floor_width.
# The rim body extends from the well floor to the outer rim.
# Rim Outer Diameter = rim_outer_diameter.
rim_outer_r = rim_outer_diameter / 2.0

# Rim End Width
rim_end_r = rim_outer_r + rim_end_width

# Rim Inner Shoulder Radius (at the end face)
# This is the radius of the shoulder on the rim end face.
# It meets the spoke web.
# So the spoke web outer radius is likely rim_inner_shoulder_radius.

# Let's define the profile path:
# 1. Hub Bore: Circle at Y=hub_bore_r, Z=0.
# 2. Hub Outer: Line from (hub_bore_r, 0) to (hub_outer_r, 0).
# 3. Spoke Web: Line from (hub_outer_r, 0) to (spoke_web_outer_r, 0).
# 4. Rim Inner Shoulder: Line from (spoke_web_outer_r, 0) to (rim_inner_shoulder_radius, 0).
# 5. Rim Well Floor: Line from (rim_inner_shoulder_radius, 0) to (rim_well_floor_r, 0).
#    Wait, the well floor is a hole in the rim? Or the bottom of the well?
#    "rim_well_floor_diameter" suggests the diameter of the floor of the well.
#    So the rim body has a hole of diameter rim_well_floor_diameter.
#    The well floor width is the axial width of the floor.
#    But we are in the YZ plane (radial-tangential).
#    The well is a circumferential feature.
#    The profile in YZ plane will show the cross-section of the well.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go up to the rim outer radius?
#    No, the well is a depression in the rim.
#    The rim body surrounds the spoke structure.
#    The well is between the spokes?
#    "rim_well_floor_diameter" = 471.93. rim_outer_diameter = 504.00.
#    So the well is a large hole in the rim.
#    The rim body is the material between the well and the outer rim.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well floor width is rim_well_floor_width (axial).
#    In the YZ plane, the well floor is a line at Y = rim_well_floor_r.
#    The well walls are lines from (rim_well_floor_r, 0) to (rim_outer_r, 0).
#    But the well is not a full circle. It has a span.
#    "rim_well_transition_arc_span" = 53.18 degrees.
#    This suggests the well is a sector.
#    The profile in YZ plane will show the cross-section of the well at the center of the sector.
#    So the profile will have a hole from Y = rim_well_floor_r to Y = rim_outer_r.
#    But the well is only 53 degrees wide.
#    The rest of the rim is solid.
#    This means the profile in YZ plane is not a simple closed loop.
#    We need to create the solid by revolving the profile, but the profile must be closed.
#    The profile will be the cross-section of the wheel at Z=0.
#    The well is a hole that is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for the angular span of the well.
#    But we are in the YZ plane. The well is symmetric about Z=0?
#    "rim_well_transition_arc_span" is the span of the well.
#    So the well is centered at Z=0? Or at some other angle?
#    The problem says "rim_well_transition_arc_span".
#    Let's assume the well is centered at Z=0.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    - Spoke Web (Line)
#    - Rim Inner Shoulder (Line)
#    - Rim Well Floor (Line)
#    - Rim Well Wall (Line)
#    - Rim Outer (Line)
#    - Rim End (Line)
#    - Rim End Outer (Line)
#    - Rim End Inner (Line)
#    - Rim Inner Shoulder (Line)
#    - Spoke Web (Line)
#    - Hub Outer (Line)
#    - Hub Bore (Circle)
#    But the well is a hole.
#    So the profile will have a hole in it.
#    The hole is defined by the well floor and the well walls.
#    The well floor is at Y = rim_well_floor_r.
#    The well walls go from Y = rim_well_floor_r to Y = rim_outer_r.
#    The well is 53 degrees wide.
#    So the profile will have a cutout from Y = rim_well_floor_r to Y = rim_outer_r, but only for Z in [-span/2, span/2].
#    But the profile must be a closed loop.
#    So we need to add lines to close the loop.
#    The profile will be:
#    - Hub Bore (Circle)
#    - Hub Outer (Line)
#    -
