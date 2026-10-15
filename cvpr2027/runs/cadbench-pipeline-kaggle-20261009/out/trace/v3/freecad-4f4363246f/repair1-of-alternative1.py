import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Document Creation ---
doc = App.newDocument("WireSafetyLanyard")
doc.Label = "Wire Safety Lanyard"
doc.FileName = str(Path(__file__).resolve())

# --- Parameters Object ---
# Define the dimensions directly from the drawing labels to ensure precision
params = doc.addObject("App::Parameter", "Params")
params.addProperty("App::PropertyLength", "width", "Params", "Width of the lanyard body")
params.width = 27.5
params.addProperty("App::PropertyLength", "top_width", "Params", "Width of the top loop")
params.top_width = 33.07
params.addProperty("App::PropertyLength", "fillet_radius_top", "Params", "Top loop fillet radius")
params.fillet_radius_top = 1.8
params.addProperty("App::PropertyLength", "fillet_radius_bottom", "Params", "Bottom fillet radius")
params.fillet_radius_bottom = 1.745
params.addProperty("App::PropertyLength", "bottom_width", "Params", "Bottom width")
params.bottom_width = 20.0 # Inferred from 10+10 or R10/R10 context, drawing shows R20 fillet
params.addProperty("App::PropertyLength", "transition_radius", "Params", "Inner transition radius")
params.transition_radius = 5.0
params.addProperty("App::PropertyLength", "neck_length", "Params", "Length from top loop bottom to start of transition")
params.neck_length = 13.17
params.addProperty("App::PropertyLength", "transition_length", "Params", "Length of the curved transition section")
params.transition_length = 90.58
params.addProperty("App::PropertyLength", "bottom_neck_length", "Params", "Length from transition end to bottom loop start")
params.bottom_neck_length = 24.93
params.addProperty("App::PropertyLength", "bottom_loop_height", "Params", "Height of bottom loop")
params.bottom_loop_height = 105.0
params.addProperty("App::PropertyLength", "bottom_loop_width", "Params", "Width of bottom loop")
params.bottom_loop_width = 10.2

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (The Lanyard Profile) ---
# We use the XY plane for the profile
sketch = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch.Plane = "XY_Plane"
sketch.MapMode = "FlatFace"
sketch.AttachmentOffset = App.Vector(0, 0, 0)

# --- Constructing the Profile ---
# We will build this sketch using explicit geometry commands to match the drawing labels precisely.
# Let's define the path in a counter-clockwise manner.

# 1. Bottom Loop (The oval at the bottom)
# Width = 10.2, Height = 105.0
# We construct this as an ellipse.
# Center of bottom loop: (x=0, y=0) relative to sketch origin (later moved)
# Major Axis = 105.0, Minor Axis = 10.2
ellipse_bottom = sketch.addGeometry(Part.Ellipse(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 105.0/2, 10.2/2))

# 2. Bottom Neck (Straight line up from the bottom of the oval)
# Length = 24.93
# Start point of this line is at (0, -105.0/2)
# End point is (0, -105.0/2 + 24.93)
p_bottom_neck_start = App.Vector(0, -105.0/2, 0)
p_bottom_neck_end = p_bottom_neck_start + App.Vector(0, 24.93, 0)
line_bottom_neck = sketch.addGeometry(Part.LineSegment(p_bottom_neck_start, p_bottom_neck_end))

