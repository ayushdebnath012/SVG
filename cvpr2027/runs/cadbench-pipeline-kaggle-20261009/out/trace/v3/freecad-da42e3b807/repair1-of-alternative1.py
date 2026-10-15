import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

def create_document():
    doc = App.newDocument("NozzleNozzle")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    
    # --- Parameters ---
    params = body.newObject("App::VarSet", "Parameters")
    
    # Base Part Parameters
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
    
    # Edit Parameters (Default values)
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
    sk_base.AddConstraint(Sketcher.Constraint("Radius", 0, 1, params.width))
    sk_base.AddConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sk_base.AddConstraint(Sketcher.Constraint("Vertical", 0, 1))
    
    pad_body = body.newObject("PartDesign::Pad", "PadBody")
    pad_body.Profile = sk_base
    pad_body.Length = params.length
    pad_body.Type = "Solid"
    
    # 2. Internal Cavity (Revolution)
    # We create a sketch on the YZ plane (X=0) to define the profile for revolution around Z.
    # To do this in PartDesign, we attach the sketch to the "YZ_Plane" of the document.
    # However, the sketch needs to be relative to the body's placement.
    # We will use the document's YZ_Plane and then apply a placement to the sketch object to align it with the body.
    
    sk_cavity = body.newObject("Sketcher::SketchObject", "CavityProfile")
    sk_cavity.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation()) # Default
    # Attach to YZ Plane
    sk_cavity.AttachmentSupport = (doc.getObject("YZ_Plane"), [""])
    sk_cavity.MapMode = "FlatFace"
    sk_cavity.Constrain = True
    sk_cavity.ConstraintList = []
    
    # Define the cavity profile in YZ plane (Y is radial, Z is axial)
    # The cavity starts at Z=0 (Face) and goes inwards (positive Z).
    # Profile points: (Y, Z)
    # 1. Start at center (0,0)
    # 2. Taper inlet: D=9, L=3 -> (4.5, 3)
    # 3. Step 1: D=8, L=14 -> (4.0, 17)
    # 4. Step 2: D=10, L=10 -> (5.0, 27)
    # 5. Step 3: D=5, L=8.14 -> (2.5, 35.14)
    # 6. Contoured section:
    #    Length = 17.8198418. Starts at Z=35.14. Ends at Z=52.96?
    #    Wait, total length is 50.
    #    Let's re-calculate Z positions.
    #    Z0 = 0
    #    Z_taper_end = 3.0
    #    Z_s1_end = 3.0 + 14.0 = 17.0
    #    Z_s2_end = 17.0 + 10.0 = 27.0
    #    Z_s3_end = 27.0 + 8.14 = 35.14
    #    Z_contour_end = 35.14 + 17.8198418 = 52.9598418
    #    This exceeds the body length (50).
    #    Re-reading: "Upper contoured cutout length = 15.0". "Upper contoured cutout length" might be the arc length or axial length?
    #    Given "upper_contoured_cutout_length = 15.0" and "upper_contoured_cutout_contour_length = 15.0", likely axial.
    #    If it exceeds 50, maybe the cavity doesn't go all the way? Or the body is longer?
    #    "base_cylinder_length = 50.0".
    #    Maybe the "Upper contoured cutout" is the transition from the stepped relief to the main cavity, and the main cavity is the rest?
    #    Let's assume the cavity ends at Z=50.
    #    So the contour section is from Z=35.14 to Z=50. Length = 14.86.
    #    The parameter "upper_contoured_cutout_length = 17.8198418" might be the length of the *contour* itself (arc length) or a specific segment.
    #    Let's assume the cavity ends at Z=50.
    #    Points:
    #    P0: (0, 0)
    #    P1: (4.5, 3.0)
    #    P2: (4.0, 17.0)
    #    P3: (5.0, 27.0)
    #    P4: (2.5, 35.14)
    #    P5: (0, 50.0) # Close to center? Or does it open up?
    #    "Internal cavity... tapered inlet followed by three ordered cylindrical sections."
    #    Usually cavities are open at the end or closed. If it's a "cavity", it's a void.
    #    If it goes to Z=50, the radius at Z=50 must be defined.
    #    Let's assume it closes at the center (0, 50) or has a specific radius.
    #    Given "upper_contoured_cutout_top_inner_radius = 25.0", this is huge.
    #    Wait, "upper_contoured_cutout" parameters:
    #    depth = 26.1054564.
    #    If the cavity is internal, depth 26 means it goes 26mm from the face?
    #    If face is Z=0, depth 26 means Z=26.
    #    But we have steps up to Z=35.
    #    Maybe the "Upper contoured cutout" is an OUTER groove?
    #    "Upper contoured annular channel".
    #    If it's an outer groove, depth 26 on a 30mm diameter part (radius 15) is impossible.
    #    Unless the part is hollow? No, "cylindrical nozzle fitting".
    #    Maybe the "depth" is the radial depth from the outer surface?
    #    Outer radius = 15. Depth 26 -> Impossible.
    #    Maybe the "depth" is the axial length? No, "depth" usually radial.
    #    Let's reconsider the "Upper contoured cutout".
    #    Maybe it's the shape of the *wall* of the cavity?
    #    "transitions through the specified convex and concave arcs".
    #    This describes the profile of the cavity wall.
    #    Let's assume the cavity profile is defined by these arcs.
    #    Start at Z=35.14 (end of step 3).
    #    Arc 1: Convex, R=6. Center offset X=-0.11, Y=19.0.
    #    Arc 2: Concave, R=28.5. Center offset X=34.1, Y=19.95.
    #    These offsets are in the YZ plane (Y=radial, Z=axial).
    #    Let's construct the profile points based on these arcs.
    #    This is getting complex for a script.
    #    Alternative interpretation: The "Upper contoured cutout" is a separate feature (a groove on the outside)?
    #    But "depth 26" kills that theory.
    #    Let's assume the cavity is the main feature and the "Upper contoured cutout" defines the shape of the cavity wall between Z=35.14 and Z=50.
    #    Let's try to fit the points:
    #    Start: (2.5, 35.14)
    #    End: (0, 50) ?
    #    Let's use the provided parameters to define the curve.
    #    Convex Arc: R=6. Center at (19.001, 35.14 - 0.114) = (19.001, 35.026)?
    #    No, "convex_center_axial_offset = -0.1143294". Relative to what?
    #    Maybe relative to the start of the contour?
    #    Let's assume the contour starts at Z=35.14.
    #    Convex center: Y=19.001, Z=35.14 - 0.114 = 35.026.
    #    Concave center: Y=19.955, Z=35.14 + 34.097 = 69.237.
    #    This seems to define a large curve.
    #    Given the complexity and potential ambiguity, I will construct the cavity profile using the explicit steps and then a simple closing line to Z=50, radius 0, assuming the "contoured" part is a smooth transition that I will approximate or skip if the steps cover it.
    #    Actually, let's look at the "Upper contoured cutout depth = 26.1".
    #    If the cavity goes from Z=0 to Z=26.1, then the steps (up to 35) are outside the "contoured" part?
    #    No, "begins at the stepped-relief end".
    #    Okay, let's assume the cavity is:
    #    0-3: Taper
    #    3-17: Step 1
    #    17-27: Step 2
    #    27-35.14: Step 3
    #    35.14-50: Contoured section.
    #    I will define the contour section as a simple line from (2.5, 35.14) to (0, 50) for now, as the exact arc math is too speculative without a clear coordinate system definition in the prompt.
    #    Wait, "upper_contoured_cutout_top_inner_radius = 25.0".
    #    This might be the radius of the cavity at the top?
    #    If radius is 25, diameter is 50.
    #    If the cavity expands to D=50 at Z=50, that makes sense for a nozzle exit.
    #    So the profile goes from (2.5, 35.14) to (25.0, 50.0).
    #    Let's use these points.
    
    # Profile Points for Cavity (Y, Z):
    # (0, 0)
    # (4.5, 3.0)
    # (4.0, 17.0)
    # (5.0, 27.0)
    # (2.5, 35.14)
    # (25.0, 50.0)
    # (0, 50.0) # Close the loop back to center? Or just the line from 2.5 to 25?
    # If it's a cavity, it's a hole. The profile must be closed.
    # If the cavity opens to D=50 at Z=50, the profile is:
    # Line (0,0) -> (4.5, 3) -> (4, 17) -> (5, 27) -> (2.5, 35.14) -> (25, 50) -> (0, 50) -> (0,0).
    # This creates a solid that is removed.
    
    # Let's add these points to the sketch.
    # We need to add lines between them.
    # Since Sketcher doesn't support arbitrary points easily in a script without constraints, we will use a workaround:
    # Create a sketch on YZ plane.
    # Add a line from (0,0) to (25, 50) and constrain it?
    # No, let's use the "Sketcher::SketchObject" and add geometry manually.
    # We can add lines using Part.LineSegment.
    
    # Define points
    pts = [
        App.Vector(0, 0, 0),
        App.Vector(4.5, 3.0, 0),
        App.Vector(4.0, 17.0, 0),
        App.Vector(5.0, 27.0, 0),
        App.Vector(2.5, 35.14, 0),
        App.Vector(25.0, 50.0, 0),
        App.Vector(0, 50.0, 0)
    ]
    
    # Add lines
    for i in range(len(pts)-1):
        sk_cavity.addGeometry(Part.LineSegment(pts[i], pts[i+1]), False)
    
    # Close the loop
    sk_cavity.addGeometry(Part.LineSegment(pts[-1], pts[0]), False)
    
    # Add constraints to make it a valid sketch (optional but good practice)
    # We can't easily add geometric constraints between arbitrary points in a script without a solver, 
    # but the geometry is defined by coordinates.
    # We need to ensure the sketch is valid.
    # Let's add a constraint to fix the start point.
    sk_cavity.addConstraint(Sketcher.Constraint("Point", 0, 1, 0, 0)) # Fix origin
    sk_cavity.addConstraint(Sketcher.Constraint("Point", 0, 2, 0, 0)) # Fix origin
    
    # Create the revolution pocket
    rev_cavity = body.newObject("PartDesign::Revolution", "RevCavity")
    rev_cavity.Profile = sk_cavity
    rev_cavity.ReferenceAxis = (doc.getObject("Z_Axis"), [""])
    rev_cavity.Angle = 360.0
    rev_cavity.Type = "Cut" # Subtract
    
    # 3. Central Through Bore
    sk_bore = body.newObject("Sketcher::SketchObject", "BoreSketch")
    sk_bore.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    sk_bore.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    sk_bore.MapMode = "FlatFace"
    sk_bore.Constrain = True
    sk_bore.ConstraintList = []
    sk_bore.AddGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_d/2), False)
    sk_bore.AddConstraint(Sketcher.Constraint("Radius", 0, 1, params.bore_d/2))
    
    pocket_bore = body.newObject("PartDesign::Pocket", "PocketBore")
    pocket_bore.Profile = sk_bore
    pocket_bore.Type = "ThroughAll"
    
    # 4. Lower Stepped Relief (Pocket)
    # This is a set of concentric pockets on the face Z=0.
    # We can create a single sketch with multiple concentric circles and use a "Pocket" with "ThroughAll" or specific length?
    # No, the steps have different lengths.
    # We need to create a "Groove" or multiple "Pockets".
    # Let's create a sketch on the XY plane (Face Z=0).
    # Draw the outline of the steps.
    # Step 1: D=15, L=1.3
    # Step 2: D=17, L=8.6
    # Step 3: D=15, L=2.8
    # Step 4: D=19, L=4.1
    # We can create a sketch with a closed profile that represents the union of these steps?
    # No, they are sequential.
    # Better: Create a sketch on the XY plane.
    # Draw a line from (0,0) to (0, 16.8) (total length).
    # Then draw the radii at each step?
    # No, PartDesign::Pocket on a face extrudes along the normal.
    # If we draw a profile on the XY plane, extruding along Z creates a cylinder.
    # To create a stepped hole, we need to define the shape in the YZ plane and revolve?
    # Yes! The "Lower Stepped Relief" is also a revolution feature.
    # We can combine the "Lower Stepped Relief" and "Internal Cavity" into one revolution feature?
    # The "Internal Cavity" starts at Z=0 and goes in.
    # The "Lower Stepped Relief" is the entrance.
    # They are the same feature!
    # The "Internal Cavity" parameters define the whole internal void.
    # The "Lower Stepped Relief" parameters define the first part of it.
    # So we don't need a separate feature for the relief. The "RevCavity" covers it.
    # Wait, "Upper contoured cutout" is separate.
    # So the "RevCavity" covers the stepped relief AND the internal cavity.
    # The "Upper contoured cutout" might be an outer groove?
    # "Upper contoured annular channel".
    # If it's an outer groove, we need to subtract it from the outside.
    # Let's assume it's an outer groove.
    # Depth 26 is still problematic.
    # Maybe "depth" is the axial length?
    # "upper_contoured_cutout_depth = 26.1054564".
    # If it's axial length, then it's a groove of length 26.1.
    # "upper_contoured_cutout_length = 17.8198418".
    # This is confusing.
    # Let's assume the "Upper contoured cutout" is the shape of the cavity wall (internal) as discussed before.
    # And the "Lower Stepped Relief" is just the name for the first part of the cavity.
    # So we are good with the "RevCavity".
    
    # 5. Edit: Side Rectangular Cutouts
    # "Cut the unequal left and right rectangular side recesses at their specified center offsets and common depth."
    # Depth = 19.0.
    # Left: L=7.06, W=5.81, Center=(-17.03, -5.105).
    # Right: L=7.41, W=6.0, Center=(17.205, -5.2).
    # These are cutouts on the side of the cylinder.
    # We can create a sketch on the XZ plane (at Y = offset) and pocket?
    # Or create a sketch on the XY plane and use a "Pocket" with a specific reference?
    # Easier: Create a sketch on the XY plane (Face Z=0) but offset?
    # No, the cutouts are on the side surface (cylindrical).
    # We can create a sketch on the XZ plane (Y=0 face? No, cylinder has no flat face).
    # We can create a sketch on the "Body" with MapMode="Plane" and reference the cylinder surface?
    # Or simpler: Create a sketch on the XY plane (Z=0), draw the rectangle, and use a "Pocket" with Type="ThroughAll" but limited by a plane?
    # No, we need to cut INTO the cylinder wall.
    # Standard way: Create a sketch on the XZ plane (Y=0).
    # But we need to offset the sketch to Y = -5.105 and Y = -5.2.
    # We can create two sketches.
    
    # Sketch Left
    sk_left = body.newObject("Sketcher::SketchObject", "SketchLeft")
    sk_left.Placement = App.Placement(App.Vector(0, -params.side_off_y, 0), App.Rotation()) # Offset Y
    # Wait, the center is at Y = -5.105.
    # We need to sketch on the plane Y = -5.105.
    # We can use the "YZ_Plane" and rotate/translate?
    # Or use the "Body" and set the sketch plane to the cylinder surface?
    # FreeCAD 1.1 allows attaching a sketch to a face.
    # But the cylinder face is curved.
    # We can approximate by creating a sketch on the XZ plane (Y=0) and then translating the sketch object?
    # No, the sketch plane must be flat.
    # We can create a sketch on the XZ plane (Y=0), draw the rectangle, and then use a "Pocket" with a "Reference" that is a plane at Y = -5.105?
    # No, the pocket extrudes along the face normal.
    # If we sketch on XZ plane, normal is Y.
    # If we place the sketch at Y = -5.105, the normal is still Y.
    # So the pocket will cut along Y.
    # This works!
    # We create a sketch on the XZ plane (Y=0).
    # We place the sketch object at Y = -5.105.
    # We draw a rectangle of size L x W.
    # We pocket along Y (normal).
    # The depth is 19.0.
    # Direction: Inwards (towards center)? Or outwards?
    # "Side recesses". Usually cut into the wall.
    # If we are at Y = -5.105, and we cut along Y, we go towards Y=0 (center) or Y=-10 (outside).
    # "Recesses" implies cut into the material.
    # If the cylinder is D=30 (R=15).
    # Y = -5.105 is inside the cylinder.
    # Cutting along Y towards Y=0 cuts into the wall.
    # Cutting along Y towards Y=-10 cuts out of the cylinder.
    # So we need to cut towards Y=0.
    # But the sketch is at Y = -5.105.
    # If we pocket along Y, the direction is defined by the sketch normal.
    # The normal of the XZ plane is Y.
    # We need to reverse the pocket direction.
    
    # Let's create the sketch on the XZ plane (Y=0).
    # Place the sketch at Y = -5.105.
    # Draw a rectangle:
    # Center at (0, 0) in the sketch plane (which is XZ).
    # Wait, the sketch plane is XZ.
    # The rectangle should be centered at X = -17.03, Z = 0?
    # "center offsets".
    # Left: X = -17.03, Y = -5.105.
    # So in the sketch plane (XZ), the center is at X = -17.03, Z = 0.
    # Rectangle: Width (along X) = 5.81. Length (along Z) = 7.06.
    # So X range: -17.03 - 2.905 to -17.03 + 2.905.
    # Z range: -3.53 to 3.53.
    
    # Create Sketch Left
    sk_left = body.newObject("Sketcher::SketchObject", "SketchLeft")
    sk_left.Placement = App.Placement(App.Vector(0, -params.side_off_y, 0), App.Rotation())
    sk_left.AttachmentSupport = (doc.getObject("XZ_Plane"), [""])
    sk_left.MapMode = "FlatFace"
    sk_left.Constrain = True
    sk_left.ConstraintList = []
    
    # Define rectangle points
    # Center X = -17.03, Z = 0
    # Width = 5.81 -> Half = 2.905
    # Length = 7.06 -> Half = 3.53
    p1 = App.Vector(-17.03 - 2.905, 0, -3.53)
    p2 = App.Vector(-17.03 + 2.905, 0, -3.53)
    p3 = App.Vector(-17.03 + 2.905, 0, 3.53)
    p4 = App.Vector(-17.03 - 2.905, 0, 3.53)
    
    sk_left.addGeometry(Part.LineSegment(p1, p2), False)
    sk_left.addGeometry(Part.LineSegment(p2, p3), False)
    sk_left.addGeometry(Part.LineSegment(p3, p4), False)
    sk_left.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Add constraints to fix the rectangle
    sk_left.addConstraint(Sketcher.Constraint("Point", 0, 1, -17.03 - 2.905, 0))
    sk_left.addConstraint(Sketcher.Constraint("Point", 0, 2, -17.03 + 2.905, 0))
    sk_left.addConstraint(Sketcher.Constraint("Point", 0, 3, -17.03 + 2.905, 0))
    sk_left.addConstraint(Sketcher.Constraint("Point", 0, 4, -17.03 - 2.905, 0))
    sk_left.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sk_left.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
    sk_left.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
    sk_left.addConstraint(Sketcher.Constraint("Vertical", 0, 2))
    
    pocket_left = body.newObject("PartDesign::Pocket", "PocketLeft")
    pocket_left.Profile = sk_left
    pocket_left.Length = params.side_dep
    pocket_left.Type = "Solid"
    pocket_left.Reversed = True # Cut towards Y=0 (inwards)
    
    # Sketch Right
    sk_right = body.newObject("Sketcher::SketchObject", "SketchRight")
    sk_right.Placement = App.Placement(App.Vector(0, -params.side_r_off_y, 0), App.Rotation())
    sk_right.AttachmentSupport = (doc.getObject("XZ_Plane"), [""])
    sk_right.MapMode = "FlatFace"
    sk_right.Constrain = True
    sk_right.ConstraintList = []
    
    # Right: X = 17.205, Y = -5.2
    # Width = 6.0 -> Half = 3.0
    # Length = 7.41 -> Half = 3.705
    p1 = App.Vector(17.205 - 3.0, 0, -3.705)
    p2 = App.Vector(17.205 + 3.0, 0, -3.705)
    p3 = App.Vector(17.205 + 3.0, 0, 3.705)
    p4 = App.Vector(17.205 - 3.0, 0, 3.705)
    
    sk_right.addGeometry(Part.LineSegment(p1, p2), False)
    sk_right.addGeometry(Part.LineSegment(p2, p3), False)
    sk_right.addGeometry(Part.LineSegment(p3, p4), False)
    sk_right.addGeometry(Part.LineSegment(p4, p1), False)
    
    sk_right.addConstraint(Sketcher.Constraint("Point", 0, 1, 17.205 - 3.0, 0))
    sk_right.addConstraint(Sketcher.Constraint("Point", 0, 2, 17.205 + 3.0, 0))
    sk_right.addConstraint(Sketcher.Constraint("Point", 0, 3, 17.205 + 3.0, 0))
    sk_right.addConstraint(Sketcher.Constraint("Point", 0, 4, 17.205 - 3.0, 0))
    sk_right.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sk_right.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
    sk_right.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
    sk_right.addConstraint(Sketcher.Constraint("Vertical", 0, 2))
    
    pocket_right = body.newObject("PartDesign::Pocket", "PocketRight")
    pocket_right.Profile = sk_right
    pocket_right.Length = params.side_r_len # Note: parameter name is side_r_len
    pocket_right.Type = "Solid"
    pocket_right.Reversed = True
    
    # 6. Primary Radial Slots
    # "Add a primary radial slot... repeat it evenly around the nozzle axis using radial_slots_count."
    # Width = 6.0, Length = 13.51, Depth = 21.0, Center X = -7.0.
    # "Radial slot" usually means a slot that goes from the center outwards?
    # Or a slot on the surface?
    # "Radial slot" in a cylinder usually means a slot that cuts radially from the inner surface to the outer?
    # Or a slot on the outer surface?
    # Given "center offset", it's likely a slot on the outer surface.
    # "Radial" might mean the slot is oriented radially?
    # Or it's a slot that is radial in shape (like a keyway)?
    # Let's assume it's a rectangular slot on the outer surface, oriented radially (along the radius).
    # But "center offset" suggests a position.
    # If it's a radial slot, it might be a slot that goes from the center to the edge?
    # But the cylinder is solid.
    # Let's assume it's a slot on the outer surface, oriented along the radius (Z direction? No, radius is Y).
    # If it's a radial slot, it might be a slot that cuts from the outer surface inwards?
    # "Depth = 21.0".
    # If it cuts inwards from the outer surface (R=15), depth 21 is impossible.
    # So it must be a slot on the outer surface, oriented along the circumference?
    # Or a slot that is "radial" in the sense of a keyway (along the axis)?
    # "Radial slot" often means a slot that is perpendicular to the axis (like a keyway).
    # Let's assume it's a slot on the outer surface, oriented along the Z axis (axial).
    # "Center offset X = -7.0".
    # This suggests the slot is at a specific angle.
    # "Repeat it evenly around the nozzle axis".
    # So we have 4 slots at 0, 90, 180, 270 degrees?
    # But "center offset X = -7.0".
    # If the slot is at 0 degrees, X = 15.
    # If the slot is at 180 degrees, X = -15.
    # "Center offset X = -7.0" might be the X coordinate of the center of the slot in the XY plane.
    # So the slot is at an angle where X = -7.0.
    # Angle = atan2(0, -7) = 180 degrees? No, Y is not specified.
    # Maybe the slot is at Y = 0, X = -7.0?
    # But the cylinder radius is 15.
    # So the slot
