from pathlib import Path
import FreeCAD as App
import Part
import PartDesign
import Sketcher
import math

# Define parameters as requested
EXTRUSION_LENGTH = 1040.0
EXTRUSION_AXIS_START_OFFSET = -520.0
CROSS_SECTION_HALF_WIDTH = 15.0
CROSS_SECTION_HALF_HEIGHT = 30.0

# T-Slot Parameters
NUMBER_OF_T_SLOTS = 6
T_SLOT_OPENING_WIDTH = 9.0
T_SLOT_LOBED_ARC_ANGLE_1 = 54.1331978
T_SLOT_LOBED_ARC_ANGLE_2 = 125.8668022
T_SLOT_LOBED_ARC_ANGLE_3 = 144.1331978
T_SLOT_LOBED_ARC_ANGLE_4 = -144.1331978
T_SLOT_LOBED_ARC_ANGLE_5 = -125.8668022
T_SLOT_LOBED_ARC_ANGLE_6 = -54.1331978
T_SLOT_LOBED_ARC_ANGLE_7 = -35.8668022
T_SLOT_LOBED_ARC_ANGLE_8 = 35.8668022
T_SLOT_LOBED_ARC_CENTER_OFFSET_1 = -3.43
T_SLOT_LOBED_ARC_CENTER_OFFSET_2 = 18.43
T_SLOT_LOBED_ARC_CENTER_OFFSET_3 = 11.57
T_SLOT_LOBED_ARC_CENTER_OFFSET_4 = 3.43
T_SLOT_LOBED_ARC_CENTER_OFFSET_5 = -18.43
T_SLOT_LOBED_ARC_CENTER_OFFSET_6 = -11.57
T_SLOT_PRIMARY_ARC_RADIUS = 3.15
T_SLOT_FILLET_RADIUS = 1.0
PROFILE_WALL_STEP = 0.5
T_SLOT_FILLET_ANGLE_INCREMENT = 15.0
T_SLOT_BOUNDARY_STEP_VALUE_1 = -29.5
T_SLOT_BOUNDARY_STEP_VALUE_2 = -24.91
T_SLOT_BOUNDARY_STEP_VALUE_3 = -4.59
T_SLOT_BOUNDARY_STEP_VALUE_4 = 4.59
T_SLOT_BOUNDARY_STEP_VALUE_5 = 9.91
T_SLOT_BOUNDARY_STEP_VALUE_6 = -19.59
T_SLOT_BOUNDARY_STEP_VALUE_7 = -10.27
T_SLOT_BOUNDARY_STEP_VALUE_8 = 9.77
T_SLOT_BOUNDARY_STEP_VALUE_9 = 10.27
T_SLOT_BOUNDARY_STEP_VALUE_10 = 19.59
T_SLOT_BOUNDARY_STEP_VALUE_11 = 29.5
T_SLOT_BOUNDARY_STEP_VALUE_12 = 24.91
T_SLOT_BOUNDARY_STEP_VALUE_13 = -9.91
T_SLOT_BOUNDARY_STEP_VALUE_14 = -9.77

# Central Channel Parameters
CENTRAL_CHANNEL_HALF_WIDTH = 13.0
CENTRAL_CHANNEL_HALF_HEIGHT = 9.0
CENTRAL_CHANNEL_TRANSITION_X_OFFSET_1 = -9.23
CENTRAL_CHANNEL_TRANSITION_X_OFFSET_2 = -4.73
CENTRAL_CHANNEL_TRANSITION_X_OFFSET_3 = 4.73
CENTRAL_CHANNEL_TRANSITION_X_OFFSET_4 = 9.23

# Corner Screw Port Parameters
CORNER_SCREW_PORT_DIAMETER = 4.2
NUMBER_OF_CORNER_SCREW_PORTS = 4
CORNER_SCREW_PORT_CENTER_X_OFFSET = 11.5
CORNER_SCREW_PORT_CENTER_Y_OFFSET = 26.5
PERIMETER_CORNER_FILLET_ARC_RADIUS = 1.5
PERIMETER_CORNER_FILLET_CENTRAL_ANGLE = 90.0

