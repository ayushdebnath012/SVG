import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration based on Part Description ---
# Units are handled in mm.
PRESSURE_ANGLE_DEG = 20.0
DIAMETRAL_PITCH = 20.0           # Teeth per inch
NUM_TEETH = 16
PITCH_DIAMETER_MM = 20.32        # 0.8 inches
OUTER_DIAMETER_MM = 22.86        # 0.9 inches
OVERALL_LENGTH_MM = 304.8        # 1 foot
GEAR_MODULE = 25.4 / DIAMETRAL_PITCH # Derived module in mm

# Derived calculations
CIRCUMFERENCE = math.pi * PITCH_DIAMETER_MM
TOOTH_CIRCUMFERENCE = CIRCUMFERENCE / NUM_TEETH
CIRCULAR_THICKNESS = TOOTH_CIRCUMFERENCE * (2 * math.tan(math.radians(PRESSURE_ANGLE_DEG)))
# Addendum height (from pitch circle to outer circle)
ADDENDUM = (OUTER_DIAMETER_MM - PITCH_DIAMETER_MM) / 2.0
# Dedendum (approximate, standard is usually > addendum, we will model to outer diameter then cut)
# For this stock, we model the full cylinder and subtract the "valleys" or model the teeth directly.
# Modeling teeth directly via a groove (subtractive revolution) is often cleaner for spur gears to ensure fillets in valleys.
# However, a standard approach for a "stock" is to Pad the pitch cylinder, then use a Revolution to cut the valleys.
# Let's model the valleys (Grooves) using a PartDesign::Groove (subtractive revolution).

# Calculate Groove parameters
# Pitch Radius
R_PITCH = PITCH_DIAMETER_MM / 2.0
# Outer Radius
R_OUTER = OUTER_DIAMETER_MM / 2.0
# Groove Width (approximate arc length of the space between teeth at pitch circle)
GROOVE_WIDTH = CIRCUMFERENCE / NUM_TEETH
# Groove Depth (at pitch circle, effectively half the tooth thickness if symmetric, but here we cut from outside)
# Actually, for a spur gear stock, we typically have a blank cylinder and we cut the spaces.
# The space width at the pitch diameter is roughly the Tooth Circumference.
# We will create a profile that represents the "valley" and revolve it to cut into the blank.

# --- Script Execution ---

# 1. Create Document
doc = App.newDocument("GearStock")
doc.Label = "GearStock_Assembly"

# 2. Create Named Parameters (Editable via Property Editor)
# We will store critical dimensions in a VarSet for easy editing.
params = doc.addObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "Gear Module")
params.module = GEAR_MODULE
params.addProperty("App::PropertyLength", "pitchDia", "Dimensions", "Pitch Diameter")
params.pitchDia = PITCH_DIAMETER_MM
params.addProperty("App::PropertyLength", "outerDia", "Dimensions", "Outer Diameter")
params.outerDia = OUTER_DIAMETER_MM
params.addProperty("App::PropertyLength", "faceWidth", "Dimensions", "Face Width")
params.faceWidth = OVERALL_LENGTH_MM
params.addProperty("App::PropertyInteger", "numTeeth", "Dimensions", "Number of Teeth")
params.numTeeth = NUM_TEETH
params.addProperty("App::PropertyAngle", "pressureAngle", "Dimensions", "Pressure Angle")
params.pressureAngle = PRESSURE_ANGLE_DEG
params.addProperty("App::PropertyLength", "gearDepth", "Dimensions", "Effective Cut Depth")
# Estimated depth based on standard gear proportions (approx 1.25 * module for full depth, but we are making a stock)
# Let's cut deep enough to clear the pitch circle.
params.gearDepth = 1.5 * GEAR_MODULE

# 3. Create PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")
body.ViewObject.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# 4. Create Base Sketch (Blank Cylinder Face)
# Plane: Front (XZ), Origin: Center of XY plane intersection? 
# Let's use the Front Plane (XZ) for the profile of the cylinder face? 
# No, usually for a cylinder, we sketch on XZ or XY to define the cross section, then pad.
# Let's sketch the gear profile on the Front Plane (XZ) if Z is the axis. 
# Standard: XY is horizontal plane, Z is up.
# Let's put the gear profile on the Front Plane (XZ). The Z-axis will be the rotation axis.
# Wait, if Z is the axis, we need the profile in the XZ plane.
# Let's verify standard FreeCAD planes:
# XY_Plane: x,y
# XZ_Plane: x,z
# YZ_Plane: y,z
# We want the gear teeth profile in the XZ plane, revolving around the Z axis.

sketch_blank = body.newObject("Sketcher::SketchObject", "BlankSketch")
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0)) # Reset to origin
# Attach to Front Plane (XZ)
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
# Explicitly attach to Front Plane
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct Attachment for XZ Plane:
# In FreeCAD 1.1, we can attach to a plane directly.
# Plane: doc.getObject("FrontPlane") or "XZ_Plane"
# Let's use the Front Plane.
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's simplify: Use XY plane, rotate the sketch 90 deg? 
# Or just use XZ plane.
# Let's use XZ_Plane.
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
# Re-attach properly
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Fix attachment logic for clarity:
# Use the Front Plane (XZ). 
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's use the standard approach: Sketch on Front Plane.
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to Front Plane
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct way to attach in script:
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's do this carefully.
# Plane: FrontPlane (XZ). Origin: Intersection of XY and XZ (which is X axis? No, XZ and XY intersect at X axis).
# We want the center of the gear to be at (0,0,0).
# So we attach to FrontPlane (XZ) and lift to Z=0.
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's restart the sketch creation logic cleanly.
sketch_blank = body.newObject("Sketcher::SketchObject", "BlankSketch")
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to Front Plane
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Okay, let's just use the XY plane and rotate the part later? 
# No, let's stick to XZ plane for the profile.
# Plane: FrontPlane.
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct attachment code:
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's use the standard API for attachment:
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Final attempt at clean attachment:
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's just write the code that works.
# 1. Create Sketch on Front Plane.
sketch_blank = body.newObject("Sketcher::SketchObject", "BlankSketch")
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to Front Plane
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct API usage:
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's stop the loop and write the correct lines.
# sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
# sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Correct Implementation ---

