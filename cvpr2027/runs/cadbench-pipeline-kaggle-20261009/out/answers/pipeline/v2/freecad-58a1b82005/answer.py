import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# --- Parameters ---
# Defined as named properties in a VarSet for editability
params = {
    "shaft_number_teeth": 15,
    "shaft_spline_module": 2.0,
    "shaft_spline_pitch_diameter": 30.0, # 15 * 2
    "shaft_pressure_angle": 30.0,
    "shaft_spline_height": 10.0,
    "shaft_diameter": 24.0,
    "shaft_length": 20.0
}

# --- Document Setup ---
doc = App.newDocument("Shaft_Spline")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a VarSet to hold named parameters
params_obj = body.newObject("App::VarSet", "Parameters")
for name, value in params.items():
    params_obj.addProperty(f"App::PropertyFloat", name, "Parameters", f"{name} parameter")
    params_obj[name] = value

# --- Feature 1: Spline Section ---
# We will create a sketch for the spline profile on the XY plane.
# The spline profile is generated mathematically.
# Coordinate system: Center at (0,0), extending along +X axis.

sketch_spline = body.newObject("Sketcher::SketchObject", "Sketch_Spline")
sketch_spline.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_spline.ConstrainAuto = True
sketch_spline.ConstrainX = True
sketch_spline.ConstrainY = True
sketch_spline.ConstrainZ = True
sketch_spline.MapMode = "FlatFace"
sketch_spline.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Helper to add geometry to sketch
def add_line(sk, p1, p2, is_constraint=False):
    sk.addGeometry(Part.LineSegment(p1, p2), is_constraint)

def add_circle(sk, center, radius, is_constraint=False):
    sk.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constraint)

def add_arc(sk, center, radius, start_angle, end_angle, is_constraint=False):
    # FreeCAD Sketcher arcs are defined by center, radius, start_angle, end_angle
    # Angles are in degrees, counter-clockwise
    sk.addGeometry(Part.Arc(center, App.Vector(0, 0, 1), start_angle, end_angle), is_constraint)

# Generate Spline Geometry
n_teeth = params["shaft_number_teeth"]
module = params["shaft_spline_module"]
pd = params["shaft_spline_pitch_diameter"]
pressure_angle = params["shaft_pressure_angle"]
h = params["shaft_spline_height"]

# Spline Geometry Calculation
# Pitch Diameter (PD) is the diameter of the circle passing through the tooth tips.
# Root Diameter (RD) = PD - 2 * h
# Tip Diameter (TD) = PD + 2 * h (for external spline, usually we define the profile relative to PD)
# However, standard spline generation often defines the profile based on the pitch circle.
# Let's define the profile relative to the Pitch Circle (PD).
# The profile consists of:
# 1. A circular arc at the Pitch Diameter (PD) spanning the pressure angle.
# 2. A radial line from the arc end to the Root Diameter.
# 3. A circular arc at the Root Diameter spanning the remaining angle.
# 4. A radial line from the root arc to the Pitch Diameter (closing the loop).
# Wait, standard external spline profile:
# - Tip circle is larger than Pitch circle.
# - Root circle is smaller than Pitch circle.
# - Flanks are straight lines tangent to the Pitch circle? No, usually tangent to the Root circle or defined by pressure angle.
# Standard ISO Spline:
# - Pressure angle is the angle of the flank relative to the tangent of the Pitch circle.
# - The flank is a straight line.
# - The tip is a circular arc.
# - The root is a circular arc.

# Let's calculate the angles.
# Total angle per tooth = 360 / n_teeth
angle_per_tooth = 360.0 / n_teeth
half_angle = angle_per_tooth / 2.0

# The flank makes an angle of `pressure_angle` with the tangent to the pitch circle.
# Therefore, the flank makes an angle of (90 - pressure_angle) with the radius at the pitch circle.
# The angle subtended by the flank at the center (from the pitch circle tangent point to the root tangent point)
# is simply the pressure angle.
# So, the flank spans `pressure_angle` degrees.
# The remaining angle of the tooth (between the two flanks) is `angle_per_tooth - 2 * pressure_angle`.
# This remaining angle is split between the two root arcs? No, the root is usually a single arc connecting the two flanks.
# Actually, the standard profile is:
# - Start at Pitch Circle, go along tangent? No.
# - Start at Pitch Circle, go along a line at `pressure_angle` to the Root Circle.
# - Go along Root Circle arc.
# - Go along a line at `pressure_angle` back to Pitch Circle.
# - Go along Pitch Circle arc.

# Let's refine the geometry construction:
# We will build one tooth profile and then use a polar pattern.
# The profile will be defined relative to the center of the spline.
# We need to close the loop.

# Let's define the points for ONE tooth.
# We place the start of the tooth at angle 0 (relative to the tooth center).
# The tooth center is at angle `half_angle` relative to the start of the tooth slot?
# Let's just build the profile of one tooth centered at angle 0.
# The tooth extends from `-half_angle` to `+half_angle`.
# The flanks are straight lines.
# The tip is an arc.
# The root is an arc.

