import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize the document
doc = App.newDocument("StepPart")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject(App.GetClassOf(body), "Body") # Ensure it's added to the doc tree properly in 1.1 if needed, 
                                             # though newObject usually handles it.
doc.recompute() # Initial recompute

# Define named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyInteger", "number_of_tiers", "Dimensions", "Number of steps")
params.number_of_tiers = 3

params.addProperty("App::PropertyLength", "riser", "Dimensions", "Height of each step")
params.riser = 150.0

params.addProperty("App::PropertyLength", "depth", "Dimensions", "Depth of each step")
params.depth = 300.0

params.addProperty("App::PropertyLength", "width", "Dimensions", "Extrusion width")
params.width = 1200.0

# --- Step 1: Create the Side Profile Sketch ---
# We sketch on the XZ plane. 
# X axis corresponds to the "Run" (horizontal).
# Z axis corresponds to the "Rise" (vertical).
sketch = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0)) # Origin at 0,0
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Attach to the XZ Plane (Standard axes: XY is 0, YZ is 1, XZ is 2 usually, but we specify plane name or index)
# In FreeCAD 1.1, AttachmentSupport for XZ plane is typically the plane object or "XZ_Plane"
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0))

# Define the geometry for the stepped profile
# We start at (0,0) and go right by 'total_run', then up by 'total_rise', alternating.
# Actually, standard step profile: 
# Start bottom-left. Go right (tread), go up (riser).
# Repeat.
# End at top-right.

# Calculate totals
num_tiers = params.number_of_tiers
riser_h = params.riser
depth_w = params.depth

# We will construct the profile points:
# (0,0) -> (depth, 0) -> (depth, riser) -> (2*depth, riser) -> ... -> (total_run, total_rise)
# Then close the loop back to (0, total_rise) -> (0,0)

points = []
x = 0.0
y = 0.0 # This is Z in our sketch coordinate system where X=Run, Z=Rise

# First tread
points.append(App.Vector(x, y))
x += depth_w
points.append(App.Vector(x, y))

# Intermediate risers and treads
for i in range(num_tiers - 1):
    # Riser
    y += riser_h
    points.append(App.Vector(x, y))
    # Tread
    x += depth_w
    points.append(App.Vector(x, y))

# Final riser to reach the top level
y += riser_h
points.append(App.Vector(x, y))

# Close the profile: Top edge back to origin X
x -= depth_w * (num_tiers - 1) # Back to the left edge of the top block
points.append(App.Vector(x, y))

# Close loop: Down the total rise to origin
y -= riser_h * num_tiers
points.append(App.Vector(x, y))
# Back to start
points.append(App.Vector(0, 0))

# Create geometry segments
for i in range(len(points) - 1):
    sk = sketch.addGeometry(Part.LineSegment(points[i], points[i+1]), False)
    sk = sk[0] # Get the geometry object

