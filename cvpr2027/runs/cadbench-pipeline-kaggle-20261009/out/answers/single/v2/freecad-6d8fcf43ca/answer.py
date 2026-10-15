import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from the prompt requirements
PRESSURE_ANGLE_DEG = 20.0
GEAR_MODULE = 1.0
NUMBER_OF_TEETH = 60
PITCH_DIAMETER = 60.0
OUTER_DIAMETER = 62.0
FACE_WIDTH = 6.0
HUB_DIAMETER = 18.0
HUB_WIDTH = 8.0
SHAFT_DIAMETER = 8.0
OVERALL_WIDTH = 14.0

# Calculated parameters based on ISO/DIN standards provided in prompt
PRESSURE_ANGLE = math.radians(PRESSURE_ANGLE_DEG)
ADDENDUM = PITCH_DIAMETER / NUMBER_OF_TEETH
DEDENDUM = 1.25 * GEAR_MODULE
WHOLE_DEPTH = ADDENDUM + DEDENDUM
ROOT_DIAMETER = PITCH_DIAMETER - 2 * DEDENDUM
BASE_DIAMETER = PITCH_DIAMETER * math.cos(PRESSURE_ANGLE)

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold our named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.gear_module = GEAR_MODULE
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Teeth")
params.number_of_teeth = NUMBER_OF_TEETH
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Width")
params.face_width = FACE_WIDTH
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub")
params.hub_diameter = HUB_DIAMETER
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub")
params.hub_width = HUB_WIDTH
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Bore")
params.shaft_diameter = SHAFT_DIAMETER
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Total")
params.overall_width = OVERALL_WIDTH
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Angle")
params.pressure_angle = PRESSURE_ANGLE_DEG

# --- Sketch 1: Gear Profile (XY Plane) ---
sketch_gear = body.newObject("Sketcher::SketchObject", "Sketch_GearProfile")
sketch_gear.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_gear.ConstrainToCurrentPlane = True
sketch_gear.MapMode = "FlatFace"
sketch_gear.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Helper to add geometry to sketch
def add_line(sk, p1, p2, is_constraint=False):
    sk.addGeometry(Part.LineSegment(p1, p2), is_constraint)

def add_circle(sk, center, radius, is_constraint=False):
    sk.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constraint)

# 1. Base Circle (Pitch Diameter)
add_circle(sketch_gear, App.Vector(0, 0, 0), PITCH_DIAMETER / 2.0)

# 2. Outer Circle (Tip Diameter)
add_circle(sketch_gear, App.Vector(0, 0, 0), OUTER_DIAMETER / 2.0)

# 3. Root Circle (Bottom Diameter)
add_circle(sketch_gear, App.Vector(0, 0, 0), ROOT_DIAMETER / 2.0)

# 4. Base Circle (for involute generation)
add_circle(sketch_gear, App.Vector(0, 0, 0), BASE_DIAMETER / 2.0)

# 5. Tooth Profile Generation
# We need to generate the involute curve. 
# In FreeCAD Sketcher, we can use a Point and a Line, or construct the curve mathematically.
# Since Sketcher doesn't natively support "Involute" constraint directly on a curve object in the same way CAD kernels do,
# we will construct the involute using a series of points or a specific geometric construction if available.
# However, the most robust way in FreeCAD scripting for an exact involute is to create a curve.
# But Sketcher::SketchObject primarily handles Lines, Circles, Arcs, Points.
# To get a perfect involute in Sketcher, we often use a "Point" and a "Line" with a specific constraint, 
# OR we generate the curve in Part and project it, but that breaks the "Sketcher" constraint logic slightly.
# 
# Alternative: Use the "Point" and "Line" method to define the involute mathematically via a script-generated curve?
# No, Sketcher constraints are geometric.
# 
# Best approach for FreeCAD 1.1 Scripting: 
# Create a curve in Part, then add it to the sketch? No, Sketcher::SketchObject doesn't accept Part::Curve directly as geometry in older versions, 
# but in 1.1 it might. Let's try to construct the involute using the standard parametric definition:
# x = r_b * (cos(t) + t*sin(t))
# y = r_b * (sin(t) - t*cos(t))
# where r_b is base radius.
# We can create a Part::Curve, then add it to the sketch.
# Actually, the most reliable way to get a smooth involute in a sketch for gear generation is to use the "Point" and "Line" 
# to define the tangent, but that's complex.
# 
# Let's use the `Part::Curve` approach. We create the curve in memory, then add it to the sketch.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
curve_points = []
for i in range(num_points):
    t = (i / num_points) * math.pi
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    curve_points.append(App.Vector(x, y, 0))

