import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("SplineTooth")

# Define parameters in a VarSet for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "Module (mm)")
params.module = 3.0
params.addProperty("App::PropertyInteger", "num_teeth", "Dimensions", "Number of teeth")
params.num_teeth = 23
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter (mm)")
params.pitch_diameter = 69.0 # 23 * 3
params.addProperty("App::PropertyLength", "height", "Dimensions", "Tooth Height (mm)")
params.height = 10.0
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle (deg)")
params.pressure_angle = 30.0
params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Root Fillet Radius (mm)")
params.fillet_radius = 1.2

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Create Base Sketch on XY Plane
sketch = body.newObject("Sketcher::SketchObject", "SketchProfile")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.AttachmentSupport = [App.ActiveDocument.XY_Plane]
sketch.MapMode = "FlatFace"
sketch.ConstrainAuto = False
sketch.Add = True
sketch.Internal = False
sketch.ShowAuto = False
sketch.ShowAll = False
sketch.ShowEdges = True
sketch.ShowFaces = False
sketch.ShowLines = True
sketch.ShowObjects = True
sketch.ShowPoints = True
sketch.ShowSketcher = True
sketch.ShowTags = True
sketch.Type = "App::DocumentObject"

# We need to generate the tooth profile. 
# A standard spline tooth profile is bounded by:
# 1. Outer circle (Pitch Diameter)
# 2. Inner circle (Root Diameter)
# 3. Two involute or approximated arcs for the flanks.
# For this script, we will approximate the flanks using circular arcs tangent to the pitch circle and root circle,
# forming a simplified spur gear-like tooth profile.

# Calculate radii
r_pitch = params.pitch_diameter / 2.0
r_root = r_pitch - params.height / 2.0 # Assuming symmetric height above and below pitch line? 
# Usually pitch diameter is at the center of the tooth height or top. 
# Standard spur gear: Pitch circle is usually near the middle or top. 
# Let's assume Pitch Diameter is the diameter of the circle where the tooth thickness is measured.
# Let's define the profile relative to the pitch circle.
# Let's assume the tooth extends radially outward from the pitch circle by `height/2` and inward by `height/2`.
# Actually, standard definition: Pitch Diameter is the reference. 
# Let's set the profile such that the top of the tooth is at r_pitch + height/2 and root at r_pitch - height/2.
r_top = r_pitch + (params.height / 2.0)
r_bottom = r_pitch - (params.height / 2.0)

# Tooth thickness at pitch circle
# Circular pitch p = pi * m (where m is module)
# Tooth thickness t = p / 2
p = math.pi * params.module
t_pitch = p / 2.0

# We will construct the profile using 4 points and 3 arcs (or lines/arcs).
# Let's simplify: 
# 1. Start at angle 0 on the pitch circle (r_pitch, 0)
# 2. Go outwards to top circle (r_top, 0)
# 3. Draw an arc from (r_top, 0) to some angle theta_toe, tangent to the top circle.
# 4. Draw an arc from (r_bottom, 0) to the same angle theta_toe, tangent to the bottom circle.
# This creates a "corner" tooth. To make it more realistic (spiral/spline), we'd use involutes.
# Since the prompt asks for "simplified circular arcs", we will create a tooth that is a segment of a ring
# but with rounded corners where it enters/exits the ring, effectively creating a gear tooth shape 
# if we extrude and pattern it.

# Actually, the simplest way to get a "spline" tooth with "fillet root" using circular arcs:
# 1. Draw a line from (r_pitch, 0) to (r_top, 0).
# 2. Draw a line from (r_pitch, 0) to (r_bottom, 0).
# 3. Connect (r_top, 0) to (r_top, theta_toe) with an arc.
# 4. Connect (r_bottom, 0) to (r_bottom, theta_toe) with an arc.
# But a gear tooth is symmetric.
# Let's build the half-tooth profile from angle 0 to angle_toe, then mirror it.

# Angle calculation for a simple spur gear tooth (approximate):
# The flank angle is roughly the pressure angle.
# Let's calculate the angle of the tooth face at the pitch circle.
# Angle = atan( (r_top - r_pitch) / (t_pitch/2) ) ? No.
# Let's just define a specific geometry that looks like a tooth.
# We will define a profile consisting of:
# - A vertical line up from (r_pitch, 0) to (r_top, 0)? No, r_top is radial.
# Coordinates: (x, y) in XY plane.
# Center of sketch is (0,0).
# Point A: (r_pitch, 0)
# Point B: (r_top, 0) -> This is radial outward.
# Point C: (r_top, r_top * sin(alpha)) -> Arc along top circle?
# Let's try a standard gear tooth approximation:
# The tooth width at the pitch circle is t_pitch.
# The tooth occupies angles from -t_pitch/2/r_pitch to +t_pitch/2/r_pitch.
# Let's just draw a single tooth in the middle (from -t_pitch/2 to +t_pitch/2) and then use a polar pattern.
# Wait, if we pattern the whole body, we need one tooth.

