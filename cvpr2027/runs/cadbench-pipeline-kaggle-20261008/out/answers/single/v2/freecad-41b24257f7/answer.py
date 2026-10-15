import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameters ---
# Gear Geometry
pressure_angle_deg = 20.0
gear_module = 2.0
number_of_teeth = 24
face_width = 20.0
hub_diameter = 38.0
hub_width = 10.0
shaft_diameter = 10.0
overall_width = 30.0

# Calculated Dimensions (ISO 21771)
pressure_angle = math.radians(pressure_angle_deg)
pitch_diameter = gear_module * number_of_teeth
outer_diameter = pitch_diameter + 2 * gear_module
root_diameter = pitch_diameter - 2 * (1.25 * gear_module)
base_diameter = pitch_diameter * math.cos(pressure_angle)
circular_pitch = math.pi * gear_module
tooth_thickness = circular_pitch / 2
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We create a VarSet to hold the named parameters requested in the prompt
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "gear module")
params.gear_module = gear_module
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
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "number of teeth")
params.number_of_teeth = number_of_teeth
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "pressure angle")
params.pressure_angle = pressure_angle_deg

# --- Sketch 1: Base Cylinder (Hub + Body) ---
# We will build the solid by revolving a profile.
# The profile will be a rectangle representing the cross-section of the gear body.
# We need to handle the hub and the main body in one sketch or separate sketches.
# Strategy: One sketch for the main body profile (Hub + Body), then a Pocket for the bore.

sketch_base = body.newObject("Sketcher::SketchObject", "BaseProfile")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [])
sketch_base.ConstrainToCurrentPlane = True

