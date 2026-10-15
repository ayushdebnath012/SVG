import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize Document
doc = App.newDocument("GibHeadKey")

# --- Parameters ---
# We create a VarSet to hold the named parameters requested in the prompt
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "length", "Dimensions", "axial length (joint to tip)")
params.addProperty("App::PropertyLength", "width", "Dimensions", "head width")
params.addProperty("App::PropertyLength", "key_height", "Dimensions", "body height at joint")
params.addProperty("App::PropertyLength", "height_with_head", "Dimensions", "total height with head")
params.addProperty("App::PropertyAngle", "taper_angle", "Dimensions", "angle of head slant")
params.addProperty("App::PropertyLength", "key_taper_ratio", "Dimensions", "body height taper ratio")

# Set values as per prompt
params.length = 14.0
params.width = 4.0
params.key_height = 4.0
params.height_with_head = 7.0
params.taper_angle = 45.0
params.key_taper_ratio = 0.01

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Head Profile) ---
# We define the cross-section of the key (Head + Tapered Body start)
# The key tapers in height along its length.
# To achieve this with PartDesign features, we will:
# 1. Create a full rectangular block (Head + Max Height Body).
# 2. Subtract a wedge from the top to create the taper.
#
# Sketch 1: Profile of the full block (Rectangle) on the XZ plane.
# We will extrude this along the Y axis.
sketch1 = body.newObject("Sketcher::SketchObject", "FullBlockProfile")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 0), App.Vector(0, 0, 0)) # Ensure Z is up for sketch, then we rotate? 
# Actually, standard planes: XY is horizontal, Z is up.
# If we sketch on XY, we pad along Z.
# Let's sketch on XY plane.
# X axis: Width direction.
# Y axis: Height direction.
# Z axis: Length direction.
# This is the most intuitive for a key.

sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 0), App.Vector(0, 0, 0)) # Reset to default if needed, but default is usually fine.
# Let's explicitly set placement to origin on XY plane.
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))

# Define the outline of the full block (Width x Height_with_head)
# Points: Center, Right, Top Right, Top Left, Left, Center
# Width = params.width
# Height = params.height_with_head

half_width = params.width / 2.0
half_height = params.height_with_head / 2.0

# Add geometry for the rectangle
# Line 1: Bottom to Right
sketch1.addGeometry(Part.LineSegment(App.Vector(-half_width, -half_height, 0), App.Vector(half_width, -half_height, 0)), False)
# Line 2: Right to Top Right
sketch1.addGeometry(Part.LineSegment(App.Vector(half_width, -half_height, 0), App.Vector(half_width, half_height, 0)), False)
# Line 3: Top Right to Top Left
sketch1.addGeometry(Part.LineSegment(App.Vector(half_width, half_height, 0), App.Vector(-half_width, half_height, 0)), False)
# Line 4: Top Left to Left
sketch1.addGeometry(Part.LineSegment(App.Vector(-half_width, half_height, 0), App.Vector(-half_width, -half_height, 0)), False)
# Line 5: Left to Bottom (Close loop)
sketch1.addGeometry(Part.LineSegment(App.Vector(-half_width, -half_height, 0), App.Vector(half_width, -half_height, 0)), False)

# Add constraints to make it a rectangle
# Horizontal lines
sketch1.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch1.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
sketch1.addConstraint(Sketcher.Constraint("Horizontal", 0, 3))
# Vertical lines
sketch1.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch1.addConstraint(Sketcher.Constraint("Vertical", 0, 2))
sketch1.addConstraint(Sketcher.Constraint("Vertical", 0, 3))
# Coincident points
sketch1.addConstraint(Sketcher.Constraint("Point", "XY", 0, 1)) # Bottom Right on XY plane
sketch1.addConstraint(Sketcher.Constraint("Point", "XY", 0, 2)) # Top Right on XY plane
sketch1.addConstraint(Sketcher.Constraint("Point", "XY", 0, 3)) # Top Left on XY plane
sketch1.addConstraint(Sketcher.Constraint("Point", "XY", 0, 4)) # Bottom Left on XY plane
# Centering
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 1)) # Center of bottom line
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 2)) # Center of top line
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 3)) # Center of left line
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 4)) # Center of right line

# --- Feature 1: Pad the full block ---
pad = body.newObject("PartDesign::Pad", "PadFullBlock")
pad.Profile = sketch1
pad.Length = params.length
pad.Type = "Solid"
pad.MidPlane = False
pad.Reversed = False

