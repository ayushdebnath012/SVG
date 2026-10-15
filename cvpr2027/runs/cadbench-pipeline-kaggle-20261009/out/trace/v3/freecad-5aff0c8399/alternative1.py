from pathlib import Path
import FreeCAD as App, Part, Sketcher

# Create new document
doc = App.newDocument("RightAngleBracket")

# --- Part 1: The Main L-Shaped Bracket Body ---
body_main = doc.addObject("PartDesign::Body", "Body_Main")
params_main = body_main.newObject("App::VarSet", "MainParams")

# Base Sketch for the L-Shape (Front View)
sketch_main = body_main.newObject("Sketcher::SketchObject", "Sketch_Main")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.BaseConstraint = Sketcher.Constraint(
    "Axis", doc.addObject("App::Link", "Z_Axis").LinkObject, 1) # Attach to global Z
sketch_main.AddPlaneConstraint = [doc.addObject("App::Link", "XY_Plane").LinkObject]

# Define Geometry based on drawing measurements:
# Main body total length: 180mm
# Main body height: 55mm
# Main body width: 35mm
# Flange length: 55mm (measured from end)
# Flange height: 10mm (measured from bottom)
# Corner radius: R4.25mm (measured on the fillet)
# Flange cutout: 15mm long x 5mm high

# Define lines for the main L-shape profile
# Line 1: Bottom horizontal base (0,0) to (180,0)
l1 = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(180, 0, 0))
sketch_main.addGeometry(l1, False)

# Line 2: Right vertical section (180,0) to (180,55)
l2 = Part.LineSegment(App.Vector(180, 0, 0), App.Vector(180, 55, 0))
sketch_main.addGeometry(l2, False)

# Line 3: Top horizontal section (180,55) to (55,55)
l3 = Part.LineSegment(App.Vector(180, 55, 0), App.Vector(55, 55, 0))
sketch_main.addGeometry(l3, False)

# Line 4: Left vertical section (55,55) to (55, 45) -> Flange starts here (height 55-10=45)
l4 = Part.LineSegment(App.Vector(55, 55, 0), App.Vector(55, 45, 0))
sketch_main.addGeometry(l4, False)

# Line 5: Flange top (55,45) to (10,45)
l5 = Part.LineSegment(App.Vector(55, 45, 0), App.Vector(10, 45, 0))
sketch_main.addGeometry(l5, False)

# Line 6: Flange left (10,45) to (10, 35) -> Flange ends at height 35
l6 = Part.LineSegment(App.Vector(10, 45, 0), App.Vector(10, 35, 0))
sketch_main.addGeometry(l6, False)

# Line 7: Flange bottom (10,35) to (55,35)
l7 = Part.LineSegment(App.Vector(10, 35, 0), App.Vector(55, 35, 0))
sketch_main.addGeometry(l7, False)

# Line 8: Bottom left corner (55,0) to (10,0)
l8 = Part.LineSegment(App.Vector(55, 0, 0), App.Vector(10, 0, 0))
sketch_main.addGeometry(l8, False)

# Line 9: Vertical drop for flange cutout (55, 35) to (55, 30)
l9 = Part.LineSegment(App.Vector(55, 35, 0), App.Vector(55, 30, 0))
sketch_main.addGeometry(l9, False)

# Line 10: Bottom of cutout (55,30) to (40,30)
l10 = Part.LineSegment(App.Vector(55, 30, 0), App.Vector(40, 30, 0))
sketch_main.addGeometry(l10, False)

# Line 11: Vertical up (40,30) to (40, 25)
l11 = Part.LineSegment(App.Vector(40, 30, 0), App.Vector(40, 25, 0))
sketch_main.addGeometry(l11, False)

# Line 12: Top of cutout (40,25) to (55,25)
l12 = Part.LineSegment(App.Vector(40, 25, 0), App.Vector(55, 25, 0))
sketch_main.addGeometry(l12, False)

# Add fillet R4.25 at the inside corner of the main L shape
# Edge indices: Line 3 (l3) connects to Line 4 (l4).
# Line 3 index is 2, Line 4 index is 3.
sketch_main.addConstraint(
    Sketcher.Constraint("Radius", 2, 1, 3, 1, 4.25), False)

# Add constraints to fix dimensions (optional but good practice)
# Length 180
sketch_main.addConstraint(
    Sketcher.Constraint("Length", 0, 0, 0, 1, 180), False)
# Width 55
sketch_main.addConstraint(
    Sketcher.Constraint("Length", 1, 0, 1, 0, 55), False)
# Flange length 55
sketch_main.addConstraint(
    Sketcher.Constraint("Length", 5, 0, 5, 0, 55), False)
# Flange height 10 (distance from top 55 to 45)
sketch_main.addConstraint(
    Sketcher.Constraint("DistanceXY", 2, 0, 3, 0, 10), False)

# Pad the sketch to create the L-bracket body
pad_main = body_main.newObject("PartDesign::Pad", "Pad_Main")
pad_main.Profile = sketch_main
pad_main.Length = 35.0 # Depth of the bracket
pad_main.Type = "Solid"
pad_main.makeSolid()

