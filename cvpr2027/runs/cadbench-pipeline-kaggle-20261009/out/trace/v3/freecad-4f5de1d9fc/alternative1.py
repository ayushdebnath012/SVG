import FreeCAD as App
import Part
import PartDesign
from pathlib import Path
import Sketcher
import math

# Initialize Document
doc = App.newDocument("L_Bracket")

# Create a Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObjectGroup", "Group")
doc.setActiveObject("Body")

# Define Named Parameters (Editable)
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_length", "Dimensions", "Total Length")
params.l_triangle_bracket_plate_length = 34.5
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_height", "Dimensions", "Total Height")
params.l_triangle_bracket_plate_height = 34.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_depth", "Dimensions", "Depth")
params.l_triangle_bracket_plate_depth = 29.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_flange_thickness", "Dimensions", "Flange Thickness")
params.l_triangle_bracket_plate_flange_thickness = 5.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_vertical_inner_straight_length", "Dimensions", "Vertical Inner Straight")
params.l_triangle_bracket_plate_vertical_inner_straight_length = 5.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_horizontal_inner_straight_length", "Dimensions", "Horizontal Inner Straight")
params.l_triangle_bracket_plate_horizontal_inner_straight_length = 5.0
params.addProperty("App::PropertyLength", "bottom_hollow_recess_length", "Dimensions", "Recess Length")
params.bottom_hollow_recess_length = 30.5
params.addProperty("App::PropertyLength", "bottom_hollow_recess_width", "Dimensions", "Recess Width")
params.bottom_hollow_recess_width = 23.0
params.addProperty("App::PropertyLength", "bottom_hollow_recess_center_x_offset", "Dimensions", "Recess X Offset")
params.bottom_hollow_recess_center_x_offset = 19.25
params.addProperty("App::PropertyLength", "bottom_hollow_recess_center_y_offset", "Dimensions", "Recess Y Offset")
params.bottom_hollow_recess_center_y_offset = -14.5
params.addProperty("App::PropertyLength", "left_mounting_slot_length", "Dimensions", "Slot Length")
params.left_mounting_slot_length = 16.0
params.addProperty("App::PropertyLength", "left_mounting_slot_arc_radius", "Dimensions", "Slot Radius")
params.left_mounting_slot_arc_radius = 3.5
params.addProperty("App::PropertyLength", "left_mounting_slot_vertical_offset", "Dimensions", "Slot Y Offset")
params.left_mounting_slot_vertical_offset = -17.0
params.addProperty("App::PropertyLength", "left_mounting_slot_center_x_offset", "Dimensions", "Slot X Offset")
params.left_mounting_slot_center_x_offset = -14.5
params.addProperty("App::PropertyLength", "top_mounting_slot_length", "Dimensions", "Top Slot Length")
params.top_mounting_slot_length = 16.0
params.addProperty("App::PropertyLength", "top_mounting_slot_arc_radius", "Dimensions", "Top Slot Radius")
params.top_mounting_slot_arc_radius = 3.5
params.addProperty("App::PropertyLength", "top_mounting_slot_horizontal_offset", "Dimensions", "Top Slot X Offset")
params.top_mounting_slot_horizontal_offset = 17.0
params.addProperty("App::PropertyLength", "top_mounting_slot_center_y_offset", "Dimensions", "Top Slot Y Offset")
params.top_mounting_slot_center_y_offset = 14.5

# --- Main Side Profile Sketch (Side View) ---
# Origin: Shared outside corner (0,0)
# X axis: Along horizontal arm
# Y axis: Along vertical arm
sketch_side = body.newObject("Sketcher::SketchObject", "SideProfile")
sketch_side.Plane = "XY_Plane"
sketch_side.ConstrainAuto = False
sketch_side.MappingType = "Auto"

