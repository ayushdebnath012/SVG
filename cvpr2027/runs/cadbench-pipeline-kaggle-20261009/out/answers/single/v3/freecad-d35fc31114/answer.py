import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__ to ensure the script is self-contained and portable
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Parameters
params = {
    "channel_length": 55.1,
    "opposite_channel_end_longitudinal_station": -23.1,
    "channel_clear_width": 42.0,
    "channel_flange_depth": 10.0,
    "channel_web_thickness": 6.0,
    "channel_flange_thickness": 4.0,
    "channel_sidewall_taper_angle": 45.0, # degrees
    "jaw_plate_thickness": 8.9,
    "jaw_arm_outer_edge_length": 40.0,
    "jaw_arm_inner_edge_length": 34.0,
    "small_hole_diameter": 3.2,
    "jaw_open_end_hole_center_distance_from_inner_tip": 8.75,
    "cross_pivot_hole_diameter": 4.2,
    "cross_pivot_hole_pattern_radius": 12.0,
    "jaw_throat_hole_center_distance_from_inner_tip": 25.25
}

# --- Document Setup ---
doc = App.newDocument("PivotBracket")

# Create standard planes
# XY_Plane (X, Y), XZ_Plane (X, Z), YZ_Plane (Y, Z)
# We will use XY_Plane as the base sketch plane (Z=0)
# Longitudinal direction = X
# Transverse direction = Y
# Thickness direction = Z

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObjectGroup", "Group") # Optional grouping if needed, but Body is root

# --- Parameters Object ---
# We create a VarSet to hold the parameters as editable properties
param_obj = body.newObject("App::VarSet", "Parameters")
for name, value in params.items():
    param_obj.addProperty("App::PropertyFloat", name, "Parameters", name)
    param_obj[name] = value

# --- Helper Functions ---
def get_param(name):
    return param_obj[name]

def create_sketch(name, plane, offset=0.0):
    """Creates a sketch object attached to a plane."""
    sketch = body.newObject("Sketcher::SketchObject", name)
    # Find the plane object
    plane_obj = doc.getObject(plane)
    if not plane_obj:
        raise RuntimeError(f"Plane {plane} not found.")
    
    sketch.Plane = plane_obj
    sketch.MapMode = "FlatFace"
    sketch.AttachmentOffset = App.Vector(0, 0, offset)
    sketch.Constrain = True
    sketch.Locked = False
    return sketch

def add_line(sketch, p1, p2, constraint_type="Horizontal" if p1.Y == p2.Y else "Vertical"):
    """Adds a line segment and a constraint."""
    sketch.addGeometry(Part.LineSegment(p1, p2), False)
    # Add constraint based on orientation relative to sketch plane (XY)
    # If Y is constant, it's horizontal. If X is constant, it's vertical.
    if abs(p1.Y - p2.Y) < 1e-6:
        sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
    elif abs(p1.X - p2.X) < 1e-6:
        sketch.addConstraint(Sketcher.Constraint("Vertical", 0))
    else:
        # General line constraint
        sketch.addConstraint(Sketcher.Constraint("LineToExpression", 0, "X1", "X2"))
        sketch.addConstraint(Sketcher.Constraint("LineToExpression", 0, "Y1", "Y2"))

def add_circle(sketch, center, radius, constraint_type="Radius"):
    """Adds a circle and a radius constraint."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)
    sketch.addConstraint(Sketcher.Constraint("Radius", 0, radius))

def add_coincident(sketch, obj_idx, point_idx, ref_obj_idx, ref_point_idx):
    """Adds a coincident constraint."""
    sketch.addConstraint(Sketcher.Constraint("Coincident", obj_idx, point_idx, ref_obj_idx, ref_point_idx))

def add_parallel(sketch, obj_idx, point_idx, ref_obj_idx, ref_point_idx):
    """Adds a parallel constraint."""
    sketch.addConstraint(Sketcher.Constraint("Parallel", obj_idx, point_idx, ref_obj_idx, ref_point_idx))

def add_perpendicular(sketch, obj_idx, point_idx, ref_obj_idx, ref_point_idx):
    """Adds a perpendicular constraint."""
    sketch.addConstraint(Sketcher.Constraint("Perpendicular", obj_idx, point_idx, ref_obj_idx, ref_point_idx))

def add_distance(sketch, obj_idx, point_idx, ref_obj_idx, ref_point_idx, dist):
    """Adds a distance constraint."""
    sketch.addConstraint(Sketcher.Constraint("Distance", obj_idx, point_idx, ref_obj_idx, ref_point_idx, dist))

def add_symmetry(sketch, obj_idx, point_idx, axis_obj_idx, axis_point_idx, axis_dir_idx):
    """Adds a symmetry constraint."""
    sketch.addConstraint(Sketcher.Constraint("Symmetry", obj_idx, point_idx, axis_obj_idx, axis_point_idx, axis_dir_idx))

def add_tangent(sketch, obj_idx, point_idx, ref_obj_idx, ref_point_idx):
    """Adds a tangent constraint."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj_idx, point_idx, ref_obj_idx, ref_point_idx))

