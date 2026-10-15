import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from task description
PRESSURE_ANGLE_DEG = 20.0
DIAMETRAL_PITCH = 24.0
NUMBER_OF_TEETH = 16
PITCH_DIAMETER_MM = 16.9418
OUTER_DIAMETER_MM = 19.05
OVERALL_LENGTH_MM = 304.8
GEAR_MODULE_MM = 25.4 / DIAMETRAL_PITCH

# --- Setup Document ---
doc = App.newDocument("GearStock")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold our named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.pitch_diameter = PITCH_DIAMETER_MM

params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.outer_diameter = OUTER_DIAMETER_MM

params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Overall Length")
params.overall_length = OVERALL_LENGTH_MM

params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.number_of_teeth = NUMBER_OF_TEETH

params.addProperty("App::PropertyLength", "module", "Dimensions", "Module")
params.module = GEAR_MODULE_MM

params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = PRESSURE_ANGLE_DEG

params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.face_width = 10.0 # Arbitrary face width for the stock

# --- Base Stock (Cylinder) ---
# Create a sketch for the base cylinder profile (rectangle)
base_sketch = body.newObject("Sketcher::SketchObject", "BaseStockSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.ConstrainAuto = True
base_sketch.ConstrainToCurrent = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add rectangle geometry: width = outer_diameter, height = face_width
# Centered at origin
base_sketch.addGeometry(Part.LineSegment(App.Vector(-params.outer_diameter / 2, -params.face_width / 2, 0), 
                                         App.Vector(params.outer_diameter / 2, -params.face_width / 2, 0)), False)
base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_diameter / 2, -params.face_width / 2, 0), 
                                         App.Vector(params.outer_diameter / 2, params.face_width / 2, 0)), False)
base_sketch.addGeometry(Part.LineSegment(App.Vector(params.outer_diameter / 2, params.face_width / 2, 0), 
                                         App.Vector(-params.outer_diameter / 2, params.face_width / 2, 0)), False)
base_sketch.addGeometry(Part.LineSegment(App.Vector(-params.outer_diameter / 2, params.face_width / 2, 0), 
                                         App.Vector(-params.outer_diameter / 2, -params.face_width / 2, 0)), False)

# Add constraints to make it a perfect rectangle centered at origin
base_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 1, 0, 0, 1, 0)) # Vertical edge vertical
base_sketch.addConstraint(Sketcher.Constraint("Axis", 1, 2, 0, 0, 1, 0)) # Horizontal edge horizontal
base_sketch.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, params.outer_diameter)) # Width
base_sketch.addConstraint(Sketcher.Constraint("DistanceY", 1, 2, params.face_width)) # Height
base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0, 0, 0)) # Centered on X
base_sketch.addConstraint(Sketcher.Constraint("Center", 1, 0, 0, 0)) # Centered on Y

# Pad the base stock
base_pad = body.newObject("PartDesign::Pad", "BaseStockPad")
base_pad.Profile = base_sketch
base_pad.Length = params.overall_length
base_pad.Type = "Solid"
base_pad.MidPlane = False

# --- Gear Teeth ---
# We will create a sketch on the top face of the stock (Z = face_width/2)
# However, PartDesign sketches are usually on planes. 
# Let's create a sketch on the XY plane, then lift it using an offset or just place it correctly.
# Actually, standard practice in PartDesign is to sketch on a plane. 
# We will sketch on XY plane, then use a Pad to extrude the teeth up to the top of the stock.
# Wait, the teeth need to be on the side. 
# Strategy: 
# 1. Create a sketch on the XY plane (Z=0).
# 2. Draw the tooth profile relative to the pitch circle.
# 3. Use a Pad to extrude the teeth along Z (upwards).
# 4. The teeth will sit on the XY plane. We need to position the sketch such that the teeth are centered vertically?
# No, the teeth are on the cylinder surface. 
# Correct Strategy for PartDesign:
# 1. Create a sketch on the XY plane.
# 2. Draw the tooth profile (arc + lines) relative to the pitch circle.
# 3. Use a Pad to extrude this profile along the Z axis.
# 4. The resulting solid will be a set of teeth standing on the XY plane.
# 5. We need to ensure the teeth are positioned correctly relative to the cylinder.
#    The cylinder is centered at (0,0,0) with height = face_width.
#    The teeth should be on the top face? Or distributed along the length?
#    "spur gear stock consists of a cylindrical gear blank extended into a long stock body"
#    Usually, the teeth are on the end face or along the length. 
#    Given "spur gear", teeth are on the cylindrical surface.
#    If we extrude a profile on the XY plane, we get a flat gear.
#    To get a cylindrical gear, we need to revolve a tooth profile around the Z axis.
#    BUT, the prompt asks for "spur gear teeth formed around the outer circumference".
#    This implies a standard spur gear shape (flat face, teeth on the rim).
#    So the geometry is: A cylinder of length L. On the top face (or distributed?), there are teeth.
#    Standard spur gear: Teeth are on the cylindrical surface, extending axially.
#    So we need to extrude a tooth profile along the Z axis.
#    The tooth profile is defined in the XY plane.
#    We will create ONE tooth profile sketch.
#    Then we will use a Polar Pattern to create all teeth.
#    Then we will Pad the patterned teeth along Z.
#    Finally, we might need to trim or ensure they don't interfere with the stock if the stock is just a cylinder.
#    Actually, if we Pad the teeth, they become part of the solid.
#    The "stock" is the cylinder. The "gear" is the teeth added to it.
#    So:
#    1. Base Cylinder (already done).
#    2. Create a sketch for ONE tooth on the XY plane.
#    3. Pad the tooth sketch along Z (height = face_width).
#    4. Polar Pattern the tooth Pad.
#    5. The result is a gear with teeth.

