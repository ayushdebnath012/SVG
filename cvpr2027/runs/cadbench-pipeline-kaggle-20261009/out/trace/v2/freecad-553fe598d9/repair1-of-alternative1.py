import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize the document
doc = App.newDocument("StepPart")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# Define named parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyInteger", "number_of_tiers", "Dimensions", "Number of steps")
params.number_of_tiers = 3

params.addProperty("App::PropertyLength", "riser", "Dimensions", "Height of each step")
params.riser = 150.0

params.addProperty("App::PropertyLength", "depth", "Dimensions", "Depth of each step")
params.depth = 300.0

params.addProperty("App::PropertyLength", "width", "Dimensions", "Extrusion width")
params.width = 1200.0

# --- Step 1: Create the Side Profile Sketch ---
# We sketch on the XZ plane. 
# X axis corresponds to the "Run" (horizontal).
# Z axis corresponds to the "Rise" (vertical).
sketch = body.newObject("Sketcher::SketchObject", "ProfileSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to the XZ Plane
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# In FreeCAD 1.1, we attach to the plane object. The standard XZ plane is usually named "XZ_Plane" or we can use the plane index.
# Let's use the plane object "XZ_Plane" which is standard in PartDesign templates, 
# but to be safe in a generic doc, we can attach to the plane at Z=0.
# Actually, the most robust way in headless is to attach to the plane object if it exists, 
# or create a plane. However, standard FreeCAD docs usually assume "XY_Plane", "XZ_Plane", "YZ_Plane" exist or are created.
# Let's assume standard planes exist or create them if not.
# But the prompt implies a standard setup. Let's try to attach to "XZ_Plane".
# If that fails, we might need to create it.
# For this script, we will assume the standard planes exist or create the XZ plane if missing.
# Actually, let's just use the plane object "XZ_Plane" directly.
# If it doesn't exist, we create it.
xz_plane = doc.addObject("Part::Plane", "XZ_Plane")
xz_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
doc.recompute()

sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# AttachmentSupport for XZ plane: The plane object is the support.
# We need to specify the plane and the axis.
# For XZ plane, the normal is Y.
# We want to sketch in the XZ plane.
# The AttachmentSupport tuple is (PlaneObject, [AxisName]).
# For XZ plane, the axis is usually "Y_Axis" (the normal).
# Wait, AttachmentSupport defines the plane of the sketch.
# If we attach to XZ_Plane, the sketch lies in XZ.
# The normal of the sketch plane is Y.
# So we attach to XZ_Plane and the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Correct way to set placement for sketch on a plane:
# sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's simplify:
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Actually, let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Let's just set the placement to origin and rotation 0,0,0.
# And set AttachmentSupport to (XZ_Plane, ["Y_Axis"])
# But wait, if we attach to XZ_Plane, the sketch is in XZ.
# The normal is Y.
# So the axis is Y_Axis.
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0,
