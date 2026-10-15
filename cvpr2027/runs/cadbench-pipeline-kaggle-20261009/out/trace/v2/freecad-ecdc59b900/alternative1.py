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
body.Type = "Body"

# 3. Create Sketches and Features
# We need 7 sketches, one for each step.
# We will place them along the Z-axis.

# Helper to get the current Z-position
current_z = 0.0

for i in range(1, 8):
    # --- Create Sketch ---
    sketch_name = f"Sketch_Section{i}"
    sketch = body.newObject("Sketcher::SketchObject", sketch_name)
    sketch.Placement = App.Placement(App.Vector(0, 0, current_z))
    sketch.Placement.Rotation = App.Rotation() # Identity rotation
    sketch.Placement.Rotation.X = 0
    sketch.Placement.Rotation.Y = 0
    sketch.Placement.Rotation.Z = 0
    sketch.Placement.Rotation.Quaternion = App.Vector(0, 0, 0, 1)
    
    # Attach to XY plane relative to the sketch's placement (which is at current_z)
    # The sketch plane is always local to the sketch object's placement.
    # We need to define the circle geometry.
    
    # Get parameter values
    diam = getattr(params, f"section_{i}_diameter")
    radius = diam / 2.0
    
    # Add Circle Geometry
    circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
    sketch.addGeometry(circle, False)
    
    # Add Constraint: Circle must be centered on the origin of the sketch plane
    # In Sketcher, we usually constrain the center point (1, 2) to the origin axes (3, 4) or simply use the center constraint.
    # However, the simplest robust way in FreeCAD 1.1 headless for a centered circle on the sketch plane:
    # We constrain the center point of the circle to the X and Y axes of the sketch plane.
    # Note: Sketcher constraints indices are relative to the sketch.
    # Geometry 1 is the circle. 
    # We can use the constraint "Coincident" between the circle center and the axes, 
    # OR use the "Center" constraint type if available, or simply constrain the center point.
    # Standard approach: Constrain center point (1, 1) to X-axis (3, 2) and Y-axis (3, 3)? 
    # Actually, for a circle on a plane, we constrain the center point to the origin.
    # Let's use the explicit center constraint logic:
    # Sketcher Constraint: "Center" is not always exposed simply by index in headless without knowing exact object types.
    # Robust method: Constrain the circle center (1, 2) to the X-Axis (3, 2) and Y-Axis (3, 3) intersection? 
    # Easier: Constrain the center point (1, 2) to the X-Axis (3, 2) and the Y-Axis (3, 3).
    # Actually, the standard way is to constrain the center point (1,2) to the X-Axis (3,2) and the Y-Axis (3,3).
    # Let's try: Coincident 1,2 to 3,2 (X axis) and 1,2 to 3,3 (Y axis).
    # Wait, indices: 1=Circle, 2=Center of circle (Point). 3=X_Axis, 4=Y_Axis.
    # Let's use the constraint "Center" on the sketch object properties if possible, 
    # but generically: Coincident 1,2 to 3,2 and 1,2 to 3,3.
    # Actually, let's use the standard constraint: "Center" on the circle geometry?
    # Let's use explicit Coincident to axes.
    # X Axis is usually object 3. Y Axis is usually object 4.
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 3, 2)) # Center to X axis
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 3, 3)) # Center to Y axis
    # Add a fixed radius constraint to prevent scaling
    sketch.addConstraint(Sketcher.Constraint("Radius", 1, 1, radius)) 
    # Wait, if we define the circle with a specific radius in the Part object, 
    # we might not need a radius constraint if we don't scale the sketch. 
    # But to be safe and parametric:
    # Let's remove the explicit radius in Part.Circle and use a constraint, 
    # or keep the Part.Circle and add a constraint to lock it.
    # Better approach for parametric: Create circle with variable radius and add constraint.
    # Re-doing circle creation with variable radius:
    # sketch.addGeometry(Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), radius), False)
    # Then add constraint: sketch.addConstraint(Sketcher.Constraint("Radius", 1, 1, radius))
    # This is redundant if the circle is already created with 'radius'.
    # However, if we want to drive 'radius' from the parameter, we should create the circle with a fixed size 
    # and then add a constraint that overrides it? No, that's complex.
    # Simplest: Create circle with the parameter value. It is already parameterized via the variable 'radius' 
    # which is just a float at runtime, but the FCStd needs an expression or a constraint to be editable.
    # To make it strictly parametric in the tree:
    # 1. Create circle with a dummy size or expression.
    # 2. Add constraint "Radius" referencing the parameter.
    # Let's do that to ensure the 'Dimensions' group in the tree drives it.
    
    # Re-create geometry with a default size for the constraint to reference
    sketch.removeGeometry(sketch.Geometry[0])
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 10.0), False) # Dummy
    sketch.addConstraint(Sketcher.Constraint("Radius", 1, 1, params, f"section_{i}_diameter/2"))
    
    # --- Create Pad ---
    pad = body.newObject("PartDesign::Pad", f"Pad_Section{i}")
    pad.Profile = sketch
    pad.Length = getattr(params, f"section_{i}_length")
    pad.Midplane = False # Extrude positive Z
    pad.Reversed = False
    
    # Update current Z for next sketch
    current_z += getattr(params, f"section_{i}_length")

# 4. Cleanup
doc.removeObject("XY_Plane")
doc.removeObject("XZ_Plane")
doc.removeObject("YZ_Plane")
doc.removeObject("X_Axis")
doc.removeObject("Y_Axis")
doc.removeObject("Z_Axis")

# 5. Recompute and Save
doc.recompute()

# Save to the specific path required by the prompt
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
