import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document named "Washer"
doc = App.newDocument("Washer")

# 1. Create Parameters for dimensioning
# We use App::VarSet as the container to hold named properties that drive geometry
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outside_diameter", "Dimensions", "Outer diameter of the washer")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter (hole) of the washer")
params.addProperty("App::PropertyLength", "thickness", "Dimensions", "Thickness of the washer")

# Set initial values
params.outside_diameter = 4.0
params.inner_diameter = 1.7
params.thickness = 0.3

# 2. Create the PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# 3. Create the Base Sketch on XY Plane
base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0)) # Ensure no rotation relative to XY
base_sketch.Supports = (doc.getObject("XY_Plane"), [""])
base_sketch.ConstrainAuto = False

# Create a reference circle for the outer diameter
# We will construct the geometry using Part primitives and then constrain them
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outside_diameter / 2.0)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)

# Add geometry to sketch
base_sketch.addGeometry(outer_circle, True)
base_sketch.addGeometry(inner_circle, True)

# Constrain circles to be concentric at origin
base_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 0, 0, 1, 1)) # Axis of circle 0 and 1
base_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 0, 0, 0, 0)) # Center of circle 0 at origin
base_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 1, 0, 0, 0)) # Center of circle 1 at origin

# 4. Create the Pad Feature (Extrusion)
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.thickness
# Ensure we extrude from the sketch plane downwards or upwards consistently
# By default Pad extrudes in Z+.
# Note: In FreeCAD 1.1, expressions are handled via setExpression
pad.setExpression("Length", "Parameters.thickness")

# 5. Save the initial base model
script_path = Path(__file__).resolve()
base_file = script_path.parent / f"{script_path.stem}_base.FCStd"
doc.recompute()
doc.saveAs(str(base_file))

# 6. Modify parameters to create the final "Edit" version (optional step for demonstration of editability, 
#    but we will just proceed to save the final result with the requested dimensions immediately).
#    The script ensures the structure is editable.

# 7. Final Recompute and Save as the requested output
doc.recompute()
output_file = script_path.parent / f"{script_path.stem}.FCStd"
doc.saveAs(str(output_file))

# Cleanup
App.closeDocument(doc.Name)
