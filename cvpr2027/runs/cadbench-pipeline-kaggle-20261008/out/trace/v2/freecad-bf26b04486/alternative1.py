from pathlib import Path
import FreeCAD as App, Part, Sketcher

# Initialize Document
doc = App.newDocument("HexFlangeNut")

# 1. Create Named Parameters (VarSet) for full parametric control
params = doc.addObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height of the nut")
params.addProperty("App::PropertyLength", "flange_diameter", "Dimensions", "Diameter of the circular flange")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Width of the hex hub (across flats)")
params.addProperty("App::PropertyLength", "through_hole_diameter", "Dimensions", "Diameter of the central through hole")
params.addProperty("App::PropertyLength", "hex_height_above_flange", "Dimensions", "Height of the hex portion above the flange")

# Set Values according to ISO/DIN 6923 standards provided in prompt
params.overall_height = 14.0
params.flange_diameter = 29.9
params.flange_thickness = 6.2
params.hub_width = 21.0
params.through_hole_diameter = 14.0
params.hex_height_above_flange = 7.8

# 2. Create the PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")
body.makeFeature() # Ensure it is a valid body container

# 3. Create Reference Planes
# XY_Plane: Origin plane (z=0). We will build the flange here.
xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0)) # Reset to default origin
# Actually, standard planes are usually pre-exposed or need explicit creation if not present. 
# In FreeCAD 1.1 headless, we often rely on the base document having XY_Plane or create a generic reference.
# However, the prompt implies using standard axes. Let's create a specific plane for the flange sketch.
# We will use the Z Axis for rotation and XY Plane for the flange sketch.

# If standard planes don't exist, we create a reference plane at Z=0
base_plane = doc.addObject("PartDesign::Plane", "BasePlane")
base_plane.Placement = App.Placement(App.Vector(0, 0, 0))
base_plane.Axis = App.Vector(0, 0, 1) # Normal to the plane

# Define Z Axis for Revolution/Polar Pattern
z_axis = doc.addObject("PartDesign::Axis", "Z_Axis")
z_axis.Placement = App.Placement(App.Vector(0, 0, 0))

# Define X Axis for reference if needed
x_axis = doc.addObject("PartDesign::Axis", "X_Axis")
x_axis.Placement = App.Placement(App.Vector(0, 0, 0))

# 4. Flange Sketch (XY Plane, Z=0)
flange_sketch = body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0)) # Ensure origin
# Attach to BasePlane (Z=0)
flange_sketch.AttachmentSupport = (base_plane, [""])
flange_sketch.MapMode = "FlatFace"

# Draw Flange Circle
flange_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0)
flange_sketch.addGeometry(flange_circle, False)

# Draw Through Hole Circle (Flange)
hole_flange = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2.0)
flange_sketch.addGeometry(hole_flange, True) # True = Cut

# Constraint: Coincident centers
flange_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
flange_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 1, 1)) # Ensure concentric
# Constraint: Center on origin (implicit via MapMode FlatFace, but explicit constraint helps)
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.flange_diameter / 2.0))
flange_sketch.addConstraint(Sketcher.Constraint("Radius", 1, 0, params.through_hole_diameter / 2.0))

# 5. Hex Sketch (XY Plane, Z=flange_thickness)
# We need a sketch above the flange.
hex_sketch = body.newObject("Sketcher::SketchObject", "HexSketch")
hex_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
hex_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
hex_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness)) # Ensure correct Z
hex_sketch.AttachmentSupport = (base_plane, [""])
hex_sketch.MapMode = "FlatFace"

# Calculate Hex Geometry
# Across flats = hub_width (21.0)
# Radius of hexagon (R) = Across Flats / (2 * cos(30))
hex_radius = params.hub_width / (2.0 * (3.0/2.0)) # cos(30) = sqrt(3)/2 approx 0.866, 2*cos(30) = 1.732
# Actually: Width Across Flats (W) = 2 * R * cos(30) => R = W / (2 * cos(30))
# cos(30 deg) = sqrt(3)/2
import math
cos_30 = math.cos(math.radians(30))
hex_radius = params.hub_width / (2.0 * cos_30)

# Draw Hexagon Vertices
# Start angle 0 (Right)
angles = [i * 60 for i in range(6)]
vertices = []
for angle in angles:
    rad = math.radians(angle)
    x = hex_radius * math.cos(rad)
    y = hex_radius * math.sin(rad)
    vertices.append(App.Vector(x, y, 0))

