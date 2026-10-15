import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
frame_thickness = 15.0
housing_left_end_radius = 22.0
housing_right_corner_radius = 13.0
housing_overall_length = 81.0
housing_overall_width = 68.0

# Edit Parameters
left_window_end_radius = 13.0
window_transition_radius = 5.0
upper_window_lobe_radius = 14.0
left_window_width = 20.25
left_window_height = 50.0
left_window_center_x = 19.13
left_window_center_y = 0.0

upper_window_width = 37.0
upper_window_height = 21.0
upper_window_center_x = 54.50
upper_window_center_y = 15.50
upper_window_lobe_pair_half_spacing = 4.01
upper_window_lobe_vertical_offset = 3.50
upper_window_transition_horizontal_offset = 13.50
upper_window_transition_vertical_offset = 5.50
upper_window_lobe_sweep_angle = 80.0
upper_window_transition_sweep_angle = 100.0

boss_outer_diameter = 10.0
boss_height = 8.0
boss_bore_diameter = 5.0

mounting_slot_count = 2
mounting_slot_end_radius = 2.50
mounting_slot_straight_length = 10.0
mounting_slot_center_offset = 19.0

recess_outline_inset = 3.0
recess_depth = 1.0

# --- Helper Functions ---

def create_param_set(doc, name):
    """Creates a VarSet object to hold parameters."""
    obj = doc.addObject("App::VarSet", name)
    obj.addProperty("App::PropertyLinkList", "Parameters", "Parameters", "Linked parameters")
    obj.Parameters = []
    return obj

def add_param(obj, name, value, unit="mm"):
    """Adds a parameter to the VarSet."""
    obj.addProperty("App::PropertyLength", name, "Parameters", f"Parameter {name}")
    obj.setPropertyValue(name, value)
    obj.Parameters.append(name)
    return obj

def add_param_double(obj, name, value):
    """Adds a double parameter to the VarSet."""
    obj.addProperty("App::PropertyDouble", name, "Parameters", f"Parameter {name}")
    obj.setPropertyValue(name, value)
    obj.Parameters.append(name)
    return obj

def add_param_angle(obj, name, value):
    """Adds an angle parameter to the VarSet."""
    obj.addProperty("App::PropertyAngle", name, "Parameters", f"Parameter {name}")
    obj.setPropertyValue(name, value)
    obj.Parameters.append(name)
    return obj

def create_sketch(body, name, plane_name="XY_Plane", offset=0.0):
    """Creates a sketch object attached to a plane."""
    plane = doc.getObject(plane_name)
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane
    sketch.MapMode = "FlatFace"
    sketch.AttachmentOffset = offset
    sketch.Constrain = True
    sketch.Locked = False
    return sketch

def add_line(sketch, p1, p2):
    """Adds a line segment to a sketch."""
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sketch, center, radius):
    """Adds a circle to a sketch."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_ellipse(sketch, center, major_axis, minor_axis, angle=0):
    """Adds an ellipse to a sketch."""
    sketch.addGeometry(Part.Ellipse(center, major_axis, minor_axis, angle), False)

def add_arc(sketch, center, radius, start_angle, end_angle):
    """Adds an arc to a sketch."""
    sketch.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), False)

def add_tangent_line(sketch, p1, p2):
    """Adds a line segment to a sketch."""
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_constraint(sketch, type, *args):
    """Adds a constraint to a sketch."""
    sketch.addConstraint(Sketcher.Constraint(type, *args))

def add_constraint_tangent(sketch, obj1, obj2):
    """Adds a tangent constraint between two geometry objects."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj1, obj2))

def add_constraint_coincident(sketch, obj1, obj2):
    """Adds a coincident constraint between two geometry objects."""
    sketch.addConstraint(Sketcher.Constraint("Coincident", obj1, obj2))

def add_constraint_horizontal(sketch, obj, y_val):
    """Adds a horizontal constraint to an object at a specific Y value."""
    sketch.addConstraint(Sketcher.Constraint("Y", obj, y_val))

def add_constraint_vertical(sketch, obj, x_val):
    """Adds a vertical constraint to an object at a specific X value."""
    sketch.addConstraint(Sketcher.Constraint("X", obj, x_val))

