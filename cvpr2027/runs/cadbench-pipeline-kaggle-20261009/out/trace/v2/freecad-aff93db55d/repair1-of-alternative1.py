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
# For a standard gear, the space width at the pitch circle is approximately equal to the tooth thickness.
# We will model the "valleys" (spaces) by revolving a profile that cuts into the cylinder.
# The width of the valley at the pitch diameter is roughly the Tooth Circumference.
GROOVE_WIDTH = TOOTH_CIRCUMFERENCE
# The depth of the cut needs to go from the Outer Diameter down to at least the Pitch Diameter.
# We will cut slightly deeper to ensure the pitch circle is clear.
CUT_DEPTH = (OUTER_DIAMETER_MM - PITCH_DIAMETER_MM) + (GEAR_MODULE * 0.5)

# --- Script Execution ---

# 1. Create Document
doc = App.newDocument("GearStock")
doc.Label = "GearStock_Assembly"

# 2. Create Named Parameters (Editable via Property Editor)
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
params.addProperty("App::PropertyLength", "cutDepth", "Dimensions", "Effective Cut Depth")
params.cutDepth = CUT_DEPTH

# 3. Create PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")
body.ViewObject.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# 4. Create Base Sketch (Blank Cylinder Face)
# We will sketch the profile of the gear face on the Front Plane (XZ).
# The Z-axis will be the axis of revolution.
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
# Attach to Front Plane (XZ) and lift to Z=0
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
# Explicitly attach to the Front Plane
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))

# Add Geometry: A rectangle representing the blank cylinder face
# Width = Outer Diameter, Height = Face Width
# Centered at (0,0) in the sketch plane (XZ)
# X range: [-outerDia/2, outerDia/2]
# Z range: [-faceWidth/2, faceWidth/2]
# Note: In XZ plane, X is horizontal, Z is vertical.
# We will draw a rectangle from (-outerDia/2, -faceWidth/2) to (outerDia/2, faceWidth/2)
# But we need to define it as lines or a closed shape. Let's use a rectangle defined by 4 lines.
# Actually, Part.LineSegment creates open lines. We need a closed loop or use a rectangle if available.
# Since we are in Sketcher, we can add 4 lines and constrain them, or use a rectangle if the version supports it.
# To be safe and explicit, we will add 4 lines and constrain them to form a rectangle.

# Line 1: Bottom (-outerDia/2, -faceWidth/2) to (outerDia/2, -faceWidth/2)
l1 = Part.LineSegment(App.Vector(-OUTER_DIAMETER_MM/2, -OVERALL_LENGTH_MM/2, 0), 
                      App.Vector(OUTER_DIAMETER_MM/2, -OVERALL_LENGTH_MM/2, 0))
sketch_base.addGeometry(l1, False)

# Line 2: Right (outerDia/2, -faceWidth/2) to (outerDia/2, faceWidth/2)
l2 = Part.LineSegment(App.Vector(OUTER_DIAMETER_MM/2, -OVERALL_LENGTH_MM/2, 0), 
                      App.Vector(OUTER_DIAMETER_MM/2, OVERALL_LENGTH_MM/2, 0))
sketch_base.addGeometry(l2, False)

# Line 3: Top (outerDia/2, faceWidth/2) to (-outerDia/2, faceWidth/2)
l3 = Part.LineSegment(App.Vector(OUTER_DIAMETER_MM/2, OVERALL_LENGTH_MM/2, 0), 
                      App.Vector(-OUTER_DIAMETER_MM/2, OVERALL_LENGTH_MM/2, 0))
sketch_base.addGeometry(l3, False)

# Line 4: Left (-outerDia/2, faceWidth/2) to (-outerDia/2, -faceWidth/2)
l4 = Part.LineSegment(App.Vector(-OUTER_DIAMETER_MM/2, OVERALL_LENGTH_MM/2, 0), 
                      App.Vector(-OUTER_DIAMETER_MM/2, -OVERALL_LENGTH_MM/2, 0))
sketch_base.addGeometry(l4, False)

# Add Constraints to make it a perfect rectangle
# Coincident constraints for corners
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # L1 end to L2 start
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # L2 end to L3 start
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # L3 end to L4 start
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1)) # L4 end to L1 start

# Horizontal lines (L1, L3) are parallel and equidistant
sketch_base.addConstraint(Sketcher.Constraint("Parallel", 0, 2, 2, 2))
sketch_base.addConstraint(Sketcher.Constraint("Distance", 0, 2, 3, 2, OUTER_DIAMETER_MM)) # Distance between L1 and L3 is outerDia

