import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("FlangePart")

# --- Parameters ---
# Define a VarSet to hold the named parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central through bore")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of individual bolt holes")
params.addProperty("App::PropertyInteger", "number_of_bolt_holes", "Dimensions", "Number of bolt holes")

# Set default values as per the prompt
params.outer_diameter = 125.4125
params.flange_thickness = 23.01875
params.bore_diameter = 64.690625
params.bolt_circle_diameter = 103.1875
params.bolt_hole_diameter = 13.49375
params.number_of_bolt_holes = 4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange Profile) ---
# Create a sketch on the XY plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.ConstrainAuto = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add geometry: Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Add geometry: Inner Circle (Bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
base_sketch.addGeometry(inner_circle, False)

# Add constraints: Concentric
base_sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1, 0, 1)) # Radii equal (concentric)
base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Centers coincident

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False
# Drive length from parameter
pad.setExpression("Length", "Parameters.flange_thickness")

# --- Bore Pocket ---
# Create a sketch for the bore on the top face of the pad
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
bore_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
bore_sketch.ConstrainAuto = True
bore_sketch.MapMode = "FlatFace"
bore_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add geometry: Bore Circle
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
bore_sketch.addGeometry(bore_circle, False)

# Add constraints: Center at origin
bore_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "XY"))
bore_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.bore_diameter / 2.0))

# Create the pocket
pocket = body.newObject("PartDesign::Pocket", "BorePocket")
pocket.Profile = bore_sketch
pocket.Type = "ThroughAll"
pocket.Clearance = 0.0

# --- Bolt Hole Pattern ---
# We need to create the first bolt hole sketch, then pattern it.
# The pattern axis is Z (perpendicular to flange).

# 1. Create the first bolt hole sketch
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
bolt_sketch.ConstrainAuto = True
bolt_sketch.MapMode = "FlatFace"
bolt_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add geometry: Bolt Hole Circle
bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
bolt_sketch.addGeometry(bolt_circle, False)

# Add constraints: Center at origin
bolt_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "XY"))
bolt_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.bolt_hole_diameter / 2.0))

# 2. Create the Pocket for the single bolt hole
bolt_pocket = body.newObject("PartDesign::Pocket", "BoltPocket")
bolt_pocket.Profile = bolt_sketch
bolt_pocket.Type = "ThroughAll"
bolt_pocket.Clearance = 0.0

# 3. Create the Polar Pattern
pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
pattern.Originals = [bolt_pocket]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_of_bolt_holes
pattern.Distribute = True
pattern.Reverse = False

# --- Finalize ---
doc.recompute()

# --- Save ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
