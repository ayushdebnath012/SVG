import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration and Parameters ---

# Base Part Parameters
P_base_core_midplane = 0.0
P_base_collar_len = 3.0
P_base_shoulder_len = 6.0
P_base_taper_start_len = 13.25
P_base_end_len = 19.25
P_base_plate_thick = 6.0
P_base_prim_arc = 7.0
P_base_side_arc = 11.56
P_base_large_fillet = 1.5
P_base_small_fillet = 0.8
P_base_side_cx = 20.48
P_base_side_cy = 0.08
P_base_left_hook_x = 8.27
P_base_left_hook_y = 2.79
P_base_left_hook_len = 1.0
P_base_left_trans_x = 0.75
P_base_left_trans_drop_o = 0.75
P_base_left_trans_drop_i = 1.05
P_base_frame_x = 10.0
P_base_frame_y = 5.25
P_base_frame_w = 17.75
P_base_frame_h = 9.0
P_base_frame_step = 0.28
P_base_link_cham1 = 0.86
P_base_link_len = 1.0
P_base_link_cham2 = 0.25
P_base_tab_x = 6.39
P_base_tab_w = 2.90
P_base_tab_y = 2.85

# Base Dimensions
D_base_support_out = 14.0
D_base_shoulder_out = 10.0
D_base_taper_inner = 8.0
D_base_taper_outer = 7.0
D_base_end_out = 6.4

# Edit Instruction Parameters
P_edit_lower_len = 10.5
P_edit_lower_rev = 360.0
P_edit_lower_z = -7.25
P_edit_lower_y_apex = -4.25
P_edit_lower_y_shoulder = -6.65
P_edit_lower_y_taper = -7.0
P_edit_upper_span_in = 5.75
P_edit_upper_span_trans = 7.75
P_edit_upper_span_out = 9.25
P_edit_upper_top = 14.25
P_edit_upper_shoulder = 11.88
P_edit_upper_y = 8.5
P_edit_cut_arc_r = 5.78
P_edit_cut_depth = 17.75
P_edit_cut_cx = 8.47
P_edit_cut_cw = 3.0
P_edit_cut_lower = 13.41
P_edit_cut_top = 14.91
P_edit_hous_arc_r = 3.38
P_edit_hous_depth = 0.75
P_edit_hous_cy = 8.5
P_edit_hous_bot = 4.20
P_edit_web_thick = 1.0
P_edit_web_off = -0.5
P_edit_web_root_w = 3.0
P_edit_web_bot = -6.70
P_edit_web_span = 8.0
P_edit_web_shoulder = -3.70
P_edit_web_top = -3.0
P_edit_web_seed = 0.0
P_edit_web_count = 4

def create_sketch(doc, body, plane_obj, name):
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.Plane = plane_obj
    sk.MapMode = "FlatFace"
    sk.ConstrainToPlane = True
    sk.ConstrainToAxes = False
    return sk

def create_pad(body, sketch, length, name="Pad"):
    p = body.newObject("PartDesign::Pad", name)
    p.Profile = sketch
    p.Length = length
    return p

def create_pocket(body, sketch, length, name="Pocket"):
    p = body.newObject("PartDesign::Pocket", name)
    p.Profile = sketch
    p.Length = length
    return p

def get_midplane(doc, axis="Z"):
    return doc.getObject(f"{axis}_Axis")

def get_plane(doc, name):
    return doc.getObject(name)

def create_solid_from_extrude(body, sketch, direction, length, is_cut=False, name="Feature"):
    feat = None
    if is_cut:
        feat = body.newObject("PartDesign::Pocket", name)
        feat.Profile = sketch
        feat.Length = length
    else:
        feat = body.newObject("PartDesign::Pad", name)
        feat.Profile = sketch
        feat.Length = length
    return feat

# --- Base Part Construction ---

doc = App.newDocument("Part")

