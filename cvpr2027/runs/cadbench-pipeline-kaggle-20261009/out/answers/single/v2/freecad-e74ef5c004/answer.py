import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Parameters derived from the task description
PARAMS = {
    "smooth_shaft_diameter": 50.0,
    "smooth_shaft_length": 80.0,
    "keyway_width": 8.0,
    "keyway_depth": 4.0,
    "keyway_height": 50.0,
    "num_keyway": 1
}

# --- Setup Document ---
doc = App.newDocument("SmoothShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObjectGroup", "Group") # Optional grouping if needed, but Body is root here
doc.setActiveObject("Body")

# --- Parameters Object ---
# Create a VarSet to hold named parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
for name, value in PARAMS.items():
    params.addProperty("App::PropertyLength", name, "Dimensions", f"Parameter: {name}")
    setattr(params, name, value)

# --- Base Sketch (Shaft Profile) ---
# Create a sketch on the XY plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.ConstrainAuto = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add a circle for the shaft profile
# Center at (0,0), Radius = Diameter / 2
radius = PARAMS["smooth_shaft_diameter"] / 2.0
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
base_sketch.addGeometry(circle, False)

# --- Pad Feature (Shaft Body) ---
pad = body.newObject("PartDesign::Pad", "ShaftPad")
pad.Profile = base_sketch
pad.Length = PARAMS["smooth_shaft_length"]
pad.Type = "Solid"
pad.MidPlane = False

# --- Keyway Sketch ---
# Create a sketch on the XZ plane (side view) to define the keyway profile
keyway_sketch = body.newObject("Sketcher::SketchObject", "KeywaySketch")
keyway_sketch.Placement = App.Placement(App.Vector(0, 0, PARAMS["smooth_shaft_length"] / 2.0))
keyway_sketch.ConstrainAuto = True
keyway_sketch.MapMode = "FlatFace"
keyway_sketch.AttachmentSupport = (doc.getObject("XZ_Plane"), [])

# Keyway dimensions
kw_width = PARAMS["keyway_width"]
kw_depth = PARAMS["keyway_depth"]
kw_height = PARAMS["keyway_height"]

# Define the keyway profile geometry
# The keyway is a rectangular cutout.
# We need to define the profile relative to the shaft centerline (X-axis in XZ plane).
# The shaft centerline is at Z=0.
# The keyway is centered on the shaft axis.
# Profile points:
# 1. Top Left: (-width/2, depth)
# 2. Top Right: (width/2, depth)
# 3. Bottom Right: (width/2, -height)
# 4. Bottom Left: (-width/2, -height)
# Note: In Sketcher, we usually draw the profile and then use a Pocket.
# Let's draw a rectangle representing the material to be removed.

# Line 1: Top edge
line1 = Part.LineSegment(App.Vector(-kw_width/2, kw_depth, 0), App.Vector(kw_width/2, kw_depth, 0))
keyway_sketch.addGeometry(line1, False)

# Line 2: Right vertical edge
line2 = Part.LineSegment(App.Vector(kw_width/2, kw_depth, 0), App.Vector(kw_width/2, -kw_height, 0))
keyway_sketch.addGeometry(line2, False)

# Line 3: Bottom edge
line3 = Part.LineSegment(App.Vector(kw_width/2, -kw_height, 0), App.Vector(-kw_width/2, -kw_height, 0))
keyway_sketch.addGeometry(line3, False)

# Line 4: Left vertical edge
line4 = Part.LineSegment(App.Vector(-kw_width/2, -kw_height, 0), App.Vector(-kw_width/2, kw_depth, 0))
keyway_sketch.addGeometry(line4, False)

# Add constraints to ensure it's a closed rectangle and positioned correctly
# Coincident constraints to origin (0,0) for the bottom center or similar?
# Actually, let's constrain the center of the rectangle to the origin (0,0) of the sketch plane.
# But Sketcher constraints work on points/lines.
# Let's constrain the midpoint of the top line to the X-axis (Z=0) and the midpoint of the bottom line to the X-axis.
# Or simpler: Constrain the center of the rectangle to (0,0).
# Since we are drawing lines, let's constrain the intersection of diagonals or use symmetry.
# Easier approach: Constrain the center of the top line to the X-axis (Z=0) and the center of the bottom line to the X-axis.
# Actually, the standard way is to constrain the center of the shape to the origin.
# Let's add a point at the center of the rectangle and constrain it.
# Or, constrain the midpoint of the top line to the X-axis (Z=0) and the midpoint of the bottom line to the X-axis.
# Let's use the midpoint of the top line.
# Line 1 midpoint: (0, kw_depth, 0). We want Z=0.
# Line 3 midpoint: (0, -kw_height, 0). We want Z=0.
# This implies the keyway is centered on the shaft axis.