def add_constraint_radius(sketch, obj, radius):
    """Adds a radius constraint to an object."""
    sketch.addConstraint(Sketcher.Constraint("Radius", obj, radius))

def add_constraint_diameter(sketch, obj, diameter):
    """Adds a diameter constraint to an object."""
    sketch.addConstraint(Sketcher.Constraint("Diameter", obj, diameter))

def add_constraint_length(sketch, obj, length):
    """Adds a length constraint to an object."""
    sketch.addConstraint(Sketcher.Constraint("Length", obj, length))

def add_constraint_angle(sketch, obj1, obj2, angle):
    """Adds an angle constraint between two objects."""
    sketch.addConstraint(Sketcher.Constraint("Angle", obj1, obj2, angle))

def add_constraint_perpendicular(sketch, obj1, obj2):
    """Adds a perpendicular constraint between two objects."""
    sketch.addConstraint(Sketcher.Constraint("Perpendicular", obj1, obj2))

def add_constraint_parallel(sketch, obj1, obj2):
    """Adds a parallel constraint between two objects."""
    sketch.addConstraint(Sketcher.Constraint("Parallel", obj1, obj2))

def add_constraint_symmetry(sketch, obj1, obj2, axis):
    """Adds a symmetry constraint between two objects."""
    sketch.addConstraint(Sketcher.Constraint("Symmetry", obj1, obj2, axis))

def add_constraint_tangent_to_line(sketch, obj, line_obj):
    """Adds a tangent constraint between an object and a line."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_obj))

def add_constraint_tangent_to_circle(sketch, obj, circle_obj):
    """Adds a tangent constraint between an object and a circle."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_obj))

def add_constraint_tangent_to_arc(sketch, obj, arc_obj):
    """Adds a tangent constraint between an object and an arc."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_obj))

def add_constraint_tangent_to_ellipse(sketch, obj, ellipse_obj):
    """Adds a tangent constraint between an object and an ellipse."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_obj))

def add_constraint_tangent_to_point(sketch, obj, point_obj):
    """Adds a tangent constraint between an object and a point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_obj))

def add_constraint_tangent_to_line_segment(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_end(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment end."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_end(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment end."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment_end(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment end."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment_end(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment end."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment_end(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment end."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_start(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment start."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_start(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment start."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment_start(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment start."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment_start(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment start."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment_start(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment start."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_mid(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment mid."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_mid(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment mid."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment_mid(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment mid."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment_mid(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment mid."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment_mid(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment mid."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_end_point(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment end point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_end_point(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment end point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment_end_point(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment end point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment_end_point(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment end point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment_end_point(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment end point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_start_point(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment start point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_start_point(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment start point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment_start_point(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment start point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment_start_point(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment start point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment_start_point(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment start point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_mid_point(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment mid point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_mid_point(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment mid point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment_mid_point(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment mid point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment_mid_point(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment mid point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment_mid_point(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment mid point."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_end_line(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment end line."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_end_line(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint between an object and a circle segment end line."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, circle_segment_obj))

def add_constraint_tangent_to_arc_segment_end_line(sketch, obj, arc_segment_obj):
    """Adds a tangent constraint between an object and an arc segment end line."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, arc_segment_obj))

def add_constraint_tangent_to_ellipse_segment_end_line(sketch, obj, ellipse_segment_obj):
    """Adds a tangent constraint between an object and an ellipse segment end line."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, ellipse_segment_obj))

def add_constraint_tangent_to_point_segment_end_line(sketch, obj, point_segment_obj):
    """Adds a tangent constraint between an object and a point segment end line."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, point_segment_obj))

def add_constraint_tangent_to_line_segment_start_line(sketch, obj, line_segment_obj):
    """Adds a tangent constraint between an object and a line segment start line."""
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj, line_segment_obj))

def add_constraint_tangent_to_circle_segment_start_line(sketch, obj, circle_segment_obj):
    """Adds a tangent constraint
