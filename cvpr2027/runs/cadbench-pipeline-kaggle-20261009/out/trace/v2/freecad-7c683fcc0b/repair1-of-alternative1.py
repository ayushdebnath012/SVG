import os
import sys
import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Parameters are defined in a named object to ensure they are editable and drive the geometry.
# We will set their initial values here.

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

# --- Helper to create a Plane object in the Body ---
# This ensures we have a valid support for sketches.
def create_plane_in_body(name, offset_z):
    p = body.newObject("Part::Plane", name)
    p.Placement = App.Placement(App.Vector(0, 0, offset_z))
    return p

# --- Feature 1: Base Sketch (Bottom Flange) ---
# Plane at Z=0
plane_base = create_plane_in_body("Plane_Base", 0.0)

sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_BaseFlange")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (plane_base, [""])

# Draw Flange Circle
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0), False)

# Add center point and constrain
sketch_base.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
# Constrain center of circle to center point
sketch_base.addConstraint(App.Sketcher.Constraint("Coincident", 0, 1, 1, 1))

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
# Plane at Z = flange_thickness
plane_hole = create_plane_in_body("Plane_Hole", params.flange_thickness)

sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hole.Support = (plane_hole, [""])

# Inner circle
sketch_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0), False)
sketch_hole.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
sketch_hole.addConstraint(App.Sketcher.Constraint("Coincident", 0, 1, 1, 1))

# --- Feature 4: Pocket (The Through Hole) ---
pocket = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket.Profile = sketch_hole
pocket.Type = "ThroughAll"
# Drive depth from parameter (extends to top of nut)
pocket.setExpression("Length", "Parameters.overall_height")

# --- Feature 5: Hex Hub Sketch ---
# The hex hub starts at Z = flange_thickness and extends to Z = overall_height.
# Height of hex section = overall_height - flange_thickness.
hex_height = params.overall_height - params.flange_thickness

plane_hex = create_plane_in_body("Plane_Hex", params.flange_thickness)

sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
sketch_hex.Support = (plane_hex, [""])

# Hexagon creation
# Hub_width is width across flats.
# Radius of hexagon (distance from center to vertex) = Hub_width / (2 * cos(30°)) = Hub_width / sqrt(3)
hex_radius = params.hub_width / (math.sqrt(3))

# We create a closed loop of lines
lines = []
for i in range(6):
    angle = i * 60.0 # 0 to 300 degrees
    x = hex_radius * math.cos(math.radians(angle))
    y = hex_radius * math.sin(math.radians(angle))
    p1 = App.Vector(x, y, 0)
    p2 = App.Vector(hex_radius * math.cos(math.radians((i+1)*60.0)), hex_radius * math.sin(math.radians((i+1)*60.0)), 0)
    lines.append(Part.LineSegment(p1, p2))
    
sketch_hex.addGeometry(lines, False)
# Add center point and constrain
sketch_hex.addGeometry(Part.Point(App.Vector(0, 0, 0)), False)
# Constrain center of first line segment to center point
# Index 0 is the first LineSegment, sub-element 1 is its center.
# Index 1 is the Point, sub-element 1 is the point itself.
sketch_hex.addConstraint(App.Sketcher.Constraint("Coincident", 0, 1, 1, 1))

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
# We need to chamfer the edges of the hexagon at the top and bottom of the hexagonal section.
# The hexagonal section is created by Pad_Hex.
# The bottom face of Pad_Hex is at Z=flange_thickness.
# The top face of Pad_Hex is at Z=overall_height.

# Chamfer 1: Top of Hex (at Z=overall_height)
chamfer_top = body.newObject("PartDesign::Chamfer", "Chamfer_TopHex")
chamfer_top.Base = (pad_hex, ["Edge1"]) # Edge1 is the perimeter of the top face
chamfer_top.Size = 1.0

# Chamfer 2: Bottom of Hex (at Z=flange_thickness)
# This is the edge where the hex meets the flange.
chamfer_bot = body.newObject("PartDesign::Chamfer", "Chamfer_BotHex")
chamfer_bot.Base = (pad_hex, ["Edge1"]) # Edge1 is the perimeter of the bottom face
chamfer_bot.Size = 1.0

# --- Finalize ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

try:
    doc.saveAs(str(output_path))
    print(f"Model saved successfully to: {output_path}")
except Exception as e:
    print(f"Error saving file: {e}")
    sys.exit(1)
