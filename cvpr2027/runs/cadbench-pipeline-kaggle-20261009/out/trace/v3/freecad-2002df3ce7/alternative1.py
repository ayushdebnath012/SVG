import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration & Parameters ---
doc = App.newDocument("TrussPlate")

# Body
body = doc.addObject("PartDesign::Body", "Body")
body.Location = App.Placement(App.Vector(0,0,0), App.Rotation())

# Named Parameters (Editable in PropertyEditor)
# Dimensions
p_thickness = body.newObject("App::PropertyLength", "plate_thickness")
p_thickness.Thumb = "Material"
p_thickness.Width = 8.00

p_base_sketch_rotation = body.newObject("App::PropertyAngle", "base_sketch_plane_rotation_angle")
p_base_sketch_rotation.Thumb = "Material"
p_base_sketch_rotation.Angle = 90.0

# Outer Profile Dimensions
p_large_width = body.newObject("App::PropertyLength", "large_outer_rectangle_width")
p_large_width.Width = 280.00
p_large_height = body.newObject("App::PropertyLength", "large_outer_rectangle_height")
p_large_height.Width = 447.00
p_large_center_y = body.newObject("App::PropertyLength", "large_outer_rectangle_center_y")
p_large_center_y.Width = -51.00

p_mid_width = body.newObject("App::PropertyLength", "middle_outer_rectangle_width")
p_mid_width.Width = 144.00
p_mid_height = body.newObject("App::PropertyLength", "middle_outer_rectangle_height")
p_mid_height.Width = 64.00
p_mid_center_y = body.newObject("App::PropertyLength", "middle_outer_rectangle_center_y")
p_mid_center_y.Width = 204.50

p_small_width = body.newObject("App::PropertyLength", "small_outer_rectangle_width")
p_small_width.Width = 52.00
p_small_height = body.newObject("App::PropertyLength", "small_outer_rectangle_height")
p_small_height.Width = 38.00
p_small_center_y = body.newObject("App::PropertyLength", "small_outer_rectangle_center_y")
p_small_center_y.Width = 255.50

# Fillets & Chamfers
p_corner_fillet = body.newObject("App::PropertyLength", "rectangular_section_corner_chamfer_fillet_radius")
p_corner_fillet.Width = 10.00
p_lower_flat_w = body.newObject("App::PropertyLength", "large_outer_rectangle_lower_corner_chamfer_flat_width")
p_lower_flat_w.Width = 200.00
p_upper_setback = body.newObject("App::PropertyLength", "large_outer_rectangle_upper_corner_chamfer_setback")
p_upper_setback.Width = 17.00
p_recess_depth = body.newObject("App::PropertyLength", "large_outer_rectangle_side_trapezoidal_recess_depth")
p_recess_depth.Width = 17.00
p_recess_01_cy = body.newObject("App::PropertyLength", "large_outer_rectangle_side_trapezoidal_recess_01_center_y")
p_recess_01_cy.Width = -149.50
p_recess_01_h_out = body.newObject("App::PropertyLength", "large_outer_rectangle_side_trapezoidal_recess_01_outer_height")
p_recess_01_h_out.Width = 98.28
p_recess_01_h_in = body.newObject("App::PropertyLength", "large_outer_rectangle_side_trapezoidal_recess_01_inner_flat_height")
p_recess_01_h_in.Width = 47.72
p_recess_02_cy = body.newObject("App::PropertyLength", "large_outer_rectangle_side_trapezoidal_recess_02_center_y")
p_recess_02_cy.Width = 25.50
p_recess_02_h_out = body.newObject("App::PropertyLength", "large_outer_rectangle_side_trapezoidal_recess_02_outer_height")
p_recess_02_h_out.Width = 148.28
p_recess_02_h_in = body.newObject("App::PropertyLength", "large_outer_rectangle_side_trapezoidal_recess_02_inner_flat_height")
p_recess_02_h_in.Width = 97.72

# Truss Layout Angles
p_diag_1 = body.newObject("App::PropertyAngle", "truss_diagonal_angle_family_1")
p_diag_1.Angle = 27.3777028
p_diag_2 = body.newObject("App::PropertyAngle", "truss_diagonal_angle_family_2")
p_diag_2.Angle = 63.4349488
p_diag_3 = body.newObject("App::PropertyAngle", "truss_diagonal_angle_family_3")
p_diag_3.Angle = 28.8386275
p_diag_4 = body.newObject("App::PropertyAngle", "truss_diagonal_angle_family_4")
p_diag_4.Angle = 46.1233027
p_diag_5 = body.newObject("App::PropertyAngle", "truss_diagonal_angle_family_5")
p_diag_5.Angle = 165.8183429

