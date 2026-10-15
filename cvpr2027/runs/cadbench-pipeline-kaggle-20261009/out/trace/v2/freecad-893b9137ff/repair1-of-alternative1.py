import FreeCAD as App
import Part
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__ as requested
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameter Definition ---
# We define parameters here to be added to the document.
params_config = {
    "LegoUnitSize": 8.0,
    "LegoHeight": 9.6,
    "LegoThickness": 1.6,
    "NumStudsRows": 2,
    "NumStudsColumns": 4,
    "StudsDistance": 8.0,
    "StudCenter": (4.0, 4.0),
    "StudDiameter": 4.8,
    "StudHeight": 1.6,
    "TubeCenter": (8.0, 8.0),
    "TubeOuterDiameter": 6.4,
    "TubeInnerDiameter": 4.8,
    "TubeDistance": 8.0
}

# --- Document Creation ---
doc = App.newDocument("LegoBrick")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# --- Helper to create parameters ---
def add_param_doc(name, value, unit="mm"):
    param = doc.addObject("App::Parameter", name)
    param.Expression = f"= {value} {unit}"
    doc.recompute()
    return param

# Add all parameters to the document
for name, value in params_config.items():
    add_param_doc(name, value)

# --- Geometry Construction ---

# 1. Base Brick Body
# Based on the analysis:
# StudCenter=(4,4) is the center of the 2x4 grid.
# X spread (4 cols, dist 8): 3 intervals * 8 = 24. Range: 4 +/- 12 -> [-8, 16].
# Y spread (2 rows, dist 8): 1 interval * 8 = 8. Range: 4 +/- 4 -> [0, 8].
# Brick dimensions: 24 x 8 x 9.6.

# Sketch 1: Profile for the main brick (Top view / XY plane)
sketch_base = body.newObject("Sketcher::SketchObject", "BaseProfile")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))

# Define the rectangle for the main body
# X: -8 to 16 (Width 24)
# Y: 0 to 8 (Height 8)
pt1 = App.Vector(-8, 0, 0)
pt2 = App.Vector(16, 0, 0)
pt3 = App.Vector(16, 8, 0)
pt4 = App.Vector(-8, 8, 0)

sketch_base.addGeometry(Part.LineSegment(pt1, pt2), False)
sketch_base.addGeometry(Part.LineSegment(pt2, pt3), False)
sketch_base.addGeometry(Part.LineSegment(pt3, pt4), False)
sketch_base.addGeometry(Part.LineSegment(pt4, pt1), False)

# Add Constraints to make it a rectangle and fix position
# Fix pt1 at (-8, 0)
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 1, 2, -8, 0))
# Fix pt2 at (16, 0)
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 2, 3, 16, 0))
# Fix pt3 at (16, 8)
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 3, 4, 16, 8))
# Fix pt4 at (-8, 8)
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 4, 1, -8, 8))

# Pad the base
pad_base = body.newObject("PartDesign::Pad", "BasePad")
pad_base.Profile = sketch_base
pad_base.Length = params_config["LegoHeight"]
doc.recompute()

# --- Studs ---
# Grid calculation:
# Center (4, 4).
# X indices: -1.5, -0.5, 0.5, 1.5 (relative to center in units of half-step)
# Step = 8. Half-step = 4.
# X coords: 4 + [-12, -4, 4, 12] = [-8, 0, 8, 16]
# Y indices: -0.5, 0.5 (relative to center)
# Y coords: 4 + [-4, 4] = [0, 8]

stud_positions_x = [-8, 0, 8, 16]
stud_positions_y = [0, 8]

# Function to create a stud feature
def create_stud(x, y, name_suffix):
    # Sketch for stud (Top view circle)
    sketch_stud = body.newObject("Sketcher::SketchObject", f"StudSketch_{name_suffix}")
    # Place sketch on top of the base
    sketch_stud.Placement = App.Placement(App.Vector(x, y, params_config["LegoHeight"]))
    
    # Circle for stud top
    stud_center = App.Vector(0, 0, 0) # Local to sketch
    r = params_config["StudDiameter"] / 2.0
    circle = Part.Circle(stud_center, App.Vector(0, 0, 1), r)
    sketch_stud.addGeometry(circle, False)
    
    # Constraint: Center of circle at sketch origin
    sketch_stud.addConstraint(Sketcher.Constraint("Center", 1))
    
    # Pad the stud
    pad_stud = body.newObject("PartDesign::Pad", f"StudPad_{name_suffix}")
    pad_stud.Profile = sketch_stud
    pad_stud.Length = params_config["StudHeight"]
    
    return pad_stud

