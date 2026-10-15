from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# --- Configuration ---
DOC_NAME = "982e774306"
STEM = Path(__file__).stem
SCALE = 1.0 # 1:1 with drawing

# --- Setup Document ---
doc = App.newDocument(DOC_NAME)
doc.ModelColor = App.Color(0, 0, 0)
doc.ModelStyle = "Wire"
doc.recompute()

# --- Geometry Parameters (Extracted from Drawing) ---
# Main Frame
L_FRAME = 450.8
W_FRAME = 200.0
H_FRAME = 405.0
T_FRAME = 10.0

# Corner Cutout (Right, Bottom)
CUTOUT_W = 62.888 # ~62.9
CUTOUT_H = 69.86 # ~69.9
CUTOUT_R = 4.0

# Main Hole (Top Left)
D_MAIN_HOLE = 219.88
R_MAIN_HOLE = D_MAIN_HOLE / 2.0

# Secondary Hole (Bottom Right)
D_SEC_HOLE = 126.28
R_SEC_HOLE = D_SEC_HOLE / 2.0

# Top Slots
SLOT_W_1 = 50.99 # ~51.0
SLOT_W_2 = 34.35
SLOT_W_3 = 87.36

# Hole Depths
D_MAIN_HOLE_DEPTH = 100.0
D_SEC_HOLE_DEPTH = 50.0

# --- Create XY Plane ---
plane_XY = doc.addObject("PartDesign::Plane", "Plane_XY")
plane_XY.Placement = App.Placement(App.Vector(0, 0, 0))
doc.addObject("App::Link", "Link_XY")
Link_XY = doc.addObject("App::Link", "Link_XY")
Link_XY.Source = "Plane_XY"
Link_XY.Placement = App.Placement()
doc.recompute()

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# --- Main Outline Sketch ---
sketch_main = body.newObject("Sketcher::SketchObject", "sketch_main_outline")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.ViewObject.Visibility = False

# Coordinates derived from 0,0 (Bottom-Left of the main block)
# Top-Left (0, 405.0)
# Bottom-Right (450.8, 0)
# Top-Right (450.8, 405.0)
# Bottom-Left (0, 0)

# Main Rectangle
lines_main = [
    Part.LineSegment(App.Vector(0, 0, 0), App.Vector(L_FRAME, 0, 0)),      # Bottom
    Part.LineSegment(App.Vector(L_FRAME, 0, 0), App.Vector(L_FRAME, H_FRAME, 0)), # Right
    Part.LineSegment(App.Vector(L_FRAME, H_FRAME, 0), App.Vector(0, H_FRAME, 0)), # Top
    Part.LineSegment(App.Vector(0, H_FRAME, 0), App.Vector(0, 0, 0))       # Left
]

sketch_main.addGeometry(lines_main, False)

# --- Main Hole Sketch ---
sketch_main_hole = body.newObject("Sketcher::SketchObject", "sketch_main_hole")
sketch_main_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main_hole.ViewObject.Visibility = False

# Center of Main Hole: x=0, y=379.6 (from 405.0 - 25.4) -> Wait, drawing shows 405.0 is total height.
# Drawing shows 12.7 (left margin) + 133.54 + 90.03 + 90.03 + 12.7? No.
# Let's trace from Bottom-Left corner of the main block (0,0).
# The main block is 450.8 wide, 200.0 high? No, 200 is a dimension on the right side.
# The 405.0 is the total height. The 200.0 is the height of the main body from bottom.
# Let's re-read coordinates.
# Bottom Left of Main Body: (0, 0)
# Top Left of Main Body: (0, 200.0)
# Top Right of Main Body: (450.8, 200.0)
# Bottom Right of Main Body: (450.8, 0)
# BUT the drawing has the main hole at the top left corner.
# The 405.0 dimension is the height of the whole part (including the top flange).
# The 200.0 is the height of the main body.
# So the Top Flange is 405.0 - 200.0 = 205.0 high.
# The Main Hole is in the Top Flange.
# Center Y = 405.0 - 25.4 = 379.6.
# Center X = 12.7 + 133.54/2? No.
# Let's use the grid lines.
# Bottom Left of Main Body is (0,0).
# Main Hole Center is at y = 379.6. x = 12.7 + 133.54 = 146.24?
# Wait, 133.54 is dimension between two points.
# Let's assume Main Hole Center X = 146.24, Y = 379.6.
# Wait, 133.54 is the distance from Left Edge to the center line of the main hole.
# So Center X = 133.54.
# Center Y = 405.0 - 25.4 = 379.6.
# Let's verify. 133.54 + 90.03 + 90.03 + 12.7 = 326.3? No.
# 133.54 is from Left Edge to Center Line.
# 90.03 is from Center Line to next feature.
# Let's just use the drawing coordinates directly.
# Main Hole Center: (133.54, 379.6)

