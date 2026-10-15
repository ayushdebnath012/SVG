import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Parameters Definition ---
# Derived from __file__ to ensure editability and clear paths
param_base = Path(__file__).parent
output_file = param_base / "answer.FCStd"

# Dimensions
L_OV = 40.13
R_REAR = 1.75
L_TAP_REAR = 0.38
R_MAIN = 1.98
L_MAIN = 20.32
L_TRANS = 0.99
R_RED = 0.99
L_TIP_TAP = 5.08

N_GROOVE = 2
R_GROOVE = 0.64
Z_GROOVE_1 = 6.40
P_GROOVE = 3.10
HALF_ANGLE_GROOVE = math.radians(36.8698976)

N_LOBE = 5
R_LOBE_ROOT = 0.05
R_LOBE_ROOT_OFF = 0.38
R_LOBE_OUT = 0.61
HALF_ANGLE_LOBE_OUT = math.radians(19.4989779)
R_SWEEP = 25.40
X_SWEEP = 42.91
Y_SWEEP = 25.63
ANG_SWEEP_S = math.radians(-108.5085355)
ANG_SWEEP_E = math.radians(-96.2678608)

H_PROJ = 1.52
Z_OFF = -0.76
Z_CROWN_CEN = 12.98
W_CROWN = 2.06
R_CROWN_ARC = 4.42
R_CROWN_BASE = 1.44

R_CUT = 2.72
HALF_ANGLE_CUT = math.radians(44.71061805)

# --- Document Setup ---
doc = App.newDocument("DriverBit")
doc.Label = "DriverBit_Model"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "L_OV", "Dimensions", "Overall Length")
params.L_OV = L_OV
params.addProperty("App::PropertyLength", "R_REAR", "Dimensions", "Rear Radius")
params.R_REAR = R_REAR
params.addProperty("App::PropertyLength", "L_TAP_REAR", "Dimensions", "Rear Taper Length")
params.L_TAP_REAR = L_TAP_REAR
params.addProperty("App::PropertyLength", "R_MAIN", "Dimensions", "Main Shank Radius")
params.R_MAIN = R_MAIN
params.addProperty("App::PropertyLength", "L_MAIN", "Dimensions", "Main Shank Length")
params.L_MAIN = L_MAIN
params.addProperty("App::PropertyLength", "L_TRANS", "Dimensions", "Transition Length")
params.L_TRANS = L_TRANS
params.addProperty("App::PropertyLength", "R_RED", "Dimensions", "Reduced Shank Radius")
params.R_RED = R_RED
params.addProperty("App::PropertyLength", "L_TIP_TAP", "Dimensions", "Tip Taper Length")
params.L_TIP_TAP = L_TIP_TAP

params.addProperty("App::PropertyInteger", "N_GROOVE", "Dimensions", "Groove Count")
params.N_GROOVE = N_GROOVE
params.addProperty("App::PropertyLength", "R_GROOVE", "Dimensions", "Groove Radius")
params.R_GROOVE = R_GROOVE
params.addProperty("App::PropertyLength", "Z_GROOVE_1", "Dimensions", "First Groove Axial")
params.Z_GROOVE_1 = Z_GROOVE_1
params.addProperty("App::PropertyLength", "P_GROOVE", "Dimensions", "Groove Pitch")
params.P_GROOVE = P_GROOVE
params.addProperty("App::PropertyLength", "HALF_ANGLE_GROOVE", "Dimensions", "Groove Half Angle")
params.HALF_ANGLE_GROOVE = HALF_ANGLE_GROOVE

