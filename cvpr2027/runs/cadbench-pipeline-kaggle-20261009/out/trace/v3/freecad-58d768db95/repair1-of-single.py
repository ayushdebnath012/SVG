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
# Coincident corners
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) 
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) 
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 3)) 
sketch_env.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 4)) 
# Horizontal/Vertical lines
sketch_env.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch_env.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
# Point on unconstrained line constraints for all segments
for i in range(1, 9):
    sketch_env.addConstraint(Sketcher.Constraint("PointOnUnconstrainedLine", 0, 1, 1, i))

# --- Sketch 2: Central Channel ---
sketch_cc = body.newObject("Sketcher::SketchObject", "Sketch_CentralChannel")
sketch_cc.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_cc.ConstrainToCurrentBody = True
sketch_cc.ConstrainToCurrentPlane = True
sketch_cc.Plane = "XY_Plane"

# Central Channel Geometry
# Top half
# Start at left waist
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_HALF_WIDTH, 0, 0), App.Vector(CC_HALF_WIDTH, 0, 0)), False)
# Diagonal up to transition 2
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_HALF_WIDTH, 0, 0), App.Vector(CC_TRANS_X_2, CC_HALF_HEIGHT, 0)), False)
# Horizontal to transition 3
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_TRANS_X_2, CC_HALF_HEIGHT, 0), App.Vector(CC_TRANS_X_3, CC_HALF_HEIGHT, 0)), False)
# Diagonal up to transition 4
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_TRANS_X_3, CC_HALF_HEIGHT, 0), App.Vector(CC_TRANS_X_4, CC_HALF_HEIGHT, 0)), False)
# Horizontal to right waist
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_TRANS_X_4, CC_HALF_HEIGHT, 0), App.Vector(CS_HALF_WIDTH, CC_HALF_HEIGHT, 0)), False)
# Diagonal down to top right corner
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH, CC_HALF_HEIGHT, 0), App.Vector(CS_HALF_WIDTH, CS_HALF_HEIGHT, 0)), False)
# Top edge
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH, CS_HALF_HEIGHT, 0), App.Vector(-CS_HALF_WIDTH, CS_HALF_HEIGHT, 0)), False)
# Diagonal down to top left corner
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH, CS_HALF_HEIGHT, 0), App.Vector(-CS_HALF_WIDTH, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0)), False)
# Horizontal to left waist
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_1, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0)), False)
# Diagonal down to transition 1
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_1, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_2, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0)), False)
# Horizontal to transition 3 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_2, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_3, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0)), False)
# Diagonal down to transition 4 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_3, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_4, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0)), False)
# Horizontal to left waist (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_4, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0), App.Vector(-CC_HALF_WIDTH, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0)), False)
# Diagonal down to bottom left corner
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_HALF_WIDTH, CS_HALF_HEIGHT - CC_HALF_HEIGHT, 0), App.Vector(-CC_HALF_WIDTH, -CC_HALF_HEIGHT, 0)), False)
# Bottom edge
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_HALF_WIDTH, -CC_HALF_HEIGHT, 0), App.Vector(CC_HALF_WIDTH, -CC_HALF_HEIGHT, 0)), False)
# Diagonal up to bottom right corner
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_HALF_WIDTH, -CC_HALF_HEIGHT, 0), App.Vector(CC_HALF_WIDTH, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to right waist (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_HALF_WIDTH, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(CC_TRANS_X_1, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Diagonal up to transition 2 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_TRANS_X_1, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(CC_TRANS_X_2, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to transition 3 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_TRANS_X_2, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(CC_TRANS_X_3, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Diagonal up to transition 4 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_TRANS_X_3, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(CC_TRANS_X_4, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to right waist (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CC_TRANS_X_4, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(CS_HALF_WIDTH, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Diagonal up to bottom right corner (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH, -CC_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(CS_HALF_WIDTH, -CS_HALF_HEIGHT, 0)), False)
# Bottom edge (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(CS_HALF_WIDTH, -CS_HALF_HEIGHT, 0), App.Vector(-CS_HALF_WIDTH, -CS_HALF_HEIGHT, 0)), False)
# Diagonal up to bottom left corner (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH, -CS_HALF_HEIGHT, 0), App.Vector(-CS_HALF_WIDTH, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to left waist (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CS_HALF_WIDTH, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(-CC_HALF_WIDTH, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Diagonal up to transition 1 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_HALF_WIDTH, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_1, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to transition 2 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_1, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_2, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to transition 3 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_2, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_3, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to transition 4 (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_3, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(-CC_TRANS_X_4, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Horizontal to left waist (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_TRANS_X_4, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(-CC_HALF_WIDTH, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0)), False)
# Diagonal up to bottom left corner (mirrored)
sketch_cc.addGeometry(Part.LineSegment(App.Vector(-CC_HALF_WIDTH, -CS_HALF_HEIGHT + CC_HALF_HEIGHT, 0), App.Vector(-CC_HALF_WIDTH, -CC_HALF_HEIGHT, 0)), False)

# Constraints for Central Channel
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 3))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 4))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 5))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 6))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 7))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 8))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 9))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 10))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 11))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 12))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 13))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 14))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 15))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 16))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 17))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 18))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 19))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 20))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 21))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 22))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 23))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 24))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 25))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 26))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 27))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 28))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 29))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 30))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 31))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 32))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 33))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 34))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 35))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 36))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 37))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 38))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 39))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 40))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 41))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 42))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 43))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 44))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 45))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 46))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 47))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 48))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 49))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 50))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 51))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 52))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 53))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 54))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 55))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 56))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 57))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 58))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 59))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 60))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 61))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 62))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 63))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 64))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 65))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 66))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 67))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 68))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 69))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 70))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 71))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 72))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 73))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 74))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 75))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 76))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 77))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 78))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 79))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 80))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 81))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 82))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 83))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 84))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 85))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 86))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 87))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 88))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 89))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 90))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 91))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 92))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 93))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 94))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 95))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 96))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 97))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 98))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 99))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 100))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 101))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 102))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 103))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 104))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 105))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 106))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 107))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 108))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 109))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 110))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 111))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 112))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 113))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 114))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 115))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 116))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 117))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 118))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 119))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 120))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 121))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 122))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 123))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 124))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 125))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 126))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 127))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 128))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 129))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 130))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 131))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 132))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 133))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 134))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 135))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 136))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 137))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 138))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 139))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 140))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 141))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 142))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 143))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 144))
sketch_cc.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 145))
sketch_cc.addConstraint(Sketch
