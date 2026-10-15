import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

def create_document():
    """Creates a new FreeCAD document with a PartDesign Body."""
    doc = App.newDocument("CameraMountBase")
    
    # Create the Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create Parameters for easy editing
    params = body.newObject("App::VarSet", "Parameters")
    
    # Base Parameters
    params.addProperty("App::PropertyLength", "base_side_length", "Dimensions", "Base square side")
    params.base_side_length = 60.0
    
    params.addProperty("App::PropertyLength", "base_extrusion_depth", "Dimensions", "Base depth")
    params.base_extrusion_depth = 80.0
    
    params.addProperty("App::PropertyInteger", "base_pattern_element_count", "Dimensions", "Mounting holes count")
    params.base_pattern_element_count = 4
    
    # Slot Parameters
    params.addProperty("App::PropertyLength", "slot_cutout_overall_width", "Dimensions", "Slot overall width")
    params.slot_cutout_overall_width = 52.0
    
    params.addProperty("App::PropertyLength", "slot_cutout_central_tab_width", "Dimensions", "Slot tab width")
    params.slot_cutout_central_tab_width = 10.0
    
    params.addProperty("App::PropertyLength", "slot_cutout_ledge_height", "Dimensions", "Slot ledge height")
    params.slot_cutout_ledge_height = 3.5
    
    params.addProperty("App::PropertyLength", "slot_cutout_central_tab_height", "Dimensions", "Slot tab height")
    params.slot_cutout_central_tab_height = 6.0
    
    params.addProperty("App::PropertyLength", "slot_cutout_depth", "Dimensions", "Slot depth")
    params.slot_cutout_depth = 55.0
    
    # Mounting Hole Parameters
    params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "Hole diameter")
    params.mounting_hole_diameter = 6.66
    
    params.addProperty("App::PropertyLength", "mounting_hole_horizontal_spacing", "Dimensions", "Hole X spacing")
    params.mounting_hole_horizontal_spacing = 35.0
    
    params.addProperty("App::PropertyLength", "mounting_hole_vertical_spacing", "Dimensions", "Hole Y spacing")
    params.mounting_hole_vertical_spacing = 30.0
    
    params.addProperty("App::PropertyLength", "mounting_hole_depth", "Dimensions", "Hole depth")
    params.mounting_hole_depth = 25.4
    
    # Pocket Parameters
    params.addProperty("App::PropertyLength", "pocket_cutout_length", "Dimensions", "Pocket length")
    params.pocket_cutout_length = 21.0
    
    params.addProperty("App::PropertyLength", "pocket_cutout_width", "Dimensions", "Pocket width")
    params.pocket_cutout_width = 25.0
    
    params.addProperty("App::PropertyInteger", "number_of_pocket_cutouts", "Dimensions", "Number of pockets")
    params.number_of_pocket_cutouts = 2
    
    params.addProperty("App::PropertyLength", "pocket_cutout_depth", "Dimensions", "Pocket depth")
    params.pocket_cutout_depth = 45.0
    
    params.addProperty("App::PropertyLength", "pocket_cutout_offset_from_top", "Dimensions", "Pocket offset from top")
    params.pocket_cutout_offset_from_top = 10.0
    
    params.addProperty("App::PropertyLength", "pocket_cutout_vertical_position", "Dimensions", "Pocket Y position")
    params.pocket_cutout_vertical_position = 35.5
    
    # Side Pocket Parameters
    params.addProperty("App::PropertyLength", "side_pocket_length", "Dimensions", "Side pocket length")
    params.side_pocket_length = 25.0
    
    params.addProperty("App::PropertyLength", "side_pocket_width", "Dimensions", "Side pocket width")
    params.side_pocket_width = 20.0
    
    params.addProperty("App::PropertyInteger", "number_of_side_pockets", "Dimensions", "Number of side pockets")
    params.number_of_side_pockets = 2
    
    params.addProperty("App::PropertyLength", "side_pocket_vertical_gap", "Dimensions", "Side pocket gap")
    params.side_pocket_vertical_gap = 10.0
    
    params.addProperty("App::PropertyLength", "side_pocket_depth", "Dimensions", "Side pocket depth")
    params.side_pocket_depth = 102.5
    
    return doc

