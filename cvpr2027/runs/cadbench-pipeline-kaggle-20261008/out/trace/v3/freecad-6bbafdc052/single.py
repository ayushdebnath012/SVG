import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Base Parameters
params_base = {
    "bracket_overall_width": 65.0,
    "bracket_overall_height": 65.0,
    "bracket_depth": 22.2,
    "flange_thickness": 22.2,
    "leg_width": 22.2,
    "inside_corner_fillet_radius": 10.0,
}

# Edit Parameters
params_edit = {
    "rectangular_opening_long_side": 18.7,
    "rectangular_opening_short_side": 15.2,
    "corner_scallop_diameter": 32.0,
}

def create_document(name):
    doc = App.newDocument(name)
    doc.Label = name
    return doc

def setup_planes(doc):
    # Create standard planes if they don't exist (FreeCAD usually has them, but explicit is safer for headless)
    # In FreeCAD 1.1, standard planes are usually available as XY_Plane, XZ_Plane, YZ_Plane
    # We will reference them by name.
    return doc

def build_base_part(doc):
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    for k, v in params_base.items():
        params.addProperty("App::PropertyLength", k, "Dimensions", k)
        params.setProperty(k, "DisplayLabel", k)
        params.setProperty(k, "Unit", "mm")
        params.setProperty(k, "ReadOnly", False)
        params.setProperty(k, "Expression", "")
        params.setProperty(k, "Value", v)

    # Sketch 1: L-Profile (XZ Plane)
    sketch_profile = body.newObject("Sketcher::SketchObject", "Profile_Sketch")
    sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_profile.Support = [doc.getObject("XZ_Plane")]
    sketch_profile.MapMode = "FlatFace"
    sketch_profile.Constrain = True
    
    # Geometry: L-Shape
    # Bottom horizontal line (Flange bottom)
    sketch_profile.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params_base["bracket_overall_width"], 0, 0)), False)
    # Vertical line (Leg right side)
    sketch_profile.addGeometry(Part.LineSegment(App.Vector(params_base["bracket_overall_width"], 0, 0), App.Vector(params_base["bracket_overall_width"], 0, params_base["bracket_overall_height"])), False)
    # Top horizontal line (Leg top)
    sketch_profile.addGeometry(Part.LineSegment(App.Vector(params_base["bracket_overall_width"], 0, params_base["bracket_overall_height"]), App.Vector(0, 0, params_base["bracket_overall_height"])), False)
    # Left vertical line (Flange left side)
    sketch_profile.addGeometry(Part.LineSegment(App.Vector(0, 0, params_base["bracket_overall_height"]), App.Vector(0, 0, 0)), False)
    
    # Constraints: Make it a closed loop
    # We need to constrain vertices to form a rectangle with a cutout or just a simple L?
    # The description says "L-shaped side profile".
    # Let's define points:
    # P0: (0,0,0)
    # P1: (W,0,0)
    # P2: (W,H,0)
    # P3: (0,H,0)
    # This forms a rectangle. We need to remove the top-left corner to make it L-shaped?
    # Wait, description: "horizontal flange spans... rises by flange_thickness... vertical leg... continues to bracket_overall_height".
    # Usually L-bracket: Bottom bar (width W, thickness T), Vertical bar (width W_leg, height H).
    # Let's re-read carefully: "horizontal flange spans bracket_overall_width and rises by flange_thickness from the bottom; the centered vertical leg has leg_width and continues to bracket_overall_height."
    # This implies the flange is the bottom part (Z=0 to Z=T). The leg is on top of it? Or is the leg the vertical part going up from the flange?
    # "centered vertical leg ... continues to bracket_overall_height".
    # Interpretation: 
    # 1. Base block: Width W, Height T (Flange thickness), Depth D.
    # 2. Leg: Width W_leg, Height (H - T), sitting on top of the base block, centered on the width W.
    # Total Height = H.
    # Let's construct the profile in XZ plane (Y is depth).
    # X range: 0 to W. Z range: 0 to H.
    # Flange: Z=0 to T. X=0 to W.
    # Leg: Z=T to H. X = (W - W_leg)/2 to (W + W_leg)/2.
    
    # Let's redefine the sketch geometry based on this interpretation.
    # Points:
    # A: (0, 0) -> Bottom Left
    # B: (W, 0) -> Bottom Right
    # C: (W, T) -> Flange Right Top
    # D: (W - W_leg/2, T) -> Leg Right Bottom
    # E: (W - W_leg/2, H) -> Leg Top Right
    # F: (0, H) -> Top Left (Wait, leg is centered, so left side of leg is at W - W_leg/2)
    # The profile is the boundary of the solid.
    # Path: A -> B -> C -> D -> E -> F -> A? 
    # No, F is (0, H). The leg is centered. So the top part of the profile goes from (0, H) to (W-leg/2, H)? 
    # No, the leg is the vertical part. The flange is the horizontal part.
    # If the leg is centered on the flange, the profile looks like an inverted 'L' or a 'Gamma' shape?
    # "L-shaped side profile". Usually means the corner is cut out.
    # Let's assume the solid occupies:
    # Region 1 (Flange): 0 <= x <= W, 0 <= z <= T
    # Region 2 (Leg): (W-W_leg)/2 <= x <= (W+W_leg)/2, T <= z <= H
    # Union of these.
    # Boundary points (Counter-Clockwise for CCW normal +Y):
    # 1. (0, 0)
    # 2. (W, 0)
    # 3. (W, T)
    # 4. (W - W_leg/2, T)  <-- Start of leg
    # 5. (W - W_leg/2, H)
    # 6. (0, H)             <-- Top Left corner of the bounding box? 
    #    Wait, if the leg is centered, the top left of the solid is at x = (W - W_leg)/2.
    #    So the profile goes from (W - W_leg/2, H) to (0, H)? No, that would be empty space above the flange on the left.
    #    The description says "L-shaped". 
    #    Let's assume the standard L-bracket: 
    #    Vertical leg on the left? Or right?
    #    "centered vertical leg".
    #    Okay, let's trace the perimeter of the union.
    #    Start (0,0) -> (W,0) -> (W, T) -> (W - W_leg/2, T) -> (W - W_leg/2, H) -> (0, H) -> (0,0).
    #    This creates a shape where the top-left corner is cut out.
    #    Is this "L-shaped"? Yes, if you rotate it.
    #    Let's check the fillet: "tangent inside fillet ... joins the flange upper face to the leg's negative-X face".
    #    Flange upper face: Z=T. Leg negative-X face: x = (W - W_leg)/2.
    #    Intersection is at x = (W - W_leg)/2, z = T.
    #    This matches the corner (4) in my list above.
    #    So the profile is:
    #    (0,0) -> (W,0) -> (W,T) -> (W-W_leg/2, T) -> (W-W_leg/2, H) -> (0, H) -> (0,0).
    
    # Let's create the geometry for this profile.
    W = params_base["bracket_overall_width"]
    H = params_base["bracket_overall_height"]
    T = params_base["flange_thickness"]
    W_leg = params_base["leg_width"]
    
    # Points
    p0 = App.Vector(0, 0, 0)
    p1 = App.Vector(W, 0, 0)
    p2 = App.Vector(W, T, 0)
    p3 = App.Vector(W - W_leg/2, T, 0)
    p4 = App.Vector(W - W_leg/2, H, 0)
    p5 = App.Vector(0, H, 0)
    
    sketch_profile.addGeometry(Part.LineSegment(p0, p1), False)
    sketch_profile.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_profile.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_profile.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_profile.addGeometry(Part.LineSegment(p4, p5), False)
    sketch_profile.addGeometry(Part.LineSegment(p5, p0), False)
    
    # Constraints
    # Horizontal lines
    sketch_profile.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) # p0-p1
    sketch_profile.addConstraint(Sketcher.Constraint("Horizontal", 2, 3)) # p2-p3
    sketch_profile.addConstraint(Sketcher.Constraint("Horizontal", 4, 5)) # p4-p5
    # Vertical lines
    sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 0, 5)) # p0-p5
    sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 1, 2)) # p1-p2
    sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 3, 4)) # p3-p4
    # Lengths
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 0, 1, W))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 4, 5, W)) # Top width
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 1, 2, T))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 3, 4, H-T))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 2, 3, W_leg/2))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 4, 3, W_leg/2))
    # Coincident/Closed
    sketch_profile.addConstraint(Sketcher.Constraint("Point", 0, "XY")) # Origin
    sketch_profile.addConstraint(Sketcher.Constraint("Point", 5, "XZ")) # Top plane? No, just close loop.
    # Actually, let's just constrain the loop to be closed and use the lengths defined.
    # The "Point" constraint at 0,0 is good.
    # We need to ensure the loop is closed.
    sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 0, 5, 5, 0)) # p0 and p5 on same vertical line? No.
    # Let's rely on the explicit lengths and horizontal/vertical constraints.
    # Add a constraint to close the loop explicitly if needed, but usually adding all segments closes it.
    # Let's add a constraint to make p0 and p5 share X=0.
    sketch_profile.addConstraint(Sketcher.Constraint("X", 0, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("X", 5, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Y", 0, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Y", 1, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 0, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 2, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 3, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 4, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 5, 0))
    
    # Fillet
    # "tangent inside fillet of inside_corner_fillet_radius joins the flange upper face to the leg's negative-X face"
    # This is the corner at p3 (W-W_leg/2, T).
    # We need to fillet the internal corner.
    # In the sketch, this is the corner between segment 2-3 and 3-4.
    # Sketcher fillet:
    sketch_profile.addConstraint(Sketcher.Constraint("Radius", 2, 3, params_base["inside_corner_fillet_radius"]))
    
    # Pad
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_profile
    pad.Length = params_base["bracket_depth"]
    pad.Type = "Solid"
    pad.Midplane = False
    pad.Reversed = False
    
    # Fillet the internal corner of the 3D body
    # The edge is the intersection of the flange top and leg side.
    # We need to find the edge index or use a named edge.
    # Since we are building programmatically, we can't easily name the edge before recompute.
    # However, we can use the "Edge" property of the Pad if we know the index, or use a loop.
    # Better approach: Add the fillet feature after the pad.
    # We need to identify the edge.
    # Let's assume the edge is the one created by the fillet in the sketch? No, the sketch fillet creates a rounded edge in the profile.
    # The 3D fillet is on the sharp edge where the two faces meet.
    # Wait, if the sketch has a fillet, the Pad creates a rounded edge automatically?
    # Yes, if the sketch has a fillet, the resulting solid has a rounded edge corresponding to that sketch fillet.
    # So we don't need a separate Fillet feature for the inside corner if the sketch has it.
    # The description says "tangent inside fillet ... joins ...". This implies a rounded corner.
    # So the sketch fillet constraint is sufficient.
    
    doc.recompute()
    return doc

def apply_edits(doc):
    # Get parameters
    params = doc.getObject("Body").getObject("Parameters")
    
    # Edit Parameters
    edit_params = {
        "rectangular_opening_long_side": params_edit["rectangular_opening_long_side"],
        "rectangular_opening_short_side": params_edit["rectangular_opening_short_side"],
        "corner_scallop_diameter": params_edit["corner_scallop_diameter"],
    }
    
    for k, v in edit_params.items():
        if hasattr(params, k):
            params.setProperty(k, "Value", v)
        else:
            # Add if missing
            params.addProperty("App::PropertyLength", k, "Dimensions", k)
            params.setProperty(k, "DisplayLabel", k)
            params.setProperty(k, "Unit", "mm")
            params.setProperty(k, "Value", v)

    # 1. Rectangular Opening in Flange (Negative X end, through Z)
    # "Cut a rectangular opening through the horizontal flange from its negative-X end toward positive X."
    # "Give its cross-section rectangular_opening_long_side along global Y and rectangular_opening_short_side along global Z"
    # "make it flush with the global Y = bracket_depth back face"
    # "center it within flange_thickness in Z"
    
    # Flange is at Z=0 to Z=T.
    # Opening is along X (from -X end? "from its negative-X end toward positive X").
    # This implies the opening starts at X=0 and goes to X=LongSide?
    # "from its negative-X end" -> The flange extends from X=0 to X=W. Negative-X end is X=0.
    # So the opening is at X=0, extending to X=LongSide.
    # Cross section: LongSide along Y, ShortSide along Z.
    # Flush with Y=Depth back face -> Y = Depth - ShortSide/2? Or Y=Depth?
    # "flush with the global Y = bracket_depth back face". Usually means the face of the cut is at Y=Depth.
    # So the cut is in the plane Y=Depth? No, it's a hole.
    # "Cut ... through the horizontal flange ... flush with the global Y = bracket_depth back face".
    # This likely means the cut is located at the back of the flange.
    # Center in Z: Z = T/2.
    # So the hole is: X in [0, LongSide], Y in [Depth - ShortSide/2, Depth + ShortSide/2]?
    # Wait, "flush with ... back face". If the back face is at Y=Depth, and the hole is "flush", maybe the hole starts at Y=Depth and goes in?
    # But it's a hole "through the horizontal
