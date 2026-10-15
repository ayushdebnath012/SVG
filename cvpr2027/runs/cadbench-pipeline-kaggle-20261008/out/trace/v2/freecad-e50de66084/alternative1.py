import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("DeepGrooveBearing")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Section ---
# We use a generic VarSet to hold named parameters as requested for a clean tree.
params = body.newObject("App::VarSet", "Parameters")

# Define parameters based on the task description
# bore_diameter: Inner opening
params.addProperty("App::PropertyLength", "bore_diameter", "Parameters", "Bore diameter")
params.bore_diameter = 0.6

# bearing_width: Axial thickness
params.addProperty("App::PropertyLength", "bearing_width", "Parameters", "Bearing width")
params.bearing_width = 0.8

# ball_diameter: Determines raceway curvature
params.addProperty("App::PropertyLength", "ball_diameter", "Parameters", "Ball diameter")
params.ball_diameter = 0.38888888888889

# raceway_depth_ratio: Factor for groove depth relative to ball diameter
params.addProperty("App::PropertyFloat", "raceway_depth_ratio", "Parameters", "Raceway depth ratio")
params.raceway_depth_ratio = 0.4

# shoulder_diameter: Outer diameter (must be > bore and > ball)
params.addProperty("App::PropertyLength", "shoulder_diameter", "Parameters", "Shoulder diameter")
params.shoulder_diameter = 1.0666666666666675

# --- Geometry Construction ---

# 1. Base Cylinder (Body)
# Create sketch on XY plane
sketch_base = body.newObject("Sketcher::SketchObject", "Sk_Base_Cyl")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [""])
sketch_base.MapMode = "FlatFace"

# Outer profile circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shoulder_diameter / 2.0)
sketch_base.addGeometry(outer_circle, False)

# Inner profile circle (Bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
sketch_base.addGeometry(inner_circle, False)

# Constraint: Concentric
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1)) # Coincide centers

# Create the main body (Cylinder)
pad_main = body.newObject("PartDesign::Pad", "Pad_Main_Cylinder")
pad_main.Profile = sketch_base
pad_main.Type = "FullySolid"
# Pad will be extruded along Z axis based on bearing_width

# 2. Raceway Groove (Subtractive Revolution)
# We need a sketch on the XZ plane to create the groove profile rotated around Z.
sketch_groove = body.newObject("Sketcher::SketchObject", "Sk_Groove_Profile")
sketch_groove.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_groove.Support = (doc.getObject("XZ_Plane"), [""])
sketch_groove.MapMode = "FlatFace"

# Groove starts at Bore radius and goes inward to Raceway Depth
# Radius at top = bore_diameter / 2
# Depth = ball_diameter * raceway_depth_ratio
# Radius at bottom = (bore_diameter/2) - Depth

top_radius = params.bore_diameter / 2.0
depth = params.ball_diameter * params.raceway_depth_ratio
bottom_radius = top_radius - depth

# Line 1: Vertical drop from top radius
line_drop = Part.LineSegment(App.Vector(top_radius, 0, 0), App.Vector(top_radius, 0, -depth))
sketch_groove.addGeometry(line_drop, False)

# Line 2: Horizontal movement inward to bottom radius
line_in = Part.LineSegment(App.Vector(top_radius, 0, -depth), App.Vector(bottom_radius, 0, -depth))
sketch_groove.addGeometry(line_in, False)

# Line 3: Vertical rise to center line (for revolution)
line_up = Part.LineSegment(App.Vector(bottom_radius, 0, -depth), App.Vector(bottom_radius, 0, 0))
sketch_groove.addGeometry(line_up, False)

# Close the loop to a full circle profile for revolution
line_close = Part.LineSegment(App.Vector(bottom_radius, 0, 0), App.Vector(top_radius, 0, 0))
sketch_groove.addGeometry(line_close, False)

# Constraint: Coincide points to ensure clean closure (optional but good practice)
# Sketcher constraints for LineSegments are complex, so we rely on the closed loop geometry.

# Create the Revolution feature (Pocket)
# Axis is Z axis. Profile is the groove sketch.
# Angle 360.
groove_rev = body.newObject("PartDesign::Revolution", "Rev_Groove")
groove_rev.Profile = sketch_groove
groove_rev.Placement = App.Placement(App.Vector(0, 0, 0)) # Align sketch origin
groove_rev.ReferenceAxis = (doc.getObject("Z_Axis"), [""])
groove_rev.Angle = 360.0
groove_rev.Type = "Cut" # Subtract material

# Finalize
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
