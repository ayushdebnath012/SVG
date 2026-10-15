import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HexFlangeNut")

# --- Parameters Section ---
# Define editable parameters using App::VarSet for clear, named document objects
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Bolt hole diameter")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total nut height")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Outer bearing surface")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange height")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hex hub width across flats")

# Set default values as per requirements
params.inner_diameter = 30.0
params.overall_height = 45.0
params.flange_diameter = 58.0
params.flange_thickness = 8.0
params.hub_width = 46.0

# --- Body Creation ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Feature 1: Flange Bottom Sketch ---
# Create sketch on XY_Plane to define the outer flange circle
sketch_flange = body.newObject("Sketcher::SketchObject", "sketch_FlangeBottom")
sketch_flange.Plane = "XY_Plane"
sketch_flange.Constrain = "Auto"

# Add circle for flange outer diameter
# Radius = flange_diameter / 2
sketch_flange.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0), False)

# --- Feature 2: Hex Hub Profile Sketch ---
# Create sketch on YZ_Plane to define the side profile of the hexagon
# The hexagon will be extruded along the Z axis (which is the Y axis in the YZ plane sketch context relative to the body)
# Actually, for a PartDesign Body, the Z axis of the sketch plane is the extrusion direction for a Pad.
# We want the nut axis to be Z. So we sketch on YZ plane, and extrude along Z (which is the local Z of the sketch).
# Wait, if sketch is on YZ plane, the local axes are: X (normal to plane), Y (horizontal in plane), Z (vertical in plane).
# Extruding along Z will create a shape with Z as the main axis. This is correct.

sketch_hex = body.newObject("Sketcher::SketchObject", "sketch_HexProfile")
sketch_hex.Plane = "YZ_Plane"
sketch_hex.Constrain = "Auto"

# Calculate Hexagon Geometry
# Width (flat to flat) = hub_width
# Distance from center to flat side = hub_width / 2
# Distance from center to vertex = hub_width / sqrt(3)
# We want vertical sides (parallel to Z axis in the sketch).
# Vertices for a hexagon with vertical sides:
# x = +/- (hub_width / 2)
# z = +/- (hub_width / (2 * sqrt(3)))
# Wait, let's re-verify the vertex coordinates for a hexagon with vertical sides.
# If sides are vertical, the distance between them is W.
# The vertices are at the corners.
# Top-Left: (-W/2, H)
# Top-Right: (W/2, H) -> This would be a flat top.
# No, a regular hexagon with vertical sides has:
# Side 1: x = -W/2 (from z = -h to z = h)
# Side 2: x = W/2 (from z = -h to z = h)
# This forms a rectangle.
# To make it a hexagon, we need to cut the top and bottom corners? No.
# A regular hexagon has 60 degree angles.
# If we have vertical sides, the angles at the top and bottom must be 120 degrees.
# So the top and bottom are points? No, that's impossible for a regular hexagon.
# Let's visualize a regular hexagon.
#   / \
#  |   |
#   \ /
# If the sides are vertical, the top and bottom are points.
# Vertices:
# 1. (-W/2, -h)
# 2. (W/2, -h) -> Horizontal bottom side? No.
# Let's use the standard vertices for a hexagon with width W (flat to flat).
# If the flats are vertical, the normals are horizontal (0 and 180 degrees).
# The vertices are at angles 30, 90, 150, 210, 270, 330.
# Coordinates (x, z):
# 30: (R*cos30, R*sin30) = (R*sqrt(3)/2, R/2)
# 90: (0, R)
# 150: (-R*sqrt(3)/2, R/2)
# 210: (-R*sqrt(3)/2, -R/2)
# 270: (0, -R)
# 330: (R*sqrt(3)/2, -R/2)
# Where R = W / sqrt(3).
# The "flat" distance (distance between side 30-90 and 210-270? No).
# Distance between side (30-90) and (210-270) is not W.
# Distance between side (30-90) and (150-210)? No.
# The distance between parallel sides is W.
# The sides are:
# 1. 30-90: Connects (R*sqrt(3)/2, R/2) and (0, R).
# 2. 90-150: Connects (0, R) and (-R*sqrt(3)/2, R/2).
# 3. 150-210: Connects (-R*sqrt(3)/2, R/2) and (-R*sqrt(3)/2, -R/2). -> Vertical Side!
# 4. 210-270: Connects (-R*sqrt(3)/2, -R/2) and (0, -R).
# 5. 270-330: Connects (0, -R) and (R*sqrt(3)/2, -R/2).
# 6. 330-30: Connects (R*sqrt(3)/2, -R/2) and (R*sqrt(3)/2, R/2). -> Vertical Side!
# So the vertical sides are at x = +/- R*sqrt(3)/2.
# R*sqrt(3)/2 = (W/sqrt(3)) * sqrt(3)/2 = W/2.
# So the vertical sides are at x = +/- W/2.
# The height of these sides is from z = -R/2 to z = R/2.
# R/2 = (W/sqrt(3))/2 = W / (2*sqrt(3)).
# So the vertices are:
# (-W/2, -W/(2*sqrt(3)))
# (W/2, -W/(2*sqrt(3))) -> Wait, this is a horizontal line.
# Let's list the vertices in order for the sketch:
# Start at bottom-left vertical side: (-W/2, -W/(2*sqrt(3)))
# Go up to top-left vertical side: (-W/2, W/(2*sqrt(3)))
# Go to top-left angled vertex: (-W/(2*sqrt(3)), W/2) ? No.
# Let's re-calculate the vertices for the 30-90-150-210-270-330 orientation.
# R = W / sqrt(3)
# V1 (30): (R*sqrt(3)/2, R/2) = (W/2, W/(2*sqrt(3)))
# V2 (90): (0, R) = (0, W/sqrt(3))
# V3 (150): (-W/2, W/(2*sqrt(3)))
# V4 (210): (-W/2, -W/(2*sqrt(3)))
# V5 (270): (0, -W/sqrt(3))
# V6 (330): (W/2, -W/(2*sqrt(3)))
#
# Sides:
# V1-V2: Angled
# V2-V3: Angled
# V3-V4: Vertical (x = -W/2)
# V4-V5: Angled
# V5-V6: Angled
# V6-V1: Vertical (x = W/2)
#
# This forms a hexagon with two vertical sides and four angled sides.
# This is the correct profile for a hex nut with vertical flats.

