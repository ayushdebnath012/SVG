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

# --- Base Part Parameters ---
params = {
    "locking_jaw_thickness": 46.0,
    "ball_contact_arc_radius": 25.0,
    "ball_contact_arc_start_angle": -143.6036437,
    "main_upper_left_junction_longitudinal_offset": -2.29,
    "main_upper_left_junction_vertical_offset": 3.0,
    "main_upper_run_length": 28.0,
    "upper_nose_arc_radius": 8.0,
    "upper_nose_center_longitudinal_offset_from_ball_contact_center": 36.23,
    "upper_nose_center_vertical_offset_from_ball_contact_center": 0.5,
    "main_nose_tip_longitudinal_offset_from_ball_contact_center": 57.46,
    "main_nose_tip_vertical_offset_from_ball_contact_center": -9.79,
    "main_lower_run_length": 41.87,
    "side_relief_pocket_depth": 6.0,
    "ball_socket_radius": 25.4,
    "ball_socket_center_lateral_offset_from_jaw_midplane": -6.75,
    "ball_socket_center_longitudinal_offset_from_ball_contact_center": 3.64,
    "side_plate_thickness": 4.0,
    "side_plate_upper_hook_radius": 5.45,
    "side_plate_upper_hook_sweep_angle": 60.0,
    "side_plate_lower_fillet_radius": 3.0,
    "side_plate_top_edge_longitudinal_offset_from_ball_contact_center": 33.17,
    "side_plate_lower_fillet_center_offset_from_top_edge": 9.78,
    "side_plate_outer_height_above_main_lower_run": 12.35,
}

# --- Edit Part Parameters ---
edit_params = {
    "rear_socket_arc_radius": 8.5,
    "rear_socket_straight_side_spacing": 13.5,
    "rear_socket_center_longitudinal_offset_from_ball_contact_center": 9.64,
}

