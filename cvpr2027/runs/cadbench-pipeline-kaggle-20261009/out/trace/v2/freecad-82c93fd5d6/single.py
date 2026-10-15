import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from AGMA 2001 / ISO 6336 standards as requested
PRESSURE_ANGLE_DEG = 20.0
DIAMETRAL_PITCH = 32.0
NUMBER_OF_TEETH = 40
OVERALL_LENGTH = 12 * 25.4  # mm

# Calculated parameters
GEAR_MODULE = 25.4 / DIAMETRAL_PITCH
PITCH_DIAMETER = NUMBER_OF_TEETH / DIAMETRAL_PITCH * 25.4
OUTER_DIAMETER = (NUMBER_OF_TEETH + 2) / DIAMETRAL_PITCH * 25.4

# --- Document Setup ---
doc = App.newDocument("SpurGearStock")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold our named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "Gear Module")
params.module = GEAR_MODULE
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.pitch_diameter = PITCH_DIAMETER
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.outer_diameter = OUTER_DIAMETER
params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Overall Length")
params.overall_length = OVERALL_LENGTH
params.addProperty("App::PropertyInteger", "num_teeth", "Dimensions", "Number of Teeth")
params.num_teeth = NUMBER_OF_TEETH
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = PRESSURE_ANGLE_DEG

# --- Base Sketch (Pitch Circle & Reference) ---
# We define the pitch circle and the outer circle here to drive the tooth generation
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.ConstrainToCurrentBody = True
sketch_base.Support = (doc.getObject("XY_Plane"), [])
sketch_base.MapMode = "FlatFace"

# Pitch Circle
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_diameter / 2.0), False)
# Outer Circle (Addendum)
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0), False)

# --- Tooth Generation Logic ---
# We will create a single tooth profile on a temporary sketch, then use a Polar Pattern.
# The tooth profile is constructed using involute geometry approximations or exact construction.
# For a robust script, we construct the involute curve mathematically.

