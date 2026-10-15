import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
bracket_base_length = 62.0
bracket_base_width = 24.0
bracket_base_thickness = 8.0

# Edit Parameters (Target)
hinge_pin_hole_diameter = 8.0
hinge_cheek_outer_arc_radius = 10.0
hinge_cheek_outer_arc_start_angle = -35.0003487
hinge_cheek_outer_arc_end_angle = 148.6986094
hinge_cheek_x_thickness = 6.0
hinge_cheek_inner_face_offset_from_midplane = 8.0
hinge_axis_y = 12.0
hinge_axis_z = 27.0
small_boss_inner_diameter = 3.0
small_boss_outer_diameter = 6.0
small_boss_depth = 10.0
small_boss_start_inset_from_front = 13.0
small_boss_seed_center_x = 20.0
mounting_hole_diameter = 9.0
mounting_hole_end_offset_x = 8.5

# --- Helper Functions ---

def create_param_var(doc, name, value, unit="mm"):
    """Creates a named parameter in the document."""
    var = doc.addObject("App::VarSet", name)
    var.addProperty("App::PropertyLength", "Value", "Dimensions", name)
    var.Value = value
    return var

def create_sketch(doc, body, name, plane_name, offset=0.0):
    """Creates a sketch object attached to a specific plane."""
    # Get the plane object
    plane_obj = doc.getObject(plane_name)
    
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Plane = plane_obj
    sketch.MapMode = "FlatFace"
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    sketch.Constrain = True
    sketch.Locked = False
    return sketch

def add_line(sketch, p1, p2):
    sketch.addGeometry(Part.LineSegment(p1, p2), False)

def add_circle(sketch, center, radius):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

def add_constraint(sketch, constraint_type, *args):
    sketch.addConstraint(Sketcher.Constraint(constraint_type, *args))

def add_arc(sketch, center, radius, start_angle, end_angle):
    # FreeCAD Sketcher arcs are defined by center, radius, start_angle, end_angle
    # Angles are in degrees relative to X axis
    sketch.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle, radius), False)

def add_constraint_arc(sketch, center_idx, radius_idx, start_angle, end_angle):
    # This is tricky in headless API. We usually define the arc geometry and then constrain it.
    # However, for complex arcs, it's often easier to define the geometry and use constraints 
    # to fix the angles if we had a reference. 
    # Here we will rely on the geometry definition for the arc shape.
    pass

def build_base_part(doc):
    """Builds the rectangular base plate."""
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters
    p_len = create_param_var(doc, "bracket_base_length", bracket_base_length)
    p_wid = create_param_var(doc, "bracket_base_width", bracket_base_width)
    p_thi = create_param_var(doc, "bracket_base_thickness", bracket_base_thickness)
    
    # Base Sketch (XY Plane)
    base_sketch = create_sketch(doc, body, "BaseSketch", "XY_Plane", 0.0)
    
    # Define rectangle: X from 0 to Length, Y from -Width/2 to Width/2
    # Center at (0,0)
    add_line(base_sketch, App.Vector(-p_wid.Value/2, -p_len.Value/2, 0), App.Vector(p_wid.Value/2, -p_len.Value/2, 0))
    add_line(base_sketch, App.Vector(p_wid.Value/2, -p_len.Value/2, 0), App.Vector(p_wid.Value/2, p_len.Value/2, 0))
    add_line(base_sketch, App.Vector(p_wid.Value/2, p_len.Value/2, 0), App.Vector(-p_wid.Value/2, p_len.Value/2, 0))
    add_line(base_sketch, App.Vector(-p_wid.Value/2, p_len.Value/2, 0), App.Vector(-p_wid.Value/2, -p_len.Value/2, 0))
    
    # Constraints
    add_constraint(base_sketch, "Fixed", 0, 1) # Fix point
    add_constraint(base_sketch, "Horizontal", 0, 1)
    add_constraint(base_sketch, "Horizontal", 0, 2)
    add_constraint(base_sketch, "Horizontal", 0, 3)
    add_constraint(base_sketch, "Vertical", 0, 1)
    add_constraint(base_sketch, "Vertical", 0, 2)
    add_constraint(base_sketch, "Vertical", 0, 3)
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 1) # Corners
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 2)
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 3)
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 4)
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 5)
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 6)
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 7)
    add_constraint(base_sketch, "Coincident", 0, 2, 1, 8)
    
    # Pad
    pad = body.newObject("PartDesign::Pad", "BasePad")
    pad.Profile = base_sketch
    pad.Length = p_thi.Value
    pad.Type = "Solid"
    
    doc.recompute()
    return body

