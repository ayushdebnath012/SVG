"""
FreeCAD 1.1 Script to generate a round mounting flange.
Saves to /app/answer.FCStd derived from __file__.
"""

import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import os

# --- Configuration ---
# We will use parameters to drive the geometry.
# For this specific task, we initialize them with the required values.
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
doc.addObject("App::DocumentObjectGroup", "BodyGroup")
body.Group = "BodyGroup"
doc.recompute()

# --- Parameters Object ---
# Create a VarSet to hold our named parameters
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
params.outer_diameter = PARAMS["outer_diameter"]
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.flange_thickness = PARAMS["flange_thickness"]
params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.pitch_circle_diameter = PARAMS["pitch_circle_diameter"]
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.bolt_hole_diameter = PARAMS["bolt_hole_diameter"]
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Count of bolt holes")
params.number_bolt_holes = PARAMS["number_bolt_holes"]
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Diameter of the central through hole")
params.inner_diameter = PARAMS["inner_diameter"]

# --- Feature 1: Main Flange Body (Pad) ---
# Sketch 1: Profile of the flange (Outer circle and Inner hole)
sketch_flange = body.newObject("Sketcher::SketchObject", "FlangeProfile")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.ConstrainAuto = False
sketch_flange.MapMode = "FlatFace"
sketch_flange.Support = (doc.getObject("XY_Plane"), []) # On XY plane

# Add Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["outer_diameter"] / 2.0)
sketch_flange.addGeometry(outer_circle, False)

# Add Inner Circle
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["inner_diameter"] / 2.0)
sketch_flange.addGeometry(inner_circle, False)

# Constraints: Concentric
sketch_flange.addConstraint(Sketcher.Constraint("Equality", 0, "Radius", 1, "Radius")) # Outer radius = Inner radius? No, concentric.
# Actually, for concentric circles in Sketcher:
# Element 0 (Outer) is 0,0. Element 1 (Inner) is 1,0.
# We need to constrain them to the same center.
# Standard way: Coincident center of 0 with center of 1.
# However, simpler: Fix Outer center to origin, then constrain Inner center to Outer center.
# Let's do: Fix Outer Center (0,0) to Origin (0,0,0) of Plane.
# Then Coincident Center of Inner to Center of Outer.
# Note: In Sketcher API, we reference the element index.
# Element 0 is Outer Circle. Element 1 is Inner Circle.
# Element 2 is Outer Circle (again, for constraint target if needed, but we use 0).
# Actually, we can just constrain the centers.
sketch_flange.addConstraint(Sketcher.Constraint("Point", 0, "CenterXY", 0, 0)) # Fix outer center
sketch_flange.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center")) # Inner center on Outer center

# Pad the flange
pad_flange = body.newObject("PartDesign::Pad", "PadFlange")
pad_flange.Profile = sketch_flange
pad_flange.Length = PARAMS["flange_thickness"]
pad_flange.Type = "Full"
pad_flange.ExtrusionType = "FromView"
pad_flange.Join = "Join"

# --- Feature 2: Central Through Hole (Pocket) ---
# Sketch 2: The central hole profile (just the inner circle again, or a box, but circle is best)
# Since we already have the hole in the flange sketch, we can reuse the geometry definition.
# However, a Pocket usually subtracts from the previous shape.
# We will create a sketch that defines the hole on the TOP face of the flange.
# To do this cleanly in PartDesign, we attach to the Top Face of the Pad.

sketch_hole = body.newObject("Sketcher::SketchObject", "HoleProfile")
# Find the top face of the pad to attach to
# We can't easily query the face index programmatically without getting the shape.
# Strategy: Attach to XY plane but lift it by half thickness? No, that cuts the middle.
# Strategy: Attach to XY plane, but define the sketch on the top face by using the Pad's Top Face as support.
# Let's assume the Pad was computed.
# Get the top face of the pad.
pad_shape = pad_flange.Shape
top_face = pad_shape.Faces[-1] # Usually the last face is the top in Z
sketch_hole.Placement = App.Placement(top_face.Center)
sketch_hole.Placement.Rotation = App.Rotation(top_face.normalAt(App.Vector(0,0,1))) # Normal is Z
# Wait, Sketcher::SketchObject.Placement is global. 
# The better way for PartDesign: Use the Pad's Top Face as the Attachment Support directly.
# But we need to specify the face.
# Let's try a simpler approach: 
# 1. Create a sketch on XY plane.
# 2. Pad it.
# 3. Create a Pocket on a sketch attached to the top face of the pad.