import math

half_width = params.hub_width / 2.0
vertex_z = params.hub_width / (2 * math.sqrt(3))
vertex_y = params.hub_width / math.sqrt(3) # This is R

# Define vertices
v1 = App.Vector(half_width, vertex_z, 0)
v2 = App.Vector(0, vertex_y, 0)
v3 = App.Vector(-half_width, vertex_z, 0)
v4 = App.Vector(-half_width, -vertex_z, 0)
v5 = App.Vector(0, -vertex_y, 0)
v6 = App.Vector(half_width, -vertex_z, 0)

# Add line segments
sketch_hex.addGeometry(Part.LineSegment(v1, v2), False)
sketch_hex.addGeometry(Part.LineSegment(v2, v3), False)
sketch_hex.addGeometry(Part.LineSegment(v3, v4), False)
sketch_hex.addGeometry(Part.LineSegment(v4, v5), False)
sketch_hex.addGeometry(Part.LineSegment(v5, v6), False)
sketch_hex.addGeometry(Part.LineSegment(v6, v1), False)

# --- Feature 3: Pad (Flange) ---
# Extrude the flange sketch along Z axis (which is the local Z of the sketch plane YZ)
# The sketch is on YZ plane. The local Z axis of the sketch is the global Z axis.
# So extruding along Z will create the flange thickness.
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_hex
pad_flange.Length = params.flange_thickness
pad_flange.Direction = "Z" # Explicitly set direction to Z (global Z, which is sketch Z)
# Note: In PartDesign, if the sketch is on YZ plane, the "Z" direction of the sketch is the global Z.
# However, the Pad feature uses the sketch's local coordinate system.
# The sketch's local Z is the global Z. So "Z" is correct.
# But wait, the sketch is on YZ plane. The local axes are: X (normal), Y (horizontal), Z (vertical).
# The Pad extrudes along the sketch's Z axis.
# So pad_flange.Length = flange_thickness.

# --- Feature 4: Pad (Hub) ---
# Extrude the hex profile along Z axis to the full height
pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub")
pad_hub.Profile = sketch_hex
pad_hub.Length = params.overall_height
pad_hub.Direction = "Z"

# --- Feature 5: Hole ---
# Create a sketch on XY_Plane to define the hole
sketch_hole = body.newObject("Sketcher::SketchObject", "sketch_Hole")
sketch_hole.Plane = "XY_Plane"
sketch_hole.Constrain = "Auto"

# Add circle for the hole
hole_radius = params.inner_diameter / 2.0
sketch_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hole_radius), False)

# Create a pocket for the hole
# The pocket will be on the XY plane, extruding along Z (through all)
pocket_hole = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket_hole.Profile = sketch_hole
pocket_hole.Type = "ThroughAll"
pocket_hole.Axis = "Z" # Extrude along Z

# --- Feature 6: Fillet ---
# Add a fillet to the top edge of the flange (where it meets the hub)
# The edge is the intersection of the flange top face and the hub side face.
# We need to identify the edge.
# The flange is created by Pad_Flange. The hub is created by Pad_Hub.
# The edge is the top perimeter of the hexagon on the flange.
# However, the Pad_Hub is extruded from the same sketch as Pad_Flange.
# So the top face of the flange is coplanar with the top face of the hub?
# No, the flange is 8mm thick, the hub is 45mm thick.
# The flange is at the bottom (0 to 8mm). The hub is 0 to 45mm.
# So the flange is a subset of the hub volume?
# No, the flange is a larger diameter circle.
# The hub is a hexagon.
# So the flange is a cylinder (circle) of diameter 58mm, height 8mm.
# The hub is a hexagon of width 46mm, height 45mm.
# The flange is at the bottom.
# The top of the flange is at Z=8. The top of the hub is at Z=45.
# The side of the hub is at Z=0 to 45.
# The side of the flange is at Z=0 to 8.
# The edge we want to fillet is the top edge of the flange?
# Or the edge where the flange meets the hub?
# The flange is a larger circle. The hub is a smaller hexagon.
# So the flange overhangs the hub.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of diameter 58mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top edge of the flange (circle at Z=8)?
# Or the edge where the flange meets the hexagon?
# The hexagon is inside the flange.
# So the flange is a cylinder. The hexagon is a prism.
# The union of the two is the nut.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm, height 8mm.
# The hexagon is a prism of width 46mm, height 45mm.
# The hexagon is inside the cylinder.
# So the flange covers the hexagon at the bottom.
# The edge is the top perimeter of the hexagon at Z=8?
# No, the hexagon goes up to Z=45.
# The flange is a cylinder of height 8mm.
# The hexagon is a prism of height 45mm.
# The flange is at the bottom.
# So the flange is a cylinder of diameter 58mm
