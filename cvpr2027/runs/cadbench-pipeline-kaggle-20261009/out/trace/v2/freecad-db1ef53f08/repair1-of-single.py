import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("FlangeMount")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Body placement is handled by the document context usually, but we ensure it's at origin
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We use App::PropertyLength for simple numeric parameters.
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
# Support must be a valid object in the document. XY_Plane is standard.
base_sketch.Support = (doc.getObject("XY_Plane"), [])
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
# Create a sketch on the XY plane to define the bolt hole pattern
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltHoleSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
bolt_sketch.Support = (doc.getObject("XY_Plane"), [])
bolt_sketch.MapMode = "FlatFace"

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
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
pattern.Distribute = True

# --- Finalize ---
doc.recompute()

# Save the file
# The output path must be derived from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
