import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("TaperPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# We define parameters that drive the geometry.
# Note: In FreeCAD 1.1, we can use App::Parameter or simply set properties on the Body or a VarSet.
# To ensure they are editable and drive the script, we will use App::Parameter objects attached to the Body.

# Small end diameter (at the start of the taper section, after the tip)
param_small_dia = body.newObject("App::Parameter", "p_small_dia")
param_small_dia.Value = 0.6

# Overall length
param_length = body.newObject("App::Parameter", "p_length")
param_length.Value = 4.0

# Rounded end height (axial length of the fillet/rounded tip)
param_round_height = body.newObject("App::Parameter", "p_round_height")
param_round_height.Value = 0.08

# Taper ratio (slope per unit length, e.g., 0.02 for 1:50)
param_taper_ratio = body.newObject("App::Parameter", "p_taper_ratio")
param_taper_ratio.Value = 0.02

# --- Sketch 1: Base Profile (Side View) ---
# We create a sketch on the XY plane to define the profile of the pin.
# The profile will consist of:
# 1. A rounded tip at the bottom (Z=0).
# 2. A tapered section going up to the large diameter.
# 3. A flat top section (if needed, but description implies just taper to large end).
# Actually, a taper pin usually tapers from small to large. Let's assume:
# - Tip is rounded (radius = small_dia/2).
# - Then it tapers linearly to the large diameter at the top.
# - The "small_end_diameter" in the prompt is described as "radius at the start of the taper section after the rounded tip".
#   Wait, the prompt says "diameter=0.6mm (small-end diameter; the radius at the start of the taper section after the rounded tip)".
#   This phrasing is slightly ambiguous. Usually "diameter" means diameter. "radius at..." implies the value given is a radius?
#   Let's re-read carefully: "diameter=0.6mm (small-end diameter; the radius at the start of the taper section after the rounded tip)".
#   This likely means the *diameter* is 0.6mm, and this diameter occurs at the start of the taper section (which is after the rounded tip).
#   So: Tip (rounded) -> Taper Start (Dia 0.6) -> Taper End (Large Dia).
#   But we need the Large Diameter. The prompt doesn't explicitly give a "large_end_diameter" parameter value, only "taper_ratio".
#   However, a standard taper pin (1:50) usually has a specific relationship.
#   If the taper ratio is 0.02 (slope), and we have a length of 4.0mm.
#   Let's assume the "length" is the total length.
#   If the tip is rounded with height 0.08mm, the remaining length for the taper is 4.0 - 0.08 = 3.92mm.
#   If the taper starts at Dia 0.6mm, and the slope is 0.02.
#   Delta_Diameter = Slope * Length_Taper = 0.02 * 3.92 = 0.0784 mm.
#   So Large Diameter = 0.6 + 0.0784 = 0.6784 mm.
#   This seems very small for a "large end".
#   Alternative interpretation: The "diameter=0.6mm" is the *small end diameter* of the whole pin (including tip?).
#   Let's stick to the most literal interpretation of the parameters provided:
#   1. Small end diameter (at start of taper) = 0.6mm.
#   2. Rounded tip height = 0.08mm.
#   3. Taper ratio = 0.02.
#   4. Length = 4.0mm.
#   We need to calculate the large diameter based on the taper ratio and the length available for tapering.
#   Available taper length = Total Length - Rounded Height = 4.0 - 0.08 = 3.92mm.
#   Diameter increase = 3.92 * 0.02 = 0.0784mm.
#   Large Diameter = 0.6 + 0.0784 = 0.6784mm.

# Let's create the sketch geometry.
sketch_profile = body.newObject("Sketcher::SketchObject", "Sketch_Profile")
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Support = (doc.getObject("XY_Plane"), [])
sketch_profile.ConstrainAuto = True
sketch_profile.MapMode = "FlatFace"

# We will construct the profile using lines and circles.
# Coordinate system: X is horizontal (diameter), Z is vertical (length).
# Origin at the center of the rounded tip bottom.

# 1. Rounded Tip (Bottom)
# Radius = small_dia / 2 = 0.3mm.
# Center at (0, 0).
# We draw a circle.
r_tip = param_small_dia.Value / 2.0
circle_tip = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_tip)
sketch_profile.addGeometry(circle_tip, False)