def create_feature_tree(base_params, edit_params=None):
    """
    Creates a FreeCAD document with a PartDesign Body containing the requested geometry.
    Returns the document object.
    """
    doc = App.newDocument("PartDesign_Jaw")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create Parameters Object (Editable)
    params_obj = body.newObject("App::VarSet", "Parameters")
    for name, value in base_params.items():
        params_obj.addProperty("App::PropertyLength", name, "Dimensions", f"Parameter {name}")
        params_obj[name] = value
    
    if edit_params:
        for name, value in edit_params.items():
            params_obj.addProperty("App::PropertyLength", name, "Dimensions", f"Edit Parameter {name}")
            params_obj[name] = value

    # Helper to get plane
    def get_plane(plane_name):
        return doc.getObject(plane_name)

    # Helper to add geometry to sketch
    def add_line(sketch, p1, p2):
        sketch.addGeometry(Part.LineSegment(p1, p2), False)

    def add_circle(sketch, center, radius):
        sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)

    def add_constraint(sketch, constraint_type, obj1, idx1, obj2, idx2, value=None):
        sketch.addConstraint(Sketcher.Constraint(constraint_type, obj1, idx1, obj2, idx2, value), False)

    # 1. Main Body Profile Sketch (XY Plane)
    # This sketch defines the longitudinal profile of the jaw.
    # Origin: Center of Ball Contact Arc.
    # X: Longitudinal (Z in real world usually, but let's stick to Sketcher XY for profile)
    # Y: Vertical (Thickness direction)
    
    sketch_main = body.newObject("Sketcher::SketchObject", "MainProfile")
    sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_main.Support = (get_plane("XY_Plane"), [""])
    sketch_main.MapMode = "FlatFace"
    
    # Geometry Construction
    # We need to construct the profile points based on the parameters.
    # Let's define points relative to the Ball Contact Arc Center (0,0).
    
    # Ball Contact Arc
    r_bc = params["ball_contact_arc_radius"]
    start_angle = params["ball_contact_arc_start_angle"]
    end_angle = start_angle + 180 # Assuming it spans 180 degrees or similar, but let's check context. 
    # "concave ball-contact edge". Usually a semi-circle or specific arc. 
    # Given "start_angle", let's assume it goes from start_angle to start_angle + 180 for a full concave face? 
    # Or maybe just the specific arc. Let's assume a semi-circle for the main contact face for simplicity unless specified otherwise.
    # Actually, let's look at the "nose" and "lower run".
    # Let's assume the arc is the main face.
    
    # Let's define the profile path:
    # 1. Start at bottom left of the arc.
    # 2. Arc to top left of the arc.
    # 3. Upper run.
    # 4. Upper nose arc.
    # 5. Nose tip.
    # 6. Lower run.
    # 7. Bottom of arc.
    
    # Coordinates (X, Y)
    # Ball Contact Arc Center: (0, 0)
    # Start Angle: -143.6 deg. End Angle: -143.6 + 180 = 36.4 deg? 
    # Let's assume the arc covers the main contact area.
    
    # Point A: Start of Arc
    angle_start_rad = math.radians(start_angle)
    p_start = App.Vector(r_bc * math.cos(angle_start_rad), r_bc * math.sin(angle_start_rad))
    
    # Point B: End of Arc (Top Left)
    # Assuming 180 degree span for the concave face? Or maybe just the arc defined.
    # Let's assume the arc goes from start_angle to start_angle + 180.
    angle_end_rad = math.radians(start_angle + 180)
    p_end_arc = App.Vector(r_bc * math.cos(angle_end_rad), r_bc * math.sin(angle_end_rad))
    
    # Upper Left Junction
    # Offset from Ball Contact Center
    # Longitudinal (X): main_upper_left_junction_longitudinal_offset
    # Vertical (Y): main_upper_left_junction_vertical_offset
    p_junction = App.Vector(params["main_upper_left_junction_longitudinal_offset"], params["main_upper_left_junction_vertical_offset"])
    
    # Upper Run
    # From Junction to Nose Center X
    # Length: main_upper_run_length
    # So Nose Center X = p_junction.X + main_upper_run_length
    nose_center_x = p_junction.X + params["main_upper_run_length"]
    nose_center_y = params["upper_nose_center_vertical_offset_from_ball_contact_center"]
    p_nose_center = App.Vector(nose_center_x, nose_center_y)
    
    # Upper Nose Arc
    # Radius: upper_nose_arc_radius
    # From p_nose_center to Nose Tip
    nose_tip_x = params["main_nose_tip_longitudinal_offset_from_ball_contact_center"]
    nose_tip_y = params["main_nose_tip_vertical_offset_from_ball_contact_center"]
    p_nose_tip = App.Vector(nose_tip_x, nose_tip_y)
    
    # Lower Run
    # From Nose Tip to Bottom of Arc
    # Length: main_lower_run_length
    # So Bottom of Arc X = nose_tip_x + main_lower_run_length
    # Bottom of Arc Y should be roughly -r_bc (if arc is symmetric around X axis? No, arc is rotated).
    # Let's assume the bottom of the arc is at the same Y level as the start of the arc? 
    # Or simply, the lower run connects the nose tip to the bottom of the jaw.
    # Let's assume the bottom of the jaw is at Y = -r_bc (relative to arc center) if the arc is a semi-circle.
    # But the arc is rotated.
    # Let's assume the profile closes at the bottom of the arc.
    # Let's calculate the bottom of the arc based on the start angle + 180.
    # p_bottom_arc = p_end_arc (calculated above).
    
    # Let's refine the profile construction:
    # 1. Line from p_start to p_junction
    # 2. Line from p_junction to p_nose_center
    # 3. Arc from p_nose_center to p_nose_tip
    # 4. Line from p_nose_tip to p_bottom_arc (Wait, main_lower_run_length is given)
    # Let's trust the lengths.
    # p_bottom_arc_x = p_nose_tip.x + params["main_lower_run_length"]
    # p_bottom_arc_y = -params["ball_contact_arc_radius"] (Assuming the jaw thickness is defined by the arc radius roughly, but we have locking_jaw_thickness)
    
    # Let's use the explicit coordinates derived from offsets.
    # p_start: (r*cos(-143.6), r*sin(-143.6))
    # p_end_arc: (r*cos(36.4), r*sin(36.4)) -> This is the top left.
    # p_junction: (-2.29, 3.0)
    # p_nose_center: (36.23 - 2.29 + 28, 0.5) -> Wait, offset is from ball contact center.
    # p_nose_center = (36.23, 0.5)
    # p_nose_tip = (57.46, -9.79)
    # p_bottom_arc: (57.46 + 41.87, -25.0) -> (99.33, -25.0)
    
    # Let's re-verify the "Upper Left Junction".
    # "main_upper_left_junction_longitudinal_offset = -2.29"
    # "main_upper_left_junction_vertical_offset = 3.0"
    # This point connects the Arc and the Upper Run.
    
    # Profile Points:
    # 1. p_start (Bottom Left of Arc)
    # 2. p_end_arc (Top Left of Arc) -> Wait, the arc is concave. The profile is the OUTSIDE.
    # So the profile goes from p_start (bottom) to p_end_arc (top) via the arc?
    # No, the arc is the "concave ball-contact edge". This is an internal feature or the main face?
    # "solid main body... longitudinal profile contains the concave ball-contact edge".
    # This implies the outer face is concave.
    # So the profile is the arc itself.
    # Start at p_start, go along arc to p_end_arc.
    # Then line to p_junction?
    # p_junction is at (-2.29, 3.0). p_end_arc is at (25*cos(36.4), 25*sin(36.4)) = (20.1, 14.9).
    # This doesn't match.
    
    # Alternative Interpretation:
    # The "concave ball-contact edge" is the inner surface of the jaw?
    # "locking jaw... solid main body... longitudinal profile contains the concave ball-contact edge".
    # Usually, a locking jaw has a concave face to grip the ball.
    # So the profile is the arc.
    # Let's assume the profile is the arc from start_angle to start_angle + 180.
    # p_start = (25*cos(-143.6), 25*sin(-143.6)) = (-20.1, -14.9)
    # p_end = (25*cos(36.4), 25*sin(36.4)) = (20.1, 14.9)
    # p_junction = (-2.29, 3.0). This is inside the arc?
    # Maybe the "concave edge" is the inner radius, and the outer profile is defined by the junctions?
    # "horizontal upper and lower runs, a rounded upper nose".
    # This sounds like the OUTER profile.
    # So the outer profile has a concave section.
    # Let's assume the outer profile follows the arc from p_start to p_end.
    # Then from p_end (top left), we go to p_junction?
    # p_end (20.1, 14.9) to p_junction (-2.29, 3.0).
    # Then upper run to p_nose_center (36.23, 0.5).
    # Then nose arc to p_nose_tip (57.46, -9.79).
    # Then lower run to p_bottom (99.33, -25.0).
    # Then close back to p_start (-20.1, -14.9).
    
    # This seems consistent.
    
    # Let's build the sketch geometry.
    # We need to add an arc. Sketcher doesn't have a direct "Arc between two points with radius" constraint easily without defining center.
    # We can define the arc by center and radius.
    # Center: (0,0), Radius: 25.
    # Start Angle: -143.6, End Angle: 36.4.
    
    # Add Arc
    add_circle(sketch_main, App.Vector(0, 0), params["ball_contact_arc_radius"])
    # We need to constrain the arc start/end to the lines.
    # Actually, let's just add the lines and arcs and constrain them.
    
    # Add Line 1: p_start to p_end (Arc) -> We use the circle geometry.
    # Add Line 2: p_end to p_junction
    add_line(sketch_main, p_end_arc, p_junction)
    # Add Line 3: p_junction to p_nose_center
    add_line(sketch_main, p_junction, p_nose_center)
    # Add Arc 2: p_nose_center to p_nose_tip
    # Center of nose arc?
    # We have radius and two points.
    # Let's assume the nose arc is tangent to the lines? Or just defined by center.
    # "rounded upper nose".
    # Let's assume the center is at p_nose_center + (0, radius)? No.
    # Let's assume the arc connects p_nose_center and p_nose_tip.
    # We can define an arc geometry with a center.
    # Let's guess the center is at (nose_center_x, nose_center_y + radius)?
    # Or maybe the arc is part of a circle centered at (nose_center_x, nose_center_y + radius)?
    # Let's try to infer the center.
    # If the arc is "rounded", it's likely tangent to the incoming and outgoing lines.
    # Incoming: p_junction -> p_nose_center. Vector: (36.23 - (-2.29), 0.5 - 3.0) = (38.52, -2.5).
    # Outgoing: p_nose_tip -> p_bottom. Vector: (99.33 - 57.46, -25 - (-9.79)) = (41.87, -15.21).
    # This is getting complex for a script.
    # Let's simplify: Define the nose arc by its center.
    # Assume the nose arc center is at (nose_center_x, nose_center_y + radius).
    # Let's try: Center = (36.23, 0.5 + 8.0) = (36.23, 8.5).
    # Check distance to p_nose_center: 8.0. Correct.
    # Check distance to p_nose_tip: sqrt((57.46-36.23)^2 + (-9.79-8.5)^2) = sqrt(21.23^2 + 18.29^2) = sqrt(450 + 334) = 28.3. Not 8.
    # So the center is not simply above.
    # Let's assume the nose arc is defined by the two points and the radius.
    # We can add an arc geometry with a center.
    # Let's assume the center is at (nose_center_x + dx, nose_center_y + dy).
    # Let's just add the arc and constrain it to pass through the points.
    # But Sketcher doesn't support "Arc through 2 points with radius" directly as a primitive.
    # We can use a circle and constrain it.
    # Let's assume the nose arc is a circle centered at (nose_center_x, nose_center_y + radius) is wrong.
    # Let's assume the nose arc is a circle centered at (nose_center_x, nose_center_y - radius)?
    # Distance to p_nose_tip: sqrt((57.46-36.23)^2 + (-9.79 - (0.5-8))^2) = sqrt(21.23^2 + (-1.
