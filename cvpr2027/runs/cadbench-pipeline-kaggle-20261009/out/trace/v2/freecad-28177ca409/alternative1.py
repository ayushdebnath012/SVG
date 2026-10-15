import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize Document
doc = App.newDocument("GibHeadKey")

# --- Parameters ---
# We create a VarSet to hold the named parameters requested in the prompt
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "length", "Dimensions", "axial length (joint to tip)")
params.addProperty("App::PropertyLength", "width", "Dimensions", "head width")
params.addProperty("App::PropertyLength", "key_height", "Dimensions", "body height at joint")
params.addProperty("App::PropertyLength", "height_with_head", "Dimensions", "total height with head")
params.addProperty("App::PropertyAngle", "taper_angle", "Dimensions", "angle of head slant")
params.addProperty("App::PropertyLength", "key_taper_ratio", "Dimensions", "body height taper ratio")

# Set values as per prompt
params.length = 14.0
params.width = 4.0
params.key_height = 4.0
params.height_with_head = 7.0
params.taper_angle = 45.0
params.key_taper_ratio = 0.01

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Head Profile) ---
# We will define the cross-section of the key (Head + Tapered Body start)
sketch1 = body.newObject("Sketcher::SketchObject", "HeadProfileSketch")
sketch1.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.ConstrainAuto = False
sketch1.TechDrawPictogramSequence = []

# Define the outline of the head relative to the centerline (Y=0)
# Points: Center, Right Tip, Top Right Tip, Top Left Tip, Left Tip, Center
# Width = params.width -> Half Width = params.width / 2
# Height with head = params.height_with_head -> Half Height = params.height_with_head / 2

half_width = params.width / 2.0
half_height_head = params.height_with_head / 2.0
half_height_body = params.key_height / 2.0

# Construct geometry for the head profile (Symmetric around Y axis, extruded later)
# Since we are doing a Pad along Z, the sketch is on XY.
# The profile will be a closed loop representing the cross section.
# However, for a key, it's easier to define the contour and then pad.
# Let's define the contour in the XY plane.