# 3. Bottom Transition (Curved section)
# This looks like a fillet or a curve connecting the neck to the main body.
# The drawing labels a fillet radius R17.45 (inferred from 1.745 mm * 10? No, looking at scale, it's likely 1.745mm or 17.45mm). 
# Let's re-examine the drawing. The scale is 0.600.
# If 105.0 on drawing is 105mm real size, then 105/0.6 = 175mm? No.
# If 105.0 is 175mm real size, then 105/175 = 0.6. Correct.
# So the drawing dimension 105.0 means 105mm real size.
# The label R174.5 is likely 17.45mm (typo in drawing or scale factor).
# Let's assume the labels are the real dimensions.
# Radius = 17.45mm.
# The curve connects (0, -105/2 + 24.93) to the side of the body.
# Let's approximate this as a fillet on the corner or a spline.
# Given the "smooth" look, a fillet is best.
# But the body width changes from 27.5 to ...?
# Let's trace the path.
# The bottom loop is width 10.2. The main body is width 27.5.
# The transition is complex. Let's simplify the construction to match the drawing exactly.
# The drawing shows a curve R174.5. Let's use a Fillet feature or a constructed spline.
# For a script, we can use a spline if we define points.
# Or we can use a Fillet on the sharp corner if we create it.
# Let's create the sharp corner first:
# Point A: (0, -105/2 + 24.93) -> (0, -52.5 + 24.93) = (0, -27.57)
# Point B: (27.5/2, -105/2 + 24.93) = (13.75, -27.57)
# But the bottom loop is at (0, -52.5) to (0, 52.5).
# Wait, the bottom loop is centered at (0, 0)?
# Let's re-orient the sketch to make it easier.
# Center the bottom loop at (0, -105.0/2). Then the top of the loop is (0, 0).
# This matches the "bottom loop height" 105.0 and "bottom neck length" 24.93.

# RE-ORIGINATING SKETCH
# Move ellipse_bottom center to (0, -105.0/2)
sketch.addConstraint(Sketcher.Constraint("Position", ellipse_bottom, 1, "YCenter", 0, 0)) # This doesn't move it, it constrains it.
# Actually, let's just build the path from the bottom up.

# --- Rebuilding the Sketch from Scratch (Bottom to Top) ---
# Origin: Bottom of the bottom loop.

# 1. Bottom Loop (Ellipse)
# Minor radius (width/2) = 10.2 / 2 = 5.1
# Major radius (height/2) = 105.0 / 2 = 52.5
# Center: (0, 0)
ellipse_bottom = sketch.addGeometry(Part.Ellipse(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 52.5, 5.1))

# 2. Bottom Neck (Vertical Line)
# Start: Bottom of ellipse (0, -52.5)
# End: (0, -52.5 + 24.93) = (0, -27.57)
start_bottom_neck = App.Vector(0, -52.5, 0)
end_bottom_neck = App.Vector(0, -27.57, 0)
line_bottom_neck = sketch.addGeometry(Part.LineSegment(start_bottom_neck, end_bottom_neck))

# 3. Transition Curve
# The drawing shows a radius R174.5. Let's assume 17.45mm.
# The curve connects the top of the neck to the side of the body.
# The body width is 27.5. So the side is at x = 27.5/2 = 13.75.
# The curve starts at (0, -27.57) and ends at (13.75, -27.57)?
# No, the curve must go upwards to the body.
# Let's look at the shape. It's a fillet.
# The corner is at (0, -27.57). The body side is at x=13.75.
# If it's a fillet, the curve is tangent to the neck and the body side.
# But the body side is not horizontal, it's vertical.
# So the fillet center would be at (13.75, -27.57 + 17.45) = (13.75, -10.12)?
# And the radius is 17.45.
# Let's check if the curve reaches the body width.
# The curve would end at (13.75 - 17.45, -27.57) = (-3.68, -27.57)? No.
# The curve is between the neck and the body.
# Let's assume the "R174.5" is the radius of the transition.
# The transition length is 90.58.
# The transition length is the distance along the curve? Or the vertical projection?
# Usually in drawings, it's the vertical dimension.
# So the curve goes from y = -27.57 to y = -27.57 + 90.58 = 63.01.
# And x goes from 0 to 13.75.
# This is a complex curve. Let's approximate it with a spline if needed, 
# but a fillet is simpler.
# Let's create a sharp corner at (0, -27.57) and (13.75, -27.57) and fillet it.
# Then we have a horizontal line from (13.75, -27.57) to (13.75, 63.01).
# Then the main body width is 27.5. So the other side is at x = -13.75.
# So the transition is on the RIGHT side (x > 0).
# The LEFT side is symmetric.

# Let's build the profile as a closed loop.
# Path: 
# 1. Left Side of Bottom Loop: Arc from (0, -52.5) to (-13.75, -52.5) ? No, ellipse.
# Let's just define the vertices and connect them.