# Add a coincident constraint to ensure the loop is closed (or just rely on the sketcher solver)
# It's good practice to constrain the first and last points if they aren't coincident by default in the solver
sk1_idx = 0
sk2_idx = len(points) - 1
sketch.addConstraint(Sketcher.Constraint("Coincident", sk1_idx, 1, sk2_idx, 0)) # Coincide end of line 1 to start of line 2 (conceptually)
# Note: The indices above are just for the solver. The actual geometry objects are the lines added.
# The Constraint syntax is: Sketcher.Constraint("Type", SketchIndex, PointIndex, SketchIndex2, PointIndex2)
# Since we added lines, the first point of the first line is at index 0,0. The last point of the last line is at index N-1,1.
# However, Sketcher constraints on closed loops are often handled automatically if we just add the lines.
# Let's add a horizontal constraint for the bottom and a vertical for the left to fix the orientation.
sketch.addConstraint(Sketcher.Constraint("Fixed", 0, 0, "XZ_Plane", 1, 0, 0, 0)) # Fix first point at origin XZ plane
sketch.addConstraint(Sketcher.Constraint("Fixed", sk2_idx, 1, "XZ_Plane", 1, 0, 0, 0)) # Fix last point at origin XZ plane (actually we want it at (0,0) relative to sketch)
# Actually, simpler: Fix the first segment to be horizontal and start at origin.
# Let's re-add a specific constraint for the start point.
# The first line segment is index 0. Point 0 is at (0,0).
# Let's just add a horizontal constraint for the first line and a vertical for the last vertical line to ensure stability.
# But for a simple profile, adding the lines and letting the solver close it is usually fine if we constrain the start point.
# Let's constrain the start point to the origin.
# We need to find the geometry index of the first point.
# sketch.addGeometry returns a list of Geometry objects.
# Let's assume the first line is index 0.
sketch.addConstraint(Sketcher.Constraint("Fixed", 0, 0, "XZ_Plane", 1, 0, 0, 0))
# And constrain the overall height to be fixed relative to the plane
# Actually, let's just constrain the first point to (0,0) and the direction of the first line to be along X.
# This is handled by the Fixed constraint on the first point and the fact it's the first line.
# To ensure the loop closes perfectly:
# We will constrain the last point to coincide with the first point.
# But Sketcher constraints work on geometry objects.
# Let's just trust the sketcher solver to close the loop if we define the points in order.
# We will add a constraint to make the first line horizontal.
# The first line is between (0,0) and (depth, 0). It is already horizontal by construction, but we tell the sketcher.
# sketch.addConstraint(Sketcher.Constraint("Fixed", 0, 0, "XZ_Plane", 1, 0, 0, 0)) # First point at origin
# sketch.addConstraint(Sketcher.Constraint("Fixed", 1, 0, "XZ_Plane", 1, 0, depth_w, 0)) # Second point at (depth, 0)
# This over-constrains if we don't account for variables.
# Simpler approach for parametric steps:
# 1. Add lines.
# 2. Constrain first line to be horizontal.
# 3. Constrain first point to origin.
# 4. Constrain last line to be vertical.
# 5. Constrain last point to have same Z as first line + total_height? No.
# Let's just add a "Horizontal" constraint for the first line.
# And a "Vertical" constraint for the last line.
# And a "Fixed" constraint for the first point.
# And a "Coincident" constraint between the last point and the first point (to close the loop explicitly).

# Re-fetch the geometry indices for constraints
# The lines are added in order.
# Line 0: (0,0) to (depth, 0)
# ...
# Last Line: (x_start, top) to (0, top) -> Wait, my point generation created a loop.
# My points list: 
# 0: (0,0)
# 1: (depth, 0)
# 2: (depth, riser)
# ...
# Last point: (0,0)
# So the last segment connects (something, total_rise) to (0, total_rise) then (0,0) to (0,0)? 
# My loop logic: 
# ... -> (x, y) -> (x, y+riser) -> (x+depth, y+riser)
# Final step: y += riser -> append (x, y) -> x -= depth*(n-1) -> append (x, y) -> y -= total -> append (x, y) -> append (0,0)
# This results in a closed loop.
# We need to constrain the first point to the origin.
# We need to constrain the first line to be horizontal.
# We need to constrain the last vertical line to be vertical.

# Let's identify the geometry objects
geom_objs = sketch.Geometry
# First line index 0
sketch.addConstraint(Sketcher.Constraint("Fixed", 0, 0, "XZ_Plane", 1, 0, 0, 0))
sketch.addConstraint(Sketcher.Constraint("Fixed", 0, 1, "XZ_Plane", 1, 0, depth_w, 0)) # This fixes the second point too, which is good for a defined step
# But wait, if we fix all points, it's not parametric anymore.
# We must use the parameters.
# Instead of fixing absolute coordinates, we fix relative to the parameters or use the "Horizontal/Vertical" constraints.

# Correct Parametric Approach:
# 1. Add lines.
# 2. Constrain Line 0 to be Horizontal.
# 3. Constrain Point 0 to be at Origin (Fixed).
# 4. Constrain Line Last-1 (the last vertical riser) to be Vertical.
# 5. Constrain Point Last to coincide with Point 0 (to close the loop).

# Let's rebuild the constraints properly.
# We need to reference the geometry objects by index.
# The lines are stored in sketch.Geometry.
# Line 0: (0,0) -> (depth, 0)
# Line Last-1: The segment before the final return to origin.
# Actually, let's just constrain the first point to the origin and the first line to be horizontal.
# And the last line to be vertical.
# And the last point to coincide with the first point.

# Get the number of lines
n_lines = len(sketch.Geometry)

# Constraint 1: First point at origin
sketch.addConstraint(Sketcher.Constraint("Fixed", 0, 0, "XZ_Plane", 1, 0, 0, 0))

# Constraint 2: First line horizontal
sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 0)) # Line 0, Point 0 to Point 1