# Cutout Radius
p_cutout_radius = body.newObject("App::PropertyLength", "truss_cutout_transition_radius")
p_cutout_radius.Width = 3.00

# Mounting Holes
p_hole_diam = body.newObject("App::PropertyLength", "mounting_hole_diameter")
p_hole_diam.Width = 4.30
p_center_bore_diam = body.newObject("App::PropertyLength", "center_bore_diameter")
p_center_bore_diam.Width = 7.00
p_center_bore_y = body.newObject("App::PropertyLength", "center_bore_axis_y")
p_center_bore_y.Width = 264.50
p_center_mount_half_sp = body.newObject("App::PropertyLength", "center_mounting_hole_pair_half_spacing")
p_center_mount_half_sp.Width = 18.00
p_upper_inner_half_sp = body.newObject("App::PropertyLength", "upper_inner_mounting_hole_pair_half_spacing")
p_upper_inner_half_sp.Width = 62.00
p_lower_inner_half_sp = body.newObject("App::PropertyLength", "lower_inner_mounting_hole_pair_half_spacing")
p_lower_inner_half_sp.Width = 61.76
p_upper_inner_y = body.newObject("App::PropertyLength", "upper_inner_mounting_hole_pair_y")
p_upper_inner_y.Width = 226.50
p_lower_inner_y = body.newObject("App::PropertyLength", "lower_inner_mounting_hole_pair_y")
p_lower_inner_y.Width = 165.50
p_side_hole_x = body.newObject("App::PropertyLength", "side_mounting_hole_axis_x")
p_side_hole_x.Width = 136.00
p_side_row_1_y = body.newObject("App::PropertyLength", "side_mounting_hole_row_1_y")
p_side_row_1_y.Width = 137.50
p_side_row_2_y = body.newObject("App::PropertyLength", "side_mounting_hole_row_2_y")
p_side_row_2_y.Width = 113.50
p_side_row_3_y = body.newObject("App::PropertyLength", "side_mounting_hole_row_3_y")
p_side_row_3_y.Width = -62.50
p_side_row_4_y = body.newObject("App::PropertyLength", "side_mounting_hole_row_4_y")
p_side_row_4_y.Width = -86.50
p_side_row_5_y = body.newObject("App::PropertyLength", "side_mounting_hole_row_5_y")
p_side_row_5_y.Width = -216.32
p_side_row_6_y = body.newObject("App::PropertyLength", "side_mounting_hole_row_6_y")
p_side_row_6_y.Width = -240.32

# Large Triangular Openings
p_ltp_01_02_base = body.newObject("App::PropertyLength", "large_triangular_opening_pair_01_02_base_length")
p_ltp_01_02_base.Width = 141.90
p_ltp_01_02_angle = body.newObject("App::PropertyAngle", "large_triangular_opening_pair_01_02_base_angle")
p_ltp_01_02_angle.Angle = 27.3777028
p_ltp_01_cx = body.newObject("App::PropertyLength", "large_triangular_opening_pair_01_positive_member_centroid_x")
p_ltp_01_cx.Width = 86.75
p_ltp_01_cy = body.newObject("App::PropertyLength", "large_triangular_opening_pair_01_positive_member_centroid_y")
p_ltp_01_cy.Width = -170.50
p_ltp_02_cx = body.newObject("App::PropertyLength", "large_triangular_opening_pair_02_positive_member_centroid_x")
p_ltp_02_cx.Width = 24.25
p_ltp_02_cy = body.newObject("App::PropertyLength", "large_triangular_opening_pair_02_positive_member_centroid_y")
p_ltp_02_cy.Width = -170.50
p_ltp_03_base = body.newObject("App::PropertyLength", "large_triangular_opening_pair_03_base_length")
p_ltp_03_base.Width = 133.12
p_ltp_03_angle = body.newObject("App::PropertyAngle", "large_triangular_opening_pair_03_base_angle")
p_ltp_03_angle.Angle = 28.8386275
p_ltp_03_cx = body.newObject("App::PropertyLength", "large_triangular_opening_pair_03_positive_member_centroid_x")
p_ltp_03_cx.Width = 86.78
p_ltp_03_cy = body.newObject("App::PropertyLength", "large_triangular_opening_pair_03_positive_member_centroid_y")
p_ltp_03_cy.Width = 16.50

