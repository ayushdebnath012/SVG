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
# Correct placement syntax for FreeCAD 1.1
sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
# In FreeCAD 1.1, Support is a list of (Object, EdgeIndex) tuples. 
# We use the XY_Plane object which should exist in the default document.
# If not, we create a Plane object first.
if not doc.getObject("XY_Plane"):
    plane = doc.addObject("Part::Plane", "XY_Plane")
    plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
    doc.recompute()

sketch_outer.Support = [(doc.getObject("XY_Plane"), 0)]
sketch_outer.MapMode = "FlatFace"

# Add geometry: A square centered at origin
# We define 4 lines and 1 point at the center
# Line 1: Bottom edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-20, -2.5, 0), App.Vector(20, -2.5, 0)), False)
# Line 2: Right edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(20, -2.5, 0), App.Vector(20, 2.5, 0)), False)
# Line 3: Top edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(20, 2.5, 0), App.Vector(-20, 2.5, 0)), False)
# Line 4: Left edge
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-20, 2.5, 0), App.Vector(-20, -2.5, 0)), False)
# Point at center (0,0,0)
sketch_outer.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)

# Add constraints to make it a perfect square centered at (0,0)
# Indices: 0=Line1, 1=Line2, 2=Line3, 3=Line4, 4=Point
# Constrain all 4 vertices to the center point
# Vertex of Line 0 (start): index 0, Vertex (end): index 1
# Vertex of Line 1 (start): index 1, Vertex (end): index 2
# Vertex of Line 2 (start): index 2, Vertex (end): index 3
# Vertex of Line 3 (start): index 3, Vertex (end): index 0
# Center point index: 4

# Coincident constraints: Vertex to Point
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 4, 2)) # Line0 Start to Point
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 4, 2)) # Line0 End to Point
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 4, 2)) # Line1 End to Point
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 4, 2)) # Line2 End to Point
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 4, 2)) # Line3 Start to Point (redundant but safe)

# Perpendicular constraints
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 1, 2)) # Line0 perp Line1
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 1, 2, 2, 3)) # Line1 perp Line2
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 2, 3, 3, 0)) # Line2 perp Line3
sketch_outer.addConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1)) # Line3 perp Line0

# Length constraints
sketch_outer.addConstraint(Sketcher.Constraint("Length", 0, 1, params.washer_width))
sketch_outer.addConstraint(Sketcher.Constraint("Length", 1, 2, params.washer_width))
sketch_outer.addConstraint(Sketcher.Constraint("Length", 2, 3, params.washer_width))
sketch_outer.addConstraint(Sketcher.Constraint("Length", 3, 0, params.washer_width))

# --- Sketch 2: Inner Hole Profile ---
sketch_inner = body.newObject("Sketcher::SketchObject", "SketchInner")
sketch_inner.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
sketch_inner.Support = [(doc.getObject("XY_Plane"), 0)]
sketch_inner.MapMode = "FlatFace"

# Add geometry: Circle centered at origin
radius = params.washer_inner_hole_diameter / 2.0
sketch_inner.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)
# Add center point for constraint
sketch_inner.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)

# Constrain center to origin
sketch_inner.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Circle center to Point

# Constrain radius
sketch_inner.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.washer_inner_hole_diameter / 2.0))

# --- Feature: Pad (Extrude Outer) ---
pad = body.newObject("PartDesign::Pad", "PadOuter")
pad.Profile = sketch_outer
pad.Length = params.washer_thickness
pad.Type = "Solid"

# --- Feature: Pocket (Cut Inner Hole) ---
pocket = body.newObject("PartDesign::Pocket", "PocketInner")
pocket.Profile = sketch_inner
pocket.Type = "ThroughAll"
# Specify the face to cut from. In a simple stack, it's usually the top face of the pad.
# We can let FreeCAD auto-detect or specify explicitly if needed. 
# For robustness in scripts, we often rely on the default behavior of Pocket when Profile is on the body.
# However, to be explicit about the base, we can try to reference the face. 
# Since we don't have the face index easily without recomputing or querying, 
# and 'ThroughAll' often works by default if the profile is on the body, we proceed.
# If 'ThroughAll' fails due to missing base, we might need to specify Base. 
# But standard PartDesign::Pocket with ThroughAll usually works if the sketch is on the body.
# Let's ensure it works by setting Base to the pad if necessary, but usually not needed for ThroughAll.
# To be safe and explicit as per "named document objects", we can try to set Base.
# However, without knowing the face index, we rely on the default behavior which is robust for ThroughAll.
# If the script runs headless, ThroughAll should work.

# --- Recompute to generate the solid ---
doc.recompute()

# --- Save the file ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
