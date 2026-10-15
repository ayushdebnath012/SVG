import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameters ---
# Gear Geometry
pressure_angle_deg = 20.0
gear_module = 1.0
number_of_teeth = 24
face_width = 10.0
hub_diameter = 20.0
hub_width = 10.0
shaft_diameter = 8.0
overall_width = 20.0

# Calculated Dimensions (ISO 54 / DIN 867)
pressure_angle = math.radians(pressure_angle_deg)
pitch_diameter = gear_module * number_of_teeth
outer_diameter = pitch_diameter + 2 * gear_module
root_diameter = pitch_diameter - 2 * (1.25 * gear_module)
base_diameter = pitch_diameter * math.cos(pressure_angle)
circular_pitch = math.pi * gear_module
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
bore_diameter = shaft_diameter

# --- Document Setup ---
doc = App.newDocument("Gear")
doc.Label = "Spur Gear"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We use a VarSet to store named parameters that drive the geometry
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Diameter")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "Pressure Angle")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")

# Set initial values
params.gear_module = gear_module
params.face_width = face_width
params.hub_diameter = hub_diameter
params.hub_width = hub_width
params.shaft_diameter = shaft_diameter
params.overall_width = overall_width
params.pressure_angle_deg = pressure_angle_deg
params.number_of_teeth = number_of_teeth

# --- Sketch 1: Gear Tooth Profile (Involute) ---
# We create a sketch on the XY plane. The profile will be defined relative to the pitch circle.
# The gear is built by revolving this profile 360 degrees.
sketch_gear = body.newObject("Sketcher::SketchObject", "Sketch_GearProfile")
sketch_gear.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_gear.ConstrainToCurrentPlacement = True
sketch_gear.MapMode = "FlatFace"
sketch_gear.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# We will define the profile using lines and arcs.
# Coordinate system: Origin at center of gear.
# We define the profile for one tooth (or a segment) and use a pattern.
# However, to keep it simple and robust in PartDesign, we often define the full involute curve 
# or a simplified polygonal approximation if exact involute generation via sketch constraints is tricky.
# Given the requirement for "editable features", we will construct the involute using a series of 
# small line segments or a precise arc/line combination.
# 
# Strategy: Define the involute curve mathematically using a loop of points and add them as geometry.
# Then use a Polar Pattern to create the teeth.

def get_involute_points(num_points=100, r_base=None):
    """Generates points on an involute of a circle."""
    if r_base is None:
        r_base = base_diameter / 2.0
    points = []
    for i in range(num_points):
        theta = 2 * math.pi * i / num_points
        # Involute equations:
        # x = r_base * (cos(t) + t*sin(t))
        # y = r_base * (sin(t) - t*cos(t))
        # where t is the unwrapping angle. 
        # For a gear tooth, we usually start from the base circle.
        # Let's generate a continuous curve from t=0 to t=2*pi (full circle)
        # and then we will slice it.
        t = theta
        x = r_base * (math.cos(t) + t * math.sin(t))
        y = r_base * (math.sin(t) - t * math.cos(t))
        points.append(App.Vector(x, y, 0))
    return points

# Generate the full involute curve (one full rotation)
# We need points from the base circle outwards.
# The involute starts at the base circle (t=0) and goes out.
# We need enough points to cover the tooth height.
# Max radius is outer_diameter/2.
# t_max = sqrt((r_outer/r_base)^2 - 1)
r_base_val = base_diameter / 2.0
r_outer_val = outer_diameter / 2.0
t_max = math.sqrt((r_outer_val / r_base_val)**2 - 1)

# Generate points from t=0 to t=t_max
involute_points = []
steps = 200
for i in range(steps + 1):
    t = (t_max / steps) * i
    x = r_base_val * (math.cos(t) + t * math.sin(t))
    y = r_base_val * (math.sin(t) - t * math.cos(t))
    involute_points.append(App.Vector(x, y, 0))

# We need to construct the tooth profile.
# A standard gear tooth consists of:
# 1. Addendum circle arc (top)
# 2. Dedendum circle arc (bottom)
# 3. Flank (involute)
# 4. Root fillet (optional, but standard gears have a root radius)
# 
# To make this editable and simple in a sketch:
# We will define the profile of ONE tooth and then use a Polar Pattern.
# Tooth pitch angle = 360 / number_of_teeth
pitch_angle = 360.0 / params.number_of_teeth