# Medium Triangular Openings
p_mtp_01_02_base = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_01_02_base_length")
p_mtp_01_02_base.Width = 73.49
p_mtp_01_02_angle = body.newObject("App::PropertyAngle", "medium_triangular_opening_pair_01_02_base_angle")
p_mtp_01_02_angle.Angle = 62.6222972
p_mtp_01_cx = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_01_positive_member_centroid_x")
p_mtp_01_cx.Width = 55.50
p_mtp_01_cy = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_01_positive_member_centroid_y")
p_mtp_01_cy.Width = -230.85
p_mtp_02_cx = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_02_positive_member_centroid_x")
p_mtp_02_cx.Width = 55.50
p_mtp_02_cy = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_02_positive_member_centroid_y")
p_mtp_02_cy.Width = -110.15
p_mtp_03_cx = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_03_center_x")
p_mtp_03_cx.Width = 30.11
p_mtp_03_cy = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_03_center_y")
p_mtp_03_cy.Width = -7.95
p_mtp_03_w = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_03_envelope_width")
p_mtp_03_w.Width = 36.23
p_mtp_03_h = body.newObject("App::PropertyLength", "medium_triangular_opening_pair_03_envelope_height")
p_mtp_03_h.Width = 66.89

# Right Triangular Openings
p_rtp_base = body.newObject("App::PropertyLength", "right_triangular_opening_pair_base_length")
p_rtp_base.Width = 73.30
p_rtp_angle = body.newObject("App::PropertyAngle", "right_triangular_opening_pair_base_angle")
p_rtp_angle.Angle = 61.1613725
p_rtp_01_cx = body.newObject("App::PropertyLength", "right_triangular_opening_01_centroid_x")
p_rtp_01_cx.Width = 55.50
p_rtp_01_cy = body.newObject("App::PropertyLength", "right_triangular_opening_01_centroid_y")
p_rtp_01_cy.Width = -40.31
p_rtp_02_cx = body.newObject("App::PropertyLength", "right_triangular_opening_02_centroid_x")
p_rtp_02_cx.Width = -55.50
p_rtp_02_cy = body.newObject("App::PropertyLength", "right_triangular_opening_02_centroid_y")
p_rtp_02_cy.Width = -40.31

# Central Trapezoidal Opening
p_cto_center_y = body.newObject("App::PropertyLength", "central_trapezoidal_opening_center_y")
p_cto_center_y.Width = 96.50
p_cto_corner_r = body.newObject("App::PropertyLength", "central_trapezoidal_opening_corner_radius")
p_cto_corner_r.Width = 10.00
p_cto_w = body.newObject("App::PropertyLength", "central_trapezoidal_opening_envelope_width")
p_cto_w.Width = 184.30
p_cto_h = body.newObject("App::PropertyLength", "central_trapezoidal_opening_envelope_height")
p_cto_h.Width = 118.00
p_cto_lower_w = body.newObject("App::PropertyLength", "central_trapezoidal_opening_lower_flat_width")
p_cto_lower_w.Width = 108.61

# Small Triangular Opening
p_sto_cx = body.newObject("App::PropertyLength", "small_triangular_opening_centroid_x")
p_sto_cx.Width = 0.00
p_sto_cy = body.newObject("App::PropertyLength", "small_triangular_opening_centroid_y")
p_sto_cy.Width = 186.39
p_sto_base = body.newObject("App::PropertyLength", "small_triangular_opening_base_length")
p_sto_base.Width = 86.69
p_sto_angle = body.newObject("App::PropertyAngle", "small_triangular_opening_base_angle")
p_sto_angle.Angle = 43.8766972

# Chamfer Cut Right Triangles
p_crt_01_cx = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_01_center_x")
p_crt_01_cx.Width = -32.55
p_crt_01_cy = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_01_center_y")
p_crt_01_cy.Width = 203.69
p_crt_01_w = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_01_envelope_width")
p_crt_01_w.Width = 38.90
p_crt_01_h = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_01_envelope_height")
p_crt_01_h.Width = 37.63
p_crt_02_cx = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_02_center_x")
p_crt_02_cx.Width = 32.55
p_crt_02_cy = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_02_center_y")
p_crt_02_cy.Width = 203.69
p_crt_02_w = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_02_envelope_width")
p_crt_02_w.Width = 38.90
p_crt_02_h = body.newObject("App::PropertyLength", "chamfer_cut_right_triangular_opening_02_envelope_height")
p_crt_02_h.Width = 37.63

# Helper to add geometry to sketch
def add_line(sk, p1, p2, name=None):
    if name is None: name = "Line"
    sk.addGeometry(Part.LineSegment(p1, p2), False)
    return name

def add_circle(sk, center, radius, name=None):
    if name is None: name = "Circle"
    sk.addGeometry(Part.Circle(center,
