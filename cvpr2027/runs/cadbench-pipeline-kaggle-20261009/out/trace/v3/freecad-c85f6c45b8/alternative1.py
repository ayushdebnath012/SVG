import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("WheelRim")

# --- Parameters ---
# Define a named object for parameters to keep them editable and organized
params = doc.addObject("App::ParameterObject", "Parameters")
params.addProperty("App::PropertyLength", "rim_profile_fillet_radius", "Dimensions", "rim_profile_fillet_radius")
params.rim_profile_fillet_radius = 10.00
params.addProperty("App::PropertyLength", "rim_well_transition_arc_span", "Dimensions", "rim_well_transition_arc_span")
params.rim_well_transition_arc_span = 53.18152443071139
params.addProperty("App::PropertyLength", "hub_bore_diameter", "Dimensions", "hub_bore_diameter")
params.hub_bore_diameter = 50.00
params.addProperty("App::PropertyLength", "hub_outer_diameter", "Dimensions", "hub_outer_diameter")
params.hub_outer_diameter = 90.00
params.addProperty("App::PropertyLength", "hub_axial_width", "Dimensions", "hub_axial_width")
params.hub_axial_width = 140.00
params.addProperty("App::PropertyLength", "spoke_web_axial_width", "Dimensions", "spoke_web_axial_width")
params.spoke_web_axial_width = 100.00
params.addProperty("App::PropertyLength", "rim_axial_width", "Dimensions", "rim_axial_width")
params.rim_axial_width = 160.00
params.addProperty("App::PropertyLength", "rim_end_width", "Dimensions", "rim_end_width")
params.rim_end_width = 2.99
params.addProperty("App::PropertyLength", "rim_outer_diameter", "Dimensions", "rim_outer_diameter")
params.rim_outer_diameter = 504.00
params.addProperty("App::PropertyLength", "rim_inner_shoulder_radius", "Dimensions", "rim_inner_shoulder_radius")
params.rim_inner_shoulder_radius = 220.00
params.addProperty("App::PropertyLength", "rim_well_floor_diameter", "Dimensions", "rim_well_floor_diameter")
params.rim_well_floor_diameter = 471.93
params.addProperty("App::PropertyLength", "rim_well_floor_width", "Dimensions", "rim_well_floor_width")
params.rim_well_floor_width = 109.99
params.addProperty("App::PropertyInteger", "curved_spoke_cutout_count", "Dimensions", "curved_spoke_cutout_count")
params.curved_spoke_cutout_count = 8
params.addProperty("App::PropertyLength", "curved_spoke_side_arc_radius", "Dimensions", "curved_spoke_side_arc_radius")
params.curved_spoke_side_arc_radius = 143.28
params.addProperty("App::PropertyLength", "curved_spoke_hub_arc_radius", "Dimensions", "curved_spoke_hub_arc_radius")
params.curved_spoke_hub_arc_radius = 34.38
params.addProperty("App::PropertyLength", "curved_spoke_rim_arc_radius", "Dimensions", "curved_spoke_rim_arc_radius")
params.curved_spoke_rim_arc_radius = 210.00
params.addProperty("App::PropertyLength", "curved_spoke_opening_hub_arc_center_radius", "Dimensions", "curved_spoke_opening_hub_arc_center_radius")
params.curved_spoke_opening_hub_arc_center_radius = 100.00
params.addProperty("App::PropertyLength", "curved_spoke_opening_side_arc_center_radius", "Dimensions", "curved_spoke_opening_side_arc_center_radius")
params.curved_spoke_opening_side_arc_center_radius = 170.17
params.addProperty("App::PropertyAngle", "curved_spoke_opening_side_arc_center_offset_angle", "Dimensions", "curved_spoke_opening_side_arc_center_offset_angle")
params.curved_spoke_opening_side_arc_center_offset_angle = 37.229172353940534
params.addProperty("App::PropertyAngle", "curved_spoke_opening_side_arc_span", "Dimensions", "curved_spoke_opening_side_arc_span")
params.curved_spoke_opening_side_arc_span = 49.90826665492402
params.addProperty("App::PropertyAngle", "curved_spoke_opening_hub_arc_span", "Dimensions", "curved_spoke_opening_hub_arc_span")
params.curved_spoke_opening_hub_arc_span = 141.95690310574687
params.addProperty("App::PropertyAngle", "curved_spoke_opening_rim_arc_span", "Dimensions", "curved_spoke_opening_rim_arc_span")
params.curved_spoke_opening_rim_arc_span = 10.933863699266055
params.addProperty("App::PropertyLength", "detailed_cutout_leading_edge_arc_radius", "Dimensions", "detailed_cutout_leading_edge_arc_radius")
params.detailed_cutout_leading_edge_arc_radius = 65.48
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_edge_arc_radius", "Dimensions", "detailed_cutout_trailing_edge_arc_radius")
params.detailed_cutout_trailing_edge_arc_radius = 87.46
params.addProperty("App::PropertyLength", "spoke_end_arc_radius", "Dimensions", "spoke_end_arc_radius")
params.spoke_end_arc_radius = 5.00
params.addProperty("App::PropertyAngle", "detailed_cutout_rim_arc_start_offset", "Dimensions", "detailed_cutout_rim_arc_start_offset")
params.detailed_cutout_rim_arc_start_offset = 12.272454253038745
params.addProperty("App::PropertyAngle", "detailed_cutout_rim_arc_span", "Dimensions", "detailed_cutout_rim_arc_span")
params.detailed_cutout_rim_arc_span = 19.28518904899144
params.addProperty("App::PropertyLength", "detailed_cutout_end_arc_center_radius", "Dimensions", "detailed_cutout_end_arc_center_radius")
params.detailed_cutout_end_arc_center_radius = 162.32
params.addProperty("App::PropertyAngle", "detailed_cutout_end_arc_center_offset_angle", "Dimensions", "detailed_cutout_end_arc_center_offset_angle")
params.detailed_cutout_end_arc_center_offset_angle = 21.6948128
params.addProperty("App::PropertyAngle", "detailed_cutout_end_arc_span", "Dimensions", "detailed_cutout_end_arc_span")
params.detailed_cutout_end_arc_span = 137.71759300920402
params.addProperty("App::PropertyLength", "detailed_cutout_leading_edge_center_radius", "Dimensions", "detailed_cutout_leading_edge_center_radius")
params.detailed_cutout_leading_edge_center_radius = 154.42
params.addProperty("App::PropertyAngle", "detailed_cutout_leading_edge_center_offset_angle", "Dimensions", "detailed_cutout_leading_edge_center_offset_angle")
params.detailed_cutout_leading_edge_center_offset_angle = 47.2519169565992
params.addProperty("App::PropertyAngle", "detailed_cutout_leading_edge_arc_span", "Dimensions", "detailed_cutout_leading_edge_arc_span")
params.detailed_cutout_leading_edge_arc_span = 43.914664785758816
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_edge_center_radius", "Dimensions", "detailed_cutout_trailing_edge_center_radius")
params.detailed_cutout_trailing_edge_center_radius = 151.85
params.addProperty("App::PropertyAngle", "detailed_cutout_trailing_edge_center_offset_angle", "Dimensions", "detailed_cutout_trailing_edge_center_offset_angle")
params.detailed_cutout_trailing_edge_center_offset_angle = -12.32880601664715
params.addProperty("App::PropertyAngle", "detailed_cutout_trailing_edge_arc_span", "Dimensions", "detailed_cutout_trailing_edge_arc_span")
params.detailed_cutout_trailing_edge_arc_span = 32.59979260417278
params.addProperty("App::PropertyLength", "detailed_cutout_leading_tip_center_radius", "Dimensions", "detailed_cutout_leading_tip_center_radius")
params.detailed_cutout_leading_tip_center_radius = 205.03
params.addProperty("App::PropertyAngle", "detailed_cutout_leading_tip_center_offset_angle", "Dimensions", "detailed_cutout_leading_tip_center_offset_angle")
params.detailed_cutout_leading_tip_center_offset_angle = 31.406630862972946
params.addProperty("App::PropertyAngle", "detailed_cutout_leading_tip_arc_span", "Dimensions", "detailed_cutout_leading_tip_arc_span")
params.detailed_cutout_leading_tip_arc_span = 136.90153698896054
params.addProperty("App::PropertyAngle", "detailed_cutout_trailing_tip_center_offset_angle", "Dimensions", "detailed_cutout_trailing_tip_center_offset_angle")
params.detailed_cutout_trailing_tip_center_offset_angle = 12.423466698621468
params.addProperty("App::PropertyAngle", "detailed_cutout_trailing_tip_arc_span", "Dimensions", "detailed_cutout_trailing_tip_arc_span")
params.detailed_cutout_trailing_tip_arc_span = 130.2010852390235
params.addProperty("App::PropertyLength", "outer_curved_profile_arc_radius", "Dimensions", "outer_curved_profile_arc_radius")
params.outer_curved_profile_arc_radius = 314.10
params.addProperty("App::PropertyLength", "inner_curved_profile_arc_radius", "Dimensions", "inner_curved_profile_arc_radius")
params.inner_curved_profile_arc_radius = 255.24
params.addProperty("App::PropertyLength", "outer_curved_profile_arc_center_radius", "Dimensions", "outer_curved_profile_arc_center_radius")
params.outer_curved_profile_arc_center_radius = 199.28
params.addProperty("App::PropertyAngle", "outer_curved_profile_arc_center_angle", "Dimensions", "outer_curved_profile_arc_center_angle")
params.outer_curved_profile_arc_center_angle = 13.496204762634408
params.addProperty("App::PropertyAngle", "outer_curved_profile_arc_span", "Dimensions", "outer_curved_profile_arc_span")
params.outer_curved_profile_arc_span = 28.56487753739316
params.addProperty("App::PropertyLength", "inner_curved_profile_arc_center_radius", "Dimensions", "inner_curved_profile_arc_center_radius")
params.inner_curved_profile_arc_center_radius = 205.91
params.addProperty("App::PropertyAngle", "inner_curved_profile_arc_center_angle", "Dimensions", "inner_curved_profile_arc_center_angle")
params.inner_curved_profile_arc_center_angle = 27.27419351807198
params.addProperty("App::PropertyAngle", "inner_curved_profile_arc_span", "Dimensions", "inner_curved_profile_arc_span")
params.inner_curved_profile_arc_span = 34.268192263825085
params.addProperty("App::PropertyLength", "rim_trim_inner_radius", "Dimensions", "rim_trim_inner_radius")
params.rim_trim_inner_radius = 60.75
params.addProperty("App::PropertyLength", "rim_trim_outer_radius", "Dimensions", "rim_trim_outer_radius")
params.rim_trim_outer_radius = 210.11
params.addProperty("App::PropertyLength", "rim_trim_arc_top_radius", "Dimensions", "rim_trim_arc_top_radius")
params.rim_trim_arc_top_radius = 209.05
params.addProperty("App::PropertyLength", "left_rim_trim_side_axial_offset", "Dimensions", "left_rim_trim_side_axial_offset")
params.left_rim_trim_side_axial_offset = -87.93
params.addProperty("App::PropertyLength", "right_rim_trim_side_axial_offset", "Dimensions", "right_rim_trim_side_axial_offset")
params.right_rim_trim_side_axial_offset = 53.29
params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "number_of_mounting_holes")
params.number_of_mounting_holes = 6
params.addProperty("App::PropertyLength", "hub_mounting_bolt_circle_diameter", "Dimensions", "hub_mounting_bolt_circle_diameter")
params.hub_mounting_bolt_circle_diameter = 105.00
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "mounting_hole_diameter")
params.mounting_hole_diameter = 10.20
params.addProperty("App::PropertyLength", "mounting_hole_counterbore_diameter", "Dimensions", "mounting_hole_counterbore_diameter")
params.mounting_hole_counterbore_diameter = 13.50
params.addProperty("App::PropertyLength", "mounting_hole_counterbore_depth", "Dimensions", "mounting_hole_counterbore_depth")
params.mounting_hole_counterbore_depth = 5.00

