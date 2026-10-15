import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

def main():
    # Create a new document
    doc = App.newDocument("SteppedShaft")
    
    # Create a PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Create named parameters. 
    # In FreeCAD 1.1, we use App::PropertyLength directly on the Body or a VarSet.
    # Using a VarSet is cleaner for grouping parameters.
    params = body.newObject("App::VarSet", "Parameters")
    
    # Section 1
    params.addProperty("App::PropertyLength", "s1_d", "Parameters", "Diameter Section 1")
    params.s1_d = 10.0
    params.addProperty("App::PropertyLength", "s1_l", "Parameters", "Length Section 1")
    params.s1_l = 40.0
    
    # Section 2
    params.addProperty("App::PropertyLength", "s2_d", "Parameters", "Diameter Section 2")
    params.s2_d = 15.0
    params.addProperty("App::PropertyLength", "s2_l", "Parameters", "Length Section 2")
    params.s2_l = 30.0
    
    # Section 3
    params.addProperty("App::PropertyLength", "s3_d", "Parameters", "Diameter Section 3")
    params.s3_d = 20.0
    params.addProperty("App::PropertyLength", "s3_l", "Parameters", "Length Section 3")
    params.s3_l = 40.0
    
    # Section 4
    params.addProperty("App::PropertyLength", "s4_d", "Parameters", "Diameter Section 4")
    params.s4_d = 40.0
    params.addProperty("App::PropertyLength", "s4_l", "Parameters", "Length Section 4")
    params.s4_l = 10.0
    
    # Section 5
    params.addProperty("App::PropertyLength", "s5_d", "Parameters", "Diameter Section 5")
    params.s5_d = 30.0
    params.addProperty("App::PropertyLength", "s5_l", "Parameters", "Length Section 5")
    params.s5_l = 20.0

    # --- Section 1: Base Cylinder ---
    # Sketch 1 on XY_Plane
    sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_S1")
    sketch1.Plane = "XY_Plane"
    sketch1.MapMode = "FlatFace"
    sketch1.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s1_d / 2.0))
    
    # Offset Plane 1 (Z = s1_l)
    offset1 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_1")
    offset1.Plane = "XY_Plane"
    offset1.Length = params.s1_l
    
    # --- Section 2 ---
    sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_S2")
    sketch2.Plane = "OffsetPlane_1"
    sketch2.MapMode = "FlatFace"
    sketch2.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s2_d / 2.0))
    
    offset2 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_2")
    offset2.Plane = "OffsetPlane_1"
    offset2.Length = params.s2_l
    
    # --- Section 3 ---
    sketch3 = body.newObject("Sketcher::SketchObject", "Sketch_S3")
    sketch3.Plane = "OffsetPlane_2"
    sketch3.MapMode = "FlatFace"
    sketch3.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s3_d / 2.0))
    
    offset3 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_3")
    offset3.Plane = "OffsetPlane_2"
    offset3.Length = params.s3_l
    
    # --- Section 4 ---
    sketch4 = body.newObject("Sketcher::SketchObject", "Sketch_S4")
    sketch4.Plane = "OffsetPlane_3"
    sketch4.MapMode = "FlatFace"
    sketch4.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s4_d / 2.0))
    
    offset4 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_4")
    offset4.Plane = "OffsetPlane_3"
    offset4.Length = params.s4_l
    
    # --- Section 5 ---
    sketch5 = body.newObject("Sketcher::SketchObject", "Sketch_S5")
    sketch5.Plane = "OffsetPlane_4"
    sketch5.MapMode = "FlatFace"
    sketch5.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s5_d / 2.0))
    
    # Create Offset Plane 5 for the end of the shaft (not strictly needed for the last pad but good for completeness)
    offset5 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_5")
    offset5.Plane = "OffsetPlane_4"
    offset5.Length = params.s5_l
    
    # --- Pads to connect sections ---
    # Pad 1: From XY_Plane to OffsetPlane_1
    pad1 = body.newObject("PartDesign::Pad", "Pad_S1")
    pad1.Profile = sketch1
    pad1.Length = params.s1_l
    pad1.Clean = True
    
    # Pad 2: From OffsetPlane_1 to OffsetPlane_2
    pad2 = body.newObject("PartDesign::Pad", "Pad_S2")
    pad2.Profile = sketch2
    pad2.Length = params.s2_l
    pad2.Clean = True
    
    # Pad 3: From OffsetPlane_2 to OffsetPlane_3
    pad3 = body.newObject("PartDesign::Pad", "Pad_S3")
    pad3.Profile = sketch3
    pad3.Length = params.s3_l
    pad3.Clean = True
    
    # Pad 4: From OffsetPlane_3 to OffsetPlane_4
    pad4 = body.newObject("PartDesign::Pad", "Pad_S4")
    pad4.Profile = sketch4
    pad4.Length = params.s4_l
    pad4.Clean = True
    
    # Pad 5: From OffsetPlane_4 to OffsetPlane_5
    pad5 = body.newObject("PartDesign::Pad", "Pad_S5")
    pad5.Profile = sketch5
    pad5.Length = params.s5_l
    pad5.Clean = True
    
    # Recompute to generate the geometry
    doc.recompute()
    
    # Save the file to the specific location required next to the script
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / "answer.FCStd"
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    main()