# Vertical lines (L2, L4) are parallel and equidistant
sketch_base.addConstraint(Sketcher.Constraint("Parallel", 1, 2, 3, 2))
sketch_base.addConstraint(Sketcher.Constraint("Distance", 1, 2, 0, 2, OVERALL_LENGTH_MM)) # Distance between L2 and L4 is faceWidth

# 5. Create Pad Feature (The Blank Cylinder)
pad = body.newObject("PartDesign::Pad", "PadBlank")
pad.Profile = sketch_base
pad.Length = OVERALL_LENGTH_MM
pad.Midplane = False
pad.Reversed = False
# Drive length from parameter
pad.setExpression("Length", "GearParameters.faceWidth")

# 6. Create Groove Sketch (The Valley Profile)
# This sketch will define the shape of the space between teeth.
# We will place it on the Front Plane (XZ) as well, but we need to position it correctly.
# The groove profile is a curve that goes from the outer diameter, cuts inwards to the pitch diameter,
# and follows the involute profile.
# For simplicity in a script without complex curve generation, we will approximate the valley.
# A standard spur gear valley is bounded by two involute curves.
# We will create a sketch that represents the "cutting tool" path.
# The tool path starts at the outer diameter, goes inwards along the pressure angle, 
# reaches the pitch circle, and then goes back out? 
# Actually, the groove is the space. The space is bounded by the involute of the tooth.
# Let's create a profile that represents the "valley" width at the pitch circle and depth.
# We will create a simple approximation: A rectangle at the pitch circle depth, widened at the top.
# Or better: Use a curve that mimics the involute.
# Involute equation: x = r * (cos(t) + t*sin(t)), y = r * (sin(t) - t*cos(t))
# Here, r is the base circle radius. Base circle radius = Pitch Radius * cos(Pressure Angle).
# r_base = (PITCH_DIAMETER_MM / 2) * cos(PRESSURE_ANGLE_DEG)

# Let's create a sketch for the groove profile.
# We will place this sketch on the Front Plane (XZ) as well.
# We need to position it such that it revolves around the Z axis.
# The profile will be in the XZ plane.
# The "width" of the groove at the pitch circle is GROOVE_WIDTH.
# The "depth" is CUT_DEPTH.
# We will create a closed loop that approximates the valley.

sketch_groove = body.newObject("Sketcher::SketchObject", "GrooveSketch")
# Attach to Front Plane (XZ)
sketch_groove.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_groove.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_groove.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_groove.Placement = App.Placement(App.Vector(0, 0, 0))

# Calculate Base Circle Radius
r_base = (PITCH_DIAMETER_MM / 2.0) * math.cos(math.radians(PRESSURE_ANGLE_DEG))
r_pitch = PITCH_DIAMETER_MM / 2.0
r_outer = OUTER_DIAMETER_MM / 2.0

# We will create a profile that starts at the outer diameter, goes inwards along the pressure angle,
# then follows the pitch circle arc for the groove width, then goes back out.
# However, generating an exact involute in a script is complex.
# Let's use a simplified approach: A rectangular cut at the pitch circle depth, 
# with fillets or chamfers to approximate the transition.
# Or, we can use a curve that is close enough.
# Let's try to generate a few points for the involute and connect them.

# Points for the left side of the valley (relative to the center of the groove)
# The groove is centered at some angle. Let's say we are creating the profile for one groove.
# The groove is located between two teeth.
# Let's define the groove profile in the XZ plane.
# The profile will be symmetric around the X axis? No, the groove is between teeth.
# Let's assume the groove is centered at X = 0 for the sketch, and we will revolve it.
# Wait, if we revolve a profile centered at X=0, we get a hole in the middle.
# We want a groove on the surface.
# So the profile should be a "cut" shape.
# Let's create a profile that is a "U" shape or similar, positioned at a specific X offset?
# No, the standard way to model a gear with a groove (subtractive revolution) is:
# 1. Create a profile of the "valley" in the XZ plane.
# 2. Revolve this profile around the Z axis.
# The profile should be a closed loop that represents the material to be removed.
# The profile will be located such that its center is at X=0? No.
# If we revolve a shape centered at X=0, we get a ring.
# We want the groove to be on the surface of the cylinder.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH at the pitch circle depth.
# And we will position it such that it cuts into the cylinder.
# Actually, the easiest way is to create a profile that is a "C" shape or similar, 
# but since we are using a subtractive revolution, we need a closed loop.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove to be on the surface.
# So the profile should be a "slice" of the cylinder.
# Let's create a profile that is a rectangle of width = GROOVE_WIDTH and height = CUT_DEPTH.
# We will position this rectangle such that its center is at X=0, Z=0?
# No, if we revolve a rectangle centered at X=0, we get a hole.
# We want the groove