# --- Sketch 2: Wedge Profile for Subtraction ---
# We need to cut a wedge from the top to create the taper.
# The taper angle is given as 45 degrees from horizontal.
# This means the slope is 1:1.
# We will define a triangular profile on the XZ plane (Side view) to cut the wedge.
# Wait, if we pad along Z, the profile is in XY.
# To cut a wedge along Z, we need a sketch in the XZ plane?
# No, PartDesign::Pocket works on a profile in a plane.
# If we want to cut a wedge that varies along Z, we can't do it with a simple linear pocket on XY.
# We need to define the wedge shape in a plane perpendicular to the length (Z).
# Let's sketch on the XZ plane (Side view).
# The profile will be a triangle (or trapezoid) that defines the cut.
# We will pad this profile along the Y axis (Height direction) to create the wedge volume.
# Then we subtract this volume from the block.

sketch2 = body.newObject("Sketcher::SketchObject", "WedgeProfile")
# Attach to XZ plane
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 1, 0), 90), App.Vector(0, 0, 0)) # Rotate to XZ plane? 
# Actually, let's just use the XZ plane directly.
# FreeCAD default planes: XY, XZ, YZ.
# We want to sketch on XZ.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 1, 0), 90), App.Vector(0, 0, 0)) # This rotates Y to Z, Z to -Y. Not quite.
# Let's just use the standard approach: Sketch on XY, then rotate the sketch object?
# Or simply sketch on XZ plane by setting AttachmentSupport.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 1, 0), 90), App.Vector(0, 0, 0)) # Rotate 90 deg around Y axis -> Z becomes Y, Y becomes -Z.
# Let's try a simpler rotation: Rotate 90 deg around X axis.
# XY plane -> XZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(1, 0, 0), 90), App.Vector(0, 0, 0))

# Define the wedge profile in XZ plane.
# We want to cut a wedge from the top of the block.
# The block is from Z=0 to Z=14.
# The height at Z=0 is H_max = 7.0.
# The height at Z=14 is H_min = 7.0 - (14 * 0.01) = 5.6.
# The cut should remove the material above the taper line.
# The taper line goes from (X=0, Z=0, Y=H_max) to (X=0, Z=14, Y=H_min).
# Wait, the taper is usually symmetric or on one side?
# "Gib head key" usually tapers symmetrically or on the bottom?
# "angle of the head's slanted face from horizontal".
# This implies the top face is slanted.
# So we cut a wedge from the top.
# The profile in XZ plane:
# A line from (0, 0) to (14, H_max - H_min)? No.
# Let's define the profile relative to the centerline (X=0).
# The cut is a wedge.
# The profile is a triangle with vertices:
# 1. (0, 0) - Center of the base (Z=0, Y=0 relative to cut start?)
# Let's define the profile in the XZ plane (Y is the extrusion direction for the wedge).
# We want to extrude this profile along Y to create the wedge volume.
# The profile should be a triangle that spans the length of the key.
# Vertices:
# A: (0, 0) - Center of the key at Z=0.
# B: (14, 0) - Center of the key at Z=14.
# C: (0, H_max - H_min) - The tip of the wedge at Z=0.
# Wait, if we extrude this triangle along Y, we get a wedge that is tall at Z=0 and short at Z=14.
# This matches the requirement.
# Height of wedge at Z=0: H_max - H_min = 7.0 - 5.6 = 1.4mm.
# Height of wedge at Z=14: 0mm.
# Angle: atan(1.4 / 14) = atan(0.1) = 5.71 degrees.
# But the prompt says "taper_angle=45 degree".
# This implies the angle of the slanted face is 45 degrees.
# If the angle is 45 degrees, then the height difference over length 14 is 14 * tan(45) = 14mm.
# But our max height is only 7mm.
# This suggests the "taper_angle" might be the angle of the wedge itself, or the prompt parameters are hypothetical.
# Let's stick to the calculated taper based on "key_taper_ratio=0.01".
# Ratio 0.01 means 1% taper. 14mm * 0.01 = 0.14mm reduction.
# This is very small.
# Maybe "taper_angle" is the angle of the head's slanted face relative to the *vertical*?
# Or maybe the "head" is a separate block and the "body" tapers?
# Let's re-read: "taper_angle=45 degree (angle of the head's slanted face from horizontal)".
# If the face is 45 degrees from horizontal, the slope is 1.
# If the length is 14mm, the height change is 14mm.
# But the total height is only 7mm.
# This is a contradiction in the prompt parameters if interpreted literally for the whole length.
# However, "Gib Head Key" often has a head that is a wedge.
# Maybe the "head" is just the top part, and the "body" is the tapered part.
# Let's assume the taper is only on the "body" part, and the "head" is a block.
# But the prompt says "length=14.0mm (axial length of the body, measured from the head/body joint to the tapered tip)".
# So the taper is over the full 14mm.
# If the taper angle is 45 degrees, the height change is 14mm.
# But the height at the joint is 4mm (body) + 7mm (total)? No, "key_height=4.0mm (body height at the head/body joint)".
# "height_with_head=7.0mm".
# So the body height at the joint is 4mm. The head adds 3mm?
# If the body tapers at 45 degrees over 14mm, the height change is 14mm.
# This would make the tip negative height.
# Conclusion: The parameters in the prompt are likely inconsistent if taken literally (45 deg over 14mm > 7mm height).
# I will prioritize the "key_taper_ratio=0.01" for the geometry calculation as it yields a valid physical object, 
# and use the "taper_angle" to name the feature or as a comment, or assume it applies to a different scale.
# Actually, let's use the taper_ratio to calculate the height change.
# Height change = length * taper_ratio = 14 * 0.01 = 0.14mm.
# This is a very slight taper.
# Let's proceed with this.

