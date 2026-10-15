from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Initialize document
    doc = App.newDocument("SmoothShaft")
    doc.Label = "SmoothShaft_Parametric"

    # Create the Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # --- Parameters ---
    params = body.newObject("App::VarSet", "Parameters")
    
    params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
    params.shaft_diameter = 30.0
    
    params.addProperty("App::PropertyLength", "shaft_length", "Dimensions", "Shaft Length")
    params.shaft_length = 50.0
    
    params.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "Keyway Width")
    params.keyway_width = 7.0
    
    params.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "Keyway Depth")
    params.keyway_depth = 4.0
    
    params.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "Keyway Height")
    params.keyway_height = 20.0
    
    params.addProperty("App::PropertyInteger", "num_keyways", "Dimensions", "Number of Keyways")
    params.num_keyways = 1

    # Ensure standard planes exist for sketching
    # In a headless script, we must ensure the planes exist before creating sketches.
    # We create them as Part::Plane objects if they don't exist, then use them as support.
    # Note: Sketcher::SketchObject AttachmentSupport expects a Face. Part::Plane provides a face.
    
    def get_or_create_plane(name, normal):
        obj = doc.getObject(name)
        if obj is None:
            p = doc.addObject("Part::Plane", name)
            p.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(*normal))
            doc.recompute()
            return p
        return obj

    # Create planes if missing
    # XY_Plane: Normal Z (0,0,1)
    # XZ_Plane: Normal Y (0,1,0)
    # YZ_Plane: Normal X (1,0,0)
    plane_xy = get_or_create_plane("XY_Plane", (0, 0, 1))
    plane_xz = get_or_create_plane("XZ_Plane", (0, 1, 0))
    plane_yz = get_or_create_plane("YZ_Plane", (1, 0, 0))

    # --- Feature 1: Pad (Cylinder) ---
    # Sketch in XY plane to define the circle.
    sketch_cylinder = body.newObject("Sketcher::SketchObject", "Sketch_Cylinder")
    sketch_cylinder.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_cylinder.Support = [(plane_xy, [""])]
    sketch_cylinder.MapMode = "FlatFace"
    
    # Add Circle
    sketch_cylinder.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaft_diameter / 2.0), False)
    
    # Pad the cylinder
    pad = body.newObject("PartDesign::Pad", "Pad_Cylinder")
    pad.Profile = sketch_cylinder
    pad.Length = params.shaft_length
    pad.Midplane = False

    # --- Feature 2: Keyway ---
    # The keyway is a rectangular slot along the shaft axis (Z).
    # We will create a sketch in the XZ plane (Side view) to define the slot profile.
    # The slot is defined by a rectangle.
    # We will use a Pocket feature to cut this slot.
    # Since the keyway is a slot along Z, and we are in XZ plane:
    # The "profile" of the pocket in XZ will be the cross-section of the slot.
    # However, a standard Pocket extrudes along the normal of the sketch plane.
    # If we sketch in XZ (Normal Y), extruding along Y creates a slot that goes through the diameter (Y direction).
    # This matches the "Depth" of the keyway (radial cut).
    # The "Height" of the keyway (axial length) is the Length of the Pocket.
    # The "Width" of the keyway is the width of the rectangle in the XZ sketch.
    
    sketch_keyway = body.newObject("Sketcher::SketchObject", "Sketch_Keyway")
    sketch_keyway.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_keyway.Support = [(plane_xz, [""])]
    sketch_keyway.MapMode = "FlatFace"
    
    # Define Keyway Geometry in XZ plane:
    # Center at (0,0).
    # Width (X direction): keyway_width.
    # Depth (Y direction in 3D, but here we are in XZ plane, so the rectangle extends in Z? No.)
    # Wait. 
    # If we sketch in XZ plane:
    #   X axis is horizontal.
    #   Z axis is vertical.
    #   Normal is Y.
    # If we create a rectangle in this plane:
    #   Width along X = keyway_width.
    #   Height along Z = keyway_height.
    # If we Pocket this along the Normal (Y), we cut a slot that goes through the diameter (Y direction).
    # This creates a slot of:
    #   - Width (X) = keyway_width
    #   - Depth (Y) = keyway_depth (Wait, the sketch height is Z, but the extrusion is Y).
    #   - Length (Z) = keyway_height (This is the dimension along the shaft axis).
    #
    # So the sketch rectangle should be:
    #   - X range: [-width/2, +width/2]
    #   - Z range: [0, height] (or centered).
    #   - The extrusion direction is Y.
    #   - The extrusion length should be the "Depth" (radial cut).
    #
    # Let's refine the sketch geometry:
    # We need a closed loop.
    # Rectangle corners:
    #   (-w/2, 0) -> (w/2, 0) -> (w/2, h) -> (-w/2, h) -> (-w/2, 0)
    #   Where w = keyway_width, h = keyway_height.
    #   This rectangle lies in the XZ plane.
    #   Extruding along Y (Normal) with Length = keyway_depth will cut a slot:
    #     - Width = w
    #     - Axial Length = h
    #     - Radial Depth = keyway_depth
    #   This perfectly matches the requirements.
    
    w = params.keyway_width
    h = params.keyway_height
    d = params.keyway_depth
    
    # Line 1: Bottom edge (on X axis)
    sketch_keyway.addGeometry(Part.LineSegment(App.Vector(-w/2, 0, 0), App.Vector(w/2, 0, 0)), False)
    # Line 2: Right edge (up Z)
    sketch_keyway.addGeometry(Part.LineSegment(App.Vector(w/2, 0, 0), App.Vector(w/2, 0, h)), False)
    # Line 3: Top edge (parallel to X)
    sketch_keyway.addGeometry(Part.LineSegment(App.Vector(w/2, 0, h), App.Vector(-w/2, 0, h)), False)
    # Line 4: Left edge (down Z)
    sketch_keyway.addGeometry(Part.LineSegment(App.Vector(-w/2, 0, h), App.Vector(-w/2, 0, 0)), False)
    
    # Add constraints to ensure it's a rectangle and centered
    # Coincident to origin for bottom-left? No, let's just constrain lines.
    # Horizontal lines parallel to X axis.
    # Vertical lines parallel to Z axis.
    # Right angle at corners.
    # Distance between vertical lines = w.
    # Distance between horizontal lines = h.
    
    # Constraint: Horizontal lines are parallel to X axis (Angle 0)
    sketch_keyway.addConstraint(Sketcher.Constraint("Angle", 0, 1, 0), False) # Line 0 (bottom)
    sketch_keyway.addConstraint(Sketcher.Constraint("Angle", 0, 2, 0), False) # Line 2 (top)
    # Constraint: Vertical lines are parallel to Z axis (Angle 90)
    sketch_keyway.addConstraint(Sketcher.Constraint("Angle", 90, 1, 2), False) # Line 1 (right)
    sketch_keyway.addConstraint(Sketcher.Constraint("Angle", 90, 3, 2), False) # Line 3 (left)
    # Constraint: Right angle at corner (Line 0 and Line 1)
    sketch_keyway.addConstraint(Sketcher.Constraint("RightAngle", 0, 1), False)
    # Constraint: Distance between vertical lines (Line 1 and Line 3) = w
    sketch_keyway.addConstraint(Sketcher.Constraint("DistanceX", 1, 3, w), False)
    # Constraint: Distance between horizontal lines (Line 0 and Line 2) = h
    sketch_keyway.addConstraint(Sketcher.Constraint("DistanceZ", 0, 2, h), False)
    # Coincident bottom-left corner to origin (0,0,0)
    sketch_keyway.addConstraint(Sketcher.Constraint("Point", 0, 1, "XY_Plane", "Origin"), False)
    # Actually, simpler: Coincident Line 0 start to Origin, Line 1 start to Line 0 start.
    # Let's just constrain the first point to origin.
    sketch_keyway.addConstraint(Sketcher.Constraint("Point", 0, 1, "XY_Plane", "Origin"), False)
    # Ensure the rectangle is in the correct quadrant (X>0, Z>0) for the pocket to work correctly?
    # The pocket will cut along Y. The rectangle is in XZ.
    # The rectangle is at X in [-w/2, w/2].
    # The pocket will cut a slot centered at X=0. This is correct.
    
    # Pocket the keyway
    pocket = body.newObject("PartDesign::Pocket", "Pocket_Keyway")
    pocket.Profile = sketch_keyway
    pocket.Type = "Blind"
    pocket.Length = d # Radial depth
    pocket.Midplane = False
    pocket.Reverse = False

    # --- Feature 3: Keyways Pattern (Optional based on num_keyways) ---
    # If num_keyways > 1, we need to pattern the pocket.
    # However, the pocket is already created. We can pattern the pocket feature.
    # But PartDesign::PolarPattern patterns the selected features.
    # We need to select the pocket.
    # Note: The pocket is centered at X=0. 
    # If we pattern it, we need to define the axis and angle.
    # The axis of rotation for the keyways is the Z axis (Shaft axis).
    # The angle is 360 / num_keyways.
    
    if params.num_keyways > 1:
        # We need to get the Z axis. 
        # In FreeCAD, Z_Axis is usually available in the document.
        # If not, we can create it or use the body's Z axis.
        # Let's try to get Z_Axis.
        z_axis = doc.getObject("Z_Axis")
        if z_axis is None:
            # Create a simple axis object if missing
            z_axis = doc.addObject("Part::Line", "Z_Axis")
            z_axis.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(0,0,0))
            # Part::Line doesn't have a clear "Axis" property for patterns directly in all versions.
            # Usually, we use the document's Z_Axis which is a Part::Line or similar.
            # Let's assume Z_Axis exists or create a placeholder.
            # Actually, PartDesign::PolarPattern expects an Axis object (Part::Line or similar).
            # Let's create a Part::Line representing the Z axis.
            z_line = Part.makeLine(App.Vector(0,0,-100), App.Vector(0,0,100))
            z_axis = doc.addObject("Part::Feature", "Z_Axis")
            z_axis.Shape = z_line
        
        pattern = body.newObject("PartDesign::PolarPattern", "Pattern_Keyways")
        pattern.Originals = [pocket]
        pattern.Axis = (z_axis, [""])
        pattern.Angle = 360.0 / params.num_keyways
        pattern.Occurrences = params.num_keyways
        pattern.Reverse = False
        pattern.Tangent = False
    else:
        # If only 1, no pattern needed, but we can create an empty pattern or just leave it.
        # The prompt says "number of keyways", so if 1, just the pocket.
        pass

    # --- Finalize ---
    doc.recompute()
    
    # Save the file next to the script
    script_path = Path(__file__).resolve()
    output_path = script_path.with_suffix(".FCStd")
    
    doc.saveAs(str(output_path))
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    main()