# --- Single Tooth Sketch ---
tooth_sketch = body.newObject("Sketcher::SketchObject", "SingleToothSketch")
tooth_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
tooth_sketch.ConstrainAuto = True
tooth_sketch.ConstrainToCurrent = True
tooth_sketch.MapMode = "FlatFace"
tooth_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Calculate tooth dimensions
# Pitch Diameter (PD)
PD = params.pitch_diameter
# Outer Diameter (OD)
OD = params.outer_diameter
# Module (m)
m = params.module
# Pressure Angle (PA)
PA = params.pressure_angle

# Tooth geometry calculations (Standard Spur Gear)
# Addendum = m
# Dedendum = 1.25 * m (standard)
# Clearance = 0.25 * m
# Tooth Thickness at Pitch Circle = PI * m / 2
# Tooth Thickness at Outer Circle = (PI * m / 2) - (PA_rad * (OD - PD) / 2) ? 
# Actually, simpler approach:
# We define the profile relative to the pitch circle.
# The tooth is symmetric about the X-axis (if we orient the tooth along X).
# Let's define the tooth profile in the XY plane.
# The tooth will be centered at (0,0) for the sketch, then we will pattern it.
# Wait, if we center the tooth at (0,0), the pitch circle is centered at (0,0).
# The tooth profile needs to be drawn such that the pitch circle passes through the pitch point.

# Pitch Radius
PR = PD / 2.0
# Outer Radius
OR = OD / 2.0
# Addendum
A = m
# Dedendum
D = 1.25 * m

# Tooth Thickness at Pitch Circle
t_pc = (App.pi * m) / 2.0

# Tooth Thickness at Outer Circle
# The involute profile is complex to draw with simple lines/arcs in a sketch without constraints.
# However, for a "stock" representation, we can approximate or use the standard simplified profile.
# Standard simplified profile:
# 1. Base circle radius: Rb = PR * cos(PA_rad)
# 2. Involute curve from Base circle to Outer circle.
# 3. Fillet at root.
# 4. Fillet at tip.
# 5. Straight sides.

# Let's try to construct the profile using lines and arcs for a standard look.
# We will define the tooth from the centerline (X-axis) to the edge.
# Points:
# 1. Pitch Point: (t_pc/2, 0)
# 2. Outer Tip: (t_oc/2, A) -> where t_oc is thickness at outer circle.
#    t_oc = t_pc - 2 * (PA_rad * (OR - PR) / 2) ? No.
#    The change in thickness is related to the arc length.
#    Arc length from Pitch to Outer = (OR - PR) * PA_rad (approx for small angles, but exact is integral).
#    Actually, the standard formula for tooth thickness at any radius r is:
#    s = s0 + (r - r0) * tan(PA) - (r^2 - r0^2) / (2 * r0) * sin(2*PA) ... too complex for sketch constraints.
#    Let's use a simplified approximation often used in CAD for stock gears:
#    The sides are straight lines tangent to the base circle? No.
#    Let's use the "Standard" simplified tooth profile:
#    - Top: Flat or rounded.
#    - Sides: Straight lines meeting at the pitch circle? No.
#    - Let's use the involute approximation with arcs.

# Let's define the profile points manually based on standard gear geometry.
# We will draw the right half of the tooth (from centerline to edge).
# Centerline is Y=0.
# Pitch Point P: (t_pc/2, 0)
# Outer Tip T: (t_oc/2, A)
# Root Point R: (t_rc/2, -D)

