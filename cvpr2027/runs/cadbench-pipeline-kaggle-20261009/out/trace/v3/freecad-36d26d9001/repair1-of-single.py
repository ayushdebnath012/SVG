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

def add_constraint_fixedarc21d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc21D", index, axis, value))

def add_constraint_fixedpoint22d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint22D", index, axis, value))

def add_constraint_fixedline22d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine22D", index, axis, value))

def add_constraint_fixedcircle22d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle22D", index, axis, value))

def add_constraint_fixedarc22d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc22D", index, axis, value))

def add_constraint_fixedpoint23d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint23D", index, axis, value))

def add_constraint_fixedline23d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine23D", index, axis, value))

def add_constraint_fixedcircle23d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle23D", index, axis, value))

def add_constraint_fixedarc23d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc23D", index, axis, value))

def add_constraint_fixedpoint24d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint24D", index, axis, value))

def add_constraint_fixedline24d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine24D", index, axis, value))

def add_constraint_fixedcircle24d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle24D", index, axis, value))

def add_constraint_fixedarc24d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc24D", index, axis, value))

def add_constraint_fixedpoint25d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint25D", index, axis, value))

def add_constraint_fixedline25d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine25D", index, axis, value))

def add_constraint_fixedcircle25d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle25D", index, axis, value))

def add_constraint_fixedarc25d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc25D", index, axis, value))

def add_constraint_fixedpoint26d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint26D", index, axis, value))

def add_constraint_fixedline26d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine26D", index, axis, value))

def add_constraint_fixedcircle26d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle26D", index, axis, value))

def add_constraint_fixedarc26d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc26D", index, axis, value))

def add_constraint_fixedpoint27d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint27D", index, axis, value))

def add_constraint_fixedline27d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine27D", index, axis, value))

def add_constraint_fixedcircle27d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle27D", index, axis, value))

def add_constraint_fixedarc27d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc27D", index, axis, value))

def add_constraint_fixedpoint28d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint28D", index, axis, value))

def add_constraint_fixedline28d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine28D", index, axis, value))

def add_constraint_fixedcircle28d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle28D", index, axis, value))

def add_constraint_fixedarc28d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc28D", index, axis, value))

def add_constraint_fixedpoint29d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint29D", index, axis, value))

def add_constraint_fixedline29d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine29D", index, axis, value))

def add_constraint_fixedcircle29d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle29D", index, axis, value))

def add_constraint_fixedarc29d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc29D", index, axis, value))

def add_constraint_fixedpoint30d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint30D", index, axis, value))

def add_constraint_fixedline30d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine30D", index, axis, value))

def add_constraint_fixedcircle30d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle30D", index, axis, value))

def add_constraint_fixedarc30d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc30D", index, axis, value))

def add_constraint_fixedpoint31d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint31D", index, axis, value))

def add_constraint_fixedline31d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine31D", index, axis, value))

def add_constraint_fixedcircle31d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle31D", index, axis, value))

def add_constraint_fixedarc31d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc31D", index, axis, value))

def add_constraint_fixedpoint32d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint32D", index, axis, value))

def add_constraint_fixedline32d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine32D", index, axis, value))

def add_constraint_fixedcircle32d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle32D", index, axis, value))

def add_constraint_fixedarc32d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc32D", index, axis, value))

def add_constraint_fixedpoint33d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint33D", index, axis, value))

def add_constraint_fixedline33d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine33D", index, axis, value))

def add_constraint_fixedcircle33d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle33D", index, axis, value))

def add_constraint_fixedarc33d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc33D", index, axis, value))

def add_constraint_fixedpoint34d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint34D", index, axis, value))

def add_constraint_fixedline34d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine34D", index, axis, value))

def add_constraint_fixedcircle34d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle34D", index, axis, value))

def add_constraint_fixedarc34d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc34D", index, axis, value))

def add_constraint_fixedpoint35d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint35D", index, axis, value))

def add_constraint_fixedline35d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine35D", index, axis, value))

def add_constraint_fixedcircle35d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle35D", index, axis, value))

def add_constraint_fixedarc35d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc35D", index, axis, value))

def add_constraint_fixedpoint36d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint36D", index, axis, value))

def add_constraint_fixedline36d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine36D", index, axis, value))

def add_constraint_fixedcircle36d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle36D", index, axis, value))

def add_constraint_fixedarc36d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc36D", index, axis, value))

def add_constraint_fixedpoint37d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint37D", index, axis, value))

def add_constraint_fixedline37d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine37D", index, axis, value))

def add_constraint_fixedcircle37d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle37D", index, axis, value))

def add_constraint_fixedarc37d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc37D", index, axis, value))

def add_constraint_fixedpoint38d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint38D", index, axis, value))

def add_constraint_fixedline38d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine38D", index, axis, value))

def add_constraint_fixedcircle38d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle38D", index, axis, value))

def add_constraint_fixedarc38d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc38D", index, axis, value))

def add_constraint_fixedpoint39d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint39D", index, axis, value))

def add_constraint_fixedline39d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine39D", index, axis, value))

def add_constraint_fixedcircle39d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle39D", index, axis, value))

def add_constraint_fixedarc39d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc39D", index, axis, value))

def add_constraint_fixedpoint40d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint40D", index, axis, value))

def add_constraint_fixedline40d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine40D", index, axis, value))

def add_constraint_fixedcircle40d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle40D", index, axis, value))

def add_constraint_fixedarc40d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc40D", index, axis, value))

def add_constraint_fixedpoint41d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint41D", index, axis, value))

def add_constraint_fixedline41d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine41D", index, axis, value))

def add_constraint_fixedcircle41d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle41D", index, axis, value))

def add_constraint_fixedarc41d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc41D", index, axis, value))

def add_constraint_fixedpoint42d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint42D", index, axis, value))

def add_constraint_fixedline42d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine42D", index, axis, value))

def add_constraint_fixedcircle42d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle42D", index, axis, value))

def add_constraint_fixedarc42d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc42D", index, axis, value))

def add_constraint_fixedpoint43d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint43D", index, axis, value))

def add_constraint_fixedline43d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine43D", index, axis, value))

def add_constraint_fixedcircle43d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle43D", index, axis, value))

def add_constraint_fixedarc43d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc43D", index, axis, value))

def add_constraint_fixedpoint44d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint44D", index, axis, value))

def add_constraint_fixedline44d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine44D", index, axis, value))

def add_constraint_fixedcircle44d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle44D", index, axis, value))

def add_constraint_fixedarc44d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc44D", index, axis, value))

def add_constraint_fixedpoint45d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint45D", index, axis, value))

def add_constraint_fixedline45d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine45D", index, axis, value))

def add_constraint_fixedcircle45d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle45D", index, axis, value))

def add_constraint_fixedarc45d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedArc45D", index, axis, value))

def add_constraint_fixedpoint46d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint46D", index, axis, value))

def add_constraint_fixedline46d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine46D", index, axis, value))

def add_constraint_fixedcircle46d(sketch, index, axis, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle46D", index, axis, value))

def
