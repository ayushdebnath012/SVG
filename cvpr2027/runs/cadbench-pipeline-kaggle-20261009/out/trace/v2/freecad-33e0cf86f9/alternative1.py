import os
from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("WoodruffKey")
    
    # Define parameters in a VarSet for easy editing
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Diameter of the full circle")
    params.diameter = 4.0
    params.addProperty("App::PropertyLength", "moon_height", "Dimensions", "Height of the semi-circular part")
    params.moon_height = 1.4
    params.addProperty("App::PropertyLength", "key_thickness", "Dimensions", "Thickness of the key")
    params.key_thickness = 1.0
    
    # Create the Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Create the base sketch on XY plane
    # Note: In FreeCAD 1.1, we attach to the Plane object if it exists, or use the default XY_Plane
    # We will create a sketch on the XY plane (Z=0)
    sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sketch.Plane = "XY_Plane"
    sketch.ConstraintsFix = True
    
    # Add geometry to the sketch
    # We need to create a shape that represents the profile
    # A Woodruff key is typically a circle with a segment removed.
    # However, the standard way to model a Woodruff key in one shot is often:
    # 1. Create a full circle.
    # 2. Pad it to create the cylinder.
    # 3. Cut out the segment that doesn't fit the shaft (usually defined by the moon_height).
    # 
    # Alternatively, we can construct the shape directly in the sketch.
    # Let's construct the shape: A circle of diameter D, and a line segment representing the chord.
    # Then we can use a shell or just subtract a segment.
    # But the most robust PartDesign approach for a "half moon" shape is:
    # 1. Create a full circle sketch.
    # 2. Pad it.
    # 3. Create a second sketch with a rectangle/segment to subtract the unused part.
    
    # Method 1: Direct Sketch Construction (Circle + Line segment constraint)
    # This creates the exact 2D profile of the Woodruff key.
    
    # Center of the key
    center = App.Vector(0, 0, 0)
    radius = params.diameter / 2.0
    
    # Add a circle
    circle = Part.Circle(center, App.Vector(0, 0, 1), radius)
    sketch.addGeometry(circle, False)
    
    # To get the specific "half moon" shape (segment removed), we need to subtract a part.
    # A Woodruff key is defined by the diameter and the depth of the cut (moon_height).
    # The chord length can be calculated, or we can define the chord by a line.
    # The distance from the center to the chord is: d_center_chord = sqrt(r^2 - (chord/2)^2)
    # Also, moon_height = r - d_center_chord (if measuring from bottom of arc to chord).
    # Actually, standard definition: moon_height is the distance from the lowest point of the arc to the chord.
    # So, d_center_chord = radius - moon_height.
    
    dist_from_center = radius - params.moon_height
    
    # We need a line tangent to a circle of radius (dist_from_center) at the bottom?
    # No, the line is the chord. The line is at distance (dist_from_center) from the center.
    # Since the key sits on the bottom, the chord is horizontal.
    # The line is at Y = -dist_from_center.
    
    # Let's add two points and a line segment to define the chord, then constrain them.
    # Point 1: ( -L/2, -dist_from_center, 0 )
    # Point 2: ( L/2, -dist_from_center, 0 )
    # Where L = 2 * sqrt(r^2 - dist_from_center^2)
    
    import math
    L = 2 * math.sqrt(radius**2 - dist_from_center**2)
    p1 = App.Vector(-L/2, -dist_from_center, 0)
    p2 = App.Vector(L/2, -dist_from_center, 0)
    
    line1 = Part.LineSegment(p1, p2)
    sketch.addGeometry(line1, False)
    
    # Constraints
    # 1. Coincident circle center with origin
    sketch.addConstraint(Sketcher.Constraint("Point", "Point1", 2, "XY_Plane")) # Point1 is on circle
    sketch.addConstraint(Sketcher.Constraint("Point", "Point2", 2, "XY_Plane")) # Point2 is on circle
    # Actually, simpler: Coincident Point1 and Point2 to circle points.
    # Let's use indices.
    # Geometry index 0 is the circle.
    # We need to constrain the line endpoints to be on the circle.
    # Sketcher constraints use indices starting from 1 in the constraint list? No, indices in geometry list.
    # Circle is index 0.
    # Line is index 1.
    # We need to constrain Point1 and Point2 to be on the circle (index 0).
    # And we need to constrain the distance between P1 and P2 to be L.
    # And we need to constrain the Y position of the line to be -dist_from_center.
    
    # Let's refine the sketch setup.
    # Geometry: [Circle, LineSegment]
    # Constraint 1: Coincident P1 (Line) to Circle
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # P1 on Circle
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # P2 on Circle
    # Constraint 2: Distance between P1 and P2
    sketch.addConstraint(Sketcher.Constraint("Distance", 1, 1, L))
    # Constraint 3: Horizontal line (Symmetry or explicit Y)
    # Let's enforce the line is horizontal by making P1 and P2 have same Y relative to each other (Distance XY)
    # Or simply constrain P1 to the X axis? No.
    # Let's constrain P1 to the X-axis (Y=0)? No, that puts it at top.
    # We want the line to be at a specific Y.
    # Let's constrain P1 to the horizontal line Y = -dist_from_center.
    # We can create a helper line or just use a constraint relative to the XY_Plane axis.
    # Sketcher constraints allow "Horizontal" or "Vertical".
    # Let's use symmetry.
    sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 1, 1, 0, 1)) # Symmetric around X axis? No.
    
    # Simpler approach for the chord:
    # Create a line segment from (-L/2, -dist, 0) to (L/2, -dist, 0).
    # Constrain P1 to circle.
    # Constrain P2 to circle.
    # Constrain the line to be parallel to X axis.
    # Constrain the distance between P1 and P2.
    # Constrain P1 to be below the center? 
    # Actually, if P1 and P2 are on the circle, and the distance is L, there are two solutions (top or bottom).
    # We need to fix the Y position.
    # Let's constrain the midpoint of the line to be at Y = -dist_from_center.
    
    # Let's restart the sketch geometry definition to be cleaner.
    sketch.clearGeometry()
    sketch.addGeometry(circle, False)
    sketch.addGeometry(line1, False)
    
    # Clear constraints
    sketch.clearConstraints()
    
    # 1. Center of circle at origin
    sketch.addConstraint(Sketcher.Constraint("Center", 0, 0, 0, 0))
    
    # 2. Endpoints on circle
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2))
    
    # 3. Length of chord
    sketch.addConstraint(Sketcher.Constraint("Distance", 1, 1, L))
    
    # 4. Orientation: The line must be horizontal.
    # We can constrain the midpoint's Y coordinate.
    # But Sketcher constraints don't have "Point to XY plane at Y".
    # We can constrain the line to be parallel to the X axis (Horizontal).
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 1))
    
    # 5. Position: The line must be below the center.
    # Distance from center to line is dist_from_center.
    # We can measure distance from Point1 (midpoint of line? No, P1 is endpoint) to the center (0,0).
    # Actually, we can constrain the distance between the midpoint of the line and the origin.
    # But Sketcher constraints work on geometry objects.
    # Let's constrain the distance between P1 (endpoint) and the center point (0,0) in Y? No.
    # Let's constrain the distance between P1 and P2 (done) and P1 to center?
    # If we constrain P1 to center, distance is radius.
    # We want the Y coordinate of the line to be -dist_from_center.
    # Let's create a point at (0, -dist_from_center, 0) and constrain P1 to it? No.
    
    # Alternative: Constrain the distance between the center of the circle and the midpoint of the line segment.
    # We need to reference the midpoint. Sketcher doesn't support midpoint directly in constraints usually.
    # Workaround: Create a point P_mid on the line segment 1 (index 1) at parameter 0.5? No, points are vertices.
    # Let's use the distance between P1 and the center (0,0) in the Y direction? No.
    
    # Let's try a different geometric definition.
    # Instead of a chord, let's define the key shape by subtracting a segment.
    # But we are building the profile first.
    # How about we constrain the distance from P1 to the point (0, -dist_from_center)?
    # We can't create that point easily without a new geometry.
    
    # Let's use the fact that the circle is centered at (0,0).
    # The line is horizontal.
    # The distance from (0,0) to the line is dist_from_center.
    # If we constrain the distance between P1 and the center (0,0) to be radius (already implied by Coincident).
    # We need to break the symmetry between the top and bottom chord.
    # We can constrain P1 to be in the lower half plane.
    # Add constraint: P1 Y < 0? No.
    # Add constraint: P1 is coincident with a point on the circle that has Y = -dist_from_center?
    # Let's calculate the angle.
    # sin(theta) = dist_from_center / radius.
    # We can constrain P1 to be at a specific angle? No direct constraint.
    
    # Simplest way: Constrain the distance between P1 and the center (0,0) to be radius (done).
    # Constrain the distance between P1 and P2 to be L (done).
    # Constrain P1 to be below the center?
    # Let's constrain the distance between P1 and the center (0,0) in the Y direction?
    # We can use a "Point" constraint to a specific location? No.
    # Let's add a point P_ref at (0, -dist_from_center, 0).
    # Then constrain P1 to P_ref? No, P1 is on the circle.
    # Constrain the distance between P1 and P_ref to be 0? No.
    
    # Let's just constrain the distance between P1 and the center (0,0) to be radius.
    # And constrain the distance between P1 and P2 to be L.
    # And constrain the line to be horizontal.
    # This still leaves two solutions (top and bottom).
    # We need to force P1 to have Y < 0.
    # We can constrain P1 to the point (0, -dist_from_center, 0) by distance?
    # Let's create a point P_anchor at (0, -dist_from_center, 0).
    # Then constrain P1 to P_anchor? No, P1 is on the circle.
    # Constrain the distance between P1 and P_anchor to be 0? No.
    # Constrain the distance between P1 and the center (0,0) to be radius.
    # Constrain the distance between P1 and P_anchor to be ...?
    # Distance(P1, P_anchor) = sqrt( (x1-0)^2 + (y1 - (-d))^2 ).
    # Since y1 = -d, dist = |x1|.
    # This doesn't fix y1.
    
    # Let's try this: Constrain the distance between the center (0,0) and the line segment to be dist_from_center.
    # In Sketcher, we can constrain the distance between a point and a line?
    # Yes, "Distance" constraint between Point and Line.
    # We need a point on the line. Let's use P1.
    # We need the distance from the center (0,0) to the line to be dist_from_center.
    # But the distance from center to the line is always |y_line|.
    # So we need to constrain the distance between the center (0,0) and the line (1) to be dist_from_center.
    # Wait, the "Distance" constraint in Sketcher between a Point and a Line is the perpendicular distance.
    # So: sketch.addConstraint(Sketcher.Constraint("Distance", 0, 1, 0, 1, dist_from_center))
    # This works! Point 0 is the center of the circle (0,0). Line 1 is our chord.
    # Distance from (0,0) to line is dist_from_center.
    # This forces the line to be at Y = dist_from_center or Y = -dist_from_center.
    # Combined with "Horizontal", it allows two positions.
    # We need to select the negative one.
    # We can constrain P1 to be below the X axis?
    # Or we can constrain the distance between P1 and the center to be ...?
    # Let's constrain P1 to be in the lower half.
    # Add constraint: P1 to Point (0,0) is radius (already done).
    # Add constraint: P1 Y coordinate < 0? No.
    # Let's constrain the distance between P1 and the point (0,0) to be radius.
    # Let's constrain the distance between P1 and the point (0, -dist_from_center) to be 0? No.
    # Let's constrain the distance between P1 and the point (0,0) to be radius.
    # Let's constrain the distance between P1 and the point (0,0) in the Y direction? No.
    
    # Let's add a point P_mid at (0, -dist_from_center, 0).
    # Then constrain P_mid to P1? No.
    # Constrain P_mid to the center? No.
    # Constrain P_mid to the line? Yes, P_mid is on the line.
    # So: Add point P_mid (geometry index 2).
    # Constrain P_mid to center (0,0) with distance dist_from_center.
    # Constrain P_mid to line 1 with "Coincident".
    # Constrain P_mid to be on the line segment? "Coincident" to line usually snaps to the line.
    # Then constrain P1 to P_mid? No, P1 is an endpoint.
    # Constrain P1 to be at distance L/2 from P_mid.
    
    # Okay, let's implement this:
    # 1. Circle (0)
    # 2. Line (1)
    # 3. Point P_mid (2)
    
    # Clear and rebuild
    sketch.clearGeometry()
    sketch.addGeometry(circle, False)
    sketch.addGeometry(line1, False)
    
    # Add a point P_mid
    p_mid = App.Vector(0, -dist_from_center, 0)
    p_mid_obj = Part.Point(p_mid)
    sketch.addGeometry(p_mid_obj, False)
    
    # Constraints
    sketch.clearConstraints()
    
    # 1. Center of circle
    sketch.addConstraint(Sketcher.Constraint("Center", 0, 0, 0, 0))
    
    # 2. Endpoints on circle
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2))
    
    # 3. Length of chord
    sketch.addConstraint(Sketcher.Constraint("Distance", 1, 1, L))
    
    # 4. Horizontal line
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 1))
    
    # 5. Midpoint P_mid on the line
    sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 0, 1, 0)) # Point 2 coincident with Line 1 at param 0?
    # Actually, "Coincident" between Point and Line snaps the point to the line.
