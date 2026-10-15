import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("SplineTooth")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We will store parameters in a VarSet object attached to the Body to keep them organized
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "Module")
params.module = 3.0
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.pitch_diameter = 69.0
params.addProperty("App::PropertyLength", "height", "Dimensions", "Height")
params.height = 10.0
params.addProperty("App::PropertyInteger", "num_teeth", "Dimensions", "Number of Teeth")
params.num_teeth = 23
params.addProperty("App::PropertyLength", "fillet_radius", "Dimensions", "Fillet Radius")
params.fillet_radius = 1.2
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = 30.0

# --- Base Sketch (Outer Cylinder) ---
# Create a sketch on the XY plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Support = (doc.getObject("XY_Plane"), [])
base_sketch.MapMode = "FlatFace"

# Add a circle for the pitch diameter
base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_diameter / 2.0), False)
base_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.pitch_diameter / 2.0), False)
base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 1), False)

# Pad the base to create the cylinder
pad_base = body.newObject("PartDesign::Pad", "PadBase")
pad_base.Profile = base_sketch
pad_base.Length = params.height
pad_base.Type = "Solid"
pad_base.Reversed = False

# --- Tooth Profile Sketch ---
# We need to create a sketch on the XZ plane (or a plane offset from it) to define the tooth profile.
# The profile will be drawn relative to the centerline (X axis) and the top/bottom of the tooth.
# Coordinate system: X is horizontal (tangent to pitch circle), Z is vertical (height).
# The profile will be symmetric around X=0.

tooth_sketch = body.newObject("Sketcher::SketchObject", "ToothSketch")
tooth_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to XZ plane
tooth_sketch.Support = (doc.getObject("XZ_Plane"), [])
tooth_sketch.MapMode = "FlatFace"

# Calculate tooth geometry
# Pitch Radius
R_pitch = params.pitch_diameter / 2.0
# Tooth Height (half of total height since we draw symmetric profile)
h_tooth = params.height / 2.0
# Pressure Angle
alpha = params.pressure_angle * (3.141592653589793 / 180.0)

# 1. Center Line (X axis)
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(100, 0, 0)), False)
tooth_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 1), False)

# 2. Top of the tooth (Horizontal line at height h_tooth)
# We need a point at the top. Let's define a point P_top at (R_pitch, h_tooth)
# Actually, for a spline, the involute starts at the pitch circle. 
# The tooth height is usually defined from the pitch circle.
# Let's define the profile points:
# A: (0, 0) - Center of tooth
# B: (R_pitch, 0) - Pitch circle intersection
# C: (R_pitch, h_tooth) - Top of tooth at pitch circle radius
# D: (R_pitch + delta, h_tooth) - Top corner (approximated)
# E: (R_pitch + delta, -h_tooth) - Bottom corner
# F: (R_pitch, -h_tooth) - Bottom of tooth at pitch circle radius
# G: (0, 0) - Back to center

# However, a standard spline tooth profile is an involute. 
# The prompt asks for "simplified circular arcs". 
# A common simplification for a straight-sided tooth (like a spur gear) is:
# - Two straight lines from the pitch circle outwards at the pressure angle.
# - A top land (flat top).
# - Fillets at the roots.

# Let's construct the profile using lines and arcs.
# Point 1: Origin (0,0)
# Point 2: (R_pitch, 0)
# Point 3: (R_pitch + h_tooth * tan(alpha), h_tooth) -> This is where the flank meets the top land if we assume a specific addendum.
# But usually, the tooth height is fixed. Let's assume the top land is at y = h_tooth.
# The flank line goes from (R_pitch, 0) with angle (90 - alpha) relative to Z axis? 
# No, pressure angle is measured from the tangent to the pitch circle.
# So the line makes an angle `alpha` with the vertical (Z axis) if we are looking at the profile in XZ plane where X is radial?
# Wait, in XZ plane:
# X is radial direction. Z is axial direction.
# The tangent to the pitch circle is the Z axis.
# The pressure angle is the angle between the line of action and the tangent.
# So the flank line makes an angle `alpha` with the Z axis.
# Slope in XZ plane: dx/dz = tan(alpha).
# So the line equation is x = R_pitch + z * tan(alpha).

