import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("SteppedShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.addObject("App::DocumentObjectGroup", "BodyGroup")
doc.addObject("App::DocumentObjectGroup", "BodyGroup").addObject("PartDesign::Body", "Body")
doc.recompute()

# Define parameters as named properties on the Body for editability
# We will add these as App::PropertyLength and App::PropertyLengthList
# Note: In FreeCAD 1.1, we can add properties directly to the Body object
# to make them editable parameters.

# Helper to add a parameter
def add_param(obj, name, value, unit="mm"):
    obj.addProperty("App::PropertyLength", name, "Parameters", f"{name} ({unit})")
    setattr(obj, name, value)

# Add section parameters
for i in range(1, 10):
    add_param(body, f"shaft_section_{i}_diameter", 0.0)
    add_param(body, f"shaft_section_{i}_length", 0.0)

# Set the specific values from the prompt
# Section 1
body.shaft_section_1_diameter = 10.0
body.shaft_section_1_length = 20.0
# Section 2
body.shaft_section_2_diameter = 15.0
body.shaft_section_2_length = 30.0
# Section 3
body.shaft_section_3_diameter = 20.0
body.shaft_section_3_length = 40.0
# Section 4
body.shaft_section_4_diameter = 40.0
body.shaft_section_4_length = 10.0
# Section 5
body.shaft_section_5_diameter = 30.0
body.shaft_section_5_length = 20.0
# Section 6
body.shaft_section_6_diameter = 25.0
body.shaft_section_6_length = 25.0
# Section 7
body.shaft_section_7_diameter = 20.0
body.shaft_section_7_length = 20.0
# Section 8
body.shaft_section_8_diameter = 50.0
body.shaft_section_8_length = 20.0
# Section 9
body.shaft_section_9_diameter = 30.0
body.shaft_section_9_length = 10.0

# Create the first sketch on the XY plane
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch1")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Support = (doc.getObject("XY_Plane"), [])
sketch1.MapMode = "FlatFace"

# Add a circle for the first section
# Center at (0,0), radius = diameter/2
r1 = body.shaft_section_1_diameter / 2.0
sketch1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r1), False)
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch1.addConstraint(Sketcher.Constraint("Radius", 0, r1))

# Pad the first section
pad1 = body.newObject("PartDesign::Pad", "Pad1")
pad1.Profile = sketch1
pad1.Length = body.shaft_section_1_length
pad1.Type = "Solid"
pad1.Midplane = False
pad1.Reversed = False

# Create subsequent sketches and pads
# We need to position each sketch at the end of the previous one along Z
current_z = body.shaft_section_1_length

for i in range(2, 10):
    # Create sketch
    sketch = body.newObject("Sketcher::SketchObject", f"Sketch{i}")
    sketch.Placement = App.Placement(App.Vector(0, 0, current_z))
    sketch.Support = (doc.getObject("XY_Plane"), [])
    sketch.MapMode = "FlatFace"
    
    # Add circle
    r = body.shaft_section_{i}_diameter / 2.0
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r), False)
    sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    sketch.addConstraint(Sketcher.Constraint("Radius", 0, r))
    
    # Pad
    pad = body.newObject("PartDesign::Pad", f"Pad{i}")
    pad.Profile = sketch
    pad.Length = body.shaft_section_{i}_length
    pad.Type = "Solid"
    pad.Midplane = False
    pad.Reversed = False
    
    # Update current Z for next iteration
    current_z += body.shaft_section_{i}_length

# Recompute to ensure all features are built
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
