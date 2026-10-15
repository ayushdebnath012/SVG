import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration & Parameters ---
# Base Part Parameters
base_plate_length = 406.4
base_plate_width = 101.6
base_plate_thickness = 4.76
number_mounting_holes = 6
mounting_hole_diameter = 8.0
mounting_hole_column_spacing = 355.6
mounting_hole_outer_row_spacing = 63.5

# Edit/Target Parameters
number_hooks = 4
hook_spacing = 101.6
first_hook_origin_x = -152.4
hook_thickness = 25.4
hook_inner_radius = 19.05
hook_outer_radius = 25.4
hook_arc_angle_deg = 160
hook_arc_center_x = -27.78
hook_arc_center_y = -44.2
hook_main_length = 95.0
hook_upper_arm_length = 63.5
hook_upper_arm_angle_deg = 45
hook_bottom_arm_length = 38.1

# --- Document Setup ---
doc = App.newDocument("Part")
doc.Type = "Part"
# Ensure we are in a headless environment context, though App.newDocument works standalone.

# Create the single Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Helper Functions ---

def create_sketch(name, plane_ref, offset=0.0):
    """Creates a Sketcher::SketchObject attached to the body."""
    sketch = body.newObject("Sketcher::SketchObject", name)
    # Attachment: Plane + Offset + Axis (default is X)
    sketch.Placement = App.Placement(App.Vector(0, 0, offset))
    sketch.Support = (plane_ref, [App.Vector(1, 0, 0)]) # Default axis X
    sketch.MapMode = "Body"
    sketch.Constrain = False # We add constraints explicitly or let solver handle it
    sketch.Lifted = False
    return sketch

def add_line(sketch, p1, p2, constrained=False, constraint_type="Horizontal"):
    """Adds a line segment to the sketch and adds a constraint if requested."""
    sketch.addGeometry(Part.LineSegment(p1, p2), constrained)
    if constrained:
        sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
        sketch.addConstraint(Sketcher.Constraint("Fixed", 0, 0, p1.X, p1.Y, 0))

def add_circle(sketch, center, radius, constrained=False):
    """Adds a circle to the sketch."""
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), constrained)

def add_arc(sketch, center, radius1, radius2, angle1, angle2, constrained=False):
    """
    Adds a circular arc segment.
    Angle in degrees. 0 is +X, 90 is +Y.
    """
    from math import radians, cos, sin
    start_angle = angle1 * radians
    end_angle = angle2 * radians
    
    p1 = App.Vector(center.X + radius1 * cos(start_angle), center.Y + radius1 * sin(start_angle), 0)
    p2 = App.Vector(center.X + radius2 * cos(end_angle), center.Y + radius2 * sin(end_angle), 0)
    
    # For a simple arc, we construct a full circle and clip it, or use a specific geometry type.
    # FreeCAD Sketcher doesn't have a direct "Arc" geometry constructor in the same way as Part,
    # but we can use a circle and constrain points, or use a LineSegment chain.
    # However, the most robust way for "Arc" in a sketch is often approximating or using the 
    # specific geometry if available. 
    # Alternative: Use a Circle and constrain two points to lie on it and the radius.
    # But the prompt asks for concentric arcs. 
    # Let's use the standard approach: Create a circle, add constraints for the arc extent.
    # Actually, FreeCAD Sketcher supports "Circle" geometry. We can create a circle, 
    # but we need it to look like an arc.
    # The cleanest way in FreeCAD 1.1 headless for an arc segment is often to use a 
    # Circle and constrain specific points to be on the circle, then constrain those points 
    # to be on the lines radiating from center.
    
    # Simpler approach for scriptability:
    # We will create a full circle and then use constraints to fix the start and end points 
    # to specific angles, effectively creating an arc segment.
    circle = Part.Circle(center, App.Vector(0, 0, 1), radius1)
    sketch.addGeometry(circle, constrained)
    
    # Constraint start point
    sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "XY", p1.X, p1.Y))
    # Constraint end point
    sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "XY", p2.X, p2.Y))
    # Constraint Center
    sketch.addConstraint(Sketcher.Constraint("Center", 0, 2, center.X, center.Y))
    # Constraint Radius
    sketch.addConstraint(Sketcher.Constraint("Radius", 0, 2, radius1))
    
    return p1, p2