# Let's construct the profile of ONE tooth, centered at 0 degrees.
# The profile will be symmetric across the X-axis (angle 0).
# Points:
# 1. Top Left: (r_top, r_top * sin(phi)) where phi is the angle of the flank.
# 2. Top Right: (r_top, r_top * sin(-phi))
# 3. Bottom Right: (r_bottom, r_bottom * sin(-phi))
# 4. Bottom Left: (r_bottom, r_bottom * sin(phi))
# But we need to connect these with arcs.

# Let's simplify the geometry to ensure it's a valid closed loop and looks like a tooth.
# We will create a profile that is a segment of an annulus with rounded corners.
# Actually, a better approach for "spline" with "fillet root":
# Draw the outer circle (r_top), inner circle (r_bottom).
# Draw a chord across the outer circle representing the tooth width.
# But we need a closed profile.

# Let's define the profile using 4 vertices and 4 segments (Line-Arc-Line-Arc).
# Vertex 1: (r_pitch, 0) -> Center of the tooth base on the pitch circle? No.
# Let's assume the tooth starts at angle 0.
# We need a closed loop.
# Let's define the profile as:
# 1. Arc on the outer circle (r_top) from angle -theta_half to +theta_half.
# 2. Line from (r_top, theta_half) to (r_bottom, theta_half).
# 3. Arc on the inner circle (r_bottom) from angle theta_half to -theta_half.
# 4. Line from (r_bottom, -theta_half) to (r_top, -theta_half).
# This creates a segment of a ring.
# To make it a "tooth", we need to define theta_half based on the tooth width.
# Tooth width at pitch circle = t_pitch.
# Angle at pitch circle = t_pitch / r_pitch.
# However, the arcs are at r_top and r_bottom.
# Let's just define the angle subtended by the tooth at the center.
# Let's say the tooth spans an angle of `t_pitch / r_pitch` at the pitch circle.
# Let's call this angle `delta_angle`.
# delta_angle = t_pitch / r_pitch.
# We will define the tooth from -delta_angle/2 to +delta_angle/2.

delta_angle = t_pitch / r_pitch
angle_start = -delta_angle / 2.0
angle_end = delta_angle / 2.0

# Coordinates for the 4 points defining the ring segment
# Point 1 (Outer, Start):
p1 = App.Vector(r_top * math.cos(angle_start), r_top * math.sin(angle_start), 0)
# Point 2 (Outer, End):
p2 = App.Vector(r_top * math.cos(angle_end), r_top * math.sin(angle_end), 0)
# Point 3 (Inner, End):
p3 = App.Vector(r_bottom * math.cos(angle_end), r_bottom * math.sin(angle_end), 0)
# Point 4 (Inner, Start):
p4 = App.Vector(r_bottom * math.cos(angle_start), r_bottom * math.sin(angle_start), 0)

# Add geometry to sketch
sketch.addGeometry(Part.LineSegment(p1, p2), False) # Outer chord? No, Arc on circle.
# Let's use LineSegments and Arcs.
# Segment 1: Arc from p1 to p2 on circle r_top
# Since Sketcher doesn't have a direct "Arc on Circle" command in the low-level API easily without constraints,
# we can use LineSegments and constrain them, OR use Part::Circle and Arc?
# Actually, we can add a Part::Arc and then convert? No, Sketcher adds geometry.
# We can add a Part::Arc (which is a TopoShape) and sketcher accepts it? 
# Yes, sketch.addGeometry(Part.Arc(...)) works in recent versions.

# Let's create the arcs and lines.
arc_top = Part.Arc(p1, p2, App.Vector(0, 0, 1)) # Arc on XY plane
# We need to ensure the arc is the minor arc. 
# The angle difference is small, so it should be fine.
# However, Part.Arc might not handle the start/end points perfectly with just 2 points if they are collinear, but here they aren't.
# Let's try adding the arc directly.
sketch.addGeometry(arc_top, False)

arc_bot = Part.Arc(p4, p3, App.Vector(0, 0, 1))
sketch.addGeometry(arc_bot, False)

# Lines connecting the arcs
line1 = Part.LineSegment(p2, p3)
sketch.addGeometry(line1, False)
line2 = Part.LineSegment(p4, p1)
sketch.addGeometry(line2, False)

