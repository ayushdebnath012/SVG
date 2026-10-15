import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Define parameters as requested
params = {
    "base_frame_extrusion_depth": 80.0,
    "number_of_vertical_supports": 2,
    "number_of_top_rails": 1,
    "mounting_hole_diameter": 10.0,
    "number_of_mounting_holes": 4,
    "mounting_hole_depth": 20.0,
    "mounting_hole_centerline_y_offset": 40.0,
    "mounting_hole_left_outer_center_x": -815.0,
    "mounting_hole_left_inner_center_x": -785.0,
    "mounting_hole_right_inner_center_x": 785.0,
    "mounting_hole_right_outer_center_x": 815.0,
    "number_of_deep_mounting_holes": 2,
    "mounting_hole_cut_depth": 2333.0,
    "deep_mounting_hole_primary_center_x": -160.0,
    "deep_mounting_hole_secondary_center_x": -190.0,
    "deep_mounting_hole_center_y": 25.0,
    "support_boss_height": 50.0,
    "support_boss_diameter": 20.0,
    "number_of_support_bosses": 12,
    "spacing_distance_between_support_bosses": 263.0,
    "end_boss_diameter": 20.0,
    "number_of_end_bosses": 2,
    "end_boss_height": 10.0,
    "end_boss_left_center_x": -799.2678421,
    "end_boss_right_center_x": 799.2678421,
    "end_boss_center_y": 34.2678421,
    "frame_left_end_x": -1500.0,
    "frame_right_end_x": 1500.0,
    "frame_top_y": 450.0,
    "frame_inner_top_y": 380.0,
    "frame_bottom_y": -450.0,
    "left_support_outer_x": -835.0,
    "left_support_inner_x": -765.0,
    "right_support_inner_x": 765.0,
    "right_support_outer_x": 835.0,
    "support_boss_pattern_direction_x": -1.0,
    "support_boss_seed_center_x": 1445.0,
    "support_boss_seed_center_y": -415.0,
}

# Create document
doc = App.newDocument("ConveyorBaseFrame")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObjectGroup", "Group")
doc.setActiveObject("Body")