# Let's define the vertices:
# V1: (0, 0)
# V2: (R_pitch, 0)
# V3: (R_pitch + h_tooth * tan(alpha), h_tooth)
# V4: (R_pitch + h_tooth * tan(alpha), -h_tooth)
# V5: (R_pitch, -h_tooth)
# V6: (0, 0)

# We will draw lines connecting these points.
# Note: FreeCAD Sketcher uses (x, y) in the sketch plane. Here X is x, Z is y.

# Line 1: V1 to V2
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(R_pitch, 0, 0)), False)
# Line 2: V2 to V3
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(R_pitch, 0, 0), App.Vector(R_pitch + h_tooth * App.cos(alpha), h_tooth, 0)), False)
# Line 3: V3 to V4 (Top Land)
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(R_pitch + h_tooth * App.cos(alpha), h_tooth, 0), App.Vector(R_pitch + h_tooth * App.cos(alpha), -h_tooth, 0)), False)
# Line 4: V4 to V5
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(R_pitch + h_tooth * App.cos(alpha), -h_tooth, 0), App.Vector(R_pitch, -h_tooth, 0)), False)
# Line 5: V5 to V1
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(R_pitch, -h_tooth, 0), App.Vector(0, 0, 0)), False)

# Constraints
# Horizontal lines (Top and Bottom)
tooth_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 1), False) # V2-V3
tooth_sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 1), False) # V3-V4
tooth_sketch.addConstraint(Sketcher.Constraint("Horizontal", 4, 1), False) # V4-V5
tooth_sketch.addConstraint(Sketcher.Constraint("Horizontal", 5, 1), False) # V5-V1 (Wait, V5 to V1 is not horizontal)
# Let's re-verify indices.
# 0: V1 (0,0)
# 1: V2 (R, 0)
# 2: V3 (R+dx, h)
# 3: V4 (R+dx, -h)
# 4: V5 (R, -h)
# 5: V1 (0,0) - Closed loop

# Constraints:
# V1-V2: Horizontal (Z=0)
tooth_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 1), False)
# V2-V3: Angle alpha with Vertical (Z axis). In Sketcher, we can use Angle constraint.
# Angle between V2-V3 and V1-V2 (Horizontal) is 90 - alpha.
tooth_sketch.addConstraint(Sketcher.Constraint("Angle", 1, 2, 0, 1, 90 - alpha), False)
# V3-V4: Horizontal
tooth_sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 3), False)
# V4-V5: Angle alpha with Vertical (symmetric)
tooth_sketch.addConstraint(Sketcher.Constraint("Angle", 3, 4, 4, 5, 90 - alpha), False)
# V5-V1: Horizontal? No, V5 is (R, -h), V1 is (0,0). This is a straight line back to origin.
# Wait, the profile I described is not a standard gear tooth. A standard gear tooth has a root circle.
# The prompt says "simplified circular arcs".
# Let's stick to the straight sides and a flat top, but ensure the root is closed properly.
# The line V5-V1 connects (R, -h) to (0,0). This is a straight line.
# Is this correct? 
# Usually, the tooth width at the root is smaller than at the pitch circle.
# But for a "spline" with "straight teeth", this trapezoidal-ish shape is acceptable if we assume the root is at the center.
# However, the prompt mentions "fillet root tooth". This implies the root is rounded.
# My current profile has a sharp corner at V1 (0,0) if we just connect lines.
# Actually, V1 is the center of the spline. The tooth starts there.
# The "root" of the tooth is the bottom part.
# Let's refine the profile to be more realistic:
# 1. Center line (X axis).
# 2. Pitch circle intersection.
# 3. Flank lines going out.
# 4. Top land.
# 5. Return along the other flank.
# 6. Root fillet.

# Let's redefine the sketch geometry to be cleaner:
# We will draw the profile from the centerline up to the top, then mirror it.
# But Sketcher doesn't have a direct "mirror" feature in the sketcher constraints easily without duplicating geometry.
# Let's just draw the full symmetric profile.

# Points:
# P0: (0, 0)
# P1: (R_pitch, 0)
# P2: (R_pitch + h_tooth * tan(alpha), h_tooth)
# P3: (R_pitch + h_tooth * tan(alpha), -h_tooth)
# P4: (R_pitch, -h_tooth)
# P5: (0, 0)

# Lines:
# L0: P0-P1
# L1: P1-P2
# L2: P2-P3
# L3: P3-P4
# L4: P4-P5