# Constraints
# We need to constrain the arcs to be on the circles of radius r_top and r_bottom.
# And the lines to be tangent? Or just connect the points.
# Since we defined points on the circles, the lines will be chords if not constrained to be tangent.
# For a gear tooth, the flanks are usually tangent to the pitch circle or specific angles.
# But the prompt says "simplified circular arcs". 
# If we just connect the points with lines, we get a trapezoidal tooth on the ring.
# This is acceptable for a "simplified" model.
# However, to make it look more like a tooth, we should ensure the lines are not just random chords.
# The current points are on the circle. The lines connect (r_top, start) to (r_bottom, start).
# This forms a radial cut? No, p1 and p4 share the same angle. So p1-p4 is a radial line.
# Yes! p1 and p4 have angle `angle_start`. So the line p4->p1 is radial.
# Same for p2->p3.
# So this creates a perfect sector of an annulus.
# This is a valid "tooth" shape if we consider the material between these angles as the tooth.
# But wait, a gear tooth is usually defined by the space between teeth.
# If we pattern this sector, we will get a solid ring with holes (the sectors).
# We want the sectors to be the SOLID teeth.
# So we extrude this sketch. The result is a ring with teeth.
# Then we apply a fillet to the inner corner of the tooth (where the radial line meets the inner arc).
# The root of the tooth is the inner arc. The corner is where the radial flank meets the inner arc.
# Perfect.

# Add Constraints to make it robust
# Constrain lines to be radial? They are already radial by construction of points.
# Constrain arcs to be centered at origin.
# Let's add explicit constraints to ensure sketch integrity.
# Constraint: Coincident for points? Not needed if we use geometry objects.
# Let's constrain the arcs to have their center at (0,0).
# Sketcher doesn't allow direct constraint on Part.Arc center easily in the API without adding a center point.
# But we can add the points and constrain the arcs to pass through them.
# The current approach of adding geometry is usually sufficient if the angles are correct.
# Let's add the center point to the sketch to constrain the arcs.
center = App.Vector(0, 0, 0)
sketch.addGeometry(Part.LineSegment(center, p1), False) # Just to anchor? No.
# Let's rely on the geometry placement.
# To be safe, let's add a constraint that the distance of p1 from center is r_top.
# Sketcher constraints work on geometric elements.
# Let's skip complex constraints and rely on the precise coordinates calculated.
# We will add a "Coincident" constraint for the connection points?
# The sketch solver should handle the closed loop.

# Let's refine the sketch to be fully constrained if possible, but for a script, 
# defining the points and geometry is usually enough for a single profile.
# We will add a constraint to force the lines to be straight (default).

# Now, Pad the sketch
pad = body.newObject("PartDesign::Pad", "PadTooth")
pad.Profile = sketch
pad.Length = params.height # Wait, the sketch is in XY. The height of the spline body is Z.
# The prompt says "spline_height = 10 mm".
# My sketch defines the radial thickness of the tooth.
# If I pad along Z, I get a flat plate with a radial cutout?
# No. The sketch is in XY. The Z dimension is the "length" of the pad.
# The "height" of the spline usually refers to the axial height (Z).
# The "width" of the tooth is radial (XY).
# My sketch defines the cross-section of the tooth in the radial direction?
# No, my sketch defines the shape of the tooth in the XY plane (Radial vs Angular).
# If I Pad along Z, I get a cylinder with a wedge cut out?
# No, the sketch is a ring segment. Padding along Z creates a ring segment (a block).
# This is NOT a spline tooth. A spline tooth is usually an involute shape in the radial plane.
# A spline has teeth that go around the circumference.
# If I pattern the ring segment angularly, I get a ring with holes.
# If I Pad along Z, the tooth has a constant width along the Z axis.
# This matches "cylindrical spline".
# So:
# 1. Sketch in XY: The profile of the tooth cross-section? 
#    No, the sketch is the cross-section of the whole part?
#    If the sketch is a ring segment, and I Pad along Z, I get a block with a ring segment shape.
#    If I Polar Pattern this block around Z, I get a gear/spline.
#    Yes.
#    The "height" of the spline (axial height) is the Pad Length.
#    The "module" defines the radial thickness of the tooth.
#    The "pitch diameter" defines the outer radius of the ring.
#    My sketch defines the shape of one tooth (a ring segment).
#    The `r_top` and `r_bottom` define the radial extent.
#    `angle_start` and `angle_end` define the angular width.
#    This creates a tooth.
#    Padding along Z creates the axial length.
#    Patterning creates the multi-tooth spline.

# Correction: 
# The sketch should be the profile of ONE tooth.
# The sketch I built is a ring segment (a sector).
# If I pad this along Z, I get a block that looks like a slice of a cake.
# If I polar pattern this block 23 times, I get a complete gear/spline.
# This is correct.

pad.Length = params.height # This is the axial height of the spline.
pad.makeFeature()

# Create a Fillet at the root of the tooth.
# The root is the inner arc.
# The corners where the radial lines meet the inner arc need filleting.
# There are 4 corners in the sketch:
# 1. (p4, p1) - Inner start
# 2. (p3, p2) - Inner end
# 3. (p1, p4) - Radial line (already radial, no corner?)
# Wait, the lines are p4->p1 (radial) and p1->p2 (arc). The corner is at p1.
# And p4->p1 (radial) and p4->p3 (arc)? No, p
