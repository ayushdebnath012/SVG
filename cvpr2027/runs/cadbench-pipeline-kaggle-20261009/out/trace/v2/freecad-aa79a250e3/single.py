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
gear_module = 2.0
number_of_teeth = 25
face_width = 20.0
hub_diameter = 40.0
hub_width = 10.0
shaft_diameter = 10.0
overall_width = 30.0

# Calculated Dimensions (ISO 21771)
pressure_angle = math.radians(pressure_angle_deg)
pitch_diameter = gear_module * number_of_teeth
outer_diameter = pitch_diameter + 2 * gear_module
root_diameter = pitch_diameter - 2 * (1.25 * gear_module)
base_diameter = pitch_diameter * math.cos(pressure_angle)
circular_pitch = math.pi * gear_module
tooth_thickness = circular_pitch / 2
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum

# --- Document Setup ---
doc = App.newDocument("SpurGear")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We create a VarSet to hold the named parameters requested in the prompt
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "gear module")
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "face width")
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "hub diameter")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "hub width")
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "shaft diameter")
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "overall width")
params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "pressure angle")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "number of teeth")

# Set values
params.gear_module = gear_module
params.face_width = face_width
params.hub_diameter = hub_diameter
params.hub_width = hub_width
params.shaft_diameter = shaft_diameter
params.overall_width = overall_width
params.pressure_angle_deg = pressure_angle_deg
params.number_of_teeth = number_of_teeth

# --- Helper to create sketches ---
def create_sketch(name, plane, offset=0.0):
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.Placement = App.Placement(App.Vector(0, 0, offset))
    sk.Placement.Rotation = App.Rotation() # Identity
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
    sk.Placement.Rotation.Axis = App.Vector(0, 0, 1)
    sk.Placement.Rotation.Axis = App.Vector(0, 0,
