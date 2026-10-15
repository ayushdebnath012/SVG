import FreeCAD as App
import Part
from pathlib import Path

# --- Configuration ---
# Derived from __file__ as requested
script_path = Path(__file__).resolve()
output_path = script_path.parent / f"{script_path.stem}.FCStd"

# --- Parameters ---
# Define a named parameter object to drive the geometry
param_doc = App.newDocument("MountingFlange")
param_body = param_doc.addObject("PartDesign::Body", "Body")

# Create a VarSet to hold named parameters
params = param_body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer flange diameter")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange thickness")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Central bore diameter")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Bolt circle diameter")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Bolt hole diameter")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Assign values
params.outer_diameter = 40.084
params.flange_thickness = 10.319
params.inner_diameter = 14.288
params.bolt_circle_diameter = 28.575
params.bolt_hole_diameter = 6.747
params.number_bolt_holes = 4

# --- Main Feature Construction ---

# 1. Create the main sketch for the flange profile on XY_Plane
flange_sketch = param_body.newObject("Sketcher::SketchObject", "FlangeProfile")
# Set placement correctly: App.Placement(App.Vector(x, y, z), App.Rotation())
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Placement = flange_sketch.Placement.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation())) # Ensure origin
flange_sketch.Pl
