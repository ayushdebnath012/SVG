import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure the script is self-contained and portable
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Parameters
P = {
    "lower_horizontal_width": 584.20,
    "clip_wall_thickness": 6.35,
    "upper_horizontal_width": 635.0,
    "outer_upper_vertical_edge_height": 190.50,
    "outer_v_apex_height": 45.99,
    "outer_slant_edge_vertical_height": 101.60,
    "outer_lower_vertical_edge_height": 25.4,
    "retention_slot_corner_radius": 0.0,
    "clip_length": 76.2
}

# --- Document Setup ---
doc = App.newDocument("Clip")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We create a VarSet to hold the parameters as editable properties
params = body.newObject("App::VarSet", "Parameters")
for name, value in P.items():
    params.addProperty("App::PropertyLength", name, "Parameters", name)
    setattr(params, name, value)

# --- Sketch 1: Outer Profile ---
# We define the profile in the XZ plane (Y=0). 
# The sketch will be placed on the XY plane of the body, but we will orient it 
# so that the drawing happens in the XZ plane (using Z as the vertical axis of the sketch).
# Actually, standard practice in PartDesign is to draw on a plane. 
# Let's draw on the XY plane of the body, but interpret the sketch coordinates such that:
# Sketch X -> Part X
# Sketch Y -> Part Z (Vertical)
# This requires a specific placement or just drawing on the XZ plane.
# Let's use the XZ plane of the body.

sketch_outer = body.newObject("Sketcher::SketchObject", "OuterProfile")
sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_outer.Support = "XZ_Plane"
sketch_outer.ConstrainToCurrentPlane = True
sketch_outer.MapMode = "FlatFace"

# Define points for the right half of the profile (X > 0).
# The profile is symmetric about X=0.
# Coordinates (X, Z):
# 1. Start at bottom center: (0, 0)
# 2. Go right to lower bridge end: (lower_horizontal_width/2, 0)
# 3. Go up outer_lower_vertical_edge_height: (lower_horizontal_width/2, outer_lower_vertical_edge_height)
# 4. Go up-right (slant): 
#    Run = (upper_horizontal_width - lower_horizontal_width) / 2
#    Rise = outer_slant_edge_vertical_height
#    End: (lower_horizontal_width/2 + Run, outer_lower_vertical_edge_height + outer_slant_edge_vertical_height)
# 5. Go up outer_upper_vertical_edge_height:
#    End: (lower_horizontal_width/2 + Run, outer_lower_vertical_edge_height + outer_slant_edge_vertical_height + outer_upper_vertical_edge_height)
# 6. Go left to top center: (0, same Z)
# 7. Go down to V apex: (0, outer_v_apex_height)
# 8. Close to start.

# Let's calculate the intermediate X coordinate for the slant top
x_slant_top = P["lower_horizontal_width"] / 2 + (P["upper_horizontal_width"] - P["lower_horizontal_width"]) / 2
z_slant_top = P["outer_lower_vertical_edge_height"] + P["outer_slant_edge_vertical_height"]
z_top = z_slant_top + P["outer_upper_vertical_edge_height"]

