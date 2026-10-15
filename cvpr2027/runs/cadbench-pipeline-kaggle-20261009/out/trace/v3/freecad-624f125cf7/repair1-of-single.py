import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure the script is self-contained and portable
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Parameters
P = {
    "lower_horizontal_width": 584.20,
    "clip_wall_thickness": 6.35,
    "upper_horizontal_width": 635.0,
    "outer_upper_vertical_edge_height": 190.50,
    "outer_v_apex_height": 45.99,
    "outer_slant_edge_vertical_height": 101.60,
    "outer_lower_vertical_edge_height": 25.4,
    "retention_slot_corner_radius": 0.0,
    "clip_length": 76.2
}

# --- Document Setup ---
doc = App.newDocument("Clip")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement() # Default is (0,0,0) with Identity rotation

# --- Parameters Object ---
# We create a VarSet to hold the parameters as editable properties
params = body.newObject("App::VarSet", "Parameters")
for name, value in P.items():
    params.addProperty("App::PropertyLength", name, "Parameters", name)
    setattr(params, name, value)

# --- Sketch 1: Outer Profile ---
# We define the profile in the XZ plane (Y=0). 
# The sketch will be placed on the XZ plane of the body.
# Coordinates: Sketch X -> Part X, Sketch Y -> Part Z.

sketch_outer = body.newObject("Sketcher::SketchObject", "OuterProfile")
sketch_outer.Placement = App.Placement()
sketch_outer.Support = "XZ_Plane"
sketch_outer.ConstrainToCurrentPlane = True
sketch_outer.MapMode = "FlatFace"

# Calculate key coordinates for the right half (X > 0)
# 1. Bottom Center: (0, 0)
# 2. Bottom Right: (L/2, 0)
# 3. Lower Vertical Top: (L/2, h_lower)
# 4. Slant Top X: L/2 + (Upper - Lower)/2
# 5. Slant Top Z: h_lower + h_slant
# 6. Top Vertical Top: h_lower + h_slant + h_upper
# 7. Top Center: (0, Top Z)
# 8. V Apex: (0, h_v_apex)
# 9. Close to Bottom Center: (0, 0)

L = P["lower_horizontal_width"]
h_lower = P["outer_lower_vertical_edge_height"]
h_slant = P["outer_slant_edge_vertical_height"]
h_upper = P["outer_upper_vertical_edge_height"]
h_top = h_lower + h_slant + h_upper
x_slant = L / 2 + (P["upper_horizontal_width"] - L) / 2
h_v_apex = P["outer_v_apex_height"]

# Add Segments for the Right Half (Counter-Clockwise loop starting from bottom center)
# 1. Bottom Bridge (Right)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(L/2, 0, 0)), False)
# 2. Lower Vertical
sketch_outer.addGeometry(Part.LineSegment(App.Vector(L/2, 0, 0), App.Vector(L/2, 0, h_lower)), False)
# 3. Slant Edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(L/2, 0, h_lower), App.Vector(x_slant, 0, h_lower + h_slant)), False)
# 4. Upper Vertical
sketch_outer.addGeometry(Part.LineSegment(App.Vector(x_slant, 0, h_lower + h_slant), App.Vector(x_slant, 0, h_top)), False)
# 5. Top Horizontal (Right to Center)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(x_slant, 0, h_top), App.Vector(0, 0, h_top)), False)
# 6. V Leg (Top Center to Apex)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(0, 0, h_top), App.Vector(0, 0, h_v_apex)), False)
# 7. Center Vertical (Apex to Bottom)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(0, 0, h_v_apex), App.Vector(0, 0, 0)), False)

# --- Sketch 2: Inner Profile (Offset) ---
# Create an offset sketch based on the outer profile.
# We use the Offset feature of Sketcher.
sketch_inner = body.newObject("Sketcher::SketchObject", "InnerProfile")
sketch_inner.Placement = App.Placement()
sketch_inner.Support = "XZ_Plane"
sketch_inner.ConstrainToCurrentPlane = True
sketch_inner.MapMode = "FlatFace"

