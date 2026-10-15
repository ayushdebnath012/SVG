from pathlib import Path
import FreeCAD as App
import Part
from math import cos, pi, radians

# --- Configuration & Parameters ---
# Default values as per prompt, but defined as properties for editability
PARAMS = {
    "pressure_angle": 20.0, # degrees
    "gear_module": 2.0,     # mm
    "number_of_teeth": 30,
    "face_width": 20.0,     # mm
    "hub_diameter": 50.0,   # mm
    "hub_width": 10.0,      # mm
    "shaft_diameter": 10.0, # mm
    "overall_width": 30.0,  # mm
}

# --- Helper to create/attach parameters ---
def ensure_params(body, name):
    """Ensures a parameter exists in the body's VarSet or creates it."""
    try:
        obj = body.getObject(name)
        if obj:
            return obj
    except:
        pass
    
    # Create the VarSet if not present in body
    if not body.hasProperty("Parameters"):
        try:
            body.addProperty("App::Property", "Parameters")
        except:
            # In some versions, VarSet needs to be created separately
            varset = body.newObject("App::VarSet", "Parameters")
            return varset
    
    # If it's a VarSet object, we can't add properties to the object itself easily 
    # without it being the parent, but usually we add to the VarSet object.
    # Standard pattern: The VarSet is an object, we add properties to that object.
    # However, PartDesign Body usually has a 'Parameters' property that is a VarSet.
    # Let's try adding to the body's Parameters property directly if it exists, 
    # or create the VarSet object and link it.
    
    # Robust approach for this specific FreeCAD 1.1 context:
    # Check if body has a 'Parameters' object or property.
    # If it has a 'Parameters' property, we assume we can set it.
    # If it has a 'Parameters' object (VarSet), we add props there.
    
    if hasattr(body, "Parameters") and isinstance(body.Parameters, App._Base):
        # It's a property reference? No, usually 'Parameters' is a property name.
        # Let's rely on the standard App::VarSet object pattern.
        pass

    # Let's just create the VarSet object if we don't have a 'Parameters' object
    if not body.hasObject("Parameters"):
        varset = body.newObject("App::VarSet", "Parameters")
        # Add all params to this VarSet
        for key, val in PARAMS.items():
            try:
                varset.addProperty("App::Property", key)
                varset.setProperty(key, str(val))
            except:
                pass # Some might fail if duplicate
        return varset
    
    return None

# --- Script Execution ---

# 1. Create Document
doc = App.newDocument("GearBuilder")

# 2. Create Base Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# 3. Define Parameters Object
# We create a VarSet object inside the body to hold named parameters
param_obj = body.newObject("App::VarSet", "Parameters")
for key, val in PARAMS.items():
    try:
        param_obj.addProperty("App::Property", key)
        param_obj.setProperty(key, str(val))
    except Exception as e:
        print(f"Warning: Could not add param {key}: {e}")

# 4. Create Sketches and Features
# We will build the gear from the inside out:
# 1. Hub Cylinder (Pad)
# 2. Gear Teeth (Revolution)
# 3. Bore (Pocket)
# 4. Fillets

# --- Feature 1: Hub ---
# Sketch on XZ plane (Rotational axis is Z)
# Note: In FreeCAD, the default sketch plane is usually XY. 
# We need to attach to XZ to have the circle in the plane of rotation (Z axis).
# However, PartDesign SketchObject AttachmentSupport usually refers to the plane normal.
# Let's use the XY plane but orient the sketch such that the profile is in XZ? 
# No, easiest is to use the XZ plane or rotate the sketch.
# Let's use the XZ plane (Plane at Z axis, normal Y).

hub_sketch = body.newObject("Sketcher::SketchObject", "Hub_Sketch")
hub_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
hub_sketch.AttachmentSupport = (doc.getObject("XZ_Plane"), []) # Normal Y
hub_sketch.MapMode = "FlatFace"
hub_sketch.Constraints = []

# Define Hub Profile: Rectangle (width x height)
# Hub Width is along X (radius direction? No, hub width is axial Z).
# Hub Diameter is the circle size.
# Profile: Rectangle centered at (0,0). Width = hub_diameter, Height = hub_width.
# Since sketch is on XZ plane: X is radial, Z is axial.
r_hub = PARAMS["hub_diameter"] / 2.0
w_hub = PARAMS["hub_width"]

hub_sketch.addGeometry(Part.LineSegment(App.Vector(-r_hub, 0, 0), App.Vector(r_hub, 0, 0)))
hub_sketch.addGeometry(Part.LineSegment(App.Vector(r_hub, 0, 0), App.Vector(r_hub, 0, w_hub)))
hub_sketch.addGeometry(Part.LineSegment(App.Vector(r_hub, 0, w_hub), App.Vector(-r_hub, 0, w_hub)))
hub_sketch.addGeometry(Part.LineSegment(App.Vector(-r_hub, 0, w_hub), App.Vector(-r_hub, 0, 0)))