# 2. Taper Section
# Starts at Z = r_tip (top of the circle).
# Ends at Z = r_tip + (Length - r_tip) = Length.
# Wait, the rounded tip height is 0.08mm.
# If the circle radius is 0.3mm, the height of the circle is 0.6mm.
# This contradicts "rounded_end_height=0.08mm".
# Re-evaluating the geometry description:
# "rounded_end_height=0.08mm (axial length of the rounded section at each end)"
# This implies the tip is a small fillet or a small sphere cap, not a full hemisphere of the main diameter.
# However, the prompt says "diameter=0.6mm (small-end diameter; the radius at the start of the taper section after the rounded tip)".
# This is confusing. Let's assume a standard engineering drawing interpretation:
# - The pin has a total length L.
# - At the very end, there is a rounded tip of height H_round.
# - Immediately after the tip, the diameter is D_small = 0.6mm.
# - From there, it tapers to D_large over the remaining length.
# - The taper ratio is 0.02.

# Let's refine the sketch construction:
# Point A: Bottom of the tip. Z = 0.
# Point B: Top of the tip. Z = 0.08.
# At Z = 0.08, the diameter is 0.6mm. So the radius is 0.3mm.
# So at Z=0.08, we have a point (0.3, 0.08) and (-0.3, 0.08).
# The tip connects (0,0) to (0.3, 0.08) and (-0.3, 0.08).
# To make it a "rounded section", we can use a fillet or a small circle arc.
# Given the constraints of a simple sketch, let's approximate the tip as a small circle of radius 0.04mm (since 0.08 is the height, diameter 0.16? No, that's too small).
# Or, we can just draw a line from (0,0) to (0.3, 0.08) and apply a fillet later?
# But the prompt asks for a "rounded section".
# Let's assume the tip is a small sphere of diameter 0.16mm (radius 0.08mm) sitting on the taper start?
# No, "axial length of the rounded section" usually means the height of the fillet.
# Let's try this:
# 1. Draw a line from (0, 0) to (0.3, 0.08).
# 2. Draw a line from (0.3, 0.08) to (D_large/2, Length).
# 3. Apply a fillet of radius 0.08mm at the bottom corner (0,0)-(0.3, 0.08)? No, that would make the tip height 0.08mm only if the tangent is horizontal.
# Let's simplify:
# The "rounded section" is likely a small sphere at the tip.
# Let's assume the tip is a sphere of diameter 0.16mm (radius 0.08mm).
# Then the taper starts at Z = 0.08mm with diameter 0.6mm.
# This fits "rounded_end_height=0.08mm" perfectly if the tip is a hemisphere of radius 0.08mm.
# But then the diameter at the start of the taper (Z=0.08) would be 0.16mm (the sphere diameter), not 0.6mm.
# Unless the "small-end diameter" refers to the diameter of the *tapered section* at its smallest point, which is 0.6mm.
# And the tip is a separate feature?
# Let's go with the most robust interpretation for a script:
# 1. Tip: A small circle of radius 0.08mm (height 0.16mm? No, height 0.08mm implies radius 0.04mm if it's a hemisphere, or diameter 0.08mm).
#    Let's assume the tip is a small circle of diameter 0.08mm (radius 0.04mm). Height = 0.08mm.
#    So at Z=0.08, the radius is 0.04mm.
#    Then the taper starts. But the prompt says "diameter=0.6mm ... at the start of the taper section".
#    This implies a discontinuity or a very sharp transition if we just switch from 0.04mm to 0.6mm.
#    Maybe the "rounded section" is a fillet connecting the tip to the taper?
#    Let's try this geometry:
#    - Start at (0,0).
#    - Go to (0.3, 0.08). (This creates a slope).
#    - Then taper to (D_large/2, 4.0).
#    - Apply a fillet of radius 0.08mm at the corner (0.3, 0.08)? No, that would round the corner.
#    - Apply a fillet at (0,0)?
#    Let's assume the "rounded section" is a small sphere at the very tip.
#    Radius = 0.08mm.
#    So the profile goes from (0,0) to (0.08, 0.08) (quarter circle).
#    Then from (0.08, 0.08) to (0.3, 0.08)? That's a horizontal line.
#    Then taper from (0.3, 0.08) to (D_large/2, 4.0).
#    This seems plausible.
#    Let's calculate D_large again.
#    Taper length = 4.0 - 0.08 = 3.92mm.
#    Slope = 0.02.
#    Delta_D = 3.92 * 0.02 = 0.0784mm.
#    D_large = 0.6 + 0.0784 = 0.6784mm.
#    Radius at top = 0.3392mm.
#    Radius at taper start (Z=0.08) = 0.3mm.
#    Radius at tip top (Z=0.08) = 0.08mm.
#    So there is a step from 0.08mm to 0.3mm at Z=0.08.
#    This is a "shoulder".
#    Let's refine the sketch to match this:
#    1. Circle at (0,0) with radius 0.08mm. (Tip)
#    2. Line from (0.08, 0.08) to (0.3, 0.08). (Shoulder)
#    3. Line from (0.3, 0.08) to (0.3392, 4.0). (Taper)
#    4. Close the loop.

