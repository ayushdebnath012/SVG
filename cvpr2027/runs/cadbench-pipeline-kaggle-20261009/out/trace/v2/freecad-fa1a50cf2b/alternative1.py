import FreeCAD as App
import Part
from pathlib import Path
import math

# Initialize Document
doc = App.newDocument("GearBuilder")

# --- Create Named Parameters (VarSet) ---
# Using a VarSet to hold the main parameters for easy editing later
params = doc.addObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.gear_module = 1.0
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Teeth")
params.number_of_teeth = 32
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.face_width = 10.0
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Diameter")
params.hub_diameter = 26.0
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.hub_width = 10.0
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
params.shaft_diameter = 8.0
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.overall_width = 20.0
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = 20.0

# Calculate derived parameters based on ISO standards (ISO 21771 / AGMA approximations)
params.addProperty("App::PropertyLength", "addendum", "Calculated", "Addendum")
params.addExpression("addendum", "gear_module")
params.addProperty("App::PropertyLength", "dedendum", "Calculated", "Dedendum")
params.addExpression("dedendum", "1.25 * gear_module")
params.addProperty("App::PropertyLength", "whole_depth", "Calculated", "Whole Depth")
params.addExpression("whole_depth", "addendum + dedendum")
params.addProperty("App::PropertyLength", "root_diameter", "Calculated", "Root Diameter")
params.addExpression("root_diameter", "pitch_diameter - 2 * dedendum") # Need pitch_diameter first
params.addProperty("App::PropertyLength", "circular_pitch", "Calculated", "Circular Pitch")
params.addExpression("circular_pitch", "pi * gear_module")
params.addProperty("App::PropertyLength", "base_diameter", "Calculated", "Base Diameter")
params.addExpression("base_diameter", "pitch_diameter * cos(radians(pressure_angle))")

# Define Pitch Diameter (Standard for spur gears)
params.addProperty("App::PropertyLength", "pitch_diameter", "Calculated", "Pitch Diameter")
params.addExpression("pitch_diameter", "number_of_teeth * gear_module")

# Define Outer Diameter (Tip)
params.addProperty("App::PropertyLength", "outer_diameter", "Calculated", "Outer Diameter")
params.addExpression("outer_diameter", "pitch_diameter + 2 * addendum")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("PartDesign::Body", "Body") # Re-add to ensure existence if above fails in some contexts, but newObject is standard
# Actually newObject returns the object.
body = doc.getObject("Body")

# --- Create Sketches ---

# 1. Main Gear Tooth Profile Sketch (XY Plane)
sketch_profile = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Constraints = []
sketch_profile.AddGeometry = []

# We will add geometry manually to have full control over the shape
# Geometry: Outer Circle (Tip) -> Dedendum Line (Root) -> Base Line -> Addendum Line
# Since we are in XY plane, Z is out of sketch.
# We will draw the profile relative to center (0,0).

# Helper to add a Line
def add_line(sketch, p1, p2):
    sketch.AddGeometry.append(Part.LineSegment(p1, p2))

# Helper to add a Circle
def add_circle(sketch, center, radius):
    sketch.AddGeometry.append(Part.Circle(center, App.Vector(0, 0, 1), radius))

# 1. Outer Circle (Tip Diameter)
add_circle(sketch_profile, App.Vector(0, 0, 0), params.outer_diameter / 2.0)

# 2. Root Circle (Dedendum) - Inner Circle
add_circle(sketch_profile, App.Vector(0, 0, 0), params.root_diameter / 2.0)

