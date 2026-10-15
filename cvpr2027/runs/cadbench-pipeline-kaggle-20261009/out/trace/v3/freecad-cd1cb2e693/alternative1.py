from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import PartDesign

# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================
def main():
    # 1. Initialize Document
    doc = App.newDocument("BoomCylinderPistonRing")
    App.addModule("Part")
    App.addModule("Sketcher")
    App.addModule("PartDesign")

    # ==============================================================================
    # 2. Create Named Parameters (Derived from measurements)
    # ==============================================================================
    # Based on reading the drawing:
    # Outer Diameter (OD): 276.5
    # Inner Diameter (ID): 252
    # Flange Thickness: 10
    # Flange Height: 64
    # Groove Depth: 10
    # Piston Ring Width: 14
    # Cylinder Outer Diameter: 272
    # Cylinder Inner Diameter: 252 (matches flange ID)
    # Groove Diameter (Inner): 208.5
    # Groove Diameter (Outer): 272
    # Groove Depth (from 272): 10
    # Main Cylinder Length: 161
    # Total Length: 169
    # Piston Ring Groove Diameter: 208.5
    # Piston Ring Groove Width: 14
    # Piston Ring Groove Depth: 10
    # Piston Ring Groove Radius: 4
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    # Piston Ring Groove Inner Diameter: 208.5
    # Piston Ring Groove Outer Diameter: 272
    # Piston Ring Groove Length: 161
    # Piston Ring Groove Height: 64
    
    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "OD", "Dimensions", "Outer Diameter")
    params.addProperty("App::PropertyLength", "ID", "Dimensions", "Inner Diameter")
    params.addProperty("App::PropertyLength", "FlangeThick", "Dimensions", "Flange Thickness")
    params.addProperty("App::PropertyLength", "FlangeHeight", "Dimensions", "Flange Height")
    params.addProperty("App::PropertyLength", "GrooveDepth", "Dimensions", "Groove Depth")
    params.addProperty("App::PropertyLength", "PistonRingWidth", "Dimensions", "Piston Ring Width")
    params.addProperty("App::PropertyLength", "CylinderOD", "Dimensions", "Cylinder OD")
    params.addProperty("App::PropertyLength", "CylinderID", "Dimensions", "Cylinder ID")
    params.addProperty("App::PropertyLength", "GrooveDiamInner", "Dimensions", "Groove Inner Diameter")
    params.addProperty("App::PropertyLength", "GrooveDiamOuter", "Dimensions", "Groove Outer Diameter")
    params.addProperty("App::PropertyLength", "MainCylinderLength", "Dimensions", "Main Cylinder Length")
    params.addProperty("App::PropertyLength", "TotalLength", "Dimensions", "Total Length")
    params.addProperty("App::PropertyLength", "PistonRingGrooveDiam", "Dimensions", "Piston Ring Groove Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveWidth", "Dimensions", "Piston Ring Groove Width")
    params.addProperty("App::PropertyLength", "PistonRingGrooveDepth", "Dimensions", "Piston Ring Groove Depth")
    params.addProperty("App::PropertyLength", "PistonRingGrooveRadius", "Dimensions", "Piston Ring Groove Radius")
    params.addProperty("App::PropertyLength", "PistonRingGrooveLength", "Dimensions", "Piston Ring Groove Length")
    params.addProperty("App::PropertyLength", "PistonRingGrooveHeight", "Dimensions", "Piston Ring Groove Height")
    params.addProperty("App::PropertyLength", "PistonRingGrooveInnerDiam", "Dimensions", "Piston Ring Groove Inner Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveOuterDiam", "Dimensions", "Piston Ring Groove Outer Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveLength", "Dimensions", "Piston Ring Groove Length")
    params.addProperty("App::PropertyLength", "PistonRingGrooveHeight", "Dimensions", "Piston Ring Groove Height")
    params.addProperty("App::PropertyLength", "PistonRingGrooveInnerDiam", "Dimensions", "Piston Ring Groove Inner Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveOuterDiam", "Dimensions", "Piston Ring Groove Outer Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveLength", "Dimensions", "Piston Ring Groove Length")
    params.addProperty("App::PropertyLength", "PistonRingGrooveHeight", "Dimensions", "Piston Ring Groove Height")
    params.addProperty("App::PropertyLength", "PistonRingGrooveInnerDiam", "Dimensions", "Piston Ring Groove Inner Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveOuterDiam", "Dimensions", "Piston Ring Groove Outer Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveLength", "Dimensions", "Piston Ring Groove Length")
    params.addProperty("App::PropertyLength", "PistonRingGrooveHeight", "Dimensions", "Piston Ring Groove Height")
    params.addProperty("App::PropertyLength", "PistonRingGrooveInnerDiam", "Dimensions", "Piston Ring Groove Inner Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveOuterDiam", "Dimensions", "Piston Ring Groove Outer Diameter")
    params.addProperty("App::PropertyLength", "PistonRingGrooveLength", "Dimensions", "Piston Ring Groove Length")
    params.addProperty("App::PropertyLength", "PistonRingGrooveHeight", "Dimensions", "Piston Ring Groove Height")
    
    # Set values
    params.OD = 276.5
    params.ID = 252.0
    params.FlangeThick = 10.0
    params.FlangeHeight = 64.0
    params.GrooveDepth = 10.0
    params.PistonRingWidth = 14.0
    params.CylinderOD = 272.0
    params.CylinderID = 252.0
    params.GrooveDiamInner = 208.5
    params.GrooveDiamOuter = 272.0
    params.MainCylinderLength = 161.0
    params.TotalLength = 169.0
    params.PistonRingGrooveDiam = 208.5
    params.PistonRingGrooveWidth = 14.0
    params.PistonRingGrooveDepth = 10.0
    params.PistonRingGrooveRadius = 4.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    params.PistonRingGrooveInnerDiam = 208.5
    params.PistonRingGrooveOuterDiam = 272.0
    params.PistonRingGrooveLength = 161.0
    params.PistonRingGrooveHeight = 64.0
    
    # ==============================================================================
    # 3. Create Body
    # ==============================================================================
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # ==============================================================================
    # 4. Create Base Sketch (Front View Profile)
    # ==============================================================================
    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.Object = base_sketch
    base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    base_sketch.MapMode = "FlatFace"
    base_sketch.ConstrainAll = True
    
    # Create base circle (OD)
    base_circle = base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.OD/2), False)
    base_circle.Visibility = True
    
    # Create inner circle (ID)
    base_inner_circle = base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.ID/2), False)
    base_inner_circle.Visibility = True
    
    # Add constraints
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 1))
    
    # Add more circles for other diameters
    base_circle_272 = base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.CylinderOD/2), False)
    base_circle_272.Visibility = True
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 1))
    
    base_circle_208_5 = base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.GrooveDiamInner/2), False)
    base_circle_208_5.Visibility = True
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    base_sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1, 1, 1))
    
    # Add lines for flange and cylinder lengths
    base_line_flange = base_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.TotalLength/2, 0), App.Vector(0, params.TotalLength/2 - params.FlangeHeight, 0)), False)
    base_line_flange.Visibility = True
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    
    base_line_cylinder = base_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.TotalLength/2 - params.FlangeHeight, 0), App.Vector(0, params.TotalLength/2 - params.FlangeHeight - params.MainCylinderLength, 0)), False)
    base_line_cylinder.Visibility = True
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    
    # Add fillets
    base_fillet_flange = base_sketch.addGeometry(Part.Fillet(App.Vector(0, params.TotalLength/2, 0), App.Vector(0, params.TotalLength/2 - params.FlangeHeight, 0), 0), False)
    base_fillet_flange.Visibility = True
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    
    base_fillet_cylinder = base_sketch.addGeometry(Part.Fillet(App.Vector(0, params.TotalLength/2 - params.FlangeHeight, 0), App.Vector(0, params.TotalLength/2 - params.FlangeHeight - params.MainCylinderLength, 0), 0), False)
    base_fillet_cylinder.Visibility = True
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    
    # ==============================================================================
    # 5. Create Features
    # ==============================================================================
    
    # Pad the base shape
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = base_sketch
    pad.Length = params.TotalLength
    pad.MidPlane = True
    pad.Reversed = False
    pad.setExpression("Length", "Parameters.TotalLength")
    
    # Pocket for the main cylinder bore
    pocket_main = body.newObject("PartDesign::Pocket", "PocketMain")
    pocket_main.Profile = base_sketch
    pocket_main.Length = params.TotalLength - params.FlangeHeight
    pocket_main.MidPlane = True
    pocket_main.Reversed = True
    pocket_main.setExpression("Length", "Parameters.TotalLength - Parameters.FlangeHeight")
    
    # Pocket for the flange inner diameter
    pocket_flange = body.newObject("PartDesign::Pocket", "PocketFlange")
    pocket_flange.Profile = base_sketch
    pocket_flange.Length = params.FlangeHeight
    pocket_flange.MidPlane = True
    pocket_flange.Reversed = True
    pocket_flange.setExpression("Length", "Parameters.FlangeHeight")
    
    # Pocket for the groove
    pocket_groove = body.newObject("PartDesign::Pocket", "PocketGroove")
    pocket_groove.Profile = base_sketch
    pocket_groove.Length = params.GrooveDepth
    pocket_groove.MidPlane = True
    pocket_groove.Reversed = True
    pocket_groove.setExpression("Length", "Parameters.GrooveDepth")
    
    # Revolution for the piston ring groove
    rev_piston_ring = body.newObject("PartDesign::Revolution", "RevPistonRing")
    rev_piston_ring.Profile = base_sketch
    rev_piston_ring.ReferenceAxis = (doc.getObject("Z_Axis"), [""])
    rev_piston_ring.Angle = 360.0
    rev_piston_ring.setExpression("Angle", "360.0")
    
    # Chamfer for the flange edge
    chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
    chamfer.Base = (pad, ["Edge1"])
    chamfer.Size = 1.0
    chamfer.setExpression("Size", "1.0")
    
    # Fillet for the cylinder edge
    fillet = body.newObject("PartDesign::Fillet", "Fillet")
    fillet.Base = (pad, ["Edge1"])
    fillet.Radius = 2.0
    fillet.setExpression("Radius", "2.0")
    
    # ==============================================================================
    # 6. Recompute and Save
    # ==============================================================================
    doc.recompute()
    
    # Save to file
    output_path = Path(__file__).resolve().parent / "answer.FCStd"
    doc.save(str(output_path))
    
    print(f"Part saved to {output_path}")

# ==============================================================================
# EXECUTE
# ==============================================================================
if __name__ == "__main__":
    main()
