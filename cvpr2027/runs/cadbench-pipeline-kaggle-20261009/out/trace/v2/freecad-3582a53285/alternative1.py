import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
SCRIPT_PATH = Path(__file__).resolve()
OUTPUT_PATH = SCRIPT_PATH.with_name("answer.FCStd")

# Create a new document
doc = App.newDocument("Washer")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We use a VarSet to hold parameters that can be edited in the GUI
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "washer_width", "Dimensions", "Outer square width")
params.addProperty("App::PropertyLength", "washer_thickness", "Dimensions", "Plate thickness")
params.addProperty("App::PropertyLength", "washer_inner_hole_diameter", "Dimensions", "Center hole diameter")

# Set default values as requested
params.washer_width = 40.0
params.washer_thickness = 5.0
params.washer_inner_hole_diameter = 7.5

# --- Base Sketch (Outer Profile) ---
# Place sketch on XY plane, centered at origin
sketch_outer = body.newObject("Sketcher::SketchObject", "SketchOuter")
sketch_outer.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
sketch_outer.MapMode = "FlatFace"
sketch_outer.ConstraintsType = "Sketcher::NoConstraint" # Disable auto constraints initially

# Create geometry: Square centered at (0,0)
# Side length = washer_width
# Vertices: (w/2, w/2), (-w/2, w/2), (-w/2, -w/2), (w/2, -w/2)
w = params.washer_width
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-w/2, -w/2, 0), App.Vector(w/2, -w/2, 0)), False)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(w/2, -w/2, 0), App.Vector(w/2, w/2, 0)), False)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(w/2, w/2, 0), App.Vector(-w/2, w/2, 0)), False)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(-w/2, w/2, 0), App.Vector(-w/2, -w/2, 0)), False)

# --- Hole Sketch ---
# Place sketch on XY plane, centered at origin (coincident with outer)
sketch_hole = body.newObject("Sketcher::SketchObject", "SketchHole")
sketch_hole.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
sketch_hole.MapMode = "FlatFace"

d = params.washer_inner_hole_diameter
sketch_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), d/2), False)

# --- Features ---

# 1. Pad (Extrude Outer Square)
pad = body.newObject("PartDesign::Pad", "PadBase")
pad.Profile = sketch_outer
pad.Length = params.washer_thickness
pad.Type = "Solid"

# 2. Pocket (Cut Hole)
pocket = body.newObject("PartDesign::Pocket", "PocketHole")
pocket.Profile = sketch_hole
pocket.Type = "ThroughAll"
pocket.MidPlane = False # Standard ThroughAll removes the face entirely

# 3. Fillet (Corner Radius)
# Add a fillet to the vertical edges of the pad. 
# Since we are in PartDesign, we select the Edges of the Pad feature.
# We will fillet the 4 vertical edges.
fillet = body.newObject("PartDesign::Fillet", "FilletCorners")
fillet.Radius = 1.0 # Example radius, could be parameterized if desired
# Note: In PartDesign, Fillet usually selects edges of the result of previous features.
# We select the edges of the Pad feature.
fillet.Base = (pad, ["Edge1", "Edge2", "Edge3", "Edge4"])

# --- Finalize ---
# Ensure all features are recomputed to update the solid
doc.recompute()

# Save the file
# The prompt requires saving next to the script using the script stem.
# Since the script is named answer.py, the file should be answer.FCStd.
# We ensure the path is absolute based on __file__.
doc.saveAs(str(OUTPUT_PATH))

print(f"Model saved to: {OUTPUT_PATH}")
