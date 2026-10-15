import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize the document
doc = App.newDocument("SteppedShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Define parameters for each shaft section
# Format: Name -> [Diameter, Length]
sections_params = {
    "Diam_1": 10.0, "Len_1": 20.0,
    "Diam_2": 15.0, "Len_2": 30.0,
    "Diam_3": 20.0, "Len_3": 40.0,
    "Diam_4": 40.0, "Len_4": 10.0,
    "Diam_5": 30.0, "Len_5": 20.0,
    "Diam_6": 25.0, "Len_6": 25.0,
    "Diam_7": 20.0, "Len_7": 20.0,
    "Diam_8": 50.0, "Len_8": 20.0,
    "Diam_9": 30.0, "Len_9": 10.0,
    "Diam_10": 50.0, "Len_10": 20.0,
    "Diam_11": 30.0, "Len_11": 10.0,
}

# Helper to add a parameter to the Body
def add_param(name, value, unit="mm"):
    param_obj = body.newObject("App::Parameter", name)
    param_obj.BaseValue = f"{value}{unit}"
    param_obj.Type = "Length"
    return name

# Register all parameters
for key in sections_params:
    if key.startswith("Diam"):
        add_param(key, sections_params[key])
    elif key.startswith("Len"):
        add_param(key, sections_params[key])

# Create the initial sketch on XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
sketch.Support = [(doc.getObject("XY_Plane"), ["", "", ""])], []
sketch.MapMode = "FlatFace"
sketch.Tolerance = 0.001
sketch.ConstraintTolerance = 0.001
sketch.Closed = True

# Add circle for the first section (we will extrude this and then pad others)
# Diameter 10mm -> Radius 5mm
sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 5.0), True)
sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, 5.0))

# Create the first pad
pad1 = body.newObject("PartDesign::Pad", "Pad_Section_1")
pad1.Profile = sketch
pad1.Length = sections_params["Len_1"]
pad1.Type = "Solid"
pad1.Direction = (1, 0, 0) # X direction

# Now we need to build the rest of the shaft.
# Strategy: Create a sketch at the end of the previous pad, define the new diameter, 
# then pad it in the same direction.
# Since PartDesign pads always start from the "Base" (or previous feature if chained),
# and we are on a single axis, we can simply create new sketches offset along Z (the axis of the shaft).
# Wait, the first pad was in X direction. The shaft grows along X.
# So the next sketch should be placed at Z=sections_params["Len_1"]?
# No, the sketch is on a plane. The Pad extrudes from the sketch.
# Let's restart the logic for clarity.
# 1. Sketch on XY plane (Z=0). Draw circle. Pad in +X direction by Len_1.
# 2. We need a new sketch on the plane X=Len_1 (YZ plane) or XY plane at Z=Len_1?
#    If we pad in X, the face is at X=Len_1. The normal is X.
#    To continue the shaft in X, the next sketch should be on the plane X=Len_1 (YZ plane).
#    But Sketcher::SketchObject needs a flat face. The face at X=Len_1 is flat.
#    We can attach the sketch to that face.

# However, creating sketches on dynamic faces (YZ plane at X=Len_1) requires getting the plane object or creating a custom plane.
# Easier approach: Keep all sketches on XY plane (Z=constant).
# But the shaft is a cylinder. If we pad in X, the next segment must start at the end of the previous segment.
# If we draw the next sketch on XY plane at Z = current_Z, and pad in X, it will overlap or be disconnected if not careful.
# Actually, the standard way to make a stepped shaft in one body is:
# Sketch 1 on XY (Z=0). Pad X by Len_1.
# Sketch 2 on XY (Z=Len_1). Pad X by Len_2? 
#   If we pad X from Z=Len_1, it starts at X=-inf? No, Pad has a profile.
#   If the profile is a circle at Z=Len_1, and we pad in X, it creates a cylinder starting at the sketch plane? 
#   No, Pad extrudes along the normal of the sketch? No, Pad has a direction.
#   If we set Direction = (1,0,0), it extrudes in +X.
#   If we have a sketch at Z=Len_1, and we pad in +X, it creates a cylinder from X = -infinity? No, from the sketch face?
#   PartDesign Pad works on the Sketch face. If the sketch is on XY plane, the face is at Z=Len_1.
#   The Pad extrudes perpendicular to the face? No, Pad has a direction vector.
#   If direction is (1,0,0), it extrudes along X.
#   The "Base" of the pad is the sketch face.
#   If we want a continuous shaft, we usually chain them.
#   Let's try a different approach: Revolution.
#   Create ONE sketch on XY plane with the profile of the entire shaft (a stepped line from -Radius to Radius?).
#   Then Revolution around Z axis.
#   This creates the solid in one go. But the prompt asks for "sequential shaft_section_1 ... shaft_section_11".
#   This implies separate features for each section to maintain editability per section length/diameter.
#   
#   Revised Strategy:
#   1. Sketch on XY (Z=0). Circle D1. Pad in +X by Len_1.
#   2. We need to attach the next sketch to the face created by Pad_1.
#      The face is a circle at X=Len_1. Its normal is (1,0,0).
#      We create a sketch attached to this face. 
#      Draw a circle D2.
#      Pad in the same direction (+X) by Len_2.
#   3. Repeat for all 11 sections.
#   This requires dynamically getting the last feature or creating planes.
#   Since we know the order, we can create a list of features.

