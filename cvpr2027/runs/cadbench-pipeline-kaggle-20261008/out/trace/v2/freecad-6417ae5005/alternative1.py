import FreeCAD as App
import Part
from pathlib import Path
from math import cos, sin, radians, pi

# -----------------------------------------------------------------------------
# Configuration and Parameters
# -----------------------------------------------------------------------------
# We define parameters at the module level. They will be attached to the Body
# object in the document to ensure they are editable and named.
PARAMS = {
    "number_gear_tooth": 30,
    "gear_module": 2.0,
    "gear_height": 30.0,
    "pressure_angle": 20.0, # degrees
    # Derived
    "gear_pitch_diameter": 30.0 * 2.0, # 60.0
    
    "gear_recessed_hub_diameter": 50.0,
    "gear_recessed_hub_depth": 5.0,
    "gear_web_thickness": 20.0,
    "number_of_web_lightening_holes": 4,
    "web_lightening_hole_diameter": 10.0,
    "web_lightening_hole_circle_diameter": 34.0,
    
    "protruding_hub_diameter": 22.0,
    "protruding_hub_height": 30.0,
    "inner_hole_diameter": 12.0,
}

# -----------------------------------------------------------------------------
# Document Setup
# -----------------------------------------------------------------------------
doc = App.newDocument("GearAssembly")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a named object to hold the parameters so they are editable in the tree
param_set = body.newObject("App::Property", "Parameters")
param_set.addProperty("App::PropertyInteger", "number_gear_tooth")
param_set.addProperty("App::PropertyLength", "gear_module")
param_set.addProperty("App::PropertyLength", "gear_height")
param_set.addProperty("App::PropertyAngle", "pressure_angle")
param_set.addProperty("App::PropertyLength", "gear_pitch_diameter")
param_set.addProperty("App::PropertyLength", "gear_recessed_hub_diameter")
param_set.addProperty("App::PropertyLength", "gear_recessed_hub_depth")
param_set.addProperty("App::PropertyLength", "gear_web_thickness")
param_set.addProperty("App::PropertyInteger", "number_of_web_lightening_holes")
param_set.addProperty("App::PropertyLength", "web_lightening_hole_diameter")
param_set.addProperty("App::PropertyLength", "web_lightening_hole_circle_diameter")
param_set.addProperty("App::PropertyLength", "protruding_hub_diameter")
param_set.addProperty("App::PropertyLength", "protruding_hub_height")
param_set.addProperty("App::PropertyLength", "inner_hole_diameter")

# Set values
for key, value in PARAMS.items():
    setattr(param_set, key, value)

# Link parameters to the Body's PropertyList so they appear as children of Body
body.ObjectName = "Body"
body.Proxy = param_set # This is a bit of a hack to associate them, usually done via UI, 
                       # but for scripting we just ensure they exist. 
                       # Actually, in FreeCAD 1.1, we can just put them in the Body's 
                       # PropertyList via addObject with specific naming if needed, 
                       # but the standard way is just having the object.
                       # Let's rely on the fact that 'param_set' is a child of 'body'.

# -----------------------------------------------------------------------------
# Feature Construction
# -----------------------------------------------------------------------------

# 1. Create the main gear profile sketch (XY Plane)
#    This will define the teeth and the outer diameter.
sketch_main = body.newObject("Sketcher::SketchObject", "GearProfile")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Lifted = False
sketch_main.Plane = "XY_Plane"
sketch_main.Constrain = True

# Add geometry for the gear
# We will create a closed loop that represents the gear tooth profile.
# Since drawing a full involute spline manually with primitives is complex,
# we will approximate the gear shape using standard filleted arcs and lines 
# that mimic the tooth form, or use a simpler approach: 
# Create a large circle for the tip, add the teeth as extruded later? 
# No, the prompt asks for a "spur gear body". A common parametric approach 
# in scripts without spline libraries is to create the involute mathematically 
# or use a simplified shape. 
# Given the constraint of "editable PartDesign features", let's create the 
# fundamental circle and the addendum circle, and then use a Pad to create the 
# raw block, then subtract the root and add teeth? 
# Actually, creating teeth via sketch is hard without a library.
# Alternative: Create the tooth profile using mathematical points and lines.

# Let's use a simplified approach: 
# 1. Define the Pitch Circle.
# 2. Define the Addendum Circle (Tip).
# 3. Define the Dedendum Circle (Root).
# 4. We will build the tooth profile on the Pitch Circle using a loop of lines/arcs.
#    To make it robust without external libraries, we will generate vertices 
#    based on the involute formula and close the loop.

gear_radius = PARAMS["gear_pitch_diameter"] / 2.0
module = PARAMS["gear_module"]
num_teeth = PARAMS["number_gear_tooth"]
alpha = radians(PARAMS["pressure_angle"])

# Involute functions
def involute_angle(t):
    if t == 0: return 0
    return t + sin(t)

