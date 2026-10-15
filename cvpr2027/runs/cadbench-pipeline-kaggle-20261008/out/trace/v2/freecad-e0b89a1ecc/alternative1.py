from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

# Determine output paths from the script location
script_dir = Path(__file__).resolve().parent
output_fcstd = script_dir / "answer.FCStd"

# Create a new document
doc = App.newDocument("GearStock")

# 1. Define Named Parameters (App::VarSet)
# This allows us to drive dimensions and angles from a single object.
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter_mm", "Dimensions", "Outer diameter of gear blank")
params.addProperty("App::PropertyLength", "pitch_diameter_mm", "Dimensions", "Pitch circle diameter")
params.addProperty("App::PropertyLength", "length_mm", "Dimensions", "Total length of stock")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of gear teeth")
params.addProperty("App::PropertyInteger", "pressure_angle_deg", "Dimensions", "Pressure angle (deg)")
params.addProperty("App::PropertyLength", "module_mm", "Dimensions", "Module (mm)")
params.addProperty("App::PropertyLength", "root_diameter_mm", "Dimensions", "Root diameter calculation")
params.addProperty("App::PropertyLength", "addendum_mm", "Dimensions", "Addendum calculation")

# Set initial values based on the problem description
# pressure_angle = 20 deg, diametral_pitch = 24, N = 16
# P = 24 DP => m = 25.4 / 24 mm
# D = N / DP = 16 / 24 * 25.4 = 16.9418 mm
# OD = 0.75 in = 19.05 mm (This implies a specific tooth height or clearance setup, we will use these values directly)
# Length = 304.8 mm

params.outer_diameter_mm = 19.05
params.pitch_diameter_mm = 16.9418
params.length_mm = 304.8
params.number_of_teeth = 16
params.pressure_angle_deg = 20.0
params.module_mm = 25.4 / 24.0
params.addendum_mm = params.module_mm # Standard addendum = 1*module
params.root_diameter_mm = params.pitch_diameter_mm - 2 * params.addendum_mm # Standard dedendum approx

# 2. Create PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# 3. Create Base Profile Sketch (Extrusion Profile)
# We need a rectangle: width = outer_diameter, height = length
sketch_base = body.newObject("Sketcher::SketchObject", "BaseProfile")
sketch_base.Plane = "XY_Plane"
sketch_base.ConstrainToView = False
# Set the rectangle dimensions using expressions
sketch_base.addGeometry(Part.LineSegment(App.Vector(-params.outer_diameter_mm/2, -params.length_mm/2, 0), 
                                          App.Vector(params.outer_diameter_mm/2, -params.length_mm/2, 0)), False)
sketch_base.addGeometry(Part.LineSegment(App.Vector(params.outer_diameter_mm/2, -params.length_mm/2, 0), 
                                          App.Vector(params.outer_diameter_mm/2, params.length_mm/2, 0)), False)
sketch_base.addGeometry(Part.LineSegment(App.Vector(params.outer_diameter_mm/2, params.length_mm/2, 0), 
                                          App.Vector(-params.outer_diameter_mm/2, params.length_mm/2, 0)), False)
sketch_base.addGeometry(Part.LineSegment(App.Vector(-params.outer_diameter_mm/2, params.length_mm/2, 0), 
                                          App.Vector(-params.outer_diameter_mm/2, -params.length_mm/2, 0)), False)

# Constraints: Horizontal/Vertical, Coincident center
sketch_base.addConstraint(Sketcher.Constraint("Axis1", 0, 0, "X_Axis"))
sketch_base.addConstraint(Sketcher.Constraint("Axis1", 0, 1, "X_Axis"))
sketch_base.addConstraint(Sketcher.Constraint("Axis1", 1, 0, "X_Axis"))
sketch_base.addConstraint(Sketcher.Constraint("Axis1", 1, 1, "X_Axis"))
sketch_base.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch_base.addConstraint(Sketcher.Constraint("Center", 1, 0))
sketch_base.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, params.outer_diameter_mm))
sketch_base.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, params.length_mm))
sketch_base.ConstrainToView = False

# 4. Pad the Base Body
pad = body.newObject("PartDesign::Pad", "PadStock")
pad.Profile = sketch_base
pad.Length = params.length_mm
pad.Type = "Fully"
pad.Reversed = False
# Drive length from parameter
pad.setExpression("Length", "Parameters.length_mm")

# 5. Create Gear Teeth Sketch
# We need to generate the involute profile for the teeth.
# Reference circle (pitch diameter)
# Outer circle (tip diameter)
# Root circle (root diameter)
# Pressure angle = 20 deg

