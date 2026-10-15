import FreeCAD as App
import Part
from pathlib import Path

# Derive paths from __file__
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Create a new document
doc = App.newDocument("FrustumPart")

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")
# Body placement is handled by the feature tree, default is (0,0,0)

# Create a VarSet to hold parameters
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "top_diameter", "Dimensions", "Top diameter of the frustum")
params.addProperty("App::PropertyLength", "bottom_diameter", "Dimensions", "Bottom diameter of the frustum")
params.addProperty("App::PropertyLength", "height", "Dimensions", "Height of the frustum")

# Set default values
params.top_diameter = 15.0
params.bottom_diameter = 25.0
params.height = 30.0

# Create the profile sketch on XZ plane
# We need to reference the XZ_Plane which is usually available in the document
# If not, we can create a sketch on the default XY plane and rotate it, 
# but standard practice is to use the plane. Let's try to get XZ_Plane.
xz_plane = None
for obj in doc.Objects:
    if obj.Label == "XZ_Plane":
        xz_plane = obj
        break

if xz_plane is None:
    # Fallback: Create a sketch on XY plane and rotate the profile later? 
    # No, PartDesign::Revolution needs a ReferenceAxis. 
    # Let's create the sketch on XY plane and define the profile there, 
    # then revolve around Z axis. The Z axis is the same in XY plane context.
    # Actually, if XZ_Plane doesn't exist, we can use XY_Plane and the Z_Axis.
    # Let's assume standard planes exist or create a sketch on XY_Plane.
    xy_plane = None
    for obj in doc.Objects:
        if obj.Label == "XY_Plane":
            xy_plane = obj
            break
    
    if xy_plane is None:
        # If no planes exist, we can't easily attach. 
        # However, FreeCAD usually initializes XY_Plane, XZ_Plane, YZ_Plane.
        # Let's assume XY_Plane exists.
        pass

    sketch = body.newObject("Sketcher::SketchObject", "ProfileSketch")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.AttachmentSupport = (xy_plane, [])
    sketch.MapMode = "FlatFace"
    sketch.ConstrainAuto = True
    sketch.ConstrainFully = True
else:
    sketch = body.newObject("Sketcher::SketchObject", "ProfileSketch")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.AttachmentSupport = (xz_plane, [])
    sketch.MapMode = "FlatFace"
    sketch.ConstrainAuto = True
    sketch.ConstrainFully = True

# Helper to get expression string
def get_expr(val):
    return f"Parameters.{val}"

# Add geometry to form the trapezoid profile
# We will define the profile on the plane. 
# If on XZ plane: X is horizontal, Z is vertical.
# If on XY plane: X is horizontal, Y is vertical.
# Let's assume we are on a plane where one axis is horizontal and one is vertical.
# We will construct lines based on the plane's orientation.
# Since we don't know the exact plane orientation without checking, 
# we will use the standard approach: Sketch on XY plane, X horizontal, Y vertical.
# Then revolve around Z axis.

# Re-creating sketch logic to be safe on XY plane if XZ not found, or just use XY.
# Let's force XY plane usage for robustness if XZ is missing, or just use the found one.
# Actually, let's just use the found plane. If it's XZ, X is horiz, Z is vert.
# If it's XY, X is horiz, Y is vert.
# The revolution axis will be the vertical axis of that plane.

# Let's rebuild the sketch logic to be generic:
# We need 4 points.
# Let's assume the plane has a "Horizontal" axis and a "Vertical" axis.
# We will use the plane's local coordinates.

# Clear previous geometry if any (though new object)
sketch.Geometry = []

# Define points relative to the sketch's local coordinate system
# Bottom Left, Bottom Right, Top Right, Top Left
# We need to know which axis is which.
# Let's try to detect or just assume standard: 
# If AttachmentSupport is XY_Plane: X=Horiz, Y=Vert.
# If AttachmentSupport is XZ_Plane: X=Horiz, Z=Vert.

support = sketch.AttachmentSupport[0]
# Check if the support is XZ_Plane
is_xz = False
if hasattr(support, "Type") and "XZ" in str(support.Type):
    is_xz = True

# Define vertices
# We will use Part.LineSegment
# Vertices:
# 1: (-bottom/2, 0)
# 2: (bottom/2, 0)
# 3: (top/2, height)
# 4: (-top/2, height)

# If XZ plane: X is first coord, Z is second.
# If XY plane: X is first coord, Y is second.
# In both cases, the first coord is horizontal, second is vertical.

b_d = params.bottom_diameter
t_d = params.top_diameter
h = params.height

# Line 1: Bottom
p1 = App.Vector(-b_d / 2, 0, 0)
p2 = App.Vector(b_d / 2, 0, 0)
l1 = Part.LineSegment(p1, p2)
sketch.addGeometry(l1, False)

