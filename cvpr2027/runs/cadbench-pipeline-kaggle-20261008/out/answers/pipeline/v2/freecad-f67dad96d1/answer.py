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
params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Diameter of the central through hole")

# Set values as per specification
params.outer_diameter = 66.675
params.flange_thickness = 13.49375
params.pitch_circle_diameter = 53.18125
params.bolt_hole_diameter = 6.746875
params.number_bolt_holes = 4
params.inner_diameter = 25.4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange Profile) ---
# Create a sketch on the XY plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.ConstrainAuto = True
base_sketch.ConstrainToCurrent = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Add inner circle (for the through hole reference, though we will make a pocket later)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
base_sketch.addGeometry(inner_circle, False)

# Add constraints to ensure concentricity
base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center of outer coincident with center of inner
base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Center of outer coincident with origin (0,0)
base_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 1, 2)) # Center of inner coincident with origin (0,0)

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False
pad.Reversed = False

# --- Through Hole Pocket ---
# Create a sketch for the central hole on the top face of the pad
# We need to reference the top face of the pad. 
# Since we are building parametrically, we can create a sketch on the XY plane 
# and use a "ThroughAll" pocket, or create a sketch on the top face.
# Using ThroughAll on the XY plane is simpler and robust for a central hole.

hole_sketch = body.newObject("Sketcher::SketchObject", "HoleSketch")
hole_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
hole_sketch.ConstrainAuto = True
hole_sketch.ConstrainToCurrent = True
hole_sketch.MapMode = "FlatFace"
hole_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add circle for the through hole
hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
hole_sketch.addGeometry(hole_circle, False)

# Add constraints
hole_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Center coincident with origin
hole_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center coincident with outer circle center (redundant but safe)

pocket = body.newObject("PartDesign::Pocket", "ThroughHole")
pocket.Profile = hole_sketch
pocket.Type = "ThroughAll"
pocket.Base = (pad, ["Face1"]) # Ensure it cuts into the pad

# --- Bolt Hole Pattern ---
# We need to create a sketch for one bolt hole, then pattern it.
# The bolt holes are on a circle defined by pitch_circle_diameter.

bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
bolt_sketch.ConstrainAuto = True
bolt_sketch.ConstrainToCurrent = True
bolt_sketch.MapMode = "FlatFace"
bolt_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add circle for one bolt hole
bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
bolt_sketch.addGeometry(bolt_circle, False)

# Add constraints
bolt_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Center coincident with origin
bolt_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center coincident with outer circle center

# Create the pattern
# Note: In FreeCAD PartDesign, PolarPattern works on features. 
# We will pattern the pocket created from this sketch.
# However, the standard workflow is often: Sketch -> Pad/Pocket -> Pattern the feature.
# Let's create a pocket for the single bolt hole first.

bolt_pocket = body.newObject("PartDesign::Pocket", "BoltPocket")
bolt_pocket.Profile = bolt_sketch
bolt_pocket.Type = "ThroughAll"
bolt_pocket.Base = (pad, ["Face1"])

# Now pattern the pocket
pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
pattern.Originals = [bolt_pocket]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
pattern.Distribution = "Angle"
pattern.Radius = params.pitch_circle_diameter / 2.0

# --- Finalize ---
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
