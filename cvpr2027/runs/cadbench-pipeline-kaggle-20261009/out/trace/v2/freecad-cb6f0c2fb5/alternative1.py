import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

# --- Configuration ---
# Derived from task requirements
params = {
    "handle_length": 110.0,
    "handle_diameter": 28.0,
    "cross_flat_width": 80.0,
    "hex_height": 30.0
}

# --- Document Setup ---
doc = App.newDocument("Dumbbell")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# Add Parameters (App::PropertyLength) to the document root for easy access
# Note: In FreeCAD 1.1, we can add properties to the Body or keep them global.
# To ensure they are "named document objects" as requested and editable, 
# we will add them as properties to the Body object itself using VarSet pattern 
# or just standard properties if supported, but the prompt example used App::VarSet.
# However, standard PartDesign workflow often uses properties directly on the Body or 
# App::PropertyLength added to the Body. Let's use properties on the Body for robustness.
body.addProperty("App::PropertyLength", "handle_length")
body.handle_length = params["handle_length"]
body.addProperty("App::PropertyLength", "handle_diameter")
body.handle_diameter = params["handle_diameter"]
body.addProperty("App::PropertyLength", "cross_flat_width")
body.cross_flat_width = params["cross_flat_width"]
body.addProperty("App::PropertyLength", "hex_height")
body.hex_height = params["hex_height"]

# --- Feature Construction ---

# 1. Handle Sketch (Cylinder)
# Attached to XY plane, centered at origin
handle_sketch = body.newObject("Sketcher::SketchObject", "HandleSketch")
handle_sketch.Plane = "XY_Plane"
handle_sketch.Locked = False
handle_sketch.ConstrainX = False
handle_sketch.ConstrainY = False
handle_sketch.ConstrainZ = False

# Add Geometry
# Line for diameter
l1 = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params["handle_diameter"], 0, 0))
handle_sketch.addGeometry(l1, False)

# Circle for the handle end
c1 = Part.Circle(App.Vector(params["handle_diameter"]/2, 0, 0), App.Vector(0, 0, 1), params["handle_diameter"]/2)
handle_sketch.addGeometry(c1, False)

# Add Constraints
# Horizontal line on X axis
handle_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
# Line starts at origin (Coincident with origin point implied by Plane, or explicit point constraint)
# Since Plane is XY_Plane at 0,0,0, the start of the line is at origin.
# We need to constrain the end of the circle to be on the line.
# Actually, simpler: Line segment from 0 to D. Circle center at D/2, Radius D/2.
# This creates a perfect semicircle on the line.
handle_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Circle center (1,2) coincides with Line end (0,1)? No.
# Let's use explicit coordinates or standard constraints.
# Line: Point A (0,0) to Point B (D,0).
# Circle: Center C (D/2, 0), Radius R = D/2.
# Constraint: Circle center coincident with Midpoint of Line? Or just define line and circle independently.
# Let's constrain the circle center to the line.
handle_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 0, 0)) # Circle center (1,2) on Line (0,0)
# Tangency between Circle and Line ends
handle_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 1, 2, 0)) # Circle center on Line
# Distance from Circle Center to Line End is Radius
handle_sketch.addConstraint(Sketcher.Constraint("DistanceXY", 1, 2, 0, 1, 0, params["handle_diameter"]/2))

# 2. Handle Pad
handle_pad = body.newObject("PartDesign::Pad", "HandlePad")
handle_pad.Profile = handle_sketch
handle_pad.Length = params["handle_length"]
handle_pad.Midplane = False
handle_pad.setExpression("Length", "handle_length")
handle_pad.setExpression("Profile", "HandleSketch")

# 3. Hex End Sketch
# We need two hex sketches, one at +Z and one at -Z.
# We will create a generic sketch object first, then move it.
hex_sketch = body.newObject("Sketcher::SketchObject", "HexSketch")
hex_sketch.Plane = "YZ_Plane" # Start on YZ to draw profile facing X
# We will later move this sketch to the correct location.

# Define Hexagon Profile
# Cross flat width = 2 * apothem (distance from center to flat).
# Apothem = cross_flat_width / 2.
# Vertices for a flat-sided hexagon (flats parallel to Y axis):
# Width (across flats) is along Y. Length (point to point) is along X.
# Flat width W = 80. Apothem A = 40.
# Radius R = 40 / cos(30) = 80 / sqrt(3) approx 46.19.
# Points: (R, A), (R/2, -A), (-R/2, -A), (-R, A), (-R/2, A), (R/2, A) ?
# Let's trace carefully.
# Center at (0,0).
# Flat 1: x = A. Points (A, -R*sin(30)) to (A, R*sin(30))? No.
# Standard orientation: Flats vertical (parallel to Y).
# Points:
# 1. (A, -R*sin(30)) -> (A, -0.5*R)
# 2. (R, 0)
# 3. (A, 0.5*R)
# 4. (-A, 0.5*R)
# 5. (-R, 0)
# 6. (-A, -0.5*R)
# Where R = A / cos(30) = A / (sqrt(3)/2) = 2*A/sqrt(3).
# Let's calculate R.
import math
apothem = params["cross_flat_width"] / 2.0
R_hex = apothem / math.cos(math.radians(30))

