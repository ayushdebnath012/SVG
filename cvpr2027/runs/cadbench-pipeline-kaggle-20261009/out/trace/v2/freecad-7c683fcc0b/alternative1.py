import os
import FreeCAD as App
import Part
from pathlib import Path
from sketcher import Constraint

# --- Configuration from Task Description ---
# We will define these in a named object to keep the script clean and editable.
# However, to ensure the specific values are used immediately, we set them directly 
# or via a Parameter object. The prompt asks for "named document objects" whose properties drive geometry.

# Create Document
doc = App.newDocument("HexFlangeNut")

# Create Parameters Object (App::VarSet)
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter of the hole")
params.inner_diameter = 24.0

params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the nut")
params.overall_height = 36.0

params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of the bottom flange")
params.flange_diameter = 45.0

params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the bottom flange")
params.flange_thickness = 6.0

params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Width across flats of the hexagonal hub")
params.hub_width = 36.0

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Feature 1: Base Sketch (Bottom Flange) ---
# We place the bottom face on the XY plane to build upwards.
sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_BaseFlange")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to XY_Plane (which is Z=0 in standard coordinates for the body's local space usually, 
# but we need to ensure we are on a valid plane. PartDesign creates XY_Plane, XZ_Plane, YZ_Plane by default).
# In PartDesign::Body, the default placement of the body puts the origin at 0,0,0.
# We will attach to the Body's XY_Plane.
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0)) 
# Note: Sketcher::SketchObject attachment requires a specific plane object. 
# We assume the Body provides standard planes. Let's use the XY_Plane of the Body.
# If the Body doesn't have it explicitly created as an object, we might need to add it or use a reference.
# Standard practice in 1.1: Body.newObject("PartDesign::Body") creates the body.
# The planes are usually available as "XY_Plane", "XZ_Plane", "YZ_Plane" inside the body or doc if created.
# Let's create the planes explicitly to be safe and robust.

# Create Planes
xy_plane = body.newObject("PartDesign::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0)) # Origin
# Actually, PartDesign::Plane is not the standard way to attach sketches in 1.1 often.
# Usually, we attach to the Body's coordinate system or specific Plane objects.
# Let's rely on the standard "XY_Plane" object that PartDesign creates if we instantiate the body correctly,
# OR we create a Part::Plane.
# The most robust way in 1.1 headless:
# We create a sketch and set Placement. Then we add geometry relative to that placement.
# For constraints, we need references.
# Let's try attaching to a Plane object created in the Body.

plane_xy = body.newObject("PartDesign::Plane", "Plane_XY")
plane_xy.Placement = App.Placement(App.Vector(0, 0, 0))
# Actually, to get a plane at Z=0, we usually rotate the standard XY plane.
# Let's just use the default XY_Plane if available, or create a Part::Plane.
# Simpler approach for Headless 1.1:
# Use the Body's local coordinate system (0,0,0).
# We will create a sketch on the XY plane by setting Placement.Z=0 and ensuring normal is Z.

# Re-initializing sketch to use a standard plane reference if available.
# In FreeCAD 1.1, when you create a Body, it often has XY_Plane, XZ_Plane, YZ_Plane.
# Let's try to reference them. If they don't exist, we create a Part::Plane.
# Since I cannot check existence easily without try/except or hasattr on doc, 
# I will create a Part::Plane object in the Body to be the sketch support.

plane_support = body.newObject("Part::Plane", "Sketch_Plane")
plane_support.Placement = App.Placement(App.Vector(0, 0, 0))
plane_support.Placement.Rot = App.Rotation((1, 0, 0), 0) # Normal pointing X? No, need Z.
# Part::Plane placement: The plane is defined by the position and the Z-axis of the placement.
# If I want the plane to be XY (normal Z), I place it at 0,0,0.
# Wait, Part::Plane's placement defines the plane. The local Z of the placement is the plane normal.
# So if I place at (0,0,0) with identity rotation, the plane is XY.
plane_support.Placement = App.Placement(App.Vector(0, 0, 0))

sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_BaseFlange")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0)) # Position on the plane
sketch_base.Support = (plane_support, [""])

# Draw Flange Circle
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0), False)

