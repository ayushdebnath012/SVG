import os
import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize Document
doc = App.newDocument("SplineGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# Define a VarSet to hold editable parameters
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft outer diameter")
params.addProperty("App::PropertyLength", "root_diameter", "Dimensions", "Spline root diameter")
params.addProperty("App::PropertyInteger", "number_teeth", "Dimensions", "Number of teeth")
params.addProperty("App::PropertyLength", "tooth_width", "Dimensions", "Width of the spline groove")
params.addProperty("App::PropertyLength", "spline_thickness", "Dimensions", "Radial height of the spline")

# Set initial values as per requirements
params.shaft_diameter = 14.0
params.root_diameter = 11.0
params.number_teeth = 6
params.tooth_width = 3.0
params.spline_thickness = 1.0

# --- Sketch 1: The Spline Profile ---
# We will draw the profile on the XY plane, centered at the origin.
# The profile will consist of the outer shaft diameter and the inner spline grooves.

sketch = body.newObject("Sketcher::SketchObject", "SplineProfile")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.ConstraintType = "NoConstraint"
sketch.ConstraintsPrecision = 5

# Helper to add line segments to the sketch
def add_line(start, end, locked=False):
    sketch.addGeometry(Part.LineSegment(start, end), locked)

# Helper to add circles to the sketch
def add_circle(center, radius, locked=False):
    sketch.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), locked)

# --- Drawing the Profile ---
# 1. Outer Shaft Circle (Full Diameter)
# Center at (0,0), Radius = shaft_diameter / 2
outer_radius = params.shaft_diameter / 2.0
add_circle(App.Vector(0, 0, 0), outer_radius, locked=True)

# 2. Spline Grooves (Inner Cuts)
# The spline consists of flat-bottomed grooves between teeth.
# Number of teeth = 6. Angle between teeth = 60 degrees.
# Tooth width is given as linear width.
# We need to calculate the angular span of the tooth or the groove.
# Let's construct the profile by drawing the flat bottoms of the grooves and the arc segments connecting them.
# However, for a spline, the "tooth" is usually the land between two grooves.
# Let's assume the "tooth_width" refers to the width of the flat land (the part that carries load) or the groove width.
# Standard interpretation in such simple prompts: 'tooth_width' is the width of the groove (the flat part we cut out).
# Let's calculate the position of the groove centers.

teeth_count = params.number_teeth
angle_step = 360.0 / teeth_count
groove_width = params.tooth_width

# We need to place circles representing the flat bottom of the groove.
# Since we are on a 2D sketch, the "root_diameter" defines the circle passing through the flat bottom of the grooves?
# Or does root_diameter define the radius of the groove bottom?
# Usually, Root Diameter is the smallest diameter of the gear/spline.
# So, the grooves go down to the root_diameter.
root_radius = params.root_diameter / 2.0

# The grooves are spaced by 'tooth_width'.
# There are 'number_teeth' grooves.
# Total circumference = 2 * PI * shaft_radius.
# But the grooves might not span the full width if it's a crowning spline, but let's assume straight sides.
# Let's place the center of each groove at intervals.
# If we have 6 teeth, we have 6 grooves.
# The distance between groove centers along the arc?
# Or is the width linear? Let's assume linear width at the radius of interest (approx shaft radius).
# Actually, simpler approach: Divide the circle into segments.
# Segment 1: Groove
# Segment 2: Tooth
# But the prompt says "tooth_width". Let's assume this is the width of the groove itself.
# We will place the groove circles such that the arc length between them corresponds to the geometry.
# Let's distribute the groove centers evenly.

groove_centers = []
# Start angle offset. Let's start a tooth at 0 and a groove at 30 deg (half tooth pitch).
# Pitch angle = 60 deg. Groove center at 30 deg, 90 deg, etc.
for i in range(teeth_count):
    angle = 30.0 + i * angle_step
    x = outer_radius * math.cos(angle * math.pi / 180)
    y = outer_radius * math.sin(angle * math.pi / 180)
    groove_centers.append(App.Vector(x, y, 0))

# Now we need to draw the groove bottoms.
# The groove bottom is at root_radius.
# The width is 'tooth_width'.
# How to define the width in a sketch?
# We can define a circle at the center of the groove with diameter = tooth_width.
# But the groove is on the surface of the shaft.
# So we draw a circle of diameter 'tooth_width' at the calculated center.
# Then we constrain its center to the outer circle? No, it's inside.
# We constrain the center of the groove circle to be on a circle of radius = outer_radius?
# No, the center of the groove circle is at distance 'outer_radius' from the main center?
# Yes, if the groove is on the surface.
# So:
# 1. Create a circle at the groove center position.
# 2. Constrain its center to the main outer circle (Coincident).
# 3. Constrain its radius to tooth_width/2.
# 4. Constrain it to be tangent to the "land" circles?
# This is getting complex for a pure sketch without intermediate circles.