# Geometry: Outer Rectangle (L-shape boundary)
# We define the L-shape using a closed loop of lines.
# Points: (0,0) -> (L, 0) -> (L, -F) -> (L, H-F) -> (L, H) -> (0, H) -> (0,0)
# Wait, coordinate system check:
# "positive horizontal distance runs toward the free end of the horizontal arm" -> +X
# "positive vertical distance runs toward the free end of the vertical arm" -> +Y
# "depth is normal to this profile" -> +Z (extruded)
#
# Outer Edges:
# Horizontal Arm Top: (0, H) to (L, H)
# Vertical Arm Right: (L, H) to (L, 0)
# Horizontal Arm Bottom: (L, 0) to (0, 0)
# Vertical Arm Left: (0, 0) to (0, H)
# Wait, description says "L-triangle bracket plate". Usually L-bracket is 90 deg.
# Let's re-read carefully: "constant-depth triangular bracket body".
# "vertical and horizontal arms".
# "shared outside corner".
# If it's an L-bracket, the profile is an L-shape.
# Points: (0,0) is the shared outside corner.
# Horizontal arm goes to +X. Vertical arm goes to +Y.
# Outer boundary:
# 1. (0,0) to (L, 0) [Bottom of Horiz Arm]
# 2. (L, 0) to (L, H) [Right side of Horiz Arm? No, L shape]
# Let's assume standard L-bracket orientation:
# Bottom edge is Y=0 from X=0 to X=L.
# Right edge is X=L from Y=0 to Y=Height_of_horizontal_arm_part.
# Top edge is Y=H from X=0 to X=Width_of_vertical_arm_part.
# Left edge is X=0 from Y=0 to Y=H.
#
# BUT, the description says:
# "At the vertical-arm free end, the inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length."
# "At the horizontal-arm free end, the inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_horizontal_inner_straight_length."
# "A single straight diagonal joins the ends of those two inner straight portions."
#
# This implies the inner boundary is NOT a simple L-shape corner (90 deg). It has a chamfer/cutout at the inner corner.
#
# Let's define the outer boundary first.
# Outer Boundary Points:
# A: (0, 0) - Shared Outside Corner
# B: (L, 0) - End of Horizontal Arm (Outer)
# C: (L, -F) - Start of Vertical Inner Wall? No.
# Let's visualize the L-shape cross-section.
#
# Outer Face 1 (Bottom of Horiz): Y=0, X in [0, L]
# Outer Face 2 (Right of Vert): X=L, Y in [0, H] ?? No, usually L bracket has one flat outer face.
# Let's assume the "Side Profile" is the view looking at the L-shape.
# X axis along Horiz Arm. Y axis along Vert Arm.
#
# Outer Perimeter:
# (0,0) -> (L, 0) -> (L, H) -> (0, H) -> (0,0) ? That's a rectangle.
# An L-bracket has a "step".
# Let's assume:
# Horizontal Arm is the bottom leg. Length L. Height F (flange thickness).
# Vertical Arm is the left leg. Height H. Width F.
# Shared corner is (0,0).
#
# Outer Boundary:
# 1. (0,0) to (L, 0) [Bottom of Horiz Arm]
# 2. (L, 0) to (L, H) [Right side of Horiz Arm + Right side of Vert Arm?]
# No, if it's an L-bracket, the vertical arm sticks up from the horizontal arm.
# Let's assume the "Side Profile" is the plane containing the L-shape.
#
# Points:
# P1: (0, 0) - Shared Outside Corner (Bottom Left)
# P2: (L, 0) - End of Horizontal Arm (Bottom Right)
# P3: (L, H) - Top Right Corner? No.
#
# Let's try this configuration:
# Horizontal Arm: Extends from X=0 to X=L at Y=0. Thickness is Z-depth? No, "flange thickness" is likely the dimension perpendicular to the face where the slot is.
# "left mounting slot lies on the outer face of the vertical arm."
# "top mounting slot lies on the outer face of the horizontal arm."
#
# Okay, let's build the L-shape in the XY plane.
# Origin (0,0) is the shared outside corner.
# Horizontal Arm extends +X. Vertical Arm extends +Y.
#
# Outer Boundary:
# (0,0) -> (L, 0) [Bottom edge of Horiz Arm]
# (L, 0) -> (L, H) [Right edge of Horiz Arm and Vert Arm combined? No]
#
# Let's assume the standard L-shape:
# Horizontal Arm: Width L (X), Height F (Y).
# Vertical Arm: Height H (Y), Width F (X).
# They meet at (0,0).
#
# Outer Perimeter:
# (0,0) -> (L, 0) -> (L, F) -> (L, H) -> (0, H) -> (0, 0)
# Wait, if Width is F, then Vertical Arm occupies X in [0, F].
# If Height is H, then Vertical Arm occupies Y in [0, H].
# If Horizontal Arm is Y in [0, F] and X in [0, L].
#
# Intersection is [0, F] x [0, F].
#
# Outer Boundary Path:
# Start (0,0).
# Go to (L, 0). (Bottom of Horiz)
# Go to (L, F). (Right side of Horiz)
# Go to (L, H). (Right side of Vert? No, Vert is at X=0..F)
#
# Let's rethink. "L-triangle bracket". "Triangular" might imply the profile is a triangle?
# "constant-depth triangular bracket body, perpendicular vertical and horizontal arms".
# "outer edges reach l_triangle_bracket_plate_length and l_triangle_bracket_plate_height".
# "inner boundary... runs back toward the shared corner".
# "A single straight diagonal joins the ends of those two inner straight portions."
#
# This description strongly suggests the profile is a rectangle with a triangular cutout at the inner corner?
# OR, the profile IS a triangle (right triangle) where the arms are the legs, but the thickness is constant?
# "perpendicular vertical and horizontal arms" -> Legs of a right triangle.
# "outer edges reach L and H". -> Hypotenuse connects (L,0) and (0,H)?
# If it's a right triangle, the outer boundary is (0,0)->(L,0)->(L,H)->(0,H)->(0,0)? No, that's a rectangle.
# If it's a triangle, it's (0,0)->(L,0)->(0,H)->(0,0).
# But then "flange thickness" implies a 3D extrusion of a 2D profile.
# If the profile is a triangle, the "arms" are the legs.
#
# Let's re-read: "At the vertical-arm free end, the inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length."
# If the profile is a triangle, the "inner boundary" is the hypotenuse?
# No, "inner boundary" usually refers to the material boundary inside the footprint.
# If it's an L-shape (rectangular cross section with a corner cut), the inner boundary is the "step".
#
# Let's assume the "Side Profile" is the view of the L-shape.
# Outer edges:
# 1. Bottom of Horiz Arm: Y=0, X from 0 to L.
# 2. Right of Vert Arm: X=L? No, if it's an L-bracket, the vertical arm is usually on the left or right.
# Let's assume:
# Horizontal Arm: Base Y=0, X from 0 to L. Thickness (Y-dir) = F.
# Vertical Arm: Base X=0, Y from 0 to H. Thickness (X-dir) = F.
#
# If they meet at (0,0), and form an L:
# Horizontal part: X in [0, L], Y in [0, F].
# Vertical part: X in [0, F], Y in [0, H].
#
# Outer Boundary:
# (0,0) -> (L, 0) -> (L, F) -> (L, H) -> (0, H) -> (0, 0).
# This creates a shape with a "step" at (F, F) to (L, F) to (L, H)? No.
# The step is at X=F.
# Points:
# (0,0) -> (L, 0) -> (L, F) -> (F, F) -> (F, H) -> (0, H) -> (0,0).
# This is a standard L-shape.
#
# Now apply the "inner boundary" description:
# "At the vertical-arm free end (Y=H), the inner boundary is inset by flange thickness (F) and runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length (V_ISL)."
# Current inner corner of standard L is (F, F).
# Inner edge of Vertical arm is X=F, from Y=0 to Y=H.
# "Inset by flange thickness": This phrasing is tricky.
# "runs back toward the shared corner for V_ISL".
# Maybe the "inner boundary" is the line X = F - F = 0? No.
# Maybe the "inner boundary" starts at the free end (Y=H) and goes inwards (X direction) by F?
# Start point: (F, H). Move X by F? -> (0, H). That's the top edge.
#
# Let's interpret "inset by flange thickness" as "the material thickness is F".
# "runs back toward the shared corner for V_ISL".
# From the free end of the vertical arm (X=F, Y=H), we move towards the corner (0,0).
# Direction: Diagonal? Or along the edge?
# "At the vertical-arm free end, the inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length."
#
# Hypothesis: The profile is a rectangle L x H, with a rectangular cutout at the inner corner (F, F) to (L, H)? No.
# Let's try the "Triangular" hint again.
# "Triangular bracket body". "Perpendicular vertical and horizontal arms".
# Maybe the profile is a Right Triangle (0,0), (L,0), (0,H).
# Area = 0.5 * L * H.
# "Flange thickness" -> The thickness of the legs.
# If it's a triangle, the "arms" are the legs.
# "At the vertical-arm free end (0,H), the inner boundary is inset by flange thickness..."
# In a triangle, the inner boundary is the hypotenuse.
# But it says "runs back ... for V_ISL". This implies a straight segment of length V_ISL.
#
# Alternative Interpretation (Most likely for "L-triangle"):
# The profile is an L-shape, but the inner corner is modified.
# Outer Boundary: (0,0) -> (L,0) -> (L,F) -> (L,H) -> (0,H) -> (0,0). (Wait, this is not an L, this is a rect with a step).
# Standard L-shape:
# Outer: (0,0) -> (L,0) -> (L,F) -> (F,F) -> (F,H) -> (0,H) -> (0,0).
# Inner Corner is at (F,F).
#
# "At the vertical-arm free end (F,H), the inner boundary is inset by the flange thickness (F) and runs back toward the shared corner for V_ISL."
# Start at (F,H). Inset by F (X direction)? -> (0,H). That's the top edge.
# Then "runs back ... for V_ISL".
#
# Let's try this:
# The inner boundary of the vertical arm is a line segment starting at (F,H) going towards (0,0) but limited to length V_ISL?
# No, "runs back ... for V_ISL".
# Maybe the inner boundary of the vertical arm is NOT at X=F.
# Maybe the vertical arm is thicker?
#
# Let's look at the numbers.
# L=34.5, H=34.0, F=5.0.
# V_ISL = 5.0, H_ISL = 5.0.
# These are small.
#
# "A single straight diagonal joins the ends of those two inner straight portions."
# This implies the inner corner is a triangle/cutout.
#
# Scenario:
# Outer boundary is a rectangle L x H? No, "L-triangle".
# Maybe the outer boundary is (0,0)->(L,0)->(
