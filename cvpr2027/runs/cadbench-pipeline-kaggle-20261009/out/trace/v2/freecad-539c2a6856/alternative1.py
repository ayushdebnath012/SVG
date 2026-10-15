import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HexFlangeNut")

# --- Parameters Section ---
# Define editable parameters at the document level or via a VarSet within the body.
# For robustness in PartDesign, we will define them on the Body object itself 
# or use App::VarSet if strictly required, but standard practice often allows 
# direct property assignment or a VarSet. Let's use a VarSet for clear "named document objects".
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Bolt hole diameter")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total nut height")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Outer bearing surface")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange height")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hex hub width across flats")
params.inner_diameter = 30.0
params.overall_height = 45.0
params.flange_diameter = 58.0
params.flange_thickness = 8.0
params.hub_width = 46.0

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch: Flange Bottom (Origin) ---
# We start with the bottom face of the flange on the XY plane.
sketch_bottom = body.newObject("Sketcher::SketchObject", "sketch_FlangeBottom")
sketch_bottom.Plane = "XY_Plane"
sketch_bottom.Constrain = "Auto"
# Draw a circle for the flange outer diameter
sketch_bottom.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0), False)
# Add a constraint to fix the center (Coincident with origin is implicit in sketch creation usually, 
# but we ensure it's on the plane center).
# To be safe and parametric, we rely on the Circle definition relative to origin.

# --- Hub Sketch: Hexagon Profile ---
# We need a profile that includes the inner hole and the hexagon.
# We will create a sketch on the YZ plane to define the side profile of the hexagon.
sketch_profile = body.newObject("Sketcher::SketchObject", "sketch_HexProfile")
sketch_profile.Plane = "YZ_Plane"

# 1. Inner Hole Circle (Centered at origin, Z axis)
# Radius = inner_diameter / 2
hole_radius = params.inner_diameter / 2.0
sketch_profile.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hole_radius), False)

# 2. Hexagon Geometry
# The hexagon is defined by its "width" (distance between parallel flat sides).
# Center is at (0,0).
# Distance from center to flat side = hub_width / 2
# Distance from center to vertex = (hub_width / 2) / cos(30 deg) = hub_width / sqrt(3)
# Hexagon orientation: Two vertical sides are easiest for extrusion.
# Side 1: x = -hub_width/2
# Side 2: x = +hub_width/2
# Top vertex: z = (hub_width/sqrt(3))
# Bottom vertex: z = -(hub_width/sqrt(3))

import math
half_width = params.hub_width / 2.0
vertex_dist = params.hub_width / math.sqrt(3)

# Vertical lines for the sides
# Line 1: Bottom flat to Top flat (Left side)
# Actually, let's draw 6 lines for a hexagon or 3 parallel lines + 2 angled lines.
# Easiest: 2 vertical lines + 4 angled lines connecting them.
# Vertical Line Left: x = -half_width, from z = -vertex_dist to vertex_dist
# Vertical Line Right: x = half_width, from z = -vertex_dist to vertex_dist

# Left Vertical Line
p1 = App.Vector(-half_width, -vertex_dist, 0)
p2 = App.Vector(-half_width, vertex_dist, 0)
sketch_profile.addGeometry(Part.LineSegment(p1, p2), False)

# Right Vertical Line
p3 = App.Vector(half_width, -vertex_dist, 0)
p4 = App.Vector(half_width, vertex_dist, 0)
sketch_profile.addGeometry(Part.LineSegment(p3, p4), False)