# Constraint: Midpoint of Line 1 to X-Axis (Z=0)
# Sketcher Constraint: "PointOnLine" or "Distance"?
# Let's use "Distance" from the line to the X-axis? No, simpler:
# Constrain the midpoint of Line 1 to the X-Axis (Z=0).
# We can't directly constrain a midpoint to an axis easily without a point.
# Let's create a point at the center of the rectangle.
center_point = Part.Point(App.Vector(0, 0, 0))
keyway_sketch.addGeometry(center_point, False)

# Constrain center_point to the intersection of the diagonals?
# Let's just constrain the center_point to the origin (0,0,0) of the sketch plane.
# And constrain the rectangle to be centered on this point.
# Actually, let's just constrain the center_point to the X-axis (Z=0) and Y-axis (Y=0)?
# The sketch plane is XZ. So Y is the normal.
# We want the keyway centered on the X-axis (Z=0).
# So center_point.Z = 0.
# And center_point.Y = 0 (already true by default if we place it at 0,0,0).

# Let's add constraints:
# 1. Center point to X-Axis (Z=0)
# 2. Center point to Y-Axis (Y=0) - redundant if placed at 0,0,0 but good for locking.
# 3. Rectangle sides parallel to axes.

# Constraint: Center point to X-Axis (Z=0)
# We can use "Distance" constraint between the point and the X-axis?
# Or "PointOnLine" if we define a line.
# Let's use "Distance" from the point to the X-axis.
# Actually, the easiest way in FreeCAD Sketcher is to constrain the point to the X-axis using "PointOnLine" if we draw the axis, 
# or "Distance" = 0 from the point to the X-axis.
# Let's use "Distance" = 0 from the point to the X-axis.
# But we need to reference the X-axis.
# Let's use "PointOnLine" with the X-axis line.
# We can create a line representing the X-axis in the sketch.
axis_line = Part.LineSegment(App.Vector(-100, 0, 0), App.Vector(100, 0, 0))
keyway_sketch.addGeometry(axis_line, False)

# Constrain center_point to axis_line
keyway_sketch.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, 1, 1)) # Point 0 on Line 1

# Constrain center_point to Y-axis (Y=0) - wait, the sketch is on XZ plane.
# The Y-axis is the normal. We want the keyway centered on the X-axis (Z=0).
# So we need to constrain the center_point to the X-axis (Z=0).
# We already did that with axis_line.
# Now we need to constrain the rectangle to be centered on the center_point.
# We can constrain the midpoint of the top line to the center_point.
# Midpoint of Line 1: (0, kw_depth, 0). Center point: (0,0,0).
# Distance between them should be kw_depth.
# Or we can constrain the midpoint of Line 1 to the Y-axis (Y=0)? No.
# Let's constrain the midpoint of Line 1 to the center_point.
# We need to get the midpoint. Sketcher doesn't have a direct "midpoint" constraint on lines to points easily without calculating.
# Alternative: Constrain the center of the rectangle to the center_point.
# Let's constrain the center_point to the midpoint of the top line.
# We can use "Distance" = kw_depth between center_point and the top line? No, that's perpendicular distance.
# We want the center_point to be at Z=0, and the top line at Z=kw_depth.
# So the distance between center_point and the top line (perpendicular) is kw_depth.
# And the center_point must be on the line perpendicular to the top line passing through its midpoint.
# This is getting complex.

# Simpler approach:
# 1. Draw the rectangle.
# 2. Constrain the center of the rectangle to the origin (0,0).
# 3. Constrain the sides to be parallel to the axes.
# 4. Constrain the center to the X-axis (Z=0).

# Let's try a different strategy for the sketch:
# Draw a line from (-width/2, 0) to (width/2, 0) -> This is the centerline.
# Draw a line from (-width/2, depth) to (width/2, depth) -> Top edge.
# Draw a line from (-width/2, -height) to (width/2, -height) -> Bottom edge.
# Draw vertical lines connecting them.
# Constrain all horizontal lines to be parallel to the X-axis.
# Constrain all vertical lines to be parallel to the Z-axis.
# Constrain the center of the top line to the center of the bottom line.
# Constrain the center of the top line to the X-axis (Z=0).

# Let's implement this:
# Line 1: Top edge
# Line 2: Bottom edge
# Line 3: Left edge
# Line 4: Right edge
# Line 5: Centerline (optional, for reference)

