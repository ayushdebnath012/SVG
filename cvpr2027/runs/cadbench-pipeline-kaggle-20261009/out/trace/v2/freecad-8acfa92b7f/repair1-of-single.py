import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("SlipOnFlange")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Body placement is handled by the document context, default is (0,0,0)
# We do not set Placement directly on the Body object in this manner.

# --- Parameters ---
# Define dimensions as local variables for clarity, 
# but in a real parametric script, these would be App::PropertyLength objects on the Body.
# For this specific request to build the geometry correctly, we use the values directly.
outer_circle_diameter = 108.0
flange_thickness = 12.2
total_height = 17.5
bore_diameter = 34.5
hub_diameter = 50.8
raised_face_diameter = 49.3
raised_face_thickness = 2.0
bolt_circle_diameter = 79.2
bolt_hole_diameter = 15.7
number_bolt_holes = 4

# --- Base Sketch (Outer Profile) ---
# Ensure XY plane exists
if "XY_Plane" not in doc.Objects:
    xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
    doc.recompute()

sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [])
sketch_base.MapMode = "FlatFace"

# Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), outer_circle_diameter / 2.0)
sketch_base.addGeometry(outer_circle, False)

# Bore Circle (for reference)
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_diameter / 2.0)
sketch_base.addGeometry(bore_circle, False)

# Hub Circle (for reference)
hub_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hub_diameter / 2.0)
sketch_base.addGeometry(hub_circle, False)

# Raised Face Circle (for reference)
raised_face_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), raised_face_diameter / 2.0)
sketch_base.addGeometry(raised_face_circle, False)

# Bolt Circle (for reference)
bolt_circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_circle_diameter / 2.0)
sketch_base.addGeometry(bolt_circle_geom, False)

# Constraints: Coincident centers
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Outer & Bore
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Outer & Hub
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 3)) # Outer & Raised
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 4)) # Outer & Bolt

doc.recompute()

# --- Feature 1: Pad (Main Body) ---
pad = body.newObject("PartDesign::Pad", "Pad_Flange")
pad.Profile = sketch_base
pad.Length = total_height
pad.Type = "Solid"
pad.MidPlane = False
pad.Reverse = False

doc.recompute()

# --- Feature 2: Pocket (Bore) ---
# Create a sketch for the bore on the top face (Z = total_height)
sketch_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, total_height))
sketch_bore.Support = (doc.getObject("Z_Axis"), [])
sketch_bore.MapMode = "FlatFace"

# Bore profile
bore_profile = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_diameter / 2.0)
sketch_bore.addGeometry(bore_profile, False)

doc.recompute()

pocket_bore = body.newObject("PartDesign::Pocket", "Pocket_Bore")
pocket_bore.Profile = sketch_bore
pocket_bore.Type = "ThroughAll"

doc.recompute()

# --- Feature 3: Pad (Hub) ---
# Create a sketch for the hub on the top face (Z = total_height)
sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, total_height))
sketch_hub.Support = (doc.getObject("Z_Axis"), [])
sketch_hub.MapMode = "FlatFace"

# Hub profile
hub_profile = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hub_diameter / 2.0)
sketch_hub.addGeometry(hub_profile, False)

doc.recompute()

pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub")
pad_hub.Profile = sketch_hub
pad_hub.Length = raised_face_thickness
pad_hub.Type = "Solid"
pad_hub.MidPlane = False
pad_hub.Reverse = False

doc.recompute()

# --- Feature 4: Pocket (Raised Face) ---
# Create a sketch for the raised face on the top of the hub (Z = total_height + raised_face_thickness)
sketch_raised = body.newObject("Sketcher::SketchObject", "Sketch_RaisedFace")
sketch_raised.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
sketch_raised.Support = (doc.getObject("Z_Axis"), [])
sketch_raised.MapMode = "FlatFace"

# Raised face profile
raised_profile = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), raised_face_diameter / 2.0)
sketch_raised.addGeometry(raised_profile, False)

doc.recompute()

pocket_raised = body.newObject("PartDesign::Pocket", "Pocket_RaisedFace")
pocket_raised.Profile = sketch_raised
pocket_raised.Type = "ThroughAll"

doc.recompute()

# --- Feature 5: Hole (Bolt Holes) ---
# Create a sketch for a single bolt hole
sketch_single_hole = body.newObject("Sketcher::SketchObject", "Sketch_SingleHole")
sketch_single_hole.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
sketch_single_hole.Support = (doc.getObject("Z_Axis"), [])
sketch_single_hole.MapMode = "FlatFace"

single_hole_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_hole_diameter / 2.0)
sketch_single_hole.addGeometry(single_hole_geom, False)

# Constraint: Center on Z axis
# We add a point at the center of the sketch and constrain it to the Z axis.
# This ensures the hole is centered on the axis.
# Note: In FreeCAD 1.1, adding a Point geometry and constraining it is the robust way.
# However, for a circle centered at (0,0) in a sketch attached to Z_Axis, it is usually centered by default.
# To be absolutely sure, let's add a constraint "CenterOnLine" if available, or rely on the setup.
# Given the previous constraints worked, we assume the circle is centered.
# If not, we can add a point. Let's try adding a point constraint logic implicitly by ensuring the sketch is valid.
# Actually, let's just add a point at (0,0) and constrain it to the Z axis to be safe.
# But adding a point geometry might clutter. Let's rely on the standard behavior of MapMode "FlatFace" with Z_Axis.
# The origin of the sketch is at the intersection of the plane and the axis.
# So the circle at (0,0) is centered.

doc.recompute()

# Create the Hole feature
hole_feature = body.newObject("PartDesign::Hole", "Hole_Bolt")
hole_feature.Profile = sketch_single_hole
hole_feature.Type = "Simple"
hole_feature.Diameter = bolt_hole_diameter
hole_feature.Length = raised_face_thickness
# The hole is placed at the sketch's placement, which is centered on the Z axis.
# We need to ensure the hole is placed at the correct Z level.
# The sketch is at Z = total_height + raised_face_thickness.
# The Hole feature subtracts from the current solid.
# We need to set the placement of the hole feature to be at the top surface.
# However, the Hole feature's placement is relative to the sketch.
# Let's set the Placement of the hole feature explicitly to ensure it's at the top.
# Actually, the Hole feature uses the sketch's placement.
# We need to make sure the sketch is at the correct Z.
# The sketch is at Z = total_height + raised_face_thickness.
# The hole should go through the raised face.
# The length of the hole is raised_face_thickness.
# So the hole starts at Z = total_height + raised_face_thickness and goes down.
# This is correct.

doc.recompute()

# Create a PolarPattern of the Hole feature
pattern_bolt = body.newObject("PartDesign::PolarPattern", "Pattern_BoltHoles")
pattern_bolt.Originals = [hole_feature]
pattern_bolt.Axis = (doc.getObject("Z_Axis"), [])
pattern_bolt.Angle = 360.0
pattern_bolt.Occurrences = number_bolt_holes
pattern_bolt.Distribution = "Angle"

doc.recompute()

# --- Final Save ---
# Save the document to the specified path
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
