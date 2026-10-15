import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from task description
PRESSURE_ANGLE_DEG = 20.0
DIAMETRAL_PITCH = 24.0
NUM_TEETH = 20
PITCH_DIAMETER_MM = 21.1582
OUTER_DIAMETER_MM = 23.368
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
params.addProperty("App::PropertyLength", "pitchDiameter", "Dimensions", "Pitch Diameter")
params.pitchDiameter = PITCH_DIAMETER_MM
params.addProperty("App::PropertyLength", "outerDiameter", "Dimensions", "Outer Diameter")
params.outerDiameter = OUTER_DIAMETER_MM
params.addProperty("App::PropertyLength", "overallLength", "Dimensions", "Overall Length")
params.overallLength = OVERALL_LENGTH_MM
params.addProperty("App::PropertyInteger", "numTeeth", "Dimensions", "Number of Teeth")
params.numTeeth = NUM_TEETH
params.addProperty("App::PropertyAngle", "pressureAngle", "Dimensions", "Pressure Angle (deg)")
params.pressureAngle = PRESSURE_ANGLE_DEG
params.addProperty("App::PropertyLength", "module", "Dimensions", "Module")
params.module = GEAR_MODULE_MM

# --- Base Cylinder (Blade) ---
# Create a sketch for the base cylinder profile
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.ConstrainAuto = True
base_sketch.ConstrainFully = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Add a circle for the base
base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitchDiameter / 2.0), False)

# Add constraints to fix the circle
base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
base_sketch.addConstraint(Sketcher.Constraint("Radius", 0, params.pitchDiameter / 2.0))

# Pad the base cylinder
base_pad = body.newObject("PartDesign::Pad", "BasePad")
base_pad.Profile = base_sketch
base_pad.Length = params.overallLength
base_pad.Type = "Solid"
base_pad.MidPlane = False

