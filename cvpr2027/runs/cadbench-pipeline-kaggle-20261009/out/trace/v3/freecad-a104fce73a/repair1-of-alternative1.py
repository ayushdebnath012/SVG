import FreeCAD as App
import Part
import math
from pathlib import Path

# --- Configuration ---
# Base Part Parameters
PARAMS_BASE = {
    "bracket_base_length": 62.0,
    "bracket_base_width": 24.0,
    "bracket_base_thickness": 8.0,
}

# Edit Part Parameters (Target)
PARAMS_EDIT = {
    "hinge_pin_hole_diameter": 8.0,
    "hinge_cheek_outer_arc_radius": 10.0,
    "hinge_cheek_outer_arc_start_angle": -35.0003487,
    "hinge_cheek_outer_arc_end_angle": 148.6986094,
    "hinge_cheek_x_thickness": 6.0,
    "hinge_cheek_inner_face_offset_from_midplane": 8.0,
    "hinge_axis_y": 12.0,
    "hinge_axis_z": 27.0,
    "small_boss_inner_diameter": 3.0,
    "small_boss_outer_diameter": 6.0,
    "small_boss_depth": 10.0,
    "small_boss_start_inset_from_front": 13.0,
    "small_boss_seed_center_x": 20.0,
    "mounting_hole_diameter": 9.0,
    "mounting_hole_end_offset_x": 8.5,
}

