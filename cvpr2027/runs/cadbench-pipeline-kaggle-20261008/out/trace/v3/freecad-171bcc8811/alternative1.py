from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # --- Configuration ---
    parameters = {
        "profile_length": 175.0,
        "cross_section_outer_size": 30.0,
        "center_bore_diameter": 6.5,
        "quadrant_count": 4,
        "interior_square_corner_hole_size": 3.5,
        "corner_center_offset": 13.5,
        "outer_corner_radius": 1.5,
        "face_slot_opening_half_width": 4.0,
        "slot_lip_inner_offset": 13.0,
        "slot_shoulder_half_width": 8.0,
        "slot_inner_half_width": 6.0,
        "slot_diagonal_outer_offset": 9.41,
        "slot_diagonal_inner_offset": 4.59
    }

    # --- Document Setup ---
    doc = App.newDocument("Rail")
    
    # Create Planes
    # We will use the default XY, XZ, YZ planes provided by FreeCAD, but we need to ensure they exist.
    # In a fresh document, XY_Plane exists.
    if not doc.getObject("XY_Plane"):
        plane = doc.addObject("Part::Plane", "XY_Plane")
        plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0,1))
    if not doc.getObject("XZ_Plane"):
        plane = doc.addObject("Part::Plane", "XZ_Plane")
        plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0,1))
    if not doc.getObject("YZ_Plane"):
        plane = doc.addObject("Part::Plane", "YZ_Plane")
        plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0,1))
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0,1))
    
    # --- Parameters ---
    # Create a VarSet to hold parameters if not present, or just add properties to Body directly?
    # The prompt suggests "Params = body.newObject('App::VarSet', 'Parameters')". 
    # However, standard practice for simple parametric scripts often adds to Body or uses a VarSet.
    # Let's use the VarSet approach as hinted in the prompt's generic example to keep it strictly editable.
    
    if not body.getObjectName("Parameters"):
        params = body.newObject("App::VarSet", "Parameters")
        for key, val in parameters.items():
            params.addProperty(f"App::PropertyFloat", key, "Parameters", f"Parameter {key}")
            setattr(params, key, val)
    else:
        params = body.getObject("Parameters")

    # --- Feature 1: Base Profile Sketch (Outer Square with Rounded Corners) ---
    sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_BaseProfile")
    sketch_base.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0,1)) # On XY Plane
    sketch_base.Support = ("XY_Plane", ["", ""])
    sketch_base.ConstrainToCurrentPlane = True
    
    # Create geometry for outer square with rounded corners
    # Outer size = 30. Radius = 1.5
    size = parameters["cross_section_outer_size"]
    radius = parameters["outer_corner_radius"]
    half_size = size / 2
    
    # Points for the square corners (before rounding)
    # We need 8 points to draw the rounded square
    p1 = App.Vector(-half_size + radius, -half_size + radius) # Top-Right-ish start
    p2 = App.Vector(half_size - radius, -half_size + radius)    # Top-Right end
    p3 = App.Vector(half_size - radius, half_size - radius)     # Bottom-Right end
    p4 = App.Vector(-half_size + radius, half_size - radius)    # Bottom-Right start
    
    # Wait, standard coordinate system: X horizontal, Y vertical.
    # Let's define the box: -15 to 15. Radius 1.5.
    # Corner 1 (Top Right): x goes -13.5 to 13.5, y goes -13.5 to 13.5? No.
    # Top Right quadrant: x in [13.5, 15], y in [13.5, 15].
    
    # Let's construct lines and circles explicitly.
    # Top Edge: (-15, 15) to (15, 15)
    # Right Edge: (15, 15) to (15, -15)
    # ... etc.
    
    # We will create 4 LineSegments for straight parts and 4 Circles for corners.
    # Actually, Sketcher supports LineSegments and Arcs/Circles.
    # Let's use LineSegments for the straights and Arcs for the corners.
    
    # Top Edge Straight
    l_top = Part.LineSegment(App.Vector(-half_size + radius, half_size - radius), 
                             App.Vector(half_size - radius, half_size - radius))
    sketch_base.addGeometry(l_top, True)
    
    # Right Edge Straight
    l_right = Part.LineSegment(App.Vector(half_size - radius, half_size - radius), 
                               App.Vector(half_size - radius, -half_size + radius))
    sketch_base.addGeometry(l_right, True)
    
    # Bottom Edge Straight
    l_bottom = Part.LineSegment(App.Vector(half_size - radius, -half_size + radius), 
                                App.Vector(-half_size + radius, -half_size + radius))
    sketch_base.addGeometry(l_bottom, True)
    
    # Left Edge Straight
    l_left = Part.LineSegment(App.Vector(-half_size + radius, -half_size + radius), 
                              App.Vector(-half_size + radius, half_size - radius))
    sketch_base.addGeometry(l_left, True)
    
    # Corners (Arcs)
    # Corner 1: Top Right (Center 15, 15, Radius 1.5)
    c1 = Part.Arc(App.Vector(half_size - radius, half_size - radius), 
                  App.Vector(half_size, half_size), 
                  App.Vector(half_size, half_size - radius)) # From start to end
    sketch_base.addGeometry(c1, True)
    
    # Corner 2: Bottom Right (Center 15, -15)
    c2 = Part.Arc(App.Vector(half_size - radius, -half_size + radius), 
                  App.Vector(half_size, -half_size), 
                  App.Vector(half_size, -half_size + radius))
    sketch_base.addGeometry(c2, True)
    
    # Corner 3: Bottom Left (Center -15, -15)
    c3 = Part.Arc(App.Vector(-half_size + radius, -half_size + radius), 
                  App.Vector(-half_size, -half_size), 
                  App.Vector(-half_size, -half_size + radius))
    sketch_base.addGeometry(c3, True)
    
    # Corner 4: Top Left (Center -15, 15)
    c4 = Part.Arc(App.Vector(-half_size + radius, half_size - radius), 
                  App.Vector(-half_size, half_size), 
                  App.Vector(-half_size, half_size - radius))
    sketch_base.addGeometry(c4, True)
    
    # Constraints:
    # 1. Horizontal/Vertical lines
    # 2. Tangent between lines and arcs
    # 3. Symmetry about X and Y axes
    
    # Helper to get geometry index
    def get_geom_idx(obj, geom):
        # This is tricky in headless. We usually rely on order.
        # Since we add them in order, let's assume indices 0..7.
        # But better to use sketcher constraint references if possible.
        # For simplicity in this generated script, we will rely on the order of addition 
        # and standard naming conventions if needed, but here we use indices.
        # Note: LineSegments and Arcs are added sequentially.
        # 0: Top L, 1: Right L, 2: Bottom L, 3: Left L
        # 4: Top R Arc, 5: Bot R Arc, 6: Bot L Arc, 7: Top L Arc
        return [0, 1, 2, 3, 4, 5, 6, 7]

    # Let's try a different approach for constraints: Use "LineSegment" and "Circle" types 
    # and constrain them directly. It's more robust.
    # Reset sketch and rebuild with simpler shapes.
    
    sketch_base.removeGeometry()
    sketch_base.clearConstraints()
    
    # Re-add geometry: 4 Lines, 4 Circles (Centered at corners)
    # Line Top: (-15, 15) to (15, 15)
    l_top = Part.LineSegment(App.Vector(-half_size, half_size), App.Vector(half_size, half_size))
    sketch_base.addGeometry(l_top, False)
    # Line Right: (15, 15) to (15, -15)
    l_right = Part.LineSegment(App.Vector(half_size, half_size), App.Vector(half_size, -half_size))
    sketch_base.addGeometry(l_right, False)
    # Line Bottom: (15, -15) to (-15, -15)
    l_bottom = Part.LineSegment(App.Vector(half_size, -half_size), App.Vector(-half_size, -half_size))
    sketch_base.addGeometry(l_bottom, False)
    # Line Left: (-15, -15) to (-15, 15)
    l_left = Part.LineSegment(App.Vector(-half_size, -half_size), App.Vector(-half_size, half_size))
    sketch_base.addGeometry(l_left, False)
    
    # Circle Top Right: Center (15, 15), Radius 1.5
    c_tr = Part.Circle(App.Vector(half_size, half_size), App.Vector(0, 0, 1), radius)
    sketch_base.addGeometry(c_tr, False)
    # Circle Bot Right: Center (15, -15)
    c_br = Part.Circle(App.Vector(half_size, -half_size), App.Vector(0, 0, 1), radius)
    sketch_base.addGeometry(c_br, False)
    # Circle Bot Left: Center (-15, -15)
    c_bl = Part.Circle(App.Vector(-half_size, -half_size), App.Vector(0, 0, 1), radius)
    sketch_base.addGeometry(c_bl, False)
    # Circle Top Left: Center (-15, 15)
    c_tl = Part.Circle(App.Vector(-half_size, half_size), App.Vector(0, 0, 1), radius)
    sketch_base.addGeometry(c_tl, False)
    
    # Indices: 0:LineTop, 1:LineRight, 2:LineBot, 3:LineLeft
    # 4:ArcTR, 5:ArcBR, 6:ArcBL, 7:ArcTL
    
    # Constraints:
    # 1. Fix Point 0 (LineTop start) at (-15, 15)
    # 2. Fix Point 0 (LineRight start) at (15, 15)
    # Actually, let's constrain symmetry and distances.
    
    # Symmetry about Y-axis (X=0)
    # LineTop (0) <-> LineBottom (2) ? No, LineTop and LineBottom are parallel.
    # LineTop (0) symmetric to itself? No.
    # LineTop (0) and LineBottom (2) are symmetric wrt X-axis? No, Y-axis.
    # LineTop (y=15) and LineBottom (y=-15) are symmetric wrt X-axis.
    # LineRight (x=15) and LineLeft (x=-15) are symmetric wrt Y-axis.
    
    # Let's do full symmetry constraints.
    # Symmetry about XZ plane (Y=0) -> LineTop <-> LineBottom
    # Symmetry about YZ plane (X=0) -> LineRight <-> LineLeft
    
    # To make it robust, let's just constrain the outer box size and center.
    # And tangency.
    
    # Tangent: LineTop (0) tangent to ArcTR (4)
    sk_con = Sketcher.Constraint("Tangent", 0, 1, 4, 1) # Line 0, Arc 4
    sketch_base.addConstraint(sk_con, True)
    sk_con = Sketcher.Constraint("Tangent", 0, 1, 4, 0) # Line 0, Arc 4
    sketch_base.addConstraint(sk_con, True)
    
    # Tangent: LineRight (1) tangent to ArcTR (4)
    sk_con = Sketcher.Constraint("Tangent", 1, 1, 4, 1)
    sketch_base.addConstraint(sk_con, True)
    sk_con = Sketcher.Constraint("Tangent", 1, 1, 4, 0)
    sketch_base.addConstraint(sk_con, True)
    
    # Similar for other corners. This is tedious.
    # Alternative: Use "Coincident" constraints to fix the radius and center.
    # But the arcs are circles.
    
    # Let's simplify: Constrain the 4 lines to be perpendicular and form a box of known size.
    # Constrain LineTop (0) to be horizontal?
    # Constrain LineRight (1) to be vertical?
    # This requires specific constraint types.
    
    # Let's rely on the "Box" constraint if available, or manual points.
    # Manual points:
    # Point 0 (LineTop start) at (-15, 15)
    # Point 3 (LineRight end) at (15, -15)
    # ...
    
    # Let's just add constraints for the center and size.
    # Distance between LineTop start and LineRight start?
    
    # Okay, let's use the "Symmetry" constraint which is powerful.
    # But first, let's just constrain the lines to be orthogonal.
    # And fix the center of the whole sketch.
    
    # Let's assume the user has defined the geometry correctly and just constrain the symmetry.
    # We need to ensure the sketch is fully defined.
    
    # Constraint: LineTop (0) is symmetric to LineBottom (2) wrt X axis (Y=0)
    # This implies Y coordinates are opposite.
    # But we need to define the reference.
    
    # Let's try a different strategy: Create a sketch on XY plane.
    # Add 4 Lines forming a cross (+) and 4 Arcs? No.
    
    # Let's stick to the lines + circles and constrain them tightly.
    # 1. Coincident: LineTop start (-15, 15) with LineRight start (15, 15)? No.
    # 2. Coincident: LineTop start with a point on the axis?
    
    # Let's use the "Distance" constraint.
    # Distance between LineTop start (0) and LineRight start (1) should be 30? No, they are corners.
    # Distance between LineTop start (0) and LineRight end (1)? No.
    
    # Let's just constrain the outer points.
    # Point 0 (LineTop start) at (-15, 15)
    # Point 1 (LineRight start) at (15, 15)
    # Point 2 (LineBottom start) at (15, -15)
    # Point 3 (LineLeft start) at (-15, -15)
    
    # We can't easily constrain absolute positions without a reference point.
    # Let's create a reference point on the origin.
    pt_origin = Part.Point(App.Vector(0,0,0))
    sketch_base.addGeometry(pt_origin, True) # Add as point
    
    # Coincident: LineTop start (0) with Origin? No, it's at (-15, 15).
    # Let's move the sketch origin.
    # Let's place the center of the sketch at the origin.
    # Then constrain:
    # LineTop start (0) and LineRight start (1) distance = 30? No.
    # Distance between LineTop start (0) and LineRight start (1) is sqrt(30^2 + 30^2)? No.
    # They are corners of a 30x30 square. Distance is 30*sqrt(2).
    
    # Let's constrain:
    # Distance between LineTop start (0) and LineRight start (1) is 30*sqrt(2)
    # Distance between LineTop start (0) and LineLeft start (3) is 30
    # Distance between LineTop start (0) and LineBottom start (2) is 30
    
    # Wait, indices:
    # 0: Top (-15, 15) to (15, 15). Start (-15, 15).
    # 1: Right (15, 15) to (15, -15). Start (15, 15).
    # 2: Bot (15, -15) to (-15, -15). Start (15, -15).
    # 3: Left (-15, -15) to (-15, 15). Start (-15, -15).
    
    # Dist(0, 1) = 30