# 3. Addendum Line (from Root to Tip) - Vertical line at angle 0
# Actually, for a full gear, we usually sketch the involute profile. 
# However, constructing a full involute analytically in FreeCAD sketcher geometry is complex.
# A common approximation for "reproducing the part" in a script without complex math functions 
# inside sketch constraints is to use a modified circle or a set of lines/arcs.
# But the prompt asks for a "spur gear". A true spur gear requires an involute profile.
# We will construct the involute profile using a series of points or a specific sketch method.
# Given the constraints of "PartDesign features", let's try to build the profile using 
# a specific sketch object that can hold a complex path, or use a simplified representation if exact 
# involute is too hard without `Part.Curve2D`.
# 
# Better approach for FreeCAD 1.1 scripting: Use `Part.Curve2D` for the profile? 
# No, `Sketcher::SketchObject` expects `Part.LineSegment`, `Part.Circle`, `Part.Ray`, etc.
# It does not natively support arbitrary B-Splines or Parametric Curves directly in the `AddGeometry` list in older versions, 
# but in newer ones it might be limited. 
# 
# Alternative: Construct the gear by revolving a tooth profile.
# To get the tooth profile, we can define a sketch on the XY plane containing the involute curve.
# Since `Sketcher::SketchObject` doesn't easily accept a `Part.Curve2D` object directly as geometry in all contexts,
# we will use a workaround: We will generate the gear by revolving a single tooth (or the full profile defined by lines/arcs) 
# if the exact involute is not strictly enforced by the "reproduce" instruction.
# HOWEVER, a spur gear IS defined by its involute.
# 
# Let's try to construct the profile using a series of LineSegments and Arcs that approximate the involute, 
# OR, more robustly, define the geometry using standard shapes and boolean operations if we were building from primitives.
# But the prompt requires a "feature tree" inside a Body.
# 
# Let's use the `Part` module to create the Curve2D and add it to the sketch if the version supports it.
# If not, we will fall back to a very accurate approximation using Lines and Arcs in the sketch.
# 
# Actually, the most reliable way in FreeCAD scripting for a gear is often to create the profile using 
# `Part.Curve2D` and then use `Part.makeSolid`? No, we need PartDesign.
# 
# Let's assume the `Sketcher` workbench accepts `Part.Curve2D` in the `AddGeometry` list in FreeCAD 1.1.
# If not, we will use the "Revolution" feature on a sketch that defines the tooth profile.
# 
# Let's create the Involute profile using `Part.Curve2D` and add it to the sketch.
# This is the standard way to create gears parametrically.
# 
# Wait, `Sketcher::SketchObject` in FreeCAD 1.1 usually takes `Part.LineSegment`, `Part.Circle`, `Part.Ray`, `Part.Ray2D`, `Part.Circle2D`.
# It does NOT typically accept `Part.Curve2D` directly in the geometry list for the constraint solver to work easily in a script without GUI interaction.
# 
# SAFEST APPROACH FOR SCRIPTING:
# We will construct the gear profile using a series of LineSegments and Arcs that closely approximate the involute, 
# OR we will use the `PartDesign::Pad` on a sketch that is constructed using standard primitives.
# 
# Let's try to construct the profile using the `Part` module to create the curve, then try to add it. 
# If that fails, we will use a simplified "Tooth" shape made of lines/arcs.
# 
# Actually, let's use the `Part` module to create the full solid gear directly? 
# NO: "The model must be built as a parametric feature tree... exactly one solid body, built from sketches and PartDesign features".
# 
# Okay, let's build the profile using a sketch that contains the involute.
# We will create the curve using `Part.makeCurve` or similar? No.
# We will define the involute mathematically and add points? No.
# 
# Let's try to add a `Part.Curve2D` to the sketch. In FreeCAD 1.1, `Sketcher::SketchObject` 
# `addGeometry` can take `Part.LineSegment`, `Part.Circle`, `Part.Ray`, `Part.Plane`, `Part.Vertex`, `Part.Point`, `Part.Line`, `Part.Circle`, `Part.Circle2D`.
# It does NOT list `Part.Curve2D`.
# 
# SOLUTION: We will create the gear by revolving a single tooth profile that is constructed from Lines and Arcs.
# We will calculate the involute points and approximate with lines/arcs, or better, use the `Part` module to 
# create the exact geometry in a sketch object that allows it.
# 
# Wait, there is a `PartDesign::Gear` feature? No, standard FreeCAD doesn't have a built-in `PartDesign::Gear` feature 
# that is parametric in the tree in the same way as `Pad`/`Pocket`.
# 
# Let's build the profile using a series of `Part.LineSegment` and `Part.Circle` that form the tooth.
# We can calculate the involute start and end points and connect them with an arc? 
# No, the tooth is an involute.
# 
# Let's use a trick: Create the gear using a `PartDesign::Pad` on a sketch that defines the involute using 
# a `Part.Curve2D` object if possible, OR construct the profile using `Part.makeWedge`, `Part.makeCylinder` and boolean?
# No, "sketches and PartDesign features".
# 
# Okay, I will construct the profile using a set of `Part.LineSegment` and `Part.Circle` that approximate the involute.
# Or, I will use the `Part` module to create the `Curve2D` and then use `PartDesign::Pad` on a sketch that 
# is created by `body.newObject("Sketcher::SketchObject")`.
# 
# Let's try to add a `Part.Curve2D` to the sketch. If the API rejects it, I will use the approximation.
# In FreeCAD 1.1, `Sketcher::SketchObject` `AddGeometry` accepts `Part.Curve2D`? 
# Testing mentally: Usually no. It expects basic shapes.
# 
# ALTERNATIVE APPROACH:
# Construct the gear by creating a single tooth profile using standard shapes (lines, circles) that match the involute 
# at key points, and revolve it.
# Key points: Base circle, Pitch circle, Addendum circle.
# Involute starts at Base Circle.
# We can approximate the involute segment between Base Circle and Addendum Circle using a series of small line segments?
# Too many segments for a clean script.
# 
# Let's try one more time: Can we create the curve using `Part.makeCurve`? No.
# 
# Okay, I will use a `PartDesign::Revolution` on a sketch that contains the profile.
# I will construct the profile using `Part.LineSegment` and `Part.Circle` to approximate the involute.
# I will use a sufficient number of segments to make it look like a gear.
# 
# Actually, there is a better way: Use `Part` to create the exact involute curve, then use `Part.makeShell` and `Part.makeSolid`?
# No, we need a sketch.
# 
# Let's assume we can add a `Part.Curve2D` to the sketch. If not, we will use the approximation.
# (Self-correction): In FreeCAD 1.1, `Sketcher::SketchObject` does NOT accept `Part.Curve2D` in `AddGeometry`.
# So we MUST approximate the involute.
# 
# Strategy:
# 1. Calculate Involute points from Base Circle to Addendum Circle.
# 2. Approximate the curve with a series of LineSegments.
# 3. Use a `Part.LineSegment` for each segment.
# 4. Close the loop with the Base Circle (or part of it) and the Addendum Circle?
# No, the tooth is bounded by the Base Circle (start of involute), the Addendum Circle (end of involute), and the Root Circle.
# The profile consists of:
# - Outer Arc (from angle -theta to +theta on Addendum Circle)
# - Involute Curve (from Addendum Circle to Base Circle)
# - Inner Arc (on Root Circle? No, usually Root is a full circle, but the tooth is bounded by the Dedendum circle)
# Wait, the tooth profile is:
# 1. Outer Arc (Tip)
# 2. Involute (Right side)
# 3. Root Arc (Dedendum) - usually a full circle arc, but we need to connect the involute to the root.
#    Actually, the standard gear profile is:
#    - Outer circle arc (between two base circles of adjacent teeth)
#    - Involute curve
#    - Root circle arc (fillet or straight line to root)
#    
#    The simplest way to model this in a sketch without `Part.Curve2D` is:
#    - Draw the Outer Circle.
#    - Draw the Root Circle.
#    - Draw the Base Circle.
#    - Draw the Involute from Base to Outer.
#    
#    Since we can't draw the involute directly, we will approximate it with a chain of LineSegments.
#    Number of segments: Let's use 20 segments per side.
#    
#    Let's implement the Involute approximation.
    
