import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derive output path from __file__ to ensure it is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# --- Parameters ---
# Defined as requested, noting the geometric implication:
# Flange (3mm) + Hub (10mm) = 13mm total height.
# The prompt specifies overall_height=9.0, but also specifies hub_width=10.0 and flange_thickness=3.0.
# To satisfy the explicit dimensions for the features (Flange and Hub), we will use the sum (13mm).
# If strict adherence to 9mm total height is required, hub_width would need to be 6mm.
# Given the explicit "hub_width = 10.0" in the parameter list, we prioritize that dimension for the Hub feature.
params = {
    "overall_height": 9.0,
    "flange_diameter": 14.0,
    "flange_thickness": 3.0,
    "hub_width": 10.0,
    "bore_diameter": 6.0,
    "hex_head_width_across_flats": 10.0,
    "hex_head_width_across_corners": 10.0 / math.cos(math.radians(30)),
    "hex_head_angle": 30.0
}

# --- Document Setup ---
doc = App.newDocument("HexFlangeNut")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters Object ---
# Create a VarSet to hold named parameters
params_obj = body.newObject("App::VarSet", "Parameters")
for name, value in params.items():
    if isinstance(value, float):
        if name == "hex_head_angle":
            prop_type = "App::PropertyAngle"
        else:
            prop_type = "App::PropertyLength"
    else:
        prop_type = "App::PropertyString"
        
    params_obj.addProperty(prop_type, name, "Dimensions", f"Parameter: {name}")
    params_obj[name] = value

# --- Feature 1: Flange Pad ---
# Sketch Flange on XY Plane (Z=0)
sketch_flange = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_flange.ConstrainToCurrentPlane = True
sketch_flange.MapMode = "FlatFace"

# Add Flange Outer Circle
circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params["flange_diameter"] / 2)
sketch_flange.addGeometry(circle_geom, False)

# Add Flange Bore (for reference)
bore_radius = params["bore_diameter"] / 2
bore_circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_radius)
sketch_flange.addGeometry(bore_circle_geom, False)

# Constraint: Concentric (Center to Center)
# Index 0 is outer circle, Index 1 is inner circle.
sketch_flange.addConstraint(Sketcher.Constraint("Concentric", 0, 1, 1, 1))

# Pad Flange (Downwards)
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_flange
pad_flange.Length = params["flange_thickness"]
pad_flange.Reversed = True # Extrude in negative Z

# --- Feature 2: Hex Hub Pad ---
# Sketch Hex on XY Plane (Z=0)
# We will pad this downwards. Since it starts at Z=0 and goes down, 
# it will merge with the flange (which is also at Z=0 going down).
sketch_hex = body.newObject("Sketcher::SketchObject", "Sketch_Hex")
sketch_hex.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hex.ConstrainToCurrentPlane = True
sketch_hex.MapMode = "FlatFace"

# Hexagon Geometry
# Width across flats = 10.0
# Width across corners = 11.547...
R = params["hex_head_width_across_corners"] / 2

# Vertices
verts = []
for i in range(6):
    angle = math.radians(i * 60)
    x = R * math.cos(angle)
    y = R * math.sin(angle)
    verts.append(App.Vector(x, y, 0))

# Add Line Segments
for i in range(6):
    p1 = verts[i]
    p2 = verts[(i+1)%6]
    line = Part.LineSegment(p1, p2)
    sketch_hex.addGeometry(line, False)

# Pad Hex (Downwards)
# Length = hub_width. 
# Since it starts at Z=0 and goes down, total height becomes flange_thickness + hub_width.
pad_hex = body.newObject("PartDesign::Pad", "Pad_Hex")
pad_hex.Profile = sketch_hex
pad_hex.Length = params["hub_width"]
pad_hex.Reversed = True

# --- Feature 3: Bore Pocket ---
# Sketch Bore on XY Plane (Z=0)
sketch_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bore.ConstrainToCurrentPlane = True
sketch_bore.MapMode = "FlatFace"

# Add Bore Circle
bore_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params["bore_diameter"] / 2)
sketch_bore.addGeometry(bore_geom, False)

# Pocket Bore (Through All)
pocket_bore = body.newObject("PartDesign::Pocket", "Pocket_Bore")
pocket_bore.Profile = sketch_bore
pocket_bore.Type = "ThroughAll"

# --- Finalize ---
doc.recompute()

# Save the file next to the script
doc.saveAs(str(output_path))