# Let's define the profile of a single tooth centered at angle 0.
# We need to find the intersection of the involute with the addendum and dedendum circles.
# Actually, the involute naturally intersects these circles.
# We can just take the segment of the involute between the addendum and dedendum radii.
# But we also need the root fillet and the tip fillet.
# For simplicity and robustness in FreeCAD sketches, we will approximate the root and tip with arcs 
# and use the involute for the flanks.

# Calculate angles for intersections
# r = r_base * sqrt(1 + t^2) => t = sqrt((r/r_base)^2 - 1)
t_add = math.sqrt((r_outer_val / r_base_val)**2 - 1)
t_ded = math.sqrt(((root_diameter/2) / r_base_val)**2 - 1)

# Points on involute at addendum and dedendum
p_add = App.Vector(r_base_val * (math.cos(t_add) + t_add * math.sin(t_add)), 
                   r_base_val * (math.sin(t_add) - t_add * math.cos(t_add)), 0)
p_ded = App.Vector(r_base_val * (math.cos(t_ded) + t_ded * math.sin(t_ded)), 
                   r_base_val * (math.sin(t_ded) - t_ded * math.cos(t_ded)), 0)

# We need to close the loop for the sketch.
# The profile of one tooth (from -pitch/2 to +pitch/2):
# 1. Start at p_ded (rotated to center)
# 2. Go along involute to p_add (rotated to center)
# 3. Arc at outer_diameter/2 to the next flank start? 
#    Actually, standard gear drawing:
#    - Top: Arc of outer circle between the two addendum points.
#    - Bottom: Arc of root circle between the two dedendum points (with fillet).
#    - Sides: Involute.
#
# Let's define the vertices for the sketch polygon/curve.
# We will create a sketch that contains the profile of ONE tooth, then pattern it.
# The tooth is symmetric around the X-axis (if we align it that way).
# Let's align the tooth center to the X-axis.
# Angle of p_add relative to base circle tangent?
# The involute parameter t is the angle of the tangent.
# The position angle phi = t + alpha, where alpha is pressure angle? No.
# Position angle phi = t + atan(t).
# Let's calculate the absolute angles of p_add and p_ded.
# phi = atan2(y, x)
phi_add = math.atan2(p_add.Y, p_add.X)
phi_ded = math.atan2(p_ded.Y, p_ded.X)

# We want the tooth centered at 0. So we rotate these points by -phi_add/2? 
# No, the tooth is between phi_add and -phi_add? 
# The involute starts at base circle. The tooth flanks are symmetric.
# The angle of the tooth center line is the average of the angles of the two flanks at the pitch circle?
# Let's just generate the points for the left flank and right flank.
# Right flank: from p_ded to p_add.
# Left flank: from p_add to p_ded (symmetric).
# Actually, the involute is continuous. We just need to select the segment.
# The segment from t_ded to t_add corresponds to the tooth flank.
# We need to rotate this segment so it is centered.
# The angle of the segment at the pitch circle (t_pitch) is the center.
# t_pitch = sqrt((pitch_diameter/2 / r_base_val)**2 - 1)
t_pitch = math.sqrt(((pitch_diameter/2) / r_base_val)**2 - 1)
phi_pitch = math.atan2(
    r_base_val * (math.sin(t_pitch) - t_pitch * math.cos(t_pitch)),
    r_base_val * (math.cos(t_pitch) + t_pitch * math.sin(t_pitch))
)

# We want the tooth centered at 0. So we rotate the whole involute segment by -phi_pitch.
# Let's create the profile points for the RIGHT flank (from dedendum to addendum)
# and the LEFT flank (from addendum to dedendum).
# And connect them with arcs at top and bottom.

# Helper to rotate a point
def rotate(v, angle_deg):
    a = math.radians(angle_deg)
    return App.Vector(v.X * math.cos(a) - v.Y * math.sin(a),
                      v.X * math.sin(a) + v.Y * math.cos(a),
                      v.Z)

# Define the profile points for ONE tooth
# 1. Start at Dedendum (Right side)
# 2. Involute to Addendum (Right side)
# 3. Arc at Outer Diameter to Left Addendum
# 4. Involute to Dedendum (Left side)
# 5. Arc at Root Diameter to Right Dedendum (with fillet)

# Right Flank Points (t from t_ded to t_add)
right_flank_pts = []
for i in range(100):
    t = t_ded + (t_add - t_ded) * (i / 99.0)
    x = r_base_val * (math.cos(t) + t * math.sin(t))
    y = r_base_val * (math.sin(t) - t * math.cos(t))
    right_flank_pts.append(App.Vector(x, y, 0))

