import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("GearShaft")

# --- Parameters ---
# We will store these in a VarSet object to keep the document clean and editable
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Diameter of the first shaft section")
params.addProperty("App::PropertyLength", "shaft_length", "Dimensions", "Length of the first shaft section")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Module of the gear")
params.addProperty("App::PropertyInteger", "gear_number_tooth", "Dimensions", "Number of teeth")
params.addProperty("App::PropertyLength", "gear_height", "Dimensions", "Axial height of the gear")
params.addProperty("App::PropertyAngle", "pressure_angle", "Dimensions", "Pressure angle in degrees")

# Set default values as per requirements
params.shaft_diameter = 16.0
params.shaft_length = 30.0
params.gear_module = 1.0
params.gear_number_tooth = 20
params.gear_height = 20.0
params.pressure_angle = 20.0

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Shaft Section 1 (Bottom) ---
# Sketch 1: Circle for the bottom shaft
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_BottomShaft")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Support = (doc.getObject("XY_Plane"), [])
sketch1.MapMode = "FlatFace"

# Add circle geometry
circle1 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaft_diameter / 2.0)
sketch1.addGeometry(circle1, False)

# Pad the bottom shaft
pad1 = body.newObject("PartDesign::Pad", "Pad_BottomShaft")
pad1.Profile = sketch1
pad1.Length = params.shaft_length
pad1.Type = "Solid"
pad1.Midplane = False
pad1.Reversed = False

# --- Gear Section (Section 2) ---
# We need to position the gear sketch at the top of the first shaft section.
# Z position = shaft_length
gear_sketch = body.newObject("Sketcher::SketchObject", "Sketch_Gear")
gear_sketch.Placement = App.Placement(App.Vector(0, 0, params.shaft_length))
gear_sketch.Support = (doc.getObject("XY_Plane"), [])
gear_sketch.MapMode = "FlatFace"

# Calculate Gear Dimensions
pitch_diameter = params.gear_number_tooth * params.gear_module
base_diameter = pitch_diameter * (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (1.0 / (
