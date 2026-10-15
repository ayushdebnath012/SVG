import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# --- Parameters ---
# Gear Geometry
pressure_angle_deg = 20.0
gear_module = 1.0
number_of_teeth = 20
pitch_diameter = 20.0
outer_diameter = 22.0
face_width = 10.0
hub_diameter = 16.0
hub_width = 10.0
shaft_diameter = 6.0
overall_width = 20.0

# Calculated ISO 54 Proportions
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
root_diameter = pitch_diameter - 2 * dedendum
circular_pitch = math.pi * gear_module

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We use a VarSet to hold the named parameters requested in the prompt
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "gear module")
params.gear_module = gear_module
params.addProperty("App::PropertyLength", "number_of_teeth", "Dimensions", "number of teeth")
params.number_of_teeth = number_of_teeth
params.addProperty("App::PropertyLength", "pressure_angle", "Dimensions", "pressure angle (deg)")
params.pressure_angle = pressure_angle_deg
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "pitch diameter")
params.pitch_diameter = pitch_diameter
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "outer diameter")
params.outer_diameter = outer_diameter
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "face width")
params.face_width = face_width
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "hub diameter")
params.hub_diameter = hub_diameter
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "hub width")
params.hub_width = hub_width
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "shaft diameter")
params.shaft_diameter = shaft_diameter
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "overall width")
params.overall_width = overall_width
params.addProperty("App::PropertyLength", "addendum", "Dimensions", "addendum")
params.addendum = addendum
params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "dedendum")
params.dedendum = dedendum
params.addProperty("App::PropertyLength", "whole_depth", "Dimensions", "whole depth")
params.whole_depth = whole_depth
params.addProperty("App::PropertyLength", "root_diameter", "Dimensions", "root diameter")
params.root_diameter = root_diameter
params.addProperty("App::PropertyLength", "circular_pitch", "Dimensions", "circular pitch")
params.circular_pitch = circular_pitch

# --- Sketch 1: Gear Teeth Profile ---
# We create a sketch on the XY plane. 
# The profile will be a closed loop representing one tooth space or the gear outline.
# Strategy: Create a sketch with the outer circle, root circle, and the involute/tooth profile.
# To make it parametric and editable, we will construct the tooth profile using lines and arcs 
# constrained to the calculated diameters.

sketch_teeth = body.newObject("Sketcher::SketchObject", "Sketch_Geometry")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_teeth.ConstrainToCurrentPlacement = True
sketch_teeth.Support = (doc.getObject("XY_Plane"), [""])
sketch_teeth.MapMode = "FlatFace"

# Helper to add geometry
def add_line(p1, p2, name="Line"):
    return sketch_teeth.addGeometry(Part.LineSegment(p1, p2), False, name)

def add_circle(center, radius, name="Circle"):
    return sketch_teeth.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), False, name)

# 1. Outer Circle (Tip Circle)
# Diameter = outer_diameter
add_circle(App.Vector(0, 0, 0), params.outer_diameter / 2.0, "OuterCircle")

# 2. Root Circle (Bottom of teeth)
# Diameter = root_diameter
add_circle(App.Vector(0, 0, 0), params.root_diameter / 2.0, "RootCircle")

