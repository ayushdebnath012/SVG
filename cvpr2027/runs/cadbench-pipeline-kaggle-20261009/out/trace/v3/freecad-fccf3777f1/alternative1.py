"""
FreeCAD 1.1 Script: Connecting Rod Base + Fork/Slot Edit
Generates <script_stem>_base.FCStd and <script_stem>_edit.FCStd
"""
from pathlib import Path
import FreeCAD as App
import Part
import math

def create_connecting_rod_base():
    """
    Creates the base connecting rod geometry.
    """
    doc = App.newDocument("Rod_Base")
    
    # --- Parameters ---
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "big_end_arc_radius", "Dimensions", "Radius of large end arc")
    params.big_end_arc_radius = 35.0
    params.addProperty("App::PropertyLength", "small_end_arc_radius", "Dimensions", "Radius of small end arc")
    params.small_end_arc_radius = 27.5
    params.addProperty("App::PropertyLength", "rod_body_width", "Dimensions", "Width of the main rod section")
    params.rod_body_width = 25.0
    params.addProperty("App::PropertyLength", "large_opening_center_spacing", "Dimensions", "Distance between small end center and large opening center")
    params.large_opening_center_spacing = 200.0
    params.addProperty("App::PropertyLength", "fork_transition_segment_length", "Dimensions", "Length of diagonal transition segment")
    params.fork_transition_segment_length = 22.0
    params.addProperty("App::PropertyLength", "rod_body_thickness", "Dimensions", "Thickness of the rod body (Z-direction)")
    params.rod_body_thickness = 12.0
    
    # --- Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    
    # --- Sketch 1: Small End ---
    # Plane: XY
    s_small = body.newObject("Sketcher::SketchObject", "Sketch_SmallEnd")
    s_small.Placement = App.Placement(App.Vector(0, 0, 0))
    s_small.Support = (doc.getObject("XY_Plane"), [""])
    
    # Geometry: Small arc + Thickness lines
    # Arc center at (0,0), radius R_small
    # We need lines to define thickness. Let's draw the profile relative to center.
    R_small = params.small_end_arc_radius
    R_big = params.big_end_arc_radius
    Width = params.rod_body_width
    Thickness = params.rod_body_thickness
    
    # Left side line (vertical in XY, defining thickness/2)
    s_small.addGeometry(Part.LineSegment(App.Vector(-Width/2, -R_small, 0), App.Vector(-Width/2, R_small, 0)), False)
    # Right side line
    s_small.addGeometry(Part.LineSegment(App.Vector(Width/2, -R_small, 0), App.Vector(Width/2, R_small, 0)), False)
    # Top arc connector (actually the small end is the left part in X, but let's orient X as longitudinal)
    # Let's re-orient: X is longitudinal axis.
    # Small end is at X = -LargeSpacing. Large opening is at X = 0.
    # Let's place Small End Sketch at X = -LargeSpacing.
    # Profile: Arc at X=0 (local sketch coords) radius R_small? 
    # Description: "smaller rounded end". Usually implies an eye.
    # Let's make the profile: Two vertical lines at +/- Width/2. 
    # At the bottom (Y=-R_small), they meet an arc. At top Y=R_small, they meet an arc?
    # "straight parallel sides connect the small end to diagonal transitions".
    # So the small end is defined by the arc and the straight sides.
    
    # Let's refine the sketch geometry for the Small End (at X = -200):
    # It looks like a 'D' on its side.
    # Vertical lines at x = +/- Width/2.
    # Bottom arc connecting them? Or top?
    # "large concave semicircular opening at the opposite end".
    # So Small End is convex-ish.
    
    s_small.addGeometry(Part.LineSegment(App.Vector(-Width/2, -R_small, 0), App.Vector(-Width/2, R_small, 0)), False)
    s_small.addGeometry(Part.LineSegment(App.Vector(Width/2, -R_small, 0), App.Vector(Width/2, R_small, 0)), False)
    # Arc at the bottom (y = -R_small) connecting the two lines?
    # Or is the arc the main shape?
    # Let's assume the standard connecting rod small end:
    # Two vertical lines, connected by an arc at one end (say bottom).
    s_small.addGeometry(Part.Circle(App.Vector(0, -R_small, 0), App.Vector(0, 1, 0), Width/2), False)
    
    # Constraints
    s_small.addConstraint(Sketcher.Constraint("Equal", 0, 1, 0, 1), False) # Radii? No, lines length.
    # Fix positions relative to arc
    s_small.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 2, 0, 1, 1, 1), False) # Line end
    s_small.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 1, 2, 0, 1, 0, 0), False)
    # Make it closed
    s_small.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 2, 0, 1, 0, 0), False) # Close loop
    
    # Better constraints for simple shape:
    # Center of arc on origin (0,0) relative to sketch? 
    # Let's just constrain lines to be parallel and arc tangent? 
    # FreeCAD sketch constraints are tricky without a template.
    # Let's use expressions or simple constraints:
    s_small.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, 0, 1, 0, 0), False) # X of line ends
    s_small.addConstraint(Sketcher.Constraint("DistanceX", 1, 2, 0, 1, Width/2, 0), False) # Right line X
    s_small.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, 0, 1, -Width/2, 0), False) # Left line X
    
    # Make the lines vertical
    s_small.addConstraint(Sketcher.Constraint("Vertical", 0, 2), False)
    s_small.addConstraint(Sketcher.Constraint("Vertical", 1, 2), False)
    
    # Make the arc tangent to lines at ends
    s_small.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 0, 1, 0, 0), False) # Line top
    s_small.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 0, 1, 0, 0), False) # Line bottom
    # Arc center on Y axis?
    s_small.addConstraint(Sketcher.Constraint("DistanceX", 0, 3, 0, 1, 0, 0), False) # Arc center X
    
    # --- Sketch 2: Large Opening ---
    # Plane: XZ (Rotation 90 deg around Y)
    s_large = body.newObject("Sketcher::SketchObject", "Sketch_LargeEnd")
    s_large.Placement = App.Placement(App.Vector(0, 0, 0)) # Will adjust offset
    s_large.Support = (doc.getObject("XZ_Plane"), [""])
    
    # Geometry: Large Concave Semicircular Opening.
    # This is a hole. 
    # The body width is still Width.
    # The opening is a semicircle.
    # "diagonal transitions beside the large opening".
    # So we have the main body, then the opening, then the diagonal lines to the other side?
    # Wait, the description says: "Straight parallel sides connect the small end to diagonal transitions beside the large opening."
    # This implies the shape in the XZ plane (cross section) is:
    # Small End (at X=-200): Vertical lines, Arc.
    # Main Body (X=-200 to X=0): Vertical lines at +/- Width/2.
    # Large Opening (at X=0): A semicircular cutout.
    # Transition (X=0 to X=22): Diagonal lines closing the gap between the body width and the opening?
    # No, the opening is IN the body.
    # Let's re-read: "large concave semicircular opening at the opposite end."
    # Usually, a big end is a loop.
    # Maybe the "opening" is the internal space? Or an external shape?
    # "connecting-rod body". External shape.
    # Let's interpret:
    # Left side (Small End): Rounded.
    # Right side (Big End): Large concave opening.
    # This sounds like a single piece of metal with a hole? 
    # Or the "opening" is the main shape itself? "concave semicircular opening".
    # If it's an external face, it's a cutout.
    # Let's assume the profile is:
    # X < -200: Small end arc shape.
    # -200 < X < 0: Rectangular body.
    # At X=0: A large semicircular indentation (concave).
    # From X=0 to X=22: Diagonal lines connecting the body sides to the opening sides.
    
    # Let's build the profile in XZ plane.
    # Center of Large Opening at (0, 0) in sketch coords.
    # Radius of large opening = R_big.
    # The opening is concave. So it's a hole in the profile?
    # If it's a solid body, and there is a "concave opening", it's a U-shape cut into the block.
    # But the prompt says "body... producing exactly one solid".
    # So the profile must be a closed loop.
    # Maybe the "opening" is just the shape of the big end?
    # "concave semicircular opening" -> Could be a U-channel.
    # Let's assume the profile consists of:
    # 1. Left vertical lines (Body width).
    # 2. Small end arc (Convex).
    # 3. Right vertical lines (Body width).
    # 4. Large end arc (Concave? i.e. facing left?).
    # 5. Diagonal transitions.
    
    # Let's try a different interpretation:
    # The "Large Opening" is a hole THROUGH the rod? No, "at the opposite end".
    # Let's assume the profile is defined by the Outer Boundary.
    # Top Line: Starts at Small End Top, goes Right to X=0.
    # At X=0, instead of continuing straight, it curves IN (Concave).
    # So the top line follows the arc of the large opening?
    # Then diagonal lines?
    
    # Let's construct the profile points:
    # A: Top Left (-200, Width/2)
    # B: Top Right of Small End (-200, Width/2 + something?) No, straight sides connect.
    # So Top Line: (-200, Width/2) -> (0, Width/2).
    # Then at (0, Width/2), we have the "concave semicircular opening".
    # This implies the boundary goes IN to the center of the opening?
    # If it's a "concave opening", the material is outside the arc.
    # So the boundary goes from (0, Width/2) -> Arc Center (0,0)? No, that's too sharp.
    # "Diagonal transitions beside the large opening".
    # This suggests the opening is large, and the body tapers down to the sides of the opening?
    # Let's assume the "Large Opening" is a hole in the profile, making the end look like a 'U'.
    # But it says "connecting-rod body".
    # Let's assume the "Large Opening" is the main feature of the Big End.
    # Shape: A large U-shape.
    # Top and Bottom arms of the U are the "Body".
    # The bottom of the U is the "concave opening".
    # The "diagonal transitions" connect the vertical body sides to the U-arms?
    # No, "Straight parallel sides connect the small end to diagonal transitions beside the large opening."
    # This implies: Small End -> Straight Sides -> Diagonal -> Large Opening Area.
    
    # Let's simplify the geometry to match the parameters:
    # 1. Small End Sketch (XY): Defines the small end radius and width.
    # 2. Large End Sketch (XZ): Defines the large end shape.
    #    - Center of large opening at X=0, Z=0. Radius R_big.
    #    - The profile includes the "concave" part.
    #    - Let's make the profile: 
    #      - Vertical lines at X=-200 (Small end).
    #      - Diagonal lines from (-200, Width/2) to (-22, Y_trans) and (-200, -Width/2) to (-22, -Y_trans).
    #      - Then the large opening arc?
    #      - Actually, let's make the large opening a THROUGH hole? No, "opening at the opposite end".
    #      Let's assume the profile is a solid shape that has a large cutout.
    #      Profile: 
    #      - Left: Vertical lines at x=-200.
    #      - Right: Large concave arc (facing left) centered at (0,0) with radius R_big.
    #      - The "diagonal transitions" connect the vertical lines (at x=-200) to the "shoulders" of the large opening?
    #      - But the large opening is at X=0.
    #      - Maybe the "Large Opening" is the hole, and the body is the material around it.
    #      - But "Straight parallel sides connect... to diagonal transitions".
    #      - Okay, let's build a profile that looks like a connecting rod big end with a deep cup.
    
    # Revised Profile Logic:
    # X-axis: Longitudinal. Z-axis: Thickness.
    # Small End at X = -200.
    # Large Opening Center at X = 0.
    # The profile is symmetric about Z=0.
    # Top Line:
    # 1. From X=-200, Z=Width/2 (Small End Top).
    # 2. Horizontal to X = -22 (Transition start).
    # 3. Diagonal to X = -22 + 22 = 0? No, "fork_transition_segment_length".
    #    Let's say the diagonal starts at X = -200 + 200 - 22 = -22.
    #    So from (-200, Width/2) to (-22, Y_diag).
    #    Slope? We need to connect to the Large Opening.
    #    The Large Opening is a concave semicircle.
    #    Let's assume the Large Opening is a hole in the profile, so the profile goes around it.
    #    But "concave semicircular opening" usually means the shape itself is concave (like a bowl).
    #    If it's a bowl shape:
    #    The boundary goes from the transition point, curves inward (concave) to the bottom of the bowl, then curves back?
    #    No, "concave opening" implies a cut.
    #    Let's assume the profile is:
    #    - Outer boundary: Small End Arc -> Straight -> Diagonal -> Large Concave Arc -> Diagonal -> Straight -> Small End Arc.
    #    - The "Large Concave Arc" is the bottom of the big end.
    #    - The "Opening" is the space inside this arc?
    #    - If the profile is closed, the "opening" is just a feature of the shape.
    #    - Let's define the Large End Sketch to create this shape.
    
    # Sketch Geometry (XZ):
    # 1. Left Vertical Line: X = -200, Z from -Width/2 to Width/2.
    # 2. Diagonal Lines: Connect (-200, Width/2) to (0, R_big)?
    #    If the large opening is a semicircle of radius R_big centered at (0,0), the top of the arc is (0, R_big).
    #    If the diagonal connects to the shoulder of the arc...
    #    Let's assume the diagonal connects to the point (0, R_big - margin)?
    #    Or maybe the diagonal connects the straight side to the arc.
    #    Let's assume the diagonal starts at X = -200 + (200 - 22) = -22.
    #    Connect (-22, Width/2) to (0, R_big).
    #    Then the Arc from (0, R_big) to (0, -R_big)?
    #    This creates a shape that tapers in.
    
    # Let's refine the "Diagonal" logic.
    # "diagonal transitions beside the large opening".
    # This implies the transition is NEXT to the opening.
    # So: Straight Side -> Diagonal -> Opening.
    # Opening is at X=0.
    # Straight Side is at X=-200.
    # Diagonal is between X=-200 and X=0.
    # Let's place the diagonal from X = -200 + (200 - 22) = -22 to X = 0.