params.addProperty("App::PropertyInteger", "N_LOBE", "Dimensions", "Lobe Count")
params.N_LOBE = N_LOBE
params.addProperty("App::PropertyLength", "R_LOBE_ROOT", "Dimensions", "Lobe Root Radius")
params.R_LOBE_ROOT = R_LOBE_ROOT
params.addProperty("App::PropertyLength", "R_LOBE_ROOT_OFF", "Dimensions", "Lobe Root Offset")
params.R_LOBE_ROOT_OFF = R_LOBE_ROOT_OFF
params.addProperty("App::PropertyLength", "R_LOBE_OUT", "Dimensions", "Lobe Outer Radius")
params.R_LOBE_OUT = R_LOBE_OUT
params.addProperty("App::PropertyLength", "HALF_ANGLE_LOBE_OUT", "Dimensions", "Lobe Outer Half Angle")
params.HALF_ANGLE_LOBE_OUT = HALF_ANGLE_LOBE_OUT
params.addProperty("App::PropertyLength", "R_SWEEP", "Dimensions", "Sweep Path Radius")
params.R_SWEEP = R_SWEEP
params.addProperty("App::PropertyLength", "X_SWEEP", "Dimensions", "Sweep Path Center X")
params.X_SWEEP = X_SWEEP
params.addProperty("App::PropertyLength", "Y_SWEEP", "Dimensions", "Sweep Path Center Y")
params.Y_SWEEP = Y_SWEEP
params.addProperty("App::PropertyAngle", "ANG_SWEEP_S", "Dimensions", "Sweep Start Angle")
params.ANG_SWEEP_S = ANG_SWEEP_S
params.addProperty("App::PropertyAngle", "ANG_SWEEP_E", "Dimensions", "Sweep End Angle")
params.ANG_SWEEP_E = ANG_SWEEP_E

params.addProperty("App::PropertyLength", "H_PROJ", "Dimensions", "Extrusion Height")
params.H_PROJ = H_PROJ
params.addProperty("App::PropertyLength", "Z_OFF", "Dimensions", "Z Offset")
params.Z_OFF = Z_OFF
params.addProperty("App::PropertyLength", "Z_CROWN_CEN", "Dimensions", "Crown Axial Center")
params.Z_CROWN_CEN = Z_CROWN_CEN
params.addProperty("App::PropertyLength", "W_CROWN", "Dimensions", "Crown Half Width")
params.W_CROWN = W_CROWN
params.addProperty("App::PropertyLength", "R_CROWN_ARC", "Dimensions", "Crown Arc Radius")
params.R_CROWN_ARC = R_CROWN_ARC
params.addProperty("App::PropertyLength", "R_CROWN_BASE", "Dimensions", "Crown Base Radius")
params.R_CROWN_BASE = R_CROWN_BASE

params.addProperty("App::PropertyLength", "R_CUT", "Dimensions", "Cutout Arc Radius")
params.R_CUT = R_CUT
params.addProperty("App::PropertyAngle", "HALF_ANGLE_CUT", "Dimensions", "Cutout Half Angle")
params.HALF_ANGLE_CUT = HALF_ANGLE_CUT

# --- Sketch 1: Axial Profile (Rear to Main Shank) ---
# Plane: XY, Origin: (0,0,0)
s1 = body.newObject("Sketcher::SketchObject", "Sketch_Profile")
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.Placement = s1.Placement.multiply(App.Placement(App.Vector(0,0,0), App.Rotation())) # Ensure correct origin
s1.Placement = App.Placement(App.Vector(0, 0, 0))
s1.ViewObject.Visibility = False
# Constraints will be added implicitly or explicitly via geometry
# Geometry: 
# X=0, Y=0: Start
# X=L_TAP_REAR, Y=R_REAR: End of taper
# X=L_TAP_REAR, Y=R_MAIN: Start of main shank
# X=L_MAIN + L_TAP_REAR, Y=R_MAIN: End of main shank
# X=L_MAIN + L_TAP_REAR, Y=R_RED: Start of tip taper
# X=L_OV, Y=R_RED: End of tip taper

# We need to construct the polyline segments.
# Segment 1: (0,0) to (L_TAP_REAR, R_REAR)
# Segment 2: (L_TAP_REAR, R_REAR) to (L_TAP_REAR, R_MAIN)
# Segment 3: (L_TAP_REAR, R_MAIN) to (L_MAIN + L_TAP_REAR, R_MAIN)
# Segment 4: (L_MAIN + L_TAP_REAR, R_MAIN) to (L_MAIN + L_TAP_REAR, R_RED)
# Segment 5: (L_MAIN + L_TAP_REAR, R_RED) to (L_OV, R_RED)

