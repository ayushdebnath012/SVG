import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derive output path from __file__
script_dir = Path(__file__).parent
output_path = script_dir / "answer.FCStd"

# --- Document Setup ---
doc = App.newDocument("Shaft")
App.ActiveDocument = doc

# Create a Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Create a VarSet to hold named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")

params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft diameter")
params.shaft_diameter = 50.0

params.addProperty("App::PropertyLength", "shaft_length", "Dimensions", "Shaft length")
params.shaft_length = 80.0

params.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "Keyway width")
params.keyway_width = 5.0

params.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "Keyway depth")
params.keyway_depth = 3.0

params.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "Keyway height")
params.keyway_height = 20.0

params.addProperty("App::PropertyInteger", "num_keyways", "Dimensions", "Number of keyways")
params.num_keyways = 2

# --- Feature 1: Main Shaft ---
# Sketch on XY plane (Origin)
main_sketch = body.newObject("Sketcher::SketchObject", "MainShaftSketch")
main_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
main_sketch.ObjectType = "Sketcher::Plane"
main_sketch.Plane = "XY_Plane"
main_sketch.Lock = False
main_sketch.Constraints = []

# Add a circle to the sketch
main_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaft_diameter / 2.0), False)
main_sketch.updateGeo()

# Pad the circle to create the shaft
main_pad = body.newObject("PartDesign::Pad", "MainShaftPad")
main_pad.Profile = main_sketch
main_pad.Length = params.shaft_length
main_pad.makeSolid = True
main_pad.setExpression("Length", "Parameters.shaft_length")
main_pad.setExpression("Profile", "MainShaftSketch")

# --- Feature 2: Keyways ---
# We need to create the keyways using a sketch on the top face of the shaft.
# Since we cannot easily get the "Top" face object programmatically without querying topology,
# we will place the sketch on a plane parallel to XY at Z = shaft_length/2 - keyway_height/2? 
# No, keyways are usually cut from the side or top depending on orientation.
# Let's assume the shaft stands on the XY plane (base at Z=0).
# The top face is at Z = shaft_length.
# We will create a sketch on a plane parallel to XY at Z = shaft_length - keyway_height.
# Actually, to make it fully parametric and robust, let's place the sketch on a plane 
# defined by a distance from the origin or from the body's base.

# Define a plane for the keyway sketch. 
# Z_position of the cut face = Shaft Length - Keyway Height.
# We use a Sketcher::SketchObject with AttachmentOffset.
keyway_sketch = body.newObject("Sketcher::SketchObject", "KeywaySketch")
keyway_sketch.Placement = App.Placement(App.Vector(0, 0, params.shaft_length - params.keyway_height))
keyway_sketch.ObjectType = "Sketcher::Plane"
keyway_sketch.Plane = "XY_Plane"
keyway_sketch.Lock = False
keyway_sketch.Constraints = []

# Calculate radius for the keyway sketch
shaft_radius = params.shaft_diameter / 2.0
keyway_radius = shaft_radius - params.keyway_depth

# Add a rectangle for the keyway profile
# Rectangle width = keyway_width, height = keyway_width (square cut usually)
# Position it to start at the edge. 
# Left edge at x = -keyway_radius, Right edge at x = -keyway_radius + keyway_width
# y goes from -keyway_width/2 to +keyway_width/2
keyway_rect = Part.makeBox(
    params.keyway_width, 
    params.keyway_width, 
    0.0, # thickness, will be extruded
    App.Vector(-keyway_radius, 0, 0)
)
keyway_sketch.addGeometry(keyway_rect, False)
keyway_sketch.updateGeo()

# Add constraints to lock the rectangle relative to the sketch plane
# 1. Bottom edge tangent to the circle (shaft outline)
# 2. Top edge tangent to the circle (shaft outline)
# 3. Centered on Y axis? Or aligned? Let's assume centered on Y axis for simplicity 
#    and symmetry, or aligned to one side. 
#    Standard keyways are often centered or offset. Let's center them on the X-axis 
#    (spanning from -R to -R+W) is easier to define by tangency.
#    Actually, the rectangle above is placed at x = -R.
#    Let's add tangency constraints to the circle.

# Constraint 1: Bottom horizontal line tangent to circle
# Constraint 2: Top horizontal line tangent to circle
# We need to identify the segments. In Sketcher, lines are segments.
# The rectangle has 4 segments. 
# Let's simplify: Add a circle of the same diameter to the sketch as a reference, 
# then constrain the rectangle to it.
ref_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), shaft_radius)
keyway_sketch.addGeometry(ref_circle, False)

