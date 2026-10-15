import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

def create_document():
    doc = App.newDocument("NozzleNozzle")
    App.setLastActiveView(doc) # Ensure doc is active for object creation if needed
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    doc.addObject("PartDesign::Body", "Body") # Fix duplicate if needed by logic, but standard is one line.
    # Actually, the line above creates the object. Let's restart cleanly.
    doc = App.newDocument("NozzleNozzle")
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    
    # --- Parameters ---
    # Base Part Parameters
    p = body.newObject("App::Property", "Params") # Just a container if needed, but FreeCAD 1.1 prefers setting properties directly on the Body or a specific VarSet if complex.
    # However, to keep it simple and robust in headless mode without App::VarSet clutter, we will set properties directly on the Body or use a dedicated Parameter object if expressions are needed.
    # Let's use the Body directly for simplicity in this specific constraint set, or a dedicated object for clarity.
    # The prompt asks for "named document objects whose properties drive the geometry".
    
    params = body.newObject("App::VarSet", "Parameters")
    params.width = 30.0
    params.length = 50.0
    params.step1_d = 15.0
    params.step1_l = 1.3
    params.step2_d = 17.0
    params.step2_l = 8.6
    params.step3_d = 15.0
    params.step3_l = 2.8
    params.step4_d = 19.0
    params.step4_l = 4.1
    params.upper_len = 17.8198418
    params.upper_depth = 26.1054564
    params.upper_r_inner = 25.0
    params.upper_r_conv = 6.0
    params.upper_r_conc = 28.5
    params.upper_contour_l = 15.0
    params.upper_overshoot = -1.2
    params.upper_conv_x = -0.1143294
    params.upper_conv_y = 19.0010894
    params.upper_conc_x = 34.0971297
    params.upper_conc_y = 19.955369
    params.bore_d = 2.0
    params.cav_taper_d = 9.0
    params.cav_taper_l = 3.0
    params.cav_s1_d = 8.0
    params.cav_s1_l = 14.0
    params.cav_s2_d = 10.0
    params.cav_s2_l = 10.0
    params.cav_s3_d = 5.0
    params.cav_s3_l = 8.14
    
    # Edit Parameters (Default values, will be overridden or used for logic)
    params.side_len = 7.06
    params.side_w = 5.81
    params.side_dep = 19.0
    params.side_off_x = -17.03
    params.side_off_y = -5.105
    params.side_r_len = 7.41
    params.side_r_w = 6.0
    params.side_r_off_x = 17.205
    params.side_r_off_y = -5.2
    params.prim_w = 6.0
    params.prim_l = 13.51
    params.prim_dep = 21.0
    params.prim_off_x = -7.0
    params.prim_count = 4
    params.sec_w = 5.12
    params.sec_dep = 10.0
    params.sec_l = 13.5
    params.sec_off_y = 14.25

    # --- Sketches and Features ---
    
    # 1. Base Cylinder
    sk_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sk_base.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    sk_base.Constrain = True
    sk_base.ConstraintList = []
    sk_base.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.width), False)
    sk_base.AddConstraint(Sketcher.Constraint("Radius", 0, 1, params.width)) # Redundant but safe
    sk_base.AddConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # Centerline
    sk_base.AddConstraint(Sketcher.Constraint("Vertical", 0, 1)) # Centerline
    
    pad_body = body.newObject("PartDesign::Pad", "PadBody")
    pad_body.Profile = sk_base
    pad_body.Length = params.length
    pad_body.Type = "Solid"
    
    # 2. Lower Stepped Relief (Subtractive)
    # We need a sketch representing the stepped profile.
    # Strategy: Create a closed profile of the outer diameter minus the steps.
    # Or simpler: Create a sketch on the face, draw the step geometry relative to the face normal.
    
    # Let's define the steps relative to the start face (Z=0).
    # The cutout goes INWARD.
    # Step 1: D=15, L=1.3
    # Step 2: D=17, L=8.6
    # Step 3: D=15, L=2.8
    # Step 4: D=19, L=4.1
    # Total length = 1.3+8.6+2.8+4.1 = 16.8mm.
    # Remaining length = 50 - 16.8 = 33.2mm.
    # Upper contour starts at 16.8mm.
    
    sk_lower = body.newObject("Sketcher::SketchObject", "LowerStepSketch")
    sk_lower.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    sk_lower.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    sk_lower.MapMode = "FlatFace"
    
    # Define points for the stepped cutout
    # We draw a closed loop: Outer diameter circle, then steps inward.
    # Actually, it's easier to draw the steps as a profile and subtract.
    # Profile: Start at center, go up Z to max_depth, step in/out? No, it's axial cutouts.
    # Let's create a sketch on the XY plane (Z=0).
    # Draw the outline of the solid part in the XY plane at Z=0? No, that's the whole cylinder.
    # We need to cut INTO the cylinder.
    # Sketch on Front Plane (YZ plane) is better for axial steps?
    # Let's stick to XY plane and use a 3D sketch or just a 2D profile extruded.
    # Wait, PartDesign Pocket on a face.
    # Face is XY plane (Z=0). Normal is Z.
    # We need to cut along Z.
    # So the sketch should be on the XY plane, defining the shape of the hole/cutout.
    # But the cutout is a "stepped relief" on the END FACE? 
    # "One end contains a four-stage stepped annular relief."
    # This implies the cutout is on the face, extending axially? Or is it a groove on the face?
    # "Annular relief" usually means a recessed area on the face surface.
    # "Internal cavity begins at the stepped-relief end".
    # Interpretation: The end face (Z=0) has a complex shape. 
    # Center: Through bore.
    # Ring 1: Cutout D15x1.3 (Depth into face? Or axial?)
    # "Axial body". "Internal cavity begins at the stepped-relief end".
    # It sounds like the end face is modified, and the internal cavity starts there.
    # Let's assume the "stepped relief" is a set of concentric grooves cut INTO the face (Z negative direction relative to the face normal? Or positive?)
    # Let's assume Z is the cylinder axis. The face is at Z=0. The body is 0 to 50.
    # The relief is on the face Z=0, going towards Z=0 (negative) or Z=50?
    # "Internal cavity begins at the stepped-relief end".
    # This implies the relief is the entrance to the internal cavity.
    # So the relief is a groove on the face Z=0, extending into the face (Z < 0) or is it a hole?
    # "Annular relief" -> Groove on the face.
    # But the parameters have lengths (1.3, 8.6, etc). These sound like axial lengths of a stepped hole.
    # "Four-stage stepped annular relief".
    # Hypothesis: It is a stepped hole starting from the face Z=0, going into the cylinder (positive Z).
    # But the cylinder is 50mm long.
    # If the hole is at the end, it goes from Z=0 to Z=16.8.
    # Then the "upper contoured channel" follows?
    # "Upper contoured annular channel transitions through the specified convex and concave arcs."
    # This sounds like the wall thickness changes or an outer groove.
    # "Centered axial body".
    # "Small coaxial bore passes through".
    # "Larger internal cavity begins at the stepped-relief end with a tapered inlet followed by three ordered cylindrical sections."
    
    # Re-reading carefully:
    # "One end contains a four-stage stepped annular relief." -> This describes the feature on the end face.
    # "An upper contoured annular channel transitions..." -> This is likely the outer wall geometry or a groove near the end.
    # "A small coaxial bore passes through".
    # "A larger internal cavity begins at the stepped-relief end..."
    
    # Let's model the "stepped relief" as a stepped hole starting from the face Z=0 going inwards (positive Z).
    # Why? Because "internal cavity begins at... end".
    # So:
    # 0 to 1.3mm: D=15
    # 1.3 to 9.9mm: D=17
    # 9.9 to 12.7mm: D=15
    # 12.7 to 16.8mm: D=19
    # 16.8 to 50mm: Base D=30 (Wall thickness varies?)
    # Wait, "Annular relief" suggests it's a depression on the face, not a through hole.
    # But "internal cavity begins at the stepped-relief end".
    # Maybe the "stepped relief" IS the internal cavity entrance.
    # And the "upper contoured channel" is the transition of the internal cavity wall?
    # Or is it an outer groove? "Annular channel" could be outer.
    # Given "Upper contoured cutout depth = 26mm", and cylinder radius = 15mm.
    # If it's an inner cutout (cavity), depth 26mm means it eats through the 15mm radius?
    # Radius 15. Depth 26 implies it goes past the center to the other side?
    # Or is it an outer groove?
    # If it's an outer groove, depth 26mm on a 30mm diameter part (radius 15) is impossible (max depth 15).
    # So it MUST be an internal cavity.
    # Depth 26mm means the cavity goes from Z=0 to Z=26? Or Z=0 to Z=-26?
    # If the cylinder is 0 to 50.
    # Cavity starts at Z=0. Depth 26. So it exists in Z=0 to Z=26?
    # But there is a "stepped relief" first.
    # So:
    # 0-16.8: Stepped entrance.
    # 16.8-26: Contoured section (Upper contoured cutout).
    # 26-50: Main cavity?
    
    # Let's assume the "Upper contoured cutout" is the shape of the internal cavity wall between the stepped section and the main cavity.
    # The "Internal stepped cavity" parameters define the rest of the cavity.
    
    # Plan:
    # 1. Pad Cylinder (Z=0 to Z=50, D=30).
    # 2. Pocket "InternalCavity". 
    #    - This pocket will create the internal void.
    #    - It needs to handle the stepped entrance, the contoured transition, and the stepped sections.
    #    - Sketch on Z=0 plane (Face).
    #    - Profile: A curve representing the cavity boundary in the YZ plane (since it's axial).
    #    - Wait, PartDesign Sketch is 2D.
    #    - We can sketch on the XY plane and use a "Pocket" with a specific reference? No, Pocket extrudes along the face normal.
    #    - If we sketch on XY plane, extrude is along Z.
    #    - Profile needs to be the shape of the hole in the XY plane? No, that would be a through hole.
    #    - We need to define the shape of the cavity in the YZ plane, then rotate? No, we can't rotate a sketch profile in a standard Pocket.
    #    - Solution: Create a sketch on the YZ plane (at X=0)? No, Body must be attached to a face.
    #    - Solution: Create a sketch on the XY plane (Face Z=0), but define the profile as a line from (0,0) to (0, 26) with the varying radius?
    #    - No, Sketcher creates a 2D shape.
    #    - Trick: Use a "Pocket" on the face, but the profile is the cross-section of the cavity in the YZ plane? 
    #    - This is not possible directly with standard PartDesign::Pocket on a face unless the feature is a "Shell" or similar, or we use a "Pad" to subtract.
    #    - Better approach: Create the cavity as a "Pad" (additive) rotated 180? No.
    #    - Best approach for non-constant cross-section: 
    #      1. Sketch on YZ plane (X=0)? No, needs a face.
    #      2. Create a sketch on the XY plane (Z=0). Draw a circle of max diameter.
    #      3. Use "PartDesign::Pocket" with Type="ThroughAll"? No.
    #      4. Alternative: Create the internal cavity as a separate "Pad" (negative) using a "Revolution" of the YZ profile?
    #      - Yes! Create a sketch on the YZ plane (X=0, YZ plane). 
    #      - Reference: The face Z=0 is not in the YZ plane.
    #      - We need to reference the Cylinder Face (Z=0) and the Cylinder Axis (Z).
    #      - Sketcher::SketchObject can be attached to a face. If we attach to Z=0 face, the sketch plane is XY.
    #      - If we want to sketch in YZ, we need to attach to a face that lies in YZ, e.g., X=0 face. But the cylinder has no flat face at X=0.
    #      - Solution: Create a "PartDesign::Face" (a flat face on the cylinder surface)? No.
    #      - Standard trick: Sketch on XY plane. Define the profile as a closed loop?
    #      - If we want a variable radius cavity, we can't do it with a simple 2D sketch and Pad/Pocket.
    #      - UNLESS: We use "PartDesign::Pocket" with a "Reference" that is a curve? No.
    #      - We must use "PartDesign::Revolution" or "PartDesign::Groove" (which is a revolution pocket).
    #      - Yes! "Groove" is a subtractive revolution.
    #      - We can create a sketch on the XY plane (Face Z=0). 
    #      - Draw a line from (0,0) to (0, 26) representing the radius vs depth? No, Sketcher doesn't do 3D lines.
    #      - We need to sketch the profile in the YZ plane.
    #      - How to sketch on YZ plane?
    #        - Create a sketch attached to the "YZ_Plane" of the document? But the part is centered.
    #        - Create a sketch attached to the "Body" with MapMode="Plane"?
    #        - In FreeCAD, to sketch a profile for a revolution:
    #          - Create a sketch on the XY plane.
    #          - Draw a line from (0,0) to (0, 26)?? No, that's just a line.
    #          - We need a closed profile to revolve?
    #          - If we draw a line from (0,0) to (R, Z) and revolve around Z, it creates the surface.
    #          - But PartDesign::Revolution requires a closed profile (or open line? Open line creates a surface, closed creates solid).
    #          - We can create a closed profile by adding a line from (R