# Constraints:
# L0: Horizontal
# L1: Angle (90-alpha) with L0
# L2: Horizontal
# L3: Angle (90-alpha) with L4? No, L3 and L4 meet at P4.
# L3: Angle (90-alpha) with L4 (which is P4-P5).
# L4: Horizontal? No, P4 is (R, -h), P5 is (0,0). Slope is h/R.
# This shape is a bit weird. The root is a point.
# Let's assume the "root" is the bottom of the tooth, and we apply a fillet there.
# The fillet will be applied to the edges meeting at the bottom.
# But if the bottom is a point (P5), we can't fillet a point.
# We need a small root radius or a flat root.
# Let's assume the tooth has a small flat root at the bottom, or the fillet connects the flanks directly to the center?
# "Fillet root tooth" usually means the bottom of the tooth is rounded.
# Let's modify the profile to have a small flat bottom or just let the fillet handle the corner at P5 if we treat P5 as a vertex.
# Actually, if we connect P4 to P5 and P5 to P0, the angle at P5 is determined by the lines.
# Let's just use the lines as defined and apply a fillet to the edges meeting at the bottom.
# Wait, if P5 is (0,0), the edges are P4-P5 and P5-P0.
# The fillet will round the corner at P5.
# This creates a rounded root. This matches the requirement.

# Re-evaluating constraints for P4-P5 and P5-P0:
# P4=(R, -h), P5=(0,0). Vector P4->P5 is (-R, h).
# P5=(0,0), P0=(0,0)? No, P0 is (0,0). P5 is (0,0).
# Ah, P0 and P5 are the same point.
# So the loop is P0->P1->P2->P3->P4->P0.
# Edges:
# 0: P0-P1 (Horizontal)
# 1: P1-P2 (Flank)
# 2: P2-P3 (Top)
# 3: P3-P4 (Flank)
# 4: P4-P0 (Root)

# Constraints:
# 0: Horizontal
# 1: Angle (90-alpha) with 0
# 2: Horizontal
# 3: Angle (90-alpha) with 4? 
#    Vector P3->P4 is (0, -2h). Vertical.
#    Vector P4->P0 is (-R, h).
#    Angle between Vertical and P4->P0?
#    Let's just constrain the angle of the flank relative to the top land.
#    Top land is horizontal. Flank P3-P4 should be at angle alpha to vertical.
#    So angle between P2-P3 (Horizontal) and P3-P4 is 90+alpha? No.
#    P2-P3 is horizontal. P3-P4 goes down.
#    Angle between Horizontal and P3-P4 is 90 + alpha (if alpha is from vertical).
#    Or simply: Angle between P3-P4 and P2-P3 is 90 + alpha.
#    Wait, P2-P3 is horizontal. P3-P4 is at angle alpha from vertical.
#    So the angle between them is 90 + alpha.
#    Similarly for P4-P0.
#    P4-P0 connects (R, -h) to (0,0).
#    We want the flank P3-P4 and P4-P0 to be symmetric?
#    If the tooth is symmetric, P4-P0 should be the mirror of P1-P2.
#    P1-P2 goes from (R,0) to (R+dx, h).
#    P4-P0 goes from (R, -h) to (0,0).
#    These are not symmetric in position, but symmetric in shape relative to the centerline?
#    No, the centerline is X-axis.
#    P1-P2 is above. P4-P0 is below.
#    P1-P2: starts at (R,0), goes up-right.
#    P4-P0: starts at (R, -h), goes up-left to (0,0).
#    This is not symmetric.
#    Let's rethink the geometry.
#    Standard gear tooth:
#    - Pitch circle at R.
#    - Flanks are involutes.
#    - Top land is flat.
#    - Root is flat or rounded.
#    - Symmetric about the centerline of the tooth.
#    The centerline of the tooth is the radial line from the origin.
#    In our XZ sketch, the radial line is the X-axis.
#    So the tooth should be symmetric about the X-axis.
#    My previous points:
#    P0 (0,0) - Center of spline.
#    P1 (R, 0) - Pitch circle.
#    P2 (R+dx, h) - Top right.
#    P3 (R+dx, -h) - Bottom right.
#    P4 (R, -h) - Bottom pitch circle.
#    P5 (0,0) - Center.
#    This shape is NOT symmetric about X-axis.
#    P1
