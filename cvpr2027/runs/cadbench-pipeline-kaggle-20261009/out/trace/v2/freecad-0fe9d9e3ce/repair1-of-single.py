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
# In FreeCAD 1.1, Placement is a PropertyPlacement, not a constructor call with arguments in this context
sketch_base.Placement = App.Placement() 
sketch_base.ConstrainToCurrentPlane = True
# Attach to XY plane
sketch_base.Support = (doc.getObject("XY_Plane"), [])

# Add geometry: Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
sketch_base.addGeometry(outer_circle, False)

# Add geometry: Inner Circle (Through Hole)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_base.addGeometry(inner_circle, False)

# Add constraints: Concentric
# Constraint 0,1 refers to geometry 0 (outer circle), constraint type Equal (radii)
# Constraint 1,2 refers to geometry 1 (inner circle)
sketch_base.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 2)) 
# Centers coincide
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) 

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "PadFlange")
pad.Profile = sketch_base
# Set length via expression to drive from parameter
pad.setExpression("Length", "Parameters.flange_thickness")
pad.Type = "Solid"
pad.MidPlane = False

# --- Bolt Hole Sketch ---
# Create a sketch on the top face of the flange to define bolt holes
sketch_bolt_single = body.newObject("Sketcher::SketchObject", "BoltHoleSketchSingle")
sketch_bolt_single.Placement = App.Placement()
sketch_bolt_single.ConstrainToCurrentPlane = True
# Attach to the top face of the pad
sketch_bolt_single.Support = (pad, ["Top"])

# Add geometry: Bolt Hole Circle (Single)
bolt_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
sketch_bolt_single.addGeometry(bolt_hole, False)

# --- Pocket Feature (Single Bolt Hole) ---
pocket_single = body.newObject("PartDesign::Pocket", "PocketBoltSingle")
pocket_single.Profile = sketch_bolt_single
pocket_single.Type = "ThroughAll"
pocket_single.Clearance = 0.0

# --- Polar Pattern ---
pattern = body.newObject("PartDesign::PolarPattern", "PatternBolts")
pattern.Originals = [pocket_single]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.setExpression("Angle", "360")
pattern.setExpression("Occurrences", "Parameters.number_bolt_holes")

# --- Final Recompute ---
doc.recompute()

# --- Save ---
# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