# Constraint 3: Last line vertical (the one connecting top-right to top-left)
# The last line in my list connects (x, total_rise) to (0, total_rise). Wait, my loop logic:
# ... -> (x, y) [top right corner of the last tread] -> (x, y+riser) [top left corner?] NO.
# Let's re-trace the points:
# Start (0,0). 
# Step 1: (depth, 0) -> (depth, riser). (Tread, then Riser)
# Step 2: (2*depth, riser) -> (2*depth, 2*riser).
# ...
# Step N: ((N-1)*depth, (N-1)*riser) -> (N*depth, (N-1)*riser) -> (N*depth, N*riser).
# Then: (N*depth, N*riser) -> ((N-1)*depth, N*riser). (Top edge back left)
# Then: ((N-1)*depth, N*riser) -> (0, N*riser). (Top edge back to origin X)
# Then: (0, N*riser) -> (0, 0). (Left edge down)
# My code:
# 1. (0,0) -> (depth, 0) (Tread 1)
# Loop N-1 times:
#   (x, y) -> (x, y+riser) (Riser)
#   (x, y+riser) -> (x+depth, y+riser) (Tread)
# After loop: x = (N-1)*depth, y = (N-1)*riser.
# Add Riser: (N-1)*depth, (N-1)*riser -> (N-1)*depth, N*riser.
# Add Tread? No, the loop added treads. The last tread was added in the last iteration of the loop?
# Range(N-1): i=0 to N-2.
# i=0: (0,0)->(depth,0) [Tread]. (depth,0)->(depth, riser) [Riser]. (depth,riser)->(2*depth, riser) [Tread].
# ...
# Last iter i=N-2: ((N-2)*depth, (N-2)*riser) -> ... -> ( (N-1)*depth, (N-1)*riser ).
# So after loop: we are at ((N-1)*depth, (N-1)*riser).
# Then: y += riser -> (N-1)*depth, N*riser. (Riser up)
# Points: ..., ((N-1)*depth, N*riser).
# Then: x -= depth*(N-1). x = 0.
# Points: ..., (0, N*riser).
# Then: y -= N*riser. y = 0.
# Points: ..., (0, 0).
# So the lines are:
# 1. (0,0) -> (depth, 0) [Tread 1]
# 2. (depth, 0) -> (depth, riser) [Riser 1]
# 3. (depth, riser) -> (2*depth, riser) [Tread 2]
# ...
# Last Riser: ((N-1)*depth, (N-1)*riser) -> ((N-1)*depth, N*riser)
# Then Line: ((N-1)*depth, N*riser) -> (0, N*riser) [Top Edge]
# Then Line: (0, N*riser) -> (0, 0) [Left Edge]
# The constraint "Last line vertical" applies to the segment from (0, N*riser) to (0,0)? Or the one before?
# The segment (0, N*riser) -> (0,0) is the left vertical edge.
# The segment ((N-1)*depth, N*riser) -> (0, N*riser) is horizontal.
# So the vertical line is the LAST line in the list (index n_lines-1).
# Wait, the list ends with (0,0). The previous point is (0, N*riser).
# So the last line is (0, N*riser) -> (0,0). This is vertical.
# So constraint: Vertical on the last line.

if n_lines > 0:
    sketch.addConstraint(Sketcher.Constraint("Vertical", n_lines - 1, 0, 0))
    # Also constrain the last point to coincide with the first point to close the loop explicitly
    # Line n_lines-1 is from (0, N*riser) to (0,0).
    # Point (n_lines-1, 1) is (0,0). Point (0,0) is (0,0).
    # They are already coincident in my logic, but let's add a constraint to enforce it.
    sketch.addConstraint(Sketcher.Constraint("Coincident", n_lines - 1, 1, 0, 0))

# --- Step 2: Extrude the Profile ---
# Pad to the right (positive X direction)
# We need to extrude along the X axis.
# The sketch is on XZ plane. X is horizontal.
# We need a reference axis for the pad? Pad extrudes along the normal of the plane if no axis is specified?
# No, Pad extrudes along the Z axis of the sketch plane by default? 
# Actually, PartDesign::Pad extrudes along the normal of the sketch plane.
# Since our sketch is on XZ, the normal is Y.
# We want to extrude along X.
# So we must use a Revolution or a Pad with a specific axis?
# Wait, if the sketch is on XZ, the normal is Y. Extruding along normal gives a wall along Y.
# We want a block along X.
# So we should sketch on the XY plane (normal Z) and extrude along Z?
# Or sketch on XZ and use a "Pad" with a specific axis?
# Part
