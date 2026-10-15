"""
FreeCAD 1.1 Script: Spur Gear Stock Generator
Generates a parametric spur gear stock using PartDesign features.
"""

import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from the task description
PARAMS = {
    "pressure_angle": 20.0,          # degrees
    "diametral_pitch": 16.0,         # teeth per inch
    "number_of_teeth": 24,           # count
    "pitch_diameter": 38.1,          # mm
    "outer_diameter": 41.402,        # mm
    "overall_length": 304.8,         # mm
    "gear_module": 1.5875,           # mm (25.4 / 16)
}

# Calculate remaining geometric parameters needed for the sketch
# Circular Pitch (mm) = PI / Diametral Pitch
circular_pitch = math.pi / PARAMS["diametral_pitch"]

# Base Diameter = Pitch Diameter * cos(Pressure Angle)
base_diameter = PARAMS["pitch_diameter"] * math.cos(math.radians(PARAMS["pressure_angle"]))
base_radius = base_diameter / 2.0

# Addendum (height of tooth above pitch circle)
# For standard gears: Addendum = 1 / Diametral Pitch
addendum = 1.0 / PARAMS["diametral_pitch"]
# Root Diameter = Pitch Diameter - 2 * Addendum * sin(Pressure Angle)
# (Standard formula: d_f = (N - 2.5)/P_d, but we will calculate involute explicitly for precision)
# Let's stick to the explicit diameter constraints provided in the prompt where possible,
# and calculate the root radius based on standard AGMA clearance or the provided outer diameter context.
# The prompt gives Outer Diameter. Let's calculate the Root Diameter.
# Standard: Root Dia = Pitch Dia - 2 * Addendum
# However, to match the specific "stock" look, we often cut slightly deeper.
# Let's define the Root Radius based on standard calculation:
# d_f = (number_of_teeth - 2.5) / diametral_pitch
root_diameter = (PARAMS["number_of_teeth"] - 2.5) / PARAMS["diametral_pitch"]

# --- Initialize Document ---
doc = App.newDocument("SpurGearStock")

# --- Create Body ---
body = doc.addObject("PartDesign::Body", "GearBody")
doc.addObject(body)

# --- Create Parameters Set ---
# We will use expressions for all driven dimensions to make them editable
param_set = body.newObject("App::VarSet", "GearParameters")
param_set.addProperty("App::PropertyLength", "pitchDiameter", "Dimensions", "Pitch Diameter")
param_set.pitchDiameter = PARAMS["pitch_diameter"]

param_set.addProperty("App::PropertyLength", "outerDiameter", "Dimensions", "Outer Diameter")
param_set.outerDiameter = PARAMS["outer_diameter"]

param_set.addProperty("App::PropertyLength", "overallLength", "Dimensions", "Stock Length")
param_set.overallLength = PARAMS["overall_length"]

param_set.addProperty("App::PropertyLength", "module", "Dimensions", "Module")
param_set.module = PARAMS["gear_module"]

param_set.addProperty("App::PropertyAngle", "pressureAngle", "Dimensions", "Pressure Angle (deg)")
param_set.pressureAngle = PARAMS["pressure_angle"]

param_set.addProperty("App::PropertyInteger", "numTeeth", "Dimensions", "Number of Teeth")
param_set.numTeeth = PARAMS["number_of_teeth"]

param_set.addProperty("App::PropertyLength", "baseRadius", "Dimensions", "Calculated Base Radius")
# We will set this via expression in the sketch or feature, but let's store the calc logic here
# Actually, better to just define the sketch geometry using these parameters directly.

# --- Create Main Profile Sketch (RHS - Right Half Side) ---
# We will sketch only half the tooth profile (from center line to outer edge) 
# and then mirror it. This simplifies the involute calculation.
sketch_base = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.ConstraintType = "XY_Plane"
sketch_base.Pivot = "XY_Plane"
sketch_base.UpdateShape()

# We need to construct the involute curve.
# Since FreeCAD's standard sketcher does not have a built-in "Involute" tool,
# we will use a polyline approximation or a circle with a specific constraint setup.
# However, the most robust way in a script without external libraries is to define the 
# involute points mathematically and add them as vertices if the sketcher supports vertices,
# OR use a circle that is tangent to the base circle and create the envelope? 
# No, that's for generating the curve itself.
# Best approach for PartDesign: Add vertices for the involute profile.

# Involute Equation:
# x = r_b * (cos(t) + t*sin(t))
# y = r_b * (sin(t) - t*cos(t))
# where t is the involute function parameter (radians)
# We need points from the base circle (t=0) up to the outer circle radius.

r_base = PARAMS["baseRadius"]
r_outer = PARAMS["outerDiameter"] / 2.0

# Calculate the angle at the outer radius
# r = r_b * sqrt(1 + t^2) => t = sqrt((r/r_b)^2 - 1)
# t_outer = sqrt((r_outer / r_base)^2 - 1)

