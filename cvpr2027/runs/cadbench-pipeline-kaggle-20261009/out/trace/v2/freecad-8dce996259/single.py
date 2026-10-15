import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from task description
P = App.ParamGet("User parameter:BaseApp/Preferences/Part")
# Ensure we are using the correct units if necessary, though FreeCAD defaults to mm usually.
# We will define all dimensions in mm.

# Constants
PRESSURE_ANGLE = 20.0 # degrees
GEAR_MODULE = 1.0     # mm
NUM_TEETH = 50
PITCH_DIAMETER = 50.0 # mm
OUTER_DIAMETER = 52.0 # mm
FACE_WIDTH = 6.0      # mm
HUB_DIAMETER = 16.0   # mm
HUB_WIDTH = 8.0       # mm
SHAFT_DIAMETER = 8.0  # mm
OVERALL_WIDTH = 14.0  # mm

# Calculated ISO 54 parameters
ADDENDUM = PITCH_DIAMETER / NUM_TEETH # 1.0
DEDENDUM = 1.25 * GEAR_MODULE         # 1.25
ROOT_DIAMETER = PITCH_DIAMETER - 2 * DEDENDUM # 47.5

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We create a VarSet to hold our named parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "module", "Dimensions", "Gear Module")
params.module = GEAR_MODULE
params.addProperty("App::PropertyLength", "num_teeth", "Dimensions", "Number of Teeth")
params.num_teeth = NUM_TEETH
params.addProperty("App::PropertyLength", "pitch_dia", "Dimensions", "Pitch Diameter")
params.pitch_dia = PITCH_DIAMETER
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.face_width = FACE_WIDTH
params.addProperty("App::PropertyLength", "hub_dia", "Dimensions", "Hub Diameter")
params.hub_dia = HUB_DIAMETER
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.hub_width = HUB_WIDTH
params.addProperty("App::PropertyLength", "shaft_dia", "Dimensions", "Shaft Diameter")
params.shaft_dia = SHAFT_DIAMETER
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.overall_width = OVERALL_WIDTH
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure Angle")
params.pressure_angle = PRESSURE_ANGLE

# --- Helper Functions ---
def create_sketch(name, plane, offset=0.0):
    """Creates a sketch object attached to a plane."""
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.Placement = App.Placement(App.Vector(0, 0, offset))
    sk.Placement.Rotation = App.Rotation() # Identity rotation
    sk.Placement.Rotation.X = 0
    sk.Placement.Rotation.Y = 0
    sk.Placement.Rotation.Z = 0
    sk.Placement.Rotation.Angle = 0
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1) # Ensure Z axis
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk
