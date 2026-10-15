import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

# --- Configuration & Parameters ---
# Derived values based on ISO standards and task description
pressure_angle_deg = 20.0
gear_module = 2.0
number_of_teeth = 20
pitch_diameter = 40.0
outer_diameter = 44.0
face_width = 20.0
hub_diameter = 32.0
hub_width = 10.0
shaft_diameter = 10.0
overall_width = 30.0

# Calculated ISO values
addendum = pitch_diameter / number_of_teeth  # 2.0
dedendum = 1.25 * gear_module               # 2.5
root_diameter = pitch_diameter - 2 * dedendum # 35.0

# --- Document Setup ---
doc = App.newDocument("Gear")

# Create named parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "module", "Parameters", "Gear Module")
params.module = gear_module
params.addProperty("App::PropertyInteger", "teeth", "Parameters", "Number of Teeth")
params.teeth = number_of_teeth
params.addProperty("App::PropertyLength", "pitchDiam", "Parameters", "Pitch Diameter")
params.pitchDiam = pitch_diameter
params.addProperty("App::PropertyLength", "faceWidth", "Parameters", "Face Width")
params.faceWidth = face_width
params.addProperty("App::PropertyLength", "hubDiam", "Parameters", "Hub Diameter")
params.hubDiam = hub_diameter
params.addProperty("App::PropertyLength", "hubWidth", "Parameters", "Hub Width")
params.hubWidth = hub_width
params.addProperty("App::PropertyLength", "shaftDiam", "Parameters", "Shaft Bore Diameter")
params.shaftDiam = shaft_diameter
params.addProperty("App::PropertyLength", "overallWidth", "Parameters", "Overall Width")
params.overallWidth = overall_width
params.addProperty("App::PropertyAngle", "pressureAngle", "Parameters", "Pressure Angle (deg)")
params.pressureAngle = pressure_angle_deg

# Create the PartDesign Body
body = doc.addObject("PartDesign::Body", "GearBody")
body.Label = "GearBody"

# --- Feature 1: Base Geometry (Shaft Bore) ---
# We start with the smallest feature to keep the tree clean, then add the hub, 
# then the gear teeth to the outer profile.
# Sketch Plane: XY (default)

sketch_bore = body.newObject("Sketcher::SketchObject", "SketchShaftBore")
sketch_bore.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch_bore.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bore.ConstrainAutomatic = True

# Create a circle for the shaft bore
# Center at (0,0), Radius = shaft_diameter / 2
radius_shaft = params.shaftDiam / 2.0
sketch_bore.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius_shaft), False)

sketch_bore = doc.recomputeObject(sketch_bore) # Ensure constraints are applied immediately
bore_pad = body.newObject("PartDesign::Pad", "PadShaftBore")
bore_pad.Profile = sketch_bore
bore_pad.Type = "Hollow" # Hollow means it subtracts from the solid
bore_pad.Length = params.overallWidth
bore_pad.Method = "Blind"
bore_pad.Reversed = True # Subtracting creates the hole

# --- Feature 2: Hub ---
# Sketch Plane: XY
sketch_hub = body.newObject("Sketcher::SketchObject", "SketchHub")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hub.ConstrainAutomatic = True

# Inner circle (bore)
circle_hub_inner = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaftDiam / 2.0)
sketch_hub.addGeometry(circle_hub_inner, False)

# Outer circle (hub face)
circle_hub_outer = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hubDiam / 2.0)
sketch_hub.addGeometry(circle_hub_outer, False)

# Coaxial constraint
sketch_hub.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch_hub.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.shaftDiam / 2.0))
sketch_hub.addConstraint(Sketcher.Constraint("Radius", 0, 2, params.hubDiam / 2.0))
sketch_hub = doc.recomputeObject(sketch_hub)

hub_pad = body.newObject("PartDesign::Pad", "PadHub")
hub_pad.Profile = sketch_hub
hub_pad.Length = params.hubWidth
hub_pad.Type = "Blind"
hub_pad.Reversed = False # Add material

# --- Feature 3: Gear Teeth ---
# Sketch Plane: XY
sketch_teeth = body.newObject("Sketcher::SketchObject", "SketchTeeth")
sketch_teeth.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_teeth.ConstrainAutomatic = True

# 1. Outer Circle (Base for Outer Diameter)
circle_outer = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outerDiam / 2.0)
sketch_teeth.addGeometry(circle_outer, False)

# 2. Root Circle (Base for Root Diameter)
circle_root = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.rootDiam / 2.0)
sketch_teeth.addGeometry(circle_root, False)

# 3. Pitch Circle (Reference for tooth spacing)
circle_pitch = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitchDiam / 2.0)
sketch_teeth.addGeometry(circle_pitch, False)

# 4. Keyway / Hub Cutout (Optional but good for realism, defined in Hub feature usually, 
#    but here we ensure the tooth profile sits on the hub. 
#    We will draw the tooth profile relative to the pitch circle.)

# Calculate tooth geometry
module = params.module
num_teeth = params.teeth
pressure_angle_rad = params.pressureAngle * (3.14159265359 / 180.0)
base_radius = (params.pitchDiam / 2.0) * (1 - (1/3.0) * (pressure_angle_rad / (2 * 3.14159265359))) # Approximate base circle for involute
# Actually, base radius = Pitch Radius * cos(Pressure Angle)
base_radius_calc = (params.pitchDiam / 2.0) * (App.cos(params.pressureAngle * (3.14159265359 / 180.0)))

# Tooth pitch
tooth_pitch = (3.14159265359 * params.pitchDiam) / num_teeth

# We will generate one tooth profile and pattern it.
# Profile starts at the bottom of the tooth (on the root circle or slightly inside).
# Standard approach: Draw the tooth flank lines using involute math or simple lines for this script complexity.
# Given the constraints of a single script without external libraries, we will approximate the involute 
# with two lines tangent to a base circle, or simply define the points.
# Let's define the tooth profile explicitly.

# Start point: Top of tooth on Outer Circle
start_point = App.Vector(0, params.outerDiam / 2.0)

# End points: Bottom of tooth on Root Circle
# Angle for one tooth
delta_angle = (360.0 / num_teeth) * (3.14159265359 / 180.0)

# We need to draw the flank. 
# To keep it simple and robust in FreeCAD Python without complex trig loops in constraints,
# we will create a custom geometry for the tooth flank.
# The flank is an involute curve. We can approximate it with a spline or lines.
# Let's use a precise geometric construction:
# 1. Define the contact point on the base circle.
# 2. Draw a line tangent to the base circle.
# 3. The tooth height is from Base Circle to Outer Circle? No, from Root to Outer.
# Actually, the tooth profile is the involute from the Base Circle to the Top Land.

# Let's build the profile line by line:
# Point 0: Top of tooth (0, Outer/2)
# Point 1: Corner between Top Land and Flank
# Point 2: Bottom of tooth (on Root Circle)

# Let's calculate the coordinates for a single tooth at angle 0 (top).
# We will shift the sketch to the correct angle later via the Pattern.
# Current sketch is at 0 deg.

# Tooth height = Addendum (Top) + Dedendum (Bottom)? 
# Outer = Pitch + Addendum. Root = Pitch - 2*Dedendum.
# Total tooth height = Addendum + Dedendum.

# Let's define the points for one tooth centered at 90 degrees (top) for easier drawing on XY plane (0, R).
# Shift logic: We will rotate the sketch later or just draw one tooth at 0 and pattern it.
# Let's draw one tooth centered at 0 degrees (Right side) and pattern it 360/20 times.

# Tooth Geometry:
# Pitch Radius (Rp) = 20.0
# Outer Radius (Ro) = 22.0
# Root Radius (Rr) = 17.5

# Angle of pressure line (tangent to base circle) relative to radius vector.
# For a standard gear, the flank is tangent to the base circle.
# Base Radius (Rb) = 20.0 * cos(20 deg) = 18.794
# The involute starts at the base circle.
# The tooth height above base circle = Addendum + (Dedendum - (Root - Base correction))?
# Simpler: The tooth profile is an involute from Rb to Ro, and a root fillet from Rr.
# We will approximate the root with a circle (Root Circle) and the flank with lines tangent to Base Circle.

# Let's create the profile using LineSegments and Arcs.
# Center of gear: (0,0)

# Tooth 1 Position: 0 degrees (Vector (1, 0))
# Tooth 2 Position: 18 degrees.

# Let's build the profile for one tooth.
# Points:
# A: Top of tooth. (Ro, 0) -> (0, 22) if rotated 90, or (22, 0) if 0. Let's use 0 deg.
#    A = (22, 0)
# B: Intersection of Outer Circle and Flank.
# C: Intersection of Base Circle and Flank (Start of Involute).
# D: Bottom of tooth (Root Circle).

# To make this script robust and concise, we will use the "Gear" shape generation logic:
# 1. Draw the Pitch Circle.
# 2. Draw the Root Circle.
# 3. Draw the Outer Circle.
# 4. Generate the tooth profile using the "Gear" shape approximation via lines.

# Profile construction:
# Start at top of tooth (0, Ro).
# Go down to the "Corner" where the involute starts? No, involute starts at Base Circle.
# The "Top Land" is the flat part at the top.
# Length of Top Land = Module * (1.6 - 0.25*...)? Let's assume standard.
# Usually, the flank meets the top land at the intersection of the involute and the outer circle.

