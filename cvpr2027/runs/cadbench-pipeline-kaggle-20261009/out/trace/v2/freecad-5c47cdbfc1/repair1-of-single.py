import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("FlangePart")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# --- Parameters ---
# We will use App::PropertyLength and App::PropertyInteger for parameters
# to drive the geometry.

# Create a parameter container
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Diameter of the central bore")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Set default values
params.outer_diameter = 40.084
params.flange_thickness = 10.319
params.inner_diameter = 14.288
params.bolt_circle_diameter = 28.575
params.bolt_hole_diameter = 6.747
params.number_bolt_holes = 4

# --- Sketch 1: Flange Profile (Outer and Inner) ---
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
# Default placement is (0,0,0) with identity rotation. We just need to ensure it's set correctly.
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.Support = (doc.getObject("XY_Plane"), [])
sketch_flange.ConstrainAuto = True
sketch_flange.MapMode = "FlatFace"

# Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
sketch_flange.addGeometry(outer_circle, False)

# Inner Circle (Concentric)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_flange.addGeometry(inner_circle, False)

# Constraint: Concentric (Centers must coincide)
# Geometry 0 is outer circle, Geometry 1 is inner circle.
# Point 2 of circle 0 is center. Point 1 of circle 1 is center.
sketch_flange.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))

# Constraint: Outer diameter expression
sketch_flange.addConstraint(Sketcher.Constraint("Length", 0, 2, "Parameters.outer_diameter"))
# Constraint: Inner diameter expression
sketch_flange.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.inner_diameter"))

# --- Sketch 2: Bolt Hole Pattern ---
sketch_bolts = body.newObject("Sketcher::SketchObject", "Sketch_Bolts")
sketch_bolts.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bolts.Support = (doc.getObject("XY_Plane"), [])
sketch_bolts.ConstrainAuto = True
sketch_bolts.MapMode = "FlatFace"

# We need to create the bolt holes dynamically based on the number of holes.
# We will create a list of circles and add them to the sketch.
# First, let's create the first hole at (0,0) temporarily to establish the sketch, 
# then we will use a pattern feature to replicate it. 
# However, the pattern feature in PartDesign usually patterns a feature (like a Pocket), 
# not the sketch geometry itself directly in a way that creates multiple holes in one sketch 
# unless we use a loop or a specific pattern sketch method.
# 
# Alternative approach: Create one hole in the sketch, then use a PolarPattern on the Pocket feature.
# This is cleaner and more robust.

# Create one bolt hole circle
bolt_radius = params.bolt_hole_diameter / 2.0
bolt_circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_radius)
sketch_bolts.addGeometry(bolt_circle_geom, False)

# Constraint: Bolt hole diameter
sketch_bolts.addConstraint(Sketcher.Constraint("Length", 0, 2, "Parameters.bolt_hole_diameter"))

# --- Feature 1: Pad (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "Pad_Flange")
pad.Profile = sketch_flange
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False

# --- Feature 2: Pocket (Central Bore) ---
# PartDesign::Pocket takes a SketchObject as Profile. 
# If we use the same sketch, it will try to extrude the whole sketch (outer and inner).
# In FreeCAD PartDesign, if you assign a sketch with multiple closed loops to a Pad/Pocket,
# it treats the outermost loop as the profile and inner loops as holes automatically.
# So reusing sketch_flange for the pocket is correct! The inner circle will be cut out.

pocket_center = body.newObject("PartDesign::Pocket", "Pocket_Center")
pocket_center.Profile = sketch_flange
pocket_center.Type = "ThroughAll"

# --- Feature 3: Polar Pattern (Bolt Holes) ---
# We create a pocket for the single bolt hole first, then pattern it.
# But wait, the sketch_bolts only has one hole.
# Let's create a Pocket for that single hole.
pocket_bolt = body.newObject("PartDesign::Pocket", "Pocket_Bolt_Original")
pocket_bolt.Profile = sketch_bolts
pocket_bolt.Type = "ThroughAll"

# Now pattern this pocket
pattern = body.newObject("PartDesign::PolarPattern", "Pattern_Bolts")
pattern.Originals = [pocket_bolt]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
pattern.Distribution = "Angle"
pattern.DistributionAngle = 360.0 / params.number_bolt_holes

# --- Finalize ---
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().parent / "answer.FCStd"
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
