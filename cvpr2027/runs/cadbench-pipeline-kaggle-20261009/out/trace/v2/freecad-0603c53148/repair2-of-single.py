import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("MountingFlange")

# --- Parameters ---
# Define a VarSet to hold the named parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central bore")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Set initial values as per the prompt
params.outer_diameter = 107.156
params.flange_thickness = 21.034
params.bore_diameter = 49.213
params.bolt_circle_diameter = 87.312
params.bolt_hole_diameter = 9.922
params.number_bolt_holes = 4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange Profile) ---
# Create a sketch on the XY plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement() # Default is (0,0,0)
base_sketch.ConstrainAuto = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Add inner circle (bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
base_sketch.addGeometry(inner_circle, False)

# Add constraints to ensure concentricity
# Constraint: Concentric between centers of outer and inner circles
base_sketch.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 2))

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False
pad.Reversed = False

# --- Bore Pocket ---
# Create a sketch for the bore on the top face of the pad
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
bore_sketch.Placement = App.Placement()
bore_sketch.ConstrainAuto = True
bore_sketch.MapMode = "FlatFace"
bore_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add circle for the bore
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
bore_sketch.addGeometry(bore_circle, False)

# Add constraint to center it (coincident with origin)
bore_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "XY"))
bore_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "X", 0))
bore_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "Y", 0))

# Create the pocket
pocket = body.newObject("PartDesign::Pocket", "BorePocket")
pocket.Profile = bore_sketch
pocket.Type = "ThroughAll"
pocket.Clean = True

# --- Bolt Hole Pattern ---
# We will create one hole and then pattern it.
# First, create a sketch for a single bolt hole on the top face.
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
bolt_sketch.Placement = App.Placement()
bolt_sketch.ConstrainAuto = True
bolt_sketch.MapMode = "FlatFace"
bolt_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add circle for the bolt hole
bolt_circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
bolt_sketch.addGeometry(bolt_circle_geom, False)

# Add constraints to center the hole
bolt_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "XY"))
bolt_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "X", 0))
bolt_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, "Y", 0))

# Create the single hole feature
bolt_hole = body.newObject("PartDesign::Pocket", "BoltHole")
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
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
