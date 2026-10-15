import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
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
doc = App.newDocument("SmoothShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Correct placement initialization for FreeCAD 1.1
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# Add a parameter set to drive dimensions
params_obj = body.newObject("App::VarSet", "Parameters")

# Map prompt parameter names to internal object property names
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
# Use the standard XY_Plane from the main document if available, otherwise create one.
# In FreeCAD 1.1 headless, standard planes might not be pre-loaded in the new doc.
# We will try to attach to the main doc's XY_Plane first.
try:
    support_plane = App.getDocument("FreeCAD").getObject("XY_Plane")
except KeyError:
    # Fallback: Create a local plane attached to the body
    support_plane = doc.addObject("PartDesign::Plane", "LocalPlane")
    support_plane.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
    support_plane.Parent = body
    support_plane.Type = "Face"

sketch_shaft.Support = (support_plane, [""])
sketch_shaft.MapMode = "FlatFace"
sketch_shaft.ConstrainToOtherObjects = False

diameter = PARAMS["smooth_shaft_diameter"]
radius = diameter / 2.0

# Draw the main shaft profile (Rectangle centered at 0,0)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-radius, 0, 0), App.Vector(radius, 0, 0)), False)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(radius, 0, 0), App.Vector(radius, radius, 0)), False)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(radius, radius, 0), App.Vector(-radius, radius, 0)), False)
sketch_shaft.addGeometry(Part.LineSegment(App.Vector(-radius, radius, 0), App.Vector(-radius, 0, 0)), False)

# Constraints
sketch_shaft.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
sketch_shaft.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch_shaft.addConstraint(Sketcher.Constraint("Perpendicular", 1, 0, 2, 1))
sketch_shaft.addConstraint(Sketcher.Constraint("Perpendicular", 2, 0, 3, 1))
sketch_shaft.addConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1))
sketch_shaft.addConstraint(Sketcher.Constraint("Length", 0, 2, 0, 1, radius))

# Create the Pad feature
pad_shaft = body.newObject("PartDesign::Pad", "ShaftPad")
pad_shaft.Profile = sketch_shaft
pad_shaft.setExpression("Length", "Parameters.smooth_shaft_length")
pad_shaft.Type = "Blind"
pad_shaft.Midplane = False
pad_shaft.Reverse = False
pad_shaft.Precision = 1e-06

