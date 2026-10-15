import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from task description
PARAMS = {
    "inner_diameter": 8.0,
    "overall_height": 8.0,
    "flange_diameter": 17.9,
    "flange_thickness": 3.5,
    "hex_head_width_across_flats": 13.0,
    "hex_head_width_across_corners": 13.0 / (3.0/5.0), # Approx cos(30) for simplicity in expression, or calculated directly
    "hex_head_angle": 30.0
}

# Pre-calculate corner width for convenience if expressions are too complex, 
# but we will use expressions for parametric integrity where possible.
# cos(30) is 0.866025... 
# 13 / 0.866025 = 15.0111...
# We will use the exact calculation in the script.

# --- Setup Document ---
doc = App.newDocument("HexNut")

# Define Planes (Standard XY_Plane at Z=0 is usually available, but let's ensure context)
# In FreeCAD 1.1, standard planes are often available as App::Placement or objects.
# We will use the standard XY_Plane object if it exists, otherwise create a Body and attach to it.
# Actually, PartDesign::Body usually attaches to existing planes.
# Let's try to get the XY_Plane.
try:
    xy_plane = doc.getObject("XY_Plane")
    if not xy_plane:
        # Fallback: Create a Body, then we might need to add planes if not standard.
        # However, standard FreeCAD installs usually have XY_Plane.
        # If not, we assume the environment provides it.
        pass
except:
    xy_plane = None

# Create Body
body = doc.addObject("PartDesign::Body", "HexNutBody")
body.Label = "HexNutBody"

# Add Parameters (Named properties)
# We use App::PropertyLength and App::PropertyInteger/Float as needed.
# To make them editable in the GUI (PropertyTree), we add them to the Body or a VarSet.
# The prompt suggests: body.newObject("App::VarSet", "Parameters")
params = body.newObject("App::Property", "Parameters") # Note: App::Property is generic, usually App::PropertyLength etc.
# Actually, standard way for named parameters in PartDesign is often just adding properties to the Body or a VarSet object.
# Let's use a VarSet object as per the hint in the system prompt, but ensure property types are correct.
varset = body.newObject("App::VarSet", "Parameters")

# Add parameters to the VarSet
varset.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Thread Hole")
varset.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Nut Height")
varset.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Flange")
varset.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange Thickness")
varset.addProperty("App::PropertyLength", "hex_across_flats", "Dimensions", "Hex Width")
varset.addProperty("App::PropertyLength", "hex_across_corners", "Dimensions", "Hex Width Diag")
varset.addProperty("App::PropertyAngle", "hex_angle", "Dimensions", "Hex Angle")

# Set values
varset.inner_diameter = PARAMS["inner_diameter"]
varset.overall_height = PARAMS["overall_height"]
varset.flange_diameter = PARAMS["flange_diameter"]
varset.flange_thickness = PARAMS["flange_thickness"]
varset.hex_across_flats = PARAMS["hex_head_width_across_flats"]
varset.hex_across_corners = PARAMS["hex_head_width_across_corners"]
varset.hex_angle = PARAMS["hex_head_angle"]

# --- Feature Construction ---

# 1. Flange Bottom Sketch
# Plane: XY (Z=0). Circle centered at (0,0).
flange_sketch = body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Plane = (doc.getObject("XY_Plane"), [""])
flange_sketch.ViewObject.DisplayMode = "Wire" # Just for clarity, not strictly necessary
flange_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), varset.flange_diameter / 2.0), False)
# Constraint: Center at origin
flange_sketch.addConstraint(Sketcher.Constraint("Center", 0, 1)) # Point 0 is circle, 1 is center? No, Sketcher constraint indices refer to geometry indices.
# Easier: Center constraint on the circle relative to the plane origin if possible, or just rely on the circle center.
# Actually, Sketcher::SketchObject has a 'Center' constraint type that centers the circle on the plane.
flange_sketch.addConstraint(Sketcher.Constraint("Center", 0)) 
# Center constraint on the first geometry (circle) aligns its center to the plane origin.
# Wait, 'Center' constraint in Sketcher aligns the center of a circle/ellipse to the origin of the plane.
# But we need to ensure the circle is created at 0,0. 
# The addGeometry with App.Vector(0,0,0) creates it there. The constraint ensures it stays there.

