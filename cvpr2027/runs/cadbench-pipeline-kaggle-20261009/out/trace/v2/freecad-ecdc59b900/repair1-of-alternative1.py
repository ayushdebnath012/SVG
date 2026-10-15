import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("Shaft")

# 1. Define Parameters
# We create a VarSet to hold our named parameters.
params = doc.addObject("App::VarSet", "Parameters")

# Define the 14 parameters for the 7 sections
# Format: property_name, label_group, value
param_def = [
    ("section_1_diameter", "Dimensions", 10.0),
    ("section_1_length", "Dimensions", 20.0),
    ("section_2_diameter", "Dimensions", 15.0),
    ("section_2_length", "Dimensions", 30.0),
    ("section_3_diameter", "Dimensions", 20.0),
    ("section_3_length", "Dimensions", 40.0),
    ("section_4_diameter", "Dimensions", 40.0),
    ("section_4_length", "Dimensions", 10.0),
    ("section_5_diameter", "Dimensions", 30.0),
    ("section_5_length", "Dimensions", 20.0),
    ("section_6_diameter", "Dimensions", 25.0),
    ("section_6_length", "Dimensions", 25.0),
    ("section_7_diameter", "Dimensions", 20.0),
    ("section_7_length", "Dimensions", 20.0),
]

# Add properties to the parameter set
for name, group, val in param_def:
    params.addProperty(f"App::PropertyLength", name, "Dimensions", f"{name} length/diameter")
    setattr(params, name, val)

# 2. Create the Body
body = doc.addObject("PartDesign::Body", "Body")

# 3. Create Sketches and Features
# We need 7 sketches, one for each step.
# We will place them along the Z-axis.

# Helper to get the current Z-position
current_z = 0.0

for i in range(1, 8):
    # --- Create Sketch ---
    sketch_name = f"Sketch_Section{i}"
    sketch = body.newObject("Sketcher::SketchObject", sketch_name)
    
    # Place the sketch at current_z on the XY plane (which is the default local plane of the sketch)
    # We use a placement to move the sketch along Z.
    sketch.Placement = App.Placement(App.Vector(0, 0, current_z))
    
    # Get parameter values
    diam = getattr(params, f"section_{i}_diameter")
    radius = diam / 2.0
    
    # Add Circle Geometry
    # We create the circle with the calculated radius. 
    # To ensure it is driven by the parameter in the tree, we add a constraint.
    circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
    sketch.addGeometry(circle, False)
    
    # Add Constraints:
    # 1. Center the circle on the sketch origin (Coincident center to X and Y axes)
    #    Geometry 1 is the circle. Point 2 is its center.
    #    Object 3 is X_Axis, Object 4 is Y_Axis (standard FreeCAD sketcher objects).
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 3, 2)) # Center to X axis
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 3, 3)) # Center to Y axis
    
    # 2. Fix the radius to the parameter value
    #    We use an expression or a constraint. A constraint is more robust for the tree structure.
    #    Constraint: Radius of geometry 1, point 1 equals the parameter value.
    sketch.addConstraint(Sketcher.Constraint("Radius", 1, 1, params, f"section_{i}_diameter/2"))
    
    # --- Create Pad ---
    pad = body.newObject("PartDesign::Pad", f"Pad_Section{i}")
    pad.Profile = sketch
    pad.Length = getattr(params, f"section_{i}_length")
    pad.Midplane = False # Extrude positive Z
    pad.Reversed = False
    
    # Update current Z for next sketch
    current_z += getattr(params, f"section_{i}_length")

# 4. Cleanup default planes/axes if they clutter the tree (optional but clean)
# We only remove them if they exist and are not used as supports (though our sketches use local placement)
# In FreeCAD 1.1, the default planes are often created automatically.
# We will leave them as they are standard supports, but ensure our sketches don't depend on them 
# by using explicit Placement (which we did).

# 5. Recompute and Save
doc.recompute()

# Save to the specific path required by the prompt
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