# We need to copy the geometry from sketch_outer to sketch_inner and offset it.
# Since we cannot directly reference another sketch's geometry in a simple way without constraints,
# and the offset is uniform, we can use the "Offset" constraint type if we had points, 
# but here we have lines. 
# A robust way in script is to create the same lines but with reduced width.
# However, the prompt asks for "uniform inward offset".
# We can achieve this by creating a new sketch and using the "Offset" feature if available, 
# or manually calculating the offset lines.
# Given the complexity of manually offsetting arbitrary polygons in a script without a library,
# and the fact that Sketcher supports "Offset" constraints on lines if we had points,
# let's try a different approach: Use the `Part::OffsetShape` logic? No, must be Sketcher.
# Actually, we can create the inner sketch by offsetting the outer sketch's geometry using the `Sketcher::Offset` constraint 
# if we convert lines to points? No.
# 
# Alternative: Use the `Part::OffsetShape` to create the inner shape from the outer shape, 
# then create a sketch from that shape? 
# But the requirement is "editable PartDesign features".
# 
# Let's use the `Sketcher::Offset` constraint on the lines? 
# No, `Offset` constraint in Sketcher is for distance from a point or line.
# 
# Best approach for "Uniform Inward Offset" in a script:
# 1. Create the outer sketch (done).
# 2. Create a new sketch.
# 3. Add the same lines but with coordinates reduced by `clip_wall_thickness`.
# This is not a true "offset" feature (which handles corners automatically), but for a rectangular-ish shape 
# with 90 degree corners (mostly), it works. 
# However, the slant edge will also be offset.
# To do a true offset of a polygon with slanted edges in a script, we need to calculate the offset lines.
# 
# Let's calculate the offset lines for the right half.
# The offset distance is `clip_wall_thickness`.
# 
# Segment 1 (Bottom): (0,0) to (L/2, 0). Offset inward (Left): (-thickness, 0) to (L/2 - thickness, 0).
# Segment 2 (Lower Vert): (L/2, 0) to (L/2, h_lower). Offset inward (Left): (L/2 - thickness, 0) to (L/2 - thickness, h_lower).
# Segment 3 (Slant): From (L/2, h_lower) to (x_slant, h_lower+h_slant).
#   Vector V = (dx, dy) = (x_slant - L/2, h_slant).
#   Normal N (inward) = (-dy, dx) normalized? 
#   We want to move the line inward (towards X=0).
#   The line equation: (y - y1) = m * (x - x1).
#   Offset line: (y - y1) = m * (x - x1) + c.
#   Distance = c / sqrt(1+m^2).
#   Since we want inward (smaller X), we subtract the offset from the X coordinate along the normal.
#   Normal pointing inward (towards center): (-sin(theta), cos(theta))?
#   Let's use vector math.
#   V = (dx, dy). Length = L_v.
#   Unit Tangent T = (dx/L_v, dy/L_v).
#   Unit Normal N (inward) = (-dy/L_v, dx/L_v). (Check: dot(T, N) = 0. If dx>0, dy>0, N points left/up? 
#   Wait, if we go from bottom-right to top-right, dx>0, dy>0. 
#   Inward is towards X=0. So we need negative X component.
#   N = (-dy/L_v, dx/L_v). X component is negative. Correct.
#   Offset points = Original Points + thickness * N.
# 
# Segment 4 (Upper Vert): (x_slant, h_lower+h_slant) to (x_slant, h_top).
#   Offset inward (Left): (x_slant - thickness, ...)
# Segment 5 (Top Horiz): (x_slant, h_top) to (0, h_top).
#   Offset inward (Down): (..., h_top - thickness)
# Segment 6 (V Leg): (0, h_top) to (0, h_v_apex).
#   Offset inward (Right): (thickness, ...)
# Segment 7 (Center Vert): (0, h_v_apex) to (0, 0).
#   Offset inward (Right): (thickness, ...)

