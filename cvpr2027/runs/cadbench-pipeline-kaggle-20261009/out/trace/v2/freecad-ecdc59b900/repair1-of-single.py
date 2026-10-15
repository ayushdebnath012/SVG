import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("Shaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")

# Define the 7 sections with their specific diameters and lengths
# Using expressions to drive geometry
params.addProperty("App::PropertyLength", "section_1_diameter", "Dimensions", "Diameter of section 1")
params.section_1_diameter = 10.0

params.addProperty("App::PropertyLength", "section_1_length", "Dimensions", "Length of section 1")
params.section_1_length = 20.0

params.addProperty("App::PropertyLength", "section_2_diameter", "Dimensions", "Diameter of section 2")
params.section_2_diameter = 15.0

params.addProperty("App::PropertyLength", "section_2_length", "Dimensions", "Length of section 2")
params.section_2_length = 30.0

params.addProperty("App::PropertyLength", "section_3_diameter", "Dimensions", "Diameter of section 3")
params.section_3_diameter = 20.0

params.addProperty("App::PropertyLength", "section_3_length", "Dimensions", "Length of section 3")
params.section_3_length = 40.0

params.addProperty("App::PropertyLength", "section_4_diameter", "Dimensions", "Diameter of section 4")
params.section_4_diameter = 40.0

params.addProperty("App::PropertyLength", "section_4_length", "Dimensions", "Length of section 4")
params.section_4_length = 10.0

params.addProperty("App::PropertyLength", "section_5_diameter", "Dimensions", "Diameter of section 5")
params.section_5_diameter = 30.0

params.addProperty("App::PropertyLength", "section_5_length", "Dimensions", "Length of section 5")
params.section_5_length = 20.0

params.addProperty("App::PropertyLength", "section_6_diameter", "Dimensions", "Diameter of section 6")
params.section_6_diameter = 25.0

params.addProperty("App::PropertyLength", "section_6_length", "Dimensions", "Length of section 6")
params.section_6_length = 25.0

params.addProperty("App::PropertyLength", "section_7_diameter", "Dimensions", "Diameter of section 7")
params.section_7_diameter = 20.0

params.addProperty("App::PropertyLength", "section_7_length", "Dimensions", "Length of section 7")
params.section_7_length = 20.0

# Helper function to create a sketch and pad for a section
def create_section(section_num, prev_pad, diameter_prop, length_prop):
    # Create sketch
    sketch_name = f"Sketch_Section{section_num}"
    sketch = body.newObject("Sketcher::SketchObject", sketch_name)
    
    # Determine support: XY plane for first section, Top face of previous pad for others
    if section_num == 1:
        sketch.Support = (doc.getObject("XY_Plane"), [])
        sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    else:
        # Get the top face of the previous pad
        # In PartDesign, the 'Top' face of a Pad feature is accessible via the feature itself
        # We use the previous pad object as the support
        sketch.Support = (prev_pad, ["Top"])
        # The placement is handled by the MapMode and Support automatically in most cases,
        # but we ensure it's on the correct plane.
        sketch.Placement = App.Placement(App.Vector(0, 0, 0))

    sketch.MapMode = "FlatFace"
    
    # Add circle geometry
    radius = diameter_prop / 2.0
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)
    
    # Add constraints
    sketch.Constraints = [
        Sketcher.Constraint("Point", 0, 2, "XY"),
        Sketcher.Constraint("Radius", 0, 1, diameter_prop)
    ]
    
    # Create Pad
    pad_name = f"Pad_Section{section_num}"
    pad = body.newObject("PartDesign::Pad", pad_name)
    pad.Profile = sketch
    pad.Length = length_prop
    pad.Type = "Solid"
    pad.MidPlane = False
    pad.Reversed = False
    
    return pad

# Create Section 1
pad1 = create_section(1, None, params.section_1_diameter, params.section_1_length)

# Create Sections 2-7
pad2 = create_section(2, pad1, params.section_2_diameter, params.section_2_length)
pad3 = create_section(3, pad2, params.section_3_diameter, params.section_3_length)
pad4 = create_section(4, pad3, params.section_4_diameter, params.section_4_length)
pad5 = create_section(5, pad4, params.section_5_diameter, params.section_5_length)
pad6 = create_section(6, pad5, params.section_6_diameter, params.section_6_length)
pad7 = create_section(7, pad6, params.section_7_diameter, params.section_7_length)

# Recompute the document to generate the solid
doc.recompute()

# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Save the document
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
