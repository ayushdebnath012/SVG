import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Washer")

# --- Parameters ---
# In FreeCAD 1.1, parameters are typically stored as App::PropertyLength/Float inside 
# a PartDesign::Body or a dedicated App::VarSet, not as App::Parameter objects directly 
# in the document root for this specific API pattern. 
# We will create a VarSet inside the Body to hold our named parameters.

body = doc.addObject("PartDesign::Body", "Body")

# Create a parameter container
params = body.newObject("App::VarSet", "Parameters")

# Define parameters
# washer_diameter: 60.0
param_dia = params.newObject("App::PropertyLength", "p_diameter")
param_dia.Value = 60.0

# washer_thickness: 10.0
param_thick = params.newObject("App::PropertyLength", "p_thickness")
param_thick.Value = 10.0

# square_neck_hole_width: 20.0
param_hole = params.newObject("App::PropertyLength", "p_hole_width")
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
# Attach to the same XY plane but offset slightly in Z to ensure valid placement 
# before the body has any faces.
sketch_inner = body.newObject("Sketcher::SketchObject", "Sketch_Inner")
sketch_inner.Placement = App.Placement(App.Vector(0, 0, 0.01))
sketch_inner.ConstrainToCurrentPlane = True
sketch_inner.MapMode = "FlatFace"

# Add square geometry
# Center at (0,0), Width = param_hole_width
half_width = param_hole_width.Value / 2.0
# Create a square using 4 lines
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