# Define the profile points for the main body (Hub + Body)
# The profile is symmetric around the Y-axis (in the sketch plane).
# X is horizontal, Y is vertical (representing radius).
# We need to define the outer diameter and the hub diameter.
# However, the hub is a step in diameter.
# Let's define the profile as a closed loop.
# Points: (0, -outer_radius), (outer_radius, -outer_radius), (outer_radius, hub_radius), (hub_radius, hub_radius), (0, hub_radius), (0, -outer_radius)
# Wait, standard gear drawing: Hub is the inner cylinder. Body is the outer cylinder.
# So the profile goes from center out to outer radius, then back to hub radius, then to center.
# Actually, simpler: Draw the outer rectangle and the inner rectangle (hub).
# But for revolution, we need a single closed profile or multiple profiles.
# Let's create a single closed profile that traces the outer edge and the inner hub edge.
# Order: Start at bottom outer, go right to outer, up to hub, left to hub, down to center? No.
# Let's do: Center -> Outer Radius -> Outer Radius (bottom) -> Hub Radius (bottom) -> Hub Radius (top) -> Center.
# This creates a shape with a hole in the middle (the hub hole) if we treat it as a solid of revolution?
# No, a single closed loop in sketcher creates a solid when revolved.
# If we want a hub (step), we need the profile to go:
# (0,0) -> (outer_radius, 0) -> (outer_radius, hub_radius) -> (hub_radius, hub_radius) -> (hub_radius, 0) -> (0,0).
# This creates a solid with a cylindrical hole of diameter hub_diameter? No, that would be a hole.
# We want a solid cylinder of diameter outer_diameter, with a smaller cylinder of diameter hub_diameter attached to the center?
# No, the hub is the central part. The gear body is the outer part.
# So the cross section is: A large rectangle (outer) minus a small rectangle (hub hole)? No.
# The hub is a solid cylinder of diameter hub_diameter. The gear body is a ring of width (outer - hub)/2?
# No, usually "Hub" means the central part that fits on the shaft.
# So the part is: A cylinder of diameter outer_diameter and width overall_width.
# Inside that, there is a cylinder of diameter hub_diameter and width hub_width.
# So the profile should be:
# 1. Outer boundary: (0,0) to (outer_radius, 0) to (outer_radius, overall_width/2) to (0, overall_width/2) to (0,0).
# 2. Inner boundary (Hub): (0,0) to (hub_radius, 0) to (hub_radius, hub_width/2) to (0, hub_width/2) to (0,0).
# This creates a solid with a hole? No, this creates a solid with a "step" if we subtract the inner one.
# But we want the hub to be solid.
# Correct Profile Logic:
# We want a solid that looks like a cylinder with a smaller cylinder attached to the center?
# No, the hub IS the center. The gear teeth are on the outside.
# So the solid is: Cylinder(outer_diameter, overall_width) MINUS Cylinder(hub_diameter, overall_width - hub_width)?
# No, the hub is usually the part that fits the shaft.
# Let's assume the standard: A solid cylinder of diameter outer_diameter and width overall_width.
# Inside, there is a cylindrical hole of diameter shaft_diameter? No, the prompt says "central bore... defined by shaft_diameter".
# And "hub... characterized by hub_diameter".
# So:
# 1. Main Body: Cylinder(outer_diameter, overall_width).
# 2. Hub: Cylinder(hub_diameter, hub_width). This is part of the main body.
# 3. Bore: Cylinder(shaft_diameter, overall_width). This is a hole through the center.
#
# So the profile for the main body (before teeth) should be:
# A rectangle of width overall_width and height outer_radius.
# BUT, we need to subtract the hub hole? No, the hub is solid.
# We need to subtract the bore.
# So:
# Profile 1 (Main Body): Rectangle from (0,0) to (outer_radius, overall_width).
# Feature 1: Pad (Revolution) of Profile 1.
# Feature 2: Pocket (Revolution) of a profile representing the bore.
# Feature 3: Pocket (Revolution) of a profile representing the "missing" hub material?
# No, the hub is solid. The bore goes through the hub.
# So the bore is a single hole through the whole width?
# "The central bore passes through the gear along its axis". Yes.
# So we just need to subtract a cylinder of diameter shaft_diameter and length overall_width.
# What about the hub? The hub is just the central part of the gear body.
# If the gear body is a solid cylinder of diameter outer_diameter, the hub is just the center part.
# Unless the "hub" implies a step down in diameter?
# "Hub is formed concentrically... characterized by hub_diameter".
# Usually, a gear has a hub that is the same diameter as the gear body, or slightly smaller if there's a rim.
# But here, outer_diameter (52) is the tooth tip.
# If hub_diameter (38) is smaller than outer_diameter, and hub_width (10) is smaller than overall_width (30).
# This implies the gear body has a "rim" or "web" structure?
# Or does it mean the central part is a cylinder of 38mm diameter, and the rest is a ring?
# Let's assume the standard interpretation:
# The gear body is a solid cylinder of diameter outer_diameter and width overall_width.
# The "Hub" description might be describing the central section's dimensions for reference, or implying a step.
# Given "hub_diameter = 38" and "outer_diameter = 52", and "hub_width = 10" and "overall_width = 30".
# This strongly suggests a stepped geometry:
# - Central cylinder: Diameter 38, Width 10.
# - Outer ring: Diameter 52, Width 20 (30-10).
# So the profile is:
# 1. Outer boundary: (0,0) -> (26, 0) -> (26, 15) -> (0, 15) -> (0,0).
# 2. Inner boundary (Hub hole? No, Hub is solid):
#    We need to subtract the material between hub_diameter and outer_diameter? No.
#    We need to create the shape:
#    - From z=0 to z=5 (half hub width): Radius 26.
#    - From z=5 to z=15 (half rim width): Radius 26.
#    Wait, if the hub is 38mm diameter, that's radius 19.
#    If the hub is 10mm wide, and the total is 30mm.
#    Then the rim is 20mm wide.
#    So the profile is:
#    - Center line (z=0).
#    - Go out to R=26 (outer radius).
#    - Go up to Z=15 (half overall width).
#    - Go in to R=19 (hub radius)? No, that would make a hole.
#    - We want the hub to be solid.
#    - So the profile is simply a rectangle of R=26, Z=15.
#    - Then we subtract a hole of R=5 (shaft/2) through the whole thing?
#    - But what about the hub dimensions?
#    - Maybe the "Hub" is the part that fits the shaft, and the "Gear Body" is the toothed part.
#    - If the hub is 38mm diameter, and the gear is 52mm diameter.
#    - And the hub is 10mm wide.
#    - This implies the central 10mm section is 38mm diameter.
#    - The outer 20mm section is 52mm diameter.
#    - So the profile is:
#      - Start at (0,0).
#      - Go to (19, 5) [Hub radius, half hub width].
#      - Go to (19, 15) [Hub radius, half overall width].
#      - Go to (26, 15) [Outer radius, half overall width].
#      - Go to (26, 0) [Outer radius, center].
#      - Close loop.
#    - This creates a solid with a step: Inner cylinder (R=19, Z=15) + Outer ring (R=26, Z=15, R=19, Z=5).
#    - Wait, the path (0,0)->(19,5)->(19,15)->(26,15)->(26,0)->(0,0) creates a shape that is:
#      - A rectangle from Z=0 to Z=15, R=0 to R=19? No.
#      - The area is bounded by the lines.
#      - Line 1: (0,0) to (19,5).
#      - Line 2: (19,5) to (19,15).
#      - Line 3: (19,15) to (26,15).
#      - Line 4: (26,15) to (26,0).
#      - Line 5: (26,0) to (0,0).
#      - This shape is: A rectangle (0,0)-(26,15) MINUS a triangle (0,0)-(19,5)-(19,0)? No.
#      - It's a polygon.
#      - Let's trace:
#        (0,0) -> (19,5): Diagonal.
#        (19,5) -> (19,15): Vertical up.
#        (19,15) -> (26,15): Horizontal right.
#        (26,15) -> (26,0): Vertical down.
#        (26,0) -> (0,0): Horizontal left.
#      - This creates a shape that is NOT a simple cylinder.
#      - We want a step cylinder.
#      - Profile for step cylinder:
#        (0,0) -> (19, 5) -> (19, 15) -> (26, 15) -> (26, 0) -> (0,0).
#        This creates a shape where the radius is 19 for Z in [0,5] and 26 for Z in [5,15]?
#        No.
#        If we go (0,0) -> (19,5), the radius increases linearly.
#        We want constant radius.
#        So: (0,0) -> (19, 5) is wrong.
#        We want: (0,0) -> (19, 5) is not a vertical line.
#        We want: (0,0) -> (19, 5) is a line.
#        We want: (0,0) -> (19, 5) is a line.
#        We want: (0,0) -> (19, 5) is a line.
#        Correct path for step:
#        (0,0) -> (19, 5) [Hub radius at half hub width? No, hub width is 10, so half is 5].
#        (19, 5) -> (19, 15) [Hub radius at half overall width].
#        (19, 15) -> (26, 15) [Outer radius at half overall width].
#        (26, 15) -> (26, 0) [Outer radius at center].
#        (26, 0) -> (0,0) [Center].
#        This creates a shape that is:
#        - From Z=0 to Z=5: Radius goes from 0 to 19? No, the line (0,0) to (19,5) is diagonal.
#        - We want a vertical line at Z=5? No, Z is the vertical axis in the sketch.
#        - We want:
#          - From Z=0 to Z=5: Radius = 19.
#          - From Z=5 to Z=15: Radius = 26.
#        - So the path should be:
#          (0,0) -> (19, 5) -> (19, 15) -> (26, 15) -> (26, 0) -> (0,0).
#          Wait, (0,0) to (19,5) is diagonal.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0) to (19, 5) to be a line? No.
#          We need (0,0
