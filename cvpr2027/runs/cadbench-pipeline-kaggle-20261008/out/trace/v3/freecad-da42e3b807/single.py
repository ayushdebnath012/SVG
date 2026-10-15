import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration & Parameters ---
# Base Part Parameters
base_cylinder_diameter = 30.0
base_cylinder_length = 50.0
lower_step_cutout_step_1_diameter = 15.0
lower_step_cutout_step_1_length = 1.3
lower_step_cutout_step_2_diameter = 17.0
lower_step_cutout_step_2_length = 8.6
lower_step_cutout_step_3_diameter = 15.0
lower_step_cutout_step_3_length = 2.8
lower_step_cutout_step_4_diameter = 19.0
lower_step_cutout_step_4_length = 4.1
upper_contoured_cutout_length = 17.8198418
upper_contoured_cutout_depth = 26.1054564
upper_contoured_cutout_top_inner_radius = 25.0
upper_contoured_cutout_convex_radius = 6.0
upper_contoured_cutout_concave_radius = 28.5
upper_contoured_cutout_contour_length = 15.0
upper_contoured_cutout_inner_overshoot = -1.2
upper_contoured_cutout_convex_center_axial_offset = -0.1143294
upper_contoured_cutout_convex_center_radial_offset = 19.0010894
upper_contoured_cutout_concave_center_axial_offset = 34.0971297
upper_contoured_cutout_concave_center_radial_offset = 19.955369
central_through_bore_diameter = 2.0
internal_stepped_cavity_taper_inlet_diameter = 9.0
internal_stepped_cavity_taper_length = 3.0
internal_stepped_cavity_step_1_diameter = 8.0
internal_stepped_cavity_step_1_length = 14.0
internal_stepped_cavity_step_2_diameter = 10.0
internal_stepped_cavity_step_2_length = 10.0
internal_stepped_cavity_step_3_diameter = 5.0
internal_stepped_cavity_step_3_length = 8.14

# Edit Parameters
side_rectangular_cutouts_length = 7.06
side_rectangular_cutouts_width = 5.81
side_rectangular_cutouts_depth = 19.0
side_rectangular_cutouts_left_center_x_offset = -17.03
side_rectangular_cutouts_left_center_y_offset = -5.105
side_rectangular_cutouts_right_length = 7.41
side_rectangular_cutouts_right_width = 6.0
side_rectangular_cutouts_right_center_x_offset = 17.205
side_rectangular_cutouts_right_center_y_offset = -5.2
primary_radial_slots_width = 6.0
primary_radial_slots_length = 13.51
primary_radial_slots_depth = 21.0
primary_radial_slots_center_x_offset = -7.0
radial_slots_count = 4
secondary_radial_slots_width = 5.12
secondary_radial_slots_depth = 10.0
secondary_radial_slots_length = 13.5
secondary_radial_slots_center_y_offset = 14.25

# --- Helper Functions ---

def create_sketch(body, name, plane_name, offset_z=0.0):
    """Creates a Sketcher::SketchObject attached to a specific plane."""
    plane = doc.getObject(plane_name)
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane
    sketch.MapMode = "FlatFace"
    sketch.Placement = App.Placement(App.Vector(0, 0, offset_z))
    return sketch

def add_line(sketch, p1, p2, is_constraint=False):
    sketch.addGeometry(Part.LineSegment(p1, p2), is_constraint)

def add_circle(sketch, center, radius, is_constraint=False):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constraint)

def add_ellipse(sketch, center, major_axis, minor_axis, angle=0.0, is_constraint=False):
    # FreeCAD Part.Ellipse expects center, major_axis (vector), minor_axis (vector)
    # Or center, major_radius, minor_radius, angle
    # Using Part.Ellipse(center, major_radius, minor_radius, angle)
    sketch.addGeometry(Part.Ellipse(center, major_axis, minor_axis, angle), is_constraint)

def add_constraint(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint(*args))

def add_constraint_line(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("LineToConstraint", *args))