# Add Lines/Segments for Hexagon
# We will add lines between points
p1 = App.Vector(apothem, -0.5 * R_hex, 0)
p2 = App.Vector(R_hex, 0, 0)
p3 = App.Vector(apothem, 0.5 * R_hex, 0)
p4 = App.Vector(-apothem, 0.5 * R_hex, 0)
p5 = App.Vector(-R_hex, 0, 0)
p6 = App.Vector(-apothem, -0.5 * R_hex, 0)

l1 = Part.LineSegment(p1, p2)
l2 = Part.LineSegment(p2, p3)
l3 = Part.LineSegment(p3, p4)
l4 = Part.LineSegment(p4, p5)
l5 = Part.LineSegment(p5, p6)
l6 = Part.LineSegment(p6, p1)

hex_sketch.addGeometry(l1, False)
hex_sketch.addGeometry(l2, False)
hex_sketch.addGeometry(l3, False)
hex_sketch.addGeometry(l4, False)
hex_sketch.addGeometry(l5, False)
hex_sketch.addGeometry(l6, False)

# Constraints for Hexagon
# Horizontal/Vertical lines where appropriate
# l1: Vertical? No, p1 to p2.
# Actually, let's constrain points relative to center (0,0,0) of the plane.
# Since Plane is YZ, X=0 is the center line.
# We need to define the shape relative to the sketch origin.
# Let's add constraints for horizontal/vertical segments if any, or just coordinate constraints.
# Segments 2-3 and 4-5 are vertical (parallel to Y).
# Segments 1-2 and 5-6 are slanted.
# Let's use PointOnObject to anchor vertices to lines or axes.
# Anchor p2 (R, 0) to X axis (Local Y=0).
hex_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 1, 2, 1, 1)) # Line 1 (p1-p2) point 2 on Line 1 (X axis)? No.
# Let's simplify: Constrain points to axes.
# p2 is on X axis (Local Y=0).
hex_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 1, 2, 1, 1)) # Line 1 is p1-p2. Point 2 is p2. Line 1 is not X axis.
# Let's just use coordinates.
hex_sketch.addConstraint(Sketcher.Constraint("XY", 1, 2, 0, R_hex, 0))
hex_sketch.addConstraint(Sketcher.Constraint("XY", 1, 3, 0, apothem, apothem/math.sin(math.radians(30)))) # Approx
# Better approach: 
# l1 (p1-p2): Vertical? No.
# Let's make lines horizontal/vertical where possible.
# Rotate sketch? No, stick to YZ.
# Let's just constrain the circle that circumscribes it? No, it's a hex.
# Let's use the fact that flats are vertical.
# l2 (p2-p3): Vertical segment.
# l5 (p5-p6): Vertical segment.
# l3 (p3-p4): Horizontal segment.
# l4 (p4-p5): Slanted.
# This is getting complex with lines.
# Alternative: Use a circle and trim? No, must be editable PartDesign.
# Let's just define the 6 lines and constrain endpoints to each other and axes.
# p2: X=R, Y=0
# p3: X=A, Y=A*tan(30)
# p4: X=-A, Y=A*tan(30)
# p5: X=-R, Y=0
# p6: X=-A, Y=-A*tan(30)
# p1: X=A, Y=-A*tan(30)

# Helper for tan30
tan30 = math.tan(math.radians(30))

# Constraint p2 on X axis
hex_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 1, 2, 1, 1)) # This is tricky.
# Let's use explicit coordinates for vertices.
# l1 is p1->p2. l2 is p2->p3.
hex_sketch.addConstraint(Sketcher.Constraint("XY", 1, 2, 0, R_hex, 0))
hex_sketch.addConstraint(Sketcher.Constraint("XY", 1, 3, 0, apothem, apothem*tan30))
hex_sketch.addConstraint(Sketcher.Constraint("XY", 1, 4, 0, -apothem, apothem*tan30))
hex_sketch.addConstraint(Sketcher.Constraint("XY", 1, 5, 0, -R_hex, 0))
hex_sketch.addConstraint(Sketcher.Constraint("XY", 1, 6, 0, -apothem, -apothem*tan30))
hex_sketch.addConstraint(Sketcher.Constraint("XY", 0, 1, 0, apothem, -apothem*tan30))