# Points for Right Half (Counter-Clockwise for normal outward, or just consistent loop)
# Let's trace: Bottom-Center -> Bottom-Right -> Slant-Top-Right -> Top-Right -> Top-Center -> V-Apex -> Bottom-Center
# Wait, the V apex is at the centerline. The path goes from Top-Right -> Top-Center -> V-Apex -> Bottom-Center?
# No, the description says: "From their upper endpoints, two equal diagonal legs descend inward and meet on the profile centerline at outer_v_apex_height".
# So the path is: Top-Right -> Top-Center -> V-Apex -> Bottom-Center? 
# Actually, usually the V is at the bottom of the upper section.
# Let's re-read: "central V-shaped return".
# Path: 
# 1. (0,0)
# 2. (L/2, 0)
# 3. (L/2, h_lower)
# 4. (x_slant, h_lower + h_slant)
# 5. (x_slant, h_lower + h_slant + h_upper)
# 6. (0, h_lower + h_slant + h_upper)  <-- Top Center
# 7. (0, h_v_apex)                     <-- V Apex
# 8. (0, 0)                            <-- Close? 
# Wait, if we go 6->7->8, we have a vertical line down the center. 
# The V shape implies the line comes from Top-Right to V-Apex, then V-Apex to Bottom-Left?
# "From their upper endpoints... descend inward and meet... at outer_v_apex_height".
# This implies the V is formed by the legs. The bottom of the V is at the centerline.
# Does the profile close at the bottom center? Yes, it's a closed loop.
# So the sequence is:
# Start (0,0) -> (L/2, 0) -> (L/2, h_lower) -> (x_slant, h_lower+h_slant) -> (x_slant, h_top) -> (0, h_top) -> (0, h_v_apex) -> (0,0).
# This creates a vertical line from h_top to h_v_apex and then to 0.
# Is that a "V-shaped return"? 
# Usually, a clip like this has the V at the bottom, connecting the two sides.
# If the V apex is at h_v_apex, and the bottom is at 0, there is a gap between the V apex and the bottom bridge?
# Or does the V apex connect to the bottom bridge?
# "meet on the profile centerline at outer_v_apex_height".
# If the bottom bridge is at Z=0, and the V apex is at Z=45.99, then the V is floating?
# Or is the "lower bridge" the bottom part, and the V is the return part above it?
# Let's assume the geometry is:
# Bottom Bridge (Z=0 to Z=h_lower)
# Slant (Z=h_lower to Z=h_lower+h_slant)
# Top Vertical (Z=h_lower+h_slant to Z=h_top)
# Top Horizontal (Z=h_top)
# Then the V shape connects the Top Horizontal ends to the Centerline at Z=h_v_apex.
# Then from Z=h_v_apex, does it go down to Z=0?
# If it goes straight down to Z=0, it's a vertical line.
# If the V is the "return", maybe the bottom of the V connects to the bottom of the clip?
# But the height is 45.99, and the lower bridge is 25.4.
# If the V apex is at 45.99, and the bottom is at 0, the V apex is above the bottom bridge.
# This implies the "V-shaped return" is the feature that goes from the top corners down to the centerline at 45.99.
# And then presumably back up? Or is the bottom of the V connected to the bottom bridge?
# If the bottom of the V (apex) is at 45.99, and the bottom bridge is at 0, there is a gap.
# Unless the "lower bridge" is not at Z=0, but the V apex is the lowest point?
# "outer_lower_vertical_edge_height = 25.4". This is the height of the vertical edge rising from the lower bridge.
# So the lower bridge is at Z=0. The vertical edge goes to Z=25.4.
# The V apex is at Z=45.99.
# This means the V apex is HIGHER than the top of the lower vertical edge.
# So the sequence must be:
# Bottom Bridge (0 to 25.4)
# Slant (25.4 to 25.4+101.6 = 127.0)
# Top Vertical (127.0 to 127.0+190.5 = 317.5)
# Top Horizontal (317.5)
# Then from Top Horizontal ends, legs go down to V Apex (45.99).
# Then from V Apex, legs go down to Bottom Bridge (0)?
# If so, the V apex is just a point on the centerline. The profile would look like a 'U' with a V cut out of the top?
# No, "V-shaped return" usually means the part that returns to the center.
# Let's assume the profile is:
# 1. (0,0) -> (L/2, 0)
# 2. (L/2, 25.4)
# 3. (x_slant, 25.4+101.6)
# 4. (x_slant, 25.4+101.6+190.5)
# 5. (0, 25.4+101.6+190.5)
# 6. (0, 45.99)  <-- V Apex
# 7. (0, 0)      <-- Close
# This creates a vertical line from 317.5 down to 45.99, then down to 0.
# This is not a "V". This is a vertical line with a kink.
# 
# Alternative Interpretation:
# The "V-shaped return" is the bottom part.
# Maybe the "lower bridge" is the top of the V?
# "centered lower bridge... At each end, an outer lower vertical edge rises...".
# This implies the bridge is at the bottom.
# "From their upper endpoints... descend inward and meet... at outer_v_apex_height".
# If the V apex is at 45.99, and the bottom is at 0, the V apex is above the bottom.
# This implies the V is the top part of the return?
# Let's reconsider the shape. A "retaining clip" often has a C-shape or U-shape.
# If it's a "Z-shaped side", it goes Up, Slant, Up.
# Then the "V-shaped return" connects the tops.
# If the V apex is at 45.99, and the bottom is at 0, the V apex is floating.
# UNLESS the "lower bridge" is not at Z=0, but the V apex is the lowest point?
# But "outer_lower_vertical_edge_height" is 25.4. If the V apex is the lowest, then the vertical edge must start above the V apex?
# That contradicts "rises by...".
# 
# Let's assume the standard interpretation:
# The profile is defined by the outer boundary.
# The V apex is at Z=45.99.
# The bottom of the clip is at Z=0.
# The V apex is connected to the bottom of the clip?
# If the V apex is at 45.99, and the bottom is at 0, there must be a segment connecting them.
# If the V is "return", maybe it goes from Top-Right -> V-Apex -> Bottom-Left?
# If so, the path is:
# (0,0) -> (L/2, 0) -> (L/2, 25.4) -> (x_slant, 127.0) -> (x_slant, 317.5) -> (0, 317.5) -> (0, 45.99) -> (0,0).
# This creates a vertical line from 317.5 to 45.99, then 45.99 to 0.
# This is a "step" down the center, not a V.
# 
# What if the "V-shaped return" is the bottom part, and the "lower bridge" is the top of the V?
# "centered lower bridge... At each end, an outer lower vertical edge rises".
# This implies the bridge is the base.
# Maybe the V apex is at the bottom?
# "meet on the profile centerline at outer_v_apex_height".
# If the V apex is at 45.99, and the bottom is at 0, then the V apex is NOT the bottom.
# 
# Let's try a different topology:
# The clip is a "Z" shape.
# Left side: Up, Slant, Up.
# Right side: Up, Slant, Up.
# Connected by a bottom bridge.
# And a "V-shaped return" in the middle.
# Maybe the V is formed by the two upper vertical edges meeting? No, they are separated by upper_horizontal_width.
# Maybe the V is formed by the slanted edges? No, they are outer.
# 
# Let's assume the V apex is the lowest point of the upper section, and the bottom bridge is separate?
# No, it's a single solid.
# 
# Let's assume the V apex is at Z=45.99, and the bottom bridge is at Z=0.
# The connection between the V apex and the bottom bridge is a vertical line?
# If so, the shape is:
# Bottom Bridge (0 to 25.4)
# Slant (25.4 to 127.0)
# Top Vertical (127.0 to 317.5)
# Top Horizontal (317.5)
# V Legs (317.5 to 45.99)
# Center Vertical (45.99 to 0)
# This is a valid closed loop. It looks like a bucket with a V-shaped handle attachment point?
# Or maybe the "V-shaped return" is the part that goes from the top corners down to the V apex, and then the V apex connects to the bottom bridge via a vertical line?
# This seems the most logical interpretation of the dimensions provided.
# The "V" is the shape formed by the two legs descending from the top corners to the centerline.
# The "return" might refer to the fact that it returns to the centerline.
# The vertical line from the V apex to the bottom bridge is just a connector.
# 
# Let's proceed with this geometry.
# Points for Right Half:
# 1. (0, 0)
# 2. (L/2, 0)
# 3. (L/2, h_lower)
# 4. (x_slant, h_lower + h_slant)
# 5. (x_slant, h_top)
# 6. (0, h_top)
# 7. (0, h_v_apex)
# 8. (0, 0)