# --- Part 2: The Mounting Block ---
# Block position: Bottom center of the L-shape (10mm high, 180mm long).
# Dimensions: 20mm width x 10mm depth x 10mm height (inferred from context and typical blocks).
# The drawing shows a block at the very bottom of the L-shape.
# Let's create a separate body for the block to keep it clean, or add it to the main body.
# The drawing shows the block is 20mm wide, 10mm deep, and 10mm high.
# It is centered horizontally at the bottom.

body_block = doc.addObject("PartDesign::Body", "Body_Block")
params_block = body_block.newObject("App::VarSet", "BlockParams")

sketch_block = body_block.newObject("Sketcher::SketchObject", "Sketch_Block")
sketch_block.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_block.AddPlaneConstraint = [doc.addObject("App::Link", "XY_Plane").LinkObject]

# Line 1: Bottom (0,0) to (20,0)
l_b1 = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(20, 0, 0))
sketch_block.addGeometry(l_b1, False)

# Line 2: Right side (20,0) to (20,10)
l_b2 = Part.LineSegment(App.Vector(20, 0, 0), App.Vector(20, 10, 0))
sketch_block.addGeometry(l_b2, False)

# Line 3: Top (20,10) to (0,10)
l_b3 = Part.LineSegment(App.Vector(20, 10, 0), App.Vector(0, 10, 0))
sketch_block.addGeometry(l_b3, False)

# Line 4: Left side (0,10) to (0,0)
l_b4 = Part.LineSegment(App.Vector(0, 10, 0), App.Vector(0, 0, 0))
sketch_block.addGeometry(l_b4, False)

# Add constraints
sketch_block.addConstraint(
    Sketcher.Constraint("Length", 0, 0, 0, 1, 20), False) # Width 20
sketch_block.addConstraint(
    Sketcher.Constraint("Length", 1, 0, 1, 0, 10), False) # Height 10

# Pad the block
pad_block = body_block.newObject("PartDesign::Pad", "Pad_Block")
pad_block.Profile = sketch_block
pad_block.Length = 10.0 # Depth 10
pad_block.Type = "Solid"
pad_block.makeSolid()

# --- Part 3: The Mounting Hole ---
# Hole position: Center of the block.
# Diameter: 8mm (standard M8 hole size).
# Depth: 5mm.

body_hole = doc.addObject("PartDesign::Body", "Body_Hole")
params_hole = body_hole.newObject("App::VarSet", "HoleParams")

sketch_hole = body_hole.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hole.AddPlaneConstraint = [doc.addObject("App::Link", "XY_Plane").LinkObject]

# Circle for the hole
# Center at (10, 5), Radius 4mm (Diameter 8mm)
hole_c = Part.Circle(App.Vector(10, 5, 0), App.Vector(0, 0, 1), 4.0)
sketch_hole.addGeometry(hole_c, False)

# Add constraint
sketch_hole.addConstraint(
    Sketcher.Constraint("Size2D", 0, 0, 4.0), False) # Diameter 8mm

# Pocket the hole
pocket_hole = body_hole.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket_hole.Profile = sketch_hole
pocket_hole.Type = "ThroughAll" # Go through the block
pocket_hole.makeSolid()

# --- Part 4: The Side Mounting Hole ---
# Hole position: On the side face of the L-shape.
# Dimensions: 10mm diameter.
# Depth: 10mm.

body_side_hole = doc.addObject("PartDesign::Body", "Body_SideHole")
params_side_hole = body_side_hole.newObject("App::VarSet", "SideHoleParams")

sketch_side_hole = body_side_hole.newObject("Sketcher::SketchObject", "Sketch_SideHole")
sketch_side_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_side_hole.AddPlaneConstraint = [doc.addObject("App::Link", "XY_Plane").LinkObject]

# Circle for the side hole
# Center at (10, 100), Radius 5mm (Diameter 10mm)
side_hole_c = Part.Circle(App.Vector(10, 100, 0), App.Vector(0, 0, 1), 5.0)
sketch_side_hole.addGeometry(side_hole_c, False)

# Add constraint
sketch_side_hole.addConstraint(
    Sketcher.Constraint("Size2D", 0, 0, 5.0), False) # Diameter 10mm

# Pocket the side hole
pocket_side_hole = body_side_hole.newObject("PartDesign::Pocket", "Pocket_SideHole")
pocket_side_hole.Profile = sketch_side_hole
pocket_side_hole.Type = "ThroughAll"
pocket_side_hole.makeSolid()

# --- Part 5: The Hole Pattern ---
# Pattern the side hole.
# Number of holes: 6.
# Spacing: 70mm (center-to-center).
# Angle: 360 degrees (full circle).

pattern_holes = body_side_hole.newObject("PartDesign::PolarPattern", "Pattern_Holes")
pattern_holes.Profile = sketch_side_hole
pattern_holes.ReferenceAxis = [doc.addObject("App::Link", "Z_Axis").LinkObject]
pattern_holes.Originals = [pocket_side_hole]
pattern_holes.Occurrences = 6
pattern_holes.Angle = 360.0
pattern_holes.makeSolid()

# --- Save the document ---
# Save to /app/answer.FCStd
doc.saveAs(str(Path(__file__).resolve().with_suffix(".FCStd")))