# 2. Keyway Features (Pocket)
# Strategy: Sketch on XY plane (normal Z). The profile is a rectangle representing the 
# footprint of the keyway on the top surface.
# X range: [-width/2, width/2]
# Z range: [-height/2, height/2]
# The Pocket operation with Type="ThroughAll" will cut this rectangular hole through the entire shaft.
# This creates a keyway that is W wide, H long, and goes all the way through the diameter.
# Note: The prompt asks for "keyway_depth". A standard keyway is a groove on the surface, 
# not a hole through the center. However, creating a groove of specific depth (e.g., 3mm) 
# requires a more complex feature (like a custom extrusion or a specific pocket setup).
# Given the constraints of standard PartDesign features and the "ThroughAll" nature of simple pockets,
# and the fact that a 3mm depth on a 50mm diameter shaft is very shallow, 
# we will implement the keyway as a "ThroughAll" cut for simplicity and robustness in this script,
# OR we can try to make it a blind pocket if the geometry allows.
# 
# Let's re-evaluate: A keyway is a slot. If we use a Pocket on XY plane, it cuts along Z.
# If we set Type="Blind" and Length=2*radius - depth, it won't work easily because the pocket 
# subtracts from the sketch plane outwards.
# 
# Actually, the most robust way to make a keyway of specific depth in PartDesign is:
# 1. Sketch on XY plane.
# 2. Define the rectangle: X in [-w/2, w/2], Z in [-h/2, h/2].
# 3. Use a Pocket with Type="Blind".
# 4. The Length of the pocket should be the depth of the keyway? 
#    No, the pocket subtracts along the normal (Z). So Length is the depth of the cut.
#    If we set Length = keyway_depth, it cuts 3mm deep.
#    But where does it cut? It cuts from the sketch plane (Z=0) towards -Z (or +Z).
#    This creates a groove on the top surface.
#    We need TWO pockets (one +Z, one -Z) or a symmetric setup?
#    Usually, a keyway is centered. 
#    If we sketch on XY, the profile is the footprint.
#    If we use a Pocket with Length = keyway_depth, it cuts 3mm deep.
#    To make it centered, we might need to offset the sketch or use two pockets.
#    However, the simplest interpretation for a script is often a single cut or a centered cut.
#    Let's assume the keyway is centered on the shaft axis.
#    If we sketch on XY, the profile is centered.
#    If we use a Pocket with Length = keyway_depth, it cuts from Z=0 to Z=-depth.
#    This is not centered.
#    
#    Alternative: Use a REVOLVE? No.
#    Alternative: Use a Pocket on the XZ plane?
#    If we sketch on XZ, the normal is Y. The pocket cuts along Y.
#    Profile: Rectangle W x D.
#    If we set Length = keyway_height (50mm), it cuts a groove along Z?
#    No, the pocket subtracts the volume defined by the sketch along the normal.
#    If sketch is on XZ, normal is Y. It cuts a hole through the diameter (Y direction).
#    This is not a keyway along Z.
#    
#    Correct approach for a centered keyway of specific depth:
#    We need to cut a groove of depth D along the length H.
#    This is a rectangular prism cut.
#    We can achieve this by:
#    1. Sketching the profile on the XZ plane? No.
#    2. Sketching on XY plane, defining the footprint.
#    3. Using a Pocket with Type="Blind" and Length = keyway_depth.
#    4. But we need it centered.
#    
#    Let's try a different approach:
#    Sketch on XY plane.
#    Profile: Rectangle X in [-w/2, w/2], Z in [-h/2, h/2].
#    Pocket Type: "Blind".
#    Length: keyway_depth.
#    This cuts a groove of depth D.
#    To center it, we can't easily do it with one pocket unless we offset the sketch.
#    But wait, if we use "ThroughAll", it cuts through.
#    If the requirement is strictly "depth = 3mm", then "ThroughAll" is wrong.
#    Let's assume the user wants a groove of 3mm depth.
#    We will create a pocket that cuts 3mm deep.
#    To center it, we can create two pockets: one at +Z, one at -Z?
#    Or, we can create a pocket that cuts from Z=0 to Z=-depth, and another from Z=0 to Z=+depth?
#    Actually, the standard way to make a centered keyway in PartDesign is often to use a 
#    "Groove" feature if available, or a specific setup.
#    Since "Groove" is a specific feature in PartDesign (PartDesign::Groove), let's check if it exists.
#    Yes, PartDesign::Groove exists. It is a subtractive revolution.
#    But a keyway is not a revolution.
#    
#    Let's stick to the most reliable method:
#    Sketch on XY plane.
#    Profile: Rectangle X in [-w/2, w/2], Z in [-h/2, h/2].
#    Pocket Type: "Blind".
#    Length: keyway_depth.
#    This creates a groove.
#    To center it, we can't easily do it with one pocket.
#    However, if we assume the keyway is just a cut on one side or the user accepts a cut from the surface,
#    we can proceed.
#    BUT, the prompt says "smooth shaft... two keyway features". Usually implies centered.
#    
#    Let's try to make it centered using a trick:
#    If we sketch on XY, and use a Pocket with Length = keyway_depth, it cuts from Z=0.
#    If we want it centered, we need to cut from Z=-depth/2 to Z=+depth/2.
#    This is not possible with a single Blind Pocket starting from Z=0.
#    
#    Alternative: Use a Pocket with Type="ThroughAll" but limit the depth by the geometry? No.
#    
#    Let's reconsider the "Groove" feature.
#    PartDesign::Groove is a revolution. Not suitable.
#    
#    Let's go back to basics.
#    We can create a "Pocket" on the XY plane.
#    Profile: Rectangle X in [-w/2, w/2], Z in [-h/2, h/2].
#    Type: "Blind".
#    Length: keyway_depth.
#    This cuts a groove of depth D.
#    If we want it centered, we can create TWO pockets:
#    1. Pocket 1: Profile same, Length = keyway_depth/2. (Cuts from Z=0 to Z=-depth/2)
#    2. Pocket 2: Profile same, Length = keyway_depth/2. (Cuts from Z=0 to Z=+depth/2)
#    Wait, the second pocket would cut from Z=0 to Z=+depth/2.
#    The first cuts from Z=0 to Z=-depth/2.
#    Together they form a centered groove.
#    This works!
#    
#    So, we will create:
#    - One sketch for the keyway footprint.
#    - Two pockets: one cutting down (-Z), one cutting up (+Z).
#    - Then pattern them.

# Create the sketch for the keyway footprint
sketch_keyway = body.newObject("Sketcher::SketchObject", "KeywaySketch")
# Attach to XY plane again
sketch_keyway.Support = (support_plane, [""])
sketch_keyway.MapMode = "FlatFace"

key_w = PARAMS["keyway_width"] / 2.0
key_h = PARAMS["keyway_height"] / 2.0

# Draw the footprint rectangle
sketch_keyway.addGeometry(Part.LineSegment(App.Vector(-key_w, -key_h, 0), App.Vector(key_w, -key_h, 0)), False)
sketch_keyway.addGeometry(Part.LineSegment(App.Vector(key_w, -key_h, 0), App.Vector(key_w, key_h, 0)), False)
sketch_keyway.addGeometry(Part.LineSegment(App.Vector(key_w, key_h, 0), App.Vector(-key_w, key_h, 0)), False)
sketch_keyway.addGeometry(Part.LineSegment(App.Vector(-key_w, key_h, 0), App.Vector(-key_w, -key_h, 0)), False)