# Let's calculate the angle of the intersection of the flank (tangent to Base Circle) with the Outer Circle.
# Angle of tangent point on Base Circle (theta_b):
# sin(theta_b) = (Ro / Rb) * sin(theta_outer)? No.
# Let's use the property: The normal to the involute passes through the base circle.
# The angle of the tangent line to the base circle is constant relative to the radius vector? No.

# Simplified Approach for Script Reliability:
# We will construct the tooth profile using 4 points:
# 1. Top Center: (0, Ro)
# 2. Top Right Corner: (Ro * cos(alpha), Ro * sin(alpha))
# 3. Bottom Right: (Rr * cos(beta), Rr * sin(beta))
# 4. Bottom Center: (0, Rr)

# This requires solving for the intersection of the involute and the circles.
# Given the complexity, we will use a very close approximation using straight lines (tangents) 
# which looks good enough for most purposes, or better:
# We will use the exact involute parameterization if possible, but FreeCAD PartGeom is heavy.
# Let's use the standard "Approximation" method:
# The flank is a straight line from (Base Circle) to (Outer Circle intersection).
# The base circle is Rb = 18.794.
# The flank is tangent to the base circle.
# We need the point where the tangent from the base circle touches the outer circle.
# This is complex to solve analytically in a short script without a solver.

# Alternative: Use the "Gear" shape from a standard library? No external libs.
# Let's use a very robust approximation:
# The tooth profile is defined by:
# - Top Land: Flat line at Ro.
# - Flank: Line tangent to Base Circle.
# - Root: Circle Rr.

# Let's calculate the intersection point P between the tangent line (to Base Circle) and the Outer Circle.
# Let the tooth be at angle 0.
# The tangent line equation: x * cos(phi) + y * sin(phi) = Rb.
# We need to find the angle of the normal to the base circle.
# Actually, the simplest way to draw a gear tooth in a script without heavy math is:
# 1. Define the pitch circle.
# 2. Define the base circle.
# 3. Define the addendum and dedendum.
# 4. Draw the involute using a spline if we can generate points.
#    We can generate points for the involute: 
#    x = Rb * (cos(t) + t * sin(t))
#    y = Rb * (sin(t) - t * cos(t))
#    where t is the rolling angle.

# Let's generate the involute points.
import math

Rb = base_radius_calc
Ro = params.outerDiam / 2.0
Rr = params.rootDiam / 2.0

# Calculate the max t for the tooth height (from Base to Outer)
# Distance from center to point on involute = Rb * sqrt(1 + t^2)
# We need Rb * sqrt(1 + t^2) = Ro
# sqrt(1 + t^2) = Ro / Rb
# 1 + t^2 = (Ro/Rb)^2
# t = sqrt((Ro/Rb)^2 - 1)
t_max = math.sqrt((Ro/Rb)**2 - 1)

# Generate points for the flank
# We need points from t=0 (Base Circle) to t=t_max (Outer Circle).
# Then we connect to the top land.
# Then we go down the other flank.
# Then the root circle.

# Let's create a list of points for the profile of ONE tooth.
# Tooth center angle = 0 (pointing to +Y for easier drawing? No, let's stick to +Y for top).
# Let's orient the tooth pointing to +Y.
# Profile starts at (-ToothWidth/2, Rr), goes to (-ToothWidth/2, Ro) ?? No.

# Let's define the tooth geometry relative to the Y-axis.
# Top of tooth is at (0, Ro).
# We need the "Corner" points where the top land meets the flank.
# Let's calculate the angle of the tangent point on the base circle relative to the center.
# The tangent point is at angle alpha_t such that the line from origin to tangent point is perpendicular to the tangent line? No.
# The tangent line is at distance Rb from origin.
# The intersection of the tangent line (tangent at angle theta) and the circle Ro.
# Let's assume the tangent point on the base circle is at angle theta_b.
# The tangent line equation: x*cos(theta_b) + y*sin(theta_b) = Rb.
# We want to find the intersection with x=0 (the Y axis)? No, the tooth is symmetric around Y axis.
# The two flanks are symmetric.
# The tangent points on the base circle for the two flanks are at angles +/- theta_b.
# Where theta_b is the angle where the involute meets the outer circle? No.

# Let's just generate the points along the involute curve from t=0 to t_max.
# Then we will mirror them.

points = []
# We need the angle of the tooth. Let's say the tooth is centered at 90 degrees (0, Ro).
# The involute starts at the base circle.
# The angle of the tangent point on the base circle (relative to the tooth center line) is not t.
# The parameter t IS the angle of the tangent point on the base circle relative to the line of centers (the normal).
# So, if the tooth center is at 90 deg,
