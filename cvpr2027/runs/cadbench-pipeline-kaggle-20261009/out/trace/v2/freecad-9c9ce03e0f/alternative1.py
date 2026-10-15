import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize document
doc = App.newDocument("SpurGear")

# --- 1. Create Parameters Object (Editable) ---
params = doc.addObject("PartDesign::BodyParameter", "Parameters")
params.Label = "Parameters"
params.Type = "App::VarSet"

params.addProperty("App::PropertyLength", "module", "Dimensions", "Module m")
params.module = 1.0

params.addProperty("App::PropertyInteger", "teeth", "Dimensions", "Number of teeth Z")
params.teeth = 80

params.addProperty("App::PropertyLength", "width", "Dimensions", "Face Width")
params.width = 6.0

params.addProperty("App::PropertyLength", "hub_dia", "Dimensions", "Hub Diameter")
params.hub_dia = 18.0

params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.hub_width = 8.0

params.addProperty("App::PropertyLength", "shaft_dia", "Dimensions", "Shaft Diameter")
params.shaft_dia = 8.0

params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "Pressure Angle deg")
params.pressure_angle_deg = 20.0

params.addProperty("App::PropertyLength", "whole_depth", "Dimensions", "Whole Depth")
params.whole_depth = 2.25

# Derived Dimensions (can be driven by expressions, but set values for stability in headless)
params.addExpression("pitch_diameter", "Parameters.module * Parameters.teeth")
params.addExpression("outer_diameter", "Parameters.pitch_diameter + 2 * Parameters.module")
params.addExpression("root_diameter", "Parameters.pitch_diameter - 2 * Parameters.whole_depth")
params.addExpression("base_diameter", "Parameters.pitch_diameter * cos(Parameters.pressure_angle_deg * pi / 180)")
params.addExpression("circular_pitch", "pi * Parameters.module")
params.addExpression("tooth_thickness", "Parameters.circular_pitch / 2")
params.addExpression("addendum", "Parameters.module")
params.addExpression("dedendum", "1.25 * Parameters.module")
params.addExpression("overall_width", "Parameters.hub_width + Parameters.width")

# --- 2. Create Body ---
body = doc.addObject("PartDesign::Body", "Body")
body.Label = "Body"

# --- 3. Define Sketches and Features ---

# Plane definitions (standard XY, XZ, YZ are available in the new document usually, 
# but to be safe we use the standard naming conventions FreeCAD expects or creates)
# FreeCAD 1.1 standard planes: XY_Plane, XZ_Plane, YZ_Plane, X_Axis, Y_Axis, Z_Axis

# --- Sketch 1: Gear Teeth Profile (Radial) ---
# Plane: XY_Plane (for the cross-section of the tooth)
sk1 = body.newObject("Sketcher::SketchObject", "Sketch_Teeth")
sk1.Placement = App.Placement(App.Vector(0, 0, 0))
sk1.ConstraintType = "Locked" # Optional: locks position
sk1.Plane = "XY_Plane"
sk1.AddGeometry(Part.LineSegment(App.Vector(0, 0), App.Vector(0, 100)), True) # Placeholder line to define sketch plane context if needed, but usually not needed if plane is set
sk1.Constraints = [] # We will add constraints manually for precision

# Define the tooth profile geometry relative to the center (0,0)
# Tooth thickness at pitch circle
cp = 3.14159265358979323846 # pi
half_thickness = cp / 2 / params.teeth # Approximation for single tooth center
# For a full involute, we generate the curve points or use analytic geometry.
# Since we need a closed loop for the pad/pocket, we construct the profile for ONE tooth 
# and then pattern it.
# Profile: Outer Circle -> Addendum Circle -> Involute -> Base Circle -> Root Circle -> Addendum Circle...

# Helper function to get involute point
def get_involute_point(theta_deg):
    theta = theta_deg * 3.14159265358979323846 / 180
    base_r = params.base_diameter / 2
    # Involute equation: r = base_r / cos(theta_inv), theta_inv = theta - atan(theta * tan(base_r/r))
    # Simplified parameterization by angle on base circle:
    # Let phi be the angle on the base circle.
    # The point on the involute is: 
    # x = base_r * (cos(phi) + phi * sin(phi))
    # y = base_r * (sin(phi) - phi * cos(phi))
    # where the angle from center is phi + atan(phi)
    
    # We need the angle 'phi' such that the total angle from center is 'theta'.
    # theta = phi + atan(phi)
    # This requires solving for phi.
    # Approximation or iterative solution? 
    # Let's use a simpler approach: generate enough points for the involute arc.
    pass

# Let's construct the path for one tooth manually using analytic curves
# Start at top of outer diameter, go down involute to pitch circle, down to root, around root, up involute to pitch, up to outer.
# Actually, standard gear profile:
# 1. Outer Arc (Addendum)
# 2. Involute (from outer to pitch)
# 3. Involute (from pitch to root) - Note: The active flank is involute, but the root is usually truncated by a fillet or straight line. 
#    The problem description implies standard ISO gear. Standard gear root is usually a fillet, but for a simple script, 
#    we can approximate the root as a straight line or use a small fillet. 
#    Given the constraints, we will create a closed loop: 
#    Outer Arc -> Involute (Active) -> Root Line (approx) -> Involute (Other side) -> Outer Arc.
#    Wait, the tooth profile is usually: Top Circle -> Involute -> Base Circle -> ... NO.
#    Top Circle -> Involute -> Pitch Circle -> Base Circle (theoretical) -> Root Circle (truncated).
#    Let's build the profile for ONE tooth centered on X-axis.
    
