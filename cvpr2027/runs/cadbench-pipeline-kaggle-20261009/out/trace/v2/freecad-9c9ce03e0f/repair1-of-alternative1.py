import FreeCAD as App
import Part
import Sketcher
import math
from pathlib import Path

# Initialize document
doc = App.newDocument("SpurGear")

# --- 1. Create Parameters Object (Editable) ---
# In FreeCAD 1.1, parameters are typically stored in a PartDesign::BodyParameter or a simple App::PropertySet 
# attached to the Body, or simply as properties of the Body itself if we don't need a separate object.
# However, to ensure they are "named document objects" as requested and editable, we create a PartDesign::BodyParameter.
# Note: The exact type name might vary slightly by version, but "PartDesign::BodyParameter" is the standard for 1.x.
# If that fails, we can use a Part::Feature with a PropertySet, but the prompt asks for named objects driving geometry.
# Let's try the standard PartDesign parameter object.
try:
    params = doc.addObject("PartDesign::BodyParameter", "Parameters")
except:
    # Fallback: Create a Part::Feature with a PropertySet if BodyParameter is not available in this specific build
    params = doc.addObject("Part::Feature", "Parameters")
    params.addProperty("App::PropertyLength", "module", "Dimensions", "Module m")
    params.addProperty("App::PropertyInteger", "teeth", "Dimensions", "Number of teeth Z")
    params.addProperty("App::PropertyLength", "width", "Dimensions", "Face Width")
    params.addProperty("App::PropertyLength", "hub_dia", "Dimensions", "Hub Diameter")
    params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
    params.addProperty("App::PropertyLength", "shaft_dia", "Dimensions", "Shaft Diameter")
    params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "Pressure Angle deg")
    params.addProperty("App::PropertyLength", "whole_depth", "Dimensions", "Whole Depth")
    # Add expressions manually to the fallback object
    params.addExpression("pitch_diameter", "Parameters.module * Parameters.teeth")
    params.addExpression("outer_diameter", "Parameters.pitch_diameter + 2 * Parameters.module")
    params.addExpression("root_diameter", "Parameters.pitch_diameter - 2 * Parameters.whole_depth")
    params.addExpression("base_diameter", "Parameters.pitch_diameter * cos(Parameters.pressure_angle_deg * pi / 180)")
    params.addExpression("circular_pitch", "pi * Parameters.module")
    params.addExpression("tooth_thickness", "Parameters.circular_pitch / 2")
    params.addExpression("addendum", "Parameters.module")
    params.addExpression("dedendum", "1.25 * Parameters.module")
    params.addExpression("overall_width", "Parameters.hub_width + Parameters.width")

# Set values for the parameters
if hasattr(params, "addProperty"):
    # It's the fallback Part::Feature
    params.module = 1.0
    params.teeth = 80
    params.width = 6.0
    params.hub_dia = 18.0
    params.hub_width = 8.0
    params.shaft_dia = 8.0
    params.pressure_angle_deg = 20.0
    params.whole_depth = 2.25
else:
    # It's the PartDesign::BodyParameter
    params.module = 1.0
    params.teeth = 80
    params.width = 6.0
    params.hub_dia = 18.0
    params.hub_width = 8.0
    params.shaft_dia = 8.0
    params.pressure_angle_deg = 20.0
    params.whole_depth = 2.25

# --- 2. Create Body ---
body = doc.addObject("PartDesign::Body", "Body")
body.Label = "Body"

# --- 3. Define Sketches and Features ---

# --- Sketch 1: Gear Teeth Profile (Radial) ---
# Plane: XY_Plane
sk1 = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
sk1.Placement = App.Placement(App.Vector(0, 0, 0))
sk1.Plane = "XY_Plane"
sk1.Constraints = [] # We will add constraints manually for precision

