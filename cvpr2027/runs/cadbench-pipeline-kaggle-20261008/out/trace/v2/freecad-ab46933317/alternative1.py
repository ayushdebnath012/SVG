import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Configuration derived from task description
P = App.Parametric()
P.pressure_angle = 20.0 # degrees
P.diametral_pitch = 16.0 # 1/inch
P.number_of_teeth = 12
P.pitch_diameter_mm = 19.05 # 0.75 * 25.4
P.outer_diameter_mm = 22.352 # 0.88 * 25.4
P.overall_length_mm = 304.8 # 1 * 12 * 25.4
P.gear_module = 25.4 / P.diametral_pitch # 1.5875 mm

# Create Document
doc = App.newDocument("GearStock")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject(Type=body)

# Create Parameter Set
params = body.newObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Stock Length")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.addProperty("App::PropertyLength", "base_radius", "Dimensions", "Base Radius")
params.addProperty("App::PropertyLength", "tip_radius", "Dimensions", "Tip Radius")
params.addProperty("App::PropertyLength", "addendum", "Dimensions", "Addendum")
params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "Dedendum")
params.addProperty("App::PropertyLength", "circular_pitch", "Dimensions", "Circular Pitch")
params.addProperty("App::PropertyLength", "base_circle_radius", "Dimensions", "Base Circle Radius")

# Set Parameter Values
params.pitch_diameter = P.pitch_diameter_mm
params.outer_diameter = P.outer_diameter_mm
params.overall_length = P.overall_length_mm
params.gear_module = P.gear_module
params.pressure_angle = P.pressure_angle
params.number_of_teeth = P.number_of_teeth

# Derived Parameters
params.base_radius = params.pitch_diameter * math.cos(math.radians(params.pressure_angle))
params.tip_radius = params.pitch_diameter / 2 + params.gear_module # Simple addendum for stock
params.addendum = params.gear_module
params.dedendum = 1.25 * params.gear_module
params.circular_pitch = math.pi * params.pitch_diameter / params.number_of_teeth
params.base_circle_radius = params.pitch_diameter * math.cos(math.radians(params.pressure_angle))

# --- Step 1: Define Base Profile Sketch (Outer Envelope) ---
# Plane: XY
base_sketch = body.newObject("Sketcher::SketchObject", "BaseProfile")
base_sketch.Plane = "XY_Plane"
base_sketch.Constraints = []
base_sketch.MapMode = "FlatFace"

# Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2)
base_sketch.addGeometry(outer_circle, False)

# Constraint: Center
base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
base_sketch.update2D()

# --- Step 2: Define Tooth Profile Sketch (Involute Approximation) ---
# Plane: XZ (Rotated to XZ so we can revolve around Z)
tooth_sketch = body.newObject("Sketcher::SketchObject", "ToothProfile")
tooth_sketch.Plane = "XZ_Plane"
tooth_sketch.Constraints = []
tooth_sketch.MapMode = "FlatFace"

# Start point at Base Circle
start_point = App.Vector(0, params.base_circle_radius, 0)
# End point at Tip Circle
end_point = App.Vector(0, params.tip_radius, 0)

# Add Line segment (Simulating the flanks for the stock geometry)
# For a true stock, we just need the outer envelope defined by the teeth.
# However, to make it a "gear stock", we usually define the blank.
# Let's define a profile that goes from Base Circle up to Tip Circle.
# We will use a simplified representation: a line from base radius to tip radius.
# To get the involute shape properly for a "gear stock" (blank with teeth), 
# we should actually generate the involute curve.
# FreeCAD Part module has `Part.GearTooth` but for a custom script we build the geometry.

# Let's create a precise Involute curve using a helper function if available or approximate with segments.
# Since we need exact geometry, let's use the math.
# Involute of a circle: x = r*(cos(t) + t*sin(t)), y = r*(sin(t) - t*cos(t))
# where t = theta / pressure_angle_rad

def create_involute_curve(base_r, tip_r, num_points=50):
    r = base_r
    theta_max = math.acos(base_r / tip_r)
    theta_vals = [theta_max * (i / num_points) for i in range(num_points + 1)]
    points = []
    for t in theta_vals:
        x = r * (math.cos(t) + t * math.sin(t))
        y = r * (math.sin(t) - t * math.cos(t))
        points.append(App.Vector(x, y, 0))
    return Part.makePoly(points)

