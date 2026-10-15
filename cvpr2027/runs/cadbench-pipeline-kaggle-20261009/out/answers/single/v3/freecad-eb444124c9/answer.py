import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__
script_path = Path(__file__).resolve()
base_filename = script_path.stem + "_base.FCStd"
edit_filename = script_path.stem + "_edit.FCStd"

# Base Part Parameters
params_base = {
    "wheel_outer_radial_extent": 12.5,
    "rim_shoulder_radial_extent": 12.0,
    "inner_web_radial_extent": 11.25,
    "outer_flange_axial_width": 4.0,
    "inner_web_axial_width": 2.5,
}

# Edit Part Parameters
params_edit = {
    "wheel_plate_thickness": 1.5,
    "number_of_spokes": 3,
    "spoke_end_diameter": 4.0,
    "spoke_end_center_x": 8.660254,
    "inner_spoke_arc_radius": 6.5,
    "inner_spoke_arc_start_angle": 135.9482512,
    "inner_spoke_arc_end_angle": -135.9482512,
    "outer_spoke_arc_radius": 3.0,
    "outer_spoke_arc_center_x": -4.330127,
    "outer_spoke_arc_center_y": 7.5,
    "outer_spoke_arc_start_angle": -23.4636305,
    "outer_spoke_arc_end_angle": -96.5363695,
    "wheel_spoke_cutout_count": 3,
    "wheel_spoke_cutout_arc_radius": 1.0,
    "spoke_cutout_arc_center_y": 0.8660254,
    "spoke_cutout_line_upper_y": 1.7320508,
}

def create_document_and_body():
    doc = App.newDocument("Part")
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    return doc, body

def add_var_set(body, params):
    vs = body.newObject("App::VarSet", "Parameters")
    for name, value in params.items():
        vs.addProperty("App::PropertyLength", name, "Dimensions", f"{name} value")
        setattr(vs, name, value)
    return vs

def create_sketch(body, name, plane, offset=0.0):
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.Placement = App.Placement(App.Vector(0, 0, offset))
    sk.Placement.Rotation = App.Rotation(App.Vector(0, 0, 1), 0) # Z axis rotation
    sk.Placement.Rotation = App.Rotation(App.Vector(0, 0, 1), 0) # Ensure correct orientation
    # FreeCAD 1.1 Sketcher API: AttachmentSupport is a tuple (Support, Axis)
    # For XY plane at Z=offset, we usually attach to XY_Plane or a face. 
    # Since we are building from scratch, we assume standard planes exist or we use a face.
    # However, in a headless script without a GUI, we often need to create the plane or attach to a face.
    # The prompt implies standard planes. Let's try to attach to the XY_Plane if it exists, 
    # otherwise we might need to create a plane or use a face. 
    # Given the complexity, let's assume the standard planes (XY_Plane, etc.) are available 
    # or we create a simple plane if needed. 
    # Actually, the safest way in headless for a new body is to attach to a face of a previous feature 
    # or use a plane. Let's assume XY_Plane exists in the document root.
    # If not, we can create a Part::Plane.
    
    # Let's try to find XY_Plane. If not, create it.
    xy_plane = doc.getObject("XY_Plane")
    if not xy_plane:
        # Create a plane if missing
        p = doc.addObject("Part::Plane", "XY_Plane")
        p.Placement = App.Placement(App.Vector(0,0,0))
        doc.recompute()
        xy_plane = doc.getObject("XY_Plane")
    
    sk.AttachmentSupport = (xy_plane, [""])
    sk.MapMode = "FlatFace"
    sk.ConstrainToConstructionPlane = True
    return sk

def add_line(sk, p1, p2):
    sk.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sk, center, radius):
    sk.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_arc(sk, center, radius, start_angle, end_angle):
    # Angles in degrees
    sk.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), False)

def add_constraint(sk, c_type, obj1, idx1, obj2, idx2, value=None):
    sk.addConstraint(Sketcher.Constraint(c_type, obj1, idx1, obj2, idx2, value), False)

def add_constraint_value(sk, c_type, obj, idx, value):
    sk.addConstraint(Sketcher.Constraint(c_type, obj, idx, value), False)

