import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure the output is saved next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# --- Part Parameters ---
# Basic Gear Dimensions
P_MODULE = 1.0          # mm
P_PRESSURE_ANGLE = 20.0 # degrees
P_NUM_TEETH = 45        # count

# Calculated Gear Dimensions (ISO 21771 style)
P_PITCH_DIAMETER = P_MODULE * P_NUM_TEETH          # 45.0
P_OUTER_DIAMETER = P_PITCH_DIAMETER + 2 * P_MODULE # 47.0
P_ROOT_DIAMETER = P_PITCH_DIAMETER - 2.5 * P_MODULE # 42.5
P_BASE_DIAMETER = P_PITCH_DIAMETER * math.cos(math.radians(P_PRESSURE_ANGLE)) # ~42.286
P_CIRCULAR_PITCH = math.pi * P_MODULE              # ~3.14159
P_TOOTH_THICKNESS = P_CIRCULAR_PITCH / 2           # ~1.5708
P_ADDENDUM = P_MODULE                              # 1.0
P_DEDEDUMEN = 1.25 * P_MODULE                      # 1.25
P_WHOLE_DEPTH = P_ADDENDUM + P_DEDEDUMEN           # 2.25

# Face Dimensions
P_FACE_WIDTH = 6.0
P_HUB_DIAMETER = 16.0
P_HUB_WIDTH = 6.0
P_SHAFT_DIAMETER = 8.0
P_OVERALL_WIDTH = 12.0

# --- Document Creation ---
doc = App.newDocument("SpurGear")
doc.Label = "SpurGear"

# 1. Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))
body.Proxy = None # Ensure no baked shape

# 2. Create Named Parameters (VarSet)
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "P_MODULE", "Dimensions", "Gear Module")
params.P_MODULE = P_MODULE
params.addProperty("App::PropertyLength", "P_FACE_WIDTH", "Dimensions", "Face Width")
params.P_FACE_WIDTH = P_FACE_WIDTH
params.addProperty("App::PropertyLength", "P_OVERALL_WIDTH", "Dimensions", "Overall Width")
params.P_OVERALL_WIDTH = P_OVERALL_WIDTH
params.addProperty("App::PropertyLength", "P_SHAFT_DIAMETER", "Dimensions", "Shaft Diameter")
params.P_SHAFT_DIAMETER = P_SHAFT_DIAMETER
params.addProperty("App::PropertyLength", "P_HUB_DIAMETER", "Dimensions", "Hub Diameter")
params.P_HUB_DIAMETER = P_HUB_DIAMETER
params.addProperty("App::PropertyLength", "P_HUB_WIDTH", "Dimensions", "Hub Width")
params.P_HUB_WIDTH = P_HUB_WIDTH

params.addProperty("App::PropertyAngle", "P_PRESSURE_ANGLE", "Dimensions", "Pressure Angle")
params.P_PRESSURE_ANGLE = P_PRESSURE_ANGLE
params.addProperty("App::PropertyInteger", "P_NUM_TEETH", "Dimensions", "Number of Teeth")
params.P_NUM_TEETH = P_NUM_TEETH

# --- Feature Construction ---

# Reference Planes: XY_Plane, XZ_Plane, YZ_Plane are automatically available in FreeCAD document
# We will attach sketches to the XY plane (Z=0) and extrude along Z.

# 1. Base Geometry Sketch (Hub + Shaft Hole + Outer Limit)
# This sketch defines the central hole, the hub outer cylinder, and the gear outer diameter limit.
sketch_base = body.newObject("Sketcher::SketchObject", "BaseGeometry")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = [doc.getObject("XY_Plane")]
sketch_base.ConstrainToPlane = "XY_Plane"
sketch_base.Locked = True # Prevent accidental modification of constraints

# Lines
# Center line
sketch_base.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(100, 0, 0)))
# Hub outer diameter circle
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.P_HUB_DIAMETER / 2))
# Gear outer diameter circle
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.P_OUTER_DIAMETER / 2))
# Shaft hole diameter circle
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.P_SHAFT_DIAMETER / 2))

# Constraints
# Coincident center of Hub, Shaft, and Gear OD
sketch_base.addConstraint(Sketcher.Constraint("Point", 0, 1, 0, 0)) # Hub center on origin
sketch_base.addConstraint(Sketcher.Constraint("Point", 0, 2, 0, 0)) # Shaft center on origin
sketch_base.addConstraint(Sketcher.Constraint("Point", 0, 3, 0, 0)) # Gear OD center on origin
sketch_base.addConstraint(Sketcher.Constraint("Horizontal", 0, 0)) # Centerline horizontal
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 0, 0), 0, 0, 1, 0) # Hub on centerline
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 0, 0), 0, 0, 1, 0) # Shaft on centerline
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 3, 0, 0), 0, 0, 1, 0) # Gear OD on centerline

