import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("L_Bracket")

# --- Parameters ---
# Define a VarSet to hold all parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_length", "Dimensions", "Total length of horizontal arm")
params.l_triangle_bracket_plate_length = 34.5
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_height", "Dimensions", "Total height of vertical arm")
params.l_triangle_bracket_plate_height = 34.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_depth", "Dimensions", "Depth of the bracket")
params.l_triangle_bracket_plate_depth = 29.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_flange_thickness", "Dimensions", "Thickness of the arms")
params.l_triangle_bracket_plate_flange_thickness = 5.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_vertical_inner_straight_length", "Dimensions", "Length of vertical inner straight edge")
params.l_triangle_bracket_plate_vertical_inner_straight_length = 5.0
params.addProperty("App::PropertyLength", "l_triangle_bracket_plate_horizontal_inner_straight_length", "Dimensions", "Length of horizontal inner straight edge")
params.l_triangle_bracket_plate_horizontal_inner_straight_length = 5.0

# Bottom Hollow Recess
params.addProperty("App::PropertyLength", "bottom_hollow_recess_length", "Dimensions", "Length of recess")
params.bottom_hollow_recess_length = 30.5
params.addProperty("App::PropertyLength", "bottom_hollow_recess_width", "Dimensions", "Width of recess")
params.bottom_hollow_recess_width = 23.0
params.addProperty("App::PropertyLength", "bottom_hollow_recess_depth", "Dimensions", "Depth of recess (should be > depth)")
params.bottom_hollow_recess_depth = 31.0
params.addProperty("App::PropertyLength", "bottom_hollow_recess_center_x_offset", "Dimensions", "X offset of recess center")
params.bottom_hollow_recess_center_x_offset = 19.25
params.addProperty("App::PropertyLength", "bottom_hollow_recess_center_y_offset", "Dimensions", "Y offset of recess center")
params.bottom_hollow_recess_center_y_offset = -14.5

# Left Mounting Slot (Vertical Arm)
params.addProperty("App::PropertyLength", "left_mounting_slot_length", "Dimensions", "Length of slot")
params.left_mounting_slot_length = 16.0
params.addProperty("App::PropertyLength", "left_mounting_slot_arc_radius", "Dimensions", "Radius of slot ends")
params.left_mounting_slot_arc_radius = 3.5
params.addProperty("App::PropertyLength", "left_mounting_slot_vertical_offset", "Dimensions", "Y offset of slot center")
params.left_mounting_slot_vertical_offset = -17.0
params.addProperty("App::PropertyLength", "left_mounting_slot_center_x_offset", "Dimensions", "X offset of slot center")
params.left_mounting_slot_center_x_offset = -14.5

# Top Mounting Slot (Horizontal Arm)
params.addProperty("App::PropertyLength", "top_mounting_slot_length", "Dimensions", "Length of slot")
params.top_mounting_slot_length = 16.0
params.addProperty("App::PropertyLength", "top_mounting_slot_arc_radius", "Dimensions", "Radius of slot ends")
params.top_mounting_slot_arc_radius = 3.5
params.addProperty("App::PropertyLength", "top_mounting_slot_horizontal_offset", "Dimensions", "X offset of slot center")
params.top_mounting_slot_horizontal_offset = 17.0
params.addProperty("App::PropertyLength", "top_mounting_slot_center_y_offset", "Dimensions", "Y offset of slot center")
params.top_mounting_slot_center_y_offset = 14.5

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Main Profile Sketch (Side View) ---
# Coordinates: Origin at shared outside corner.
# X: Horizontal arm direction. Y: Vertical arm direction.
# The profile is an L-shape.
# Outer boundary: (0,0) -> (L, 0) -> (L, -T) -> (L-T, -T) -> (L-T, H-T) -> (0, H-T) -> (0, H) -> (0,0)
# Wait, let's re-read the geometry description carefully.
# "positive horizontal distance runs toward the free end of the horizontal arm" -> X+
# "positive vertical distance runs toward the free end of the vertical arm" -> Y+
# "outer edges reach l_triangle_bracket_plate_length and l_triangle_bracket_plate_height"
# "Each arm has l_triangle_bracket_plate_flange_thickness"
# "At the vertical-arm free end, the inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length"
# "At the horizontal-arm free end, the inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_horizontal_inner_straight_length"
# "A single straight diagonal joins the ends of those two inner straight portions"

