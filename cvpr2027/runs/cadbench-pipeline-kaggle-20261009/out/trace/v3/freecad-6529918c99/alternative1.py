import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Define parameters based on the task description
# Global X follows frame length, Y follows height, Z follows depth.
# Frame is in XY plane at Z=0. Extrusion is along Z.

base_frame_extrusion_depth = 80.0
number_of_vertical_supports = 2
number_of_top_rails = 1

mounting_hole_diameter = 10.0
number_of_mounting_holes = 4
mounting_hole_depth = 20.0
mounting_hole_centerline_y_offset = 40.0
mounting_hole_left_outer_center_x = -815.0
mounting_hole_left_inner_center_x = -785.0
mounting_hole_right_inner_center_x = 785.0
mounting_hole_right_outer_center_x = 815.0

number_of_deep_mounting_holes = 2
mounting_hole_cut_depth = 2333.0
deep_mounting_hole_primary_center_x = -160.0
deep_mounting_hole_secondary_center_x = -190.0
deep_mounting_hole_center_y = 25.0

support_boss_height = 50.0
support_boss_diameter = 20.0
number_of_support_bosses = 12
spacing_distance_between_support_bosses = 263.0

end_boss_diameter = 20.0
number_of_end_bosses = 2
end_boss_height = 10.0
end_boss_left_center_x = -799.2678421
end_boss_right_center_x = 799.2678421
end_boss_center_y = 34.2678421

frame_left_end_x = -1500.0
frame_right_end_x = 1500.0
frame_top_y = 450.0
frame_inner_top_y = 380.0
frame_bottom_y = -450.0
left_support_outer_x = -835.0
left_support_inner_x = -765.0
right_support_inner_x = 765.0
right_support_outer_x = 835.0
support_boss_pattern_direction_x = -1.0
support_boss_seed_center_x = 1445.0
support_boss_seed_center_y = -415.0

# Create Document
doc = App.newDocument("ConveyorBaseFrame")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject(Type="PartDesign::Body", Name="Body", Label="Body")
body = doc.getObject("Body")

# Helper to create sketches on the XY plane relative to the body
def create_sketch(name, z_offset=0.0):
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.Placement = App.Placement(App.Vector(0, 0, z_offset))
    sk.Placement = App.Placement(App.Vector(0, 0, z_offset), App.Rotation())
    sk.Placement = App.Placement(App.Vector(0, 0, z_offset)) # Default is origin
    # Explicitly set placement to origin for simplicity as Body is at origin
    sk.Placement = App.Placement(App.Vector(0, 0, z_offset))
    return sk

# 1. Main Frame Body Sketch (XY Plane, Z=0)
# Profile: Top Rail + Vertical Supports
sk_main = create_sketch("sk_main")
sk_main.Placement = App.Placement(App.Vector(0, 0, 0))

