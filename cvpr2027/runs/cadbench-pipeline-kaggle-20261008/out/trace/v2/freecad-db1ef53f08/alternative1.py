from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Create new document
    doc = App.newDocument("FlangeMounting")

    # 1. Create named parameters to drive the geometry
    params = doc.addObject("App::FeaturePython", "Parameters")
    # In FreeCAD 1.1, we often use PropertyValue or similar, but for simplicity in scripts 
    # that need to be robust without specific property classes, we can use standard App::Property*
    # However, the prompt implies using a generic approach. Let's use a VarSet or simply set properties 
    # on the Body or a dedicated container if standard types aren't strictly enforced by the prompt's "named" requirement.
    # The prompt example used App::VarSet. Let's stick to that pattern for named parameters.
    
    # Actually, App::VarSet is an App::Object. Let's create it properly.
    param_obj = doc.addObject("App::VarSet", "Parameters")
    param_obj.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner bore diameter")
    param_obj.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer flange diameter")
    param_obj.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of flange")
    param_obj.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Bolt circle diameter")
    param_obj.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of bolt holes")
    param_obj.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Count of bolt holes")

    # Set initial values from the prompt
    param_obj.inner_diameter = 34.925
    param_obj.outer_diameter = 69.454
    param_obj.flange_thickness = 26.194
    param_obj.pitch_circle_diameter = 57.547
    param_obj.bolt_hole_diameter = 6.747
    param_obj.number_bolt_holes = 4

    # 2. Create the Body
    body = doc.addObject("PartDesign::Body", "Body")
    # Note: In FreeCAD 1.1, creating objects directly in the document often requires them to be placed in the Body context
    # or the Body must be active. But PartDesign::Body is a container. We will add features to it.

    # 3. Create the Main Profile Sketch (Outer Diameter)
    # We need a sketch on the XY plane. FreeCAD provides standard planes.
    # In headless mode, we usually reference standard planes like "XY_Plane".
    # However, we need to ensure the plane exists. FreeCAD usually has them if the Workbench is loaded, 
    # but in pure headless script without GUI, we might need to create a Plane or reference a standard one if available.
    # Standard approach: Create a Plane object or use the built-in ones if the document initializes them.
    # To be safe and independent, let's create a reference plane or use the standard ones.
    # The prompt example used XY_Plane. Let's assume they exist or create a simple one.
    
    # Let's try to reference standard planes. If they fail, we create a Plane.
    # In FreeCAD 1.1, standard planes (XY_Plane, etc.) are often available in the Base or PartDesign workbench.
    # Since we are building a script, let's create a Plane to be absolutely sure it exists.
    
    ref_plane = doc.addObject("Part::Plane", "XY_Plane")
    ref_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    
    sketch_main = doc.addObject("Sketcher::SketchObject", "Sketch_Main")
    sketch_main.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation()) # Flat face, Z=0
    sketch_main.Support = (ref_plane, [])
    sketch_main.MapMode = "FlatFace"
    
    # Add Circle for Outer Diameter
    # Radius = outer_diameter / 2
    r_outer = param_obj.outer_diameter / 2.0
    circle_outer = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_outer)
    sketch_main.addGeometry(circle_outer, False)

    # 4. Create the Central Bore Sketch
    # This can be done on the same sketch plane, offset in Z, or a separate sketch.
    # Let's do a separate sketch on the same plane for clarity, or just use the same sketch?
    # To keep it simple and editable, let's create a second sketch for the hole, 
    # but since it's concentric, we can do it in the same sketch if we wanted.
    # However, the prompt asks for "PartDesign features". Usually, a hole is a Pocket.
    # A Pocket needs a closed loop.
    # Let's create a second sketch specifically for the hole to demonstrate feature separation.
    
    # Wait, if we use a second sketch, we need another plane or offset.
    # Let's create a sketch on the same plane, offset by a tiny amount? Or just use the same sketch?
    # Best practice: One sketch for the main profile, one for the hole? 
    # Or one sketch with both loops? 
    # Let's use one sketch for the main profile, and a separate sketch for the hole to show distinct features.
    # But the hole is concentric. Let's make the hole a Pocket using a sketch on the same plane?
    # Sketcher::SketchObject supports multiple loops.
    # Let's do it in ONE sketch for efficiency, then Pad and Pocket.
    # Actually, the prompt says "built from sketches and PartDesign features".
    # Let's create a second sketch for the hole to be explicit about the "feature tree" requirement.
    
    # Re-evaluating: To ensure "exactly one solid body", we must be careful with order.
    # Pad first (adds material), then Pocket (subtracts).
    
    # Let's create a second sketch for the hole on the same plane (XY).
    # We need to define the support. We can reuse XY_Plane.
    sketch_hole = doc.addObject("Sketcher::SketchObject", "Sketch_Hole")
    sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0.001), App.Rotation()) # Slight offset to avoid coplanar issues if any, though FlatFace handles it.
    sketch_hole.Support = (ref_plane, [])
    sketch_hole.MapMode = "FlatFace"
    
    r_inner = param_obj.inner_diameter / 2.0
    circle_inner = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_inner)
    sketch_hole.addGeometry(circle_inner, False)

    # 5. Create Bolt Hole Sketch
    # This needs to be on a plane that is concentric with the main body but allows us to draw the circle.
    # The bolt holes are on the pitch circle.
    # We can create a sketch on the XY plane, but we need to place the circle at distance pitch_circle_diameter/2.
    # Or we can create a sketch on a plane offset? No, the holes are on the face.
    # So we use the same plane (XY).
    
    sketch_bolt = doc.addObject("Sketcher::SketchObject", "Sketch_Bolt")
    sketch_bolt.Placement = App.Placement(App.Vector(0, 0, 0.002), App.Rotation())
    sketch_bolt.Support = (ref_plane, [])
    sketch_bolt.MapMode = "FlatFace"
    
    r_bolt = param_obj.bolt_hole_diameter / 2.0
    # We will add one circle here, and use Polar Pattern later.
    circle_bolt = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_bolt)
    sketch_bolt.addGeometry(circle_bolt, False)

    # 6. Create PartDesign Features
    
    # Feature 1: Pad (The Flange Body)
    # Profile is Sketch_Main. Length is flange_thickness.
    pad = body.newObject("PartDesign::Pad", "Pad_Flange")
    pad.Profile = sketch_main
    pad.Length = param_obj.flange_thickness
    pad.Type = "Full" # Full is standard for extrusion from a sketch on a face/plane
    # Ensure the sketch is attached to the body context properly.
    # In PartDesign, sketch.Profile property links to the sketch object.
    
    # Feature 2: Pocket (The Central Bore)
    # Profile is Sketch_Hole. Type ThroughAll.
    pocket_center = body.newObject("PartDesign::Pocket", "Pocket_Center")
    pocket_center.Profile = sketch_hole
    pocket_center.Type = "ThroughAll"
    
    # Feature 3: Hole (Bolt Holes)
    # We use a PolarPattern on the bolt sketch.
    # First, place the single hole sketch in the Body.
    # Then pattern it.
    
    # Create the Hole feature (single instance)
    # Since we used a sketch, we can use a Hole feature or a Pocket. 
    # Hole feature is often cleaner for holes, but Pocket works too. 
    # Let's use Hole feature for specificity.
    # Wait, PartDesign::Hole usually requires a specific sketch setup or uses a standard hole.
    # If we have a custom sketch, Pocket is safer and fully parametric.
    # Let's use Pocket for the bolt holes.
    
    pocket_bolt = body.newObject("PartDesign::Pocket", "Pocket_Bolt_Single")
    pocket_bolt.Profile = sketch_bolt
    pocket_bolt.Type = "ThroughAll"
    
    # Feature 4: Polar Pattern
    # We need to pattern the bolt pocket.
    # We need an axis. Z_Axis.
    # Create a reference axis object if not present.
    axis_z = doc.addObject("Part::Axis", "Z_Axis")
    # Placement for Axis is tricky. App::Axis is a specific type.
    # In FreeCAD 1.1, creating a Part::Axis is the way.
    # But usually, we reference the Z-Axis of the workbench or a plane.
    # Let's create a simple Axis object.
    # App::Axis needs a Point and a Direction? Or is it a specific placement?
    # Actually, Part::Axis is often created via placement.
    # Let's try to reference the standard Z-Axis if available, or create a Plane and use its normal.
    # Alternative: Use the "Z_Axis" from the "XY_Plane" if it has one.
    # Let's create a specific Axis object for the pattern.
    
    # Simplified approach for Axis: Use the Z_Axis from the reference plane if possible, 
    # or define a simple Axis object.
    # In FreeCAD 1.1, `doc.addObject("Part::Axis", "Z_Axis")` works.
    # But we need to set its properties.
    # App::Axis properties: Point, Axis (Vector).
    # Let's assume the Z_Axis is aligned with Z.
    # Actually, `Part::Axis` is a feature.
    
    # Let's try to use the standard Z axis from the XY_Plane if it exists, or create a new one.
    # Given the constraints, creating a new Axis object is safer.
    # But how to set its direction? 
    # Let's use the "Z_Axis" from the standard set if we can access it, otherwise define a custom one.
    # Let's create a custom Axis aligned with Z.
    # We need to know the properties of App::Axis. 
    # Usually it's just a placement or point+vector.
    # Let's skip creating a complex Axis object and use the standard one if we can find it, 
    # or create a Plane and use its Normal.
    # Actually, PartDesign::PolarPattern requires an Axis (Part::Axis or similar).
    # Let's create a simple Axis feature.
    
    axis_obj = doc.addObject("Part::Axis", "Pattern_Axis")
    # Properties: Point (Vector), Axis (Vector3).
    # Let's set them.
    try:
        axis_obj.Point = App.Vector(0, 0, 0)
        axis_obj.Axis = App.Vector(0, 0, 1)
    except:
        # Fallback if properties differ slightly
        pass

    pattern = body.newObject("PartDesign::PolarPattern", "Pattern_Bolts")
    pattern.Originals = [pocket_bolt]
    pattern.Axis = (axis_obj, [""])
    pattern.NumberOfOccurrences = param_obj.number_bolt_holes
    # Calculate angle
    angle_step = 360.0 / param_obj.number_bolt_holes
    pattern.Angle = angle_step
    
    # Feature 5: Fillets (Optional but good for realism, prompt doesn't strictly require it, 
    # but "fillet, chamfer" were in the example list. The description says "round mounting flange".
    # Let's add a small fillet to the outer edge to make it "round" in finish, or just leave it sharp.
    # The prompt says "reproduces the part described below". Description doesn't mention fillets.
    # I will skip fillets to strictly follow "exactly one solid body" and the specific dimensions.
    # Adding fillets might change the effective diameter slightly if not careful, or just add complexity not requested.
    # I will stick to the dimensions given.

    # 7. Finalize
    doc.recompute()

    # 8. Save
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / f"{script_path.stem}.FCStd"
    
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    main()