# Create Parameters object to store values
params_obj = body.newObject("App::VarSet", "Parameters")
for key, value in params.items():
    prop_name = key.replace("_", "")
    if "number_of" in key:
        prop_name = key.replace("number_of", "count")
    elif "distance" in key:
        prop_name = key.replace("distance", "dist")
    elif "center" in key:
        prop_name = key.replace("center", "pos")
    elif "depth" in key:
        prop_name = key.replace("depth", "dpth")
    elif "diameter" in key:
        prop_name = key.replace("diameter", "diam")
    elif "height" in key:
        prop_name = key.replace("height", "hgt")
    elif "offset" in key:
        prop_name = key.replace("offset", "ofs")
    elif "bosses" in key:
        prop_name = key.replace("bosses", "boss_cnt")
    elif "boss" in key:
        prop_name = key.replace("boss", "boss")
    elif "support" in key:
        prop_name = key.replace("support", "supp")
    elif "mounting" in key:
        prop_name = key.replace("mounting", "mnt")
    elif "hole" in key:
        prop_name = key.replace("hole", "hl")
    elif "frame" in key:
        prop_name = key.replace("frame", "fr")
    elif "end" in key:
        prop_name = key.replace("end", "end")
    elif "left" in key:
        prop_name = key.replace("left", "left")
    elif "right" in key:
        prop_name = key.replace("right", "right")
    elif "inner" in key:
        prop_name = key.replace("inner", "in")
    elif "outer" in key:
        prop_name = key.replace("outer", "out")
    elif "top" in key:
        prop_name = key.replace("top", "top")
    elif "bottom" in key:
        prop_name = key.replace("bottom", "bot")
    elif "primary" in key:
        prop_name = key.replace("primary", "prim")
    elif "secondary" in key:
        prop_name = key.replace("secondary", "sec")
    elif "seed" in key:
        prop_name = key.replace("seed", "seed")
    elif "pattern" in key:
        prop_name = key.replace("pattern", "pat")
    elif "spacing" in key:
        prop_name = key.replace("spacing", "spc")
    elif "cut" in key:
        prop_name = key.replace("cut", "cut")
    elif "boss_cnt" in key:
        prop_name = key.replace("boss_cnt", "boss_cnt")
    elif "boss_hgt" in key:
        prop_name = key.replace("boss_hgt", "boss_hgt")
    elif "boss_diam" in key:
        prop_name = key.replace("boss_diam", "boss_diam")
    elif "boss_pos" in key:
        prop_name = key.replace("boss_pos", "boss_pos")
    elif "supp_cnt" in key:
        prop_name = key.replace("supp_cnt", "supp_cnt")
    elif "supp_hgt" in key:
        prop_name = key.replace("supp_hgt", "supp_hgt")
    elif "supp_diam" in key:
        prop_name = key.replace("supp_diam", "supp_diam")
    elif "supp_pos" in key:
        prop_name = key.replace("supp_pos", "supp_pos")
    elif "mnt_cnt" in key:
        prop_name = key.replace("mnt_cnt", "mnt_cnt")
    elif "mnt_diam" in key:
        prop_name = key.replace("mnt_diam", "mnt_diam")
    elif "mnt_dpth" in key:
        prop_name = key.replace("mnt_dpth", "mnt_dpth")
    elif "mnt_ofs" in key:
        prop_name = key.replace("mnt_ofs", "mnt_ofs")
    elif "mnt_pos" in key:
        prop_name = key.replace("mnt_pos", "mnt_pos")
    elif "fr_extr" in key:
        prop_name = key.replace("fr_extr", "fr_extr")
    elif "fr_left" in key:
        prop_name = key.replace("fr_left", "fr_left")
    elif "fr_right" in key:
        prop_name = key.replace("fr_right", "fr_right")
    elif "fr_top" in key:
        prop_name = key.replace("fr_top", "fr_top")
    elif "fr_bot" in key:
        prop_name = key.replace("fr_bot", "fr_bot")
    elif "fr_in_top" in key:
        prop_name = key.replace("fr_in_top", "fr_in_top")
    elif "left_out" in key:
        prop_name = key.replace("left_out", "left_out")
    elif "left_in" in key:
        prop_name = key.replace("left_in", "left_in")
    elif "right_in" in key:
        prop_name = key.replace("right_in", "right_in")
    elif "right_out" in key:
        prop_name = key.replace("right_out", "right_out")
    elif "pat_dir" in key:
        prop_name = key.replace("pat_dir", "pat_dir")
    elif "seed_x" in key:
        prop_name = key.replace("seed_x", "seed_x")
    elif "seed_y" in key:
        prop_name = key.replace("seed_y", "seed_y")
    elif "spc_dist" in key:
        prop_name = key.replace("spc_dist", "spc_dist")
    elif "cut_dpth" in key:
        prop_name = key.replace("cut_dpth", "cut_dpth")
    elif "prim_x" in key:
        prop_name = key.replace("prim_x", "prim_x")
    elif "sec_x" in key:
        prop_name = key.replace("sec_x", "sec_x")
    elif "end_diam" in key:
        prop_name = key.replace("end_diam", "end_diam")
    elif "end_hgt" in key:
        prop_name = key.replace("end_hgt", "end_hgt")
    elif "end_left" in key:
        prop_name = key.replace("end_left", "end_left")
    elif "end_right" in key:
        prop_name = key.replace("end_right", "end_right")
    elif "end_y" in key:
        prop_name = key.replace("end_y", "end_y")
    elif "hl_diam" in key:
        prop_name = key.replace("hl_diam", "hl_diam")
    elif "hl_dpth" in key:
        prop_name = key.replace("hl_dpth", "hl_dpth")
    elif "hl_ofs" in key:
        prop_name = key.replace("hl_ofs", "hl_ofs")
    elif "hl_left_out" in key:
        prop_name = key.replace("hl_left_out", "hl_left_out")
    elif "hl_left_in" in key:
        prop_name = key.replace("hl_left_in", "hl_left_in")
    elif "hl_right_in" in key:
        prop_name = key.replace("hl_right_in", "hl_right_in")
    elif "hl_right_out" in key:
        prop_name = key.replace("hl_right_out", "hl_right_out")
    elif "hl_cnt" in key:
        prop_name = key.replace("hl_cnt", "hl_cnt")
    elif "hl_cut" in key:
        prop_name = key.replace("hl_cut", "hl_cut")
    elif "hl_prim" in key:
        prop_name = key.replace("hl_prim", "hl_prim")
    elif "hl_sec" in key:
        prop_name = key.replace("hl_sec", "hl_sec")
    elif "hl_y" in key:
        prop_name = key.replace("hl_y", "hl_y")
    elif "boss_cnt" in key:
        prop_name = key.replace("boss_cnt", "boss_cnt")
    elif "boss_hgt" in key:
        prop_name = key.replace("boss_hgt", "boss_hgt")
    elif "boss_diam" in key:
        prop_name = key.replace("boss_diam", "boss_diam")
    elif "boss_pos" in key:
        prop_name = key.replace("boss_pos", "boss_pos")
    elif "supp_cnt" in key:
        prop_name = key.replace("supp_cnt", "supp_cnt")
    elif "supp_hgt" in key:
        prop_name = key.replace("supp_hgt", "supp_hgt")
    elif "supp_diam" in key:
        prop_name = key.replace("supp_diam", "supp_diam")
    elif "supp_pos" in key:
        prop_name = key.replace("supp_pos", "supp_pos")
    elif "mnt_cnt" in key:
        prop_name = key.replace("mnt_cnt", "mnt_cnt")
    elif "mnt_diam" in key:
        prop_name = key.replace("mnt_diam", "mnt_diam")
    elif "mnt_dpth" in key:
        prop_name = key.replace("mnt_dpth", "mnt_dpth")
    elif "mnt_ofs" in key:
        prop_name = key.replace("mnt_ofs", "mnt_ofs")
    elif "mnt_pos" in key:
        prop_name = key.replace("mnt_pos", "mnt_pos")
    elif "fr_extr" in key:
        prop_name = key.replace("fr_extr", "fr_extr")
    elif "fr_left" in key:
        prop_name = key.replace("fr_left", "fr_left")
    elif "fr_right" in key:
        prop_name = key.replace("fr_right", "fr_right")
    elif "fr_top" in key:
        prop_name = key.replace("fr_top", "fr_top")
    elif "fr_bot" in key:
        prop_name = key.replace("fr_bot", "fr_bot")
    elif "fr_in_top" in key:
        prop_name = key.replace("fr_in_top", "fr_in_top")
    elif "left_out" in key:
        prop_name = key.replace("left_out", "left_out")
    elif "left_in" in key:
        prop_name = key.replace("left_in", "left_in")
    elif "right_in" in key:
        prop_name = key.replace("right_in", "right_in")
    elif "right_out" in key:
        prop_name = key.replace("right_out", "right_out")
    elif "pat_dir" in key:
        prop_name = key.replace("pat_dir", "pat_dir")
    elif "seed_x" in key:
        prop_name = key.replace("seed_x", "seed_x")
    elif "seed_y" in key:
        prop_name = key.replace("seed_y", "seed_y")
    elif "spc_dist" in key:
        prop_name = key.replace("spc_dist", "spc_dist")
    elif "cut_dpth" in key:
        prop_name = key.replace("cut_dpth", "cut_dpth")
    elif "prim_x" in key:
        prop_name = key.replace("prim_x", "prim_x")
    elif "sec_x" in key:
        prop_name = key.replace("sec_x", "sec_x")
    elif "end_diam" in key:
        prop_name = key.replace("end_diam", "end_diam")
    elif "end_hgt" in key:
        prop_name = key.replace("end_hgt", "end_hgt")
    elif "end_left" in key:
        prop_name = key.replace("end_left", "end_left")
    elif "end_right" in key:
        prop_name = key.replace("end_right", "end_right")
    elif "end_y" in key:
        prop_name = key.replace("end_y", "end_y")
    elif "hl_diam" in key:
        prop_name = key.replace("hl_diam", "hl_diam")
    elif "hl_dpth" in key:
        prop_name = key.replace("hl_dpth", "hl_dpth")
    elif "hl_ofs" in key:
        prop_name = key.replace("hl_ofs", "hl_ofs")
    elif "hl_left_out" in key:
        prop_name = key.replace("hl_left_out", "hl_left_out")
    elif "hl_left_in" in key:
        prop_name = key.replace("hl_left_in", "hl_left_in")
    elif "hl_right_in" in key:
        prop_name = key.replace("hl_right_in", "hl_right_in")
    elif "hl_right_out" in key:
        prop_name = key.replace("hl_right_out", "hl_right_out")
    elif "hl_cnt" in key:
        prop_name = key.replace("hl_cnt", "hl_cnt")
    elif "hl_cut" in key:
        prop_name = key.replace("hl_cut", "hl_cut")
    elif "hl_prim" in key:
        prop_name = key.replace("hl_prim", "hl_prim")
    elif "hl_sec" in key:
        prop_name = key.replace("hl_sec", "hl_sec")
    elif "hl_y" in key:
        prop_name = key.replace("hl_y", "hl_y")
    elif "boss_cnt" in key:
        prop_name = key.replace("boss_cnt", "boss_cnt")
    elif "boss_hgt" in key:
        prop_name = key.replace("boss_hgt", "boss_hgt")
    elif "boss_diam" in key:
        prop_name = key.replace("boss_diam", "boss_diam")
    elif "boss_pos" in key:
        prop_name = key.replace("boss_pos", "boss_pos")
    elif "supp_cnt" in key:
        prop_name = key.replace("supp_cnt", "supp_cnt")
    elif "supp_hgt" in key:
        prop_name = key.replace("supp_hgt", "supp_hgt")
    elif "supp_diam" in key:
        prop_name = key.replace("supp_diam", "supp_diam")
    elif "supp_pos" in key:
        prop_name = key.replace("supp_pos", "supp_pos")
    elif "mnt_cnt" in key:
        prop_name = key.replace("mnt_cnt", "mnt_cnt")
    elif "mnt_diam" in key:
        prop_name = key.replace
