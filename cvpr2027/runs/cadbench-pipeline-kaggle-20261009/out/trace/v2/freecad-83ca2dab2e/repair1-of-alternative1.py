import FreeCAD as App
import Part
from pathlib import Path

# --- Configuration ---
# Parameters are defined as document properties to allow editing in the GUI
doc = App.newDocument("BallJoint")

# 1. Create Named Parameters
# In FreeCAD 1.1, parameters are created using App::PropertyLength, App::PropertyFloat, etc.
# We create them and set their values immediately.
doc.addObject("App::PropertyLength", "ShaftDia").ShaftDia = 4.0
doc.addObject("App::PropertyLength", "ShaftLen").ShaftLen = 5.9
doc.addObject("App::PropertyLength", "BallDia").BallDia = 5.0
doc.addObject("App::PropertyLength", "HoleDia").HoleDia = 2.0
doc.addObject("App::PropertyLength", "HoleDepth").HoleDepth = 10.0

# 2. Create the PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# 3. Create Base Sketch (Shaft Profile)
# Plane: XY (bottom)
sketch_shaft = body.newObject("Sketcher::SketchObject", "Shaft_Sketch")
sketch_shaft.Plane = "XY_Plane"

# Draw a vertical line representing the shaft cross-section on the XY plane
# Since the shaft is vertical (Z-axis), we sketch on XY.
# Line from (-2, 0) to (2, 0) represents diameter 4.0
l1 = Part.LineSegment(App.Vector(-2.0, 0, 0), App.Vector(2.0, 0, 0))
sketch_shaft.addGeometry(l1, False)

# Add constraint to define the length parameter relation later via expression or just dimension
# We will use a dimension constraint to link to ShaftLen? No, let's keep it simple 
# and use Pad length driven by expression. The sketch defines the cross-section.

# Add Coincident to origin for stability
sketch_shaft.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "Origin", 0, 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Coincident", 0, 2, "XY_Plane", "Origin", 1))

# 4. Create Shaft Feature (Pad)
# Pad from 0 to ShaftLen
pad_shaft = body.newObject("PartDesign::Pad", "Shaft_Pad")
pad_shaft.Profile = sketch_shaft
pad_shaft.Length = "ShaftLen" # Driven by parameter
pad_shaft.Direction = App.Vector(0, 0, 1) # Extend along Z

# 5. Create Ball Sketch
# We need to offset the sketch to the top of the shaft.
# The shaft ends at Z = 5.9. We want the ball centered there, so the sketch plane should be at Z=5.9.
# Since standard planes don't exist at arbitrary Z, we create a sketch on XY_Plane but lift it.

sketch_ball = body.newObject("Sketcher::SketchObject", "Ball_Sketch")
sketch_ball.Plane = "XY_Plane"
sketch_ball.AttachmentOffset = "ShaftLen" # Lift to top of shaft
# Now sketch a circle. Diameter = 5.0.
# Center at (0,0) in local coords, but since it's on XY plane lifted to Z, it sits on the face.
# Wait, if we lift the sketch, it sketched on the face at Z=5.9.
# Circle radius = 2.5.
c1 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2.5)
sketch_ball.addGeometry(c1, False)

# 6. Create Ball Feature (Pad)
# Pad from top of shaft upwards. Length = BallDia.
pad_ball = body.newObject("PartDesign::Pad", "Ball_Pad")
pad_ball.Profile = sketch_ball
pad_ball.Length = "BallDia"
pad_ball.Direction = App.Vector(0, 0, 1)

# 7. Create Hole Sketch
# We need a hole centered on the Z axis.
# The hole starts at Z=0 (bottom of shaft) and goes depth.
# Sketch on XY_Plane at Z=0.
sketch_hole = body.newObject("Sketcher::SketchObject", "Hole_Sketch")
sketch_hole.Plane = "XY_Plane"
# No offset needed as it's at the base.
h_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), "HoleDia")
sketch_hole.addGeometry(h_circ, False)

# 8. Create Hole Feature (Pocket)
# Type: ThroughAll? No, depth is specified.
# But standard Pocket is subtractive.
pocket = body.newObject("PartDesign::Pocket", "Hole_Pocket")
pocket.Profile = sketch_hole
pocket.Length = "HoleDepth"
pocket.Type = "Blind" # Use Blind to respect the Length parameter
pocket.Direction = App.Vector(0, 0, 1) # Cut upwards from the bottom sketch

# 9. Compute
doc.recompute()

# --- Save ---
# Determine output path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_suffix(".FCStd")

# Save the document
doc.saveAs(str(output_path))

# Clean up document name in title if desired
App.ActiveDocument = doc
print(f"Ball Joint model saved to: {output_path}")
