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
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central through hole")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "Diameter of the mounting holes")
params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "Count of mounting holes")

# Set default values as per the prompt
params.outer_diameter = 125.4125
params.flange_thickness = 23.01875
params.bore_diameter = 28.971875
params.bolt_circle_diameter = 103.1875
params.mounting_hole_diameter = 13.49375
params.number_of_mounting_holes = 4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Main Flange Sketch (Outer Profile & Bore) ---
# Create the main sketch on the XY plane
main_sketch = body.newObject("Sketcher::SketchObject", "MainSketch")
main_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
main_sketch.ConstrainAuto = True
main_sketch.ConstrainAuto2D = True
main_sketch.MapMode = "FlatFace"
main_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
main_sketch.addGeometry(outer_circle, False)

# Add Bore Circle (Concentric)
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
main_sketch.addGeometry(bore_circle, False)

# Add Coincident Constraint (Center to Center)
# Note: Sketcher constraints in 1.1 use indices. 
# We need to ensure the circles are added in a way that allows easy constraint indexing or use explicit geometry references if possible.
# However, standard practice in scripts is often to add constraints by index if order is guaranteed, 
# or use the 'Coincident' constraint with specific geometry IDs.
# Let's rely on the fact that the first two added geometries are the circles.
# Geometry 0: Outer Circle, Geometry 1: Bore Circle.
# We constrain the center of the outer circle (0, 2) to the center of the bore circle (1, 1).
main_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))

# --- Pad Feature (Main Flange) ---
pad = body.newObject("PartDesign::Pad", "PadFlange")
pad.Profile = main_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
# Drive length from parameter
pad.setExpression("Length", "Parameters.flange_thickness")

# --- Bore Pocket ---
# Create a sketch for the hole on the top face of the pad
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
bore_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
bore_sketch.MapMode = "FlatFace"
bore_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add Bore Circle
bore_sketch.addGeometry(bore_circle, False)
# Constrain to center of pad (which is effectively the origin of the sketch plane relative to the body)
# Since the sketch is on the top face, we just need to ensure it's centered. 
# The sketch origin is at (0,0,thickness). The circle is at (0,0,thickness).
# We add a constraint to the center of the main sketch's outer circle to ensure alignment if needed, 
# but usually, creating the sketch on the face and centering the circle is sufficient.
# To be robust, let's constrain the center of this bore circle to the center of the main sketch's outer circle.
# We need to reference the main sketch geometry.
# Main sketch is at index 0 in the body.
bore_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center of Bore Circle (1,1) to Center of Outer Circle (0,2)

bore_pocket = body.newObject("PartDesign::Pocket", "PocketBore")
bore_pocket.Profile = bore_sketch
bore_pocket.Type = "ThroughAll"

# --- Mounting Holes Pattern ---
# Create a sketch for the mounting holes on the top face
mount_sketch = body.newObject("Sketcher::SketchObject", "MountSketch")
mount_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
mount_sketch.MapMode = "FlatFace"
mount_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add Mounting Hole Circle
mount_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.mounting_hole_diameter / 2.0)
mount_sketch.addGeometry(mount_circle, False)
# Constrain to center
mount_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))

# Create the Pocket for the single mounting hole
mount_pocket = body.newObject("PartDesign::Pocket", "PocketMountSingle")
mount_pocket.Profile = mount_sketch
mount_pocket.Type = "ThroughAll"

# Create the Polar Pattern
pattern = body.newObject("PartDesign::PolarPattern", "PatternMount")
pattern.Originals = [mount_pocket]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_of_mounting_holes
# Drive occurrences from parameter
pattern.setExpression("Occurrences", "Parameters.number_of_mounting_holes")

# --- Finalize ---
doc.recompute()

# --- Save ---
# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