# 3. Tooth Profile Construction
# We need to generate the profile for one tooth and close the loop.
# Standard spur gear tooth profile consists of:
# - Addendum circle arc (part of outer circle)
# - Dedendum circle arc (part of root circle)
# - Flank (involute)
# - Tip (fillet or straight, usually fillet in simplified models, but standard is involute)
# 
# Simplified Parametric Approach for FreeCAD Script:
# We will define the profile by creating a closed loop of lines and arcs that approximate 
# the gear tooth space, or better, we create the solid by revolving a 2D profile.
# 
# Let's create a profile that represents the "Tooth Space" (the gap between teeth) 
# or the "Tooth" itself. Revolving the tooth space creates the gear body.
# 
# Tooth Space Geometry:
# - Starts at Root Circle
# - Goes along Root Circle to the start of the flank
# - Goes up the flank (approximated by lines for simplicity in script, or arcs)
# - Goes along Addendum Circle
# - Goes down the other flank
# - Closes at Root Circle
#
# To make it fully parametric without complex constraint solving for involutes in a script,
# we will use the standard simplified construction:
# 1. Define the angle of the tooth space.
#    Total angle = 360 / N
#    Tooth thickness angle = (Total angle / 2) - (Pressure Angle / 2) ? 
#    Actually, standard spacing:
#    Circular Pitch = pi * m
#    Tooth Thickness Angle = (Circular Pitch / 2) / Radius = (pi * m / 2) / (m * N / 2) = pi / N
#    Wait, simpler: 
#    Angle between teeth = 360 / N
#    Half angle of tooth space = (360/N) / 2 = 180/N
#    The flank angle relative to the radial line is the pressure angle.
#
# Let's calculate the start and end angles for the tooth space relative to the X-axis.
# We place the tooth space symmetrically around the X-axis (0 degrees).
# Start Angle = - (180/N) - (PressureAngle/2) ? No.
# The standard definition:
# The tooth space is centered on the radial line.
# The flank makes an angle of PressureAngle with the tangent to the pitch circle.
# 
# Let's define the vertices of the tooth space profile:
# 1. Point A: On Root Circle, at angle - (180/N) - (PressureAngle/2) ? 
#    Actually, let's use the standard formula for the angle of the tooth space boundaries.
#    Angle of tooth space = 360 / N
#    Half angle = 180 / N
#    The flank is inclined at PressureAngle to the tangent.
#    So the angle of the flank relative to the radial line is (90 - PressureAngle).
#    The angle of the flank relative to the X-axis (if tooth space is centered on X) is:
#    Start Angle = - (180/N) - (90 - PressureAngle)
#    End Angle = + (180/N) + (90 - PressureAngle)
#    Wait, this is getting complicated to get exactly right without a CAD tool.
#    
#    Alternative: Use the standard "Simplified" gear generation method often used in scripts.
#    We create a profile that is:
#    - Outer Arc from angle -alpha to +alpha
#    - Two straight lines (flanks) connecting outer to inner
#    - Inner Arc from -alpha to +alpha
#    
#    Where alpha is the half-angle of the tooth space.
#    Alpha = (180 / N) + (PressureAngle / 2) ? 
#    Let's stick to the geometry:
#    The tooth space is bounded by two involutes.
#    For a script, we can approximate the involute with a straight line if we want speed, 
#    but for a "correct" gear, we should try to be accurate.
#    However, FreeCAD's PartDesign allows us to use Part::MakeBRep or similar if needed, 
#    but the prompt asks for sketches and features.
#    
#    Let's use the standard approximation:
#    The angle of the tooth space (gap) is 360/N.
#    The tooth thickness is also 360/N (at pitch circle).
#    The flank angle is defined by the pressure angle.
#    
#    Let's define the profile points explicitly:
#    1. Start of Root Arc: Angle = - (180/N) - (PressureAngle/2) -> This is wrong.
#    
#    Correct Logic:
#    The tooth space is centered at 0 degrees.
#    The width of the tooth space at the pitch circle is Circular Pitch / 2.
#    The angle subtended by the tooth space at the pitch circle is (Circular Pitch / 2) / PitchRadius = (pi*m/2) / (m*N/2) = pi/N = 180/N.
#    So the tooth space spans from -90/N to +90/N? No.
#    Total angle for N teeth = 360. Angle per tooth = 360/N.
#    The tooth space is half of that? No, the tooth space is the gap.
#    The gap angle = 360/N.
#    So the gap spans from -180/N to +180/N.
#    The flanks are inclined at PressureAngle to the tangent.
#    The tangent at the pitch circle is perpendicular to the radius.
#    So the flank makes an angle of (90 - PressureAngle) with the radius.
#    Therefore, the flank line goes from the pitch circle outwards/inwards at an angle of (90 - PressureAngle) from the radial line.
#    
#    Let's define the vertices:
#    V1: On Root Circle, at angle = - (180/N) - (90 - PressureAngle)
#    V2: On Pitch Circle, at angle = - (180/N)
#    V3: On Addendum Circle, at angle = - (180/N)
#    V4: On Addendum Circle, at angle = + (180/N)
#    V5: On Pitch Circle, at angle = + (180/N)
#    V6: On Root Circle, at angle = + (180/N) + (90 - PressureAngle)
#    
#    Wait, the flanks are not straight lines in reality, but for a scriptable parametric model, 
#    using straight lines (chamfered look) is a common simplification unless we use complex curves.
#    Given the constraints of a single script, we will use straight lines for the flanks.
#    This creates a "simplified" gear which is valid for many applications.
#    
#    Let's refine the angles:
#    Tooth Space Center Angle = 0.
#    Tooth Space Half Angle (at Pitch Circle) = 180 / N.
#    Flank Angle (from radial) = 90 - PressureAngle.
#    
#    Start of Flank (Inner): Angle = - (180/N) - (90 - PressureAngle)
#    End of Flank (Inner): Angle = + (180/N) + (90 - PressureAngle)
#    
#    Let's calculate these angles.
#    N = 20, PressureAngle = 20.
#    Half Tooth Space Angle = 180/20 = 9 deg.
#    Flank Angle = 90 - 20 = 70 deg.
#    Start Angle = -9 - 70 = -79 deg.
#    End Angle = +9 + 70 = +79 deg.
#    
#    So the profile is:
#    1. Arc on Root Circle from -79 to +79 deg.
#    2. Line from (+79 deg, Root) to (+9 deg, Pitch)? No.
#       The flank connects the Root Circle to the Addendum Circle.
#       But the flank is tangent to the base circle.
#       Simplified: Connect Root Circle point to Addendum Circle point with a straight line.
#       Where do these lines start/end?
#       They start/end at the "tooth space boundaries".
#       The boundary at the pitch circle is at +/- 9 deg.
#       The boundary at the root circle is at +/- 79 deg.
#       The boundary at the addendum circle is at +/- 9 deg (since the tooth tip is usually centered).
#       
#    So the profile loop:
#    1. Arc on Root Circle from -79 to +79 deg.
#    2. Line from (+79 deg, Root) to (+9 deg, Pitch)? No, the flank goes from Root to Addendum.
#       But the flank angle is constant.
#       Let's just connect the points:
#       P_root_start = (R_root, -79 deg)
#       P_root_end = (R_root, +79 deg)
#       P_pitch_start = (R_pitch, -9 deg)
#       P_pitch_end = (R_pitch, +9 deg)
#       P_add_start = (R_add, -9 deg)
#       P_add_end = (R_add, +9 deg)
#       
#    The flank connects P_root_start to P_add_start?
#    If we connect them with a straight line, the angle might not be exactly the pressure angle, 
#    but it's a valid parametric approximation.
#    
#    Let's construct the loop:
#    1. Arc Root Circle: -79 to +79 deg.
#    2. Line: (+79 deg, Root) to (+9 deg, Pitch)? No, that's a chord.
#       We need the flank.
#       Let's assume the flank is a straight line connecting the Root Circle point to the Addendum Circle point.
#       But where?
#       The tooth space is defined by the intersection of the two flanks.
#       The flanks are inclined at 20 deg to the tangent.
#       So the angle of the flank line relative to the X-axis (if tooth space is on X) is:
#       Angle = 90 - 20 = 70 deg (from radial).
#       So the line goes from the inner radius to the outer radius at 70 deg from the radial line.
#       
#    Let's try a different approach: Define the profile by points and constraints.
#    Points:
#    A: (0, -R_root) -> No, let's use polar.
#    Let's define the profile as a closed loop of 4 segments:
#    1. Arc on Root Circle from -79 to +79 deg.
#    2. Line from (+79 deg, Root) to (+9 deg, Pitch)? No.
#       Let's just use the standard "Simplified Gear" profile:
#       - Outer Arc (Addendum) from -9 to +9 deg.
#       - Two straight lines (flanks) connecting Outer to Inner.
#       - Inner Arc (Root) from -79 to +79 deg.
#       
#    Wait, the flanks must connect the Outer Arc to the Inner Arc.
#    The Outer Arc is at +/- 9 deg.
#    The Inner Arc is at +/- 79 deg.
#    So we need lines from (+9 deg, Add) to (+79 deg, Root)?
#    No, the tooth space is the gap.
#    The gap is bounded by the flanks.
#    The flanks go from the Root Circle to the Addendum Circle.
#    The angle of the flank is 70 deg from the radial.
#    So the line starts at the Root Circle at angle -79 deg and ends at the Addendum Circle at angle -9 deg?
#    Let's check the slope.
#    Radial vector at -79 deg. Tangent is at -169 deg.
#    Flank is 20 deg from tangent. So -169 + 20 = -149? Or -169 - 20 = -189?
#    This is getting too complex for a quick script.
#    
#    Let's use the standard "Involute" approximation with straight lines:
#    We will create a profile that looks like a gear tooth space.
#    We will define the vertices:
#    1. Start of Root Arc: Angle = - (180/N) - (90 - PressureAngle)
#    2. End of Root Arc: Angle = + (180/N) + (90 - PressureAngle)
#    3. End of Addendum Arc: Angle = + (180/N)
#    4. Start of Addendum Arc: Angle = - (180/N)
#    
#    And
