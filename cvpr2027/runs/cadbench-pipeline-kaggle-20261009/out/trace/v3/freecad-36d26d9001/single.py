import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
base_plate_length = 406.4
base_plate_width = 101.6
base_plate_thickness = 4.76
number_mounting_holes = 6
mounting_hole_diameter = 8.0
mounting_hole_column_spacing = 355.6
mounting_hole_outer_row_spacing = 63.5

# Edit Parameters (Target)
number_hooks = 4
hook_spacing = 101.6
first_hook_origin_x = -152.4
hook_thickness = 25.4
hook_inner_radius = 19.05
hook_outer_radius = 25.4
hook_arc_angle = 160.0 # degrees
hook_arc_center_x = -27.78
hook_arc_center_y = -44.2
hook_main_length = 95.0
hook_upper_arm_length = 63.5
hook_upper_arm_angle = 45.0 # degrees
hook_bottom_arm_length = 38.1

# --- Helper Functions ---

def create_sketch(body, name, plane_name, offset=0.0):
    """Creates a Sketcher::SketchObject attached to a specific plane."""
    plane = App.ActiveDocument.getObject(plane_name)
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane
    sketch.MapMode = "FlatFace"
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    return sketch

def add_line(sketch, p1, p2):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sketch, center, radius):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_constraint(sketch, constraint_type, *args):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, *args))

def add_constraint_point(sketch, constraint_type, index, point_type, value):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, index, point_type, value))

def add_constraint_line(sketch, constraint_type, index, line_type, value):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, index, line_type, value))

def add_constraint_arc(sketch, constraint_type, index, arc_type, value):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, index, arc_type, value))

def add_constraint_angle(sketch, constraint_type, index1, index2, value):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, index1, index2, value))

def add_constraint_coincident(sketch, index1, index2):
    sketch.addConstraint(Sketcher.Constraint("Coincident", index1, index2))

def add_constraint_perpendicular(sketch, index1, index2):
    sketch.addConstraint(Sketcher.Constraint("Perpendicular", index1, index2))

def add_constraint_tangent(sketch, index1, index2):
    sketch.addConstraint(Sketcher.Constraint("Tangent", index1, index2))

def add_constraint_horizontal(sketch, index):
    sketch.addConstraint(Sketcher.Constraint("Horizontal", index))

def add_constraint_vertical(sketch, index):
    sketch.addConstraint(Sketcher.Constraint("Vertical", index))