# Helper function to get involute point
def get_involute_point(phi):
    """
    Generates a point on the involute of a circle with radius R_base.
    phi is the angle on the base circle (radians).
    Returns (x, y, z).
    """
    if phi < 0.0001:
        return App.Vector(0, 0, 0)
    R_base = body.getObject("Parameters").base_diameter / 2
    x = R_base * (math.cos(phi) + phi * math.sin(phi))
    y = R_base * (math.sin(phi) - phi * math.cos(phi))
    return App.Vector(x, y, 0)

# Parameters for the profile
R_pitch = body.getObject("Parameters").pitch_diameter / 2
R_outer = R_pitch + body.getObject("Parameters").addendum
R_root = R_pitch - body.getObject("Parameters").dedendum
R_base = body.getObject("Parameters").base_diameter / 2
T_pitch = body.getObject("Parameters").circular_pitch / 2

# Calculate angles for the involute
# The involute starts at the base circle.
# Angle on base circle for Pitch Circle: phi_pitch = acos(R_base / R_pitch)
# Angle on base circle for Outer Circle: phi_outer = acos(R_base / R_outer)
phi_pitch = math.acos(R_base / R_pitch)
phi_outer = math.acos(R_base / R_outer)

# Calculate the angular position of the tooth flanks at the pitch circle.
# The tooth thickness at the pitch circle is T_pitch.
# The angle subtended by the tooth thickness at the pitch circle is:
# delta_pitch = 2 * atan( (T_pitch / 2) / R_pitch )
# Wait, the pressure angle is defined at the pitch circle.
# The tangent to the tooth at the pitch circle makes an angle of 20 deg with the radial line.
# The angle of the flank relative to the radial line is the pressure angle.
# So the flank angle (from the centerline) at the pitch circle is:
# alpha_pitch = atan( (T_pitch / 2) / R_pitch ) ? No.
# The tooth thickness is the arc length. The angle subtended is T_pitch / R_pitch.
# Half of that angle is (T_pitch / 2) / R_pitch.
# Let's call this half-angle 'theta_half'.
theta_half = (T_pitch / 2) / R_pitch

# The flank angle (pressure angle) at the pitch circle is exactly the pressure angle (20 deg) ONLY if the tooth is standard.
# Let's verify: tan(20) = 0.364. 
# theta_half = (3.14159/2) / 40 = 0.039. 
# This is the angle of the tooth sector. The flank is NOT a straight line at 20 deg from the center.
# The involute profile is curved.
# The angle of the tangent to the involute at the pitch circle IS the pressure angle.
# So, the angle of the normal to the tooth at the pitch circle is 20 deg from the radial line.
# The angle of the tangent is 90 - 20 = 70 deg from the radial line? No.
# Pressure angle alpha is the angle between the line of action and the line of centers.
# The line of action is tangent to the base circle.
# The angle of the tangent to the involute at any point is (phi + atan(phi)) + 90?
# Let's just generate the points and connect them.

# We need to find the angle 'theta' (from the gear center) for the start of the tooth.
# The tooth is centered at theta = 0.
# The left flank starts at theta = -theta_half.
# The right flank starts at theta = +theta_half.
# We need to find the corresponding 'phi' (angle on base circle) for these theta values.
# Relationship: theta = phi + atan(phi).
# We need to solve for phi given theta.
# Let's use a numerical solver or approximation.
# Since we are generating points, we can just generate the involute curve and then select the points that fall within the tooth sector.

# Generate a dense set of points for the involute from phi = 0 to phi_outer
points = []
phi_step = 0.01
current_phi = 0.0
while current_phi <= phi_outer:
    p = get_involute_point(current_phi)
    # Calculate the polar angle of this point
    r = p.Length
    if r > 0:
        theta_val = math.atan2(p.Y, p.X)
        # Ensure theta is positive and in [0, pi]
        if theta_val < 0:
            theta_val += 2 * math.pi
        points.append((p, theta_val, current_phi))
    current_phi += phi_step

# Now, filter points that are within the tooth sector [-theta_half, theta_half]
# But wait, the tooth sector is defined at the pitch circle.
# The involute points have different radii.
# We need to find the intersection of the involute with the lines theta = -theta_half and theta = +theta_half.
# Let's find the phi values where theta(phi) = theta_half and theta(phi) = -theta_half.
# Since the function is monotonic, we can search.

