import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("SmoothShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")

# --- Parameters ---
# We will create a VarSet to hold our parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")

# Section 1
params.addProperty("App::PropertyLength", "section_1_diameter", "Dimensions", "Section 1 Diameter")
params.section_1_diameter = 10.0
params.addProperty("App::PropertyLength", "section_1_length", "Dimensions", "Section 1 Length")
params.section_1_length = 40.0

# Section 2
params.addProperty("App::PropertyLength", "section_2_diameter", "Dimensions", "Section 2 Diameter")
params.section_2_diameter = 15.0
params.addProperty("App::PropertyLength", "section_2_length", "Dimensions", "Section 2 Length")
params.section_2_length = 30.0

# Section 3
params.addProperty("App::PropertyLength", "section_3_diameter", "Dimensions", "Section 3 Diameter")
params.section_3_diameter = 20.0
params.addProperty("App::PropertyLength", "section_3_length", "Dimensions", "Section 3 Length")
params.section_3_length = 40.0

# Section 4
params.addProperty("App::PropertyLength", "section_4_diameter", "Dimensions", "Section 4 Diameter")
params.section_4_diameter = 40.0
params.addProperty("App::PropertyLength", "section_4_length", "Dimensions", "Section 4 Length")
params.section_4_length = 10.0

# Section 5
params.addProperty("App::PropertyLength", "section_5_diameter", "Dimensions", "Section 5 Diameter")
params.section_5_diameter = 30.0
params.addProperty("App::PropertyLength", "section_5_length", "Dimensions", "Section 5 Length")
params.section_5_length = 20.0

# Section 6
params.addProperty("App::PropertyLength", "section_6_diameter", "Dimensions", "Section 6 Diameter")
params.section_6_diameter = 25.0
params.addProperty("App::PropertyLength", "section_6_length", "Dimensions", "Section 6 Length")
params.section_6_length = 25.0

# --- Sketch 1: Base Section (Section 1) ---
# We build the shaft from the bottom up (Z+ direction)
# Sketch 1 defines the profile for Section 1
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_Section1")
sketch1.Placement = App.Placement() # Default placement is (0,0,0)
sketch1.Support = (doc.getObject("XY_Plane"), [])
sketch1.MapMode = "FlatFace"

# Add a circle for Section 1
# Center at (0,0), Radius = section_1_diameter / 2
r1 = params.section_1_diameter / 2.0
sketch1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r1), False)

# Add constraints to center the circle
# Constraint: Center on X axis (Y=0)
sketch1.addConstraint(Sketcher.Constraint("CenterY", 0, 1))
# Constraint: Center on Y axis (X=0)
sketch1.addConstraint(Sketcher.Constraint("CenterX", 0, 1))

# Pad Section 1
pad1 = body.newObject("PartDesign::Pad", "Pad_Section1")
pad1.Profile = sketch1
pad1.Length = params.section_1_length
pad1.Type = "Solid"
pad1.Midplane = False
pad1.Reversed = False

# --- Sketch 2: Section 2 ---
# Position: Z = section_1_length
sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_Section2")
sketch2.Placement = App.Placement(App.Vector(0, 0, params.section_1_length))
sketch2.Support = (doc.getObject("XY_Plane"), [])
sketch2.MapMode = "FlatFace"

r2 = params.section_2_diameter / 2.0
sketch2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r2), False)
sketch2.addConstraint(Sketcher.Constraint("CenterY", 0, 1))
sketch2.addConstraint(Sketcher.Constraint("CenterX", 0, 1))

# Pad Section 2
pad2 = body.newObject("PartDesign::Pad", "Pad_Section2")
pad2.Profile = sketch2
pad2.Length = params.section_2_length
pad2.Type = "Solid"
pad2.Midplane = False
pad2.Reversed = False

# --- Sketch 3: Section 3 ---
# Position: Z = section_1_length + section_2_length
z3 = params.section_1_length + params.section_2_length
sketch3 = body.newObject("Sketcher::SketchObject", "Sketch_Section3")
sketch3.Placement = App.Placement(App.Vector(0, 0, z3))
sketch3.Support = (doc.getObject("XY_Plane"), [])
sketch3.MapMode = "FlatFace"

r3 = params.section_3_diameter / 2.0
sketch3.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r3), False)
sketch3.addConstraint(Sketcher.Constraint("CenterY", 0, 1))
sketch3.addConstraint(Sketcher.Constraint("CenterX", 0, 1))

# Pad Section 3
pad3 = body.newObject("PartDesign::Pad", "Pad_Section3")
pad3.Profile = sketch3
pad3.Length = params.section_3_length
pad3.Type = "Solid"
pad3.Midplane = False
pad3.Reversed = False

# --- Sketch 4: Section 4 ---
# Position: Z = section_1 + section_2 + section_3
z4 = z3 + params.section_3_length
sketch4 = body.newObject("Sketcher::SketchObject", "Sketch_Section4")
sketch4.Placement = App.Placement(App.Vector(0, 0, z4))
sketch4.Support = (doc.getObject("XY_Plane"), [])
sketch4.MapMode = "FlatFace"

r4 = params.section_4_diameter / 2.0
sketch4.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r4), False)
sketch4.addConstraint(Sketcher.Constraint("CenterY", 0, 1))
sketch4.addConstraint(Sketcher.Constraint("CenterX", 0, 1))

# Pad Section 4
pad4 = body.newObject("PartDesign::Pad", "Pad_Section4")
pad4.Profile = sketch4
pad4.Length = params.section_4_length
pad4.Type = "Solid"
pad4.Midplane = False
pad4.Reversed = False

# --- Sketch 5: Section 5 ---
# Position: Z = previous + section_4_length
z5 = z4 + params.section_4_length
sketch5 = body.newObject("Sketcher::SketchObject", "Sketch_Section5")
sketch5.Placement = App.Placement(App.Vector(0, 0, z5))
sketch5.Support = (doc.getObject("XY_Plane"), [])
sketch5.MapMode = "FlatFace"

r5 = params.section_5_diameter / 2.0
sketch5.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r5), False)
sketch5.addConstraint(Sketcher.Constraint("CenterY", 0, 1))
sketch5.addConstraint(Sketcher.Constraint("CenterX", 0, 1))

# Pad Section 5
pad5 = body.newObject("PartDesign::Pad", "Pad_Section5")
pad5.Profile = sketch5
pad5.Length = params.section_5_length
pad5.Type = "Solid"
pad5.Midplane = False
pad5.Reversed = False

# --- Sketch 6: Section 6 ---
# Position: Z = previous + section_5_length
z6 = z5 + params.section_5_length
sketch6 = body.newObject("Sketcher::SketchObject", "Sketch_Section6")
sketch6.Placement = App.Placement(App.Vector(0, 0, z6))
sketch6.Support = (doc.getObject("XY_Plane"), [])
sketch6.MapMode = "FlatFace"

r6 = params.section_6_diameter / 2.0
sketch6.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r6), False)
sketch6.addConstraint(Sketcher.Constraint("CenterY", 0, 1))
sketch6.addConstraint(Sketcher.Constraint("CenterX", 0, 1))

# Pad Section 6
pad6 = body.newObject("PartDesign::Pad", "Pad_Section6")
pad6.Profile = sketch6
pad6.Length = params.section_6_length
pad6.Type = "Solid"
pad6.Midplane = False
pad6.Reversed = False

# --- Finalize ---
# Recompute to generate the solid
doc.recompute()

# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Save the document
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