# To make this robust in a script without complex geometry queries for the last face:
# We can create the sketch on a specific plane that moves.
# But simpler: Create the sketch on the XY plane, but offset the sketch in Z? No.
# Let's stick to: Sketch on the face of the previous pad.
# How to attach sketch to a face programmatically?
# sketch.Support = [(last_pad, ["Face1", ...])]
# We need to know which face is the "end" face. For a pad in +X, the end face is the one with max X.
# We can assume the sketch is always attached to the last face of the previous feature.

# Let's write the loop.
current_face_index = 0 # Index in the last feature's list of faces
current_feature = pad1

# We need to store the last feature to attach the next sketch.
# Actually, we can just create the sketch on the XY plane but shifted in X?
# If we shift the sketch in X to match the end of the previous pad, the Pad direction (1,0,0) 
# will still extrude in +X, creating the next segment.
# BUT: The sketch plane is XY. The normal is Z. The Pad direction is X.
# This works perfectly. The Pad creates a cylinder extending in X from the sketch plane (Z).
# So:
# Sketch 1 at Z=0. Pad X -> Segment 1 (X: 0 to Len_1). End at X=Len_1.
# Sketch 2 at Z=Len_1? No. The sketch is on XY plane.
# If we put Sketch 2 at Z=Len_1, it is floating in space.
# The Pad will create a cylinder from X=0 to X=Len_2 (relative to sketch).
# This does not connect to the previous segment.
# 
# Correction: The sketch must be located at the END of the previous segment.
# If the previous segment ends at X=Len_1, the new sketch must be at X=Len_1.
# But Sketcher::SketchObject works on a plane.
# If we use the XY plane, we can only vary Z.
# If we use the XZ plane, we can vary Y.
# We need a plane at X=Len_1 that is perpendicular to the shaft axis (X).
# That plane is the YZ plane at X=Len_1.
# FreeCAD has "Plane" objects. We can create a plane at X=Len_1, YZ orientation.
# Then attach sketch to that plane.
# Then Pad in X direction.

# Let's implement this "Dynamic Plane" strategy.

def create_sketch_and_pad(prev_feature, diam_mm, len_mm, dir_vec, offset_vec):
    """
    Creates a sketch on a plane parallel to the previous sketch's normal? 
    No, we need a plane perpendicular to the shaft axis (X).
    We will create a new Plane object for each section.
    """
    # Get the center of the previous feature to determine position
    # Actually, for a shaft along X, the previous pad ended at X = sum of lengths.
    # We can track the current X position.
    pass

# Let's simplify. We will create a "CurrentPosition" variable.
current_x = 0.0

# List of sections data
sections = [
    (10.0, 20.0), (15.0, 30.0), (20.0, 40.0), (40.0, 10.0),
    (30.0, 20.0), (25.0, 25.0), (20.0, 20.0), (50.0, 20.0),
    (30.0, 10.0), (50.0, 20.0), (30.0, 10.0)
]

# We already created Pad_Section_1 manually in the thought process above.
# Let's restart the script logic cleanly in the final block.
# We need to create a Plane for each section end.

# Re-initialize logic inside the script
# ... (See final code)

# Let's refine the loop logic:
# 1. Create Plane at current_x, YZ orientation.
# 2. Create Sketch on that Plane.
# 3. Add Circle with diameter = D.
# 4. Create Pad, Length = L, Direction = (1,0,0).
# 5. Update current_x += L.
# 6. Repeat.