# Add constraints to center it (Coincident with origin)
# We need to reference the origin or axes.
# Let's add a constraint to the center of the circle being coincident with the origin (0,0).
# But Sketcher constraints need indices.
# Let's add a point at center manually or use Coincident with an axis.
# Easier: Coincident with the X_Axis at 0?
# Let's use the "Center" constraint if available, or just Coincident with a point.
# To be safe with indices, let's add a Point at origin and constrain circle center to it.
sketch_base.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1)) # Center of circle (0,1) coincident with Point (1,1)
# Wait, indices: Element, SubElement, Element, SubElement.
# Circle center is at index 0, sub-element 1 (Center). Point is at index 1, sub-element 1 (Point).
# Actually, Part.Point is index 1 in list.
# Let's assume standard indices: 0=Line/Circle, 1=Point.
# Constraint: Coincident, Circle(0), Center(1), Point(1), Point(1)

# --- Feature 2: Pad (The Flange) ---
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_base
pad_flange.Length = params.flange_thickness
pad_flange.Type = "Solid"
pad_flange.TaperAngle = 0.0
pad_flange.Midplane = False
pad_flange.Reversed = False
# Drive length from parameter
pad_flange.setExpression("Length", "Parameters.flange_thickness")

# --- Feature 3: Hole Sketch ---
# We need a sketch for the hole. It will be on the XY plane at Z = flange_thickness.
plane_hole = body.newObject("Part::Plane", "Plane_Hole")
plane_hole.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))

sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hole.Support = (plane_hole, [""])

# Inner circle
sketch_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0), False)
sketch_hole.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
sketch_hole.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1))

# --- Feature 4: Pocket (The Through Hole) ---
pocket = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket.Profile = sketch_hole
pocket.Type = "ThroughAll"
# Drive depth
pocket.setExpression("Length", "Parameters.overall_height")

# --- Feature 5: Hex Hub Sketch ---
# The hex hub starts at Z = flange_thickness and extends to Z = overall_height.
# Height of hex section = overall_height - flange_thickness.
hex_height = params.overall_height - params.flange_thickness

plane_hex = body.newObject("Part::Plane", "Plane_Hex")
plane_hex.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))

sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hex.Support = (plane_hex, [""])

# Hexagon creation
# Hub_width is width across flats.
# Radius of hexagon (distance from center to vertex) = Hub_width / (2 * cos(30°)) = Hub_width / sqrt(3)
import math
hex_radius = params.hub_width / (math.sqrt(3))

# We can create a polygon or use a circle approximation, but a polygon is better.
# Or we can use a circle with a specific diameter and then chamfer, but the prompt says "Hexagonal outer body".
# Let's create a 6-gon.
points = []
for i in range(6):
    angle = i * 60.0 # 0 to 300
    # Rotate by 30 to align flats horizontally if desired, or vertices. 
    # Standard hex: vertices at 0, 60, 120...
    # Flats are vertical if vertices are at 0, 60...
    # Let's do vertices at 0, 60...
    x = hex_radius * math.cos(math.radians(angle))
    y = hex_radius * math.sin(math.radians(angle))
    points.append(App.Vector(x, y, 0))
    
# Create a closed loop of lines
lines = []
for i in range(6):
    p1 = points[i]
    p2 = points[(i+1)%6]
    lines.append(Part.LineSegment(p1, p2))
    
sketch_hex.addGeometry(lines, False)
# Add center point and constrain
sketch_hex.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
# Constrain center of first line segment (0,1) to center point (1,1) - Midpoint of line
# Actually, let's just constrain the lines to form a closed loop?
# Sketcher has "Line" constraints.
# Let's just constrain the center of the first line to the origin.
sketch_hex.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1)) # Center of first segment to Point center

# --- Feature 6: Pad (The Hex Body) ---
pad_hex = body.newObject("PartDesign::Pad", "Pad_Hex")
pad_hex.Profile = sketch_hex
# Length is the height of the hex section
hex_pad_len = params.overall_height - params.flange_thickness
pad_hex.Length = hex_pad_len
# Pad extends from the sketch plane (Z=flange_thickness) upwards.
# Total Z will be flange_thickness + hex_pad_len = overall_height. Correct.
pad_hex.setExpression("Length", "Parameters.overall_height - Parameters.flange_thickness")

# --- Feature 7: Chamfers ---
# We need to chamfer the top of the flange (where it meets the hex) and the bottom of the flange.
# 1. Top of Flange (Bottom of Hex): Edge between flange circle and hex body.
#    The pad_hex created a new solid. The edge is the top face of the flange.
#    Wait, the order: Pad_Flange -> Pocket_Hole -> Pad_Hex.
#    The edge is the intersection of the flange face (XY at Z=thickness) and the hex body.
#    Actually, Pad_Hex creates volume from the sketch up.
#    The edge exists at the interface Z=thickness.
#    We need to chamfer the edges of the hexagon on the top face of the flange.
#    And the edges of the hexagon on the bottom face of the nut (Z=0).