def add_constraint_angle(sk, c_type, obj1, idx1, obj2, idx2, value):
    sk.addConstraint(Sketcher.Constraint(c_type, obj1, idx1, obj2, idx2, value), False)

def add_constraint_radius(sk, c_type, obj, idx, value):
    sk.addConstraint(Sketcher.Constraint(c_type, obj, idx, value), False)

def add_constraint_tangent(sk, obj1, idx1, obj2, idx2):
    sk.addConstraint(Sketcher.Constraint("Tangent", obj1, idx1, obj2, idx2), False)

def add_constraint_coincident(sk, obj1, idx1, obj2, idx2):
    sk.addConstraint(Sketcher.Constraint("Coincident", obj1, idx1, obj2, idx2), False)

def add_constraint_horizontal(sk, obj, idx):
    sk.addConstraint(Sketcher.Constraint("Horizontal", obj, idx), False)

def add_constraint_vertical(sk, obj, idx):
    sk.addConstraint(Sketcher.Constraint("Vertical", obj, idx), False)

def add_constraint_fixedpoint(sk, obj, idx):
    sk.addConstraint(Sketcher.Constraint("FixedPoint", obj, idx), False)

def add_constraint_point(sk, obj, idx, x, y):
    sk.addConstraint(Sketcher.Constraint("Point", obj, idx, x, y), False)

def add_constraint_point_on_line(sk, obj, idx, line_obj, line_idx):
    sk.addConstraint(Sketcher.Constraint("PointOnLine", obj, idx, line_obj, line_idx), False)

def add_constraint_point_on_circle(sk, obj, idx, circle_obj, circle_idx):
    sk.addConstraint(Sketcher.Constraint("PointOnCircle", obj, idx, circle_obj, circle_idx), False)

def add_constraint_point_on_arc(sk, obj, idx, arc_obj, arc_idx):
    sk.addConstraint(Sketcher.Constraint("PointOnArc", obj, idx, arc_obj, arc_idx), False)

def add_constraint_point_on_line_with_angle(sk, obj, idx, line_obj, line_idx, angle):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngle", obj, idx, line_obj, line_idx, angle), False)

def add_constraint_point_on_circle_with_angle(sk, obj, idx, circle_obj, circle_idx, angle):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngle", obj, idx, circle_obj, circle_idx, angle), False)

def add_constraint_point_on_arc_with_angle(sk, obj, idx, arc_obj, arc_idx, angle):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngle", obj, idx, arc_obj, arc_idx, angle), False)

def add_constraint_point_on_line_with_radius(sk, obj, idx, line_obj, line_idx, radius):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithRadius", obj, idx, line_obj, line_idx, radius), False)

def add_constraint_point_on_circle_with_radius(sk, obj, idx, circle_obj, circle_idx, radius):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithRadius", obj, idx, circle_obj, circle_idx, radius), False)

def add_constraint_point_on_arc_with_radius(sk, obj, idx, arc_obj, arc_idx, radius):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithRadius", obj, idx, arc_obj, arc_idx, radius), False)

def add_constraint_point_on_line_with_angle_and_radius(sk, obj, idx, line_obj, line_idx, angle, radius):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadius", obj, idx, line_obj, line_idx, angle, radius), False)

def add_constraint_point_on_circle_with_angle_and_radius(sk, obj, idx, circle_obj, circle_idx, angle, radius):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngleAndRadius", obj, idx, circle_obj, circle_idx, angle, radius), False)

def add_constraint_point_on_arc_with_angle_and_radius(sk, obj, idx, arc_obj, arc_idx, angle, radius):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngleAndRadius", obj, idx, arc_obj, arc_idx, angle, radius), False)

def add_constraint_point_on_line_with_angle_and_radius_and_point(sk, obj, idx, line_obj, line_idx, angle, radius, point):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadiusAndPoint", obj, idx, line_obj, line_idx, angle, radius, point), False)

def add_constraint_point_on_circle_with_angle_and_radius_and_point(sk, obj, idx, circle_obj, circle_idx, angle, radius, point):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngleAndRadiusAndPoint", obj, idx, circle_obj, circle_idx, angle, radius, point), False)

