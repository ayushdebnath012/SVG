"""
FreeCAD 1.1 Script to generate a round mounting flange.
Saves to /app/answer.FCStd derived from __file__.
"""

import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
PARAMS = {
    "outer_diameter": 66.675,
    "flange_thickness": 13.49375,
    "pitch_circle_diameter": 53.18125,
    "bolt_hole_diameter": 6.746875,
    "number_bolt_holes": 4,
    "inner_diameter": 25.4
}

# --- Document Setup ---
doc = App.newDocument("FlangePart")

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# --- Parameters Object ---
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter")
params.outer_diameter = PARAMS["outer_diameter"]
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness")
params.flange_thickness = PARAMS["flange_thickness"]
params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "PCD")
params.pitch_circle_diameter = PARAMS["pitch_circle_diameter"]
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Bolt Hole Dia")
params.bolt_hole_diameter = PARAMS["bolt_hole_diameter"]
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Count")
params.number_bolt_holes = PARAMS["number_bolt_holes"]
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner Dia")
params.inner_diameter = PARAMS["inner_diameter"]

# --- Feature 1: Main Flange Body (Pad) ---
sketch_flange = body.newObject("Sketcher::SketchObject", "FlangeProfile")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.ConstrainAuto = False
sketch_flange.MapMode = "FlatFace"
sketch_flange.Support = (doc.getObject("XY_Plane"), [])

# Add Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["outer_diameter"] / 2.0)
sketch_flange.addGeometry(outer_circle, False)

# Add Inner Circle
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["inner_diameter"] / 2.0)
sketch_flange.addGeometry(inner_circle, False)

# Constraints: Concentric
sketch_flange.addConstraint(Sketcher.Constraint("Point", 0, "CenterXY", 0, 0))
sketch_flange.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"))

pad_flange = body.newObject("PartDesign::Pad", "PadFlange")
pad_flange.Profile = sketch_flange
pad_flange.Length = PARAMS["flange_thickness"]
pad_flange.Type = "Full"
pad_flange.Join = "Join"

# --- Helper to get top face index ---
def get_top_face_index(feature):
    shape = feature.Shape
    for i, face in enumerate(shape.Faces):
        if abs(face.normalAt(App.Vector(0,0,1)).z) > 0.99:
            return i
    return -1

# --- Feature 2: Central Through Hole (Pocket) ---
# Create a plane at the top of the flange to host the sketch
plane_obj = doc.addObject("Part::Plane", "HolePlane")
plane_obj.Placement = App.Placement(App.Vector(0, 0, PARAMS["flange_thickness"]/2))
doc.recompute()

sketch_hole = body.newObject("Sketcher::SketchObject", "HoleProfile")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hole.MapMode = "FlatFace"
sketch_hole.AttachmentSupport = (plane_obj, [""])

hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["inner_diameter"] / 2.0)
sketch_hole.addGeometry(hole_circle, False)
sketch_hole.addConstraint(Sketcher.Constraint("Point", 0, "CenterXY", 0, 0))

pocket_hole = body.newObject("PartDesign::Pocket", "PocketCentralHole")
pocket_hole.Profile = sketch_hole
pocket_hole.Type = "ThroughAll"
pocket_hole.Join = "Join"

# --- Feature 3: Bolt Holes (Pattern) ---
# Create a plane for the bolt sketch (same Z level)
# We can reuse the plane object or create a new one. Let's create a new one to be safe.
plane_bolt = doc.addObject("Part::Plane", "BoltPlane")
plane_bolt.Placement = App.Placement(App.Vector(0, 0, PARAMS["flange_thickness"]/2))
doc.recompute()

sketch_bolt = body.newObject("Sketcher::SketchObject", "BoltHoleProfile")
sketch_bolt.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bolt.MapMode = "FlatFace"
sketch_bolt.AttachmentSupport = (plane_bolt, [""])

bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["bolt_hole_diameter"] / 2.0)
sketch_bolt.addGeometry(bolt_circle, False)
sketch_bolt.addConstraint(Sketcher.Constraint("Point", 0, "CenterXY", 0, 0))

# Create the single pocket for the pattern
pocket_bolt_single = body.newObject("PartDesign::Pocket", "BoltHoleSingle")
pocket_bolt_single.Profile = sketch_bolt
pocket_bolt_single.Type = "Blind"
pocket_bolt_single.Length = PARAMS["flange_thickness"]
pocket_bolt_single.Join = "Join"

# Position the single pocket on the Pitch Circle Diameter
radius_pcd = PARAMS["pitch_circle_diameter"] / 2.0
pocket_bolt_single.Placement = App.Placement(
    App.Vector(radius_pcd, 0.0, 0.0),
    App.Rotation(App.Vector(0, 0, 1), 0)
)

# --- Polar Pattern ---
pattern = body.newObject("PartDesign::PolarPattern", "BoltHolePattern")
pattern.Originals = (pocket_bolt_single, [""])
pattern.Axis = (doc.getObject("Z_Axis"), [""])
pattern.Angle = 360.0
pattern.Occurrences = PARAMS["number_bolt_holes"]

# --- Save ---
# Ensure the script path is used
script_path = Path(__file__).resolve()
output_path = script_path.with_suffix(".FCStd")

doc.recompute()
doc.saveAs(str(output_path))