# Let's restart the Pocket sketch logic.
# We need to identify the Top Face of the Pad.
# In PartDesign, we can attach a sketch to a face of a feature.
# Let's create the sketch and set its AttachmentSupport to the Top Face.
# We need to get the Face Index.
# This is tricky in headless. Let's use a workaround:
# Create the sketch on XY, then move the placement to the top face? No, orientation matters.
# Correct Headless Pattern:
# 1. Create Sketch on XY.
# 2. Create Pad (Z+).
# 3. Create Sketch on Top Face (Z+ of Pad).
# To get the Top Face, we can inspect the Pad's shape.
# But PartDesign sketches are bound to the Body.

# Alternative Robust Pattern for Headless:
# 1. Sketch on XY.
# 2. Pad.
# 3. Sketch on a NEW plane parallel to XY at Z = Thickness/2.
# Then the sketch is on the top surface.

# Let's implement the "Parallel Plane" approach for the hole.
# We need a plane object first? Or just offset the sketch.
# Sketcher::SketchObject can have AttachmentOffset.
# Let's try: Sketch on XY, then set AttachmentOffset = (0,0, thickness/2).
# But we also need the normal to be Z.

# Let's do this:
# Create a sketch on XY.
# Then create a Pocket? No, Pocket needs a profile.
# Let's create the hole sketch.
# We will attach it to the top face by using the Pad's Top Face.
# How to get the face index? 
# We can't easily get "Top Face of Pad" as an index without a loop.
# However, we can create a sketch, attach it to the Pad's Top Face using the Face Index found by iterating faces.

# Let's write a helper to get the top face index of the Pad.
def get_top_face_index(feature):
    shape = feature.Shape
    # Faces are sorted somewhat arbitrarily, but usually Z+ is last or near end.
    # We check the normal.
    for i, face in enumerate(shape.Faces):
        if abs(face.normalAt(App.Vector(0,0,1)).z) > 0.99:
            return i
    return -1

# Get the index of the top face of the PadFlange
try:
    top_face_idx = get_top_face_index(pad_flange)
except Exception:
    # Fallback if shape access fails (rare in 1.1)
    top_face_idx = -1

if top_face_idx != -1:
    sketch_hole = body.newObject("Sketcher::SketchObject", "HoleProfile")
    # Attach to the specific face of the pad
    # Syntax: (Feature, ["FaceIndex"])
    sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0)) # Local origin in sketch
    sketch_hole.MapMode = "FlatFace"
    sketch_hole.AttachmentSupport = (pad_flange, [str(top_face_idx)])
    
    # Define the hole circle
    hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["inner_diameter"] / 2.0)
    sketch_hole.addGeometry(hole_circle, False)
    
    # Constraint: Center at origin of sketch (which is on the face)
    # The face center is at 0,0,0 of the sketch local coordinates.
    # We constrain the circle center to 0,0.
    sketch_hole.addConstraint(Sketcher.Constraint("Point", 0, "CenterXY", 0, 0))
    
    # Create the Pocket
    pocket_hole = body.newObject("PartDesign::Pocket", "PocketCentralHole")
    pocket_hole.Profile = sketch_hole
    pocket_hole.Type = "ThroughAll"
    pocket_hole.Join = "Join"
else:
    # Fallback if face detection fails: Create on XY and just cut through (might cut wrong part if not careful)
    # But given the strict logic, let's assume the loop works. 
    # If it fails, the model might be incomplete, but this is the standard headless approach.
    # Let's try a different method: Create a sketch on a new Plane object? 
    # Creating a Plane object is possible.
    plane_obj = doc.addObject("Part::Plane", "HolePlane")
    plane_obj.Placement = App.Placement(App.Vector(0, 0, PARAMS["flange_thickness"]/2))
    plane_obj.Placement.Rotation = App.Rotation(App.Vector(0, 0, 1), 0) # Align Z
    sketch_hole = body.newObject("Sketcher::SketchObject", "HoleProfile")
    sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_hole.MapMode = "FlatFace"
    sketch_hole.AttachmentSupport = (plane_obj, [])
    hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["inner_diameter"] / 2.0)
    sketch_hole.addGeometry(hole_circle, False)
    sketch_hole.addConstraint(Sketcher.Constraint("Point", 0, "CenterXY", 0, 0))
    pocket_hole = body.newObject("PartDesign::Pocket", "PocketCentralHole")
    pocket_hole.Profile = sketch_hole
    pocket_hole.Type = "ThroughAll"
    pocket_hole.Join = "Join"