# Get Planes
XY = get_plane(doc, "XY_Plane")
YZ = get_plane(doc, "YZ_Plane")
ZX = get_plane(doc, "Z_Axis") # Z Axis is origin, use YZ for sketch? No, Z_Axis is line. Use YZ_Plane.
# Actually, standard is XY, XZ, YZ.
# Core Axis is Z. Plate is XZ (Horizontal is X, Up is Y). 
# Wait, prompt says: "transverse plate's horizontal direction is -Z". 
# "X for the longitudinal core direction". "Y for upward".
# So Core is along Z? No, "longitudinal core direction" usually Z.
# "transverse plate's horizontal direction is -Z". This implies the plate lies in the X-Y plane? 
# If horizontal is -Z, and Up is Y, then the plate lies in the Y-Z plane? 
# Let's re-read carefully.
# "X for the longitudinal core direction". -> Core is along X axis.
# "Y for upward". -> Y is Up.
# "transverse plate's horizontal direction is -Z". -> Plate horizontal is -Z.
# "transverse plate's datum origin is on the core axis".
# So Plate lies in the X-Y plane? No. If horizontal is -Z and Up is Y, the plane is Y-Z.
# BUT "X for the longitudinal core direction".
# If Core is X, and Plate horizontal is -Z, then Plate is perpendicular to Core. Correct.
# So Plate is in the Y-Z plane.
# Sketch Plane for Core Profile: X-Y plane (YZ in FreeCAD terms? No, X-Y is XY_Plane).
# Sketch Plane for Plate: Y-Z plane (XZ_Plane).
# Let's verify FreeCAD planes.
# XY_Plane: X, Y
# XZ_Plane: X, Z
# YZ_Plane: Y, Z
# Core Profile (Side view): Needs X (longitudinal) and Y (up). Use XY_Plane.
# Plate Profile (Top view): Needs Y (up) and Z (horizontal). Use YZ_Plane.