def add_angle(sketch, obj_idx, point_idx, ref_obj_idx, ref_point_idx, angle):
    """Adds an angle constraint."""
    sketch.addConstraint(Sketcher.Constraint("Angle", obj_idx, point_idx, ref_obj_idx, ref_point_idx, angle))

def add_fixed(sketch, obj_idx, point_idx):
    """Adds a fixed constraint."""
    sketch.addConstraint(Sketcher.Constraint("Fixed", obj_idx, point_idx))

def add_equality(sketch, obj_idx, point_idx, ref_obj_idx, ref_point_idx):
    """Adds an equality constraint."""
    sketch.addConstraint(Sketcher.Constraint("Equality", obj_idx, point_idx, ref_obj_idx, ref_point_idx))

def add_3point(sketch, obj_idx, point_idx, p1, p2, p3):
    """Adds a 3-point constraint."""
    sketch.addConstraint(Sketcher.Constraint("3Point", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, p3.X, p3.Y))

def add_2point(sketch, obj_idx, point_idx, p1, p2):
    """Adds a 2-point constraint."""
    sketch.addConstraint(Sketcher.Constraint("2Point", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y))

def add_1point(sketch, obj_idx, point_idx, p1):
    """Adds a 1-point constraint."""
    sketch.addConstraint(Sketcher.Constraint("1Point", obj_idx, point_idx, p1.X, p1.Y))

def add_2point_angle(sketch, obj_idx, point_idx, p1, p2, angle):
    """Adds a 2-point angle constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointAngle", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, angle))

def add_2point_distance(sketch, obj_idx, point_idx, p1, p2, dist):
    """Adds a 2-point distance constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointDistance", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, dist))

def add_2point_parallel(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point parallel constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointParallel", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_perpendicular(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point perpendicular constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointPerpendicular", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_tangent(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point tangent constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointTangent", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_angle(sketch, obj_idx, point_idx, p1, p2, angle):
    """Adds a 2-point angle constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointAngle", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, angle))

def add_2point_distance(sketch, obj_idx, point_idx, p1, p2, dist):
    """Adds a 2-point distance constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointDistance", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, dist))

def add_2point_parallel(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point parallel constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointParallel", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_perpendicular(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point perpendicular constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointPerpendicular", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_tangent(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point tangent constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointTangent", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_angle(sketch, obj_idx, point_idx, p1, p2, angle):
    """Adds a 2-point angle constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointAngle", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, angle))

def add_2point_distance(sketch, obj_idx, point_idx, p1, p2, dist):
    """Adds a 2-point distance constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointDistance", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, dist))

def add_2point_parallel(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point parallel constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointParallel", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_perpendicular(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point perpendicular constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointPerpendicular", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_tangent(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point tangent constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointTangent", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_angle(sketch, obj_idx, point_idx, p1, p2, angle):
    """Adds a 2-point angle constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointAngle", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, angle))

def add_2point_distance(sketch, obj_idx, point_idx, p1, p2, dist):
    """Adds a 2-point distance constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointDistance", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, dist))

def add_2point_parallel(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point parallel constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointParallel", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_perpendicular(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point perpendicular constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointPerpendicular", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_tangent(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point tangent constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointTangent", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_angle(sketch, obj_idx, point_idx, p1, p2, angle):
    """Adds a 2-point angle constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointAngle", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, angle))

def add_2point_distance(sketch, obj_idx, point_idx, p1, p2, dist):
    """Adds a 2-point distance constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointDistance", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, dist))

def add_2point_parallel(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point parallel constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointParallel", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_perpendicular(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point perpendicular constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointPerpendicular", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_tangent(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point tangent constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointTangent", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_angle(sketch, obj_idx, point_idx, p1, p2, angle):
    """Adds a 2-point angle constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointAngle", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, angle))

def add_2point_distance(sketch, obj_idx, point_idx, p1, p2, dist):
    """Adds a 2-point distance constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointDistance", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, dist))

def add_2point_parallel(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point parallel constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointParallel", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_perpendicular(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point perpendicular constraint."""
    sketch.addConstraint(Sketcher.Constraint("2PointPerpendicular", obj_idx, point_idx, p1.X, p1.Y, p2.X, p2.Y, ref_obj_idx, ref_point_idx))

def add_2point_tangent(sketch, obj_idx, point_idx, p1, p2, ref_obj_idx, ref_point_idx):
    """Adds a 2-point tangent constraint."""
    sketch.addConstraint(Sketcher.Constraint("2
