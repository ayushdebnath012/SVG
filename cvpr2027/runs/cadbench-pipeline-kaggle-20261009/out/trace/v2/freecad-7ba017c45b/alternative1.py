import FreeCAD as App
import Part
import Sketcher
import os
from pathlib import Path

# Create a new document
doc = App.newDocument("HexFlangeNut")

# 1. Define Named Parameters
# These parameters will drive the geometry.
params = doc.addObject("App::FeaturePython", "Parameters")
params.ViewObject = App.ViewProvider() # Placeholder to make it a valid object
params.Type = "App::FeaturePython"

# We will store parameters in a Property (VarSet) for the Body to access, 
# or directly on the Body for simplicity in this specific script structure.
# Let's use the Body's properties directly to ensure robustness and simplicity 
# as per the "single Body" requirement.

body = doc.addObject("PartDesign::Body", "Body")
doc.recompute() # Initial recompute

# --- Parameters ---
# We set these directly on the Body object to ensure they are editable document objects
# as requested (driven by named document objects).

body.addProperty("App::PropertyLength", "overall_height", "Dimensions")
body.overall_height = 9.0

body.addProperty("App::PropertyLength", "flange_diameter", "Dimensions")
body.flange_diameter = 14.0

body.addProperty("App::PropertyLength", "flange_thickness", "Dimensions")
body.flange_thickness = 3.0

body.addProperty("App::PropertyLength", "hub_width", "Dimensions")
body.hub_width = 10.0

body.addProperty("App::PropertyLength", "bore_diameter", "Dimensions")
body.bore_diameter = 6.0

body.addProperty("App::PropertyLength", "hex_across_flats", "Dimensions")
body.hex_across_flats = 10.0

# Hex across corners is derived: width_across_flats / cos(30)
# We define it as a calculated parameter for clarity, though it's constant.
body.addProperty("App::PropertyLength", "hex_across_corners", "Dimensions")
body.hex_across_corners = 11.547005383792516 

body.addProperty("App::PropertyAngle", "hex_angle", "Dimensions")
body.hex_angle = 30.0

doc.recompute()

# --- Plane Management ---
# Ensure standard planes exist. If missing, create them.
planes = ["XY_Plane", "XZ_Plane", "YZ_Plane", "X_Axis", "Y_Axis", "Z_Axis"]
for p_name in planes:
    if not doc.exists(p_name):
        plane_obj = doc.addObject("Part::Plane", p_name)
        # Standard placements for FreeCAD default planes
        if "XY" in p_name:
            plane_obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        elif "XZ" in p_name:
            plane_obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        elif "YZ" in p_name:
            plane_obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
        elif "X_Axis" in p_name:
            plane_obj.Placement = App.Placement(App.Vector(0, 0, 0)) # Line object logic usually handled by constraints, but let's make it a Plane for compatibility if needed, 
            # Actually, PartDesign features often take Axis objects. Let's create Axis objects for the hex revolve.
            pass
        doc.recompute()

# Create Axis objects if they don't exist (needed for Revolution)
if not doc.exists("X_Axis"):
    axis = doc.addObject("Part::Line", "X_Axis")
    axis.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0)) # Just a reference point, logic in feature
    doc.recompute()

# --- Feature Construction ---

# 1. Base Sketch: Hub Hexagon + Inner Bore Circle
# Plane: XY_Plane. Origin: (0,0,0). Z up.
sketch_hub = body.newObject("Sketcher::SketchObject", "HubSketch")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch_hub.ConstraintType = "Sketcher::FlatFace" # Lift to 0 thickness initially
sketch_hub.Support = (doc.getObject("XY_Plane"), [])

# Define Hexagon Vertices
# Across flats = W. Radius of inscribed circle = W / (2 * tan(30)) = W * sqrt(3) / 3
# Radius of circumscribed circle = W / (2 * sin(30)) = W
# Wait, "width across flats" is the distance between parallel sides.
# For a regular hexagon, side length s = W / 2.
# Vertices are at distance R = W / (2 * sin(60))? No.
# Let's use coordinates. Flat to Flat distance is W.
# Distance from center to side (apothem) = W/2.
# Angle 0 is to the right (East). 
# If flat is vertical, vertices are at 0, 60, 120...
# Let's orient the hexagon with flats vertical (horizontal sides) or vertical flats?
# Standard nut orientation: flats are vertical (top/bottom) or horizontal? 
# Usually, "width across flats" is the horizontal width if the nut is sitting flat.
# Let's assume the hexagon is oriented with two vertical sides (flats at 90 and 270 deg) and vertices at 0, 60, 120...
# No, if flats are vertical, the distance between them is 2 * apothem.
# Apothem = W/2.
# Vertices angle: 0, 60, 120, 180, 240, 300.
# x = R * cos(angle), y = R * sin(angle).
# R = apothem / cos(30) = (W/2) / (sqrt(3)/2) = W / sqrt(3).
# Let's calculate R based on `hex_across_flats`.
R_hex = body.hex_across_flats / (2 * (3**0.5)) # Apothem / cos(30)