# Since we can't easily add constraints to a polyline in this script format without a loop, 
# we will use a compound curve or simply add lines and constrain them. 
# However, Part.LineSegment is the safest for the base.
# Let's create the profile as a sequence of lines.
# Note: Sketcher::SketchObject expects a closed loop for extrusion usually, but we can use a solid feature if closed.
# Let's create a closed polygon.
# Point A: (0,0)
# Point B: (L_TAP_REAR, R_REAR)
# Point C: (L_TAP_REAR, R_MAIN)
# Point D: (L_MAIN + L_TAP_REAR, R_MAIN)
# Point E: (L_MAIN + L_TAP_REAR, R_RED)
# Point F: (L_OV, R_RED)
# Point G: (L_OV, 0) -> Wait, the description says "bit axis follows global X... rear-end center at global origin".
# The profile is in XY. Y is radial.
# So at X=0, Y=0. At X=L_OV, Y=0 (if it tapers to a point or just ends). 
# "reduced shank leading to the driver tip". Usually a tip is a point or small radius.
# Assuming it tapers to Y=0 at L_OV based on "reduced shank leading to the driver tip".
# Let's assume Point G (L_OV, 0) closes the loop.

# Helper to add line
def add_line(s, p1, p2):
    s.addGeometry(Part.LineSegment(p1, p2), False)

add_line(s1, App.Vector(0, 0, 0), App.Vector(params.L_TAP_REAR, params.R_REAR, 0))
add_line(s1, App.Vector(params.L_TAP_REAR, params.R_REAR, 0), App.Vector(params.L_TAP_REAR, params.R_MAIN, 0))
add_line(s1, App.Vector(params.L_TAP_REAR, params.R_MAIN, 0), App.Vector(params.L_MAIN + params.L_TAP_REAR, params.R_MAIN, 0))
add_line(s1, App.Vector(params.L_MAIN + params.L_TAP_REAR, params.R_MAIN, 0), App.Vector(params.L_MAIN + params.L_TAP_REAR, params.R_RED, 0))
add_line(s1, App.Vector(params.L_MAIN + params.L_TAP_REAR, params.R_RED, 0), App.Vector(params.L_OV, params.R_RED, 0))
add_line(s1, App.Vector(params.L_OV, params.R_RED, 0), App.Vector(params.L_OV, 0, 0))
add_line(s1, App.Vector(params.L_OV, 0, 0), App.Vector(0, 0, 0))

