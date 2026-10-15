import FreeCAD as App
import Part
import math
from pathlib import Path

# ==============================================================================
# Configuration and Constants
# ==============================================================================
# Derived parameters based on ISO standards for a metric spur gear
GEAR_MODULE = 1.0
NUMBER_OF_TEETH = 20
PRESSURE_ANGLE_DEG = 20.0
PRESSURE_ANGLE = math.radians(PRESSURE_ANGLE_DEG)

# Derived Dimensions
PITCH_DIAMETER = GEAR_MODULE * NUMBER_OF_TEETH
OUTER_DIAMETER = PITCH_DIAMETER + 2.0 * GEAR_MODULE
ROOT_DIAMETER = PITCH_DIAMETER - 2.5 * GEAR_MODULE # 2 * 1.25
FACE_WIDTH = 10.0
HUB_DIAMETER = 16.0
HUB_WIDTH = 10.0
SHAFT_DIAMETER = 6.0
OVERALL_WIDTH = 20.0

ADDENDUM = GEAR_MODULE
DEDENDUM = 1.25 * GEAR_MODULE
WHOLE_DEPTH = ADDENDUM + DEDENDUM

# ==============================================================================
# Document Creation
# ==============================================================================
doc = App.newDocument("SpurGear")

# Create the main Body
body = doc.addObject("PartDesign::Body", "GearBody")
# In FreeCAD 1.1, Body.Placement is a PropertyPlacement, not a direct assignment in some contexts, 
# but usually App.Placement works. If not, we set it via the property.
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Define named parameters for easy editing
params = body.newObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "gear module")
params.module = GEAR_MODULE
params.addProperty("App::PropertyInteger", "teeth", "Dimensions", "number of teeth")
params.teeth = NUMBER_OF_TEETH
params.addProperty("App::PropertyLength", "faceWidth", "Dimensions", "gear width")
params.faceWidth = FACE_WIDTH
params.addProperty("App::PropertyLength", "shaftDiameter", "Dimensions", "bore size")
params.shaftDiameter = SHAFT_DIAMETER
params.addProperty("App::PropertyLength", "hubDiameter", "Dimensions", "hub size")
params.hubDiameter = HUB_DIAMETER
params.addProperty("App::PropertyLength", "hubWidth", "Dimensions", "hub size")
params.hubWidth = HUB_WIDTH
params.addProperty("App::PropertyLength", "overallWidth", "Dimensions", "total width")
params.overallWidth = OVERALL_WIDTH
params.addProperty("App::PropertyAngle", "pressureAngle", "Angles", "20 deg")
params.pressureAngle = PRESSURE_ANGLE_DEG

# Helper to calculate derived values from parameters
def calculate_derived():
    m = params.module.Value
    z = params.teeth.Value
    fa = math.radians(params.pressureAngle.Value)
    
    params.addProperty("App::PropertyLength", "pitchDiameter", "Derived", "calculated")
    params.pitchDiameter = m * z
    
    params.addProperty("App::PropertyLength", "outerDiameter", "Derived", "calculated")
    params.outerDiameter = m * z + 2.0 * m
    
    params.addProperty("App::PropertyLength", "rootDiameter", "Derived", "calculated")
    params.rootDiameter = m * z - 2.5 * m
    
    params.addProperty("App::PropertyLength", "addendum", "Derived", "calculated")
    params.addendum = m
    
    params.addProperty("App::PropertyLength", "dedendum", "Derived", "calculated")
    params.dedendum = 1.25 * m
    
    params.addProperty("App::PropertyLength", "wholeDepth", "Derived", "calculated")
    params.wholeDepth = 2.25 * m
    
    params.addProperty("App::PropertyLength", "circularPitch", "Derived", "calculated")
    params.circularPitch = math.pi * m
    
    return params

params = calculate_derived()

# ==============================================================================
# Feature Construction
# ==============================================================================

# 1. Base Cylinder (Disk)
# Sketch on XY plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseDiskSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Type = "Cartesian"
base_sketch.TechDraw_Plane = "XY"

# Outer diameter line (using radius for circle)
base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outerDiameter.Value / 2.0), False)

# Constraints
base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
base_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.outerDiameter.Value / 2.0), False)

# Pad the disk
base_pad = body.newObject("PartDesign::Pad", "BaseDiskPad")
base_pad.Profile = base_sketch
base_pad.Length = params.faceWidth.Value
base_pad.Type = "Solid"
base_pad.Reversed = False

# 2. Central Bore
# Sketch on XY plane, concentric
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
bore_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
bore_sketch.Type = "Cartesian"
bore_sketch.TechDraw_Plane = "XY"

bore_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaftDiameter.Value / 2.0), False)
bore_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
bore_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.shaftDiameter.Value / 2.0), False)

# Pocket through all
bore_pocket = body.newObject("PartDesign::Pocket", "CentralBorePocket")
bore_pocket.Profile = bore_sketch
bore_pocket.Length = params.overallWidth.Value
bore_pocket.Type = "ThroughAll"

