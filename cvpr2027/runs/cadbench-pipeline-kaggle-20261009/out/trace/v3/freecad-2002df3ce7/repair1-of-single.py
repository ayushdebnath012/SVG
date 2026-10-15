import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# All dimensions in mm, angles in degrees
params = {
    "plate_thickness": 8.00,
    "base_sketch_plane_rotation_angle": 90.0,
    "large_outer_rectangle_width": 280.00,
    "large_outer_rectangle_height": 447.00,
    "large_outer_rectangle_center_y": -51.00,
    "middle_outer_rectangle_width": 144.00,
    "middle_outer_rectangle_height": 64.00,
    "middle_outer_rectangle_center_y": 204.50,
    "small_outer_rectangle_width": 52.00,
    "small_outer_rectangle_height": 38.00,
    "small_outer_rectangle_center_y": 255.50,
    "rectangular_section_corner_chamfer_fillet_radius": 10.00,
    "large_outer_rectangle_lower_corner_chamfer_flat_width": 200.00,
    "large_outer_rectangle_upper_corner_chamfer_setback": 17.00,
    "large_outer_rectangle_side_trapezoidal_recess_depth": 17.00,
    "large_outer_rectangle_side_trapezoidal_recess_01_center_y": -149.50,
    "large_outer_rectangle_side_trapezoidal_recess_01_outer_height": 98.28,
    "large_outer_rectangle_side_trapezoidal_recess_01_inner_flat_height": 47.72,
    "large_outer_rectangle_side_trapezoidal_recess_02_center_y": 25.50,
    "large_outer_rectangle_side_trapezoidal_recess_02_outer_height": 148.28,
    "large_outer_rectangle_side_trapezoidal_recess_02_inner_flat_height": 97.72,
    "truss_layout_symmetry_axis_x": 0.00,
    "truss_cutout_transition_radius": 3.00,
    "truss_diagonal_angle_family_1": 27.3777028,
    "truss_diagonal_angle_family_2": 63.4349488,
    "truss_diagonal_angle_family_3": 28.8386275,
    "truss_diagonal_angle_family_4": 46.1233027,
    "truss_diagonal_angle_family_5": 165.8183429,
    "mounting_hole_diameter": 4.30,
    "center_bore_diameter": 7.00,
    "center_bore_axis_y": 264.50,
    "center_mounting_hole_pair_half_spacing": 18.00,
    "upper_inner_mounting_hole_pair_half_spacing": 62.00,
    "lower_inner_mounting_hole_pair_half_spacing": 61.76,
    "upper_inner_mounting_hole_pair_y": 226.50,
    "lower_inner_mounting_hole_pair_y": 165.50,
    "side_mounting_hole_axis_x": 136.00,
    "side_mounting_hole_row_1_y": 137.50,
    "side_mounting_hole_row_2_y": 113.50,
    "side_mounting_hole_row_3_y": -62.50,
    "side_mounting_hole_row_4_y": -86.50,
    "side_mounting_hole_row_5_y": -216.32,
    "side_mounting_hole_row_6_y": -240.32,
    "large_triangular_opening_pair_01_02_base_length": 141.90,
    "large_triangular_opening_pair_01_02_base_angle": 27.3777028,
    "large_triangular_opening_pair_01_positive_member_centroid_x": 86.75,
    "large_triangular_opening_pair_01_positive_member_centroid_y": -170.50,
    "large_triangular_opening_pair_02_positive_member_centroid_x": 24.25,
    "large_triangular_opening_pair_02_positive_member_centroid_y": -170.50,
    "large_triangular_opening_pair_03_positive_member_centroid_x": 86.78,
    "large_triangular_opening_pair_03_positive_member_centroid_y": 16.50,
    "large_triangular_opening_pair_03_base_length": 133.12,
    "large_triangular_opening_pair_03_base_angle": 28.8386275,
    "medium_triangular_opening_pair_01_02_base_length": 73.49,
    "medium_triangular_opening_pair_01_02_base_angle": 62.6222972,
    "medium_triangular_opening_pair_01_positive_member_centroid_x": 55.50,
    "medium_triangular_opening_pair_01_positive_member_centroid_y": -230.85,
    "medium_triangular_opening_pair_02_positive_member_centroid_x": 55.50,
    "medium_triangular_opening_pair_02_positive_member_centroid_y": -110.15,
    "medium_triangular_opening_pair_03_center_x": 30.11,
    "medium_triangular_opening_pair_03_center_y": -7.95,
    "medium_triangular_opening_pair_03_envelope_width": 36.23,
    "medium_triangular_opening_pair_03_envelope_height": 66.89,
    "right_triangular_opening_pair_base_length": 73.30,
    "right_triangular_opening_pair_base_angle": 61.1613725,
    "right_triangular_opening_01_centroid_x": 55.50,
    "right_triangular_opening_01_centroid_y": -40.31,
    "central_trapezoidal_opening_center_y": 96.50,
    "central_trapezoidal_opening_corner_radius": 10.00,
    "central_trapezoidal_opening_envelope_width": 184.30,
    "central_trapezoidal_opening_envelope_height": 118.00,
    "central_trapezoidal_opening_lower_flat_width": 108.61,
    "small_triangular_opening_centroid_x": 0.00,
    "small_triangular_opening_centroid_y": 186.39,
    "small_triangular_opening_base_length": 86.69,
    "small_triangular_opening_base_angle": 43.8766972,
    "chamfer_cut_right_triangular_opening_01_center_x": -32.55,
    "chamfer_cut_right_triangular_opening_01_center_y": 203.69,
    "chamfer_cut_right_triangular_opening_01_envelope_width": 38.90,
    "chamfer_cut_right_triangular_opening_01_envelope_height": 37.63,
    "chamfer_cut_right_triangular_opening_02_center_x": 32.55,
    "chamfer_cut_right_triangular_opening_02_center_y": 203.69,
    "chamfer_cut_right_triangular_opening_02_envelope_width": 38.90,
    "chamfer_cut_right_triangular_opening_02_envelope_height": 37.63,
    "right_triangular_opening_02_centroid_x": -55.50,
    "right_triangular_opening_02_centroid_y": -40.31
}

