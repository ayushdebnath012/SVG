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
params.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "Keyway width (Axial)")
params.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "Keyway depth (Radial)")
params.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "Keyway height (Circumferential)")
params.addProperty("App::PropertyInteger", "num_keyway", "Dimensions", "Number of keyways")

# Set default values
params.smooth_shaft_diameter = 30.0
params.smooth_shaft_length = 60.0
params.keyway_width = 6.0
params.keyway_depth = 3.0
params.keyway_height = 30.0
params.num_keyway = 2

# 3. Create Base Sketch (Cylinder Profile)
# We will create the cylinder by revolving a rectangle or padding a circle.
# Strategy: Sketch a circle on XY plane, Pad along Z.
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

# 4. Create Keyways
# Keyway dimensions interpretation based on prompt:
# - keyway_width: Axial length of the slot (along Z)
# - keyway_depth: Radial depth (how deep into the shaft)
# - keyway_height: Circumferential width (arc length or chord)
# Note: The prompt says "keyway_height = 30" and "smooth_shaft_length = 60". 
# If height is 30, it's half the shaft length. This suggests the axial length is 30.
# Let's assume:
# Axial Length = keyway_height (30)
# Circumferential Width = keyway_width (6)
# Radial Depth = keyway_depth (3)

# We will create a tangent plane at the surface of the cylinder (at X = Radius).
# Then sketch a rectangle on this plane and use a Pocket to cut it out.
# Since we need multiple keyways, we will create one and use a Polar Pattern.

# Plane setup for Keyway 1 (at 0 degrees, tangent at X=Radius)
# We create a Part::Plane object to serve as the sketch support.
plane_key = doc.addObject("Part::Plane", "Plane_Key")
plane_key.Placement = App.Placement(App.Vector(params.smooth_shaft_diameter / 2.0, 0, 0))
# Rotate the plane so it is vertical (tangent to the cylinder). 
# Default XY plane normal is Z. We want normal X. Rotate 90 deg around Y.
plane_key.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), math.pi / 2)
doc.recompute()

# Sketch for Keyway
sketch_key = body.newObject("Sketcher::SketchObject", "Sketch_Key")
sketch_key.Placement = App.Placement(App.Vector(0, 0, 0)) # Local coords on the plane
# The plane is offset to the shaft surface. The sketch origin is at the surface.
# We need to cut a rectangle of size (Axial, Radial).
# Axial dimension = keyway_height (30) -> along Z axis of world (which is Y axis of this sketch plane? No.)
# Let's analyze the plane orientation:
# Original XY plane: X right, Y up, Z out.
# Rotate 90 deg around Y: X becomes Z (out), Z becomes -X (in). Y stays Y.
# So the new plane has:
# - Y axis (up) -> corresponds to World Y.
# - Z axis (out) -> corresponds to World Z.
# - Normal (X) -> corresponds to World X.
# The shaft is along World Z.
# So the "Axial" direction of the keyway (along the shaft) is World Z.
# In the sketch plane, World Z is the Sketch Z axis.
# The "Radial" direction (into the shaft) is World -X.
# In the sketch plane, World -X is the Sketch -Z axis (since Normal is +X).
# So we need a rectangle in the Sketch plane:
# - Extent along Sketch Z (Axial): keyway_height
# - Extent along Sketch -Z (Radial): keyway_depth
# Wait, if the sketch plane is at X=Radius, and we want to cut INWARDS (towards center),
# we need to cut in the -X direction.
# In the sketch plane, -X is the -Z direction.
# So we draw a rectangle from (0,0) to (keyway_height, -keyway_depth)?
# Or we can just draw a rectangle of size (keyway_height, keyway_depth) and orient it correctly.
# Let's draw a rectangle from (0,0) to (keyway_height, keyway_depth) in the Sketch X-Y plane?
# No, the sketch plane axes are Y (World Y) and Z (World Z).
# We want the cut to be along World Z (Axial) and World -X (Radial).
# So in the sketch plane:
# - One side is along Sketch Z (World Z). Length = keyway_height.
# - One side is along Sketch -Z (World -X). Length = keyway_depth.
# This is confusing because the sketch plane's Z axis is World Z.
# Let's re-orient the plane to make it easier.
# We want the sketch plane to be the XZ plane (tangent at Y=0)? No, tangent at X=R.
# Let's just define the sketch geometry explicitly using vectors in the sketch plane.
# Sketch Plane Basis:
# - U (Sketch X) = World Y (0, 1, 0)
# - V (Sketch Y) = World Z (0, 0, 1)
# - Normal = World X (1, 0, 0)
# We want a rectangle:
# - Along World Z (V): length = keyway_height
# - Along World -X (Normal): length = keyway_depth
# So in the sketch plane, we need a rectangle that spans:
# - From 0 to keyway_height along V (Sketch Y).
# - From 0 to -keyway_depth along Normal? 
# But the sketch is 2D. We can't draw along the normal directly in the sketch.
# The Pocket operation will extrude the sketch profile along the normal.
# So the sketch profile must be a line segment or a shape in the plane.
# If we draw a rectangle in the sketch plane, the Pocket will cut a prism.
# We want the cut to be:
# - Axial length = keyway_height (along World Z).
# - Radial depth = keyway_depth (along World -X).
# - Circumferential width = keyway_width (along World Y).
# Wait, my previous interpretation of "keyway_width" as circumferential might be wrong if the sketch is on a tangent plane.
# If the sketch is on a tangent plane, the "width" of the keyway in the circumferential direction is the length of the cut along the plane perpendicular to the axial direction.
# So:
# - Axial (World Z) = keyway_height (30)
# - Circumferential (World Y) = keyway_width (6)
# - Radial (World -X) = keyway_depth (3)
# So the sketch profile should be a rectangle in the tangent plane (XZ plane shifted to X=R):
# - One side along World Z (Axial): length = keyway_height.
# - One side along World Y (Circumferential): length = keyway_width.
# The Pocket will then cut this rectangle out, and the "depth" will be determined by the body boundary (ThroughAll) or a specific length.
# Since we want to cut radially INWARDS, we need to specify the direction.
# If we use Type="ThroughAll", it cuts through the body in the normal direction.
# The normal is +X. The body is at -X. So it cuts from the surface to the center? 
# No, ThroughAll cuts from the sketch plane in both directions of the normal until it hits the boundary.
# Since the body is only on one side, it cuts from the surface to the center (and potentially beyond if the body was on both sides, but it's not).
# So ThroughAll should work perfectly to cut the full radial depth.

