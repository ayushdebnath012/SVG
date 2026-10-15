import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create Document
doc = App.newDocument("PowerStrip")

# --- Parameters ---
# Global
p_block_length = 34.75
p_block_width = 98.6
p_block_thickness = 3.2
p_base_x_min = -17.38
p_base_y_min = -96.79

# Outer Wall
p_block_extrude_depth = 17.46
p_outer_profile_top_y = -0.05
p_outer_profile_bottom_y = -95.04
p_outer_profile_left_side_x = -15.92
p_outer_profile_right_side_x = 15.9
p_top_edge_width = 19.87
p_top_edge_left_x = -9.99
p_top_edge_right_x = 9.88

# Top Terminals
p_terminal_L_center_x = -10.05
p_terminal_L_center_y = -8.36
p_terminal_L_radius = 5.85
p_terminal_L_start = 140.1317284
p_terminal_L_end = -179.9020586

p_terminal_R_center_x = 9.95
p_terminal_R_center_y = -8.56
p_terminal_R_radius = 5.94
p_terminal_R_start = 2.217415716
p_terminal_R_end = 41.38540326

# Transition Seed
p_trans_L_upper_center_x = -10.14
p_trans_L_upper_center_y = -17.59
p_trans_L_upper_radius = 5.74
p_trans_L_upper_start = -179.7005474
p_trans_L_upper_end = -107.6458007

p_trans_R_upper_center_x = 10.08
p_trans_R_upper_center_y = -17.74
p_trans_R_upper_radius = 5.81
p_trans_R_upper_start = -71.1286391
p_trans_R_upper_end = -3.748504046

p_trans_L_lower_center_x = -10.05
p_trans_L_lower_center_y = -32.23
p_trans_L_lower_radius = 5.82
p_trans_L_lower_start = 134.2342454
p_trans_L_lower_end = -180.0984463

p_trans_R_lower_center_x = 10.41
p_trans_R_lower_center_y = -32.12
p_trans_R_lower_radius = 5.46
p_trans_R_lower_start = 0.2098737116
p_trans_R_lower_end = 46.18730732

p_trans_L_elbow_x = -11.91
p_trans_L_elbow_y = -25.85
p_trans_R_elbow_x = 11.97
p_trans_R_elbow_y = -26.0

# Bottom Connectors
p_bot_L_center_x = -10.87
p_bot_L_center_y = -89.98
p_bot_L_radius = 5.05
p_bot_L_start = -180.0
p_bot_L_end = -90.0

p_bot_R_center_x = 10.74
p_bot_R_center_y = -89.88
p_bot_R_radius = 5.16
p_bot_R_start = -90.0
p_bot_R_end = 0.0

p_bot_straight_span = 21.61

# Stepped Inner Wall
p_stepped_extrude = 3.73
p_stepped_center_x = 0.0
p_stepped_top_y = -3.58
p_stepped_bottom_y = -91.36
p_cavity_width = 23.19
p_cavity_height = 87.78
p_stepped_top_flat = 11.23

# Right Side Stepped Profile
p_tr_corner_r = 2.43
p_tr_corner_a = 45.7064486
p_tc_r = 1.7
p_tl_r = 2.04
p_tl_a = 44.6468796
p_tl_corner_r = 2.08
p_us_r = 1.49
p_us_a = 85.4445613
p_ms_r = 1.24
p_mr_r = 1.48
p_ls_r = 1.3
p_lsr_r = 1.55

p_tr_shoulder = 5.6
p_tl_shoulder = 5.59

p_uov_r = 8.12
p_uol_r = 8.21
p_uhr_r = 0.78
p_uhl_r = 0.79
p_uiv_r = 11.33
p_uil_r = 11.27
p_utd_r = 3.2
p_utd_l = 3.27

p_mov_r = 8.96
p_mol_r = 9.18
p_mhr_r = 0.72
p_mhl_r = 1.05
p_miv_r = 11.39
p_mil_r = 10.9
p_mtd_r = 3.06
p_mtd_l = 3.7

p lov_r = 8.98
p lol_r = 8.91
p_lhr_r = 0.68
p_lhl_r = 0.99
p_liv_r = 11.07
p_lil_r = 11.01
p_ltd_r = 3.49
p_ltd_l = 3.59

p bov_r = 10.31
p bol_r = 10.31
p_boe_r = 4.9
p_boe_l = 4.98
p_bbr = 0.48
p_bbl = 0.48

p_br_ba = 36.6341139
p_bl_ba = 42.4362298