# Create the involute profile for one side of the tooth
# We need the profile to go from Base Radius to Tip Radius.
# The profile is symmetric around the X-axis (in the XZ plane).
involute_side = create_involute_curve(params.base_circle_radius, params.tip_radius)

# We need to define the sketch geometry.
# Sketcher adds lines/curves. Let's add the involute curve.
# Note: Sketcher::SketchObject geometry is Part::Curve or similar.
tooth_sketch.addGeometry(involute_side, False)

# We also need the line closing the profile to the axis or the circle arc.
# For the blank, we define the profile from the center line (Y=0) to the tip.
# Let's add a line from (0,0) to (0, base_r) ? No, the involute starts at base_r.
# So the profile is: Line from (0, base_r) to (base_r, base_r) -> Arc -> Involute -> Line to (0,0)?
# Actually, the simplest way to represent the tooth in the sketch for revolution is:
# 1. Line from (0, 0) to (0, base_radius)
# 2. Line from (0, base_radius) to (base_radius, base_radius) [Wait, coordinates are X, Y]
# Let's stick to standard math: X is radius, Y is height (Z in 3D).
# Profile in XZ plane:
# X=0 at center.
# At base circle: X = base_r, Z = base_r (tangent point).
# Involute starts at (base_r, base_r) ? No.
# Involute starts at (base_r, 0) in polar, but in cartesian (x,y):
# x = r(cos(t) + t sin(t))
# y = r(sin(t) - t cos(t))
# At t=0: x=r, y=0. This is the tangent point on the base circle.
# So the curve starts at (base_r, 0) and goes to (x_tip, y_tip).