# Create the curve
involute_curve = Part.makeCurve(curve_points)

# Add the curve to the sketch
sketch_gear.addGeometry(involute_curve, False)

# --- Constraints for Gear Teeth ---
# We need to define the tooth profile using the involute curve and circular arcs.
# Strategy:
# 1. Define the involute curve (done).
# 2. Define the tip circle arc (part of outer circle).
# 3. Define the root circle arc (part of root circle).
# 4. Connect them with lines (fillets or straight lines depending on gear type, usually straight for standard gears).
#    Standard spur gears have straight flanks (involute) and rounded roots (dedendum).
#    The prompt implies standard ISO gears.
#    The profile consists of:
#    - Involute from Base Circle to Tip Circle.
#    - Root fillet (usually a circular arc tangent to involute and root circle).
#    - Root circle arc.
#    - Symmetry.

# To make this editable and robust in a script:
# We will create a "Tooth" sketch that is symmetric.
# We will define the involute curve, the tip arc, and the root arc.
# Then we will use a "Mirror" or just draw the half-tooth and mirror it.
# However, Sketcher constraints are tricky with curves.
# Let's simplify: We will create the full tooth profile using the involute curve and circular arcs.
# We need to find the intersection of the involute and the tip circle to define the start of the tip arc.
# And the intersection of the involute and the root circle (or the fillet).

# Let's calculate the intersection of the involute and the tip circle.
# This is hard to do analytically in a script without a solver.
# Alternative: Use the "Point" constraint on the curve and the circle.
# We can add a Point on the involute curve and constrain it to the outer circle.
# But we need to know WHERE on the curve.
# 
# Let's try a different approach often used in FreeCAD gear scripts:
# Create the involute curve.
# Create a Point on the curve.
# Constrain the Point to the Outer Circle.
# Constrain the Point to the Base Circle? No.
# 
# Actually, the most robust way for a scriptable, editable gear in FreeCAD is to use the `PartDesign::Pad` with a `Part::Part` shape if the sketch is too complex.
# BUT the requirement is "PartDesign features... driven by named document objects".
# So we must use Sketcher.
# 
# Let's construct the tooth profile explicitly:
# 1. Involute Curve (from base circle to tip circle).
# 2. Tip Arc (from involute intersection to next tooth).
# 3. Root Arc (from involute intersection to next tooth).
# 4. Fillet at the root.
# 
# Since we can't easily solve for the intersection point analytically in a simple script without a loop,
# we will approximate the intersection by finding the point on the involute that is closest to the tip circle radius.
# Or, we can use the "Point" on the curve and constrain it to the circle.
# Let's add a Point on the involute curve.
# We need to find the parameter 't' where radius = OUTER_DIAMETER/2.
# r(t) = r_b * sqrt( (cos t + t sin t)^2 + (sin t - t cos t)^2 )
# r(t) = r_b * sqrt( cos^2 + t^2 sin^2 + 2t sin cos + sin^2 + t^2 cos^2 - 2t sin cos )
# r(t) = r_b * sqrt( 1 + t^2 )
# So, r(t) = r_b * sqrt(1 + t^2)
# We need r(t) = R_tip.
# R_tip / r_b = sqrt(1 + t^2)
# (R_tip / r_b)^2 = 1 + t^2
# t = sqrt( (R_tip/r_b)^2 - 1 )

R_tip = OUTER_DIAMETER / 2.0
R_base = BASE_DIAMETER / 2.0
t_tip = math.sqrt((R_tip / R_base)**2 - 1)

# Calculate the point on the involute at t_tip
x_tip = R_base * (math.cos(t_tip) + t_tip * math.sin(t_tip))
y_tip = R_base * (math.sin(t_tip) - t_tip * math.cos(t_tip))
# This point should be exactly on the tip circle.