def add_constraint_point(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Point", *args))

def add_constraint_coincident(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Coincident", *args))

def add_constraint_perpendicular(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Perpendicular", *args))

def add_constraint_horizontal(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Horizontal", *args))

def add_constraint_vertical(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Vertical", *args))

def add_constraint_fixed_size(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedSize", *args))

def add_constraint_radius(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Radius", *args))

def add_constraint_tangent(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Tangent", *args))

def add_constraint_parallel(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Parallel", *args))

def add_constraint_distance(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Distance", *args))

def add_constraint_angle(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Angle", *args))

def add_constraint_symmetry(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Symmetry", *args))

def add_constraint_equality(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("Equality", *args))

def add_constraint_fixed_point(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", *args))

def add_constraint_fixed_line(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedLine", *args))

def add_constraint_fixed_circle(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle", *args))

def add_constraint_fixed_ellipse(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedEllipse", *args))

def add_constraint_fixed_helix(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedHelix", *args))

def add_constraint_fixed_spline(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedSpline", *args))

def add_constraint_fixed_surface(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedSurface", *args))

def add_constraint_fixed_volume(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedVolume", *args))

def add_constraint_fixed_wire(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedWire", *args))

def add_constraint_fixed_face(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedFace", *args))

def add_constraint_fixed_edge(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedEdge", *args))

def add_constraint_fixed_vertex(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedVertex", *args))

def add_constraint_fixed_axis(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedAxis", *args))

def add_constraint_fixed_plane(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("FixedPlane", *args))

def add_constraint_fixed_point_on_line(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLine", *args))

def add_constraint_fixed_point_on_circle(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnCircle", *args))

def add_constraint_fixed_point_on_ellipse(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnEllipse", *args))

def add_constraint_fixed_point_on_helix(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnHelix", *args))

def add_constraint_fixed_point_on_spline(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnSpline", *args))

def add_constraint_fixed_point_on_surface(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnSurface", *args))

def add_constraint_fixed_point_on_volume(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnVolume", *args))

def add_constraint_fixed_point_on_wire(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnWire", *args))

def add_constraint_fixed_point_on_face(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnFace", *args))

def add_constraint_fixed_point_on_edge(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnEdge", *args))

def add_constraint_fixed_point_on_vertex(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnVertex", *args))

def add_constraint_fixed_point_on_axis(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnAxis", *args))

def add_constraint_fixed_point_on_plane(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnPlane", *args))

def add_constraint_fixed_point_on_line_on_circle(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnCircle", *args))

def add_constraint_fixed_point_on_line_on_ellipse(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnEllipse", *args))

def add_constraint_fixed_point_on_line_on_helix(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnHelix", *args))

def add_constraint_fixed_point_on_line_on_spline(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnSpline", *args))

def add_constraint_fixed_point_on_line_on_surface(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnSurface", *args))

def add_constraint_fixed_point_on_line_on_volume(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnVolume", *args))

def add_constraint_fixed_point_on_line_on_wire(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnWire", *args))

def add_constraint_fixed_point_on_line_on_face(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnFace", *args))

def add_constraint_fixed_point_on_line_on_edge(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnEdge", *args))

def add_constraint_fixed_point_on_line_on_vertex(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnVertex", *args))

def add_constraint_fixed_point_on_line_on_axis(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnAxis", *args))

def add_constraint_fixed_point_on_line_on_plane(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnPlane", *args))

def add_constraint_fixed_point_on_line_on_line_on_circle(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnCircle", *args))

def add_constraint_fixed_point_on_line_on_line_on_ellipse(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnEllipse", *args))

def add_constraint_fixed_point_on_line_on_line_on_helix(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnHelix", *args))

def add_constraint_fixed_point_on_line_on_line_on_spline(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnSpline", *args))

def add_constraint_fixed_point_on_line_on_line_on_surface(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnSurface", *args))

def add_constraint_fixed_point_on_line_on_line_on_volume(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnVolume", *args))

def add_constraint_fixed_point_on_line_on_line_on_wire(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnWire", *args))

def add_constraint_fixed_point_on_line_on_line_on_face(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnFace", *args))

def add_constraint_fixed_point_on_line_on_line_on_edge(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnEdge", *args))

def add_constraint_fixed_point_on_line_on_line_on_vertex(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnVertex", *args))

def add_constraint_fixed_point_on_line_on_line_on_axis(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnAxis", *args))

def add_constraint_fixed_point_on_line_on_line_on_plane(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnPlane", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_circle(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnCircle", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_ellipse(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnEllipse", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_helix(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnHelix", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_spline(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnSpline", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_surface(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnSurface", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_volume(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnVolume", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_wire(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnWire", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_face(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnFace", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_edge(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnEdge", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_vertex(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnVertex", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_axis(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnAxis", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_plane(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnPlane", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_line_on_circle(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnLineOnCircle", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_line_on_ellipse(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnLineOnEllipse", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_line_on_helix(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnLineOnHelix", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_line_on_spline(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnLineOnSpline", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_line_on_surface(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnLineOnSurface", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_line_on_volume(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnLineOnVolume", *args))

def add_constraint_fixed_point_on_line_on_line_on_line_on_line_on_wire(sketch, *args):
    sketch.addConstraint(Sketcher.Constraint("PointOnLineOnLineOnLineOnLineOnWire",