def build_hinge_cheeks(doc, body, p_len, p_wid, p_thi, p_hinge):
    """Builds the two hinge cheeks."""
    
    # Parameters
    p_hole_d = create_param_var(doc, "hinge_pin_hole_diameter", p_hinge.hinge_pin_hole_diameter)
    p_arc_r = create_param_var(doc, "hinge_cheek_outer_arc_radius", p_hinge.hinge_cheek_outer_arc_radius)
    p_arc_s = create_param_var(doc, "hinge_cheek_outer_arc_start_angle", p_hinge.hinge_cheek_outer_arc_start_angle)
    p_arc_e = create_param_var(doc, "hinge_cheek_outer_arc_end_angle", p_hinge.hinge_cheek_outer_arc_end_angle)
    p_x_thi = create_param_var(doc, "hinge_cheek_x_thickness", p_hinge.hinge_cheek_x_thickness)
    p_inner_off = create_param_var(doc, "hinge_cheek_inner_face_offset_from_midplane", p_hinge.hinge_cheek_inner_face_offset_from_midplane)
    p_axis_y = create_param_var(doc, "hinge_axis_y", p_hinge.hinge_axis_y)
    p_axis_z = create_param_var(doc, "hinge_axis_z", p_hinge.hinge_axis_z)
    
    # Left Cheek (Negative X)
    # Sketch on XZ plane, offset by -p_inner_off
    left_sketch = create_sketch(doc, body, "LeftCheekSketch", "XZ_Plane", -p_inner_off.Value)
    
    # Geometry for Left Cheek
    # Center of cheek is at X = -p_inner_off, Z = 0.
    # We need to define the profile in the XZ plane.
    # The cheek extends from X = -p_inner_off - p_x_thi to X = -p_inner_off.
    # Wait, the description says "extend it outward by hinge_cheek_x_thickness".
    # Usually "outward" from the midplane means further negative X.
    # So X range: [-p_inner_off - p_x_thi, -p_inner_off].
    
    # Let's define the profile relative to the sketch origin (which is at X=-p_inner_off, Z=0).
    # We will draw the profile such that the inner face is at X=0 (local) and outer is at X=-p_x_thi.
    
    # Points:
    # Inner Top: (0, p_axis_y)
    # Inner Bottom: (0, -p_axis_y)
    # Outer Top Arc Start: (-p_x_thi, p_axis_y)
    # Outer Top Arc End: (-p_x_thi, -p_axis_y)
    # Outer Bottom Arc Start: (-p_x_thi, -p_axis_y)
    # Outer Bottom Arc End: (-p_x_thi, p_axis_y)
    # Wait, the arc connects the top and bottom flanks.
    # Flanks are straight lines from Inner Top to Outer Top, and Inner Bottom to Outer Bottom.
    # Then an arc connects Outer Top to Outer Bottom.
    
    # Let's refine the points based on "crown with ... arc ... join it to the base top with straight rear and front flanks"
    # Base top is at Z = p_thi/2. Base bottom is at Z = -p_thi/2.
    # The sketch is on XZ plane.
    # The "base top" in the sketch context corresponds to the line Z = p_thi/2.
    # The "base bottom" corresponds to Z = -p_thi/2.
    
    # Let's define the profile vertices:
    # 1. Inner Top: (0, p_axis_y)
    # 2. Inner Bottom: (0, -p_axis_y)
    # 3. Outer Top: (-p_x_thi, p_axis_y)
    # 4. Outer Bottom: (-p_x_thi, -p_axis_y)
    # 5. Outer Arc: Connects Outer Top and Outer Bottom with radius p_arc_r.
    #    The arc center is at (0, 0) relative to the sketch origin? 
    #    If the arc is centered at (0,0), then the distance from (0,0) to Outer Top is p_x_thi.
    #    But the radius is p_arc_r. So the arc center must be shifted.
    #    Actually, the description says "form the crown with ... arc ...".
    #    Usually, this implies the arc is part of the outer boundary.
    #    If the arc radius is R, and it connects (X_out, Y_top) and (X_out, Y_bot), 
    #    and the flanks are straight, then the arc center is at (X_out - R, 0) if the arc bulges out?
    #    Or (X_out + R, 0) if it bulges in?
    #    "Crown" usually implies bulging out.
    #    Let's assume the arc center is at (X_center, 0).
    #    Distance from center to (X_out, Y_top) is R.
    #    (X_out - X_center)^2 + Y_top^2 = R^2.
    #    We know Y_top = p_axis_y.
    #    So X_center = X_out - sqrt(R^2 - Y_top^2).
    #    But we also have start and end angles.
    #    Angle of Top point: atan2(Y_top, X_out - X_center).
    #    Angle of Bottom point: atan2(-Y_top, X_out - X_center).
    #    The difference should match the given angles.
    #    Given: start = -35 deg, end = 148.7 deg.
    #    This implies the arc spans from -35 to 148.7.
    #    Let's calculate the required geometry to match these angles.
    #    Let the arc center be at (Cx, 0).
    #    Point A (Top): (X_out, Y_top). Angle = atan2(Y_top, X_out - Cx).
    #    Point B (Bot): (X_out, -Y_top). Angle = atan2(-Y_top, X_out - Cx).
    #    We need Angle_A = -35 deg (or 325 deg) and Angle_B = 148.7 deg?
    #    Wait, -35 to 148 is a span of ~183 degrees.
    #    If we go from -35 to 148, we pass through 0.
    #    So Top is at -35, Bottom is at 148? That would mean the arc goes "over" the top.
    #    Or Top is at 148 and Bottom is at -35 (going clockwise)?
    #    Let's assume standard counter-clockwise.
    #    Start = -35, End = 148.7.
    #    Top point angle = -35? Bottom point angle = 148.7?
    #    If Top is at -35, then Y_top must be negative? No, Y_top is positive.
    #    So Top point angle must be positive?
    #    Maybe the angles are defined differently or the arc is on the other side.
    #    Let's try: Top point angle = 148.7, Bottom point angle = -35 (which is 325).
    #    Span = 325 - 148.7 = 176.3 degrees.
    #    This looks like a valid arc.
    #    So:
    #    Top Point: (X_out, Y_top) -> Angle 148.7
    #    Bottom Point: (X_out, -Y_top) -> Angle -35
    #    Center (Cx, 0).
    #    X_out - Cx = R * cos(148.7)
    #    Y_top = R * sin(148.7)
    #    Check consistency: Y_top / sin(148.7) should equal R.
    #    And X_out - Cx = R * cos(148.7).
    #    Also check bottom: -Y_top = R * sin(-35).
    #    sin(148.7) = sin(180-31.3) = sin(31.3).
    #    sin(-35) = -sin(35).
    #    These are not equal. 31.3 != 35.
    #    The provided angles might be specific to the design and not perfectly symmetric with the axis, 
    #    OR the "hinge_axis_y" is not the midpoint of the arc chord.
    #    However, the problem states "Place the hinge axis at hinge_axis_y".
    #    This implies the axis of rotation is at Y = hinge_axis_y.
    #    The arc is the "crown".
    #    Let's assume the arc is defined by the angles and radius, and we construct the points accordingly.
    #    We will place the arc using the given angles and radius.
    #    We need to find the center (Cx, 0) such that the arc passes through the flanks.
    #    Actually, let's just construct the arc geometry directly using the angles.
    #    We need two points on the arc: P_start and P_end.
    #    P_start angle = -35 deg. P_end angle = 148.7 deg.
    #    Radius = R.
    #    Center = (0, 0) in the local arc coordinate system?
    #    If we set the arc center at (0,0), then P_start = (R*cos(-35), R*sin(-35)).
    #    P_end = (R*cos(148.7), R*sin(148.7)).
    #    Then we need to connect these to the straight flanks.
    #    The flanks are at Y = hinge_axis_y and Y = -hinge_axis_y?
    #    No, the hinge axis is at Y = hinge_axis_y.
    #    The cheek is symmetric about Z=0? Yes.
    #    So the top flank is at Y = hinge_axis_y.
    #    The bottom flank is at Y = -hinge_axis_y.
    #    So the arc must connect (X_out, hinge_axis_y) and (X_out, -hinge_axis_y).
    #    This implies the arc center is at (X_center, 0).
    #    And the angles given must correspond to the angles of these points relative to the center.
    #    Let's solve for X_center and R given Y_top, angles.
    #    Y_top = R * sin(theta_top).
    #    X_out - X_center = R * cos(theta_top).
    #    We have Y_top = 12.0.
    #    We have theta_top = 148.7 deg? Or -35?
    #    If theta_top = 148.7, sin(148.7) = 0.52. R = 12 / 0.52 = 23.
    #    If theta_bot = -35, sin(-35) = -0.57. R = 12 / 0.57 = 21.
    #    R is not consistent.
    #    Maybe the angles are not relative to the center
