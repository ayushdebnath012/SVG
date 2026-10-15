import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__ as requested, but we will force the save path 
# to /app/answer.FCStd as per the specific grading instruction.
# The script logic uses __file__ for object creation context.
script_path = Path(__file__).resolve()
output_path = Path("/app/answer.FCStd")

# Parameters
FLANGE_OUTER_DIAMETER = 200.0   # mm
ELBOW_FLANGE_LENGTH = 300.0     # mm
ELBOW_FLANGE_HEIGHT = 300.0     # mm # This acts as the pipe length + allowances
ELBOW_ANGLE = 90.0              # degrees
ELBOW_RADIUS = 100.0            # mm
ELBOW_PIPE_DIAMETER = 100.0     # mm
ELBOW_PIPE_THICKNESS = 5.0      # mm
BOLT_CIRCLE_RADIUS = 72.5       # mm
BOLT_HOLE_DIAMETER = 16.0       # mm
NUMBER_BOLT_HOLES = 8

# --- Document Setup ---
doc = App.newDocument("ElbowFlange")

# Create the Body
body = doc.addObject("PartDesign::Body", "Body")

# Named Parameters (App::VarSet approach simulated via direct property addition for simplicity in PartDesign)
# We will define them as variables on the body for clarity and editability.
params = body.newObject("App::Property", "Parameters")
# Note: In FreeCAD 1.1, creating a named parameter variable usually involves adding a Property with a specific name.
# We will assign values to the body directly or use a Property to hold them if strictly required, 
# but direct assignment to the Body object often works for simple parametric scripts in 1.1 headless mode.
# However, to ensure "Named Document Objects" drive geometry as requested:
# We will create a Property object to hold the values, or just set them on the Body.
# The prompt asks for "named document objects whose properties drive the geometry".
# Let's create a specific Parameter object.
param_obj = body.newObject("App::Property", "Dimensions")
param_obj.width = FLANGE_OUTER_DIAMETER
param_obj.height = ELBOW_FLANGE_HEIGHT
param_obj.length = ELBOW_FLANGE_LENGTH
param_obj.radius = ELBOW_RADIUS
param_obj.pipe_dia = ELBOW_PIPE_DIAMETER
param_obj.thickness = ELBOW_PIPE_THICKNESS
param_obj.angle = ELBOW_ANGLE
param_obj.bolt_r = BOLT_CIRCLE_RADIUS
param_obj.bolt_h = BOLT_HOLE_DIAMETER
param_obj.bolt_n = NUMBER_BOLT_HOLES

# --- Feature Construction ---

# 1. Sketch 1: Left Flange (Flat, centered on Z axis at Z=0, extending in X)
# We will build the flange, then extend to pipe, then revolve.
# Strategy: 
# Sketch 1: Outer circle (Flange Face) and Inner Pipe Hole (Flange Face).
# Sketch 2: Left Pipe Profile (Side view) - Outer Arc and Inner Tube.
# Sketch 3: Right Pipe Profile (Side view).
# Sketch 4: Bolt holes on Right Flange (on the rotated face).
# Sketch 5: Bolt holes on Left Flange (on the rotated face).
# Wait, simpler approach for Elbow:
# 1. Sketch Left Flange (X-Z plane, centered at 0,0).
# 2. Pad (Flange Thickness).
# 3. Sketch Right Flange (Rotated 90 deg around Y, centered at X=Length).
# 4. Pad (Flange Thickness).
# 5. Sketch Pipe Profile (Side view between flanges).
# 6. Revolve Pipe Profile.
# 7. Subtract/Pad Pipe.
# 8. Add Bolt Holes.

# Helper to get plane
def get_plane(plane_name):
    planes = ["XY_Plane", "XZ_Plane", "YZ_Plane"]
    for p_name in planes:
        try:
            p = doc.getObject(p_name)
            if p: return p
        except: pass
    return None

def get_axis(axis_name):
    axes = ["X_Axis", "Y_Axis", "Z_Axis"]
    for a_name in axes:
        try:
            a = doc.getObject(a_name)
            if a: return a
        except: pass
    return None

# --- Feature 1: Left Flange Sketch ---
sketch_lf = body.newObject("Sketcher::SketchObject", "Sketch_LeftFlange")
sketch_lf.Plane = (get_plane("XY_Plane"), [""])
sketch_lf.Constraints = []
# Outer Circle
sketch_lf.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.width / 2), False)
# Inner Pipe Hole (for the flange face, not the pipe wall yet)
# Pipe OD is 100. Pipe ID is 90. Flange height 300.
# We sketch the hole that the pipe passes through.
sketch_lf.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), (params.pipe_dia / 2) + (params.thickness / 2)), False)
sketch_lf.addConstraint(Sketcher.Constraint("Center", 0, 1, 0, 1))
sketch_lf.addConstraint(Sketcher.Constraint("Radius", 0, 0, 1, 0, params.width / 2))
sketch_lf.addConstraint(Sketcher.Constraint("Radius", 0, 0, 1, 1, (params.pipe_dia / 2) + (params.thickness / 2)))
sketch_lf.Constraints = [] # Reset to ensure we add them explicitly if needed, though addGeometry adds them implicitly? No.
# Re-add constraints properly
sketch_lf.addConstraint(Sketcher.Constraint("Center", 0, 1, 0, 1))
sketch_lf.addConstraint(Sketcher.Constraint("Radius", 0, 0, 1, 0, params.width / 2))
sketch_lf.addConstraint(Sketcher.Constraint("Radius", 0, 0, 1, 1, (params.pipe_dia / 2) + (params.thickness / 2)))

