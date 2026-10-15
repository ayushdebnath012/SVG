import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration derived from task description ---
PARAMS = {
    "plate_thickness": 3.0,
    "hole_center_distance": 29.0,
    "head_outer_diameter": 7.0,
    "hole_diameter": 3.0,
    "shaft_width": 3.0
}

# --- Setup Document ---
doc = App.newDocument("ConnectingRod")

# 1. Create named parameters
params = doc.addObject("App::VarSet", "Parameters")
for name, value in PARAMS.items():
    params.addProperty(f"App::PropertyFloat", name, "Dimensions", name)
    params.setPropertyVisibility(name, True)
    setattr(params, name, value)

# 2. Define planes and axes for the Body
# We will create sketches on XY and XZ planes.
# XY_Plane (x, y) -> Thickness along Z
# XZ_Plane (x, z) -> Shaft profile

# Get standard planes/axes if they exist, otherwise create them in a hidden body or rely on default.
# In PartDesign, the Body usually attaches to existing planes or we create a dummy body for planes.
# However, standard practice in scriptable PartDesign is to attach to existing document planes if available.
# Let's ensure we have the standard planes.
# Note: In a fresh doc, XY_Plane, XZ_Plane, YZ_Plane might not exist. 
# We will create a dummy "Planes" body to hold them if they are missing, 
# or simply attach sketches to the XY and XZ planes defined in the document context.
# To be robust, let's create a dummy body to hold the coordinate system planes if the document is empty.
try:
    doc.getObject("XY_Plane")
    has_planes = True
except:
    has_planes = False

if not has_planes:
    planes_body = doc.addObject("PartDesign::Body", "Planes")
    # Add standard planes
    xy = planes_body.newObject("PartDesign::Plane", "XY_Plane")
    xy.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
    
    xz = planes_body.newObject("PartDesign::Plane", "XZ_Plane")
    xz.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(App.Vector(0, 1, 0))) # Rotate 90 deg around Y
    
    yz = planes_body.newObject("PartDesign::Plane", "YZ_Plane")
    yz.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(App.Vector(1, 0, 0))) # Rotate 90 deg around X

    z_axis = planes_body.newObject("PartDesign::Axis", "Z_Axis")
    z_axis.Placement = App.Placement(App.Vector(0,0,0))
    z_axis.Orientation = (0, 0, 1)

# 3. Create Main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Feature Construction ---

# STEP A: Create the main plate (Head1 - Shaft - Head2)
# We use the XY plane for the top-down view to draw the outline.
sketch_plate = body.newObject("Sketcher::SketchObject", "PlateSketch")
sketch_plate.Placement = App.Placement(App.Vector(0,0,0)) # XY plane
sketch_plate.Plane = doc.getObject("XY_Plane")

# Geometry for the profile on XY plane:
# Head 1 (Circle), Shaft (Rectangle), Head 2 (Circle)
# Center of Head 1 at (0,0). Center of Head 2 at (hole_center_distance, 0).

# Helper to get parameter
def get_param(name): return params[name]

# Head 1 Circle
head1_c = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), get_param("head_outer_diameter") / 2)
head2_c = Part.Circle(App.Vector(get_param("hole_center_distance"), 0, 0), App.Vector(0, 0, 1), get_param("head_outer_diameter") / 2)

# Shaft Rectangle: From x=0 to x=hole_center_distance, y = -width/2 to +width/2
# We construct lines manually.
# Line 1: Head1 Left to Shaft Left (0, -w/2) to (0, w/2) -> Actually coincident with circle edge? 
# Better: Draw the full rectangle for the shaft and then union/cut, or draw the specific shape.
# Let's draw the specific shape: 
# 1. Line from (-w/2, -w/2) to (head1_c.X_center - r, -w/2) ... this is getting complex.
# Simpler approach: Draw the shaft rectangle fully, then use Coincident/Horizontal constraints to align.
# Or simply draw the path: 
# (0, -w/2) -> (dist, -w/2) -> (dist, w/2) -> (0, w/2) -> (0, -w/2)
# And circles at ends.

