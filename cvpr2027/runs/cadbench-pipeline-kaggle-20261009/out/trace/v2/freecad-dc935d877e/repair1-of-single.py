import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Drawer")

# --- Parameters ---
# We use App::VarSet to store named parameters that drive the geometry.
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Outer length")
params.addProperty("App::PropertyLength", "width", "Dimensions", "Outer width")
params.addProperty("App::PropertyLength", "height", "Dimensions", "Outer height")
params.addProperty("App::PropertyLength", "wall_thickness", "Dimensions", "Wall thickness")

# Set values
params.length = 500.0
params.width = 300.0
params.height = 150.0
params.wall_thickness = 20.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Bottom Face) ---
# Create the bottom face sketch on the XY plane
sketch_bottom = body.newObject("Sketcher::SketchObject", "SketchBottom")
sketch_bottom.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bottom.Support = (doc.getObject("XY_Plane"), [])
sketch_bottom.MapMode = "FlatFace"

# Define the outer rectangle
# Points: (0,0), (L,0), (L,W), (0,W)
# We will use LineSegments and constraints.
l1 = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.length, 0, 0))
l2 = Part.LineSegment(App.Vector(params.length, 0, 0), App.Vector(params.length, params.width, 0))
l3 = Part.LineSegment(App.Vector(params.length, params.width, 0), App.Vector(0, params.width, 0))
l4 = Part.LineSegment(App.Vector(0, params.width, 0), App.Vector(0, 0, 0))

sketch_bottom.addGeometry(l1, False)
sketch_bottom.addGeometry(l2, False)
sketch_bottom.addGeometry(l3, False)
sketch_bottom.addGeometry(l4, False)

# Add constraints to make it a perfect rectangle based on parameters
# Coincident points to form a loop
sketch_bottom.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # P0-P1
sketch_bottom.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # P1-P2
sketch_bottom.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # P2-P3
sketch_bottom.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1)) # P3-P0

# Horizontal length constraint
sketch_bottom.addConstraint(Sketcher.Constraint("Length", 0, 1, params.length))
# Vertical width constraint
sketch_bottom.addConstraint(Sketcher.Constraint("Length", 1, 2, params.width))
# Horizontal angle constraint
sketch_bottom.addConstraint(Sketcher.Constraint("Angle", 0, 1, 90))
# Vertical angle constraint
sketch_bottom.addConstraint(Sketcher.Constraint("Angle", 1, 2, 90))

# --- Outer Pad ---
pad_outer = body.newObject("PartDesign::Pad", "PadOuter")
pad_outer.Profile = sketch_bottom
pad_outer.Length = params.height
pad_outer.Type = "Solid"

# Recompute to create the solid and expose the top face
doc.recompute()

# --- Inner Cavity Sketch ---
# Get the top face of the outer pad to place the cavity sketch
pad_shape = pad_outer.Shape
top_face = None
max_z = -1e9
for face in pad_shape.Faces:
    if face.Placement.Z > max_z:
        max_z = face.Placement.Z
        top_face = face

if not top_face:
    raise Exception("Could not find top face on PadOuter")

# Create the cavity sketch on the top face
sketch_cavity = body.newObject("Sketcher::SketchObject", "SketchCavity")
sketch_cavity.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_cavity.Support = (top_face, [])
sketch_cavity.MapMode = "FlatFace"

# Define the inner rectangle
# The cavity is inset by wall_thickness from all sides.
# Inner Length = Outer Length - 2 * wall_thickness
# Inner Width = Outer Width - 2 * wall_thickness
inner_len = params.length - (2 * params.wall_thickness)
inner_wid = params.width - (2 * params.wall_thickness)

# Points for inner rectangle
# Center of outer rect is (L/2, W/2). 
# Inner rect starts at (L/2 - inner_len/2, W/2 - inner_wid/2)
center_x = params.length / 2.0
center_y = params.width / 2.0
start_x = center_x - inner_len / 2.0
start_y = center_y - inner_wid / 2.0

l1_in = Part.LineSegment(App.Vector(start_x, start_y, 0), App.Vector(start_x + inner_len, start_y, 0))
l2_in = Part.LineSegment(App.Vector(start_x + inner_len, start_y, 0), App.Vector(start_x + inner_len, start_y + inner_wid, 0))
l3_in = Part.LineSegment(App.Vector(start_x + inner_len, start_y + inner_wid, 0), App.Vector(start_x, start_y + inner_wid, 0))
l4_in = Part.LineSegment(App.Vector(start_x, start_y + inner_wid, 0), App.Vector(start_x, start_y, 0))

sketch_cavity.addGeometry(l1_in, False)
sketch_cavity.addGeometry(l2_in, False)
sketch_cavity.addGeometry(l3_in, False)
sketch_cavity.addGeometry(l4_in, False)

# Constraints for inner rectangle
sketch_cavity.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch_cavity.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
sketch_cavity.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1))
sketch_cavity.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1))

sketch_cavity.addConstraint(Sketcher.Constraint("Length", 0, 1, inner_len))
sketch_cavity.addConstraint(Sketcher.Constraint("Length", 1, 2, inner_wid))
sketch_cavity.addConstraint(Sketcher.Constraint("Angle", 0, 1, 90))
sketch_cavity.addConstraint(Sketcher.Constraint("Angle", 1, 2, 90))

# --- Inner Pocket ---
pocket_inner = body.newObject("PartDesign::Pocket", "PocketInner")
pocket_inner.Profile = sketch_cavity
pocket_inner.Type = "ThroughAll" # Cuts all the way through the top (which is open)

# --- Final Recompute ---
doc.recompute()

# --- Save ---
# Determine output path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Save the document
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