# Edge 1: Top of Flange (Inner radius of flange meets hex? No, Hex is inside flange outer diameter).
# The flange is a cylinder. The hex is a cylinder.
# The edge is the perimeter of the hexagon at Z=thickness.
# And the perimeter of the hexagon at Z=0 (bottom of nut).

# Let's identify edges.
# The Pad_Hex creates a hexagonal prism.
# The top face of this prism is at Z=overall_height.
# The bottom face of this prism is at Z=flange_thickness.
# The edge at Z=flange_thickness is the intersection of the hex prism and the flange cylinder.
# We want to chamfer the edges of the hexagon.

# We need to select the edge.
# In PartDesign::Chamfer, Base is a list of (Feature, [EdgeIndex]).
# We can select edges from Pad_Hex.
# The bottom face of Pad_Hex is at Z=thickness. The edges are the perimeter.
# Which edge index? Usually 0 is the first loop.
# Let's apply chamfer to the edges of the hexagon at the top and bottom.

# Chamfer 1: Top of Flange (Bottom of Hex)
chamfer_top = body.newObject("PartDesign::Chamfer", "Chamfer_TopFlange")
chamfer_top.Base = (pad_hex, ["Edge1"]) # Assuming Edge1 is the perimeter of the bottom face of hex
chamfer_top.Size = 1.0 # Chamfer distance

# Chamfer 2: Bottom of Nut (Bottom of Hex)
# The bottom face of Pad_Hex is at Z=thickness.
# Wait, Pad_Hex starts at Z=thickness.
# So the bottom face of Pad_Hex is the interface with the flange.
# The top face of Pad_Hex is at Z=overall_height.
# We need to chamfer the bottom face of Pad_Hex? No, that's inside.
# We need to chamfer the bottom face of the Flange? No, that's flat.
# We need to chamfer the bottom of the Hexagon (at Z=thickness) AND the top of the Hexagon (at Z=overall_height)?
# The prompt says "Hex flange nut". Usually, the top is flat. The bottom is flat.
# The chamfer is usually on the side edges where the hex meets the flange?
# Or the edges of the hex on the top/bottom faces.
# Let's assume standard chamfer on the top and bottom faces of the hexagonal portion.
# Top Face of Hex (at Z=overall_height): Edges are the perimeter.
# Bottom Face of Hex (at Z=thickness): Edges are the perimeter.

# Let's create a chamfer for the top face of the hexagon.
chamfer_top_hex = body.newObject("PartDesign::Chamfer", "Chamfer_TopHex")
chamfer_top_hex.Base = (pad_hex, ["Edge1"]) # Top perimeter of hex
chamfer_top_hex.Size = 1.0

# Chamfer for the bottom face of the hexagon (at the junction with flange)
chamfer_bot_hex = body.newObject("PartDesign::Chamfer", "Chamfer_BotHex")
chamfer_bot_hex.Base = (pad_hex, ["Edge1"]) # Wait, Pad_Hex creates one face loop for the bottom?
# Actually, Pad creates a solid. The bottom face is a single face with 6 edges.
# So Edge1 should be the perimeter.
chamfer_bot_hex.Base = (pad_hex, ["Edge1"]) 
chamfer_bot_hex.Size = 1.0

# Wait, if I chamfer both, I might remove material.
# Usually, a nut has chamfers on the top and bottom corners.
# Let's assume we want chamfers on the top (Z=H) and bottom (Z=0) of the hex part.
# But the bottom of the hex part is at Z=thickness.
# The bottom of the flange is at Z=0.
# Do we chamfer the flange bottom? No, that's the bearing surface.
# Do we chamfer the hex bottom? Yes, the corner where hex meets flange.
# Do we chamfer the hex top? Yes.

# Let's refine the Edge selection.
# When creating Pad_Hex, the bottom face is created at Z=thickness.
# The edge is the perimeter of the hexagon.
# When creating Pad_Flange, it adds material below.
# So the edge at Z=thickness is the top of the flange, bottom of hex.
# The edge at Z=0 is the bottom of the flange.
# We want to chamfer the edges of the hexagon at Z=thickness (bottom of hex) and Z=overall_height (top of