# Let's implement the offset calculation.
def offset_line(p1, p2, offset_dist, inward_normal):
    # inward_normal is a vector (nx, ny)
    # Returns p1_offset, p2_offset
    p1_off = App.Vector(p1.X + offset_dist * inward_normal.X, p1.Y + offset_dist * inward_normal.Y, p1.Z)
    p2_off = App.Vector(p2.X + offset_dist * inward_normal.X, p2.Y + offset_dist * inward_normal.Y, p2.Z)
    return p1_off, p2_off

# Calculate offsets for Right Half
thickness = P["clip_wall_thickness"]

# 1. Bottom: (0,0) -> (L/2, 0). Inward Normal: (-1, 0)
p1_1 = App.Vector(0, 0, 0)
p2_1 = App.Vector(L/2, 0, 0)
p1_1_off, p2_1_off = offset_line(p1_1, p2_1, thickness, App.Vector(-1, 0, 0))

# 2. Lower Vert: (L/2, 0) -> (L/2, h_lower). Inward Normal: (0, -1) (Wait, inward is Left, so (-1, 0)? No, vertical line, inward is Left (-1,0))
# Actually, for a vertical line at x=L/2, inward is -X direction.
# p1_2 = (L/2, 0), p2_2 = (L/2, h_lower).
# Normal: (-1, 0).
p1_2 = App.Vector(L/2, 0, 0)
p2_2 = App.Vector(L/2, 0, h_lower)
p1_2_off, p2_2_off = offset_line(p1_2, p2_2, thickness, App.Vector(-1, 0, 0))

# 3. Slant: (L/2, h_lower) -> (x_slant, h_lower+h_slant)
p1_3 = App.Vector(L/2, 0, h_lower)
p2_3 = App.Vector(x_slant, 0, h_lower + h_slant)
dx = x_slant - L/2
dy = h_slant
len_v = (dx*dx + dy*dy)**0.5
# Inward Normal: (-dy, dx) / len_v
n_x = -dy / len_v
n_y = dx / len_v
p1_3_off, p2_3_off = offset_line(p1_3, p2_3, thickness, App.Vector(n_x, n_y, 0))

# 4. Upper Vert: (x_slant, h_lower+h_slant) -> (x_slant, h_top)
# Inward Normal: (-1, 0)
p1_4 = App.Vector(x_slant, 0, h_lower + h_slant)
p2_4 = App.Vector(x_slant, 0, h_top)
p1_4_off, p2_4_off = offset_line(p1_4, p2_4, thickness, App.Vector(-1, 0, 0))

# 5. Top Horiz: (x_slant, h_top) -> (0, h_top)
# Inward Normal: (0, -1) (Down)
p1_5 = App.Vector(x_slant, 0, h_top)
p2_5 = App.Vector(0, 0, h_top)
p1_5_off, p2_5_off = offset_line(p1_5, p2_5, thickness, App.Vector(0, -1, 0))

# 6. V Leg: (0, h_top) -> (0, h_v_apex)
# Inward Normal: (1, 0) (Right)
p1_6 = App.Vector(0, 0, h_top)
p2_6 = App.Vector(0, 0, h_v_apex)
p1_6_off, p2_6_off = offset_line(p1_6, p2_6, thickness, App.Vector(1, 0, 0))

# 7. Center Vert: (0, h_v_apex) -> (0, 0)
# Inward Normal: (1, 0) (Right)
p1_7 = App.Vector(0, 0, h_v_apex)
p2_7 = App.Vector(0, 0, 0)
p1_7_off, p2_7_off = offset_line(p1_7, p2_7, thickness, App.Vector(1, 0, 0))

# Add Inner Segments
sketch_inner.addGeometry(Part.LineSegment(p1_1_off, p2_1_off), False)
sketch_inner.addGeometry(Part.LineSegment(p1_2_off, p2_2_off), False)
sketch_inner.addGeometry(Part.LineSegment(p1_3_off, p2_3_off), False)
sketch_inner.addGeometry(Part.LineSegment(p1_4_off, p2_4_off), False)
sketch_inner.addGeometry(Part.LineSegment(p1_5_off, p2_5_off), False)
sketch_inner.addGeometry(Part.LineSegment(p1_6_off, p2_6_off), False)
sketch_inner.addGeometry(Part.LineSegment(p1_7_off, p2_7_off), False)

