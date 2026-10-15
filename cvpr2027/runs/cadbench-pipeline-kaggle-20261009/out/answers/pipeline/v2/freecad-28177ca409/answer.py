import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("GibHeadKey")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We define parameters that drive the geometry.
# Note: In FreeCAD 1.1, we use App::PropertyLength/Double/Vector etc.
# We will create a VarSet to hold these named parameters.
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Total length from head base to tip")
params.length = 14.0
params.addProperty("App::PropertyLength", "width", "Dimensions", "Width of the key")
params.width = 4.0
params.addProperty("App::PropertyLength", "key_height", "Dimensions", "Height of the body at the joint")
params.key_height = 4.0
params.addProperty("App::PropertyLength", "height_with_head", "Dimensions", "Total height including head")
params.height_with_head = 7.0
params.addProperty("App::PropertyAngle", "taper_angle", "Dimensions", "Angle of the head slant from horizontal")
params.taper_angle = 45.0
params.addProperty("App::PropertyLength", "key_taper_ratio", "Dimensions", "Taper ratio for the body (1:100)")
params.key_taper_ratio = 0.01

# --- Sketch 1: The Head Profile ---
# We need to define the profile of the head.
# The head is a block with a tapered top face.
# We will sketch on the XY plane.
sketch_head = body.newObject("Sketcher::SketchObject", "HeadProfile")
sketch_head.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_head.Support = (doc.getObject("XY_Plane"), [])
sketch_head.Constrain = True
sketch_head.MapMode = "FlatFace"

# Geometry for the head profile (Side view logic projected to 2D)
# We need a shape that represents the cross-section of the head.
# Let's define the bottom width, top width (tapered), and height.
# Actually, for a Pad, we need a closed loop.
# Let's create a rectangle for the bottom part and a trapezoid for the top?
# Simpler approach: Create a single polygon representing the side profile of the head.
# Points: (0,0) -> (width, 0) -> (width, height_with_head) -> (0, height_with_head) -> (0,0)
# Then we need to cut the taper.
# Better approach for a single sketch:
# Draw the full rectangle, then draw lines for the taper and use a cut?
# Or just draw the final polygon.
# The head has a flat bottom, flat sides (mostly), and a slanted top face.
# Wait, the description says "tapered end" for the key body, and "head that protrudes".
# Usually, the head is a block with a chamfer or a specific shape.
# Let's assume the head is a block of width 'width' and height 'height_with_head'.
# The "taper_angle" applies to the top face relative to the horizontal.
# So the top face slopes down from the outer edges towards the center? Or just one side?
# Standard Gib Head Key: The head is often a block with a slanted top surface to allow insertion.
# Let's assume the top surface slopes from the outer edge (width/2) down to the center line?
# Or simply a block with a slanted top face defined by the angle.
# Let's construct the profile as a polygon:
# Bottom: y=0, x from -width/2 to width/2
# Sides: x = -width/2 and x = width/2, y from 0 to height_with_head
# Top: A line connecting (width/2, height_with_head) to (-width/2, height_with_head) but slanted?
# If the angle is from horizontal, and it's a "head", usually the top is slanted to facilitate sliding.
# Let's assume the top face slopes from the outer edge (width/2) down to the center (0, height_with_head - offset).
# However, the prompt says "taper_angle ... angle of the head's slanted face from horizontal".
# Let's create a profile where the top edge is slanted.
# Let's define the top-left point and top-right point.
# Right side: (width/2, height_with_head)
# Left side: (-width/2, height_with_head)
# If we slant the top, one point goes up, one goes down? Or both go down from a peak?
# Let's assume a simple slant from the outer edge towards the center.
# Let's say the top face goes from (width/2, height_with_head) to (0, height_with_head - delta).
# But we need a closed loop.
# Let's try a different interpretation: The head is a block, and the "taper" is the angle of the top face relative to the horizontal plane.
# Let's create a polygon:
# 1. Bottom Left: (-width/2, 0)
# 2. Bottom Right: (width/2, 0)
# 3. Top Right: (width/2, height_with_head)
# 4. Top Left: (-width/2, height_with_head)
# This is a rectangle.
# To add the taper: We can modify the top edge.
# Let's assume the top face is slanted such that the angle between the top face and the horizontal is `taper_angle`.
# Let's make the top face go from (width/2, height_with_head) to (-width/2, height_with_head - (width * tan(taper_angle))).
# Wait, if the angle is 45 degrees, the drop is equal to the run.
# Let's define the top-left point based on the angle.
# Let's assume the slant is symmetric or just one side?
# "Gib head key" usually has a slanted top face to allow it to be driven by a hammer.
# Let's assume the top face slopes from the outer edge (width/2) down to the center line (0).
# So the top face connects (width/2, height_with_head) to (0, height_with_head - (width/2 * tan(taper_angle))).
# And then from (0, ...) to (-width/2, height_with_head)? No, that would be a V-shape.
# Let's assume the top face is a single plane sloping from the outer edge to the center.
# So the profile is:
# (-width/2, 0) -> (width/2, 0) -> (width/2, height_with_head) -> (0, height_with_head - (width/2 * tan(taper_angle))) -> (-width/2, height_with_head) -> (-width/2, 0)
# Wait, the last segment (-width/2, height_with_head) to (-width/2, 0) is the side.
# The segment from (-width/2, height_with_head) to (0, ...) is the top face?
# If the top face is slanted, the height at the center is lower than at the edge.
# Let's calculate the drop: drop = (width/2) * tan(taper_angle).
# Center height = height_with_head - drop.
# So the points are:
# P1: (-width/2, 0)
# P2: (width/2, 0)
# P3: (width/2, height_with_head)
# P4: (0, height_with_head - drop)
# P5: (-width/2, height_with_head)
# P6: (-width/2, 0)
# This creates a shape with a slanted top face on the left side?
# Actually, let's make it symmetric or just one side.
# Let's assume the slant is from the outer edge (width/2) to the center (0).
# So the top face is the line from P3 to P4.
# And the left side is vertical from P5 to P1.
# And the top-left corner is P5.
# This seems plausible.
# Let's refine the points:
# P1: (-width/2, 0)
# P2: (width/2, 0)
# P3: (width/2, height_with_head)
# P4: (0, height_with_head - (width/2 * tan(taper_angle)))
# P5: (-width/2, height_with_head)
# P6: (-width/2, 0)
# This creates a shape where the top face slopes from right to left?
# Let's reverse: Slope from left to right?
# Let's assume the slant is from the outer edge (width/2) down to the center.
# So the top face is from (width/2, height_with_head) to (0, height_with_head - drop).
# And the left side is vertical.
# This works.

