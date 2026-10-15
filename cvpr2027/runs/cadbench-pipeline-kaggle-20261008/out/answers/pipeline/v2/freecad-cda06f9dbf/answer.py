import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HexFlangeNut")

# --- Parameters ---
# We will use App::VarSet to store parameters that can be edited in the tree
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
sketch_flange.TechDrawPictogramSequence = 1
sketch_flange.ViewObject.DisplayMode = "Flat"

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
# Create sketch on XZ plane (rotated 90 deg around Y to stand up)
sketch_nut = body.newObject("Sketcher::SketchObject", "Sketch_Nut")
# Attach to XZ plane. In FreeCAD, XZ plane is usually at Z=0, but we need to orient it correctly.
# Standard planes: XY (Z=0), XZ (Y=0), YZ (X=0).
# We want the sketch to be in the XZ plane, so we attach to XZ_Plane.
# However, the default orientation of XZ_Plane in Sketcher might vary. 
# Let's explicitly place it.
# XZ Plane normal is Y. We want the sketch to lie in XZ.
# Placement: Origin (0,0,0). Rotation: 0,0,0 usually aligns Sketcher's local XY with World XY.
# To get Sketcher's local XY to align with World XZ, we rotate -90 deg around Y axis.
sketch_nut.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, -90))

# Add Hexagon
# Center at (0,0) in sketch coords.
# Width across flats = params.hex_width_across_flats
# Width across corners = params.hex_width_across_corners
# Half angle = params.hex_half_angle
# We construct the hexagon using lines and constraints or a polygon.
# Using a polygon approach with vertices derived from parameters.
# Radius to flat = hex_width_across_flats / 2
# Radius to corner = hex_width_across_corners / 2
# Angle of flat side relative to X axis? 
# Standard hex: flats are parallel to X axis if vertices are at 0, 60, 120...
# Let's define vertices.
# If width across flats is Wf, distance from center to flat is Wf/2.
# If width across corners is Wc, distance from center to corner is Wc/2.
# Angle of corner from center: 30, 90, 150, 210, 270, 330 (if flats are horizontal).
# Let's verify: 
# Point at 30 deg: x = R*cos(30), y = R*sin(30). 
# Distance between (30) and (150) is 2*R*sin(60) = 2*(Wc/2)*sin(60) = Wc * sqrt(3)/2.
# We want this to be Wf. So Wf = Wc * sqrt(3)/2 => Wc = Wf * 2/sqrt(3) = Wf / cos(30). Matches.
# So vertices at 30, 90, 150, 210, 270, 330 degrees work for a flat-top hexagon.

R_corner = params.hex_width_across_corners / 2.0
R_flat = params.hex_width_across_flats / 2.0

# Define vertices
verts = []
for i in range(6):
    angle = 30 + i * 60
    x = R_corner * App.Vector(cos(angle), sin(angle), 0).X
    y = R_corner * App.Vector(cos(angle), sin(angle), 0).Y
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
# Extrude the flange sketch along the Y axis (which is the sketch's local Z after rotation? No.)
# Sketch is in XZ plane. Local X is World X. Local Y is World Z. Local Z is World Y.
# We want to extrude along World Y (the axis of the nut).
# So we extrude along the sketch's local Z axis.
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_flange
# Length is flange_thickness
pad_flange.Length = params.flange_thickness
# Direction: +Z in sketch coords corresponds to +Y in world coords.
pad_flange.Direction = (1, 0, 0) # Sketcher direction vector in sketch coords. 
# Wait, Sketcher::Pad Direction is defined in the sketch's local coordinate system.
# Our sketch is in XZ plane. Local X=World X, Local Y=World Z, Local Z=World Y.
# We want to go along World Y. So we need Local Z.
# Vector (0, 0, 1) in sketch coords is (0, 0, 1) in world coords? 
# Let's re-verify placement.
# Placement: App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, -90))
# Rotation(0, 0, -90) rotates around World Z by -90.
# World X -> World X
# World Y -> World Y
# World Z -> World Z
# Wait, Rotation(0,0,-90) in FreeCAD (Euler angles) usually means:
# Rotate around X by 0, Y by 0, Z by -90.
# This rotates the local X axis to local Y? No.
# Let's use a simpler approach: Explicitly define the sketch plane and orientation.
# Actually, let's just use the standard XY plane for the flange and extrude along Z.
# Then rotate the whole body? No, PartDesign features are sequential.
# Let's stick to the plan: Flange on XY, extrude along Z. Then Nut on XZ?
# If Flange is on XY (Z=0), extruding along Z makes a cylinder.
# Then Nut sketch on XZ (Y=0). Extruding along Y makes a cylinder.
# This works perfectly.

# RE-DO SKETCH FLANGE:
# Place on XY plane. Extrude along Z.
sketch_flange.Placement = App.Placement(App.Vector(0, 0, 0)) # Default XY
# Circle Flange
sketch_flange.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.flange_diameter / 2.0), False)
# Circle Inner (Cutout)
sketch_flange.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hex_width_across_flats / 2.0), False)
# Circle Hole
sketch_flange.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0), False)

# Pad Flange
pad_flange = body.newObject("PartDesign::Pad", "Pad_Flange")
pad_flange.Profile = sketch_flange
pad_flange.Length = params.flange_thickness
pad_flange.Direction = (0, 0, 1) # +Z

