import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("MountingFlange")

# --- Parameters ---
# Define a VarSet to hold the named parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Central hole diameter")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Flange outer diameter")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange thickness")
params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Bolt circle diameter")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Bolt hole diameter")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Count of bolt holes")

# Set the values as requested
params.inner_diameter = 34.925
params.outer_diameter = 69.454
params.flange_thickness = 13.097
params.pitch_circle_diameter = 56.356
params.bolt_hole_diameter = 6.747
params.number_bolt_holes = 4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange Profile) ---
# Create the main sketch for the flange body
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.ConstrainToCurrentPlane = True
sketch_base.Support = (doc.getObject("XY_Plane"), [])

# Add geometry: Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
sketch_base.addGeometry(outer_circle, False)

# Add geometry: Inner Circle (Through Hole)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_base.addGeometry(inner_circle, False)

# Add constraints: Concentric
sketch_base.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 2)) # Radius of outer = Radius of inner (concentric)
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Centers coincide

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "PadFlange")
pad.Profile = sketch_base
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False
# Drive length from parameter
pad.setExpression("Length", "Parameters.flange_thickness")

# --- Bolt Hole Sketch ---
# Create a sketch on the top face of the flange to define bolt holes
sketch_bolt = body.newObject("Sketcher::SketchObject", "BoltHoleSketch")
sketch_bolt.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness / 2.0))
sketch_bolt.ConstrainToCurrentPlane = True
# Attach to the top face of the pad
sketch_bolt.Support = (pad, ["Top"])

# Add geometry: Bolt Circle
bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_circle_diameter / 2.0)
sketch_bolt.addGeometry(bolt_circle, False)

# Add geometry: Bolt Hole Circle
bolt_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
sketch_bolt.addGeometry(bolt_hole, False)

# Add constraints: Concentric
sketch_bolt.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 2))
sketch_bolt.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2))

# --- Bolt Hole Pattern ---
# We will create one pocket for the bolt hole and pattern it.
# Note: In PartDesign, patterns usually work on features. 
# To make it fully parametric and editable, we create one pocket feature and then pattern it.
# However, standard PartDesign::PolarPattern patterns the feature itself.
# We need to create the pocket first.

# Create a temporary sketch for the single bolt hole if needed, or reuse the geometry logic.
# Actually, the cleanest way in PartDesign for a pattern of holes is:
# 1. Create a sketch with ONE hole.
# 2. Create a Pocket from that sketch.
# 3. Create a PolarPattern of that Pocket.

# Let's refine the Bolt Hole Sketch to contain only ONE hole centered at origin.
sketch_bolt_single = body.newObject("Sketcher::SketchObject", "BoltHoleSketchSingle")
sketch_bolt_single.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness / 2.0))
sketch_bolt_single.ConstrainToCurrentPlane = True
sketch_bolt_single.Support = (pad, ["Top"])

# Add geometry: Bolt Hole Circle (Single)
sketch_bolt_single.addGeometry(bolt_hole, False)
# No constraints needed for a single centered hole on a sketch attached to a face, 
# but let's ensure it's centered relative to the sketch origin which is on the face center.

# --- Pocket Feature (Single Bolt Hole) ---
pocket_single = body.newObject("PartDesign::Pocket", "PocketBoltSingle")
pocket_single.Profile = sketch_bolt_single
pocket_single.Type = "ThroughAll"
pocket_single.Clearance = 0.0

# --- Polar Pattern ---
pattern = body.newObject("PartDesign::PolarPattern", "PatternBolts")
pattern.Originals = [pocket_single]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
# Drive occurrences from parameter
pattern.setExpression("Occurrences", "Parameters.number_bolt_holes")

# --- Final Recompute ---
doc.recompute()

# --- Save ---
# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