# Constraints: Horizontal, Vertical, Coincident to origin
hub_sketch.addConstraint(Sketcher.Constraint("Horz", 0, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Vert", 0, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 0, 0)) # Bottom-Left to origin? 
# Actually, simpler: Center the box.
# Let's just make the box start at origin for simplicity in constraints, then pad.
# But let's do centering to be safe.
hub_sketch.addConstraint(Sketcher.Constraint("Point", 0, 1, 0)) # Bottom-Left corner on axis
hub_sketch.addConstraint(Sketcher.Constraint("Point", 0, 1, 1)) # Top-Left corner on axis
hub_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Point", 0, 1, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Point", 1, 1, 1))

# Pad Hub
hub_pad = body.newObject("PartDesign::Pad", "Hub_Pad")
hub_pad.Profile = hub_sketch
hub_pad.Length = PARAMS["face_width"] # Extend through the whole gear width
hub_pad.Midplane = True

# --- Feature 2: Gear Teeth ---
# Sketch on XZ plane again
gear_sketch = body.newObject("Sketcher::SketchObject", "Gear_Sketch")
gear_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
gear_sketch.AttachmentSupport = (doc.getObject("XZ_Plane"), [])
gear_sketch.MapMode = "FlatFace"
gear_sketch.Constraints = []

# Gear Geometry Calculations
m = PARAMS["gear_module"]
z = PARAMS["number_of_teeth"]
alpha_deg = PARAMS["pressure_angle"]
alpha = radians(alpha_deg)

# ISO 21771 / Standard Spur Gear Dimensions
# Addendum = m
# Dedendum = 1.25 * m
# Whole Depth = 2.25 * m
# Pitch Diameter = m * z
# Outer Diameter = m * (z + 2)
# Root Diameter = m * (z - 2.5)
# Base Diameter = m * z * cos(alpha)
# Circular Pitch = pi * m
# Tooth Thickness = Circular Pitch / 2

d_pitch = m * z
d_outer = m * (z + 2)
d_root = m * (z - 2.5)
d_base = m * z * cos(alpha)

# Tooth Geometry Generation
# We need to generate the involute profile.
# Start angle for tooth: (Tooth Thickness / 2) / Radius?
# No, we generate the arc.
# Number of segments for smooth curve
n_segments = 100
radius_pitch = d_pitch / 2.0

# Function to generate points on involute
def get_involute_points(r_base, r_current, theta_deg, steps=100):
    theta_rad = radians(theta_deg)
    # Involute formula: r = r_base * sqrt(1 + theta^2) (where theta is unwrapping angle in rads)
    # But we need to map theta_deg to the actual unwrapping angle.
    # This is complex to do precisely without a solver. 
    # Alternative: Use FreeCAD's built-in gear generation logic? No, must write script.
    # Simplified approach: Generate a polyline approximating the involute.
    
    # Let's use a standard parametric generation for the tooth profile
    # We define the points relative to the center.
    pass

# Let's use a robust method: Generate points using the definition of involute.
# Angle of unwinding phi.
# r = r_base * sqrt(1 + phi^2)
# theta_inv = phi - atan(phi)
# Coordinates:
# x = r * cos(theta_inv)
# y = r * sin(theta_inv)
# where theta_inv is the angle from the X axis.

def generate_tooth_profile(r_base, r_start, r_end, steps=20):
    """Generates a list of Points for a single tooth half (flank)."""
    # We need the range of phi (unwrapping angle) corresponding to r_start and r_end.
    # phi = sqrt((r/r_base)^2 - 1)
    
    phi_start = (r_start/r_base)**2 - 1
    phi_start = phi_start**0.5 if phi_start > 0 else 0
    
    phi_end = (r_end/r_base)**2 - 1
    phi_end = phi_end**0.5 if phi_end > 0 else 0
    
    points = []
    for i in range(steps+1):
        t = i / steps
        phi = phi_start + (phi_end - phi_start) * t
        
        if phi < 0: phi = 0
        
        # Radius at this point
        r = r_base * (1 + phi**2)**0.5
        
        # Angle of the point
        theta = phi - (phi / (1 + phi**2)**0.5) # atan(phi) approximation
        
        x = r * cos(theta)
        y = r * sin(theta)
        points.append(App.Vector(x, y, 0))
    return points

