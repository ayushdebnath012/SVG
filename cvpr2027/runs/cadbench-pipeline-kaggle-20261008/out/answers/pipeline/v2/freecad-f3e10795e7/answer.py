import FreeCAD as App
import Part
from pathlib import Path
import os

# Ensure we are in the correct directory for saving
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Create a new document
doc = App.newDocument("FrustumPart")

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a VarSet to hold parameters
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "top_diameter", "Dimensions", "Top diameter of the frustum")
params.addProperty("App::PropertyLength", "bottom_diameter", "Dimensions", "Bottom diameter of the frustum")
params.addProperty("App::PropertyLength", "height", "Dimensions", "Height of the frustum")

# Set default values
params.top_diameter = 15.0
params.bottom_diameter = 25.0
params.height = 30.0

# Create the base sketch on XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch.MapMode = "FlatFace"
sketch.ConstrainAuto = True
sketch.ConstrainFully = True

# Add geometry: Two concentric circles representing the top and bottom rims
# We will define the profile as a closed loop. 
# Strategy: Create a large circle (bottom) and a small circle (top) offset by height/2? 
# No, standard frustum sketch is usually a trapezoid or two arcs.
# Let's create a profile sketch on the XZ plane for revolution.
# Actually, the prompt asks for a frustum. A frustum is a truncated cone.
# Best approach for PartDesign: Sketch the profile (trapezoid) on XZ plane and Revolve.

# Let's switch to XZ plane for the profile sketch
sketch2 = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.AttachmentSupport = (doc.getObject("XZ_Plane"), [])
sketch2.MapMode = "FlatFace"
sketch2.ConstrainAuto = True
sketch2.ConstrainFully = True

# We need to construct the trapezoid profile.
# Center at (0,0). Bottom radius = bottom_diameter/2. Top radius = top_diameter/2.
# Height = height.
# Points: 
# 1. Bottom Left: (-bottom_diameter/2, 0)
# 2. Bottom Right: (bottom_diameter/2, 0)
# 3. Top Right: (top_diameter/2, height)
# 4. Top Left: (-top_diameter/2, height)

# Helper to get expression string
def get_expr(val):
    return f"Parameters.{val}"

# Add lines to form the trapezoid
# Line 1: Bottom edge
l1 = Part.LineSegment(App.Vector(-params.bottom_diameter / 2, 0, 0), App.Vector(params.bottom_diameter / 2, 0, 0))
sketch2.addGeometry(l1, False)

# Line 2: Right slanted edge
l2 = Part.LineSegment(App.Vector(params.bottom_diameter / 2, 0, 0), App.Vector(params.top_diameter / 2, params.height, 0))
sketch2.addGeometry(l2, False)

# Line 3: Top edge
l3 = Part.LineSegment(App.Vector(params.top_diameter / 2, params.height, 0), App.Vector(-params.top_diameter / 2, params.height, 0))
sketch2.addGeometry(l3, False)

# Line 4: Left slanted edge
l4 = Part.LineSegment(App.Vector(-params.top_diameter / 2, params.height, 0), App.Vector(-params.bottom_diameter / 2, 0, 0))
sketch2.addGeometry(l4, False)

# Add constraints to make it fully defined
# Coincident points for corners
# Corner 1 (Bottom Left): Line 1 start, Line 4 end
sketch2.addConstraint(Sketcher.Constraint("Point", 0, 1, "XY")) # Point on X axis
sketch2.addConstraint(Sketcher.Constraint("Point", 3, 1, "XY")) # Point on X axis
sketch2.addConstraint(Sketcher.Constraint("Point", 0, 2, "XZ")) # Point on Z axis
sketch2.addConstraint(Sketcher.Constraint("Point", 3, 2, "XZ")) # Point on Z axis

# Horizontal lines (Bottom and Top)
sketch2.addConstraint(Sketcher.Constraint("Horizontal", 0)) # Bottom line
sketch2.addConstraint(Sketcher.Constraint("Horizontal", 2)) # Top line

# Vertical alignment of centers (implicitly handled by symmetry if we constrain midpoints or use symmetry constraint)
# Let's add symmetry constraint for the whole sketch to ensure it's centered
sketch2.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 2, 1, 3, 1)) # Symmetry around Z axis for the shape

# Link dimensions to parameters
# Bottom width
sketch2.addConstraint(Sketcher.Constraint("Length", 0, 1, get_expr("bottom_diameter")))
# Top width
sketch2.addConstraint(Sketcher.Constraint("Length", 2, 3, get_expr("top_diameter")))
# Height
sketch2.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, get_expr("height"))) # Distance between bottom line and top line along Z

# Create the Revolution feature
rev = body.newObject("PartDesign::Revolution", "Revolution")
rev.Profile = sketch2
rev.ReferenceAxis = (doc.getObject("Z_Axis"), [])
rev.Angle = 360.0
rev.Tangent = False
rev.Reverse = False

# Recompute to generate the solid
doc.recompute()

# Save the file
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