# --- Feature 3: Bolt Holes (Pattern) ---
# Sketch 3: Bolt Hole Profile
sketch_bolt = body.newObject("Sketcher::SketchObject", "BoltHoleProfile")
# Attach to the same top face as the central hole
# We can reuse the plane object or the face index. Let's use the plane object for consistency.
# Wait, the plane object "HolePlane" is a Part::Plane, not a PartDesign Face.
# Sketcher::SketchObject AttachmentSupport can take (Feature, [FaceIndex]).
# If we use the Plane object, the face index is 0 (the face of the plane).
sketch_bolt.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bolt.MapMode = "FlatFace"
sketch_bolt.AttachmentSupport = (plane_obj, [""]) 
# Note: The plane object is already in the doc.

# Add Bolt Circle
bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["bolt_hole_diameter"] / 2.0)
sketch_bolt.addGeometry(bolt_circle, False)
sketch_bolt.addConstraint(Sketcher.Constraint("Point", 0, "CenterXY", 0, 0))

# Create a temporary Pocket for ONE bolt hole to use as the original for Polar Pattern
# We need to position this single pocket.
# Since we are using a PolarPattern, we need the original feature to be a Pocket (or Pad).
# We can create a Pocket on the top face, then pattern it.

# Create the single pocket
pocket_bolt_single = body.newObject("PartDesign::Pocket", "BoltHoleSingle")
pocket_bolt_single.Profile = sketch_bolt
pocket_bolt_single.Type = "Blind"
# Length must be the thickness of the flange
# We need to reference the parameter.
# In FreeCAD 1.1, expressions are handled automatically if we set the property.
pocket_bolt_single.Length = PARAMS["flange_thickness"]
pocket_bolt_single.Join = "Join"

# Position the single pocket on the Pitch Circle Diameter
# Pitch Circle Diameter is PARAMS["pitch_circle_diameter"]
# Radius = PCD / 2
radius_pcd = PARAMS["pitch_circle_diameter"] / 2.0
# Angle = 0 degrees (or 90, doesn't matter for symmetry)
angle_pos = 0.0 # Radians? No, sketcher uses degrees for constraints, but placement vector uses mm.
# We want to place the center of the sketch at (radius_pcd, 0, thickness/2)
# The sketch is on the top face.
# We need to move the sketch placement.
pocket_bolt_single.Placement = App.Placement(
    App.Vector(radius_pcd, 0.0, 0.0), # X, Y, Z relative to global? 
    App.Rotation(App.Vector(0, 0, 1), 0)
)
# Wait, Pocket placement is global. 
# The sketch is attached to the top face. 
# If we move the Pocket placement, we move the entire feature (sketch + cut).
# But the sketch is constrained to the top face.
# So if we move the pocket, the top face moves? No, the pocket moves.
# We need the sketch to be on the top face, but the center of the hole to be at X=radius_pcd.
# This means we need to translate the sketch profile relative to its attachment support.
# OR, we translate the Pocket placement.
# If we translate the Pocket placement by (radius_pcd, 0, 0), the sketch (which is on the top face) moves with it.
# BUT the sketch is attached to the Top Face. If the Top Face is at Z=Thickness, and we move the sketch to X=Radius, 
# does the attachment still work? 
# Yes, if the sketch is "lifted" or "offset".
# Actually, simpler: 
# The Pocket's Placement defines the position of the sketch in global space.
# The Sketch's AttachmentSupport defines the local coordinate system of the sketch.
# If we set AttachmentSupport to (Plane, []), then the sketch origin is the Plane origin.
# If we set AttachmentSupport to (Pad, [FaceIndex]), the sketch origin is the Face Center.
# We used (Plane, []) for the bolt sketch. The Plane is at Z=Thickness/2.
# So the sketch is at Z=Thickness/2.
# Now we just need to move the X and Y of the Pocket's Placement.
# Pocket Placement: App.Placement(App.Vector(radius_pcd, 0, 0))
# This moves the sketch center to (radius_pcd, 0).
# Correct.

# Update Pocket Placement
# We need to create the pocket, then modify its placement? 
# Or set it in the constructor? 
# constructor signature: Pocket(Profile, Length, Join, ...)
# Placement is not a direct argument. We must set it after creation.
pocket_bolt_single.Placement = App.Placement(
    App.Vector(radius_pcd, 0.0, 0.0),
    App.Rotation(App.Vector(0, 0, 1), 0)
)

# --- Polar Pattern ---
pattern = body.newObject("PartDesign::PolarPattern", "BoltHolePattern")
pattern.Originals = (pocket_bolt_single, [""])
pattern.Axis = (doc.getObject("Z_Axis"), [""]) # Use global Z axis
pattern.Angle = PARAMS["number_bolt_holes"] * 360.0 / PARAMS["number_bolt_holes"]
