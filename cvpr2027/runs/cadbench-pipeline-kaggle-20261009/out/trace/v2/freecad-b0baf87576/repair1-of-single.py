import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("SmoothShaft")

# --- Parameters ---
# Define parameter names
P_SHAFT_DIAM = "smooth_shaft_diameter"
P_SHAFT_LEN = "smooth_shaft_length"
P_KEY_W = "keyway_width"
P_KEY_D = "keyway_depth"
P_KEY_H = "keyway_height"
P_NUM_KEY = "num_keyway"

# Create Parameter objects
params = []
for name in [P_SHAFT_DIAM, P_SHAFT_LEN, P_KEY_W, P_KEY_D, P_KEY_H, P_NUM_KEY]:
    p = doc.addObject("App::Parameter", name)
    p.Value = 0.0
    params.append(p)

# Set initial values
params[0].Value = 50.0  # diameter
params[1].Value = 80.0  # length
params[2].Value = 5.0   # width
params[3].Value = 3.0   # depth
params[4].Value = 20.0  # height (length of keyway along shaft)
params[5].Value = 2     # number

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Main Shaft Sketch ---
# Create a sketch on the XY plane
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftProfile")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.ConstrainAuto = True

# Add a circle for the shaft profile
# Center at (0,0), Radius = Diameter / 2
radius_expr = f"({params[0].Value})/2"
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), float(radius_expr))
sketch_shaft.addGeometry(circle, False)

# Add a point at the origin for constraints
origin_point = Part.Point(App.Vector(0, 0, 0))
sketch_shaft.addGeometry(origin_point, False)

# Constraint: Coincident between circle center and origin
# Geometry indices: 0 is circle, 1 is point.
# Circle center index: 2. Point index: 0.
sketch_shaft.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 0))

# --- Pad the Shaft ---
pad_shaft = body.newObject("PartDesign::Pad", "PadShaft")
pad_shaft.Profile = sketch_shaft
# Length driven by parameter
pad_shaft.setExpression("Length", f"{params[1].Value}")
pad_shaft.Type = "Solid"
pad_shaft.MidPlane = False

# --- Keyway Sketch ---
# Strategy: Sketch on XY plane (cross-section), then Pad along Z (shaft axis).
# Rectangle: Width = keyway_width (along X), Height = keyway_depth (along Y).
sketch_key = body.newObject("Sketcher::SketchObject", "KeywayProfile")
sketch_key.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_key.ConstrainAuto = True

# Draw Rectangle
w_expr = f"({params[2].Value})"
d_expr = f"({params[3].Value})"

# Points for rectangle centered at origin
p1 = App.Vector(-float(w_expr)/2, -float(d_expr)/2, 0)
p2 = App.Vector(float(w_expr)/2, -float(d_expr)/2, 0)
p3 = App.Vector(float(w_expr)/2, float(d_expr)/2, 0)
p4 = App.Vector(-float(w_expr)/2, float(d_expr)/2, 0)

sketch_key.addGeometry(Part.LineSegment(p1, p2), False)
sketch_key.addGeometry(Part.LineSegment(p2, p3), False)
sketch_key.addGeometry(Part.LineSegment(p3, p4), False)
sketch_key.addGeometry(Part.LineSegment(p4, p1), False)

# Add origin point
origin_point_key = Part.Point(App.Vector(0, 0, 0))
sketch_key.addGeometry(origin_point_key, False)

# Constraints
# Center X: Coincident midpoint of bottom line (0) to origin (4)
sketch_key.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 4, 0))
# Center Y: Coincident midpoint of left line (3) to origin (4)
sketch_key.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 4, 0))
# Perpendicular: Bottom line (0) and Left line (3)
sketch_key.addConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 3, 0))

# --- Pocket the Keyway (Single Instance) ---
pocket_key = body.newObject("PartDesign::Pocket", "PocketKeyway")
pocket_key.Profile = sketch_key
pocket_key.Type = "Blind"
# Extrude along Z (normal to XY plane)
pocket_key.setExpression("Length", f"{params[4].Value}")

# --- Polar Pattern of Keyways ---
# We need to pattern the pocket around the Z axis.
# The pocket is a subtractive feature. We can pattern the feature itself.
pattern = body.newObject("PartDesign::PolarPattern", "PatternKeyway")
pattern.Originals = [pocket_key]
pattern.Axis = (doc.getObject("Z_Axis"), [""])
pattern.setExpression("Angle", "360")
pattern.setExpression("Occurrences", f"{params[5].Value}")
pattern.setExpression("StepAngle", "180") # 360 / 2

# --- Fillet the Edges (Optional but good for "smooth shaft") ---
# Fillet the outer cylindrical surface where the keyway starts/ends?
# Or just leave it sharp as per "smooth shaft" description usually implying the main body.
# Let's add a small fillet to the outer edge of the keyway cut if it exists, 
# but the prompt asks for a "smooth shaft" with "keyway features". 
# Usually, keyways have sharp corners or small radii. Let's add a fillet to the outer cylinder 
# at the ends of the shaft to make it "smooth" at the ends.
# However, the prompt doesn't specify end fillets. Let's stick to the core requirements.
# The prompt says "smooth shaft... with keyway features". 
# I will add a fillet to the outer edge of the keyway cut to make it less sharp, 
# as "smooth" might imply no sharp internal corners.
# But standard keyways are sharp. Let's skip fillets to strictly follow "uniform diameter" 
# unless "smooth" implies end chamfers/fillets. 
# Given "smooth shaft", I will add a small fillet to the outer cylinder at the ends.
# But wait, the prompt says "uniform diameter". Fillets change the diameter at the ends.
# Let's assume "smooth" refers to the surface finish or lack of sharp edges on the main body.
# I will NOT add fillets to the ends to maintain "uniform diameter" as strictly as possible,
# unless the keyway corners are meant to be rounded.
# Let's add a fillet to the inner corners of the keyway to make it "smooth" inside.
# This requires selecting edges.
# Let's skip complex edge selection in headless script for robustness unless necessary.
# The current model satisfies: Cylinder + Keyways.

# --- Recompute and Save ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")
doc.saveAs(str(output_path))