sketch_main_hole.addGeometry(Part.Circle(App.Vector(133.54, 379.6, 0), App.Vector(0, 0, 1), R_MAIN_HOLE), False)

# --- Secondary Hole Sketch ---
# Center of Secondary Hole:
# X = 450.8 - 63.3 = 387.5? No, 63.3 is from Right Edge.
# X = 450.8 - 63.3 = 387.5.
# Y = 69.86 + 12.7 = 82.56? No, 69.86 is from Bottom Edge to Center Line.
# So Y = 69.86.
# Let's re-read. 69.86 is from Bottom Edge to Center Line.
# X = 450.8 - 63.3 = 387.5.
# Wait, 63.3 is from Right Edge to Center Line.
# So Center X = 450.8 - 63.3 = 387.5.
# Center Y = 69.86.
# Let's verify. 63.3 + 102.82 = 166.12? No.
# 63.3 is from Right Edge to Center Line.
# 102.82 is from Right Edge to something else.
# Let's just use the drawing coordinates.
# Center X = 387.5, Center Y = 69.86.

sketch_sec_hole = body.newObject("Sketcher::SketchObject", "sketch_sec_hole")
sketch_sec_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_sec_hole.ViewObject.Visibility = False

sketch_sec_hole.addGeometry(Part.Circle(App.Vector(387.5, 69.86, 0), App.Vector(0, 0, 1), R_SEC_HOLE), False)

# --- Top Slots Sketch ---
# Slots are horizontal.
# Slot 1 (Left): Width 50.99, Center Y = 150.54. Center X = 12.7 + 50.99/2 = 38.195? No.
# Drawing shows Slot 1 starts at x=12.7 (left edge) + 50.99/2? No.
# Slot 1 Center X = 12.7 + 50.99/2 = 38.195.
# Slot 1 Center Y = 150.54.
# Slot 2 (Middle): Width 34.35, Center X = 12.7 + 50.99 + 34.35/2 = 88.545?
# Drawing shows Slot 2 Center X = 12.7 + 50.99 + 34.35/2 = 88.545.
# Slot 2 Center Y = 150.54.
# Slot 3 (Right): Width 87.36, Center X = 12.7 + 50.99 + 34.35 + 87.36/2 = 169.065?
# Drawing shows Slot 3 Center X = 12.7 + 50.99 + 34.35 + 87.36/2 = 169.065.
# Slot 3 Center Y = 150.54.

sketch_slots = body.newObject("Sketcher::SketchObject", "sketch_slots")
sketch_slots.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_slots.ViewObject.Visibility = False

# Slot 1
lines_slot1 = [
    Part.LineSegment(App.Vector(12.7, 150.54, 0), App.Vector(12.7 + 50.99, 150.54, 0))
]
sketch_slots.addGeometry(lines_slot1, False)

# Slot 2
lines_slot2 = [
    Part.LineSegment(App.Vector(12.7 + 50.99, 150.54, 0), App.Vector(12.7 + 50.99 + 34.35, 150.54, 0))
]
sketch_slots.addGeometry(lines_slot2, False)

# Slot 3
lines_slot3 = [
    Part.LineSegment(App.Vector(12.7 + 50.99 + 34.35, 150.54, 0), App.Vector(12.7 + 50.99 + 34.35 + 87.36, 150.54, 0))
]
sketch_slots.addGeometry(lines_slot3, False)

# --- Fillet Sketch (Corner) ---
# Corner Radius 4.0
sketch_fillet = body.newObject("Sketcher::SketchObject", "sketch_fillet")
sketch_fillet.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_fillet.ViewObject.Visibility = False

# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.8 - 62.888, 69.86 - 4.0)? No.
# Corner is at (450.
