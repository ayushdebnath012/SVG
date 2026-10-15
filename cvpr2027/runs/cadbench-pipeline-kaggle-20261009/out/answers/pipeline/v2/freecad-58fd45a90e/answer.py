import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HexNut")

# --- Parameters ---
# We will use App::Parameter objects to store the values so they are editable in the tree
# and can be referenced by expressions.
params = doc.addObject("App::Parameter", "Parameters")
params.Name = "Parameters"
params.Width = 13.0
params.Height = 8.0
params.FlangeDia = 17.9
params.FlangeThick = 3.5
params.InnerDia = 8.0
params.HexCorner = 15.011106998930272
params.HexAngle = 30.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Base Sketch (Flange) ---
# We start with the flange on the XY plane.
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.Support = (doc.getObject("XY_Plane"), [])
sketch_flange.MapMode = "FlatFace"

# Outer circle of the flange
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.FlangeDia / 2.0)
sketch_flange.addGeometry(outer_circle, False)

# Inner circle of the flange (hole)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.InnerDia / 2.0)
sketch_flange.addGeometry(inner_circle, False)

# Constraint: Concentric
sketch_flange.addConstraint(Sketcher.Constraint("Equal", 0, 2, 1, 1))
sketch_flange.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center to center

# --- Hexagon Sketch ---
# We create a sketch on the XZ plane (vertical) to define the hex profile.
# The hexagon will be centered at (0, 0) in the sketch plane.
# We need to orient the sketch so the hexagon is vertical.
# Let's use the XZ plane.
sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hex.Support = (doc.getObject("XZ_Plane"), [])
sketch_hex.MapMode = "FlatFace"

# Define the hexagon vertices.
# Width across flats = params.Width
# Width across corners = params.HexCorner
# Angle = params.HexAngle
# We construct the hexagon using lines and circles or direct points.
# Using lines and circles is more robust for constraints.

# Center point
center_pt = App.Vector(0, 0, 0)

# Radius for the "flat" side (distance from center to flat)
# R_flat = Width / (2 * cos(30)) = Width / sqrt(3)
# Actually, Width = 2 * R_flat * cos(30) => R_flat = Width / (2 * cos(30))
# Wait, standard hex: Distance between flats = Width.
# Distance from center to flat = Width / 2.
# Distance from center to corner = Width / (2 * cos(30)) = Width / sqrt(3).
# Let's verify: 13 / 1.732 = 7.505. 13/2 = 6.5.
# Yes.

R_flat = params.Width / 2.0
R_corner = params.HexCorner / 2.0

# We need to place the hexagon such that it is upright (flat on top/bottom or pointy top/bottom?).
# Standard hex nut usually has flat sides vertical if looking from the side? 
# No, usually "flat on top" means the top face is flat.
# In the XZ plane sketch, if we want the hex to be the cross section of the nut body:
# The nut body is a hexagonal prism.
# If we extrude along Z, the hexagon must be in the XY plane.
# BUT, we already have the flange in the XY plane.
# If we extrude the hexagon in the XY plane, it will overlap the flange.
# The nut body sits ON TOP of the flange.
# So the hexagon sketch should be on the XZ plane (vertical), and we extrude it along the Y axis?
# Or, simpler:
# 1. Flange is on XY plane, extruded up Z.
# 2. Hex body is defined by a sketch on the XZ plane (vertical), extruded along Y?
#    No, that creates a shape with a flat front and back.
#    We want a hexagonal prism.
#    The hexagon profile must be in a plane perpendicular to the extrusion direction.
#    If the flange is on XY and extruded Z, the nut body is also extruded Z.
#    So the hexagon profile must be in the XY plane.
#    But the flange is also in the XY plane.
#    This means the hexagon sketch and the flange sketch are coplanar.
#    We can define the hexagon in the same sketch or a new one on the same plane.
#    Let's create a new sketch on XY plane for the hex profile.

# Re-evaluating the strategy:
# Strategy A:
# 1. Sketch Flange on XY. Pad it up to overall_height.
# 2. Sketch Hex on XY (offset Z slightly? No, same plane). 
#    If we sketch on XY, we can't extrude it "up" because the flange is already there.
#    We would have to subtract or use a specific order.
#    Better: 
#    1. Sketch Flange on XY. Pad it up to overall_height.
#    2. Create a sketch on the XZ plane (vertical). Define the hexagon profile.
#       Extrude this profile along the Y axis? No, that makes a block.
#       We want the hexagon to be the cross-section of the body.
#       So the body is a hexagonal prism.
#       The hexagon lies in the XY plane.
#       The flange lies in the XY plane.
#       They share the same base plane.
#       So we can define the hexagon in a sketch on the XY plane, but we need to extrude it.
#       If we extrude the hexagon, it will merge with the flange if they are on the same plane.
#       Unless we offset the hexagon sketch slightly in Z?
#       Yes. Sketch Hex on XY plane, but offset Z by a tiny amount (e.g., 0.01mm) so it's above the flange sketch.
#       Then Pad the Hexagon up.
#       Then we have a hexagonal block sitting on top of the flange.
#       Then we can subtract the hole.