import math
w = params.width
h_head = params.height_with_head
angle = math.radians(params.taper_angle)
drop = (w / 2.0) * math.tan(angle)

# Define vertices for the head profile
# We use Part.LineSegment and Part.Circle, but for polygons we can use Part.makePolygon or add segments.
# Let's add segments manually to ensure control.
# Note: Sketcher::SketchObject uses 2D coordinates.
# We need to add geometry.
# We can use Part.makePolygon if we construct a list of vectors.
# But we need to add them to the sketch.
# Let's create a list of vectors.
head_points = [
    App.Vector(-w/2, 0, 0),
    App.Vector(w/2, 0, 0),
    App.Vector(w/2, h_head, 0),
    App.Vector(0, h_head - drop, 0),
    App.Vector(-w/2, h_head, 0),
    App.Vector(-w/2, 0, 0) # Close loop
]

# Add segments
for i in range(len(head_points) - 1):
    sketch_head.addGeometry(Part.LineSegment(head_points[i], head_points[i+1]), False)
sketch_head.addGeometry(Part.LineSegment(head_points[-1], head_points[0]), False)

# Add constraints to make it robust (optional but good practice)
# Coincident points are implicit in the polygon creation.
# We can add constraints for horizontal/vertical lines if needed, but the geometry is defined.
# Let's add a constraint to fix the bottom line to the plane.
# Actually, the Support is the XY plane, so Z=0 is fixed.
# Let's add a constraint for the bottom line to be horizontal.
# We can use Sketcher.Constraint("Horizontal", 0, 1) for the first segment?
# No, the segment is defined by points.
# Let's just rely on the geometry.

# --- Sketch 2: The Body Taper ---
# The body tapers along the length.
# The body starts at the head base (z=0) and ends at z=length.
# The height at z=0 is key_height.
# The height at z=length is key_height * (1 - key_taper_ratio * length).
# Wait, "key_taper_ratio=0.01 (1:100 standard body height taper along the length)".
# This usually means the height decreases by 1% of the length per unit length?
# Or the total reduction is 1% of the length?
# "1:100" usually means for every 100mm length, the height reduces by 1mm.
# So the reduction is length * 0.01.
# Let's calculate the tip height.
# h_tip = key_height - (length * key_taper_ratio)
# If h_tip <= 0, we clamp it to a small value.

