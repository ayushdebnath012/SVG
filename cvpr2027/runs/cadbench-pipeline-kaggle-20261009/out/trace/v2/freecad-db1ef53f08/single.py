import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("FlangeMount")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We use App::PropertyLength for simple numeric parameters.
# In FreeCAD 1.1, we can add properties directly to the Body or a VarSet.
# Adding to Body is straightforward for this scope.

# Define parameters with default values matching the prompt
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner bore diameter")
params.inner_diameter = 34.925

params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer flange diameter")
params.outer_diameter = 69.454

params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange thickness")
params.flange_thickness = 26.194

params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Bolt circle diameter")
params.pitch_circle_diameter = 57.547

params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Bolt hole diameter")
params.bolt_hole_diameter = 6.747

params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")
params.number_bolt_holes = 4

# --- Base Flange Sketch ---
# Create a sketch on the XY plane to define the outer profile and inner bore
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Support = (App.ActiveDocument.XY_Plane, [])
base_sketch.ConstrainToCurrentPlane = True
base_sketch.MapMode = "FlatFace"

# Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Inner Circle (Bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
base_sketch.addGeometry(inner_circle, False)

# Constraint: Concentric
base_sketch.addConstraint(Sketcher.Constraint("Equal", outer_circle, inner_circle, "Center"))

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "PadFlange")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False

# --- Bolt Hole Sketch ---
# Create a sketch on the XY plane (same plane as base) to define the bolt hole pattern
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltHoleSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
bolt_sketch.Support = (App.ActiveDocument.XY_Plane, [])
bolt_sketch.MapMode = "FlatFace"

# We need to create the holes dynamically based on the number of holes.
# Since we cannot loop in the sketch geometry creation easily without a loop,
# we will create the first hole and then use a Polar Pattern feature.
# However, the Polar Pattern feature in PartDesign works on PartDesign features (like Pockets),
# not directly on Sketcher geometry lines/circles in older versions, but in 1.1 it can pattern sketches.
# Actually, the standard robust way is:
# 1. Create a sketch with ONE hole.
# 2. Create a PartDesign::Pocket (or Hole) from that sketch.
# 3. Pattern the Pocket.
# 4. Delete the original Pocket if we want to keep the sketch clean, or just leave it.
# Let's do: Sketch -> Pocket -> Pattern(Pocket).

# Create the single bolt hole geometry
bolt_hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
bolt_sketch.addGeometry(bolt_hole_circle, False)

# --- Pocket Feature (Single Hole) ---
pocket = body.newObject("PartDesign::Pocket", "PocketBolt")
pocket.Profile = bolt_sketch
pocket.Type = "ThroughAll"
pocket.Clearance = 0.0

# --- Polar Pattern Feature ---
# Pattern the pocket around the Z axis
pattern = body.newObject("PartDesign::PolarPattern", "PatternBolts")
pattern.Originals = [pocket]
pattern.Axis = (App.ActiveDocument.Z_Axis, [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
pattern.Distribute = True

# --- Fillet Feature (Optional but good for mounting) ---
# Add a small fillet to the outer edge for better handling
# We need to select the outer edge of the pad.
# Since the pad is a solid, we can select the edge of the resulting shape.
# However, PartDesign::Fillet requires selecting edges from the Body's shape or specific features.
# Let's add a fillet to the outer cylindrical face edge.
# Note: Selecting edges programmatically can be tricky without knowing the exact edge index.
# A safer approach for a script is to skip the fillet if edge selection is ambiguous, 
# OR use a Chamfer/Fillet on the sketch if it were a face, but this is a 3D edge.
# Let's try to fillet the outer edge of the Pad.
# We will assume the outer edge is the first edge of the pad's shape if it's a simple cylinder.
# But to be safe and robust, we will omit the fillet if we can't guarantee the edge index, 
# or we can try to select the edge of the Pad feature.
# Let's attempt to fillet the outer edge of the Pad.
# We need to get the edge from the Pad.
# In FreeCAD 1.1, we can access edges via the shape of the feature.
# However, the most reliable way in a script without GUI is often to skip complex edge selection 
# unless we can query the shape.
# Let's try to add a fillet to the outer edge of the Pad.
# We will create a temporary selection or try to find the edge.
# Actually, let's just add a small fillet to the outer rim.
# We'll try to select the edge of the Pad.
# Note: This might fail if the topology is complex, but for a simple cylinder it should work.
# We will try to get the edge from the Pad's shape.
# Since we can't easily iterate shapes in headless mode without knowing indices, 
# we will skip the fillet to ensure the script runs perfectly without errors, 
# as the core requirement is the parametric feature tree. 
# (The prompt asks for "Fillet, Chamfer..." as examples, but the specific part description 
# doesn't explicitly mandate a fillet, just the holes and bore).

# --- Finalize ---
doc.recompute()

# Save the file
# The output path must be derived from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
