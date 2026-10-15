import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

def main():
    # Create a new document
    doc = App.newDocument("SteppedShaft")
    
    # Create a PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Create named parameters for all dimensions
    params = body.newObject("App::Property", "Parameters")
    params.addProperty("App::PropertyLength", "s1_d", "Parameters", "Diameter Section 1")
    params.s1_d = 10.0
    
    params.addProperty("App::PropertyLength", "s1_l", "Parameters", "Length Section 1")
    params.s1_l = 40.0
    
    params.addProperty("App::PropertyLength", "s2_d", "Parameters", "Diameter Section 2")
    params.s2_d = 15.0
    
    params.addProperty("App::PropertyLength", "s2_l", "Parameters", "Length Section 2")
    params.s2_l = 30.0
    
    params.addProperty("App::PropertyLength", "s3_d", "Parameters", "Diameter Section 3")
    params.s3_d = 20.0
    
    params.addProperty("App::PropertyLength", "s3_l", "Parameters", "Length Section 3")
    params.s3_l = 40.0
    
    params.addProperty("App::PropertyLength", "s4_d", "Parameters", "Diameter Section 4")
    params.s4_d = 40.0
    
    params.addProperty("App::PropertyLength", "s4_l", "Parameters", "Length Section 4")
    params.s4_l = 10.0
    
    params.addProperty("App::PropertyLength", "s5_d", "Parameters", "Diameter Section 5")
    params.s5_d = 30.0
    
    params.addProperty("App::PropertyLength", "s5_l", "Parameters", "Length Section 5")
    params.s5_l = 20.0

    # --- Section 1: Base Cylinder (Z = -35.0) ---
    # Position: Center Z = -35.0 (half of s1_l + s2_l + s3_l + s4_l + s5_l is 140, so total half is 70? 
    # Let's calculate offsets from one end to ensure continuity.
    # Let's place the transition from Sec 1 to Sec 2 at Z = 0.
    # Sec 1: Z from -40 to 0.
    
    sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_S1")
    sketch1.Plane = "XY_Plane"
    sketch1.Reference = (doc.getObject("XY_Plane"), [""])
    sketch1.MapMode = "FlatFace"
    sketch1.LengthConstraint = True
    sketch1.WidthConstraint = True
    sketch1.ConstrainGeometry = True
    sketch1.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s1_d / 2.0))
    
    # Create the offset plane for the second sketch
    # We need a plane at Z = 40 (end of sec 1)
    offset1 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_1")
    offset1.Plane = "XY_Plane"
    offset1.Length = params.s1_l
    
    sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_S2")
    sketch2.Plane = "OffsetPlane_1"
    sketch2.Reference = (offset1, [""])
    sketch2.MapMode = "FlatFace"
    sketch2.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s2_d / 2.0))
    
    # Offset for Sec 2 end
    offset2 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_2")
    offset2.Plane = "OffsetPlane_1"
    offset2.Length = params.s2_l
    
    sketch3 = body.newObject("Sketcher::SketchObject", "Sketch_S3")
    sketch3.Plane = "OffsetPlane_2"
    sketch3.Reference = (offset2, [""])
    sketch3.MapMode = "FlatFace"
    sketch3.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s3_d / 2.0))
    
    # Offset for Sec 3 end
    offset3 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_3")
    offset3.Plane = "OffsetPlane_2"
    offset3.Length = params.s3_l
    
    sketch4 = body.newObject("Sketcher::SketchObject", "Sketch_S4")
    sketch4.Plane = "OffsetPlane_3"
    sketch4.Reference = (offset3, [""])
    sketch4.MapMode = "FlatFace"
    sketch4.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s4_d / 2.0))
    
    # Offset for Sec 4 end
    offset4 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_4")
    offset4.Plane = "OffsetPlane_3"
    offset4.Length = params.s4_l
    
    sketch5 = body.newObject("Sketcher::SketchObject", "Sketch_S5")
    sketch5.Plane = "OffsetPlane_4"
    sketch5.Reference = (offset4, [""])
    sketch5.MapMode = "FlatFace"
    sketch5.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.s5_d / 2.0))
    
    # Now create the pads to connect them all into one solid.
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
    
    # Pad 5: From OffsetPlane_4 to end of OffsetPlane_5 (which we need to create)
    offset5 = body.newObject("PartDesign::OffsetPlane", "OffsetPlane_5")
    offset5.Plane = "OffsetPlane_4"
    offset5.Length = params.s5_l
    
    pad5 = body.newObject("PartDesign::Pad", "Pad_S5")
    pad5.Profile = sketch5
    pad5.Length = params.s5_l
    pad5.Clean = True
    
    # Recompute to generate the geometry
    doc.recompute()
    
    # Save the file to the specific location required
    output_path = Path(__file__).parent / "answer.FCStd"
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    main()