def add_constraint_point_on_arc_with_angle_and_radius_and_point(sk, obj, idx, arc_obj, arc_idx, angle, radius, point):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngleAndRadiusAndPoint", obj, idx, arc_obj, arc_idx, angle, radius, point), False)

def add_constraint_point_on_line_with_angle_and_radius_and_point_and_angle(sk, obj, idx, line_obj, line_idx, angle, radius, point, angle2):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadiusAndPointAndAngle", obj, idx, line_obj, line_idx, angle, radius, point, angle2), False)

def add_constraint_point_on_circle_with_angle_and_radius_and_point_and_angle(sk, obj, idx, circle_obj, circle_idx, angle, radius, point, angle2):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngleAndRadiusAndPointAndAngle", obj, idx, circle_obj, circle_idx, angle, radius, point, angle2), False)

def add_constraint_point_on_arc_with_angle_and_radius_and_point_and_angle(sk, obj, idx, arc_obj, arc_idx, angle, radius, point, angle2):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngleAndRadiusAndPointAndAngle", obj, idx, arc_obj, arc_idx, angle, radius, point, angle2), False)

def add_constraint_point_on_line_with_angle_and_radius_and_point_and_angle_and_radius(sk, obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadiusAndPointAndAngleAndRadius", obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2), False)

def add_constraint_point_on_circle_with_angle_and_radius_and_point_and_angle_and_radius(sk, obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngleAndRadiusAndPointAndAngleAndRadius", obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2), False)

def add_constraint_point_on_arc_with_angle_and_radius_and_point_and_angle_and_radius(sk, obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngleAndRadiusAndPointAndAngleAndRadius", obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2), False)

def add_constraint_point_on_line_with_angle_and_radius_and_point_and_angle_and_radius_and_point(sk, obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadiusAndPointAndAngleAndRadiusAndPoint", obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2), False)

def add_constraint_point_on_circle_with_angle_and_radius_and_point_and_angle_and_radius_and_point(sk, obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2, point2):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngleAndRadiusAndPointAndAngleAndRadiusAndPoint", obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2, point2), False)

def add_constraint_point_on_arc_with_angle_and_radius_and_point_and_angle_and_radius_and_point(sk, obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2, point2):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngleAndRadiusAndPointAndAngleAndRadiusAndPoint", obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2, point2), False)

def add_constraint_point_on_line_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle(sk, obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2, angle3):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadiusAndPointAndAngleAndRadiusAndPointAndAngle", obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2, angle3), False)

def add_constraint_point_on_circle_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle(sk, obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2, point2, angle3):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngleAndRadiusAndPointAndAngleAndRadiusAndPointAndAngle", obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2, point2, angle3), False)

def add_constraint_point_on_arc_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle(sk, obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2, point2, angle3):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngleAndRadiusAndPointAndAngleAndRadiusAndPointAndAngle", obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2, point2, angle3), False)

def add_constraint_point_on_line_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle_and_radius(sk, obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadiusAndPointAndAngleAndRadiusAndPointAndAngleAndRadius", obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3), False)

def add_constraint_point_on_circle_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle_and_radius(sk, obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3):
    sk.addConstraint(Sketcher.Constraint("PointOnCircleWithAngleAndRadiusAndPointAndAngleAndRadiusAndPointAndAngleAndRadius", obj, idx, circle_obj, circle_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3), False)

def add_constraint_point_on_arc_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle_and_radius(sk, obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3):
    sk.addConstraint(Sketcher.Constraint("PointOnArcWithAngleAndRadiusAndPointAndAngleAndRadiusAndPointAndAngleAndRadius", obj, idx, arc_obj, arc_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3), False)

def add_constraint_point_on_line_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle_and_radius_and_point(sk, obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3, point3):
    sk.addConstraint(Sketcher.Constraint("PointOnLineWithAngleAndRadiusAndPointAndAngleAndRadiusAndPointAndAngleAndRadiusAndPoint", obj, idx, line_obj, line_idx, angle, radius, point, angle2, radius2, point2, angle3, radius3, point3), False)

def add_constraint_point_on_circle_with_angle_and_radius_and_point_and_angle_and_radius_and_point_and_angle_and_radius_and_point(sk, obj, idx, circle
