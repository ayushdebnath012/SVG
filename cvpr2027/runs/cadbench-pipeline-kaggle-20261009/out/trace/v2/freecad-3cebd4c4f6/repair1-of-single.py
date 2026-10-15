import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("Key")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
# In FreeCAD 1.1, Body.Placement is a PropertyPlacement, not a constructor call
body.Placement = App.Placement()

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Key diameter")
params.addProperty("App::PropertyLength", "height", "Dimensions", "Key height")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Key length")

# Set default values based on the prompt
params.diameter = 5.0
params.height = 3.0
params.length = 10.0

# Create the base sketch on the XY plane
# We need to reference the XY_Plane which is usually available in the document
# If not, we can create a Plane, but standard practice assumes XY_Plane exists or we use the Body's default plane.
# However, Sketcher::SketchObject requires an AttachmentSupport.
# Let's try to get XY_Plane. If it doesn't exist, we might need to create it or use a workaround.
# Standard FreeCAD documents usually have XY_Plane, XZ_Plane, YZ_Plane in the root.
xy_plane = doc.getObject("XY_Plane")
if not xy_plane:
    # Fallback: Create a plane if missing (though rare in fresh docs)
    # Actually, for a robust script, we can create a Plane object.
    plane = doc.addObject("Part::Plane", "XY_Plane")
    plane.Placement = App.Placement()
    xy_plane = plane

sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement()
sketch.AttachmentSupport = (xy_plane, [])
sketch.MapMode = "FlatFace"
sketch.ConstrainAuto = True
sketch.ConstrainFully = True

# Add a circle for the key profile
# Center at (0,0), radius = diameter / 2
radius = params.diameter / 2.0
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
sketch.addGeometry(circle, False)

# Add constraints to fully define the sketch
# Fix center to origin
sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
# Fix radius to parameter
# Note: The second argument to Constraint is the geometry index in the sketch.
# We added one circle, so index is 0.
# The third argument is the value.
sketch.addConstraint(Sketcher.Constraint("Radius", 0, radius, params.diameter / 2.0))

# Create the Pad feature to extrude the key
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = params.length
pad.Type = "Solid"
pad.Reversed = False
pad.MidPlane = False

# Drive the length from the parameter
pad.setExpression("Length", "Parameters.length")

# Recompute to generate the solid
doc.recompute()

# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Ensure the directory exists
output_path.parent.mkdir(parents=True, exist_ok=True)

# Save the document
doc.saveAs(str(output_path))
print(f"Model saved to: {output_path}")