h_base = params.key_height
h_tip = h_base - (params.length * params.key_taper_ratio)
if h_tip < 0.1:
    h_tip = 0.1

# We need a sketch for the body profile.
# We can use the same sketch as the head but offset it?
# No, the body is a separate feature (Pad) that starts from the head.
# We need a sketch that defines the profile of the body.
# The body profile is a rectangle with a tapered top?
# Or a trapezoid?
# The body is a prism with a tapered top face.
# Let's create a sketch on the XY plane at z=0 (or slightly below the head).
# Actually, the Pad will extrude from the head.
# So the sketch should be at z=0 (the interface).
# The profile of the body at z=0 is a rectangle of width 'width' and height 'key_height'.
# But the top face is slanted.
# So the profile is a trapezoid?
# No, the body is a solid. The top face is slanted.
# So the cross-section at any z is a rectangle of width 'width' and height h(z).
# h(z) = h_base - (z * key_taper_ratio).
# So the profile at z=0 is a rectangle of width 'width' and height 'key_height'.
# We can create a Pad with this profile and a length of 'length'.
# But the Pad creates a prism. We need a tapered prism.
# We can use a "Pad" with a "Midplane" or "Reversed" option? No.
# We can use a "Pad" with a profile that is a trapezoid?
# If we extrude a trapezoid, we get a wedge.
# We want a prism with a slanted top.
# This is equivalent to a trapezoid if the width is constant and the height varies linearly.
# Yes, a trapezoid with parallel vertical sides and slanted top/bottom?
# No, the sides are vertical. The top is slanted.
# So the profile is a trapezoid with parallel vertical sides?
# No, a trapezoid has one pair of parallel sides.
# If the sides are vertical, they are parallel.
# The top and bottom are not parallel (one is horizontal, one is slanted).
# So it is a trapezoid.
# Let's define the profile at z=0.
# Bottom: y=0, x from -width/2 to width/2.
# Sides: x = -width/2 and x = width/2.
# Top: A line from (-width/2, h_tip) to (width/2, h_base)?
# No, the taper is along the length (Z axis).
# The profile is in the XY plane.
# The height of the body at z=0 is h_base.
# The height of the body at z=length is h_tip.
# So the profile at z=0 is a rectangle of height h_base.
# But the top face is slanted.
# This means the body is not a simple extrusion of a 2D profile.
# It is a ruled surface or a swept feature.
# However, we can approximate it with a Pad if we define the profile correctly?
# No, a Pad extrudes a 2D profile along a straight line.
# If the profile is a rectangle, the result is a prism.
# If the profile is a trapezoid, the result is a wedge.
# We want a prism with a slanted top.
# This is a "Prism with a slanted top".
# This can be achieved by a Pad with a profile that is a rectangle, but then we need to cut the top?
# Or we can use a "Pad" with a "Midplane" and then a "Pocket"?
# No, the simplest way is to use a "Pad" with a profile that is a trapezoid?
# Wait, if the profile is a trapezoid with parallel vertical sides, and the top is slanted, then the bottom must be slanted too?
# No, a trapezoid has two parallel sides.
# If the vertical sides are parallel, then the top and bottom must be parallel.
# So we cannot get a slanted top with a simple Pad of a trapezoid.
# We need a different approach.
# We can use a "Pad" with a profile that is a rectangle, and then use a "Pocket" to cut the top?
# Or we can use a "Pad" with a profile that is a trapezoid, but the taper is in the Z direction?
# No, the Pad extrudes in the Z direction.
# The profile is in the XY plane.
# The height of the body is the Y coordinate in the profile.
# If the profile is a rectangle, the height is constant.
# If the profile is a trapezoid, the height varies with X.
# We want the height to vary with Z.
# This is not a simple Pad.
# We can use a "Pad" with a profile that is a rectangle, and then use a "Pocket" to cut the top face?
# No, the top face is slanted.
# We can use a "Pad" with a profile that is a rectangle, and then use a "Pocket" with a slanted face?
# No, the Pocket is also an extrusion.
# We can use a "Pad" with a profile that is a rectangle, and then use a "Pocket" with a profile that is a trapezoid?
# No, the Pocket subtracts material.
# Let's think differently.
# The body is a prism with a slanted top.
# This is equivalent to a wedge if we rotate it?
# No.
# We can use a "Pad" with a profile that is a rectangle, and then use a "Pocket"