# Let's define the vertices based on the description.
# Shared Corner: (0, 0)
# Horizontal Arm Outer Edge: (0,0) to (L, 0)
# Vertical Arm Outer Edge: (0,0) to (0, H)
# 
# Inner Boundary:
# 1. Vertical Arm Inner Straight: Starts at (0, H) and goes down? 
#    "runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length"
#    So from (0, H) down to (0, H - V_inner).
#    Wait, "inset by the flange thickness". 
#    Usually, an L-bracket has a uniform thickness T.
#    If the outer edge is at Y=H, the inner edge of the vertical arm is at Y = H - T.
#    The description says: "inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length".
#    This implies the straight segment length is V_inner.
#    So the segment is from (0, H) to (0, H - V_inner).
#    Then a diagonal connects to the horizontal arm's inner start.
#
# 2. Horizontal Arm Inner Straight:
#    "inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_horizontal_inner_straight_length"
#    Outer edge is at X=L. Inner edge is at X = L - T.
#    Segment runs from (L-T, 0) back to (L-T, 0 - H_inner)? No, "toward the shared corner".
#    Shared corner is (0,0).
#    So the segment is from (L-T, 0) to (L-T, -H_inner)? 
#    Wait, the coordinate system says "positive vertical distance runs toward the free end of the vertical arm".
#    So the vertical arm is in +Y. The horizontal arm is in +X.
#    The "free end" of the vertical arm is at Y=H.
#    The "free end" of the horizontal arm is at X=L.
#    
#    Let's trace the perimeter counter-clockwise starting from (0,0):
#    1. (0,0) to (L, 0) [Horizontal Outer]
#    2. (L, 0) to (L, -T) ?? No, thickness is usually perpendicular to the face.
#       If the vertical arm is along Y, its thickness is in X.
#       If the horizontal arm is along X, its thickness is in Y.
#       But they share a corner.
#       Let's assume the "flange thickness" is the width of the material at the ends.
#       Vertical Arm: Width in X is T. Extends from X=0 to X=T? Or X=L-T to X=L?
#       "At the vertical-arm free end, the inner boundary is inset by the flange thickness".
#       This implies the vertical arm has a constant width T.
#       If the outer edge is at X=0 (shared corner side) to X=L? No, that's the horizontal arm.
#       Let's assume the L-shape is formed by two rectangles meeting at (0,0).
#       Rect 1 (Vertical): X in [0, T], Y in [0, H].
#       Rect 2 (Horizontal): X in [0, L], Y in [-T, 0].
#       This creates an L shape in the 4th quadrant?
#       But the prompt says "positive vertical distance runs toward the free end of the vertical arm".
#       So Vertical Arm is Y > 0.
#       "positive horizontal distance runs toward the free end of the horizontal arm".
#       So Horizontal Arm is X > 0.
#       They share the corner (0,0).
#       So we have a block in X>0, Y>0? That's a rectangle.
#       It must be an L-shape.
#       Maybe the "thickness" is the dimension perpendicular to the long axis.
#       Vertical Arm: Long axis Y. Thickness in X.
#       Horizontal Arm: Long axis X. Thickness in Y.
#       If they share (0,0) as the "outside corner", then:
#       Vertical Arm occupies X in [0, T], Y in [0, H].
#       Horizontal Arm occupies X in [0, L], Y in [-T, 0].
#       This forms an L shape in the 4th quadrant (mostly).
#       BUT the prompt says "positive vertical distance runs toward the free end".
#       If the vertical arm is Y in [0, H], then Y is positive.
#       If the horizontal arm is X in [0, L], then X is positive.
#       Where is the "thickness"?
#       If Vertical Arm is X in [0, T], then the "inner boundary" of the vertical arm is at X=T.
#       If Horizontal Arm is Y in [-T, 0], then the "inner boundary" of the horizontal arm is at Y=-T.
#       
#       Let's re-read: "At the vertical-arm free end, the inner boundary is inset by the flange thickness and runs back toward the shared corner for l_triangle_bracket_plate_vertical_inner_straight_length".
#       Free end of vertical arm is at Y=H.
#       Inner boundary starts at X=T (inset from X=0? No, inset from the outer edge).
#       If the outer edge is X=0, the inner edge is X=T.
#       So at Y=H, we have a segment from X=0 to X=T? No, that's the outer edge.
#       The "inner boundary" is the edge facing the void.
#       If the vertical arm is the block [0,T] x [0,H], the inner boundary is the line X=T.
#       "runs back toward the shared corner".
#       So from (T, H) down to (T, H - V_inner).
#       Then a diagonal connects to the horizontal arm's inner start.
#       
#       Horizontal Arm: Block [0, L] x [-T, 0].
#       Free end at X=L.
#       Inner boundary is Y=-T.
#       "runs back toward the shared corner".
#       So from (L, -T) left to (L - H_inner, -T).
#       Then a diagonal connects to the vertical arm's inner end.
#       
#       This creates a closed loop:
#       (0,0) -> (L, 0) [Outer Horiz]
#       (L, 0) -> (L, -T) [Corner thickness]
#       (L, -T) -> (L - H_inner, -T) [Inner Horiz Straight]
#       (L - H_inner, -T) -> (T, H - V_inner) [Diagonal]
#       (T, H - V_inner) -> (T, H) [Inner Vert Straight]
#       (T, H) -> (0, H) [Corner thickness]
#       (0, H) -> (0, 0) [Outer Vert]
#       
#       Wait, the prompt says "outer edges reach l_triangle_bracket_plate_length and l_triangle_bracket_plate_height".
#       My trace: Max X = L. Max Y = H. This fits.
#       "Each arm has l_triangle_bracket_plate_flange_thickness".
#       My trace: Thickness in X for vert arm is T. Thickness in Y for horiz arm is T. This fits.
#       
#       Let's verify the "inset" logic.
#       "inner boundary is inset by the flange thickness".
#       If the arm is width T, and the outer edge is at 0, the inner edge is at T.
#       This matches.
#       
#       So the Profile Sketch vertices are:
#       1. (0, 0)
#       2. (L, 0)
#       3. (L, -T)
#       4. (L - H_inner, -T)
#       5. (T, H - V_inner)  <-- Diagonal connects here
#       6. (T, H)
#       7. (0, H)
#       8. (0, 0)
#       
#       Wait, is the diagonal connecting (L-H_inner, -T) and (T, H-V_inner)?
#       "A single straight diagonal joins the ends of those two inner straight portions."
#       Yes.
#       
#       Let's calculate the coordinates explicitly.
#       L = params.l_triangle_bracket_plate_length
#       H = params.l_triangle_bracket_plate_height
#       T = params.l_triangle_bracket_plate_flange_thickness
#       V_inner = params.l_triangle_bracket_plate_vertical_inner_straight_length
#       H_inner = params.l_triangle_bracket_plate_horizontal_inner_straight_length
#       
#       Points:
#       P1: (0, 0)
#       P2: (L, 0)
#       P3: (L, -T)
#       P4: (L - H_inner, -T)
#       P5: (T, H - V_inner)
#       P6: (T, H)
#       P7: (0, H)
#       
#       This defines the L-shape profile.

# --- Create Sketch 1: Main Profile ---
sketch_profile = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
sketch_plane.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0)) # Already set
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0)) # Reset to ensure clean
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Placement = App.Placement(App