# Geometry for ONE tooth (centered at x=0):
# Tooth thickness at pitch circle = circular_pitch / 2
# Pitch Radius = params.pitch_diameter / 2
# Outer Radius = Pitch Radius + Addendum
# Root Radius = Pitch Radius - Dedendum
# Base Radius = Pitch Radius * cos(Pressure Angle)

# We will create a closed spline or polyline approximating the involute.
# Or better: Use Part::Polygon or Part::Spline if available, but Part::Spline is preferred for curves.
# Let's generate points for the Involute.

def generate_involute_points(r_base, r_start_angle_deg, r_end_angle_deg, num_points=50):
    """Generates points on an involute starting from base circle radius r_base."""
    points = []
    # Angle on the base circle (phi) goes from 0 to (theta_end - theta_start)
    # Total rotation angle theta = phi + atan(phi)
    # We need to find phi for a given theta.
    # We'll iterate phi from 0 upwards.
    
    # Actually, let's just generate points along the angle 'theta' of the involute relative to the gear center.
    # The relationship is theta = phi + atan(phi).
    # We can solve for phi given theta numerically or just generate phi and calculate theta.
    
    # Let's generate phi from 0 to max_phi such that the resulting radius reaches the target.
    # Max phi is roughly (theta_target - atan(theta_target)) ... hard to guess.
    # Instead, let's generate phi from 0 to, say, 2 radians (covers most of the active flank).
    
    current_phi = 0.0
    phi_step = 0.02
    
    while current_phi < 3.0: # Safety limit
        # Calculate point for this phi
        r = r_base / (1.0 / current_phi + 0.001) # Avoid div by zero at start
        # Correct formula: 
        # x = r_base * (cos(phi) + phi * sin(phi))
        # y = r_base * (sin(phi) - phi * cos(phi))
        
        # Calculate actual polar angle from center
        theta_val = current_phi + (current_phi / (1 + current_phi**2)) # Approx? No.
        # Exact: theta = phi + atan(phi)
        theta_val = current_phi + math.atan(current_phi)
        
        x = r_base * (math.cos(current_phi) + current_phi * math.sin(current_phi))
        y = r_base * (math.sin(current_phi) - current_phi * math.cos(current_phi))
        
        points.append(App.Vector(x, y, 0))
        
        current_phi += phi_step
        if len(points) > num_points:
            break
            
    return points

import math

# Parameters for the profile
R_pitch = params.pitch_diameter / 2
R_outer = R_pitch + params.addendum
R_root = R_pitch - params.dedendum
R_base = params.base_diameter / 2

# Tooth Thickness at Pitch Circle
T_pitch = params.circular_pitch / 2

# We need to generate the profile for one tooth.
# The tooth is symmetric around X=0.
# Left side (from -T_pitch/2 to 0): Active flank (Involute)
# Right side (from 0 to T_pitch/2): Active flank (Involute)
# Top: Arc of Outer Diameter
# Bottom: Root Circle (truncated)

# Strategy:
# 1. Start at Top Left (Outer Dia, -T_pitch/2)
# 2. Involute to Pitch Circle Left (-T_pitch/2)
# 3. Involute to Root (Left side, at angle corresponding to Root Radius)
#    Wait, the root is usually cut off. The profile stops at the Root Radius.
#    So: Outer -> Involute -> Pitch -> Involute -> Root (straight line? or fillet?)
#    Standard gear: The root is a fillet. But for a script, let's use a straight line tangent to the base? 
#    Or just use the root circle arc. 
#    Let's use a simplified profile: 
#    Outer Arc -> Involute -> Root Circle Arc -> Involute -> Outer Arc.
#    This creates a "stub" tooth if the involute doesn't reach the root.
#    Actually, the involute starts at the base circle. 
#    If Root Radius < Base Radius (which is true here: 38.75 < 37.58? No. 77.5/2 = 38.75. Base = 75.175/2 = 37.59. 
#    So Root > Base. The involute exists down to the base circle.
#    Between Base and Root, there is no involute. It's a non-involute region.
#    Usually, this region is cut with a fillet or a straight line.
#    We will approximate the root as a straight line connecting the two points where the involute meets the root circle? 
#    No, the involute meets the base circle. 
#    Let's simplify: Generate the profile from Outer to Base, then connect Base to Root with a small arc or line.
#    Given the complexity of exact ISO gear root fillet in a script, we will:
#    1. Generate Involute from Outer Radius down to Base Radius.
#    2. Connect Base Radius to Root Radius with a straight line (vertical in the local tooth frame? No, it's curved).
#    3. Close the loop.
#    Better approach for a "good enough" spur gear:
#    Create a spline through:
#    A: ( -T_pitch/2, R_outer )
#    B: Involute point at R_outer, angle corresponding to T_pitch/2
#    C: Involute point at R_base, angle corresponding to T_pitch/2
#    D: ( -T_pitch/2, R_root ) -- Wait, this is getting complex.
    