# Let's re-orient the plane to make the sketch easier.
# We want the sketch plane to be the XZ plane (tangent at Y=0)? No, tangent at X=R.
# Let's keep the plane at X=R, normal X.
# We want the sketch to define a rectangle of:
# - Width (along Y): keyway_width
# - Height (along Z): keyway_height
# And the Pocket will cut along X (Normal).
# So the sketch profile is a rectangle in the YZ plane (which is the plane at X=R).
# This matches the plane orientation:
# - Sketch X = World Y
# - Sketch Y = World Z
# So we draw a rectangle from (0,0) to (keyway_width, keyway_height) in the sketch plane.
# This rectangle lies in the plane X=R.
# The Pocket will cut along the normal (X).
# Since the body is at X < R, the cut will go from X=R inwards to X=0 (center).
# This creates a rectangular slot of:
# - Axial length = keyway_height
# - Circumferential width = keyway_width
# - Radial depth = Radius (full depth).
# This is exactly what we want!

# Update Plane Orientation to match Sketch X=World Y, Sketch Y=World Z
# Current: Rotate 90 deg around Y.
# Original: X=(1,0,0), Y=(0,1,0), Z=(0,0,1).
# Rotate 90 around Y: X->Z, Z->-X.
# New X=(0,0,1) (World Z), New Y=(0,1,0) (World Y), New Z=(-1,0,0) (World -X).
# This is not what we want. We want Sketch X=World Y, Sketch Y=World Z.
# We need a plane with Normal = World X.
# And Basis vectors: U=World Y, V=World Z.
# This is the plane X=R.
# How to get this in FreeCAD?
# Create a plane at X=R, normal X.
# The default placement of a Plane object is at (0,0,0) with normal Z.
# We need to translate to (R, 0, 0) and rotate so Normal becomes X.
# Rotation: 90 deg around Y axis.
# Let's check:
# Start: Normal=(0,0,1). Rotate 90 around Y.
# New Normal = (1,0,0). Correct.
# Start: X=(1,0,0). Rotate 90 around Y -> (0,0,-1).
# Start: Y=(0,1,0). Rotate 90 around Y -> (0,1,0).
# So the new basis is: X=(0,0,-1) [World -Z], Y=(0,1,0) [World Y].
# This means Sketch X is World -Z, Sketch Y is World Y.
# We want Sketch X to be World Y, Sketch Y to be World Z.
# So we need to swap axes or rotate differently.
# Let's try rotating 90 deg around Z axis? No, normal must be X.
# Let's try rotating 90 deg around X axis? No, normal must be X.
# We need a rotation that maps Z->X and Y->Z?
# Rotation matrix R such that R * [0,0,1]^T = [1,0,0]^T and R * [0,1,0]^T = [0,0,1]^T.
# This is a rotation of -90 deg around the Y axis?
# Let's check -90 deg around Y:
# Z(0,0,1) -> (1,0,0) (X). Correct.
# Y(0,1,0) -> (0,1,0) (Y). Correct.
# X(1,0,0) -> (0,0,-1) (-Z).
# So if we rotate -90 deg around Y, we get:
# Normal = X.
# Sketch X = World -Z.
# Sketch Y = World Y.
# This is close. We want Sketch X = World Y, Sketch Y = World Z.
# So we need to swap the sketch axes? Or just draw the rectangle differently.
# If Sketch X = World -Z (Axial), and Sketch Y = World Y (Circumferential).
# Then we draw a rectangle of size (keyway_height, keyway_width) in the sketch plane.
# This rectangle lies in the plane X=R.
# The Pocket cuts along Normal (World X).
# This works perfectly!
# So:
# - Sketch X (World -Z) -> Length = keyway_height (Axial)
# - Sketch Y (World Y) -> Length = keyway_width (Circumferential)
# - Pocket cuts along World X (Radial).