# 2. Flange Pad (Bottom)
# Direction: Z+ (Upwards).
flange_pad = body.newObject("PartDesign::Pad", "FlangePad")
flange_pad.Profile = flange_sketch
flange_pad.Length = varset.flange_thickness
flange_pad.Reverse = True # Grow downwards from Z=0 to Z=-thickness? 
# Usually, if we want the nut to sit on Z=0 and go up, we build Flange at Z=0 going UP?
# Let's rethink orientation.
# Standard: XY plane is at Z=0.
# Option A: Flange is at Z=0, Nut body is above it.
#   Sketch at Z=0. Pad grows +Z.
# Option B: Nut body is at Z=0, Flange is below.
#   Sketch at Z=0. Pad grows -Z.
# Let's do Option A: Flange at bottom (Z=0), Nut body on top.
#   Flange Pad: Length = thickness, Reverse = False (grows +Z).
#   Hex Sketch: Attached to top face of Flange Pad (Z = thickness).
#   Hex Pad: Grows +Z.

# Correction: If Flange is at Z=0 and grows +Z, the top face is at Z = thickness.
# The Hex sketch should be attached to that top face.
# Let's adjust the Flange Pad direction.
flange_pad.Reverse = False
flange_pad.setExpression("Length", "Parameters.flange_thickness")

# 3. Hex Nut Body Sketch
# Attach to the top face of the Flange Pad.
# We need to identify the top face. 
# PartDesign::SketchObject can attach to a face of a feature.
# We pass the Feature object and a list of faces (empty means all, but we want the top one).
# Actually, we can attach to the body's top face directly if we assume the body is built sequentially.
# Better: Attach to the "FlangePad" feature.
# The face index for the top of a cylinder is usually 0 (if convex) or we can specify.
# For a Pad growing from Z=0 to Z=thickness, the top face is the first face created? 
# Let's try attaching to the Body's top face generally, or specifically to the feature.
# Method: body.newObject(..., "HexSketch"). AttachmentSupport = (flange_pad, [""]) 
# This attaches to the first face of flange_pad.
hex_sketch = body.newObject("Sketcher::SketchObject", "HexSketch")
hex_sketch.Plane = (flange_pad, [""]) 
# Note: In 1.1, passing a Feature object directly to AttachmentSupport works for the first face.

# Define Hexagon geometry
# Width across flats = W. Radius of circumscribed circle = R = W / (2 * sin(30)) = W / 1.0 = W?
# Wait. Hexagon geometry:
# Distance between flats (minor diameter) = W.
# Distance between corners (major diameter) = W / cos(30) = W / 0.866 = 1.1547 * W.
# The vertices are at angles 0, 60, 120...
# If flat-to-flat is W, the distance from center to flat is W/2.
# The distance from center to corner is (W/2) / cos(30) = W / (2 * 0.866) = W / 1.732 = W * sqrt(3)/3?
# No. Let's visualize.
# Side length 'a'. Flat to flat = 2 * a * cos(30) = 1.732 * a.
# Corner to corner = 2 * a.
# Ratio Corner/Flat = 1 / cos(30) = 1.1547. Correct.
# We are given "width_across_flats" = 13.
# So we need a hexagon with flat-to-flat distance = 13.
# We can construct this using lines and constraints.
# Or use a circle with radius R_corner = 13 / (2 * cos(30))? 
# Distance center to corner = (Width_across_flats / 2) / cos(30) = 6.5 / 0.866 = 7.5055.
# Let's construct the hexagon explicitly using lines for precision.
# Points at angles 0, 60, 120... relative to the vertical?
# Standard orientation: Flat top/bottom? Or Pointy top/bottom?
# Nuts usually have flat top/bottom for stability.
# Let's make flat top/bottom.
# Then the first flat is horizontal.
# Vertices are at angles: 30, 90, 150, 210, 270, 330 degrees.
# Y-coords: +/- (R_corner). X-coords: +/- (R_corner * cos(60)) = +/- (R_corner / 2).
# Let R_corner = varset.hex_across_corners / 2.
# Wait, varset.hex_across_corners is the full width (corner to corner).
# So R_corner = varset.hex_across_corners / 2.

R_corner = varset.hex_across_corners / 2.0

# Add geometry points/lines
# We add lines connecting vertices.
# Vertex 1 (Top Right): (R_corner * cos(30), R_corner * sin(30))
# Vertex 2 (Top Left): (-R_corner * cos(30), R_corner * sin(30))
# ...
# Actually, simpler: Define 3 points and close the loop? No, Sketcher needs explicit lines or a closed shape.
# We can add 6 LineSegments.

# Helper to get coordinates
# Angle 0 is X-axis. 90 is Y-axis.
# We want flat top (Horizontal line).
# Top edge is at Y = R_corner.
# Top-Right corner: X = R_corner * cos(30), Y = R_corner.
# Top-Left corner: X = -R_corner * cos(30), Y = R_corner.

