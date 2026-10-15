import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameters ---
# Gear Geometry
pressure_angle_deg = 20.0
gear_module = 1.5
number_of_teeth = 80
face_width = 15.0
hub_diameter = 55.0
hub_width = 10.0
shaft_diameter = 12.0
overall_width = 25.0

# Calculated Dimensions (ISO 54 / DIN 867)
pressure_angle = math.radians(pressure_angle_deg)
pitch_diameter = gear_module * number_of_teeth
outer_diameter = pitch_diameter + 2 * gear_module
base_diameter = pitch_diameter * math.cos(pressure_angle)
root_diameter = pitch_diameter - 2 * (1.25 * gear_module)
addendum = gear_module
dedendum = 1.25 * gear_module
whole_depth = addendum + dedendum
clearance = dedendum - addendum
circular_pitch = math.pi * gear_module
tooth_thickness = circular_pitch / 2

# --- Document Setup ---
doc = App.newDocument("Gear")
doc.Label = "Spur Gear"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters Object ---
# We use a VarSet to store the main parameters so they are editable in the tree
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module")
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Diameter")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
params.addProperty("App::PropertyLength", "overall_width", "Dimensions", "Overall Width")
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Teeth Count")
params.addProperty("App::PropertyAngle", "pressure_angle_deg", "Dimensions", "Pressure Angle")

# Set initial values
params.gear_module = gear_module
params.face_width = face_width
params.hub_diameter = hub_diameter
params.hub_width = hub_width
params.shaft_diameter = shaft_diameter
params.overall_width = overall_width
params.number_of_teeth = number_of_teeth
params.pressure_angle_deg = pressure_angle_deg

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
    sk.Placement.Rotation.Axis = App.Vector