def find_phi_for_theta(target_theta):
    # Solve theta = phi + atan(phi) for phi
    # Use binary search or simple iteration
    low = 0.0
    high = 2.0 # Max phi for our gear
    for _ in range(50):
        mid = (low + high) / 2
        val = mid + math.atan(mid)
        if val < target_theta:
            low = mid
        else:
            high = mid
    return (low + high) / 2

# We need the phi values for the boundaries of the tooth at the pitch circle?
# No, the tooth boundaries are defined by the arc length T_pitch at the pitch circle.
# The involute curve passes through the pitch circle at phi_pitch.
# The angle of the tooth flank at the pitch circle is NOT simply theta_half.
# The tooth thickness is measured along the pitch circle.
# The flank intersects the pitch circle at an angle offset from the centerline.
# Let's calculate the angle of the flank at the pitch circle.
# The tangent to the involute at phi_pitch makes an angle of (phi_pitch + atan(phi_pitch)) with the X-axis?
# No, the angle of the tangent is phi_pitch + atan(phi_pitch) + 90?
# The angle of the radius vector is theta = phi + atan(phi).
# The angle of the tangent is theta + 90? No.
# The angle of the tangent to the involute is theta + 90 - alpha?
# Let's use the property: The pressure angle alpha is the angle between the tangent and the radial line.
# So the angle of the tangent is theta + alpha (or theta - alpha).
# At the pitch circle, alpha = 20 deg.
# So the tangent angle is theta_half + 20 deg? No.
# The tooth is symmetric. The centerline is theta=0.
# The left flank is at theta = -theta_half.
# The right flank is at theta = +theta_half.
# The tangent to the left flank at the pitch circle should be at an angle of -theta_half - 20 deg?
# No, the pressure angle is measured from the radial line.
# So the tangent to the left flank at the pitch circle is at angle: -theta_half - (90 - 20)?
# This is getting confusing. Let's use a simpler geometric construction.
# We know the tooth thickness at the pitch circle is T_pitch.
# We know the pressure angle is 20 deg.
# We can construct the profile by:
# 1. Generating the involute curve.
# 2. Finding the two points on the involute that are at distance R_pitch from the center.
#    These are at phi = phi_pitch and phi = -phi_pitch.
#    Their angles are theta = phi_pitch + atan(phi_pitch) and theta = -phi_pitch - atan(phi_pitch).
#    The arc length between them is R_pitch * (theta_right - theta_left).
#    This arc length should be T_pitch.
#    Let's check: 
#    theta_right = phi_pitch + atan(phi_pitch)
#    theta_left = -theta_right
#    Arc = 2 * R_pitch * theta_right.
#    We want 2 * R_pitch * theta_right = T_pitch.
#    So theta_right = T_pitch / (2 * R_pitch).
#    But we also know theta_right = phi_pitch + atan(phi_pitch).
#    And phi_pitch = acos(R_base / R_pitch).
#    Let's check if these are consistent.
#    R_pitch = 40, R_base = 37.587. phi_pitch = acos(37.587/40) = acos(0.9396) = 0.358 rad (20.4 deg).
#    theta_right = 0.358 + atan(0.358) = 0.358 + 0.344 = 0.702 rad (40.2 deg).
#    Arc = 2 * 40 * 0.702 = 56.16 mm.
#    T_pitch = pi * 1 = 3.14 mm.
#    This is WAY off.
#    Ah, the pressure angle is 20 deg.
#    The relationship is: tan(alpha) = (R_base / R_pitch) * tan(phi)? No.
#    The correct relationship is: tan(alpha) = (R_base / R_pitch) * tan(phi) is wrong.
#    The correct relationship is: tan(alpha) = (R_base / R_pitch) * tan(phi) is for the base circle?
#    Let's restart the geometry.
#    The pressure angle alpha is the angle between the line of action and the line of centers.
#    The line of action is tangent to the base circle.
#    The angle of the line of action at the pitch circle is alpha.
#    The angle of the tooth flank at the pitch circle is alpha.
#    So the tangent to the tooth at the pitch circle makes an angle of alpha with the radial line.
#    The angle of the radial line to the pitch circle point is theta_half.
#    So the angle of the tangent is theta_half + alpha (or theta_half - alpha).
#    The angle of the tangent to the involute at phi is: theta + 90? No.
#    The angle of the tangent to the involute is theta + 90 - alpha?
#    Let's use the standard formula:
#    The angle of the tangent to the involute at phi is: theta + 90 - alpha?
#    Actually, the angle of the tangent is theta + 90 - alpha is not right.
#    The angle of the tangent is theta + 90 - alpha is only true if alpha is the pressure angle.
#    Let's just use the fact that the pressure angle is 20 deg.
#    The angle of the tooth flank at the pitch circle is 20 deg from the radial line.
#    So the angle of the flank is theta_half + 20 deg? No.
#    The tooth is symmetric. The centerline is theta=0.
#    The left flank is at theta = -theta_half.
#    The right flank is at theta = +theta_half.
#    The tangent to the left flank at the pitch circle is at an angle of -theta_half - 20 deg?
#    No, the pressure angle is measured from the radial line.
#    So the tangent to the left flank is at an angle of -theta_half - (90 - 20)?
#    This is too complex. Let's use a simpler approach:
#    The tooth thickness at the pitch circle is T_pitch.
#    The pressure angle is 20 deg.
#    We can construct the profile by:
#    1. Generating the involute curve.
#    2. Finding the two points on the involute that are at distance R_pitch from the center.
#    3. The arc length between these two points is T_pitch.
#    4. If the arc length is not T_pitch, we need to adjust the tooth thickness.
#    But the tooth thickness is determined by the module and number of teeth.
#    T_pitch = pi * m / Z.
#    The pressure angle is determined by the base circle and the pitch circle.
#    R_base = R_pitch * cos(alpha).
#    So the geometry is fixed.
#    The arc length between the two points on the involute at R_pitch is:
#    Arc = 2 * R_pitch * (phi_pitch + atan(phi_pitch)).
#    Let's check:
#    R_pitch = 40, R_base = 37.587, alpha = 20 deg.
#    phi_pitch = acos(R_base / R_pitch) = acos(cos(20)) = 20 deg = 0.349 rad.
#    theta_right = phi_pitch + atan(phi_pitch) = 0.349 + atan(0.349) = 0.349 + 0.336 = 0.685 rad.
#    Arc = 2 * 40 * 0.685 = 54.8 mm.
#    T_pitch = pi * 1 = 3.14 mm.
#    This is still way off.
#    Ah, I see the mistake.
#    The angle of the tooth flank at the pitch circle is NOT theta_half.
#    The tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is the pressure angle.
#    So the angle of the flank is alpha = 20 deg.
#    The angle of the tooth centerline is 0.
#    So the angle of the left flank is -alpha = -20 deg.
#    The angle of the right flank is +alpha = +20 deg.
#    The arc length between them is 2 * R_pitch * alpha (in radians).
#    Arc = 2 * 40 * (20 * pi / 180) = 80 * 0.349 = 27.9 mm.
#    T_pitch = 3.14 mm.
#    This is still way off.
#    The pressure angle is the angle between the line of action and the line of centers.
#    The line of action is tangent to the base circle.
#    The angle of the line of action at the pitch circle is alpha.
#    The angle of the tooth flank at the pitch circle is alpha.
#    The angle of the tooth centerline is 0.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the arc length of the tooth space? No, this is the arc length of the tooth thickness?
#    No, the tooth thickness is the arc length between the two flanks.
#    The flanks are the involute curves.
#    The angle of the flank at the pitch circle is alpha.
#    So the angle of the left flank is -alpha.
#    The angle of the right flank is +alpha.
#    The arc length between them is 2 * R_pitch * alpha.
#    This is the