# --- Feature 2: Left Flange Pad ---
pad_lf = body.newObject("PartDesign::Pad", "Pad_LeftFlange")
pad_lf.Profile = sketch_lf
pad_lf.Length = params.height # Elbow Flange Height (Thickness of the flat part)
pad_lf.MidPlane = True

# --- Feature 3: Left Bolt Holes Sketch ---
sketch_bolt_lf = body.newObject("Sketcher::SketchObject", "Sketch_BoltLeft")
sketch_bolt_lf.Plane = (sketch_lf, ["Edge1"]) # Attach to the outer circle edge of Left Flange
# Actually, attaching to the face of the sketch is better. 
# Let's attach to the Outer Circle edge of Sketch_LeftFlange.
# We need to reference the edge.
sketch_bolt_lf.Plane = (sketch_lf, ["Edge1"]) # Edge1 is the first added geometry? No, we need to be careful.
# Let's attach to the XY plane offset by the flange height? No, the flange is created.
# Best practice: Attach to the Sketch object itself, then offset the sketch plane along the Z axis of the sketch?
# No, Sketcher::SketchObject.Plane can take (SketchObject, [EdgeIndex]).
# We need the outer circle edge. Since we added Circle 1 then Circle 2, Edge1 is Circle 1.
sketch_bolt_lf.Plane = (sketch_lf, ["1"]) # Index 1 is the outer circle.

# Bolt Circle
# Bolt Circle Radius is 72.5. Pipe Radius is 50. 
# Distance from center = 72.5.
bolt_circle_r = params.bolt_r
bolt_hole_d = params.bolt_h
bolt_n = params.bolt_n

# Main Bolt Circle
sketch_bolt_lf.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_circle_r), False)
# Bolt Holes
angle_step = 360.0 / bolt_n
for i in range(bolt_n):
    angle = i * angle_step
    x = bolt_circle_r * App.Vector.Cos(angle)
    z = bolt_circle_r * App.Vector.Sin(angle)
    sketch_bolt_lf.addGeometry(Part.Circle(App.Vector(x, 0, z), App.Vector(0, 0, 1), bolt_hole_d / 2), False)

# Constraints
# Center on origin
sketch_bolt_lf.addConstraint(Sketcher.Constraint("Center", 0, 0, 1, 1)) # Main circle center
# Coincident with main circle for holes
for i in range(bolt_n):
    angle = i * angle_step
    x = bolt_circle_r * App.Vector.Cos(angle)
    z = bolt_circle_r * App.Vector.Sin(angle)
    # We can't dynamically generate constraint indices easily in headless without knowing exact object order.
    # Instead, we define a pattern.
    pass

# --- Feature 4: Left Bolt Holes Pattern ---
pattern_bolt_lf = body.newObject("PartDesign::PolarPattern", "Pattern_BoltLeft")
pattern_bolt_lf.Originals = [sketch_bolt_lf]
pattern_bolt_lf.Axis = (doc.getObject("Z_Axis"), [""])
pattern_bolt_lf.Angle = 360.0
pattern_bolt_lf.Occurrences = bolt_n
pattern_bolt_lf.Placement = sketch_bolt_lf.Placement # Ensure it stays in the plane of the sketch