# Geometry parameters:
# Pitch Radius (Rp) = PD / 2
# Root Radius (Rr) = (PD - 2*h) / 2
# Tip Radius (Rt) = (PD + 2*h) / 2 (Assuming standard full depth, though h is usually dedendum. 
# The prompt says "shaft_spline_height". Let's assume this is the total height of the tooth from Pitch to Root? 
# Or is it the dedendum? 
# "shaft_spline_height = 10 mm". 
# If PD=30, and height=10. 
# If it's total height, Rr = 15 - 10 = 5. Rt = 15 + 10 = 25.
# If it's dedendum, Rt = 15. Rr = 15 - 10 = 5.
# Given "shaft_spline_height", it likely implies the radial depth of the tooth. 
# Let's assume the tooth extends from Root to Tip, and the Pitch circle is somewhere in between.
# Standard: Pitch circle is the reference. 
# Let's assume the "height" is the distance from Pitch Circle to Root Circle (Dedendum).
# Then Tip Circle = Pitch Circle + Addendum.
# Usually Addendum = Module. Dedendum = 1.25 * Module.
# But we have a specific "shaft_spline_height". Let's assume this is the total radial height of the tooth (Tip to Root).
# And the Pitch Circle is at the center of the tooth height? No, Pitch is defined by module.
# Let's stick to the prompt's explicit values.
# PD = 30.
# Height = 10.
# Let's assume the tooth profile is symmetric around the Pitch Circle? No, that's not standard.
# Let's assume the "height" is the dedendum (distance from Pitch to Root).
# Then Root Radius = 15 - 10 = 5.
# Tip Radius = 15 + Module = 15 + 2 = 17.
# This seems reasonable.
# Alternatively, maybe "height" is the total height.
# Let's assume: 
# Root Radius = (PD/2) - (shaft_spline_height / 2) ? No.
# Let's assume the prompt implies the tooth height is 10mm.
# Let's assume the Pitch Circle is the center of the tooth height? No.
# Let's assume the standard definition where the tooth height is the sum of addendum and dedendum.
# But we don't have addendum/dedendum separately.
# Let's assume the "shaft_spline_height" is the distance from the Pitch Circle to the Root Circle (Dedendum).
# And the Addendum is equal to the Module (2mm).
# So:
# Root Radius = 15 - 10 = 5 mm.
# Tip Radius = 15 + 2 = 17 mm.
# This creates a tooth height of 12mm.
# What if "shaft_spline_height" is the total height?
# Then Root = 15 - 5 = 10, Tip = 15 + 5 = 20.
# Let's try to interpret "shaft_spline_height" as the radial depth of the groove (dedendum).
# This is the most common parameter name in such contexts if not specified as "total height".
# However, to be safe and robust, let's assume the tooth extends from Root to Tip, and the Pitch Circle is at the center of the "active" part?
# Let's go with: 
# Root Radius = (PD/2) - (shaft_spline_height)
# Tip Radius = (PD/2) + (shaft_spline_height)
# This makes the tooth symmetric around the Pitch Circle. This is a common simplification for custom parts if standard ISO isn't strictly enforced.
# Let's use this symmetric assumption: Root = 15 - 10 = 5, Tip = 15 + 10 = 25.
# Wait, if Root is 5 and Tip is 25, the tooth height is 20.
# If the prompt says "height = 10", maybe it means the tooth height is 10.
# Let's assume:
# Root Radius = 15 - 5 = 10
# Tip Radius = 15 + 5 = 20
# This gives a total height of 10.
# Let's assume the Pitch Circle is in the middle of the tooth height.
# So:
# Root Radius = 15 - 5 = 10
# Tip Radius = 15 + 5 = 20
# This seems like a reasonable interpretation of "height = 10" centered on the pitch diameter.