# Add Hexagon Points
for i in range(6):
    angle = i * 60.0
    x = R_hex * App.Vector(cos(angle), sin(angle), 0).X # Wait, need trig
    # Correct trig:
    rad = math.radians(angle)
    x = R_hex * math.cos(rad)
    y = R_hex * math.sin(rad)
    # Create points
    p1 = sketch_hub.addGeometry(Part.Point(App.Vector(x, y, 0)), False)
    if i > 0:
        sketch_hub.addConstraint(Sketcher.Constraint("Distance", p1-1, p1, 0, 0, R_hex), False) # Distance from origin? No, let's use Coincident for center first.
    
# Simpler Hex construction using Lines and Constraints or Points with Distance from Origin
# Let's use Points relative to origin (0,0)
hex_points = []
for i in range(6):
    rad = math.radians(60*i)
    x = R_hex * math.cos(rad)
    y = R_hex * math.sin(rad)
    p = sketch_hub.addGeometry(Part.Point(App.Vector(x, y, 0)), False)
    hex_points.append(p)

# Constraint all points to be distance R_hex from origin
for p in hex_points:
    sketch_hub.addConstraint(Sketcher.Constraint("Distance", p, 0, 0, 0, R_hex), False)

# Connect points to form hexagon
for i in range(6):
    next_i = (i + 1) % 6
    sketch_hub.addConstraint(Sketcher.Constraint("LineToNext", hex_points[i], hex_points[next_i]), False)

# 2. Bore Sketch (Inner Circle)
# We can do this on the same sketch or a second sketch. 
# The prompt asks for "exactly one solid body, built from sketches". 
# It is cleaner to do the bore on the same sketch to ensure the cut starts from the base.
# Add a circle for the bore.
circle = sketch_hub.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), body.bore_diameter / 2), False)
sketch_hub.addConstraint(Sketcher.Constraint("Coincident", circle, 0, 0, 0, 0, 0), False) # Center at origin
sketch_hub.addConstraint(Sketcher.Constraint("Radius", circle, 0, 0, 0, body.bore_diameter/2), False)

doc.recompute()

# 3. Pad: Create the main Hexagonal Body (Hub + Flange height)
# The nut is 9mm high. 
# Orientation: XY plane is horizontal. Z is up.
# Pad up 9mm.
pad = body.newObject("PartDesign::Pad", "PadMain")
pad.Profile = sketch_hub
pad.Length = body.overall_height
pad.Midplane = False
pad.Reverse = False
doc.recompute()

# 4. Flange Sketch
# We need to cut the flange. 
# The flange is an annular region extending beyond the hex.
# Thickness is 3mm. Let's place the sketch at Z = 9mm - 3mm = 6mm? 
# Or cut from the top face.
# Let's create a sketch on the top face of the Pad (Z = 9mm).
# Plane: Top face of the pad.
# But we need a named plane or support. 
# We can use a sketch attached to the face.
# However, to keep it simple and robust without complex face selection in headless:
# Let's use the Z=6 plane or simply attach to the top face of the pad.
# In PartDesign, SketchObject can attach to a Face.
# Let's find the top face of the pad.
# Or, simpler: Use a plane at Z = 6.
# Let's assume the flange is at the top.
# Sketch at Z = 6mm (3mm below top).
# Actually, let's attach to the top face of the Pad.
# We need to get the face.
# Let's create a sketch "FlangeSketch" attached to the top face of Pad.

# Get the top face of the Pad
pad_face = pad.Shape.Faces[0] if len(pad.Shape.Faces) == 1 else None
# If the pad is a simple block, it has 6 faces. Top is index 2 usually? 
# Let's rely on the sketch attachment mechanism which is safer.
# But in headless, getting the face index can be tricky if orientation varies.
# Let's assume standard orientation: Top face is the one with normal +Z.
# Let's create a sketch on the XY plane at Z=6? No, that cuts the middle.
# We want to cut from the TOP.
# Let's attach to the top face.
# We need to identify the face.
# Since the Pad is extruded from Z=0 to Z=9 along +Z, the top face has normal +Z.
# We can iterate faces.

top_face = None
for face in pad.Shape.Faces:
    if abs(face.normalAt().toTuple()[2]) > 0.99: # Normal is mostly Z
        top_face = face
        break

if not top_face:
    raise RuntimeError("Could not find top face of Pad.")

