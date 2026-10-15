import os
import sys
from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

def create_model():
    # Initialize document
    doc = App.newDocument("BoltHead")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Visibility = True

    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    
    # Base Part Parameters
    params.addProperty("App::PropertyLength", "head_height", "Dimensions", "height of the cylindrical head blank")
    params.head_height = 5.7
    
    params.addProperty("App::PropertyLength", "shank_diameter", "Dimensions", "diameter of the shank")
    params.shank_diameter = 8.0
    
    params.addProperty("App::PropertyLength", "shank_length", "Dimensions", "length of the shank")
    params.shank_length = 15.0
    
    params.addProperty("App::PropertyLength", "tip_diameter", "Dimensions", "diameter of the tip")
    params.tip_diameter = 5.5
    
    params.addProperty("App::PropertyLength", "tip_length", "Dimensions", "length of the tip")
    params.tip_length = 3.0
    
    # Edit Parameters (initially set to base values, will be overridden for edit file)
    params.addProperty("App::PropertyLength", "hex_head_across_flats", "Dimensions", "width across flats for hex head")
    params.hex_head_across_flats = 13.0
    
    params.addProperty("App::PropertyLength", "head_recess_depth", "Dimensions", "depth of the annular recess")
    params.head_recess_depth = 0.6
    
    params.addProperty("App::PropertyAngle", "head_underside_chamfer_angle", "Dimensions", "angle of chamfer from horizontal")
    params.head_underside_chamfer_angle = 30.0
    
    params.addProperty("App::PropertyLength", "head_underside_chamfer_axial_width", "Dimensions", "axial width of the chamfer")
    params.head_underside_chamfer_axial_width = 0.7

    # Helper to get plane
    def get_plane(name):
        return doc.getObject(name)

    # --- STEP 1: Create Base Geometry ---
    
    # 1.1 Head Sketch (Top face of head)
    # We start with a large cylinder for the head, then subtract the shank and tip.
    # The head is defined by the hex shape first, then we extrude the whole block.
    
    sk_head_top = body.newObject("Sketcher::SketchObject", "HeadTopSketch")
    sk_head_top.Placement = App.Placement(App.Vector(0, 0, params.head_height / 2))
    sk_head_top.Reference = (get_plane("XY_Plane"), [""])
    sk_head_top.Locked = True
    
    # Hexagon for the head top
    # Across flats = D. Radius to flat = D/2.
    # For a regular hexagon, distance from center to flat = R_in.
    # Distance from center to vertex = R_out = 2 * R_in / sqrt(3).
    # Wait, "across flats" is the distance between parallel sides. So R_in = (hex_head_across_flats) / 2.
    hex_af = params.hex_head_across_flats
    R_in = hex_af / 2.0
    R_out = R_in * (2.0 / math.sqrt(3.0))
    
    # Vertices for hexagon (flat top/bottom? No, usually flats are vertical in drawing, but here we just need the shape)
    # Let's orient with a flat at the top (y = R_in).
    angles = [30, 90, 150, 210, 270, 330] # degrees
    pts = []
    for ang in angles:
        rad = math.radians(ang)
        pts.append(App.Vector(R_out * math.cos(rad), R_out * math.sin(rad), 0))
    
    for i in range(len(pts)):
        sk_head_top.addGeometry(Part.LineSegment(pts[i], pts[(i+1)%len(pts)]), False)
        
    sk_head_top.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_head_top.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 0, 0, get_plane("XY_Plane"))) # Center
    sk_head_top.updateSubElements()
    
    # 1.2 Head Bottom Sketch (For chamfer and recess planning, but we will do features on the body)
    # Actually, for the base part, we just need the solid block.
    # Let's create the Hex Pad.
    
    pad_hex = body.newObject("PartDesign::Pad", "HexPad")
    pad_hex.Profile = sk_head_top
    pad_hex.Length = params.head_height
    pad_hex.makeSolid() # Ensure it's a solid
    
    # 1.3 Shank Sketch (Internal hole for shank)
    sk_shank = body.newObject("Sketcher::SketchObject", "ShankSketch")
    sk_shank.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_shank.Reference = (get_plane("XY_Plane"), [""])
    
    circle_shank = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shank_diameter / 2.0)
    sk_shank.addGeometry(circle_shank, False)
    sk_shank.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_shank.updateSubElements()
    
    # 1.4 Tip Sketch (Internal hole for tip)
    sk_tip = body.newObject("Sketcher::SketchObject", "TipSketch")
    sk_tip.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_tip.Reference = (get_plane("XY_Plane"), [""])
    
    circle_tip = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.tip_diameter / 2.0)
    sk_tip.addGeometry(circle_tip, False)
    sk_tip.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_tip.updateSubElements()

    # --- STEP 2: Create Features ---
    
    # 2.1 Pad the Hex Head
    # Since we already created a pad, let's remove it and do it properly in sequence or just use the one created.
    # To keep it clean, let's replace the previous manual pad creation with a feature.
    # We need to delete the manual HexPad created above and do it properly.
    body.removeObject("HexPad")
    
    pad_hex_new = body.newObject("PartDesign::Pad", "HexPad")
    pad_hex_new.Profile = sk_head_top
    pad_hex_new.Length = params.head_height
    pad_hex_new.makeSolid()
    
    # 2.2 Pocket for Shank (Through all from bottom of head)
    # The shank goes through the head and continues down.
    # We can model the shank as a cylinder starting from z=0 to z=shank_length and then tip.
    # Or, we can pocket the shank through the head and then add the shank cylinder.
    # Strategy: 
    # 1. Hex Pad (Head block)
    # 2. Pocket Shank (Through head, leaving the shank cylinder solid later?) 
    #    Actually, easier: Create the Hex Pad. Pocket the Shank (through head). 
    #    Then Pad the Shank cylinder from z=0 to z=shank_length.
    #    Then Pad the Tip cylinder from z=shank_length to z=shank_length+tip_length.
    
    pocket_shank = body.newObject("PartDesign::Pocket", "PocketShank")
    pocket_shank.Profile = sk_shank
    pocket_shank.Length = params.head_height # Through the head
    pocket_shank.makeSolid()
    
    # 2.3 Pad Shank
    pad_shank = body.newObject("PartDesign::Pad", "PadShank")
    pad_shank.Profile = sk_shank
    pad_shank.Placement = App.Placement(App.Vector(0, 0, 0))
    # The profile is at z=0. We want to go from z=0 to z=shank_length.
    pad_shank.Length = params.shank_length
    pad_shank.makeSolid()
    
    # 2.4 Pad Tip
    pad_tip = body.newObject("PartDesign::Pad", "PadTip")
    pad_tip.Profile = sk_tip
    pad_tip.Placement = App.Placement(App.Vector(0, 0, params.shank_length))
    pad_tip.Length = params.tip_length
    pad_tip.makeSolid()
    
    # 2.5 Pocket for Head Recess (Annular)
    # This is the edit step. For the base, we don't do this.
    # But the prompt says "Base part... round cylindrical head... underside recess... are absent".
    # So we skip this in the base build.
    
    # 2.6 Chamfer for Head Underside
    # This is also the edit step.
    
    # --- END BASE BUILD ---
    
    # --- EDIT STEP ---
    # We need to add the Recess and the Chamfer.
    # Since we are writing a script that produces both files, we will manipulate the parameters
    # and the feature tree to add the missing features.
    
    # However, the prompt asks for a script that produces the BASE and the EDIT.
    # The "Edit Instruction" says "Finish the oversized round head blank...".
    # This implies the script should construct the Base first, then construct the Edit version
    # OR modify the Base tree to add features.
    # Given the constraint "Write a FreeCAD Python script... that produces the edited part... This is a two-step task. First, build the base... Then apply the edit... Both .FCStd files are graded".
    # It implies one script run generates both files.
    # Since PartDesign features are destructive (usually) or hard to insert into an existing computed tree without recomputing everything, 
    # and we need the "Base" to NOT have these features, the best approach is:
    # 1. Build the tree with a flag or conditional logic to create/edit features.
    # 2. Save as Base.
    # 3. Reload or Rebuild with Edit flags? 
    #    FreeCAD API doesn't support "reload". We must rebuild the document object graph.
    #    But rebuilding is expensive.
    #    Alternative: The script creates the Base. Then it creates a NEW document or modifies the existing one by adding features?
    #    "Then apply the edit instruction to that base to produce the target part."
    #    This suggests modifying the existing document.
    #    In PartDesign, you can add new features to an existing Body.
    #    So:
    #    1. Build Base features (Pad Hex, Pocket Shank, Pad Shank, Pad Tip).
    #    2. Save as Base.
    #    3. Modify the document: Add the Recess Pocket and Chamfer features to the existing Body.
    #    4. Save as Edit.
    
    # Wait, if I save as Base, the document is saved. If I then modify it and save as Edit, 
    # I need to make sure I don't lose the Base file.
    # The script should:
    # 1. Create Doc.
    # 2. Build Base Features.
    # 3. Save as Base.
    # 4. Reload Base? No, that's messy.
    # 5. Better: The script creates the Base, saves it. Then it creates a NEW Document for the Edit, 
    #    copying the structure but adding the extra features?
    #    Or simply: The script builds the Base. Then it adds features to the SAME document, updates, and saves as Edit.
    #    This is valid.
    
    # Let's refine the plan:
    # 1. Create Doc "BoltHead".
    # 2. Create Body, Params, Sketches, Base Features (HexPad, PocketShank, PadShank, PadTip).
    # 3. Save as <stem>_base.FCStd.
    # 4. Add Recess Pocket and Chamfer to the same document.
    # 5. Update Params for Edit values (if different, though prompt implies specific values for edit).
    #    Actually, the Base description says "recess... absent". So in the Base build, we simply don't create them.
    #    In the Edit build, we create them.
    #    So:
    #    - Build Base features only. Save.
    #    - Add Edit features. Save.
    
    # Wait, the prompt says "The model must be built as a parametric feature tree...".
    # If I add features to an existing tree, it's still a tree.
    
    # Implementation details for Edit Features:
    # Recess:
    #   - Sketch at z = head_height - recess_depth (bottom of head).
    #   - Outer circle: Hex perimeter? No, "extends outward to the hexagonal perimeter".
    #     This means the pocket is defined by the Hex shape (from top) and the circle (from shank)?
    #     "circular inner boundary is tangent to all six head flats".
    #     Inner radius = R_in = hex_af / 2.
    #     Outer boundary: "extends outward to the hexagonal perimeter".
    #     This implies the pocket is the area between the Hexagon and the Inner Circle.
    #     But PartDesign::Pocket takes a single sketch.
    #     So we need a sketch with a Hexagon and a Circle, constrained to be coincident at the tangent points?
    #     Or just use the Hexagon and subtract the Circle? No, pocket subtracts the sketch area.
    #     We want to subtract the area of the Hexagon MINUS the area of the Circle? 
    #     No, we want to remove material where the Hexagon is, BUT KEEP the middle circle?
    #     "recessed region extends outward to the hexagonal perimeter".
    #     This sounds like the recess is the ring between the circle (tangent to flats) and the Hexagon.
    #     So the Sketch should have:
    #       1. Hexagon (from top sketch).
    #       2. Circle (radius = R_in).
    #     And we want to pocket the area defined by (Hexagon - Circle)? 
    #     Standard Pocket subtracts the sketch.
    #     If we draw the Hexagon and the Circle, and constrain them (tangent), the sketch is a ring?
    #     Sketcher allows regions. If we draw the outer Hex and inner Circle, and define them as separate entities, 
    #     the "Pocket" operation might subtract both if they are both selected as profile?
    #     No, usually you define a closed loop.
    #     To get an annular pocket, we can draw the Hexagon and the Circle, and use "Pocket" on the area between them?
    #     In FreeCAD PartDesign, if you have two closed loops in a sketch, you can select both. 
    #     The first selected is usually the outer boundary (subtracted), the second is inner (kept).
    #     So: Sketch has Hex and Circle. Pocket subtracts Hex, keeps Circle?
    #     Wait, "recessed region extends outward to the hexagonal perimeter".
    #     This means the material removed is the ring.
    #     So the solid remaining is the Circle.
    #     So the Pocket should subtract the Ring.
    #     Sketch: Hexagon (Outer), Circle (Inner).
    #     Pocket: Select both. The outer is the hole, the inner is the keep.
    #     Result: The material inside the Circle remains, the ring is removed. Correct.
    
    # Chamfer:
    #   - Base: The face of the HexPad at the bottom (z = head_height).
    #   - How to select the face?
    #     We can use `pad_hex_new`. It has a `Faces` property? No, it computes it.
    #     We need to reference the face of the Body.
    #     Usually, Chamfer can take a `Face` or an `Edge`.
    #     If we use the Edge of the HexPad perimeter at the bottom, it will chamfer that edge.
    #     "axisymmetric annular chamfer around the outer perimeter".
    #     This implies a conical chamfer on the vertical walls? 
    #     "Set its straight conical face by head_underside_chamfer_angle measured from the underside plane".
    #     This describes a chamfer on the top face (underside of the head), cutting into the Hex face?
    #     Or on the vertical side wall?
    #     "around the outer perimeter of the same head underside".
    #     This phrasing is slightly ambiguous.
    #     "underside of the finished head" -> The face at z=5.7.
    #     "outer perimeter of the same head underside" -> The edge where the underside meets the shank?
    #     No, the shank is below. The underside is the flat face.
    #     If we chamfer the perimeter of the underside face (the hex edge), we are chamfering the vertical transition?
    #     Or we are chamfering the corner of the underside face?
    #     "straight conical face... measured from the underside plane".
    #     If the chamfer is on the vertical edge (intersection of side and bottom), the angle is usually measured from the side or bottom.
    #     If it's a "conical face", it suggests a frustum.
    #     "axisymmetric annular chamfer around the outer perimeter".
    #     This sounds like a fil
