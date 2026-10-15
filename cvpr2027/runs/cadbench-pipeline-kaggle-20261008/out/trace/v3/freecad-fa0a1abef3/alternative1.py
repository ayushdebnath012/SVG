import FreeCAD as App
import Part
import math
import os

# Ensure we are in FreeCAD 1.1 environment
# No GUI elements are used.

def create_asymmetric_clevis():
    # Create Document
    doc = App.newDocument("AsymmetricClevis")
    
    # --- Parameters ---
    # Define a VarSet to hold all parameters for easy editing
    params = doc.addObject("App::VarSet", "Parameters")
    
    # Connector Body
    params.addProperty("App::PropertyLength", "connector_body_length", "Dimensions", "Length of central rectangular body")
    params.connector_body_length = 75.0
    params.addProperty("App::PropertyLength", "connector_body_width", "Dimensions", "Width of central rectangular body")
    params.connector_body_width = 45.0
    params.addProperty("App::PropertyLength", "connector_body_thickness", "Dimensions", "Thickness of central rectangular body")
    params.connector_body_thickness = 12.0

    # Large Clevis (Positive X end)
    params.addProperty("App::PropertyLength", "clevis_end_outer_diameter", "Dimensions", "Outer diameter of large clevis")
    params.clevis_end_outer_diameter = 45.0
    params.addProperty("App::PropertyLength", "pin_hole_diameter", "Dimensions", "Diameter of pin hole in large clevis")
    params.pin_hole_diameter = 25.0
    params.addProperty("App::PropertyLength", "clevis_slot_width_gap", "Dimensions", "Gap between clevis slots")
    params.clevis_slot_width_gap = 5.0
    params.addProperty("App::PropertyLength", "clevis_arc_center_x_offset", "Dimensions", "X offset of clevis arc center from body start")
    params.clevis_arc_center_x_offset = 37.5
    params.addProperty("App::PropertyLength", "clevis_body_depth", "Dimensions", "Depth of clevis extrusion")
    params.clevis_body_depth = 50.0
    params.addProperty("App::PropertyLength", "clevis_body_depth_offset", "Dimensions", "Z offset of clevis start from body top face")
    params.clevis_body_depth_offset = -20.0
    params.addProperty("App::PropertyAngle", "first_clevis_outer_slot_tangent_angle", "Dimensions", "Tangent angle for outer clevis slot")
    params.first_clevis_outer_slot_tangent_angle = 6.3793702
    params.addProperty("App::PropertyAngle", "first_clevis_inner_slot_tangent_angle", "Dimensions", "Tangent angle for inner clevis slot")
    params.first_clevis_inner_slot_tangent_angle = 11.536959
    params.addProperty("App::PropertyLength", "first_clevis_inner_prong_tangent_x", "Dimensions", "X coordinate for inner prong tangent")
    params.first_clevis_inner_prong_tangent_x = 49.7474487
    params.addProperty("App::PropertyLength", "first_clevis_outer_prong_tangent_x", "Dimensions", "X coordinate for outer prong tangent")
    params.first_clevis_outer_prong_tangent_x = 59.8606798
    params.addProperty("App::PropertyLength", "pin_hole_depth", "Dimensions", "Depth of pin hole cut")
    params.pin_hole_depth = 34.5
    params.addProperty("App::PropertyLength", "pin_hole_center_offset_x", "Dimensions", "X offset of pin hole center from clevis start")
    params.pin_hole_center_offset_x = 37.5

    # Small Fork (Negative X end)
    params.addProperty("App::PropertyLength", "clevis_fork_outer_arc_radius", "Dimensions", "Outer radius of fork arc")
    params.clevis_fork_outer_arc_radius = 17.5
    params.addProperty("App::PropertyLength", "clevis_fork_inner_arc_radius", "Dimensions", "Inner radius of fork arc")
    params.clevis_fork_inner_arc_radius = 7.5
    params.addProperty("App::PropertyAngle", "clevis_fork_arc_central_angle", "Dimensions", "Central angle of fork arc")
    params.clevis_fork_arc_central_angle = 180.0
    params.addProperty("App::PropertyLength", "clevis_fork_prong_straight_length", "Dimensions", "Straight length of fork prongs inward")
    params.clevis_fork_prong_straight_length = 15.0
    params.addProperty("App::PropertyLength", "clevis_fork_prong_thickness", "Dimensions", "Thickness of fork extrusion")
    params.clevis_fork_prong_thickness = 8.0
    
    # Fork Slots (Derived from parameters but stored for clarity if needed, 
    # though the prompt implies these define the geometry directly in the arm description.
    # However, the prompt says "smaller fork... concentric prong arcs, U-shaped opening... use corresponding clevis_fork and clevis_slot parameters"
    # But then it lists specific clevis_slot parameters under "Key parameters".
    # Let's assume the fork uses the specific slot parameters listed later in the text or derive them.
    # Actually, looking at the text: "The smaller fork... use the corresponding clevis_fork and clevis_slot parameters."
    # Then it lists "clevis_slot_arc_radius", "clevis_slot_straight_length", etc.
    # It seems there are two sets of slot parameters? Or maybe the fork uses the generic 'clevis_slot' set?
    # The prompt lists: clevis_slot_arc_radius, clevis_slot_arc_central_angle, clevis_slot_straight_length, clevis_slot_profile_width, clevis_slot_depth.
    # And later: clevis_fork_prong_thickness is the extrusion thickness.
    # Let's map the generic 'clevis_slot' parameters to the fork geometry as requested.
    params.addProperty("App::PropertyLength", "clevis_slot_arc_radius", "Dimensions", "Radius of slot arcs in fork")
    params.clevis_slot_arc_radius = 7.5
    params.addProperty("App::PropertyAngle", "clevis_slot_arc_central_angle", "Dimensions", "Central angle of slot arcs in fork")
    params.clevis_slot_arc_central_angle = 180.0
    params.addProperty("App::PropertyLength", "clevis_slot_straight_length", "Dimensions", "Straight length of slot in fork")
    params.clevis_slot_straight_length = 15.0
    params.addProperty("App::PropertyLength", "clevis_slot_profile_width", "Dimensions", "Width of slot profile in fork")
    params.clevis_slot_profile_width = 15.0
    params.addProperty("App::PropertyLength", "clevis_slot_depth", "Dimensions", "Depth of slot cut in fork")
    params.clevis_slot_depth = 34.5

    # Long Side Arm
    params.addProperty("App::PropertyLength", "clevis_pin_hole_diameter", "Dimensions", "Diameter of hole in arm end")
    params.clevis_pin_hole_diameter = 15.0
    params.addProperty("App::PropertyLength", "clevis_end_arc_radius", "Dimensions", "Radius of arm end")
    params.clevis_end_arc_radius = 20.0
    params.addProperty("App::PropertyAngle", "clevis_end_arc_central_angle", "Dimensions", "Central angle of arm end")
    params.clevis_end_arc_central_angle = 180.0
    params.addProperty("App::PropertyLength", "clevis_arm_length", "Dimensions", "Total length of arm profile")
    params.clevis_arm_length = 46.7196386
    params.addProperty("App::PropertyLength", "clevis_arm_width", "Dimensions", "Width of arm")
    params.clevis_arm_width = 40.0
    params.addProperty("App::PropertyLength", "clevis_arm_depth", "Dimensions", "Depth of arm")
    params.clevis_arm_depth = 45.0
    params.addProperty("App::PropertyLength", "clevis_arm_profile_start_x", "Dimensions", "X start of arm profile")
    params.clevis_arm_profile_start_x = 52.9513389
    params.addProperty("App::PropertyLength", "clevis_arm_end_center_x", "Dimensions", "X center of arm end")
    params.clevis_arm_end_center_x = 99.6709775
    params.addProperty("App::PropertyLength", "clevis_arm_end_center_z_offset", "Dimensions", "Z offset of arm end center")
    params.clevis_arm_end_center_z_offset = 9.0

    # Relief Slots on Arm
    params.addProperty("App::PropertyLength", "clevis_slot_length", "Dimensions", "Length of main relief slot")
    params.clevis_slot_length = 74.88
    params.addProperty("App::PropertyLength", "clevis_slot_width", "Dimensions", "Width of main relief slot")
    params.clevis_slot_width = 5.21
    params.addProperty("App::PropertyLength", "clevis_slot_y_min", "Dimensions", "Y min of main relief slot")
    params.clevis_slot_y_min = -2.71
    
    params.addProperty("App::PropertyLength", "upper_slot_length", "Dimensions", "Length of upper relief slot")
    params.upper_slot_length = 72.25
    params.addProperty("App::PropertyLength", "upper_slot_width", "Dimensions", "Width of upper relief slot")
    params.upper_slot_width = 6.96
    params.addProperty("App::PropertyLength", "upper_slot_y_min", "Dimensions", "Y min of upper relief slot")
    params.upper_slot_y_min = 16.3556146
    
    params.addProperty("App::PropertyLength", "lower_slot_length", "Dimensions", "Length of lower relief slot")
    params.lower_slot_length = 73.8
    params.addProperty("App::PropertyLength", "lower_slot_width", "Dimensions", "Width of lower relief slot")
    params.lower_slot_width = 10.06
    params.addProperty("App::PropertyLength", "lower_slot_y_min", "Dimensions", "Y min of lower relief slot")
    params.lower_slot_y_min = -26.4156146
    
    params.addProperty("App::PropertyLength", "slot_depth", "Dimensions", "Depth of relief slots")
    params.slot_depth = 73.6

    # --- PartDesign Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    
    # --- Central Body Sketch ---
    # Plane: XY
    sketch_body = body.newObject("Sketcher::SketchObject", "Sketch_CentralBody")
    sketch_body.Plane = (doc.getObject("XY_Plane"), [])
    sketch_body.ConstrainAuto = False
    
    # Rectangle for central body
    # Length = connector_body_length, Width = connector_body_width
    # Centered at (0,0)
    rect_body = Part.makeBox(
        params.connector_body_length, 
        params.connector_body_width, 
        0 # Z will be handled by offset later or just thickness=0 for now
    )
    sketch_body.addGeometry(rect_body, False)
    sketch_body.setExpression("Length", "Parameters.connector_body_length")
    sketch_body.setExpression("Width", "Parameters.connector_body_width")
    # Note: Sketcher::SketchObject in 1.1 often uses 'Length' and 'Width' for bounding box or specific constraints.
    # Better to use constraints.
    # Let's define vertices manually to be safe and clear.
    # Clear previous geometry
    sketch_body.removeGeometry()
    
    # Define rectangle vertices: Bottom-Left, Bottom-Right, Top-Right, Top-Left
    # Centered at (0,0,0)
    l = params.connector_body_length
    w = params.connector_body_width
    p1 = App.Vector(-l/2, -w/2, 0)
    p2 = App.Vector(l/2, -w/2, 0)
    p3 = App.Vector(l/2, w/2, 0)
    p4 = App.Vector(-l/2, w/2, 0)
    
    sketch_body.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_body.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_body.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_body.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Constraints
    # Coincident 0-1, 1-2, 2-3, 3-0 (Closed)
    # Symmetry? No, just closed loop.
    # Centered? Let's just constrain origin to center of line 1-2
    c1 = sketch_body.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Start at origin? No, let's constrain center to origin
    # Actually, let's constrain the center of the rectangle to the origin.
    # Midpoint of 0-1 is (0, -w/2). Midpoint of 2-3 is (0, w/2).
    # Let's just constrain the midpoint of edge 0-1 to the X axis? 
    # Simplest: Constrain midpoint of edge 0-1 to (0,0,0)? No, that fixes Y.
    # Let's constrain the center point (0,0) to the intersection of diagonals.
    # Or simply: Constrain midpoint of 0-1 to X_Axis and midpoint of 0-2 to Y_Axis.
    c_mid_x = sketch_body.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, 1, 1), "XY_Plane", "X_Axis")
    c_mid_y = sketch_body.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, 2, 2), "XY_Plane", "Y_Axis")
    # Wait, PointOnLine constraint syntax in 1.1: (EdgeIndex, PointOnEdge, ReferenceObject, ReferenceEdge/Point)
    # Let's use standard Coincident for corners to origin if we want alignment, but centering is better.
    # Let's just constrain the center of the loop to the origin.
    # We can add a point at center and constrain it.
    # Or just rely on the box placement if we construct it via Part.
    # Let's stick to the Part.makeBox approach but placed correctly.
    # Re-adding geometry using Part.makeBox placed at center.
    sketch_body.removeGeometry()
    # We need to add the box as a shape.
    # However, Sketcher::SketchObject expects lines/circles.
    # Let's use constraints to define the rectangle.
    sketch_body.removeGeometry()
    # Add 4 lines
    sketch_body.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_body.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_body.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_body.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Constraints:
    # 1. 4 coincident to form loop (optional if we constrain points)
    # 2. Center to origin
    # Let's constrain the midpoint of the bottom edge to origin.
    # Edge 0 is p1-p2. Midpoint is (0, -w/2).
    # Constrain midpoint to X_Axis (y=0).
    c_bottom_mid = sketch_body.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, 1, 1), "XY_Plane", "X_Axis")
    # Constrain midpoint of left edge (p4-p1) to Y_Axis (x=0).
    c_left_mid = sketch_body.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, 2, 2), "XY_Plane", "Y_Axis")
    
    # Close loop
    sketch_body.addConstraint(Sketcher.Constraint("Equal", 0, 2, 1, 1)) # Wait, Equal is for length?
    # Coincident to close loop
    c_close = sketch_body.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # This might not work as expected for closing
    # Standard way: Coincident last to first.
    # Edge 3 is p4-p1. Edge 0 is p1-p2.
    # Let's just add a constraint that makes it closed.
    # Actually, if we constrain midpoints to axes and lengths, it works.
    # Let's add length constraints.
    sketch_body.setExpression("Length", "Parameters.connector_body_length") # For edge 0? No, sketcher doesn't have direct edge length property like that usually.
    # Let's just define the geometry with constraints on points.
    # Let's simplify: Use Part.makeBox in the body directly? No, must use sketches.
    # Let's try to make the sketch define the rectangle by constraints.
    # Remove previous constraints
    sketch_body.clearConstraints()
    sketch_body.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_body.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_body.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_body.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Constraints:
    # Center of rectangle to origin.
    # We can add a point at (0,0) and constrain it to intersection of diagonals? No.
    # Let's constrain the center of the bounding box to origin.
    # Sketcher::SketchObject has properties like Center? No.
    # Let's constrain the midpoint of edge 0 (p1-p2) to the X axis.
    # And midpoint of edge 2 (p3-p4) to the X axis.
    # And midpoint of edge 1 (p2
