import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Staircase")

# --- 1. Parameters ---
# We create a VarSet to hold editable parameters as requested by the prompt logic
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyInteger", "number_of_steps", "Dimensions", "Number of steps")
params.number_of_steps = 5

params.addProperty("App::PropertyLength", "step_riser", "Dimensions", "Height of each step")
params.step_riser = 170.0

params.addProperty("App::PropertyLength", "step_depth", "Dimensions", "Depth of each step")
params.step_depth = 300.0

params.addProperty("App::PropertyLength", "step_width", "Dimensions", "Width of the staircase")
params.step_width = 1200.0

params.addProperty("App::PropertyLength", "step_length", "Dimensions", "Total length of the staircase (derived)")
# Note: In the prompt, total_run = number_of_steps * step_depth. 
# We define this as a parameter for clarity, though it can be calculated.
params.step_length = 1500.0

# --- 2. Setup Body ---
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))
# Body placement ensures the sketch is centered or at origin. 
# Since the prompt asks for profile_origin (0,0), we keep body at 0,0,0.

# --- 3. Create Sketch for Stair Profile ---
# The sketch will be on the XY plane (X=Run, Y=Width in 3D space? No, Prompt says:
# tread_direction = +X, rise_direction = +Z.
# So the profile plane must be the XZ plane.
# FreeCAD PartDesign Body attaches sketches to the Body's Placement.
# The Body is at 0,0,0. 
# We need the sketch plane to be XZ.
# We will attach to the "XZ_Plane" which exists in the document root or Body.
# In modern FreeCAD, we usually attach to the "XY_Plane" of the Body and rotate, 
# OR attach to the global "XZ_Plane" if available.
# However, the most robust way for a specific orientation is to create a sketch 
# attached to the Body's XY plane and define the geometry such that X is run and Z is rise.
# Wait, Body.Placement affects the sketch position.
# Let's attach to the global "XZ_Plane" to ensure X is Run and Z is Rise naturally.

sketch = body.newObject("Sketcher::SketchObject", "StairProfile")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# We attach to the global XZ plane. If the document doesn't have XZ_Plane yet, 
# we rely on the Body's local planes or standard document planes.
# Standard practice in PartDesign: attach to a face/plane.
# Let's attach to the Body's XY plane and manually orient the lines, 
# OR attach to a plane created in the body.
# Actually, the simplest robust way for "XZ Plane" orientation in a new doc:
# Attach to the "XY_Plane" of the Body, but we need X to be horizontal and Z vertical.
# The Body's XY plane has X horizontal and Y vertical (in the sketch context).
# We need Z to be vertical.
# Therefore, we attach to the XZ plane.
# In FreeCAD 1.1, if we attach to the Body, we get the Body's local planes.
# To get XZ, we can attach to the global XZ plane if it exists, or create one.
# Let's create a Plane in the Body to ensure we have the exact orientation we want.
# Plane: X axis, Z axis, Y normal.

# Actually, let's use the global planes if they exist, otherwise create a sketch 
# on the Body's XY plane and use coordinates (x, z) where z is the Y of the sketch?
# No, that confuses the user.
# Let's create a sketch on the Body's XY plane. 
# In this sketch: X axis = Step Depth (Run), Y axis = Step Rise (Height).
# Then we extrude along Y? No, prompt says extrusion_direction = +Y (step_width).
# So the Profile plane must be XZ.
# Extrusion is along Y.
# So the Profile sketch needs to lie in the XZ plane.
# We will attach the sketch to the global "XZ_Plane". 
# If it doesn't exist, we can create it or just use the Body's placement to orient it.
# Let's try attaching to the "XZ_Plane" object. If it fails, we fall back to creating one.
# Actually, for a standalone script, creating a sketch on the Body's XY plane 
# and interpreting the sketch Y as Z is error-prone.
# Better approach: Create a sketch on the Body, attach to the Body's XY plane.
# Then define geometry using X (Run) and the Sketch's Y (which we will treat as Rise).
# Then we Extrude along the Body's Z axis? 
# Prompt: "extrusion_direction = +Y".
# So the profile must be in XZ.
# Let's create a sketch on the Body, attach to the Body's XY plane.
# We will draw the profile using X (Run) and the Sketch's Y coordinate as the Height.
# Then we will extrude the sketch along the Body's Z axis? 
# No, the prompt says extrusion_direction = +Y.
# This implies the "Width" of the stair is along Y.
# So the Profile is in XZ.
# We must attach the sketch to the XZ plane.
# To ensure XZ plane exists, we can create a "PartDesign::Plane" or use the global one.
# Let's create a Plane object in the Body to be safe and explicit.

# Create a Plane for the XZ orientation (Normal Y)
plane = body.newObject("PartDesign::Plane", "XZ_Plane")
plane.Placement = App.Placement(App.Vector(0, 0, 0))

