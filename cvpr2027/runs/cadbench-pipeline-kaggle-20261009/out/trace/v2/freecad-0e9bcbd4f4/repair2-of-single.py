import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HexNut")

# --- Parameters ---
# Create a named object to hold parameters
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "hex_width_across_flats", "Dimensions", "Hex width across flats")
params.hex_width_across_flats = 17.0

params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Overall length of the nut")
params.overall_length = 30.0

params.addProperty("App::PropertyLength", "through_hole_diameter", "Dimensions", "Diameter of the central hole")
params.through_hole_diameter = 10.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Hexagon) ---
# Create a sketch on the XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
# Set placement correctly using App.Placement with a Vector
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.MapMode = "FlatFace"
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Calculate radius for circumcircle based on hex_width_across_flats
# R = W / (2 * cos(30)) = W / sqrt(3)
R = params.hex_width_across_flats / (2 * (3**0.5))

# Add 6 lines forming a hexagon
# Vertices angles: 30, 90, 150, 210, 270, 330 degrees (flats vertical)
lines = []
for i in range(6):
    angle = 30 + i * 60
    p1 = App.Vector(R * App.Vector.Cos(angle), R * App.Vector.Sin(angle), 0)
    p2 = App.Vector(-R * App.Vector.Cos(angle), -R * App.Vector.Sin(angle), 0)
    lines.append(Part.LineSegment(p1, p2))

for line in lines:
    sketch.addGeometry(line, False)

# Add constraints to make it a perfect hexagon centered at (0,0)
# 1. Coincident first vertex to origin
sketch.addConstraint(Sketcher.Constraint("Point", 0, "XY", 0, 0, 0))

# 2. Equal Length for all lines
for i in range(1, 6):
    sketch.addConstraint(Sketcher.Constraint("Length", i, i-1))

# 3. Equal Angle between adjacent lines (120 degrees)
sketch.addConstraint(Sketcher.Constraint("Angle", 0, 1, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 1, 2, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 2, 3, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 3, 4, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 4, 5, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 5, 0, 120))

# --- Hole Sketch ---
# Create a sketch on the XY plane for the hole profile
hole_sketch = body.newObject("Sketcher::SketchObject", "HoleSketch")
hole_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
hole_sketch.ConstrainAuto = True
hole_sketch.MapMode = "FlatFace"
hole_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add a circle with diameter = through_hole_diameter
hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2)
hole_sketch.addGeometry(hole_circle, False)

# --- Pad (Hex Body) ---
pad = body.newObject("PartDesign::Pad", "HexPad")
pad.Profile = sketch
pad.Length = params.overall_length
pad.Type = "Solid"
pad.Midplane = False
pad.Reversed = False

# --- Pocket (Through Hole) ---
pocket = body.newObject("PartDesign::Pocket", "ThroughHole")
pocket.Profile = hole_sketch
pocket.Type = "ThroughAll"
pocket.BaseFeature = pad

# --- Recompute ---
doc.recompute()

# --- Save ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