# Vertices:
# V1: (0, -52.5) # Bottom of bottom loop
# V2: (-5.1, -52.5) # Left of bottom loop
# V3: (-5.1, -105) # Bottom of bottom loop (Left side) -> Wait, ellipse is centered at (0,0).
# V_left_bottom = App.Vector(-5.1, -52.5, 0)
# V_right_bottom = App.Vector(5.1, -52.5, 0)
# V_top_bottom = App.Vector(0, 52.5, 0)

# Let's trace the perimeter clockwise from the bottom.
# P1: (0, -52.5)
# P2: (5.1, -52.5) # Right of bottom loop
# P3: (5.1, -27.57) # End of bottom neck (Right side)
# P4: (13.75, -27.57) # Start of body side (Right side)
# P5: (13.75, 63.01) # End of transition (Right side)
# P6: (0, 63.01 + 13.17) = (0, 76.18) # Top of transition (Center)
# P7: (0, 76.18 + 5.1) = (0, 81.28) # Start of top loop
# P8: (16.535, 81.28) # Right of top loop (Width 33.07 / 2 = 16.535)
# P9: (16.535, 81.28 + 1.8) = (16.535, 83.08) # Top of top loop (Height 3.6? No, R1.8)
# P10: (0, 83.08) # Top of top loop (Center)
# P11: (-16.535, 83.08) # Left of top loop
# P12: (-16.535, 81.28) # Bottom of top loop
# P13: (-13.75, 81.28) # Start of body side (Left side)
# P14: (-13.75, 63.01) # End of transition (Left side)
# P15: (-5.1, 63.01) # Start of bottom neck (Left side)
# P16: (-5.1, -52.5) # Left of bottom loop

# Now we need to connect these points.
# P1-P2: Arc (part of ellipse)
# P2-P3: Line
# P3-P4: Line
# P4-P5: Line (Side of body)
# P5-P6: Line (Transition side)
# P6-P7: Line (Top of transition)
# P7-P8: Line (Side of top loop)
# P8-P9: Arc (Top of top loop)
# P9-P10: Line (Top of top loop)
# P10-P11: Line (Top of top loop)
# P11-P12: Arc (Bottom of top loop)
# P12-P13: Line
# P13-P14: Line (Side of body)
# P14-P15: Line (Transition side)
# P15-P16: Line
# P16-P1: Arc (part of ellipse)

# Let's simplify the "Transition".
# The drawing shows a curve R174.5.
# It connects (13.75, -27.57) to (0, 63.01)?
# No, the transition is on the side.
# The drawing shows the curve R174.5 is on the INSIDE of the body.
# So the body width is 27.5. The inner radius is R174.5.
# This implies the body is not a rectangle, but a shape with rounded corners.
# Let's assume the body is a rectangle with rounded corners (R17.45).
# Width = 27.5, Height = 90.58 + 13.17 = 103.75 (from bottom neck top to top neck bottom).
# Let's check the drawing again.
# The transition length is 90.58.
# The neck length is 13.17.
# The bottom neck length is 24.93.
# The bottom loop height is 105.0.
# The top loop width is 33.07.
# The top loop height is ...?
# The drawing shows R1.8 for the top loop. So height is 3.6.
# The drawing shows R174.5 for the transition.

# Let's build the sketch using a "Spline" to fit the R17.45 curve.
# But FreeCAD's Sketcher doesn't have a direct "Fillet Spline" command in the API.
# We can use a "Fillet" feature on the body, but the base must be a polygon.
# So, let's create a base polygon (rectangle with straight lines) and then use a Fillet feature.
# The base polygon:
# 1. Left Side of Bottom Loop: Arc from (-5.1, -52.5) to (-5.1, 52.5) ? No, it's an ellipse.
# Let's just use the ellipse for the bottom loop.
# Then a vertical line from (-5.1, -52.5) to (-5.1, 52.5) ? No.
# The bottom loop is width 10.2. The body is width 27.5.
# So the bottom loop is narrower than the body.
# The transition is on the side of the body.
# So the profile is:
# - Bottom Loop (Ellipse, W=10.2, H=105.0)
# - Two vertical lines (Bottom Necks) from the top of the ellipse to the start of the body.
# - The Body (Rectangle, W=27.5, H=103.75) with rounded corners