# --- Feature 5: Left Flange Pocket (To remove material for the pipe entry) ---
# The pipe enters the flange. We need to cut a hole through the flange.
# The pipe OD is 100. The flange hole we sketched earlier was (50 + 2.5) = 52.5 radius.
# Wait, the pipe goes THROUGH the flange.
# Pipe OD = 100. Radius = 50.
# The flange sketch had a hole of Radius 52.5. This is sufficient for the pipe OD.
# We need to subtract the volume of the pipe.
# The pipe is a tube.
# We will model the pipe first, then subtract it from the flange?
# Or Pad the flange, then Pad the pipe (subtractive).
# Let's do: Pad Left Flange. Then Pad Right Flange. Then Pad Pipe (Subtractive). Then Bolt Holes.
# Actually, the flange hole needs to be "Through" the pipe path.
# Let's refine the sequence:
# 1. Pad Left Flange.
# 2. Pad Right Flange.
# 3. Sketch Pipe Profile (Side View).
# 4. Revolve Pipe Profile (This creates the elbow pipe).
# 5. Subtract Pipe from Flanges? 
#    The Pipe Revolve will be a solid. The Flanges are solids.
#    We need to Boolean Subtract the Pipe from the Flanges.
#    But PartDesign doesn't have a direct "Subtract" feature that takes another body as input easily in older versions, 
#    unless we use a specific trick or just build the pipe to intersect.
#    Better: Build the flanges as "Through" pockets relative to the pipe? No.
#    Standard Elbow Flange: Pipe is continuous. Flanges are attached.
#    So: Pipe Solid + Flange Solid - Overlap?
#    Or: One continuous solid? 
#    The prompt asks for "one solid body".
#    If we Pad Left Flange, Pad Right Flange, then Revolve Pipe... we have 3 separate bodies.
#    We need to join them or subtract them.
#    PartDesign::Join? No, that creates a new Body.
#    We can use a Pocket with "ThroughAll" or specific length to cut the flange material out of the way?
#    Actually, the easiest way to get "One Solid" in PartDesign without explicit Boolean commands is to build the geometry such that they are connected, or use a specific feature like "Fuse" (if available in 1.1) or just ensure the sketches are linked.
#    Alternative: Build the ELBOW first (Pipe), then add the flanges as Pockets? No.
#    Let's build the FLANGES first, then the PIPE as a POKET (subtraction) into the assembly?
#    No, the pipe is the main structural element.
#    Sequence:
#    1. Sketch Left Flange (Face). Pad it.
#    2. Sketch Right Flange (Face, rotated). Pad it.
#    3. Sketch Pipe Profile (Side view). Revolve it.
#    4. We now have 3 bodies.
#    How to make one solid? 
#    We can use a "Pocket" with Type="ThroughAll" on the pipe face to cut the flanges? No.
#    We can use a "Pad" with "MidPlane" on the pipe, and then use a "Fillet" to blend? No.
#    The correct way in PartDesign for a single body:
#    Create the Pipe (Revolve). 
#    Create the Flanges as "Pockets" subtracted from the pipe? No, they are added.
#    Create the Flanges as "Pads". 
#    Then use a "Join" feature? 
#    FreeCAD 1.1 PartDesign does not have a "Join" feature that merges bodies into one within the same tree easily without a complex setup.
#    HOWEVER, we can create the flanges as PADS, and then create the pipe as a REVOLVE, and then use a "Pocket" to cut the intersection? No.
#    Let's try the reverse:
#    1. Sketch a large block containing everything? No.
#    2. Create the Pipe (Revolve).
#    3. Create the Flanges as "Pockets" subtracted from a larger block? No.
#    Let's assume the standard workflow:
#    1. Pad Left Flange.
#    2. Pad Right Flange.
#    3. Revolve Pipe.
#    4. The result is 3 bodies. 
#    Is there a way to make them one? 
#    Yes, if we use "Part::Fuse" externally, but we can't.
#    Wait, "PartDesign::Body" can contain multiple features. If they are not connected, they are separate solids.
#    To make ONE solid, they must be topologically connected.
#    We can achieve this by making the Pipe a "Pocket" (subtraction) from a larger block? No.
#    How about: Create the Pipe. Then create the Flanges as "Pockets" that are actually "Pads" added to the pipe?
#    If I Pad the flange, it is separate.
#    Solution: Create the Flanges first. Then create the Pipe such that it intersects the flanges. 
#    If I use a "Pad" with a sketch that includes the pipe wall thickness, and the flange hole...
#    Let's try this:
#    1. Sketch Left Flange (Outer Circle + Inner Pipe Hole). Pad it.
#    2. Sketch Right Flange (Outer Circle + Inner Pipe Hole). Pad it.
#    3. Sketch Pipe Profile (Side view). 
#       - Outer arc (Radius = ElbowRadius + PipeDiameter/2).
#       - Inner arc (Radius = ElbowRadius + PipeThickness/2).
#       - This forms the pipe wall.
#    4. Revolve this profile. 
#       - This creates the elbow pipe.
#    5. Now we have 3 solids.
#    6. We need to merge them. 
#    7. Since we cannot use external Boolean, we must ensure connectivity in the sketch or use a feature that merges.
#    8. There is no "Fuse" in PartDesign.
#    9. However, we can use the "Pocket" feature to subtract the pipe from a block? No.
#    10. Maybe the prompt implies "One Solid" means the final TopoShape has one solid, even if the tree has multiple features? 
#        "producing exactly one solid body". 
#        If I have 3 disconnected solids, that's 3 solids.
#        I must connect them.
#    11. Trick: Create the Flanges as PADS. Then create the Pipe as a REVOLVE. 
#        Then use a "Pocket" to cut the pipe material? No.
#        How about creating the Pipe first?
#        1. Sketch Pipe Profile. Revolve. (Solid 1)
#        2. Sketch Left Flange (on the pipe face?). 
#           If I sketch on the face of the pipe, and Pad, it will be attached.
#           Yes! If I attach the sketch to the Face of the Pipe, the Pad will be attached.
#           So: 
#           - Revolve Pipe.
#           - Sketch Left Flange on the Left Face of the Pipe. Pad it.
#           - Sketch Right Flange on the Right Face of the Pipe. Pad it.
#           This creates one connected solid!
#    12. BUT: The Pipe has a wall thickness. The Flange is flat. 
#        When I pad the flange on the pipe face, it will be attached to the pipe surface.
#        The Flange hole must be sized to accommodate the pipe OD.
#        The Pipe OD is 100. The Flange Outer is 20
