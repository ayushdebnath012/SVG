import FreeCAD as App
import Part
from pathlib import Path
import math

# Create document
doc = App.newDocument("SpurGearStock")

# --- Parameters ---
# Derived from prompt requirements
P = doc.addObject("App::VarSet", "Parameters")
P.addProperty("App::PropertyInteger", "number_of_teeth", "Parameters", "Total count of teeth")
P.addProperty("App::PropertyFloat", "pressure_angle", "Parameters", "Pressure angle in degrees")
P.addProperty("App::PropertyFloat", "diametral_pitch", "Parameters", "Diametral pitch (1/in)")
P.addProperty("App::PropertyFloat", "gear_module", "Parameters", "Module in mm")
P.addProperty("App::PropertyLength", "pitch_diameter", "Parameters", "Reference diameter")
P.addProperty("App::PropertyLength", "outer_diameter", "Parameters", "Outer diameter")
P.addProperty("App::PropertyLength", "overall_length", "Parameters", "Axial length")

# Set values based on prompt
P.number_of_teeth = 24
P.pressure_angle = 20.0
P.diametral_pitch = 12.0
P.gear_module = 2.1166666667 # 25.4 / 12
P.pitch_diameter = 50.8      # 2 * 25.4
P.outer_diameter = 55.118    # 2.17 * 25.4
P.overall_length = 304.8     # 1 ft * 12 * 25.4

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Shaft (The blank) ---
# We will create a pad on the XY plane to form the main cylinder.
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Constraints = []
base_sketch.Geometry = [
    Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), P.pitch_diameter.Value / 2)
]
base_sketch.Constraints.append(Sketcher.Constraint("Radius", 0, 0, P.pitch_diameter.Value / 2))
base_sketch.Constraints.append(Sketcher.Constraint("Fixed", 0, 2)) # Fix center to origin Z

base_pad = body.newObject("PartDesign::Pad", "BasePad")
base_pad.Profile = base_sketch
base_pad.Length = P.overall_length.Value
base_pad.Type = "Solid"

# --- Tooth Generation ---
# Strategy: Create a single tooth profile sketch on the XZ plane (using Y as axis of revolution).
# The tooth profile will be generated parametrically relative to the gear parameters.
# We use the Pitch Diameter to define the reference circle.
# The addendum circle is Outer Diameter / 2.

# Define base circle, addendum, dedendum logic implicitly via sketch geometry
# Pitch Radius
r_pitch = P.pitch_diameter.Value / 2.0
# Outer Radius (Addendum is added to pitch radius)
r_outer = P.outer_diameter.Value / 2.0
# Pressure Angle
pa_rad = math.radians(P.pressure_angle)
# Module
m = P.gear_module.Value

# Tooth geometry calculations for a standard full-depth gear (simplified for stock)
# For a spur gear stock, we often just extrude the involute profile between the base circle and the outer circle.
# However, to keep it simple and robust within PartDesign, we will draw the profile on the XZ plane.
# The gear rotates around the Y axis.
# The profile is symmetric around the X axis (in the sketch plane).

# We need to calculate the involute curve points.
# Base circle radius: rb = r_pitch * cos(pa)
rb = r_pitch * math.cos(pa_rad)

# Function to calculate involute point (r, theta)
# theta = sqrt((r/rb)^2 - 1)
# x = rb * (cos(theta) + theta*sin(theta))
# z = rb * (sin(theta) - theta*cos(theta))
# Note: In our sketch on XZ plane, X is the radius direction, Z is the tangential direction.
# The gear axis is Y. So we revolve around Y.

def get_involute_points(r_start, r_end, num_points=50):
    points = []
    rb_base = rb
    for i in range(num_points):
        # Interpolate radius
        t = i / (num_points - 1)
        r = r_start + (r_end - r_start) * t
        
        if r <= rb_base:
            continue
            
        theta = math.sqrt((r/rb_base)**2 - 1)
        
        # Involute formulas
        # x = rb * (cos(theta) + theta*sin(theta))
        # z = rb * (sin(theta) - theta*cos(theta))
        x = rb_base * (math.cos(theta) + theta * math.sin(theta))
        z = rb_base * (math.sin(theta) - theta * math.cos(theta))
        
        points.append(App.Vector(x, 0, z))
    return points

# Create Tooth Sketch
tooth_sketch = body.newObject("Sketcher::SketchObject", "ToothSketch")
tooth_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
# Orientation: XZ plane. Y is the normal.
tooth_sketch.Placement.Rotation = App.Rotation((0, 1, 0)) # Rotate 90 deg around X to align normal to Y? 
# Actually, default Sketcher object is on XY plane (normal Z). 
# We want to sketch in XZ plane (normal Y). So we rotate 90 deg around X axis.
tooth_sketch.Placement = App.Placement(App.Rotation(App.Vector(1, 0, 0), math.pi/2))

