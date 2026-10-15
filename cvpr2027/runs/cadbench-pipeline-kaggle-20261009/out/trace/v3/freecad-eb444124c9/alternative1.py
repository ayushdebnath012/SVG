import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Configuration ---
# Derived from __file__
script_dir = Path(__file__).parent
script_stem = Path(__file__).stem

# Base Parameters
params_base = {
    "wheel_outer_radial_extent": 12.5,
    "rim_shoulder_radial_extent": 12.0,
    "inner_web_radial_extent": 11.25,
    "outer_flange_axial_width": 4.0,
    "inner_web_axial_width": 2.5,
}

# Edit Parameters
params_edit = {
    "wheel_plate_thickness": 1.5,
    "number_of_spokes": 3,
    "spoke_end_diameter": 4.0,
    "spoke_end_center_x": 8.660254,
    "inner_spoke_arc_radius": 6.5,
    "inner_spoke_arc_start_angle": 135.9482512,
    "inner_spoke_arc_end_angle": -135.9482512,
    "outer_spoke_arc_radius": 3.0,
    "outer_spoke_arc_center_x": -4.330127,
    "outer_spoke_arc_center_y": 7.5,
    "outer_spoke_arc_start_angle": -23.4636305,
    "outer_spoke_arc_end_angle": -96.5363695,
    "wheel_spoke_cutout_count": 3,
    "wheel_spoke_cutout_arc_radius": 1.0,
    "spoke_cutout_arc_center_y": 0.8660254,
    "spoke_cutout_line_upper_y": 1.7320508,
}

