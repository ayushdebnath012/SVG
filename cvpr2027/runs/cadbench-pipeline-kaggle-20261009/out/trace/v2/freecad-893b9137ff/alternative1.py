import FreeCAD as App
import Part
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__ as requested
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameter Definition ---
# We use a dictionary to hold parameters that will be mapped to document objects later.
# This allows us to define the logic cleanly before creating the document structure.
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
body.Proxy = "Body" # Ensure it exists
doc.setActiveObject("Body")

# --- Helper to create parameters ---
def add_param_doc(name, value, unit="mm"):
    param = doc.addObject("App::Parameter", name)
    param.Expression = f"= {value} {unit}"
    doc.recompute()
    return param

# Add all parameters to the document
for name, value in params_config.items():
    if isinstance(value, tuple):
        # For tuple parameters, we might need to split them or handle them specifically
        # For simplicity in this script, we will use expressions that reference math or just store the base
        # However, FreeCAD PartDesign parameters are usually scalar. 
        # We will create two parameters for coordinates if needed, or rely on math functions in constraints.
        pass 
    add_param_doc(name, value)

# --- Geometry Construction ---

# 1. Base Brick Body
# Sketch 1: Profile for the main brick (Top view / XY plane)
sketch_base = body.newObject("Sketcher::SketchObject", "BaseProfile")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.ConstrainToAll = True
sketch_base.ConstrainToView = True

# Define the rectangle for the main body based on studs layout + thickness
# Main body width = StudCenter[0] * 2 + StudDistance/2 (approx logic) or simply derive from studs.
# Standard Lego: Main body is slightly smaller than the studs grid.
# Let's define the main block boundaries.
# Width = (NumStudsColumns * StudDistance) - (LegoUnitSize/2) ?? 
# Actually, simpler: The studs are centered. 
# Let's create a rectangle that encompasses the studs area minus the thickness.
# Width = StudCenter[0]*2 + StudDistance/2 * 2 ? No.
# Let's assume the studs grid defines the outer envelope.
# Envelope X = StudCenter[0]*2 + StudDistance/2 (half gap from center to edge)
# Actually, let's just use the provided "LegoUnitSize" logic.
# Total Width = NumStudsColumns * StudDistance + (LegoUnitSize/2) ? 
# Let's stick to the coordinates given: StudCenter=(4,4), TubeCenter=(8,8).
# Implies the grid starts at 0.
# Max X = 4 + 8 = 12. Max Y = 4 + 8 = 12.
# So the brick is 12x12 roughly.
# Let's define the rectangle explicitly using the config.
# Width = (NumStudsColumns * StudDistance) / 2 * 2 + (LegoUnitSize/2)? 
# Let's calculate: 
# Max X extent = StudCenter[0] + StudDistance/2 = 4 + 4 = 8? 
# Wait, if center is 4 and distance is 8, next is 12. So width is 12.
# Let's create a rectangle that matches the stud grid outer bounds, then subtract thickness.
# Actually, the brick body is continuous.
# Let's define a rectangle of size: (MaxStudsX + Margin) x (MaxStudsY + Margin)
# Based on "StudsDistance=8", "StudCenter=(4,4)". 
# The studs are at x=4, 12 and y=4, 12. 
# So the bounding box of studs is 12x12.
# The brick body should be slightly smaller or same. Let's make it 12x12 for now, then we can refine.
# But usually the brick is slightly larger than the stud holes but smaller than the studs? 
# No, studs are on top, brick body is underneath.
# Let's create a rectangle: 12 x 12.
# But wait, the "LegoUnitSize" is 8.0. 
# If we have 2 rows and 4 columns with distance 8.
# Total width = 4 * 8 = 32? No, that's too big.
# "StudsDistance" is likely the center-to-center distance.
# If Center is (4,4), then the first stud is at 4. The distance to the next is 8. So next is 12.
# So we have studs at 4 and 12.
# The total width of the brick usually covers this.
# Let's set the rectangle to: 
# Width = StudCenter[0] * 2 + StudDistance/2 (half the last stud's radius?) No.
# Let's assume the brick spans from -0.5*unit to +0.5*unit relative to centers?
# Let's just use the explicit dimensions derived from the tuple centers.
# Max X = 4 + 8 = 12. Min X = 4 - 4 = 0? No, center is 4.
# If there are 2 rows (Y direction) and 4 columns (X direction)?
# "num_studs_rows=2, num_studs_columns=4".
# StudCenter=(4,4). This is likely the center of the grid? Or the first stud?
# "For example, a 2x4 lego...".
# If Center is (4,4), and we have 4 columns.
# Maybe the center of the 2x4 block is (4,4)?
# If so, the studs are distributed around (4,4).
# Let's assume the provided coordinates (4,4) are the CENTER of the stud grid.
# Then:
# X range: 4 - (1.5 * 8) to 4 + (1.5 * 8)? 
# 4 columns -> indices 0, 1, 2, 3. Center of 0..3 is 1.5.
# So X range: 4 - 12 = -8 to 4 + 12 = 16. Width = 24.
# 2 rows -> indices 0, 1. Center of 0..1 is 0.5.
# So Y range: 4 - 4 = 0 to 4 + 4 = 8. Height = 8.
# This seems plausible. 24x8 brick.
# Let's re-read: "StudCenter=(4mm,4mm)".
# If it's the center of the whole brick, then the brick size is determined by the studs.
# Let's assume the coordinates given are the CENTER of the stud array.
# X Spread: 4 columns. Distance 8. Span = 3 * 8 = 24. Half span = 12.
# X range: 4 - 12 = -8 to 4 + 12 = 16.
# Y Spread: 2 rows. Distance 8. Span = 1 * 8 = 8. Half span = 4.
# Y range: 4 - 4 = 0 to 4 + 4 = 8.
# So Brick Base Size: 24 x 8.
# But "LegoUnitSize=8.0". 24 is 3 units. 8 is 1 unit. 
# A 2x4 brick is typically 3 units wide, 1 unit deep? Or vice versa?
# Standard 2x4 is 3 studs wide, 1 stud deep? No, 2 rows x 4 columns.
# Usually 2x4 means 2 studs high (vertical) and 4 studs long? 
# In Lego terms, "2x4" usually means 2 studs across, 4 studs down? Or 2x4 studs on top.
# Let's assume the parameters define the geometry directly.
# Let's create the base rectangle based on the calculated spread from the center (4,4).
# Width = 24, Height = 8.
# Thickness = LegoThickness (1.6).
# Height = LegoHeight (9.6).

