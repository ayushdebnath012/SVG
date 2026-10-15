import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Initialize the document
doc = App.newDocument("SteppedShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Define parameters for each shaft section
# Format: Name -> [Diameter, Length]
sections_data = [
    (10.0, 20.0), (15.0, 30.0), (20.0, 40.0), (40.0, 10.0),
    (30.0, 20.0), (25.0, 25.0), (20.0, 20.0), (50.0, 20.0),
    (30.0, 10.0), (50.0, 20.0), (30.0, 10.0)
]

# Helper to add a parameter to the Body
def add_param(body, name, value):
    param_obj = body.newObject("App::Parameter", name)
    param_obj.BaseValue = f"{value}mm"
    param_obj.Type = "Length"
    return name

# Register all parameters
for i, (d, l) in enumerate(sections_data):
    add_param(body, f"Diam_{i+1}", d)
    add_param(body, f"Len_{i+1}", l)

# Current position along X axis
current_x = 0.0

# Create the shaft sections
for i, (d, l) in enumerate(sections_data):
    d_name = f"Diam_{i+1}"
    l_name = f"Len_{i+1}"
    
    # Create a plane at current_x, oriented YZ (normal X)
    # We create a Part::Plane object. In FreeCAD 1.1, this is done via App::Plane or Part::Plane.
    # We use App::Plane to create a geometric plane object.
    plane = doc.addObject("Part::Plane", f"Plane_Section_{i+1}")
    plane.Placement = App.Placement(App.Vector(current_x, 0, 0))
    # The plane created this way is perpendicular to the Z axis by default? 
    # No, App::Plane creates a plane at the given position with a default orientation (usually XY).
    # We need to rotate it to be YZ (normal X).
    # Rotation: Rotate 90 deg around Y axis.
    plane.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 90)
    
    # Create Sketch on this plane
    sketch = body.newObject("Sketcher::SketchObject", f"Sketch_Section_{i+1}")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0)) # Local to the plane
    sketch.Support = [(plane, [""]), []], []
    sketch.MapMode = "FlatFace"
    sketch.Tolerance = 0.001
    sketch.ConstraintTolerance = 0.001
    sketch.Closed = True
    
    # Add Circle with diameter = D
    # Radius = D/2
    radius = d / 2.0
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), True)
    sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, radius))
    
    # Create Pad
    pad = body.newObject("PartDesign::Pad", f"Pad_Section_{i+1}")
    pad.Profile = sketch
    pad.Length = l
    pad.Type = "Solid"
    # Direction: (1, 0, 0) is +X. 
    # Since the plane is YZ (normal X), and we want to extend along +X, this is correct.
    pad.Direction = (1, 0, 0)
    
    # Update current position
    current_x += l

# Recompute the document to generate the solid
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")
doc.saveAs(str(output_path))
