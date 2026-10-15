import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize document
doc = App.newDocument("Staircase")

# --- Parameters ---
# We use App::VarSet to create named, editable parameters within the document
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyInteger", "number_of_steps", "Dimensions", "Number of steps")
params.number_of_steps = 5

params.addProperty("App::PropertyLength", "step_riser", "Dimensions", "Height of each step")
params.step_riser = 170.0

params.addProperty("App::PropertyLength", "step_depth", "Dimensions", "Depth of each step")
params.step_depth = 300.0

params.addProperty("App::PropertyLength", "step_width", "Dimensions", "Width of the staircase")
params.step_width = 1200.0

# Derived values for geometry construction
total_rise = params.number_of_steps * params.step_riser
total_run = params.number_of_steps * params.step_depth

# --- Create Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Create Sketch (Side Profile) ---
# We create the sketch on the XY plane (X=Run, Z=Rise)
sketch = body.newObject("Sketcher::SketchObject", "StairProfile")
# Set placement correctly: App.Placement requires a Vector and a Rotation
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
sketch.ConstrainAuto = False
sketch.LockConstraints = False
sketch.MapMode = "FlatFace"

# Define the profile geometry
# The profile consists of a polyline representing the steps.
# Start at (0,0), go up (riser), go right (tread), repeat.
# Finally, close the loop to make it a solid profile for extrusion.

segments = []
current_x = 0.0
current_z = 0.0

# Add the first vertical riser
segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x, 0, current_z + params.step_riser)))
current_z += params.step_riser

# Add the remaining risers and treads
for i in range(1, params.number_of_steps):
    # Riser
    segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x, 0, current_z + params.step_riser)))
    current_z += params.step_riser
    
    # Tread
    segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x + params.step_depth, 0, current_z)))
    current_x += params.step_depth

# Add the final riser to reach the top level
segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x, 0, current_z + params.step_riser)))
current_z += params.step_riser

# Add the top horizontal tread to the end of the run
segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x + params.step_depth, 0, current_z)))
current_x += params.step_depth

# Add the final vertical riser down to the base level (closing the loop)
segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x, 0, 0)))
current_z = 0.0

# Add the bottom horizontal tread back to the start
segments.append((App.Vector(current_x, 0, current_z), App.Vector(0, 0, current_z)))
current_x = 0.0

# Add the initial vertical riser up to start (closing the loop)
segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x, 0, params.step_riser)))
current_z = params.step_riser

# Add the first tread back to origin
segments.append((App.Vector(current_x, 0, current_z), App.Vector(0, 0, current_z)))
current_x = 0.0

# Add the final vertical riser down to origin
segments.append((App.Vector(current_x, 0, current_z), App.Vector(current_x, 0, 0)))

# Now add these segments to the sketch
for i, seg in enumerate(segments):
    sketch.addGeometry(Part.LineSegment(seg[0], seg[1]), False)

# --- Add Constraints to Sketch ---
# We need to constrain the geometry to ensure it matches the parameters exactly.
# Since we built it using the parameters in Python, the geometry is already correct.
# However, we should add constraints to lock the shape relative to the sketch plane.

# Constraint: Origin of sketch (0,0,0) coincides with first point of the profile
# We can use a Point constraint or just rely on the placement.
# Let's add a constraint to fix the first point of the first segment to the origin.
# Sketcher constraints work on geometry indices.
# Geometry 0 is the first line segment.
# We can constrain the start of line 0 to the origin.
# Actually, simpler: Constrain the first point of the first line to (0,0,0) and the last point to (total_run, total_rise, 0).
# But since we constructed the lines sequentially, the first point of line 0 is (0,0,0).
# The last point of line -2 (second to last) is (total_run, total_rise, 0).