doc.recompute()

# --- Setup PartDesign Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# --- Base Section: Hub and Rim Well ---
# Coordinates: Origin at center of hub end face (negative X side). Hub extends to -X.
# Rim end face is at X = hub_axial_width/2. Rim well floor starts at X = hub_axial_width/2 - rim_well_floor_width.
# However, the description says "Place the global origin at the center of the hub end face on the positive-X side".
# This implies the face at X = +hub_axial_width/2 is the reference? No, "center of the hub end face".
# Let's assume the Hub Center Face is at X=0. The hub extends from X=0 to X=-hub_axial_width.
# The rim well floor is at X = -hub_axial_width + rim_well_floor_width?
# Actually, the description says "The base section has ... hub_axial_width, spoke_web_axial_width, rim_axial_width".
# And "The two matching rim-end flats each have rim_end_width".
# Let's build from the center of the Hub (X=0).
# Hub Face 1: X = -hub_axial_width/2. Hub Face 2: X = +hub_axial_width/2.
# Spoke Web: X = -hub_axial_width/2 to X = -hub_axial_width/2 + spoke_web_axial_width.
# Rim Well: X = -hub_axial_width/2 + spoke_web_axial_width to X = -hub_axial_width/2 + spoke_web_axial_width + rim_well_floor_width.
# Rim Ends: X = -hub_axial_width/2 + spoke_web_axial_width + rim_well_floor_width to X = -hub_axial_width/2 + spoke_web_axial_width + rim_well_floor_width + rim_end_width (Wait, this logic is getting complex).

