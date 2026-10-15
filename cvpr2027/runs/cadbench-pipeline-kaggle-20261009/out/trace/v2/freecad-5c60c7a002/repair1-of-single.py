import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("SteppedShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# In FreeCAD 1.1, Body.Placement is a PropertyPlacement, not a constructor call
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We will store parameters in a VarSet object to keep them organized and editable
params = body.newObject("App::VarSet", "Parameters")

# Define the 11 sections with their specific diameters and lengths
# Note: FreeCAD uses mm by default.
params.addProperty("App::PropertyLength", "d1", "Dimensions", "shaft_section_1_diameter")
params.d1 = 10.0
params.addProperty("App::PropertyLength", "l1", "Dimensions", "shaft_section_1_length")
params.l1 = 20.0

params.addProperty("App::PropertyLength", "d2", "Dimensions", "shaft_section_2_diameter")
params.d2 = 15.0
params.addProperty("App::PropertyLength", "l2", "Dimensions", "shaft_section_2_length")
params.l2 = 30.0

params.addProperty("App::PropertyLength", "d3", "Dimensions", "shaft_section_3_diameter")
params.d3 = 20.0
params.addProperty("App::PropertyLength", "l3", "Dimensions", "shaft_section_3_length")
params.l3 = 40.0

params.addProperty("App::PropertyLength", "d4", "Dimensions", "shaft_section_4_diameter")
params.d4 = 40.0
params.addProperty("App::PropertyLength", "l4", "Dimensions", "shaft_section_4_length")
params.l4 = 10.0

params.addProperty("App::PropertyLength", "d5", "Dimensions", "shaft_section_5_diameter")
params.d5 = 30.0
params.addProperty("App::PropertyLength", "l5", "Dimensions", "shaft_section_5_length")
params.l5 = 20.0

params.addProperty("App::PropertyLength", "d6", "Dimensions", "shaft_section_6_diameter")
params.d6 = 25.0
params.addProperty("App::PropertyLength", "l6", "Dimensions", "shaft_section_6_length")
params.l6 = 25.0

params.addProperty("App::PropertyLength", "d7", "Dimensions", "shaft_section_7_diameter")
params.d7 = 20.0
params.addProperty("App::PropertyLength", "l7", "Dimensions", "shaft_section_7_length")
params.l7 = 20.0

params.addProperty("App::PropertyLength", "d8", "Dimensions", "shaft_section_8_diameter")
params.d8 = 50.0
params.addProperty("App::PropertyLength", "l8", "Dimensions", "shaft_section_8_length")
params.l8 = 20.0

params.addProperty("App::PropertyLength", "d9", "Dimensions", "shaft_section_9_diameter")
params.d9 = 30.0
params.addProperty("App::PropertyLength", "l9", "Dimensions", "shaft_section_9_length")
params.l9 = 10.0

params.addProperty("App::PropertyLength", "d10", "Dimensions", "shaft_section_10_diameter")
params.d10 = 50.0
params.addProperty("App::PropertyLength", "l10", "Dimensions", "shaft_section_10_length")
params.l10 = 20.0

params.addProperty("App::PropertyLength", "d11", "Dimensions", "shaft_section_11_diameter")
params.d11 = 30.0
params.addProperty("App::PropertyLength", "l11", "Dimensions", "shaft_section_11_length")
params.l11 = 10.0

# --- Base Sketch ---
# Create the first sketch on the XY plane to define the start of the shaft
sketch1 = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
# In FreeCAD 1.1, Support is a tuple of (Object, [FaceIndex])
# We use the standard XY_Plane which should exist in the document
sketch1.Support = (doc.getObject("XY_Plane"), [])
sketch1.MapMode = "FlatFace"

# Add a circle for the first section
# Center at (0,0), Radius = d1/2
r1 = params.d1 / 2.0
sketch1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r1), False)

# Add constraints to fix the circle center
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
sketch1.addConstraint(Sketcher.Constraint("Radius", 0, r1), False)

# Pad the first section
pad1 = body.newObject("PartDesign::Pad", "Pad_Section1")
pad1.Profile = sketch1
pad1.Length = params.l1
pad1.Type = "Solid"
pad1.MidPlane = False
pad1.Reversed = False

# --- Loop for remaining sections ---
# We need to create sketches for sections 2 through 11.
# Each sketch will be placed on the face of the previous pad.
# We track the current Z position to ensure sketches are on the correct face.
current_z = params.l1
current_face = pad1.Placement.Base.Z # Actually, we need the face object. 
# In PartDesign, it's easier to reference the last created feature's face or use a loop 
# that creates a sketch on the top face of the previous pad.

# To make this robust in a script without GUI interaction, we will:
# 1. Get the top face of the previous pad.
# 2. Create a sketch on that face.
# 3. Pad it.
# 4. Update current_z.

# We store the last pad object to get its top face
last_pad = pad1

for i in range(2, 12):
    # Get the top face of the previous pad
    # The top face is usually the last face in the pad's TopoShape, but accessing via object is safer
    # We assume the pad is solid and convex enough that the top face is accessible.
    # In FreeCAD 1.1, we can get the face from the pad's shape.
    shape = last_pad.Shape
    # Find the face with the maximum Z coordinate (assuming we build upwards)
    faces = shape.Faces
    top_face = None
    max_z = -1e9
    
    for f in faces:
        # Get the center of the face to determine Z
        # Or simply check the normal and position. 
        # Since we build along Z, the face with the highest Z coordinate is the top.
        # We can approximate by checking the bounding box or just iterating.
        # A more reliable way in script: The last face added to a Pad is often the top, 
        # but let's be explicit.
        # We'll use the face with the highest Z coordinate of its center.
        center = f.Center
        if center.Z > max_z:
            max_z = center.Z
            top_face = f

    if top_face is None:
        raise Exception("Could not find top face on previous pad.")

    # Create new sketch on the top face
    sketch_name = f"Sketch_Section{i}"
    sketch = body.newObject("Sketcher::SketchObject", sketch_name)
    sketch.Placement = App.Placement(App.Vector(0, 0, 0)) # Local placement
    sketch.Support = (top_face, [])
    sketch.MapMode = "FlatFace"

    # Add circle for current section
    r = params[f"d{i}"] / 2.0
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    
    # Constraints
    sketch.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    sketch.addConstraint(Sketcher.Constraint("Radius", 0, r), False)

    # Pad the section
    pad_name = f"Pad_Section{i}"
    pad = body.newObject("PartDesign::Pad", pad_name)
    pad.Profile = sketch
    pad.Length = params[f"l{i}"]
    pad.Type = "Solid"
    pad.MidPlane = False
    pad.Reversed = False

    # Update references for next iteration
    last_pad = pad
    current_z += params[f"l{i}"]

# --- Finalize ---
doc.recompute()

# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Save the document
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