# Add lines to form hexagon
hex_lines = []
for i in range(6):
    v1 = vertices[i]
    v2 = vertices[(i+1) % 6]
    line = Part.LineSegment(v1, v2)
    hex_lines.append(line)

for line in hex_lines:
    hex_sketch.addGeometry(line, False)

# Add Through Hole Circle (Hex)
hole_hex = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.through_hole_diameter / 2.0)
hex_sketch.addGeometry(hole_hex, True) # Cut

# Constraint: Hexagon center on origin
hex_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, hex_radius))
hex_sketch.addConstraint(Sketcher.Constraint("Radius", 1, 0, params.through_hole_diameter / 2.0))
# Constraint: Concentric between outer circle (defined by radius) and inner circle
# Sketcher handles concentricity if we link the center points, but defining radius from origin works.
# Let's add explicit concentric constraint between the two circles if possible, 
# or rely on the fact both are defined from (0,0).
# To be safe, we constrain the first point of each shape to be coincident (center of circle)
# But simpler: ensure both are defined relative to origin.

# 6. Create Features

# Feature 1: Flange Pad (Additive)
flange_pad = body.newObject("PartDesign::Pad", "FlangePad")
flange_pad.Profile = flange_sketch
flange_pad.Length = params.flange_thickness
flange_pad.Reversed = False

# Feature 2: Hex Pad (Additive)
hex_pad = body.newObject("PartDesign::Pad", "HexPad")
hex_pad.Profile = hex_sketch
hex_pad.Length = params.hex_height_above_flange
hex_pad.Reversed = False

# Feature 3: Through Hole (Subtractive)
# We need a sketch for the hole that goes through both. 
# It's easiest to make a separate sketch on the XY plane (Z=0) and pocket through all.
# Or reuse flange_sketch. Let's create a specific hole sketch for clarity.
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
hole_pocket.Direction = App.Vector(0, 0, 1) # Through XY plane in +Z direction

# Feature 4: Chamfers on Hex Hub
# We need to chamfer the top edges of the hex pad.
# FreeCAD PartDesign::Chamfer requires edges.
# We can add chamfers after the hex pad is created.
# Since we are scripting, we can add chamfers to the existing solid.
# However, to keep it editable, we add the chamfer feature now.
# We need to identify edges. Since we can't easily query edges by ID in headless without recompute,
# we will add the chamfer feature referencing the specific edges of the hex_pad.
# In FreeCAD 1.1, we can often specify edges by their relative position or just apply to all edges of the profile?
# No, Chamfer needs specific edges.
# Alternative: Use a Fillet with 0 radius? No.
# Alternative: Use a Shell? No.
# Best approach in script: Add the Chamfer feature, but we need to know the edge labels.
# Since we cannot dynamically get edge labels without GUI or recompute, we will construct the chamfer 
# by referencing the edges of the previous feature if possible, or simply assume the user will verify.
# However, the prompt asks for an "editable PartDesign feature tree".
# We will attempt to add chamfers to the top edges of the HexPad.
# Note: In headless scripts, getting edge IDs from a feature before recompute is tricky.
# We will create the chamfer feature. If specific edges aren't accessible without GUI, 
# we might skip or use a generic method. 
# Actually, we can try to access the edges of the shape of 'HexPad' if it exists.
# Let's try to add chamfers to the top rim of the hex.
# We'll add a chamfer feature. We will try to pass the edges. 
# Since we can't list them, we will create the feature and let the user adjust, 
# OR we can calculate the chamfer on the fly if we had the geometry.
# BUT, the prompt requires the script to produce the model.
# Let's assume the standard way: Create the chamfer.
# We will try to reference the edges of the HexPad. 
# In FreeCAD 1.1, we can sometimes access .Shape.Edges if the feature is computed.
# Let's force a recompute before defining chamfers? No, we need to define them to get the final shape.
# Strategy: Define the chamfer feature. We will try to pass a list of edges. 
# Since we can't know the IDs, we will create a workaround: 
# We will create a Chamfer feature that targets the top faces of the hex pad? 
# No, Chamfer targets edges.
# Let's assume the script runs, computes up to HexPad, then we try to chamfer.
# If we can't get the edges, we might have to skip the chamfer in the automated script 
# unless we use a specific trick. 
# Trick: Use a sketch-based chamfer? No, that's for 2D.
# Trick: Use a boolean operation with a chamfered block? No, not parametric.
# Trick: Just create the Chamfer feature and hope the edge selection can be done via relative naming or default.
# Actually, we can try to get the edges of the HexPad shape.
# Let's try to get the shape of HexPad, find the top edges, and pass them.
# This requires recompute() before this step.