# We need to place teeth around the circle.
# Tooth thickness at pitch circle = pi * m / 2.
# Tooth spacing angle = 360 / z.
# Start angle of a tooth (root to root)?
# Center of tooth is at angle 0.
# Half tooth width at pitch circle: w_half = (pi * m / 2) / (m * z) * 180? No.
# Arc length = angle * radius.
# Angle of half tooth at pitch circle = (pi * m / 2) / (d_pitch / 2) = pi / z.
# So the tooth spans from -pi/z to +pi/z centered at 0? No, that's the space.
# The tooth occupies the space.
# Let's define the start of the tooth profile.
# The tooth starts at the root radius.
# We need to find the angle at the root where the tooth starts.
# But usually we generate the profile from the base circle outwards.
# Let's generate the flank from Base Circle to Root Circle.
# Then we generate the addendum circle part? 
# Usually the tooth is continuous from root to outer.
# We need the angle offset.
# Angle of tooth half-width at pitch circle: alpha_half = (pi / z) / 2.
# Wait, total pitch angle = 2*pi/z. Half pitch angle = pi/z.
# The tooth center is at 0. The tooth edges are at +/- pi/z? No.
# The pitch line is the line of contact.
# The space between teeth is also pi/z.
# So the tooth occupies [-pi/(2*z), +pi/(2*z)]? No.
# Total angle = 2pi. Teeth = z. Angle per tooth = 2pi/z.
# Tooth occupies the middle? No, teeth are solid.
# Let's say tooth 1 center is at 0. The tooth extends from -pi/z to +pi/z?
# No, that would be 2*pi/z total width. Yes.
# So the tooth flank goes from Angle = -pi/z to Angle = +pi/z?
# Wait, the root is inside. The root diameter is smaller.
# The tooth exists from r_root to r_outer.
# We need to calculate the starting angle at the root.
# Let's use a simpler approximation: 
# Generate the involute curve from Base to Root and Base to Outer.
# Then rotate these curves by (tooth_angle / 2) + k * (tooth_angle).

# Let's calculate the angular positions.
# Tooth Angle = 360 / z
# Half Tooth Angle = 180 / z
# We will generate the profile for one tooth centered at 0 degrees.
# The profile goes from Root Radius to Outer Radius.
# But the involute doesn't start at the root radius usually, it starts at Base.
# We need to connect the involute to the fillet at the root? 
# The prompt asks for a spur gear. Standard gear has a root fillet.
# We will create the tooth profile as a closed loop or use the Revolve feature with a specific sketch.
# Sketch: Generate the profile of ONE tooth (from outer to root, then back).
# Then Revolve by 360 with 30 occurrences? Or generate full profile and revolve once?
# Better: Generate ONE tooth profile in the sketch, then use Polar Pattern on the Revolve?
# No, Revolve creates a solid. If we pattern the Revolve, we get duplicate holes/cylinders.
# We want teeth.
# Strategy:
# 1. Create a sketch with ONE TOOTH profile (closed shape from outer to root and back).
# 2. Create a Revolve feature of this tooth.
# 3. Use a Polar Pattern on the Pad? No, Revolve is a single feature.
# Alternative Strategy:
# 1. Create a sketch with the FULL GEAR profile (all teeth)? Too many constraints.
# 2. Create a sketch with ONE tooth.
# 3. Use a Polar Pattern of the sketch? No, we need to revolve.
# 4. Correct Approach:
#    - Create a sketch with ONE tooth profile.
#    - Create a Pad from this sketch.
#    - Use a Polar Pattern on the Pad to create the teeth.
#    - BUT, the hub is already there. The Pad will create a cylinder.
#    - We need to subtract the void between teeth?
#    - Or: Create the Hub, then create the Teeth as a separate solid (Pad of 1 tooth), then Polar Pattern the Teeth Pad, then Unite with Hub.
#    - Then Pocket the bore.
#    - Then Fillet.

# Revised Plan:
# 1. Pad Hub (Cylinder).
# 2. Pad Teeth (Single tooth profile).
# 3. Polar Pattern the Teeth Pad.
# 4. Unite Hub and Teeth (optional, but they should be one solid if we union, or just keep separate and boolean later? 
#    PartDesign allows multiple solids in one body, but prompt says "exactly one solid". So we must Union them).
# 5. Pocket Bore.
# 6. Fillet Roots.

# Let's refine the Single Tooth Sketch.
# The tooth profile is symmetric.
# We draw from Outer Radius down to Root Radius on the right side, then close at the bottom (root circle), then up the left side?
# No, the root is a circle. The tooth sits on top of the root circle.
# Profile:
# 1. Line from (0, Outer/2) to (0, Root/2) ? No.
# 2. Involute flank from Base to Root.
# 3. Involute flank from Base to Outer.
# 4. Line connecting Outer and Base? No, Outer is a circle.
# 5. We need the profile of the TOOTH ONLY.
#    - Top: Line from Outer/2 to Outer/2? No, the tooth top is a line (or slightly curved).
#    - Sides: Involute curves.
#    - Bottom: The root circle arc? No, the tooth ends at the root circle.
#    So the profile is: 
#      (0, Outer/2) -> Involute Up -> (0, Outer/2) ?? No.
#      (0, Outer/2) -> Involute Out -> (Angle, Outer/2) -> Line -> (Angle, Root/2) -> Involute In -> (
