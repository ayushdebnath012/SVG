import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# Create a new document
doc = App.newDocument("HexFlangeNut")

# --- Parameters ---
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Thread hole diameter")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of nut")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of base flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of base flange")
params.addProperty("App::PropertyLength", "hex_width_across_flats", "Dimensions", "Hex width across flats")
params.addProperty("App::PropertyLength", "hex_width_across_corners", "Dimensions", "Hex width across corners")
params.addProperty("App::PropertyAngle", "hex_half_angle", "Dimensions", "Half angle of hexagon")

# Set values based on prompt
params.inner_diameter = 10.0
params.overall_height = 15.0
params.flange_diameter = 22.0
params.flange_thickness = 4.0
params.hex_width_across_flats = 16.0
params.hex_width_across_corners = 18.475208614068023
params.hex_half_angle = 30.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Flange) ---
# Create sketch on XY plane
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.ConstrainAuto = True

# Add Circle for Flange Outer Diameter
circle_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0)
sketch_flange.addGeometry(circle_flange, False)

# Add Circle for Flange Inner Diameter (Cutout for nut body)
circle_inner = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hex_width_across_flats / 2.0)
sketch_flange.addGeometry(circle_inner, False)

# Add Circle for Through Hole
circle_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_flange.addGeometry(circle_hole, False)

# --- Nut Body Sketch ---
# Create sketch on XZ plane. 
# We want the sketch to lie in the XZ plane. 
# Standard Sketcher on XZ plane: Local X = World X, Local Y = World Z, Local Z = World Y.
# We will construct the hexagon in this local coordinate system.
sketch_nut = body.newObject("Sketcher::SketchObject", "Sketch_Nut")
sketch_nut.Placement = App.Placement(App.Vector(0, 0, 0))

# Define Hexagon Vertices
# Width across flats = params.hex_width_across_flats
# Width across corners = params.hex_width_across_corners
# Angle of flat side relative to X axis? 
# Standard hex: flats are parallel to X axis if vertices are at 30, 90, 150, 210, 270, 330 degrees.
# Radius to corner = hex_width_across_corners / 2
R_corner = params.hex_width_across_corners / 2.0

verts = []
for i in range(6):
    angle = 30 + i * 60
    x = R_corner * math.cos(math.radians(angle))
    y = R_corner * math.sin(math.radians(angle))
    verts.append(App.Vector(x, y, 0))

# Create a closed loop of lines
lines = []
for i in range(6):
    p1 = verts[i]
    p2 = verts[(i+1)%6]
    lines.append(Part.LineSegment(p1, p2))

for line in lines:
    sketch_nut.addGeometry(line, False)

# --- Features ---

# 1. Pad the Flange (Base)
# Extrude the flange sketch along the Z axis (World Z)
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_flange
pad_flange.Length = params.flange_thickness
pad_flange.Direction = (0, 0, 1) # +Z

# 2. Pad the Nut Body
# Extrude the nut sketch along the Y axis (World Y)
# In the sketch's local coords (on XZ plane), the Y axis of the sketch corresponds to World Y.
# Wait, let's re-verify the orientation.
# Placement is default (0,0,0). 
# Sketcher's local axes on XZ plane: 
# Local X -> World X
# Local Y -> World Z
# Local Z -> World Y
# We want to extrude along World Y. So we need Local Z.
# Vector (0, 0, 1) in sketch coords is (0, 0, 1) in world coords? 
# Yes, because Local Z is aligned with World Y.
pad_nut = body.newObject("PartDesign::Pad", "Pad_Nut")
pad_nut.Profile = sketch_nut
# Length is overall_height - flange_thickness
pad_nut.Length = params.overall_height - params.flange_thickness
pad_nut.Direction = (0, 0, 1) # Local Z -> World Y

# --- Through Hole ---
# Create a sketch on the XY plane (same as flange) and use a Pocket with "ThroughAll".
# This will cut a hole through the flange and the nut.
sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0), False)

pocket = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket.Profile = sketch_hole
pocket.Type = "ThroughAll"
pocket.Direction = (0, 0, 1) # +Z

# --- Fillets ---
# Add fillets to the top edges of the hexagon on the nut body.
# We need to identify these edges dynamically.
# We will do this after the initial recompute.
doc.recompute()

# Helper to get top face edges
def get_top_hex_edges(body_obj):
    solid = body_obj.Shape
    top_face = None
    for face in solid.Faces:
        # Check normal Z component
        if abs(face.normalAt().toTuple()[2] - 1.0) < 0.1:
            top_face = face
            break
    
    if not top_face:
        return []
    
    hex_edges = []
    for edge in top_face.Edges:
        # Check if it's a line (hex) or circle (hole)
        # We can check the shape type or length
        # Hex edges are lines. Hole edges are circles.
        # In Part, we can check the shape type.
        # Part.TopoDS.Edge has a .ShapeType property or we can check the underlying shape.
        # A simpler heuristic: Hex edges are straight lines.
        # We can check if the edge is a circle by checking the number of vertices or using Part::ShapeType.
        # However, in FreeCAD 1.1, we can check the type of the edge's shape.
        # Let's try to get the shape of the edge.
        try:
            edge_shape = edge.Shape
            # If it's a circle, it has a specific type.
            # We can check if it's a circle by checking the number of vertices (circle has 1 vertex in B-Rep usually, or many in mesh)
            # Or simply check the type string.
            # Let's use a robust method: check if the edge is a circle.
            # In Part, we can check the type.
            # But let's assume the hole is the only circle on that face.
            # We can check the length of the edge. Hex edges are straight.
            # Let's check the type of the edge.
            # edge.ShapeType is not directly available in Python API for TopoDS.Edge in the same way.
            # Let's try to get the shape and check its type.
            if edge_shape.ShapeType == "Circle":
                continue
            hex_edges.append(edge)
        except:
            continue
            
    return hex_edges

try:
    top_edges = get_top_hex_edges(body)
    if len(top_edges) > 0:
        fillet = body.newObject("PartDesign::Fillet", "Fillet_Top")
        fillet.Base = (top_edges, [])
        fillet.Radius = 1.0
        fillet.setExpression("Radius", "1.0")
except Exception as e:
    print(f"Could not add fillet automatically: {e}")

# Final recompute to apply fillets
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))
