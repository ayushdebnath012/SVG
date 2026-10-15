import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize Document
doc = App.newDocument("RetainingClip")
doc.Label = "RetainingClip"

# --- Parameters ---
# Define parameters in a VarSet for easy editing and expression driving
params = doc.addObject("App::VarSet", "ClipParameters")
params.addProperty("App::PropertyLength", "lower_horizontal_width", "Dimensions", "Width of lower bridge")
params.addProperty("App::PropertyLength", "clip_wall_thickness", "Dimensions", "Uniform wall thickness")
params.addProperty("App::PropertyLength", "upper_horizontal_width", "Dimensions", "Distance between outer upper edges")
params.addProperty("App::PropertyLength", "outer_upper_vertical_edge_height", "Dimensions", "Height of outer upper vertical edge")
params.addProperty("App::PropertyLength", "outer_v_apex_height", "Dimensions", "Height where V-legs meet centerline")
params.addProperty("App::PropertyLength", "outer_slant_edge_vertical_height", "Dimensions", "Vertical rise of outer slanted edge")
params.addProperty("App::PropertyLength", "outer_lower_vertical_edge_height", "Dimensions", "Height of outer lower vertical edge")
params.addProperty("App::PropertyLength", "retention_slot_corner_radius", "Dimensions", "Corner radius of retention slot")
params.addProperty("App::PropertyLength", "clip_length", "Dimensions", "Physical length of the clip")

# Assign values
params.lower_horizontal_width = 584.20
params.clip_wall_thickness = 6.35
params.upper_horizontal_width = 635.0
params.outer_upper_vertical_edge_height = 190.50
params.outer_v_apex_height = 45.99
params.outer_slant_edge_vertical_height = 101.60
params.outer_lower_vertical_edge_height = 25.4
params.retention_slot_corner_radius = 0.0
params.clip_length = 76.2

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "ClipBody")
body.Label = "ClipBody"

# Helper to create sketches on XY plane
def create_sketch(name, offset=0):
    """Creates a Sketcher::SketchObject on the XY plane at Z = offset."""
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    sketch.Support = (doc.getObject("XY_Plane"), [])
    sketch.MapMode = "FlatFace"
    return sketch

# Create Base Sketch (Outer Profile)
# We will construct the profile on the XY plane. 
# Geometry will be generated based on the parameters.
# Coordinate system: Origin at bottom center of the lower bridge.
# Y is Up (Z in physical model), X is Width.

sketch_outer = create_sketch("OuterSketch")

# Calculate intermediate dimensions for geometry construction
# Left side width is half of lower_horizontal_width
half_lower_w = params.lower_horizontal_width / 2.0
# Half width of the upper section relative to center (based on upper_horizontal_width)
half_upper_w = params.upper_horizontal_width / 2.0
# Horizontal run of the slanted edge
slant_run = half_upper_w - half_lower_w
# Half thickness for inner offset logic later

# 1. Lower Bridge Horizontal Line (Bottom)
# From -half_lower_w to +half_lower_w at Y=0
p1 = App.Vector(-half_lower_w, 0, 0)
p2 = App.Vector(half_lower_w, 0, 0)
sketch_outer.addGeometry(Part.LineSegment(p1, p2), False)

# 2. Lower Vertical Edge (Left Side)
# From (-half_lower_w, 0) to (-half_lower_w, outer_lower_vertical_edge_height)
p3 = App.Vector(-half_lower_w, params.outer_lower_vertical_edge_height, 0)
sketch_outer.addGeometry(Part.LineSegment(p2, p3), False)

# 3. Outer Slanted Edge (Left Side)
# From (-half_lower_w, outer_lower_vertical_edge_height) to (-half_upper_w, outer_lower + outer_slant)
p4_y = params.outer_lower_vertical_edge_height + params.outer_slant_edge_vertical_height
p4 = App.Vector(-half_upper_w, p4_y, 0)
sketch_outer.addGeometry(Part.LineSegment(p3, p4), False)