def create_involute_curve(base_radius, pressure_angle_deg, num_points=100):
    """
    Creates an involute curve starting from base_radius up to the pressure angle.
    Returns a list of Part.LineSegments.
    """
    base_r = base_radius
    pressure_angle_rad = pressure_angle_deg * 3.14159265359 / 180.0
    points = []
    
    # Involute equation:
    # x = r * (cos(t) + t * sin(t))
    # y = r * (sin(t) - t * cos(t))
    # where t is the unwrapping angle.
    # At the base circle, t=0.
    # The pressure angle alpha is related to t by tan(alpha) = t.
    
    t_max = pressure_angle_rad # This gives us the tip of the involute at the pressure angle
    
    # We need to generate points from base circle to the tip of the tooth.
    # The tooth extends from the root circle to the tip circle.
    # However, the prompt asks for a "spur gear stock". 
    # Usually, a stock is a blank. But the description says "toothed gear body".
    # We will generate the full involute teeth.
    
    # Let's define the tooth profile relative to the pitch circle.
    # Root diameter is typically Pitch - 2.25*Module (for 20deg) or similar.
    # But since we are given specific outer and pitch, let's assume standard full depth teeth.
    # Root Radius = (Pitch_Diameter - 2.25 * Module) / 2
    # Tip Radius = (Pitch_Diameter + 1.25 * Module) / 2 ? 
    # Actually, standard: Addendum = 1.0*m, Dedendum = 1.25*m.
    # Tip Dia = (N + 2)*m = Outer Diameter (matches prompt logic roughly)
    # Root Dia = (N - 2.5)*m
    
    root_radius = (params.pitch_diameter - 2.5 * params.module) / 2.0
    tip_radius = (params.pitch_diameter + 1.0 * params.module) / 2.0
    
    # We need to generate the involute from root to tip.
    # The involute starts at the base circle.
    # Base Radius = Pitch_Diameter * cos(Pressure_Angle)
    base_r_calc = params.pitch_diameter * (params.pressure_angle / 90.0) # cos(20) approx 0.9397
    
    # Generate points along the involute from base_r to tip_radius
    # t = sqrt(r^2 - base_r^2) / base_r
    # We need to cover the angular span of the tooth.
    
    # Let's create a function to get a point on the involute given a radius r >= base_r
    def get_involute_point(r):
        if r < base_r_calc:
            return App.Vector(0, 0, 0)
        t = ((r**2 - base_r_calc**2) / base_r_calc**2) ** 0.5
        # Angle of the point on the base circle
        theta = t
        # Coordinates relative to the start of the involute generation
        x = r * (App.cos(theta) + t * App.sin(theta))
        y = r * (App.sin(theta) - t * App.cos(theta))
        return App.Vector(x, y, 0)

    # Generate the profile for one half of the tooth (from pitch circle to tip, then to root)
    # Actually, let's generate the full tooth profile:
    # 1. Start at Root (on the involute curve corresponding to root_radius)
    # 2. Go along the involute to the Pitch Circle
    # 3. Go along the involute to the Tip
    # 4. Close the loop with the root circle arc.
    
    # Wait, the standard tooth profile is:
    # - Flank: Involute from Root to Pitch
    # - Flank: Involute from Pitch to Tip
    # - Root: Circular arc
    
    # Let's generate points for the right flank (0 to 90 deg relative to center of tooth)
    # We need the angle of the tooth.
    # Tooth Thickness at Pitch Circle = Pi / DP = Pi / 32
    # Half angle at pitch circle = (Pi / DP) / 2 / Pitch_Radius
    
    half_tooth_angle_rad = (App.pi / DIAMETRAL_PITCH) / 2 / (params.pitch_diameter / 2.0)
    
    # We need to find the radius at the start of the involute for the flank.
    # The flank starts at the intersection of the involute and the root circle.
    # Let's just generate a dense set of points from root_radius to tip_radius along the involute.
    
    points_list = []
    
    # Generate points from Root to Tip
    # We need to ensure we cover the angular width of the tooth.
    # Let's generate points for the "right" side of the tooth (positive x).
    # The tooth is centered at angle 0.
    # The flank goes from some negative angle to positive angle.
    
    # Let's simplify: Generate the involute curve from base_r to tip_r.
    # Then we will select the segment that corresponds to the tooth flank.
    
    # Actually, let's build the profile explicitly.
    # Point A: Intersection of Root Circle and Involute (Start of Flank)
    # Point B: Intersection of Pitch Circle and Involute (Pitch Point)
    # Point C: Intersection of Tip Circle and Involute (End of Flank)
    
    # Calculate t for Root Radius
    t_root = ((root_radius**2 - base_r_calc**2) / base_r_calc**2) ** 0.5
    # Calculate t for Tip Radius
    t_tip = ((tip_radius**2 - base_r_calc**2) / base_r_calc**2) ** 0.5
    
    # The angle of the tooth centerline relative to the base circle tangent is 0.
    # The flank angle at radius r is theta = t.
    # The tooth half-angle at pitch circle is half_tooth_angle_rad.
    # The involute angle at pitch circle is t_pitch = sqrt((pitch_r^2 - base_r^2)/base_r^2).
    # The flank extends from t_root to t_tip.
    # The angular position of the flank on the gear is:
    # phi = t - half_tooth_angle_rad (for the left flank) ? No.
    # The tooth is symmetric.
    # The flank starts at angle -half_tooth_angle_rad at the pitch circle? No.
    # The tooth thickness is defined at the pitch circle.
    # The involute flanks diverge from the pitch circle.
    
    # Let's generate the profile by sampling radii from root to tip.
    # For each radius r, we have two points on the involute: one at angle +phi, one at -phi.
    # But we need to know the angular position of the tooth.
    # The tooth is centered at 0.
    # The angle of the involute point at radius r is t.
    # The angle of the tooth flank at radius r is t - (angle of pitch circle point).
    # This is getting complex. Let's use a simpler approach:
    # Generate the involute curve from base_r to tip_r.
    # Then rotate it to align with the tooth.
    
    # Simpler approach for script:
    # 1. Generate involute points from base_r to tip_r.
    # 2. These points are at angles t relative to the base circle tangent.
    # 3. The tooth flank is a segment of this curve.
    # 4. The angular width of the tooth at the pitch circle is half_tooth_angle_rad.
    # 5. The involute angle at pitch circle is t_pitch.
    # 6. The flank extends from t_root to t_tip.
    # 7. The angular position of the flank on the gear is shifted by -t_pitch + half_tooth_angle_rad?
    #    Actually, the tooth is centered. The pitch point is at angle 0.
    #    The involute point at pitch circle is at angle t_pitch.
    #    So we need to shift the generated curve by -(t_pitch - half_tooth_angle_rad).
    
    # Let's just generate the curve and then rotate it.
    # Curve points: (x, y) = get_involute_point(r)
    # Rotate by angle -t_pitch + half_tooth_angle_rad
    
    # Wait, the standard definition:
    # The involute starts at the base circle.
    # The angle of the tangent to the involute is alpha.
    # The angle of the radius vector is theta = t + alpha? No.
    # Let's stick to the parametric equations:
    # x = r * (cos(t) + t*sin(t))
    # y = r * (sin(t) - t*cos(t))
    # Here t is the angle of the tangent.
    # The angle of the radius vector is phi = t - arcsin(t/sqrt(1+t^2))? No.
    # phi = t - alpha, where tan(alpha) = t.
    # So phi = t - atan(t).
    
    # We want the tooth centered at 0.
    # The pitch point is at radius pitch_r, angle 0.
    # At pitch_r, t = t_pitch.
    # The angle of the radius vector at pitch_r is phi_pitch = t_pitch - atan(t_pitch).
    # We want this to be 0. So we need to rotate the curve by -phi_pitch.
    
    # Let's generate points from root to tip.
    # We need the angular span of the tooth.
    # The tooth extends from the root circle to the tip circle.
    # The flank is the involute.
    # The root is a circular arc connecting the two flanks.
    
    # Let's generate the right flank (positive x).
    # It goes from root_radius to tip_radius.
    # The angle of the radius vector at radius r is phi(r) = t(r) - atan(t(r)).
    # We want the tooth to be centered at 0.
    # The pitch point is at r=pitch_r, phi=0.
    # So we rotate the curve by -phi(pitch_r).
    
    # Let's generate the profile.
    # We need points for the right flank and left flank.
    # Right flank: r from root to tip.
    # Left flank: r from root to tip.
    # Root: arc from left flank end to right flank end.
    
    # Calculate t for root and tip
    t_root = ((root_radius**2 - base_r_calc**2) / base_r_calc**2) ** 0.5
    t_tip = ((tip_radius**2 - base_r_calc**2) / base_r_calc**2) ** 0.5
    
    # Calculate t for pitch
    t_pitch = (( (params.pitch_diameter/2.0)**2 - base_r_calc**2 ) / base_r_calc**2) ** 0.5
    
    # Rotation angle to center the tooth at 0
    # phi = t - atan(t)
    phi_pitch = t_pitch - App.atan(t_pitch)
    rotation_angle = -phi_pitch
    
    # Generate Right Flank
    # We sample radii from root to tip
    right_flank_points = []
    for r in App.Vector([root_radius, tip_radius]).getValues():
        # Interpolate t between t_root and t_tip
        # Actually, t is a function of r.
        t = ((r**2 - base_r_calc**2) / base_r_calc**2) ** 0.5
        x = r * (App.cos(t) + t * App.sin(t))
        y = r * (App.sin(t) - t * App.cos(t))
        # Rotate
        angle = rotation_angle
        x_rot = x * App.cos(angle) - y * App.sin(angle)
        y_rot = x * App.sin(angle) + y * App.cos(angle)
        right_flank_points.append(App.Vector(x_rot, y_rot, 0))
        
    # Generate Left Flank
    # Symmetric to right flank across Y axis? No, across X axis?
    # The tooth is symmetric across the X axis (if we consider the tooth centerline as X).
    # Wait, the tooth centerline is the X axis.
    # The right flank is in the first quadrant (mostly).
    # The left flank is in the second quadrant.
    # So we reflect across the Y axis (x -> -x).
    left_flank_points = [App.Vector(-p.x, p.y, 0) for p in right_flank_points]
    
    # Combine: Left Flank (bottom to top) -> Root Arc -> Right Flank (top to bottom)
    # But our points are generated from root to tip.
    # So: Left Flank (root to tip) -> Root Arc (tip to tip) -> Right Flank (tip to root)
    
    # Root Arc
    # From left flank tip to right flank tip.
    # Angle of left flank tip: phi_tip = t_tip - atan(t_tip)
    # Angle of right flank tip: -phi_tip
    # We need to connect them with an arc of radius root_radius.
    # The arc goes from angle phi_tip to -phi_tip (clockwise) or vice versa.
    # Since we are going root -> tip -> root -> tip, we need to close the loop.
    # Profile: Left Flank (root->tip) -> Root Arc (tip->tip) -> Right Flank (tip->root)
    
    # Left Flank points are already root->tip.
    # Right Flank points are root->tip. We need tip->root.
    right_flank_points_rev = list(reversed(right_flank_points))
    
    # Root Arc
    # Start at left_flank_points[-1] (tip), end at right_flank_points_rev[0] (tip)
    # Radius is root_radius.
    # Center is (0,0).
    # Angle of start point: atan2(y, x)
    # Angle of end point: atan2(y, x)
    # We need to go the short way.
    
    start_angle = App.atan2(left_flank_points[-1].y, left_flank_points[-1].x)
    end_angle = App.atan2(right_flank_points_rev[0].y, right_flank_points_rev[0].x)
    
    # Create arc
    arc = Part.Arc(App.Vector(0, 0, 0), App.Vector(0, 0, 1), start_angle, end_angle, True) # True for counter-clockwise?
    # FreeCAD Arc: startAngle, endAngle, direction (True=
