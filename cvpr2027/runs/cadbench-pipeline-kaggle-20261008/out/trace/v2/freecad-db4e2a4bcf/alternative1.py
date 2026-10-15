import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Configuration derived from the task description
CONFIG = {
    "ladder_side_rails_length": 2400.0,
    "ladder_side_rail_width": 40.0,
    "ladder_side_rail_thickness": 90.0,
    "ladder_rung_length": 400.0,   # Clear span
    "ladder_rung_width": 40.0,     # Vertical dimension in sketch
    "ladder_rung_thickness": 40.0, # Out-of-plane thickness
    "ladder_number_of_rungs": 7,
    "ladder_rung_spacing": 300.0,
}

# Calculate derived parameters
outer_width = CONFIG["ladder_rung_length"] + (2 * CONFIG["ladder_side_rail_width"])
total_rung_span = (CONFIG["ladder_number_of_rungs"] - 1) * CONFIG["ladder_rung_spacing"]

# Initialize Document
doc = App.newDocument("Ladder")
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Parameters Object ---
# We create a VarSet to hold the named parameters requested by the prompt
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "ladder_side_rails_length", "Dimensions", "Side rail length")
params.addProperty("App::PropertyLength", "ladder_side_rail_width", "Dimensions", "Side rail width")
params.addProperty("App::PropertyLength", "ladder_side_rail_thickness", "Dimensions", "Side rail thickness")
params.addProperty("App::PropertyLength", "ladder_rung_length", "Dimensions", "Rung clear span")
params.addProperty("App::PropertyLength", "ladder_rung_width", "Dimensions", "Rung vertical height")
params.addProperty("App::PropertyLength", "ladder_rung_thickness", "Dimensions", "Rung thickness")
params.addProperty("App::PropertyLength", "ladder_rung_spacing", "Dimensions", "Rung spacing")
params.addProperty("App::PropertyInteger", "ladder_number_of_rungs", "Dimensions", "Number of rungs")

# Set initial values
params.ladder_side_rails_length = CONFIG["ladder_side_rails_length"]
params.ladder_side_rail_width = CONFIG["ladder_side_rail_width"]
params.ladder_side_rail_thickness = CONFIG["ladder_side_rail_thickness"]
params.ladder_rung_length = CONFIG["ladder_rung_length"]
params.ladder_rung_width = CONFIG["ladder_rung_width"]
params.ladder_rung_thickness = CONFIG["ladder_rung_thickness"]
params.ladder_rung_spacing = CONFIG["ladder_rung_spacing"]
params.ladder_number_of_rungs = CONFIG["ladder_number_of_rungs"]

# --- Feature 1: Side Rail Sketch ---
# We need a sketch that defines the cross-section of the side rails.
# Orientation: The ladder lies along Z. The rails run along Z.
# The cross-section (Width x Thickness) is in the X-Y plane.
# Let's place the sketch on the XY plane, centered at origin.
# X axis: Half of total outer width. Y axis: Half of rail thickness.

sketch_rails = body.newObject("Sketcher::SketchObject", "SideRailSketch")
sketch_rails.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_rails.AttachmentSupport = [doc.getObject("XY_Plane"), ""]
sketch_rails.MapMode = "FlatFace"

# Geometry for one rail cross section
# Left Rail: x = -outer_width/2, width = rail_width
# Right Rail: x = +outer_width/2, width = rail_width
# Thickness in Y direction: rail_thickness

# Left Rail Rectangle
# Points: (-W/2, -T/2), (-W/2, T/2), (W/2, T/2), (W/2, -T/2) -> No, wait.
# Left rail is at x = -outer_width/2. Width is rail_width.
# So x ranges from -outer_width/2 to -outer_width/2 + rail_width.
# Y ranges from -rail_thickness/2 to rail_thickness/2.

rail_half_width = CONFIG["ladder_side_rail_width"] / 2.0
rail_half_thickness = CONFIG["ladder_side_rail_thickness"] / 2.0
rail_left_x = -CONFIG["ladder_rung_length"] / 2.0 - rail_half_width
rail_right_x = -CONFIG["ladder_rung_length"] / 2.0 + rail_half_width