# --- Gear Teeth Generation ---
# We will create a sketch on the top face (Z = overallLength/2) to define the tooth profile
# Then we will use a Revolution feature to create the teeth around the Z axis.
# Note: To make the teeth "run along the overall length", we typically extrude the tooth profile 
# along the axis. However, the prompt asks for a "cylindrical gear body with external spur teeth running along the overall length".
# This implies the teeth are the full length of the cylinder.
# Strategy: 
# 1. Create a sketch on the top face (Z = L/2).
# 2. Draw the tooth profile (involute or simplified trapezoid) relative to the pitch circle.
# 3. Use a Revolution feature to rotate this profile 360 degrees. 
#    Since the profile is on the top face, revolving it creates a solid that is a "cap" of teeth.
#    To get teeth along the full length, we can either:
#    a) Pad the tooth profile along Z (but the profile is on the top face, so we need to offset it).
#    b) Create the tooth profile on a plane perpendicular to the axis (XY plane at Z=0) and Pad it along Z.
#    c) Create the tooth profile on the top face, and use a "Pad" with MidPlane=False starting from the top face downwards? No, that creates a hole or a cap.
#    
#    Let's go with the most robust parametric approach for a gear blank:
#    1. Create a sketch on the XY plane (Z=0).
#    2. Draw the tooth profile (the cross-section of a tooth).
#    3. Use a Revolution feature to create the full gear teeth volume.
#    4. Use a Pad feature to extend the base cylinder to the full length.
#    
#    Wait, if we revolve the tooth profile on Z=0, we get a gear that is 0 length (a disk).
#    We need the teeth to have length.
#    
#    Revised Strategy:
#    1. Create a sketch on the XY plane (Z=0).
#    2. Draw the tooth profile (cross section).
#    3. Use a Revolution feature to create the gear teeth. BUT, the Revolution feature in PartDesign creates a solid by rotating a profile. 
#       If the profile is 2D in XY, revolving it creates a 3D object with depth 0 unless we define a "Reference Axis" and the profile has depth? No.
#       Actually, PartDesign::Revolution rotates a 2D profile around an axis to create a 3D solid. The "depth" of the resulting solid is determined by the profile's extent perpendicular to the rotation plane? No.
#       The Revolution feature creates a solid by sweeping the profile along a circular path. The resulting solid has a volume.
#       If the profile is in the XY plane and we rotate around Z, the resulting solid is a ring/disk. It has no "length" along Z unless the profile itself has a Z-extent.
#       
#    Correct Approach for "Teeth running along length":
#    The teeth are generated by revolving a 2D profile that exists in the XZ plane (or YZ plane) around the Z axis? No, that would make a cone or a sphere.
#    To make a cylinder with teeth, the teeth are formed by revolving a profile that is in the XY plane? No, that makes a disk.
#    
#    Let's rethink the geometry.
#    A spur gear is a cylinder with teeth on the side.
#    The "tooth profile" is usually defined in a plane containing the axis of rotation (e.g., XZ plane).
#    If we take a profile in the XZ plane (representing one tooth) and revolve it around the Z axis, we get the full gear.
#    The profile in the XZ plane must look like a tooth cross-section.
#    The revolution will sweep this profile around the Z axis, creating the cylindrical teeth.
#    
#    So:
#    1. Create a sketch on the XZ plane (or a plane offset to Z=0, but oriented XZ).
#    2. Draw the tooth profile (Outer Diameter arc, Root Diameter arc, Flank lines).
#    3. Use PartDesign::Revolution to rotate this profile 360 degrees around the Z axis.
#    4. This creates the gear teeth solid.
#    5. We need to ensure the base cylinder is also created.
#    
#    Let's refine the "Tooth Profile" in XZ plane:
#    - Center of pitch circle is at (0, 0, 0).
#    - Pitch radius = pitchDiameter / 2.
#    - Outer radius = outerDiameter / 2.
#    - Root radius = (pitchDiameter - 2 * module) / 2. (Approximation for standard gear)
#    - The profile consists of:
#      - An arc at the top (Outer Diameter).
#      - An arc at the bottom (Root Diameter).
#      - Two straight lines (flanks) connecting them.
#      - The profile is symmetric around the X axis (in the XZ sketch).
#    
#    Steps:
#    1. Create a sketch on the XZ plane.
#    2. Add a circle for the Outer Diameter (centered at 0,0).
#    3. Add a circle for the Root Diameter (centered at 0,0).
#    4. Add lines to define the tooth flanks.
#       - The pressure angle is measured at the pitch circle.
#       - The flank lines should be tangent to the pitch circle? No, involute.
#       - For a simplified stock gear, we can approximate the flanks as straight lines tangent to the pitch circle at the pressure angle.
#       - Angle of flank relative to radial line = pressure angle.
#       - So, in the XZ plane, the line starts from the pitch circle and goes outwards at angle (90 - pressure_angle) from the X axis?
#       - Let's visualize: X is radial, Z is axial.
#       - At the pitch circle (radius R_p), the tangent makes an angle of pressure_angle with the radial line.
#       - So the line goes from (R_p, 0) upwards? No, the tooth is centered on the X axis.
#       - The tooth occupies the region between angle -theta and +theta.
#       - The flank line starts at the pitch circle and goes to the outer circle.
#       - The angle of the line with the radial vector (X axis) is the pressure angle.
#       - So the line equation in XZ: Z = tan(pressure_angle) * (X - R_p)? No.
#       - The line is tangent to the pitch circle. The point of tangency is at angle alpha = pressure_angle from the radial line?
#       - Actually, the standard definition: The pressure angle is the angle between the line of action and the tangent to the pitch circle.
#       - For the tooth profile in the radial plane: The flank is a straight line tangent to the base circle? No, that's involute.
#       - For a "stock" gear, we can approximate the flank as a straight line tangent to the pitch circle at the pressure angle.
#       - So, the line passes through (R_p * cos(alpha), R_p * sin(alpha)) and has a slope perpendicular to the radius? No.
#       - The line is tangent to the pitch circle. The point of tangency is at angle alpha from the X axis?
#       - Let's simplify: We want a tooth centered on the X axis.
#       - The flank line starts at the pitch circle. The angle between the radial line (X axis) and the flank line is the pressure angle.
#       - So the line goes from (R_p, 0) to (R_o, Z_max).
#       - The slope in the XZ plane: The line makes an angle of (90 - pressure_angle) with the Z axis?
#       - Let's use the property that the line is tangent to the pitch circle.
#       - The point of tangency is at angle `pressure_angle` from the X axis? No.
#       - The pressure angle is the angle between the line of action and the tangent to the pitch circle.
#       - In the radial plane, the flank is tangent to the pitch circle.
#       - The point of tangency is at an angle `pressure_angle` from the radial line? No.
#       - The line of action is tangent to the base circle.
#       - Let's just construct the line such that it is tangent to the pitch circle at an angle of `pressure_angle` relative to the radial line.
#       - Point of tangency: (R_p * cos(pressure_angle), R_p * sin(pressure_angle)).
#       - Normal vector at this point: (cos(pressure_angle), sin(pressure_angle)).
#       - Tangent vector: (-sin(pressure_angle), cos(pressure_angle)).
#       - The flank line is along the tangent vector? No, the flank line is the line of action?
#       - The flank line is the line of action.
#       - So the line passes through the point of tangency and has the direction of the tangent vector.
#       - Wait, the tooth flank is the line of action.
#       - So the line passes through (R_p * cos(alpha), R_p * sin(alpha)) and has direction (-sin(alpha), cos(alpha)).
#       - But we want the tooth to be symmetric around the X axis.
#       - So we need two lines: one for the left flank, one for the right flank.
#       - Right flank: Tangent to pitch circle at angle `+alpha`.
#       - Left flank: Tangent to pitch circle at angle `-alpha`.
#       - The tooth profile is the area between these two lines, bounded by the outer and root circles.
#    
#    Implementation details for the sketch:
#    - Origin at (0,0).
#    - Circle 1: Outer Diameter (R_o).
#    - Circle 2: Root Diameter (R_r).
#    - Line 1: Tangent to Circle 1 at angle `pressure_angle`.
#    - Line 2: Tangent to Circle 1 at angle `-pressure_angle`.
#    - We need to constrain the lines to be tangent to the pitch circle?
#      - Actually, the lines are tangent to the pitch circle.
#      - We can define the lines by their distance from the origin? No.
#      - We can define the lines by their angle of tangency.
#      - In FreeCAD Sketcher, we can use "Tangent" constraint between a line and a circle.
#      - We can also use "Angle" constraint.
#    
#    Let's build the sketch:
#    1. Add Circle (Outer).
#    2. Add Circle (Root).
#    3. Add Line (Right Flank).
#    4. Add Line (Left Flank).
#    5. Constraints:
#       - Coincident: Center of circles at (0,0).
#       - Radius: Outer = params.outerDiameter/2, Root = (params.pitchDiameter - 2*params.module)/2.
#       - Tangent: Right Flank tangent to Outer Circle? No, the flank is tangent to the Pitch Circle.
#       - We need to add the Pitch Circle to the sketch to define the tangency point?
#       - Or we can define the line by its angle.
#       - Let's add the Pitch Circle.
#       - Tangent: Right Flank tangent to Pitch Circle.
#       - Angle: The angle between the Pitch Circle radius to the tangent point and the X axis is `pressure_angle`.
#       - How to enforce this?
#       - We can use a "Point" on the Pitch Circle, then constrain the Line to pass through that point and be tangent to the Pitch Circle.
#       - Then constrain the Point's angle to `pressure_angle`.
#    
#    Simplified approach for the sketch:
#    - Add Pitch Circle.
#    - Add Point on Pitch Circle at angle `pressure_angle`.
#    - Add Line tangent to Pitch Circle at that Point.
#    - Add Line tangent to Pitch Circle at angle `-pressure_angle`.
#    - The tooth profile is the region bounded by these two lines and the Outer/Root circles.
#    - We need to close the profile.
#    - The profile is the area between the two lines, cut by the Outer and Root circles.
#    - We can use a "Trim" or just define the vertices.
#    - Actually, the Revolution feature will take the closed profile.
#    - The profile should be:
#      - Start at intersection of Right Flank and Outer Circle.
#      - Go along Outer Circle to intersection of Left Flank and Outer Circle.
#      - Go along Left Flank to intersection with Root Circle.
#      - Go along Root Circle to intersection with Right Flank.
#      - Close.
#    
#    This is complex to sketch manually.
#    Alternative: Use a "Pad" on the tooth profile? No, we need Revolution.
#    Alternative: Create the tooth profile as a simple shape (e.g., a trapezoid) and let the user know it's an approximation?
#    The prompt asks for "spur teeth". A simplified trapezoidal tooth is often acceptable for a "stock" gear unless specified as "involute".
#    Given the parameters (pressure angle), it implies involute geometry.
#    Let's try to construct the involute profile in the sketch.
#    
#    Sketch Construction Plan:
#    1. Origin (0,0).
#    2. Circle_Pitch (R_p).
#    3. Circle_Outer (R_o).
#    4. Circle_Root (R_r).
#    5. Point_Tangent_Right on Circle_Pitch at angle `pressure_angle`.
#    6. Line_Right: Tangent to Circle_Pitch at Point_Tangent_Right.
#    7. Point_Tangent_Left on Circle_Pitch at angle `-pressure_angle`.
#    8. Line_Left: Tangent to Circle_Pitch at Point_Tangent_Left.
#    9. Intersection_Right = Line_Right intersect Circle_Outer.
#    10. Intersection_Left = Line_Left intersect Circle_Outer.
#    11. Intersection_Root_Right = Line_Right intersect Circle_Root.
#    12. Intersection_Root_Left = Line_Left intersect Circle_Root.
#    13. Arc_Outer: From Intersection_Right to Intersection_Left (counter-clockwise? No, the tooth is between the lines).
#        - The tooth is centered on the X axis.
#        - The lines are at +alpha and -alpha.
#        - The arc is the part of the Outer Circle between the two intersection points that contains the X axis.
#    14. Arc_Root: From Intersection_Root_Left to Intersection_Root_Right (containing the X axis).
#    15. Line segments connecting the intersections