# Alternative: Draw the "Tooth" lands directly.
# Land width = (Pitch - Groove Width).
# But we don't know the exact pitch definition from the prompt.
# Let's try a different construction:
# Draw the inner circle (Root Diameter).
# Draw the outer circle (Shaft Diameter).
# Now, for the splines:
# We can use a polar array of a pattern later, but the profile must be closed.
# Let's create a closed polyline representing one tooth/groove pair, then pattern it.
# One unit cell:
# 1. Start at angle 0 on Outer Circle.
# 2. Go inwards to Root Radius? No, splines usually have flat lands.
# 3. Let's assume the "tooth_width" is the width of the flat land.
#    Then the groove width would be the rest of the pitch.
#    OR "tooth_width" is the groove width.
#    Let's assume "tooth_width" is the groove width (the cut).
#    Pitch = 360 / 6 = 60 deg.
#    If groove width is 3mm, what is the land width?
#    Arc length of 60 deg at 14mm diameter = PI * 14 * (60/360) = 7.33 mm.
#    If groove is 3mm, land is 4.33mm.
#    
#    Construction Strategy:
#    1. Define the main outer circle.
#    2. Define the main inner circle (Root Diameter).
#    3. We need to connect them with the spline geometry.
#    4. We can create a "Tooth" profile segment and pattern it.
#    
#    Let's define ONE tooth profile (Land + Groove) and mirror/rotate it.
#    Actually, a spline is often defined by the groove centers.
#    Let's draw the groove circles on the outer circle, then project lines to the inner circle?
#    No, splines have flat bottoms.
#    
#    Refined Construction:
#    1. Outer Circle (Shaft Dia).
#    2. Inner Circle (Root Dia).
#    3. We will create a "Groove" circle of diameter = tooth_width.
#    4. Place this groove circle such that its center lies on the Outer Circle.
#    5. We need to space them correctly.
#    6. If we have 6 teeth, we have 6 grooves.
#    7. The grooves are equally spaced.
#    8. Let's place the center of the first groove at 30 degrees.
#    9. Constrain the center of the groove circle to the Outer Circle.
#    10. Constrain the radius of the groove circle to tooth_width/2.
#    11. We also need to constrain the groove to the inner circle? 
#        The bottom of the groove is the root diameter.
#        So the groove circle must be tangent to the Inner Circle?
#        If the groove circle has diameter Dg, and center is at distance R_out from origin.
#        The closest point to origin is R_out - Dg/2.
#        This must equal R_in (root radius).
#        So R_out - Dg/2 = R_in => Dg/2 = R_out - R_in.
#        Let's check: (14-11)/2 = 1.5mm.
#        But the prompt says tooth_width = 3.0mm.
#        This implies the "tooth_width" is NOT the diameter of the groove circle that touches the root.
#        It likely means the width of the TOOTH (the land).
#        Or the prompt implies a specific geometry where the groove width is 3mm and the land is different.
#        Given the ambiguity, I will interpret "tooth_width" as the width of the flat LAND (the tooth).
#        And the groove width is the remainder of the pitch.
#        
#    Revised Plan:
#    1. Outer Circle (R=7).
#    2. Inner Circle (R=5.5).
#    3. We need to create a pattern of 6 elements.
#    4. One element (One Tooth):
#       - An arc from Outer Circle to Inner Circle? No, splines have flats.
#       - A flat segment on the outer circle?
#       - A flat segment on the inner circle?
#       - Typically: Flat on Outer, Flat on Inner, Radial lines connecting?
#       - Or: Flat on Outer, Flat on Inner, and the sides are arcs or lines.
#       - Let's assume standard involute-like approximation for simplicity:
#         - Flat land on the outside (Shaft surface).
#         - Flat land on the inside (Root surface).
#         - Connect them.
#
#    Let's try this specific interpretation:
#    - The spline is a ring of flats.
#    - Number of flats = number_teeth = 6.
#    - Width of each flat (Land) = tooth_width = 3.0mm.
#    - The rest is the groove.
#    - The flats go from Root Diameter to Shaft Diameter.
#    
#    Sketch Steps:
#    1. Draw Outer Circle (R=7).
#    2. Draw Inner Circle (R=5.5).
#    3. Draw a line segment tangent to Outer Circle and Inner Circle?
#       No, let's draw the "Tooth" profile explicitly.
#       Start at Outer Circle.
#       Move along the outer circle by arc_length(tooth_width).
#       Move radially inward to Inner Circle.
#       Move along the inner circle by arc_length(tooth_width).
#       Move radially outward to Outer Circle.
#       Connect to start.
#       
#       Wait, if we do this, the "tooth" is the land.
#       Then we pattern this shape 6 times.
#       Does this match "number_teeth=6"? Yes, 6 lands.
#       
#    Implementation:
#    - We cannot easily draw "arc_length" directly in a sketch without parametric constraints.
#    - We can use a workaround:
#      1. Create a "Reference" circle for the tooth center.
#      2. Use a polar pattern of a line segment? No.
#      3. Let's create the profile using a single closed loop and then use a Polar Pattern of the feature, but we need the profile to be closed first.
#      4. Since the sketch must be closed:
#         - Draw Outer Circle.
#         - Draw Inner Circle.
#         - We need to cut out the grooves.
#         - Let's draw the Grooves explicitly.
#         - Groove 1 Center: 30 deg.
#         - Groove 2 Center: 90 deg.
#         - ...
#         - Draw a circle at each groove center with Diameter = tooth_width.
#         - Constrain center to Outer Circle.
#         - Constrain radius to tooth_width/2.
#         - Constrain the circle to be tangent to the Inner Circle?
#           (As calculated before, if width=3, radius=1.5. R_out=7. 7-1.5 = 5.5 = R_in. Perfect!)
#         - So, we have 6 small circles (grooves) on the outer surface, touching the inner surface.
#         - Now, we need to connect the outer circle to the inner circle where there are no grooves.
#         - The "land" is the arc of the outer circle between two grooves, connected to the corresponding arc of the inner circle.
#         - We can achieve this by:
#           1. Drawing the Outer Circle.
#           2. Drawing the Inner Circle.
#           3. Drawing the 6 Groove Circles (constrained as above).
#           4. Now, the sketch is a collection of disjoint lines (circles). This is not a single closed profile.
#           5. We need to "join" the lands.
#           6. We can use the "Join" function in Sketcher? No, we need to draw lines.
#           7. Draw a line from Outer Circle (start of land) to Inner Circle (start of land).
#              This requires finding the intersection of the "Groove" circle with the Outer/Inner circles?
#              The Groove Circle touches the Inner Circle at one point.
#              It intersects the Outer Circle at two points.
#              The "Land" is the arc of the Outer Circle between the two intersection points of adjacent Groove Circles.
#              And the arc of the Inner Circle between the touch points of adjacent Groove Circles?
#              Wait, the Groove Circle touches the Inner Circle.
#              So the "Land" on the inner side is the arc between the touch point of Groove N and Groove N+1.
#              The "Land" on the outer side is the arc between the intersection points of Groove N and Groove N+1.
#              
#    Let's refine the sketch construction to be robust:
#    1. Outer Circle (R=7).
#    2. Inner Circle (R=5.5).
#    3. Groove Circle 1: Center on Outer Circle, Radius 1.5, Tangent to Inner Circle.
#    4. Groove Circle 2: Same, rotated 60 deg.
#    ...
#    5. Now, how to close the loop?
#       We can't easily draw the arcs between circles in FreeCAD Sketcher directly with standard constraints without creating intermediate lines.
#       Alternative: Create a "Tooth" profile using a construction line and a circle, then pattern the feature?
#       No, the sketch must be a single closed wire.
#       
#    Trick:
#    Use the fact that we can create a "Closed" profile by connecting the outer circle and inner circle segments.
#    Since we have 6 grooves, we have 6 lands.
#    Let's create the profile of ONE land + one half-groove, then mirror? No, 6 is even.
#    Let's create the profile of ONE TOOTH (Land + 1/2 Groove on each side).
#    Profile:
#      - Start at Outer Circle (between Groove 1 and 2).
#      - Go along Outer Circle to Groove 1 intersection.
#      - Go along Groove 1 circle to Inner Circle.
#      - Go along Inner Circle to Groove 2 touch point? No.
#      - Go along Inner Circle to the touch point of Groove 1?
#      - Go along Groove 1 circle back to Outer Circle?
#      - Then along Outer Circle to Groove 2?
#      This creates a "C" shape, not a closed loop.
#      
#    Correct approach for a closed loop with multiple disjoint circles:
#    We must draw the connecting lines/arcs.
#    But FreeCAD Sketcher doesn't have "Arc Between Circle Intersection" as a direct primitive to draw.
#    We can approximate or use a workaround.
#    
#    Workaround:
#    1. Draw the Outer Circle.
#    2. Draw the Inner Circle.
#    3. Draw the 6 Groove Circles.
#    4. Use the "Constraint" -> "Tangent" between the Groove Circles and the Outer/Inner circles? They are already tangent/intersecting.
#    5. We need to create the "Land" arcs.
#       We can create a circle with very large