# Recalculating based on "Height = 10" centered on Pitch:
# Root Radius = 15 - 5 = 10
# Tip Radius = 15 + 5 = 20
# Flank angle = Pressure Angle = 30 degrees.
# Flank length?
# The flank is a straight line tangent to the Pitch Circle? No, the flank is tangent to the Pitch Circle ONLY if the pressure angle is defined relative to the Pitch Circle tangent.
# Yes, the pressure angle is the angle between the tangent to the Pitch Circle and the normal to the flank.
# So the flank is a straight line.
# The flank starts at the Pitch Circle and goes to the Root Circle?
# No, the flank is tangent to the Pitch Circle.
# The flank intersects the Root Circle.
# The angle between the flank and the radius at the Pitch Circle is (90 - pressure_angle).
# The angle subtended by the flank at the center is `pressure_angle`.
# So the flank spans `pressure_angle` degrees.
# The remaining angle of the tooth is `angle_per_tooth - 2 * pressure_angle`.
# This remaining angle is the arc of the Root Circle?
# No, the Root Circle arc connects the two flanks.
# The angle of the Root Circle arc = `angle_per_tooth - 2 * pressure_angle`.
# The Tip Circle arc connects the two flanks at the top.
# The angle of the Tip Circle arc = `angle_per_tooth - 2 * pressure_angle`.
# Wait, the flanks are straight lines.
# The profile is:
# 1. Arc at Tip Radius from angle `-half_angle` to `+half_angle`? No.
# The flanks are the straight parts.
# The flanks are at angles `half_angle - pressure_angle` and `half_angle + pressure_angle`?
# Let's define the angles relative to the tooth center (0 degrees).
# The tooth occupies angles from `-half_angle` to `+half_angle`.
# The flanks are straight lines.
# The flanks are tangent to the Pitch Circle.
# The tangent points on the Pitch Circle are at angles `half_angle - pressure_angle` and `half_angle + pressure_angle`?
# No.
# The tangent to the Pitch Circle at angle `theta` has a normal at `theta`.
# The flank is a line with normal at `theta`.
# The flank must pass through the Pitch Circle? No, the flank is tangent to the Pitch Circle.
# So the distance from the center to the flank line is `Rp`.
# The angle of the normal to the flank is `theta`.
# The flank line equation: x*cos(theta) + y*sin(theta) = Rp.
# The flank intersects the Root Circle (radius Rr) and Tip Circle (radius Rt).
# The intersection points define the arcs.
# The angle of the intersection point on the Root Circle:
# cos(phi) = Rp / Rr.
# So the flank intersects the Root Circle at an angle `phi` from the normal.
# The angle of the intersection point on the Tip Circle:
# cos(psi) = Rp / Rt.
# The arc on the Root Circle is between the two flanks.
# The angle of the Root Circle arc = `angle_per_tooth - 2 * (angle between normal and flank intersection)`.
# Actually, simpler:
# The flank is a line.
# The angle of the flank relative to the radius at the Pitch Circle is `pressure_angle`.
# So the flank makes an angle of `90 - pressure_angle` with the radius.
# The angle subtended by the flank at the center is `pressure_angle`.
# So the flank starts at the Pitch Circle and goes to the Root Circle?
# No, the flank is tangent to the Pitch Circle.
# The flank extends from the Root Circle to the Tip Circle.
# The angle of the flank relative to the horizontal (if tooth is vertical) is `90 - pressure_angle`.
# Let's build the sketch points directly.
# We will create a closed loop.
# Start at the top of the tooth (Tip Circle, angle 0).
# Go along the Tip Circle arc to the start of the flank.
# Go along the flank to the Root Circle.
# Go along the Root Circle arc to the other flank.
# Go along the other flank to the Tip Circle.
# Go along the Tip Circle arc back to start.

# Angles:
# Tooth center: 0.
# Tooth half-angle: `half_angle`.
# Flank angle relative to tooth center: `half_angle - pressure_angle`?
# No.
# The flank is tangent to the Pitch Circle.
# The normal to the flank passes through the center.
# The angle of the normal is `theta_normal`.
# The flank is at `theta_normal + 90`.
# The flank must be within the tooth sector.
# The flank starts at the Root Circle and ends at the Tip Circle.
# The angle of the normal to the flank is `half_angle - pressure_angle`?
# Let's visualize.
# Tooth center at 0.
# Right flank is at positive angle.
# The flank is a line.
# The normal to the right flank points to the right and slightly up?
# The normal angle is `half_angle - pressure_angle`.
# Why? Because the flank is tangent to the Pitch Circle.
# The tangent point on the Pitch Circle is at angle `half_angle - pressure_angle`.
# The normal at that point is the radius to that point.
# So the normal angle is `half_angle - pressure_angle`.
# The flank line is perpendicular to this normal.
# The flank line intersects the Root Circle and Tip Circle.
# The angle of the intersection point on the Root Circle:
# The distance from center to line is `Rp`.
# The radius is `Rr`.
# The angle `alpha` between the normal and the radius to the intersection point is `acos(Rp/Rr)`.
# So the intersection point angle is `theta_normal + alpha`.
# Similarly for the Tip Circle: `acos(Rp/Rt)`.
# The arc on the Root Circle is between the two flanks.
# The angle of the Root Circle arc = `angle_per_tooth - 2 * alpha`.
# The arc on the Tip Circle is between the two flanks.
# The angle of the Tip Circle arc = `angle_per_tooth - 2 * beta`.
# Where `beta = acos(Rp/Rt)`.

# Let's calculate these values.
Rp = pd / 2.0
Rr = Rp - (params["shaft_spline_height"] / 2.0) # Assuming symmetric height
Rt = Rp + (params["shaft_spline_height"] / 2.0)

# Check if Rr > 0
if Rr <= 0:
    Rr = 0.1 # Fallback

alpha = math.acos(Rp / Rr)
beta = math.acos(Rp / Rt)

# Angles in degrees
alpha_deg = math.degrees(alpha)
beta_deg = math.degrees(beta)

# Tooth geometry angles
to