# Now link them up.
# p1 to p2 (l1)
# p2 to p3 (l2)
# p3 to p4 (l3)
# p4 to p5 (l4)
# p5 to p6 (l5)
# p6 to p1 (l6)
# We need to ensure continuity.
# Let's just add constraints that the lines connect.
# Sketcher handles this if we define segments and points correctly.
# The addGeometry adds segments. We need to constrain the endpoints to match coordinates.
# We did that above. Now connect them.
# Since we defined them as segments, we just need to ensure they form a loop.
# Add constraints that the end of l1 is start of l2, etc.
# But we defined them as independent segments.
# Let's assume the constraints above are enough if we treat them as a closed loop.
# Actually, we need to constrain the geometric relationship.
# Let's just add the segments and rely on the coordinate constraints to fix the shape.
# We need to close the loop.
# Let's add constraints that point 2 of l1 is point 1 of l2? No, segments are defined by points.
# We need to constrain the segments to form a closed loop.
# Sketcher has "Constrained" mode.
# Let's just add the segments. The coordinates are fixed. The loop closure is implicit if the points match.
# But we need to tell Sketcher they are connected.
# Sketcher adds constraints automatically if we use "Constrain" on the sketch? No.
# We need to use Sketcher::Constraint to link segments.
# Constraint: "Linear" or "Coincident" between segments.
# Let's skip explicit link constraints if the coordinates are exact and the sketch is in "Constrained" mode?
# The sketch is not set to "Constrained" (Locked=False).
# Let's just add the segments. The coordinate constraints should be sufficient to define the shape rigidly.
# To ensure it's a single face, we might need to use "Closed" constraint on the last segment.
# Let's add a constraint that the end of l6 coincides with start of l1? No, segments don't have start/end IDs like that.
# Let's just trust the coordinates and recompute. If it's not closed, we can use a loop constraint.
# Let's add a constraint for the loop.
# We can use "Loop" constraint if available, or just ensure the segments meet.
# Let's assume the coordinate constraints are sufficient.

# --- Hex End 1 (Positive Z) ---
# Move HexSketch to Z = hex_height/2
# But wait, the sketch is on YZ plane. The extrusion direction is X.
# We want the hex face to be at Z = +hex_height/2.
# So we need to move the sketch object to Z = +hex_height/2.
# AttachmentSupport: YZ_Plane is default.
# Placement: Move Z by hex_height/2.
hex_sketch_1 = body.newObject("Sketcher::SketchObject", "HexSketch1")
# Copy properties from HexSketch to save typing
hex_sketch_1.Plane = "YZ_Plane"
hex_sketch_1.Locked = False
# Copy geometry constraints (we can't copy the list easily, so redefine)
# Redefine geometry for HexSketch1 with same constraints but different placement?
# No, the sketch is a local 2D object. We move the whole sketch object.
# So we just need to move the sketch object.
hex_sketch_1.Plane = "YZ_Plane"
hex_sketch_1.Locked = False
# We need to re-add the geometry and constraints for HexSketch1
# (Copy logic from HexSketch)
# Redefine HexSketch1 geometry:
# Points are the same, but we will move the sketch object in placement.
# Wait, the sketch object defines the 2D geometry. The placement moves the 3D sketch object.
# So we can reuse the geometry definition.
# Let's just create HexSketch1 with the same geometry.
# But to avoid code duplication, let's just create it again with the same logic.
# Actually, we can just use HexSketch and move it? No, it's a Body child.
# We need a new object.
# Let's just copy the geometry creation block.
# (Simplified: We will just create the sketch with the same geometry, then move it)

# HexSketch1 Geometry
p1_1 = App.Vector(apothem, -0.5 * R_hex, 0)
p2_1 = App.Vector(R_hex, 0, 0)
p3_1 = App.Vector(apothem, 0.5 * R_hex, 0)
p4_1 = App.Vector(-apothem, 0.5 * R_hex, 0)
p5_1 = App.Vector(-R_hex, 0, 0)
p6_1 = App.Vector(-apothem, -0.5 * R_hex, 0)

l1_1 = Part.LineSegment(p1_1, p2_1)
l2_1 = Part.LineSegment(p2_1, p3_1)
l3_1 = Part.LineSegment(p3_1, p4_1)
l4_1 = Part.LineSegment(p4_1, p5_1)
l5_1 = Part.LineSegment(p5_1, p6_1)
l6_1 = Part.LineSegment(p6_1, p1_1)

hex_sketch_1.addGeometry(l1_1, False)
hex_sketch_1.addGeometry(l2_1, False)
hex_sketch_1.addGeometry(l3_1, False)
hex_sketch_1.addGeometry(l4_1, False)
hex_sketch_1.addGeometry(l5_1, False)
hex_sketch_1.addGeometry(l6_1, False)

# Constraints
hex_sketch_1.addConstraint(Sketcher.Constraint("
