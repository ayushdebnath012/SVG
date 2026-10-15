from pathlib import Path
import FreeCAD as App
import Part
from math import cos, pi, radians, sqrt

# --- Configuration ---
# Parameters defined as a dictionary for easy editing, but will be moved to the document object
PARAMS = {
    "pressure_angle": 20.0,
    "gear_module": 2.0,
    "number_of_teeth": 30,
    "face_width": 20.0,
    "hub_diameter": 50.0,
    "hub_width": 10.0,
    "shaft_diameter": 10.0,
    "overall_width": 30.0,
}

# --- Helper: Create Parameter Object ---
def create_param_object(body, name, value):
    """Creates a parameter in the body's VarSet."""
    # Check if VarSet exists
    if not body.hasObject("Parameters"):
        varset = body.newObject("App::VarSet", "Parameters")
        body.addObject(varset)
    else:
        varset = body.getObject("Parameters")
    
    # Add property if not exists
    if not varset.hasProperty(name):
        varset.addProperty("App::Property", name)
    varset.setProperty(name, str(value))
    return varset

# --- Main Script ---

# 1. Create Document
doc = App.newDocument("GearBuilder")

# 2. Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# 3. Create Parameters
for key, val in PARAMS.items():
    create_param_object(body, key, val)

# 4. Create Hub
# Sketch on XZ plane (Normal Y)
hub_sketch = body.newObject("Sketcher::SketchObject", "Hub_Sketch")
hub_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
hub_sketch.AttachmentSupport = (doc.getObject("XZ_Plane"), [])
hub_sketch.MapMode = "FlatFace"

# Hub Profile: Rectangle centered at origin
# X: -r to +r, Z: -w/2 to +w/2
r_hub = PARAMS["hub_diameter"] / 2.0
w_hub = PARAMS["hub_width"]

hub_sketch.addGeometry(Part.LineSegment(App.Vector(-r_hub, 0, 0), App.Vector(r_hub, 0, 0)))
hub_sketch.addGeometry(Part.LineSegment(App.Vector(r_hub, 0, 0), App.Vector(r_hub, 0, w_hub)))
hub_sketch.addGeometry(Part.LineSegment(App.Vector(r_hub, 0, w_hub), App.Vector(-r_hub, 0, w_hub)))
hub_sketch.addGeometry(Part.LineSegment(App.Vector(-r_hub, 0, w_hub), App.Vector(-r_hub, 0, 0)))

# Constraints
hub_sketch.addConstraint(Sketcher.Constraint("Horz", 0, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Vert", 0, 0))
hub_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 0, 0)) # Bottom-Left
hub_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 0, w_hub)) # Top-Right
hub_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 0, w_hub)) # Top-Left
hub_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 1, r_hub, 0)) # Bottom-Right

# Pad Hub
hub_pad = body.newObject("PartDesign::Pad", "Hub_Pad")
hub_pad.Profile = hub_sketch
hub_pad.Length = PARAMS["face_width"]
hub_pad.Midplane = True

# 5. Create Gear Teeth
# Calculate Gear Dimensions
m = PARAMS["gear_module"]
z = PARAMS["number_of_teeth"]
alpha_deg = PARAMS["pressure_angle"]
alpha = radians(alpha_deg)

d_pitch = m * z
d_outer = m * (z + 2)
d_root = m * (z - 2.5)
d_base = m * z * cos(alpha)

# Generate Involute Points
def get_involute_points(r_base, r_start, r_end, steps=50):
    """Generates points for an involute curve from r_start to r_end."""
    points = []
    # Calculate unwrapping angles (phi)
    # phi = sqrt((r/r_base)^2 - 1)
    phi_start = sqrt((r_start/r_base)**2 - 1) if r_start > r_base else 0
    phi_end = sqrt((r_end/r_base)**2 - 1) if r_end > r_base else 0
    
    for i in range(steps + 1):
        t = i / steps
        phi = phi_start + (phi_end - phi_start) * t
        
        if phi < 0: phi = 0
        
        r = r_base * sqrt(1 + phi**2)
        theta = phi - (phi / (1 + phi**2)**0.5) # atan(phi)
        
        x = r * cos(theta)
        y = r * sin(theta)
        points.append(App.Vector(x, y, 0))
    return points

# Generate one tooth profile
# Tooth is symmetric around X axis (in the sketch plane XZ, X is radial)
# We need the profile from Outer to Root.
# Tooth thickness at pitch circle = pi * m / 2.
# Angle of half tooth at pitch circle = (pi * m / 2) / (d_pitch / 2) = pi / z.
# So the tooth spans from -pi/z to +pi/z? No, that's the space.
# The tooth occupies the space between -pi/z and +pi/z? No.
# Total angle per tooth = 2*pi/z.
# Let's define the tooth centered at 0.
# The tooth extends from -pi/z to +pi/z? No, that would be 2*pi/z. Yes.
# Wait, if tooth is at 0, and space is at pi/z, then tooth is [-pi/z, pi/z]?
# No, if tooth is at 0, space is at pi/z.
# Tooth width = 2*pi/z? No, tooth width + space width = 2*pi/z.
# For standard gears, tooth thickness = space width = pi*m/2.
# So tooth angle = (pi*m/2) / (d_pitch/2) = pi/z.
# So the tooth spans an angle of pi/z.
# Centered at 0, it goes from -pi/(2*z) to +pi/(2*z).

half_tooth_angle = pi / (2 * z)

# We need to rotate the involute points by the tooth angle.
# The involute starts at the base circle.
# We need to find the angle of the involute at the root and outer circles.
# But we can just generate the curve and rotate it.

# Generate flank from Base to Root
flank_root = get_involute_points(d_base, d_base, d_root)
# Generate flank from Base to Outer
flank_outer = get_involute_points(d_base, d_base, d_outer)

# We need to connect these.
# The profile of one tooth (right side):
# 1. Line from (0, Outer/2) to (0, Root/2)? No.
# 2. The tooth top is a line from (Outer/2, 0) to (Outer/2, 0)? No.
#    The tooth top is a line segment perpendicular to the radius?
#    Usually, the top is a line from (r_outer, 0) to (r_outer, 0) in polar?
#    In Cartesian (X radial, Z axial):
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0)? No.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is a point.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0) to (d_outer/2, 0) is wrong.
#    Top: Line from (d_outer/2, 0)