# Let's implement this.
# Coordinates:
# P1: (0, 0)
# P2: (0.08, 0.08) -> Top of tip
# P3: (0.3, 0.08) -> Start of taper
# P4: (0.3392, 4.0) -> End of taper (Large end)
# P5: (0, 4.0) -> Top center (to close)
# P6: (0, 0) -> Back to start

# Wait, we need to close the loop symmetrically.
# We will draw the right half and use symmetry? Or just draw the full profile.
# Let's draw the full profile.
# Points:
# (0, 0) -> (0.08, 0.08) [Arc/Circle]
# (0.08, 0.08) -> (0.3, 0.08) [Line]
# (0.3, 0.08) -> (0.3392, 4.0) [Line]
# (0.3392, 4.0) -> (0, 4.0) [Line]
# (0, 4.0) -> (0, 0) [Line]
# (0, 0) -> (0.08, 0.08) [Arc/Circle]

# Actually, to make it a single solid, we need to close the loop.
# Let's define the points explicitly.
# We need to handle the circle at the bottom.
# We can add a circle geometry and then lines.

# Calculate values
r_tip = param_round_height.Value / 2.0 # Assuming hemisphere? Or just height?
# "rounded_end_height=0.08mm". If it's a sphere, diameter = 0.16, radius = 0.08.
# Let's assume the tip is a sphere of diameter 0.16mm (radius 0.08mm).
# So at Z=0.08, the radius is 0.08mm.
# Then the taper starts at radius 0.3mm.
# This creates a step.
# Let's proceed with this.

# Taper calculation
L_total = param_length.Value
H_round = param_round_height.Value
D_small = param_small_dia.Value
slope = param_taper_ratio.Value

# Length of taper section
L_taper = L_total - H_round
# Diameter increase
delta_D = L_taper * slope
D_large = D_small + delta_D
R_large = D_large / 2.0
R_small_taper = D_small / 2.0

# Sketch Geometry
# 1. Tip Circle
# Center at (0, 0), Radius = 0.08mm.
# We add this circle.
circle_tip = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_tip)
sketch_profile.addGeometry(circle_tip, False)

# 2. Line from top of tip to start of taper
# Start: (0.08, 0.08)
# End: (0.3, 0.08)
line_shoulder = Part.LineSegment(App.Vector(0.08, 0.08, 0), App.Vector(0.3, 0.08, 0))
sketch_profile.addGeometry(line_shoulder, False)

# 3. Taper Line
# Start: (0.3, 0.08)
# End: (R_large, L_total)
line_taper = Part.LineSegment(App.Vector(0.3, 0.08, 0), App.Vector(R_large, L_total, 0))
sketch_profile.addGeometry(line_taper, False)

# 4. Top Line (Center to Large End)
# Start: (R_large, L_total)
# End: (0, L_total)
line_top = Part.LineSegment(App.Vector(R_large, L_total, 0), App.Vector(0, L_total, 0))
sketch_profile.addGeometry(line_top, False)

# 5. Bottom Line (Center to Tip Center)
# Start: (0, L_total)
# End: (0, 0)
line_bottom = Part.LineSegment(App.Vector(0, L_total, 0), App.Vector(0, 0, 0))
sketch_profile.addGeometry(line_bottom, False)

# Constraints
# Coincident: Tip circle center (0,0) with line intersection?
# Let's constrain the lines to meet at the circle.
# We need to constrain the lines to the circle