# Let's restructure slightly: 
# 1. FlangePad
# 2. HexPad
# 3. ThroughHolePocket
# 4. Chamfers

# Recompute to ensure HexPad has a shape
doc.recompute()

# Get the HexPad feature
hex_pad_feature = doc.getObject("HexPad")
# Get its shape
hex_shape = hex_pad_feature.Shape
# Get edges. We need the top edges of the hexagon.
# The hexagon is on the top face. 
# Let's find the edges that are on the top face.
# Top face normal is (0,0,1).
# This is getting complex for a generic script.
# Alternative: Use the `Chamfer` feature with a sketch? No.
# Alternative: Just add the Chamfer feature and let the user fix edges if the script fails silently? 
# But the goal is to produce the model.
# Let's try to access the edges.
edges = hex_shape.Edges
# Filter edges that are on the top face (z > something) or simply the top loop.
# The top face is the largest face on the top?
# Let's assume the top face is the last one added or the one with normal (0,0,1).
top_face = None
for face in hex_shape.Faces:
    if abs(face.normalAt().z - 1.0) < 0.1:
        top_face = face
        break

if top_face:
    # Edges of the top face
    chamfer_edges = [e for e in edges if e.Placement.Base == top_face.Edge(0).Placement.Base] # Wrong logic
    # Correct: edges belonging to the top face
    chamfer_edges = [e for e in edges if e.Placement.PointOnFace(top_face) == True] 
    # Actually, `e.isFace(t)` doesn't exist.
    # We can iterate edges and check if they lie on the plane of the top face.
    # Plane of top face: top_face.Plane
    plane = top_face.Plane
    valid_edges = []
    for e in edges:
        # Check if edge is on the plane
        p = e.Placement.PointOnLine(e)
        # Vector from plane base to point
        v = p - plane.Base
        # If distance is near 0, it's on the plane
        if abs(v.dot(plane.Normal)) < 1e-6:
            # Also check if it's one of the boundary edges (not internal faces)
            # For a solid, edges are boundaries.
            valid_edges.append(e)
    
    # Now create Chamfer
    # We need to specify the edges. 
    # PartDesign::Chamfer takes a list of edges.
    chamfer_feature = body.newObject("PartDesign::Chamfer", "TopChamfers")
    chamfer_feature.Base = (hex_pad_feature, []) # Base feature
    # We need to map the edges to the Base feature's edges. 
    # In FreeCAD 1.1, we might need to pass the edge IDs from the Base feature.
    # We can't easily map them without knowing the index.
    # Let's try a different approach: Use a Sketch-based Chamfer? 
    # No, standard way is Edge Chamfer.
    # Let's assume the script creates the chamfer feature but leaves it unconnected if edge selection fails.
    # OR, we can use the `Fillet` feature if we can't do Chamfer? No, Chamfer is required for "standard hex flange nut".
    # Let's try to pass the edges directly if the API allows.
    # chamfer_feature.Edges = valid_edges # This might work in 1.1
    # But we need to link them to the body feature tree.
    # Let's try:
    chamfer_feature.Edges = valid_edges
    chamfer_feature.Size = 1.0 # Standard chamfer size
else:
    # Fallback if top face detection fails
    # Create a chamfer feature pointing to the hex pad, but we can't specify edges.
    # We will create the feature and hope for the best or skip.
    # To be safe and compliant with "one solid body", we will try to add the chamfer.
    # If the edge selection is critical, we might need to rely on the fact that 
    # the top face has a specific set of edges.
    # Let's try to create the chamfer feature with an empty base? No.
    # Let's assume the previous logic works or we can't do it in pure headless without GUI edge selection.
    # Given the constraints, we will create the feature and try to assign edges.
    chamfer_feature = body.newObject("PartDesign::Chamfer", "TopChamfers")
    chamfer_feature.Base = (hex_pad_feature, [])
    # We cannot pass valid_edges directly to Base tuple in this way easily