flange_sketch = body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0)) # Local placement
flange_sketch.Support = (top_face, [])
flange_sketch.ConstraintType = "Sketcher::FlatFace"

# Define Flange Geometry
# Outer Circle: flange_diameter
# Inner Hole: bore_diameter (already exists, we just need to constrain the cut)
# We are subtracting a shape.
# We draw a circle with diameter = flange_diameter.
# We also need to ensure the cut is within the bore? 
# No, the bore is already a hole in the solid. 
# The flange cut is an annular ring? 
# Wait, the description says "integrated flange". 
# The hub is hex. The flange is circular.
# So the flange extends outwards from the hex.
# The bore goes through the flange too.
# So we need to subtract a circle of diameter `flange_diameter` from the top.
# But wait, the bore is already there.
# If we subtract a circle of `flange_diameter`, it will remove material where the flange is.
# The hex part remains (since the hex is inside the flange diameter? No, hex is smaller).
# Hex width ~11.5mm. Flange dia ~14mm.
# So the flange is bigger.
# We want to remove the "solid hex" part at the top and replace it with "solid ring"?
# No, the nut is one solid.
# Construction: 
# 1. Pad Hex up 9mm. (Solid Hex)
# 2. Cut Flange: We want the top 3mm to be circular, not hexagonal?
# Or does the hex continue through the flange? "Hexagonal hub section integrated with a circular flange".
# Usually, the flange sits on the hex. The hex is the middle.
# So: Bottom 6mm = Hex. Top 3mm = Circular Ring (Flange) + Hex center?
# No, "Hexagonal hub section integrated with a circular flange".
# This implies the shape changes from Hex to Circle at the transition.
# So:
# Z=0 to Z=6: Hexagon.
# Z=6 to Z=9: Circle (Annulus? No, solid disk with hole).
# But the hex is inside the circle.
# So at Z=6, we have a Hex. We want to extend the material out to the circle?
# No, the hex is the "hub". The flange is the "circular part".
# So the top part is a Circle (minus the bore).
# The bottom part is a Hex (minus the bore).
# To achieve this:
# 1. Pad Hex up 9mm. (Now we have a Hex column).
# 2. We want to add material to make the top circular? No, PartDesign Pad adds material.
# 3. We want to cut the Hex into a Circle at the top?
# Yes. We need to subtract the corners of the hex at the top 3mm.
# So, Sketch at Z=6 (Top of the 6mm hex part).
# Draw a Circle of `flange_diameter`.
# Subtract this circle from the Hex part?
# If we subtract a circle from a hex, we get a hole in the middle? No.
# The Hex is larger than the Bore, but smaller than the Flange.
# Hex width ~11.5. Flange ~14.
# If we subtract a circle of 14 from the Hex (width 11.5), we remove the whole hex and leave a hole. That's wrong.
# We want to keep the center (the hub) and add the outer ring?
# No, the hex IS the hub.
# The geometry is: 
# Bottom 6mm: Hexagon.
# Top 3mm: Circular Flange.
# This means the Hexagon is capped by a Circle?
# No, that would mean the hex stops and a circle starts.
# If the hex stops at 6mm, and a circle starts at 6mm, we need to ADD the circle material?
# But the circle material must cover the hex center.
# So:
# 1. Pad Hex 6mm.
# 2. Pad Circle 3mm (starting from Z=6).
# 3. The Circle will cover the Hex.
# 4. The result is a Hex base with a circular cap.
# 5. Then subtract the bore through the whole thing.

# Let's refine:
# Step 1: Pad Hex 6mm (Hub).
# Step 2: Pad Circle 3mm (Flange) on top of the Hex.
# The Circle must be centered on the Hex.
# Since the Hex is smaller, the Circle will just sit on top, covering the Hex corners?
# No, the Hex is inside the Circle.
# So the union is: Hex (bottom) + Circle (top).
# This creates a step: Hex side wall, then at Z=6, it expands to Circle diameter.
# Wait, if we Pad the Circle on top, it creates a flat top of diameter 14.
# The Hex part below is diameter 11.5.
# So there is a "lip" or "shoulder" at Z=6?
# Yes, "integrated".
# So:
# 1. Pad Hex 6mm.
# 2. Pad Circle 3mm.
# 3. Subtract Bore through all.

# Let's execute this.

# 2.1. Pad Hex (Hub)
pad_hub = body.newObject("PartDesign::Pad", "PadHub")
pad_hub.Profile = sketch_hub
pad_hub.Length = body.hub_width # 10.0 mm? 
# Wait, prompt says: "hub_width = 10.0 mm". "overall_height = 9.0 mm". "flange_thickness = 3.0 mm".
# So Hub Height = 9 - 3 = 6mm? 
# The prompt says "hub_width" is 10.0mm. 
# And "overall_height" is 9