# Points (X, Y)
# 1. Center Bottom
p1 = App.Vector(0, -half_height_body)
# 2. Right Bottom
p2 = App.Vector(half_width, -half_height_body)
# 3. Right Top (Head starts)
p3 = App.Vector(half_width, -half_height_body) 
# Wait, the geometry is: A rectangle for the head, then a taper down to the shaft height.
# Actually, the prompt says "tapered end". Usually, the head is wider and taller.
# Let's model the Head Profile in the XY plane.
# Y is the vertical dimension (height), X is the horizontal (width).
# The key has a rectangular head section and a tapered body section below it? 
# Or is the head a separate block? 
# "Tapered end" usually means the length tapers. "Head" is the top part.
# Let's assume the standard Gib Head Key shape:
# Top part (Head): Rectangular block of width X, height H_head.
# Bottom part (Body): Tapers from the bottom of the head down to the tip.
# But the prompt says "key_height" is body height at joint. "height_with_head" is total.
# So at Z=0 (joint), Height = 7.0. At Z=14 (tip), Height = 7.0 - (14 * 0.01) = 5.6? 
# Or is the taper on the head itself? "taper_angle... angle of the head's slanted face".
# This implies the head is a wedge.
# Let's interpret: 
# The "Body" of the key (the part that goes into the keyway) tapers along its length.
# The "Head" is the top part used for handling.
# Standard Gib Key: The head is a square/rectangular prism. The shank tapers slightly.
# OR: The head is a trapezoid? 
# "taper_angle... angle of the head's slanted face from horizontal". This suggests the head itself is tapered (like a wedge).
# Let's build a Head that is a trapezoid in cross-section? 
# No, "gib head key" usually has a square head and a tapered shank. 
# Let's look at the parameters again. 
# "taper_angle=45 degree (angle of the head's slanted face from horizontal)".
# This strongly suggests the HEAD is a wedge shape (trapezoidal profile).
# So the profile in the XY plane (if we pad along Z) is a trapezoid? 
# No, we pad the profile to create length.
# Let's do this:
# 1. Sketch on XY plane: Define the Cross-Section (Width vs Height).
#    The cross-section changes along Z (Length).
#    So we need a Pad that varies, or we sketch the profile on XZ plane?
#    Standard practice: Sketch on XY (Cross section), Pad along Z. 
#    If the cross section changes, we need a Pad with a variable length or a solid sweep.
#    BUT, PartDesign::Pad is linear. 
#    Alternative: Sketch on XZ (Side view) and Pad along Y? No, keyway is usually horizontal.
#    Let's assume the Key is oriented such that Length is Z-axis.
#    The Cross Section (X-Y) is the shape we pad.
#    If the cross section changes (taper), a simple Pad won't work unless we use a complex profile or multiple features.
#    HOWEVER, the prompt asks for "Parametric feature tree". 
#    Maybe the "Head" is the top part (Z=0 to Z=some) and the "Body" is the bottom part (tapered)?
#    Let's assume the "Head" is a block on top of a tapered wedge?
#    Or, simpler interpretation: The object IS the tapered wedge, and the "Head" is just the name, but the geometry has a flat top part?
#    Let's re-read carefully: "tapered end and a head that protrudes". 
#    Usually, the head is wider than the body.
#    Let's create a composite solid:
#    1. Head Block: Rectangular prism (Width X, Height H_head, Length L_head).
#    2. Body Wedge: A wedge attached to the bottom of the head, tapering from H_body_joint to H_tip over Length L_body.
#    
#    Wait, if I pad a profile, the profile must be constant.
#    If the profile changes, I cannot use a single Pad.
#    UNLESS: I sketch the "Head" profile and pad it to the joint length. Then sketch the "Body" profile and pad it?
#    No, they connect.
#    Correct approach for variable cross-section in PartDesign:
#    Sketch the profile at the base (Joint). Pad to the tip.
#    If the tip is smaller, the profile at the tip must match.
#    So:
#    Sketch 1: Profile at Z=0 (Joint).
#    Pad 1: From Z=0 to Z=14.
#    But the profile at Z=14 must be smaller (tapered).
#    A Pad creates a prism. It does not taper the profile itself.
#    To get a tapered profile, we need a **PartDesign::Pad** with a **Shape** that is a wedge? No.
#    We need a **PartDesign::Pad** where the Profile is a line? No.
#    We need to model the Taper as a separate volume subtraction or a specific feature.
#    
#    Alternative Strategy:
#    Model the "Head" as a block.
#    Model the "Body" as a tapered wedge.
#    But they must join seamlessly.
#    
#    Let's try this geometry construction:
#    The "Key" is a wedge that gets smaller towards the end.
#    The "Head" is the top flat part.
#    Maybe the "Head" is just the top portion of the tapered body?
#    "angle of the head's slanted face". This implies the top surface is slanted.
#    So the whole thing is a wedge?
#    If the whole thing is a wedge (trapezoidal in X-Y cross section? No, trapezoidal in X-Z? No).
#    Let's assume the standard "Tapered Key" geometry:
#    It is a prism that tapers in height.
#    If I define the profile in the X-Y plane, and I want the height to taper along Z, 
#    I cannot use a standard Pad with a closed profile.
#    
#    WORKAROUND for Tapered Extrusion in FreeCAD PartDesign:
#    1. Create the "Head" as a block (Rectangular Prism).
#    2. Create the "Body" as a Wedge (created by a Pad on a triangular profile? No).
#    Let's define the "Body" as a wedge by extruding a triangle?
#    No, the body must connect to the head.
#    
#    Let's rethink the orientation.
#    Maybe the Key is extruded along the Y axis? 
#    Sketch on XZ plane (Side view).
#    Profile: A trapezoid (Top width W, Bottom width W, Height changes?).
#    If the profile is constant, the extrusion is constant.
#    
#    Okay, let's look at the "Gib Head Key" specifically.
#    It is a wedge. The wedge angle is the taper.
#    The "Head" is the top part which is often square.
#    Actually, a Gib Key is a wedge that is wider at the top than the bottom.
#    So the cross-section (looking from the front) is a rectangle? No, the width is constant, the thickness varies?
#    No, Gib keys fit into a keyway. The width fits the keyway width. The height varies (taper).
#    So:
#    Width = Constant (4.0mm).
#    Height = Varies (Tapers from 7.0mm at head to ~5.6mm at tip).
#    Length = 14.0mm.
#    
#    So the profile is a rectangle (Width x Height).
#    Since Height changes along Length, we cannot use a single Pad.
#    We must build it as a **Wedge**.
#    How to make a wedge in PartDesign?
#    1. Create a sketch of the rectangle (Width x Max_Height) at the base.
#    2. Pad it to the full length.
#    3. This creates a rectangular prism.
#    4. Now we need to taper it.
#    5. We can use a **PartDesign::Pad** with a **Midplane** and a **Wedge**? No, Pad doesn't do wedges directly on a profile.
#    6. We can use a **PartDesign::Pad** with a **Linear** motion, but we need to reduce the size.
#    7. Trick: Use a **PartDesign::Pad** to create the block. Then use a **PartDesign::Pocket** with a taper? No, Pocket is also linear usually.
#    8. Better: Use a **PartDesign::Revolution**? No, it's a linear key.
#    9. Correct Feature: **PartDesign::Pad** with a **Shape** that is a wedge? No.
#    
#    Let's use the **Wedge** logic via a combination of features:
#    1. Create a block (Width 4, Height 7, Length 14).
#    2. To taper it, we can cut a wedge out of it?
#       If we cut a wedge, we leave a smaller prism.
#       But we need the top to remain flat (or slanted?).
#       "Head that protrudes".
#       Usually, the head is the top part. The bottom tapers.
#       If we cut a wedge from the bottom, the top remains flat.
#       But the prompt says "angle of the head's slanted face".
#       This implies the HEAD is slanted.
#       So the TOP surface is slanted.
#       This means the object is a wedge where the thickness decreases along the length.
#    
#    Construction Plan:
#    1. Sketch on XY plane (Top view? No, we need the profile).
#       Let's sketch on XZ plane (Side view).
#       We want to extrude along Y.
#       Profile in XZ:
#       X range: -2 to +2 (Width 4).
#       Z range: 0 to 14 (Length).
#       Height (Y): Varies from 7.0 (at Z=0) to 7.0 - (14 * 0.01) = 5.6 (at Z=14)?
#       Wait, "key_height=4.0mm (body height at the head/body joint)".
#       "height_with_head=7.0mm".
#       This implies there is a distinct "Head" part and a "Body" part.
#       Joint is at Z=0?
#       If the head is slanted, maybe the head is a wedge itself?
#       Let's assume the Head is a wedge (Trapezoid in X-Z? No, X-Y?).
#       
#    Let's try the most robust interpretation for "Gib Head Key" with these params:
#    The key is a wedge.
#    The "Head" is the top portion.
#    The "Body" is the bottom portion.
#    The "Head" has a slanted face.
#    This means the top surface is inclined.
#    
#    Let's build it as:
#    1. **Sketch 1 (Base Profile)**: On the XZ plane (Side view).
#       Define the outline of the key in the X-Z plane.
#       Since the key tapers in height (Y), we need to extrude the profile along Y?
#       No, if the profile is in XZ, extruding along Y gives a constant height.
#       We need the height (Y) to change along Z.
#       This requires a **Sweep** or **Revolution** (around Y? No) or **Pad** with a varying profile.
#       
#    Since PartDesign::Pad is the only extrusion tool, and it requires a constant profile, 
#    we must decompose the geometry.
#    
#    Decomposition:
#    1. **Head**: A block.
#       Dimensions: Width 4, Height (some portion of 7), Length (some portion of 14).
#       Wait, if the head is slanted, it's a wedge.
#    2. **Body**: A tapered wedge.
#    
#    Let's try this specific geometry which fits "Head slanted":
#    The object is a wedge.
#    Top face is slanted.
#    Side faces are vertical (Width constant).
#    Bottom face is flat (on XY plane).
#    
#    To create a wedge in PartDesign:
#    1. Create a block (Width 4, Height 7, Length 14).
#    2. Cut a wedge from the top?
#       If we cut a wedge from the top, we get a slanted top.
#       But we need the cut to be a specific angle (45 deg).
#       How to cut a wedge in PartDesign?
#       We can use a **PartDesign::Pad** with a **Negative** value (Pocket) if we define a wedge shape?
#       No, Pocket is usually linear or rotational.
#       
#    Alternative: **PartDesign::Pad** with a **Wedge** shape?
#    FreeCAD PartDesign does not have a "Wedge" feature directly.
#    BUT, we can create a **Part::Wedge** and use it as a **PartDesign::Pocket** or **PartDesign::Pad** base?
#    Yes! `body.newObject("PartDesign::Pocket", ...)` can take a `PocketBase`? No, it takes a `Profile`.
#    However, `PartDesign::Pocket` can use a `Part::Wedge` as the cutter if we convert it?
#    Actually, there is a feature `PartDesign::Pad` that accepts a `Reference`?
#    
#    Let's use the **Wedge** creation via a sketch trick:
#    1. Sketch a rectangle (Width 4, Height 7) on XZ plane.
#    2. Pad it along Y to length 14? No, that makes a prism.
#    
#    Okay, let's flip the logic.
#    The "Head" is a block. The "Body" is a tapered extension.
#    1. **Sketch 1 (Head Profile)**: On XY plane.
#       Shape: Rectangle (Width 4, Height 3.5? No, total height 7).
#       Pad along Z for length `L_head`.
#    2. **Sketch 2 (Body Profile)**: On XY plane?
#       No, we need to taper the height.
#    
#    Let's go with the most reliable method for tapered solids in FreeCAD PartDesign:
#    **Create the full block, then subtract a wedge.**
#    But how to subtract a wedge?
#    We can
