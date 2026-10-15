from pathlib import Path
import FreeCAD as App
import Part
import PartDesign
import Sketcher
import math

def main():
    doc = App.newDocument("RibbedCoverPlate")
    
    # Create the Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement()
    
    # Create a VarSet for named parameters
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "OverallLength", "Dimensions", "100")
    params.addProperty("App::PropertyLength", "OverallWidth", "Dimensions", "50")
    params.addProperty("App::PropertyLength", "Height", "Dimensions", "10")
    params.addProperty("App::PropertyLength", "RibHeight", "Dimensions", "3")
    params.addProperty("App::PropertyLength", "RibSpacing", "Dimensions", "12")
    params.addProperty("App::PropertyLength", "BossDiameter", "Dimensions", "13")
    params.addProperty("App::PropertyLength", "BossHeight", "Dimensions", "5")
    params.addProperty("App::PropertyLength", "BossSpacing", "Dimensions", "12")
    params.addProperty("App::PropertyLength", "BossOffset", "Dimensions", "5")
    params.addProperty("App::PropertyLength", "SideFlangeHeight", "Dimensions", "10")
    params.addProperty("App::PropertyLength", "SideFlangeWidth", "Dimensions", "23")
    
    # Attach planes
    doc.addObject("PartDesign::Placement", "XY_Plane").Placement = App.Placement(App.Vector(0, 0, 0))
    doc.addObject("PartDesign::Placement", "XZ_Plane").Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, math.pi/2))
    doc.addObject("PartDesign::Placement", "YZ_Plane").Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, math.pi/2, 0))
    doc.addObject("PartDesign::Placement", "Z_Axis").Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, math.pi/2))
    doc.addObject("PartDesign::Placement", "Y_Axis").Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, math.pi/2, 0))
    doc.addObject("PartDesign::Placement", "X_Axis").Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    
    # Base Sketch (Front view - top surface)
    sk0 = body.newObject("Sketcher::SketchObject", "Sketch_Top")
    sk0.Placement = App.Placement(App.Vector(0, 0, 0))
    sk0.Lifted = False
    sk0.MapMode = "Plane"
    sk0.Plane = (doc.getObject("XY_Plane"), [""])
    
    # Main rectangle (100 x 50)
    sk0.addGeometry(Part.LineSegment(App.Vector(-50, -25, 0), App.Vector(-50, 25, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(-50, 25, 0), App.Vector(50, 25, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(50, 25, 0), App.Vector(50, -25, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(50, -25, 0), App.Vector(-50, -25, 0)), False)
    
    # 4x Ø13 Boss holes
    # Positions: (BossOffset, BossSpacing*i) and (-BossOffset, BossSpacing*i)
    # Left bosses at x = -BossOffset = -5
    # Right bosses at x = +BossOffset = +5
    # Spacing: 12, so y = -23, -11, +11, +23
    positions = [
        (-5, -23), (-5, -11), (-5, 11), (-5, 23),
        (5, -23), (5, -11), (5, 11), (5, 23)
    ]
    
    for px, py in positions:
        sk0.addGeometry(Part.Circle(App.Vector(px, py, 0), App.Vector(0, 0, 1), params.BossDiameter/2), False)
    
    # Side flange rectangles (23 x 10)
    # Left side: x = -50, y from -23 to -13 (width 10)
    # Right side: x = +50, y from -23 to -13
    sk0.addGeometry(Part.LineSegment(App.Vector(-73, -13, 0), App.Vector(-73, 13, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(-73, 13, 0), App.Vector(-73, -13, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(-50, -13, 0), App.Vector(-73, -13, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(-50, 13, 0), App.Vector(-73, 13, 0)), False)
    
    sk0.addGeometry(Part.LineSegment(App.Vector(50, -13, 0), App.Vector(73, -13, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(50, 13, 0), App.Vector(73, 13, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(73, 13, 0), App.Vector(73, -13, 0)), False)
    sk0.addGeometry(Part.LineSegment(App.Vector(50, -13, 0), App.Vector(73, -13, 0)), False)
    
    # Create the main pad
    mainPad = body.newObject("PartDesign::Pad", "Pad")
    mainPad.Profile = sk0
    mainPad.Length = params.Height
    mainPad.Type = "Solid"
    
    # Ribs sketch
    sk1 = body.newObject("Sketcher::SketchObject", "Sketch_Ribs")
    sk1.Placement = App.Placement(App.Vector(0, 0, params.RibHeight))
    sk1.MapMode = "Plane"
    sk1.Plane = (doc.getObject("XY_Plane"), [""])
    
    # Ribs: 3 vertical ribs at x = -25, 0, +25 (centered on boss spacing of 12)
    # Actually, looking at the drawing, ribs are spaced 12mm apart
    # Rib positions: x = -25, 0, +25 (to span the 50mm width with 12mm spacing)
    rib_positions = [-25, 0, 25]
    
    for x_pos in rib_positions:
        # Each rib is 12mm wide (spacing), centered at x_pos
        sk1.addGeometry(Part.LineSegment(App.Vector(x_pos - 6, 0, 0), App.Vector(x_pos - 6, 3, 0)), False)
        sk1.addGeometry(Part.LineSegment(App.Vector(x_pos - 6, 3, 0), App.Vector(x_pos + 6, 3, 0)), False)
        sk1.addGeometry(Part.LineSegment(App.Vector(x_pos + 6, 3, 0), App.Vector(x_pos + 6, 0, 0)), False)
        sk1.addGeometry(Part.LineSegment(App.Vector(x_pos + 6, 0, 0), App.Vector(x_pos - 6, 0, 0)), False)
    
    # Create ribs (subtractive)
    ribCut = body.newObject("PartDesign::Pocket", "RibsPocket")
    ribCut.Profile = sk1
    ribCut.Type = "Blind"
    ribCut.Length = params.RibHeight
    
    # Bosses sketch (side view - elevating the bosses)
    sk2 = body.newObject("Sketcher::SketchObject", "Sketch_Bosses")
    sk2.Placement = App.Placement(App.Vector(0, 0, params.Height))
    sk2.MapMode = "Plane"
    sk2.Plane = (doc.getObject("XZ_Plane"), [""])
    
    # Bosses are 13mm diameter, 5mm tall, centered on the main body
    # They are at y positions: -23, -11, 11, 23 (same as holes)
    boss_positions = [-23, -11, 11, 23]
    
    for y_pos in boss_positions:
        # Bosses are at x = -5 and x = +5 (same as holes)
        # Sketch on XZ plane, so x is vertical in this view
        sk2.addGeometry(Part.Circle(App.Vector(0, y_pos, 0), App.Vector(0, 0, 1), params.BossDiameter/2), False)
    
    # Create boss pads
    bossPad = body.newObject("PartDesign::Pad", "BossPad")
    bossPad.Profile = sk2
    bossPad.Length = params.BossHeight
    bossPad.Type = "Solid"
    
    # Side flanges sketch (front view - elevating the side flanges)
    sk3 = body.newObject("Sketcher::SketchObject", "Sketch_Flanges")
    sk3.Placement = App.Placement(App.Vector(0, 0, params.Height))
    sk3.MapMode = "Plane"
    sk3.Plane = (doc.getObject("XY_Plane"), [""])
    
    # Side flanges are 23mm wide (x direction), 10mm tall (y direction)
    # They are at the edges of the main body
    sk3.addGeometry(Part.LineSegment(App.Vector(-73, -13, 0), App.Vector(-73, 13, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(-73, 13, 0), App.Vector(-73, -13, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(-50, -13, 0), App.Vector(-73, -13, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(-50, 13, 0), App.Vector(-73, 13, 0)), False)
    
    sk3.addGeometry(Part.LineSegment(App.Vector(50, -13, 0), App.Vector(73, -13, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(50, 13, 0), App.Vector(73, 13, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(73, 13, 0), App.Vector(73, -13, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(50, -13, 0), App.Vector(73, -13, 0)), False)
    
    # Create side flange pads
    flangePad = body.newObject("PartDesign::Pad", "FlangePad")
    flangePad.Profile = sk3
    flangePad.Length = params.SideFlangeHeight
    flangePad.Type = "Solid"
    
    # Round corners on the main pad
    cornerFillet = body.newObject("PartDesign::Fillet", "CornerFillet")
    cornerFillet.Base = [mainPad]
    cornerFillet.EdgeList = [
        mainPad.Edges[0], # Bottom left
        mainPad.Edges[1], # Top left
        mainPad.Edges[2], # Top right
        mainPad.Edges[3]  # Bottom right
    ]
    cornerFillet.Radius = 2.0
    
    # Document recompute
    doc.recompute()
    
    # Save the document
    output_path = Path(__file__).resolve().parent / "answer.FCStd"
    doc.saveAs(str(output_path))
    
    print(f"Part saved to {output_path}")

if __name__ == "__main__":
    main()
