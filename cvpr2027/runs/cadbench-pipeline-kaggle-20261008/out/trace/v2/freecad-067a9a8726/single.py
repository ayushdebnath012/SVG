import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize document
doc = App.newDocument("HexNut")

# --- Parameters ---
# Define a VarSet to hold editable parameters
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "through_hole_diameter", "Dimensions", "Diameter of the central through-hole")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the nut")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of the circular flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Width of the hexagonal drive")
params.addProperty("App::PropertyLength", "hex_head_height", "Dimensions", "Height of the hexagonal head")

# Set default values as per specification
params.through_hole_diameter = 18.0
params.overall_height = 27.0
params.flange_diameter = 34.0
params.flange_thickness = 5.0
params.hub_width = 27.0
params.hex_head_height = 22.0 # Calculated as 27.0 - 5.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange) ---
# Create sketch on XY plane
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.ConstrainAuto = True
sketch_flange.TechDrawPictogramSequence = 1
sketch_flange.ViewObject.DisplayMode = "Flat"

# Add Circle for Flange
circle_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0)
sketch_flange.addGeometry(circle_flange, False)

# Add Center Point
point_center = Part.Point(App.Vector(0, 0, 0))
sketch_flange.addGeometry(point_center, False)

# Add Constraint: Coincident center
sketch_flange.addConstraint(Sketcher.Constraint("Center", 0, 0))

# --- Hex Profile Sketch ---
# Create sketch on XZ plane (rotated 90 deg around Y to stand up)
# We will place this sketch at Z = flange_thickness
sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hex.ConstrainAuto = True
sketch_hex.TechDrawPictogramSequence = 1
sketch_hex.ViewObject.DisplayMode = "Flat"

# Define Hexagon vertices
# Width = hub_width. Distance from center to flat side = hub_width / 2
# Distance from center to vertex = hub_width / (2 * cos(30)) = hub_width / sqrt(3)
# Let's use standard hexagon construction: 6 lines.
# Center point
point_hex = Part.Point(App.Vector(0, 0, 0))
sketch_hex.addGeometry(point_hex, False)

# Vertices relative to center on XZ plane
# Angle 0, 60, 120, 180, 240, 300 degrees
# Radius R = hub_width / (2 * cos(30))
R_hex = params.hub_width / (2 * (3**0.5))

vertices = []
for i in range(6):
    angle = i * 60
    x = R_hex * App.Vector(cos(angle), sin(angle), 0).X
    z = R_hex * App.Vector(cos(angle), sin(angle), 0).Z
    vertices.append(App.Vector(x, 0, z))

# Add lines connecting vertices
for i in range(6):
    p1 = vertices[i]
    p2 = vertices[(i + 1) % 6]
    line = Part.LineSegment(p1, p2)
    sketch_hex.addGeometry(line, False)

# Add constraints to define the hexagon shape relative to center
# We need to constrain vertices to be equidistant from center and at 60 degree intervals.
# Simplified approach: Constrain all vertices to be distance R_hex from center.
# And constrain adjacent vertices to be distance hub_width apart? No, that's chord length.
# Chord length = 2 * R * sin(30) = R. So chord length = R_hex.
# Wait, width across flats = 2 * R * cos(30) = hub_width.
# So R = hub_width / sqrt(3).
# Distance between adjacent vertices (side length) = R.
# So we constrain distance between adjacent vertices to be R_hex.

for i in range(6):
    p1 = vertices[i]
    p2 = vertices[(i + 1) % 6]
    # Constrain distance between p1 and p2
    sketch_hex.addConstraint(Sketcher.Constraint("Distance", i, 1, 1, 2, 1)) # This syntax is tricky in headless without indices
    
    # Better: Constrain distance from center to each vertex
    # Sketcher constraints use indices of geometries.
    # Geometry 0 is point_hex. Geometry 1..6 are lines.
    # We need to add vertices as geometry.
    # Let's re-add vertices explicitly as points.
    pass

# Re-doing sketch hex geometry addition properly
sketch_hex.clearGeometry()
sketch_hex.clearConstraints()

# Add Center Point
sketch_hex.addGeometry(point_hex, False)

# Add Vertices
for v in vertices:
    sketch_hex.addGeometry(Part.Point(v), False)

