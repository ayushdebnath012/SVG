from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

# --- Configuration & Parameters ---
# Define a parameter set for the shaft sections to ensure parametric control
params = {
    "section_1_diameter": 10.0,
    "section_1_length": 40.0,
    "section_2_diameter": 15.0,
    "section_2_length": 30.0,
    "section_3_diameter": 20.0,
    "section_3_length": 40.0,
    "section_4_diameter": 40.0,
    "section_4_length": 10.0,
    "section_5_diameter": 30.0,
    "section_5_length": 20.0,
    "section_6_diameter": 25.0,
    "section_6_length": 25.0
}

# --- Document Setup ---
doc = App.newDocument("ShaftDesign")

# Create a PartDesign Body to hold the feature tree
body = doc.addObject("PartDesign::Body", "ShaftBody")

# Helper to add properties to the body
def addParam(name, value, description):
    prop = body.addProperty("App::PropertyFloat", name)
    prop.Description = description
    prop.Value = value
    return prop

# Add parameters to the body
addParam("section_1_diameter", params["section_1_diameter"], "Diameter of section 1")
addParam("section_1_length", params["section_1_length"], "Length of section 1")
addParam("section_2_diameter", params["section_2_diameter"], "Diameter of section 2")
addParam("section_2_length", params["section_2_length"], "Length of section 2")
addParam("section_3_diameter", params["section_3_diameter"], "Diameter of section 3")
addParam("section_3_length", params["section_3_length"], "Length of section 3")
addParam("section_4_diameter", params["section_4_diameter"], "Diameter of section 4")
addParam("section_4_length", params["section_4_length"], "Length of section 4")
addParam("section_5_diameter", params["section_5_diameter"], "Diameter of section 5")
addParam("section_5_length", params["section_5_length"], "Length of section 5")
addParam("section_6_diameter", params["section_6_diameter"], "Diameter of section 6")
addParam("section_6_length", params["section_6_length"], "Length of section 6")

# --- Sketch 1: Section 1 (Leftmost) ---
# Plane: XY at Z=0
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_Section1")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.Support = [("XY_Plane", [])]
r1 = params["section_1_diameter"] / 2.0
sketch1.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r1), False)

# --- Sketch 2: Section 2 ---
# Plane: XY at Z=section_1_length
sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_Section2")
sketch2.Placement = App.Placement(App.Vector(0, 0, params["section_1_length"]))
sketch2.Support = [("XY_Plane", [])]
r2 = params["section_2_diameter"] / 2.0
sketch2.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r2), False)

# --- Sketch 3: Section 3 ---
# Plane: XY at Z=section_1_length + section_2_length
sketch3 = body.newObject("Sketcher::SketchObject", "Sketch_Section3")
sketch3.Placement = App.Placement(App.Vector(0, 0, params["section_1_length"] + params["section_2_length"]))
sketch3.Support = [("XY_Plane", [])]
r3 = params["section_3_diameter"] / 2.0
sketch3.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r3), False)

# --- Sketch 4: Section 4 ---
# Plane: XY at Z=... + section_3_length
sketch4 = body.newObject("Sketcher::SketchObject", "Sketch_Section4")
sketch4.Placement = App.Placement(App.Vector(0, 0, params["section_1_length"] + params["section_2_length"] + params["section_3_length"]))
sketch4.Support = [("XY_Plane", [])]
r4 = params["section_4_diameter"] / 2.0
sketch4.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r4), False)

# --- Sketch 5: Section 5 ---
# Plane: XY at Z=... + section_4_length
sketch5 = body.newObject("Sketcher::SketchObject", "Sketch_Section5")
sketch5.Placement = App.Placement(App.Vector(0, 0, params["section_1_length"] + params["section_2_length"] + params["section_3_length"] + params["section_4_length"]))
sketch5.Support = [("XY_Plane", [])]
r5 = params["section_5_diameter"] / 2.0
sketch5.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r5), False)

# --- Sketch 6: Section 6 ---
# Plane: XY at Z=... + section_5_length
sketch6 = body.newObject("Sketcher::SketchObject", "Sketch_Section6")
sketch6.Placement = App.Placement(App.Vector(0, 0, params["section_1_length"] + params["section_2_length"] + params["section_3_length"] + params["section_4_length"] + params["section_5_length"]))
sketch6.Support = [("XY_Plane", [])]
r6 = params["section_6_diameter"] / 2.0
sketch6.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r6), False)

# --- PartDesign Pads (Extrusions) ---
# Pad 1
pad1 = body.newObject("PartDesign::Pad", "Pad_Section1")
pad1.Profile = sketch1
pad1.Length = params["section_1_length"]
pad1.Type = "Solid"

# Pad 2
pad2 = body.newObject("PartDesign::Pad", "Pad_Section2")
pad2.Profile = sketch2
pad2.Length = params["section_2_length"]
pad2.Type = "Solid"

# Pad 3
pad3 = body.newObject("PartDesign::Pad", "Pad_Section3")
pad3.Profile = sketch3
pad3.Length = params["section_3_length"]
pad3.Type = "Solid"

# Pad 4
pad4 = body.newObject("PartDesign::Pad", "Pad_Section4")
pad4.Profile = sketch4
pad4.Length = params["section_4_length"]
pad4.Type = "Solid"

# Pad 5
pad5 = body.newObject("PartDesign::Pad", "Pad_Section5")
pad5.Profile = sketch5
pad5.Length = params["section_5_length"]
pad5.Type = "Solid"

# Pad 6
pad6 = body.newObject("PartDesign::Pad", "Pad_Section6")
pad6.Profile = sketch6
pad6.Length = params["section_6_length"]
pad6.Type = "Solid"

# --- Finalization ---
# Force recomputation to ensure geometry is generated
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.parent / "answer.FCStd"

# Save to the required path
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