def add_constraint_fixedpoint(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", index, axis, value))

def add_constraint_fixedline(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine", index, axis, value))

def add_constraint_fixedcircle(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle", index, axis, value))

def add_constraint_fixedarc(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc", index, axis, value))

def add_constraint_fixedpoint2d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint2D", index, axis, value))

def add_constraint_fixedline2d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine2D", index, axis, value))

def add_constraint_fixedcircle2d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle2D", index, axis, value))

def add_constraint_fixedarc2d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc2D", index, axis, value))

def add_constraint_fixedpoint3d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint3D", index, axis, value))

def add_constraint_fixedline3d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine3D", index, axis, value))

def add_constraint_fixedcircle3d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle3D", index, axis, value))

def add_constraint_fixedarc3d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc3D", index, axis, value))

def add_constraint_fixedpoint4d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint4D", index, axis, value))

def add_constraint_fixedline4d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine4D", index, axis, value))

def add_constraint_fixedcircle4d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle4D", index, axis, value))

def add_constraint_fixedarc4d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc4D", index, axis, value))

def add_constraint_fixedpoint5d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint5D", index, axis, value))

def add_constraint_fixedline5d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine5D", index, axis, value))

def add_constraint_fixedcircle5d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle5D", index, axis, value))

def add_constraint_fixedarc5d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc5D", index, axis, value))

def add_constraint_fixedpoint6d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint6D", index, axis, value))

def add_constraint_fixedline6d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine6D", index, axis, value))

def add_constraint_fixedcircle6d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle6D", index, axis, value))

def add_constraint_fixedarc6d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc6D", index, axis, value))

def add_constraint_fixedpoint7d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint7D", index, axis, value))

def add_constraint_fixedline7d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine7D", index, axis, value))

def add_constraint_fixedcircle7d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle7D", index, axis, value))

def add_constraint_fixedarc7d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc7D", index, axis, value))

def add_constraint_fixedpoint8d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint8D", index, axis, value))

def add_constraint_fixedline8d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine8D", index, axis, value))

def add_constraint_fixedcircle8d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle8D", index, axis, value))

def add_constraint_fixedarc8d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc8D", index, axis, value))

def add_constraint_fixedpoint9d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint9D", index, axis, value))

def add_constraint_fixedline9d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine9D", index, axis, value))

def add_constraint_fixedcircle9d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle9D", index, axis, value))

def add_constraint_fixedarc9d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc9D", index, axis, value))

def add_constraint_fixedpoint10d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint10D", index, axis, value))

def add_constraint_fixedline10d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine10D", index, axis, value))

def add_constraint_fixedcircle10d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle10D", index, axis, value))

def add_constraint_fixedarc10d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc10D", index, axis, value))

def add_constraint_fixedpoint11d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint11D", index, axis, value))

def add_constraint_fixedline11d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine11D", index, axis, value))

def add_constraint_fixedcircle11d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle11D", index, axis, value))

def add_constraint_fixedarc11d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc11D", index, axis, value))

def add_constraint_fixedpoint12d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint12D", index, axis, value))

def add_constraint_fixedline12d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine12D", index, axis, value))

def add_constraint_fixedcircle12d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle12D", index, axis, value))

def add_constraint_fixedarc12d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc12D", index, axis, value))

def add_constraint_fixedpoint13d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint13D", index, axis, value))

def add_constraint_fixedline13d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine13D", index, axis, value))

def add_constraint_fixedcircle13d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle13D", index, axis, value))

def add_constraint_fixedarc13d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc13D", index, axis, value))

def add_constraint_fixedpoint14d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint14D", index, axis, value))

def add_constraint_fixedline14d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine14D", index, axis, value))

def add_constraint_fixedcircle14d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle14D", index, axis, value))

def add_constraint_fixedarc14d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc14D", index, axis, value))

def add_constraint_fixedpoint15d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint15D", index, axis, value))

def add_constraint_fixedline15d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine15D", index, axis, value))

def add_constraint_fixedcircle15d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle15D", index, axis, value))

def add_constraint_fixedarc15d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc15D", index, axis, value))

def add_constraint_fixedpoint16d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint16D", index, axis, value))

def add_constraint_fixedline16d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine16D", index, axis, value))

def add_constraint_fixedcircle16d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle16D", index, axis, value))

def add_constraint_fixedarc16d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc16D", index, axis, value))

def add_constraint_fixedpoint17d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint17D", index, axis, value))

def add_constraint_fixedline17d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine17D", index, axis, value))

def add_constraint_fixedcircle17d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle17D", index, axis, value))

def add_constraint_fixedarc17d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc17D", index, axis, value))

def add_constraint_fixedpoint18d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint18D", index, axis, value))

def add_constraint_fixedline18d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine18D", index, axis, value))

def add_constraint_fixedcircle18d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle18D", index, axis, value))

def add_constraint_fixedarc18d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc18D", index, axis, value))

def add_constraint_fixedpoint19d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint19D", index, axis, value))

def add_constraint_fixedline19d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine19D", index, axis, value))

def add_constraint_fixedcircle19d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle19D", index, axis, value))

def add_constraint_fixedarc19d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc19D", index, axis, value))

def add_constraint_fixedpoint20d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint20D", index, axis, value))

def add_constraint_fixedline20d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine20D", index, axis, value))

def add_constraint_fixedcircle20d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle20D", index, axis, value))

def add_constraint_fixedarc20d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc20D", index, axis, value))

def add_constraint_fixedpoint21d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint21D", index, axis, value))

def add_constraint_fixedline21d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine21D", index, axis, value))

def add_constraint_fixedcircle21d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle21D", index, axis, value))

def add_constraint_fixedarc
