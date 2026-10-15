import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from __file__
script_path = Path(__file__).resolve()
base_filename = script_path.stem + "_base.FCStd"
edit_filename = script_path.stem + "_edit.FCStd"

# Base Part Parameters
params_base = {
    "plate_width": 70.0,
    "plate_height": 12.0,
    "plate_thickness": 40.0,
    "clevis_slot_width": 17.5,
    "clevis_slot_depth": 2.4,
    "pin_hole_diameter": 12.0,
    "pin_boss_arc_radius": 12.0,
    "pin_boss_height": 22.0,
    "pin_boss_base_width": 27.84,
    "pin_boss_depth": 28.0,
    "bolt_hole_diameter": 15.0,
    "number_of_bolt_holes": 4,
    "bolt_hole_horizontal_spacing": 50.0,
    "bolt_hole_vertical_spacing": 20.0,
    "bolt_hole_counterbore_depth": 1.0,
}

# Edit Part Parameters (Target)
params_edit = {
    "bolt_hole_through_diameter": 9.0,
    "clevis_arm_relief_width": 8.0,
    "clevis_arm_relief_pocket_depth": 3.5,
    "clevis_arm_pad_width": 8.0,
    "clevis_arm_pad_depth": 3.5,
    "clevis_arm_pad_depth_offset": 6.0,
}