# Define Base Rectangle Points
# X: -8 to 16 (Width 24)
# Y: 0 to 8 (Height 8)
# Let's adjust to make it symmetric if possible, or just use these bounds.
# Let's shift Y to be positive for simplicity in sketching if needed, but relative is fine.
# Let's make it centered at (4,4).
# X_min = 4 - 12 = -8. X_max = 4 + 12 = 16.
# Y_min = 4 - 4 = 0. Y_max = 4 + 4 = 8.

# Create Base Profile
pt1 = App.Vector(-8, 0, 0)
pt2 = App.Vector(16, 0, 0)
pt3 = App.Vector(16, 8, 0)
pt4 = App.Vector(-8, 8, 0)

sketch_base.addGeometry(Part.LineSegment(pt1, pt2), False)
sketch_base.addGeometry(Part.LineSegment(pt2, pt3), False)
sketch_base.addGeometry(Part.LineSegment(pt3, pt4), False)
sketch_base.addGeometry(Part.LineSegment(pt4, pt1), False)

# Add Constraints to make it a rectangle
sketch_base.addConstraint(Sketcher.Constraint("Equal", 1, 2)) # Horizontal
sketch_base.addConstraint(Sketcher.Constraint("Equal", 2, 3)) # Vertical
sketch_base.addConstraint(Sketcher.Constraint("Equal", 3, 4)) # Horizontal
sketch_base.addConstraint(Sketcher.Constraint("Equal", 4, 1)) # Vertical
sketch_base.addConstraint(Sketcher.Constraint("Horizontal", 1, 2))
sketch_base.addConstraint(Sketcher.Constraint("Horizontal", 3, 4))
sketch_base.addConstraint(Sketcher.Constraint("Vertical", 2, 3))
sketch_base.addConstraint(Sketcher.Constraint("Vertical", 4, 1))
sketch_base.addConstraint(Sketcher.Constraint("PointOnLine", 1, 2, 1, 1)) # pt1 on line
sketch_base.addConstraint(Sketcher.Constraint("PointOnLine", 2, 3, 1, 2))
sketch_base.addConstraint(Sketcher.Constraint("PointOnLine", 3, 4, 1, 3))
sketch_base.addConstraint(Sketcher.Constraint("PointOnLine", 4, 1, 1, 4))
# Actually, simpler: Fix pt1, then perpendiculars.
# Let's just constrain the lines to form a rectangle and fix the position.
# pt1 at (-8, 0)
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 1, 2, -8, 0)) # X of pt1
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 1, 2, 0, 0)) # Y of pt1
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 2, 3, 16, 0)) # X of pt2
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 3, 4, 16, 8)) # X of pt3, Y of pt3
sketch_base.addConstraint(Sketcher.Constraint("DistanceXY", 4, 1, -8, 8)) # Y of pt4

