import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
STRAP_THICKNESS = 2.78
STRAP_WIDTH = 19.05
UPPER_TRANSITION_INNER_RADIUS = 2.78
UPPER_STRAP_PROFILE_HEIGHT = 34.93
UPPER_SIDE_LEG_STRAIGHT_LENGTH = 22.23
TOP_FLAT_WIDTH = 14.78
UPPER_TRANSITION_TANGENT_ANGLE = 67.68612906 # degrees
STRAP_CONNECTION_OVERLAP = 19.06
PIVOT_HOLE_DIAMETER = 11.12

# Edit Parameters
LOWER_LOOP_INNER_RADIUS = 10.32
LOWER_LOOP_STRAIGHT_LEG_LENGTH = 24.61
ROD_CHANNEL_DIAMETER = 6.34
ROD_CHANNEL_AXIS_HEIGHT = 16.67

# --- Helper Functions ---

def create_sketch_on_plane(body, plane_name, offset=0.0):
    """Creates a Sketcher::SketchObject on a specific plane with optional Z offset."""
    # Get the plane object (XY, XZ, YZ)
    plane_obj = None
    for obj in doc.Objects:
        if obj.Name == plane_name:
            plane_obj = obj
            break
    
    if not plane_obj:
        raise RuntimeError(f"Plane {plane_name} not found.")

    sketch = body.newObject("Sketcher::SketchObject", f"Sketch_{plane_name}")
    sketch.Plane = plane_obj
    sketch.MapMode = "FlatFace"
    sketch.AttachmentOffset = App.Vector(0, 0, offset)
    sketch.Constrain = True
    sketch.Locked = False
    return sketch

def add_line(sketch, p1, p2, locked=False):
    sketch.addGeometry(Part.LineSegment(p1, p2), locked)

def add_circle(sketch, center, radius, locked=False):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), locked)

def add_constraint(sketch, constraint_type, *args):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, *args))

def add_constraint_point(sketch, constraint_type, point_idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, point_idx, locked=locked))

def add_constraint_line(sketch, constraint_type, line_idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, line_idx, locked=locked))

def add_constraint_arc(sketch, constraint_type, arc_idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, arc_idx, locked=locked))

def add_constraint_angle(sketch, constraint_type, angle_deg, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, angle_deg, locked=locked))

def add_constraint_distance(sketch, constraint_type, dist, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, dist, locked=locked))

def add_constraint_radius(sketch, constraint_type, radius, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, radius, locked=locked))

def add_constraint_tangent(sketch, constraint_type, idx1, idx2, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx1, idx2, locked=locked))

def add_constraint_coincident(sketch, constraint_type, idx1, idx2, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx1, idx2, locked=locked))

def add_constraint_parallel(sketch, constraint_type, idx1, idx2, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx1, idx2, locked=locked))

def add_constraint_perpendicular(sketch, constraint_type, idx1, idx2, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx1, idx2, locked=locked))

def add_constraint_symmetry(sketch, constraint_type, idx1, idx2, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx1, idx2, locked=locked))

def add_constraint_horizontal(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_vertical(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint2(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint3(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint4(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint5(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint6(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint7(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint8(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint9(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint10(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint11(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint12(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint13(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint14(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint15(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint16(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint17(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint18(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint19(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint20(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint21(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint22(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint23(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint24(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint25(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint26(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint27(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint28(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint29(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint30(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint31(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint32(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint33(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint34(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint35(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint36(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint37(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint38(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint39(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint40(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint41(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint42(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint43(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint44(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint45(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint46(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint47(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint48(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint49(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint50(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint51(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint52(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint53(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint54(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint55(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint56(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint57(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint58(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint59(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint60(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint61(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint62(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint63(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint64(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint65(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint66(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint67(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint68(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint69(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint70(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint71(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint72(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint73(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint74(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint75(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint76(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint77(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint78(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint79(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint80(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint81(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint82(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint83(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint84(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint85(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint86(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint87(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint88(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint89(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint90(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint91(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint92(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint93(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint94(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint95(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint96(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint97(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint98(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint99(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint100(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint101(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint102(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint103(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint104(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint105(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint106(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint107(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint108(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint109(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint110(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint111(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint112(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint113(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint114(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint115(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint116(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint117(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint118(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint119(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint120(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint121(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint122(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint123(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint124(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint125(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint126(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint127(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint128(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint129(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint130(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint131(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint132(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint133(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint134(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint135(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint136(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint137(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint138(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint139(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint140(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint141(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint142(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint143(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint144(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint145(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint146(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint147(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint148(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint149(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint150(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint151(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint152(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint153(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint154(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint155(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint156(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint157(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint158(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint159(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint160(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint161(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint162(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint163(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint164(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint165(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint166(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint167(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint168(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint169(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint170(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint171(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint172(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint173(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint174(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint175(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint176(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint177(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint178(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint179(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint180(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint181(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, idx, locked=locked))

def add_constraint_fixedpoint182(sketch, constraint_type, idx, locked=False):
    sketch.addConstraint(Sketcher.Constraint
