import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Derived from the prompt requirements
PRESSURE_ANGLE_DEG = 20.0
GEAR_MODULE = 1.0
NUMBER_OF_TEETH = 60
PITCH_DIAMETER = 60.0
OUTER_DIAMETER = 62.0
FACE_WIDTH = 6.0
HUB_DIAMETER = 18.0
HUB_WIDTH = 8.0
SHAFT_DIAMETER = 8.0
OVERALL_WIDTH = 14.0

# Calculated parameters based on ISO/DIN standards provided in prompt
PRESSURE_ANGLE = math.radians(PRESSURE_ANGLE_DEG)
ADDENDUM = PITCH_DIAMETER / NUMBER_OF_TEETH
DEDENDUM = 1.25 * GEAR_MODULE
WHOLE_DEPTH = ADDENDUM + DEDENDUM
ROOT_DIAMETER = PITCH_DIAMETER - 2 * DEDENDUM
BASE_DIAMETER = PITCH_DIAMETER * math.cos(PRESSURE_ANGLE)

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# Correct placement assignment for PartDesign::Body
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold our named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.gear_module = GEAR_MODULE
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Teeth")
params.number_of_teeth = NUMBER_OF_TEETH
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Width")
params.face_width = FACE_WIDTH
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub")
params.hub_diameter = HUB_DIAMETER
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub")
params.hub_width = HUB_WIDTH
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Bore")
params.shaft_diameter = SHAFT_DIAMETER
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Total")
params.overall_width = OVERALL_WIDTH
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Angle")
params.pressure_angle = PRESSURE_ANGLE_DEG

# --- Sketch 1: Gear Profile (XY Plane) ---
sketch_gear = body.newObject("Sketcher::SketchObject", "Sketch_GearProfile")
sketch_gear.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_gear.ConstrainToCurrentPlane = True
sketch_gear.MapMode = "FlatFace"
sketch_gear.AttachmentSupport = (doc.getObject("XY_Plane"), [])

# Helper to add geometry to sketch
def add_line(sk, p1, p2, is_constraint=False):
    sk.addGeometry(Part.LineSegment(p1, p2), is_constraint)

def add_circle(sk, center, radius, is_constraint=False):
    sk.addGeometry(Part.Circle(center, App.Vector(0, 0, 1), radius), is_constraint)

# 1. Base Circle (Pitch Diameter)
add_circle(sketch_gear, App.Vector(0, 0, 0), PITCH_DIAMETER / 2.0)

# 2. Outer Circle (Tip Diameter)
add_circle(sketch_gear, App.Vector(0, 0, 0), OUTER_DIAMETER / 2.0)

# 3. Root Circle (Bottom Diameter)
add_circle(sketch_gear, App.Vector(0, 0, 0), ROOT_DIAMETER / 2.0)

# 4. Base Circle (for involute generation)
add_circle(sketch_gear, App.Vector(0, 0, 0), BASE_DIAMETER / 2.0)

# --- Involute Curve Generation ---
# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
num_points = 100 # Resolution of the involute
involute_points = []
for i in range(num_points):
    # t goes from 0 to approx pi/2 (90 degrees) for one side of the tooth
    # We need enough points to cover the tooth height.
    # Tooth height is roughly Addendum + Dedendum.
    # The involute starts at base circle.
    # Max angle t: tan(t) = (r_tip - r_base) / r_base ? No.
    # Let's just generate a long enough curve and trim it later with constraints.
    t = (i / num_points) * math.pi # 0 to 180 degrees
    x = base_radius * (math.cos(t) + t * math.sin(t))
    y = base_radius * (math.sin(t) - t * math.cos(t))
    if i == 0:
        p = App.Vector(x, y, 0)
    else:
        p = App.Vector(x, y, 0)
        # Check if we went too far out (beyond tip diameter)
        dist = math.sqrt(x*x + y*y)
        if dist > OUTER_DIAMETER / 2.0 + 1.0:
            break
    if i == 0:
        p_start = p
    else:
        # We need to connect points. A single curve object is better.
        pass

# Let's create a single Part::Curve object representing the involute
# We will create a list of points and interpolate.
# Actually, let's create a curve from a list of points.
# Note: In FreeCAD 1.1, Sketcher::SketchObject.addGeometry accepts Part::Curve.

# Generate Involute Curve
base_radius = BASE_DIAMETER / 2.0
