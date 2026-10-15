import FreeCAD as App
import Part
import Sketcher
import math
import os
from pathlib import Path

# Create a new document
doc = App.newDocument("HexFlangeNut")

# --- 1. Define Named Parameters on the Body ---
# We create a PartDesign::Body and add properties directly to it.
# This ensures they are editable document objects driving the geometry.
body = doc.addObject("PartDesign::Body", "Body")

# Add parameters
body.addProperty("App::PropertyLength", "overall_height", "Dimensions")
body.overall_height = 9.0

body.addProperty("App::PropertyLength", "flange_diameter", "Dimensions")
body.flange_diameter = 14.0

body.addProperty("App::PropertyLength", "flange_thickness", "Dimensions")
body.flange_thickness = 3.0

body.addProperty("App::PropertyLength", "hub_width", "Dimensions")
body.hub_width = 6.0  # Derived: overall_height - flange_thickness

body.addProperty("App::PropertyLength", "bore_diameter", "Dimensions")
body.bore_diameter = 6.0

body.addProperty("App::PropertyLength", "hex_across_flats", "Dimensions")
body.hex_across_flats = 10.0

# Hex across corners is derived: width_across_flats / cos(30)
body.addProperty("App::PropertyLength", "hex_across_corners", "Dimensions")
body.hex_across_corners = 11.547005383792516 

body.addProperty("App::PropertyAngle", "hex_angle", "Dimensions")
body.hex_angle = 30.0

doc.recompute()

# --- 2. Ensure Standard Planes Exist ---
# FreeCAD usually has these, but we ensure they exist for robustness.
standard_objects = ["XY_Plane", "XZ_Plane", "YZ_Plane", "X_Axis", "Y_Axis", "Z_Axis"]
for name in standard_objects:
    if not doc.exists(name):
        obj = doc.addObject("Part::Plane", name)
        # Default placement for planes is usually at origin, orientation depends on name
        # We set explicit placements to match standard FreeCAD behavior
        if "XY" in name:
            obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        elif "XZ" in name:
            obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        elif "YZ" in name:
            obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        doc.recompute()

# --- 3. Create Base Sketch (Hub Hexagon + Bore) ---
# Plane: XY_Plane. Origin: (0,0,0).
sketch_hub = body.newObject("Sketcher::SketchObject", "HubSketch")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch_hub.Support = (doc.getObject("XY_Plane"), [])
sketch_hub.MapMode = "FlatFace"

# Calculate Hexagon Radius
# Width across flats (W) = 10.0
# Apothem (distance from center to side) = W / 2 = 5.0
# Radius (distance from center to vertex) = Apothem / cos(30) = 5.0 / (sqrt(3)/2) = 10.0 / sqrt(3)
R_hex = body.hex_across_flats / (2 * math.cos(math.radians(30)))

# Add Hexagon Points
hex_points = []
for i in range(6):
    angle = i * 60.0
    rad = math.radians(angle)
    x = R_hex * math.cos(rad)
    y = R_hex * math.sin(rad)
    p = sketch_hub.addGeometry(Part.Point(App.Vector(x, y, 0)), False)
    hex_points.append(p)

# Constrain points to be distance R_hex from origin
for p in hex_points:
    sketch_hub.addConstraint(Sketcher.Constraint("Distance", p, 0, 0, 0, R_hex), False)

# Connect points to form hexagon
for i in range(6):
    next_i = (i + 1) % 6
    sketch_hub.addConstraint(Sketcher.Constraint("LineToNext", hex_points[i], hex_points[next_i]), False)

# Add Bore Circle
circle = sketch_hub.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), body.bore_diameter / 2), False)
sketch_hub.addConstraint(Sketcher.Constraint("Coincident", circle, 0, 0, 0, 0, 0), False)
sketch_hub.addConstraint(Sketcher.Constraint("Radius", circle, 0, 0, 0, body.bore_diameter/2), False)

doc.recompute()

# --- 4. Pad the Hub ---
# Pad the hexagon up by hub_width (6mm)
pad_hub = body.newObject("PartDesign::Pad", "PadHub")
pad_hub.Profile = sketch_hub
pad_hub.Length = body.hub_width
pad_hub.Midplane = False
pad_hub.Reverse = False
doc.recompute()

# --- 5. Create Flange Sketch ---
# We need to sketch on the top face of the PadHub.
# Find the top face (normal +Z)
top_face = None
for face in pad_hub.Shape.Faces:
    if abs(face.normalAt().toTuple()[2]) > 0.99: # Normal is mostly Z
        top_face = face
        break

if not top_face:
    raise RuntimeError("Could not find top face of PadHub.")

flange_sketch = body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
flange_sketch.Support = (top_face, [])
flange_sketch.MapMode = "FlatFace"

# Add Flange Circle (Outer)
# Diameter = flange_diameter
flange_circle = flange_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), body.flange_diameter / 2), False)
flange_sketch.addConstraint(Sketcher.Constraint("Coincident", flange_circle, 0, 0, 0, 0, 0), False)
flange_sketch.addConstraint(Sketcher.Constraint("Radius", flange_circle, 0, 0, 0, body.flange_diameter/2), False)

# Add Bore Circle (Inner) - to define the hole for the flange part
# We reuse the bore diameter
bore_circle = flange_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), body.bore_diameter / 2), False)
flange_sketch.addConstraint(Sketcher.Constraint("Coincident", bore_circle, 0, 0, 0, 0, 0), False)
flange_sketch.addConstraint(Sketcher.Constraint("Radius", bore_circle, 0, 0, 0, body.bore_diameter/2), False)

doc.recompute()

# --- 6. Pad the Flange ---
# Pad the flange circle up by flange_thickness (3mm)
pad_flange = body.newObject("PartDesign::Pad", "PadFlange")
pad_flange.Profile = flange_sketch
pad_flange.Length = body.flange_thickness
pad_flange.Midplane = False
pad_flange.Reverse = False
doc.recompute()

# --- 7. Through Bore Pocket ---
# Create a sketch for the through hole on the bottom face (or just use the existing geometry)
# To ensure it goes through the entire part, we can use a sketch on the bottom face.
# Find bottom face (normal -Z)
bottom_face = None
for face in pad_hub.Shape.Faces:
    if abs(face.normalAt().toTuple()[2]) < -0.99: # Normal is mostly -Z
        bottom_face = face
        break

if not bottom_face:
    raise RuntimeError("Could not find bottom face of PadHub.")

sketch_bore = body.newObject("Sketcher::SketchObject", "BoreSketch")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch_bore.Support = (bottom_face, [])
sketch_bore.MapMode = "FlatFace"

# Add Bore Circle
bore_sketch_circle = sketch_bore.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), body.bore_diameter / 2), False)
sketch_bore.addConstraint(Sketcher.Constraint("Coincident", bore_sketch_circle, 0, 0, 0, 0, 0), False)
sketch_bore.addConstraint(Sketcher.Constraint("Radius", bore_sketch_circle, 0, 0, 0, body.bore_diameter/2), False)

pocket = body.newObject("PartDesign::Pocket", "PocketBore")
pocket.Profile = sketch_bore
pocket.Type = "ThroughAll"
pocket.Clearance = 0.0
doc.recompute()

# --- 8. Save the Document ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_suffix(".FCStd")

# Save
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
