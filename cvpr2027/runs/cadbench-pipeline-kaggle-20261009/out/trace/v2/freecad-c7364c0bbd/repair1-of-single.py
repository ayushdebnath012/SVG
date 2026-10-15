import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("MountingFlange")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Body placement is optional in 1.1 if not explicitly needed for the feature tree logic, 
# but setting it ensures correct coordinate system context.
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central bore")
params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Set default values as per the prompt
params.outer_diameter = 69.453
params.flange_thickness = 13.097
params.bore_diameter = 34.925
params.pitch_circle_diameter = 57.944
params.bolt_hole_diameter = 6.747
params.number_bolt_holes = 4

# --- Step 1: Create the Base Flange (Pad) ---
# Create the base sketch for the flange profile
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Support = (doc.getObject("XY_Plane"), [])
base_sketch.ConstrainAuto = True
base_sketch.MapMode = "FlatFace"

# Add outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Add inner circle (for the bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
base_sketch.addGeometry(inner_circle, False)

# Add constraints to ensure concentricity
# Constraint: Concentric between the two circles
try:
    base_sketch.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 2))
except Exception:
    # Fallback if Concentric isn't supported in this specific context/version
    pass

# Create the Pad feature
pad = body.newObject("PartDesign::Pad", "FlangePad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False
pad.Reversed = False

# --- Step 2: Create the Central Bore (Pocket) ---
# Create a sketch for the central hole
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
# Lift the sketch to the top face of the flange
bore_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness / 2.0))
bore_sketch.Support = (doc.getObject("XY_Plane"), [])
bore_sketch.MapMode = "FlatFace"

# Add circle for the bore
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
bore_sketch.addGeometry(bore_circle, False)

# Create the Pocket feature
pocket = body.newObject("PartDesign::Pocket", "CentralBore")
pocket.Profile = bore_sketch
pocket.Type = "ThroughAll"
pocket.Clean = True

# --- Step 3: Create the Bolt Hole Pattern ---
# We need to create one bolt hole and then pattern it.
# First, create a sketch for a single bolt hole.
# The bolt circle is at Z = flange_thickness / 2.
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness / 2.0))
bolt_sketch.Support = (doc.getObject("XY_Plane"), [])
bolt_sketch.MapMode = "FlatFace"

# Add circle for the bolt hole
bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
bolt_sketch.addGeometry(bolt_circle, False)

# Create the single bolt hole pocket
bolt_hole = body.newObject("PartDesign::Pocket", "SingleBoltHole")
bolt_hole.Profile = bolt_sketch
bolt_hole.Type = "ThroughAll"
bolt_hole.Clean = True

# Create the Polar Pattern
pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
pattern.Originals = [bolt_hole]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
pattern.Distribute = True

# --- Finalize ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