# Now we need to add geometric constraints.
# Since we added a rectangle and a circle to the same sketch, we can constrain them.
# However, FreeCAD 1.1 Python API for adding constraints programmatically requires specific indices.
# It is safer to construct the geometry such that it fits or use the 'Coincident'/'Tangent' method.
# Let's try to constrain the rectangle's bottom-left corner to the circle? No.
# Let's use the 'Tangent' constraint.
# We need to add the constraint objects.
# Note: In headless mode, adding specific constraints by index can be tricky if geometry order changes.
# Alternative: Just place the box manually and rely on the fact that it's a subtraction.
# But to ensure it fits perfectly (tangent), we must constrain it.

# Let's try a different approach for the sketch geometry:
# 1. Add a line segment at y=0, x from -R to -R+W.
# 2. Add a line segment at y=0, x from -R to -R+W (top? no).
# Let's stick to the Box method but add constraints explicitly.
# The rectangle segments are 0,1,2,3.
# Circle points? Hard to index dynamically.

# Robust Headless Approach:
# 1. Create a sketch.
# 2. Add a circle (shaft profile).
# 3. Add a rectangle.
# 4. Add constraint: Tangent between bottom of rect and circle.
# 5. Add constraint: Tangent between top of rect and circle.
# 6. Add constraint: Symmetry on Y (if centered) or fix X position.
# Let's assume the keyway is on the negative X side, spanning from -R to -R+W.
# We will constrain the left side of the rectangle to be tangent to the circle?
# No, the rectangle is flat. The side is vertical.
# Let's define the rectangle by its center.
# Center X = -R + W/2. Center Y = 0.
# We can add a point at (-R, 0) and constrain it to be on the circle? No, it's inside.
# Let's just define the rectangle dimensions and position manually in the vector, 
# and add a 'Fixed' or 'Parallel' constraint to ensure it stays on the plane.
# And 'Tangent' constraints.

# Re-evaluating constraint addition in headless:
# Sketcher.Constraint("Tangent", segmentIndex1, pointIndex1, segmentIndex2, pointIndex2)
# This is complex to get right without GUI feedback.
# SIMPLIFICATION: We will construct the sketch geometry such that it is self-contained 
# and use a 'Point' on the circle and 'Distance' constraints.

# New Sketch Construction:
# 1. Circle (Shaft)
# 2. Point A on the circle at angle 180 (leftmost point).
# 3. Point B offset from A by keyway_width along X.
# 4. Point C offset from B by keyway_width along Y.
# 5. Point D offset from C by keyway_width along -Y.
# 6. Connect A-B-C-D-A.
# 7. Constraint: Point A is on Circle.
# 8. Constraint: Point B is on Circle? No, B is inside.
# 9. Constraint: Line AB is tangent to Circle?
#    If we make A the leftmost point of the circle, the tangent is vertical.
#    So we need a vertical line at x = -R.
#    Then extend it up and down by keyway_width/2? No, keyway width is usually the cut width.
#    Let's assume the keyway is a square hole cut into the side.
#    Width = 5mm. Depth = 3mm. Height = 20mm.
#    So on the top face, we cut a 5x5mm square? Or 5mm wide slot?
#    "Keyway: width, depth, height". Usually width is along the shaft axis? 
#    No, for a shaft, keyway width is the dimension across the face (transverse).
#    Depth is how deep it goes in. Height is the length of the keyway along the shaft.
#    Wait, standard keyway dimensions:
#    - Width (b): dimension across the face (transverse).
#    - Depth (t): dimension into the shaft.
#    - Length (L): dimension along the axis.
#    The prompt says: "keyway_width = 5 mm, keyway_depth = 3 mm, keyway_height = 20 mm".
#    Given "Height" = 20mm and Shaft Length = 80mm, it is highly likely "Height" refers to the 
#    length of the keyway along the shaft axis.
#    So we are cutting a slot of 5mm width (transverse) x 3mm depth (radial) x 20mm length (axial).
#    And there are 2 such keyways.

# Correction on Sketch Orientation:
# The sketch is on the TOP FACE (XY plane at Z = shaft_length - depth).
# The sketch needs to define the slot along the Z-axis (which is the shaft axis).
# So the sketch should be on the plane Z = shaft_length - depth.
# The sketch plane normal is Z (same as XY).
# The sketch geometry will be a rectangle:
# - Width = keyway_width (along X or Y)
# - Length = keyway_height (along the other axis, which is the shaft axis).
# Let's align the keyway along the Y-axis (length of keyway along shaft).
# Position: 
#   Center X = -shaft_radius + keyway_width/2 (Left side, centered on X? Or aligned to edge?)
#   Let's align the inner edge to the surface of the shaft for a standard keyway.
#   Inner X = -shaft_radius. Outer X = -shaft_radius + keyway_width.
#   Center Y = 0.
#   Length along Y = keyway_height.

