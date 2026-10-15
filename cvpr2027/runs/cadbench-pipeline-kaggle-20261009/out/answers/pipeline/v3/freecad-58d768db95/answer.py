import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration Parameters ---
# Derived from the prompt's specific values
EXTRUSION_LENGTH = 1040.0
EXTRUSION_START_OFFSET = -520.0
CS_HALF_WIDTH = 15.0
CS_HALF_HEIGHT = 30.0
NUM_T_SLOTS = 6
T_SLOT_OPENING = 9.0
T_SLOT_LOBED_ANGLE_1 = 54.1331978
T_SLOT_LOBED_ANGLE_2 = 125.8668022
T_SLOT_LOBED_ANGLE_3 = 144.1331978
T_SLOT_LOBED_ANGLE_4 = -144.1331978
T_SLOT_LOBED_ANGLE_5 = -125.8668022
T_SLOT_LOBED_ANGLE_6 = -54.1331978
T_SLOT_LOBED_ANGLE_7 = -35.8668022
T_SLOT_LOBED_ANGLE_8 = 35.8668022
T_SLOT_LOBED_OFFSET_1 = -3.43
T_SLOT_LOBED_OFFSET_2 = 18.43
T_SLOT_LOBED_OFFSET_3 = 11.57
T_SLOT_LOBED_OFFSET_4 = 3.43
T_SLOT_LOBED_OFFSET_5 = -18.43
T_SLOT_LOBED_OFFSET_6 = -11.57
T_SLOT_PRIMARY_RADIUS = 3.15
T_SLOT_FILLET_RADIUS = 1.0
PROFILE_WALL_STEP = 0.5
T_SLOT_FILLET_INC = 15.0
T_SLOT_BOUND_1 = -29.5
T_SLOT_BOUND_2 = -24.91
T_SLOT_BOUND_3 = -4.59
T_SLOT_BOUND_4 = 4.59
T_SLOT_BOUND_5 = 9.91
T_SLOT_BOUND_6 = -19.59
T_SLOT_BOUND_7 = -10.27
T_SLOT_BOUND_8 = 9.77
T_SLOT_BOUND_9 = 10.27
T_SLOT_BOUND_10 = 19.59
T_SLOT_BOUND_11 = 29.5
T_SLOT_BOUND_12 = 24.91
T_SLOT_BOUND_13 = -9.91
T_SLOT_BOUND_14 = -9.77

CC_HALF_WIDTH = 13.0
CC_HALF_HEIGHT = 9.0
CC_TRANS_X_1 = -9.23
CC_TRANS_X_2 = -4.73
CC_TRANS_X_3 = 4.73
CC_TRANS_X_4 = 9.23

CORNER_SCREW_DIA = 4.2
NUM_CORNER_SCREWS = 4
CORNER_SCREW_X = 11.5
CORNER_SCREW_Y = 26.5
CORNER_FILLET_R = 1.5
CORNER_FILLET_ANGLE = 90.0

# --- Document Setup ---
doc = App.newDocument("Extrusion")
doc.Label = "Extrusion_Model"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We will store the main dimensions here to allow easy editing if needed,
# though the script uses hardcoded values for the specific geometry requested.
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "ExtrusionLength", "Dimensions", "Length of extrusion")
params.ExtrusionLength = EXTRUSION_LENGTH
params.addProperty("App::PropertyLength", "ExtrusionStartOffset", "Dimensions", "Start offset")
params.ExtrusionStartOffset = EXTRUSION_START_OFFSET
params.addProperty("App::PropertyLength", "CSHalfWidth", "Dimensions", "Cross section half width")
params.CSHalfWidth = CS_HALF_WIDTH
params.addProperty("App::PropertyLength", "CSHalfHeight", "Dimensions", "Cross section half height")
params.CSHalfHeight = CS_HALF_HEIGHT
params.addProperty("App::PropertyLength", "TSlotOpening", "Dimensions", "T-slot opening width")
params.TSlotOpening = T_SLOT_OPENING
params.addProperty("App::PropertyLength", "ProfileWallStep", "Dimensions", "Profile wall step")
params.ProfileWallStep = PROFILE_WALL_STEP
params.addProperty("App::PropertyLength", "CornerFilletRadius", "Dimensions", "Corner fillet radius")
params.CornerFilletRadius = CORNER_FILLET_R
params.addProperty("App::PropertyLength", "CentralChannelHalfWidth", "Dimensions", "Central channel half width")
params.CentralChannelHalfWidth = CC_HALF_WIDTH
params.addProperty("App::PropertyLength", "CentralChannelHalfHeight", "Dimensions", "Central channel half height")
params.CentralChannelHalfHeight = CC_HALF_HEIGHT
params.addProperty("App::PropertyLength", "CornerScrewDiameter", "Dimensions", "Corner screw diameter")
params.CornerScrewDiameter = CORNER_SCREW_DIA
params.addProperty("App::PropertyLength", "CornerScrewXOffset", "Dimensions", "Corner screw X offset")
params.CornerScrewXOffset = CORNER_SCREW_X
params.addProperty("App::PropertyLength", "CornerScrewYOffset", "Dimensions", "Corner screw Y offset")
params.CornerScrewYOffset = CORNER_SCREW_Y