shaft_width_half = get_param("shaft_width") / 2
center_x1 = 0
center_x2 = get_param("hole_center_distance")

# Points for the shaft rectangle corners
p1 = App.Vector(center_x1, -shaft_width_half, 0)
p2 = App.Vector(center_x2, -shaft_width_half, 0)
p3 = App.Vector(center_x2, shaft_width_half, 0)
p4 = App.Vector(center_x1, shaft_width_half, 0)

# Add geometries
sketch_plate.addGeometry(head1_c, False)
sketch_plate.addGeometry(head2_c, False)
sketch_plate.addGeometry(Part.LineSegment(p1, p2), False)
sketch_plate.addGeometry(Part.LineSegment(p2, p3), False)
sketch_plate.addGeometry(Part.LineSegment(p3, p4), False)
sketch_plate.addGeometry(Part.LineSegment(p4, p1), False)

# Constraints to lock the geometry relative to each other and origin
# 1. Origin constraints for Head 1
sketch_plate.addConstraint(Sketcher.Constraint("Axis", 0, 0, "XY", "X")) # Center X on X axis
sketch_plate.addConstraint(Sketcher.Constraint("Axis", 0, 0, "XY", "Y")) # Center Y on Y axis
sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 2, "XY", "X")) # Center of circle 0 on X axis (redundant but safe)
# Actually, let's use standard constraints.
# Constraint: Circle center at origin
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "X")) 
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "Y"))

# Constraint: Circle 1 tangent to Line 1 (Left of head1) - wait, the line starts at the circle edge?
# My points p1 and p4 are at x=0. The circle radius is R. So the circle extends to -R.
# The rectangle starts at 0. There is a gap.
# Correct approach: The shaft should connect to the *center* of the head, or the rectangle should start at -R?
# Usually, the shaft runs between the holes. The "Head" is the larger circle.
# Let's assume the shaft width is the distance between the inner faces of the heads? 
# No, "connected by a straight shaft".
# Let's make the rectangle start at -R (left edge of head1) and end at Dist + R (right edge of head2).
# Then the shaft_width is the y-extent.
# Let's redefine the rectangle points to match the circle radii.

R_head = get_param("head_outer_diameter") / 2
R_shaft = get_param("shaft_width") / 2 # Wait, shaft_width is usually the thickness of the bar, not radius.
# "shaft_width = 3.0 mm". This is the full width of the bar.
# So y goes from -1.5 to +1.5.

# Redefine points to align with Head centers
# Head 1 Center: (0,0). Head 1 Left Edge: (-R_head, 0).
# Head 2 Center: (Dist, 0). Head 2 Right Edge: (Dist + R_head, 0).
# Shaft Rectangle: x from -R_head to Dist + R_head. y from -R_shaft to +R_shaft.

p_start = App.Vector(-R_head, -R_shaft, 0)
p_end_left = App.Vector(-R_head, R_shaft, 0)
p_mid = App.Vector(get_param("hole_center_distance") + R_head, R_shaft, 0)
p_end_right = App.Vector(get_param("hole_center_distance") + R_head, -R_shaft, 0)
p_close = App.Vector(-R_head, -R_shaft, 0)

sketch_plate.removeGeometry(p1, p2, p3, p4) # Remove old lines
sketch_plate.addGeometry(Part.LineSegment(p_start, p_end_left), False)
sketch_plate.addGeometry(Part.LineSegment(p_end_left, p_mid), False)
sketch_plate.addGeometry(Part.LineSegment(p_mid, p_end_right), False)
sketch_plate.addGeometry(Part.LineSegment(p_end_right, p_close), False)

# Re-apply constraints for the new shape
# Head 1 at origin
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "X")) 
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "Y"))

