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

# --- Setup Body and Parameters ---
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "hub_bore_diameter", "Dimensions", "hub_bore_diameter")
params.addProperty("App::PropertyLength", "hub_outer_diameter", "Dimensions", "hub_outer_diameter")
params.addProperty("App::PropertyLength", "hub_axial_width", "Dimensions", "hub_axial_width")
params.addProperty("App::PropertyLength", "spoke_web_axial_width", "Dimensions", "spoke_web_axial_width")
params.addProperty("App::PropertyLength", "rim_axial_width", "Dimensions", "rim_axial_width")
params.addProperty("App::PropertyLength", "rim_end_width", "Dimensions", "rim_end_width")
params.addProperty("App::PropertyLength", "rim_outer_diameter", "Dimensions", "rim_outer_diameter")
params.addProperty("App::PropertyLength", "rim_inner_shoulder_radius", "Dimensions", "rim_inner_shoulder_radius")
params.addProperty("App::PropertyLength", "rim_well_floor_diameter", "Dimensions", "rim_well_floor_diameter")
params.addProperty("App::PropertyLength", "rim_well_floor_width", "Dimensions", "rim_well_floor_width")
params.addProperty("App::PropertyLength", "curved_spoke_cutout_count", "Dimensions", "curved_spoke_cutout_count")
params.addProperty("App::PropertyLength", "curved_spoke_side_arc_radius", "Dimensions", "curved_spoke_side_arc_radius")
params.addProperty("App::PropertyLength", "curved_spoke_hub_arc_radius", "Dimensions", "curved_spoke_hub_arc_radius")
params.addProperty("App::PropertyLength", "curved_spoke_rim_arc_radius", "Dimensions", "curved_spoke_rim_arc_radius")
params.addProperty("App::PropertyLength", "curved_spoke_opening_hub_arc_center_radius", "Dimensions", "curved_spoke_opening_hub_arc_center_radius")
params.addProperty("App::PropertyLength", "curved_spoke_opening_side_arc_center_radius", "Dimensions", "curved_spoke_opening_side_arc_center_radius")
params.addProperty("App::PropertyLength", "curved_spoke_opening_side_arc_center_offset_angle", "Dimensions", "curved_spoke_opening_side_arc_center_offset_angle")
params.addProperty("App::PropertyLength", "curved_spoke_opening_side_arc_span", "Dimensions", "curved_spoke_opening_side_arc_span")
params.addProperty("App::PropertyLength", "curved_spoke_opening_hub_arc_span", "Dimensions", "curved_spoke_opening_hub_arc_span")
params.addProperty("App::PropertyLength", "curved_spoke_opening_rim_arc_span", "Dimensions", "curved_spoke_opening_rim_arc_span")
params.addProperty("App::PropertyLength", "detailed_cutout_leading_edge_arc_radius", "Dimensions", "detailed_cutout_leading_edge_arc_radius")
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_edge_arc_radius", "Dimensions", "detailed_cutout_trailing_edge_arc_radius")
params.addProperty("App::PropertyLength", "spoke_end_arc_radius", "Dimensions", "spoke_end_arc_radius")
params.addProperty("App::PropertyLength", "detailed_cutout_rim_arc_start_offset", "Dimensions", "detailed_cutout_rim_arc_start_offset")
params.addProperty("App::PropertyLength", "detailed_cutout_rim_arc_span", "Dimensions", "detailed_cutout_rim_arc_span")
params.addProperty("App::PropertyLength", "detailed_cutout_end_arc_center_radius", "Dimensions", "detailed_cutout_end_arc_center_radius")
params.addProperty("App::PropertyLength", "detailed_cutout_end_arc_center_offset_angle", "Dimensions", "detailed_cutout_end_arc_center_offset_angle")
params.addProperty("App::PropertyLength", "detailed_cutout_end_arc_span", "Dimensions", "detailed_cutout_end_arc_span")
params.addProperty("App::PropertyLength", "detailed_cutout_leading_edge_center_radius", "Dimensions", "detailed_cutout_leading_edge_center_radius")
params.addProperty("App::PropertyLength", "detailed_cutout_leading_edge_center_offset_angle", "Dimensions", "detailed_cutout_leading_edge_center_offset_angle")
params.addProperty("App::PropertyLength", "detailed_cutout_leading_edge_arc_span", "Dimensions", "detailed_cutout_leading_edge_arc_span")
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_edge_center_radius", "Dimensions", "detailed_cutout_trailing_edge_center_radius")
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_edge_center_offset_angle", "Dimensions", "detailed_cutout_trailing_edge_center_offset_angle")
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_edge_arc_span", "Dimensions", "detailed_cutout_trailing_edge_arc_span")
params.addProperty("App::PropertyLength", "detailed_cutout_leading_tip_center_radius", "Dimensions", "detailed_cutout_leading_tip_center_radius")
params.addProperty("App::PropertyLength", "detailed_cutout_leading_tip_center_offset_angle", "Dimensions", "detailed_cutout_leading_tip_center_offset_angle")
params.addProperty("App::PropertyLength", "detailed_cutout_leading_tip_arc_span", "Dimensions", "detailed_cutout_leading_tip_arc_span")
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_tip_center_offset_angle", "Dimensions", "detailed_cutout_trailing_tip_center_offset_angle")
params.addProperty("App::PropertyLength", "detailed_cutout_trailing_tip_arc_span", "Dimensions", "detailed_cutout_trailing_tip_arc_span")
params.addProperty("App::PropertyLength", "outer_curved_profile_arc_radius", "Dimensions", "outer_curved_profile_arc_radius")
params.addProperty("App::PropertyLength", "inner_curved_profile_arc_radius", "Dimensions", "inner_curved_profile_arc_radius")
params.addProperty("App::PropertyLength", "outer_curved_profile_arc_center_radius", "Dimensions", "outer_curved_profile_arc_center_radius")
params.addProperty("App::PropertyLength", "outer_curved_profile_arc_center_angle", "Dimensions", "outer_curved_profile_arc_center_angle")
params.addProperty("App::PropertyLength", "outer_curved_profile_arc_span", "Dimensions", "outer_curved_profile_arc_span")
params.addProperty("App::PropertyLength", "inner_curved_profile_arc_center_radius", "Dimensions", "inner_curved_profile_arc_center_radius")
params.addProperty("App::PropertyLength", "inner_curved_profile_arc_center_angle", "Dimensions", "inner_curved_profile_arc_center_angle")
params.addProperty("App::PropertyLength", "inner_curved_profile_arc_span", "Dimensions", "inner_curved_profile_arc_span")
params.addProperty("App::PropertyLength", "rim_trim_inner_radius", "Dimensions", "rim_trim_inner_radius")
params.addProperty("App::PropertyLength", "rim_trim_outer_radius", "Dimensions", "rim_trim_outer_radius")
params.addProperty("App::PropertyLength", "rim_trim_arc_top_radius", "Dimensions", "rim_trim_arc_top_radius")
params.addProperty("App::PropertyLength", "left_rim_trim_side_axial_offset", "Dimensions", "left_rim_trim_side_axial_offset")
params.addProperty("App::PropertyLength", "right_rim_trim_side_axial_offset", "Dimensions", "right_rim_trim_side_axial_offset")
params.addProperty("App::PropertyLength", "number_of_mounting_holes", "Dimensions", "number_of_mounting_holes")
params.addProperty("App::PropertyLength", "hub_mounting_bolt_circle_diameter", "Dimensions", "hub_mounting_bolt_circle_diameter")
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "mounting_hole_diameter")
params.addProperty("App::PropertyLength", "mounting_hole_counterbore_diameter", "Dimensions", "mounting_hole_counterbore_diameter")
params.addProperty("App::PropertyLength", "mounting_hole_counterbore_depth", "Dimensions", "mounting_hole_counterbore_depth")
params.addProperty("App::PropertyLength", "rim_profile_fillet_radius", "Dimensions", "rim_profile_fillet_radius")
params.addProperty("App::PropertyLength", "rim_well_transition_arc_span", "Dimensions", "rim_well_transition_arc_span")