# Line 2: Right Slant
p3 = App.Vector(t_d / 2, h, 0)
l2 = Part.LineSegment(p2, p3)
sketch.addGeometry(l2, False)

# Line 3: Top
p4 = App.Vector(-t_d / 2, h, 0)
l3 = Part.LineSegment(p3, p4)
sketch.addGeometry(l3, False)

# Line 4: Left Slant
l4 = Part.LineSegment(p4, p1)
sketch.addGeometry(l4, False)

# Constraints
# 1. Horizontal lines (Bottom and Top)
# We need to identify the line indices. 
# Index 0: l1, 1: l2, 2: l3, 3: l4
# l1 is horizontal. l3 is horizontal.
sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
sketch.addConstraint(Sketcher.Constraint("Horizontal", 2))

# 2. Vertical alignment (Symmetry)
# Symmetry around the vertical axis (Y or Z)
# We can constrain the midpoint of the bottom line to be on the vertical axis.
# Or use symmetry constraint between left and right halves.
# Let's use symmetry constraint for the whole shape.
# Symmetry axis is the vertical axis.
# We need to define the axis. 
# If XY plane, axis is Y. If XZ plane, axis is Z.
# Sketcher Constraint "Symmetry" takes: (Element, Axis, Element, Axis, ...)
# Actually, simpler: Constrain the center of the bottom line to be on the vertical axis.
# But we don't have a point object.
# Let's use the "Symmetry" constraint on the lines.
# Symmetry axis: The vertical axis of the plane.
# We can specify the axis by its direction in the sketcher constraint.
# However, a robust way is to constrain the midpoint of the bottom line to be on the vertical axis.
# Let's create a point at the midpoint of the bottom line and constrain it.
# Or, simpler: Constrain the distance of the left and right endpoints from the vertical axis to be equal.
# But we don't have the axis object in the sketcher constraint easily without knowing the plane.
# Alternative: Use "Point" constraint to force the bottom line to be centered?
# No, let's use the "Symmetry" constraint properly.
# Syntax: Sketcher.Constraint("Symmetry", <Element>, <Axis>, <Element>, <Axis>, ...)
# If we assume the sketch is on a standard plane, the vertical axis is either Y or Z.
# Let's try to constrain the midpoint of the bottom line (Line 0) to be on the vertical axis.
# We can't easily do that without a point.
# Let's use the "Symmetry" constraint on the two slanted lines (1 and 3) with respect to the vertical axis.
# But we need to define the axis.
# Let's try a different approach: Constrain the bottom line to be centered on the vertical axis.
# We can do this by constraining the midpoint of the bottom line to be on the vertical axis.
# Since we can't create a point easily in the sketcher geometry list without adding it,
# let's rely on the "Symmetry" constraint.
# We will assume the vertical axis is the second axis of the plane.
# If XY plane, axis is Y (index 1). If XZ plane, axis is Z (index 1 in local coords).
# The constraint syntax for Symmetry is: (Element, Axis, Element, Axis, ...)
# We want to reflect Line 1 (Right Slant) across the vertical axis to match Line 3 (Left Slant).
# But we need to specify the axis.
# Let's try: Sketcher.Constraint("Symmetry", 1, 1, 3, 1) -> Symmetry of Line 1 around Axis 1 (Y) with Line 3 around Axis 1.
# This assumes Axis 1 is the vertical axis.
# If the plane is XZ, Axis 1 is Z. If XY, Axis 1 is Y. This works!
sketch.addConstraint(Sketcher.Constraint("Symmetry", 1, 1, 3, 1))

# 3. Link dimensions
# Bottom width
sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, get_expr("bottom_diameter")))
# Top width
sketch.addConstraint(Sketcher.Constraint("Length", 2, 3, get_expr("top_diameter")))
# Height (Distance between bottom line and top line along the vertical axis)
# We can use "DistanceX" if the vertical axis is the second axis (index 1).
# Distance between Line 0 and Line 2 along Axis 1.
sketch.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, get_expr("height")))

# Create the Revolution feature
# Reference Axis: The vertical axis of the plane.
# If XY plane, it's Y_Axis. If XZ plane, it's Z_Axis.
# We can find the axis object.
ref_axis = None
if is_xz:
    for obj in doc.Objects:
        if obj.Label == "Z_Axis":
            ref_axis = obj
            break
else:
    for obj in doc.Objects:
        if obj.Label == "Y_Axis":
            ref_axis = obj
            break

if ref_axis is None:
    # Fallback: Try to find any axis
    for obj in doc.Objects:
        if obj.Label.endswith("_Axis"):
            ref_axis = obj
            break

rev = body.newObject("PartDesign::Revolution", "Revolution")
rev.Profile = sketch
rev.ReferenceAxis = (ref_axis, [])
rev.Angle = 360.0
rev.Tangent = False
rev.Reverse = False

# Recompute to generate the solid
doc.recompute()

# Save the file
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