def create_feature_tree(params):
    """
    Creates a PartDesign Body with all features based on the provided parameters dict.
    Returns the document object.
    """
    doc = App.newDocument("PartDesign_Clevis")
    
    # 1. Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # 2. Parameters (VarSet)
    params_obj = body.newObject("App::VarSet", "Parameters")
    for name, value in params.items():
        params_obj.addProperty("App::PropertyLength", name, "Dimensions", f"{name.replace('_', ' ').title()}")
        setattr(params_obj, name, value)
    
    # 3. Main Plate Sketch (XY Plane)
    sketch_plate = body.newObject("Sketcher::SketchObject", "Sketch_Plate")
    sketch_plate.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_plate.Support = (doc.getObject("XY_Plane"), [""])
    sketch_plate.MapMode = "FlatFace"
    
    # Rectangle
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-params["plate_width"]/2, -params["plate_height"]/2, 0), 
                                              App.Vector(params["plate_width"]/2, -params["plate_height"]/2, 0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(params["plate_width"]/2, -params["plate_height"]/2, 0), 
                                              App.Vector(params["plate_width"]/2, params["plate_height"]/2, 0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(params["plate_width"]/2, params["plate_height"]/2, 0), 
                                              App.Vector(-params["plate_width"]/2, params["plate_height"]/2, 0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-params["plate_width"]/2, params["plate_height"]/2, 0), 
                                              App.Vector(-params["plate_width"]/2, -params["plate_height"]/2, 0)), False)
    
    # Constraints
    sketch_plate.addConstraint(Sketcher.Constraint("Axis", 0, 1, 1, 2)) # Horizontal
    sketch_plate.addConstraint(Sketcher.Constraint("Axis", 1, 2, 1, 3)) # Vertical
    sketch_plate.addConstraint(Sketcher.Constraint("Size", 0, "Parameters.plate_width"))
    sketch_plate.addConstraint(Sketcher.Constraint("Size", 1, "Parameters.plate_height"))
    sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center X
    sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # Center Y
    
    # 4. Pad Plate
    pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
    pad_plate.Profile = sketch_plate
    pad_plate.Length = params["plate_thickness"]
    pad_plate.Type = "Solid"
    
    # 5. Clevis Slot Sketch (XY Plane, offset Z)
    sketch_clevis = body.newObject("Sketcher::SketchObject", "Sketch_Clevis")
    sketch_clevis.Placement = App.Placement(App.Vector(0, 0, params["plate_thickness"]))
    sketch_clevis.Support = (doc.getObject("XY_Plane"), [""])
    sketch_clevis.MapMode = "FlatFace"
    
    # Rectangle for slot
    sketch_clevis.addGeometry(Part.LineSegment(App.Vector(-params["clevis_slot_width"]/2, -params["plate_height"]/2, 0), 
                                               App.Vector(params["clevis_slot_width"]/2, -params["plate_height"]/2, 0)), False)
    sketch_clevis.addGeometry(Part.LineSegment(App.Vector(params["clevis_slot_width"]/2, -params["plate_height"]/2, 0), 
                                               App.Vector(params["clevis_slot_width"]/2, params["plate_height"]/2, 0)), False)
    sketch_clevis.addGeometry(Part.LineSegment(App.Vector(params["clevis_slot_width"]/2, params["plate_height"]/2, 0), 
                                               App.Vector(-params["clevis_slot_width"]/2, params["plate_height"]/2, 0)), False)
    sketch_clevis.addGeometry(Part.LineSegment(App.Vector(-params["clevis_slot_width"]/2, params["plate_height"]/2, 0), 
                                               App.Vector(-params["clevis_slot_width"]/2, -params["plate_height"]/2, 0)), False)
    
    # Constraints
    sketch_clevis.addConstraint(Sketcher.Constraint("Axis", 0, 1, 1, 2))
    sketch_clevis.addConstraint(Sketcher.Constraint("Axis", 1, 2, 1, 3))
    sketch_clevis.addConstraint(Sketcher.Constraint("Size", 0, "Parameters.clevis_slot_width"))
    sketch_clevis.addConstraint(Sketcher.Constraint("Size", 1, "Parameters.plate_height"))
    sketch_clevis.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
    sketch_clevis.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
    
    # 6. Pocket Clevis
    pocket_clevis = body.newObject("PartDesign::Pocket", "Pocket_Clevis")
    pocket_clevis.Profile = sketch_clevis
    pocket_clevis.Length = params["clevis_slot_depth"]
    pocket_clevis.Type = "Blind"
    
    # 7. Pin Boss Sketch (XY Plane, offset Z)
    sketch_boss = body.newObject("Sketcher::SketchObject", "Sketch_Boss")
    sketch_boss.Placement = App.Placement(App.Vector(0, 0, params["plate_thickness"]))
    sketch_boss.Support = (doc.getObject("XY_Plane"), [""])
    sketch_boss.MapMode = "FlatFace"
    
    # Outer Arc
    sketch_boss.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params["pin_boss_arc_radius"]), False)
    
    # Inner Circle (Pin Hole)
    sketch_boss.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params["pin_hole_diameter"]/2), False)
    
    # Constraints
    sketch_boss.addConstraint(Sketcher.Constraint("Center", 0, 1))
    sketch_boss.addConstraint(Sketcher.Constraint("Radius", 0, "Parameters.pin_boss_arc_radius"))
    sketch_boss.addConstraint(Sketcher.Constraint("Radius", 1, "Parameters.pin_hole_diameter"))
    sketch_boss.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Center on origin
    
    # 8. Pad Boss
    pad_boss = body.newObject("PartDesign::Pad", "Pad_Boss")
    pad_boss.Profile = sketch_boss
    pad_boss.Length = params["pin_boss_height"]
    pad_boss.Type = "Solid"
    
    # 9. Pocket Boss Hole
    pocket_boss = body.newObject("PartDesign::Pocket", "Pocket_Boss_Hole")
    pocket_boss.Profile = sketch_boss
    pocket_boss.Length = params["pin_boss_depth"]
    pocket_boss.Type = "Blind"
    # Note: The sketch has the hole defined. We need to ensure the pocket removes it.
    # Since the sketch has the hole, the pocket will remove the material inside the circle.
    # However, the boss pad adds material. The pocket removes it.
    # To get a through hole, we usually define the hole in the sketch and use a ThroughAll pocket 
    # OR define the hole in a separate sketch. 
    # Given the instruction "centered rounded pin boss with a coaxial pin passage", 
    # and the sketch has the hole, a ThroughAll pocket on the boss profile will work if the boss is tall enough.
    # But the boss height is 22, depth is 28. The pocket needs to go through the boss.
    # Let's make the pocket ThroughAll relative to the boss height? No, standard is ThroughAll or Blind.
    # Let's use ThroughAll for the hole to ensure it goes all the way through the boss.
    pocket_boss.Length = 1000 # Large enough to be ThroughAll
    pocket_boss.Type = "ThroughAll"
    
    # 10. Bolt Holes Sketch (XY Plane, offset Z)
    sketch_bolts = body.newObject("Sketcher::SketchObject", "Sketch_Bolts")
    sketch_bolts.Placement = App.Placement(App.Vector(0, 0, params["plate_thickness"]))
    sketch_bolts.Support = (doc.getObject("XY_Plane"), [""])
    sketch_bolts.MapMode = "FlatFace"
    
    # Calculate positions
    spacing_x = params["bolt_hole_horizontal_spacing"]
    spacing_y = params["bolt_hole_vertical_spacing"]
    offset_x = spacing_x / 2
    offset_y = spacing_y / 2
    
    # We need 4 holes. Let's create a sketch with 4 circles.
    # To make it editable, we can add 4 circles and constrain them.
    # Or simpler: Add 4 circles and constrain them to be symmetric.
    
    # Circle 1
    c1 = Part.Circle(App.Vector(-offset_x, -offset_y, 0), App.Vector(0, 0, 1), params["bolt_hole_diameter"]/2)
    sketch_bolts.addGeometry(c1, False)
    # Circle 2
    c2 = Part.Circle(App.Vector(offset_x, -offset_y, 0), App.Vector(0, 0, 1), params["bolt_hole_diameter"]/2)
    sketch_bolts.addGeometry(c2, False)
    # Circle 3
    c3 = Part.Circle(App.Vector(-offset_x, offset_y, 0), App.Vector(0, 0, 1), params["bolt_hole_diameter"]/2)
    sketch_bolts.addGeometry(c3, False)
    # Circle 4
    c4 = Part.Circle(App.Vector(offset_x, offset_y, 0), App.Vector(0, 0, 1), params["bolt_hole_diameter"]/2)
    sketch_bolts.addGeometry(c4, False)
    
    # Constraints
    # Center all on origin
    sketch_bolts.addConstraint(Sketcher.Constraint("Center", 0, 1))
    sketch_bolts.addConstraint(Sketcher.Constraint("Center", 1, 2))
    sketch_bolts.addConstraint(Sketcher.Constraint("Center", 2, 3))
    sketch_bolts.addConstraint(Sketcher.Constraint("Center", 3, 4))
    
    # Radii
    sketch_bolts.addConstraint(Sketcher.Constraint("Radius", 0, "Parameters.bolt_hole_diameter"))
    sketch_bolts.addConstraint(Sketcher.Constraint("Radius", 1, "Parameters.bolt_hole_diameter"))
    sketch_bolts.addConstraint(Sketcher.Constraint("Radius", 2, "Parameters.bolt_hole_diameter"))
    sketch_bolts.addConstraint(Sketcher.Constraint("Radius", 3, "Parameters.bolt_hole_diameter"))
    
    # Symmetry
    sketch_bolts.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 2, 3)) # X symmetry
    sketch_bolts.addConstraint(Sketcher.Constraint("Symmetry", 0, 2, 1, 3)) # Y symmetry
    
    # 11. Pockets for Bolt Holes
    # We need to subtract these. Since they are on the same sketch, we can use a single Pocket feature 
    # if we select all circles, or multiple. Let's do one pocket with all circles.
    pocket_bolts = body.newObject("PartDesign::Pocket", "Pocket_Bolts")
    pocket_bolts.Profile = sketch_bolts
    pocket_bolts.Length = params["bolt_hole_counterbore_depth"]
    pocket_bolts.Type = "Blind"
    
    # 12. Counterbores Sketch (XY Plane, offset Z)
    sketch_counterbores = body.newObject("Sketcher::SketchObject", "Sketch_Counterbores")
    sketch_counterbores.Placement = App.Placement(App.Vector(0, 0, params["plate_thickness"]))
    sketch_counterbores.Support = (doc.getObject("XY_Plane"), [""])
    sketch_counterbores.MapMode = "FlatFace"
    
    # Add 4 larger circles for counterbores
    for i in range(4):
        cx = [-offset_x, offset_x, -offset_x, offset_x][i]
        cy = [-offset_y, -offset_y, offset_y, offset_y][i]
        c = Part.Circle(App.Vector(cx, cy, 0), App.Vector(0, 0, 1), params["bolt_hole_diameter"]/2)
        sketch_counterbores.addGeometry(c, False)
        
    # Constraints (same as bolts)
    sketch_counterbores.addConstraint(Sketcher.Constraint("Center", 0, 1))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Center", 1, 2))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Center", 2, 3))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Center", 3, 4))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Radius", 0, "Parameters.bolt_hole_diameter"))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Radius", 1, "Parameters.bolt_hole_diameter"))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Radius", 2, "Parameters.bolt_hole_diameter"))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Radius", 3, "Parameters.bolt_hole_diameter"))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Symmetry", 0, 1, 2, 3))
    sketch_counterbores.addConstraint(Sketcher.Constraint("Symmetry", 0, 2, 1, 3))
    
    # 13. Pockets for Counterbores
    pocket_counterbores = body.newObject("PartDesign::Pocket", "Pocket_Counterbores")
    pocket_counterbores.Profile = sketch_counterbores
    pocket_counterbores.Length = params["bolt_hole_counterbore_depth"]
    pocket_counterbores.Type = "Blind"
    
    # 14. Arm Relief Sketch (XY Plane, offset Z)
    sketch_arms = body.newObject("Sketcher::SketchObject", "Sketch_Arms")
    sketch_arms.Placement = App.Placement(App.Vector(0, 0, params["plate_thickness"]))
    sketch_arms.Support = (doc.getObject("XY_Plane"), [""])
    sketch_arms.MapMode = "FlatFace"
    
    # Define geometry for one arm relief
    # Spans full pin_boss_base_width along X.
    # Depth direction (Y) is clevis_arm_relief_width.
    # Inner edge offset from mid-plane (Y=0) is clevis_arm_pad_depth_offset.
    # Outer edge flush with pin-boss depth faces? 
    # Pin boss depth is 28. Plate thickness is 40. 
    # The boss is centered on the plate? 
    # "centered rounded pin boss". Usually centered on the plate.
    # Boss base width 27.84. Plate width 70.
    # Boss is centered at X=0.
    # Relief spans full pin_boss_base_width along X -> X from -13.92 to +13.92.
    # Depth direction (Y): 
    # Inner edge offset from mid-plane (Y=0) is clevis_arm_pad_depth_offset (6.0).
    # So inner edge is at Y = 6.0.
    # Width is clevis_arm_relief_width (8.0).