def build_base_part(doc):
    """Builds the base part geometry."""
    body = doc.getObject("Body")
    params = doc.getObject("Parameters")
    
    # 1. Base Block
    sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
    sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_base.Support = (doc.getObject("XY_Plane"), [""])
    sketch_base.MapMode = "FlatFace"
    
    # Base square
    sketch_base.addGeometry(Part.LineSegment(App.Vector(-params.base_side_length/2, -params.base_side_length/2, 0), App.Vector(params.base_side_length/2, -params.base_side_length/2, 0)), False)
    sketch_base.addGeometry(Part.LineSegment(App.Vector(params.base_side_length/2, -params.base_side_length/2, 0), App.Vector(params.base_side_length/2, params.base_side_length/2, 0)), False)
    sketch_base.addGeometry(Part.LineSegment(App.Vector(params.base_side_length/2, params.base_side_length/2, 0), App.Vector(-params.base_side_length/2, params.base_side_length/2, 0)), False)
    sketch_base.addGeometry(Part.LineSegment(App.Vector(-params.base_side_length/2, params.base_side_length/2, 0), App.Vector(-params.base_side_length/2, -params.base_side_length/2, 0)), False)
    
    # Constraints
    sketch_base.addConstraint(Sketcher.Constraint("Axis", 0, 1, 0, 1, 0, 1)) # Vertical
    sketch_base.addConstraint(Sketcher.Constraint("Axis", 1, 0, 0, 0, 1, 0)) # Horizontal
    sketch_base.addConstraint(Sketcher.Constraint("Length", 0, 1, params.base_side_length))
    sketch_base.addConstraint(Sketcher.Constraint("Length", 1, 2, params.base_side_length))
    sketch_base.addConstraint(Sketcher.Constraint("Length", 2, 3, params.base_side_length))
    sketch_base.addConstraint(Sketcher.Constraint("Length", 3, 0, params.base_side_length))
    
    pad_base = body.newObject("PartDesign::Pad", "PadBase")
    pad_base.Profile = sketch_base
    pad_base.Length = params.base_extrusion_depth
    pad_base.Type = "Solid"
    
    # 2. Rear Stepped Slot
    # The slot enters from the rear edge (Y = -side/2).
    # It has a central tab, then a ledge, then descends.
    # We need to define the profile on the rear face (Y = -side/2).
    
    sketch_slot = body.newObject("Sketcher::SketchObject", "SlotSketch")
    sketch_slot.Placement = App.Placement(App.Vector(0, -params.base_side_length/2, 0))
    sketch_slot.Support = (doc.getObject("YZ_Plane"), [""])
    sketch_slot.MapMode = "FlatFace"
    
    # Define the slot profile relative to the rear face center (0, 0 in sketch coords)
    # X is along the slot width, Y is along the depth (into the part).
    # Centered slot: width = slot_cutout_overall_width
    # Central tab: width = slot_cutout_central_tab_width, height = slot_cutout_central_tab_height
    # Ledge: width = slot_cutout_overall_width, height = slot_cutout_ledge_height
    # Total depth = slot_cutout_depth
    
    half_slot_width = params.slot_cutout_overall_width / 2
    half_tab_width = params.slot_cutout_central_tab_width / 2
    
    # Points: Start bottom-left, go up to tab bottom, tab top, ledge top, end top-right, etc.
    # Actually, let's trace the perimeter of the cutout.
    # The cutout is a complex shape. Let's define the outer boundary of the material remaining.
    # Or simpler: Define the cutout shape directly.
    
    # Cutout Shape:
    # Bottom edge: y = 0 (at rear face)
    # Right edge: x = half_slot_width
    # Top edge of ledge: y = slot_cutout_ledge_height
    # Top edge of tab: y = slot_cutout_ledge_height + slot_cutout_central_tab_height
    # Left edge: x = -half_slot_width
    
    # Let's construct the polygon for the cutout.
    # Start at bottom-left (-half_slot_width, 0)
    # Go to bottom-right (half_slot_width, 0)
    # Go up to ledge top (half_slot_width, slot_cutout_ledge_height)
    # Go left to tab right edge (half_tab_width, slot_cutout_ledge_height)
    # Go up to tab top (half_tab_width, slot_cutout_ledge_height + slot_cutout_central_tab_height)
    # Go left to tab left edge (-half_tab_width, slot_cutout_ledge_height + slot_cutout_central_tab_height)
    # Go down to ledge top (-half_tab_width, slot_cutout_ledge_height)
    # Go left to top-left (-half_slot_width, slot_cutout_ledge_height)
    # Go down to start (-half_slot_width, 0)
    
    p1 = App.Vector(-half_slot_width, 0, 0)
    p2 = App.Vector(half_slot_width, 0, 0)
    p3 = App.Vector(half_slot_width, params.slot_cutout_ledge_height, 0)
    p4 = App.Vector(half_tab_width, params.slot_cutout_ledge_height, 0)
    p5 = App.Vector(half_tab_width, params.slot_cutout_ledge_height + params.slot_cutout_central_tab_height, 0)
    p6 = App.Vector(-half_tab_width, params.slot_cutout_ledge_height + params.slot_cutout_central_tab_height, 0)
    p7 = App.Vector(-half_tab_width, params.slot_cutout_ledge_height, 0)
    p8 = App.Vector(-half_slot_width, params.slot_cutout_ledge_height, 0)
    
    sketch_slot.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_slot.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_slot.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_slot.addGeometry(Part.LineSegment(p4, p5), False)
    sketch_slot.addGeometry(Part.LineSegment(p5, p6), False)
    sketch_slot.addGeometry(Part.LineSegment(p6, p7), False)
    sketch_slot.addGeometry(Part.LineSegment(p7, p8), False)
    sketch_slot.addGeometry(Part.LineSegment(p8, p1), False)
    
    # Constraints
    sketch_slot.addConstraint(Sketcher.Constraint("Axis", 0, 1, 0, 1, 0, 1))
    sketch_slot.addConstraint(Sketcher.Constraint("Axis", 1, 0, 0, 0, 1, 0))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 0, 1, params.slot_cutout_overall_width))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 1, 2, params.slot_cutout_ledge_height))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 2, 3, params.slot_cutout_central_tab_width))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 3, 4, params.slot_cutout_central_tab_height))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 4, 5, params.slot_cutout_central_tab_width))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 5, 6, params.slot_cutout_central_tab_height))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 6, 7, params.slot_cutout_central_tab_width))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 7, 8, params.slot_cutout_ledge_height))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 8, 0, params.slot_cutout_overall_width))
    
    pocket_slot = body.newObject("PartDesign::Pocket", "PocketSlot")
    pocket_slot.Profile = sketch_slot
    pocket_slot.Type = "Blind"
    pocket_slot.Length = params.slot_cutout_depth
    pocket_slot.Clean = True
    
    # 3. Mounting Holes
    # Centered rectangular pattern on the rear face (Y = -side/2)
    # Pattern: 4 holes. Spacing given.
    # We need to calculate positions.
    # Let's assume the pattern is centered on the rear face.
    # Total width of pattern = (N-1) * spacing_x
    # Total height of pattern = (N-1) * spacing_y
    
    n_holes = params.base_pattern_element_count
    spacing_x = params.mounting_hole_horizontal_spacing
    spacing_y = params.mounting_hole_vertical_spacing
    
    # Calculate center of the pattern
    pattern_width = (n_holes - 1) * spacing_x
    pattern_height = (n_holes - 1) * spacing_y
    
    # Center of rear face
    face_center_x = 0
    face_center_y = 0 # In the sketch plane (YZ), X is horizontal, Y is vertical (depth)
    # Wait, sketch is on YZ plane. X is horizontal, Y is vertical (depth).
    # The pattern is on the rear face.
    # Let's define the pattern relative to the sketch origin (0,0) which is the center of the rear face.
    
    # Hole positions
    holes = []
    for i in range(n_holes):
        # i=0 is bottom-left, i=n-1 is top-right
        # x = -pattern_width/2 + i * spacing_x
        # y = -pattern_height/2 + i * spacing_y
        # But we need to map this to the sketch coordinates.
        # Sketch X is horizontal, Sketch Y is vertical (depth).
        # Let's assume the pattern is aligned with the slot? No, just centered.
        
        hx = -pattern_width/2 + i * spacing_x
        hy = -pattern_height/2 + i * spacing_y
        holes.append((hx, hy))
    
    # Create holes
    for i, (hx, hy) in enumerate(holes):
        sketch_hole = body.newObject("Sketcher::SketchObject", f"HoleSketch{i}")
        sketch_hole.Placement = App.Placement(App.Vector(0, -params.base_side_length/2, 0))
        sketch_hole.Support = (doc.getObject("YZ_Plane"), [""])
        sketch_hole.MapMode = "FlatFace"
        sketch_hole.addGeometry(Part.Circle(App.Vector(hx, hy, 0), App.Vector(0, 0, 1), params.mounting_hole_diameter/2), False)
        sketch_hole.addConstraint(Sketcher.Constraint("Axis", 0, 1, 0, 1, 0, 1))
        sketch_hole.addConstraint(Sketcher.Constraint("Axis", 1, 0, 0, 0, 1, 0))
        
        hole_feature = body.newObject("PartDesign::Hole", f"Hole{i}")
        hole_feature.Profile = sketch_hole
        hole_feature.Type = "Blind"
        hole_feature.Length = params.mounting_hole_depth
        hole_feature.Clean = True
        
        # Add constraint to align hole with slot if needed? 
        # The prompt says "centered rectangular pattern". 
        # We'll just place them relative to the face center.
        # To make them fixed, we can constrain the first hole to the origin of the sketch.
        if i == 0:
            sketch_hole.addConstraint(Sketcher.Constraint("Point", 0, 0, "XY", 0, 0)) # Force origin? No, we calculated positions.
            # Instead, let's just rely on the calculated positions being correct.
            # But to be safe, let's constrain the first hole to the sketch origin (0,0) and then offset others?
            # No, the sketch origin is (0,0). The holes are at calculated positions.
            # We need to constrain the hole center to the calculated position.
            # Sketcher doesn't support absolute coordinates easily without expressions or constraints to axes.
            # Let's constrain the first hole to the origin, and then use a pattern?
            # Or just constrain the first hole to the origin and assume the rest are relative?
            # Let's constrain the first hole to the origin (0,0) of the sketch.
            # Then the others will be at relative positions? No, they are separate sketches.
            # Let's just constrain the first hole to the origin.
            sketch_hole.addConstraint(Sketcher.Constraint("Point", 0, 0, "XY", 0, 0))
            # And the others? We can't easily constrain them to specific coordinates without expressions.
            # Let's use a Polar Pattern for the holes instead?
            # "centered rectangular pattern".
            # Let's create one hole and pattern it.
            pass
    
    # Let's redo the holes with a pattern approach for robustness.
    # Create one hole at the center of the pattern.
    # Then pattern it.
    
    # Remove the individual hole sketches/objects created above if
