from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Initialize document
    doc = App.newDocument("FlangeAssembly")
    
    # Create a PartDesign Body to hold the solid
    body = doc.addObject("PartDesign::Body", "Body")
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
    sketch_base.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center of outer circle
    sketch_base.addConstraint(Sketcher.Constraint("Center", 1, 0)) # Center of bore circle
    # Actually, simpler: just constrain them to each other or the origin. 
    # In Sketcher, adding two circles at same origin usually auto-constrains or we add Coincident.
    # Let's explicitly add Coincident for robustness if the origin isn't set.
    # But since we placed them at 0,0,0, the Center constraint on index 0 and 1 works if we define the reference.
    # Standard way:
    sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"))
    
    # Create the Pad feature
    pad = body.newObject("PartDesign::Pad", "Pad_Flange")
    pad.Profile = sketch_base
    pad.Length = params.flange_thickness
    pad.Type = "Solid"
    pad.Radius = 0.0
    pad.Reversed = False
    
    # --- Feature 2: Bolt Holes (Pocket) ---
    # Create a sketch on the XY plane (offset slightly to avoid sketch interference if needed, 
    # but since we are using PartDesign, we can just project or create a new sketch on the face.
    # However, creating a new sketch on the face is safer for the "Profile" property.
    # We will create a sketch on the top face of the pad.
    
    # Get the top face of the pad to attach the sketch
    # Note: In headless, we can't easily query TopoFaces by index without recompute.
    # But we can create the sketch on the same XY plane and use the pad's position.
    # Actually, the standard workflow in PartDesign is to create a sketch on the face.
    # Since we can't query faces programmatically before recompute, we create the sketch 
    # on the XY plane but shifted up by half thickness, or we rely on the fact that 
    # the pocket profile is on the same plane as the base sketch? 
    # No, the profile must be on a face. 
    # Alternative: Create the pocket sketch on the XY plane, but the pocket feature 
    # expects the profile to be on a face. 
    # To bypass face selection in headless scripting without GUI:
    # We create the sketch on the XY plane. Then we set the sketch's position to 
    # be on the top face. 
    # Since we don't know the face ID, we can't do `sketch.Placement = face.Placement`.
    # TRICK: We can create the sketch on the XY plane, and then in the Pocket feature,
    # we cannot select a face programmatically by ID easily in headless without a loop.
    # BETTER APPROACH: 
    # Create the bolt holes on a sketch that is placed on the top face.
    # How to get the top face placement?
    # We can compute it: The pad is at 0,0,0 with thickness T. Top face is at Z = T/2.
    # So we place the sketch at App.Placement(App.Vector(0, 0, params.flange_thickness / 2.0))
    
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
    
    # Add constraints: All centers must lie on the bolt circle
    # Sketcher constraint syntax: Constraint("Point2Distance", i, "Center", 0, "Center")? No.
    # We need to constrain all hole centers to the bolt circle path.
    # Easier: Constrain each center to the origin of the bolt circle (which is the sketch origin)
    # and constrain the distance to the bolt_radius.
    # But the sketch origin is arbitrary.
    # Let's constrain all hole centers to be equidistant from the sketch origin?
    # Better: Constrain each hole center to the bolt circle we could draw.
    # Since we didn't draw a bolt circle, let's draw one to help constraints or use Point2Distance.
    # Let's draw a reference circle for the bolt circle to make constraints easier.
    bolt_ref_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_radius)
    sketch_bolts.addGeometry(bolt_ref_circle, False)
    
    # Constrain all hole centers to lie on the bolt_ref_circle
    for i, pos in enumerate(bolt_positions):
        # Index of hole center in sketch_bolts geometry
        # 0: Outer Circle, 1: Bore Circle, 2: Bolt Ref Circle, 3..N: Bolt Holes
        hole_idx = 2 + i
        # Constrain center of hole to center of ref circle? No, to a point on it.
        # Sketcher Constraint "Point2Distance" between center of hole and center of ref circle = bolt_radius
        sketch_bolts.addConstraint(Sketcher.Constraint("Point2Distance", hole_idx, "Center", 2, "Center", bolt_radius))
        
        # Also constrain center of hole to lie on the X-Y axes relative to each other?
        # Just constraining to the circle is usually enough if they are evenly spaced, 
        # but to ensure symmetry we might add angular constraints. 
        # For simplicity and robustness in script:
        # Let's just constrain centers to the circle.
    
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
