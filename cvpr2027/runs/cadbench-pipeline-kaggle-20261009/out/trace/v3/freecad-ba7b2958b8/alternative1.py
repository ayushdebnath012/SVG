from pathlib import Path
import FreeCAD as App, Part, PartDesign, Sketcher, math

# --- Configuration ---
docName = "DualAxleMountingBracket"
# Derived from __file__ to ensure the script is self-contained and portable
scriptDir = Path(__file__).parent
# Output file path
outputPath = scriptDir / "answer.FCStd"

# Create Document
doc = App.newDocument(docName)
App.ActiveDocument = doc

# --- Parameters ---
# Define all dimensions as named properties for easy editing
params = doc.addObject("App::ParameterList", "Dimensions")

# Main Block Dimensions
params.addObject(App::PropertyLength, "Length", 544.0) # Total Length (approx 248 + 2*150 + 2*230 + ... wait, let's trace)
# Let's re-calculate based on the main dimensions in the drawing.
# From the bottom view (Front):
# Overall Length: 544 (from 233.65*2 + 248 is not right. Let's look at the main projection).
# The main projection is the 3-view drawing.
# Let's identify the main block.
# Total Length: The dimension lines indicate a total length of 544mm (233.65 * 2 + 76.7? No).
# Let's look at the bottom right view (Front view).
# Total Length: 248 (main width) + 110 (left extension) + 150 (right extension) = 508?
# Wait, the dimension 544 is not explicitly there.
# Let's use the explicit dimensions:
# Left side: 248 (width of main block) + 110 (extension) = 358? No.
# Let's re-read the drawing carefully.
# Top View (Top Left): Shows width 224, depth 328 (maybe?), 345.95 (total length).
# Front View (Bottom Right): Shows width 248, height 220.53 (approx 220), length 233.65 (right part).
# Side View (Bottom Left): Shows width 224, height 160.7 (approx), length 345.95 (total).

# Let's build based on the "Front" view (Bottom Right) and "Top" view (Top Left) and "Side" view (Bottom Left).
# 1. Main Block (Center):
#    Width: 248 (Front View)
#    Height: 160.7 (Side View - approx, or 150.03 + 2.84 + ... let's use the labeled 150.03 + 2.84 = 152.87)
#    Depth: 224 (Top View - width of main block)
#    Length: 248 (Front View - width)

# 2. Left Wing:
#    Extension Length: 110 (Front View)
#    Height: 205.03 (Front View)
#    Depth: 35.55 (Side View)
#    Features: 6x holes (6x Ø45, 6x Ø21), 2x R10 fillets on edges.

# 3. Right Wing:
#    Extension Length: 150 (Front View)
#    Height: 205.03 (Front View)
#    Depth: 35.55 (Side View)
#    Features: 6x holes (6x Ø45, 6x Ø21), 2x R10 fillets on edges.

# Let's define the main block first.
params.addObject(App::PropertyLength, "MainWidth", 248.0)
params.addObject(App::PropertyLength, "MainHeight", 152.87) # 150.03 + 2.84
params.addObject(App::PropertyLength, "MainDepth", 224.0)
params.addObject(App::PropertyLength, "MainLength", 248.0)

# Left Wing
params.addObject(App::PropertyLength, "LeftExt", 110.0)
params.addObject(App::PropertyLength, "LeftHeight", 205.03)
params.addObject(App::PropertyLength, "LeftDepth", 35.55)
params.addObject(App::PropertyLength, "LeftR10", 10.0)

# Right Wing
params.addObject(App::PropertyLength, "RightExt", 150.0)
params.addObject(App::PropertyLength, "RightHeight", 205.03)
params.addObject(App::PropertyLength, "RightDepth", 35.55)
params.addObject(App::PropertyLength, "RightR10", 10.0)

# Holes
params.addObject(App::PropertyLength, "HoleLargeD", 45.0)
params.addObject(App::PropertyLength, "HoleSmallD", 21.0)
params.addObject(App::PropertyLength, "HoleDeep", 50.0) # Assumed from typical mounting brackets, not explicitly labeled but visible.

# Angles
params.addObject(App::PropertyAngle, "WingAngle", 43.1) # Front view angle of the diagonal rib

# --- Create Body ---
body = doc.addObject("PartDesign::Body", "Body")
params = body.newObject("App::VarSet", "Parameters") # Link parameters
# Copy params to body parameters
for obj in params:
    if hasattr(obj, "Name") and obj.Name in dir(params):
        pass # Just linking