# Revised Sketch:
# 1. Circle (Reference)
# 2. Rectangle defined by:
#    - Point 1: (-shaft_radius, -keyway_height/2) -> Inner start
#    - Point 2: (-shaft_radius + keyway_width, -keyway_height/2) -> Inner end
#    - Point 3: (-shaft_radius + keyway_width, +keyway_height/2) -> Outer end
#    - Point 4: (-shaft_radius, +keyway_height/2) -> Outer start
#    - Connect 1-2-3-4-1.
# 3. Constraints:
#    - Point 1 lies on the circle? No, it's inside.
#    - The line from 1 to 4 (Left side) is tangent to the circle.
#    - The line from 1 to 2 (Bottom side) is perpendicular to 1-4.
#    - The line from 3 to 4 (Top side) is perpendicular to 1-4.
#    - The line from 2 to 3 (Right side) is perpendicular to 1-4.
#    - Symmetry on Y axis for the rectangle.
#    - Distance from center to left side = shaft_radius.

# To implement this reliably in headless without GUI interaction:
# We can create the rectangle using Part primitives and place it.
# Then we rely on the fact that we are subtracting. 
# BUT, to ensure it fits exactly on the surface (tangent), we must constrain it.
# We will add a 'Coincident' constraint between the midpoint of the left edge of the rect 
# and the leftmost point of the circle? 
# No, 'Coincident' works for points.
# We can add a 'Point' geometry at (-shaft_radius, 0) and constrain it to the circle.
# Then construct the rectangle relative to that point.

# Let's try a simpler geometric constraint set:
# 1. Circle (Shaft)
# 2. Line Segment (Left Edge of Keyway)
#    Start: (-shaft_radius, -keyway_height/2)
#    End: (-shaft_radius, +keyway_height/2)
# 3. Line Segment (Bottom Edge)
#    Start: (-shaft_radius, -keyway_height/2)
#    End: (-shaft_radius + keyway_width, -keyway_height/2)
# 4. Line Segment (Top Edge)
#    Start: (-shaft_radius + keywidth, +keyway_height/2)
#    End: (-shaft_radius, +keyway_height/2)
# 5. Close loop.
# Constraints:
#    - The start point of Line 1 is on the Circle? No.
#    - The entire Line 1 is tangent to the circle.
#    - The midpoint of Line 1 is on the circle? No, the line is outside the circle except at tangent point?
#    - Wait, the keyway is cut INTO the shaft.
#    - The rectangle represents the material to be REMOVED.
#    - The rectangle is INSIDE the circle.
#    - The LEFT edge of the rectangle touches the circle at one point?
#    - No, the keyway is a slot. The slot goes from the edge inwards.
#    - So the RIGHT edge of the rectangle is the inner part. The LEFT edge is the surface.
#    - So the LEFT edge of the rectangle should be tangent to the circle.
#    - The rectangle is defined by X from -R to -R+W.
#    - The line X = -R is tangent to the circle at (-R, 0).
#    - So we constrain the midpoint of the Left Edge (Line 1) to the circle? No.
#    - We constrain the Left Edge to be tangent to the circle.

# Since adding "Tangent" constraints between a line and a circle is complex via API indices,
# we will use a workaround:
# Create a Point at (-shaft_radius, 0). Constrain it to the Circle (Coincident).
# Then create the rectangle such that its left side passes through this point.
# And its normal is parallel to X axis.
# And its length is keyway_height.
# And its width is keyway_width.
# And it is centered on the point's Y (which is 0).

# Implementation Plan:
# 1. Add Circle.
# 2. Add Point at (-shaft_radius, 0).
# 3. Constrain Point to Circle (Coincident).
# 4. Add Line (Left Edge) passing through Point, length = keyway_height, vertical.
#    Wait, "Vertical" means along Y.
#    So Line from (-R, -H/2) to (-R, H/2).
#    This line is tangent to the circle.
# 5. Add Line (Bottom Edge) from (-R, -H/2) to (-R+W, -H/2).
# 6. Add Line (Top Edge) from (-R+W, H/2) to (-R, H/2).
# 7. Constrain Top/Bottom lines parallel to Left line?
#    Or just use a closed loop of 4 lines.
#    Constraint: Distance between Left Edge and Right Edge = keyway_width.
#    Constraint: Midpoint of Top/Bottom edges are aligned with midpoint of Left Edge?
#    Actually, simpler:
#    - Define a line segment for the width.
#    - Offset it by keyway_width.
#    - Define the height.
#    This is getting too complex for pure code constraints.

# Alternative: Use Part.makeBox and place it, then use a "Distance" constraint to push it to the surface.
# But the "Pad" subtracts the sketch area.
# If the sketch is slightly inside, the cut won't be clean.
# If the sketch is slightly outside, it clips the body.
# We must ensure the sketch is exactly tangent.
# 
# Let's use the 'Point on Circle' method to define the corner.
# Point P at (-shaft_radius, 0).
# Line L1 (Left
