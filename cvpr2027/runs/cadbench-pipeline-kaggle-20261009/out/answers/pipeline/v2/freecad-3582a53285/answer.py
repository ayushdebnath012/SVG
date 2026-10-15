import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Washer")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a VarSet to hold named parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "washer_width", "Dimensions", "Outer square width")
params.addProperty("App::PropertyLength", "washer_thickness", "Dimensions", "Plate thickness")
params.addProperty("App::PropertyLength", "washer_inner_hole_diameter", "Dimensions", "Central hole diameter")

# Set default values
params.washer_width = 40.0
params.washer_thickness = 5.0
params.washer_inner_hole_diameter = 7.5

# --- Sketch 1: Outer Square Profile ---
sketch_outer = body.newObject("Sketcher::SketchObject", "SketchOuter")
sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_outer.Support = "XY_Plane"
sketch_outer.MapMode = "FlatFace"

# Add geometry: A square centered at origin
# Line 1: Bottom edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-20, -2.5, 0), App.Vector(20, -2.5, 0)), False)
# Line 2: Right edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(20, -2.5, 0), App.Vector(20, 2.5, 0)), False)
# Line 3: Top edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(20, 2.5, 0), App.Vector(-20, 2.5, 0)), False)
# Line 4: Left edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-20, 2.5, 0), App.Vector(-20, -2.5, 0)), False)

# Add constraints to make it a perfect square centered at (0,0)
# Coincident all 4 corners to origin (0,0,0)
# Note: Sketcher indices are 0-based. 
# Points: 0:(-20,-2.5), 1:(20,-2.5), 2:(20,2.5), 3:(-20,2.5)
# We constrain all points to be coincident with the origin point (0,0,0) which is index 4 (implicit) or we can just constrain relative to each other.
# Simpler approach: Constrain all points to be coincident with each other relative to the center? 
# Actually, standard way: Constrain all 4 points to be coincident with a single point (0,0,0).
# In FreeCAD Sketcher, we can add a point at origin and constrain, or just constrain geometry.
# Let's constrain the 4 vertices to be coincident with the origin (0,0,0). 
# However, the origin isn't explicitly added as a geometry object in the sketch list usually unless added.
# Alternative: Constrain the center of the square to (0,0).
# Let's use the standard "Coincident" constraint between the 4 vertices and a single point at (0,0,0).
# Since we didn't add a point, let's just constrain the geometry to form a square centered at 0,0.
# We can constrain the midpoint of opposite sides to be coincident? No.
# Best way in script: Constrain all 4 vertices to be coincident with a point at (0,0,0).
# We need to add a point at (0,0,0) first.
sketch_outer.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
# Now constrain vertices 0,1,2,3 to point 4
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 4, 2)) # Pt 0 to Pt 4
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 4, 2)) # Pt 1 to Pt 4
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 4, 2)) # Pt 2 to Pt 4
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 4, 2)) # Pt 3 to Pt 4

# Constrain sides to be perpendicular
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 1, 2)) # Line 0 perp to Line 1
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 1, 2, 2, 3))
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 2, 3, 3, 0))
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1))

# Constrain lengths to be equal (Square)
# Length of line 0
sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 1, params.washer_width))
# Length of line 1
sketch_outer.addConstraint(Sketcher.Constraint("Length", 1, 2, params.washer_width))
# Length of line 2
sketch_outer.addConstraint(Sketcher.Constraint("Length", 2, 3, params.washer_width))
# Length of line 3
sketch_outer.addConstraint(Sketcher.Constraint("Length", 3, 0, params.washer_width))

# --- Sketch 2: Inner Hole Profile ---
sketch_inner = body.newObject("Sketcher::SketchObject", "SketchInner")
sketch_inner.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_inner.Support = "XY_Plane"
sketch_inner.MapMode = "FlatFace"

# Add geometry: Circle centered at origin
# Radius = diameter / 2
radius = params.washer_inner_hole_diameter / 2.0
sketch_inner.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)

# Constrain center to origin (0,0,0) - Point index 0
sketch_inner.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
sketch_inner.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Circle center to Point

# Constrain radius
sketch_inner.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.washer_inner_hole_diameter / 2.0))

# --- Feature: Pad (Extrude Outer) ---
pad = body.newObject("PartDesign::Pad", "PadOuter")
pad.Profile = sketch_outer
pad.Length = params.washer_thickness
pad.Type = "Solid" # Ensure it's a solid pad

# --- Feature: Pocket (Cut Inner Hole) ---
pocket = body.newObject("PartDesign::Pocket", "PocketInner")
pocket.Profile = sketch_inner
pocket.Type = "ThroughAll" # Cut all the way through
pocket.Base = (pad, ["Face1"]) # Cut from the face created by the pad

# --- Recompute to generate the solid ---
doc.recompute()

# --- Save the file ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