# 3. Hub
# Sketch on XY plane, concentric
hub_sketch = body.newObject("Sketcher::SketchObject", "HubSketch")
hub_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
hub_sketch.Type = "Cartesian"
hub_sketch.TechDraw_Plane = "XY"

hub_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hubDiameter.Value / 2.0), False)
hub_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
hub_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.hubDiameter.Value / 2.0), False)

# Pocket to create the hub recess (leaving the outer ring)
hub_pocket = body.newObject("PartDesign::Pocket", "HubPocket")
hub_pocket.Profile = hub_sketch
hub_pocket.Length = params.hubWidth.Value
hub_pocket.Type = "Blind"
hub_pocket.Reversed = True # Subtract from inside out to leave the hub ring

# 4. Gear Teeth Generation
# We will use a Polar Pattern of a single tooth profile.
# Tooth Profile Sketch on XY plane
tooth_sketch = body.newObject("Sketcher::SketchObject", "ToothProfileSketch")
tooth_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
tooth_sketch.Type = "Cartesian"
tooth_sketch.TechDraw_Plane = "XY"

# Calculate Tooth Geometry
# Pitch Radius
r_pitch = params.pitchDiameter.Value / 2.0
# Addendum Radius
r_addendum = params.outerDiameter.Value / 2.0
# Root Radius
r_root = params.rootDiameter.Value / 2.0
# Circular Pitch
cp = params.circularPitch.Value
# Tooth Width at Pitch Circle (approximate for involute, but we need the specific angles)
# Standard Involute Gear Tooth Calculation:
# Pressure Angle alpha = 20 deg
# Base Radius rb = r_pitch * cos(alpha)
rb = r_pitch * math.cos(PRESSURE_ANGLE)

# Start Angle of Tooth (from center of tooth)
# Half angular pitch = cp / (2 * pi * r_pitch) in radians
theta_pitch_half = cp / (2.0 * r_pitch) 

# Contact point on base circle (start of involute)
# phi_k = sqrt((rb/rb)^2 - 1) ... no, simpler approach:
# The involute starts at the base circle.
# Angle of involute at pitch circle: psi = sqrt(2 * (tan(alpha) - alpha_rad)) ? No.
# Formula: phi = tan(alpha) - alpha_rad (radians)
phi_pitch = math.tan(PRESSURE_ANGLE) - PRESSURE_ANGLE

# Start angle of the tooth flank relative to the center of the tooth sector
# The flank starts at the base circle. 
# Angle from base circle tangent to pitch circle point: phi_pitch
# Half tooth width at pitch circle (angular): theta_pitch_half
# Angle from center of tooth to start of involute:
# alpha_start = theta_pitch_half - phi_pitch
# But wait, the involute starts at base circle. The angle at the base circle is 0.
# The angle at the pitch circle is phi_pitch.
# The angular position of the pitch point relative to the tooth center is theta_pitch_half.
# So the angle relative to the base circle tangent (which is at -theta_pitch_half relative to tooth center?)
# Let's simplify: 
# Center of tooth is at angle 0.
# Pitch circle point is at theta_pitch_half.
# The involute starts at the base circle. The angle subtended by the arc from base circle to pitch circle on the pitch circle is phi_pitch.
# So the involute starts at angle (theta_pitch_half - phi_pitch).

start_angle_radians = theta_pitch_half - phi_pitch
start_angle_deg = math.degrees(start_angle_radians)

# End angle of the tooth flank (at the base circle intersection with root circle)
# This is more complex. We can approximate the root transition or use the standard formula.
# Standard practice for scripting: 
# 1. Line from Base Circle to Pitch Circle (approximating the dedendum flank).
# 2. Arc at Pitch Circle (face width) - actually teeth are continuous, so we define the flank.
# 3. Line from Pitch Circle to Root Circle (addendum circle to root circle) - often approximated as a straight line or a fillet. 
#    For a spur gear, the root is usually a fillet or a short straight line. Let's use a straight line for simplicity and robustness in this context, 
#    connecting the end of the addendum to the root circle, then an arc to the other side.
#    Actually, the standard tooth profile is: Involute flank -> Addendum Arc -> Fillet/Root.
#    Let's construct the profile from the root circle up to the outer circle.
#    
#    Point 1: Intersection of Root Circle and Involute (approx)
#    Let's use a simpler, robust construction often used in CAD:
#    - Line from Root Circle to Pitch Circle (approximating the dedendum flank).
#    - Arc at Pitch Circle (tooth thickness).
#    - Line from Pitch Circle to Outer Circle (addendum flank).
#    
#    Wait, the prompt asks for specific dimensions.
#    Let's use the exact angles.
#    
#    Angle of tooth center: 0
#    Angle of pitch circle point: theta_pitch_half
#    Angle of start of involute (base circle tangent): theta_start_inv = theta_pitch_half - phi_pitch
#    
#    We need the angle where the root circle intersects the involute.
#    r_root = rb / cos(phi_root)
#    cos(phi_root) = rb / r_root
#    phi_root = acos(rb / r_root)
#    theta_root = theta_start_inv + phi_root
    