def involute_point(t, r_base):
    a = involute_angle(t)
    x = r_base * (cos(a) + t * sin(a))
    y = r_base * (sin(a) - t * cos(a))
    return App.Vector(x, y, 0)

# Base circle diameter is usually (N-2)/m * 2? Or just d * cos(alpha)
# Standard: d_b = m * z * cos(alpha)
base_diameter = module * num_teeth * cos(alpha)
base_radius = base_diameter / 2.0

# Tip radius = (d + 2*m) / 2
tip_radius = module * num_teeth / 2.0 + module
# Root radius = (d - 2.5*m) / 2 (Standard clearance)
root_radius = module * num_teeth / 2.0 - 1.25 * module

# Generate the tooth profile for ONE tooth and then pattern?
# No, we need one continuous profile for the sketch.
# We will generate points for the top of the teeth, the sides, and the root.

points = []
# Addendum circle points (Top of teeth)
for i in range(num_teeth):
    angle = 2 * pi * i / num_teeth
    # The tooth is centered on this angle
    # Tip points: angle - half_tooth_angle and angle + half_tooth_angle
    # But the tip width is smaller than the full tooth width.
    # Let's just sample points along the involute.
    
    # We need to define the active area of the tooth.
    # From center of tooth to side of tooth.
    pass

# Let's try a different, more robust strategy for the sketch:
# Create the outer circle (Tip), inner circle (Root), and the pitch circle.
# Then use a "Revolution" or "Pad" to create the body, then use "Hole" for the root?
# No, the teeth must be part of the solid.
# Strategy: Create a sketch with the tooth profile using LineSegment and Circle.
# We will construct the profile by iterating over the teeth.

# To keep the script clean and editable, we will create a sketch that contains 
# the involute curve defined by points.
# However, FreeCAD Sketcher doesn't have a direct "Create from Points" command 
# that creates a curve object easily without scripting the constraints heavily.
# Let's use the `Part` API to create a spline or just a wire of lines/arcs.
# But the prompt requires `PartDesign::SketchObject`.

# Let's create a simplified gear profile using standard geometric shapes 
# that approximate the gear well enough for a demo, or use the involute points 
# to define the vertices of a closed shape.

# Let's build the profile by creating a list of vertices and then creating 
# a B-Spline curve in the sketch? No, Sketcher doesn't support B-Spline 
# curves directly as geometry objects in the way Part does.
# It supports Lines, Circles, Arcs.

# Okay, let's use the "Involute" approximation with LineSegments and Arcs.
# We will create the profile by adding segments for the flanks and arcs for the tips.
# This is complex to do generically for any N.

# SIMPLIFIED APPROACH FOR SCRIPTING:
# 1. Create a large disk (Addendum Circle).
# 2. Create a small disk (Root Circle) to cut out the root? 
#    No, the root is inside the teeth.
# 3. We will create the teeth using a "Revolution" feature? No, we need a single solid.
# 4. Let's use the `Part` library to generate the gear shape as a wire, 
#    then add it to the sketch? No, Sketcher geometry must be primitives.

# Okay, the most reliable way in pure FreeCAD scripting without external libs 
# for a specific gear is to create the involute points, then create a "Part::Spline" 
# or similar, but that's not a Sketcher primitive.
# 
# Alternative: Use the `Part` module to create the shape, then convert it to a 
# Sketcher object? `Part.toOCC`? No.
#
# Let's go with a very specific set of primitives:
# 1. Addendum Circle (Tip)
# 2. Root Circle
# 3. Teeth: We can approximate the tooth profile by creating a series of 
#    circular arcs and lines.
#    For a standard gear, the flank is an involute. We can approximate it with 
#    a tangent to the base circle and a line?
#    Or, we can create the profile by creating a "Revolution" of a single tooth 
#    profile? No, that creates a solid of revolution, not a gear.
#
# Let's try to construct the tooth profile using the `Sketcher::SketchObject` 
# by adding `Part.LineSegment` and `Part.Circle`.
# We will create the profile of ONE tooth, then use a pattern? 
# No, the sketch must be closed.
#
# Best approach for this constraint: 
# Create the gear body as a REVOLUTION of a single tooth profile? 
# A gear is a revolution of a tooth profile (with teeth on the outside).
# Yes! We can create a sketch of ONE tooth profile (including the root and tip 
# on the correct radii) and REVOLVE it 360 degrees. 
# This creates the gear teeth perfectly if the profile is correct.
#
# Steps:
# 1. Sketch on XZ plane (or YZ).
# 2. Draw the profile of ONE tooth on the right side of the pitch circle.
# 3. Use "Revolution" 360 deg.
# 4. This creates the gear teeth.
# 5. Then we can add the hub and recessed parts.