# Let's try a different, robust method: 
# Create the profile for a tooth by defining the path from the start of the left flank to the end of the right flank.
# Path:
# 1. Start at Left Flank Top: Polar angle = pi - delta. Radius = R_outer.
#    We need to find the delta such that the chord length at R_pitch is T_pitch.
#    Angle of one tooth sector = 2 * pi / Z.
#    Angle from center to the start of the tooth = pi/Z - half_thickness/R_pitch? No.
#    The tooth is centered at angle 0.
#    The flank starts at angle: alpha_start = acos(cos(alpha_pressure) / (R_outer/R_base))? No.
#    Let's calculate the pressure angle at the outer diameter.
#    tan(alpha_outer) = (R_outer/R_base) * tan(alpha_pressure)
#    alpha_outer = atan( (R_outer/R_base) * tan(alpha_pressure) )
#    
#    So the involute starts at R_base.
#    The point at R_outer is at angle alpha_outer (from the tangent point).
#    The angle from the gear center to the point (R_outer, 0) is... wait.
#    Let's use the property that the line of action is tangent to the base circle.
#    The angle of the tooth space at the base circle is:
#    theta_base = atan( (R_outer/R_base) * tan(alpha_pressure) ) - alpha_pressure
#    The angle at the outer diameter is alpha_outer.
#    
#    Let's just generate the profile points:
#    Point 1: (-T_pitch/2, R_outer)  <- Wait, this is Cartesian. We need Polar.
#    Let's define the tooth profile in Cartesian coordinates centered at (0,0).
#    Tooth is symmetric about X axis.
#    Left side (x < 0):
#      Start at Top Left: x = -T_pitch/2, y = R_outer.
#      Move along Involute to Pitch Circle: x = -T_pitch/2, y = R_pitch.
#      Move along Involute to Base Circle: x = ?, y = R_base.
#      Move along Root Circle? Or Line?
#      Move up to Root: x = -T_pitch/2, y = R_root.
#    This is an approximation. 
#    
#    Let's do a precise Involute generation:
#    Angle of the tooth space at the pitch circle: alpha_pitch = atan( (T_pitch / (2 * R_pitch)) / sin(pi/Z) )? No.
#    The angle between the tooth centerline and the flank at the pitch circle is:
#    phi_pitch = atan( (T_pitch / 2) / R_pitch ) # This is the half-angle subtended by the tooth thickness at the pitch circle.
#    # Actually, the flank is a straight line in the normal plane? No, it's curved.
#    # The pressure angle is the angle between the tangent to the tooth and the line of centers.
#    # At the pitch circle, the pressure angle IS the pressure angle (20 deg).
#    # So the tangent to the tooth at the pitch circle makes 20 deg with the radial line.
#    # Therefore, the tooth profile at the pitch circle has a slope.
#    # We can generate the profile by integrating the normal vector.
#    
#    Simplified Profile Generation:
#    We will create a curve that passes through key points:
#    1. (0, R_outer) -> Top of tooth center (Wait, tooth is at x=0? No, let's make the tooth centered at x=0).
#    2. Points at x = -T_pitch/2 and x = T_pitch/2 at y = R_pitch.
#    3. Points at x = -T_pitch/2 and x = T_pitch/2 at y = R_root.
#    4. Connect (0, R_outer) to (-T_pitch/2, R_pitch) via Involute.
#    5. Connect (-T_pitch/2, R_pitch) to (-T_pitch/2, R_root) via straight line? Or Root Circle.
#    
#    Let's use a Spline that approximates the ISO profile:
#    Points:
#    P1: (-T_pitch/2, R_outer)
#    P2: Involute point at R_outer, angle corresponding to P1.
#    ... this is too manual.
#    
#    Alternative: Use the `Part::Polygon` or `Part::Spline` with a few points that define the shape.
#    Let's generate the involute curve from R_base to R_outer.
#    The involute curve is defined by the equation:
#    x = R_base * (cos(phi) + phi*sin(phi))
#    y = R_base * (sin(phi) - phi*cos(phi))
#    where phi is the angle on the base circle.
#    The angle from the gear center (theta) is phi + atan(phi).
#    
#    We need to find the range of phi that covers the tooth.
#    At the pitch circle (R_pitch):
#    R_pitch = R_base / cos(phi_pitch) -> phi_pitch = acos(R_base/R_pitch).
#    At the outer circle (R_outer):
#    R_outer = R_base / cos(phi_outer) -> phi_outer = acos(R_base/R_outer).
#    
#    So the active flank exists for phi from phi_pitch to phi_outer (and negative).
#    The tooth thickness at the pitch circle is determined by the arc length between the two flanks.
#    Arc length at R_pitch = R_pitch * (theta_right - theta_left).
#    We want this arc length to be T_pitch.
#    Due to symmetry,