# Tangent constraint: Shaft hole tangent to Hub? No, Hub is larger.
# Tangent constraint: Shaft hole tangent to Gear? No, Gear is larger.
# We need the Shaft hole to be concentric with the Hub.
# We need the Gear OD to be concentric with the Hub.
# The Hub and Gear OD are already concentric with the center point.
# We need to ensure the Hub circle is tangent to the Gear circle? No, there is a fillet usually, but here we pad the gear first then pocket the hub?
# Actually, standard practice: Pad the Gear OD (with teeth), then Pocket the Hub (and Shaft).
# Let's define the "Gear Blank" sketch first.

# 2. Gear Tooth Sketch
# This sketch defines the profile of a single tooth on the pitch circle.
# We will use a Polar Pattern to create all teeth.
sketch_teeth = body.newObject("Sketcher::SketchObject", "GearToothProfile")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_teeth.Support = [doc.getObject("XY_Plane")]
sketch_teeth.ConstrainToPlane = "XY_Plane"
sketch_teeth.Locked = True

# Parameters for the sketch
# Pitch Radius
R_PITCH = P_PITCH_DIAMETER / 2
# Base Radius
R_BASE = P_BASE_DIAMETER / 2
# Addendum Radius (Pitch + Addendum)
R_OUTER = R_PITCH + P_ADDENDUM
# Dedendum Radius (Pitch - Dedendum)
R_ROOT = R_PITCH - P_DEDEDUMEN

# Center of the tooth sketch (placed at pitch circle radius)
# We need to calculate the start angle of the tooth.
# Tooth thickness at pitch circle = circular_pitch / 2
# Circular Pitch = pi * module
# Angle subtended by half tooth = (Circular Pitch / 2) / Pitch Radius
# Total angle per tooth = 360 / NumTeeth
# We place the tooth such that the centerline of the tooth is at angle 0 relative to the sketch origin, 
# but the sketch origin will be the center of the gear.
# So we place the sketch origin at the gear center, and draw the tooth profile relative to that.
# Actually, it's easier to place the sketch origin at the gear center, and draw the tooth profile from angle 0 to 180? 
# No, we need a closed profile for the tooth itself.
# Let's place the sketch origin at the gear center.
# The tooth will be drawn symmetrically around the X-axis (angle 0).
# The tooth starts at angle -half_tooth_angle and ends at +half_tooth_angle.
# Wait, the tooth profile is not a straight line. It's involute.
# However, for FreeCAD PartDesign, we can approximate or use exact involute.
# Exact Involute generation in FreeCAD sketch is complex.
# Alternative: Use the "Involute" constraint or generate points.
# Given the constraint of "editable features", we can create a curve by connecting points.
# Points on the involute:
# Involute angle phi (unwrapped angle) relates to radius r = R_base / cos(phi).
# Tangent angle psi = phi + alpha (pressure angle).
# Coordinates:
# x = R_base/sin(phi) * (cos(phi) + cos(alpha))
# y = R_base/sin(phi) * (sin(phi) - sin(alpha)) ... wait, standard formulas.
# Let's use a simpler approach: Define the key points of the tooth profile and connect them with lines/arcs.
# Standard Tooth Profile Points:
# 1. Base Circle (start of involute)
# 2. Addendum Circle (end of involute)
# 3. Top Land (Arc)
# 4. Dedendum Circle (start of dedendum line)
# 5. Root (Arc)

# Let's calculate the angles for the tooth boundaries.
# Angle between teeth = 360 / N
# Half angle = Angle / 2
# The tooth is symmetric.
# The pitch line is at the center of the tooth.
# The involute starts at R_base.
# The involute ends at R_outer.
# The angle of the involute at R_outer (phi_add) = acos(R_base / R_outer).
# The angular position of the tooth boundary at the pitch circle is +/- (Circular Pitch / 2) / R_pitch.
# Let's define the tooth profile as a closed loop.
# We will place the sketch origin at the gear center.
# We will draw the profile for ONE tooth, centered at angle 0?
# No, we will place the sketch origin at the gear center, and draw the profile for one tooth starting from the center line of the tooth?
# No, the polar pattern needs a closed shape.
# Let's define the profile of ONE tooth relative to the gear center.
# The tooth is centered at angle 0.
# The tooth spans from angle -Theta/2 to +Theta/2.
# But the profile is not a straight line.
# Let's calculate the coordinates of the vertices.
# Vertex 1: Root circle, start of involute side A.
# Vertex 2: Addendum circle, end of involute side A.
# Vertex 3: Top land center.
# Vertex 4: Addendum circle, end of involute side B.
# Vertex 5: Root circle, start of involute side B.

