import FreeCAD as App
import Part
from pathlib import Path
import os
import tempfile

# --- Configuration & Parameters ---

# Base Part Parameters
PARAMS_BASE = {
    "bracket_base_length": 62.0,
    "bracket_base_width": 24.0,
    "bracket_base_thickness": 8.0,
}

# Edit Part Parameters (Target)
PARAMS_EDIT = {
    "hinge_pin_hole_diameter": 8.0,
    "hinge_cheek_outer_arc_radius": 10.0,
    "hinge_cheek_outer_arc_start_angle": -35.0003487,
    "hinge_cheek_outer_arc_end_angle": 148.6986094,
    "hinge_cheek_x_thickness": 6.0,
    "hinge_cheek_inner_face_offset_from_midplane": 8.0,
    "hinge_axis_y": 12.0,
    "hinge_axis_z": 27.0,
    "small_boss_inner_diameter": 3.0,
    "small_boss_outer_diameter": 6.0,
    "small_boss_depth": 10.0,
    "small_boss_start_inset_from_front": 13.0,
    "small_boss_seed_center_x": 20.0,
    "mounting_hole_diameter": 9.0,
    "mounting_hole_end_offset_x": 8.5,
}

def create_parametric_model(base_params, edit_params):
    doc = App.newDocument("Bracket_Assembly")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Helper to add geometry to a sketch object within the body
    def add_line(x, y):
        return body.newObject("Sketcher::Line", f"L_{x}_{y}")
    
    def add_circle(c, r):
        return body.newObject("Sketcher::Circle", f"C_{c}_{r}")
    
    def add_arc(c, r, start_angle, end_angle):
        # FreeCAD Sketcher Arc: Center, Radius, Start Angle, End Angle
        # Angles in degrees. 0 is +X, 90 is +Y.
        return body.newObject("Sketcher::Arc", f"A_{c}_{r}_{start_angle}_{end_angle}")
        
    def add_constraint(obj1, obj2, type, p1, p2):
        return body.newObject("Sketcher::Constraint", f"C_{type}_{p1}_{p2}")
    
    # Create Base Plate
    plate = body.newObject("PartDesign::Part", "Plate")
    # We will build the plate geometry using a Pad feature first to establish the volume,
    # or we can just use the sketch to define the footprint. 
    # To keep it purely PartDesign features: Sketch -> Pad.
    
    plate_sketch = body.newObject("Sketcher::SketchObject", "PlateSketch")
    plate_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    plate_sketch.Constraints = App.ActiveDocument.newObject("Sketcher::Constraint", "CSK_Plate")
    plate_sketch.Constraints.Visibility = False # Hide constraint object
    
    # Create lines for the base plate footprint
    # Length along X, Width along -Y (from rear edge)
    # Center at (0,0). 
    # X range: -L/2 to +L/2
    # Y range: 0 to -W (since it extends from rear edge (0) to front (negative Y))
    
    line_len = body.newObject("Sketcher::Line", "Plate_Len")
    line_len.Placement = App.Placement(App.Vector(-params["bracket_base_length"]/2, 0, 0))
    line_len.Line = Part.LineSegment(App.Vector(-params["bracket_base_length"]/2, 0, 0), 
                                      App.Vector(params["bracket_base_length"]/2, 0, 0))
    
    line_wid = body.newObject("Sketcher::Line", "Plate_Wid")
    line_wid.Placement = App.Placement(App.Vector(params["bracket_base_length"]/2, 0, 0))
    line_wid.Line = Part.LineSegment(App.Vector(params["bracket_base_length"]/2, 0, 0), 
                                      App.Vector(params["bracket_base_length"]/2, -params["bracket_base_width"], 0))
    
    line_bot = body.newObject("Sketcher::Line", "Plate_Bot")
    line_bot.Placement = App.Placement(App.Vector(0, -params["bracket_base_width"], 0))
    line_bot.Line = Part.LineSegment(App.Vector(0, -params["bracket_base_width"], 0), 
                                      App.Vector(-params["bracket_base_length"]/2, -params["bracket_base_width"], 0))
    
    line_top = body.newObject("Sketcher::Line", "Plate_Top")
    line_top.Placement = App.Placement(App.Vector(-params["bracket_base_length"]/2, 0, 0))
    line_top.Line = Part.LineSegment(App.Vector(-params["bracket_base_length"]/2, 0, 0), 
                                      App.Vector(0, -params["bracket_base_width"], 0))
    
    # Add constraints to make it a closed loop (Rectangle)
    # Coincident endpoints
    c1 = body.newObject("Sketcher::Constraint", "C_Coin_1")
    c1.P1 = "Plate_Len", 2 # End of Len
    c1.P2 = "Plate_Top", 1 # Start of Top
    c1.Type = "Coincident"
    
    c2 = body.newObject("Sketcher::Constraint", "C_Coin_2")
    c2.P1 = "Plate_Top", 2
    c2.P2 = "Plate_Wid", 1
    c2.Type = "Coincident"
    
    c3 = body.newObject("Sketcher::Constraint", "C_Coin_3")
    c3.P1 = "Plate_Wid", 2
    c3.P2 = "Plate_Bot", 1
    c3.Type = "Coincident"
    
    c4 = body.newObject("Sketcher::Constraint", "C_Coin_4")
    c4.P1 = "Plate_Bot", 2
    c4.P2 = "Plate_Len", 1
    c4.Type = "Coincident"
    
    # Dimensions
    c_len = body.newObject("Sketcher::Constraint", "C_Dim_Len")
    c_len.P1 = "Plate_Len", 0
    c_len.P2 = "Plate_Len", 1
    c_len.Type = "Length"
    c_len.Length = params["bracket_base_length"]
    
    c_wid = body.newObject("Sketcher::Constraint", "C_Dim_Wid")
    c_wid.P1 = "Plate_Wid", 0
    c_wid.P2 = "Plate_Wid", 1
    c_wid.Type = "Length"
    c_wid.Length = params["bracket_base_width"]
    
    # Horizontal/Vertical constraints to lock orientation
    c_h = body.newObject("Sketcher::Constraint", "C_Horiz")
    c_h.P1 = "Plate_Len", 0
    c_h.P2 = "Plate_Len", 1
    c_h.Type = "Horizontal"
    
    c_v = body.newObject("Sketcher::Constraint", "C_Vert")
    c_v.P1 = "Plate_Wid", 0
    c_v.P2 = "Plate_Wid", 1
    c_v.Type = "Vertical"
    
    plate_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    plate_sketch.Placement.Rotation = App.Rotation(0, 0, 0) # XY Plane
    
    # Pad the base plate
    pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
    pad_plate.Profile = plate_sketch
    pad_plate.Length = params["bracket_base_thickness"]
    pad_plate.MidPlane = False
    pad_plate.Reverse = False
    
    # --- Hinge Cheeks Construction ---
    
    # 1. Left Cheek (Negative X side)
    # Profile Plane: YZ plane at x = -offset
    left_offset = params["hinge_cheek_inner_face_offset_from_midplane"]
    
    # Create a sketch on the YZ plane
    # We need to offset the sketch placement to the correct X position
    cheek_left_sketch = body.newObject("Sketcher::SketchObject", "CheekLeft_Sketch")
    cheek_left_sketch.Placement = App.Placement(App.Vector(-left_offset, 0, 0))
    cheek_left_sketch.Placement.Rotation = App.Rotation(0, 0, 90) # Rotate to face Z (Normal to YZ plane)
    # Actually, standard YZ plane normal is X. To sketch ON YZ plane, we usually use XY plane rotated 90 deg around X.
    # Let's use the plane definition: X axis is normal.
    # FreeCAD: Sketcher::SketchObject on a plane.
    # If we use XY plane and rotate 90 deg around X, the normal becomes Y.
    # Let's use a simpler approach: Place the sketch at (-left_offset, 0, 0) with normal X (Y-Z plane).
    # Rotation to align normal to X: 0 deg around Y/Z? 
    # Default XY plane normal is Z. We want normal X.
    # Rotation: 90 deg around Y axis.
    cheek_left_sketch.Placement.Rotation = App.Rotation(0, 1, 0, 90) 
    
    # Draw the profile for the Left Cheek
    # It extends from base_thickness to base_thickness + thickness
    # Inner face is at Z = base_thickness.
    # Outer face is at Z = base_thickness + thickness.
    # Shape: Arc connecting outer face to inner face? 
    # Description: "crown with hinge_cheek_outer_arc_radius from start to end"
    # This implies the cheek is an arc shape in the YZ plane.
    
    # Coordinates in YZ plane (Local to sketch):
    # Z axis is global Z. Y axis is global Y.
    # Center of arc: hinge_axis_z relative to base bottom? 
    # "Place the hinge axis at hinge_axis_y and hinge_axis_z"
    # Usually implies local to the cheek volume.
    # Let's assume the hinge axis is at Y = hinge_axis_y, Z = hinge_axis_z relative to the base bottom (Z=0).
    # So the arc center is (Y=hinge_axis_y, Z=hinge_axis_z).
    # The arc radius is hinge_cheek_outer_arc_radius.
    # The arc connects the outer face (Z = base_thickness + thickness) to the inner face (Z = base_thickness).
    
    # Wait, the description says "extend it outward by hinge_cheek_x_thickness".
    # And "crown with ... arc".
    # This suggests the cheek is NOT a flat plate, but a curved block.
    # The "inner face" is a flat plane at Z=base_thickness.
    # The "outer face" is an arc.
    # The "flanks" connect the base top (Z=base_thickness) to the arc start/end.
    
    # Let's construct the profile in the YZ plane.
    # Origin of sketch is at (-left_offset, 0, 0).
    # Base Top is at Z = params["bracket_base_thickness"].
    # Inner Face is a line at Z = params["bracket_base_thickness"].
    # We need to draw the profile that goes from the base top, curves outwards, and ends at the inner face?
    # Or does the arc form the outer boundary and straight lines form the sides?
    # "join it to the base top with straight rear and front flanks"
    # So: 
    # 1. Start at Base Top (Y=0, Z=base_thickness).
    # 2. Go to Arc Start.
    # 3. Follow Arc to Arc End.
    # 4. Go to Base Top (Y=?, Z=base_thickness)? No, that would close the loop at Z=base_thickness.
    # The profile must enclose the cheek.
    # The cheek sits on the base.
    # Profile: 
    # - Line from (Y=0, Z=base_thickness) to Arc Start.
    # - Arc from Start to End.
    # - Line from Arc End to (Y=?, Z=base_thickness).
    # - Line closing back to start?
    # Wait, the "Inner Face" is a flat plane.
    # So the profile must include a segment at Z = base_thickness.
    # The arc is the "crown".
    # So the profile goes:
    # 1. Point A (on Base Top, e.g., Y=0, Z=base_thickness).
    # 2. Line to Point B (Start of Arc).
    # 3. Arc to Point C (End of Arc).
    # 4. Line to Point D (on Base Top, e.g., Y=width, Z=base_thickness).
    # 5. Line D to A.
    
    # Let's calculate the arc points.
    # Center: (Y_c, Z_c) = (params["hinge_axis_y"], params["hinge_axis_z"])
    # Radius: R = params["hinge_cheek_outer_arc_radius"]
    # Start Angle: params["hinge_cheek_outer_arc_start_angle"]
    # End Angle: params["hinge_cheek_outer_arc_end_angle"]
    # Note: Angles in FreeCAD Sketcher are typically measured from X-axis (0 deg) counter-clockwise.
    # In YZ plane: Y is "X" of the sketch, Z is "Y" of the sketch? 
    # If we rotated 90 deg around Y, the local X is Global Z, local Y is Global -X? No.
    # Rotation(0, 1, 0, 90): X -> Y, Y -> -Z, Z -> X.
    # This is getting complicated. Let's use explicit vectors for the sketch geometry.
    
    # Define the arc segment in the global coordinate system, then constrain it to the sketch plane.
    # Actually, easiest is to use the "Arc" object with explicit points if we know them, or standard Arc with angles relative to the sketch normal.
    # Let's assume standard angles relative to the sketch's local X axis (which is the sketch normal? No, usually Y).
    # Standard FreeCAD Sketcher Arc: Center, Radius, Start Angle, End Angle.
    # Angles are in the sketch plane. 0 is along the sketch X-axis. 90 along Y-axis.
    # If our sketch plane is YZ, and we rotated it so Z is the local Y (up) and Y is the local X (right)?
    # Let's stick to the Rotation: 90 deg around Y.
    # Global Z becomes Local Y (Up). Global Y becomes Local X (Right).
    # So an angle of 0 in the sketch is Global Y direction. 90 deg is Global Z direction.
    # The description gives angles. Let's assume they are relative to the Y axis (0 deg) or Z axis?
    # Usually "hinge axis" is the pivot.
    # Let's assume the angles are measured from the Y-axis (0 deg) towards the Z-axis (90 deg).
    
    # Calculate Arc Start and End points in Global Coordinates
    # Center: (0, params["hinge_axis_y"], params["hinge_axis_z"])
    # Radius: R
    # Angle 0 = Global Y direction. Angle 90 = Global Z direction.
    # Vector = R * (sin(theta), cos(theta), 0)? 
    # If 0 is Y: (R, 0, 0) in local -> (0, R, 0) in global?
    # Let's use: Y = R * sin(theta), Z = R * cos(theta).
    # Check: theta=0 -> Y=0, Z=R. (Vertical).
    # theta=90 -> Y=R, Z=0. (Horizontal).
    # The prompt says "crown". Usually arcs go from near-vertical to near-horizontal.
    # Let's assume the provided angles are from the Y-axis (0 deg) rotating towards Z.
    
    # Let's define the profile points:
    # Center of arc: (0, Y_c, Z_c)
    # Start Point: C + R * (sin(s), cos(s), 0)
    # End Point: C + R * (sin(e), cos(e), 0)
    
    Y_c = params["hinge_axis_y"]
    Z_c = params["hinge_axis_z"]
    R = params["hinge_cheek_outer_arc_radius"]
    s_angle = params["hinge_cheek_outer_arc_start_angle"]
    e_angle = params["hinge_cheek_outer_arc_end_angle"]
    
    # Helper to get point
    def get_arc_point(angle):
        # Assuming 0 deg is +Y, 90 deg is +Z
        y = Y_c + R * math.sin(math.radians(angle))
        z = Z_c + R * math.cos(math.radians(angle))
        return App.Vector(0, y, z)
    
    p_start = get_arc_point(s_angle)
    p_end = get_arc_point(e_angle)
    
    # We need to connect these to the base top.
    # Base Top Z = params["bracket_base_thickness"]
    # The arc should intersect the base top level? Or the flanks connect to it.
    # "join it to the base top with straight rear and front flanks"
    # This implies the arc endpoints are NOT necessarily on the base top, but connected by vertical lines?
    # Or the arc is the