def create_and_save_document(base_params, is_base=True):
    # Create Document
    doc = App.newDocument("WheelPart")
    
    # Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Parameters Feature (App::VarSet is the standard way to expose parameters in PD 1.1)
    params = body.newObject("App::VarSet", "Parameters")
    for key, val in base_params.items():
        params.addProperty("App::PropertyLength", key, "Dimensions", key)
        params.setPropertyValue(key, val)
    
    # Global Planes (Standard FreeCAD axes, but we ensure they exist via Placement if needed, 
    # though PartDesign::SketchObject usually attaches to existing XY, XZ, YZ).
    # We create sketches relative to the Body's XY plane (z=0).
    
    # === STEP 1: Build the Axisymmetric Blank (Revolution) ===
    
    # Base Sketch for the Wheel Blank (Profile in XZ plane, revolved around Z)
    # Note: In XZ plane, X is radial, Z is axial.
    sketch_blank = body.newObject("Sketcher::SketchObject", "BlankProfile")
    sketch_blank.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_blank.PlacementRotation = App.Rotation() # Identity
    sketch_blank.Support = (doc.getObject("XY_Plane"), []) # Default XY plane in PartDesign context is usually the sketch plane.
    # Actually, for revolution around Z, we sketch in the XZ plane (Standard view XZ).
    # We will explicitly set the Placement to be on the XZ plane (Y=0, Z=0) and oriented correctly.
    # PartDesign Sketches attach to a face. We assume the Body starts with XY plane.
    # To sketch in XZ, we usually rotate the sketch or use the XZ plane.
    # Let's use the standard approach: Sketch on XY plane, then rotate the sketch plane? 
    # No, easier: Sketch on XZ plane. 
    # In FreeCAD, XY_Plane is Z up. XZ_Plane is Y up.
    # We want Revolution around Z. The profile must be in a plane containing Z. XZ is good.
    # So we attach to XZ_Plane.
    
    xz_plane = doc.addObject("PartDesign::Plane", "XZ_Plane")
    xz_plane.Placement = App.Placement(App.Vector(0,0,0))
    xz_plane.PlacementRotation = App.Rotation(0, 0, 0) # Rotate so it aligns with global XZ? 
    # Actually, standard practice in PartDesign: 
    # 1. Create Sketch on XY.
    # 2. Create Revolution around Z axis (which is the normal to XY).
    # This creates the wheel blank.
    
    sketch_blank = body.newObject("Sketcher::SketchObject", "BlankSketch")
    sketch_blank.Placement = App.Placement(App.Vector(0,0,0))
    # We define the geometry in the XY plane (X=Radial, Y=Axial) and revolve around Z.
    # X is radial, Y is axial.
    
    # Profile:
    # Outer Rim (Top part of profile): Radius = wheel_outer_radial_extent
    # Shoulder (Slope): From Outer Rim to Inner Web.
    # Inner Web (Bottom part): Radius = inner_web_radial_extent
    
    # Points:
    # 1. Origin (Center) -> (0,0)
    # 2. Inner Web Inner Radius -> (inner_web_radial_extent, 0)
    # 3. Inner Web Outer Radius -> (inner_web_radial_extent, -outer_flange_axial_width/2)  (Symmetric)
    # 4. Outer Rim Inner Radius -> (rim_shoulder_radial_extent, -outer_flange_axial_width/2)
    # 5. Outer Rim Outer Radius -> (rim_shoulder_radial_extent, outer_flange_axial_width/2)
    # 6. Inner Web Outer Radius -> (inner_web_radial_extent, outer_flange_axial_width/2)
    
    # Wait, description says: "inner web narrows to inner_web_axial_width and extends inward to the wheel axis."
    # "outer rim uses the full axial flange width"
    # "inward sloping shoulders"
    
    # Let's define the profile shape in the XY plane (X=Radial, Y=Axi al):
    # Top Half (Y > 0):
    #   Start at (inner_web_radial_extent, 0) -> Center.
    #   Go to (inner_web_radial_extent, inner_web_axial_width/2) -> End of web.
    #   Slope to (rim_shoulder_radial_extent, outer_flange_axial_width/2) -> Start of rim.
    #   Vertical line to (rim_shoulder_radial_extent, -outer_flange_axial_width/2) -> End of rim.
    #   Slope back to (inner_web_radial_extent, -inner_web_axial_width/2) -> Start of web.
    #   Close to (inner_web_radial_extent, 0).
    
    # We need to construct this in the sketch.
    # Constraints:
    # 1. Center at (0,0) ? No, the profile doesn't touch 0 unless inner_web_radial_extent = 0.
    #    The wheel is solid, so we revolve this closed profile.
    
    # Let's build the sketch points.
    # Point A: (inner_web_radial_extent, 0) - Center of wheel face? No, this is the radius.
    # The wheel has a central hole? "centered solid web". Usually implies solid cylinder for the hub area.
    # But the description says "narrow outer rim, inward sloping shoulders, and a centered solid web".
    # If it's a solid web extending inward to the wheel axis, then the inner radius of the web is 0?
    # "extends inward to the wheel axis" -> Yes, it goes to the center.
    # So the profile is defined by:
    # - Inner radius (Web): 0 to inner_web_radial_extent.
    # - Shoulder slope: from (inner_web_radial_extent, +/- inner_web_axial_width/2) to (rim_shoulder_radial_extent, +/- outer_flange_axial_width/2).
    # - Outer Rim: rim_shoulder_radial_extent to (outer_flange_axial_width/2).
    
    # Let's refine the geometry:
    # The "solid web" implies a cylinder of radius `inner_web_radial_extent` and height `inner_web_axial_width` in the center.
    # The "rim" is a cylinder of radius `rim_shoulder_radial_extent` and height `outer_flange_axial_width` at the outside.
    # They are connected by a conical frustum (shoulder).
    
    # Profile Points (X=Radial, Y=Axi al):
    # P1: (0, 0) - Center of the wheel face.
    # P2: (inner_web_radial_extent, inner_web_axial_width/2) - End of top web face.
    # P3: (rim_shoulder_radial_extent, outer_flange_axial_width/2) - Start of top rim face.
    # P4: (rim_shoulder_radial_extent, -outer_flange_axial_width/2) - End of bottom rim face.
    # P5: (inner_web_radial_extent, -inner_web_axial_width/2) - End of bottom web face.
    # P6: (0, 0) - Back to center.
    
    # We add points and constraints.
    sketch_blank.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params_base["inner_web_radial_extent"], 0, 0)), True) # Radial line to web edge
    # Actually, let's just draw the loop directly.
    
    # To make it editable and constrained:
    # 1. Line from (0,0) to (inner_web_radial_extent, 0) - Horizontal
    # 2. Line from (inner_web_radial_extent, 0) to (inner_web_radial_extent, inner_web_axial_width/2) - Vertical
    # 3. Line from (inner_web_radial_extent, inner_web_axial_width/2) to (rim_shoulder_radial_extent, outer_flange_axial_width/2) - Slope
    # 4. Line from (rim_shoulder_radial_extent, outer_flange_axial_width/2) to (rim_shoulder_radial_extent, -outer_flange_axial_width/2) - Vertical
    # 5. Line from (rim_shoulder_radial_extent, -outer_flange_axial_width/2) to (inner_web_radial_extent, -inner_web_axial_width/2) - Slope
    # 6. Line from (inner_web_radial_extent, -inner_web_axial_width/2) to (0,0) - Horizontal
    
    # Simplified construction:
    # Create 6 lines.
    # Points:
    # O = (0,0)
    # A = (inner_web_radial_extent, 0)
    # B = (inner_web_radial_extent, inner_web_axial_width/2)
    # C = (rim_shoulder_radial_extent, outer_flange_axial_width/2)
    # D = (rim_shoulder_radial_extent, -outer_flange_axial_width/2)
    # E = (inner_web_radial_extent, -inner_web_axial_width/2)
    # Back to O.
    
    # We will add these lines.
    # We need to ensure the origin is fixed.
    
    # Line 1: O to A
    l1 = sketch_blank.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params_base["inner_web_radial_extent"], 0, 0)), True)
    # Line 2: A to B
    l2 = sketch_blank.addGeometry(Part.LineSegment(App.Vector(params_base["inner_web_radial_extent"], 0, 0), App.Vector(params_base["inner_web_radial_extent"], params_base["inner_web_axial_width"]/2, 0)), True)
    # Line 3: B to C (Shoulder)
    pB = App.Vector(params_base["inner_web_radial_extent"], params_base["inner_web_axial_width"]/2, 0)
    pC = App.Vector(params_base["rim_shoulder_radial_extent"], params_base["outer_flange_axial_width"]/2, 0)
    l3 = sketch_blank.addGeometry(Part.LineSegment(pB, pC), True)
    # Line 4: C to D (Rim Height)
    l4 = sketch_blank.addGeometry(Part.LineSegment(pC, App.Vector(params_base["rim_shoulder_radial_extent"], -params_base["outer_flange_axial_width"]/2, 0)), True)
    # Line 5: D to E (Shoulder)
    pD = App.Vector(params_base["rim_shoulder_radial_extent"], -params_base["outer_flange_axial_width"]/2, 0)
    pE = App.Vector(params_base["inner_web_radial_extent"], -params_base["inner_web_axial_width"]/2, 0)
    l5 = sketch_blank.addGeometry(Part.LineSegment(pD, pE), True)
    # Line 6: E to O
    l6 = sketch_blank.addGeometry(Part.LineSegment(pE, App.Vector(0, 0, 0)), True)
    
    # Constraints
    # Fix Origin (O)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Fixed", 0, 1), False) # Fix X,Y of point 0? No, Fixed constrains point to 0,0.
    # Actually, simpler: Coincident O with Origin (if plane allows) or just fix coordinates.
    # Let's use Distance/Position constraints or just rely on the fact that we are drawing from (0,0).
    # Better: Fix the first point to (0,0).
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Fixed", 0, 1), False) # Point 0 fixed?
    # The `Fixed` constraint fixes a point to (0,0) in the sketch plane.
    
    # Coincident A and B (X coordinate)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("PointOnObject", 0, 0, 0, 0), False) # Point 0 on Line 0?
    # Let's use standard constraints:
    # 1. Point 0 Fixed.
    # 2. Point 1 (A) on Line 1 (Vertical line from A to B)? No, Line 1 is O-A.
    # Let's just make the geometry rigid by fixing the shape.
    # We'll add a PointOnObject constraint to ensure the shoulder lines are connected.
    
    # Re-adding constraints for robustness:
    # 1. Point 0 Fixed.
    # 2. Point 1 (A) Coincident with End of Line 0?
    # Let's just use the coordinates we set. In PartDesign 1.1, if we don't constrain, it might move.
    # But for a simple revolve, we can just lock the sketch.
    
    # Let's use a simpler method: Create a solid cylinder and subtract? 
    # No, "Parametric feature tree".
    # Let's just add constraints:
    # - Point 0 Fixed.
    # - Point 1 (A) on Line 0 (obviously) and on Line 6 (obviously).
    # - Line 0 Horizontal.
    # - Line 2 Vertical.
    # - Line 4 Vertical.
    # - Line 3 and 5 tangent to the circles? No, they are lines.
    
    # Simplified: Just add constraints to define the shape.
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Fixed", 0, 1), False)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Vertical", 2, 1), False) # Line 2 (A-B)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Vertical", 3, 1), False) # Line 4 (C-D)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Horizontal", 0, 1), False) # Line 0 (O-A)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Horizontal", 5, 1), False) # Line 6 (E-O)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Coincident", 0, 1, 0, 2), False) # Connect O to A (Line 0 and 2) -> Wait, Line 0 is 0-1, Line 2 is 1-2.
    # The indices in `addGeometry` are 0, 1, 2...
    # Line 0: 0->1. Line 1: 1->2. Line 2: 2->3. Line 3: 3->4. Line 4: 4->5. Line 5: 5->0.
    # Let's re-index carefully.
    # G0: O->A. G1: A->B. G2: B->C. G3: C->D. G4: D->E. G5: E->O.
    
    # Constraints:
    # G0 Horizontal.
    # G1 Vertical.
    # G3 Vertical.
    # G5 Horizontal.
    # G2 and G4 are the shoulders.
    
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Horizontal", 0, 1), False)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Vertical", 1, 1), False)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Vertical", 3, 1), False)
    Sketcher.addConstraint(sketch_blank, Sketcher.Constraint("Horizontal", 5, 1), False)
    Sketcher.addConstraint(sketch_blank