# Left Side Stepped Profile (Calculated from Right symmetry + params)
# Note: Params provided are specific. I will implement the left side geometry logic based on the param names provided which seem to mirror the right side but with different values.
# Since the prompt gives specific values for "left" params (e.g. p_tl_r, p_tl_a), I will use them.
# However, many params like p_uov_r seem to be the vertical length on the left side based on the naming convention in similar tasks, but here the naming is mixed. 
# Let's assume the provided params map directly to the Left side features where "left" is in the name, and Right where "right" is in the name.
# The prompt lists: upper_outer_vertical_right_length, upper_horizontal_ledge_right_length... 
# It also lists: upper_outer_vertical_left_length (not in text above? Wait, text says "upper_outer_vertical_right_length = 8.12 mm" then "upper_horizontal_ledge_right_length = 0.78 mm" ... then "middle_outer_vertical_right_length" ...).
# Wait, the prompt text says: "upper_outer_vertical_right_length = 8.12 mm" ... "upper_horizontal_ledge_right_length = 0.78 mm".
# It does NOT explicitly list "upper_outer_vertical_left_length" in the value list above, but it does list "upper_horizontal_ledge_left_length = 0.79 mm".
# Let's re-read carefully.
# "upper_outer_vertical_right_length = 8.12 mm"
# "upper_horizontal_ledge_right_length = 0.78 mm"
# "upper_inner_vertical_right_length = 11.33 mm"
# "upper_inner_vertical_left_length = 11.27 mm" -> Ah, here is a left one.
# "upper_transition_right_diagonal_length = 3.2 mm"
# "upper_transition_left_diagonal_length = 3.27 mm"
# So for the Left side, I need to find the corresponding vertical/ledge lengths.
# The prompt lists: "upper_outer_vertical_right_length", "upper_horizontal_ledge_right_length", "upper_inner_vertical_right_length", "upper_inner_vertical_left_length".
# It seems the "outer" vertical lengths on the left are missing explicit names in the list? 
# Let's assume symmetry or reuse the right values if not specified, or derive from the "left" versions available.
# Actually, looking at the list: 
# Right: uov_r, uhr_r, uiv_r, utd_r
# Left: uol_r (upper_outer_vertical_left_length is NOT in the list? Wait. 
# Let's look at the list again.
# "upper_outer_vertical_right_length = 8.12 mm"
# "upper_horizontal_ledge_right_length = 0.78 mm"
# "upper_inner_vertical_right_length = 11.33 mm"
# "upper_inner_vertical_left_length = 11.27 mm"
# "upper_transition_right_diagonal_length = 3.2 mm"
# "upper_transition_left_diagonal_length = 3.27 mm"
# "middle_outer_vertical_right_length = 8.96 mm"
# "middle_outer_vertical_left_length = 9.18 mm" -> Here is a left one!
# "middle_horizontal_ledge_right_length = 0.72 mm"
# "middle_horizontal_ledge_left_length = 1.05 mm"
# "middle_inner_vertical_right_length = 11.39 mm"
# "middle_inner_vertical_left_length = 10.9 mm"
# "middle_transition_right_diagonal_length = 3.06 mm"
# "middle_transition_left_diagonal_length = 3.7 mm"
# "lower_outer_vertical_right_length = 8.98 mm"
# "lower_outer_vertical_left_length = 8.91 mm" -> Here is a left one!
# "lower_horizontal_ledge_right_length = 0.68 mm"
# "lower_horizontal_ledge_left_length = 0.99 mm"
# "lower_inner_vertical_right_length = 11.07 mm"
# "lower_inner_vertical_left_length = 11.01 mm"
# "lower_transition_right_diagonal_length = 3.49 mm"
# "lower_transition_left_diagonal_length = 3.59 mm"
# "bottom_outer_vertical_right_length = 10.31 mm"
# "bottom_outer_vertical_left_length = 10.31 mm"
# "bottom_outer_ledge_right_length = 4.9 mm"
# "bottom_outer_ledge_left_length = 4.98 mm"
# "bottom_right_bevel_length = 0.48 mm"
# "bottom_left_bevel_length = 0.48 mm"

