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

# Base Parameters
params = {
    "mount_body_length": 22.86,
    "mount_width": 10.16,
    "mount_sheet_thickness": 0.92,
    "retention_bend_inner_radius": 0.91,
    "return_end_straight_length": 0.66,
    "open_end_to_first_transition_bend_center_distance": 10.16,
    "transition_bend_center_longitudinal_spacing": 2.75,
    "transition_bend_contact_angle": -17.1552626, # degrees
    "open_end_tip_clearance": 0.12,
    # Edit Parameters (will be set later for the edit file)
    "mounting_screw_hole_diameter": 4.32,
    "mounting_hole_center_distance_from_open_end": 5.08
}

def create_document_and_base():
    doc = App.newDocument("CableTieMount")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    doc.setActiveObject(body)
    
    # Create Parameters Object
    params_obj = body.newObject("App::VarSet", "Parameters")
    for name, value in params.items():
        params_obj.addProperty("App::PropertyLength", name, "Dimensions", f"{name.replace('_', ' ').title()}")
        params_obj[name] = value

    # --- Step 1: Create the Folded Strip Profile Sketch ---
    # We need to construct the S-shape profile.
    # Coordinate system: X is longitudinal (length), Y is vertical (width/thickness).
    # Origin at the center of the open end tip.
    
    sketch = body.newObject("Sketcher::SketchObject", "ProfileSketch")
    sketch.Plane = "XY_Plane"
    sketch.MapMode = "FlatFace"
    sketch.ConstrainAuto = True
    
    # Helper to add geometry
    def add_line(p1, p2, constraint_type="Fixed"):
        sketch.addGeometry(Part.LineSegment(p1, p2), False)
        sketch.addConstraint(Sketcher.Constraint(constraint_type, "X1", p1.X, "Y1", p1.Y))
        sketch.addConstraint(Sketcher.Constraint(constraint_type, "X2", p2.X, "Y2", p2.Y))
        return p2

    def add_circle(center, radius, constraint_type="Fixed"):
        sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False)
        sketch.addConstraint(Sketcher.Constraint(constraint_type, "CenterX", center.X, "CenterY", center.Y))
        sketch.addConstraint(Sketcher.Constraint(constraint_type, "Radius", radius))
        return center

    # 1. Open End Tip (Bottom Left)
    # Center of the tip
    p_tip = App.Vector(0, 0)
    sketch.addGeometry(Part.Circle(p_tip, App.Vector(0, 0, 1), params["mount_width"]/2), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "CenterX", 0, "CenterY", 0))
    sketch.addConstraint(Sketcher.Constraint("Radius", params["mount_width"]/2))
    
    # 2. First Leg (Upwards)
    # Length = open_end_to_first_transition_bend_center_distance
    p_bend1_center = App.Vector(0, params["open_end_to_first_transition_bend_center_distance"])
    sketch.addGeometry(Part.LineSegment(p_tip, p_bend1_center), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "X2", 0, "Y2", params["open_end_to_first_transition_bend_center_distance"]))
    
    # 3. First Bend (Retention Bend)
    # Inner radius, so the center of the arc is at Y = p_bend1_center.Y - radius
    r = params["retention_bend_inner_radius"]
    p_bend1_arc_center = App.Vector(0, p_bend1_center.Y - r)
    sketch.addGeometry(Part.Circle(p_bend1_arc_center, App.Vector(0, 0, 1), r), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "CenterX", 0, "CenterY", p_bend1_center.Y - r))
    sketch.addConstraint(Sketcher.Constraint("Radius", r))
    
    # 4. Second Leg (Downwards towards return)
    # Length = transition_bend_center_longitudinal_spacing
    p_bend2_center = App.Vector(0, p_bend1_center.Y - params["transition_bend_center_longitudinal_spacing"])
    sketch.addGeometry(Part.LineSegment(p_bend1_center, p_bend2_center), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "X2", 0, "Y2", p_bend1_center.Y - params["transition_bend_center_longitudinal_spacing"]))
    
    # 5. Second Bend (Retention Bend)
    # Same radius
    p_bend2_arc_center = App.Vector(0, p_bend2_center.Y - r)
    sketch.addGeometry(Part.Circle(p_bend2_arc_center, App.Vector(0, 0, 1), r), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "CenterX", 0, "CenterY", p_bend2_center.Y - r))
    sketch.addConstraint(Sketcher.Constraint("Radius", r))
    
    # 6. Third Leg (Upwards towards return)
    # We need to calculate the length to reach the return start.
    # The return starts at a specific Y relative to the second bend center?
    # Description: "S-shaped transition... closed symmetric return".
    # Usually, the return leg goes up to the level of the first bend center or similar.
    # Let's assume the return leg goes up to the same height as the first bend center (symmetry in height).
    # Height of first bend center = params["open_end_to_first_transition_bend_center_distance"]
    # Height of second bend center = Height1 - spacing
    # Height of return start = Height1 (to make the S shape symmetric vertically?)
    # Or simply, the return leg goes up to the level of the first bend center.
    target_y_return = p_bend1_center.Y
    p_return_start = App.Vector(0, target_y_return)
    
    # Calculate length of third leg
    leg3_len = target_y_return - p_bend2_center.Y
    sketch.addGeometry(Part.LineSegment(p_bend2_center, p_return_start), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "X2", 0, "Y2", target_y_return))
    
    # 7. Return Leg (Horizontal)
    # Length = return_end_straight_length
    p_return_end = App.Vector(params["return_end_straight_length"], target_y_return)
    sketch.addGeometry(Part.LineSegment(p_return_start, p_return_end), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "X2", params["return_end_straight_length"], "Y2", target_y_return))
    
    # 8. Return Tip (Closed)
    # Center at p_return_end
    sketch.addGeometry(Part.Circle(p_return_end, App.Vector(0, 0, 1), params["mount_width"]/2), False)
    sketch.addConstraint(Sketcher.Constraint("Fixed", "CenterX", params["return_end_straight_length"], "CenterY", target_y_return))
    sketch.addConstraint(Sketcher.Constraint("Radius", params["mount_width"]/2))
    
    # Add Coincident constraints for smooth transitions (Tangent)
    # Tip to Leg1
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center to Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 1, 2)) # Center to End
    
    # Leg1 to Bend1
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # End of line to Start of circle
    
    # Bend1 to Leg2
    sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1))
    
    # Leg2 to Bend2
    sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 4, 1))
    
    # Bend2 to Leg3
    sketch.addConstraint(Sketcher.Constraint("Coincident", 4, 2, 5, 1))
    
    # Leg3 to Return
    sketch.addConstraint(Sketcher.Constraint("Coincident", 5, 2, 6, 1))
    
    # Return to Tip
    sketch.addConstraint(Sketcher.Constraint("Coincident", 6, 2, 7, 1))
    
    # Add Tangent constraints for smooth bends
    # Leg1 tangent to Bend1
    sketch.addConstraint(Sketcher.Constraint("Tangent", 1, 2, 2, 1))
    # Leg2 tangent to Bend1
    sketch.addConstraint(Sketcher.Constraint("Tangent", 1, 2, 2, 2))
    # Leg2 tangent to Bend2
    sketch.addConstraint(Sketcher.Constraint("Tangent", 3, 2, 4, 1))
    # Leg3 tangent to Bend2
    sketch.addConstraint(Sketcher.Constraint("Tangent", 4, 2, 5, 1))
    # Return tangent to Leg3
    sketch.addConstraint(Sketcher.Constraint("Tangent", 5, 2, 6, 1))
    # Tip tangent to Return
    sketch.addConstraint(Sketcher.Constraint("Tangent", 6, 2, 7, 1))
    # Tip tangent to Leg1
    sketch.addConstraint(Sketcher.Constraint("Tangent", 0, 2, 1, 1))

    # --- Step 2: Create the Pad (Extrude) ---
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch
    pad.Length = params["mount_body_length"]
    pad.Midplane = False
    pad.Reversed = False
    
    # --- Step 3: Create the Hole Sketch ---
    # The hole is in the "broad mounting leg".
    # Based on the profile, the broad leg is the horizontal return leg at the top right.
    # Y coordinate of the return leg centerline is target_y_return.
    # X coordinate of the hole center is params["mounting_hole_center_distance_from_open_end"].
    
    hole_sketch = body.newObject("Sketcher::SketchObject", "HoleSketch")
    hole_sketch.Plane = "XY_Plane"
    hole_sketch.MapMode = "FlatFace"
    
    # We need to reference the existing geometry to position the hole correctly.
    # The return leg is the last line segment added (index 6 in sketch list? No, sketch list is dynamic).
    # Let's use the known coordinates derived from parameters.
    # Return Leg Centerline Y = params["open_end_to_first_transition_bend_center_distance"]
    # Return Leg Centerline X range: [0, params["return_end_straight_length"]]
    # Hole Center X = params["mounting_hole_center_distance_from_open_end"]
    
    hole_center_x = params["mounting_hole_center_distance_from_open_end"]
    hole_center_y = params["open_end_to_first_transition_bend_center_distance"]
    
    hole_sketch.addGeometry(Part.Circle(App.Vector(hole_center_x, hole_center_y, 0), App.Vector(0, 0, 1), params["mounting_screw_hole_diameter"]/2), False)
    hole_sketch.addConstraint(Sketcher.Constraint("Fixed", "CenterX", hole_center_x, "CenterY", hole_center_y))
    hole_sketch.addConstraint(Sketcher.Constraint("Fixed", "Radius", params["mounting_screw_hole_diameter"]/2))
    
    # --- Step 4: Create the Pocket (Hole) ---
    pocket = body.newObject("PartDesign::Pocket", "MountingHole")
    pocket.Profile = hole_sketch
    pocket.Type = "ThroughAll"
    pocket.Clean = True
    
    # --- Step 5: Add Fillets ---
    # We need to fillet the inner corners of the S-bends.
    # The sketch has circles for the bends. The Pad will create sharp corners between the straight lines and the arcs if not careful, 
    # but since we used circles in the sketch, the Pad should follow them.
    # However, the "bend" is the circle itself. The transition from straight line to circle is tangent.
    # The request says "All bends use retention_bend_inner_radius".
    # The sketch construction already uses circles with this radius.
    # We might need to fillet the outer corners of the return leg or the tip if they are sharp.
    # The tip and return end are circles in the sketch, so they are rounded.
    # The transitions between straight lines and circles are tangent.
    # So the geometry is already smooth.
    # Let's add a small fillet just to be safe on any sharp internal corners if the sketch logic missed a tangent constraint, 
    # but with the current logic, it should be fine.
    # Actually, let's add a fillet to the outer corner of the return leg if it's not a circle.
    # In our sketch, the return end is a circle.
    # The open tip is a circle.
    # The bends are circles.
    # So the profile is fully rounded. No extra fillets needed on the profile itself.
    
    # Wait, the "bend" in a cable tie is usually a sharp corner on the outside and a radius on the inside.
    # Our sketch uses a full circle for the bend. This creates a "D" shape or a full loop.
    # A cable tie bend is usually a quarter circle or similar.
    # Let's re-evaluate the sketch geometry.
    # "S-shaped transition".
    # Leg 1 (Up) -> Bend 1 (Right turn?) -> Leg 2 (Down) -> Bend 2 (Left turn?) -> Leg 3 (Up) -> Return (Right).
    # My previous sketch logic:
    # Leg 1: Up.
    # Bend 1: Circle centered at (0, Y1-r). This is a circle. If we traverse it, it goes around.
    # We need to constrain the arc specifically.
    # Sketcher::SketchObject allows adding arcs or we can use LineSegments and Circles and constrain them.
    # Using Circles and constraining Tangency and Coincidence works.
    # But a full circle in the sketch might create a closed loop if not careful.
    # The sketch is a closed loop: Tip -> Leg1 -> Bend1 -> Leg2 -> Bend2 -> Leg3 -> Return -> Tip.
    # If Bend1 is a full circle, the path goes around it.
    # We need to ensure the path follows the arc.
    # Sketcher handles this if we constrain the lines to be tangent to the circle at specific points.
    # But we don't know the exact angles of the tangent points without calculating them.
    # Alternative: Use LineSegments and approximate the bend, or use the "Arc" geometry type if available in FreeCAD 1.1 Sketcher.
    # FreeCAD 1.1 Sketcher supports `Part::Arc`? No, usually `Part::Circle` or `Part::LineSegment`.
    # There is `Sketcher::Arc`? No.
    # We can use `Part::Circle` and constrain the lines to be tangent.
    # To make it robust, let's assume the bends are 90 degrees or similar?
    # "S-shaped". Usually 90 degree turns.
    # Let's assume the bends are 90 degrees.
    # Leg 1 is vertical (X=0). Bend 1 turns it to horizontal (Y=const).
    # So the arc goes from (0, Y1) to (r, Y1-r)? No.
    # If Leg 1 is Up (0,0) to (0, Y1).
    # Bend 1 connects to Leg 2 (Down).
    # So Leg 1 is Up, Leg 2 is Down. The bend is a U-turn? No, S-shape.
    # S-shape: Up, Right, Down, Left, Up, Right.
    # Leg 1: Up.
    # Bend 1: Turns Right. (90 deg).
    # Leg 2: Right.
    # Bend 2: Turns Left. (90 deg).
    # Leg 3: Up.
    # Return: Right.
    
    # Let's rebuild the sketch logic to be more precise about the S-shape.
    # 1. Tip at (0,0).
    # 2. Leg 1: Up to (0, L1). L1 = open_end_to_first_transition_bend_center_distance.
    # 3. Bend 1: 90 deg turn to the Right. Center at (r, L1-r). Radius r.
    #    Start point (0, L1). End point (r, L1).
    #    Wait, if it turns right, it goes from Up to Right.
    #    Center should be at (r, L1). No, center at (r, L1) would make it go from (0, L1) to (r, L1) if it's a quarter circle?
    #    If center is (r, L1), arc from (0, L1) to (r, L1) is not a
