import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from task description
D = 50.0          # smooth_shaft_diameter
L = 80.0          # smooth_shaft_length
KW_W = 5.0        # keyway_width
KW_D = 5.0        # keyway_depth
KW_H = 20.0       # keyway_height
N_KW = 2          # num_keyway

# --- Setup Document ---
doc = App.newDocument("Shaft")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We will use expressions in the features to drive geometry from variables 
# defined in the Body's properties or via App::PropertyString variables.
# To ensure editability and named objects, we create a VarSet.
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "shaft diameter")
params.diameter = D
params.addProperty("App::PropertyLength", "length", "Dimensions", "shaft length")
params.length = L
params.addProperty("App::PropertyLength", "kw_width", "Dimensions", "keyway width")
params.kw_width = KW_W
params.addProperty("App::PropertyLength", "kw_depth", "Dimensions", "keyway depth")
params.kw_depth = KW_D
params.addProperty("App::PropertyLength", "kw_height", "Dimensions", "keyway height")
params.kw_height = KW_H
params.addProperty("App::PropertyInteger", "num_keyways", "Dimensions", "number of keyways")
params.num_keyways = N_KW

# --- Base Shaft Construction ---
# 1. Create Base Sketch (Circle)
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [])
sketch_base.MapMode = "FlatFace"

# Add Circle
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.diameter.Value)
sketch_base.addGeometry(circle, False)

# Add Constraints (Centered)
# Constraint: Center of circle to origin (0,0)
# In Sketcher, we can use "Center" constraint or "PointOnObject" with a point.
# Using "Center" constraint relative to the plane origin is standard.
sketch_base.addConstraint(Sketcher.Constraint("Center", 0, 0))

# 2. Pad the Shaft
pad_shaft = body.newObject("PartDesign::Pad", "PadShaft")
pad_shaft.Profile = sketch_base
# Length driven by parameter
pad_shaft.setExpression("Length", "Parameters.length")
pad_shaft.Length = L
pad_shaft.Type = "Solid"

# --- Keyway Construction ---
# We need to create N keyways. We will create one "Original" keyway feature 
# and then pattern it.
# Keyway geometry: A rectangular cut. 
# Orientation: The keyway is usually cut along the length of the shaft.
# The sketch for the keyway will be on a plane perpendicular to the shaft axis (XY plane).
# The cut will be a rectangle defined by width and depth.

# 1. Create Keyway Sketch
sketch_kw = body.newObject("Sketcher::SketchObject", "KeywaySketch")
sketch_kw.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_kw.Support = (doc.getObject("XY_Plane"), [])
sketch_kw.MapMode = "FlatFace"

# Define the rectangle for the keyway
# The keyway is centered on the shaft axis.
# Width = KW_W, Depth = KW_D.
# Rectangle corners: (-W/2, -D/2), (W/2, -D/2), (W/2, D/2), (-W/2, D/2)
kw_w_half = params.kw_width.Value / 2.0
kw_d_half = params.kw_depth.Value / 2.0

# Line 1: Bottom
line1 = Part.LineSegment(App.Vector(-kw_w_half, -kw_d_half, 0), App.Vector(kw_w_half, -kw_d_half, 0))
sketch_kw.addGeometry(line1, False)
# Line 2: Right
line2 = Part.LineSegment(App.Vector(kw_w_half, -kw_d_half, 0), App.Vector(kw_w_half, kw_d_half, 0))
sketch_kw.addGeometry(line2, False)
# Line 3: Top
line3 = Part.LineSegment(App.Vector(kw_w_half, kw_d_half, 0), App.Vector(-kw_w_half, kw_d_half, 0))
sketch_kw.addGeometry(line3, False)
# Line 4: Left
line4 = Part.LineSegment(App.Vector(-kw_w_half, kw_d_half, 0), App.Vector(-kw_w_half, -kw_d_half, 0))
sketch_kw.addGeometry(line4, False)

# Constraints:
# 1. Horizontal lines must be horizontal (Angle 0 or 180)
# 2. Vertical lines must be vertical (Angle 90 or 270)
# 3. Opposite sides parallel
# 4. Centered on origin
# 5. Dimensions

# Horizontal constraints
sketch_kw.addConstraint(Sketcher.Constraint("Angle", 0, 1, 0, 180)) # Line 1 horizontal
sketch_kw.addConstraint(Sketcher.Constraint("Angle", 2, 3, 0, 180)) # Line 3 horizontal
# Vertical constraints
sketch_kw.addConstraint(Sketcher.Constraint("Angle", 1, 2, 0, 90)) # Line 2 vertical
sketch_kw.addConstraint(Sketcher.Constraint("Angle", 3, 4, 0, 90)) # Line 4 vertical

# Center constraints
sketch_kw.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Line 1 center
sketch_kw.addConstraint(Sketcher.Constraint("Center", 2, 0)) # Line 3 center
sketch_kw.addConstraint(Sketcher.Constraint("Center", 1, 0)) # Line 2 center
sketch_kw.addConstraint(Sketcher.Constraint("Center", 3, 0)) # Line 4 center

# Dimension constraints
# Width
sketch_kw.addConstraint(Sketcher.Constraint("Length", 0, 1, params.kw_width.Value))
# Depth
sketch_kw.addConstraint(Sketcher.Constraint("Length", 1, 2, params.kw_depth.Value))

# 2. Create the Pocket Feature (The Original Keyway)
pocket_kw = body.newObject("PartDesign::Pocket", "PocketKeyway")
pocket_kw.Profile = sketch_kw
pocket_kw.Type = "Blind"
# The depth of the cut is the keyway height (along Z axis)
pocket_kw.setExpression("Depth", "Parameters.kw_height")
pocket_kw.Depth = KW_H

# 3. Create the Polar Pattern
# We need to pattern the pocket around the Z axis.
# Number of occurrences = N_KW
# Angle = 360 / N_KW
pattern_kw = body.newObject("PartDesign::PolarPattern", "PatternKeyway")
pattern_kw.Originals = [pocket_kw]
pattern_kw.Axis = (doc.getObject("Z_Axis"), [])
pattern_kw.setExpression("Angle", "360 / Parameters.num_keyways")
pattern_kw.Angle = 360.0 / N_KW
pattern_kw.Occurrences = N_KW

# --- Finalize ---
doc.recompute()

# --- Save ---
# Output path derived from __file__
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