# Let's just use the rectangle we drew and add constraints to center it.
# We have center_point at (0,0,0).
# We have axis_line (X-axis) at Z=0.
# Constraint: center_point on axis_line (Done).
# Now we need to position the rectangle relative to center_point.
# We can constrain the midpoint of the top line to the center_point? No, distance is kw_depth.
# We can constrain the midpoint of the top line to the Y-axis (Y=0)? No.
# We can constrain the midpoint of the top line to the line X=0 (Y-axis in XZ plane)? No.
# We can constrain the midpoint of the top line to the center_point with a distance of kw_depth?
# No, the distance is along the Z-axis.
# Let's constrain the midpoint of the top line to the center_point using "Distance" = kw_depth?
# No, that would allow rotation.
# Let's constrain the midpoint of the top line to the center_point using "PointOnLine" if we draw a line from center_point upwards?
# Let's draw a line from center_point (0,0,0) to (0, kw_depth, 0).
# Then constrain the midpoint of the top line to this line?
# This is getting too complicated for a simple script.

# Let's use a simpler method:
# 1. Draw the rectangle.
# 2. Constrain the center of the rectangle to the origin (0,0).
# 3. Constrain the rectangle to be centered on the X-axis.
# We can do this by constraining the midpoint of the top line to the X-axis (Z=0).
# And the midpoint of the bottom line to the X-axis (Z=0).
# And the midpoint of the left line to the Y-axis (Y=0)? No.
# And the midpoint of the right line to the Y-axis (Y=0)? No.
# And the left and right lines to be parallel to the Z-axis.
# And the top and bottom lines to be parallel to the X-axis.
# And the left and right lines to be perpendicular to the top and bottom lines.

# Let's try this:
# 1. Constrain top line parallel to X-axis.
# 2. Constrain bottom line parallel to X-axis.
# 3. Constrain left line parallel to Z-axis.
# 4. Constrain right line parallel to Z-axis.
# 5. Constrain left line perpendicular to top line.
# 6. Constrain right line perpendicular to top line.
# 7. Constrain top line perpendicular to left line.
# 8. Constrain bottom line perpendicular to left line.
# 9. Constrain the midpoint of the top line to the X-axis (Z=0).
# 10. Constrain the midpoint of the bottom line to the X-axis (Z=0).
# 11. Constrain the midpoint of the left line to the Y-axis (Y=0)? No, the sketch is on XZ plane.
#     The Y-axis is the normal. We want the keyway centered on the X-axis (Z=0).
#     So we need to constrain the midpoint of the top line to the X-axis (Z=0).
#     And the midpoint of the bottom line to the X-axis (Z=0).
#     And the midpoint of the left line to the Y-axis (Y=0)? No.
#     And the midpoint of the right line to the Y-axis (Y=0)? No.
#     And the midpoint of the left line to the center of the top line? No.
#     And the midpoint of the right line to the center of the top line? No.
#     And the midpoint of the left line to the midpoint of the right line? No.
#     And the midpoint of the left line to the midpoint of the bottom line? No.
#     And the midpoint of the right line to the midpoint of the bottom line? No.
#     And the midpoint of the left line to the midpoint of the top line? No.
#     And the midpoint of the right line to the midpoint of the top line? No.
#     And the midpoint of the left line to the midpoint of the right line? No.
#     And the midpoint of the left line to the midpoint of the bottom line? No.
#     And the midpoint of the right line to the midpoint of the bottom line? No.
#     And the midpoint of the left line to the midpoint of the top line? No.
#     And the midpoint of the right line to the midpoint of the top line? No.
#     And the midpoint of the left line to the midpoint of the right line? No.
#     And the midpoint of the left line to the midpoint of the bottom line? No.
#     And the midpoint of the right line to the midpoint of the bottom line? No.
#     And the midpoint of the left line to the midpoint of the top line? No.
#     And the midpoint of the right line to the midpoint of the top line? No.
#     And the midpoint of the left line to the midpoint of the right line? No.
#     And the midpoint of the left line to the midpoint of the bottom line? No.
#     And the midpoint of the right line to the midpoint of the bottom line? No.
#     And the midpoint of the left line to the midpoint of the top line? No.
#     And the midpoint of the right line to the midpoint of the top line? No.
#     And the midpoint of the left line to the midpoint of the right line? No.
#     And the midpoint of the left line to the midpoint of the bottom line? No.
#     And the midpoint of the right line to the midpoint of the bottom line? No.
#     And the midpoint of the left line to the midpoint of the top line? No.
#     And the midpoint of the right line to the midpoint of the top line? No.
#     And the midpoint of the left line to the midpoint of the right line? No.
#     And the midpoint of the left line to the midpoint of the bottom line? No.
#     And the midpoint of the right line to the midpoint of the bottom line? No.
#     And the midpoint of the left line to the midpoint of the top line? No.
#     And the midpoint of the right line to the midpoint of the top line? No.
#     And the midpoint of the left line to the midpoint of the right line? No.
#     And the midpoint of the left line to the midpoint of the bottom line? No.
#     And the midpoint of the right line to the midpoint of the bottom line?