# 4. Outer Upper Vertical Edge (Left Side)
# From (-half_upper_w, p4_y) to (-half_upper_w, p4_y + outer_upper)
p5_y = p4_y + params.outer_upper_vertical_edge_height
p5 = App.Vector(-half_upper_w, p5_y, 0)
sketch_outer.addGeometry(Part.LineSegment(p4, p5), False)

# 5. Upper Horizontal Edge (Left Side)
# From (-half_upper_w, p5_y) to (+half_upper_w, p5_y)
p6 = App.Vector(half_upper_w, p5_y, 0)
sketch_outer.addGeometry(Part.LineSegment(p5, p6), False)

# 6. Outer Slanted Edge (Right Side - Symmetric)
# From (+half_upper_w, p5_y) to (+half_upper_w, p4_y) -- Wait, the description says:
# "An outer upper vertical edge then rises... From their upper endpoints, two equal diagonal legs descend inward"
# So the top edge is horizontal. Then diagonals go DOWN INWARD.

# Let's re-verify the right side path based on symmetry and description.
# Right side outer path:
# Bottom: (-half_lower_w, 0) -> (half_lower_w, 0) [Shared]
# Left Side: (half_lower_w, 0) -> (half_lower_w, outer_lower) -> (half_upper_w, outer_lower + outer_slant) -> (half_upper_w, top) -> (inner_start, top) -> (inner_apex, 0)
# Right Side: (half_lower_w, 0) -> (half_lower_w, outer_lower) -> (half_upper_w, outer_lower + outer_slant) -> (half_upper_w, top) -> (inner_start, top) -> (inner_apex, 0)

# Let's refine the points for the full loop to ensure closure and symmetry.
# We already have Left Bottom -> Left Vertical -> Left Slant -> Left Upper Vert -> Top Horizontal (Left to Right).
# Now we need the Right side return.
# From p6 (Right Top Outer) to Right Top Inner.
# The "upper horizontal width" is the distance between the two outer upper edges.
# So the top horizontal segment is already drawn from Left Outer to Right Outer.
# Now we need to go from Right Outer (p6) to Right Inner Start.
# The description says: "From their upper endpoints, two equal diagonal legs descend inward and meet on the profile centerline at outer_v_apex_height".
# "Their upper endpoints" refers to the upper endpoints of the outer upper vertical edges.
# So we have a top horizontal segment. From its ends, we draw diagonals inward to meet at Y = outer_v_apex_height.

# Let's recalculate the geometry coordinates precisely.
# Origin: Bottom Center of Lower Bridge.
# Left Outer Bottom: (-half_lower_w, 0)
# Left Outer Top: (-half_upper_w, outer_lower + outer_slant) -> Wait, the vertical rise is separate.
# Path:
# 1. Bottom: (-half_lower_w, 0) to (half_lower_w, 0)
# 2. Left Vert Up: (-half_lower_w, 0) to (-half_lower_w, outer_lower)
# 3. Left Slant Up-Right: (-half_lower_w, outer_lower) to (-half_upper_w, outer_lower + outer_slant)
# 4. Left Vert Up: (-half_upper_w, outer_lower + outer_slant) to (-half_upper_w, outer_lower + outer_slant + outer_upper)
# 5. Top Horiz Right: (-half_upper_w, top_y) to (half_upper_w, top_y)
# 6. Right Vert Down: (half_upper_w, top_y) to (half_upper_w, outer_lower + outer_slant + outer_upper)
# 7. Right Slant Down-Left: (half_upper_w, outer_lower + outer_slant + outer_upper) to (half_upper_w, outer_lower + outer_slant) -- No, slants are diagonal.
#    The slant connects the top of the lower vert to the top of the upper vert.
#    Left Slant connects (-half_lower_w, outer_lower) to (-half_upper_w, outer_lower+outer_slant).
#    Right Slant connects (half_upper_w, outer_lower+outer_slant) to (half_upper_w, outer_lower).
# 8. Right Vert Down: (half_upper_w, outer_lower) to (half_upper_w, 0) -- No, that's not right.
#    The shape is Z-like.
#    Left side: Bottom Horiz -> Vert Up -> Slant Up-Right -> Vert Up -> Top Horiz.
#    Right side: Top Horiz -> Vert Down -> Slant Down-Left -> Vert Down -> Bottom Horiz.