# Now create the sketch attached to this plane
sketch = body.newObject("Sketcher::SketchObject", "StairProfile")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.AttachmentSupport = (plane, [""])
sketch.MapMode = "FlatFace"

# Generate Geometry for the Stair Profile
# Origin (0,0). 
# 5 steps.
# Riser (Height) = step_riser.
# Tread (Run) = step_depth.
# We start at (0,0), go up total_rise, then go right total_run?
# Or start at bottom left, go right, then up?
# Standard stair profile: Start (0,0) -> (TotalRun, 0) -> (TotalRun, TotalRise) -> (0, TotalRise) -> (0,0)?
# No, that's a rectangle. A staircase is a step function.
# We need a polyline that goes Up, Right, Up, Right...
# Let's trace the outer boundary of the 5 steps.
# Start at (0,0).
# Go Right (Tread) -> (step_depth, 0)
# Go Up (Riser) -> (step_depth, step_riser)
# Go Right (Tread) -> (2*step_depth, step_riser)
# ...
# End at (TotalRun, TotalRise).
# Then close the shape? 
# The extrusion will cut the solid. We need a closed profile or a closed loop?
# Pad requires a closed profile.
# So we need to close the loop back to (0,0).
# From (TotalRun, TotalRise), go Left to (0, TotalRise), then Down to (0,0).
# This creates a solid block of stairs.

# We will use App::Polyline or add segments.
# Since FreeCAD 1.1 Scripting API for Sketcher is complex with direct segment addition,
# we will construct the polyline points and add them as a Line (Polyline) geometry.

num_steps = params.number_of_steps
riser = params.step_riser
depth = params.step_depth

points = []
current_x = 0
current_y = 0 # This Y in sketch is Z in 3D (Rise)

# 1. Start at origin
points.append(App.Vector(current_x, current_y, 0))

# 2. Traverse the steps
for i in range(num_steps):
    # Tread
    current_x += depth
    points.append(App.Vector(current_x, current_y, 0))
    
    # Riser
    current_y += riser
    points.append(App.Vector(current_x, current_y, 0))

# 3. Close the shape
# Go back horizontally to x=0
current_x = 0
points.append(App.Vector(current_x, current_y, 0))

# Go down vertically to origin
current_y = 0
points.append(App.Vector(current_x, current_y, 0))

# Add the polyline
# Note: Sketcher::SketchObject addGeometry for Polyline
# We need to construct a Part::Polyline or similar? 
# Actually, Sketcher::SketchObject supports 'Part::Polyline' as geometry.
polyline = Part.makePolyline(points)
sketch.addGeometry(polyline, False)

# Add constraints to ensure it's clean? 
# The coordinates are exact, so constraints are implicit in the geometry creation.
# But we should ensure the shape is valid.
# Sketcher::SketchObject usually needs constraints for solver stability, 
# but for a simple polyline defined by math, it might skip.
# Let's add a constraint between the first and last point to ensure closure visually?
# Actually, makePolyline creates a closed shape if we repeat the start point, which we did.
# The sketch might complain if not constrained.
# Let's add a coincident constraint between the last and first segment endpoints?
# Or just rely on the geometry.
# To be safe, let's add a constraint between the first and last element of the sketch?
# Sketcher indices start at 1.
# Let's try to add a coincident constraint between the end of the last line and start of first.
# However, the polyline is one object. 
# Let's just add the polyline. If the sketch fails to compute, it's because of missing constraints.
# We'll add a constraint between the start and end of the polyline.
# We need to identify the start and end of the polyline in the sketch.
# The polyline is at index 1 (1-based).
# Sketcher.Constraint("Coincident", 1, 0, 1, 0) ? 
# This is tricky without a GUI.
# Let's assume the geometry is sufficient for the Pad to work, or add a simple circle constraint?
# No, let's add a constraint between the first and last point of the polyline.
# The polyline is a single geometry object.
# We can't easily constrain points of a polyline object in script without parsing.
# Alternative: Add line segments individually and constrain them.
# That's tedious.
# Let's try the Polyline. If it fails, we might need to break it.
# But usually, making a shape and adding it is enough for PartDesign if it's closed.
# Let's add a "Horizontal" and "Vertical" constraint for the first step to anchor it?
# Constraint: X is aligned with X axis, Y is aligned with Z axis?
# The sketch is on XZ plane.
# X axis of sketch = X axis of plane.
# Y axis of sketch = Z axis of plane.
# So we can constrain the first segment to be horizontal and the second vertical.

# Let's add the segments as separate lines to make constraints easier and robust.
# This ensures the "Editable" requirement is met with clear constraints.

sketch.clearGeometry() # Clear the polyline we just made
sketch.clearConstraints()