r_root_val = params.rootDiameter.Value / 2.0
if r_root_val > rb:
    phi_root = math.acos(rb / r_root_val)
    theta_root = start_angle_radians + phi_root
else:
    # If root circle is smaller than base circle, the root is a fillet, not an involute.
    # For standard gears, r_root < rb is common (undercut). 
    # rb = 10 * cos(20) = 9.397. r_root = 8.75. 
    # So r_root < rb. The root is a fillet between the two flanks.
    # We will construct the flank up to the base circle, then a circular arc for the root.
    
    # Flank goes from Base Circle (start_angle_radians) to Base Circle (end_angle_radians)
    # Then a fillet from Base Circle to Root Circle.
    # Actually, the standard profile is:
    # 1. Involute from Base Circle to Outer Circle.
    # 2. Fillet at Root connecting the two involutes.
    # So we only draw the involute part and the fillet.
    
    # Start of involute: Base Circle, angle start_angle_radians
    # End of involute: Outer Circle, angle theta_outer = start_angle_radians + phi_outer
    # cos(phi_outer) = rb / r_addendum
    # r_addendum = 11.0. rb = 9.397. phi_outer = acos(9.397/11) = 30.3 deg.
    
    r_addendum_val = params.outerDiameter.Value / 2.0
    phi_outer = math.acos(rb / r_addendum_val)
    theta_outer = start_angle_radians + phi_outer
    
    # Now we have the involute arc.
    # We need to close the loop.
    # The other side of the tooth is symmetric.
    # The tooth space is between this tooth and the next.
    # We just need to define the profile of ONE tooth and pattern it.
    # The profile consists of:
    # 1. Line from (0,0) to Base Circle? No.
    # 2. Arc of Base Circle? No, the tooth comes out of the base circle.
    # 3. Involute Arc from Base Circle to Outer Circle.
    # 4. Circular Arc at Root connecting to the other flank? 
    #    The standard "Tooth" in a polar pattern usually just defines the flank and the top.
    #    Let's define the profile as:
    #    - Line from (r_pitch, 0) to (r_addendum, theta_outer) - Wait, this is an arc.
    #    - Arc from (r_addendum, theta_outer) to (r_addendum, 0)? No.
    
    # Let's try a simpler, robust approach for the sketch:
    # 1. Line from Pitch Circle to Outer Circle (Addendum)
    # 2. Arc at Outer Circle (Tip) - usually very small or ignored if just flanks.
    # 3. Involute Flank.
    # 4. Root Fillet.
    
    # Correct Sequence for one half of the tooth (from center line to flank):
    # 1. Point at Pitch Circle, Angle 0 (Center Line intersection).
    # 2. Arc at Pitch Circle to the flank start? No, the flank starts at the base circle.
    #    The space between the center line and the flank start is filled with material.
    #    So the profile is:
    #    - Line from (r_pitch, 0) to (r_pitch, theta_pitch_half)? No, that's the tooth width.
    #    - We need the boundary.
    #    - Boundary starts at (r_pitch, theta_pitch_half).
    #    - Goes along the involute to (r_addendum, theta_outer).
    #    - Then along the root circle? 
    #    - Then back to (r_pitch, theta_pitch_half) via the other side?
    #    
    #    Let's construct the profile starting from the center line (angle 0) going outwards?
    #    No, the pattern will handle the repetition. We define the shape of the tooth itself.
    #    The shape is bounded by:
    #    - Line at angle 0 from r_root to r_addendum? (If no undercut)
    #    - Involute flank.
    #    - Root fillet.
    
    # Let's assume the standard "involute tooth" sketch:
    # 1. Line from (r_addendum, theta_outer) to (r_addendum, -theta_outer) - Tip arc.
    # 2. Involute from (r_addendum, -theta_outer) to (r_base, -theta_start_inv).
    # 3. Base circle arc? No, the tooth comes from the root.
    # 4. Root fillet from (r_base, -theta_start_inv) to (r_base, theta_start_inv).
    # 5. Involute from (r_base, theta_start_inv) to (r_addendum, theta_outer).
    # 6. Close.
    
    # This creates a tooth with a rounded root and involute flanks.
    # We need to define the angles correctly.
    # Center of tooth is at 0.
    # Right flank:
    #   - Start at Base Circle, angle start_angle_radians.
    #   - End at Outer Circle, angle theta_outer.
    # Left flank (symmetric):
    #   - Start at Base Circle, angle -start_angle_radians.
    #   - End at Outer Circle, angle -theta_outer.
    
    # Root fillet:
    #   - Connects (r_base, -start_angle_radians) to (r_base, start_angle_radians).
    #   - Radius = r_base - r_root? 
    #   - The fillet radius is usually small. Let's use a generic small fillet or the difference.
    #   - Actually, the root