# Add Geometry
# We need to add lines and constraints.
# Since we are using Part.LineSegment, we can just add the segments.
# However, for a clean sketch, we should add points and constraints.
# But for simplicity and robustness in a script, adding segments directly is often easier if we trust the coordinates.
# Let's add segments.

# Segment 1: (0,0) to (L/2, 0)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(P["lower_horizontal_width"]/2, 0, 0)), False)
# Segment 2: (L/2, 0) to (L/2, h_lower)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(P["lower_horizontal_width"]/2, 0, 0), App.Vector(P["lower_horizontal_width"]/2, 0, P["outer_lower_vertical_edge_height"])), False)
# Segment 3: (L/2, h_lower) to (x_slant, h_lower+h_slant)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(P["lower_horizontal_width"]/2, 0, P["outer_lower_vertical_edge_height"]), App.Vector(x_slant, 0, P["outer_lower_vertical_edge_height"] + P["outer_slant_edge_vertical_height"])), False)
# Segment 4: (x_slant, h_lower+h_slant) to (x_slant, h_top)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(x_slant, 0, P["outer_lower_vertical_edge_height"] + P["outer_slant_edge_vertical_height"]), App.Vector(x_slant, 0, P["outer_lower_vertical_edge_height"] + P["outer_slant_edge_vertical_height"] + P["outer_upper_vertical_edge_height"])), False)
# Segment 5: (x_slant, h_top) to (0, h_top)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(x_slant, 0, P["outer_lower_vertical_edge_height"] + P["outer_slant_edge_vertical_height"] + P["outer_upper_vertical_edge_height"]), App.Vector(0, 0, P["outer_lower_vertical_edge_height"] + P["outer_slant_edge_vertical_height"] + P["outer_upper_vertical_edge_height"])), False)
# Segment 6: (0, h_top) to (0, h