def create_model(params):
    doc = App.newDocument("Bracket_Assembly")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Helper to create a sketch object on a specific plane with a specific placement
    def create_sketch(name, plane_name, placement):
        sk = body.newObject("Sketcher::SketchObject", name)
        sk.Placement = placement
        sk.Plane = plane_name
        return sk

    # 1. Base Plate
    # Sketch on XY plane
    plate_sketch = create_sketch("PlateSketch", "XY_Plane", App.Placement(App.Vector(0, 0, 0)))
    
    # Define rectangle: Length along X, Width along -Y
    # Center at (0,0). X: -L/2 to L/2. Y: 0 to -W.
    L = params["bracket_base_length"]
    W = params["bracket_base_width"]
    
    # Lines
    l1 = plate_sketch.addGeometry(Part.LineSegment(App.Vector(-L/2, 0, 0), App.Vector(L/2, 0, 0)))
    l2 = plate_sketch.addGeometry(Part.LineSegment(App.Vector(L/2, 0, 0), App.Vector(L/2, -W, 0)))
    l3 = plate_sketch.addGeometry(Part.LineSegment(App.Vector(L/2, -W, 0), App.Vector(-L/2, -W, 0)))
    l4 = plate_sketch.addGeometry(Part.LineSegment(App.Vector(-L/2, -W, 0), App.Vector(-L/2, 0, 0)))
    
    # Constraints
    # Coincident
    c1 = plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # l1 end, l4 start
    c2 = plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 2)) # l1 end, l2 start
    c3 = plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # l2 end, l3 start
    c4 = plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 2)) # l3 end, l4 start
    # Wait, indices are tricky. Let's use explicit indices 0..3 for lines.
    # l1: 0, l2: 1, l3: 2, l4: 3
    # l1 end (1) coincident l2 start (0)
    # l2 end (1) coincident l3 start (0)
    # l3 end (1) coincident l4 start (0)
    # l4 end (1) coincident l1 start (0)
    
    plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    plate_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    
    # Dimensions
    plate_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, L))
    plate_sketch.addConstraint(Sketcher.Constraint("Length", 1, 0, W))
    # Horizontal/Vertical
    plate_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    plate_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    
    # Pad Plate
    pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
    pad_plate.Profile = plate_sketch
    pad_plate.Length = params["bracket_base_thickness"]
    pad_plate.MidPlane = False
    pad_plate.Reverse = False
    
    # 2. Hinge Cheeks
    # Parameters
    offset = params["hinge_cheek_inner_face_offset_from_midplane"]
    thickness = params["hinge_cheek_x_thickness"]
    arc_r = params["hinge_cheek_outer_arc_radius"]
    arc_start = params["hinge_cheek_outer_arc_start_angle"]
    arc_end = params["hinge_cheek_outer_arc_end_angle"]
    axis_y = params["hinge_axis_y"]
    axis_z = params["hinge_axis_z"]
    
    # Helper to calculate arc points
    def get_arc_point(angle_deg):
        rad = math.radians(angle_deg)
        # Assuming 0 deg is +Y, 90 deg is +Z
        y = axis_y + arc_r * math.sin(rad)
        z = axis_z + arc_r * math.cos(rad)
        return App.Vector(0, y, z)
    
    p_start = get_arc_point(arc_start)
    p_end = get_arc_point(arc_end)
    
    # Left Cheek (Negative X)
    # Sketch on YZ plane (Normal X). Placement at x = -offset.
    # Rotation: 90 deg around Y to align Z with local Y (up) and Y with local X (right)?
    # Actually, standard YZ plane sketch: Normal is X.
    # We want to sketch in YZ. 
    # Placement: Vector(-offset, 0, 0). 
    # Rotation: 90 deg around Y axis maps Global Z to Local Y (Up) and Global Y to Local X (Right).
    # This matches our angle assumption (0=Y, 90=Z).
    
    cheek_left_sketch = create_sketch("CheekLeftSketch", "YZ_Plane", 
                                       App.Placement(App.Vector(-offset, 0, 0), App.Rotation(0, 1, 0, 90)))
    
    # Profile for Left Cheek
    # Base Top Z = params["bracket_base_thickness"]
    # Inner Face is at Z = Base Top.
    # The cheek extends from Base Top to Base Top + thickness.
    # The arc is the outer boundary.
    # We need to connect the arc to the base top.
    # "join it to the base top with straight rear and front flanks"
    # This implies vertical lines connecting the arc endpoints to the base top level?
    # Or the arc endpoints ARE on the base top?
    # Given "crown", the arc is likely the top surface.
    # Let's assume the profile goes:
    # 1. Start at (Y=0, Z=BaseTop) -> Front Flank?
    # 2. Line to Arc Start?
    # 3. Arc to Arc End?
    # 4. Line to (Y=?, Z=BaseTop)?
    # 5. Line back to start.
    
    # Let's construct the profile points explicitly.
    # Base Top Z = params["bracket_base_thickness"]
    base_z = params["bracket_base_thickness"]
    
    # We need to find where the arc intersects Z=base_z? 
    # Or just draw lines from the arc endpoints down to Z=base_z?
    # "join it to the base top with straight rear and front flanks"
    # This suggests the flanks are vertical (parallel to Z).
    # So the profile is:
    # - Line from (Y=0, Z=base_z) to (Y=p_start.Y, Z=base_z)? No, that's not a flank.
    # - Flank connects Arc Start to Base Top.
    # - Flank connects Arc End to Base Top.
    # - Then close the loop.
    
    # Let's assume the "flanks" are vertical lines dropping from the arc endpoints to the base top level.
    # And the "base top" connection is a line along Z=base_z between the two flank bottoms.
    # And the "inner face" is the plane at Z=base_z.
    # So the profile is a closed loop:
    # 1. Point A: (Y=0, Z=base_z) - Front corner of base?
    # 2. Line A -> B: Vertical line up to Arc Start?
    # 3. Arc B -> C
    # 4. Line C -> D: Vertical line down to Base Top?
    # 5. Line D -> A: Line along Base Top?
    
    # Wait, the cheek is symmetric? No, "symmetric pair".
    # Let's assume the cheek sits on the base.
    # The profile must be closed.
    # Let's define the profile points:
    # P1: (0, base_z) - Front edge of base at the cheek location.
    # P2: (p_start.Y, base_z) - Bottom of front flank.
    # P3: (p_start.Y, p_start.Z) - Top of front flank (Arc Start).
    # P4: (p_end.Y, p_end.Z) - Arc End.
    # P5: (p_end.Y, base_z) - Bottom of rear flank.
    # P6: (0, base_z) - Back to start?
    # This creates a shape that is open on the left (Y<0).
    # The cheek should probably extend from Y=0 to Y=something?
    # Or maybe the "flanks" connect the arc to the base corners?
    # Let's assume the cheek starts at Y=0 (front of base) and goes backwards?
    # No, "extend it outward by hinge_cheek_x_thickness".
    # Let's assume the profile is:
    # - Line from (0, base_z) to (p_start.Y, base_z) ? No.
    # - Let's assume the cheek is bounded by Y=0 (front), Y=something (back), Z=base_z (bottom), and the arc.
    # But the arc is the "crown".
    # Let's try this profile:
    # 1. Line from (0, base_z) to (p_start.Y, base_z) -> This is on the base top.
    # 2. Line from (p_start.Y, base_z) to (p_start.Y, p_start.Z) -> Front Flank.
    # 3. Arc from (p_start.Y, p_start.Z) to (p_end.Y, p_end.Z).
    # 4. Line from (p_end.Y, p_end.Z) to (p_end.Y, base_z) -> Rear Flank.
    # 5. Line from (p_end.Y, base_z) to (0, base_z) -> Back to start.
    # This forms a closed loop.
    
    # Create geometry for Left Cheek
    # Line 1: (0, base_z) to (p_start.Y, base_z)
    cheek_left_sketch.addGeometry(Part.LineSegment(App.Vector(0, base_z, 0), App.Vector(p_start.Y, base_z, 0)))
    # Line 2: (p_start.Y, base_z) to (p_start.Y, p_start.Z)
    cheek_left_sketch.addGeometry(Part.LineSegment(App.Vector(p_start.Y, base_z, 0), App.Vector(p_start.Y, p_start.Z, 0)))
    # Arc: Center (0, axis_y, axis_z), Radius, Start, End
    # Note: The arc center in the sketch plane (YZ) is (0, axis_y) if we consider Y as X and Z as Y?
    # Our rotation was 90 deg around Y.
    # Global Y -> Local X. Global Z -> Local Y.
    # Center in Global: (0, axis_y, axis_z).
    # In Local: X = axis_y, Y = axis_z.
    # So Center = (axis_y, axis_z) in sketch coords.
    # Radius = arc_r.
    # Start Angle = arc_start. End Angle = arc_end.
    cheek_left_sketch.addGeometry(Part.Arc(App.Vector(0, axis_y, axis_z), App.Vector(0, 0, 1), arc_r, arc_start, arc_end))
    # Line 3: (p_end.Y, p_end.Z) to (p_end.Y, base_z)
    cheek_left_sketch.addGeometry(Part.LineSegment(App.Vector(p_end.Y, p_end.Z, 0), App.Vector(p_end.Y, base_z, 0)))
    # Line 4: (p_end.Y, base_z) to (0, base_z)
    cheek_left_sketch.addGeometry(Part.LineSegment(App.Vector(p_end.Y, base_z, 0), App.Vector(0, base_z, 0)))
    
    # Constraints for Left Cheek
    # Coincident
    c1 = cheek_left_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    c2 = cheek_left_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    c3 = cheek_left_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    c4 = cheek_left_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    # Horizontal/Vertical
    cheek_left_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0)) # Line 1
    cheek_left_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))   # Line 2
    cheek_left_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))   # Line 3
    cheek_left_sketch.addConstraint(Sketcher.Constraint("Horizontal", 4, 0)) # Line 4
    
    # Pad Left Cheek
    pad_left = body.newObject("PartDesign::Pad", "Pad_CheekLeft")
    pad_left.Profile = cheek_left_sketch
    pad_left.Length = thickness
    pad_left.MidPlane = False
    pad_left.Reverse = False
    
    # Right Cheek (Positive X)
    # Symmetric. Sketch on YZ plane at x = +offset.
    # Rotation: -90 deg around Y (or 270) to align Z with Local Y and Y with Local X?
    # If we rotate -90 around Y: Global Z -> Local -Y. Global Y -> Local X.
    # We want Z to be Up (Local Y). So we need +90 around Y?
    # Wait, for the right cheek, the "inner face" is at x = +offset.
    # The profile is the same, just mirrored?
    # No, the profile is in the YZ plane. The geometry is identical.
    # Placement: Vector(+offset, 0, 0).
    # Rotation: 90 deg around Y.
    
    cheek_right_sketch = create_sketch("CheekRightSketch", "YZ_Plane", 
                                        App.Placement(App.Vector(offset, 0, 0), App.Rotation(0, 1, 0, 90)))
    
    # Copy geometry
    cheek_right_sketch.addGeometry(Part.LineSegment(App.Vector(0, base_z, 0), App.Vector(p_start.Y, base_z, 0)))
    cheek_right_sketch.addGeometry(Part.LineSegment(App.Vector(p_start.Y, base_z, 0), App.Vector(p_start.Y, p_start.Z, 0)))
    cheek_right_sketch.addGeometry(Part.Arc(App.Vector(0, axis_y, axis_z), App.Vector(0, 0, 1), arc_r, arc_start, arc_end))
    cheek_right_sketch.addGeometry(Part.LineSegment(App.Vector(p_end.Y, p_end.Z, 0), App.Vector(p_end.Y, base_z, 0)))
    cheek_right_sketch.addGeometry(Part.LineSegment(App.Vector(p_end.Y, base_z, 0), App.Vector(0, base_z, 0)))
    
    # Constraints
    c1 = cheek_right_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    c2 = cheek_right_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    c3 = cheek_right_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    c4 = cheek_right_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    cheek_right_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    cheek_right_sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 0))
    cheek_right_sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 0))
    cheek_right_sketch.addConstraint(Sketcher.Constraint("Horizontal", 4, 0))
    
    pad_right = body.newObject("PartDesign::Pad", "Pad_CheekRight")
    pad_right.Profile = cheek_right_sketch
    pad_right.Length = thickness
    pad_right.MidPlane = False
    pad_right.Reverse = False
    
    # 3. Small Bosses
    # Two bosses, symmetric about X=0.
    # Axis parallel to Y at Z = axis_z.
    # Seed at x = seed_x.
    # Start inset from front (Y=0) by inset.
    # Extend depth towards +Y.
    
    seed_x = params["small_boss_seed_center_x"]
    inset = params["small_boss_start_inset_from_front"]
    depth = params["small_boss_depth"]
    d_in = params["small_boss_inner_diameter"]
    d_out = params["small_boss_outer_diameter"]
    
    # Boss 1 (Left)
    boss1_sketch = create_sketch("Boss1Sketch", "XY_Plane", App.Placement(App.Vector(-seed_x, 0, 0)))
    # Profile: Circle centered at (0, inset) with radius d_out/2?
    # "start it ... from the rear base edge" -> Y = inset.
    # "extend it ... toward positive Y" -> The boss is a cylinder along Y?
    # "axes parallel to Y" -> Yes, cylinder axis is Y.
    # So the profile is a circle in the XZ plane?
    # Wait, if the axis is Y, the cross-section is in the XZ plane.
    # But we are sketching on XY plane?
    # If we sketch on XY plane, the extrusion direction is Z.
    # We need the boss to be along Y.
    # So we should sketch on XZ plane.
    
    boss1_sketch = create_sketch("Boss1Sketch", "XZ_Plane", App.Placement(App.Vector(-seed_x, 0, 0)))
    # Rotation: 90 deg around X?
    # XZ plane normal is Y.
    # We want to sketch in XZ.
    # Placement: Vector(-seed_x, 0, 0).
    # Rotation: 90 deg around X maps Global Z to Local Y (Up) and Global Y to Local -X?
    # Let's use explicit vectors.
    
    # Profile: Circle in XZ plane.
    # Center: (X=0, Z=inset).
    # Radius: d_out/2.
    # Hole: Radius: d_in/2.
    
    # Let's use a sketch on XZ plane.
    # Center of circle: (0, inset) in XZ coords.
    # X axis is global X. Z axis is global Z.
    # So Center = App.Vector(0, 0, inset).
    # Radius = d_out/2.
    
    boss1_sketch.addGeometry(Part.Circle(App.Vector(0, 0, inset), App.Vector(0, 0, 1), d_out/2))
    boss1_sketch.addGeometry(Part.Circle(App.Vector(0, 0, inset), App.Vector(0, 0, 1), d_in/2))
    
    # Constraints
    boss1_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Center at origin of sketch
    boss1_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0)) # Circle center on X axis? No, center is (0, inset).
    # We need to constrain the center to (0, inset).
    # Let's use a point and distance.
    # Actually, simpler: Center the circle at (0,0) and offset the sketch?
    # No, let's just constrain the center point.
    # Add a point at (0,0) and (0, inset)?
    # Let's use the "Center" constraint on the circle relative to the origin?
    # The circle center is (0,0) in sketch coords.
    # We want it at (0, inset) in global XZ.
    # So we need to offset the sketch placement?
    # Placement: Vector(-seed_x, 0, 0).
    # If we rotate the sketch 90 deg around X, the local Z becomes global Y? No.
    # Let's just use the sketch on XZ plane with no rotation (Normal Y).
    # Then the circle center is at (0,0) in XZ.
    # We want it at (0, inset) in XZ.
    # So we add a point at (0, inset) and constrain the circle center to it.
    
    p_center = boss1_sketch.addGeometry(Part.Point(App.Vector(0, 0, inset)))
    boss1_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0)) # Circle center
    boss1_sketch.addConstraint(Sketcher.Constraint("Point", 0, 0, 0, 0)) # Circle center coincident with point
    boss1_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0)) # Circle center on X axis? No.
    # The circle center is (0, inset).
    # We need to constrain the center to be on the line X=0, Z=inset.
    # Let's just use the point constraint.
    
    # Pad Boss 1
    pad_boss1 = body.newObject("PartDesign::Pad", "Pad_Boss1")
    pad_boss1.Profile = boss1_sketch
    pad_boss1.Length = depth
    pad_boss1.MidPlane = False
    pad_boss1.Reverse = False
    
    # Boss 2 (Right)
    boss2_sketch = create_sketch("Boss2Sketch", "XZ_Plane", App.Placement(App.Vector(seed_x, 0, 0)))
    boss2_sketch.addGeometry(Part.Circle(App.Vector(0, 0, inset), App.Vector(0, 0, 1), d_out/2))
    boss2_sketch.addGeometry(Part.Circle(App.Vector(0, 0, inset), App.Vector(0, 0, 1), d_in/2))
    p_center2 = boss2_sketch.addGeometry(Part.Point(App.Vector(0, 0, inset)))
    boss2_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    boss2_sketch.addConstraint(Sketcher.Constraint("Point", 0, 0, 0, 0))
    
    pad_boss2 = body.newObject("PartDesign::Pad", "Pad_Boss2")
    pad_boss2.Profile = boss2_sketch
    pad_boss2.Length = depth
    pad_boss2.MidPlane = False
    pad_boss2.Reverse = False
    
    # 4. Mounting Holes
    # Two holes, symmetric in X.
    # Center at Y = W/2 (front edge)?
    # "mounting_hole_end_offset_x from its nearest base end"
    # Nearest base end for the hole?
    # "along Z on the base-width centerline" -> Y = W/2.
    # "symmetric in X" -> X = +/- offset_x.
    # "each center mounting_hole_end_offset_x from its nearest base end"
    # Nearest base end for the hole center?
    # If the hole is at X = +offset_x, the nearest base end is X = L/2.
    # So L/2 - offset_x = hole_x?
    # Or is the hole at X = offset_x from the end?
    # "center ... from its nearest base end" -> Distance from end to center is offset_x.
    # So Hole X = L/2 - offset_x.
    
    hole_x = params["bracket_base_length"]/2 - params["mounting_hole_end_offset_x"]
    hole_y = params["bracket_base_width"]/2
    hole_z = 0 # Center on base? Or through the plate?
    # "through holes along Z" -> Through the plate.
    # Center Z = 0 (mid-plane of plate)? Or on the surface?
    # Usually through holes are centered on the thickness.
    # But the sketch is on XY plane, so Z=0 is the center of the plate.
    
    hole_d = params["mounting_hole_diameter"]
    
    hole1_sketch = create_sketch("Hole1Sketch", "XY_Plane", App.Placement(App.Vector(hole_x, 0, 0)))
    hole1_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hole_d/2))
    hole1_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    hole1_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    hole1_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    
    hole2_sketch = create_sketch("Hole2Sketch", "XY_Plane", App.Placement(App.Vector(-hole_x, 0, 0)))
    hole2_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hole_d/2))
    hole2_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    hole2_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
    hole2_sketch.addConstraint(Sketcher.Constraint("Vertical", 0, 0))
    
    pocket1 = body.newObject("PartDesign::Pocket", "Pocket_Hole1")
    pocket1.Profile = hole1_sketch
    pocket1.Type = "ThroughAll"
    
    pocket2 = body.newObject("PartDesign::Pocket", "Pocket_Hole2")
    pocket2.Profile = hole2_sketch
    pocket2.Type = "ThroughAll"
    
    doc.recompute()
    
    return doc

def main():
    script_path = Path(__file__).resolve()
    stem = script_path.stem
    
    # Step 1: Create Base
    doc_base = create_model(PARAMS_BASE)
    doc_base.saveAs(str(script_path.with_suffix("_base.FCStd")))
    
    # Step 2: Create Edit
    doc_edit = create_model(PARAMS_EDIT)
    doc_edit.saveAs(str(script_path.with_suffix("_edit.FCStd")))

if __name__ == "__main__":
    main()