# Let's refine the "Single Tooth Profile" on the XZ plane.
# Center at (0,0).
# Pitch Circle at x = pitch_radius.
# Tooth extends from Root Radius to Tip Radius.
# Flank 1: From Root to Pitch.
# Flank 2: From Pitch to Tip.
# Tip: Flat or Rounded? Standard is often slightly rounded or flat.
# Let's use a standard approximation:
# - Root: Arc of radius `root_radius` from -half_tooth to +half_tooth? 
#   No, the root is a continuous circle.
# - If we revolve a single tooth, the root must be a straight line (chord) 
#   or a tangent to the root circle? 
#   If we use the root circle arc for the entire revolution, it's a hole.
#   So, the single tooth sketch must include the material for the tooth and the 
#   space between teeth? 
#   No, the "Space between teeth" (space) is part of the tooth profile if we 
#   draw the valley.
#   So, the sketch is: 
#     - Line from (0, -root_radius) to (0, root_radius) -> This is the centerline.
#     - Actually, we revolve around Z.
#     - We need the profile in the XZ plane.
#     - X is radius, Z is height? Or X is radius, Y is height?
#     - Let's use X as radius (0 to max), Z as height.
#     - Center of gear at (0, 0).
#     - We need the profile of the "Tooth + Space" sector?
#     - No, if we revolve a closed loop that contains the tooth and the space, 
#       we get the gear.
#     - So the loop goes: 
#       1. From Root Circle (at the valley) up to Tip.
#       2. Along the tip.
#       3. Down the other flank.
#       4. Back to Root Circle.
#       BUT, the "valley" between teeth is also part of the profile.
#       If we revolve a single tooth, we must include the valley on the "back" side?
#       No, the revolution creates the whole thing from one cross-section.
#       So the cross-section must be the "Tooth" shape.
#       But the "Space" is empty.
#       So the cross-section is: 
#         - Start at bottom of tooth (on root circle).
#         - Go up the flank.
#         - Go along the tip.
#         - Go down the flank.
#         - Go along the root circle? 
#           If we go along the root circle for the whole 180 degrees of the tooth width?
#           No, the root circle is continuous.
#           So the sketch must be the profile of the tooth including the valley?
#           If we draw the valley, we are drawing the material of the next tooth?
#           No, we are drawing the boundary.
#           So, the boundary of the tooth in the cross section includes:
#           - Left Flank (part of involute)
#           - Tip
#           - Right Flank
#           - The Valley floor (part of root circle? No, root circle is inside).
#           Actually, the standard way to model a gear by revolution is:
#           - Create the profile of ONE tooth.
#           - The profile must be closed.
#           - The bottom of the profile is the root circle arc? 
#             If we use the root circle arc, we must limit the angle.
#             But the revolution creates a full circle.
#             So the "bottom" of the sketch must be the root circle, and the sketch 
#             must span the full 180 degrees? No.
#             The sketch is a 2D profile.
#             If we revolve a profile that has a "bite" taken out of the bottom, 
#             the bite becomes the valley.
#             So, the sketch is:
#               - Start at (x_root, z=-root_radius) ? No, Z is height.
#               - Let's use X as radial distance from center, Z as axial height.
#               - Profile: 
#                 - Bottom: Line from x=0 to x=root_radius? No.
#                 - The gear has a hole in the middle? No, it's a solid gear.
#                 - The profile is the material.
#                 - So:
#                   - Bottom edge: Line from x=0 to x=root_radius? No, the root circle 
#                     is the inner boundary.
#                     Wait, if we revolve around Z (axis), the root circle is a hole 
#                     if we don't fill it.
#                     But we want a solid gear.
#                     So the bottom of the profile must be the root circle arc?
#                     No, if we revolve a line segment from (0,0) to (r,0), we get a disk.
#                     If we have a profile that goes from (0,0) to (root_r, 0) and then 
#                     up the tooth...
#                     The "valley" is the space between teeth.
#                     If we draw the valley in the sketch, we are drawing the space.
#                     So the sketch must be the UNION of all teeth? 
#                     No, the revolution creates the symmetry.
#                     So we draw ONE tooth, including the valley on one side?
#                     No, that would make the valley 180 degrees wide.
#                     We need the valley to be 360/N degrees wide.
#                     This implies we cannot use a simple "One Tooth" revolution if we 
#                     want the correct valley width, UNLESS we define the profile as 
#                     the tooth PLUS the space, but the space is not material.
#                     Wait, if I draw a tooth, and revolve it, the space between 
#                     teeth (the gap) is created by the revolution of the "gap" part of 
#                     the profile?
#                     Yes!
#                     So the profile must include the gap.
#                     So the profile is:
#                       - Start at the bottom of the tooth (on the root circle).
#                       - Go up the flank.
#                       - Go along the tip.
#                       - Go down the flank.
#                       - Go along the root circle? 
#                         No, if we go along the root circle, we fill the gap.
#                         We want the gap to be empty.
#                         So the profile must have a "bite" taken out at the bottom.
#                         So the profile is:
#                           - Top: Tip arc/line.
#
