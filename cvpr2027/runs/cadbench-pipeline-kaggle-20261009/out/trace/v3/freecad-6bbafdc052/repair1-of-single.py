import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

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
    # Ensure standard planes exist. In FreeCAD 1.1, they are usually present.
    # We reference them by name.
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
    # The profile is in the XZ plane. Y is the depth direction.
    # Coordinate system: X (width), Z (height), Y (depth).
    # Profile points (X, Z):
    # 0: (0, 0)
    # 1: (W, 0)
    # 2: (W, T)
    # 3: (W - W_leg/2, T)  <-- Inner corner
    # 4: (W - W_leg/2, H)
    # 5: (0, H)
    
    sketch_profile = body.newObject("Sketcher::SketchObject", "Profile_Sketch")
    sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_profile.Support = [doc.getObject("XZ_Plane")]
    sketch_profile.MapMode = "FlatFace"
    sketch_profile.Constrain = True
    
    W = params_base["bracket_overall_width"]
    H = params_base["bracket_overall_height"]
    T = params_base["flange_thickness"]
    W_leg = params_base["leg_width"]
    
    # Define Points
    p0 = App.Vector(0, 0, 0)
    p1 = App.Vector(W, 0, 0)
    p2 = App.Vector(W, T, 0)
    p3 = App.Vector(W - W_leg/2, T, 0)
    p4 = App.Vector(W - W_leg/2, H, 0)
    p5 = App.Vector(0, H, 0)
    
    # Add Geometry
    sketch_profile.addGeometry(Part.LineSegment(p0, p1), False)
    sketch_profile.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_profile.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_profile.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_profile.addGeometry(Part.LineSegment(p4, p5), False)
    sketch_profile.addGeometry(Part.LineSegment(p5, p0), False)
    
    # Constraints
    # Horizontal lines
    sketch_profile.addConstraint(Sketcher.Constraint("Horizontal", 0, 1)) 
    sketch_profile.addConstraint(Sketcher.Constraint("Horizontal", 2, 3)) 
    sketch_profile.addConstraint(Sketcher.Constraint("Horizontal", 4, 5)) 
    # Vertical lines
    sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 0, 5)) 
    sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 1, 2)) 
    sketch_profile.addConstraint(Sketcher.Constraint("Vertical", 3, 4)) 
    # Lengths
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 0, 1, W))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 4, 5, W)) 
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 1, 2, T))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 3, 4, H-T))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 2, 3, W_leg/2))
    sketch_profile.addConstraint(Sketcher.Constraint("Length", 4, 3, W_leg/2))
    # Origin and alignment
    sketch_profile.addConstraint(Sketcher.Constraint("Point", 0, "XY")) 
    sketch_profile.addConstraint(Sketcher.Constraint("X", 0, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Y", 0, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 0, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 1, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 2, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 3, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 4, 0))
    sketch_profile.addConstraint(Sketcher.Constraint("Z", 5, 0))
    
    # Fillet at inner corner (between segment 2-3 and 3-4)
    sketch_profile.addConstraint(Sketcher.Constraint("Radius", 2, 3, params_base["inside_corner_fillet_radius"]))
    
    # Pad
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_profile
    pad.Length = params_base["bracket_depth"]
    pad.Type = "Solid"
    pad.Midplane = False
    pad.Reversed = False
    
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
            params.addProperty("App::PropertyLength", k, "Dimensions", k)
            params.setProperty(k, "DisplayLabel", k)
            params.setProperty(k, "Unit", "mm")
            params.setProperty(k, "Value", v)

    # 1. Rectangular Opening in Flange
    # "Cut a rectangular opening through the horizontal flange from its negative-X end toward positive X."
    # "Give its cross-section rectangular_opening_long_side along global Y and rectangular_opening_short_side along global Z"
    # "make it flush with the global Y = bracket_depth back face"
    # "center it within flange_thickness in Z"
    
    # Flange is at Z=0 to Z=T.
    # Opening is along X (from X=0 to X=LongSide).
    # Cross section: LongSide along Y, ShortSide along Z.
    # Flush with Y=Depth back face -> The cut is at the back of the flange.
    # Center in Z: Z = T/2.
    # The cut is a rectangular hole.
    
    # Sketch for the flange cut (XZ plane, but extruded along Y? No, the cut is through the flange thickness? 
    # Wait, "through the horizontal flange". The flange is the bottom part.
    # The cut goes through the flange. The flange has depth D.
    # The cut is "flush with the global Y = bracket_depth back face".
    # This implies the cut is located at Y = Depth.
    # But the flange is the bottom part (Z=0 to T).
    # If the cut is at Y=Depth, it is at the back of the flange.
    # The cut goes "from its negative-X end toward positive X".
    # So the cut is in the plane Y=Depth? No, it's a hole.
    # It's a rectangular hole.
    # Dimensions:
    # X: 0 to LongSide
    # Y: Depth - ShortSide/2 to Depth + ShortSide/2? 
    #    "flush with ... back face". If the back face is at Y=Depth, and the hole is flush, 
    #    maybe the hole is centered on the back face?
    #    "center it within flange_thickness in Z".
    #    So Z is centered at T/2.
    #    Y is centered at Depth? Or the hole starts at Depth?
    #    "flush with ... back face" usually means the face of the hole is coplanar with the back face.
    #    So the hole is in the plane Y=Depth? No, that would be a slot on the surface.
    #    "Cut ... through the horizontal flange".
    #    This implies a hole going through the material.
    #    If it's flush with the back face, the hole is located at the back.
    #    Let's assume the hole is centered at Y=Depth, Z=T/2.
    #    X range: 0 to LongSide.
    #    Y range: Depth - ShortSide/2 to Depth + ShortSide/2.
    #    Z range: T/2 - ShortSide/2 to T/2 + ShortSide/2.
    #    Wait, "cross-section ... along global Y and ... along global Z".
    #    This means the hole's cross-section (in the plane perpendicular to the cut direction) is defined by these dimensions.
    #    The cut direction is X (from negative-X end).
    #    So the hole is a rectangular prism removed from the solid.
    #    Extent: X in [0, LongSide], Y in [Depth - ShortSide/2, Depth + ShortSide/2], Z in [T/2 - ShortSide/2, T/2 + ShortSide/2].
    
    # Sketch 2: Flange Cut (XZ Plane)
    # We need to define the profile of the cut in the XZ plane, then extrude along Y?
    # No, the cut is a rectangular hole.
    # We can create a sketch in the XZ plane at Y=Depth?
    # Or create a sketch in the XY plane at Z=T/2?
    # Let's create a sketch in the XZ plane at Y=Depth.
    # The profile will be a rectangle: X from 0 to LongSide, Z from T/2 - ShortSide/2 to T/2 + ShortSide/2.
    # Then we extrude along Y (Pocket).
    
    sketch_flange_cut = body.newObject("Sketcher::SketchObject", "Flange_Cut_Sketch")
    sketch_flange_cut.Placement = App.Placement(App.Vector(0, params_base["bracket_depth"], 0))
    sketch_flange_cut.Support = [doc.getObject("XZ_Plane")]
    sketch_flange_cut.MapMode = "FlatFace"
    sketch_flange_cut.Constrain = True
    
    L = params_edit["rectangular_opening_long_side"]
    S = params_edit["rectangular_opening_short_side"]
    T = params_base["flange_thickness"]
    
    # Points for the rectangle
    q0 = App.Vector(0, 0, 0) # X=0, Z=T/2 - S/2
    q1 = App.Vector(L, 0, 0) # X=L, Z=T/2 - S/2
    q2 = App.Vector(L, 0, S) # X=L, Z=T/2 + S/2
    q3 = App.Vector(0, 0, S) # X=0, Z=T/2 + S/2
    
    sketch_flange_cut.addGeometry(Part.LineSegment(q0, q1), False)
    sketch_flange_cut.addGeometry(Part.LineSegment(q1, q2), False)
    sketch_flange_cut.addGeometry(Part.LineSegment(q2, q3), False)
    sketch_flange_cut.addGeometry(Part.LineSegment(q3, q0), False)
    
    # Constraints
    sketch_flange_cut.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sketch_flange_cut.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
    sketch_flange_cut.addConstraint(Sketcher.Constraint("Vertical", 0, 3))
    sketch_flange_cut.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
    sketch_flange_cut.addConstraint(Sketcher.Constraint("Length", 0, 1, L))
    sketch_flange_cut.addConstraint(Sketcher.Constraint("Length", 0, 3, S))
    sketch_flange_cut.addConstraint(Sketcher.Constraint("X", 0, 0))
    sketch_flange_cut.addConstraint(Sketcher.Constraint("Z", 0, 0))
    
    pocket_flange = body.newObject("PartDesign::Pocket", "Pocket_Flange")
    pocket_flange.Profile = sketch_flange_cut
    pocket_flange.Type = "Blind"
    pocket_flange.Length = params_base["bracket_depth"] # Cut through the depth
    pocket_flange.Midplane = False
    pocket_flange.Reversed = False
    
    # 2. Rectangular Opening in Leg
    # "Cut the second rectangular opening downward through the vertical leg from the maximum-Z top face."
    # "Use rectangular_opening_long_side along global X and rectangular_opening_short_side along global Y"
    # "make it flush with the leg's positive-X face"
    # "center it within bracket_depth in Y"
    
    # Leg is at Z=T to Z=H.
    # Opening is downward (from Z=H to Z=H - LongSide).
    # Cross section: LongSide along X, ShortSide along Y.
    # Flush with leg's positive-X face -> X = W.
    # Center in Y -> Y = Depth/2.
    
    # Sketch 3: Leg Cut (XY Plane)
    # We need to define the profile in the XY plane at Z=H.
    # The profile will be a rectangle: X from W - LongSide to W, Y from Depth/2 - ShortSide/2 to Depth/2 + ShortSide/2.
    # Then we extrude along Z (Pocket).
    
    sketch_leg_cut = body.newObject("Sketcher::SketchObject", "Leg_Cut_Sketch")
    sketch_leg_cut.Placement = App.Placement(App.Vector(0, 0, params_base["bracket_overall_height"]))
    sketch_leg_cut.Support = [doc.getObject("XY_Plane")]
    sketch_leg_cut.MapMode = "FlatFace"
    sketch_leg_cut.Constrain = True
    
    L_leg = params_edit["rectangular_opening_long_side"]
    S_leg = params_edit["rectangular_opening_short_side"]
    W = params_base["bracket_overall_width"]
    
    # Points for the rectangle
    r0 = App.Vector(0, 0, 0) # X=W - L_leg, Y=Depth/2 - S_leg/2
    r1 = App.Vector(0, 0, S_leg) # X=W - L_leg, Y=Depth/2 + S_leg/2
    r2 = App.Vector(L_leg, 0, S_leg) # X=W, Y=Depth/2 + S_leg/2
    r3 = App.Vector(L_leg, 0, 0) # X=W, Y=Depth/2 - S_leg/2
    
    sketch_leg_cut.addGeometry(Part.LineSegment(r0, r1), False)
    sketch_leg_cut.addGeometry(Part.LineSegment(r1, r2), False)
    sketch_leg_cut.addGeometry(Part.LineSegment(r2, r3), False)
    sketch_leg_cut.addGeometry(Part.LineSegment(r3, r0), False)
    
    # Constraints
    sketch_leg_cut.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sketch_leg_cut.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
    sketch_leg_cut.addConstraint(Sketcher.Constraint("Vertical", 0, 3))
    sketch_leg_cut.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
    sketch_leg_cut.addConstraint(Sketcher.Constraint("Length", 0, 3, S_leg))
    sketch_leg_cut.addConstraint(Sketcher.Constraint("Length", 0, 1, L_leg))
    sketch_leg_cut.addConstraint(Sketcher.Constraint("X", 3, 0)) # Flush with positive X face
    sketch_leg_cut.addConstraint(Sketcher.Constraint("Y", 0, 0)) # Center in Y? No, Y=0 is center.
    # Wait, the placement is at Z=H. The XY plane is at Z=H.
    # The center of the sketch should be at Y=Depth/2.
    # The sketch is defined relative to the XY plane origin (0,0,0).
    # So we need to shift the sketch or constrain the center.
    # Let's shift the sketch placement to (0, Depth/2, H).
    sketch_leg_cut.Placement = App.Placement(App.Vector(0, params_base["bracket_depth"]/2, params_base["bracket_overall_height"]))
    
    # Re-add geometry with new placement
    # Actually, let's just redefine the points relative to the new origin.
    # New origin: (0, Depth/2, H).
    # Points:
    # r0: (-L_leg/2, -S_leg/2) relative to center? No.
    # X range: W - L_leg to W.
    # Y range: Depth/2 - S_leg/2 to Depth/2 + S_leg/2.
    # Relative to (0, Depth/2, H):
    # X: -L_leg to 0.
    # Y: -S_leg/2 to S_leg/2.
    
    sketch_leg_cut2 = body.newObject("Sketcher::SketchObject", "Leg_Cut_Sketch2")
    sketch_leg_cut2.Placement = App.Placement(App.Vector(0, params_base["bracket_depth"]/2, params_base["bracket_overall_height"]))
    sketch_leg_cut2.Support = [doc.getObject("XY_Plane")]
    sketch_leg_cut2.MapMode = "FlatFace"
    sketch_leg_cut2.Constrain = True
    
    # Points relative to new origin
    r0 = App.Vector(-L_leg, 0, 0)
    r1 = App.Vector(-L_leg, S_leg, 0)
    r2 = App.Vector(0, S_leg, 0)
    r3 = App.Vector(0, 0, 0)
    
    sketch_leg_cut2.addGeometry(Part.LineSegment(r0, r1), False)
    sketch_leg_cut2.addGeometry(Part.LineSegment(r1, r2), False)
    sketch_leg_cut2.addGeometry(Part.LineSegment(r2, r3), False)
    sketch_leg_cut2.addGeometry(Part.LineSegment(r3, r0), False)
    
    # Constraints
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("Vertical", 0, 3))
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("Vertical", 1, 2))
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("Length", 0, 3, S_leg))
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("Length", 0, 1, L_leg))
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("X", 3, 0)) # Flush with positive X face (X=0 in local coords)
    sketch_leg_cut2.addConstraint(Sketcher.Constraint("Y", 0, 0)) # Center in Y
    
    pocket_leg = body.newObject("PartDesign::Pocket", "Pocket_Leg")
    pocket_leg.Profile = sketch_leg_cut2
    pocket_leg.Type = "Blind"
    pocket_leg.Length = params_base["bracket_overall_height"] - params_base["flange_thickness"] # Cut through the leg
    pocket_leg.Midplane = False
    pocket_leg.Reversed = False
    
    # 3. Corner Scallops
    # "Add two circular cuts of corner_scallop_diameter."
    # "Center the flange cut at the intersection of the body's negative-X boundary and global Y = bracket_depth"
    # "cut parallel to global Z"
    # "Center the upper-leg cut at the intersection of the leg's positive-X boundary and the bracket's maximum-Z boundary"
    # "cut parallel to global Y"
    # "Only the quadrant of each circle that overlaps the solid should be removed"
    
    # Flange Scallop
    # Location: X=0, Y=Depth.
    # Cut parallel to Z.
    # Diameter: D.
    # We need to remove the quadrant that overlaps the solid.
    # The solid is at X>0, Y<Depth (since Y goes from 0 to Depth).
    # Wait, the flange is at Y from 0 to Depth.
    # The cut is at Y=Depth.
    # The solid is at X>0.
    # So the quadrant to remove is X>0, Y<Depth.
    # This is the quadrant in the 4th quadrant relative to the center (if X is right, Y is down).
    # We can create a sketch in the XY plane at Z=T/2 (center of flange thickness).
    # The circle is centered at (0, Depth).
    # We need to cut only the part where X>0 and Y<Depth.
    # We can use a sketch with a circle and a line, then use a "Cut" feature with a specific profile?
    # Or use a "Pocket" with a specific profile.
    # Let's create a sketch in the XY plane at Z=T/2.
    # Circle: Center (0, Depth), Radius D/2.
    # Line: X=0 (Y axis).
    # We need to cut the quadrant X>0, Y<Depth.
    # We can create a closed profile consisting of the arc and the two radii.
    
    sketch_flange_scallop = body.newObject("Sketcher::SketchObject", "Flange_Scallop_Sketch")
    sketch_flange_scallop.Placement = App.Placement(App.Vector(0, params_base["bracket_depth"], params_base["flange_thickness"]/2))
    sketch_flange_scallop.Support = [doc.getObject("XY_Plane")]
    sketch_flange_scallop.MapMode = "FlatFace"
    sketch_flange_scallop.Constrain = True
    
    D = params_edit["corner_scallop_diameter"]
    R = D/2
    
    # Circle
    c = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), R)
    sketch_flange_scallop.addGeometry(c, False)
    
    # Line X=0 (from Y=-R to Y=R)
    l1 = Part.LineSegment(App.Vector(0, -R, 0), App.Vector(0, R, 0))
    sketch_flange_scallop.addGeometry(l1, False)
    
    # We need to cut the quadrant X>0, Y<Depth.
    # In the local coordinates of the sketch (centered at 0,0), this is X>0, Y<0.
    # This is the 4th quadrant.
    # We can create a closed profile by adding the arc and the two radii.
    # Arc from (0, -R) to (R, 0) in the 4th quadrant.
    # Line from (R, 0) to (0, 0).
    # Line from (0, 0) to (0, -R).
    
    # Arc
    # Start angle: -90 deg (or 270). End angle: 0 deg.
    # FreeCAD Part.Circle doesn't support arcs directly in addGeometry.
    # We need to use Part.Wire or manually construct the geometry.
    # Let's use Part.Wire.
    
    # Points for the wire
    p_a = App.Vector(0, -R, 0)
    p_b = App.Vector(R, 0, 0)
    p_c = App.Vector(0, 0, 0)
    
    # Arc
    arc = Part.Arc(p_a, p_b, App.Vector(0, 0, 1)) # Center (0,0,0), Radius R, in XY plane
    # Wait, Part.Arc needs center, start, end.
    # Center: (0,0,0). Start: (0,-R,0). End: (R,0,0).
    # This creates an arc in the XY plane.
    
    # Lines
    l_arc = Part.LineSegment(p_b, p_c)
    l_rad = Part.LineSegment(p_c, p_a)
    
    # Wire
    wire = Part.Wire([arc, l_arc, l_rad])
    # Close the wire? The arc connects p_a to p_b. l_arc connects p_b to p_c. l_rad connects p_c to p_a.
    # Yes, it's closed.
    
    # We need to add this wire to the sketch.
    # Sketcher::SketchObject.addGeometry expects Part::Edge or Part::LineSegment.
    # We can add the wire as a single geometry? No, it expects edges.
    # We can add the arc, the two lines.
    sketch_flange_scallop.addGeometry(arc, False)
    sketch_flange_scallop.addGeometry(l_arc, False)
    sketch_flange_scallop.addGeometry(l_rad, False)
    
    # Constraints
    # Coincident with center
    sketch_flange_scallop.addConstraint(Sketcher.Constraint("Point", 0, "XY")) # Center of circle
    # Radius
    sketch_flange_scallop.addConstraint(Sketcher.Constraint("Radius", 0, R))
    # Coincident with axes
    sketch_flange_scallop.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0)) # Circle center on X axis? No.
    # We need to constrain the circle center to (0,0).
    # The placement is at (0, Depth, T/2). The sketch is in XY plane.
    # The circle center is at (0,0) in local coords.
    # We need to constrain the circle to be centered at the origin of the sketch.
    # Sketcher constraint "Point" on the circle center to the origin of the sketch?
    # The circle is defined by a center point.
    # Let's use "Point" constraint on the circle center to the origin.
    # But the circle is added as a geometry.
    # We can use "Point" constraint on the circle center to the origin.
    # The circle is index 0.
    sketch_flange_scallop.addConstraint(Sketcher.Constraint("Point", 0, "XY"))
    
    # Pocket
    pocket_flange_scallop = body.newObject("PartDesign::Pocket", "Pocket_Flange_Scallop")
    pocket_flange_scallop.Profile = sketch_flange_scallop
    pocket_flange_scallop.Type = "Blind"
    pocket_flange_scallop.Length = params_base["bracket_depth"] # Cut through the depth
    pocket_flange_scallop.Midplane = False
    pocket_flange_scallop.Reversed = False
    
    # Leg Scallop
    # Location: X=W, Z=H.
    # Cut parallel to Y.
    # Diameter: D.
    # Solid is at Y<Depth.
    # Quadrant to remove: Y<Depth, Z>H? No, Z=H is the top.
    # The solid is at Z<H.
    # So the quadrant to remove is Y<Depth, Z<H.
    # This is the quadrant in the 4th quadrant relative to the center (if Y is right, Z is down).
    # We create a sketch in the XZ plane at Y=Depth/2.
    # Circle centered at (W, H).
    # Cut the quadrant X<W, Z<H.
    
    sketch_leg_scallop = body.newObject("Sketcher::SketchObject", "Leg_Scallop_Sketch")
    sketch_leg_scallop.Placement = App.Placement(App.Vector(params_base["bracket_overall_width"], params_base["bracket_depth"]/2, params_base["bracket_overall_height"]))
    sketch_leg_scallop.Support = [doc.getObject("XZ_Plane")]
    sketch_leg_scallop.MapMode = "FlatFace"
    sketch_leg_scallop.Constrain = True
    
    # Circle
    c_leg = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), R)
    sketch_leg_scallop.addGeometry(c_leg, False)
    
    # Points for the wire
    p_a_leg = App.Vector(0, -R, 0) # X=0, Z=-R
    p_b_leg = App.Vector(R, 0, 0) # X=R, Z=0
    p_c_leg = App.Vector(0, 0, 0) # X=0, Z=0
    
    # Arc
    arc_leg = Part.Arc(p_a_leg, p_b_leg, App.Vector(0, 0, 1))
    
    # Lines
    l_arc_leg = Part.LineSegment(p_b_leg, p_c_leg)
    l_rad_leg = Part.LineSegment(p_c_leg, p_a_leg)
    
    sketch_leg_scallop.addGeometry(arc_leg, False)
    sketch_leg_scallop.addGeometry(l_arc_leg, False)
    sketch_leg_scallop.addGeometry(l_rad_leg, False)
    
    # Constraints
    sketch_leg_scallop.addConstraint(Sketcher.Constraint("Point", 0, "XY"))
    sketch_leg_scallop.addConstraint(Sketcher.Constraint("Radius", 0, R))
    
    # Pocket
    pocket_leg_scallop = body.newObject("PartDesign::Pocket", "Pocket_Leg_Scallop")
    pocket_leg_scallop.Profile = sketch_leg_scallop
    pocket_leg_scallop.Type = "Blind"
    pocket_leg_scallop.Length = params_base["bracket_overall_height"] - params_base["flange_thickness"] # Cut through the leg
    pocket_leg_scallop.Midplane = False
    pocket_leg_scallop.Reversed = False
    
    doc.recompute()
    return doc

# --- Main Execution ---
script_path = Path(__file__).resolve()
script_stem = script_path.stem

# Step 1: Build Base Part
doc_base = create_document("Base")
setup_planes(doc_base)
build_base_part(doc_base)
doc_base.saveAs(str(script_path.parent / f"{script_stem}_base.FCStd"))

# Step 2: Apply Edits to create Target Part
doc_edit = create_document("Edit")
setup_planes(doc_edit)
# Copy the structure from base? 
# No, we need to rebuild the base first in the edit doc, then apply edits.
# Or we can just call build_base_part and then apply_edits.
# But build_base_part creates a new document.
# Let's rebuild the base in the edit doc.
build_base_part(doc_edit)
apply_edits(doc_edit)
doc_edit.saveAs(str(script_path.parent / f"{script_stem}_edit.FCStd"))

# Cleanup
App.closeDocument(doc_base.Name)
App.closeDocument(doc_edit.Name)