# Wait, the first section:
# Plane at X=0, YZ. Sketch Circle D1. Pad X by L1.
# Result: Cylinder from X=0 to X=L1.
# Next section:
# Plane at X=L1, YZ. Sketch Circle D2. Pad X by L2.
# Result: Cylinder from X=L1 to X=L1+L2.
# This works.

# Implementation details:
# Plane: Plane.X = current_x. Plane = "YZ".
# Sketch: Support = [Plane, ["", "", ""]]
# Pad: Profile = Sketch. Direction = (1,0,0).

# Let's write the code.

doc = App.newDocument("SteppedShaft")

# Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Parameters
for i in range(1, 12):
    d = f"Diam_{i}"
    l = f"Len_{i}"
    val_d = sections[i-1][0]
    val_l = sections[i-1][1]
    
    # Create parameter objects
    p_d = body.newObject("App::Parameter", d)
    p_d.BaseValue = f"{val_d}mm"
    p_d.Type = "Length"
    
    p_l = body.newObject("App::Parameter", l)
    p_l.BaseValue = f"{val_l}mm"
    p_l.Type = "Length"

# Current position along X axis
current_x = 0.0

# Create the shaft sections
for i, (d, l) in enumerate(sections):
    d_name = f"Diam_{i+1}"
    l_name = f"Len_{i+1}"
    
    # Create a plane at current_x, oriented YZ (normal X)
    # Plane object
    plane = body.newObject("Part::Plane", f"Plane_Section_{i+1}")
    plane.Placement = App.Placement(App.Vector(current_x, 0, 0))
    # Plane orientation: We want the plane to be YZ.
    # App::Plane has properties: Position, Normal, BaseObject (optional).
    # In FreeCAD 1.1, Part::Plane is usually defined by a base object or explicit properties?
    # Actually, Part::Plane is a specific object type.
    # Let's use the built-in planes if possible, or create a custom one.
    # Creating a custom plane in FreeCAD 1.1:
    # plane = body.newObject("Part::Plane", name)
    # plane.Placement = ...
    # plane.BaseObject = ... ?
    # Alternatively, create a sketcher object on a specific plane?
    # The cleanest way for dynamic planes in FreeCAD 1.1 without complex geometry:
    # Use a sketch on a plane defined by 3 points or use the "XY_Plane" and offset?
    # No, we need a plane perpendicular to X.
    # We can create a sketch on XY, then pad in X? No, that's the same issue.
    # Let's create a "Plane" object properly.
    # In FreeCAD 1.1, Part::Plane inherits from Part::Feature.
    # To create a plane at X=10, YZ:
    # We can create a box of small size and take a face? No.
    # We can use the "Plane" object which is a primitive.
    # plane = App.getDocument("...").addObject("Part::Plane", "P1")
    # plane.Placement = App.Placement(App.Vector(10,0,0))
    # plane.BaseObject = ... ?
    # Actually, there is a simpler way: Use a sketch on the XY plane, but shift the sketch in X?
    # If we shift the sketch in X, the Pad direction (1,0,0) will still work?
    # If Sketch is at X=10, Z=0 (on XY plane). Pad in X.
    # The Pad extrudes from the Sketch face (which is at Z=0).
    # It creates a cylinder from X=10 to X=10+L? 
    # NO. The Pad extrudes perpendicular to the sketch plane? No, along the direction vector.
    # If direction is (1,0,0), it extrudes along X.
    # The "Base" of the pad is the Sketch face.
    # If the sketch is on XY plane, the face is at Z=0.
    # The Pad creates a solid that is the swept volume of the profile along the direction.
    # If the profile is at Z=0, and we sweep along X, we get a cylinder from X=-inf to +inf?
    # No, the Pad has a length. It starts from the sketch face?
    # No, the Pad starts from the sketch face ONLY if the sketch is on a face of the body.
    # If the sketch is on a free plane (XY), the Pad creates a cylinder starting at the center of the sketch?
    # Or from the sketch face?
    # Standard behavior: Pad creates a solid by sweeping the profile along the direction.
    # The "start" of the sweep is the plane of the sketch.
    # So if Sketch is on XY at Z=0. Pad X by L.
    # It creates a cylinder from X = (Sketch center X) - L/2? Or X = Sketch center X?
    # If we set the sketch center at X=current_x.
    # And Pad Length = L.
    # Does it go from current_x to current_x + L?
    # Or from current_x - L/2 to current_x + L/2?
    # By default, Pad starts at the sketch face? No, Pad on a sketch creates a solid from the sketch face in the direction.