# Parameters Object
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "base_collar_len", "Base", "Half length of collar")
params.base_collar_len = P_base_collar_len
params.addProperty("App::PropertyLength", "base_shoulder_len", "Base", "Half length of shoulder")
params.base_shoulder_len = P_base_shoulder_len
params.addProperty("App::PropertyLength", "base_taper_start_len", "Base", "Half length to taper start")
params.base_taper_start_len = P_base_taper_start_len
params.addProperty("App::PropertyLength", "base_end_len", "Base", "Half length to end support")
params.base_end_len = P_base_end_len
params.addProperty("App::PropertyLength", "base_plate_thick", "Base", "Thickness of plate")
params.base_plate_thick = P_base_plate_thick
params.addProperty("App::PropertyLength", "base_prim_arc", "Base", "Primary contour radius")
params.base_prim_arc = P_base_prim_arc
params.addProperty("App::PropertyLength", "base_side_arc", "Base", "Side contour radius")
params.base_side_arc = P_base_side_arc
params.addProperty("App::PropertyLength", "base_large_fillet", "Base", "Large transition fillet")
params.base_large_fillet = P_base_large_fillet
params.addProperty("App::PropertyLength", "base_small_fillet", "Base", "Small transition fillet")
params.base_small_fillet = P_base_small_fillet
params.addProperty("App::PropertyLength", "base_side_cx", "Base", "Side arc center rightward")
params.base_side_cx = P_base_side_cx
params.addProperty("App::PropertyLength", "base_side_cy", "Base", "Side arc center upward")
params.base_side_cy = P_base_side_cy
params.addProperty("App::PropertyLength", "base_left_hook_x", "Base", "Left hook leftward")
params.base_left_hook_x = P_base_left_hook_x
params.addProperty("App::PropertyLength", "base_left_hook_y", "Base", "Left hook upward")
params.base_left_hook_y = P_base_left_hook_y
params.addProperty("App::PropertyLength", "base_left_hook_len", "Base", "Left hook tangent link")
params.base_left_hook_len = P_base_left_hook_len
params.addProperty("App::PropertyLength", "base_left_trans_x", "Base", "Left transition inset")
params.base_left_trans_x = P_base_left_trans_x
params.addProperty("App::PropertyLength", "base_left_trans_drop_o", "Base", "Left transition outer drop")
params.base_left_trans_drop_o = P_base_left_trans_drop_o
params.addProperty("App::PropertyLength", "base_left_trans_drop_i", "Base", "Left transition inner drop")
params.base_left_trans_drop_i = P_base_left_trans_drop_i
params.addProperty("App::PropertyLength", "base_frame_x", "Base", "Frame leftward")
params.base_frame_x = P_base_frame_x
params.addProperty("App::PropertyLength", "base_frame_y", "Base", "Frame base upward")
params.base_frame_y = P_base_frame_y
params.addProperty("App::PropertyLength", "base_frame_w", "Base", "Frame width")
params.base_frame_w = P_base_frame_w
params.addProperty("App::PropertyLength", "base_frame_h", "Base", "Frame height")
params.base_frame_h = P_base_frame_h
params.addProperty("App::PropertyLength", "base_frame_step", "Base", "Frame lower step drop")
params.base_frame_step = P_base_frame_step
params.addProperty("App::PropertyLength", "base_link_cham1", "Base", "Right link first chamfer")
params.base_link_cham1 = P_base_link_cham1
params.addProperty("App::PropertyLength", "base_link_len", "Base", "Right link horizontal")
params.base_link_len = P_base_link_len
params.addProperty("App::PropertyLength", "base_link_cham2", "Base", "Right link second chamfer")
params.base_link_cham2 = P_base_link_cham2
params.addProperty("App::PropertyLength", "base_tab_x", "Base", "Right tab inner rightward")
params.base_tab_x = P_base_tab_x
params.addProperty("App::PropertyLength", "base_tab_w", "Base", "Right tab horizontal")
params.base_tab_w = P_base_tab_w
params.addProperty("App::PropertyLength", "base_tab_y", "Base", "Right tab downward")
params.base_tab_y = P_base_tab_y

# Diameters
params.addProperty("App::PropertyLength", "D_support_out", "Base", "Support outer diameter")
params.D_support_out = P_base_support_out
params.addProperty("App::PropertyLength", "D_shoulder_out", "Base", "Shoulder outer diameter")
params.D_shoulder_out = P_base_shoulder_out
params.addProperty("App::PropertyLength", "D_taper_inner", "Base", "Tapered inner diameter")
params.D_taper_inner = P_base_taper_inner
params.addProperty("App::PropertyLength", "D_taper_outer", "Base", "Tapered outer diameter")
params.D_taper_outer = P_base_taper_outer
params.addProperty("App::PropertyLength", "D_end_out", "Base", "End support outer diameter")
params.D_end_out = P_base_end_out

body = doc.addObject("PartDesign::Body", "Body")

# --- Core Profile Sketch (XY_Plane) ---
sk_core = create_sketch(doc, body, XY, "CoreSketch")
sk_core.Plane = (XY, ["X", "Y"]) # X, Y are axes of XY_Plane

# Symmetric profile about X=0 (midplane). X is longitudinal.
# Stations: 
# -0 to -core_collar: D_support_out
# -core_collar to -core_collar - core_shoulder: D_shoulder_out
# -core_shoulder to -core_shoulder - core_taper_start: Taper from D_shoulder to D_taper_outer
# -core_taper_start to 0: Taper from D_taper_outer to D_taper_inner
# 0 to core_collar: D_taper_inner
# core_collar to core_collar + core_shoulder: D_shoulder_out
# core_collar + core_shoulder to core_collar + core_shoulder + core_taper_start: Taper from D_shoulder to D_taper_outer
# ... and so on.

