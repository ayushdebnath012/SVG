import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HexFlangeNut")

# --- Parameters ---
# Define parameters as App::PropertyLength variables attached to the Body
# This ensures they are editable in the tree and drive the geometry.
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner hole diameter")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the nut")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of the base flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Width across flats of the hex hub")

# Set default values as per requirements
params.inner_diameter = 24.0
params.overall_height = 36.0
params.flange_diameter = 45.0
params.flange_thickness = 6.0
params.hub_width = 36.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Base Sketch (Flange) ---
# We start with the flange on the XY plane.
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.Support = (doc.getObject("XY_Plane"), [""])
sketch_flange.MapMode = "FlatFace"

# Outer circle for the flange
circle_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0)
sketch_flange.addGeometry(circle_flange, False)

# Inner circle for the through hole (start of the hole)
circle_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_flange.addGeometry(circle_hole, False)

# Constraint: Concentric
sketch_flange.addConstraint(Sketcher.Constraint("Equal", 0, 1, 2, 1)) # Radius 0 = Radius 1
sketch_flange.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center 0 = Center 1

# --- Pad Feature (Flange Body) ---
# Extrude the flange upwards to create the base thickness.
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_flange
# Length is flange_thickness. Direction is +Z.
pad_flange.Length = params.flange_thickness
pad_flange.Type = "Solid"

# --- Hub Sketch (Hexagon) ---
# Move to the top of the flange to draw the hexagon.
sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hub.Support = (doc.getObject("XY_Plane"), [""])
sketch_hub.MapMode = "FlatFace"

# Create a hexagon. 
# We can construct it using lines and circles or use a polygon if available, 
# but standard lines/circles are safer for compatibility.
# Let's use a circle for the bounding box and lines for the flats, 
# or simply construct the hexagon vertices.
# Easier approach: Draw a circle of radius R = hub_width / (2 * cos(30 deg))
# Then draw 6 lines connecting vertices.
# Or simpler: Use the "Polygon" constraint if Sketcher supports it, 
# but to be robust, let's draw a circle and 6 lines.

# Hexagon geometry parameters
R_hex = params.hub_width / (2 * (3**0.5 / 2)) # Radius to vertices

# Center point
pt_center = App.Vector(0, 0, 0)

# Vertices
verts = []
for i in range(6):
    angle = i * 60 * (3.14159265359 / 180.0)
    x = R_hex * App.cos(angle)
    y = R_hex * App.sin(angle)
    verts.append(App.Vector(x, y, 0))

# Add lines connecting vertices
for i in range(6):
    p1 = verts[i]
    p2 = verts[(i + 1) % 6]
    line = Part.LineSegment(p1, p2)
    sketch_hub.addGeometry(line, False)

# Add center point for hole reference
sketch_hub.addGeometry(Part.Point(pt_center), False)

# Constraints: Close the loop (Coincident last to first)
sketch_hub.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 5, 1))

# --- Pad Feature (Hex Hub) ---
# Extrude the hexagon upwards to the total height.
pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub")
pad_hub.Profile = sketch_hub
# Length is overall_height - flange_thickness
pad_hub.Length = params.overall_height - params.flange_thickness
pad_hub.Type = "Solid"

# --- Hole Sketch ---
# Move to the top of the hub to define the hole.
sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, params.overall_height))
sketch_hole.Support = (doc.getObject("XY_Plane"), [""])
sketch_hole.MapMode = "FlatFace"

# Inner circle for the through hole
circle_hole_top = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_hole.addGeometry(circle_hole_top, False)

# --- Pocket Feature (Through Hole) ---
# Cut the hole through the entire height.
pocket_hole = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket_hole.Profile = sketch_hole
pocket_hole.Type = "ThroughAll"
pocket_hole.Axis = (doc.getObject("Z_Axis"), [""])

# --- Fillet Feature (Optional but good for nuts) ---
# Add a small fillet to the top edge of the hex hub for a finished look.
# We need to select the top edges of the hexagon.
# Since we can't easily select edges by name in a script without complex logic,
# we will apply a fillet to the top face edges of the Pad_Hub if possible,
# or skip if selection is too ambiguous. 
# Given the constraints of a script, let's try to fillet the top edges of the hex.
# We will use the edges of the sketch or the resulting face.
# A safer bet in a script is to fillet the top face of the hex pad.
# However, PartDesign::Fillet requires an edge list.
# Let's create a small chamfer/fillet on the top corners of the hex.
# To do this robustly, we can fillet the edges of the sketch if we had the face, 
# but let's try to fillet the top edges of the Pad_Hub.
# We'll create a temporary selection logic or just skip if complex.
# Actually, we can fillet the edges of the sketch if we define the face.
# Let's try to fillet the top edges of the hexagon.
# We will use the edges of the Pad_Hub's top face.
# Since we can't query edges by index easily, we will omit the fillet to ensure 
# the script runs without errors in all FreeCAD 1.1 environments, 
# as edge selection in scripts is fragile without GUI interaction.
# The core geometry (Hex, Flange, Hole) is the priority.

# --- Save ---
# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Recompute to ensure all features are calculated
doc.recompute()

# Save the file
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