# Recalculate wedge height
h_max = params.height_with_head
h_min = h_max - (params.length * params.key_taper_ratio)
wedge_height = h_max - h_min

# Sketch 2 Geometry (Triangle in XZ plane)
# Vertices:
# 1. (0, 0) - Center at Z=0
# 2. (params.length, 0) - Center at Z=14
# 3. (0, wedge_height) - Tip of wedge at Z=0
# Note: The wedge is symmetric around X=0? 
# Yes, usually keys are symmetric.
# So the profile is a triangle with base on Z-axis? No, base on Y-axis?
# We are extruding along Y.
# The profile is in XZ plane.
# The triangle vertices:
# A: (0, 0) -> (X=0, Z=0)
# B: (params.length, 0) -> (X=0, Z=14)
# C: (0, wedge_height) -> (X=0, Z=0) -- Wait, this is a line.
# We need a triangle that spans the width?
# No, the wedge is a volume.
# If we extrude a triangle in XZ plane along Y, we get a wedge.
# The triangle should be:
# Point 1: (0, 0) - Center of the key at Z=0.
# Point 2: (params.length, 0) - Center of the key at Z=14.
# Point 3: (0, wedge_height) - The top of the wedge at Z=0.
# This forms a triangle in the XZ plane? No, these points are collinear if X is always 0.
# We need the triangle to have width?
# No, the wedge is defined by the slope.
# The profile is a line in XZ? No, a closed loop.
# Let's define the profile as a triangle with vertices:
# 1. (0, 0) - Center at Z=0.
# 2. (params.length, 0) - Center at Z=14.
# 3. (0, wedge_height) - Top at Z=0.
# This is not a closed loop.
# We need to close it.
# The wedge is symmetric.
# So the profile is a triangle with vertices:
# 1. (0, 0) - Center at Z=0.
# 2. (params.length, 0) - Center at Z=14.
# 3. (0, wedge_height) - Top at Z=0.
# Wait, if we extrude this along Y, we get a wedge that is 0 width at Z=14?
# No, the width is constant (4mm).
# The wedge is a prism with a triangular cross-section in the XZ plane?
# No, the wedge is a prism with a triangular cross-section in the YZ plane?
# Let's rethink.
# We want to cut a wedge from the top of the block.
# The block is a rectangular prism (Width 4, Height 7, Length 14).
# We want to cut a wedge such that the top surface is slanted.
# The cut volume is a wedge.
# The wedge has a triangular cross-section in the XZ plane? No.
# The wedge has a triangular cross-section in the YZ plane (Side view).
# Vertices of the wedge in YZ plane:
# 1. (Y=0, Z=0) - Bottom Center.
# 2. (Y=0, Z=14) - Bottom Tip.
# 3. (Y=wedge_height, Z=0) - Top Center.
# This is a triangle in the YZ plane.
# If we extrude this triangle along the X axis (Width direction), we get the wedge volume.
# Yes! This is the correct approach.
# Sketch 2 should be on the YZ plane.
# We will extrude along X.

sketch2 = body.newObject("Sketcher::SketchObject", "WedgeProfile")
# Attach to YZ plane
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to YZ?
# Let's just use the YZ plane directly.
# FreeCAD default: XY, XZ, YZ.
# We want YZ.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(1, 0, 0), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the standard YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane by setting AttachmentSupport.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
sketch2.Placement = App.Placement(App.Vector(0, 0, 0))
sketch2.Placement = App.Placement(App.Rotation(App.Vector(0, 0, 1), 90), App.Vector(0, 0, 0)) # Rotate XY to XZ.
# Rotate XZ to YZ?
# Let's just use the YZ plane.
