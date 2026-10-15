import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Derived from the prompt requirements
PARAMS = {
    "smooth_shaft_diameter": 50.0,
    "smooth_shaft_length": 80.0,
    "keyway_width": 8.0,
    "keyway_depth": 3.0,
    "keyway_height": 50.0,
    "num_keyway": 2,
}

# Output path derived from __file__
script_path = Path(__file__).resolve()
doc_path = script_path.parent / f"{script_path.stem}.FCStd"

# -----------------------------------------------------------------------------
# Document Setup
# -----------------------------------------------------------------------------
# Create a new document
doc = App.newDocument("SmoothShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Add a parameter set to drive dimensions
params_obj = body.newObject("App::VarSet", "Parameters")

# Map prompt parameter names to internal object property names
# We use 'Dimensions' as the group for all parameters
d = params_obj
d.addProperty("App::PropertyLength", "smooth_shaft_diameter", "Dimensions", "overall diameter")
d.smooth_shaft_diameter = PARAMS["smooth_shaft_diameter"]

d.addProperty("App::PropertyLength", "smooth_shaft_length", "Dimensions", "overall length")
d.smooth_shaft_length = PARAMS["smooth_shaft_length"]

d.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "keyway width")
d.keyway_width = PARAMS["keyway_width"]

d.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "keyway depth")
d.keyway_depth = PARAMS["keyway_depth"]

d.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "keyway height")
d.keyway_height = PARAMS["keyway_height"]

d.addProperty("App::PropertyInteger", "num_keyway", "Dimensions", "number of keyways")
d.num_keyway = PARAMS["num_keyway"]

# -----------------------------------------------------------------------------
# Feature Construction
# -----------------------------------------------------------------------------

# 1. Main Shaft Body (Pad)
# Sketch on XY plane (Z=0)
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftSketch")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.Support = (App.getDocument("FreeCAD").getObject("XY_Plane"), [""]) # Using default XY_Plane if available, otherwise fallback
# Ensure we use a plane relative to the body if standard planes aren't guaranteed in headless
# For robustness in headless, we often use the body's attached plane or create a generic one.
# However, standard FreeCAD templates usually have XY_Plane, XZ_Plane, YZ_Plane in the main doc.
# If strict headless without template, we might need to create a plane. 
# Assuming standard FreeCAD installation includes standard planes or we create one.
# Let's try to attach to the standard XY_Plane first. If it fails, we create a plane attached to the body.

try:
    support_plane = App.getDocument("FreeCAD").getObject("XY_Plane")
except KeyError:
    # Create a local plane if standard ones are missing
    support_plane = doc.addObject("PartDesign::Plane", "LocalPlane")
    support_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
    support_plane.Parent = body
    support_plane.Type = "Face"
    support_plane.Placement = App.Placement(App.Vector(0,0,0))

sketch_shaft.Support = (support_plane, [""])
sketch_shaft.ConstrainToOtherObjects = False
sketch_shaft.MapMode = "FlatFace"
sketch_shaft.Tangent = False
sketch_shaft.ConstrainToAxis = False
sketch_shaft.ConstrainToFace = False

# Draw the main shaft profile (Rectangle centered at 0,0)
# Width = diameter, Height = diameter
# We use named expressions or direct values. Direct values for simplicity in this specific shape,
# but let's drive the radius for clarity.
diameter = PARAMS["smooth_shaft_diameter"]
radius = diameter / 2.0

# Line 1: Bottom (-d/2, 0) to (d/2, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-radius, 0, 0), App.Vector(radius, 0, 0)), False)
# Line 2: Right (d/2, 0) to (d/2, d/2)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(radius, 0, 0), App.Vector(radius, radius, 0)), False)
# Line 3: Top (d/2, d/2) to (-d/2, d/2)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(radius, radius, 0), App.Vector(-radius, radius, 0)), False)
# Line 4: Left (-d/2, d/2) to (-d/2, 0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-radius, radius, 0), App.Vector(-radius, 0, 0)), False)

# Constraints: Horizontal, Vertical, Closed, Dimensions
# Using a simple closed constraint loop and horizontal/vertical
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch_shaft.addConstraint(Sketcher.Constraint("Perpendicular", 1, 0, 2, 1)) # Angle between 1 and 2
sketch_shaft.addConstraint(Sketcher.Constraint("Perpendicular", 2, 0, 3, 1))
sketch_shaft.addConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1))

# Dimension the width (distance from 0,0 to right edge)
sketch_shaft.addConstraint(Sketcher.Constraint("Length", 0, 2, 0, 1, radius))