sketch_teeth = body.newObject("Sketcher::SketchObject", "GearTeeth")
sketch_teeth.Plane = "XY_Plane" # We will revolve this later, so we define it on XY plane to get a cylinder-like gear if we revolve around Z
# However, usually gears are modeled by sketching the cross-section in XZ or XY and revolving.
# Let's sketch the cross section in the XZ plane (Profile of the gear tooth) and revolve around the Z axis (Gear axis).
# Wait, the stock is a cylinder. The teeth are on the outside.
# Strategy: 
# 1. Create a cylinder stock (done via Pad on XY plane rectangle).
# 2. Create a sketch on the YZ plane (or XZ) that represents one tooth profile.
# 3. Use a Polar Pattern on the cylinder surface? No, PartDesign Polar Pattern works on faces/edges but usually requires a face reference.
# Alternative Strategy (more robust for gears):
# 1. Sketch the tooth profile on the XY plane (cross section at the pitch diameter).
# 2. Use Revolution to create the gear teeth ring? 
#    If we sketch the tooth profile (line from root to tip) and revolve 360, we get a gear.
#    But we need to attach it to the existing stock.
#    Better: Create the teeth as a separate solid using Revolution, then use a Pocket to cut them into the stock?
#    Or: Create the teeth profile in the XY plane (as a set of teeth) and extrude? No, that makes a disk.
#    Correct approach for "Stock":
#    - We have a Cylinder (Body).
#    - We need to add material for teeth OR cut the stock if it was a blank? 
#    The prompt says "spur gear stock... with spur gear teeth formed". 
#    Usually, this means we start with a blank (OD * Length) and the teeth are the final shape at the OD.
#    So we can:
#    1. Pad the blank (done).
#    2. Create a sketch on the XY plane (end face) showing the tooth profile? No, that's 2D.
#    3. Create a sketch on the XZ plane (radial cross section). 
#    4. Create a "Groove" or "Pocket" that removes material from the blank to form teeth? 
#       No, teeth are added material relative to the root, but the blank is usually the OD.
#       Actually, standard gear blank is often made to OD, and then teeth are cut? 
#       No, standard gear blank is made to OD + clearance, then teeth are cut.
#       BUT, the prompt says "outer_diameter" is 0.75in. And "pitch_diameter" is 0.667in.
#       So the blank is the outer envelope. The teeth are formed OUTWARDS from the pitch circle to the outer circle.
#       Wait, if the blank is OD=0.75, and pitch is 0.667, the teeth must protrude from the pitch circle to the OD.
#       So we can:
#       1. Create the blank (Cylinder).
#       2. Create a sketch on the XZ plane (radial slice) defining the tooth profile from Pitch Dia to OD.
#       3. Use a "Groove" (subtractive revolution) to cut the material? 
#          No, we need to ADD teeth to the blank? 
#          If the blank is already OD, and the teeth are between Pitch and OD...
#          Actually, the "Stock" is the cylinder. The "Gear" is the result.
#          If the blank is OD=0.75, then the teeth are already there? 
#          No, a "stock" usually implies a cylindrical blank. The teeth are the feature.
#          Let's assume the blank is the cylinder of OD=0.75 and Length=1ft.
#          The teeth are the involute profile between PitchDia and ODDia.
#          So we can create the tooth profile on the XZ plane, and use a **Pad** to add the teeth?
#          But the Pad would add to the cylinder.
#          If we pad from the cylinder surface, we need a specific face.
#          Better approach: 
#          1. Create the blank (Cylinder).
#          2. Create a sketch on the XZ plane. Define the profile of ONE tooth relative to the pitch circle.
#          3. Use **Revolution** to rotate this profile 360 degrees. 
#             If the profile includes the space between teeth (the void), we can use a **Pocket** (subtractive revolution) to cut the teeth into the blank.
#             This is the most reliable way to model a gear from a cylindrical blank.
#
# Step 5.1: Calculate tooth geometry
# Module m = 1.058333
# P = 24
# Addendum a = m = 1.0583
# Dedendum d = 1.25*m = 1.3229 (Standard)
# Pitch Dia Dp = 16.9418
# Root Dia Dr = Dp - 2*d = 16.9418 - 2.6458 = 14.296
# Tip Dia Dt = Dp + 2*a = 16.9418 + 2.1167 = 19.058 (Matches prompt 19.05 approx)
# Pressure Angle = 20 deg

