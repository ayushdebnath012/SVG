import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HexNut")

# --- Parameters ---
# We use App::VarSet to create named, editable parameters within the document.
# This allows us to drive geometry with specific names as requested.
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
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstrainAuto = True
sketch.MapMode = "FlatFace"
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add a regular hexagon centered at (0,0)
# The distance from center to flat is hex_width_across_flats / 2
# The distance from center to vertex is hex_width_across_flats / (2 * cos(30))
# We will construct it using lines and constraints to ensure it scales correctly with the parameter.
# Alternatively, we can use a circle and a polygon, but explicit lines with constraints are robust.
# Let's use a circle as the base for the hexagon vertices to make it easy to constrain.
# Radius of circumcircle = hex_width_across_flats / (2 * cos(30 deg)) = hex_width_across_flats / sqrt(3)
# However, to strictly follow "driven by named document objects", we will define the geometry based on the parameter directly.

# Define the half-width (distance from center to flat)
# We'll create 6 lines forming a hexagon.
# Vertices angles: 0, 60, 120, 180, 240, 300 degrees.
# But standard hexagon orientation usually has flats vertical or horizontal.
# Let's assume flats are vertical (points at 0, 60, etc relative to flat-to-flat axis? No).
# Standard: Flat-to-flat distance is W. Radius R = W / (2 * cos(30)).
# Let's place vertices at angles 30, 90, 150, 210, 270, 330 so flats are vertical.
# Or 0, 60... so points are on X axis.
# Let's do points on X axis (0, 60, 120...) -> Flats are slanted.
# Let's do flats vertical: Angles 30, 90, 150, 210, 270, 330.
# Distance from center to vertex R = W / (2 * cos(30)) = W / sqrt(3).

R = params.hex_width_across_flats / (2 * (3**0.5))

# Add 6 lines
lines = []
for i in range(6):
    angle = 30 + i * 60
    p1 = App.Vector(R * App.Vector.Cos(angle), R * App.Vector.Sin(angle), 0)
    p2 = App.Vector(-R * App.Vector.Cos(angle), -R * App.Vector.Sin(angle), 0)
    lines.append(Part.LineSegment(p1, p2))

for i, line in enumerate(lines):
    sketch.addGeometry(line, False)

# Add constraints to make it a perfect hexagon and center it
# 1. Coincident all vertices to a center point (0,0,0)
# 2. Equal length for all lines
# 3. Equal angles (or perpendicularity between adjacent lines? No, 120 deg)
# Simpler: Coincident all 6 vertices to a single point (0,0,0) and constrain lengths equal.
# Actually, if we constrain all vertices to (0,0,0), they collapse.
# We need to constrain vertices to be equidistant from center and form a closed loop.
# Strategy:
# - Coincident V0 to (0,0,0) -> This fixes one point.
# - Equal Length for all 6 lines.
# - Equal Angle between adjacent lines (120 degrees).
# - Coincident V1 to V0? No.
# Let's use the standard approach:
# 1. Coincident V0 to (0,0,0).
# 2. Equal Length for all 6 segments.
# 3. Equal Angle between segment 0-1 and 1-2, etc. (120 deg).
# 4. Coincident V1 to V0? No, that makes a point.
# 5. Coincident V1 to a point on the circle?
# Better: 
# - Coincident V0 to (0,0,0).
# - Equal Length for all 6 segments.
# - Equal Angle between segment 0-1 and 1-2 (120 deg).
# - Equal Angle between segment 1-2 and 2-3 (120 deg)...
# - Coincident V1 to V0? No.
# - Coincident V1 to a point defined by angle?
# Let's try:
# - Coincident V0 to (0,0,0).
# - Equal Length for all 6 segments.
# - Equal Angle between segment 0-1 and 1-2 (120 deg).
# - Equal Angle between segment 1-2 and 2-3 (120 deg).
# - Equal Angle between segment 2-3 and 3-4 (120 deg).
# - Equal Angle between segment 3-4 and 4-5 (120 deg).
# - Equal Angle between segment 4-5 and 5-0 (120 deg).
# - Equal Angle between segment 5-0 and 0-1 (120 deg).
# This over-constrains if we also fix V0.
# Correct minimal set:
# 1. Coincident V0 to (0,0,0).
# 2. Equal Length for all 6 segments.
# 3. Equal Angle between segment 0-1 and 1-2 (120 deg).
# 4. Equal Angle between segment 1-2 and 2-3 (120 deg).
# 5. Equal Angle between segment 2-3 and 3-4 (120 deg).
# 6. Equal Angle between segment 3-4 and 4-5 (120 deg).
# 7. Equal Angle between segment 4-5 and 5-0 (120 deg).
# 8. Equal Angle between segment 5-0 and 0-1 (120 deg).
# This forces the shape to be a regular hexagon.

# Let's add the constraints
# Helper to get index in sketch geometry
def get_idx(obj, geom):
    return obj.GeometryIndex

# Vertices indices in sketch geometry (0 to 5)
# Lines indices (0 to 5)
# We need to reference vertices. Sketcher constraints use geometry index.
# Lines are 0-5. Vertices are 0-5.
# Line 0 connects V0 and V1.
# Line 1 connects V1 and V2.
# ...
# Line 5 connects V5 and V0.

# 1. Coincident V0 to (0,0,0)
sketch.addConstraint(Sketcher.Constraint("Point", 0, "XY", 0, 0, 0))

# 2. Equal Length for all lines
for i in range(6):
    if i == 0:
        sketch.addConstraint(Sketcher.Constraint("Length", 0))
    else:
        sketch.addConstraint(Sketcher.Constraint("Length", i, i-1))

# 3. Equal Angle between adjacent lines (120 degrees)
# Angle between Line 0 and Line 1
sketch.addConstraint(Sketcher.Constraint("Angle", 0, 1, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 1, 2, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 2, 3, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 3, 4, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 4, 5, 120))
sketch.addConstraint(Sketcher.Constraint("Angle", 5, 0, 120))

# --- Hole Sketch ---
# Create a sketch on the XY plane, offset slightly or same plane? 
# Usually, we create a hole sketch on the same plane as the base sketch to subtract from the pad.
# But PartDesign::Pocket can take a profile on a face.
# Let's create a separate sketch on the XY plane for the hole profile.
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
pocket.BaseFeature = pad # Explicitly link to the pad to ensure correct subtraction order

# --- Recompute ---
doc.recompute()

# --- Save ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