# Generate Studs
for i, y in enumerate(stud_positions_y):
    for j, x in enumerate(stud_positions_x):
        create_stud(x, y, f"_{j}_{i}")

doc.recompute()

# --- Receiver Tubes ---
# TubeCenter=(8, 8).
# This corresponds to the top-right corner of our grid (X=16, Y=8)? 
# Wait, if Center is (4,4) and we have 2 rows (Y), the Y coords are 0 and 8.
# If TubeCenter is (8,8), it aligns with the stud at (8,8).
# However, the problem says "TubeCenter=(8mm, 8mm)".
# Let's assume the tubes are located at the same grid positions as the studs, 
# but the provided "TubeCenter" might be a specific example or the center of the tube array.
# Given the ambiguity, and the fact that (8,8) is one of our stud positions, 
# we will place tubes at all stud positions.
# If the prompt implies a different layout, the coordinates (8,8) would be the center of the tube grid.
# If (8,8) is the center of the tube grid, and we have 2x4 tubes...
# Let's assume the tubes follow the same grid as the studs for a standard Lego brick.
# The coordinates (8,8) in the prompt might be a typo for the center (4,4) or referring to a specific tube.
# However, to be safe and create a valid "receiver" pattern, we will place tubes at the stud locations.
# If the prompt strictly means "Center of tube array is (8,8)", then the grid would be shifted.
# But (8,8) is on the edge of our calculated brick [0,8] in Y.
# Let's assume the prompt's "TubeCenter" is actually the center of the *brick* (which is (4,4)) 
# and there's a typo, OR the tube grid is different.
# Given "StudsDistance=8" and "TubeDistance=8", they likely share the grid.
# Let's place tubes at the stud positions.

tube_positions_x = [-8, 0, 8, 16]
tube_positions_y = [0, 8]

# Function to create a tube feature (Hole)
def create_tube(x, y, name_suffix):
    # Sketch for tube (Top view circle)
    sketch_tube = body.newObject("Sketcher::SketchObject", f"TubeSketch_{name_suffix}")
    # Place sketch on top of the base
    sketch_tube.Placement = App.Placement(App.Vector(x, y, params_config["LegoHeight"]))
    
    # Circle for tube hole
    tube_center = App.Vector(0, 0, 0) # Local to sketch
    r_outer = params_config["TubeOuterDiameter"] / 2.0
    r_inner = params_config["TubeInnerDiameter"] / 2.0
    
    # We need to create a profile that subtracts the tube.
    # A simple way is to draw the outer circle and the inner circle, then use a pocket.
    # Or draw the outer circle and use a hole feature.
    # Let's use a Pocket with a compound profile (Outer - Inner).
    
    # Outer Circle
    circle_outer = Part.Circle(tube_center, App.Vector(0, 0, 1), r_outer)
    sketch_tube.addGeometry(circle_outer, False)
    
    # Inner Circle (concentric)
    circle_inner = Part.Circle(tube_center, App.Vector(0, 0, 1), r_inner)
    sketch_tube.addGeometry(circle_inner, False)
    
    # Constraints
    sketch_tube.addConstraint(Sketcher.Constraint("Center", 1)) # Outer center
    sketch_tube.addConstraint(Sketcher.Constraint("Center", 2)) # Inner center
    sketch_tube.addConstraint(Sketcher.Constraint("Concentric", 1, 2))
    sketch_tube.addConstraint(Sketcher.Constraint("Radius", 1, r_outer))
    sketch_tube.addConstraint(Sketcher.Constraint("Radius", 2, r_inner))
    
    # Pocket the tube
    pocket_tube = body.newObject("PartDesign::Pocket", f"TubePocket_{name_suffix}")
    pocket_tube.Profile = sketch_tube
    pocket_tube.Type = "ThroughAll"
    
    return pocket_tube

# Generate Tubes
for i, y in enumerate(tube_positions_y):
    for j, x in enumerate(tube_positions_x):
        create_tube(x, y, f"_{j}_{i}")

doc.recompute()

# --- Save ---
# Save the document to the derived path
doc.saveAs(str(output_path))