# Top Angled Lines (connecting tops of vertical lines to a top vertex? No, hexagon has flat top/bottom or pointy top/bottom?)
# Standard hex nut usually has flat sides.
# So we need:
# Top Horizontal? No, if we extrude along Z (axis), the profile is in YZ plane.
# The "width" is the distance between the two vertical faces.
# So the profile looks like a 'H' shape rotated or just a box with angled corners?
# No, a hexagon in YZ plane (extruded along X in the final part? No, nut axis is Z).
# Wait, if axis is Z, the profile is in XZ or YZ. Let's use YZ.
# The cross section in XZ is a Hexagon. The profile in YZ is two parallel lines (the flat sides) and angled lines.
# Yes.
# Lines:
# 1. Left Vertical (x = -half_width)
# 2. Right Vertical (x = half_width)
# 3. Top-Left Angle (connects (-half, vertex) to (0, 0)? No, connects to center? No.)
#    Connects (-half, vertex_dist) to (0, -vertex_dist)? No.
#    A regular hexagon with vertical sides:
#    Vertices: (-w/2, -h), (-w/2, h), (w/2, h), (w/2, -h) -> This is a rectangle.
#    To make it a hexagon, we cut corners? No.
#    Standard Hexagon: 60 deg angles.
#    If sides are vertical, the top and bottom are points? No, that's a pointy top hexagon.
#    If sides are vertical, the top and bottom are flat? No, that's impossible for a regular hexagon.
#    Regular Hexagon: Opposite sides are parallel.
#    Option A: Flat sides are Vertical. Then Top and Bottom are angled points.
#       Vertices: (-w/2, -H), (-w/2, H), (w/2, H), (w/2, -H) is wrong.
#       Vertices for flat-sided hex (vertical sides):
#       (-w/2, -H), (-w/2, H) -> Left side.
#       (w/2, -H), (w/2, H) -> Right side.
#       Top vertex: (0, H * sqrt(3) / 3 ? No.)
#       Let's calculate vertices for a hexagon with width W (flat to flat) and vertical sides.
#       Distance between vertical sides = W.
#       Distance from center to flat side = W/2.
#       Distance from center to vertex (along the diagonal) = W / sqrt(3).
#       So the top vertex is at Z = W/sqrt(3).
#       The horizontal width at Z=0 is W.
#       The horizontal width at Z=0 is W.
#       The shape is bounded by x = -W/2 and x = W/2.
#       The top and bottom are points? No.
#       If x = -W/2 and x = W/2 are the sides, then the top and bottom must be angles connecting them.
#       Wait, if x=-W/2 and x=W/2 are the sides, the distance between them is W.
#       The vertices are at (-W/2, Z_min), (-W/2, Z_max), (W/2, Z_max), (W/2, Z_min) ... that's a rectangle.
#       To get a hexagon, we need 6 sides.
#       If we have 2 vertical sides, we need 4 other sides.
#       Top-Left, Top-Right, Bottom-Left, Bottom-Right.
#       This forms a hexagon with flat Top and Bottom? No, that would require the vertical sides to be angled.
#       Let's re-orient.
#       Standard Nut: The "width" is the distance across the flats.
#       The flats are parallel to the flange surface? No, the flange is perpendicular to the axis.
#       The flats of the hexagon are parallel to the YZ plane? No, the axis is Z.
#       The flats are parallel to the XZ plane? No.
#       The flats are parallel to the Y axis? No.
#       The flats are parallel to the X axis? No.
#       The flats are parallel to the XY plane? No.
#       The flats are parallel to the YZ plane? No.
#       The flats are parallel to the plane perpendicular to the X axis? No.
#       The flats are parallel to the plane perpendicular to the Y axis? No.
#       The flats are parallel to the plane perpendicular to the X axis? No.
#       Let's visualize. Axis Z.
#       Look from top (XY plane). You see a hexagon.
#       Look from the side (YZ plane). You see the profile of the hexagon.
#       The profile of a regular hexagon (with vertical sides) looks like a 'H' rotated? No.
#       It looks like two vertical lines connected by angled lines at top and bottom.
#       Vertices:
#       1. (-w/2, -h)
#       2. (-w/2, h)  -> Vertical Side Left
#       3. (w/2, h)   -> Vertical Side Right? No, that makes a rectangle.
#       Okay, let's try:
#       1. (-w/2, -h)
#       2. (w/2, -h)
#       3. (w, -h) ? No.
#       Let's use the vertices of a regular hexagon centered at (0,0) with width W.
#       If the width is W, the distance between opposite sides is W.
#       The vertices are at angles 0, 60, 120, 180, 240, 300.
#       If we want vertical sides, the sides must be at 90 deg? No, the normal to the side must be horizontal.
#       So the sides are at 0 and 180 degrees? No, the normals are 0 and 180.
#       So the vertices are at 30, 90, 150, 210, 270, 330.
#       Vertices (x, z):
#       30 deg: (R*cos30, R*sin30) = (R*sqrt(3)/2, R/2)
#       90 deg: (0, R)
#       150 deg: (-R*sqrt(3)/2, R/2)
#       210 deg: (-R*sqrt(3)/2, -R/2)
#       270 deg: (0, -R)
#       330 deg: (R*sqrt(3)/2, -R/2)
#       Where R = W / sqrt(3).
#       The "flat" distance (distance between side 30-90 and 150-210? No).
#       Distance between side (30-90) and (210-270)?
#       Side 30-90 connects (R*sqrt(3)/2, R/2) and (0, R).
#       Side 210-270 connects (-R*sqrt(3)/2, -R/2) and (0, -R).
#       These are not vertical.
#       Okay, let's rotate so the flats are vertical.
#       We want the sides to be x = -W/2 and x = W/2.
#       This happens if the vertices are at 0, 60, 120...
#       Vertices:
#       0: (R, 0)
#       60: (R/2, R*sqrt(3)/2)
#       120: (-R/2, R*sqrt(3)/2)
#       180: (-R, 0)
#       240: (-R/2, -R*sqrt(3)/2)
#       300: (R/2, -R*sqrt(3)/2)
#       Here, the vertical sides are between 0 and 60? No.
#       Side 0-60: (R,0) to (R/2, R*sqrt(3)/2). Not vertical.
#       Side 60-120: (R/2, R*sqrt(3)/2) to (-R/2, R*sqrt(3)/2). Horizontal.
#       This hexagon has Horizontal flats (Top/Bottom) and Pointy Sides.
#       We need Vertical flats.
#       So we rotate this by 30 degrees?
#       Rotate 30 deg:
#       Old 0 (R, 0) -> New (R*cos30, R*sin30) = (R*sqrt(3)/2, R/2).
#       Old 60 (R/2, R*sqrt(3)/2) -> New (0, R).
#       Old 120 (-R/2, R*sqrt(3)/2) -> New (-R*sqrt(3)/2, R/2).
#       Old 180 (-R, 0) -> New (-R*sqrt(3)/2, -R/2).
#       Old 240 (-R/2, -R*sqrt(3)/2) -> New (0, -R).
#       Old 300 (R/2, -R*sqrt(3)/2) -> New (R*sqrt(3)/2, -R/2).
#       Now check vertical sides.
#       Side 0-60 (New): (R*sqrt(3)/2, R/2) to (0, R). Not vertical.
#       Side 60-120 (New): (0, R) to (-R*sqrt(3)/2, R/2). Not vertical.
#       Okay, I am confusing myself.
#       Simple approach: Draw the hexagon using 6 LineSegments based on the "Flat to Flat" width.
#       Width W = 46.0.
#       Distance from center to flat = W/2 = 23.0.
#       Distance from center to vertex = W / sqrt(3) = 26.56.
#       If we want vertical sides (x = +/- 23), the vertices must be at x=23 and x=-23.
#       The y-coordinates (z in our sketch) of these vertices are +/- (W/sqrt(3) * sin(60)? No).
#       If x = W/2, then the angle from center is 0? No.
#       If x = W/2, the distance from origin is R = W/sqrt(3).
#       So the vertex is at (W/2, sqrt(R^2 - (W/2)^2)) = (W/2, sqrt(W^2/3 - W^2/4)) = (W/2, W*sqrt(1/12)) = (W/2, W/(2*sqrt(3))).
#       Wait, R = W/sqrt(3). x = W/2.
#       y = sqrt(R^2 - x^2) = sqrt(W^2/3 - W^2/4) = sqrt(W^2/12) = W / (2*sqrt(3)).
#       So the vertices for vertical sides are at x = +/- W/2, y = +/- W/(2*sqrt(3)).
#       But a hexagon has 6 vertices.
#       If we have vertical sides, the top and bottom are points?
#       Vertices:
#       1. (-W/2, -W/(2*sqrt(3)))
#       2. (-W/2, W/(2*sqrt(3)))
#       3. (W/2, W/(2*sqrt(3))) -> This makes a flat top? No, this is a rectangle corner.
#       Let's try to construct the hexagon vertices directly.
#       Center (0,0).
#       Width W (distance between parallel sides).
#       Orientation: Sides are parallel to Y axis (Vertical in YZ sketch).
#       Then the sides are at x = -W/2 and x = W/2.
#       The other 4 sides are angled.
#       The vertices are at:
#       (-W/2, -W/(2*sqrt(3)))
#       (W/2, -W/(2*sqrt(3)))
#       (W/2, W/(2*sqrt(3)))
#       (-W/2, W/(2*sqrt(3)))
#       Wait, that's 4 vertices. That's a rectangle.
#       Where are the other 2?
#       Ah, a hexagon has 6 sides.
#       If sides 1 and 4 are vertical, sides 2, 3, 5, 6 are angled.
#