# --- Document Setup ---
doc = App.newDocument("TrussPlate")
doc.Label = "TrussPlate"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# Create Parameters (App::VarSet)
params_obj = body.newObject("App::VarSet", "Parameters")
for name, value in params.items():
    prop_type = "App::PropertyLength" if isinstance(value, (int, float)) else "App::PropertyInteger"
    params_obj.addProperty(prop_type, name, "Dimensions", name)
    params_obj.setValue(name, value)

# --- Helper Functions ---

def get_sketch_object(name):
    return body.newObject("Sketcher::SketchObject", name)

def add_line(sketch, p1, p2, visible=True):
    sketch.addGeometry(Part.LineSegment(p1, p2), visible)

def add_circle(sketch, center, radius, visible=True):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), visible)

def add_constraint(sketch, constraint_type, obj1, idx1, obj2, idx2, value=None):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj1, idx1, obj2, idx2, value))

def add_constraint_point(sketch, constraint_type, obj, idx, value=None):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, value))

def add_constraint_point_value(sketch, constraint_type, obj, idx, value):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, value))

def add_constraint_point_value_expr(sketch, constraint_type, obj, idx, expr):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr))

def add_constraint_point_value_expr2(sketch, constraint_type, obj, idx, expr1, expr2):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2))

def add_constraint_point_value_expr3(sketch, constraint_type, obj, idx, expr1, expr2, expr3):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3))

def add_constraint_point_value_expr4(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4))

def add_constraint_point_value_expr5(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5))

def add_constraint_point_value_expr6(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6))

def add_constraint_point_value_expr7(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7))

def add_constraint_point_value_expr8(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8))

def add_constraint_point_value_expr9(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9))

def add_constraint_point_value_expr10(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10))

def add_constraint_point_value_expr11(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11))

def add_constraint_point_value_expr12(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12))

def add_constraint_point_value_expr13(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13))

def add_constraint_point_value_expr14(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14))

def add_constraint_point_value_expr15(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15))

def add_constraint_point_value_expr16(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16))

def add_constraint_point_value_expr17(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17))

def add_constraint_point_value_expr18(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18))

def add_constraint_point_value_expr19(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19))

def add_constraint_point_value_expr20(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20))

def add_constraint_point_value_expr21(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21))

def add_constraint_point_value_expr22(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22))

def add_constraint_point_value_expr23(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23))

def add_constraint_point_value_expr24(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24))

def add_constraint_point_value_expr25(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25))

def add_constraint_point_value_expr26(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26))

def add_constraint_point_value_expr27(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27))

def add_constraint_point_value_expr28(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28))

def add_constraint_point_value_expr29(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29))

def add_constraint_point_value_expr30(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30))

def add_constraint_point_value_expr31(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31))

def add_constraint_point_value_expr32(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32))

def add_constraint_point_value_expr33(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32, expr33):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32, expr33))

def add_constraint_point_value_expr34(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32, expr33, expr34):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32, expr33, expr34))

def add_constraint_point_value_expr35(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32, expr33, expr34, expr35):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26, expr27, expr28, expr29, expr30, expr31, expr32, expr33, expr34, expr35))

def add_constraint_point_value_expr36(sketch, constraint_type, obj, idx, expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8, expr9, expr10, expr11, expr12, expr13, expr14, expr15, expr16, expr17, expr18, expr19, expr20, expr21, expr22, expr23, expr24, expr25, expr26,