# Actually, App::VarSet is not standard for PartDesign. Let's use a regular Feature to hold parameters if needed, or just define them locally.
# But the prompt asks for "named document objects".
# Let's just use the parameters defined above in the 'params' list.
# We will reference them by name in the expressions.

# --- Feature 1: Main Block ---
# Sketch 1: Main Block Base
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_MainBlock")
sketch1.Placement = App.Placement(App.Vector(0, -112, 0)) # Shift X to center the 248 width
sketch1.Placement.Rotation = App.Rotation(-90, 0, 0) # Rotate to face Z (for Pad)
sketch1.Placement.Base = App.Vector(-124, 0, 0) # Center X
sketch1.Placement.Rotation = App.Rotation(0, 90, 0) # Rotate to face Z (for Pad) -> Wait, sketch plane is XY.
# Let's set sketch to XY plane, then pad along Z.
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Placement.Rotation = App.Rotation(0, 0, 0) # Face Z

# Draw Main Block Rectangle (Width x Depth)
# Width: MainWidth (248) -> X axis
# Depth: MainDepth (224) -> Y axis
# Center: 0, 0
# Line 1: (0,0) to (MainWidth/2, 0)
# Line 2: (MainWidth/2, 0) to (MainWidth/2, MainDepth/2)
# Line 3: (MainWidth/2, MainDepth/2) to (0, MainDepth/2)
# Line 4: (0, MainDepth/2) to (0, 0)

sketch1.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.MainWidth.Value / 2, 0, 0)), False)
sketch1.addGeometry(Part.LineSegment(App.Vector(params.MainWidth.Value / 2, 0, 0), App.Vector(params.MainWidth.Value / 2, params.MainDepth.Value / 2, 0)), False)
sketch1.addGeometry(Part.LineSegment(App.Vector(params.MainWidth.Value / 2, params.MainDepth.Value / 2, 0), App.Vector(0, params.MainDepth.Value / 2, 0)), False)
sketch1.addGeometry(Part.LineSegment(App.Vector(0, params.MainDepth.Value / 2, 0), App.Vector(0, 0, 0)), False)

sketch1.Constraints = []
sketch1.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 0, 0)) # Origin
sketch1.addConstraint(Sketcher.Constraint("Perpendicular", 0, 0, 0, 1, 0, 0))
sketch1.addConstraint(Sketcher.Constraint("Perpendicular", 0, 0, 0, 1, 0, 1))
sketch1.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, params.MainWidth.Value))
sketch1.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, params.MainDepth.Value))
sketch1.addConstraint(Sketcher.Constraint("Fixed", 0, 0)) # Fix origin

# Pad Main Block
pad1 = body.newObject("PartDesign::Pad", "Pad_MainBlock")
pad1.Profile = sketch1
pad1.Length = params.MainHeight.Value
pad1.Type = "Solid"
pad1.Midplane = False

# --- Feature 2: Left Wing ---
# Sketch 2: Left Wing Base (on XZ plane, attached to Main Block)
# We need to create a sketch attached to a face.
# Let's attach to the top face of the Main Block.
# But wait, the Left Wing is offset.
# The Left Wing is at X = -124 - 110 = -234? No.
# Main Block Center is 0. Left Edge is -124.
# Left Wing Extension is 110. So Left Wing starts at -124 - 110 = -234?
# Wait, the dimension 110 is from the edge of the main block.
# So Left Wing starts at X = -124 - 110 = -234.
# And goes to X = -124?
# Let's check the Side View (Bottom Left).
# The side view shows the Left Wing extending from the main block.
# The dimension 110 is from the left edge of the main block to the left edge of the wing?
# No, 110 is the length of the wing itself.
# So the wing is from X = -234 to X = -124.
# Width of wing (Depth) is 35.55.
# Height of wing is 205.03.
# Center of wing: X = -124 - 110/2 = -179.
# Y (Depth) = 0.
# Z (Height) = 0.

