from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Initialize document
    doc = App.newDocument("FlangeAssembly")
    
    # Create a PartDesign Body to hold the solid
    body = doc.addObject("PartDesign::Body", "Body")
    # Body placement is handled by the document context usually, but we ensure it's at origin
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # --- Parameters Definition ---
    # We will use expressions to drive features from a shared source
    params = body.newObject("App::Property", "Parameters")
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
    params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
    params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central through-bore")
    params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Diameter of the bolt circle")
    params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of the bolt holes")
    params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")
    
    # Set default values as requested
    params.outer_diameter = 69.453
    params.flange_thickness = 13.097
    params.bore_diameter = 34.925
    params.pitch_circle_diameter = 57.944
    params.bolt_hole_diameter = 6.747
    params.number_bolt_holes = 4
    
    # --- Feature 1: Base Flange (Pad) ---
    # Create a sketch on the XY plane for the outer profile and central bore
    sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_Base")
    sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_base.TangentConstraint = True
    sketch_base.ConstrainToCurrentCS = True
    
    # Add outer circle
    outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
    sketch_base.addGeometry(outer_circle, False)
    
    # Add central bore circle
    bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
    sketch_base.addGeometry(bore_circle, False)
    
    # Add coincident constraint at center (both circles share center)
    # Constraint syntax: Constraint("Coincident", index1, "Point", index2, "Point")
    # Index 0 is outer circle, Index 1 is bore circle
    sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"))
    
    # Create the Pad feature
    pad = body.newObject("PartDesign::Pad", "Pad_Flange")
    pad.Profile = sketch_base
    pad.Length = params.flange_thickness
    pad.Type = "Solid"
    pad.Radius = 0.0
    pad.Reversed = False
    
    # --- Feature 2: Bolt Holes (Pocket) ---
    # Create a sketch on the top face of the pad.
    # Since we cannot query the face ID of the top face of the pad in headless mode easily,
    # we place the sketch at the calculated Z position of the top face.
    # The pad is at Z=0 with thickness T, so top face is at Z = T/2.
    
    sketch_bolts = body.newObject("Sketcher::SketchObject", "Sketch_Bolts")
    sketch_bolts.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness / 2.0))
    
    # Calculate bolt positions
    bolt_radius = params.pitch_circle_diameter / 2.0
    angle_step = 360.0 / params.number_bolt_holes
    bolt_positions = []
    
    for i in range(params.number_bolt_holes):
        angle = i * angle_step
        x = bolt_radius * App.Vector.Cos(angle)
        y = bolt_radius * App.Vector.Sin(angle)
        bolt_positions.append((x, y))
    
    # Add circles for each bolt hole
    for pos in bolt_positions:
        circle = Part.Circle(App.Vector(pos[0], pos[1], 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
        sketch_bolts.addGeometry(circle, False)
    
    # Add a reference circle for the bolt circle to help with constraints
    bolt_ref_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_radius)
    sketch_bolts.addGeometry(bolt_ref_circle, False)
    
    # Constrain all hole centers to lie on the bolt_ref_circle
    # Geometry indices:
    # 0: Outer Circle (from sketch_base? No, this is a new sketch)
    # Wait, sketch_bolts only contains bolt holes and ref circle.
    # Let's re-index for sketch_bolts:
    # 0: Bolt Ref Circle
    # 1..N: Bolt Holes
    
    for i, pos in enumerate(bolt_positions):
        hole_idx = 1 + i
        # Constrain center of hole to center of ref circle with distance = bolt_radius
        sketch_bolts.addConstraint(Sketcher.Constraint("Point2Distance", hole_idx, "Center", 0, "Center", bolt_radius))
    
    # Create the Pocket feature
    pocket = body.newObject("PartDesign::Pocket", "Pocket_Bolts")
    pocket.Profile = sketch_bolts
    pocket.Type = "ThroughAll" # Cuts through the entire flange thickness
    pocket.Radius = 0.0
    
    # --- Finalize ---
    doc.recompute()
    
    # Determine output path
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / f"{script_path.stem}.FCStd"
    
    # Save the document
    doc.saveAs(str(output_path))
    
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    main()