s1.Constraints.append(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
s1.Constraints.append(Sketcher.Constraint("Coincident", 5, 2, 6, 1))
s1.Constraints.append(Sketcher.Constraint("Coincident", 6, 2, 0, 1))
s1.Constraints.append(Sketcher.Constraint("Perpendicular", 0, 2, 1, 1)) # Optional check
s1.Constraints.append(Sketcher.Constraint("Perpendicular", 1, 2, 2, 1))
s1.Constraints.append(Sketcher.Constraint("Perpendicular", 2, 2, 3, 1))
s1.Constraints.append(Sketcher.Constraint("Perpendicular", 3, 2, 4, 1))
s1.Constraints.append(Sketcher.Constraint("Perpendicular", 4, 2, 5, 1))
s1.Constraints.append(Sketcher.Constraint("Perpendicular", 5, 2, 6, 1))
s1.Constraints.append(Sketcher.Constraint("Horizontal", 0, 1)) # X is horizontal
s1.Constraints.append(Sketcher.Constraint("Horizontal", 1, 1))
s1.Constraints.append(Sketcher.Constraint("Horizontal", 2, 1))
s1.Constraints.append(Sketcher.Constraint("Horizontal", 3, 1))
s1.Constraints.append(Sketcher.Constraint("Horizontal", 4, 1))
s1.Constraints.append(Sketcher.Constraint("Horizontal", 5, 1))
s1.Constraints.append(Sketcher.Constraint("Vertical", 0, 2)) # Y is vertical
s1.Constraints.append(Sketcher.Constraint("Vertical", 1, 2))
s1.Constraints.append(Sketcher.Constraint("Vertical", 2, 2))
s1.Constraints.append(Sketcher.Constraint("Vertical", 3, 2))
s1.Constraints.append(Sketcher.Constraint("Vertical", 4, 2))
s1.Constraints.append(Sketcher.Constraint("Vertical", 5, 2))
s1.Constraints.append(Sketcher.Constraint("DistanceX", 1, 0, params.L_TAP_REAR))
s1.Constraints.append(Sketcher.Constraint("DistanceY", 1, 0, params.R_REAR))
s1.Constraints.append(Sketcher.Constraint("DistanceX", 2, 1, 0)) # X2 - X1
s1.Constraints.append(Sketcher.Constraint("DistanceY", 2, 1, params.R_MAIN - params.R_REAR))
s1.Constraints.append(Sketcher.Constraint("DistanceX", 3, 2, params.L_MAIN))
s1.Constraints.append(Sketcher.Constraint("DistanceY", 3, 2, 0))
s1.Constraints.append(Sketcher.Constraint("DistanceX", 4, 3, 0))
s1.Constraints.append(Sketcher.Constraint("DistanceY", 4, 3, params.R_RED - params.R_MAIN))
s1.Constraints.append(Sketcher.Constraint("DistanceX", 5, 4, params.L_OV - (params.L_MAIN + params.L_TAP_REAR)))
s1.Constraints.append(Sketcher.Constraint("DistanceY", 5, 4, 0))
s1.Constraints.append(Sketcher.Constraint("DistanceX", 6, 5, 0))
s1.Constraints.append(Sketcher.Constraint("DistanceY", 6, 5, -params.R_RED))

# --- Sketch 2: Rear Grooves ---
# Plane: XY, Origin: (L_TAP_REAR + params.P_GROOVE/2, 0, 0) -> Actually, let's calculate positions based on pitch.
# "first_ring_groove_axial_offset = 6.40 mm". "ring_groove_pitch = 3.10 mm".
# Groove 1 Center X: 6.40
# Groove 2 Center X: 6.40 + 3.10 = 9.50
# We need to create a sketch for the groove shape relative to its center, then pattern or copy.
# Since PartDesign::Pattern is rotational, and these are circumferential (rotational) grooves, 
# we might just create one sketch for one groove and use a Linear Pattern along X? 
# No, "circumferential retention grooves". They are on the shank.
# "Each groove is a minor circular arc... curves inward... center lies radially outside".
# This implies the groove is a circular arc in the XY plane? Or a hole?
# "circumferential" usually means around the axis (X). So the groove runs around the X axis?
# "Two circumferential retention grooves".
# If they are circumferential, they are rings around the X axis.
# "Each groove is a minor circular arc... center lies radially outside".
# This describes the cross-section of the groove in the XY plane.
# So we need to subtract a shape defined by this arc.
# Let's create a sketch at the axial position of the first groove.
# The groove is a "minor circular arc".
# Endpoints meet the straight main-shank profile.
# Center lies radially outside.
# Angle: ring_groove_half_angle between axial (X) and line from center to junction.

# Let's create a sketch for one groove at X = 6.40.
# We need to define the arc.
# Junction 1: (X=6.40 - L_TAP_REAR, Y=R_MAIN) -> No, the taper ends at X = L_TAP_REAR = 0.38.
# The groove is at X=6.40. The shank is straight there.
# Junction Y = R_MAIN.
# Angle = 36.87 deg.
# Let Cx, Cy be center.
# Vector from Center to Junction: (Jx - Cx, Jy - Cy).
# Angle with X axis (axial) is 36.87.
# Wait, "acute angle between the axial direction and the line from the groove-circle center to either junction".
# Axial direction is X.
# So the line from Center to Junction makes 36.87 deg with X axis.
# Since center is radially outside (Y < R_MAIN), and junction is at Y=R_MAIN