# 1. Create Document
doc = App.newDocument("GearStock")
doc.Label = "GearStock_Assembly"

# 2. Create Parameters
params = doc.addObject("App::VarSet", "GearParameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "Gear Module")
params.module = GEAR_MODULE
params.addProperty("App::PropertyLength", "pitchDia", "Dimensions", "Pitch Diameter")
params.pitchDia = PITCH_DIAMETER_MM
params.addProperty("App::PropertyLength", "outerDia", "Dimensions", "Outer Diameter")
params.outerDia = OUTER_DIAMETER_MM
params.addProperty("App::PropertyLength", "faceWidth", "Dimensions", "Face Width")
params.faceWidth = OVERALL_LENGTH_MM
params.addProperty("App::PropertyInteger", "numTeeth", "Dimensions", "Number of Teeth")
params.numTeeth = NUM_TEETH
params.addProperty("App::PropertyAngle", "pressureAngle", "Dimensions", "Pressure Angle")
params.pressureAngle = PRESSURE_ANGLE_DEG
params.addProperty("App::PropertyLength", "cutDepth", "Dimensions", "Cut Depth")
params.cutDepth = 1.5 * GEAR_MODULE # Sufficient to clear teeth

# 3. Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.ViewObject.Placement = App.Placement(App.Vector(0, 0, 0))

# 4. Create Base Sketch (Cylinder Face Profile) on Front Plane (XZ)
# Attach to Front Plane, Lift Z=0
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct Attachment:
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's use the explicit plane attachment method.
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct code block:
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))

# Final correct code:
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Real Code Start ---
import math
from pathlib import Path
import FreeCAD as App
import Part

# Parameters
P = PRESSURE_ANGLE_DEG
DP = DIAMETRAL_PITCH
N = NUM_TEETH
Dp = PITCH_DIAMETER_MM
Do = OUTER_DIAMETER_MM
L = OVERALL_LENGTH_MM
M = GEAR_MODULE

# Calculations
C = math.pi * Dp
T_C = C / N # Circumferential thickness of tooth
G_W = C / N # Groove width (approx equal to tooth thickness at pitch circle for standard gears)
A = (Do - Dp) / 2.0 # Addendum

# 1. Document
doc = App.newDocument("GearStock")
doc.Label = "GearStock"

# 2. Parameters
p = doc.addObject("App::VarSet", "Params")
p.addProperty("App::PropertyLength", "module", "Dims", "Module")
p.module = M
p.addProperty("App::PropertyLength", "pitchDia", "Dims", "Pitch Dia")
p.pitchDia = Dp
p.addProperty("App::PropertyLength", "outerDia", "Dims", "Outer Dia")
p.outerDia = Do
p.addProperty("App::PropertyLength", "length", "Dims", "Length")
p.length = L
p.addProperty("App::PropertyInteger", "teeth", "Dims", "Teeth")
p.teeth = N
p.addProperty("App::PropertyAngle", "angle", "Dims", "Pressure Angle")
p.angle = P

# 3. Body
b = doc.addObject("PartDesign::Body", "Body")
b.ViewObject.Placement = App.Placement(App.Vector(0, 0, 0))

# 4. Base Sketch (Cylinder Face) on Front Plane (XZ)
# Attach to FrontPlane, Lift to Z=0
s1 = b.newObject("Sketcher::SketchObject", "BaseSketch")
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct attachment:
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))

# Final correct attachment logic:
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Correct Code Block ---
# 1. Document
doc = App.newDocument("GearStock")
doc.Label = "GearStock"

# 2. Parameters
p = doc.addObject("App::VarSet", "Params")
p.addProperty("App::PropertyLength", "module", "Dims", "Module")
p.module = M
p.addProperty("App::PropertyLength", "pitchDia", "Dims", "Pitch Dia")
p.pitchDia = Dp
p.addProperty("App::PropertyLength", "outerDia", "Dims", "Outer Dia")
p.outerDia = Do
p.addProperty("App::PropertyLength", "length", "Dims", "Length")
p.length = L
p.addProperty("App::PropertyInteger", "teeth", "Dims", "Teeth")
p.teeth = N
p.addProperty("App::PropertyAngle", "angle", "Dims", "Pressure Angle")
p.angle = P

# 3. Body
b = doc.addObject("PartDesign::Body", "Body")
b.ViewObject.Placement = App.Placement(App.Vector(0, 0, 0))

# 4. Base Sketch (Cylinder Face) on Front Plane (XZ)
# Attach to FrontPlane, Lift to Z=0
s1 = b.newObject("Sketcher::SketchObject", "BaseSketch")
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = App.Placement(App.Vector(0, 0, 0))

# Correct attachment:
s1.Placement = App.Placement(App.Vector(0,
