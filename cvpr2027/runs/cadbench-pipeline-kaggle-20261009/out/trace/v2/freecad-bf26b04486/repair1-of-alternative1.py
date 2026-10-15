from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# 1. Initialize Document
doc = App.newDocument("HexFlangeNut")

# 2. Create Named Parameters (VarSet)
params = doc.addObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Flange diameter")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange thickness")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hex width across flats")
params.addProperty("App::PropertyLength", "through_hole_diameter", "Dimensions", "Through hole diameter")
params.addProperty("App::PropertyLength", "hex_height_above_flange", "Dimensions", "Hex height above flange")

# Set Values
params.overall_height = 14.0
params.flange_diameter = 29.9
params.flange_thickness = 6.2
params.hub_width = 21.0
params.through_hole_diameter = 14.0
params.hex_height_above_flange = 7.8

# 3. Create PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# 4. Create Reference Planes and Axes
# Base Plane at Z=0 (XY plane)
base_plane = doc.addObject("PartDesign::Plane", "BasePlane")
base_plane.Placement = App.Placement(App.Vector(0, 0, 0))

# Z Axis for revolution/patterns
z_axis = doc.addObject("PartDesign::Axis", "Z_Axis")
z_axis.Placement = App.Placement(App.Vector(0, 0, 0))

# 5. Create Flange Sketch (at Z=0)
flange_sketch = body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
flange_sketch.AttachmentSupport = (base_plane, [""])
flange_sketch.MapMode = "FlatFace"

# Flange Circle
flange_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0)
flange_sketch.addGeometry(flange_circle, False)

# Through Hole Circle (Flange)
hole_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2.0)
flange_sketch.addGeometry(hole_flange, True) # Cut

# Constraints for Flange Sketch
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.flange_diameter / 2.0))
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 1, 0, params.through_hole_diameter / 2.0))
flange_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Concentric centers

# 6. Create Hex Sketch (at Z=flange_thickness)
# Calculate Hex Radius
cos_30 = math.cos(math.radians(30))
hex_radius = params.hub_width / (2.0 * cos_30)

hex_sketch = body.newObject("Sketcher::SketchObject", "HexSketch")
hex_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
hex_sketch.AttachmentSupport = (base_plane, [""])
hex_sketch.MapMode = "FlatFace"

# Generate Hexagon Vertices
angles = [i * 60 for i in range(6)]
vertices = []
for angle in angles:
    rad = math.radians(angle)
    x = hex_radius * math.cos(rad)
    y = hex_radius * math.sin(rad)
    vertices.append(App.Vector(x, y, 0))

# Add Hexagon Lines
for i in range(6):
    v1 = vertices[i]
    v2 = vertices[(i+1) % 6]
    line = Part.LineSegment(v1, v2)
    hex_sketch.addGeometry(line, False)

# Through Hole Circle (Hex)
hole_hex = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2.0)
hex_sketch.addGeometry(hole_hex, True) # Cut

# Constraints for Hex Sketch
hex_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, hex_radius))
hex_sketch.addConstraint(Sketcher.Constraint("Radius", 1, 0, params.through_hole_diameter / 2.0))
hex_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))

# 7. Create Features

# Feature 1: Flange Pad
flange_pad = body.newObject("PartDesign::Pad", "FlangePad")
flange_pad.Profile = flange_sketch
flange_pad.Length = params.flange_thickness
flange_pad.Reversed = False

# Feature 2: Hex Pad
hex_pad = body.newObject("PartDesign::Pad", "HexPad")
hex_pad.Profile = hex_sketch
hex_pad.Length = params.hex_height_above_flange
hex_pad.Reversed = False

# Feature 3: Through Hole Pocket
hole_sketch = body.newObject("Sketcher::SketchObject", "HoleSketch")
hole_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
hole_sketch.AttachmentSupport = (base_plane, [""])
hole_sketch.MapMode = "FlatFace"

hole_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2.0)
hole_sketch.addGeometry(hole_circle, False)
hole_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.through_hole_diameter / 2.0))

hole_pocket = body.newObject("PartDesign::Pocket", "ThroughHolePocket")
hole_pocket.Profile = hole_sketch
hole_pocket.Type = "ThroughAll"
hole_pocket.Direction = App.Vector(0, 0, 1)

# Feature 4: Chamfers on Hex Top Edges
# We need to identify the top edges of the HexPad.
# Since we are in headless mode, we cannot interactively select edges.
# We will attempt to access the edges of the HexPad shape after recomputing.
# Note: This requires the HexPad to be computed first.

# Force recompute to ensure shapes exist
doc.recompute()

# Get HexPad feature and its shape
hex_pad_feature = doc.getObject("HexPad")
hex_shape = hex_pad_feature.Shape

# Find the top face (normal pointing +Z)
top_face = None
for face in hex_shape.Faces:
    if abs(face.normalAt().z - 1.0) < 0.1:
        top_face = face
        break

if top_face:
    # Get edges belonging to the top face
    chamfer_edges = []
    for edge in hex_shape.Edges:
        # Check if edge lies on the plane of the top face
        # Edge is defined by a line. Check if the line is on the plane.
        # Plane equation: N . (P - B) = 0
        plane = top_face.Plane
        p1 = edge.Placement.PointOnLine(edge)
        p2 = edge.Placement.PointOnLine(edge) # This returns the same point if not careful, use Edge endpoints
        # Better: use edge.Vertexes
        v1 = edge.Vertexes[0].Point
        v2 = edge.Vertexes[1].Point
        
        # Check distance of v1 and v2 to the plane
        dist1 = abs((v1 - plane.Base).dot(plane.Normal))
        dist2 = abs((v2 - plane.Base).dot(plane.Normal))
        
        if dist1 < 1e-6 and dist2 < 1e-6:
            chamfer_edges.append(edge)
    
    # Create Chamfer Feature
    chamfer_feature = body.newObject("PartDesign::Chamfer", "TopChamfers")
    chamfer_feature.Base = (hex_pad_feature, [])
    chamfer_feature.Edges = chamfer_edges
    chamfer_feature.Size = 1.0 # Standard chamfer size
else:
    print("Warning: Could not identify top face for chamfer.")

# 8. Final Recompute
doc.recompute()

# 9. Save the file
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
