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
# We use App::PropertyLength and App::PropertyInteger for the parameters.
# In FreeCAD 1.1, we can add these directly to the Body or a VarSet.
# Adding to Body is standard for simple parametric models.

# Define parameters with default values matching the prompt
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "flange_outer_diameter", "Dimensions", "Outer diameter of the flange")
params.flange_outer_diameter = 107.156

params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.flange_thickness = 21.034

params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central bore")
params.bore_diameter = 49.213

params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.bolt_circle_diameter = 87.313

params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.bolt_hole_diameter = 9.922

params.addProperty("App::PropertyInteger", "number_of_bolt_holes", "Dimensions", "Number of bolt holes")
params.number_of_bolt_holes = 4

# --- Feature 1: Base Flange (Pad) ---
# Create a sketch for the outer profile
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [])
sketch_base.MapMode = "FlatFace"

# Add outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_outer_diameter / 2.0)
sketch_base.addGeometry(outer_circle, False)

# Add inner circle (for the bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
sketch_base.addGeometry(inner_circle, False)

# Add concentric constraint
sketch_base.addConstraint(Sketcher.Constraint("Equal", 0, 1, 0, 1)) # Radius equality implies concentricity here since centers are same
# Explicitly constrain centers to origin to ensure concentricity
sketch_base.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane", "X", 0))
sketch_base.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane", "Y", 0))
sketch_base.addConstraint(Sketcher.Constraint("Point", 1, "XY_Plane", "X", 0))
sketch_base.addConstraint(Sketcher.Constraint("Point", 1, "XY_Plane", "Y", 0))

# Pad the base flange
pad = body.newObject("PartDesign::Pad", "PadFlange")
pad.Profile = sketch_base
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False

# --- Feature 2: Central Bore (Pocket) ---
# Create a sketch for the bore (already exists in BaseSketch, but we need a separate feature)
# Actually, we can reuse the sketch geometry if we define a new sketch object or just use the existing one with a different feature.
# To keep it clean and editable, let's create a specific sketch for the bore if needed, 
# but since the bore is concentric, we can just use the existing sketch_base and a Pocket feature.
# However, the prompt asks for a feature tree. Let's create a specific sketch for the bore to be explicit.

sketch_bore = body.newObject("Sketcher::SketchObject", "BoreSketch")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bore.Support = (doc.getObject("XY_Plane"), [])
sketch_bore.MapMode = "FlatFace"

# Add inner circle (bore)
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
sketch_bore.addGeometry(bore_circle, False)

# Constrain center
sketch_bore.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane", "X", 0))
sketch_bore.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane", "Y", 0))

# Pocket the bore
pocket_bore = body.newObject("PartDesign::Pocket", "PocketBore")
pocket_bore.Profile = sketch_bore
pocket_bore.Type = "ThroughAll"

# --- Feature 3: Bolt Hole Pattern ---
# Create a sketch for the bolt hole
sketch_bolt = body.newObject("Sketcher::SketchObject", "BoltSketch")
sketch_bolt.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bolt.Support = (doc.getObject("XY_Plane"), [])
sketch_bolt.MapMode = "FlatFace"

# Add bolt hole circle
bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
sketch_bolt.addGeometry(bolt_circle, False)

# Constrain center
sketch_bolt.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane", "X", 0))
sketch_bolt.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane", "Y", 0))

# Create a single instance of the bolt hole
bolt_instance = body.newObject("PartDesign::Pocket", "BoltHoleInstance")
bolt_instance.Profile = sketch_bolt
bolt_instance.Type = "ThroughAll"

# Create the Polar Pattern
pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
pattern.Originals = [bolt_instance]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_of_bolt_holes
pattern.Distribution = "Angle"

# --- Finalize ---
doc.recompute()

# Save the file
# The output path must be derived from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