# --- Pad Feature (Extrude) ---
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch_outer
pad.Length = P["clip_length"]
pad.Type = "Solid"
pad.Reversed = False

# --- Pocket Feature (Slot) ---
# The slot is a rectangular hole through the center.
# It spans lower_horizontal_width, has width clip_wall_thickness, square corners.
# We need to create a sketch for the slot.
sketch_slot = body.newObject("Sketcher::SketchObject", "SlotProfile")
sketch_slot.Placement = App.Placement()
sketch_slot.Support = "XZ_Plane"
sketch_slot.ConstrainToCurrentPlane = True
sketch_slot.MapMode = "FlatFace"

# Slot Geometry:
# Centered at X=0.
# Width = P["lower_horizontal_width"]
# Height (in Z) = P["clip_wall_thickness"]
# Position: Z = P["outer_lower_vertical_edge_height"] / 2 - P["clip_wall_thickness"] / 2
# Wait, "spans lower_horizontal_width across the lower bridge".
# The lower bridge is from Z=0 to Z=h_lower.
# The slot is centered on the bridge? Or just spans the width?
# "centered rectangular retention slot spans lower_horizontal_width across the lower bridge"
# This implies the slot width is lower_horizontal_width.
# And it is centered on the bridge (X-wise).
# What about Z? "across the lower bridge" usually means it goes through the bridge.
# Does it go through the whole bridge height? Or is it a specific height?
# "has width clip_wall_thickness". This is the thickness of the slot (Z-height).
# "unrounded square corners".
# Let's assume it is centered vertically within the lower bridge.
# Z_start = h_lower / 2 - thickness / 2
# Z_end = h_lower / 2 + thickness / 2

z_slot_center = P["outer_lower_vertical_edge_height"] / 2
z_slot_start = z_slot_center - P["clip_wall_thickness"] / 2
z_slot_end = z_slot_center + P["clip_wall_thickness"] / 2

# Slot Segments (Right Half)
# 1. Bottom: (L/2, z_start) to (L/2, z_end) -> No, slot is a hole.
# We need to define the boundary of the hole.
# Right side: (L/2, z_start) to (L/2, z_end)
# Top: (L/2, z_end) to (-L/2, z_end)
# Left: (-L/2, z_end) to (-L/2, z_start)
# Bottom: (-L/2, z_start) to (L/2, z_start)

# Add Right Half
sketch_slot.addGeometry(Part.LineSegment(App.Vector(P["lower_horizontal_width"]/2, 0, z_slot_start), App.Vector(P["lower_horizontal_width"]/2, 0, z_slot_end)), False)
sketch_slot.addGeometry(Part.LineSegment(App.Vector(P["lower_horizontal_width"]/2, 0, z_slot_end), App.Vector(-P["lower_horizontal_width"]/2, 0, z_slot_end)), False)
sketch_slot.addGeometry(Part.LineSegment(App.Vector(-P["lower_horizontal_width"]/2, 0, z_slot_end), App.Vector(-P["lower_horizontal_width"]/2, 0, z_slot_start)), False)
sketch_slot.addGeometry(Part.LineSegment(App.Vector(-P["lower_horizontal_width"]/2, 0, z_slot_start), App.Vector(P["lower_horizontal_width"]/2, 0, z_slot_start)), False)

pocket = body.newObject("PartDesign::Pocket", "SlotPocket")
pocket.Profile = sketch_slot
pocket.Type = "ThroughAll"
pocket.Clean = True

# --- Fillet Feature ---
# "unrounded square corners" -> Radius = 0.0.
# So no fillet needed.
# But let's add a dummy fillet feature with radius 0 to satisfy "Fillet" usage if required? 
# The prompt says "unrounded square corners governed by retention_slot_corner_radius".
# Since radius is 0, we don't need a fillet feature.

# --- Recompute and Save ---
doc.recompute()

# Save to the specific path
doc.saveAs(str(output_path))