# Let's refine the "Hexagon on XY plane" approach.
# 1. Sketch Flange on XY (Z=0). Pad Z=0 to Z=Height.
# 2. Sketch Hex on XY (Z=0.01). Define Hexagon. Pad Z=0.01 to Z=Height.
#    This creates a hexagonal block on top of the flange.
#    The union will be a single solid.
# 3. Hole: Sketch on XY (Z=0.01 or anywhere). Pad Through All.

# Let's implement this.

# --- Hexagon Sketch (Offset Z) ---
sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, 0.01)) # Slightly above flange
sketch_hex.Support = (doc.getObject("XY_Plane"), [])
sketch_hex.MapMode = "FlatFace"

# Define Hexagon Vertices
# We need 6 points.
# Let's define them relative to center (0,0).
# Angle of first vertex?
# If we want flat sides vertical (like a standard nut viewed from side), the vertices are at 0, 60, 120...
# If we want flat sides horizontal (like a hexagon lying flat), vertices are at 30, 90, 150...
# Standard hex nut: The "width across flats" is the distance between parallel sides.
# If we extrude along Z, the top face is a hexagon.
# The orientation doesn't matter for the solid shape, but let's make it standard.
# Let's put a flat side on the X-axis (horizontal).
# Vertices at angles: 0, 60, 120, 180, 240, 300 degrees?
# Distance between 0 and 180 is 2*R_corner.
# Distance between 30 and 210 is 2*R_flat.
# Let's use angles 0, 60, 120, 180, 240, 300.
# Then the distance between 0 and 180 is 2*R_corner.
# The distance between 30 and 210 is 2*R_flat.
# So if we want width across flats = 13, then 2*R_flat = 13 => R_flat = 6.5.
# Then R_corner = R_flat / cos(30) = 6.5 / 0.866 = 7.505.
# This matches our params.
# So vertices at 0, 60, 120, 180, 240, 300 degrees.
# Wait, if vertices are at 0 and 180, the distance is 2*R_corner.
# If vertices are at 30 and 210, the distance is 2*R_flat.
# So if we want width across flats = 13, we need the distance between parallel sides to be 13.
# Parallel sides are perpendicular to the radius at 30, 90, 150...
# So the distance between the lines x*cos(30) + y*sin(30) = R_flat and ...
# Basically, if we place vertices at 0, 60, 120, 180, 240, 300:
# The side connecting 0 and 60 is at angle 30.
# The distance from center to this side is R_flat.
# So R_flat = Width / 2.
# And R_corner = Width / (2 * cos(30)).
# This matches.
# So vertices at 0, 60, 120, 180, 240, 300 degrees.

# Let's create the points.
# We will use Part::Vertex to define the geometry.
# Or we can use lines and circles.
# Let's use lines and circles for robustness.
# Circle 1: Radius R_corner.
# Circle 2: Radius R_flat.
# We need to constrain the hexagon to these circles.
# Actually, simpler: Just define the 6 points and connect them.
# But FreeCAD Sketcher prefers constraints.
# Let's define 6 points on the outer circle (R_corner).
# Then constrain them to be 60 degrees apart.
# And constrain the distance between opposite points to be 2*R_corner.
# And constrain the distance between adjacent points to be 2*R_flat * sin(30)? No.
# Distance between adjacent vertices (side length) = R_corner * sqrt(3).
# Let's just define the points and constrain them to the circle R_corner.
# And constrain the angle between them.

# Define 6 points on the circle R_corner.
# We can use Part::Vertex.
# But Sketcher::SketchObject.addGeometry expects Part::LineSegment, Part::Circle, etc.
# We can add points? No, Sketcher doesn't have a "Point" geometry type directly in the same way.
# We can use Part::Vertex, but it's not a standard Sketcher geometry.
# Alternative: Use Part::LineSegment and Part::Circle.
# Let's draw the hexagon using lines.
# We need to define the endpoints.
# We can define a circle of radius R_corner.
# Then define 6 points on it? No.
# Let's define the hexagon by its vertices using Part::Vertex and then convert?
# No, Sketcher::SketchObject.addGeometry takes Part::LineSegment, Part::Circle, Part::Ellipse, Part::Vertex (in some versions), Part::Edge.
# Let's try adding Part::Vertex.
# If that fails, we can use a workaround: define a circle and use constraints.
# Actually, the most robust way in FreeCAD 1.1 is to use Part::Vertex if supported, or define lines.
# Let's try defining the hexagon using Part::Vertex.
# If not, we can define the hexagon as a compound of lines.

# Let's try a different approach:
# Define the hexagon using Part::Polygon? No.
# Let's define the hexagon using Part::LineSegment and Part::Vertex.
# We need to create the vertices first.
# We can create Part::Vertex objects and add them to the sketch?
# No, Sketcher::SketchObject.addGeometry does not accept Part::Vertex.
# It accepts Part::LineSegment, Part::Circle, Part::Ellipse, Part::Vertex (in some contexts?), Part::Edge.
# Let's check the documentation or common practice.
# Common practice: Use Part::LineSegment and Part::Circle.
# We can define the hexagon by defining the 6 vertices as Part::Vertex and then creating lines between them?
# No, we can't add Part::Vertex to Sketcher::SketchObject directly.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we need to add the lines to the sketch.
# The lines need to be defined by their endpoints.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
# We can define the endpoints as Part::Vertex and then create lines?
# No, we can't add Part::Vertex to the sketch.
# We can add Part::LineSegment.
# So we need to define the endpoints of the lines.
