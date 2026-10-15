import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Base Parameters
BIG_END_ARC_RADIUS = 35.0
SMALL_END_ARC_RADIUS = 27.5
ROD_BODY_WIDTH = 25.0
LARGE_OPENING_CENTER_SPACING = 200.0
FORK_TRANSITION_SEGMENT_LENGTH = 22.0
ROD_BODY_THICKNESS = 12.0

# Edit Parameters (Target)
PIN_HOLE_DIAMETER = 6.0
FORK_ARM_WIDTH = 12.0
FORK_ARM_STRAIGHT_LENGTH = 9.0
FORK_ARM_AXIAL_THICKNESS = 15.0
SLOT_END_CENTER_SPACING = 100.0
SLOT_WIDTH = 14.0
SLOT_POCKET_DEPTH_PER_FACE = 3.0
SLOT_CENTER_X_OFFSET_FROM_SMALL_END_ARC_CENTER = 90.0

def create_sketch_on_plane(body, plane_name, offset_z=0.0):
    """Creates a Sketcher::SketchObject on a specific plane with optional Z offset."""
    plane = App.ActiveDocument.getObject(plane_name)
    sketch = body.newObject("Sketcher::SketchObject", f"Sketch_{plane_name}")
    sketch.Plane = plane
    sketch.MapMode = "FlatFace"
    sketch.AttachmentOffset = App.Vector(0, 0, offset_z)
    return sketch

def add_line(sketch, p1, p2):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sketch, center, radius):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_constraint(sketch, constraint_type, *args):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, *args))

def add_constraint_point(sketch, constraint_type, point_idx, *args):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, point_idx, *args))

def add_constraint_line(sketch, constraint_type, line_idx, *args):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, line_idx, *args))

def add_constraint_arc(sketch, constraint_type, arc_idx, *args):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, arc_idx, *args))

def add_constraint_distance(sketch, constraint_type, obj1, idx1, obj2, idx2, value):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj1, idx1, obj2, idx2, value))

def add_constraint_symmetry(sketch, obj1, idx1, obj2, idx2, axis_obj, axis_idx):
    sketch.addConstraint(Sketcher.Constraint("Symmetry", obj1, idx1, obj2, idx2, axis_obj, axis_idx))

def add_constraint_perpendicular(sketch, obj1, idx1, obj2, idx2):
    sketch.addConstraint(Sketcher.Constraint("Perpendicular", obj1, idx1, obj2, idx2))

def add_constraint_horizontal(sketch, obj_idx):
    sketch.addConstraint(Sketcher.Constraint("Horizontal", obj_idx))

def add_constraint_vertical(sketch, obj_idx):
    sketch.addConstraint(Sketcher.Constraint("Vertical", obj_idx))

def add_constraint_tangent(sketch, obj1, idx1, obj2, idx2):
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj1, idx1, obj2, idx2))

def add_constraint_coincident(sketch, obj1, idx1, obj2, idx2):
    sketch.addConstraint(Sketcher.Constraint("Coincident", obj1, idx1, obj2, idx2))

def add_constraint_fixed_point(sketch, obj_idx, x, y):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y))

def add_constraint_fixed_point_xy(sketch, obj_idx, x, y):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y))

def add_constraint_fixed_point_x(sketch, obj_idx, x):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, 0))

def add_constraint_fixed_point_y(sketch, obj_idx, y):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, 0, y))

def add_constraint_fixed_point_z(sketch, obj_idx, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, 0, 0, z))

def add_constraint_fixed_point_xyz(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xy_z(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch2(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch3(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch4(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch5(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch6(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch7(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch8(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch9(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch10(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch11(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch12(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch13(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch14(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch15(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch16(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch17(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch18(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch19(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch20(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch21(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch22(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch23(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch24(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch25(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch26(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch27(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch28(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch29(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch30(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch31(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch32(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch33(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch34(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch35(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch36(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch37(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch38(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch39(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch40(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch41(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch42(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch43(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch44(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch45(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch46(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch47(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch48(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch49(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch50(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch51(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch52(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch53(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch54(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch55(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch56(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch57(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch58(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch59(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch60(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch61(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch62(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch63(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch64(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch65(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch66(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch67(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch68(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch69(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch70(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch71(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch72(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch73(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch74(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch75(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch76(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch77(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch78(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch79(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch80(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch81(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch82(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch83(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch84(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch85(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch86(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch87(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch88(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch89(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch90(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch91(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch92(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch93(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch94(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch95(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch96(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch97(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch98(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch99(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch100(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch101(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch102(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch103(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch104(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch105(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch106(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch107(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch108(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch109(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch110(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch111(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch112(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch113(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch114(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch115(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch116(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch117(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch118(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch119(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch120(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch121(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch122(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch123(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch124(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch125(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch126(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch127(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch128(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch129(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch130(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch131(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch132(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch133(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch134(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch135(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch136(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch137(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch138(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch139(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch140(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch141(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch142(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch143(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch144(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch145(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch146(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch147(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch148(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch149(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch150(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch151(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch152(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx, x, y, z))

def add_constraint_fixed_point_xyz_sketch153(sketch, obj_idx, x, y, z):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj_idx,