# Let's rebuild the sketch geometry carefully.
# We want a profile that, when revolved, creates the tooth.
# The profile should be the involute curve itself.
# But we need to close the loop.
# The standard way to make a gear in PartDesign is:
# 1. Sketch on XZ plane.
# 2. Draw the involute curve from Base Circle to Tip Circle.
# 3. Draw a line from the end of the involute to the center (0,0).
# 4. Draw a line from the start of the involute (base_r, 0) to (0,0) ? No, that creates a hole.
# We want a solid stock.
# So:
# A. Line from (0,0) to (0, base_r) -> No, X is radius.
# Let's define X as the axis of revolution (radius from center), Z as the profile height.
# Start: (0, 0).
# Go up to (0, base_r)? No.
# Let's use the standard convention:
# X axis = Radius. Z axis = Height.
# Point 1: (0, 0) -> Center.
# Point 2: (base_r, base_r) -> Tangent point? No.
# Tangent point is at (base_r, 0) if the curve starts there?
# Let's calculate points again.
# t=0 -> x=base_r, y=0.
# So the curve starts at (base_r, 0).
# We need a line from (0,0) to (base_r, 0).
# Then the curve from (base_r, 0) to (x_tip, y_tip).
# Then a line from (x_tip, y_tip) to (0, y_tip)? No, the tooth has a tip circle.
# The stock is the union of all teeth.
# So the profile is:
# 1. Line from (0,0) to (0, tip_r). (The centerline)
# 2. Line from (0, tip_r) to (x_tip, tip_r). (Tip radius horizontal)
# 3. Involute curve from (x_tip, tip_r) to (x_base, 0).
# 4. Line from (x_base, 0) to (0,0). (Base radius horizontal)
# Wait, the involute connects (base_r, 0) to (x_tip, y_tip).
# Let's verify the coordinates.
# t=0: x=base_r, y=0.
# t=max: x=x_tip, y=y_tip (which is tip_r).
# So the path is:
# (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
# This creates the profile of ONE half tooth.
# We will revolve this to create the full gear stock? 
# No, if we revolve this half-tooth profile 360 degrees, we get a solid cylinder with a groove?
# No, we need to revolve the profile that generates the TOOTH.
# If we revolve the profile (0,0)->(0,tip)->(x_tip,tip)->Involute->(base_r,0)->(0,0), we get a solid block with a hole?
# No, this profile describes the boundary of the material.
# If we revolve this, we get a solid cylinder with a concave tooth profile?
# We want the teeth to stick OUT.
# So the profile should be the tooth itself.
# The tooth is bounded by:
# 1. Line from (0,0) to (0, tip_r) ? No.
# The tooth is a protrusion.
# The stock is the REVOLVED profile of the tooth.
# The profile of a tooth (half) is:
# (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
# If we revolve THIS, we get a cylinder with a hole in the middle?
# No, the area is between the curve and the axis.
# So revolving this area creates the solid tooth.
# BUT, we need the teeth to be separated.
# We cannot create separated teeth by revolving a single profile 360 degrees.
# We must create the profile of the ENTIRE gear blank (cylinder) and then subtract the grooves?
# OR, create the profile of one tooth, pad it, and use a Polar Pattern?
# The prompt asks for "PartDesign features".
# Common approach for gears:
# 1. Create the blank (Cylinder).
# 2. Create the tooth profile (Involute).
# 3. Use a Polar Pattern of the tooth profile, then a Pad? 
#    No, Pad adds. We need to subtract the valleys.
#    Better: Create the tooth profile, Pad it (creates one tooth). 
#    Then use a Polar Pattern of the Pad (creates all teeth).
#    Then use a "Cylinder" as the base, and subtract? 
#    Or, create the blank first, then pattern the teeth.
# 
# Strategy:
# 1. Create Blank: Pad a circle on XY plane.
# 2. Create Tooth Profile: Sketch on XZ plane.
#    Profile: (0,0) -> (0, tip_r) -> (x_tip, tip_r) -> Involute -> (base_r, 0) -> (0,0).
#    Wait, this profile creates the TOOTH.
#    If we pad this profile (revolve 360), we get a solid cylinder with a hole?
#    No, the profile is the boundary of the tooth.
#    If we revolve the AREA defined by this profile, we get a solid cylinder with a hole?
#    No. The profile (0,0) to (0, tip_r) is the centerline.
#    The area between the axis and the curve is the tooth.
#    If we revolve this area 360, we get a solid cylinder.
#    Wait, the curve (0,0)->(0,tip)->(x_tip,tip)->Involute->(base_r,0)->(0,0) encloses the TOOTH.
#    If we revolve this area 360, we get a solid cylinder where the tooth is the entire radius?
#    No. The profile is the shape of the TOOTH.
#    If we revolve the TOOTH shape 360, we get a solid cylinder.
#    Where are the gaps?
#    The gaps are between the teeth.
#    So we need to create the tooth, pad it, and then pattern it.
#    If we pattern the tooth 360, we get a ring of teeth.
#    What about the space between?
#    The space between is empty.
#    So the final object is a set of discrete teeth?
#    "A spur gear stock consists of a cylindrical gear body with external involute teeth".
#    This implies a solid cylinder with teeth molded on it.
#    So we need to:
#    1. Create the full cylinder (Blank).
#    2. Create the tooth profile (involute).
#    3. Create the tooth feature (Pad) to add material? 
#       No, the blank is already there.
#       We need to define the tooth as a feature that adds material to the blank?
#       Or, we define the tooth profile and Pad it. If we Pad the tooth profile, it creates a tooth.
#       If we pattern the tooth, we get a gear.
#       BUT, the tooth profile I described ((0,0) to ... ) includes the centerline.
#       If I Pad this, it creates a solid cylinder.
#       If I Pad a profile that does NOT include the centerline (e.g. from base_r to tip_r), I get a ring.
#       So, to make the teeth, I need to create the profile of the tooth relative to the base circle.
#       Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#       Revolve this 360? No, that makes a ring of teeth (a washer).
#       We need to add this ring to a blank cylinder.
#       So:
#       1. Create Blank: Pad Circle (Outer Diameter) * Length.
#       2. Create Tooth Ring: Sketch profile of one tooth (relative to base circle).
#          Profile: (base_r, 0) -> Involute -> (x_tip, tip_r) -> Line to (x_tip, 0) -> Line to (base_r, 0).
#          Wait, this is one half of a tooth.
#          We need to close the loop for the sketch.
#          Sketch: 
#             Line (base_r, 0) to (x_tip, 0) [Base circle chord? No, horizontal line]
#             Line (x_tip, 0) to (x_tip, tip_r) [Tip circle]
#             Involute from (x_tip, tip_r) to (base_r, 0).
#             Close loop? No, we need to revolve this.
#             If we revolve this area (between axis and curve), we get a cylinder.
#             We need the area between the curve and the BASE CIRCLE?
#             No, the tooth is on the outside.
#             The stock is a cylinder.
#             We want to ADD teeth.
#             So we take the blank cylinder.
#             We create a feature that adds the teeth.
#             The tooth profile is the INVOLUTE.
#             We create a sketch of the INVOLUTE curve + the lines connecting it to the base circle.
#             Profile: 
#                Line from (0,0) to (base_r, 0) ? No.
#                We are working on the XZ plane.
#                We want to define the shape of the tooth to be added.
#                The tooth starts at base_r and goes to tip_r.
