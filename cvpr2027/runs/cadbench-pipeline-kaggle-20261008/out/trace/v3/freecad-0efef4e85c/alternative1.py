import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Determine paths based on script location
script_path = Path(__file__).resolve()
script_stem = script_path.stem
base_path = script_path.parent / f"{script_stem}_base.FCStd"
edit_path = script_path.parent / f"{script_stem}_edit.FCStd"

# Helper to create a new document and body
def create_base_document():
    doc = App.newDocument("ClevisBase")
    body = doc.addObject("PartDesign::Body", "Body")
    return doc, body

def create_edit_document(base_doc):
    # Clone the document to start from the base state
    doc = App.newDocument("ClevisEdit")
    # Copy body object
    body = doc.addObject("PartDesign::Body", "Body")
    # Copy parameters from base if they exist, or define them manually
    # Since we rebuild the tree, we just need to ensure parameters match the base first
    # Then we will modify specific features for the edit.
    return doc, body

def build_base_model(doc, body):
    # 1. Parameters
    p = body.newObject("App::VarSet", "Parameters")
    p.addProperty("App::PropertyLength", "plate_width", "Dimensions", "70.0")
    p.addProperty("App::PropertyLength", "plate_height", "Dimensions", "12.0")
    p.addProperty("App::PropertyLength", "plate_thickness", "Dimensions", "40.0")
    p.addProperty("App::PropertyLength", "clevis_slot_width", "Dimensions", "17.5")
    p.addProperty("App::PropertyLength", "clevis_slot_depth", "Dimensions", "2.4")
    p.addProperty("App::PropertyLength", "pin_hole_diameter", "Dimensions", "12.0")
    p.addProperty("App::PropertyLength", "pin_boss_arc_radius", "Dimensions", "12.0")
    p.addProperty("App::PropertyLength", "pin_boss_height", "Dimensions", "22.0")
    p.addProperty("App::PropertyLength", "pin_boss_base_width", "Dimensions", "27.84")
    p.addProperty("App::PropertyLength", "pin_boss_depth", "Dimensions", "28.0")
    p.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "15.0")
    p.addProperty("App::PropertyLength", "bolt_hole_through_diameter", "Dimensions", "15.0") # Base default matches diameter for no through hole
    p.addProperty("App::PropertyInteger", "number_of_bolt_holes", "Dimensions", "4")
    p.addProperty("App::PropertyLength", "bolt_hole_horizontal_spacing", "Dimensions", "50.0")
    p.addProperty("App::PropertyLength", "bolt_hole_vertical_spacing", "Dimensions", "20.0")
    p.addProperty("App::PropertyLength", "bolt_hole_counterbore_depth", "Dimensions", "1.0")

    # 2. Main Plate (Pad)
    sketch_plate = body.newObject("Sketcher::SketchObject", "SketchPlate")
    sketch_plate.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0)) # XY plane
    sketch_plate.BaseObject = None
    sketch_plate.BaseEntity = None
    sketch_plate.TechDraw_ProtectedView = 1
    sketch_plate.Appnd = False
    sketch_plate.AddGeometryToConstraint = True
    
    # Define points for rectangle: Center (0,0), width, height
    # X from -W/2 to W/2, Y from -H/2 to H/2
    w = p.plate_width.Value
    h = p.plate_height.Value
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-w/2, -h/2, 0), App.Vector(w/2, -h/2, 0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(w/2, -h/2, 0), App.Vector(w/2, h/2, 0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(w/2, h/2, 0), App.Vector(-w/2, h/2, 0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-w/2, h/2, 0), App.Vector(-w/2, -h/2, 0)), False)
    
    # Constraints
    sketch_plate.addConstraint(Sketcher.Constraint("Axis", 0, "X"), False)
    sketch_plate.addConstraint(Sketcher.Constraint("Axis", 1, "Y"), False)
    sketch_plate.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    sketch_plate.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, w/2), False)
    sketch_plate.addConstraint(Sketcher.Constraint("DistanceY", 1, 2, h/2), False)
    sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 0, 1), False)
    sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 1), False)
    
    pad_plate = body.newObject("PartDesign::Pad", "PadPlate")
    pad_plate.Profile = sketch_plate
    pad_plate.Length = p.plate_thickness.Value
    pad_plate.Direction = "ZPlus"

    # 3. Clevis Slot (Pocket on bottom face)
    sketch_slot = body.newObject("Sketcher::SketchObject", "SketchSlot")
    sketch_slot.Placement = App.Placement(App.Vector(0, 0, -p.plate_thickness.Value/2), App.Rotation(0, 0, 0))
    sketch_slot.BaseObject = None
    
    ws = p.clevis_slot_width.Value
    sd = p.clevis_slot_depth.Value
    sketch_slot.addGeometry(Part.LineSegment(App.Vector(-ws/2, 0, 0), App.Vector(ws/2, 0, 0)), False)
    sketch_slot.addConstraint(Sketcher.Constraint("Axis", 0, "X"), False)
    sketch_slot.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    sketch_slot.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, ws/2), False)
    
    pocket_slot = body.newObject("PartDesign::Pocket", "PocketSlot")
    pocket_slot.Profile = sketch_slot
    pocket_slot.Length = sd
    pocket_slot.Type = "Blind"
    pocket_slot.Direction = "ZMinus"

    # 4. Pin Boss (Pad)
    sketch_boss_profile = body.newObject("Sketcher::SketchObject", "SketchBossProfile")
    sketch_boss_profile.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_boss_profile.BaseObject = None
    # Boss base width x height
    pbw = p.pin_boss_base_width.Value
    pbh = p.pin_boss_height.Value
    sketch_boss_profile.addGeometry(Part.LineSegment(App.Vector(-pbw/2, 0, 0), App.Vector(pbw/2, 0, 0)), False)
    sketch_boss_profile.addGeometry(Part.LineSegment(App.Vector(pbw/2, 0, 0), App.Vector(pbw/2, pbh, 0)), False)
    sketch_boss_profile.addGeometry(Part.LineSegment(App.Vector(pbw/2, pbh, 0), App.Vector(-pbw/2, pbh, 0)), False)
    sketch_boss_profile.addGeometry(Part.LineSegment(App.Vector(-pbw/2, pbh, 0), App.Vector(-pbw/2, 0, 0)), False)
    sketch_boss_profile.addConstraint(Sketcher.Constraint("Axis", 0, "X"), False)
    sketch_boss_profile.addConstraint(Sketcher.Constraint("Axis", 1, "Y"), False)
    sketch_boss_profile.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    sketch_boss_profile.addConstraint(Sketcher.Constraint("DistanceX", 0, 2, pbw/2), False)
    sketch_boss_profile.addConstraint(Sketcher.Constraint("DistanceY", 1, 2, pbh), False)
    sketch_boss_profile.addConstraint(Sketcher.Constraint("Horizontal", 0, 1), False)
    sketch_boss_profile.addConstraint(Sketcher.Constraint("Vertical", 0, 1), False)

    pad_boss = body.newObject("PartDesign::Pad", "PadBoss")
    pad_boss.Profile = sketch_boss_profile
    pad_boss.Length = p.pin_boss_depth.Value
    pad_boss.Direction = "ZPlus"

    # Pin Hole (Pocket through boss)
    sketch_pin_hole = body.newObject("Sketcher::SketchObject", "SketchPinHole")
    sketch_pin_hole.Placement = App.Placement(App.Vector(0, 0, p.pin_boss_height.Value), App.Rotation(0, 0, 0))
    sketch_pin_hole.BaseObject = None
    phd = p.pin_hole_diameter.Value / 2
    sketch_pin_hole.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), phd), False)
    sketch_pin_hole.addConstraint(Sketcher.Constraint("Radius", 0, phd), False)
    sketch_pin_hole.addConstraint(Sketcher.Constraint("Center", 0, 0), False)
    
    pocket_pin = body.newObject("PartDesign::Pocket", "PocketPin")
    pocket_pin.Profile = sketch_pin_hole
    pocket_pin.Type = "ThroughAll" # Through the boss
    pocket_pin.Direction = "ZPlus"

    # 5. Bolt Holes (Pattern of Pockets)
    # Grid: X from -W/2 to W/2, Y from -H/2 to H/2
    bh_d = p.bolt_hole_diameter.Value / 2
    bh_cbd = p.bolt_hole_counterbore_depth.Value
    
    # Counterbore Sketch (XY plane, centered)
    sketch_cb = body.newObject("Sketcher::SketchObject", "SketchCB")
    sketch_cb.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_cb.BaseObject = None
    cb_d = p.bolt_hole_diameter.Value / 2
    cb_h = bh_cbd.Value
    # Outer circle
    sketch_cb.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), p.bolt_hole_diameter.Value/2), False)
    # Inner hole circle
    sketch_cb.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bh_d), False)
    sketch_cb.addConstraint(Sketcher.Constraint("Radius", 0, p.bolt_hole_diameter.Value/2), False)
    sketch_cb.addConstraint(Sketcher.Constraint("Radius", 1, bh_d), False)
    sketch_cb.addConstraint(Sketcher.Constraint("Concentric", 0, 1), False)
    sketch_cb.addConstraint(Sketcher.Constraint("Center", 0, 0), False)

    pocket_cb = body.newObject("PartDesign::Pocket", "PocketCB")
    pocket_cb.Profile = sketch_cb
    pocket_cb.Length = bh_cbd
    pocket_cb.Type = "Blind"
    pocket_cb.Direction = "ZMinus" # Cut from top face

    # Create a pattern of pockets? Or just create the feature once and pattern it?
    # The instruction says "four shallow counterbores". 
    # We need to create the pockets at specific locations.
    # Let's create a sketch for the holes positions.
    sketch_holes = body.newObject("Sketcher::SketchObject", "SketchHoles")
    sketch_holes.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_holes.BaseObject = None
    
    hx = p.bolt_hole_horizontal_spacing.Value / 2
    hy = p.bolt_hole_vertical_spacing.Value / 2
    
    # Points for 4 holes
    p1 = App.Vector(-hx, -hy, 0)
    p2 = App.Vector(hx, -hy, 0)
    p3 = App.Vector(hx, hy, 0)
    p4 = App.Vector(-hx, hy, 0)
    
    sketch_holes.addGeometry(Part.Point(p1), False)
    sketch_holes.addGeometry(Part.Point(p2), False)
    sketch_holes.addGeometry(Part.Point(p3), False)
    sketch_holes.addGeometry(Part.Point(p4), False)
    
    sketch_holes.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 0), False) # Just example constraints to fix points
    sketch_holes.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, hx), False)
    sketch_holes.addConstraint(Sketcher.Constraint("DistanceY", 1, 2, hy), False)
    
    # Actually, simpler: Create the pocket feature, then pattern it.
    # But the pocket feature needs a profile sketch.
    # Let's create one pocket at origin, then polar/linear pattern? 
    # The grid is rectangular. Linear pattern in X, then Y? Or just use a Sketcher pattern if available? 
    # Standard approach: Create one pocket, then use PartDesign::PolarPattern if circular, 
    # but for rectangular grid, we might need to manually place or use a linear pattern twice.
    # However, FreeCAD PartDesign::LinearPattern can do offsets.
    
    # Let's create the pocket feature manually first at origin? No, we need 4.
    # Let's create a sketch defining the hole geometry at the origin, then pattern it? 
    # No, the pocket feature is the one that gets patterned.
    # Let's create a sketch for the hole shape at (0,0,0).
    sketch_hole_shape = body.newObject("Sketcher::SketchObject", "SketchHoleShape")
    sketch_hole_shape.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
    sketch_hole_shape.BaseObject = None
    sketch_hole_shape.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bh_d), False)
    sketch_hole_shape.addConstraint(Sketcher.Constraint("Radius", 0, bh_d), False)
    
    pocket_hole = body.newObject("PartDesign::Pocket", "PocketHole")
    pocket_hole.Profile = sketch_hole_shape
    pocket_hole.Length = bh_cbd
    pocket_hole.Type = "Blind"
    pocket_hole.Direction = "ZMinus"
    pocket_hole.Placement = App.Placement(p1, App.Rotation(0,0,0)) # Place at first point
    
    # Now pattern this pocket? 
    # PartDesign::LinearPattern copies the selected feature.
    # Let's create a LinearPattern for X direction.
    # But we have 4 holes. 
    # Strategy: Create one pocket at center? No, grid is around center.
    # Let's create a sketch of 4 points, and use a "Pattern" feature in Sketcher? No.
    # Let's create a LinearPattern from the origin pocket to the other points.
    # Actually, let's just create 4 pockets using a LinearPattern logic manually or use the Sketcher pattern if possible.
    # Standard way: Create one feature, select it, add LinearPattern, set Offset to (-hx, hy) etc.
    # Since we can't interactively select, we script the pattern creation.
    
    # Create a pocket at the center? No, the pattern must be relative.
    # Let's create a pocket at (0,0). Then pattern it to (-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy).
    # But the pocket at (0,0) is not desired.
    # Alternative: Create a sketch of 4 circles? No, PartDesign Pocket takes one profile.
    # Alternative: Create a LinearPattern with 4 instances.
    # We can define the pattern along X then Y? 
    # Let's create a pocket at the center, then pattern it to the 4 corners.
    # Then we will have 5 holes. We need to delete the center one? Or pattern differently.
    
    # Better: Create a LinearPattern that places 4 instances.
    # We need to specify the original feature.
    # Let's create a pocket at (0,0) first, then pattern it to 3 others, then move the original?
    # No, let's create a pocket at (-hx, -hy). Then pattern it to the other 3.
    
    # Let's create a pocket at (-hx, -hy).
    pocket_hole_1 = body.newObject("PartDesign::Pocket", "PocketHole1")
    pocket_hole_1.Profile = sketch_hole_shape
    pocket_hole_1.Length = bh_cbd
    pocket_hole_1.Type = "Blind"
    pocket_hole_1.Direction = "ZMinus"
    pocket_hole_1.Placement = App.Placement(p1, App.Rotation(0,0,0))

    # Now create a LinearPattern from PocketHole1 to the other 3 points.
    # LinearPattern: Direction X, Offset X=2*hx, Occurrences=3? 
    # Then another LinearPattern? 
    # FreeCAD LinearPattern can do offsets in both X and Y.
    # Let's try to create a LinearPattern with offsets: 
    # Instance 1: (0,0) relative