# Add Lines
for i in range(6):
    p1 = vertices[i]
    p2 = vertices[(i + 1) % 6]
    sketch_hex.addGeometry(Part.LineSegment(p1, p2), False)

# Add Constraints
# 1. Center point is at origin (0,0)
sketch_hex.addConstraint(Sketcher.Constraint("Center", 0, 0))

# 2. All vertices are distance R_hex from center
for i, v in enumerate(vertices):
    idx = i + 1 # Index of point in sketch
    sketch_hex.addConstraint(Sketcher.Constraint("Distance", 0, 1, idx, 1, 0)) # Distance from center (0) to point (idx)

# 3. Adjacent vertices are distance R_hex apart (side length)
for i in range(6):
    idx1 = i + 1
    idx2 = (i + 2) % 6 + 1
    sketch_hex.addConstraint(Sketcher.Constraint("Distance", idx1, 1, idx2, 1, 0))

# --- Through Hole Sketch ---
# Create sketch on XY plane at Z = overall_height - flange_thickness (top of flange)
# Actually, let's make the hole go through the whole nut.
# We can create a sketch at Z=0 (on the flange face) and pad it through all.
# Or create a sketch at the top face and pad down.
# Let's create a sketch at Z = overall_height - flange_thickness (top of flange)
# Wait, the flange is at the bottom. The nut sits on the flange.
# So the hole starts at Z = flange_thickness and goes up to Z = overall_height.
# Let's create the hole sketch at Z = flange_thickness.

sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hole.ConstrainAuto = True
sketch_hole.TechDrawPictogramSequence = 1
sketch_hole.ViewObject.DisplayMode = "Flat"

# Add Circle for Hole
circle_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2.0)
sketch_hole.addGeometry(circle_hole, False)

# Add Center Point
point_hole = Part.Point(App.Vector(0, 0, 0))
sketch_hole.addGeometry(point_hole, False)

# Add Constraint: Center
sketch_hole.addConstraint(Sketcher.Constraint("Center", 0, 0))

# --- Features ---

# 1. Pad Flange
# Profile: Sketch_Flange
# Length: flange_thickness
# Direction: +Z (upwards from Z=0)
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_flange
pad_flange.Length = params.flange_thickness
pad_flange.Type = "Solid"
pad_flange.MidPlane = False
pad_flange.Reversed = False

# 2. Pad Hex Head
# Profile: Sketch_Hex
# Length: hex_head_height
# Direction: +Z (upwards from Z=flange_thickness)
pad_hex = body.newObject("PartDesign::Pad", "Pad_Hex")
pad_hex.Profile = sketch_hex
pad_hex.Length = params.hex_head_height
pad_hex.Type = "Solid"
pad_hex.MidPlane = False
pad_hex.Reversed = False

# 3. Pocket Through Hole
# Profile: Sketch_Hole
# Length: overall_height - flange_thickness (from top of flange to top of nut)
# Wait, the hole needs to go through the hex head too.
# The sketch is at Z = flange_thickness.
# The hole needs to go from Z = flange_thickness to Z = overall_height.
# So length = overall_height - flange_thickness.
# Type: ThroughAll? No, we need specific length.
# But wait, if we use ThroughAll, it goes through the whole body.
# The body is Flange (0 to 5) + Hex (5 to 27). Total 27.
# If we pocket from Z=5 with length 22, it goes to Z=27.
# This creates a hole from Z=5 to Z=27.
# Is there material below Z=5? Yes, the flange.
# So the hole is NOT through the flange.
# The requirement says "central plain through-hole ... runs axially through the full nut height".
# This implies the hole goes all the way through the flange too?
# "High-profile external-hex flange nut". Usually, the flange is solid, and the hole is in the nut part.
# However, "through-hole ... through the full nut height" suggests the hole exists for the entire 27mm.
# If the flange is 5mm thick, the hole must go through the flange as well.
# Let's re-read: "central plain through-hole ... runs axially through the full nut height".
# This implies the hole is present from Z=0 to Z=27.
# So we need to pocket the hole from Z=0 to Z=27.
# My sketch is at Z=5.
# If I pocket with Length = 27, it goes from Z=5 to Z=32. That's wrong.
# If I pocket with Length = 22, it goes from Z=5 to Z=27. That leaves the flange solid.
# To get a hole through the flange, I need to either:
# a) Move the sketch to Z=0 and pocket length 27.
# b) Create a separate pocket for the flange part.
# Let's move the sketch to Z=0 and pocket length 27.
# But the flange is a circle. The hole is a circle.
# If I pad the flange first (0 to 5), then pocket the hole (0 to 27), the hole will cut through the flange.
# This matches "through the full nut height".

