from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def create_part_base():
    """Creates the base housing blank as a parametric PartDesign Body."""
    doc = App.newDocument("PartDesign_Base")
    doc.Label = "Housing_Base"
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Label = "Body"
    
    # Parameters
    params = body.newObject("App::Property", "Parameters")
    params.addProperty("App::PropertyLength", "frame_thickness", "Parameters", "Plate thickness")
    params.frame_thickness = 15.0
    
    params.addProperty("App::PropertyLength", "housing_left_end_radius", "Parameters", "Left rounded corner radius")
    params.housing_left_end_radius = 22.0
    
    params.addProperty("App::PropertyLength", "housing_right_corner_radius", "Parameters", "Right rounded corner radius")
    params.housing_right_corner_radius = 13.0
    
    params.addProperty("App::PropertyLength", "housing_overall_length", "Parameters", "Total length")
    params.housing_overall_length = 81.0
    
    params.addProperty("App::PropertyLength", "housing_overall_width", "Parameters", "Total width")
    params.housing_overall_width = 68.0
    
    # Sketch for the base outline
    sketch = body.newObject("Sketcher::SketchObject", "BaseOutline")
    sketch.Plane = "XY_Plane"
    sketch.Constraints = ["Sketcher::Additive", "Sketcher::SamePoint", "Sketcher::Coincident", "Sketcher::Parallel", "Sketcher::Perpendicular"]
    sketch.GC2ndArc = False
    sketch.GC3rdArc = False
    sketch.Locked = False
    sketch.MapMode = "FlatFace"
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.Type = "Disk"
    sketch.ViewObject.DisplayMode = "Full"
    sketch.ViewObject.KeepFaceColor = False
    
    # We will construct the shape using LineSegments and Arcs
    # Coordinates: Origin at center of housing (0,0). 
    # Length along X, Width along Y.
    # Left end: X = -Length/2. Right end: X = Length/2.
    # Top edge: Y = Width/2. Bottom edge: Y = -Width/2.
    
    half_len = params.housing_overall_length / 2.0
    half_wid = params.housing_overall_width / 2.0
    
    # Points for the sketch
    # Start bottom-left, go right to left_end_radius boundary
    p1 = App.Vector(-half_len + params.housing_left_end_radius, -half_wid, 0)
    # Go up to bottom-left corner
    p2 = App.Vector(-half_len + params.housing_left_end_radius, -half_wid + params.housing_left_end_radius, 0)
    # Go right to bottom-right corner
    p3 = App.Vector(-half_len + params.housing_left_end_radius + params.housing_left_end_radius, -half_wid + params.housing_left_end_radius, 0)
    # Wait, let's trace the perimeter carefully.
    
    # Perimeter Trace:
    # 1. Bottom Straight: From Left_Corner_Start to Right_Corner_Start
    #    Left_Corner_Start X: -Length/2 + LeftRadius
    #    Right_Corner_Start X: Length/2 - RightRadius
    #    Y: -Width/2
    
    # 2. Right Rounded Corner: From Right_Corner_Start to Right_Corner_End
    #    Center of arc: (Length/2, 0) ? No.
    #    The description says: "tangent to the horizontal top/bottom edges and the straight right end".
    #    So the arc center is at (Length/2, 0) only if it's tangent to the vertical line at Length/2.
    #    Yes, tangent to "straight right end" means the arc center is on the line X=Length/2.
    #    Tangent to horizontal edges means center is on Y=0.
    #    So Center = (Length/2, 0). Radius = RightRadius.
    #    Start of arc: (Length/2 - RightRadius, -Width/2). End: (Length/2 - RightRadius, Width/2).
    
    # 3. Top Straight: From Right_Corner_End to Left_Corner_End
    #    Y: Width/2.
    #    X goes from (Length/2 - RightRadius) to (-Length/2 + LeftRadius).
    
    # 4. Left Rounded Corner:
    #    Tangent to horizontal top/bottom and straight left end.
    #    Center: (-Length/2, 0). Radius: LeftRadius.
    #    Start: (-Length/2 + LeftRadius, -Width/2). End: (-Length/2 + LeftRadius, Width/2).
    
    # Let's build the sketch geometry points in order.
    
    # Point A: Bottom-Left corner start (Tangent to bottom line)
    # This point is on the circle centered at (-Length/2, 0).
    # The circle goes from Y=-Width/2 to Y=Width/2.
    # The straight line is at Y=-Width/2. The intersection is (-Length/2 + LeftRadius, -Width/2).
    pt_a = App.Vector(-half_len + params.housing_left_end_radius, -half_wid, 0)
    
    # Point B: Bottom-Right corner start
    pt_b = App.Vector(half_len - params.housing_right_corner_radius, -half_wid, 0)
    
    # Point C: Top-Right corner start
    pt_c = App.Vector(half_len - params.housing_right_corner_radius, half_wid, 0)
    
    # Point D: Top-Left corner start
    pt_d = App.Vector(-half_len + params.housing_left_end_radius, half_wid, 0)
    
    # Add Lines
    sketch.addGeometry(Part.LineSegment(pt_a, pt_b), False)
    sketch.addGeometry(Part.LineSegment(pt_c, pt_d), False) # Top line
    
    # Add Arcs for corners
    # Right Corner Arc
    arc_right = Part.Circle(App.Vector(half_len, 0, 0), App.Vector(0, 0, 1), params.housing_right_corner_radius)
    # We need to constrain the sketch elements to this arc or define the arc directly.
    # In PartDesign sketch, we can add an Arc object.
    # However, the standard way in script is often to add LineSegments and use constraints, 
    # OR add the Arc geometry directly if supported.
    # Let's add the arc geometry directly as it's cleaner for this specific shape.
    # Note: Sketcher::SketchObject addGeometry with a Circle creates an arc if constrained, 
    # but we can just add the circle geometry and constrain it to be tangent/centered.
    # Actually, simpler: Add the circle geometry, then constrain the endpoints to the line.
    sketch.addGeometry(Part.Circle(App.Vector(half_len, 0, 0), App.Vector(0, 0, 1), params.housing_right_corner_radius), False)
    # Force the circle to be the arc between pt_b and pt_c.
    # We add constraints later.
    
    # Left Corner Arc
    arc_left = Part.Circle(App.Vector(-half_len, 0, 0), App.Vector(0, 0, 1), params.housing_left_end_radius)
    sketch.addGeometry(Part.Circle(App.Vector(-half_len, 0, 0), App.Vector(0, 0, 1), params.housing_left_end_radius), False)
    
    # Constraints
    # 1. Tangent/Coincident lines to arcs
    # Bottom Line to Right Arc
    sketch.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, 1, 0), pt_b) # Line 0, Point 1 (start) on Arc 1?
    # Let's use explicit coordinate constraints for robustness.
    
    # Define the sketch elements explicitly
    # Element 0: Bottom Line
    # Element 1: Right Arc (Circle)
    # Element 2: Top Line
    # Element 3: Left Arc (Circle)
    
    # Constraints for Right Arc:
    # Center at (Length/2, 0)
    # Start point (pt_b) on line y = -Width/2
    # End point (pt_c) on line y = Width/2
    # Tangent to vertical line X = Length/2 (implied by geometry, but let's constrain radius)
    
    # Let's simplify: Use LineSegments for the straight parts and Arcs for corners.
    # We need to link them.
    
    # Constraint: Start of Right Arc coincides with End of Bottom Line?
    # Actually, pt_b is the start of the bottom line. The arc starts at pt_b.
    # So Bottom Line End = Right Arc Start.
    # But we didn't define "Start" explicitly in the geometry list if we just add a Circle.
    # We need to constrain the Circle geometry to match the lines.
    
    # Better approach: Add LineSegments for the straight parts, and Arcs for corners.
    # Then constrain them to be tangent.
    
    # Re-evaluating geometry addition:
    # 1. Line Segment: pt_a to pt_b
    # 2. Arc: Center (half_len, 0), Radius right_radius. Start pt_b, End pt_c.
    # 3. Line Segment: pt_c to pt_d
    # 4. Arc: Center (-half_len, 0), Radius left_radius. Start pt_d, End pt_a.
    
    # How to add an Arc with specific start/end in sketch?
    # We can add a Circle and constrain it.
    
    # Let's add the Circle for Right Corner
    circle_r = sketch.addGeometry(Part.Circle(App.Vector(half_len, 0, 0), App.Vector(0, 0, 1), params.housing_right_corner_radius), False)
    # Let's add the Circle for Left Corner
    circle_l = sketch.addGeometry(Part.Circle(App.Vector(-half_len, 0, 0), App.Vector(0, 0, 1), params.housing_left_end_radius), False)
    
    # Add Lines
    line_bot = sketch.addGeometry(Part.LineSegment(pt_a, pt_b), False)
    line_top = sketch.addGeometry(Part.LineSegment(pt_c, pt_d), False)
    
    # Constraints
    # 1. pt_b is on the bottom line (it is).
    # 2. pt_b is on the right circle.
    # 3. pt_c is on the top line.
    # 4. pt_c is on the right circle.
    # 5. pt_d is on the top line.
    # 6. pt_d is on the left circle.
    # 7. pt_a is on the bottom line.
    # 8. pt_a is on the left circle.
    
    # Let's define the sketch elements indices.
    # 0: line_bot
    # 1: circle_r
    # 2: line_top
    # 3: circle_l
    
    # Constraints for Right Arc:
    # Start of circle (angle 0 relative to center vector?) No, we don't know start angle.
    # We know the circle must pass through pt_b and pt_c.
    # And the circle center is fixed at (half_len, 0).
    # So we just need to constrain the circle to pass through pt_b and pt_c.
    # Sketcher allows "PointOnObject" or "Distance".
    # Let's use "PointOnObject" for the lines and circles.
    
    # Actually, the easiest way in script for a closed loop with arcs is to constrain the arcs to be tangent to the lines at the intersection points.
    # Intersection of Bottom Line (y = -W/2) and Right Circle (x = L/2).
    # Intersection point is pt_b.
    # So: Bottom Line and Right Circle are tangent at pt_b.
    # Top Line and Right Circle are tangent at pt_c.
    # Top Line and Left Circle are tangent at pt_d.
    # Bottom Line and Left Circle are tangent at pt_a.
    
    # Constraint Syntax: Sketcher.Constraint("Tangent", index1, point1, index2, point2)
    # point1/point2 are local indices in the element (0=point, 1=point...)
    # For a LineSegment (0,1), points are 0,1.
    # For a Circle (0,1,2...), points are angles? No, usually 0,1 refer to start/end of the arc segment defined.
    # In FreeCAD scripting, for a Circle object added to sketch, we don't have start/end points easily accessible as indices 0,1 unless we constrain them.
    # Alternative: Use "Coincident" with the lines at the specific coordinates.
    
    # Let's try a different strategy: 
    # 1. Add 4 LineSegments forming the "box" minus the corners.
    # 2. Add 4 Arcs connecting them.
    # But we don't have a direct "Arc" geometry type in addGeometry that takes 3 points easily without constraints.
    
    # Robust Strategy: 
    # 1. Create the sketch.
    # 2. Add the 4 lines.
    # 3. Add the 2 circles (Right and Left).
    # 4. Constrain the circles to be tangent to the lines at the calculated intersection points.
    
    # Intersection pt_b: (-W/2, -W/2) relative to center? No.
    # pt_b = (half_len - right_rad, -half_wid)
    # pt_c = (half_len - right_rad, half_wid)
    # pt_d = (-half_len + left_rad, half_wid)
    # pt_a = (-half_len + left_rad, -half_wid)
    
    # Tangent Constraint: 
    # Element 0 (Line Bot) and Element 1 (Circle R) are tangent.
    # We need to specify the point on the line and point on the circle.
    # Point on Line 0: 1 (End).
    # Point on Circle 1: ? (0 or 1?)
    # If we constrain the circle to pass through pt_b and pt_c, and center is fixed, it becomes an arc.
    
    # Let's use "PointOnObject" to force the circle to pass through the corners.
    # Circle 1 passes through pt_b (on Line 0).
    # Circle 1 passes through pt_c (on Line 2).
    # Circle 3 passes through pt_d (on Line 2).
    # Circle 3 passes through pt_a (on Line 0).
    
    # Also, the lines must be tangent to the circles.
    # Since the lines are horizontal and circles are centered on X-axis, they are naturally tangent at the vertical extremes.
    # We just need to ensure the circle doesn't rotate. Fixing the center fixes the orientation.
    
    # Center of Circle 1: (half_len, 0).
    # We can't directly constrain the center of a Circle in Sketcher easily to a point unless we use a point object.
    # But we can constrain the circle to be concentric with a point? No.
    # We can constrain the circle to pass through pt_b and pt_c, and the distance between pt_b and pt_c is 2*Radius.
    # If we fix the center X and Radius, the circle is defined.
    # How to fix center X? 
    # We can constrain the circle to be tangent to a vertical line at X=half_len? No, the arc is on the left of that.
    # The tangent to the circle at pt_b is horizontal. The line is horizontal.
    
    # Let's try: 
    # 1. Add Line Segments.
    # 2. Add Circles.
    # 3. Constrain Circle 1 to pass through pt_b and pt_c.
    # 4. Constrain Circle 3 to pass through pt_d and pt_a.
    # 5. Constrain Circle 1 to be tangent to Line 0 at pt_b.
    # 6. Constrain Circle 1 to be tangent to Line 2 at pt_c.
    # 7. Constrain Circle 3 to be tangent to Line 2 at pt_d.
    # 8. Constrain Circle 3 to be tangent to Line 0 at pt_a.
    
    # Tangent constraint syntax: "Tangent", index1, point1, index2, point2
    # For a LineSegment, points are 0, 1.
    # For a Circle, points are 0, 1? Usually 0,1 refer to the start and end of the arc.
    # If we don't know the start/end, we can use "PointOnObject".
    
    # Let's use PointOnObject to force the circle to pass through the intersection points.
    # Then add Tangent constraints to ensure smooth joining.
    
    sketch.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, 1, 0), pt_b) # Line 0, Point 1 on Circle 1? 
    # Wait, "PointOnObject" syntax: Type, Index1, PointOn1, Index2, PointOn2.
    # If we want Point on Circle, we need to select the circle.
    # Actually, let's use the fact that the lines are tangent to the circles at the known points.
    # We can constrain the Line End to the Circle Point, and the Tangency.
    
    # Simpler: Just add the arcs as LineSegments? No, we need arcs.
    # Let's use the "Arc" geometry if possible, or rely on constraints.
    # Given the complexity of constraint scripting, let's try