# RE-DO SKETCH NUT:
# Place on XZ plane. Extrude along Y.
# XZ Plane is at Y=0. Normal is Y.
# We need to orient the sketch so that its "Up" (Local Z) aligns with World Y.
# Standard Sketcher on XZ plane: Local X = World X, Local Y = World Z, Local Z = World Y.
# So extruding along Local Z (+1, 0, 0 in sketch coords) goes along World Y.
sketch_nut.Placement = App.Placement(App.Vector(0, 0, 0)) # Default XZ
# Add Hexagon
for line in lines:
    sketch_nut.addGeometry(line, False)

# Pad Nut
pad_nut = body.newObject("PartDesign::Pad", "Pad_Nut")
pad_nut.Profile = sketch_nut
# Length is overall_height - flange_thickness
pad_nut.Length = params.overall_height - params.flange_thickness
pad_nut.Direction = (0, 0, 1) # Local Z -> World Y

# --- Through Hole ---
# We need a hole through the entire part.
# The part is now a union of Pad_Flange and Pad_Nut.
# The hole is circular, centered on the axis.
# We can create a sketch on the top face of the nut (or any face) and use a Pocket.
# Or simpler: Create a sketch on the XY plane (same as flange) but offset?
# No, the hole goes through the nut body.
# Let's create a sketch on the top face of the nut (which is at Z = flange_thickness).
# But we don't know the face index easily without recomputing or querying.
# Alternative: Create a sketch on the XY plane (Z=0) and use a Pocket with "ThroughAll"?
# If we pocket from Z=0 upwards, it will cut through the flange and the nut.
# Yes, that works. The hole is centered on the axis.
# Sketch on XY plane (Z=0). Circle diameter = inner_diameter.
# Pocket Type = ThroughAll. Direction = +Z.

sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0), False)

pocket = body.newObject("PartDesign::Pocket", "Pocket_Hole")
pocket.Profile = sketch_hole
pocket.Type = "ThroughAll"
pocket.Direction = (0, 0, 1) # +Z

# --- Fillets ---
# Add fillets to the edges of the nut body (between flange and nut) and maybe the corners?
# The prompt mentions "hexagonal nut body... corner profile".
# Usually, a hex nut has a fillet at the top corners of the hexagon.
# Let's add a fillet to the top edges of the nut.
# We need to select the edges.
# After recompute, we can select edges by name or index? 
# In script, we can select edges from the solid.
# However, PartDesign::Fillet requires a list of edges.
# We can get the edges of the solid.
# But the solid is the result of the previous features.
# Let's add a Fillet feature.
# We need to identify the edges.
# The edges of the hexagon on the top face of the nut.
# Since we can't easily query edge names in a headless script without recomputing and inspecting,
# we can try to select by position or use a generic approach.
# Actually, we can use the `Edge` object from the solid.
# Let's assume the user wants a standard fillet on the top corners.
# We will add a Fillet feature.
# To make it robust, we can try to find edges near the top corners.
# But for a script, it's safer to define the fillet on the edges of the sketch if possible?
# No, Fillet is a 3D feature.
# Let's try to select the top edges of the hexagon.
# We can get the solid, iterate edges, and pick those that are on the top face and near the corners.
# This is complex for a single script.
# Alternative: Use a Chamfer or just leave it sharp? The prompt says "corner profile".
# Let's try to add a fillet with a small radius.
# We will attempt to select the top edges of the hexagon.
# After recompute, the solid is `body.Shape`.
# We can get the edges of the top face.
# Top face is likely the one with normal (0,0,1).
# Let's implement a helper to get top edges.

# Wait, the prompt asks for "corner profile". 
# Maybe it implies the hexagon shape itself (width across corners vs flats) defines the profile, 
# and we don't necessarily need a fillet feature if the geometry is sharp.
# But "corner profile" often implies rounding.
# Let's add a fillet. We'll try to select the top edges of the hexagon.
# We can do this by getting the solid, finding the face with normal (0,0,1), getting its edges, 
# and filtering for the hexagon edges (length approx hex_width_across_flats/sin(60)?).
# Actually, the top face is a hexagon.
# Let's try to select the edges of the top face.
# We can use `body.getSubShapeName("Edge")`? No, that's not direct.
# We can iterate `body.Shape.Edges`.
# Let's do this after recompute.

# --- Finalize ---
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

# Optional: Add a fillet if we can identify the edges dynamically
# This part is tricky in headless mode without knowing the exact edge indices.
# Given the constraints, we will rely on the parametric geometry (width across corners) 
# to define the "profile". If a fillet is strictly required, it might need manual adjustment 
# or a more complex edge selection algorithm. 
# However, to ensure the script runs without errors and produces the main geometry correctly,
# we will skip the dynamic edge selection for the fillet to avoid potential crashes 
# if the topology changes unexpectedly, as the core geometry (hex, flange, hole) is fully parametric.
# If a fillet is absolutely necessary, one would typically select the edges in the GUI.
# But let's try a simple approach: Select the top face edges.
# We can get the top face by normal.
try:
    # Get the solid
    solid = body.Shape
    # Find face with normal close to (0,0,1)
    top_face = None
    for face in solid.Faces:
        if abs(face.normalAt().toTuple()[2] - 1.0) < 0.1:
            top_face = face
            break
    
    if top_face:
        # Get edges of this face
        face_edges = top_face.Edges
        # Filter for edges that are part of the hexagon (not the hole)
        # The hole is a circle, hexagon edges are straight lines.
        hex_edges = []
        for edge in face_edges:
            if isinstance(edge, Part.TopoDS.Edge):
                # Check if it's a line (hex) or circle (hole)
                # In Part, we can check the shape type or length
                # Hex edges are lines. Hole edges are circles.
                # We can check the number of vertices or the shape type.
                # Simple check: if it's a circle, skip.
                # Part.Circle vs Part.LineSegment