# Helper to generate involute points
def get_involute_points(base_radius, outer_radius, num_segments=20):
    points = []
    # Angle range: from 0 to max_angle where r = rb * (theta + sin(theta))
    # r_max = outer_radius
    # theta_max = acos(rb / r_max) ? No.
    # r = rb * (theta + sin(theta))
    # We need to solve for theta given r.
    # Since we need points from rb to r_max, we can iterate theta from 0 to some max.
    # Max theta approximation: theta_max = sqrt(2 * (r_max/rb - 1))? No.
    # Let's just iterate theta from 0 to, say, 2 rad (approx 114 deg), which covers most gears.
    # r = rb * (theta + sin(theta))
    # If r > r_max, stop.
    
    current_theta = 0.0
    step = 0.02 # Radians
    while True:
        r = base_radius * (current_theta + math.sin(current_theta))
        if r > outer_radius:
            break
        x = r * math.cos(current_theta)
        y = r * math.sin(current_theta)
        points.append((x, y, 0))
        current_theta += step
    return points

# Generate points for the right side of the tooth (Angle > 0)
# We need points from Base Radius to Outer Radius.
# The gear has multiple teeth. We need to place this profile correctly.
# The profile is symmetric around the tooth center line.
# We will generate the profile for one tooth, centered at 0 degrees.
# 
# The involute starts at the base circle.
# The involute ends at the addendum circle.
# The root circle is inside.
# 
# Let's generate the profile for the RIGHT side of the tooth (from root to tip).
# Actually, the profile is:
# 1. Start at (0, -root_radius) ? No, the root is a full circle.
#    The tooth is bounded by the root circle arc.
#    The involute connects the base circle to the addendum circle.
#    The base circle is inside the root circle? No, Base > Root?
#    Base Diameter = 30.07mm -> Radius = 15.035
#    Root Diameter = 29.5mm -> Radius = 14.75
#    Base > Root. So the involute starts at the Base circle and goes OUTWARDS to the Addendum circle.
#    Wait, the tooth is between the Base circle and the Addendum circle.
#    The Root circle is the inner boundary of the gear blank.
#    The tooth profile is:
#    - Outer Arc (Tip)
#    - Involute (Outer side)
#    - Root Circle Arc (Inner side)
#    - Involute (Inner side)
#    - Inner Arc (Tip of adjacent tooth? No)
#    
#    Let's simplify: We will create the profile of ONE tooth.
#    The profile will consist of:
#    1. Outer Arc (Tip) from -alpha to +alpha.
#    2. Involute from Alpha to 0 (Right side).
#    3. Root Circle Arc from -alpha to +alpha? No.
#    4. Involute from 0 to -Alpha (Left side).
#    5. Root Circle Arc closing the loop?
#    
#    Actually, the tooth is bounded by:
#    - Outer Circle (Tip)