# Let's simplify the coordinate system based on "Origin at the center of the hub end face on the positive-X side".
# So, Face at X = +Hub_Axial_Width / 2 is the Origin Face (X=0)? 
# Or is the Origin Face at X=0, and the Hub extends to -Hub_Axial_Width?
# "Place the global origin at the center of the hub end face on the positive-X side". 
# This phrasing is ambiguous. It likely means: The face at the "positive X side" of the hub is the origin.
# If the hub is centered at X=0, the "positive X side" face is at X = +Hub_Axial_Width/2.
# So the origin is at X = +Hub_Axial_Width/2.
# The hub extends from X=0 to X=Hub_Axial_Width? No, "hub extending from this face in the negative-X direction".
# So: Origin = Face 1 (Positive X side of hub). Hub body is at X < 0.
# Hub Inner Face (Negative X side): X = -Hub_Axial_Width.
# Spoke Web: Starts at Hub Inner Face (X = -Hub_Axial_Width), goes +X for Spoke_Web_Width.
# Rim Well: Starts after Spoke Web.
# Rim Ends: On both sides of the Well.

# Let's refine the "Origin" definition.
# "Place the global origin at the center of the hub end face on the positive-X side".
# This implies the face located at the positive X end of the hub is at X=0.
# So the hub is between X = -Hub_Width and X = 0.
# The "hub extending from this face in the negative-X direction" confirms the hub is at X < 0.
# So:
# Hub Inner Face (Negative X side): X = -Hub_Axial_Width.
# Spoke Web: X from -Hub_Axial_Width to (-Hub_Axial_Width + Spoke_Web_Width).
# Rim Well: X from (-Hub_Axial_Width + Spoke_Web_Width) to ...
# Wait, "The base section has ... rim_well_floor_diameter ... and rim_well_floor_width".
# Usually, the well is between the spokes and the rim.
# Let's assume the order from Hub (X=-Hub_W) towards Rim (X=0 is hub face, so rim
