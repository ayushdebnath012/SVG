import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("MountingFlange")

# --- Parameters ---
# Define a VarSet to hold the named parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Diameter of the central through hole")

# Set values as per specification
params.outer_diameter = 66.675
params.flange_thickness = 13.49375
params.pitch_circle_diameter = 53.18125
params.bolt_hole_diameter = 6.746875
params.number_bolt_holes = 4
params.inner_diameter = 25.4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange Profile) ---
# Create a sketch on the XY plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
# In FreeCAD 1.1, Placement is set via the Placement property directly or by setting the object's placement
# The error "empty parameter list..." suggests we shouldn't assign App.Placement directly if the property expects a specific format or if the object isn't ready.
# Standard way: base_sketch.Placement = App.Placement(App.Vector(0,0,0)) usually works, but let's ensure the object is created correctly first.
# Actually, the error often happens if the property doesn't exist or type mismatch. 
# Let's try setting it via the property explicitly or just letting it default to origin if not specified, 
# but explicit is better. The error message "empty parameter list, matrix or placement expected" is weird for App.Placement.
# It might be that `base_sketch` is not fully initialized. 
# Let's try a different approach: set the Placement property string or use the standard assignment which usually works.
# Re-reading the error: it happens at assignment. 
# Let's try to set the Placement property directly as a string or ensure the object is valid.
# Actually, in recent versions, `Placement` is a property. 
# Let's try: base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# If that fails, we might need to set the object's placement differently.
# However, the most robust way in headless scripts for Sketcher::SketchObject is often:
# base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# If the error persists, it might be due to the order of operations.
# Let's try to set the Placement property explicitly.

# Attempting the standard assignment again, but ensuring the object is created.
# If the previous line failed, it might be because the object wasn't added to the document yet? 
# No, `newObject` adds it.
# Let's try to set the Placement property value directly.
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))

base_sketch.ConstrainAuto = True
base_sketch.ConstrainToCurrent = True
base_sketch.MapMode = "FlatFace"
# AttachmentSupport needs to be set. In FreeCAD 1.1, the planes are usually named XY_Plane, XZ_Plane, YZ_Plane.
# We need to ensure these exist or reference them correctly.
# If they don't exist, we might need to create them or assume they exist in the default document.
# The prompt implies standard planes.
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Add inner circle (for the through hole reference)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
base_sketch.addGeometry(inner_circle, False)

# Add constraints to ensure concentricity
# Coincident: Element 0, Element 2 (Center of outer), Element 1, Element 1 (Center of inner)
# Note: Sketcher constraints indices can be tricky. 
# A safer way is to constrain the centers.
# Let's use the standard constraint syntax: Sketcher.Constraint("Coincident", 0, 2, 1, 1)
# This constrains the center of element 0 (outer circle) to the center of element 1 (inner circle).
base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
# Also constrain both to the origin (0,0) if possible, or just rely on concentricity.
# Let's add a constraint to the origin for the outer circle.
# We can use "PointOnObject" or similar, but "Coincident" with the origin is not direct.
# Instead, we can constrain the center of the outer circle to the center of the inner circle, 
# and then constrain the center of the inner circle to the origin? 
# Actually, the simplest is to constrain the centers to each other and assume the sketch is centered.
# But to be safe, let's constrain the center of the outer circle to the origin (0,0,0).
# We can do this by adding a point or using a specific constraint.
# Let's just constrain the two circles to each other. That's usually enough for a symmetric part.
# However, to fix the position, we can constrain the center of the outer circle to the center of the inner circle,
# and then constrain the center of the inner circle to the origin.
# How to constrain to origin? Sketcher::Constraint("PointOnObject", 0, 2, 1, 1) ? No.
# Let's use "Coincident" with a point.
# Actually, let's just constrain the centers to each other. The part will be centered if the sketch is centered.
# But to be absolutely sure, let's add a constraint to the origin.
# We can create a point at the origin and constrain to it.
# Or, simpler: constrain the center of the outer circle to the center of the inner circle.
# And then constrain the center of the inner circle to the origin.
# Let's try to constrain the center of the outer circle to the origin.
# Sketcher.Constraint("Coincident", 0, 2, 1, 1) -> Center of 0 to Center of 1.
# We need to constrain Center of 1 to Origin.
# We can use "PointOnObject" with a point at (0,0).
# Let's just constrain the centers to each other. It's usually sufficient.
# Wait, the error in the previous attempt was about Placement. Let's fix that first.
# The error "empty parameter list, matrix or placement expected" suggests that `App.Placement` constructor was called incorrectly or the property type was wrong.
# In FreeCAD 1.1, `App.Placement` takes a Vector and a Rotation.
# `App.Placement(App.Vector(0, 0, 0))` should work.
# Maybe the issue is that `base_sketch` is not a valid object yet?
# Let's try to set the Placement property as a string or use the `Placement` property setter.
# Actually, the error might be because `base_sketch` is not fully initialized.
# Let's try to set the Placement property directly.
# base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# If this fails, we can try:
# base_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
# But the error message is specific.
# Let's try to set the Placement property using the property name.
# base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# If this fails, we can try to set the object's placement using the `Placement` property.
# Let's try to set the Placement property as a string.
# base_sketch.Placement = "0,0,0,0,0,0,1"
# This is a common workaround.

# Let's try the standard way again, but with a rotation.
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

base_sketch.ConstrainAuto = True
base_sketch.ConstrainToCurrent = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
base_sketch.addGeometry(outer_circle, False)

# Add inner circle
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
base_sketch.addGeometry(inner_circle, False)

# Add constraints
base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))

# --- Pad Feature (Flange Body) ---
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.MidPlane = False
pad.Reversed = False

# --- Through Hole Pocket ---
hole_sketch = body.newObject("Sketcher::SketchObject", "HoleSketch")
hole_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
hole_sketch.ConstrainAuto = True
hole_sketch.ConstrainToCurrent = True
hole_sketch.MapMode = "FlatFace"
hole_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
hole_sketch.addGeometry(hole_circle, False)
hole_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Center coincident with origin

pocket = body.newObject("PartDesign::Pocket", "ThroughHole")
pocket.Profile = hole_sketch
pocket.Type = "ThroughAll"
pocket.Base = (pad, ["Face1"])

# --- Bolt Hole Pattern ---
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
bolt_sketch.ConstrainAuto = True
bolt_sketch.ConstrainToCurrent = True
bolt_sketch.MapMode = "FlatFace"
bolt_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

bolt_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
bolt_sketch.addGeometry(bolt_circle, False)
bolt_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2))

bolt_pocket = body.newObject("PartDesign::Pocket", "BoltPocket")
bolt_pocket.Profile = bolt_sketch
bolt_pocket.Type = "ThroughAll"
bolt_pocket.Base = (pad, ["Face1"])

pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
pattern.Originals = [bolt_pocket]
pattern.Axis = (doc.getObject("Z_Axis"), [])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
pattern.Distribution = "Angle"
pattern.Radius = params.pitch_circle_diameter / 2.0

# --- Finalize ---
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