# Correction:
# Move Sketch_Hole to Z=0.
# Update Sketch_Hole Placement.
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))

# Re-create the hole sketch geometry with new placement?
# No, just update placement. The geometry is relative to the sketch origin.
# The sketch origin is at (0,0,0) in world space now.
# The circle is at (0,0,0) relative to sketch.
# So in world space, it is at (0,0,0).
# This is correct.

# Now, Pad Flange (0 to 5)
# Pad Hex (5 to 27)
# Pocket Hole (0 to 27) -> This will cut through the flange and the hex.

# Let's adjust the order of operations to ensure clean topology.
# 1. Pad Flange (0 to 5)
# 2. Pad Hex (5 to 27)
# 3. Pocket Hole (0 to 27)

# Wait, if I pad flange first, then pad hex, the union is created.
# Then I pocket the hole.
# The pocket will start at Z=0 and go to Z=27.
# This works perfectly.

# Update Sketch_Hole placement
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))

# Re-add geometry to ensure it's at the new location? 
# Actually, the sketch geometry is defined relative to the sketch's local coordinate system.
# The Placement transforms the sketch to world space.
# So if I change Placement to (0,0,0), the circle stays at (0,0,0).
# This is correct.

# However, I need to make sure the sketch is valid.
# Let's just re-add the circle and point to be safe, or rely on the existing geometry being transformed.
# In FreeCAD, changing Placement updates the geometry position.
# So I will just update the placement.

# Wait, I need to re-add the geometry because I cleared it earlier in the thought process?
# No, I didn't clear it in the code block above, I just thought about it.
# But I did `sketch_hex.clearGeometry()` in the thought process.
# Let's assume the code below is the final version.

# Let's refine the code structure to be clean.

# --- Revised Code Structure ---

# 1. Parameters
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "through_hole_diameter", "Dimensions", "Diameter of the central through-hole")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the nut")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of the circular flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Width of the hexagonal drive")
params.addProperty("App::PropertyLength", "hex_head_height", "Dimensions", "Height of the hexagonal head")

params.through_hole_diameter = 18.0
params.overall_height = 27.0
params.flange_diameter = 34.0
params.flange_thickness = 5.0
params.hub_width = 27.0
params.hex_head_height = 22.0

# 2. Body
body = doc.addObject("PartDesign::Body", "Body")

# 3. Sketch Flange (at Z=0)
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.ConstrainAuto = True
sketch_flange.TechDrawPictogramSequence = 1
sketch_flange.ViewObject.DisplayMode = "Flat"

circle_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0)
sketch_flange.addGeometry(circle_flange, False)
point_center = Part.Point(App.Vector(0, 0, 0))
sketch_flange.addGeometry(point_center, False)
sketch_flange.addConstraint(Sketcher.Constraint("Center", 0, 0))

# 4. Sketch Hex (at Z=flange_thickness)
sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hex.ConstrainAuto = True
sketch_hex.TechDrawPictogramSequence = 1
sketch_hex.ViewObject.DisplayMode = "Flat"

# Hexagon vertices
R_hex = params.hub_width / (2 * (3**0.5))
vertices = []
for i in range(6):
    angle = i * 60
    x = R_hex * App.Vector(cos(angle), sin(angle), 0).X
    z = R_hex * App.Vector(cos(angle), sin(angle), 0).Z
    vertices.append(App.Vector(x, 0, z))

# Add Center Point
point_hex = Part.Point(App.Vector(0, 0, 0))
sketch_hex.addGeometry(point_hex, False)

# Add Vertices
for v in vertices:
    sketch_hex.addGeometry(Part.Point(v), False)

# Add Lines
for i in range(6):
    p1 = vertices[i]
    p2 = vertices[(i + 1) % 6]
    sketch_hex.addGeometry(Part.LineSegment(p1, p2), False)

# Add Constraints
sketch_hex.addConstraint(Sketcher.Constraint("Center", 0, 0))
for i, v in enumerate(vertices):
    idx = i + 1
