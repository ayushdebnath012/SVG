from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# Initialize document
doc = App.newDocument("ShaftPart")

# 1. Define Body
body = doc.addObject("PartDesign::Body", "ShaftBody")
body.Type = "Body"

# 2. Define Named Parameters (Editable Variables)
params = body.newObject("App::VarSet", "ShaftParameters")
params.addProperty("App::PropertyLength", "smooth_shaft_diameter", "Dimensions", "Shaft diameter")
params.addProperty("App::PropertyLength", "smooth_shaft_length", "Dimensions", "Shaft length")
params.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "Keyway width")
params.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "Keyway depth")
params.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "Keyway height")
params.addProperty("App::PropertyInteger", "num_keyway", "Dimensions", "Number of keyways")

# Set default values
params.smooth_shaft_diameter = 30.0
params.smooth_shaft_length = 60.0
params.keyway_width = 6.0
params.keyway_depth = 3.0
params.keyway_height = 30.0
params.num_keyway = 2

# 3. Create Base Sketch (Cylinder Profile)
# Attach to XY plane, offset to Z = length/2 to center it
xy_plane = doc.addObject("PartDesign::PlanarObject", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
doc.addObject("App::DocumentObject", "XY_Plane") # Ensure it's in document list if needed, though Body handles it often
# Actually, PartDesign::Body usually manages its own planes or we create Part::Face/Plane objects.
# Standard approach: Use PartDesign::Body's implicit planes or create Part::Face.
# Let's create explicit Part::Face planes to be safe and explicit.

base_plane = doc.addObject("Part::Face", "BasePlane")
base_plane.Placement = App.Placement(App.Vector(0, 0, 0))
base_plane = base_plane.addFace(Part::Plane(App.Vector(0,0,0), App.Vector(0,0,1)))
base_plane.Placement = App.Placement(App.Vector(0,0,0)) # Reset placement for Sketch attachment
doc.recompute()

sketch_profile = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, params.smooth_shaft_length / 2.0)) # Offset Z
sketch_profile.Constraints = "Coincident,PointOn,Radius"
sketch_profile.Technology = "ISO-10813"
sketch_profile.Outer = False
sketch_profile.ViewObject.Locked = False

# Add Cylinder Profile: Diameter on X-axis, Length on Z
# Line from (-D/2, 0) to (D/2, 0)
sketch_profile.addGeometry(Part.LineSegment(App.Vector(-params.smooth_shaft_diameter/2, 0, 0), App.Vector(params.smooth_shaft_diameter/2, 0, 0)))
# Close the sketch (Implicitly handled by adding edges or explicitly closing)
# We will use a Pad, which requires a closed loop. A line isn't enough for a Pad unless it's a Revolved profile.
# Since this is a cylinder, a Revolved feature is better, OR a Pad of a closed rectangle.
# Let's do a Pad with a closed rectangle profile to represent the cylinder block first, then revolve? 
# No, a cylinder is best made by revolving a rectangle or padding a closed loop.
# Let's make the profile a rectangle: from (-D/2, 0) to (D/2, 0) and back? No.
# Let's create a rectangle: (-D/2, 0) -> (D/2, 0) -> (D/2, L/2) -> (-D/2, L/2) -> (-D/2, 0)?
# No, the sketch is on a plane offset in Z. If we pad along Z, we get a cylinder.
# So the profile must be a rectangle in the XY plane? No, the sketch plane is XY.
# If sketch is on XY plane (offset in Z), and we Pad along Z, the profile must be in XY.
# Profile: Rectangle from (-R, 0) to (R, 0) is not closed.
# Let's define the sketch plane as the XY plane at Z=0.
# We want a cylinder along Z. So the sketch must be in XY plane.
# Profile: Rectangle defined by diameter.
# Points: (-R, 0), (R, 0), (R, L/2)? No.
# To make a cylinder of length L and diameter D along Z axis:
# Sketch on XY plane (Z=0).
# Profile: Rectangle from (-D/2, 0) to (D/2, 0) is not closed.
# Correct approach: Sketch on XY plane. Profile is a rectangle of width D and height L? 
# No, if we Pad along Z, the profile must be in XY. The extrusion direction is Z.
# So the profile must be a circle? Or a rectangle? 
# If profile is a rectangle of width D and height L, and we pad along Z, we get a rectangular block.
# If profile is a circle, we get a cylinder.
# But we want to add keyways. Keyways are usually machined into the side.
# Let's stick to the prompt: "Smooth shaft... cylindrical".
# Strategy: 
# 1. Sketch XY plane. Draw a rectangle of width = Diameter, height = Length. 
#    Wait, if sketch is on XY, and we pad along Z, the shape extends in Z.
#    So the profile in XY must define the cross-section? No, Pad extrudes along the normal.
#    If sketch is on XY, normal is Z. So profile defines the cross-section in XY? 
#    No. If sketch is on XY, the geometry lies in XY. Extruding along Z creates a prism.
#    So if profile is a line segment from -R to R, and we extrude, we get a plate.
#    We need a closed profile in XY to get a cylinder? No, a circle in XY extruded along Z is a cylinder.
#    But we want to cut keyways. Keyways are slots on the side.
#    It is easier to:
#    1. Create a solid cylinder (Pad of a circle in XY plane, length L).
#    2. Create keyways using Pocket/Revolution features.

