import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("Shaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

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

# Create the base sketch on the XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.Support = (doc.getObject("XY_Plane"), [])
sketch.MapMode = "FlatFace"

# Add circle geometry for the shaft profile
# We use a single circle that will be extruded. 
# The sketch will be used for the first section, and subsequent sections will be built using Pads with offsets.
# However, to keep it strictly parametric and simple, we can create one sketch with the first section,
# then use Pads to extend it, and then use a second sketch or a different approach for the steps.
# 
# Better approach for a stepped shaft in PartDesign:
# 1. Create a sketch with the profile of the FIRST section (or the largest one if we were subtracting, but here we add).
# 2. Actually, the cleanest way for a stepped shaft is to create a sketch with the profile of the FIRST section.
# 3. Then use a Pad to create the first section.
# 4. Then create a new sketch on the top face of the first section for the second section, etc.
# 
# Alternative (more robust for scripting):
# Create one sketch with the profile of the FIRST section.
# Pad it to length L1.
# Create a new sketch on the top face of the resulting solid.
# Draw a circle with Diameter D2.
# Pad it to length L2.
# ... repeat for all 7 sections.

# Section 1
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_Section1")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Support = (doc.getObject("XY_Plane"), [])
sketch1.MapMode = "FlatFace"
sketch1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_1_diameter / 2.0), False)
sketch1.Constraints = [
    Sketcher.Constraint("Point", 0, 2, "XY"),
    Sketcher.Constraint("Radius", 0, 1, params.section_1_diameter / 2.0)
]

pad1 = body.newObject("PartDesign::Pad", "Pad_Section1")
pad1.Profile = sketch1
pad1.Length = params.section_1_length
pad1.Type = "Solid"
pad1.MidPlane = False
pad1.Reversed = False

# Section 2
sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_Section2")
sketch2.Placement = App.Placement(App.Vector(0, 0, params.section_1_length))
sketch2.Support = (pad1, ["Top"])
sketch2.MapMode = "FlatFace"
sketch2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_2_diameter / 2.0), False)
sketch2.Constraints = [
    Sketcher.Constraint("Point", 0, 2, "XY"),
    Sketcher.Constraint("Radius", 0, 1, params.section_2_diameter / 2.0)
]

pad2 = body.newObject("PartDesign::Pad", "Pad_Section2")
pad2.Profile = sketch2
pad2.Length = params.section_2_length
pad2.Type = "Solid"
pad2.MidPlane = False
pad2.Reversed = False

# Section 3
sketch3 = body.newObject("Sketcher::SketchObject", "Sketch_Section3")
sketch3.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length))
sketch3.Support = (pad2, ["Top"])
sketch3.MapMode = "FlatFace"
sketch3.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_3_diameter / 2.0), False)
sketch3.Constraints = [
    Sketcher.Constraint("Point", 0, 2, "XY"),
    Sketcher.Constraint("Radius", 0, 1, params.section_3_diameter / 2.0)
]

pad3 = body.newObject("PartDesign::Pad", "Pad_Section3")
pad3.Profile = sketch3
pad3.Length = params.section_3_length
pad3.Type = "Solid"
pad3.MidPlane = False
pad3.Reversed = False

# Section 4
sketch4 = body.newObject("Sketcher::SketchObject", "Sketch_Section4")
sketch4.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length))
sketch4.Support = (pad3, ["Top"])
sketch4.MapMode = "FlatFace"
sketch4.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_4_diameter / 2.0), False)
sketch4.Constraints = [
    Sketcher.Constraint("Point", 0, 2, "XY"),
    Sketcher.Constraint("Radius", 0, 1, params.section_4_diameter / 2.0)
]

pad4 = body.newObject("PartDesign::Pad", "Pad_Section4")
pad4.Profile = sketch4
pad4.Length = params.section_4_length
pad4.Type = "Solid"
pad4.MidPlane = False
pad4.Reversed = False

# Section 5
sketch5 = body.newObject("Sketcher::SketchObject", "Sketch_Section5")
sketch5.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length + params.section_4_length))
sketch5.Support = (pad4, ["Top"])
sketch5.MapMode = "FlatFace"
sketch5.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_5_diameter / 2.0), False)
sketch5.Constraints = [
    Sketcher.Constraint("Point", 0, 2, "XY"),
    Sketcher.Constraint("Radius", 0, 1, params.section_5_diameter / 2.0)
]

pad5 = body.newObject("PartDesign::Pad", "Pad_Section5")
pad5.Profile = sketch5
pad5.Length = params.section_5_length
pad5.Type = "Solid"
pad5.MidPlane = False
pad5.Reversed = False

# Section 6
sketch6 = body.newObject("Sketcher::SketchObject", "Sketch_Section6")
sketch6.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length + params.section_4_length + params.section_5_length))
sketch6.Support = (pad5, ["Top"])
sketch6.MapMode = "FlatFace"
sketch6.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_6_diameter / 2.0), False)
sketch6.Constraints = [
    Sketcher.Constraint("Point", 0, 2, "XY"),
    Sketcher.Constraint("Radius", 0, 1, params.section_6_diameter / 2.0)
]

pad6 = body.newObject("PartDesign::Pad", "Pad_Section6")
pad6.Profile = sketch6
pad6.Length = params.section_6_length
pad6.Type = "Solid"
pad6.MidPlane = False
pad6.Reversed = False

# Section 7
sketch7 = body.newObject("Sketcher::SketchObject", "Sketch_Section7")
sketch7.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length + params.section_4_length + params.section_5_length + params.section_6_length))
sketch7.Support = (pad6, ["Top"])
sketch7.MapMode = "FlatFace"
sketch7.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_7_diameter / 2.0), False)
sketch7.Constraints = [
    Sketcher.Constraint("Point", 0, 2, "XY"),
    Sketcher.Constraint("Radius", 0, 1, params.section_7_diameter / 2.0)
]

pad7 = body.newObject("PartDesign::Pad", "Pad_Section7")
pad7.Profile = sketch7
pad7.Length = params.section_7_length
pad7.Type = "Solid"
pad7.MidPlane = False
pad7.Reversed = False

# Recompute the document to generate the solid
doc.recompute()

# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Save the document
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