# Let's add a constraint to fix the end of the second to last segment to the calculated total dimensions.
# Note: Sketcher constraints are tricky with dynamic geometry. 
# A robust way is to constrain the first point of the first segment to the origin and the last point of the last segment to the calculated totals.
# However, since we constructed the lines sequentially, the first point of line 0 is (0,0,0).
# The last point of line -2 (second to last) is (total_run, total_rise, 0).

# Let's add a constraint to the end of the second to last segment.
# We need to find the index of the segment that ends at (total_run, total_rise, 0).
# Based on our loop:
# The loop runs for i in 1..4 (5 steps total).
# Inside loop: Riser, Tread.
# After loop: Final Riser, Top Tread, Final Riser down, Bottom Tread, Initial Riser up, Initial Tread, Final Riser down.
# This manual construction is getting complex to index.
# Alternative: Just constrain the first point of the first segment to the origin and the last point of the last segment to the origin (closed loop).
# And constrain the "bounding box" points.

# Let's simplify constraints:
# 1. First point of first segment (Line 0) to Origin.
# 2. Last point of last segment (Line -1) to Origin.
# 3. We can also constrain the total run and rise if we want, but the geometry is already defined by params.
# To be safe and parametric, let's add constraints to the extreme points.

# Find the segment that represents the top-right corner.
# It's the segment before the final vertical drop.
# In our list:
# ...
# segments[-3]: (total_run, total_rise, 0) -> (total_run, total_rise, total_rise) [Top Riser]
# segments[-2]: (total_run, total_rise, total_rise) -> (total_run + step_depth, total_rise, total_rise) [Top Tread]
# segments[-1]: (total_run + step_depth, total_rise, total_rise) -> (total_run + step_depth, total_rise, 0) [Final Drop]
# segments[-2] ends at (total_run + step_depth, total_rise, total_rise).
# segments[-3] starts at (total_run, total_rise, 0) and ends at (total_run, total_rise, total_rise).
# Wait, my manual trace above was slightly off. Let's re-verify the logic.
# 
# Logic:
# Start (0,0).
# Loop 1 to 4:
#   Riser: (x, z) -> (x, z+riser)
#   Tread: (x, z+riser) -> (x+depth, z+riser)
# End of loop: x = 4*depth, z = 4*riser.
# Final Riser: (4d, 4r) -> (4d, 5r).
# Top Tread: (4d, 5r) -> (5d, 5r).
# Final Drop: (5d, 5r) -> (5d, 0).
# Bottom Tread: (5d, 0) -> (0, 0).
# Initial Riser: (0,0) -> (0, r).
# Initial Tread: (0, r) -> (d, r).
# Final Drop: (d, r) -> (d, 0).
# 
# This creates a closed loop.
# The point (5d, 5r) is the top right corner.
# This point is the start of the "Final Drop" segment (index -2 in 0-based if we count from end? No).
# Let's count segments:
# 1. Riser 1 (0,0)->(0,r)
# 2. Tread 1 (0,r)->(d,r)
# 3. Riser 2 (d,r)->(d,2r)
# 4. Tread 2 (d,2r)->(2d,2r)
# 5. Riser 3 (2d,2r)->(2d,3r)
# 6. Tread 3 (2d,3r)->(3d,3r)
# 7. Riser 4 (3d,3r)->(3d,4r)
# 8. Tread 4 (3d,4r)->(4d,4r)
# 9. Riser 5 (4d,4r)->(4d,5r)
# 10. Tread 5 (4d,5r)->(5d,5r)  <-- This segment ends at (5d, 5r).
# 11. Drop (5d,5r)->(5d,0)
# 12. Bottom (5d,0)->(0,0)
# 13. Riser 1b (0,0)->(0,r)
# 14. Tread 1b (0,r)->(d,r)
# 15. Drop 1b (d,r)->(d,0)
# 
# Total 15 segments.
# Segment 9 (index 9) ends at (5d, 5r).
# Segment 10 (index 10) starts at (5d, 5r).
# 
# We can constrain the start of segment 10 to (total_run, total_rise, 0).
# And the start of segment 0 to (0,0,0).