# Pad the base
pad_base = body.newObject("PartDesign::Pad", "BasePad")
pad_base.Profile = sketch_base
pad_base.Length = params_config["LegoHeight"]
doc.recompute()

# --- Studs ---
# We need to place studs in a grid.
# Grid Center: (4, 4)
# Rows: 2, Cols: 4.
# Step: 8.
# We need to calculate the positions of the centers.
# X indices: -1.5, -0.5, 0.5, 1.5 (relative to center) -> multiply by step/2?
# Distance between centers is 8.
# If we have 4 columns, the centers are at x_center + [-3, -1, 1, 3] * (8/2) = [-12, -4, 4, 12]? 
# No, distance is 8. So intervals are 8.
# Centers: c, c-8, c-16, c-24? Or c, c+8, c+16, c+24?
# Total span = 3 * 8 = 24.
# If center is 4.
# X coords: 4 - 12 = -8, 4 - 4 = 0, 4 + 4 = 8, 4 + 12 = 16.
# Y coords: 2 rows. Span = 8.
# Y coords: 4 - 4 = 0, 4 + 4 = 8.
# This matches our base rectangle boundaries (-8 to 16, 0 to 8).

# Function to create a stud feature
def create_stud(x, y, z_height, name_suffix):
    # Sketch for stud (Top view circle)
    sketch_stud = body.newObject("Sketcher::SketchObject", f"StudSketch_{name_suffix}")
    sketch_stud.Placement = App.Placement(App.Vector(x, y, params_config["LegoHeight"]))
    
    # Circle for stud top
    # Diameter = StudDiameter
    stud_center = App.Vector(x, y, 0) # Local to sketch
    r = params_config["StudDiameter"] / 2.0
    circle = Part.Circle(stud_center, App.Vector(0, 0, 1), r)
    sketch_stud.addGeometry(circle, False)
    
    # Constraint: Center on the sketch origin?
    # The sketch is placed at (x,y, height). The circle center is (0,0) in sketch coords.
    # We need to constrain the circle center to the sketch origin.
    sketch_stud.addConstraint(Sketcher.Constraint("Center", 1)) # Circle center at sketch origin
    
    # Pad the stud
    pad_stud = body.newObject("PartDesign::Pad", f"StudPad_{name_suffix}")
    pad_stud.Profile = sketch_stud
    pad_stud.Length = params_config["StudHeight"]
    
    return pad_stud

# Generate Studs
# X coords: -8, 0, 8, 16
# Y coords: 0, 8
# We need to iterate.
# Note: The sketch placement Z is the top of the base (LegoHeight).
# The pad length is StudHeight.

stud_positions_x = [-8, 0, 8, 16]
stud_positions_y = [0, 8]

for i, y in enumerate(stud_positions_y):
    for j, x in enumerate(stud_positions_x):
        create_stud(x, y, 0, f"_{j}_{i}") # Z offset handled in sketch placement

doc.recompute()

# --- Receiver Tubes ---
# Tubes are inside the brick.
# Center: (8, 8).
# Wait, our Y range is 0 to 8. Center Y=8 is on the edge?
# "TubeCenter=(8mm, 8mm)".
# If our Y range is 0 to 8, then Y=8 is the top edge. That doesn't seem right for a tube inside.
# Maybe my interpretation of the grid center was wrong.
# Let's re-evaluate "StudCenter=(4mm,4mm)" and "TubeCenter=(8mm, 8mm)".
# Maybe these are absolute coordinates of the FIRST stud and FIRST tube?
# Or maybe the brick is larger.
# If StudCenter is (4,4) and it's a 2x4 grid.
# If it's the center of the brick, then the brick is 24x8 (as calculated).
# If TubeCenter is (8,8), that is inside the 24x8 box?
# X=8 is inside [-8, 16]. Y=8 is on the edge of [0, 8].
# Perhaps the Y range is different.
# What if "2 rows" means 2 studs in Y, and "4 columns" means 4 studs in X.
# If the grid is centered at (4,4), and step is 8.
# X: -8, 0, 8, 16.
# Y: 0, 8. (If step is 8).
# If TubeCenter is (8,8), it aligns with the top-right stud?
# "Receiver tubes inside the brick".
#