# Add 4 points for Left Rail
sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_left_x, -rail_half_thickness, 0), 
                                           App.Vector(rail_left_x, rail_half_thickness, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_left_x, rail_half_thickness, 0), 
                                           App.Vector(rail_right_x, rail_half_thickness, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_right_x, rail_half_thickness, 0), 
                                           App.Vector(rail_right_x, -rail_half_thickness, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_right_x, -rail_half_thickness, 0), 
                                           App.Vector(rail_left_x, -rail_half_thickness, 0)), False)

# Right Rail Rectangle
# x ranges from CONFIG["ladder_rung_length"]/2 - rail_half_width to CONFIG["ladder_rung_length"]/2 + rail_half_width
rail_left_x_r = CONFIG["ladder_rung_length"] / 2.0 - rail_half_width
rail_right_x_r = CONFIG["ladder_rung_length"] / 2.0 + rail_half_width

sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_left_x_r, -rail_half_thickness, 0), 
                                           App.Vector(rail_left_x_r, rail_half_thickness, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_left_x_r, rail_half_thickness, 0), 
                                           App.Vector(rail_right_x_r, rail_half_thickness, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_right_x_r, rail_half_thickness, 0), 
                                           App.Vector(rail_right_x_r, -rail_half_thickness, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(rail_right_x_r, -rail_half_thickness, 0), 
                                           App.Vector(rail_left_x_r, -rail_half_thickness, 0)), False)

# Constraints for Side Rail Sketch
# 1. Coincident all vertical lines (x=const) to define width accurately
# 2. Coincident all horizontal lines (y=const) to define thickness accurately
# 3. Horizontal lines parallel to X axis
# 4. Vertical lines parallel to Y axis

# Helper to get geometry index by type and position
# Lines: 0-3 (Left), 4-7 (Right)
# 0: Left Bottom, 1: Left Top, 2: Right Top, 3: Right Bottom
# 4: Right Bottom, 5: Right Top, 6: Right Left-Top, 7: Right Left-Bottom (Wait, indices are sequential in addGeometry)
# Actually, indices are 0 to N-1.
# Let's constrain:
# Line 0 (Left Bottom) || Y
# Line 1 (Left Top) || Y
# Line 2 (Right Top) || Y
# Line 3 (Right Bottom) || Y
# Line 4 (Right Bottom) || Y (Duplicate? No, let's just constrain relative to each other)

# Simpler approach: Coincident points.
# Point 0-3 form left rect. Point 4-7 form right rect.
# Let's just constrain the lines to be parallel and coincident where needed.

# Parallel constraints
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 0, 1)) # Left sides parallel
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 2, 3)) # Right sides parallel
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 4, 5)) # Right rect sides
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 6, 7)) # Right rect sides

# Coincident vertical lines to ensure outer width is correct
# Left side (0,1) coincident with itself? No, we need them to be aligned.
# Actually, simpler: Coincident the top-left corner of left rail with top-left of right rail? No.
# We want the gap to be exactly ladder_rung_length.
# Center of left rail x = -outer_width/2 + rail_width/2 = -200 + 20 = -180.
# Center of right rail x = 200 - 20 = 180.
# Distance = 360.
# Wait, outer width = 480. Half = 240.
# Left rail center = -240 + 20 = -220.
# Right rail center = 240 - 20 = 220.
# Gap = 440?
# Prompt says: side_rail_outer_to_outer_width = 480.
# So Left Rail x_center = -240. Right Rail x_center = +240.
# Left Rail width = 40. So Left Rail spans -260 to -220.
# Right Rail width = 40. So Right Rail spans +220 to +260.
# Gap = 220 - (-220) = 440.
# Prompt says ladder_rung_length = 400.
# My calculation: 400 + 2*40 = 480. Correct.
# So Left Rail x_center = -240. Right Rail x_center = +240.
# Left Rail: -280 to -200? No.
# If outer width is 480, then x goes from -240 to +240.
# Left Rail is at the edge. So Left Rail spans -240 to (-240 + 40) = -200.
# Right Rail spans (240 - 40) to 240 = 200 to 240.
# Gap = 200 - (-200) = 400. Correct.

# Let's adjust sketch coordinates based on this:
# Left Rail: x from -240 to -200. y from -45 to 45.
# Right Rail: x from 200 to 240. y from -45 to 45.