def add_curve(sketch, center, radius1, radius2, angle1, angle2):
    """
    Adds a continuous curve of two concentric arcs connected by a tangent line segment?
    No, the prompt says: "Sweep both arcs... then join those endpoints tangentially to a straight bar".
    This implies the arc is one feature, then a line connects to it.
    Wait, "Sweep both arcs ... then join those endpoints tangentially to a straight bar".
    This describes the hook profile.
    Profile: 
    1. Bottom arm (straight)
    2. Inner arc (concave?) -> Outer arc (convex?)
    3. Main length (straight)
    4. Upper arm (angled)
    5. Cap
    
    Let's break down the hook profile geometry on a 2D sketch plane.
    The hook hangs down.
    Let's define the profile coordinates relative to a local sketch.
    """
    pass

# --- Step 1: Build Base Part ---

# 1. Base Plate Sketch
sketch_plate = create_sketch("PlateSketch", body, 0.0)
# Center of plate
sketch_plate.Placement = App.Placement(App.Vector(0, 0, 0))
# Outer rectangle
rect_p1 = App.Vector(-base_plate_length/2, -base_plate_width/2, 0)
rect_p2 = App.Vector(base_plate_length/2, base_plate_width/2, 0)
# Add rectangle via lines
sketch_plate.addGeometry(Part.LineSegment(rect_p1, App.Vector(rect_p1.X, rect_p2.Y, 0)), False)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(rect_p1.X, rect_p2.Y, 0), rect_p2), False)
sketch_plate.addGeometry(Part.LineSegment(rect_p2, App.Vector(rect_p2.X, rect_p1.Y, 0)), False)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(rect_p2.X, rect_p1.Y, 0), rect_p1), False)
# Constraints
sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center on origin? 
# Actually, let's constrain center to origin
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 2, 0, 0)) # This constrains the circle? No, for lines it's hard.
# Better: Constrain midpoints or use a circle at center.
# Let's use a circle at center to anchor, then draw box.
sketch_plate.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 100), False)
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 2, 0, 0))
sketch_plate.addConstraint(Sketcher.Constraint("Radius", 0, 2, 100))
# Box constraints
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 3))
sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 0, 2))
sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 0, 3))

# 2. Mounting Holes Sketch
# We need to place 6 holes.
# Layout: 2 columns. 
# Col spacing: 355.6
# Outer row spacing: 63.5 (from center)
# So X positions: +/- 355.6 / 2 = +/- 177.8
# Y positions: 0, +/- 63.5
# Wait, "one hole on the horizontal centerline". So Y=0 is one row.
# "Upper/lower pair". So Y = +63.5, Y = -63.5.
# Total holes: 2 cols * 3 rows = 6. Correct.

sketch_holes = create_sketch("HolesSketch", body, 0.0)
sketch_holes.Placement = App.Placement(App.Vector(0, 0, 0))

hole_positions = []
col_x = mounting_hole_column_spacing / 2.0
for y in [0, mounting_hole_outer_row_spacing, -mounting_hole_outer_row_spacing]:
    for col in [-1, 1]:
        cx = col * col_x
        cy = y
        hole_positions.append((cx, cy))

for i, (cx, cy) in enumerate(hole_positions):
    # Add circle
    sketch_holes.addGeometry(Part.Circle(App.Vector(cx, cy, 0), App.Vector(0, 0, 1), mounting_hole_diameter/2), False)
    # Constrain to position
    sketch_holes.addConstraint(Sketcher.Constraint("Point", i, 2, "XY", cx, cy))
    sketch_holes.addConstraint(Sketcher.Constraint("Radius", i, 2, mounting_hole_diameter/2))
    sketch_holes.addConstraint(Sketcher.Constraint("Center", i, 2, cx, cy))

# 3. Base Pad
pad = body.newObject("PartDesign::Pad", "BasePad")
pad.Profile = sketch_plate
pad.Length = base_plate_thickness
pad.Type = "Solid"
pad.Reversed = False
pad.Midplane = False
pad.makeFullyRigid = True

# 4. Base Holes (Through All)
# Since we have holes sketch, we can use Pocket or Hole feature.
# Hole feature is better for threaded holes, Pocket for simple through holes.
# Let's use Pocket with the holes sketch.
pocket = body.newObject("PartDesign::Pocket", "MountingHoles")
pocket.Profile = sketch_holes
pocket.Type = "ThroughAll"
pocket.MakeFullyRigid = True
pocket.Clearance = 0.0

doc.recompute()

# Save Base Part
script_path = Path(__file__).resolve()
base_filename = script_path.with_name(f"{script_path.stem}_base.FCStd")
doc.saveAs(str(base_filename))

# --- Step 2: Apply Edit (Add Hooks) ---
# We need to add hooks to the existing body.
# The hooks are "J-profile".
# We need to create a sketch for one hook profile.
# Then use a Pad (or multiple pads) to extrude them.
# The prompt says: "Start the first hook at first_hook_origin_x and repeat the hooks along the plate length at hook_spacing."
# This implies a linear pattern.

