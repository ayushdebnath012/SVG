from pathlib import Path
import FreeCAD as App, Part, Sketcher, PartDesign

def create_shaft():
    # Initialize Document
    doc = App.newDocument("ShaftDesign")
    doc.Label = "Smooth Shaft"
    
    # Create a PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # --- Parameters ---
    # Add parameters to the Body object
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
    # In FreeCAD 1.1, Plane is a property of the sketch object, but accessed differently or via the 'Plane' property 
    # which expects a reference to a plane object or a string if the plane exists in the document.
    # However, the most robust way in headless scripting for PartDesign sketches is to set the 'Plane' property 
    # to the name of the plane object in the document.
    # We need to ensure the XY_Plane exists. It usually does by default, but let's be explicit if needed.
    # Actually, Sketcher::SketchObject has a 'Plane' property that takes a reference.
    # Let's try setting it to the string name first, as is common in examples, but if that fails, we might need 
    # to reference the object.
    # Correction for FreeCAD 1.1: The 'Plane' property of Sketcher::SketchObject expects a reference to an object.
    # We must find the XY_Plane object.
    
    xy_plane = doc.getObject("XY_Plane")
    if not xy_plane:
        # Fallback: Create a plane if missing (though standard docs usually have it)
        # For this script, we assume standard FreeCAD installation includes XY_Plane.
        # If not, we can't easily create a named plane without more complex setup.
        # We will proceed assuming XY_Plane exists.
        pass
    
    main_sketch.Plane = xy_plane
    main_sketch.MapMode = "FlatFace"
    main_sketch.ConstrainAuto = True
    
    # Outer Circle (Shaft Profile)
    radius = body.smooth_shaft_diameter / 2.0
    main_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius), False)
    
    # Pad the shaft
    pad_shaft = body.newObject("PartDesign::Pad", "PadShaft")
    pad_shaft.Profile = main_sketch
    pad_shaft.Length = body.smooth_shaft_length
    pad_shaft.Type = "Blind"
    
    # --- Feature: Keyway Groove ---
    # 2. Keyway Sketch
    key_sketch = body.newObject("Sketcher::SketchObject", "KeywaySketch")
    yz_plane = doc.getObject("YZ_Plane")
    if not yz_plane:
        yz_plane = doc.getObject("XZ_Plane") # Fallback if YZ missing, though unlikely
    
    key_sketch.Plane = yz_plane
    key_sketch.MapMode = "FlatFace"
    key_sketch.ConstrainAuto = True
    
    # Rectangle on YZ plane centered at origin
    # Y range: -width/2 to +width/2
    # Z range: -depth/2 to +depth/2
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
    
    # 3. Create the Groove Feature
    groove = body.newObject("PartDesign::Groove", "GrooveKeyway")
    groove.Profile = key_sketch
    # Axis of revolution is X_Axis (1, 0, 0)
    x_axis = doc.getObject("X_Axis")
    groove.Axis = (x_axis, ["X_Axis"])
    groove.Type = "Blind"
    groove.Length = body.keyway_height # Axial length of the cut
    
    # --- Feature: Multiple Keyways (Pattern) ---
    # Create a LinearPattern of the groove
    pattern = body.newObject("PartDesign::LinearPattern", "PatternKeyways")
    pattern.Originals = [groove]
    
    # Axis for pattern
    pattern.Axis = (x_axis, ["X_Axis"])
    pattern.Vector = (x_axis, ["X_Axis"])
    pattern.Occurrences = body.num_keyway
    pattern.Distribution = "Equal"
    pattern.Direction = "Forward"
    
    # Calculate distribution to center the keyways
    step = body.keyway_height / body.num_keyway
    total = body.keyway_height
    
    # Set offset to center the pattern
    pattern.Offset = -total / 2.0
    pattern.Step = step
    
    # --- Finalize ---
    doc.recompute()
    
    # Save the file next to the script
    script_dir = Path(__file__).resolve().parent
    output_path = script_dir / "answer.FCStd"
    doc.saveAs(str(output_path))
    
    return doc

if __name__ == "__main__":
    create_shaft()