# Set initial values
for name in dir(params):
    if name.startswith("hub_bore_diameter") or name.startswith("hub_outer_diameter") or name.startswith("hub_axial_width") or name.startswith("spoke_web_axial_width") or name.startswith("rim_axial_width") or name.startswith("rim_end_width") or name.startswith("rim_outer_diameter") or name.startswith("rim_inner_shoulder_radius") or name.startswith("rim_well_floor_diameter") or name.startswith("rim_well_floor_width") or name.startswith("curved_spoke_cutout_count") or name.startswith("curved_spoke_side_arc_radius") or name.startswith("curved_spoke_hub_arc_radius") or name.startswith("curved_spoke_rim_arc_radius") or name.startswith("curved_spoke_opening_hub_arc_center_radius") or name.startswith("curved_spoke_opening_side_arc_center_radius") or name.startswith("curved_spoke_opening_side_arc_center_offset_angle") or name.startswith("curved_spoke_opening_side_arc_span") or name.startswith("curved_spoke_opening_hub_arc_span") or name.startswith("curved_spoke_opening_rim_arc_span") or name.startswith("detailed_cutout_leading_edge_arc_radius") or name.startswith("detailed_cutout_trailing_edge_arc_radius") or name.startswith("spoke_end_arc_radius") or name.startswith("detailed_cutout_rim_arc_start_offset") or name.startswith("detailed_cutout_rim_arc_span") or name.startswith("detailed_cutout_end_arc_center_radius") or name.startswith("detailed_cutout_end_arc_center_offset_angle") or name.startswith("detailed_cutout_end_arc_span") or name.startswith("detailed_cutout_leading_edge_center_radius") or name.startswith("detailed_cutout_leading_edge_center_offset_angle") or name.startswith("detailed_cutout_leading_edge_arc_span") or name.startswith("detailed_cutout_trailing_edge_center_radius") or name.startswith("detailed_cutout_trailing_edge_center_offset_angle") or name.startswith("detailed_cutout_trailing_edge_arc_span") or name.startswith("detailed_cutout_leading_tip_center_radius") or name.startswith("detailed_cutout_leading_tip_center_offset_angle") or name.startswith("detailed_cutout_leading_tip_arc_span") or name.startswith("detailed_cutout_trailing_tip_center_offset_angle") or name.startswith("detailed_cutout_trailing_tip_arc_span") or name.startswith("outer_curved_profile_arc_radius") or name.startswith("inner_curved_profile_arc_radius") or name.startswith("outer_curved_profile_arc_center_radius") or name.startswith("outer_curved_profile_arc_center_angle") or name.startswith("outer_curved_profile_arc_span") or name.startswith("inner_curved_profile_arc_center_radius") or name.startswith("inner_curved_profile_arc_center_angle") or name.startswith("inner_curved_profile_arc_span") or name.startswith("rim_trim_inner_radius") or name.startswith("rim_trim_outer_radius") or name.startswith("rim_trim_arc_top_radius") or name.startswith("left_rim_trim_side_axial_offset") or name.startswith("right_rim_trim_side_axial_offset") or name.startswith("number_of_mounting_holes") or name.startswith("hub_mounting_bolt_circle_diameter") or name.startswith("mounting_hole_diameter") or name.startswith("mounting_hole_counterbore_diameter") or name.startswith("mounting_hole_counterbore_depth") or name.startswith("rim_profile_fillet_radius") or name.startswith("rim_well_transition_arc_span"):
        val = getattr(params, name)
        if isinstance(val, float):
            params.setProperty("User", name, str(val))
        elif isinstance(val, int):
            params.setProperty("User", name, str(val))

# --- Sketches ---

# 1. Base Section Profile (Hub + Spokes + Rim)
# Origin: Center of hub end face on positive-X side. Hub extends in negative-X.
# Profile is in YZ plane (attached to YZ_Plane).
# X is axial, Y is radial, Z is tangential.
# We will create the profile in the YZ plane.
# The profile will be rotated around the X axis to create the wheel.

# Define the profile points in YZ plane.
# Y: Radial distance from center. Z: Tangential position.
# We need to construct the shape of the cross-section.

# Helper to create a sketch object
def create_sketch(name, plane_name):
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.Placement = App.Placement(App.Vector(0, 0,