# Let's re-read carefully: "An outer lower vertical edge rises... joins an outward-rising slanted edge... An outer upper vertical edge then rises... From their upper endpoints, two equal diagonal legs descend inward and meet on the profile centerline at outer_v_apex_height".

# Revised Path Points:
# A: (-half_lower_w, 0)
# B: (half_lower_w, 0)
# C: (half_lower_w, outer_lower)
# D: (half_upper_w, outer_lower + outer_slant)
# E: (half_upper_w, outer_lower + outer_slant + outer_upper)
# F: (-half_upper_w, outer_lower + outer_slant + outer_upper)
# G: (-half_upper_w, outer_lower + outer_slant)
# H: (-half_lower_w, outer_lower)
# Loop: A->B->C->D->E->F->G->H->A

# Wait, the slant is "outward-rising".
# If we start at bottom center and go out:
# Bottom: (-half_lower_w, 0) to (half_lower_w, 0)
# Left Vert Up: (-half_lower_w, 0) to (-half_lower_w, outer_lower)
# Left Slant: (-half_lower_w, outer_lower) to (-half_upper_w, outer_lower + outer_slant) -> This is UP and LEFT (outward).
# Left Vert Up: (-half_upper_w, ...) to (-half_upper_w, top_y)
# Top Horiz: Left to Right.
# Right Vert Down: (half_upper_w, top_y) to (half_upper_w, outer_lower + outer_slant)
# Right Slant: (half_upper_w, outer_lower + outer_slant) to (half_upper_w, outer_lower) -> This is DOWN and RIGHT? 
#    If the slant is "outward-rising", then on the right side, going from bottom to top, we go Right and Up.
#    So: Bottom Right -> Vert Up -> Slant (Up/Right) -> Vert Up -> Top Right.
#    This creates a shape that widens as it goes up.
#    Then the top horizontal connects Left Top and Right Top.
#    Then the "diagonal legs descend inward" from the Top Left and Top Right to meet at the center line.

# Let's check the X-coordinates.
# Lower width = 584.2. Half = 292.1.
# Upper width = 635.0. Half = 317.5.
# So the top is wider than the bottom. The slant must go OUTWARD (away from center).
# Left Side: x goes from -292.1 to -317.5 (more negative).
# Right Side: x goes from 292.1 to 317.5 (more positive).
# This matches "outward-rising".

# So the profile path is:
# 1. Bottom: (-292.1, 0) to (292.1, 0)
# 2. Left Vert Up: (-292.1, 0) to (-292.1, 25.4)
# 3. Left Slant: (-292.1, 25.4) to (-317.5, 25.4 + 101.6) = (-317.5, 127.0)
# 4. Left Vert Up: (-317.5, 127.0) to (-317.5, 127.0 + 190.5) = (-317.5, 317.5)
# 5. Top Horiz: (-317.5, 317.5) to (317.5, 317.5)
# 6. Right Vert Down: (317.5, 317.5) to (317.5, 127.0)
# 7. Right Slant: (317.5, 127.0) to (292.1, 25.4) -> Wait, if it's symmetric, the right slant should go from Top-Right to Bottom-Right?
#    No, the path is a single loop.
#    If we trace the perimeter:
#    Start Bottom-Left -> Bottom-Right -> Right-Vert-Up -> Right-Slant-Up -> Right-Vert-Up -> Top-Right -> Top-Left -> Left-Vert-Down -> Left-Slant-Down -> Left-Vert-Down -> Bottom-Left.
#    But the description says "outward-rising slanted edge". This implies the side wall angles out.
#    So Right-Vert-Up goes to x=292.1. Slant goes to x=317.5.
#    So the path on the right side (going up) is: (292.1, 0) -> (292.1, 25.4) -> (317.5, 127.0) -> (317.5, 317.5).
#    Then Top Horiz goes from (317.5, 317.5) to (-317.5, 317.5).
#    Then Left side goes down: (-317.5, 317.5) -> (-317.5, 127.0) -> (-292.1, 25.4) -> (-292.1, 0).