# Hook Profile Definition:
# The hook hangs off the plate.
# Let's define the sketch plane. The plate is on XY. The hook extrudes in Z (or -Z).
# Let's use the Front View (XZ plane) for the hook profile sketch, attached to the body.
# We need to position the sketch such that the hook is placed correctly relative to the plate.
# The plate center is (0,0,0).
# The hooks are arranged along X.
# First hook X = first_hook_origin_x = -152.4
# Hook spacing = 101.6
# There are 4 hooks.
# We will create ONE sketch profile for the hook shape.
# Then we will use a Pad to extrude it.
# To pattern it, we might need to pad multiple times or use a linear pattern on the body.
# However, the profile sketch is 2D. If we extrude it, it creates a 3D feature.
# If we want to pattern the feature, we can use PartDesign::LinearPattern.
# But the LinearPattern needs the "Profile" to be the 3D shape, not the sketch.
# So:
# 1. Create sketch for hook profile.
# 2. Extrude it once (Pad) to create the first hook instance.
# 3. Use LinearPattern to copy that Pad feature along X.

# --- Hook Profile Geometry ---
# Coordinate system for the hook sketch:
# Let's assume the hook's "back" (flat strap) is along the Y-axis of the sketch.
# The hook hangs down (negative Z in global, or positive Z in local if we orient correctly).
# Let's define the hook profile in a local sketch.
# 
# Key dimensions:
# hook_thickness = 25.4 (Width of the flat strap)
# hook_arc_center_x = -27.78
# hook_arc_center_y = -44.2
# hook_inner_radius = 19.05
# hook_outer_radius = 25.4
# hook_arc_angle = 160 deg
# hook_main_length = 95.0
# hook_upper_arm_length = 63.5
# hook_upper_arm_angle = 45 deg
# hook_bottom_arm_length = 38.1

# Let's construct the path of the hook profile.
# We need to define points in the sketch plane (let's call it U, V).
# Let's align the hook such that the flat strap is vertical in the sketch (along V axis).
# The hook hangs "forward" (along U axis).
#
# The arc is defined by center (cx, cy) relative to the hook base?
# The prompt says: "centered at hook_arc_center_x and hook_arc_center_y".
# These are global coordinates? Or relative to the hook's local coordinate system?
# Given the values (-27.78, -44.2), these look like global coordinates relative to the plate center.
# Wait, the plate is 406x101. The hook is ~25 wide.
# If the hook is placed at X=-152.4.
# The arc center X is -27.78.
# Distance from hook back (-152.4) to arc center X (-27.78) = 124.62.
# This seems large.
# Let's re-read carefully: "Start the first hook at first_hook_origin_x ... centered at hook_arc_center_x".
# This implies hook_arc_center_x is the X coordinate of the arc center in the GLOBAL coordinate system.
# But what about Y? The hook has thickness 25.4.
# The arc center Y is -44.2.
#
# Let's try to reconstruct the shape based on these global coords.
# Hook 1 is at X = -152.4.
# The hook has thickness 25.4. So it spans X from -152.4 to -152.4 + 25.4 = -127.0.
# The arc center is at X = -27.78. This is NOT inside the hook's X range.
# This suggests the "hook_arc_center_x" might be relative to the hook's local origin, OR the hook is placed differently.
# OR, the "first_hook_origin_x" is the position of the hook's FEATURE in the pattern, but the geometry is defined locally.
#
# Let's reconsider the description: "Start the first hook at first_hook_origin_x".
# Usually, this means the base of the hook (the back) is at that X.
# If the arc center is at -27.78, and the hook is at -152.4, the arc is far to the right (towards the center of the plate).
# This makes sense for a "J-hook" that curls around something or holds an object.
# But the hook thickness is 25.4.
# If the hook is at X=-152.4 to -127.0.
# And the arc center is at X=-27.78.
# Then the arc is a large curve sweeping from the hook tip towards the center.
#
# Let's build the profile in a sketch.
# We need a sketch plane. Let's use the YZ plane attached to a specific X, or just create a sketch on the XY plane and extrude in Z?
# No, the hook is a 3D object.
# Best approach: 
# 1. Create a sketch on a plane perpendicular to the plate (e.g., XZ plane).
# 2. Draw the profile of the hook (Side view).
# 3. Extrude this profile along the Y-axis (thickness direction) to create the "block" of the hook.
# 4. Then we need to position this block at X = -152.4.
#
# Wait, the hook has a specific "thickness" (25.4). This is likely the dimension along the plate surface (Y-axis in our main sketch, or Z-axis
