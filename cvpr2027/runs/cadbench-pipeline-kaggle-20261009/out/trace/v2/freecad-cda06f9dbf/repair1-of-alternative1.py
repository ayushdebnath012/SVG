import FreeCAD as App
import Part
from pathlib import Path
import math
import Sketcher

# --- Configuration derived from __file__ ---
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

# --- Part Parameters ---
PARAMS = {
    "inner_diameter": 10.0,
    "overall_height": 15.0,
    "flange_thickness": 4.0,
    "hex_nut_width_across_flats": 16.0,
    "hex_nut_width_across_corners": 16.0 / math.cos(math.radians(30.0)),
    "hex_nut_half_angle": 30.0
}

# --- Document Setup ---
doc = App.newDocument("HexFlangeNut")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObject", body)

# Create a ParameterSet object to hold our named parameters
params_obj = body.newObject("App::VarSet", "Parameters")
# Add parameters explicitly
for name, value in PARAMS.items():
    try:
        params_obj.addProperty(f"App::PropertyLength", name, "Dimensions", name)
        params_obj[name] = value
    except:
        params_obj.addProperty(f"App::PropertyAngle", name, "Dimensions", name)
        params_obj[name] = value

# --- Helper to add geometry to a sketch ---
def add_line(sketch, p1, p2, visible=True):
    sketch.addGeometry(Part.LineSegment(p1, p2), visible)

def add_circle(sketch, center, normal, radius, visible=True):
    sketch.addGeometry(Part.Circle(center, normal, radius), visible)

# --- Feature Construction ---

# 1. Base Flange Sketch (on XY plane at Z = 0)
# We create a plane object to serve as the attachment support.
plane_xy = doc.addObject("Part::Feature", "XY_Plane")
plane_xy.Placement = App.Placement(App.Vector(0,0,0))
plane_xy.Type = "Part::Plane"
doc.recompute()

sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_Flange")
sketch_base.AttachmentSupport = (plane_xy, [""])
sketch_base.MapMode = "FlatFace"
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0)) # Bottom of flange at Z=0

# Draw Flange Circle
add_circle(sketch_base, App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["flange_diameter"] / 2.0)

# Pad the Flange
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_base
pad_flange.Length = PARAMS["flange_thickness"]
pad_flange.TaperAngle = 0
pad_flange.Dir = 1 # +Z direction

# 2. Nut Body Sketch (on XY plane at Z = flange_thickness)
sketch_nut = body.newObject("Sketcher::SketchObject", "Sketch_Nut")
sketch_nut.AttachmentSupport = (plane_xy, [""])
sketch_nut.MapMode = "FlatFace"
sketch_nut.Placement = App.Placement(App.Vector(0, 0, PARAMS["flange_thickness"]))

# Draw Hexagon
# Calculate coordinates for 6 corners
h_flats = PARAMS["hex_nut_width_across_flats"] / 2.0
h_corners = PARAMS["hex_nut_width_across_corners"] / 2.0
# Angles for corners: 0, 60, 120, 180, 240, 300 degrees
angles = [0, 60, 120, 180, 240, 300]
points = [App.Vector(h_corners * math.cos(math.radians(a)), h_corners * math.sin(math.radians(a)), 0) for a in angles]

for i in range(len(points)):
    j = (i + 1) % len(points)
    add_line(sketch_nut, points[i], points[j])

# Pad the Nut Body
pad_nut = body.newObject("PartDesign::Pad", "Pad_Nut")
pad_nut.Profile = sketch_nut
# Total height of nut body (excluding flange)
pad_nut.Length = PARAMS["overall_height"] - PARAMS["flange_thickness"]
pad_nut.TaperAngle = 0
pad_nut.Dir = 1 # +Z direction

# 3. Through Hole Sketch (on XY plane at Z = overall_height)
# The hole must go all the way through the nut and flange.
# We create the sketch on the top face of the nut and use a Pocket with Type "ThroughAll".
sketch_hole_top = body.newObject("Sketcher::SketchObject", "Sketch_Hole_Top")
sketch_hole_top.AttachmentSupport = (plane_xy, [""])
sketch_hole_top.MapMode = "FlatFace"
sketch_hole_top.Placement = App.Placement(App.Vector(0, 0, PARAMS["overall_height"]))

add_circle(sketch_hole_top, App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["inner_diameter"] / 2.0)

# Create the Pocket (Hole)
# It starts at the top face and goes through all.
pocket = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket.Profile = sketch_hole_top
pocket.Type = "ThroughAll"
pocket.TaperAngle = 0

# --- Finalize ---
doc.recompute()

# Save
doc.saveAs(str(output_path))

# Report success
print(f"Part generated and saved to: {output_path}")
print("Body Object Name: Body")
print("Features: Pad_Flange, Pad_Nut, Pocket_Hole")