# Calculate t_oc (Thickness at Outer Diameter)
# The involute function is complex. Let's use a common approximation for the tooth thickness reduction.
# The reduction in thickness from pitch circle to outer circle is:
# delta_t = 2 * (OR - PR) * tan(PA_rad)
# Wait, this is the shift in the tangent point.
# The actual thickness reduction is:
# t_oc = t_pc - 2 * (OR - PR) * tan(PA_rad)
# Let's verify: 
# Arc length difference = (OR - PR) * PA_rad (if PA is the angle of the involute).
# No, the formula is: s = s0 + (r - r0)*tan(alpha) - (r^2 - r0^2)/(2*r0)*sin(2*alpha)
# For simplicity in a script, let's use the linear approximation often sufficient for stock:
# t_oc = t_pc - 2 * (OR - PR) * tan(PA_rad)
# Let's calculate PA_rad
PA_rad = App.pi * PRESSURE_ANGLE_DEG / 180.0
t_oc = t_pc - 2.0 * (OR - PR) * App.tan(PA_rad)

# Calculate t_rc (Thickness at Root Diameter)
# Root Diameter = PD - 2*D
RD = PD - 2.0 * D
t_rc = t_pc - 2.0 * (PR - RD/2.0) * App.tan(PA_rad) # Approximation

# Now we have the points for the right half of the tooth.
# We need to connect them.
# 1. Line from Root to Pitch? No, the side is an involute.
# 2. We can approximate the side with a line from the Root to the Pitch point? 
#    Or better, use an arc for the tip and a line for the side.
#    Let's use a simplified profile:
#    - Line from (t_rc/2, -D) to (t_pc/2, 0) -> This is the flank.
#    - Line from (t_pc/2, 0) to (t_oc/2, A) -> This is the face.
#    - Arc at the tip from (t_oc/2, A) to (-t_oc/2, A) -> Centered at (0, A)? No, usually rounded.
#    - Arc at the root.

# Let's refine the points for the sketch.
# We will draw the full tooth profile (symmetric).
# Points:
# P1: (t_rc/2, -D)  (Root edge)
# P2: (t_pc/2, 0)   (Pitch edge)
# P3: (t_oc/2, A)   (Outer edge)
# P4: (-t_oc/2, A)  (Outer edge left)
# P5: (-t_pc/2, 0)  (Pitch edge left)
# P6: (-t_rc/2, -D) (Root edge left)

# We will connect P1-P2-P3-P4-P5-P6-P1.
# But the sides P1-P2 and P3-P2 are not straight lines in reality (involute).
# However, for a "stock" gear, straight lines are acceptable and easier to constrain.
# Let's add constraints to make it symmetric and sized correctly.

# Add Geometry
# Right side
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(t_rc/2, -D, 0), App.Vector(t_pc/2, 0, 0)), False)
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(t_pc/2, 0, 0), App.Vector(t_oc/2, A, 0)), False)
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(t_oc/2, A, 0), App.Vector(-t_oc/2, A, 0)), False)
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(-t_oc/2, A, 0), App.Vector(-t_pc/2, 0, 0)), False)
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(-t_pc/2, 0, 0), App.Vector(-t_rc/2, -D, 0)), False)
tooth_sketch.addGeometry(Part.LineSegment(App.Vector(-t_rc/2, -D, 0), App.Vector(t_rc/2, -D, 0)), False)

# Add Constraints
# Symmetry about X axis (Y=0)
tooth_sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 0, 0, 1, 0)) # Line 0-1 symmetric about X
tooth_sketch.addConstraint(Sketcher.Constraint("Symmetry", 2, 3, 0, 0, 1, 0)) # Line 2-3 symmetric about X
tooth_sketch.addConstraint(Sketcher.Constraint("Symmetry", 4, 5, 0, 0, 1, 0)) # Line 4-5 symmetric about X
tooth_sketch.addConstraint(Sketcher.Constraint("Symmetry", 6, 7, 0, 0, 1, 0)) # Line 6-7 symmetric about X (if we had more points)

# Horizontal alignment (Root line Y = -D)
tooth_sketch.addConstraint(Sketcher.Constraint("Y", 0, 1, -D))
tooth_sketch.addConstraint(Sketcher.Constraint("Y", 4, 5, -D))

# Vertical alignment (Outer line Y = A)
tooth_sketch.addConstraint(Sketcher.Constraint("Y", 2, 3, A))

# Pitch circle constraint (Distance from origin to Pitch Point)
# We need to ensure the pitch point is at distance PR from origin.
# The pitch point is (t_pc/2, 0).
tooth_sketch.addConstraint(Sketcher.Constraint
