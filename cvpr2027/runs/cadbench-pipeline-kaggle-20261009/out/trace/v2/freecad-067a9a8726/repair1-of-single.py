import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

# Initialize document
doc = App.newDocument("HexNut")

# --- Parameters ---
# Define a VarSet to hold editable parameters
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "through_hole_diameter", "Dimensions", "Diameter of the central through-hole")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the nut")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of the circular flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Width of the hexagonal drive")
params.addProperty("App::PropertyLength", "hex_head_height", "Dimensions", "Height of the hexagonal head")

# Set default values as per specification
params.through_hole_diameter = 18.0
params.overall_height = 27.0
params.flange_diameter = 34.0
params.flange_thickness = 5.0
params.hub_width = 27.0
params.hex_head_height = 22.0 # Calculated as 27.0 - 5.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange) ---
# Create sketch on XY plane at Z=0
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.ConstrainAuto = True
sketch_flange.TechDrawPictogramSequence = 1
sketch_flange.ViewObject.DisplayMode = "Flat"

# Add Circle for Flange
circle_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0)
sketch_flange.addGeometry(circle_flange, False)

# Add Center Point
point_center = Part.Point(App.Vector(0, 0, 0))
sketch_flange.addGeometry(point_center, False)

# Add Constraint: Coincident center (Point 0 to Point 1)
# Geometry indices: 0 is circle, 1 is point.
# Actually, addGeometry returns the geometry object, but we need indices for constraints.
# In headless, we usually rely on the order or explicit indices.
# Let's assume index 0 is the first added (circle), index 1 is the second (point).
# Constraint: Center of circle (0) at origin.
sketch_flange.addConstraint(Sketcher.Constraint("Center", 0, 0))

# --- Hex Profile Sketch ---
# Create sketch on XZ plane (rotated 90 deg around Y to stand up)
# We will place this sketch at Z = flange_thickness
sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hex.ConstrainAuto = True
sketch_hex.TechDrawPictogramSequence = 1
sketch_hex.ViewObject.DisplayMode = "Flat"

# Define Hexagon vertices
# Width = hub_width. Distance from center to flat side = hub_width / 2
# Distance from center to vertex = hub_width / (2 * cos(30)) = hub_width / sqrt(3)
R_hex = params.hub_width / (2 * math.sqrt(3))

# Add Center Point
point_hex = Part.Point(App.Vector(0, 0, 0))
sketch_hex.addGeometry(point_hex, False)

# Add Vertices
vertices = []
for i in range(6):
    angle = i * 60
    x = R_hex * math.cos(math.radians(angle))
    z = R_hex * math.sin(math.radians(angle))
    v = App.Vector(x, 0, z)
    vertices.append(v)
    sketch_hex.addGeometry(Part.Point(v), False)

# Add Lines connecting vertices
for i in range(6):
    p1 = vertices[i]
    p2 = vertices[(i + 1) % 6]
    sketch_hex.addGeometry(Part.LineSegment(p1, p2), False)

# Add Constraints
# 1. Center point is at origin (0,0)
sketch_hex.addConstraint(Sketcher.Constraint("Center", 0, 0))

# 2. All vertices are distance R_hex from center
# Geometry indices: 0=center, 1..6=vertices
for i in range(1, 7):
    sketch_hex.addConstraint(Sketcher.Constraint("Distance", 0, 1, i, 1, 0))

# 3. Adjacent vertices are distance R_hex apart (side length)
# Side length of regular hexagon with radius R is R.
for i in range(6):
    idx1 = i + 1
    idx2 = (i + 2) % 6 + 1
    sketch_hex.addConstraint(Sketcher.Constraint("Distance", idx1, 1, idx2, 1, 0))

# --- Through Hole Sketch ---
# Create sketch on XY plane at Z=0 (same as flange) to ensure hole goes through flange
sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hole.ConstrainAuto = True
sketch_hole.TechDrawPictogramSequence = 1
sketch_hole.ViewObject.DisplayMode = "Flat"

# Add Circle for Hole
circle_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2.0)
sketch_hole.addGeometry(circle_hole, False)

# Add Center Point
point_hole = Part.Point(App.Vector(0, 0, 0))
sketch_hole.addGeometry(point_hole, False)

# Add Constraint: Center
sketch_hole.addConstraint(Sketcher.Constraint("Center", 0, 0))

# --- Features ---

# 1. Pad Flange
# Profile: Sketch_Flange
# Length: flange_thickness
# Direction: +Z (upwards from Z=0)
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_flange
pad_flange.Length = params.flange_thickness
pad_flange.Type = "Solid"
pad_flange.MidPlane = False
pad_flange.Reversed = False

# 2. Pad Hex Head
# Profile: Sketch_Hex
# Length: hex_head_height
# Direction: +Z (upwards from Z=flange_thickness)
pad_hex = body.newObject("PartDesign::Pad", "Pad_Hex")
pad_hex.Profile = sketch_hex
pad_hex.Length = params.hex_head_height
pad_hex.Type = "Solid"
pad_hex.MidPlane = False
pad_hex.Reversed = False

# 3. Pocket Through Hole
# Profile: Sketch_Hole
# Length: overall_height (from Z=0 to Z=27)
# Type: ThroughAll is not needed if we specify Length, but let's use Length for precision.
# The hole needs to go through the flange (0-5) and the hex (5-27).
# So length = overall_height.
pocket_hole = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket_hole.Profile = sketch_hole
pocket_hole.Length = params.overall_height
pocket_hole.Type = "Solid"
pocket_hole.MidPlane = False
pocket_hole.Reversed = False

# --- Finalize ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")
doc.saveAs(str(output_path))