t_max = math.sqrt((r_outer / r_base)**2 - 1)

# Resolution for the polyline (number of points to approximate the curve)
# Higher resolution = smoother but slower. 50 points is usually enough for visual inspection.
num_points = 60 
step = t_max / num_points

sketch_base.AddLine(App.Vector(0, 0, 0), App.Vector(10, 0, 0)) # Placeholder to ensure sketch exists
# We will clear lines and add vertices/lines later, but Sketcher::SketchObject works best with Lines/Vertices.
# Let's add the base center point and the outer point, and a line connecting them (centerline).
# Actually, let's add the involute curve as a series of lines.

# Helper to add a line segment to the sketch
def add_sketch_line(obj, p1, p2):
    obj.addGeometry(Part.LineSegment(p1, p2), False)

# 1. Center Point (Origin)
# 2. Base Circle Arc? No, let's just draw the profile lines.
# Profile starts at Base Radius (t=0) and goes to Outer Radius.
# At t=0, x = r_b, y = 0.
start_point = App.Vector(r_base, 0, 0)
end_point = App.Vector(0, 0, 0) # We need to go to the outer edge. 
# Wait, the involute starts at the base circle. 
# At t=0, x=r_base, y=0.
# As t increases, x and y change.
# The profile is symmetric about the X-axis in the sketch if we orient the gear such that the tooth is along X?
# Let's orient the tooth such that the centerline of the tooth is the X-axis.
# Then the profile goes from (0, r_base) to (r_outer, 0) ? 
# Let's re-orient:
# Let the tooth centerline be the X-axis.
# The profile starts at the base circle (x=r_base, y=0) and goes OUTWARDS along the Y direction?
# No, the involute unwinds from the base circle.
# If the tooth centerline is X, the contact point with the mating gear is on the line of action.
# Let's place the base circle at origin. The tooth centerline is the X-axis.
# The involute starts at (r_base, 0) and curves outwards towards larger Y as X increases?
# Actually, standard parameterization:
# x = r_b * (cos(t) + t*sin(t))
# y = r_b * (sin(t) - t*cos(t))
# If we start at t=0 -> (r_b, 0).
# If we want the tooth to be symmetric around the X-axis, we need two profiles: +Y and -Y.
# But the X coordinate increases as t increases.
# Let's generate the points for t from 0 to t_max.
# We will create a sketch containing:
# 1. A line from (0,0) to (r_outer, 0) representing the centerline.
# 2. The involute curve from (r_base, 0) to (x_max, y_max).
# 3. A line from (x_max, y_max) back to (x_max, -y_max)? No, the tooth tip is circular.
# So we need:
# - Centerline (0,0) to (r_outer, 0)
# - Involute from (r_base, 0) to the point on the outer circle.
# - Line from that point to the point on the outer circle with same X? No.
# The tooth tip is an arc of radius r_outer.
# So we need:
# 1. Centerline.
# 2. Involute curve.
# 3. Tangent line from the end of the involute to the outer circle? 
#    Actually, the involute meets the outer circle tangentially.
# 4. Line from the end of the involute to the centerline? No, the tooth tip is rounded.
#    We need to close the profile: Center -> Base -> Involute -> Outer Circle -> Center?
#    No, the profile is: Centerline -> Base Radius -> Involute -> Outer Circle Tip -> Centerline?
#    Let's simplify:
#    Profile = Centerline (0,0 to r_outer) + Involute (from base to outer) + Outer Circle Arc?
#    We can't easily draw an arc in a sketch without a circle constraint if we don't know the center of the arc relative to the sketch plane origin.
#    BUT, the gear teeth are circular at the tip. The center of that circle is the gear axis (0,0).
#    So we can draw a circle centered at (0,0) with radius r_outer.
#    Then we just need the involute line and the centerline.
#    The profile is bounded by: X-axis (centerline), Base Circle (implicitly handled by start of involute), Involute, and Outer Circle.
#    Wait, the tooth material is INSIDE the outer circle and OUTSIDE the root circle.
#    We are building the "Stock".
#    The stock is the union of the blank cylinder and the teeth? 
#    No, the stock IS the gear with teeth.
#    So we need the profile to include the root circle too?
#    The prompt asks for "external involute teeth".
#    Usually, a gear blank includes the root fillet.
#    Let's assume a standard root radius approximation or just cut the root circle.
#    Let's calculate the root radius point.
#    The root circle is r_root = root_diameter / 2.
#    We need to find the t_value where the involute radius is r_root.
#    t_root = sqrt((r_root / r_base)^2 - 1)
#    
#    So the profile consists of:
#    1. Centerline (0,0) to (r_outer, 0).
#    2. Outer Circle (Radius r_outer, Center 0,0).
#    3. Root Circle (Radius r_root, Center 0,0).
#    4. Involute segment from r_base to r_root? No, the tooth starts at the root.
#       The involute starts at the base circle.
#       The region between root and base is "fillet" or "land"?
#       In a stock model, we usually just extrude the full profile from root to outer.
#       The profile should be:
#       - Start at Centerline (0,0).
#       - Go to Root Circle intersection with centerline? No, the root is curved.
#       - Let's approximate the root with a circle.
#       - Profile: Centerline -> Outer Circle -> Involute -> Base Circle -> Centerline?
#       - No, the tooth is the protrusion.
#       - We want the shape that, when revolved, makes the gear.
#       - We need the profile of ONE TOOTH (half tooth, mirrored).
#       - Shape: Centerline -> Base Circle (start of involute) -> Involute Curve -> Outer Circle (Tip) -> Centerline?
#       - Wait, the tooth tip is the outer circle. The tooth base is the root circle.
#       - The involute connects the base circle to the... pressure line?
#       - Standard gear profile:
#         - From Root Circle to Base Circle: Fillet (circular).
#         - From Base Circle to Outer Circle: Involute.
#       - To simplify for a "stock" that looks like a gear, we can:
#         1. Draw the Centerline.
#         2. Draw the Outer Circle.
#         3. Draw the Root Circle.
#         4. Draw the Involute curve from Base Circle to Outer Circle.
#         5. Draw a line from the end of the involute to the Root Circle?
#         6. Draw the Root Circle arc?
#         
#    Let's construct the sketch geometry explicitly:
#    - Line 1: Centerline (0,0) to (0, r_outer). (Using Y as the radial axis for the tooth)
#    - Circle 1: Center (0,0), Radius r_outer. (Top of tooth)
#    - Circle 2: Center (0,0), Radius r_root. (Bottom of tooth)
#    - Involute Curve: From (r_base, 0) to (x_tip, y_tip) where it hits the outer circle.
#      Wait, if we use Y as the radial axis, the centerline is Y-axis.
#      Involute starts at Base Circle (radius r_base).
#      The profile is bounded by Y-axis (centerline), Outer Circle (radius r_outer), and the Involute.
#      But what about the root? The stock must include the root circle area.
#      So the profile is: Y-axis (0 to r_outer) + Outer Circle Arc + Involute + Line from Involute end to Root Circle?
#      Actually, the simplest "Gear Stock" is often defined as:
#      - Revolved Body of the Pitch Diameter cylinder.
#      - Plus teeth added?
#      - Or one solid with the full tooth profile.
#      
#    Let's build the full tooth profile (half tooth) as a closed loop:
#    Points:
#    A: (0, r_root) -> On Root Circle, on Centerline.
#    B: (0, r_outer) -> On Outer Circle, on Centerline.
#    C: Point on Outer Circle where it meets the involute.
#    D: Point on Involute at Base Circle (r_base, 0).
#    E: Point on Root Circle where it meets the involute? 
#       Usually, the involute starts at the base circle. Below the base circle is a fillet.
#       For a "stock" model, we can approximate the fillet with a straight line or a smaller circle arc.
#       Let's use the Root Circle arc from the involute start point (if it hits the root) or just connect the involute start to the root circle.
#       Actually, the Base Circle is usually larger than the Root Circle.
#       So the sequence is: Root Circle -> Fillet -> Base Circle -> Involute -> Outer Circle.
#       To keep it simple and editable:
#       We will define the profile as:
#       1. Line from (0, r_root) to (0, r_outer). (Centerline)
#       2. Circle Arc of Outer Circle from (0, r_outer) to the involute endpoint.
#       3. Involute curve from involute endpoint to (r_base, 0).
#       4. Line from (r_base, 0) to (0, r_root)? No, that cuts the corner.
#       5. We need the Root Circle arc.
#       Let's find the intersection of the Root Circle and the Involute? No, the involute doesn't start at the root.
#       We will approximate the bottom of the tooth with the Root Circle arc and a tangent line or fillet.
#       Let's just create a polyline that approximates the Root-Base transition and then the Involute.
#       OR, simpler: 
#       Create a shape that is the union of:
#       - A cylinder of radius r_pitch.
#       - Teeth generated by revolving the profile.
#       
#    Let's try the "Profile" approach again, as it's more precise.
#    Profile Loop:
#    1. Centerline segment: (0, 0) to (0, r_outer).
#    2. Outer Circle Arc: From (0, r_outer) to point P_outer on the involute.
#    3. Involute Curve: From P_outer to P_base (r_base, 0).
#    4. Line Segment: From P_base to (0, r_root)? No, that's not right.
#    5. We need to connect P_base to the Root Circle.
#       Let's assume the fillet is a circle of radius r_fillet.
#       Or, we can just use the Root Circle and a line from the Root Circle to the Base Circle?
#       Let's calculate the point on the Root Circle that is "aligned" with the tooth.
#       Actually, the most robust way for a script is to generate the vertices for the entire tooth profile