# Head 2 center on X axis
sketch_plate.addConstraint(Sketcher.Constraint("Center", 1, 0, "XY", "X")) 
sketch_plate.addConstraint(Sketcher.Constraint("Center", 1, 1, "XY", "Y"))

# Distance between Head 1 and Head 2 centers
sketch_plate.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, get_param("hole_center_distance")))

# Shaft lines parallel to X axis
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 0, 3)) # Line 3 (p_end_left to p_mid) || Line 0 (p_start to p_end_left)? No.
# Let's just constrain the lines to be horizontal (Parallel to X axis)
# Line indices: 0: p_start->p_end_left (Vertical)
# 1: p_end_left->p_mid (Horizontal)
# 2: p_mid->p_end_right (Horizontal)
# 3: p_end_right->p_close (Vertical)
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 1, "XY", "X"))
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 2, "XY", "X"))

# Lines 0 and 3 parallel to Y axis
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 0, "XY", "Y"))
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 3, "XY", "Y"))

# Tangency: Line 1 tangent to Circle 0? 
# Line 1 starts at (-R_head, R_shaft). Circle 0 is at (0,0) radius R_head.
# They are not tangent. The rectangle cuts through the head if we are not careful.
# Actually, the prompt says "connected by a straight shaft". 
# Visually, this is usually a plate with two big circles and a bar in the middle.
# The bar width (shaft_width) is likely smaller than the head diameter.
# The bar runs between the heads. 
# Let's assume the bar is defined by the rectangle, and the heads are the circles.
# The rectangle x-range is [-R_head, Dist + R_head]. This overlaps the circles.
# This creates a solid block where the shaft is wider than the "neck" if the neck is just the distance between circles.
# But if we Pad this, we get a solid block.
# To make it look like a rod:
# 1. Pad the PlateSketch.
# 2. The heads are the circles. The shaft is the rectangle.
# The current construction creates a shape where the shaft is continuous with the heads.
# This is fine. It's a single piece.

# --- Create Through Holes ---
# We need to subtract holes on the heads.
# Head 1 is at (0,0). Head 2 is at (Dist, 0).
# Hole diameter is given.

# Hole Sketch 1
sketch_hole1 = body.newObject("Sketcher::SketchObject", "HoleSketch1")
sketch_hole1.Placement = App.Placement(App.Vector(0,0,0))
sketch_hole1.Plane = doc.getObject("XY_Plane")

hole_c1 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), get_param("hole_diameter") / 2)
sketch_hole1.addGeometry(hole_c1, False)
sketch_hole1.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "X"))
sketch_hole1.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "Y"))

# Hole Sketch 2
sketch_hole2 = body.newObject("Sketcher::SketchObject", "HoleSketch2")
sketch_hole2.Placement = App.Placement(App.Vector(get_param("hole_center_distance"), 0, 0))
sketch_hole2.Plane = doc.getObject("XY_Plane")

hole_c2 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), get_param("hole_diameter") / 2)
sketch_hole2.addGeometry(hole_c2, False)
sketch_hole2.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "X"))
sketch_hole2.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "Y"))

# --- Create the Solid Body ---

# 1. Pad the main plate
pad = body.newObject("PartDesign::Pad", "MainPad")
pad.Profile = sketch_plate
pad.Length = get_param("plate_thickness")
pad.MakeFullyConnected = True # Ensure no floating islands if any (though unlikely here)

# 2. Pocket the holes
pocket1 = body.newObject("PartDesign::Pocket", "Pocket1")
pocket1.Profile = sketch_hole1
pocket1.Type = "ThroughAll"
pocket1.CleanUp = True

pocket2 = body.newObject("PartDesign::Pocket", "Pocket2")
pocket2.Profile = sketch_hole2
pocket2.Type = "ThroughAll"
pocket2.CleanUp = True

# --- Finalize ---
doc.recompute()

# --- Save ---
script_dir = Path(__file__).resolve().parent
output_path = script_dir / "answer.FCStd"

# Save to the specific required path
doc.save(output_path)

print(f"Model saved to {output_path}")