# Missing Left Verticals for Upper Transition?
# "upper_outer_vertical_right_length" is given. "upper_horizontal_ledge_right_length" is given.
# "upper_inner_vertical_right_length" is given. "upper_inner_vertical_left_length" is given.
# "upper_transition_right_diagonal_length" is given. "upper_transition_left_diagonal_length" is given.
# Is "upper_outer_vertical_left_length" missing? 
# Let's assume symmetry for the missing "outer" verticals if not explicitly provided, or check if I missed it.
# Re-reading: "upper_outer_vertical_right_length = 8.12 mm". 
# It seems "upper_outer_vertical_left_length" is NOT in the list.
# However, "middle_outer_vertical_left_length" IS in the list.
# "lower_outer_vertical_left_length" IS in the list.
# I will assume the missing "upper_outer_vertical_left_length" is the same as the right one (8.12) or calculated. 
# Given the precision, I will assume it is 8.12 if not specified, but wait, "upper_inner_vertical_left_length" is 11.27 vs 11.33 right.
# Let's assume the "outer" verticals on the left are also 8.12? Or maybe I should look for "upper_outer_vertical_left_length". 
# I will assume 8.12 for now as a fallback, but the pattern suggests asymmetry. 
# Actually, looking at the pattern of provided values:
# Right: 8.12
# Left: (Missing)
# Middle Left: 9.18 (vs Middle Right 8.96)
# Lower Left: 8.91 (vs Lower Right 8.98)
# Bottom Left: 10.31 (vs Bottom Right 10.31)
# I will use 8.12 for the missing upper left outer vertical.

# Ribs
p_rib_w = 1.6
p_rib_l = 86.7
p_rib_h = 3.2
p_gap = 7.0
p_n_ribs = 2
p_rib_L_x = -4.31
p_rib_R_x = 2.69
p_rib_y_min = -90.88

# Sockets
p_cavity_cut = 18.5
p_sock_start_z = 0.0
p_out_top_w = 12.87
p_in_top_w = 10.15
p_s_outer_tr_x = 6.54
p_s_inner_tr_x = 5.12
p_out_str_r = 7.62
p_out_str_l = 7.63
p_in_str_r = 6.06
p_in_str_l = 5.81
p_out_tr_r = 6.29
p_out_ur_r = 6.59
p_out_lr_r = 5.91
p_out_ll_r = 5.99
p_out_ul_r = 6.42
p_out_tl_r = 6.77
p_in_tr_r = 2.99
p_in_tl_r = 3.26
p_in_ul_r = 3.76
p_in_ll_r = 3.46
p_in_lr_r = 3.3
p_in_ur_r = 3.02
p_s_outer_l_x = -14.93
p_s_outer_r_x = 14.93
p_s_outer_top_y = -72.6
p_s_outer_bot_y = -94.68
p_s_inner_l_x = -11.14
p_s_inner_r_x = 11.28
p_s_inner_top_y = -75.9
p_s_inner_bot_y = -91.27

# Small Cavities
p_small_l = 2.47
p_small_w = 5.0
p_small_cut = 8.0
p_small_start_z = 0.0
p_n_small = 3
p_r_x = 5.79
p_r_y = -88.15
p_c_x = -1.19
p_c_y = -84.04
p_l_x = -8.2
p_l_y = -88.15

p_n_sockets = 4
p_pitch = 24.0

# --- Setup Body and Plane ---
body = doc.addObject("PartDesign::Body", "Body")
# Attach to XY plane
xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())

# --- Parameters Object (Editable) ---
# We create a VarSet to hold parameters, but for simplicity in this script, we will set the properties directly on the features 
# or use the expressions. The prompt asks for "named document objects" driving the geometry.
# The most robust way in FreeCAD script is to set the properties directly or use expressions.
# I will use expressions referencing a "Parameters" object to satisfy "driven by named document objects".

params = body.newObject("App::Parameter", "Parameters")

# Helper to set param
def set_param(name, val):
    params.addProperty("App::PropertyLength", name)
    params[name] = val
    return val

# Set all params
set_param("block_length", p_block_length)
set_param("block_width", p_block_width)
set_param("block_thickness", p_block_thickness)
set_param("base_x_min", p_base_x_min)
set_param("base_y_min", p_base_y_min)
set_param("block_extrude_depth", p_block_extrude_depth)
set_param("outer_profile_top_y", p_outer_profile_top_y)
set_param("outer_profile_bottom_y", p_outer_profile_bottom_y)
set_param("outer_profile_left_side_x", p_outer_profile_left_side_x)
set_param("outer_profile_right_side_x", p_outer_profile_right_side_x)
set_param("top_edge_width", p_top_edge_width)
set_param("top_edge_left_x", p_top_edge_left_x)
set_param("top_edge_right_x", p_top_edge_right_x)
set_param("terminal_L_center_x", p_terminal_L_center_x)
set_param("terminal_L_center_y", p_terminal_L_center_y)
set_param("terminal_L_radius", p_terminal_L_radius)
set_param("terminal_L_start", p_terminal_L_start)
set_param("terminal_L_end", p_terminal_L_end)
set_param("terminal_R_center_x", p_terminal_R_center_x)
set_param("terminal_R_center_y", p_terminal_R_center_y)
set_param("terminal_R_radius", p_terminal_R_radius)
set_param("terminal_R_start", p_terminal_R_start)
set_param("terminal_R_end", p_terminal_R_end)
set_param("trans_L_upper_center_x", p