sketch_rails = body.getObject("SideRailSketch")
# Re-add geometry with corrected coordinates
# Left Rail
sketch_rails.addGeometry(Part.LineSegment(App.Vector(-240, -45, 0), App.Vector(-240, 45, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(-240, 45, 0), App.Vector(-200, 45, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(-200, 45, 0), App.Vector(-200, -45, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(-200, -45, 0), App.Vector(-240, -45, 0)), False)

# Right Rail
sketch_rails.addGeometry(Part.LineSegment(App.Vector(200, -45, 0), App.Vector(200, 45, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(200, 45, 0), App.Vector(240, 45, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(240, 45, 0), App.Vector(240, -45, 0)), False)
sketch_rails.addGeometry(Part.LineSegment(App.Vector(240, -45, 0), App.Vector(200, -45, 0)), False)

# Constraints
# Verticals parallel
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 0, 1))
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 2, 3))
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 4, 5))
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 6, 7))

# Horizontals parallel
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 0, 2)) # Left Bottom || Right Top
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 1, 3))
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 4, 6))
sketch_rails.addConstraint(Sketcher.Constraint("Parallel", 5, 7))

# Coincident verticals to ensure symmetry and correct gap?
# We can constrain the mid-point of the verticals or just rely on the coordinates.
# To make it parametric: Express coordinates based on parameters.
# But for a robust script, let's constrain the relative positions.
# Constraint: Distance between vertical line 0 and vertical line 4?
# No, let's just constrain the horizontal lines to be equidistant from center (Horizontal centerline)
# And vertical lines to be symmetric.
# Actually, let's just constrain the corners.
# Corner 0 (-240, -45) and Corner 4 (200, -45) -> Same Y level.
# Corner 1 (-240, 45) and Corner 5 (200, 45) -> Same Y level.
# This ensures the gap is uniform.

sketch_rails.addConstraint(Sketcher.Constraint("EqualY", 0, 4))
sketch_rails.addConstraint(Sketcher.Constraint("EqualY", 1, 5))
sketch_rails.addConstraint(Sketcher.Constraint("EqualY", 2, 6))
sketch_rails.addConstraint(Sketcher.Constraint("EqualY", 3, 7))

# Also ensure verticals are at correct distance?
# We can define a center line constraint.
# But since we used absolute coordinates in the script, we can just set constraints to lock the shape.
# Let's add a constraint that the distance between the inner verticals is ladder_rung_length.
# Inner vertical 1 is at x=-200. Inner vertical 5 is at x=200.
# Distance = 400.
# We can use a distance constraint between two points on these lines.
# Point on Line 1 (Top-Left Inner): (-200, 45)
# Point on Line 5 (Top-Right Inner): (200, 45)
# Wait, indices:
# 0: Left Bot (-240, -45)
# 1: Left Top (-240, 45)
# 2: Right Top (240, 45)
# 3: Right Bot (240, -45)
# 4: Right Bot (200, -45)
# 5: Right Top (200, 45)
# 6: Right Top (240, 45) -- Wait, I added 8 lines.
# My list above:
# 0: (-240, -45) to (-240, 45) -> Vertical
# 1: (-240, 45) to (-200, 45) -> Horizontal
# 2: (-200, 45) to (-200, -45) -> Vertical
# 3: (-200, -45) to (-240, -45) -> Horizontal
# 4: (200, -45) to (200, 45) -> Vertical
# 5: (200, 45) to (240, 45) -> Horizontal
# 6: (240, 45) to (240, -45) -> Vertical
# 7: (240, -45) to (200, -45) -> Horizontal

# Correct Indices:
# Verts: 0, 2, 4, 6
# Horiz: 1, 3, 5, 7
# Inner Verts: 2 (Left Inner) and 4 (Right Inner).
# Constraint: Distance between top point of 2 (-200, 45) and top point of 4 (200, 45) is 400.
sketch_rails.addConstraint(Sketcher.Constraint("DistanceX", 2, 4, 400)) # Force gap to 400

# Constraint: Distance between top point of 0 (-240, 45) and top point of 6 (240, 45) is 480.
sketch_rails.addConstraint(Sketcher.Constraint("DistanceX", 0, 6, 480)) # Force outer width to 480

# Constraint: Distance between top point of 0 and top point of 2 is 40 (Rail width)
sketch_rails.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, 40))

# Constraint: Distance between top point of 4 and top point of 6 is 40 (Rail width)
sketch_rails.addConstraint(Sketcher.Constraint("