# Okay, let's build the points for the sketch.
# Center X = 0.
# Left Slant Start: x = -half_lower_w, y = outer_lower
# Left Slant End: x = -half_upper_w, y = outer_lower + outer_slant
# Right Slant Start: x = half_upper_w, y = outer_lower + outer_slant
# Right Slant End: x = half_lower_w, y = outer_lower
# Top Y = outer_lower + outer_slant + outer_upper

# Let's define the vertices for the sketch loop.
v1 = App.Vector(-half_lower_w, 0, 0)       # Bottom Left
v2 = App.Vector(half_lower_w, 0, 0)        # Bottom Right
v3 = App.Vector(half_lower_w, params.outer_lower_vertical_edge_height, 0) # Right Vert Up
v4 = App.Vector(half_upper_w, params.outer_lower_vertical_edge_height + params.outer_slant_edge_vertical_height, 0) # Right Slant Up
v5 = App.Vector(half_upper_w, params.outer_lower_vertical_edge_height + params.outer_slant_edge_vertical_height + params.outer_upper_vertical_edge_height, 0) # Right Top
v6 = App.Vector(-half_upper_w, params.outer_lower_vertical_edge_height + params.outer_slant_edge_vertical_height + params.outer_upper_vertical_edge_height, 0) # Left Top
v7 = App.Vector(-half_upper_w, params.outer_lower_vertical_edge_height + params.outer_slant_edge_vertical_height, 0) # Left Slant Down (going down the loop)
v8 = App.Vector(-half_lower_w, params.outer_lower_vertical_edge_height, 0) # Left Vert Down (going down the loop)

# Add geometries
sketch_outer.addGeometry(Part.LineSegment(v1, v2), False) # Bottom
sketch_outer.addGeometry(Part.LineSegment(v2, v3), False) # Right Lower Vert
sketch_outer.addGeometry(Part.LineSegment(v3, v4), False) # Right Slant
sketch_outer.addGeometry(Part.LineSegment(v4, v5), False) # Right Upper Vert
sketch_outer.addGeometry(Part.LineSegment(v5, v6), False) # Top
sketch_outer.addGeometry(Part.LineSegment(v6, v7), False) # Left Upper Vert
sketch_outer.addGeometry(Part.LineSegment(v7, v8), False) # Left Slant
sketch_outer.addGeometry(Part.LineSegment(v8, v1), False) # Left Lower Vert

# --- Inner Profile Sketch ---
# "The inner boundary is the uniform inward offset of the outer boundary"
# Since the outer profile has straight lines and corners, we can create a sketch and use the Offset tool.
# Or we can manually construct the inner points by subtracting clip_wall_thickness from the width dimensions.
# However, using the Offset tool in Sketcher is the most robust way to ensure "uniform inward offset" and "closed corners".
# Note: Sketcher's Offset tool usually offsets in the normal direction. Since our sketch is on XY, normal is Z.
# We want an offset INWARD in the 2D plane (X-Y plane).
# Sketcher's "Offset" constraint or tool works on the geometry itself.
# Let's use the "Offset" constraint feature of the sketch or simply add the offset geometry.
# Actually, the easiest parametric way in FreeCAD PartDesign/Sketcher is to use the 'Offset' tool if available, 
# but the standard way for "inner boundary" is often to