# Points (X, Y). Y = Radius.
# Left Side (Negative X):
# 1. x = -P_base_collar_len, y = P_base_support_out / 2
# 2. x = -P_base_collar_len - P_base_shoulder_len, y = P_base_shoulder_out / 2
# 3. x = -P_base_collar_len - P_base_shoulder_len - P_base_taper_start_len, y = P_base_taper_outer / 2
# 4. x = 0, y = P_base_taper_inner / 2
# Right Side (Positive X): Mirror of Left.

# Let's add lines and circles/arcs.
# Actually, using LineSegments is safer for complex tangents, but we can use Circle + Lines + Fillets.
# The prompt says "taper ... linearly".
# Let's construct the profile with lines and then fillet transitions? 
# "abrupt shoulder diameter step", "taper to the inner tapered diameter", "abrupt step to the end-support diameter".
# So: Vertical line, Horizontal line? No, "shoulder diameter step" usually means a step down/up.
# "abrupt shoulder diameter step": From D_support_out to D_shoulder_out. This is a vertical drop in radius? 
# Wait, if X is longitudinal, Y is radius. 
# Profile: 
# X=0, Y=D_end/2. 
# X=-core_collar, Y=D_support/2. (Vertical step up? No, D_support > D_shoulder > D_end).
# Let's trace from Center (X=0) outwards to Left (-X).
# X=0: Y = D_end/2 (End Support)
# X = -core_collar: Y = D_support/2 (Collar). Step Up.
# X = -core_collar - core_shoulder: Y = D_shoulder/2 (Shoulder). Step Down.
# X = -core_collar - core_shoulder - core_taper_start: Y = D_taper_outer/2 (Taper Start). Linear Taper Down.
# X = 0: Y = D_taper_inner/2 (Taper End). Linear Taper Up? 
# Wait, "taper to the inner tapered diameter at the shoulder station". 
# Shoulder station is at -core_collar - core_shoulder. 
# "longer taper to the outer tapered diameter at the taper-start station". 
# Taper start is further out. 
# So from Shoulder (D_shoulder) to TaperStart (D_taper_outer). 
# Then from TaperStart (D_taper_outer) to Center (D_taper_inner). 
# Then from Center (D_taper_inner) to Collar (D_support). 
# Then from Collar (D_support) to End (D_end).

# Let's define the path.
# Start at X = - (core_collar + core_shoulder + core_taper_start)
# y = D_taper_outer / 2
# Line to X = - (core_collar + core_shoulder)
# y = D_shoulder / 2
# Line to X = -core_collar
# y = D_support / 2
# Line to X = 0
# y = D_end / 2
# Mirror to Right.

# We will create a sketch using LineSegments.
# Add Points? No, just LineSegments.
# To make it closed, we need to close it.
# Sketcher doesn't have a direct "close" command, but we can add a line back to start.

def add_line(sketch, p1, p2, close=False):
    sk.addGeometry(Part.LineSegment(p1, p2), close)

# Left Side Points (X, Y)
p1 = App.Vector(- (P_base_collar_len + P_base_shoulder_len + P_base_taper_start_len), P_base_taper_outer / 2)
p2 = App.Vector(- (P_base_collar_len + P_base_shoulder_len), P_base_shoulder_out / 2)
p3 = App.Vector(- P_base_collar_len, P_base_support_out / 2)
p4 = App.Vector(0, P_base_end_out / 2)
# Mirror to Right
p5 = App.Vector(P_base_collar_len, P_base_support_out / 2)
p6 = App.Vector(P_base_collar_len + P_base_shoulder_len, P_base_shoulder_out / 2)
p7 = App.Vector(P_base_collar_len + P_base_shoulder_len + P_base_taper_start_len, P_base_taper_outer / 2)

# Add lines
# p7 -> p1 (Top edge)
add_line(sk_core, p7, p1)
# p1 -> p2 (Taper outer to shoulder)
add_line(sk_core, p1, p2)
# p2 -> p3 (Shoulder to collar)
add_line(sk_core, p