# Now, let's define the tooth profile.
# We need to generate the curve for the tooth.
# The tooth is symmetric around the X-axis (if we align the tooth center to X).
# Let's create a sketch that defines ONE tooth (half tooth) and then mirror it?
# Or define the full tooth.
# Let's define the full tooth profile.
# We need the involute curve from t=0 to t=t_tip.
# We also need the root fillet.
# The root fillet is usually tangent to the involute and the root circle.
# Let's assume a standard root fillet radius.
# Root fillet radius is often approx 0.38 * module or similar.
# Let's use a standard value: r_fillet = 0.38 * GEAR_MODULE.
# But we need to ensure it's tangent.
# 
# To keep it simple and editable, we will:
# 1. Create the involute curve (full length).
# 2. Create a Point on the involute at t_tip.
# 3. Constrain this Point to the Outer Circle.
# 4. Create a Point on the involute at the root fillet start.
#    This is complex.
# 
# SIMPLIFIED APPROACH FOR SCRIPTING:
# We will create the involute curve.
# We will create a Point on the curve at the tip.
# We will create a Point on the curve at the root (approximate).
# We will create a circular arc for the root fillet.
# We will create a circular arc for the tip (part of outer circle).
# We will create a circular arc for the root (part of root circle).
# We will connect them with lines (tangency constraints).
# 
# Let's try to construct the profile using the "Point" and "Line" method for the involute?
# No, the curve is already there.
# 
# Let's create the profile by combining:
# - Involute Curve (from base to tip)
# - Tip Arc (from tip point to next tooth start)
# - Root Arc (from root point to next tooth start)
# - Root Fillet (connecting involute to root circle)
# 
# This is getting very complex for a single script without a GUI.
# Let's use a known trick: 
# Create the involute curve.
# Create a Point on the curve at the tip.
# Constrain Point to Outer Circle.
# Create a Point on the curve at the root (where it meets the fillet).
# Constrain Point to Root Circle? No, the fillet is tangent.
# 
# Let's use a simpler geometric approximation that is standard in FreeCAD gear scripts:
# 1. Create the involute curve.
# 2. Create a Point on the curve at the tip.
# 3. Constrain Point to Outer Circle.
# 4. Create a Point on the curve at the root (approximate intersection with root circle).
#    Actually, the involute intersects the root circle at a specific point.
#    Let's calculate t_root where r(t) = R_root.
#    t_root = sqrt( (R_root/R_base)^2 - 1 )
#    Calculate point.
# 5. Create a circular arc for the root fillet.
#    The fillet is tangent to the involute at the root point and tangent to the root circle.
#    This requires a specific radius.
#    Let's assume the fillet radius is such that it is tangent.
#    Or, simpler: Just use the root circle arc and the involute, and add a fillet between them.
#    But the fillet must be tangent to the involute.
# 
# Let's try a different strategy:
# Use the `Part::Gear` object? No, must be PartDesign.
# 
# Let's go with the "Point on Curve" method.
# 1. Create Involute Curve.
# 2. Create Point P_tip on curve at t_tip.
# 3. Constrain P_tip to Outer Circle.
# 4. Create Point P_root on curve at t_root.
# 5. Constrain P_root to Root Circle.
# 6. Create a Line from P_tip to P_root? No, the profile is the curve itself.
# 7. We need to close the loop.
#    The tooth profile is:
#    - Involute from P_root to P_tip.
#    - Tip Arc from P_tip to P_next_tip (symmetric).
#    - Root Arc from P_next_root to P_root (symmetric).
#    - Root Fillet connecting P_root to the root circle?
# 
# Actually, the standard gear tooth profile is:
# - Involute flank.
# - Tip circle arc.
# - Root circle arc.
# - Root fillet (connecting flank to root circle).
# 
# Let's create the profile as a closed loop of segments:
# 1. Involute curve (from P_root to P_tip).
# 2. Tip Arc (from P_tip to P_tip_mirror).
# 3. Involute curve (from P_tip_mirror to P_root_mirror).
# 4. Root Arc (from P_root_mirror to P_root).
# 5. Root Fillets (connecting P_root to P_root_mirror? No, the root circle arc connects them).
#    Wait, the root fillet connects the involute to the root circle.