# Constraints
sketch_keyway.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
sketch_keyway.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Perpendicular", 1, 0, 2, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Perpendicular", 2, 0, 3, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Perpendicular", 3, 0, 0, 1))
sketch_keyway.addConstraint(Sketcher.Constraint("Length", 0, 2, 0, 1, key_w))
sketch_keyway.addConstraint(Sketcher.Constraint("Length", 0, 1, 0, 3, key_h))
sketch_keyway.addConstraint(Sketcher.Constraint("Center", 0, 1))

# Create the first pocket (cutting down -Z)
pocket_keyway_down = body.newObject("PartDesign::Pocket", "KeywayPocketDown")
pocket_keyway_down.Profile = sketch_keyway
pocket_keyway_down.setExpression("Length", "Parameters.keyway_depth / 2")
pocket_keyway_down.Type = "Blind"
pocket_keyway_down.Midplane = False
pocket_keyway_down.Reverse = False # Cuts in the direction of the normal? 
# Note: Pocket direction depends on the normal of the sketch plane.
# For XY plane, normal is +Z.
# If Reverse=False, it cuts in +Z direction? Or -Z?
# Usually, Pocket cuts in the direction of the normal.
# If we want to cut in -Z, we might need Reverse=True?
# Let's assume standard behavior: Reverse=False cuts in +Z.
# So we need Reverse=True to cut in -Z.
pocket_keyway_down.Reverse = True 

# Create the second pocket (cutting up +Z)
pocket_keyway_up = body.newObject("PartDesign::Pocket", "KeywayPocketUp")
pocket_keyway_up.Profile = sketch_keyway
pocket_keyway_up.setExpression("Length", "Parameters.keyway_depth / 2")
pocket_keyway_up.Type = "Blind"
pocket_keyway_up.Midplane = False
pocket_keyway_up.Reverse = False # Cuts in +Z

# Combine the two pockets into a single feature for patterning?
# No, we can pattern the "KeywayPocketDown" and then mirror it? 
# Or pattern both?
# Easier: Create a "Group" feature? No, PartDesign doesn't have a Group feature that patterns children.
# We can pattern the "KeywayPocketDown" and then use a "Mirror" feature?
# Or, we can create a "Pocket" that is the union of the two? No.
# Let's pattern the "KeywayPocketDown" around the Z axis.
# Then we need to mirror the pattern?
# Or, we can create a "Pocket" that cuts both sides?
# Actually, if we set the sketch to be symmetric and use a "ThroughAll" pocket, it cuts both sides.
# But we need specific depth.
# 
# Let's try a different approach:
# Create a "Pocket" with Type="Blind" and Length = keyway_depth.
# But how to center it?
# We can't.
# 
# Let's go with the two pockets approach.
# We will pattern the "KeywayPocketDown" around the Z axis.
# Then we will create a "Mirror" feature to mirror the patterned pockets across the XY plane?
# No, the pockets are already on the XY plane.
# We need to mirror the pockets across the XY plane?
# The pockets are cutting from Z=0.
# If we mirror the "KeywayPocketDown" (which cuts -Z) across the XY plane, we get a pocket cutting +Z.
# This is exactly what we need!
# So:
# 1. Create "KeywayPocketDown".
# 2. Pattern it around Z axis.
# 3. Create a "Mirror" feature that mirrors the patterned pockets across the XY plane.
#    Wait, the "Mirror" feature in PartDesign mirrors the geometry.
#    If we mirror a pocket that cuts -Z, the result is a pocket that cuts +Z.
#    This works perfectly.

# Pattern the down pocket
pattern_keyway = body.newObject("PartDesign::PolarPattern", "KeywayPattern")
pattern_keyway.Originals = [pocket_keyway_down]
pattern_keyway.Axis = (App.getDocument("FreeCAD").getObject("Z_Axis"), [""])
try:
    support_z = App.getDocument("FreeCAD").getObject("Z_Axis")
except KeyError:
    support_z = doc.addObject("PartDesign::Axis", "LocalZAxis")
    support_z.Placement = App.Placement(App.Vector(0,0,0), App.Rotation())
    support_z.Parent = body
    support_z.Type = "Axis"
pattern_keyway.Axis = (support_z, [""])
pattern_keyway.setExpression("Angle", "360 / Parameters.num_keyway")
pattern_keyway.setExpression("Occurrences", "Parameters.num_keyway")
pattern_keyway.Distribute = False
pattern_keyway.Reverse = False

# Mirror the patterned pockets across the XY plane
# The XY plane is the support_plane we used for the sketch.
# We need to reference the plane.
mirror_keyway = body.newObject("PartDesign::Mirror", "KeywayMirror")
mirror_keyway.Originals = [pattern_keyway]
# The mirror plane is the XY plane.
# We need to get the XY plane object.
try:
    mirror_plane = App.getDocument("FreeCAD").getObject("XY_Plane")
except KeyError:
    mirror_plane = support_plane # Use the local plane we created
mirror_keyway.Plane = (mirror_plane, [""])
mirror_keyway.Reverse = False

# -----------------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------------
doc.recompute()
doc.saveAs(str(doc_path))
