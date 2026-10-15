import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Washer")

# --- Parameters ---
# We will use App::Parameter objects to store the dimensions so they are editable in the tree.
# Note: In FreeCAD 1.1, App::Parameter is the standard way to define named variables.

# 1. Create a container for parameters if it doesn't exist, or just add to Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
# washer_diameter: 60.0
param_dia = body.newObject("App::Parameter", "p_diameter")
param_dia.Value = 60.0

# washer_thickness: 10.0
param_thick = body.newObject("App::Parameter", "p_thickness")
param_thick.Value = 10.0

# square_neck_hole_width: 20.0
param_hole = body.newObject("App::Parameter", "p_hole_width")
param_hole.Value = 20.0

# --- Sketch 1: Outer Circle ---
sketch_outer = body.newObject("Sketcher::SketchObject", "Sketch_Outer")
sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_outer.ConstrainToCurrentPlane = True
sketch_outer.MapMode = "FlatFace"

# Add circle geometry
# Center at (0,0), Radius = Diameter / 2
radius = param_dia.Value / 2.0
circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
sketch_outer.addGeometry(circle_geom, False)

# --- Sketch 2: Inner Square Hole ---
# We need to place this sketch on the same plane (XY) but offset Z slightly or use a different plane.
# Since PartDesign sketches must be on a face, and the body is empty, we attach to the XY plane.
# To keep it simple and robust, we create a second sketch on the same XY plane but offset Z by a tiny amount 
# or simply reuse the plane. However, PartDesign requires sketches to be on a face of a solid or a plane.
# Since we haven't extruded yet, we attach to the XY_Plane.
# To avoid Z-intersection issues during sketch creation, we can offset the sketch slightly in Z.

sketch_inner = body.newObject("Sketcher::SketchObject", "Sketch_Inner")
sketch_inner.Placement = App.Placement(App.Vector(0, 0, 0.01)) # Slight offset to ensure valid placement on plane
sketch_inner.ConstrainToCurrentPlane = True
sketch_inner.MapMode = "FlatFace"

# Add square geometry
# Center at (0,0), Width = param_hole_width
half_width = param_hole_width.Value / 2.0
# Create a square using 4 lines or a single polygon. 
# Using 4 lines for clarity in constraints.
p1 = App.Vector(-half_width, -half_width, 0)
p2 = App.Vector(half_width, -half_width, 0)
p3 = App.Vector(half_width, half_width, 0)
p4 = App.Vector(-half_width, half_width, 0)

line1 = Part.LineSegment(p1, p2)
line2 = Part.LineSegment(p2, p3)
line3 = Part.LineSegment(p3, p4)
line4 = Part.LineSegment(p4, p1)

sketch_inner.addGeometry(line1, False)
sketch_inner.addGeometry(line2, False)
sketch_inner.addGeometry(line3, False)
sketch_inner.addGeometry(line4, False)

# --- Feature 1: Pad (Washer Body) ---
pad = body.newObject("PartDesign::Pad", "Pad_Washer")
pad.Profile = sketch_outer
pad.Length = param_thick.Value
pad.Type = "Solid"
pad.MidPlane = False
pad.Reverse = False

# --- Feature 2: Pocket (Square Hole) ---
pocket = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket.Profile = sketch_inner
pocket.Type = "ThroughAll" # Cuts all the way through
pocket.Clean = True

# --- Finalize ---
doc.recompute()

# Save the file
# The output path must be derived from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