# Top Rail: Line from frame_left_end_x to frame_right_end_y at y=frame_top_y
# Wait, description says "top rail spans ... between frame_inner_top_y and frame_top_y". 
# This usually implies a slot or a specific width. However, it says "Construct the connected rail-and-support body as a closed profile".
# Let's interpret "top rail spans ... between frame_inner_top_y and frame_top_y" as the rail having a thickness/height in Y.
# So the top rail is a rectangle or two lines? "Closed profile".
# Let's draw a rectangle for the top rail: x from frame_left_end_x to frame_right_end_x, y from frame_inner_top_y to frame_top_y.
# Then the vertical supports connect frame_inner_top_y down to frame_bottom_y.
# Left Support: x from left_support_outer_x to left_support_inner_x.
# Right Support: x from right_support_inner_x to right_support_outer_x.
# To make it a closed profile, we connect these.
# Path:
# 1. Bottom Rail: Line from (frame_right_end_x, frame_bottom_y) to (frame_left_end_x, frame_bottom_y)?
#    The description doesn't explicitly define a bottom rail length, but usually frames are symmetric or have end caps.
#    Given "frame_left_end_x" and "frame_right_end_x", let's assume a bottom rail connecting them at frame_bottom_y.
# 2. Right End Cap? Or just the supports hold the top?
#    "connected rail-and-support body as a closed profile".
#    Let's assume a rectangular perimeter at the bottom (frame_bottom_y) from frame_left_end_x to frame_right_end_x.
#    Then vertical lines up to frame_inner_top_y.
#    Then horizontal lines to the top rail edges.
#    Then top rail up to frame_top_y.
#    Then horizontal back to start.
#    Wait, "top rail spans ... between frame_inner_top_y and frame_top_y". This is the thickness of the top rail.
#    "left support spans ... frame_inner_top_y down to frame_bottom_y".
#    So the profile is:
#    - Start (frame_left_end_x, frame_bottom_y)
#    - Line to (frame_right_end_x, frame_bottom_y) [Bottom Rail]
#    - Line to (frame_right_end_x, frame_inner_top_y) [Right Support Outer Edge]
#    - Line to (right_support_inner_x, frame_inner_top_y) [Right Support Inner Edge]
#    - Line to (right_support_outer_x, frame_inner_top_y) [Wait, supports are usually between inner/outer]
#    Let's re-read: "left support spans left_support_outer_x to left_support_inner_x... right support spans right_support_inner_x to right_support_outer_x".
#    This implies the supports are the vertical sections at those X ranges.
#    So the profile must enclose the void between inner and outer supports? Or is the support solid material?
#    "connected rail-and-support body". Usually means the supports are part of the solid.
#    So the profile goes around the supports.
#    Let's trace the outer perimeter:
#    (frame_left_end_x, frame_bottom_y) -> (frame_right_end_x, frame_bottom_y) -> (right_support_outer_x, frame_inner_top_y) -> (right_support_outer_x, frame_top_y) -> (frame_right_end_x, frame_top_y) -> (frame_left_end_x, frame_top_y) -> (frame_left_end_x, frame_inner_top_y) -> (left_support_outer_x, frame_inner_top_y) -> (left_support_outer_x, frame_bottom_y).
#    This leaves the space between supports empty. That matches "vertical supports".
#    Wait, if the support is between left_outer and left_inner, then the solid is the support itself.
#    So the profile should trace the OUTSIDE of the left support, then IN, then OUT of the right support?
#    No, a single closed profile for a solid body.
#    If the supports are the solid parts, the profile should be the UNION of the top rail and the supports.
#    Top Rail: Rect [-1500, 1500] x [380, 450].
#    Left Support: Rect [-835, -765] x [-450, 380].
#    Right Support: Rect [765, 835] x [-450, 380].
#    Union of these three rectangles.
#    This creates a single closed profile with indentations.
#    Let's generate the vertices for this union.
#    1. Start (frame_left_end_x, frame_bottom_y) = (-1500, -450)
#    2. (frame_right_end_x, frame_bottom_y) = (1500, -450)
#    3. (right_support_outer_x, frame_inner_top_y) = (835, 380)
#    4. (right_support_inner_x, frame_inner_top_y) = (765, 380)
#    5. (frame_right_end_x, frame_inner_top_y) = (1500, 380)
#    6. (frame_right_end_x, frame_top_y) = (1500, 450)
#    7. (frame_left_end_x, frame_top_y) = (-1500, 450)
#    8. (frame_left_end_x, frame_inner_top_y) = (-1500, 380)
#    9. (left_support_outer_x, frame_inner_top_y) = (-835, 380)
#    10. (left_support_inner_x, frame_inner_top_y) = (-765, 380)
#    11. (frame_left_end_x, frame_inner_top_y) = (-1500, 380) -- Wait, this closes the loop?
#        No, from 9 to 10 is the left support inner edge (going left).
#        Then from 10 we need to go to the top rail? No, the top rail starts at inner_top_y.
#        So from 10 (-765, 380) we go to (frame_left_end_x, 380) which is (-1500, 380).
#        Then up to (-1500, 450).
#        Wait, the top rail is above 380. The supports end at 380.
#        So the profile goes:
#        (-1500, -450) -> (1500, -450) -> (835, 380) -> (765, 380) -> (1500, 380) -> (1500, 450) -> (-1500, 450) -> (-1500, 380) -> (-835, 380) -> (-765, 380) -> (-1500, 380) -> (-1500, -450).
#        This works. It defines the solid union of the three rectangles.
    
#    Vertices for Main Sketch:
#    1. (frame_left_end_x, frame_bottom_y)
#    2. (frame_right_end_x, frame_bottom_y)
#    3. (right_support_outer_x, frame_inner_top_y)
#    4. (right_support_inner_x, frame_inner_top_y)
#    5. (frame_right_end_x, frame_inner_top_y)
#    6. (frame_right_end_x, frame_top_y)
#    7. (frame_left_end_x, frame_top_y)
#    8. (frame_left_end_x, frame_inner_top_y)
#    9. (left_support_outer_x, frame_inner_top_y)
#    10. (left_support_inner_x, frame_inner_top_y)
#    11. (frame_left_end_x, frame_inner_top_y)
#    12. (frame_left_end_x, frame_bottom_y) - Close loop? No, 1 to 12 is start.
#    Wait, 8 is (-1500, 380). 9 is (-835, 380). 10 is (-765, 380).
#    From 9 to 10 is the top edge of the left support (going left? No, 9 is -835, 10 is -765. So going right).
#    My previous list had 9 -> 10. -835 to -765 is increasing X. Correct.
#    Then 10 -> 11 (-1500, 380). Going left. Correct.
#    Then 11 -> 12 (-1500, -450). Going down. Correct.
#    Then 12 -> 1. Closing.
    