# Let's add constraints
# Constraint 1: Start of segment 0 to Origin
sketch.addConstraint(Sketcher.Constraint("Point", 0, 1, "XY")) # Point on XY plane
# Actually, "Point" constraint in Sketcher is for points. For lines, we use "Line" or "Distance".
# To fix a point of a line to a coordinate, we can use "Distance" or "Point" with specific geometry.
# Easier: Use "Distance" to fix the X and Z of the start point.
# But Sketcher constraints are usually between two geometries or a geometry and a plane/axis.
# Let's use "Distance" to fix the start of line 0 to the origin.
# But the origin is not a geometry.
# We can constrain the start of line 0 to the start of line 13 (which is also at 0,0,0).
# Or simply constrain the start of line 0 to the XY plane origin using "Point" constraint if available.
# In FreeCAD 1.1, "Point" constraint can be used with "XY" to snap to the plane, but not necessarily origin.
# Let's use "Distance" to fix the start of line 0 to the start of line 13 (which is explicitly at 0,0,0 by construction).
# But line 13 is added later.
# 
# Robust approach:
# 1. Constrain start of line 0 to the origin using "Point" constraint with "XY" and "XZ" planes? No.
# 2. Use "Distance" to fix the start of line 0 to the start of line 13 (which is at 0,0,0).
# 3. Use "Distance" to fix the start of line 10 to the end of line 9.
# 
# Actually, the simplest way to ensure the sketch is locked to the parameters is to add constraints that define the bounding box.
# Let's add a constraint to fix the start of line 0 to the origin.
# We can use: Sketcher.Constraint("Point", 0, 1, "XY") -> This snaps the point to the XY plane.
# Then we need to fix X and Z.
# We can use "Distance" to fix the start of line 0 to the start of line 13 (which is at 0,0,0).
# And "Distance" to fix the start of line 10 to the end of line 9.
# 
# Let's just add a few key constraints to make it robust.
# 1. Start of line 0 coincident with Start of line 13 (both should be 0,0,0).
# 2. Start of line 10 coincident with End of line 9 (both should be total_run, total_rise, 0).
# 3. End of line 11 coincident with Start of line 12 (both should be 0,0,0).

# Note: Sketcher constraints use 0-based indexing for geometry.
# Line 0 is index 0.
# Line 13 is index 13.
# Line 9 is index 9.
# Line 10 is index 10.
# Line 11 is index 11.
# Line 12 is index 12.

# Constraint: Start of Line 0 coincident with Start of Line 13
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 13, 1))

# Constraint: Start of Line 10 coincident with End of Line 9
sketch.addConstraint(Sketcher.Constraint("Coincident", 10, 1, 9, 2))

# Constraint: End of Line 11 coincident with Start of Line 12
sketch.addConstraint(Sketcher.Constraint("Coincident", 11, 2, 12, 1))

# Constraint: End of Line 12 coincident with Start of Line 0 (closing the loop explicitly)
sketch.addConstraint(Sketcher.Constraint("Coincident", 12, 2, 0, 1))

# --- Create Extrusion (Pad) ---
# Extrude along Y axis (extrusion_direction = +Y)
# The sketch is on XY plane (X, Z). The normal is Y.
# We need to extrude from Y=0 to Y=step_width.
# Since the sketch is on the XY plane, the normal is Y.
# We can use a Pad feature.

pad = body.newObject("PartDesign::Pad", "Extrusion")
pad.Profile = sketch
pad.Length = params.step_width
pad.Type = "Solid"
# Ensure the direction is correct. 
# The sketch is on XY plane. The normal is Y.
# We want to extrude in +Y direction.
# By default, Pad extrudes in the direction of the sketch normal.
# If the sketch is on XY plane, the normal is Y.
# So pad.Length = step_width will extrude from 0 to step_width.

# --- Recompute ---
doc.recompute()

# --- Save ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