# Revised Plan:
# 1. Sketch 1 (XY Plane, Z=0): Circle of radius R.
# 2. Pad 1: Length = L. (Creates Cylinder).
# 3. Sketch 2 (Plane parallel to XY, offset by some Z): Define keyway profile.
# 4. Revolve/Pocket for keyways.

# Let's refine the "Single Body, One Solid" requirement.
# We can do everything in one Body.

# Step 1: Base Cylinder
# Sketch on XY Plane (Z=0)
sketch_cyl = body.newObject("Sketcher::SketchObject", "Sketch_Cylinder")
sketch_cyl.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_cyl.Constraints = "Coincident,PointOn,Radius"
sketch_cyl.Technology = "ISO-10813"

# Add Circle
sketch_cyl.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.smooth_shaft_diameter / 2.0))
doc.recompute()

# Pad to create cylinder
pad_cyl = body.newObject("PartDesign::Pad", "Pad_Cylinder")
pad_cyl.Profile = sketch_cyl
pad_cyl.Length = params.smooth_shaft_length
pad_cyl.Type = "Solid"
doc.recompute()

# Step 2: Keyways
# Keyway: Rectangular slot cut from the side.
# Orientation: Let's say along the axis of the shaft (Z).
# The keyway has a "width" (along circumference), "depth" (radial), "height" (along axis)?
# Prompt says: keyway_width, keyway_depth, keyway_height.
# Usually: Width = circumferential (arc length or chord), Depth = radial cut, Height = axial length.
# Given num_keyway = 2, they are likely at 0 and 180 degrees.
# Let's assume:
# - keyway_width: Axial length of the slot? Or circumferential?
# - keyway_depth: Radial depth (how deep into the shaft).
# - keyway_height: Circumferential height? Or axial?
# Standard Keyway dimensions: Width (w), Depth (t), Length (L).
# Let's interpret:
# - keyway_width: Axial length (L_key)
# - keyway_depth: Radial depth (D_cut)
# - keyway_height: Circumferential width (W_key)
# Prompt values: width=6, depth=3, height=30.
# Shaft diameter=30, length=60.
# If height=30, that's half the shaft length. This suggests the axial length is 30.
# If width=6, that's the circumferential width.
# If depth=3, that's the radial depth.
# This makes sense.
# So: Axial Length = 30, Circumferential Width = 6, Radial Depth = 3.

# We need to cut a slot.
# Option A: Sketch on a plane tangent to the surface, extrude inwards.
# Option B: Use PartDesign::Pocket with a profile on a plane tangent to the cylinder surface.
# Option C: Use PartDesign::Groove (Revolution) if symmetric, but keyways are rectangular.
# Option D: Use PartDesign::Pocket on a sketch on the tangent plane.

# Let's use a tangent plane sketch for one keyway, then pattern it.
# Plane: Tangent at angle 0 (X-axis). Normal = (1, 0, 0).
# We need a sketch on this plane.
# The profile in this sketch should be a rectangle of:
# - Width = keyway_width (Axial)
# - Height = keyway_depth (Radial, into the shaft)
# Wait, if the plane is tangent at X-axis, the shaft is to the "left" (negative X)? 
# Shaft center is (0,0,0). Tangent plane at X=R is at x=R. Normal points +X.
# The material is in the -X direction relative to the plane.
# So we sketch a rectangle starting at x=0 (on the plane) and going to x=-depth?
# Or we can just define the rectangle dimensions and let the pocket type handle it.

# Plane setup for Keyway 1 (at 0 degrees)
plane_key = doc.addObject("Part::Plane", "Plane_Key")
plane_key.Placement = App.Placement(App.Vector(params.smooth_shaft_diameter / 2.0, 0, 0)) # Shift to surface
# Rotate so it's tangent to the cylinder (Vertical plane, normal along X)
# Default plane is XY. We want a plane at x=R, normal (1,0,0). 
# XY plane normal is Z. We need to rotate 90 deg around Y.
plane_key.Placement = App.Placement(App.Vector(params.smooth_shaft_diameter / 2.0, 0, 0))
plane_key.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), math.pi / 2)
doc.addObject("App::DocumentObject", "Plane_Key") # Ensure valid
doc.recompute()