# Construct the profile:
# 1. Start at Outer Circle (top of tooth)
# 2. Go down the involute side (right side) to Base Circle
# 3. Go along Base Circle (optional, but good for solid fill) or jump to other side
# 4. Go up the involute side (left side) back to Outer Circle
# 5. Close at top

# Let's generate the profile points
# Top point: r_outer, theta=0
p_top = App.Vector(r_outer, 0, 0)

# Right Involute (theta > 0)
p_inv_right = get_involute_points(r_outer, rb, 20)
# Note: get_involute_points generates from r_start to r_end.
# We want outer to base.
# The function above generates points from r_start to r_end.
# Let's invert the list to go from Outer to Base.
inv_curve_right = [App.Vector(x, 0, z) for x, y, z in zip([p[i].x for p in p_inv_right], [p[i].y for p in p_inv_right], [p[i].z for p in p_inv_right])]
# Wait, my get_involute_points returns App.Vectors. Let's re-verify.
# The function returns a list of App.Vector.
# I need to construct the path.

# Path construction:
# Point 0: Top (r_outer, 0, 0)
# Path 1: Curve from Top to Base Circle (Right side) -> Involute from r_outer to rb
# Path 2: Line along Base Circle? Or just connect to left side? 
# Standard gear stock usually includes the root circle (dedendum). 
# The prompt asks for "spur gear stock". Usually, this implies the full blank including the space between teeth.
# To make it a solid "stock", we can either:
# A) Create the tooth profile and subtract it from a cylinder.
# B) Create the tooth profile and pad it, but ensure the valleys are filled.
# Option B is harder parametrically without complex boolean logic on the profile itself.
# Option A is cleaner: 
# 1. Create a cylinder of OD and Length (BasePad already does this).
# 2. Create a tooth profile on XZ plane.
# 3. Pad the tooth profile to the length of the gear.
# 4. Pattern the tooth pad.
# 5. The result is a solid gear.

# Let's refine the Tooth Profile sketch for the "Stock" concept.
# Actually, if we pad the tooth profile, we get a single tooth. We pattern it.
# The gaps will be empty. The body will be a series of teeth. 
# Does "gear stock" imply the material between teeth is present? 
# Usually "gear stock" or "gear blank" means the whole cylinder.
# But the description says "cylindrical gear body with an external ring of involute teeth ... forming a long gear blank".
# This implies the final object should be the teeth themselves, or the cylinder with teeth cut?
# "forming a long gear blank" suggests the final output is the gear itself (the teeth), not the blank with holes.
# If it were a blank with holes, it would be "gear with slots".
# I will generate the gear as a set of teeth.

# Re-evaluating the profile for the tooth pad:
# It needs to be closed.
# Points:
# 1. Top (r_outer, 0, 0)
# 2. Involute Right (r_outer -> rb)
# 3. Root? 
# For a gear stock, we usually go down to a root circle.
# Root diameter = m * (z - 2.25) approx.
# r_root = m * (number_of_teeth - 2.25) / 2
r_root = m * (P.number_of_teeth - 2.25) / 2.0