#    Let's refine the list of segments:
#    L1: (frame_left_end_x, frame_bottom_y) to (frame_right_end_x, frame_bottom_y)
#    L2: (frame_right_end_x, frame_bottom_y) to (right_support_outer_x, frame_inner_top_y)
#    L3: (right_support_outer_x, frame_inner_top_y) to (right_support_inner_x, frame_inner_top_y)
#    L4: (right_support_inner_x, frame_inner_top_y) to (frame_right_end_x, frame_inner_top_y)
#    L5: (frame_right_end_x, frame_inner_top_y) to (frame_right_end_x, frame_top_y)
#    L6: (frame_right_end_x, frame_top_y) to (frame_left_end_x, frame_top_y)
#    L7: (frame_left_end_x, frame_top_y) to (frame_left_end_x, frame_inner_top_y)
#    L8: (frame_left_end_x, frame_inner_top_y) to (left_support_outer_x, frame_inner_top_y)
#    L9: (left_support_outer_x, frame_inner_top_y) to (left_support_inner_x, frame_inner_top_y)
#    L10: (left_support_inner_x, frame_inner_top_y) to (frame_left_end_x, frame_inner_top_y)
#    L11: (frame_left_end_x, frame_inner_top_y) to (frame_left_end_x, frame_bottom_y)

    points = [
        App.Vector(frame_left_end_x, frame_bottom_y, 0),
        App.Vector(frame_right_end_x, frame_bottom_y, 0),
        App.Vector(right_support_outer_x, frame_inner_top_y, 0),
        App.Vector(right_support_inner_x, frame_inner_top_y, 0),
        App.Vector(frame_right_end_x, frame_inner_top_y, 0),
        App.Vector(frame_right_end_x, frame_top_y, 0),
        App.Vector(frame_left_end_x, frame_top_y, 0),
        App.Vector(frame_left_end_x, frame_inner_top_y, 0),
        App.Vector(left_support_outer_x, frame_inner_top_y, 0),
        App.Vector(left_support_inner_x, frame_inner_top_y, 0),
        App.Vector(frame_left_end_x, frame_inner_top_y, 0)
    ]

    for i in range(len(points)):
        j = (i + 1) % len(points)
        sk_main.addGeometry(Part.LineSegment(points[i], points[j]), False)

    sk_main.ConstrainType = "FullyDefined" # FreeCAD Sketcher API usually handles this via constraints or lines
    # We need to add constraints to make it rigid? 
    # Actually, for a closed loop of lines, FreeCAD often needs explicit constraints if not fully defined by geometry.
    # But with a closed loop of segments, it might be enough. Let's add a closure constraint to be safe.
    # Using the Sketcher API:
    # We can just add constraints between endpoints.
    # However, the simplest way in headless script for a closed loop is often enough.
    # Let's add a constraint for the last point to the first point just in case.
    # Actually, the loop is closed by the segment index.
    # Let's add a few constraints to ensure rigidity.
    # Horizontal constraints for top and bottom rails.
    # Vertical constraints for the outer edges of supports.
    
    # Add constraints
    # Bottom Rail
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 2, 1, 1, "X"))
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 2, 1, 2, "X")) # Horizontal
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 2, 0, 2, "X"))
    
    # Top Rail
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 6, 1, 1, "X"))
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 6, 1, 2, "X"))
    
    # Verticals
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 1, 0, 2, "X"))
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 5, 0, 2, "X"))
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 7, 0, 2, "X"))
    sk_main.addConstraint(Sketcher.Constraint("Axis", 0, 10, 0, 2, "X"))

    # Center the sketch in XY plane? It is at Z=0.
    # We need to ensure the sketch is closed. The segments form a closed loop.
    # Let's add a constraint to link the last point to the first point explicitly if needed, 
    # but the segment list closes it.
    # To be robust, let's add a constraint between the start and end points.
    sk_main.addConstraint(Sketcher.Constraint("Distance", 10, 11, 0)) # Distance 0 between last and first? No, they are connected.
    # Actually, let's just rely on the geometry. If it fails, we can add constraints.
    # For a