# We will define the profile of one tooth space (or tooth) to cut.
# Let's define the profile of a TOOTH (the solid part) relative to the center.
# Or define the profile of the VOID (space between teeth) to cut.
# Cutting the void is easier for "Pocket".
# Profile of one tooth space:
# Starts at Root Dia (14.296), goes to Tip Dia (19.05).
# The space is bounded by two involutes.
# Involute angle calculation:
# Involute function: inv(phi) = tan(phi) - phi (radians)
# Pressure angle at pitch circle = 20 deg.
# At root circle, pressure angle is smaller.
# At tip circle, pressure angle is larger.
# However, for a simplified script without external libraries, we can approximate the tooth flank or use the standard AGMA formula if possible.
# Since we need a script, let's calculate the involute points.
# 
# Let's define the profile of the TOOTH (solid) to PAD it onto the blank? 
# No, the blank is already the OD.
# So we MUST CUT the material.
# We will create a sketch of the TOOTH SPACE (the gap) and use a Pocket (Revolution type) to remove it.
# 
# Tooth Space Geometry:
# Circle 1: Root Circle (Dr = 14.296). Radius r_r = 7.148.
# Circle 2: Tip Circle (Dt = 19.05). Radius r_t = 9.525.
# The tooth space starts at r_r and ends at r_t.
# The width of the space at the pitch diameter is Circular Pitch / 2.
# Circular Pitch p = PI * m = 3.14159 * 1.05833 = 3.325 mm.
# Space width at pitch circle = p / 2 = 1.6625 mm.
#
# We need to generate the involute curve for the tooth space.
# The involute starts at the Base Circle.
# Base Dia Db = Dp * cos(20deg) = 16.9418 * 0.93969 = 15.92 mm.
# Root Dia Dr = 14.296. This is < Base Dia. 
# So the root is inside the base circle. The involute doesn't exist at the root. The flank is straight (circular arc)?
# Standard gear: The flank from Root to Base is a circular arc (part of the root circle). From Base to Tip is involute.
# 
# So, the profile of the tooth space (gap) consists of:
# 1. An arc of the Root Circle (from one flank intersection to the other).
# 2. An involute curve from the Base Circle to the Tip Circle.
# 3. Another involute curve symmetric.
# 4. An arc of the Tip Circle (top of the space? No, the top of the tooth is the tip).
#    Wait, the tooth space is the empty area between teeth.
#    The boundaries of the tooth space are the flanks of the adjacent teeth.
#    So the profile of the space is bounded by:
#    - Two involute curves meeting at the Base circle? No, they start at the Base circle and go outwards.
#    - They meet the Root circle at the base of the tooth space.
#    - They meet the Tip circle at the top of the tooth space.
#    Actually, the tooth space is the region between two teeth.
#    So the profile is:
#    Start at Root Circle (R1).
#    Go along Root Circle arc to the start of the involute? 
#    Actually, the tooth space width is defined at the Pitch Circle.
#    Let's construct the profile of ONE TOOTH (solid) and then use a Pocket? 
#    No, if we pocket the tooth, we remove the tooth. We want to keep the tooth.
#    So we must pocket the SPACE.
#    
#    Profile of Space:
#    Start at Root Circle (radius r_r). 
#    The space width at Pitch Circle is p/2.
#    The involute starts at Base Circle (r_b).
#    The space profile goes:
#    1. From (r_r, angle_start) along the root circle? 
#       Actually, the tooth space is bounded by the two flanks.
#       Flank 1: Involute starting from Base Circle.
#       Flank 2: Involute starting from Base Circle.
#       The distance between these flanks at the Pitch Circle is p/2.
#       At the Root Circle, the flanks are usually cut off by the root circle arc.
#       At the Tip Circle, the flanks are cut off by the tip circle arc.
#       
#    Let's calculate the angles.
#    Pressure angle at pitch circle alpha_p = 20 deg.
#    Pressure angle at root circle? 
#       The base circle radius r_b = r_p * cos(alpha_p).
#       The root radius r_r < r_b. So the root is inside the base circle.
#       The involute does not exist below the base circle. The tooth flank is the base circle itself?
#       No, the root circle cuts the involute.
#       So the flank is a straight line? No, it's the Base Circle arc from the point where the root circle intersects the base circle?
#       Actually, standard gear drawing:
#       - From Base to Tip: Involute.
#       - From Root to Base: Circular Arc (Root circle).
#       
#    So the space profile:
#    - Start at Root Circle (r_r). 
#    - The space starts at the intersection of the Root Circle and the Involute?
#      No, the Root Circle is the bottom of the tooth. The space is between two teeth.
#      The bottom of the space is the Root Circle.
#      The top of the space is the Tip Circle.
#      The sides are the involutes.
#      
#    Let's define the points for ONE side of the space.
#    We need the angle between the two teeth.
#    Total angle = 360 / N = 360 / 16 = 22.5 deg.
#    Half angle = 11.25 deg.
#    The space is centered at 0 degrees? 
#    Let's say the space is from -11.25 to +11.25 degrees?
#    No, the space is the gap. The tooth is the solid.
#    If we sketch the gap, we need the boundary of the gap.
#    Boundary 1: Left flank of the left tooth.
#    Boundary 2: Right flank of the right tooth.
#    These flanks are involutes.
#    
#    Let's calculate the angle of the involute.
#    phi_base = 0 (at base circle).
#    phi_p = 20 deg (at pitch circle).
#    phi_tip = ?
#    r_tip = r_p / cos(phi_tip)? No.
#