# Sketch 2: Left Wing Base
sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_LeftWing")
# Attach to the top face of the Main Block (Z = MainHeight/2)
sketch2.Placement = App.Placement(App.Vector(-179, 0, params.MainHeight.Value / 2)) # Center of wing
sketch2.Placement.Rotation = App.Rotation(0, 0, 0) # Face Z (Same orientation as Main Block)
# Wait, the wing is attached to the side of the main block, not the top.
# The Front View (Bottom Right) shows the wing on the side.
# So the sketch should be on the XZ plane (Y = 0).
# The Main Block is at Y = 0 to Y = 224.
# The Left Wing is at Y = 0 to Y = 35.55?
# Let's look at the Side View (Bottom Left).
# The side view shows the wing extending to the left.
# The depth of the wing (35.55) is less than the depth of the main block (224).
# So the wing is centered on the main block's depth?
# Yes, it looks like it's aligned with the center.
# So the sketch should be on the XZ plane (Y = 0).
# Center of wing: X = -179, Y = 0, Z = params.LeftHeight.Value / 2.
# Orientation: Face Y (0, 1, 0) or Face Z (0, 0, 1)?
# The wing is a block, so we sketch the profile on the XZ plane (Y=0) and pad along Y?
# Or sketch on the XZ plane (Y=0) and pad along Z?
# Let's sketch on the XZ plane (Y=0) and pad along Y (Depth).
# Sketch 2: Left Wing Base
sketch2.Placement = App.Placement(App.Vector(-179, 0, params.LeftHeight.Value / 2))
sketch2.Placement.Rotation = App.Rotation(0, 0, 0) # Face Y (0, 1, 0) -> No, Rotation(0, 90, 0) faces Z.
# Let's set sketch to face Y (0, 1, 0) -> Rotation(90, 0, 0).
# Then we pad along Y.
# But the wing is attached to the side of the main block.
# The side of the main block is at X = -124.
# The wing extends from X = -234 to X = -124.
# So the sketch should be on the XZ plane (Y=0).
# Sketch 2: Left Wing Base
sketch2.Placement = App.Placement(App.Vector(-179, 0, params.LeftHeight.Value / 2))
sketch2.Placement.Rotation = App.Rotation(0, 0, 0) # Face Y (0, 1, 0) -> No, Rotation(0, 0, 0) faces Z.
# Let's use the standard XY plane and translate.
# Sketch 2: Left Wing Base
sketch2.Placement = App.Placement(App.Vector(-179, 0, params.LeftHeight.Value / 2))
sketch2.Placement.Rotation = App.Rotation(0, 0, 0) # Face Z
# Draw Left Wing Profile (Width x Height)
# Width: LeftExt (110) -> X axis
# Height: LeftHeight (205.03) -> Z axis
# Center: -179, 0, 102.515
# Line 1: (-179, 102.515, 0) to (-179+110/2, 102.515, 0) -> (-179, 102.515, 0) to (-173.5, 102.515, 0)
# Wait, let's draw the profile.
# Left Wing is a block.
# Profile: Rectangle (LeftExt x LeftHeight).
# Center: (-179, 102.515)
# Line 1: (-179, 102.515) to (-179 - 110/2, 102.515) -> (-179, 102.515) to (-194.5, 102.515)
# Line 2: (-194.5, 102.515) to (-194.5, 102.515 + 205.03/2) -> (-194.5, 102.515) to (-194.5, 205.035)
# Line 3: (-194.5, 205.035) to (-179 + 110/2, 205.035) -> (-194.5, 205.035) to (-173.5, 205.035)
# Line 4: (-173.5, 205.035) to (-173.5, 102.515) -> (-173.5, 205.035) to (-173.5, 102.515)
# But wait, the wing is attached to the main block.
# The main block is at X = -124 to 124.
# The wing is at X = -234 to -124.
# So the wing is attached at X = -124.
# The sketch should be on the XZ plane (Y=0).
# Sketch 2: Left Wing Base
sketch2.Placement = App.Placement(App.Vector(-179, 0, params.LeftHeight.Value / 2))
sketch2.Placement.Rotation = App.Rotation(0, 0, 0) # Face Z
# Draw Left Wing Profile
sketch2.addGeometry(Part.LineSegment(App.Vector(-179 - params.LeftExt.Value / 2, 0, 0), App.Vector(-179 - params.LeftExt.Value / 2, 0, 0)), False) # Just a point
# Let's draw the profile properly.
# Profile: Rectangle (LeftExt x LeftHeight)
# Center: (-179, 102.515)
# Line 1: (-194.5, 102.515) to (-194.5, 205.035)
# Line 2: (-1