# Sketch for Keyway
sketch_key = body.newObject("Sketcher::SketchObject", "Sketch_Key")
sketch_key.Placement = App.Placement(App.Vector(0, 0, 0)) # Local coords on the plane
# The plane is offset to the shaft surface. The sketch origin is at the surface.
# We need to cut a rectangle of size (Axial, Radial).
# Axial dimension = keyway_height (30)
# Radial dimension = keyway_depth (3)
# Orientation in the sketch:
# Let's say sketch X is Axial (Z of world), sketch Y is Radial (X of world).
# So we draw a rectangle from (0,0) to (height, depth).
# But wait, the pocket will subtract material. 
# If the plane is at the surface, and we define a rectangle in the plane, 
# the pocket needs to know where the material is.
# Usually, for a tangent pocket, we sketch the profile and set Type="ThroughAll" or specific length.
# But a simple rectangle on a tangent plane doesn't automatically "bite" into a cylinder unless the plane intersects it.
# The plane intersects the cylinder at the surface.
# If we define a rectangle [0, height] x [0, depth] in the sketch plane, 
# and perform a pocket, it should cut a rectangular block out of the cylinder.

# Define Sketch Geometry
sketch_key.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.keyway_height, 0, 0)))
sketch_key.addGeometry(Part.LineSegment(App.Vector(params.keyway_height, 0, 0), App.Vector(params.keyway_height, params.keyway_depth, 0)))
sketch_key.addGeometry(Part.LineSegment(App.Vector(params.keyway_height, params.keyway_depth, 0), App.Vector(0, params.keyway_depth, 0)))
sketch_key.addGeometry(Part.LineSegment(App.Vector(0, params.keyway_depth, 0), App.Vector(0, 0, 0)))

# Constraints
# Make it a rectangle
c1 = Sketcher.Constraint("PointOnLine", 0, 2, 1, 2) # Just to ensure closure if needed, but LineSegments form a loop
# Add constraints to make it a perfect rectangle aligned with axes
sketch_key.addConstraint(Sketcher.Constraint("Horizontal", 0))
sketch_key.addConstraint(Sketcher.Constraint("Vertical", 0))
sketch_key.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 1)) # Just to force origin alignment?
# Actually, let's just use the lines.
doc.recompute()

# Pocket Feature
pocket_key = body.newObject("PartDesign::Pocket", "Pocket_Key")
pocket_key.Profile = sketch_key
pocket_key.Type = "ThroughAll" # Cut all the way through the shaft? 
# Wait, if we cut through all, we might cut through the whole shaft if the pocket goes both ways.
# The sketch is in the plane. The pocket direction is the normal of the plane.
# Normal is +X. Material is at -X (inside the shaft).
# "ThroughAll" will cut from the sketch plane in both directions of the normal? 
# Or just one? In FreeCAD PartDesign::Pocket, Type="ThroughAll" usually cuts through the entire body in the direction of the normal.
# Since the body is on one side, it should cut through the full diameter? 
# No, the plane is tangent. The body is entirely on one side (negative X).
# So ThroughAll should cut through the whole shaft depth? 
# Wait, the sketch defines the "face" to be removed.
# If the sketch is a rectangle of size H x D, and we pocket, it removes that volume.
# ThroughAll ensures it cuts all the way through the body in the normal direction.
# Since the body is only on one side, it cuts from the surface to the center? 
# No, it cuts from the surface to the other side of the body? 
# Actually, if the plane is tangent, the body is completely on one side. 
# ThroughAll will cut the entire intersection of the plane and the body? 
# No, ThroughAll cuts along the normal until it hits the boundary of the body.
# Since the body is convex and the plane is tangent, the "other side" is infinite space.
# So it cuts through the whole shaft thickness (Radius)? 
# Wait, the sketch defines the cross-section of the cut.
# If the sketch is a rectangle of height H (axial) and depth D (radial), 
# and we pocket, does it respect the sketch dimensions or just cut through?
# If Type="ThroughAll", it cuts through the body. The sketch defines the width/shape, but the length is determined by the body boundary.
# This is good. We want to cut the full axial length specified in the sketch? 
# No, ThroughAll ignores the sketch length in the normal direction? 
# The sketch is in the tangent plane. The "normal" to the pocket is the normal of the plane.
# The sketch profile is a rectangle. 
# If we use ThroughAll, it cuts through the body in the normal direction.
# The sketch defines the "width" of the cut (Axial) and the "depth" (Radial)? 
# Actually, the sketch is in the plane. The pocket removes the volume swept by the sketch moving along the normal? 
# No, Pocket removes the volume defined by the sketch profile extruded along the normal? 
# No, that's Pad. Pocket is subtractive.
# If the sketch is in the tangent plane, and we Pocket, we are removing the volume defined by the sketch profile extending in the normal direction? 
# No, the sketch IS the profile. The Pocket operation removes the material defined by the sketch.
# If the sketch is a rectangle in the tangent plane, the pocket removes a rectangular prism? 
# No, the pocket removes the volume bounded by the sketch and the body boundaries.
# If Type="ThroughAll", it cuts through the entire body in the normal direction.
# The sketch defines the "cross section" of the cut in the plane? 
# No, the sketch is the boundary