# If r_root < rb, we stop at rb (undercut). If not, we go to r_root.
# Let's assume standard gear.
if r_root > rb:
    # Go to root
    p_root = App.Vector(r_root, 0, 0) # Simplification: straight down? 
    # Real gear has fillet at root. Let's approximate with straight lines or a simplified curve.
    # For a script, a straight line down to root and up is risky for pressure angle, but acceptable for "stock".
    # Better: Involute goes to base. Then straight line to root? 
    # Let's try: Involute (Outer->Base), then straight line (Base->Root), then straight line back (Root->Base), then Involute (Base->Outer).
    # This creates a shape that is thick at the base.
    
    # Path:
    # Start Top
    # Curve to Base (Right)
    # Line to Root (Right)
    # Line to Root (Left)
    # Line to Base (Left)
    # Curve to Top (Left - actually we are at Top already via symmetry)
    # Wait, we need to close the loop.
    
    # Let's build the list of segments:
    profile_geom = []
    
    # 1. Top to Right Base (Involute)
    points_right = get_involute_points(r_outer, rb, 20)
    # We need to reverse this to go from Outer to Base? 
    # get_involute_points(start, end) goes start->end.
    # So p[0] is r_outer, p[-1] is rb.
    # Correct.
    profile_geom.extend(points_right)
    
    # 2. Right Base to Right Root (Vertical line in sketch XZ? No, Z is tangent).
    # At base circle, theta is approx 0? No, theta depends on r.
    # At r=rb, theta=0. So Z=0.
    # At r=r_root, we need a new theta? No, below base circle is not involute.
    # It's a straight radial line or a fillet.
    # Let's do a straight line from (rb, 0) to (r_root, 0) in the XZ plane? 
    # That would mean the tooth has a flat bottom.
    # Let's just connect (rb, 0) to (r_root, 0) and back.
    # Actually, to make it a valid closed shape for a solid:
    # We need to go from Right Base to Right Root, then to Left Root, then to Left Base, then to Left Outer, then to Top.
    
    # Segment: Right Base (rb, 0, 0) to Right Root (r_root, 0, 0)? 
    # If we assume the tooth root is at a smaller radius, and we just connect straight lines.
    
    # Let's construct the vertices for the sketcher:
    v_list = []
    
    # Top
    v_list.append(p_top)
    
    # Right Involute
    for p in points_right:
        v_list.append(p)
    
    # Right Base to Right Root (Straight line inwards)
    # Note: points_right[-1] is (rb, 0, 0).
    v_list.append(App.Vector(r_root, 0, 0))
    
    # Right Root to Left Root (Line across diameter)
    # This creates a "V" shape at the root? No, just a line segment.
    v_list.append(App.Vector(-r_root, 0, 0))
    
    # Left Root to Left Base (Outwards)
    v_list.append(App.Vector(-rb, 0, 0))
    
    # Left Base to Left Outer (Involute backwards)
    # We need points from rb to r_outer.
    # Get them and reverse.
    points_left = get_involute_points(rb, r_outer, 20)
    # points_left[0] is rb, points_left[-1] is r_outer.
    # We want to go from -rb to -r_outer.
    # So we take points_left, negate X and Z.
    for p in reversed(points_left):
        v_list.append(App.Vector(-p.x, 0, -p.z))
    
    # Close the loop?
    # The last point is (-r_outer, 0, 0). The first is (r_outer, 0, 0).
    # We need to connect them via the Top?
    # My list goes: Top -> RightOuter -> RightBase -> RightRoot -> LeftRoot -> LeftBase -> LeftOuter -> (-r_outer, 0, 0).
    # Missing the connection from LeftOuter back to Top.
    # The Top is at (r_outer, 0, 0).
    # The LeftOuter is at (-r_outer, 0, 0).
    # We need to go from LeftOuter to Top.
    # The Top is actually on the X axis.
    # The profile is symmetric around Z=0.
    # So the path should be: Top -> RightInv -> RightBase -> RightRoot -> LeftRoot -> LeftBase -> LeftInv -> Top.
    # My current list ends at LeftOuter. I need to add the connection to Top.
    # But Top is (r_outer, 0, 0). LeftOuter is (-r_outer, 0, 0).
    # They are not connected directly.
    # I need to add a point at Top at the end? 
    # Sketcher closes the loop automatically if the last point is close to the first.
    # I should add the Top point again at the end? No, that creates a zero length line.
    # I should add a segment from LeftOuter to Top.
    # But the shape is symmetric.
    # Let's reconstruct the list to be a continuous chain ending near the start.
    
    # Correct Chain:
    # 1. Top (r_outer, 0, 0)
    # 2. Right Involute (r_outer -> rb)
    # 3. Line (rb, 0, 0) -> (r_root, 0, 0)
    # 4. Line (r_root, 0, 0) -> (-r_root, 0, 0)
    # 5. Line (-r_root, 0, 0) -> (-rb, 0, 0)
    # 6. Left Involute (-rb -> -r_outer) -> This is just negating the Right Involute points.
    # 7. Line (-r_outer, 0, 0) -> (r_outer, 0, 0) ?? No, that cuts through the tooth.
    # The tooth is the shape we are defining.
    # The "Top" is the peak. The "Left Outer" is the left side of the peak.
    # Wait, the peak is at (r_outer, 0, 0).
    # The left side of the peak is also at roughly (-r_outer, 0, 0)? 
    # No. The involute starts at the base circle.
    # The tooth profile is symmetric about the X-axis (in the sketch plane).
    # So the Top is at (r_outer, 0, 0).
    # The Right side goes down to (rb, 0, 0).
    # The Left side goes up to (r_outer, 0, 0).
    # So the profile is: Top -> RightInv -> RightRoot -> LeftRoot -> LeftInv -> Top.
    
    # Let's rebuild v_list correctly.
    v_list = []
    
    # Top
    v_list.append(App.Vector(r_outer, 0, 0))
    
    # Right Involute (Outer to Base)
    for p in points_right:
        v_list.append(p)
    
    # Right Base to Right Root
    v_list.append(App.Vector(r_root, 0, 0))
    
    # Right Root to Left Root
    v_list.append(App.Vector(-r_root, 0, 0))
    
    # Left Root to Left Base
    v_list.append(App.Vector(-rb, 0, 0))
    
    # Left Involute (Base to Outer)
    # We want points from rb to r_outer, then