# Correct Plane Rotation: -90 degrees around Y axis.
plane_key.Placement = App.Placement(App.Vector(params.smooth_shaft_diameter / 2.0, 0, 0))
plane_key.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), -math.pi / 2)
doc.recompute()

# Sketch for Keyway
sketch_key = body.newObject("Sketcher::SketchObject", "Sketch_Key")
sketch_key.Placement = App.Placement(App.Vector(0, 0, 0)) # Local coords on the plane
# Draw a rectangle:
# - Along Sketch X (World -Z): keyway_height
# - Along Sketch Y (World Y): keyway_width
sketch_key.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params.keyway_height, 0, 0)))
sketch_key.addGeometry(Part.LineSegment(App.Vector(params.keyway_height, 0, 0), App.Vector(params.keyway_height, params.keyway_width, 0)))
sketch_key.addGeometry(Part.LineSegment(App.Vector(params.keyway_height, params.keyway_width, 0), App.Vector(0, params.keyway_width, 0)))
sketch_key.addGeometry(Part.LineSegment(App.Vector(0, params.keyway_width, 0), App.Vector(0, 0, 0)))

# Constraints to ensure it's a rectangle
sketch_key.addConstraint(Sketcher.Constraint("Horizontal", 0))
sketch_key.addConstraint(Sketcher.Constraint("Vertical", 0))
sketch_key.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 1))
doc.recompute()

# Pocket Feature
pocket_key = body.newObject("PartDesign::Pocket", "Pocket_Key")
pocket_key.Profile = sketch_key
pocket_key.Type = "ThroughAll" # Cut through the entire shaft radially
pocket_key.Reference = (body, ["Face1"]) # Ensure it references the body face
doc.recompute()

# 5. Pattern the Keyways
# We need to pattern the pocket around the Z axis (shaft axis).
# The pocket is at angle 0 (tangent at X=R).
# We want to pattern it num_keyway times.
# Angle per keyway = 360 / num_keyway.
# But wait, the pocket is a feature. We can pattern the feature.
# However, the pocket is defined by a sketch on a specific plane.
# We need to pattern the pocket feature itself.
# PartDesign::PolarPattern can pattern a feature.
# Axis: Z_Axis.
# Angle: 360 / num_keyway.
# Occurrences: num_keyway.
# But we need to ensure the pattern is centered correctly.
# The pocket is at X=R. The center of the shaft is (0,0,0).
# The pattern axis should be the Z axis.
# The pocket feature is at angle 0.
# So we just need to pattern it.

# Create Z_Axis for reference
z_axis = doc.addObject("Part::Line", "Z_Axis")
z_axis.Placement = App.Placement(App.Vector(0, 0, 0))
z_axis = z_axis.addLine(App.Vector(0, 0, 0), App.Vector(0, 0, 1))
doc.recompute()

# Polar Pattern
pattern = body.newObject("PartDesign::PolarPattern", "Pattern_Key")
pattern.Originals = [pocket_key]
pattern.Axis = (z_axis, [""])
pattern.Angle = 360.0 / params.num_keyway
pattern.Occurrences = params.num_keyway
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))
doc.recompute()
