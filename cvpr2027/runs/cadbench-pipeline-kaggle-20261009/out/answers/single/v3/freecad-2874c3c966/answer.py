import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration and Parameters ---

# Base Part Parameters
p_base = {
    "pin_body_diameter": 13.94,
    "outer_diameter": 18.9,
    "snap_feature_diameter": 15.9,
    "undercut_diameter": 6.0,
    "front_section_length": 3.1,
    "front_snap_taper_length": 1.56,
    "first_snap_ridge_axial_length": 4.47,
    "second_snap_ridge_start_position": 8.5,
    "second_snap_ridge_end_position": 12.05,
    "main_shaft_section_start": 15.1,
    "snap_groove_width": 1.5,
    "snap_groove_apex_position": 16.6,
    "rear_shaft_section_start": 18.1,
    "rear_taper_start_position": 29.62,
    "connector_end_position": 40.1,
    "total_connector_length": 43.2,
    "undercut_depth_position": 3.0,
    "conical_bore_length": 9.0,
    "conical_bore_large_end_diameter": 13.94,
    "conical_bore_small_end_diameter": 6.0,
    "front_snap_taper_return_position": 4.03,
}

# Edit Part Parameters
p_edit = {
    "axial_slot_width": 2.0,
    "axial_slot_length": 9.89,
    "axial_slot_axial_length": 23.2,
    "number_of_axial_slot_features": 6,
    "axial_slot_total_sweep_angle": 60.0,
    "snap_tab_width": 3.2,
    "snap_tab_top_arc_radius": 9.45,
    "snap_tab_top_arc_central_angle": 19.495659,
    "snap_tab_axial_length": 14.0,
    "snap_tab_axial_offset": 15.1,
    "number_of_snap_tab_features": 4,
    "snap_tab_total_sweep_angle": 90.0,
    "conical_cutout_large_diameter": 13.94,
    "conical_cutout_small_diameter": 5.08,
    "conical_cutout_axial_length": 8.5,
}

# --- Helper Functions ---

def create_sketch_on_plane(body, plane_name, offset=0.0):
    """Creates a sketch object on a specific plane with an optional Z offset."""
    plane = doc.getObject(plane_name)
    sketch = body.newObject("Sketcher::SketchObject", f"Sketch_{plane_name}")
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    sketch.Placement = sketch.Placement * App.Placement(plane.Placement)
    sketch.Placement = sketch.Placement * App.Placement(App.Rotation(App.Vector(0, 0, 1), 0)) # Ensure Z-up if needed, but Plane handles orientation
    # Actually, simpler: attach to plane directly.
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    sketch.Placement = sketch.Placement * App.Placement(plane.Placement)
    sketch.MapMode = "FlatFace"
    sketch.ConstrainToPlane = plane
    sketch.ConstrainToPlaneAxis = plane.Axis
    return sketch

def add_line(sketch, p1, p2):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sketch, center, radius):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_ellipse(sketch, center, major_axis, minor_axis, angle=0):
    # FreeCAD Part.Ellipse expects center, major_axis_vector, minor_axis_vector
    # Or center, major_radius, minor_radius, angle
    sketch.addGeometry(Part.Ellipse(center, major_axis, minor_axis, angle), False)

def add_constraint(sketch, constraint_type, obj1, prop1, obj2, prop2, value=None):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj1, prop1, obj2, prop2, value), False)

def add_constraint_value(sketch, constraint_type, obj1, prop1, value):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj1, prop1, value), False)

def add_constraint_point(sketch, constraint_type, obj1, prop1, obj2, prop2):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, obj1, prop1, obj2, prop2), False)

def add_constraint_coincident(sketch, obj1, prop1, obj2, prop2):
    sketch.addConstraint(Sketcher.Constraint("Coincident", obj1, prop1, obj2, prop2), False)

def add_constraint_horizontal(sketch, obj, prop, value=0):
    sketch.addConstraint(Sketcher.Constraint("Horizontal", obj, prop, value), False)

def add_constraint_vertical(sketch, obj, prop, value=0):
    sketch.addConstraint(Sketcher.Constraint("Vertical", obj, prop, value), False)

def add_constraint_radius(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("Radius", obj, prop, value), False)

def add_constraint_tangent(sketch, obj1, prop1, obj2, prop2):
    sketch.addConstraint(Sketcher.Constraint("Tangent", obj1, prop1, obj2, prop2), False)

def add_constraint_perpendicular(sketch, obj1, prop1, obj2, prop2):
    sketch.addConstraint(Sketcher.Constraint("Perpendicular", obj1, prop1, obj2, prop2), False)

def add_constraint_parallel(sketch, obj1, prop1, obj2, prop2):
    sketch.addConstraint(Sketcher.Constraint("Parallel", obj1, prop1, obj2, prop2), False)

def add_constraint_fixed_size(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedSize", obj, prop, value), False)

def add_constraint_fixed_angle(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedAngle", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_distance(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedDistance", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPoint", obj, prop, value), False)

def add_constraint_fixed_line(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedLine", obj, prop, value), False)

def add_constraint_fixed_circle(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedCircle", obj, prop, value), False)

def add_constraint_fixed_ellipse(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedEllipse", obj, prop, value), False)

def add_constraint_fixed_helix(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedHelix", obj, prop, value), False)

def add_constraint_fixed_spline(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedSpline", obj, prop, value), False)

def add_constraint_fixed_surface(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedSurface", obj, prop, value), False)

def add_constraint_fixed_volume(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedVolume", obj, prop, value), False)

def add_constraint_fixed_wire(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedWire", obj, prop, value), False)

def add_constraint_fixed_face(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedFace", obj, prop, value), False)

def add_constraint_fixed_edge(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedEdge", obj, prop, value), False)

def add_constraint_fixed_vertex(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedVertex", obj, prop, value), False)

def add_constraint_fixed_axis(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedAxis", obj, prop, value), False)

def add_constraint_fixed_plane(sketch, obj, prop, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPlane", obj, prop, value), False)

def add_constraint_fixed_point_on_line(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnLine", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_circle(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnCircle", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_ellipse(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnEllipse", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_helix(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnHelix", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_spline(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnSpline", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_surface(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnSurface", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_volume(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnVolume", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_wire(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnWire", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_face(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnFace", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_edge(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnEdge", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_vertex(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnVertex", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_axis(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnAxis", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_line_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnLineOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_circle_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnCircleOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_ellipse_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnEllipseOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_helix_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnHelixOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_spline_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnSplineOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_surface_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnSurfaceOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_volume_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnVolumeOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_wire_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnWireOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_face_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnFaceOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_edge_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnEdgeOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_vertex_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnVertexOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_axis_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnAxisOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_plane_on_plane(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnPlaneOnPlane", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_line_on_line(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnLineOnLine", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_circle_on_circle(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnCircleOnCircle", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_ellipse_on_ellipse(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnEllipseOnEllipse", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_helix_on_helix(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnHelixOnHelix", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_spline_on_spline(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnSplineOnSpline", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_surface_on_surface(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnSurfaceOnSurface", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_volume_on_volume(sketch, obj1, prop1, obj2, prop2, value):
    sketch.addConstraint(Sketcher.Constraint("FixedPointOnVolumeOnVolume", obj1, prop1, obj2, prop2, value), False)

def add_constraint_fixed_point_on_wire_on_wire(sketch, obj1, prop1, obj2, prop2, value):
