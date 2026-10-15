from pathlib import Path
import FreeCAD as App, Part, Sketcher, PartDesign

def create_shaft():
    # Initialize Document
    doc = App.newDocument("ShaftDesign")
    doc.Label = "Smooth Shaft"
    
    # Create a PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # --- Parameters ---
    # We create named parameters directly on the Body object or use a VarSet.
    # To ensure they are editable properties of the document objects as requested,
    # we will add them to the Body object itself as App::PropertyLength/Number.
    body.addProperty("App::PropertyLength", "smooth_shaft_diameter", "Dimensions", "Shaft Diameter")
    body.smooth_shaft_diameter = 50.0
    
    body.addProperty("App::PropertyLength", "smooth_shaft_length", "Dimensions", "Shaft Length")
    body.smooth_shaft_length = 80.0
    
    body.addProperty("App::PropertyLength", "keyway_width", "Dimensions", "Keyway Width")
    body.keyway_width = 8.0
    
    body.addProperty("App::PropertyLength", "keyway_depth", "Dimensions", "Keyway Depth")
    body.keyway_depth = 4.0
    
    body.addProperty("App::PropertyLength", "keyway_height", "Dimensions", "Keyway Height")
    body.keyway_height = 50.0
    
    body.addProperty("App::PropertyInteger", "num_keyway", "Dimensions", "Number of Keyways")
    body.num_keyway = 1

    # --- Feature: Main Shaft Pad ---
    # 1. Main Shaft Sketch
    main_sketch = body.newObject("Sketcher::SketchObject", "MainShaftSketch")
    main_sketch.Plane = "XY_Plane"
    main_sketch.MapMode = "FlatFace"
    main_sketch.ConstrainAuto = True
    
    # Outer Circle (Shaft Profile)
    # Center at (0,0), Radius = Diameter/2
    radius = body.smooth_shaft_diameter / 2.0
    main_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)
    
    # Pad the shaft
    pad_shaft = body.newObject("PartDesign::Pad", "PadShaft")
    pad_shaft.Profile = main_sketch
    pad_shaft.Length = body.smooth_shaft_length
    pad_shaft.Type = "Blind"
    
    # --- Feature: Keyway Groove ---
    # The keyway is a slot. We will create a sketch for the slot profile and use a Groove feature
    # to cut it out. The Groove feature works similarly to a Pad but subtracts material.
    
    # 2. Keyway Sketch
    # We need to position the keyway. Standard keyways are often centered along the length or at a specific offset.
    # Given the prompt doesn't specify an axial offset, we will center it axially.
    # The keyway is a rectangle cut into the side of the cylinder.
    
    key_sketch = body.newObject("Sketcher::SketchObject", "KeywaySketch")
    key_sketch.Plane = "YZ_Plane" # YZ plane is convenient for drawing a vertical rectangle on the side
    key_sketch.MapMode = "FlatFace"
    key_sketch.ConstrainAuto = True
    
    # To define the keyway geometry properly in a sketch relative to the body:
    # We can draw a rectangle centered at (0,0) on the YZ plane.
    # The rectangle represents the cross-section of the slot.
    # Height of slot (Z direction) = keyway_height
    # Width of slot (Y direction) = keyway_width
    
    half_height = body.keyway_height / 2.0
    half_width = body.keyway_width / 2.0
    
    # Rectangle vertices
    p1 = App.Vector(-half_width, 0, half_height)
    p2 = App.Vector(-half_width, 0, -half_height)
    p3 = App.Vector(half_width, 0, -half_height)
    p4 = App.Vector(half_width, 0, half_height)
    
    # Add lines
    key_sketch.addGeometry(Part.LineSegment(p1, p2), False)
    key_sketch.addGeometry(Part.LineSegment(p2, p3), False)
    key_sketch.addGeometry(Part.LineSegment(p3, p4), False)
    key_sketch.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Add dimensions/constraints to ensure it scales correctly
    # Constraint height
    key_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, 2, 1, 2, 1, body.keyway_height))
    # Constraint width
    key_sketch.addConstraint(Sketcher.Constraint("Length", 1, 0, 3, 0, 1, 0, 3, 0, body.keyway_width))
    # Center on X axis (implicitly done by symmetry if we use symmetry constraint or just centering lines)
    # Let's add explicit center constraints to be safe
    key_sketch.addConstraint(Sketcher.Constraint("CenterX", 0, 0, 0, 0, 0, 0))
    key_sketch.addConstraint(Sketcher.Constraint("CenterZ", 0, 0, 0, 0, 0, 0))
    
    # 3. Create the Groove Feature
    # Groove creates a hole/void. We need to rotate this profile 360 degrees around the X axis (the shaft axis).
    # However, PartDesign::Groove usually takes a profile on a plane and extrudes/rotates.
    # The standard way to make a keyway in PartDesign is often:
    # 1. Create a sketch on the YZ plane (as done above).
    # 2. Use PartDesign::Groove with Type "Blind" or "ThroughAll" and set Axis to X_Axis.
    
    groove = body.newObject("PartDesign::Groove", "GrooveKeyway")
    groove.Profile = key_sketch
    groove.Axis = (App.Vector(1, 0, 0), ["X_Axis"]) # Axis of revolution
    groove.Type = "Blind"
    groove.Length = body.keyway_height # Wait, Length is along the axis of revolution? No.
    # In PartDesign, for a Groove/Pad/Revolution:
    # If the sketch is on YZ plane and we revolve around X axis:
    # The "Length" parameter controls the extent along the X axis.
    # BUT, the Keyway height is the Z dimension of the slot.
    # The prompt says keyway_height = 50mm. The shaft is 80mm long.
    # Usually keyway height is the width of the slot across the diameter (Z dimension in our sketch).
    # The "Length" of the groove feature in the direction of the axis of revolution (X) is the KEYWAY_LENGTH (axial length of the cut).
    # The prompt defines "keyway_height" = 50. This is ambiguous. Is it the axial length of the cut or the depth across the diameter?
    # "Keyway: keyway_width, keyway_depth, keyway_height, num_keyway"
    # In mechanical engineering:
    # - Width: The width of the slot (Y dimension).
    # - Depth: How deep it cuts into the shaft (Z dimension, towards center).
    # - Height: Often refers to the axial length of the keyway (X dimension).
    # Let's re-read carefully: "keyway_width, keyway_depth, keyway_height".
    # If Depth is 4mm, that's the Z dimension (radius cut).
    # If Height is 50mm, and shaft is 80mm, it's likely the axial length (X dimension).
    # So:
    # - Sketch Z-dimension (height of rect) = keyway_depth * 2? Or is keyway_depth the total Z-span?
    # Standard keyway: Width is across the shaft. Depth is how far it goes in. Height is the length along the shaft.
    # Let's assume:
    # - keyway_width = 8mm (Y span)
    # - keyway_depth = 4mm (Z span from surface to bottom? Or total Z span?)
    #   "Depth" usually implies the amount of material removed. So total Z span = 2 * 4 = 8mm? Or is it a single-sided cut?
    #   Keyways are symmetric. So total Z span = 2 * Depth.
    # - keyway_height = 50mm (X span, the length of the keyway along the shaft).
    
    # Adjusting Sketch based on this interpretation:
    # The sketch on YZ plane needs to represent the cross section.
    # The Z-dimension of the rectangle in the sketch corresponds to the "Depth" of the keyway (total height of the slot).
    # Total Z span = 2 * keyway_depth.
    # The X-dimension (Length of Groove) corresponds to keyway_height.
    
    # Let's update the sketch dimensions logic inside the code above.
    # p1/p4 Z coordinate should be keyway_depth.
    # p1/p2/p3/p4 Y coordinate should be keyway_width.
    
    # Re-calculating sketch geometry with correct interpretation:
    half_key_depth = body.keyway_depth # 4mm
    half_key_width = body.keyway_width / 2.0 # 4mm
    
    # The sketch is on YZ plane.
    # The rectangle corners in YZ:
    # Y: +/- half_key_width
    # Z: +/- half_key_depth
    
    # We need to update the sketch geometry dynamically if we want it fully parametric, 
    # but since we already added it, we will regenerate the sketch geometry in the script logic 
    # to ensure it matches the parameters perfectly.
    
    # Clearing previous sketch geometry (simulated by creating a new one in the actual script flow)
    # Actually, let's just rewrite the sketch creation part to be robust.
    
    # --- Re-defining Keyway Sketch for Correctness ---
    key_sketch.clearGeometry()
    key_sketch.clearConstraints()
    
    # Rectangle on YZ plane centered at origin
    # Y range: -width/2 to +width/2
    # Z range: -depth/2 to +depth/2
    # Note: The "Depth" in keyway specs is usually the total width of the slot in the radial direction.
    # So total Z span = keyway_depth.
    
    rect_z = body.keyway_depth / 2.0
    rect_y = body.keyway_width / 2.0
    
    p1 = App.Vector(-rect_y, 0, rect_z)
    p2 = App.Vector(-rect_y, 0, -rect_z)
    p3 = App.Vector(rect_y, 0, -rect_z)
    p4 = App.Vector(rect_y, 0, rect_z)
    
    key_sketch.addGeometry(Part.LineSegment(p1, p2), False)
    key_sketch.addGeometry(Part.LineSegment(p2, p3), False)
    key_sketch.addGeometry(Part.LineSegment(p3, p4), False)
    key_sketch.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Constraints
    key_sketch.addConstraint(Sketcher.Constraint("CenterX", 0, 0, 0, 0, 0, 0))
    key_sketch.addConstraint(Sketcher.Constraint("CenterY", 0, 0, 0, 0, 0, 0))
    # Z constraint (Total Height of slot)
    key_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, 2, 1, 2, 1, body.keyway_depth))
    # Y constraint (Total Width of slot)
    key_sketch.addConstraint(Sketcher.Constraint("Length", 1, 0, 3, 0, 1, 0, 3, 0, body.keyway_width))
    
    # Now set the Groove parameters
    groove.Profile = key_sketch
    groove.Axis = (App.Vector(1, 0, 0), ["X_Axis"])
    groove.Type = "Blind"
    groove.Length = body.keyway_height # Axial length of the cut
    
    # --- Feature: Multiple Keyways (Pattern) ---
    # We need to pattern the groove along the shaft.
    # The groove is currently centered. We need to shift it along X axis based on num_keyway.
    # Or we can pattern the groove feature itself.
    
    # Let's create a pattern of the groove.
    # The groove feature is "GrooveKeyway".
    # We need an axis for the pattern. The shaft axis is X_Axis (1,0,0).
    
    pattern = body.newObject("PartDesign::LinearPattern", "PatternKeyways")
    pattern.Originals = [groove]
    pattern.Vector = (App.Vector(1, 0, 0), ["X_Axis"])
    pattern.Occurrences = body.num_keyway
    
    # Calculate distribution
    # Total length = keyway_height
    # We want them distributed evenly.
    # Option A: Space them evenly with gaps.
    # Option B: Just space them.
    # Let's assume even distribution.
    # Distance between centers = keyway_height / num_keyway
    
    distance = body.keyway_height / body.num_keyway
    
    # We need to define the placement vectors for the pattern.
    # The pattern feature in FreeCAD 1.1 allows setting the distribution manually or via parameters.
    # Let's set the pattern to be centered and distributed.
    # Since we are using LinearPattern, we can define the offsets.
    # However, the LinearPattern feature usually handles the replication.
    # To center them, we can set the first occurrence offset to -distance/2 and step to distance.
    
    # Let's use the "Pattern" feature's internal logic.
    # We need to specify the spacing.
    pattern.SetProperty("Type", "LinearPattern")
    pattern.Axis = (App.Vector(1, 0, 0), ["X_Axis"])
    pattern.Occurrences = body.num_keyway
    pattern.Distribution = "Equal" # Or specific offsets
    
    # Actually, to control the exact position relative to the shaft length, 
    # we might want to center the entire group of keyways.
    # The LinearPattern feature allows defining the "First" and "Last" positions.
    # Let's set the pattern to distribute over the length keyway_height.
    
    # Better approach for exact centering:
    # Use "LinearPattern" with "Equal" distribution.
    # The pattern feature has a property "Position" or we can set the vectors.
    # In FreeCAD 1.1:
    pattern.Axis = (App.Vector(1, 0, 0), ["X_Axis"])
    pattern.Vector = (App.Vector(1, 0, 0), ["X_Axis"])
    pattern.Occurrences = body.num_keyway
    pattern.Distribution = "Equal"
    pattern.Direction = "Forward" # X positive
    
    # To center the pattern exactly, we can adjust the first vector.
    # But LinearPattern usually centers the set if configured right.
    # Let's try to set the vectors explicitly to ensure centering.
    # Offsets: -total/2, -total/2 + step, ..., +total/2
    
    step = body.keyway_height / body.num_keyway
    total = body.keyway_height
    
    # We will set the pattern to start at -total/2 and step by 'step'
    # But LinearPattern doesn't directly take a list of vectors easily in one line without a loop.
    # Alternative: Use "PolarPattern" logic adapted to linear? No, Linear is correct.
    # Let's use the "Pattern" feature's "Vector" property which is a list of vectors for the occurrences?
    # No, "Vector" is the axis of the pattern.
    # We need to use the "Occurrences" and "Distribution" and then manually set the "Offset" if needed?
    # FreeCAD 1.1 LinearPattern:
    # property: Vector (Axis)
    # property: Offset (Distance from start)
    # property: Step (Distance between copies)
    # property: Occurrences
    
    # Let's set Offset to -total/2 and Step to total/num.
    # This will place the first one at -total/2.
    # The last one will be at -total/2 + (num-1)*step.
    # This centers the group if num is odd. If num is even, it's slightly off-center relative to total/2.
    # But for this task, "Evenly distributed" is the standard interpretation.
    
    pattern.Offset = -total / 2.0
    pattern.Step = step
    
    # --- Finalize ---
    doc.recompute()
    
    # Save the file
    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "answer.FCStd"
    doc.saveAs(str(output_path))
    
    return doc

if __name__ == "__main__":
    create_shaft()
