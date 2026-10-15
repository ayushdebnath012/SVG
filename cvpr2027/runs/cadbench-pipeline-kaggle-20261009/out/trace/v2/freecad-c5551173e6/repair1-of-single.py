import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("HeadlessPin")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Body placement is handled by the document context, no need to set Placement property directly here
# unless moving the whole body in space, which is not needed for this simple part.

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Pin diameter")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Pin length")
params.addProperty("App::PropertyLength", "chamfer_length", "Dimensions", "Chamfer length")
params.addProperty("App::PropertyAngle", "chamfer_angle", "Dimensions", "Chamfer angle")

# Set default values based on requirements
params.diameter = 3.0
params.length = 6.0
params.chamfer_length = 1.0
params.chamfer_angle = 30.0

# Create the base sketch on the XY plane
# In FreeCAD 1.1, we must reference the standard planes from the document
# The standard planes are usually named "XY_Plane", "XZ_Plane", "YZ_Plane"
# We need to ensure they exist or reference them correctly.
# Standard practice in scripts: use the plane objects if they exist, otherwise create a sketch on a plane.
# However, for a robust script, we can create the sketch and attach it to the XY_Plane.

# Check if XY_Plane exists, if not, we might need to create it or assume it's there.
# In a fresh document, standard planes might not be auto-created unless the workbench does it.
# To be safe, we will try to get the XY_Plane. If it fails, we create a sketch on a generic plane or handle it.
# Actually, the most reliable way in a script without GUI is to create the sketch and set its support.
# Let's assume standard planes exist or create them if necessary.
# But the prompt implies a standard setup. Let's try to get them.

try:
    xy_plane = doc.getObject("XY_Plane")
    if not xy_plane:
        # If not found, create a simple plane object
        xy_plane = doc.addObject("Part::Plane", "XY_Plane")
        xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
        doc.recompute()
except:
    pass

sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to XY_Plane
sketch.AttachmentSupport = (xy_plane, [])
sketch.MapMode = "FlatFace"
sketch.ConstrainAuto = False
sketch.ConstrainFully = True

# Add a circle for the pin profile
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.diameter)
sketch.addGeometry(circle, False)

# Add constraints to center the circle
# Constraint: Center of circle to origin (0,0)
sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))

# Create the Pad feature to extrude the pin
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
# Use expression to drive length from parameter
pad.setExpression("Length", "Parameters.length")
pad.Type = "Solid"
pad.Reversed = False
pad.MidPlane = False

# Create a second sketch for the chamfer on the top face of the pad
# We need to reference the top face of the pad
chamfer_sketch = body.newObject("Sketcher::SketchObject", "ChamferSketch")
# Place the sketch on the top face of the pad
# The top face is the last face created by the Pad.
# We can reference the Pad object and the face index.
# Pad has faces. The top face is usually index 0 if it's a simple extrusion, but let's be careful.
# Actually, for a Pad, the "Top" face is the one opposite to the base.
# We can use the face name or index. Let's try referencing the Pad and the face.
# In PartDesign, we can reference a face by (Object, ["FaceName"]) or (Object, [Index]).
# Let's try to get the top face.
# A safer way for scripts: create the sketch on a plane parallel to the top face, then move it?
# No, PartDesign::SketchObject can attach to a face.
# Let's try referencing the Pad and the face.
# The Pad object is 'Pad'. The top face is the one with normal (0,0,1).
# We can try to find the face by name or index.
# Let's assume the top face is the first face of the pad if it's a simple extrusion?
# Actually, the Pad creates a solid. The faces are Top, Bottom, Side1, Side2...
# Let's try to reference the Pad and the face index 0 (Top).
# Or better, use the face name if available.
# Let's try to get the face by index.
# Note: Face indices can be tricky. Let's try to use the face name "Top" if possible, or index.
# In FreeCAD 1.1, referencing a face from a sketch:
# chamfer_sketch.AttachmentSupport = (pad, ["Top"]) -> This might work if the face is named "Top".
# If not, we can try index.
# Let's try to get the face by index. The top face of a Pad is usually index 0.
# But let's try to be robust.
# We can also create a plane at the top of the pad and attach to that.
# Let's try to attach to the Pad's top face directly.
# If that fails, we can create a plane.

# Let's try to get the top face of the pad.
# We can iterate through the pad's faces to find the one with normal (0,0,1).
# But in a script, we can just try to reference the face by index 0.
# Let's try:
chamfer_sketch.Placement = App.Placement(App.Vector(0, 0, params.length))
# Try to attach to the top face of the pad.
# We will use the face index 0.
chamfer_sketch.AttachmentSupport = (pad, [0])
chamfer_sketch.MapMode = "FlatFace"
chamfer_sketch.ConstrainAuto = False
chamfer_sketch.ConstrainFully = True

# Add a line for the chamfer profile
# The line starts at the center and goes out to the chamfer length
line_start = App.Vector(0, 0, 0)
line_end = App.Vector(params.chamfer_length, 0, 0)
line = Part.LineSegment(line_start, line_end)
chamfer_sketch.addGeometry(line, False)

# Add constraints for the chamfer sketch
# 1. Center the line start at the origin
chamfer_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
# 2. Fix the length of the line
chamfer_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.chamfer_length))
# 3. Fix the angle of the line (30 degrees)
chamfer_sketch.addConstraint(Sketcher.Constraint("Angle", 0, 1, params.chamfer_angle))

# Create the Chamfer feature
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
chamfer.Profile = chamfer_sketch
chamfer.Type = "ThroughAll"
# Reference the top face of the pad for the chamfer
# We can use the same face index 0
chamfer.Base = (pad, [0])
chamfer.Method = "Angle"

# Force recompute to ensure all features are calculated
doc.recompute()

# Save the document to the specified path derived from __file__
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