# Create the Pad feature
pad_shaft = body.newObject("PartDesign::Pad", "ShaftPad")
pad_shaft.Profile = sketch_shaft
# Length driven by parameter
pad_shaft.setExpression("Length", "Parameters.smooth_shaft_length")
pad_shaft.Type = "Blind"
pad_shaft.Midplane = False
pad_shaft.Reverse = False
pad_shaft.Precision = 1e-06

# 2. Keyway Features (Pocket)
# We need to create keyways based on 'num_keyway'.
# Since PartDesign features can be patterned, we will create one keyway pocket 
# and then pattern it.

# Create a sketch for the keyway
# Orientation: The shaft is along Z. Keyways are usually milled along the length.
# Let's place the sketch on the XZ plane (Y=0).
try:
    support_plane_xz = App.getDocument("FreeCAD").getObject("XZ_Plane")
except KeyError:
    support_plane_xz = doc.addObject("PartDesign::Plane", "LocalPlaneXZ")
    support_plane_xz.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0))
    support_plane_xz.Parent = body
    support_plane_xz.Type = "Face"

sketch_keyway = body.newObject("Sketcher::SketchObject", "KeywaySketch")
sketch_keyway.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_keyway.Support = (support_plane_xz, [""])
sketch_keyway.MapMode = "FlatFace"

# Keyway Geometry:
# A keyway is a rectangular cut. 
# On the XZ plane (Y=0), the cut goes from Y = -depth to Y = +depth? 
# No, a keyway is a slot on the side. 
# If the shaft is along Z, the keyway is a groove along Z.
# Cross section in XZ plane: A rectangle defined by width (X) and depth (Y).
# Center at (0,0) in XZ plane.
# X range: [-width/2, width/2]
# Y range: [-depth, 0] (assuming it's on one side) or [-depth/2, depth/2]?
# Standard keyway is usually symmetric or offset. Let's do symmetric for simplicity: 
# Y from -depth/2 to depth/2.

key_w = PARAMS["keyway_width"] / 2.0
key_d = PARAMS["keyway_depth"] / 2.0

# Points for the rectangle in XZ plane
p1 = App.Vector(-key_w, -key_d, 0)
p2 = App.Vector(key_w, -key_d, 0)
p3 = App.Vector(key_w, key_d, 0)
p4 = App.Vector(-key_w, key_d, 0)

sketch_keyway.addGeometry(Part.LineSegment(p1, p2), False)
sketch_keyway.addGeometry(Part.LineSegment(p2, p3), False)
sketch_keyway.addGeometry(Part.LineSegment(p3, p4), False)
sketch_keyway.addGeometry(Part.LineSegment(p4, p1), False)

# Constraints
sketch_keyway.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
sketch_keyway.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Perpendicular", 1, 0, 2, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Perpendicular", 2, 0, 3, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 4, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Perpendicular", 4, 0, 0, 1))

sketch_keyway.addConstraint(Sketcher.Constraint("Length", 0, 2, 0, 1, key_w))
sketch_keyway.addConstraint(Sketcher.Constraint("Length", 0, 1, 0, 3, key_d))
sketch_keyway.addConstraint(Sketcher.Constraint("Center", 0, 1)) # Center on origin

