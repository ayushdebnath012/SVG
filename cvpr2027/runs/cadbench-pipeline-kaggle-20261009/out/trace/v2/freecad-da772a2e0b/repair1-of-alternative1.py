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
    setattr(params, name, value)

# 2. Define planes and axes for the Body
# We will create sketches on XY and XZ planes.
# In a fresh document, standard planes might not exist. We create a dummy body to hold them.
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

# Helper to get parameter
def get_param(name): return params[name]

# Head 1 Circle
head1_c = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), get_param("head_outer_diameter") / 2)
head2_c = Part.Circle(App.Vector(get_param("hole_center_distance"), 0, 0), App.Vector(0, 0, 1), get_param("head_outer_diameter") / 2)

# Shaft Rectangle: 
# The shaft connects the two heads. 
# We define the rectangle such that it spans from the left edge of Head 1 to the right edge of Head 2.
# x_start = -R_head, x_end = hole_center_distance + R_head
# y_start = -shaft_width/2, y_end = +shaft_width/2

R_head = get_param("head_outer_diameter") / 2
R_shaft = get_param("shaft_width") / 2
center_x1 = 0
center_x2 = get_param("hole_center_distance")

# Points for the shaft rectangle corners
p_start = App.Vector(-R_head, -R_shaft, 0)
p_end_left = App.Vector(-R_head, R_shaft, 0)
p_mid = App.Vector(center_x2 + R_head, R_shaft, 0)
p_end_right = App.Vector(center_x2 + R_head, -R_shaft, 0)
p_close = App.Vector(-R_head, -R_shaft, 0)

# Add geometries
sketch_plate.addGeometry(head1_c, False)
sketch_plate.addGeometry(head2_c, False)
sketch_plate.addGeometry(Part.LineSegment(p_start, p_end_left), False)
sketch_plate.addGeometry(Part.LineSegment(p_end_left, p_mid), False)
sketch_plate.addGeometry(Part.LineSegment(p_mid, p_end_right), False)
sketch_plate.addGeometry(Part.LineSegment(p_end_right, p_close), False)

# Constraints to lock the geometry relative to each other and origin
# 1. Origin constraints for Head 1
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "X")) 
sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 0, "XY", "Y"))

# 2. Head 2 center on X axis
sketch_plate.addConstraint(Sketcher.Constraint("Center", 1, 0, "XY", "X")) 
sketch_plate.addConstraint(Sketcher.Constraint("Center", 1, 1, "XY", "Y"))

# 3. Distance between Head 1 and Head 2 centers
sketch_plate.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, get_param("hole_center_distance")))

# 4. Shaft lines parallel to X axis (Lines 1 and 2)
# Line indices: 0: p_start->p_end_left (Vertical)
# 1: p_end_left->p_mid (Horizontal)
# 2: p_mid->p_end_right (Horizontal)
# 3: p_end_right->p_close (Vertical)
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 1, "XY", "X"))
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 2, "XY", "X"))

# 5. Lines 0 and 3 parallel to Y axis
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 0, "XY", "Y"))
sketch_plate.addConstraint(Sketcher.Constraint("Parallel", 3, "XY", "Y"))

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
pad.MakeFullyConnected = True

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
