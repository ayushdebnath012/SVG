from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import PartDesign

def main():
    # Create new document
    doc = App.newDocument("ConnectorT")
    
    # Create a PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create named parameters
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "connector_plate_width", "Dimensions", "connector_plate_width")
    params.connector_plate_width = 3.5
    params.addProperty("App::PropertyLength", "connector_plate_length", "Dimensions", "connector_plate_length")
    params.connector_plate_length = 6.0
    params.addProperty("App::PropertyLength", "connector_plate_thickness", "Dimensions", "connector_plate_thickness")
    params.connector_plate_thickness = 2.0
    params.addProperty("App::PropertyLength", "connector_stem_width", "Dimensions", "connector_stem_width")
    params.connector_stem_width = 0.5
    params.addProperty("App::PropertyLength", "connector_stem_length", "Dimensions", "connector_stem_length")
    params.connector_stem_length = 2.5
    params.addProperty("App::PropertyLength", "connector_stem_thickness", "Dimensions", "connector_stem_thickness")
    params.connector_stem_thickness = 5.0
    params.addProperty("App::PropertyLength", "connector_stem_center_offset_across_plate", "Dimensions", "connector_stem_center_offset_across_plate")
    params.connector_stem_center_offset_across_plate = 1.3
    params.addProperty("App::PropertyLength", "mounting_slot_center_depth_below_plate", "Dimensions", "mounting_slot_center_depth_below_plate")
    params.mounting_slot_center_depth_below_plate = 3.2
    params.addProperty("App::PropertyLength", "mounting_slot_end_arc_radius", "Dimensions", "mounting_slot_end_arc_radius")
    params.mounting_slot_end_arc_radius = 0.5

    # --- Plate Construction ---
    # Sketch 1: Top plate profile (Rectangle)
    # Placed at Z = thickness/2
    sketch_plate = body.newObject("Sketcher::SketchObject", "Sketch_Plate")
    sketch_plate.Placement = App.Placement(App.Vector(0, 0, params.connector_plate_thickness / 2.0))
    
    # Define rectangle geometry relative to sketch origin
    w = params.connector_plate_width
    l = params.connector_plate_length
    
    # Lines
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-w/2, -l/2), App.Vector(w/2, -l/2)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(w/2, -l/2), App.Vector(w/2, l/2)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(w/2, l/2), App.Vector(-w/2, l/2)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-w/2, l/2), App.Vector(-w/2, -l/2)), False)
    
    # Constraints
    sketch_plate.addConstraint(Sketcher.Constraint("Fixed", 0, 1))
    sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 1, 0))
    sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 1, 0))
    sketch_plate.addConstraint(Sketcher.Constraint("Length", 0, 1, w))
    sketch_plate.addConstraint(Sketcher.Constraint("Length", 0, 3, l))
    
    # Pad for the plate
    pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
    pad_plate.Profile = sketch_plate
    pad_plate.Length = params.connector_plate_thickness
    pad_plate.Direction = (0, 0, 1)
    
    # --- Stem Construction ---
    # Sketch 2: Stem profile (Rectangle)
    # Placed at Z = -thickness/2 (bottom of plate)
    # Offset across plate width (Y direction)
    offset_y = params.connector_stem_center_offset_across_plate
    stem_w = params.connector_stem_width
    stem_l = params.connector_stem_length
    
    sketch_stem = body.newObject("Sketcher::SketchObject", "Sketch_Stem")
    sketch_stem.Placement = App.Placement(App.Vector(0, -offset_y, -params.connector_plate_thickness / 2.0))
    
    # Define rectangle geometry
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(-stem_w/2, -stem_l/2), App.Vector(stem_w/2, -stem_l/2)), False)
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(stem_w/2, -stem_l/2), App.Vector(stem_w/2, stem_l/2)), False)
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(stem_w/2, stem_l/2), App.Vector(-stem_w/2, stem_l/2)), False)
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(-stem_w/2, stem_l/2), App.Vector(-stem_w/2, -stem_l/2)), False)
    
    # Constraints
    sketch_stem.addConstraint(Sketcher.Constraint("Fixed", 0, 1))
    sketch_stem.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 1, 0))
    sketch_stem.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 1, 0))
    sketch_stem.addConstraint(Sketcher.Constraint("Length", 0, 1, stem_w))
    sketch_stem.addConstraint(Sketcher.Constraint("Length", 0, 3, stem_l))
    
    # Pad for the stem (extrude downwards)
    pad_stem = body.newObject("PartDesign::Pad", "Pad_Stem")
    pad_stem.Profile = sketch_stem
    pad_stem.Length = params.connector_stem_thickness
    pad_stem.Direction = (0, 0, -1)
    
    # --- Slot Construction ---
    # The slot is an obround passing through the stem side-to-side.
    # Long axis follows stem projection direction (Z).
    # Midpoint is at depth below plate underside.
    # Plate underside Z = -thickness/2.
    # Slot center Z = -thickness/2 - depth.
    
    depth = params.mounting_slot_center_depth_below_plate
    arc_r = params.mounting_slot_end_arc_radius
    
    slot_center_z = -params.connector_plate_thickness / 2.0 - depth
    
    # The slot is a hole through the stem.
    # The stem is along Z. The slot is along Z.
    # The slot profile is in the XY plane (perpendicular to Z).
    # The obround has width (along X) = 2 * arc_r.
    # The obround has length (along Y) = 2 * arc_r (since end centers are separated by one end diameter = 2*arc_r).
    # Wait, "two end centers are separated by one end diameter".
    # End diameter = 2 * arc_r.
    # Distance between centers = 2 * arc_r.
    # Total length of the straight part = distance between centers = 2 * arc_r.
    # Total length of the obround = arc_r + (2*arc_r) + arc_r = 4 * arc_r.
    # Width of the obround = 2 * arc_r.
    
    slot_w = 2 * arc_r
    slot_l = 4 * arc_r
    
    sketch_slot = body.newObject("Sketcher::SketchObject", "Sketch_Slot")
    sketch_slot.Placement = App.Placement(App.Vector(0, 0, slot_center_z))
    
    # Define obround geometry
    # Center at origin of sketch (which is at global X=0, Y=0, Z=slot_center_z)
    # The sketch plane is XY.
    # We need to draw an obround centered at (0,0) with width slot_w (X) and length slot_l (Y).
    
    # Corners of the bounding box
    x1 = -slot_w / 2
    x2 = slot_w / 2
    y1 = -slot_l / 2
    y2 = slot_l / 2
    
    # Midpoints of the straight sides
    # Top and Bottom (Y = +/- slot_l/2)
    # Left and Right (X = +/- slot_w/2)
    
    # Points for the 4 corners of the rectangle part
    p1 = App.Vector(x1, y1)
    p2 = App.Vector(x2, y1)
    p3 = App.Vector(x2, y2)
    p4 = App.Vector(x1, y2)
    
    # Points for the arc centers
    # Top arc center: (0, y2)
    # Bottom arc center: (0, y1)
    # Left arc center: (x1, 0)
    # Right arc center: (x2, 0)
    
    # We will construct the shape using lines and circles.
    # Line 1: Bottom straight (from left to right)
    # Line 2: Right straight (from bottom to top)
    # Line 3: Top straight (from right to left)
    # Line 4: Left straight (from top to bottom)
    # Circle 1: Bottom arc
    # Circle 2: Right arc
    # Circle 3: Top arc
    # Circle 4: Left arc
    
    # Actually, simpler to just draw the lines and circles.
    # Line 1: Bottom straight
    sketch_slot.addGeometry(Part.LineSegment(App.Vector(x1, y1), App.Vector(x2, y1)), False)
    # Line 2: Right straight
    sketch_slot.addGeometry(Part.LineSegment(App.Vector(x2, y1), App.Vector(x2, y2)), False)
    # Line 3: Top straight
    sketch_slot.addGeometry(Part.LineSegment(App.Vector(x2, y2), App.Vector(x1, y2)), False)
    # Line 4: Left straight
    sketch_slot.addGeometry(Part.LineSegment(App.Vector(x1, y2), App.Vector(x1, y1)), False)
    
    # Circles
    # Bottom arc
    sketch_slot.addGeometry(Part.Circle(App.Vector(x1, y1), App.Vector(0, 0, 1), arc_r), False)
    # Right arc
    sketch_slot.addGeometry(Part.Circle(App.Vector(x2, 0), App.Vector(0, 0, 1), arc_r), False)
    # Top arc
    sketch_slot.addGeometry(Part.Circle(App.Vector(x1, y2), App.Vector(0, 0, 1), arc_r), False)
    # Left arc
    sketch_slot.addGeometry(Part.Circle(App.Vector(0, y1), App.Vector(0, 0, 1), arc_r), False)
    
    # Constraints to define the shape
    # Fix origin
    sketch_slot.addConstraint(Sketcher.Constraint("Fixed", 0, 1))
    # Vertical lines
    sketch_slot.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 1, 0))
    sketch_slot.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 1, 1))
    # Horizontal lines
    sketch_slot.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 1, 0))
    sketch_slot.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 1, 1))
    # Lengths
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 0, 1, slot_w))
    sketch_slot.addConstraint(Sketcher.Constraint("Length", 0, 3, slot_l))
    # Radii
    sketch_slot.addConstraint(Sketcher.Constraint("Radius", 0, 4, arc_r))
    sketch_slot.addConstraint(Sketcher.Constraint("Radius", 0, 5, arc_r))
    sketch_slot.addConstraint(Sketcher.Constraint("Radius", 0, 6, arc_r))
    sketch_slot.addConstraint(Sketcher.Constraint("Radius", 0, 7, arc_r))
    
    # Pocket for the slot (Through All)
    pocket_slot = body.newObject("PartDesign::Pocket", "Pocket_Slot")
    pocket_slot.Profile = sketch_slot
    pocket_slot.Type = "ThroughAll"
    
    # --- Recompute and Save ---
    doc.recompute()
    
    # Save to the required path
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / "answer.FCStd"
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    main()