# Actually, the most robust way in FreeCAD for a single sketch is to define the points.
# Let's calculate the points for one half-tooth (symmetric).
# Tooth thickness at pitch circle = C / 2.
# Angle of tooth sector = C / (2 * PI * R_pitch) = (PI * m / 2) / (PI * m * N) = 1 / (2N).
# Wait, C = PI * m. Pitch Circle C = PI * m * N.
# Angle per tooth = 2 * PI / N.
# Half angle = PI / N.
# The tooth is centered at angle 0.
# The tooth boundaries at the pitch circle are at +/- PI/N.
# The involute starts at R_base.
# The angle of the involute at R_outer is phi_max = acos(R_base / R_outer).
# The actual angle of the tooth boundary at the outer circle is:
# theta_outer = (PI/N) + (phi_max - atan(R_base / R_outer * tan(PressureAngle))) ? No.
# Let's use the standard method:
# 1. Calculate the angle of the tooth sector: alpha_sector = 360 / N.
# 2. The tooth is symmetric about 0.
# 3. The involute starts at R_base.
# 4. The involute ends at R_outer.
# 5. The top land is an arc of radius R_outer.
# 6. The root is an arc of radius R_root.
# 7. The dedendum is a radial line (or slightly angled).

# Let's calculate the specific angles for the vertices.
# The tooth profile is defined by:
# - Involute from R_base to R_outer (Side A)
# - Arc from R_outer to R_outer (Top Land)
# - Involute from R_outer to R_base (Side B)
# - Arc from R_base to R_base (Root Land)
# - Radial lines connecting? No, usually filleted or sharp. Standard gear has sharp corners at the root if not specified.
# But for a "solid" gear, we usually just define the envelope.
# Let's define the profile as:
# 1. Start at Root Circle, angle = - (Half Tooth Angle + Involute Offset)
# This is getting complicated to get exactly right without a library.
# Simplified approach: 
# Define the "Gear Tooth" sketch as a closed shape.
# We will construct the shape by:
# - A circle at R_outer (Top)
# - A circle at R_root (Bottom)
# - Two involute curves connecting them.
# Since FreeCAD Sketcher doesn't have a direct "Involute" curve command in the basic list (it exists in some versions as a constraint or macro), 
# we will approximate the involute using a series of points or use the "Curves" module if available.
# However, the prompt asks for a script. The most reliable way in vanilla FreeCAD 1.1 is to use the "Involute" geometry if available or construct points.
# Let's assume we can use `Part.Curve` or similar? No, Sketcher needs specific primitives.
# Let's use the `Part` module to generate the curve and add it to the sketch? No, Sketcher::SketchObject only accepts specific geometries.
# Wait, FreeCAD 1.1 has `Sketcher::Constraint` for "Involute" in some contexts, but for a script, generating points is safest.
# Let's generate points for the involute.
# Formula for Involute:
# r = r_base / cos(phi)
# theta = phi + acos(r_base/r)  <-- This is the angle in the fixed frame? No.
# Parametric:
# phi is the angle of the generating tangent.
# x = r_base * (phi * cos(phi) + sin(phi))
# y = r_base * (sin(phi) - phi * cos(phi))
# This is for a circle at origin.
# The angle of the point on the circle is theta = phi + acos(r_base/r).
# Let's calculate the phi for the start (r=r_base, phi=0) and end (r=r_outer).
# phi_end = acos(r_base / r_outer).
# We need to shift this by the tooth angle.

# Let's define the points for one tooth profile (symmetric around 0).
# We need the angle of the tooth boundary at the pitch circle.
# Angle_tooth_half = PI / N.
# The involute starts at R_base.
# The angle of the involute at R_outer relative to the base circle start is phi_max.
# The angle of the tooth boundary at the outer circle is:
# theta_boundary_outer = Angle_tooth_half - (phi_max - alpha_pressure) ?
# Actually, let's just calculate the points along the profile.
# We will define the profile as a closed loop of points.
# Points:
# P1: Root circle, start of involute (Side A).
# P2: Addendum circle, end of involute (Side A).
# P3: Addendum circle, end of involute (Side B).
# P4: Root circle, start of involute (Side B).
# And connect P1-P4 with an arc (root).
# Connect P2-P3 with an arc (top).
# Connect P1-P2 with involute.
# Connect P4-P3 with involute.

# Calculation:
# Tooth thickness at pitch circle = C / 2.
# Angle of tooth sector = 2 * PI / N.
# The tooth is centered at 0.
# The involute starts at R_base.
# The angle of the involute at R_outer is phi_max = acos(R_base / R_outer).
# The angle of the tooth boundary at the pitch circle is PI / N.
# The angle of the tooth boundary at the root circle is:
# theta_root = PI / N - (phi_max - alpha_pressure) ?? 
# Actually, the relationship is:
# theta = PI/N - (phi_max - alpha_pressure) ?
# Let's use the standard formula for the angle of the tooth space.
# The angle of the tooth profile at the root circle is:
# theta_root = PI / N - (phi_max - alpha_pressure)
# Wait, let's just calculate the points directly.
# We need the angle of the point on the involute at radius R.
# theta = phi + acos(R_base/R).
# We know the angle of the tooth boundary at the pitch circle is PI/N.
# At R_pitch, phi_pitch = acos(R_base/R_pitch)