# Define segments
segments = []
# Segment 1: Start to First Corner (Tread)
s1_start = App.Vector(0, 0, 0)
s1_end = App.Vector(depth, 0, 0)
segments.append((s1_start, s1_end))

# Segment 2: First Corner to First Riser Top
s2_start = s1_end
s2_end = App.Vector(depth, riser, 0)
segments.append((s2_start, s2_end))

# ... Loop for steps
for i in range(1, num_steps):
    # Tread
    s_start = App.Vector((i)*depth, (i-1)*riser, 0)
    s_end = App.Vector((i+1)*depth, (i-1)*riser, 0)
    segments.append((s_start, s_end))
    
    # Riser
    s_start = s_end
    s_end = App.Vector((i+1)*depth, i*riser, 0)
    segments.append((s_start, s_end))

# Closing segments
# Last Tread end to Top Left
# Last point is (num_steps*depth, num_steps*riser)
# We need to go to (0, num_steps*riser)
s_start = App.Vector(num_steps*depth, num_steps*riser, 0)
s_end = App.Vector(0, num_steps*riser, 0)
segments.append((s_start, s_end))

# Top Left to Origin
s_start = App.Vector(0, num_steps*riser, 0)
s_end = App.Vector(0, 0, 0)
segments.append((s_start, s_end))

# Add lines and constraints
for i, (p1, p2) in enumerate(segments):
    line = Part.LineSegment(p1, p2)
    sketch.addGeometry(line, False)

# Add Constraints
# We need to constrain the geometry to fix the degrees of freedom.
# 1. Start point at Origin (0,0)
# 2. Segment 1 Horizontal (Y=0)
# 3. Segment 2 Vertical (X=const)
# 4. All Treads Horizontal
# 5. All Risers Vertical

# Helper to get constraint lines in sketch
# Sketcher.Constraint("Horizontal", line_idx, 1) ? No, that's for lines.
# We use "Point" and "Line" constraints.

# Point 1 (Start) at Origin
# Index 1 in sketch is the first line. Start point is at index 1, start=0?
# Format: Constraint("Type", LineIndex, PointIndex, LineIndex2, PointIndex2)
# For point constraint: Constraint("Point", LineIndex, PointIndex)
# PointIndex: 0=Start, 1=End.

# Line 1: Start (0,0) to (depth, 0)
# Line 2: (depth, 0) to (depth, riser)
# Line 3: (depth, riser) to (2*depth, riser)
# ...

# Constraint Set:
# 1. Line 1 Start at Origin (0,0) -> X=0, Y=0
# 2. Line 1 End at (depth, 0) -> Y=0 (Horizontal constraint on line 1)
# 3. Line 1 End coincident with Line 2 Start
# 4. Line 2 Vertical
# ...

# Let's build the constraint list manually
constraints = []

# Line 1 (Tread 1)
# Start at 0,0
constraints.append(Sketcher.Constraint("Point", 1, 0, "XY_Plane")) # X=0, Y=0? No, "XY_Plane" is a plane.
# We need "X" and "Y" constraints or "Point" with coordinates?
# In script, we usually use "Point" with the plane object?
# Actually, "XY_Plane" is not a variable.
# We can use "Point" with "XY_Plane" if we attach to it?
# Let's use explicit coordinates if possible, or constraints to axes.
# Sketcher.Constraint("X", line, point, value) -> No.
# Standard way:
# Constraint("Point", line, point) -> This snaps to a plane?
# We need to constrain to the origin.
# Let's use "Point" with "XY_Plane" and "X_Axis"?
# Actually, the easiest is to constrain the start point to the "XY_Plane" (which is the sketch plane) and set X=0, Y=0?
# No.
# Let's use: Constraint("Point", 1, 0) -> This constrains to the "XY_Plane" of the sketch? No.
# The documentation says: Constraint("Point", line_index, point_index)
# It constrains the point to the "XY_Plane" of the sketch? 
# Wait, the sketch is attached to the XZ_Plane.
# So "Point" on the sketch constrains to the XZ_Plane (Z=0).
# That's not what we want. We want (0,0).
# We need to constrain the X coordinate and Y coordinate separately.
# Constraint("X", line, point, value) -> value is a number?
# Yes, "X" constraint sets the X coordinate of the point.
# But the value must be a string expression or number.
# Let's try: Constraint("X", 1, 0, "0")
# And Constraint("Y", 1, 0, "0")

constraints.append(Sketcher.Constraint("X", 1, 0, "0"))
constraints.append(Sketcher.Constraint("Y", 1, 0, "0"))

# Line 1 is horizontal (Y=0 for all points)
constraints.append(Sketcher.Constraint("Y", 1, 1, "0"))

# Line 1 End coincident with Line 2 Start
constraints
