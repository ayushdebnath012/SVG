from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # 1. Create Document
    doc = App.newDocument("SpringPin")
    
    # Define parameters in a VarSet for editability
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the pin")
    params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter of the pin")
    params.addProperty("App::PropertyLength", "pin_length", "Dimensions", "Total length of the pin")
    params.addProperty("App::PropertyLength", "chamfer_length", "Dimensions", "Length of the chamfer")
    params.addProperty("App::PropertyAngle", "slot_angle", "Dimensions", "Angle of the longitudinal slot")
    
    # Set initial values based on requirements
    params.outer_diameter = 1.3
    params.inner_diameter = 0.8
    params.pin_length = 4.0
    params.chamfer_length = 0.35
    params.slot_angle = 15.0

    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")

    # --- Feature 1: Chamfered Cylinder Base ---
    # Sketch on XY plane (Z=0) to define the base profile including chamfer
    sketch_chamfer = body.newObject("Sketcher::SketchObject", "Sketch_Chamfer")
    sketch_chamfer.Plane = doc.getObject("XY_Plane")
    sketch_chamfer.MapMode = "FlatFace"
    
    # Line 1: Bottom outer edge
    line1 = Part.LineSegment(App.Vector(0, -params.outer_diameter/2, 0), App.Vector(0, params.outer_diameter/2, 0))
    # Line 2: Top outer edge
    line2 = Part.LineSegment(App.Vector(0, params.outer_diameter/2, 0), App.Vector(0, params.outer_diameter/2, -params.chamfer_length))
    # Line 3: Chamfer vertical face
    line3 = Part.LineSegment(App.Vector(0, params.outer_diameter/2, -params.chamfer_length), App.Vector(0, params.inner_diameter/2, -params.chamfer_length))
    # Line 4: Top inner edge
    line4 = Part.LineSegment(App.Vector(0, params.inner_diameter/2, -params.chamfer_length), App.Vector(0, params.inner_diameter/2, 0))
    # Line 5: Bottom inner edge
    line5 = Part.LineSegment(App.Vector(0, params.inner_diameter/2, 0), App.Vector(0, -params.inner_diameter/2, 0))
    # Line 6: Bottom chamfer vertical face
    line6 = Part.LineSegment(App.Vector(0, -params.inner_diameter/2, 0), App.Vector(0, -params.inner_diameter/2, -params.chamfer_length))
    # Line 7: Chamfer bottom face
    line7 = Part.LineSegment(App.Vector(0, -params.inner_diameter/2, -params.chamfer_length), App.Vector(0, -params.outer_diameter/2, -params.chamfer_length))
    # Line 8: Bottom outer edge closure
    line8 = Part.LineSegment(App.Vector(0, -params.outer_diameter/2, -params.chamfer_length), App.Vector(0, -params.outer_diameter/2, 0))

    sketch_chamfer.addGeometry(line1, False)
    sketch_chamfer.addGeometry(line2, False)
    sketch_chamfer.addGeometry(line3, False)
    sketch_chamfer.addGeometry(line4, False)
    sketch_chamfer.addGeometry(line5, False)
    sketch_chamfer.addGeometry(line6, False)
    sketch_chamfer.addGeometry(line7, False)
    sketch_chamfer.addGeometry(line8, False)

    # Constraints for Chamfer Sketch
    # Coincident center
    sketch_chamfer.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    # Parallel lines (Outer verticals)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Parallel", 0, 0, 1, 0), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Parallel", 0, 1, 1, 1), False)
    # Parallel lines (Inner verticals)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Parallel", 0, 0, 1, 2), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Parallel", 0, 2, 1, 3), False)
    # Vertical lines (Chamfers)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 1, 1), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Vertical", 0, 1, 1, 6), False)
    # Horizontal lines (Top/Bottom)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 1, 0), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Horizontal", 0, 1, 1, 2), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Horizontal", 0, 2, 1, 3), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Horizontal", 0, 5, 1, 7), False)
    # Symmetry
    sketch_chamfer.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 1, 0), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 1, 1), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Symmetry", 0, 2, 1, 2), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Symmetry", 0, 5, 1, 5), False)
    # Outer diameter constraint
    sketch_chamfer.addConstraint(Sketcher.Constraint("Length", 1, 1), False) # Approximate logic, usually done via math expression or explicit length
    # Let's use explicit geometry constraints for diameter
    # Distance from center to outer edge
    sketch_chamfer.addConstraint(Sketcher.Constraint("Distance", 0, 0, 1, 0), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Distance", 0, 0, 1, 7), False)
    # Distance from center to inner edge
    sketch_chamfer.addConstraint(Sketcher.Constraint("Distance", 0, 0, 1, 2), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Distance", 0, 0, 1, 5), False)
    # Length of chamfer face
    sketch_chamfer.addConstraint(Sketcher.Constraint("Length", 1, 1), False)
    sketch_chamfer.addConstraint(Sketcher.Constraint("Length", 1, 6), False)

    # Drive outer_diameter parameter
    sketch_chamfer.addExpression("Distance", "Parameters.outer_diameter", "0", "0")
    # Drive inner_diameter parameter
    sketch_chamfer.addExpression("Distance", "Parameters.inner_diameter", "0", "0")
    # Drive chamfer_length parameter
    sketch_chamfer.addExpression("Length", "Parameters.chamfer_length", "1", "0")

    pad_chamfer = body.newObject("PartDesign::Pad", "Pad_Chamfer")
    pad_chamfer.Profile = sketch_chamfer
    pad_chamfer.Length = params.pin_length
    pad_chamfer.Midplane = False # Extrude upwards from Z=0

    # --- Feature 2: Internal Bore ---
    # Sketch on the top face of the previous pad (or create a sketch on XY plane offset)
    # To ensure we are on the top face of the chamfered pin, we attach to the face.
    # However, to keep it simple and robust in headless mode, we will create a sketch on the XY plane 
    # but offset Z to the top of the pad, or simply define it relative to the Body coordinate system 
    # and let the feature placement handle it. 
    # Better approach for PartDesign: Create a sketch on the face of the Pad.
    
    # Get the face of the pad (Top face)
    # We need to find the face index. 
    # In PartDesign, we can't easily get the face index without recompute or complex logic.
    # Alternative: Create a sketch on XY plane at Z = pin_length.
    
    sketch_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
    sketch_bore.Plane = doc.getObject("XY_Plane")
    sketch_bore.MapMode = "FlatFace"
    sketch_bore.AttachmentOffset = 0.0 # Will be handled by the feature placement
    
    # Create a circle for the bore
    circle = Part.Circle(App.Vector(0, 0, params.pin_length), App.Vector(0, 0, 1), params.inner_diameter/2)
    sketch_bore.addGeometry(circle, False)
    
    sketch_bore.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    sketch_bore.addExpression("Radius", "Parameters.inner_diameter", "0", "0")

    pocket_bore = body.newObject("PartDesign::Pocket", "Pocket_Bore")
    pocket_bore.Profile = sketch_bore
    pocket_bore.Type = "Blind"
    pocket_bore.Reference = (doc.getObject("Z_Axis"), [""]) # Reference axis for blind depth if needed, but we want full length usually.
    # Actually, for a through hole in a spring pin, we want it to go all the way through.
    # Since the pad starts at Z=0 and goes to Z=pin_length, a "ThroughAll" on Z_Axis works perfectly.
    # We need to ensure the sketch is on the top face. 
    # The default attachment for a new sketch on XY_Plane is Z=0.
    # We must move the sketch to the top of the pad.
    # We can do this by setting the Placement of the pocket or the sketch.
    # PartDesign::Pocket has a Placement property if we use "Placement" constraint, but simpler is to use the sketch offset.
    # Let's re-attach the sketch to the top face of the pad.
    
    # To do this programmatically without interactive selection:
    # 1. Recompute to create the geometry.
    # 2. Get the top face of the pad.
    # 3. Create a new sketch attached to that face.
    # 4. Create the pocket.
    
    # Let's refactor the sketch creation order.
    pass

    # Re-do the sketch logic to ensure correct attachment
    # Step 1: Pad (Done)
    # Step 2: Create sketch on the top face of the Pad.
    
    # We need to access the Pad's result to get the face.
    # Since we haven't recomputed yet, we can't get the shape.
    # Strategy: Define the sketch plane relative to the Body's coordinate system but offset Z?
    # No, the sketch must be on a face.
    # Strategy: Use a workaround. Create the sketch on XY plane, then move the sketch's plane?
    # Or, create the sketch, then use "Link to existing face" logic.
    
    # Let's try a different approach: 
    # 1. Pad the cylinder (circular profile).
    # 2. Cut the chamfer (using a sketch on the top face).
    # 3. Cut the slot (using a sketch on the side face).
    
    # Revised Plan:
    # 1. Create a circular pad.
    # 2. Create a chamfer feature (or sketch+pad with reversed) to create the slot/chamfer.
    # Actually, a spring pin slot is a rectangular cut through the diameter.
    # It's easier to make a full cylinder, then cut the slot using a "Slot" or "Groove" or a specific sketch+pad.
    # Given the requirement for "longitudinal slot along its length", a Groove or a specific Pad/Pocket chain is best.
    
    # Let's stick to the prompt's specific features if possible, but "Slot" is not a standard PartDesign feature name in 1.1 API list provided.
    # We can simulate a slot using a "Groove" (Revolution subtraction) or a "Pocket" with a specific profile.
    # A slot along the length is essentially a rectangular prism cut out.
    
    # Plan B:
    # 1. Pad: Cylinder (Outer Dia, Length).
    # 2. Pocket: Cut the slot.
    #    Sketch: Profile of the slot on the top face.
    #    Feature: Pocket.
    
    # Let's implement Plan B cleanly.
    
    # Clear previous attempts
    doc.removeObject("Sketch_Chamfer")
    doc.removeObject("Pad_Chamfer")
    doc.removeObject("Sketch_Bore")
    doc.removeObject("Pocket_Bore")

    # --- Step 1: Main Cylinder ---
    sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_Main")
    sketch_main.Plane = doc.getObject("XY_Plane")
    sketch_main.MapMode = "FlatFace"
    
    # Create a circle for the main cylinder
    circle_main = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter/2)
    sketch_main.addGeometry(circle_main, False)
    
    sketch_main.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    sketch_main.addExpression("Radius", "Parameters.outer_diameter", "0", "0")
    
    pad_main = body.newObject("PartDesign::Pad", "Pad_Main")
    pad_main.Profile = sketch_main
    pad_main.Length = params.pin_length
    pad_main.Midplane = False

    # --- Step 2: Internal Bore ---
    # Attach sketch to the top face of Pad_Main
    # We need to find the face index of the top face.
    # Since we can't interactively select, we can create a sketch on the XY plane, 
    # but offset the sketch's plane to Z = pin_length.
    # PartDesign allows setting the Plane of a sketch to a specific Face? 
    # No, it attaches to a face.
    
    # Workaround: Create a dummy plane at the top? No.
    # Workaround: Create the sketch on XY plane, then use the "Placement" of the feature?
    # No, the sketch defines the geometry.
    
    # Correct Programmatic Way:
    # 1. Get the face of the pad.
    # 2. Create a new sketch object attached to that face.
    
    # We need to recompute first to get the shape.
    doc.recompute()
    
    # Get the solid body from the pad
    # The body has one shape.
    # Find the face with normal Z (top).
    shape = body.Shape
    # Top face is usually the one with normal (0,0,1) and max Z.
    # Or simply iterate faces.
    top_face = None
    for face in shape.Faces:
        if face.Plane.Normal.z > 0.99: # Top face
            top_face = face
            break
            
    if not top_face:
        raise Exception("Could not find top face")
        
    sketch_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
    sketch_bore.Plane = top_face
    sketch_bore.MapMode = "FlatFace"
    
    # Add inner circle
    circle_bore = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter/2)
    sketch_bore.addGeometry(circle_bore, False)
    
    sketch_bore.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    sketch_bore.addExpression("Radius", "Parameters.inner_diameter", "0", "0")
    
    pocket_bore = body.newObject("PartDesign::Pocket", "Pocket_Bore")
    pocket_bore.Profile = sketch_bore
    pocket_bore.Type = "ThroughAll"

    # --- Step 3: Longitudinal Slot ---
    # The slot is a rectangular cut along the length.
    # We can model this as a "Groove" (Revolution) or a "Pocket" on the side face.
    # Since it's a straight slot, a Pocket on the side face is easiest.
    
    # Find the side face (e.g., one of the circular edges).
    # Actually, the slot is along the length.
    # We can sketch on the side face (cylinder side).
    # But the side face is curved. Sketching on a curved face is tricky in headless.
    # Alternative: Create a "Groove" feature (PartDesign::Groove) which is a subtractive revolution.
    # Profile: Rectangle. Axis: Centerline of the cylinder.
    # This creates a slot around the cylinder.
    # We need to position it.
    
    # Let's use PartDesign::Groove.
    # Profile: Rectangle defined by width (slot width) and depth (half slot depth? No, full depth).
    # Wait, a groove is a revolution. It creates a ring of slots.
    # We want ONE slot.
    # So we cannot use Groove (which is rotational).
    # We must use a Pad (additive) or Pocket (subtractive) on a side face.
    # Or, create a "Slot" feature if it exists? No.
    #
