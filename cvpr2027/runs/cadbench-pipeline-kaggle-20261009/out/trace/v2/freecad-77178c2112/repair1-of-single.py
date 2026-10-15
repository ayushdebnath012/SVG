import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("CylindricalPin")

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Pin Diameter")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Overall Length")
params.addProperty("App::PropertyLength", "chamfer_length", "Dimensions", "Chamfer Length")
params.addProperty("App::PropertyAngle", "chamfer_angle", "Dimensions", "Chamfer Angle")

# Set default values
params.diameter = 1.0
params.length = 3.0
params.chamfer_length = 0.2
params.chamfer_angle = 15.0

# --- Sketch 1: Main Cylinder Profile ---
# We will create the cylinder by revolving a rectangle.
# The sketch will be on the XY plane.
sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_Main")
# Correct Placement initialization for Sketcher::SketchObject
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
sketch_main.Support = (doc.getObject("XY_Plane"), [])
sketch_main.MapMode = "FlatFace"

# Add a rectangle: Center at (0,0), Width = diameter, Height = length/2
# We define the rectangle from -diameter/2 to +diameter/2 on X, and 0 to +length/2 on Y.
# For revolution around Z, the profile must be in the XY plane.
# Line 1: Bottom center to Bottom right
line1 = Part.LineSegment(App.Vector(-params.diameter / 2, 0, 0), App.Vector(params.diameter / 2, 0, 0))
sketch_main.addGeometry(line1, False)

# Line 2: Bottom right to Top right
line2 = Part.LineSegment(App.Vector(params.diameter / 2, 0, 0), App.Vector(params.diameter / 2, params.length / 2, 0))
sketch_main.addGeometry(line2, False)

# Line 3: Top right to Top left
line3 = Part.LineSegment(App.Vector(params.diameter / 2, params.length / 2, 0), App.Vector(-params.diameter / 2, params.length / 2, 0))
sketch_main.addGeometry(line3, False)

# Line 4: Top left to Bottom center (closing the loop)
line4 = Part.LineSegment(App.Vector(-params.diameter / 2, params.length / 2, 0), App.Vector(-params.diameter / 2, 0, 0))
sketch_main.addGeometry(line4, False)

# Constraints
# Horizontal lines
sketch_main.addConstraint(Sketcher.Constraint("Axis", 0, 1, "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 1, 2, "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 2, 3, "X_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 3, 0, "X_Axis"))

# Vertical lines
sketch_main.addConstraint(Sketcher.Constraint("Axis", 0, 1, "Y_Axis"))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 2, 3, "Y_Axis"))

# Coincident points
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0)) # Bottom right
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 0)) # Top right
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 0)) # Top left
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 3, 0, 0, 0)) # Bottom left (center)

# Dimension constraints
# Width = diameter
sketch_main.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.diameter"))
# Height = length / 2
sketch_main.addConstraint(Sketcher.Constraint("Length", 1, 2, "Parameters.length / 2"))

# --- Feature 1: Pad (Cylinder) ---
pad = body.newObject("PartDesign::Pad", "Pad_Cylinder")
pad.Profile = sketch_main
pad.Length = "Parameters.length"
pad.Type = "Solid"

# --- Feature 2: Chamfer ---
# We use the PartDesign::Chamfer feature.
# In a script, we select the top and bottom circular edges of the cylinder.
# Since the Pad creates a cylinder, the edges are the top and bottom circles.
# We assume the first two edges (indices 0 and 1) correspond to these circles.
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer_Ends")
chamfer.Base = (pad, [0, 1])
chamfer.Size = "Parameters.chamfer_length"
chamfer.Angle = "Parameters.chamfer_angle"

# --- Recompute ---
doc.recompute()

# --- Save ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