# --- Sketch 1: Outer Envelope ---
sketch_env = body.newObject("Sketcher::SketchObject", "Sketch_Envelope")
sketch_env.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_env.ConstrainToCurrentBody = True
sketch_env.ConstrainToCurrentPlane = True
sketch_env.Plane = "XY_Plane"
sketch_env.TechDraw_Plane = "XY_Plane"

# Define the rounded rectangle envelope
# Top-Left
sketch_env.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH, CS_HALF_HEIGHT, 0), App.Vector(-CS_HALF_WIDTH + CORNER_FILLET_R, CS_HALF_HEIGHT, 0)), False)
sketch_env.addGeometry(Part.Circle(App.Vector(-CS_HALF_WIDTH + CORNER_FILLET_R, CS_HALF_HEIGHT, 0), App.Vector(0, 0, 1), CORNER_FILLET_R), False)
sketch_env.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH + CORNER_FILLET_R, CS_HALF_HEIGHT - CORNER_FILLET_R, 0), App.Vector(-CS_HALF_WIDTH, CS_HALF_HEIGHT - CORNER_FILLET_R, 0)), False)
# Top-Right
sketch_env.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH - CORNER_FILLET_R, CS_HALF_HEIGHT, 0), App.Vector(CS_HALF_WIDTH, CS_HALF_HEIGHT, 0)), False)
sketch_env.addGeometry(Part.Circle(App.Vector(CS_HALF_WIDTH - CORNER_FILLET_R, CS_HALF_HEIGHT, 0), App.Vector(0, 0, 1), CORNER_FILLET_R), False)
sketch_env.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH - CORNER_FILLET_R, CS_HALF_HEIGHT - CORNER_FILLET_R, 0), App.Vector(CS_HALF_WIDTH, CS_HALF_HEIGHT - CORNER_FILLET_R, 0)), False)
# Bottom-Right
sketch_env.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH, -CS_HALF_HEIGHT + CORNER_FILLET_R, 0), App.Vector(CS_HALF_WIDTH - CORNER_FILLET_R, -CS_HALF_HEIGHT + CORNER_FILLET_R, 0)), False)
sketch_env.addGeometry(Part.Circle(App.Vector(CS_HALF_WIDTH - CORNER_FILLET_R, -CS_HALF_HEIGHT + CORNER_FILLET_R, 0), App.Vector(0, 0, 1), CORNER_FILLET_R), False)
sketch_env.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH - CORNER_FILLET_R, -CS_HALF_HEIGHT, 0), App.Vector(CS_HALF_WIDTH, -CS_HALF_HEIGHT, 0)), False)
# Bottom-Left
sketch_env.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH, -CS_HALF_HEIGHT + CORNER_FILLET_R, 0), App.Vector(-CS_HALF_WIDTH + CORNER_FILLET_R, -CS_HALF_HEIGHT + CORNER_FILLET_R, 0)), False)
sketch_env.addGeometry(Part.Circle(App.Vector(-CS_HALF_WIDTH + CORNER_FILLET_R, -CS_HALF_HEIGHT + CORNER_FILLET_R, 0), App.Vector(0, 0, 1), CORNER_FILLET_R), False)
sketch_env.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH + CORNER_FILLET_R, -CS_HALF_HEIGHT, 0), App.Vector(-CS_HALF_WIDTH, -CS_HALF_HEIGHT, 0)), False)

# Constraints for Envelope
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Top-Left corner
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Top-Right corner
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 3)) # Bottom-Right corner
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 4)) # Bottom-Left corner
sketch_env.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch_env.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 1))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 2))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 3))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 4))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 5))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 6))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 7))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 8))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 9))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 10))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 11))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 12))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 13))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 14))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 15))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 16))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 17))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 18))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 19))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 20))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 21))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 22))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 23))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 24))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 25))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 26))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 27))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 28))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 29))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 30))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 31))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 32))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 33))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 34))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 35))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 36))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 37))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 38))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 39))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 40))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 41))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 42))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 43))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 44))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 45))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 46))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 47))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 48))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 49))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 50))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 51))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 52))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 53))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 54))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 55))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 56))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 57))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, 58))
sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1,