# Let's define the 6 vertices
# Angles: 30, 90, 150, 210, 270, 330
# Wait, if 90 is Y, then at 90 deg, x=0, y=R. That's a point.
# We want a flat top. So the top edge is horizontal.
# This means the vertices are at 30 and 150 degrees?
# At 30 deg: x = R*cos(30), y = R*sin(30).
# At 150 deg: x = R*cos(150), y = R*sin(150).
# The line connecting them is horizontal? Yes, sin(30)=0.5, sin(150)=0.5.
# So vertices at 30, 90, 150... create a pointy top.
# Vertices at 0, 60, 120... create a flat side?
# At 0: (R, 0). At 60: (R/2, R*sqrt(3)/2).
# This is getting confusing.
# Let's stick to: Flat Top.
# Top edge connects V1 and V2.
# V1 = (R_corner * cos(30), R_corner) ?? No.
# Distance from center to flat = W/2 = 6.5.
# So Y_max = 6.5.
# X at top corners = +/- sqrt(R_corner^2 - 6.5^2).
# But R_corner = W_across_corners / 2.
# Let's just calculate the coordinates based on the "Flat Top" requirement.
# Y_top = varset.hex_across_flats / 2.
# X_top = +/- sqrt( (varset.hex_across_corners/2)^2 - (varset.hex_across_flats/2)^2 )
# Wait, R_corner is distance to corner. Distance to flat is R_corner * cos(30).
# So Y_top = R_corner * cos(30) = (W_across_corners/2) * cos(30) = (W_across_flats/2). Consistent.
# X_top = R_corner * sin(30) = R_corner * 0.5.

# So vertices are at:
# Top-Right: (R_corner * 0.5, R_corner * 0.866) -> Wait, sin(60) = 0.866.
# Let's use angles 30 and 150 for the top corners?
# Angle 30: (R*cos30, R*sin30) = (0.866R, 0.5R). This is not flat top.
# Angle 60: (0.5R, 0.866R).
# Angle 120: (-0.5R, 0.866R).
# Line between 60 and 120 is horizontal.
# So we need vertices at 60, 120, 180, 240, 300, 0(360).
# Let's generate 6 lines.

# Pre-calculate geometry for the sketch
# We will add 6 LineSegments.
# Points:
# P0: (R_corner * cos(60), R_corner * sin(60))
# P1: (R_corner * cos(120), R_corner * sin(120))
# P2: (R_corner * cos(180), R_corner * sin(180))
# P3: (R_corner * cos(240), R_corner * sin(240))
# P4: (R_corner * cos(300), R_corner * sin(300))
# P5: (R_corner * cos(0), R_corner * sin(0))
# Then connect P0-P1-P2-P3-P4-P5-P0.

# Add Geometry
# We need to add 6 LineSegments.
# Note: Sketcher geometry indices are 0..N-1.
# We can add a single complex wire? No, sketcher.addGeometry adds one by one.
# We add 6 lines and then constrain them to be coincident/closed.
# Actually, adding 6 lines and constraining them to form a loop is tedious.
# Alternative: Add a closed wire? No, Part.LineSegment is added individually.
# Easier: Add 3 lines and use constraints? 
# Or add all 6 and use "Equal Length" and "Coincident" constraints.
# Let's add all 6 lines.

lines = []
for i in range(6):
    angle_rad = (60 * (i + 1)) * (3.1415926535 / 180) # Angles: 60, 120, 180, 240, 300, 360
    # Wait, the sequence 60, 120... 360(0) covers the circle.
    # Let's use angles: 60, 120, 180, 240, 300, 0.
    # Re-indexing for loop 0..5
    ang = 60 + i * 60
    px = R_corner * math.cos(math.radians(ang))
    py = R_corner * math.sin(math.radians(ang))
    # Store points to create lines later? 
    # We can add lines directly if we know start/end.
    # But we need to know the order.
    pass

import math

# Define points
pts = []
for i in range(6):
    ang = 60 + i * 60
    pts.append(App.Vector(R_corner * math.cos(math.radians(ang)), R_corner * math.sin(math.radians(ang)), 0))

# Add lines
for i in range(6):
    p1 = pts[i]
    p2 = pts[(i+1)%6]
    seg = Part.LineSegment(p1, p2)
    hex_sketch.addGeometry(seg, False)

# Constraints:
# 1. Center the hexagon at (0,0)
# 2. Ensure