# Create the Pocket feature for ONE keyway
# The pocket subtracts volume.
pocket_keyway = body.newObject("PartDesign::Pocket", "SingleKeyway")
pocket_keyway.Profile = sketch_keyway
# Reference axis for the pocket operation? 
# Pocket subtracts the area enclosed by the profile along the normal of the plane? 
# Wait, Pocket in PartDesign subtracts the profile along the Z axis (normal of XY plane) by default?
# NO. Pocket subtracts along the Z axis relative to the sketch plane.
# Our sketch is on XZ plane. Normal is Y axis.
# So a standard Pocket on XZ plane would cut a hole through Y? That's not a keyway along Z.
# We need a REVOLVE or a specific Pocket configuration? 
# Actually, the standard Pocket subtracts along the Z-axis of the sketcher workspace, 
# but if the sketch is on XZ, the normal is Y.
# To cut a groove along Z (length of shaft), we should use a REVOLVE? 
# No, a groove along Z is a simple extrusion in the negative Z direction? 
# No, the shaft is along Z. The groove is along Z. 
# So the groove is parallel to the Z axis.
# If we sketch on XZ, the profile is the cross-section of the groove.
# We need to extrude this profile along the Z axis (which is the normal of the XZ plane? No, Z is in the plane).
# The normal of XZ is Y. Extruding along Y creates a hole through the diameter.
# We need to extrude along Z. 
# In PartDesign, there is no "Extrude along arbitrary vector" for pockets directly unless we use a custom feature or 
# we sketch on the XY plane (normal Z) and extrude along Z.
# Let's re-orient the keyway sketch to the XY plane (normal Z).
# If sketch is on XY, profile is a rectangle: X from -w to w, Z from -h to h?
# No, the groove is along Z. The cross section is in the XZ plane? 
# If we sketch on XY, we see the top view. The groove is a line? No.
# Let's rethink.
# Shaft is Cylinder along Z.
# Keyway is a rectangular cut along the length (Z).
# Cross section in XZ plane: Rectangle of width W and depth D.
# To cut this, we can use a REVOLUTION if we rotate the profile? No.
# We can use a POCKET if we sketch on a plane perpendicular to the cut direction?
# The cut direction is Z. So we need a plane perpendicular to Z -> XY plane.
# If we sketch on XY plane, the profile must represent the cut in the XY plane?
# No, the pocket subtracts the area of the sketch along the normal of the sketch plane.
# If sketch is on XY, normal is Z. So it cuts along Z. Perfect.
# But what does the sketch look like on XY?
# The keyway is along Z. From the top (XY view), it looks like a rectangle?
# No, from the top, it looks like a line if it's centered? 
# Wait, a keyway is a slot. From the top, you see the slot.
# If the slot is along Z (length), and centered on X=0.
# From XY plane (top down), the slot appears as a rectangle: X from -width/2 to width/2, Y from -depth/2 to depth/2?
# NO. The depth is in the X direction? Or Y?
# Standard keyway:
# Shaft axis: Z.
# Keyway axis: Z.
# Keyway width: along X (e.g., 8mm).
# Keyway depth: along X? Or Y? Usually depth is radial, so along X if centered. 
# Keyway height: along Z (length).
# So, cross section in XZ plane: Rectangle W x D.
# If we use a POCKET on the XY plane (normal Z), the sketch defines the footprint on the top surface.
# The footprint is a rectangle: X from -W/2 to W/2, Z from -H/2 to H/2?
# But the keyway goes all the way through? No, it's a groove.
# The pocket subtracts the volume defined by the sketch profile along the normal (Z).
# So if we define a rectangle on XY: X in [-W/2, W/2], Z in [-H/2, H/2].
# The pocket will remove material in that X-Z rectangle, extending infinitely in Y?
# No, the pocket removes material within the sketch bounds, extending along the normal.
# So it removes a box: X in [-W/2, W/2], Z in [-H/2, H/2], Y from -inf to +inf?
# No, it removes the volume bounded by the sketch and the normal direction.
# If the sketch is on XY, the normal is Z. The pocket removes material between the sketch and the opposite side?
# If "ThroughAll" is used, it cuts all the way through.
# So we get a channel along Z, with width W and depth (in Y?) determined by the cut?
# This logic is tricky.
# Alternative: Use a REVOLUTION? No.
# Alternative: Sketch on XZ plane, but use a specific feature?
# Actually, the easiest way to make a keyway along Z is to sketch the profile on the XZ plane 
# and use a REVOLVE? No.
# Let's use a POCKET on the XY plane.
# Sketch on XY plane.
# Profile: A rectangle representing the cross-section of the keyway as seen from the top?
# No, the keyway is a hole in the surface.
# Let's visualize: Shaft is cylinder. Keyway is a notch on the side.
# Top view (XY): A rectangle centered at origin. Width = keyway_width (X axis). 
# Length = keyway_height (Z axis).
# So the sketch on XY plane is a rectangle: X in [-key_w/2, key_w/2], Z in [-key_h/2, key_h/2].
# The pocket operation (ThroughAll) will cut this rectangular hole through the cylinder.
# This creates a keyway that is W wide, H long, and goes all the way through the diameter?
# YES. Because the pocket cuts along the normal (Z) through the entire part.
# The depth of the keyway (radial) is determined by the cylinder radius and the fact that it cuts through.
# But wait, a keyway has a specific depth (e.g., 3mm). It doesn't go all the way through the diameter (25mm).
# So a simple ThroughAll pocket on XY will create a hole through the center.
# We need a pocket that goes only 3mm deep.
# So we need to sketch the profile on the XZ plane?
# If we sketch on XZ, we see the side view.
# Profile: Rectangle W x D.
# We need to extrude this profile along Z? No, the profile IS along Z.
# We need to extrude the profile along Y? No, the shaft is along Z.
# We need to extrude the profile along the axis perpendicular to the XZ plane? That is Y.
# That would create a keyway along Y.
# We want a keyway along Z.
# This implies we need to sketch on a plane perpendicular to the cut direction (Z) -> XY plane.
# But on XY plane, the "depth"