# --- Setup Document ---
doc = App.newDocument("Extrusion")
doc.Label = "Aluminum_Extrusion"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create Parameters Object
params = body.newObject("App::FeaturePython", "Parameters")
# Since FeaturePython is not standard in headless API for simple params, we will use App::PropertyLength directly on the Body or specific objects if needed.
# However, the prompt suggests using App::VarSet or similar. In standard FreeCAD 1.1 headless, we often just set properties on the Body or sketch objects directly for simplicity unless complex inter-dependencies exist.
# To strictly follow "driven by named document objects", we will create a specific object for parameters if possible, or rely on the fact that the script defines constants.
# The prompt example used `body.newObject("App::VarSet", "Parameters")`. This type might not exist in 1.1 headless without GUI. 
# We will stick to setting values on the sketch objects and the body itself, or using standard App::FeaturePython if available, but for robust headless scripting, direct property assignment is often safer.
# Let's create a simple FeaturePython script to hold parameters if needed, or just define them as local variables for the construction phase.
# The prompt says "Derive every output path from __file__... call doc.recompute()...".
# We will define a class to hold parameters to make them editable objects.

class ParameterSet(App::FeaturePython):
    def Execute(self):
        pass
    def GetProperties(self):
        p = []
        p.append(App::Property("App::PropertyLength", "ExtrusionLength", "Dimensions", "Length of extrusion"))
        p.append(App::Property("App::PropertyLength", "CrossSectionHalfWidth", "Dimensions", "Half width"))
        p.append(App::Property("App::PropertyLength", "CrossSectionHalfHeight", "Dimensions", "Half height"))
        p.append(App::Property("App::PropertyLength", "TSlotOpeningWidth", "Dimensions", "T slot width"))
        p.append(App::Property("App::PropertyLength", "PerimeterCornerFilletArcRadius", "Dimensions", "Corner fillet"))
        p.append(App::Property("App::PropertyLength", "CentralChannelHalfWidth", "Dimensions", "Channel width"))
        p.append(App::Property("App::PropertyLength", "CentralChannelHalfHeight", "Dimensions", "Channel height"))
        p.append(App::Property("App::PropertyLength", "CornerScrewPortDiameter", "Dimensions", "Screw port diameter"))
        p.append(App::Property("App::PropertyLength", "ProfileWallStep", "Dimensions", "Wall step"))
        p.append(App::Property("App::PropertyLength", "TSlotPrimaryArcRadius", "Dimensions", "Lobe radius"))
        p.append(App::Property("App::PropertyLength", "TSlotFilletRadius", "Dimensions", "Fillet radius"))
        p.append(App::Property("App::PropertyLength", "TSlotLobedArcCenterOffset1", "Dimensions", "Lobe offset 1"))
        p.append(App::Property("App::PropertyLength", "TSlotLobedArcCenterOffset2", "Dimensions", "Lobe offset 2"))
        p.append(App::Property("App::PropertyLength", "TSlotLobedArcCenterOffset3", "Dimensions", "Lobe offset 3"))
        p.append(App::Property("App::PropertyLength", "TSlotLobedArcCenterOffset4", "Dimensions", "Lobe offset 4"))
        p.append(App::Property("App::PropertyLength", "TSlotLobedArcCenterOffset5", "Dimensions", "Lobe offset 5"))
        p.append(App::Property("App::PropertyLength", "TSlotLobedArcCenterOffset6", "Dimensions", "Lobe offset 6"))
        p.append(App::Property("App::PropertyLength", "CentralChannelTransitionXOffset1", "Dimensions", "Transition 1"))
        p.append(App::Property("App::PropertyLength", "CentralChannelTransitionXOffset2", "Dimensions", "Transition 2"))
        p.append(App::Property("App::PropertyLength", "CentralChannelTransitionXOffset3", "Dimensions", "Transition 3"))
        p.append(App::Property("App::PropertyLength", "CentralChannelTransitionXOffset4", "Dimensions", "Transition 4"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue1", "Dimensions", "Boundary 1"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue2", "Dimensions", "Boundary 2"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue3", "Dimensions", "Boundary 3"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue4", "Dimensions", "Boundary 4"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue5", "Dimensions", "Boundary 5"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue6", "Dimensions", "Boundary 6"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue7", "Dimensions", "Boundary 7"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue8", "Dimensions", "Boundary 8"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue9", "Dimensions", "Boundary 9"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue10", "Dimensions", "Boundary 10"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue11", "Dimensions", "Boundary 11"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue12", "Dimensions", "Boundary 12"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue13", "Dimensions", "Boundary 13"))
        p.append(App::Property("App::PropertyLength", "TSlotBoundaryStepValue14", "Dimensions", "Boundary 14"))
        return p

params_obj = body.newObject("App::FeaturePython", "Parameters")
params_obj.addProperty("App::PropertyString", "Label", "Parameters", "Label")
params_obj.addProperty("App::PropertyString", "Description", "Parameters", "Description")

# Set initial values
params_obj.ExtrusionLength = EXTRUSION_LENGTH
params_obj.CrossSectionHalfWidth = CROSS_SECTION_HALF_WIDTH
params_obj.CrossSectionHalfHeight = CROSS_SECTION_HALF_HEIGHT
params_obj.TSlotOpeningWidth = T_SLOT_OPENING_WIDTH
params_obj.PerimeterCornerFilletArcRadius = PERIMETER_CORNER_FILLET_ARC_RADIUS
params_obj.CentralChannelHalfWidth = CENTRAL_CHANNEL_HALF_WIDTH
params_obj.CentralChannelHalfHeight = CENTRAL_CHANNEL_HALF_HEIGHT
params_obj.CornerScrewPortDiameter = CORNER_SCREW_PORT_DIAMETER
params_obj.ProfileWallStep = PROFILE_WALL_STEP
params_obj.TSlotPrimaryArcRadius = T_SLOT_PRIMARY_ARC_RADIUS
params_obj.TSlotFilletRadius = T_SLOT_FILLET_RADIUS
params_obj.TSlotLobedArcCenterOffset1 = T_SLOT_LOBED_ARC_CENTER_OFFSET_1
params_obj.TSlotLobedArcCenterOffset2 = T_SLOT_LOBED_ARC_CENTER_OFFSET_2
params_obj.TSlotLobedArcCenterOffset3 = T_SLOT_LOBED_ARC_CENTER_OFFSET_3
params_obj.TSlotLobedArcCenterOffset4 = T_SLOT_LOBED_ARC_CENTER_OFFSET_4
params_obj.TSlotLobedArcCenterOffset5 = T_SLOT_LOBED_ARC_CENTER_OFFSET_5
params_obj.TSlotLobedArcCenterOffset6 = T_SLOT_LOBED_ARC_CENTER_OFFSET_6
params_obj.CentralChannelTransitionXOffset1 = CENTRAL_CHANNEL_TRANSITION_X_OFFSET_1
params_obj.CentralChannelTransitionXOffset2 = CENTRAL_CHANNEL_TRANSITION_X_OFFSET_2
params_obj.CentralChannelTransitionXOffset3 = CENTRAL_CHANNEL_TRANSITION_X_OFFSET_3
params_obj.CentralChannelTransitionXOffset4 = CENTRAL_CHANNEL_TRANSITION_X_OFFSET_4
params_obj.TSlotBoundaryStepValue1 = T_SLOT_BOUNDARY_STEP_VALUE_1
params_obj.TSlotBoundaryStepValue2 = T_SLOT_BOUNDARY_STEP_VALUE_2
params_obj.TSlotBoundaryStepValue3 = T_SLOT_BOUNDARY_STEP_VALUE_3
params_obj.TSlotBoundaryStepValue4 = T_SLOT_BOUNDARY_STEP_VALUE_4
params_obj.TSlotBoundaryStepValue5 = T_SLOT_BOUNDARY_STEP_VALUE_5
params_obj.TSlotBoundaryStepValue6 = T_SLOT_BOUNDARY_STEP_VALUE_6
params_obj.TSlotBoundaryStepValue7 = T_SLOT_BOUNDARY_STEP_VALUE_7
params_obj.TSlotBoundaryStepValue8 = T_SLOT_BOUNDARY_STEP_VALUE_8
params_obj.TSlotBoundaryStepValue9 = T_SLOT_BOUNDARY_STEP_VALUE_9
params_obj.TSlotBoundaryStepValue10 = T_SLOT_BOUNDARY_STEP_VALUE_10
params_obj.TSlotBoundaryStepValue11 = T_SLOT_BOUNDARY_STEP_VALUE_11
params_obj.TSlotBoundaryStepValue12 = T_SLOT_BOUNDARY_STEP_VALUE_12
params_obj.TSlotBoundaryStepValue13 = T_SLOT_BOUNDARY_STEP_VALUE_13
params_obj.TSlotBoundaryStepValue14 = T_SLOT_BOUNDARY_STEP_VALUE_14

# Create Main Sketch on XY plane
sketch_main = body.newObject("Sketcher::SketchObject", "MainSketch")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
# Attach to XY plane
sketch_main.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch_main.MapMode = "FlatFace"
sketch_main.Constrain = True
sketch_main.Locked = False

# Helper function to create geometry
def add_line(sk, p1, p2, locked=False):
    sk.addGeometry(Part.LineSegment(p1, p2), locked)
    return len(sk.Geometry) - 1

def add_circle(sk, center, axis, radius, locked=False):
    sk.addGeometry(Part.Circle(center, axis, radius), locked)
    return len(sk.Geometry) - 1

def add_ellipse(sk, center, axis_x, radius_x, axis_y, radius_y, locked=False):
    sk.addGeometry(Part.Ellipse(center, axis_x, radius_x, axis_y, radius_y), locked)
    return len(sk.Geometry) - 1

# --- 1. Envelope ---
# Envelope: Rounded rectangle
# Width = 2 * CrossSectionHalfWidth = 30
# Height = 2 * CrossSectionHalfHeight = 60
# Radius = PerimeterCornerFilletArcRadius = 1.5

# Points for rounded rect
# Top-Left, Top-Right, Bottom-Right, Bottom-Left
# Center is (0,0)
# X goes from -15 to 15, Y from -30 to 30

# Top edge
add_line(sketch_main, App.Vector(-CROSS_SECTION_HALF_WIDTH, CROSS_SECTION_HALF_HEIGHT - PERIMETER_CORNER_FILLET_ARC_RADIUS, 0),
         App.Vector(CROSS_SECTION_HALF_WIDTH, CROSS_SECTION_HALF_HEIGHT - PERIMETER_CORNER_FILLET_ARC_RADIUS, 0), True)
# Right edge
add_line(sketch_main, App.Vector(CROSS_SECTION_HALF_WIDTH - PERIMETER_CORNER_FILLET_ARC_RADIUS, CROSS_SECTION_HALF_HEIGHT - PERIMETER_CORNER_FILLET_ARC_RADIUS, 0),
         App.Vector(CROSS_SECTION_HALF_WIDTH - PERIMETER_CORNER_FILLET_ARC_RADIUS, -CROSS_SECTION_HALF_HEIGHT + PERIMETER_CORNER_FILLET_ARC_RADIUS, 0), True)
# Bottom edge
add_line(sketch_main, App.Vector(CROSS_SECTION_HALF_WIDTH - PERIMETER_CORNER_FILLET_ARC_RADIUS, -CROSS_SECTION_HALF_HEIGHT + PERIMETER_CORNER_FILLET_ARC_RADIUS, 0),
         App.Vector(-CROSS_SECTION_HALF_WIDTH + PERIMETER_CORNER_FILLET_ARC_RADIUS, -CROSS_SECTION_HALF_HEIGHT + PERIMETER_CORNER_FILLET_ARC_RADIUS, 0), True)
# Left edge
add_line(sketch_main, App.Vector(-CROSS_SECTION_HALF_WIDTH + PERIMETER_CORNER_FILLET_ARC_RADIUS, -CROSS_SECTION_HALF_HEIGHT + PERIMETER_CORNER_FILLET_ARC_RADIUS, 0),
         App.Vector(-CROSS_SECTION_HALF_WIDTH + PERIMETER_CORNER_FILLET_ARC_RADIUS, CROSS_SECTION_HALF_HEIGHT - PERIMETER_CORNER_FILLET_ARC_RADIUS, 0), True)

# Corners
corner_radius = PERIMETER_CORNER_FILLET_ARC_RADIUS
add_circle(sketch_main, App.Vector(CROSS_SECTION_HALF_WIDTH - corner_radius, CROSS_SECTION_HALF_HEIGHT - corner_radius, 0), 
           App.Vector(0, 0, 1), corner_radius, True)
add_circle(sketch_main, App.Vector(CROSS_SECTION_HALF_WIDTH - corner_radius, -CROSS_SECTION_HALF_HEIGHT + corner_radius, 0), 
           App.Vector(0, 0, 1), corner_radius, True)
add_circle(sketch_main, App.Vector(-CROSS_SECTION_HALF_WIDTH + corner_radius, -CROSS_SECTION_HALF_HEIGHT + corner_radius, 0), 
           App.Vector(0, 0, 1), corner_radius, True)
add_circle(sketch_main, App.Vector(-CROSS_SECTION_HALF_WIDTH + corner_radius, CROSS_SECTION_HALF_HEIGHT - corner_radius, 0), 
           App.Vector(0, 0, 1), corner_radius, True)

# Constraints for envelope
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1)) # Top left start
sketch_main.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 1)) # Top left end (same point logic handled by sketch solver usually)
# Better constraints: Coincident to origin
sketch_main.addConstraint(Sketcher.Constraint("Point", 0, 1, "XY")) # Top Left start
sketch_main.addConstraint(Sketcher.Constraint("Point", 0, 4, "XY")) # Bottom Left start
sketch_main.addConstraint(S