# Left Flank Points (t from t_add to t_ded)
left_flank_pts = []
for i in range(100):
    t = t_add - (t_add - t_ded) * (i / 99.0)
    x = r_base_val * (math.cos(t) + t * math.sin(t))
    y = r_base_val * (math.sin(t) - t * math.cos(t))
    left_flank_pts.append(App.Vector(x, y, 0))

# Rotate to center the tooth
# The center of the tooth is at phi_pitch. We rotate by -phi_pitch.
# Note: phi_pitch is in radians.
center_angle = -phi_pitch

# Rotate points
right_flank_rot = [rotate(p, center_angle) for p in right_flank_pts]
left_flank_rot = [rotate(p, center_angle) for p in left_flank_pts]

# Construct the sketch geometry
# We will use a single sketch object and add lines/arcs.
# Since we have many points, we can add them as a polyline or a series of lines.
# FreeCAD Sketcher supports adding a list of points as a "Polyline" if we use the API correctly, 
# but usually we add LineSegments.
# To keep the script clean, we will add the right flank as a series of lines, 
# then an arc for the top, then the left flank, then an arc for the bottom.

# Top Arc: From end of right_flank_rot to start of left_flank_rot
# Both are at radius r_outer_val.
# We need to ensure the arc direction is correct (counter-clockwise for a closed loop).
# Right flank ends at p_add_rot. Left flank starts at p_add_rot (reversed).
# Wait, left_flank_pts goes from t_add to t_ded. So left_flank_rot[0] is at t_add.
# So we connect right_flank_rot[-1] (t_add) to left_flank_rot[0] (t_add) via an arc?
# No, they are the same point. We need to go from right_flank_rot[-1] to left_flank_rot[0] 
# via the OUTER circle arc.
# Actually, the sequence should be:
# Start at Right Dedendum -> Right Addendum (Involute) -> Top Arc -> Left Addendum -> Left Dedendum (Involute) -> Bottom Arc -> Start.

# Let's build the list of vertices for the sketch
sketch_pts = []
# 1. Right Dedendum
sketch_pts.append(right_flank_rot[0])
# 2. Right Addendum
sketch_pts.append(right_flank_rot[-1])
# 3. Left Addendum (same point as above, but we need to traverse the arc)
# We will add the arc explicitly.
# 4. Left Dedendum
sketch_pts.append(left_flank_rot[-1])
# 5. Right Dedendum (same as start, via bottom arc)

# Add Geometry
# Right Flank
for i in range(len(right_flank_rot) - 1):
    sketch_gear.addGeometry(Part.LineSegment(right_flank_rot[i], right_flank_rot[i+1]), False)

# Top Arc
# Center (0,0), Radius r_outer_val, Start Angle, End Angle
# Start: Right Addendum angle
# End: Left Addendum angle
# Angle of Right Addendum: phi_add + center_angle
# Angle of Left Addendum: phi_add + center_angle (since they are the same point on the circle)
# Wait, the arc goes from the end of the right flank to the start of the left flank.
# The angle of the point is phi_add + center_angle.
# The arc goes from this angle to ... wait.
# The tooth is symmetric. The right flank is at +pitch/2, left at -pitch/2?
# No, the involute segment is defined by t.
# The angle of the point on the involute is phi = atan2(y,x).
# The arc connects the end of the right flank to the start of the left flank.
# Since the left flank is the reverse of the right flank, the start of the left flank is the same point as the end of the right flank.
# So the arc is a full circle? No.
# The arc is the top of the tooth. It connects the two flanks.
# The two flanks meet at the addendum circle.
# So the arc is just a point? No, the flanks diverge.
# The right flank goes from dedendum to addendum.
# The left flank goes from addendum to dedendum.
# The top of the tooth is the arc of the addendum circle between the two flanks.
# The angle of the right flank at addendum is phi_add + center_angle.
# The angle of the left flank at addendum is phi_add + center_angle?
# No. The left flank is the mirror image.
# The angle of the left flank at addendum is phi_add + center_angle + pitch_angle?
# No, the tooth is centered at 0.
# The right flank is at +pitch_angle/2. The left flank is at -pitch_angle/2.
# So the angle of the right flank at addendum is phi_add + center_angle + pitch_angle/2?
# Let's re-evaluate the rotation.
# We rotated the involute segment (which was at phi_pitch) by -phi_pitch.
# So the segment is now centered at 0.
# The right flank is the "positive" side (y > 0). The left flank is "negative" side (y < 0).
# The top arc connects the end of the right flank (y>0) to the start of the left flank (y<0).
# The angle of the end of the right flank is roughly 0 + small_angle.
# The angle of the start of the left flank
