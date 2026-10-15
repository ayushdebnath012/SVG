import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

def main():
    # Create Document
    doc = App.newDocument("AsymmetricClevis")
    
    # --- Parameters ---
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
    
    # Fork Slots (Mapped from generic clevis_slot parameters)
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
    
    # --- 1. Central Body Sketch ---
    sketch_body = body.newObject("Sketcher::SketchObject", "Sketch_CentralBody")
    sketch_body.Plane = (doc.getObject("XY_Plane"), [])
    sketch_body.ConstrainAuto = False
    
    l = params.connector_body_length
    w = params.connector_body_width
    
    # Define rectangle vertices centered at origin
    p1 = App.Vector(-l/2, -w/2, 0)
    p2 = App.Vector(l/2, -w/2, 0)
    p3 = App.Vector(l/2, w/2, 0)
    p4 = App.Vector(-l/2, w/2, 0)
    
    sketch_body.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_body.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_body.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_body.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Constraints: Center to origin
    # Midpoint of bottom edge (0) to X_Axis
    sketch_body.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, 1, 1), "XY_Plane", "X_Axis")
    # Midpoint of left edge (3) to Y_Axis
    sketch_body.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, 2, 2), "XY_Plane", "Y_Axis")
    # Close loop
    sketch_body.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    
    # --- 2. Large Clevis Sketch ---
    # Plane: XZ (to extrude along Y? No, clevis is usually in XZ plane extruded along Y or XZ plane extruded along Z?)
    # "clevis... opens toward positive X... pin-hole cut enters from the positive-Z face"
    # This implies the clevis profile is in the XZ plane, and it is extruded along Y (width).
    # Wait, "pin-hole cut enters from the positive-Z face". If the profile is in XZ, the faces are parallel to XZ? No.
    # If profile is in XZ, extrusion is along Y. The faces created are parallel to XZ.
    # A hole entering from "positive-Z face" implies the face normal is Z.
    # This suggests the clevis profile is in the XY plane, extruded along Z?
    # Let's re-read: "clevis... opens toward positive X... pin-hole cut enters from the positive-Z face".
    # If the clevis is a split ring in the XZ plane (like a C-shape), the opening is along X.
    # The faces of this C-shape are parallel to the XZ plane? No, the faces are the surfaces of the ring.
    # If the ring is in XZ, the "top" and "bottom" faces are parallel to XZ? No, they are parallel to the plane of the ring? No.
    # A ring in XZ plane has a normal along Y. The faces are parallel to XZ? No, the faces are the surfaces of the material.
    # If I extrude a profile in XZ along Y, the resulting faces are parallel to XZ.
    # If I want a hole entering from the "positive-Z face", I need a face with normal +Z.
    # This implies the clevis profile is in the XY plane, and it is extruded along Z.
    # BUT, "clevis... opens toward positive X". If it's in XY, it opens along X.
    # "pin-hole cut enters from the positive-Z face". If extruded along Z, the top face is +Z.
    # This fits.
    # So: Profile in XY plane. Extrude along Z.
    # "clevis_body_depth_offset is measured from the central body's positive-Z face".
    # Central body is extruded along Z (thickness). Top face is at Z = connector_body_thickness/2.
    # Clevis starts at Z = connector_body_thickness/2 + clevis_body_depth_offset.
    
    sketch_clevis = body.newObject("Sketcher::SketchObject", "Sketch_Clevis")
    sketch_clevis.Plane = (doc.getObject("XY_Plane"), [])
    sketch_clevis.ConstrainAuto = False
    
    # Geometry construction for Clevis
    # Outer Diameter = 45. Radius = 22.5
    # Inner Diameter = ? Not given directly, but "clevis_slot_width_gap" is 5.0.
    # Usually gap is the difference between outer and inner diameters? Or the width of the slot?
    # "clevis_slot_width_gap" likely refers to the radial gap between the two arcs of the split ring.
    # Let's assume Inner Radius = Outer Radius - Gap/2? Or Gap is the full difference?
    # "split-ring profile... inner and outer circular boundaries share a center".
    # Let's assume the gap is the radial distance between the inner and outer arcs.
    # R_outer = 22.5. R_inner = 22.5 - 5.0 = 17.5? Or is the gap the width of the slot?
    # Let's assume R_inner = R_outer - clevis_slot_width_gap.
    R_outer = params.clevis_end_outer_diameter / 2.0
    R_inner = R_outer - params.clevis_slot_width_gap
    
    # Center X offset
    Cx = params.clevis_arc_center_x_offset
    
    # Tangent angles
    # "first_clevis_outer_slot_tangent_angle" and "first_clevis_inner_slot_tangent_angle"
    # These likely define the start/end angles of the arcs relative to the center.
    # "opens toward positive X". So the gap is on the positive X side.
    # The arcs should go from some angle to some angle, leaving a gap on the right.
    # Let's assume the angles are measured from the positive X axis (0 deg).
    # If it opens to +X, the gap is around 0 deg.
    # The arcs would go from -180 to -alpha and alpha to 180?
    # Or maybe the angles define the tangent direction at the start/end of the arc?
    # "tangent angle" usually means the angle of the tangent vector.
    # For a circle, tangent at angle theta is theta + 90.
    # Let's assume the angles given are the start/end angles of the arc segments.
    # Let's try: Outer arc goes from -180 + alpha_outer to alpha_outer?
    # Actually, let's look at the values: 6.37 deg and 11.53 deg. Small angles.
    # Maybe the gap is defined by these angles?
    # Let's assume the outer arc starts at -180 + 6.37 and ends at 180 - 6.37?
    # And inner arc starts at -180 + 11.53 and ends at 180 - 11.53?
    # This would create a gap on the right.
    
    # Let's construct the profile:
    # 1. Outer Arc (CCW or CW?)
    # Let's go CCW from -180 + alpha_outer to 180 - alpha_outer.
    # 2. Line segment closing the gap? No, it's a split ring.
    # 3. Inner Arc.
    # 4. Lines connecting inner to outer at the ends of the arcs.
    
    # Let's define the angles in radians.
    alpha_outer = math.radians(params.first_clevis_outer_slot_tangent_angle)
    alpha_inner = math.radians(params.first_clevis_inner_slot_tangent_angle)
    
    # Start angle for outer arc (measured from +X, CCW)
    # If gap is on +X, the arc starts at -180 + alpha_outer and goes to 180 - alpha_outer.
    start_outer = math.pi - alpha_outer
    end_outer = math.pi + alpha_outer # Wait, -180 is pi. 180 is -pi.
    # Let's use standard math: 0 is +X.
    # Gap is around 0.
    # Arc goes from -pi + alpha_outer to pi - alpha_outer.
    start_outer = -math.pi + alpha_outer
    end_outer = math.pi - alpha_outer
    
    # Inner arc:
    start_inner = -math.pi + alpha_inner
    end_inner = math.pi - alpha_inner
    
    # Points for Outer Arc
    p_outer_start = App.Vector(Cx + R_outer * math.cos(start_outer), R_outer * math.sin(start_outer), 0)
    p_outer_end = App.Vector(Cx + R_outer * math.cos(end_outer), R_outer * math.sin(end_outer), 0)
    
    # Points for Inner Arc
    p_inner_start = App.Vector(Cx + R_inner * math.cos(start_inner), R_inner * math.sin(start_inner), 0)
    p_inner_end = App.Vector(Cx + R_inner * math.cos(end_inner), R_inner * math.sin(end_inner), 0)
    
    # Tangent points for the connecting lines
    # The lines connect the end of the outer arc to the end of the inner arc.
    # We need the tangent points on the circles where the lines are tangent.
    # The problem gives "first_clevis_inner_prong_tangent_x" and "first_clevis_outer_prong_tangent_x".
    # These are likely the X-coordinates of the points where the prongs (connecting lines) are tangent to the arcs.
    # Let's use these to define the tangent points.
    
    # Tangent point on outer circle:
    # x = Cx + R_outer * cos(theta) = first_clevis_outer_prong_tangent_x
    # cos(theta) = (T_x - Cx) / R_outer
    # theta = acos(...)
    # Since it's on the right side (gap), theta is small positive or negative.
    # Let's assume the top prong connects at positive Y, bottom at negative Y.
    # So we need the tangent point in the first quadrant (for top) and fourth (for bottom).
    
    T_x_outer = params.first_clevis_outer_prong_tangent_x
    T_x_inner = params.first_clevis_inner_prong_tangent_x
    
    # Check if T_x is within range [-R, R]
    # If T_x > Cx + R, then the tangent is vertical? No, the line is vertical?
    # If the line is vertical, the tangent point is at (Cx+R, y).
    # But the problem gives specific X values.
    
    # Let's calculate the angle for the tangent point.
    # For the top prong (connecting top of outer to top of inner):
    # The line is tangent to the outer circle at some angle theta_outer_top.
    # The line is tangent to the inner circle at some angle theta_inner_top.
    # The line connects these two points.
    # The vector from center to tangent point is perpendicular to the line.
    # This is getting complex. Let's assume the given X values are the X-coordinates of the tangent points.
    
    # Top Prong Tangent Point on Outer Circle:
    # x = Cx + R_outer * cos(theta) = T_x_outer
    # cos(theta) = (T_x_outer - Cx) / R_outer
    # theta = acos(...)
    # We need the angle in the range [0, pi/2] for the top.
    cos_theta_outer_top = (T_x_outer - Cx) / R_outer
    if cos_theta_outer_top > 1: cos_theta_outer_top = 1
    if cos_theta_outer_top < -1: cos_theta_outer_top = -1
    theta_outer_top = math.acos(cos_theta_outer_top)
    
    # Bottom Prong Tangent Point on Outer Circle:
    # Symmetric, so theta_outer_bottom = -theta_outer_top
    
    # Top Prong Tangent Point on Inner Circle:
    cos_theta_inner_top = (T_x_inner - Cx) / R_inner
    if cos_theta_inner_top > 1: cos_theta_inner_top = 1
    if cos_theta_inner_top < -1: cos_theta_inner_top = -1
    theta_inner_top = math.acos(cos_theta_inner_top)
    
    # Bottom Prong Tangent Point on Inner Circle:
    theta_inner_bottom = -theta_inner_top
    
    # Now we can define the geometry:
    # 1. Outer Arc from start_outer to theta_outer_top (CCW)
    # 2. Line from theta_outer_top to theta_inner_top
    # 3. Inner Arc from theta_inner_top to end_inner (CCW? No, we need to close the loop)
    # Let's trace the perimeter:
    # Start at p_outer_start (bottom left of gap).
    # Go CCW along outer arc to theta_outer_top (top right of outer arc).
    # Go along line to theta_inner_top (top right of inner arc).
    # Go CCW along inner arc to theta_inner_bottom (bottom right of inner arc).
    # Go along line to theta_outer_bottom (bottom right of outer arc).
    # Go CCW along outer arc to p_outer_start.
    
    # Wait, the angles start_outer and end_outer were defined as -pi+alpha to pi-alpha.
    # This covers the left side.
    # The tangent points are on the right side (small angles).
    # So the path is:
    # 1. Outer Arc from start_outer (-pi+alpha) to theta_outer_bottom (-theta_outer_top).
    #    Wait, -pi+alpha is near -180. -theta_outer_top is near 0 (small negative).
    #    So we go CCW from -180 to -small.
    # 2. Line from theta_outer_bottom to theta_inner_bottom.
    # 3. Inner Arc from theta_inner_bottom to theta_inner_top.
    #    Wait, theta_inner_bottom is negative, theta_inner_top is positive.
    #    So we go CCW from negative to positive. This covers the bottom and top of the inner circle?
    #    No, we need to go the long way around?
    #    The fork is a split ring. The gap is on the right.
    #    So the inner arc should go from theta_inner_top to theta_inner_bottom (CCW)?
    #    No, that would cross the gap.
    #    The inner arc should go from theta_inner_bottom to theta_inner_top (CCW) if we are going around the left side?
    #    Let's visualize:
    #    Left side: Outer arc (large), Inner arc (small).
    #    Right side: Gap.
    #    Path: Start at bottom-left of outer arc. Go CCW to bottom-right tangent point.
    #    Then line to bottom-right tangent point of inner arc.
    #    Then go CCW along inner arc to top-right tangent point.
    #    Then line to top-right tangent point of outer arc.
    #    Then go CCW along outer arc to start.
    
    # So:
    # 1. Outer Arc: from -pi + alpha_outer to -theta_outer_top.
    # 2. Line: from -theta_outer_top to -theta_inner_top.
    # 3. Inner Arc: from -theta_inner_top to theta_inner_top.
    # 4. Line: from theta_inner_top to theta_outer_top.
    # 5. Outer Arc: from theta_outer_top to -pi + alpha_outer.
    
    # Let's verify the angles.
    # start_outer = -pi + alpha_outer.
    # end_outer_part1 = -theta_outer_top.
    # end_inner_part1 = theta_inner_top.
    # end_outer_part2 = -pi + alpha_outer.
    
    # Let's create the geometry.
    sketch_clevis.removeGeometry()
    
    # Helper to get point on circle
    def get_circle_point(r, theta):
        return App.Vector(Cx + r * math.cos(theta), r * math.sin(theta), 0)
    
    # 1. Outer Arc (Bottom Left)
    p1 = get_circle_point(R_outer, start_outer)
    p2 = get_circle_point(R_outer, -theta_outer_top)
    sketch_clevis.addGeometry(Part.Arc(p1, App.Vector(Cx, 0, 0), p2), False)
    
    # 2. Line (Bottom Right)
    p3 = get_circle_point(R_inner, -theta_inner_top)
    sketch_clevis.addGeometry(Part.LineSegment(p2, p3), False)
    
    # 3. Inner Arc (Bottom to Top)
    p4 = get_circle_point(R_inner, theta_inner_top)
    sketch_clevis.addGeometry(Part.Arc(p3, App.Vector(Cx, 0, 0), p4), False)
    
    # 4. Line (Top Right)
    p5 = get_circle_point(R_outer, theta_outer_top)
    sketch_clevis.addGeometry(Part.LineSegment(p4, p5), False)
    
    # 5. Outer Arc (Top Left)
    p6 = get_circle_point(R_outer, start_outer)
    sketch_clevis.addGeometry(Part.Arc(p5, App.Vector(Cx, 0, 0), p6), False)
    
    # Constraints: Close loop
    sketch_clevis.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    
    # --- 3. Fork Sketch ---
    # "smaller fork... opens toward negative X"
    # "rounded center one clevis_fork_prong_straight_length inward from the body end"
    # "concentric prong arcs, U-shaped opening"
    # "U-shaped opening is concentric with the rounded fork end"
    # "cut from the positive-Z face toward negative Z" -> Profile in XY, extrude along Z.
    # "clevis_fork_prong_thickness is the extrusion thickness" -> This is the Z depth.
    
    sketch_fork = body.newObject("Sketcher::SketchObject", "Sketch_Fork")
    sketch_fork.Plane = (doc.getObject("XY_Plane"), [])
    sketch_fork.ConstrainAuto = False
    
    # Fork geometry:
    # Center X: Body end is at -connector_body_length/2.
    # "rounded center one clevis_fork_prong_straight_length inward from the body end"
    # Inward from negative X end means towards positive X.
    # So Center_X = -connector_body_length/2 + clevis_fork_prong_straight_length.
    Cx_fork = -params.connector_body_length/2 + params.clevis_fork_prong_straight_length
    
    # Outer Radius
    R_outer_fork = params.clevis_fork_outer_arc_radius
    # Inner Radius
    R_inner_fork = params.clevis_fork_inner_arc_radius
    
    # Arc Central Angle: 180 degrees.
    # Opens toward negative X. So the gap is on the left.
    # Arcs go from 0 to 180? No, that's the top half.
    # If it opens to -X, the gap is around 180 deg (or -180).
    # The arcs should cover the right side (0 to 180).
    # So the arc goes from 0 to 180.
    
    # U-shaped opening: "concentric with the rounded fork end".
    # This implies the inner arc is also 180 degrees, centered at the same point.
    # So the profile is a semi-circle (outer) and a semi-circle (inner) connected by lines?
    # "U-shaped opening" usually means the gap is U-shaped.
    # But "concentric prong arcs" suggests the arcs are concentric.
    # Let's assume the profile is:
    # Outer Arc: 0 to 180.
    # Inner Arc: 0 to 180.
    # Lines connecting them at 0 and 180?
    # But at 180 (left), there is a gap.
    # So the lines connect at 0 (right) and maybe somewhere else?
    # "U-shaped opening" might mean the gap is not a straight line but curved?
    # But "concentric" implies straight lines connecting the arcs.
    # Let's assume the profile is a semi-annulus (half ring) on the right side.
    # Outer arc from 0 to 180.
    # Inner arc from 0 to 180.
    # Line at 0 (right side) connecting inner to outer.
    # Line at 180 (left side)? No, that's the gap.
    # Maybe the "U-shaped opening" refers to the shape of the fork itself?
    # Like a U-shape opening to the left.
    # So the profile is the material of the fork.
    # Material is between R_inner and R_outer, from angle 0 to 180.
    # And connected by a line at angle 0 (right side).
    # What about the left side? The gap.
    # So the profile is open on the left.
    
    # Let's construct:
    # 1. Outer Arc from 0 to 180.
    # 2. Line from 180 to 0? No, that closes the loop.
    # 3. Inner Arc from 180 to 0.
    # 4. Line from 0 to 0?
    # Let's try:
    # Start at (Cx + R_outer, 0).
    # Outer Arc CCW to (Cx - R_outer, 0).
    # Line from (Cx - R_outer, 0) to (Cx - R_inner, 0)? No, that's a line segment.
    # Inner Arc CW from (Cx - R_inner, 0) to (Cx + R_inner, 0).
    # Line from (Cx + R_inner, 0) to (Cx + R_outer, 0).
    
    # This creates a shape that is open on the left (gap) and closed on the right.
    # This matches "U-shaped opening" (opening to the left).
    
    sketch_fork.removeGeometry()
    
    # Outer Arc (0 to pi)
    p_f1 = App.Vector(Cx_fork + R_outer_fork, 0, 0)
    p_f2 = App.Vector(Cx_fork - R_outer_fork, 0, 0)
    sketch_fork.addGeometry(Part.Arc(p_f1, App.Vector(Cx_fork, 0, 0), p_f2), False)
    
    # Line (Left side, connecting outer to inner)
    p_f3 = App.Vector(Cx_fork - R_inner_fork, 0, 0)
    sketch_fork.addGeometry(Part.LineSegment(p_f2, p_f3), False)
    
    # Inner Arc (pi to 0, CW)
    p_f4 = App.Vector(Cx_fork + R_inner_fork, 0, 0)
    sketch_fork.addGeometry(Part.Arc(p_f3, App.Vector(Cx_fork, 0, 0), p_f4, False), False) # False for CW? Part.Arc direction depends on order.
    # Part.Arc(start, center, end) creates an arc. Direction is CCW by default?
    # If we want CW, we can swap start and end.
    # Let's swap:
    sketch_fork.removeGeometry()
    sketch_fork.addGeometry(Part.Arc(p_f4, App.Vector(Cx_fork, 0, 0), p_f3), False) # This is CCW from 0 to pi? No, p_f4 is at 0, p_f3 is at pi.
    # So this arc goes from 0 to pi (CCW).
    # We want the inner arc to go from pi to 0 (CW) to close the loop with the outer arc (0 to pi).
    # So we need the arc from p_f3 to p_f4.
    sketch_fork.addGeometry(Part.Arc(p_f3, App.Vector(Cx_fork, 0, 0), p_f4), False)
    
    # Line (Right side)
    sketch_fork.addGeometry(Part.LineSegment(p_f4, p_f1), False)
    
    # Constraints: Close loop
    sketch_fork.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    
    # --- 4. Side Arm Sketch ---
    # "long side arm lies against the front Y face" -> This implies it's on the Y=0 plane? Or Y=something?
    # "runs from clevis_arm_profile_start_x to the rounded end"
    # "profile uses the listed clevis_arm and clevis_end dimensions"
    # "clevis_pin_hole_diameter defines a concentric hole through its rounded end parallel to global Y"
    # "central, upper, and lower relief slots all belong to this arm"
    # "begin at clevis_arm_profile_start_x, extend toward and open through the rounded end"
    # "enter from the positive-Z face and cut toward negative Z" -> Profile in XY, extrude along Z.
    
    # Profile in XY plane.
    # Start X: clevis_arm_profile_start_x.
    # End X: clevis_arm_end_center_x.
    # End Z offset: clevis_arm_end_center_z_offset. (This is the Z-coordinate of the center of the rounded end? Or the offset from the centerline?)
    # "clevis_arm_end_center_z_offset" -> Likely the Z-coordinate of the center of the rounded end relative to the centerline (Y=0).
    # But the arm is "against the front Y face". This is confusing.
    # Maybe the arm is in the XZ plane?
    # "lies against the front Y face" -> Maybe it's on the Y=0 plane, and the "front" is the positive Y face of the body?
    # No, "front Y face" usually means the face at Y = width/2.
    # If the arm lies against it, it might be in the XZ plane at Y = width/2.
    # But then "hole... parallel to global Y" -> If the arm is in XZ, a hole parallel to Y is perpendicular to the arm plane.
    # This makes sense.
    # So: Arm profile in XZ plane. Extrude along Y.
    # "enter from the positive-Z face" -> If profile is in XZ, the faces are parallel to XZ.
    # A hole entering from "
