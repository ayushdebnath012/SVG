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

    # Define planes relative to the body
    # We will create sketches on the body's local planes
    # Plane 0: Top of the plate (Z = connector_plate_thickness / 2)
    # Plane 1: Bottom of the plate (Z = -connector_plate_thickness / 2)
    # Plane 2: Midplane of the stem (Z = -connector_plate_thickness / 2 + connector_stem_thickness / 2)
    
    # Sketch 1: Top plate profile
    sketch_plate = body.newObject("Sketcher::SketchObject", "Sketch_Plate")
    sketch_plate.Placement = App.Placement(App.Vector(0, 0, params.connector_plate_thickness / 2.0))
    sketch_plate.Placement.toPolar() # Ensure correct rotation
    sketch_plate.Placement = App.Placement(App.Vector(0, 0, params.connector_plate_thickness / 2.0), App.Rotation(0, 0, 0))
    sketch_plate.ConstrainToPlane = (body, ["Face1"]) # This is tricky in headless, let's use explicit placement
    # Actually, for headless, we define the placement and let the sketcher handle the plane via constraints or just draw on a plane
    # Let's use the standard way: create a sketch on a specific plane of the body
    # But since we are in headless mode, we need to be careful with Face references.
    # Instead, we will create the sketch on the Body's default plane (XY) and then offset it, 
    # OR create a sketch on a specific plane by setting the Placement correctly and using the Body's internal plane logic.
    # The most robust way in headless PartDesign is to use the Body's internal planes.
    # However, without GUI, referencing faces is hard. 
    # Strategy: Create sketches on the Body's XY plane (which is effectively the XY plane of the body)
    # and use the Body's Placement to position the whole body, OR use the sketch's Placement to move the sketch relative to the body.
    # Let's use the sketch's Placement to position the sketch on the specific Z level.
    # We will draw the profile in the XY plane of the sketch (which is offset from the body's origin).
    
    # Top Plate Sketch (on Z = thickness/2)
    sketch_plate.Placement = App.Placement(App.Vector(0, 0, params.connector_plate_thickness / 2.0))
    sketch_plate.ConstrainToPlane = True # This might not work headless. 
    # Alternative: Just draw lines on the XY plane of the sketch (which is offset).
    # We need to define the geometry relative to the sketch's own coordinate system.
    
    # Let's define the plate profile: Rectangle centered at origin in sketch coords.
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-params.connector_plate_width/2.0, -params.connector_plate_length/2.0), App.Vector(params.connector_plate_width/2.0, -params.connector_plate_length/2.0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(params.connector_plate_width/2.0, -params.connector_plate_length/2.0), App.Vector(params.connector_plate_width/2.0, params.connector_plate_length/2.0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(params.connector_plate_width/2.0, params.connector_plate_length/2.0), App.Vector(-params.connector_plate_width/2.0, params.connector_plate_length/2.0)), False)
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-params.connector_plate_width/2.0, params.connector_plate_length/2.0), App.Vector(-params.connector_plate_width/2.0, -params.connector_plate_length/2.0)), False)
    
    # Add constraints to make it a rectangle
    sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0)) # Corner 0-1 coincident
    sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 1)) # Corner 0-1 coincident
    sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 2)) # Corner 0-1 coincident
    sketch_plate.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 3)) # Corner 0-1 coincident
    # Wait, the above constraints are not sufficient. Let's use simpler constraints.
    # Center the rectangle.
    sketch_plate.addConstraint(Sketcher.Constraint("X", 0, 0, 0)) # Center X
    sketch_plate.addConstraint(Sketcher.Constraint("Y", 1, 0, 0)) # Center Y
    # Define lengths
    sketch_plate.addConstraint(Sketcher.Constraint("Length", 0, 1, params.connector_plate_width))
    sketch_plate.addConstraint(Sketcher.Constraint("Length", 0, 3, params.connector_plate_length))
    # This is getting complex. Let's just draw the lines and use simple constraints.
    # Reset and redo with a simpler approach:
    sketch_plate = body.newObject("Sketcher::SketchObject", "Sketch_Plate")
    sketch_plate.Placement = App.Placement(App.Vector(0, 0, params.connector_plate_thickness / 2.0))
    # Draw the plate profile
    # Line 1: Bottom edge
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-params.connector_plate_width/2.0, -params.connector_plate_length/2.0), App.Vector(params.connector_plate_width/2.0, -params.connector_plate_length/2.0)), False)
    # Line 2: Right edge
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(params.connector_plate_width/2.0, -params.connector_plate_length/2.0), App.Vector(params.connector_plate_width/2.0, params.connector_plate_length/2.0)), False)
    # Line 3: Top edge
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(params.connector_plate_width/2.0, params.connector_plate_length/2.0), App.Vector(-params.connector_plate_width/2.0, params.connector_plate_length/2.0)), False)
    # Line 4: Left edge
    sketch_plate.addGeometry(Part.LineSegment(App.Vector(-params.connector_plate_width/2.0, params.connector_plate_length/2.0), App.Vector(-params.connector_plate_width/2.0, -params.connector_plate_length/2.0)), False)
    
    # Constraints to define the rectangle
    # Origin at bottom-left
    sketch_plate.addConstraint(Sketcher.Constraint("Fixed", 0, 1)) # Fix origin
    sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 1, 0)) # Vertical line
    sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 1, 0)) # Horizontal line
    sketch_plate.addConstraint(Sketcher.Constraint("Length", 0, 1, params.connector_plate_width)) # Width
    sketch_plate.addConstraint(Sketcher.Constraint("Length", 0, 3, params.connector_plate_length)) # Length
    
    # Pad for the plate
    pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
    pad_plate.Profile = sketch_plate
    pad_plate.Length = params.connector_plate_thickness
    pad_plate.Direction = (0, 0, 1) # Upward from bottom to top
    
    # Now create the stem sketch
    # The stem is centered along the plate length, and offset across the plate width.
    # Stem location in global coords:
    # X: 0
    # Y: -params.connector_stem_center_offset_across_plate (offset from center towards negative Y)
    # Z: -params.connector_plate_thickness / 2.0 (bottom of plate)
    # Z_stem_bottom = -params.connector_plate_thickness / 2.0
    # Z_stem_top = Z_stem_bottom + params.connector_stem_thickness
    
    sketch_stem = body.newObject("Sketcher::SketchObject", "Sketch_Stem")
    sketch_stem.Placement = App.Placement(App.Vector(0, -params.connector_stem_center_offset_across_plate, -params.connector_plate_thickness / 2.0))
    
    # Stem profile: Rectangle
    # Width: connector_stem_width (along X)
    # Length: connector_stem_length (along Y, in the plate plane)
    # Centered at origin of sketch (which is at Y = -offset)
    
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(-params.connector_stem_width/2.0, -params.connector_stem_length/2.0), App.Vector(params.connector_stem_width/2.0, -params.connector_stem_length/2.0)), False)
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(params.connector_stem_width/2.0, -params.connector_stem_length/2.0), App.Vector(params.connector_stem_width/2.0, params.connector_stem_length/2.0)), False)
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(params.connector_stem_width/2.0, params.connector_stem_length/2.0), App.Vector(-params.connector_stem_width/2.0, params.connector_stem_length/2.0)), False)
    sketch_stem.addGeometry(Part.LineSegment(App.Vector(-params.connector_stem_width/2.0, params.connector_stem_length/2.0), App.Vector(-params.connector_stem_width/2.0, -params.connector_stem_length/2.0)), False)
    
    # Constraints for stem
    sketch_stem.addConstraint(Sketcher.Constraint("Fixed", 0, 1))
    sketch_stem.addConstraint(Sketcher.Constraint("Vertical", 0, 0, 1, 0))
    sketch_stem.addConstraint(Sketcher.Constraint("Horizontal", 0, 0, 1, 0))
    sketch_stem.addConstraint(Sketcher.Constraint("Length", 0, 1, params.connector_stem_width))
    sketch_stem.addConstraint(Sketcher.Constraint("Length", 0, 3, params.connector_stem_length))
    
    # Pad for the stem (extrude downwards from the plate bottom)
    # The stem is attached to the bottom of the plate.
    # The sketch is at Z = -plate_thickness/2.
    # We need to extrude downwards.
    pad_stem = body.newObject("PartDesign::Pad", "Pad_Stem")
    pad_stem.Profile = sketch_stem
    pad_stem.Length = params.connector_stem_thickness
    pad_stem.Direction = (0, 0, -1) # Downward
    
    # Now create the mounting slot
    # The slot is an obround (rectangle with semicircular ends) passing through the stem side-to-side.
    # Long axis follows the stem projection direction (Z).
    # Midpoint lies mounting_slot_center_depth_below_plate from the plate underside.
    # Plate underside is at Z = -params.connector_plate_thickness / 2.0
    # Slot center Z = -params.connector_plate_thickness / 2.0 - params.mounting_slot_center_depth_below_plate
    
    # Slot dimensions:
    # Arc radius: params.mounting_slot_end_arc_radius
    # End diameter = 2 * arc_radius
    # Distance between end centers = end_diameter
    # Total length of straight sides = connector_stem_length - 2 * arc_radius? 
    # No, the problem says "two end centers are separated by one end diameter". 
    # And "parallel straight sides".
    # So the total length of the slot is 2 * arc_radius + distance_between_centers = 2 * arc_radius + 2 * arc_radius = 4 * arc_radius?
    # Or is the distance between centers the length of the straight part?
    # "The two end centers are separated by one end diameter" -> Distance = 2 * arc_radius.
    # Total length = arc_radius + distance + arc_radius = 2*arc_radius + 2*arc_radius = 4*arc_radius.
    # But the slot is inside the stem. The stem length is 2.5mm. Arc radius is 0.5mm.
    # If total length is 2.0mm, it fits easily.
    # Let's assume the slot length is determined by the arc radius and the separation.
    # Length = 4 * arc_radius = 2.0 mm.
    # Width of the slot (along the stem width) = 2 * arc_radius = 1.0 mm.
    
    slot_center_z = -params.connector_plate_thickness / 2.0 - params.mounting_slot_center_depth_below_plate
    
    sketch_slot = body.newObject("Sketcher::SketchObject", "Sketch_Slot")
    sketch_slot.Placement = App.Placement(App.Vector(0, 0, slot_center_z))
    
    # Slot profile:
    # We need an obround shape.
    # It lies in the XZ plane of the sketch (which is at Y=0, Z=slot_center_z).
    # The stem width is along X. The slot width should be 2 * arc_radius.
    # The slot length (along Z) is 4 * arc_radius.
    # Let's construct it using lines and circles.
    
    # Center of slot in sketch coords (which is at global X=0, Y=0, Z=slot_center_z)
    # But wait, the sketch is on the XY plane of the body by default?
    # No, sketch_slot.Placement is at (0, 0, slot_center_z). This places the sketch origin at that Z.
    # The sketch plane is still XY. So the sketch will be in the plane Z = slot_center_z.
    # The slot should be side-to-side in the stem. The stem runs along Z.
    # So the slot should be in the XZ plane? No, the slot is "side-to-side" in the stem.
    # The stem is a rectangle in the XY plane (at Z = bottom of plate to bottom + thickness).
    # Wait, the stem is extruded along Z.
    # The slot passes through the stem side-to-side.
    # Side-to-side usually means across the width of the stem (X direction) and along the depth (Z direction)?
    # Or across the width (X) and along the length (Z)?
    # "Long axis follows the stem projection direction" -> Long axis is Z.
    # "Midpoint lies ... from the plate underside" -> Z position.
    # "Side-to-side" -> Across the width of the stem (X direction)?
    # No, "side-to-side" in the context of a stem usually means from one side to the other.
    # The stem has width (X) and length (Y in plate plane, but Z in 3D).
    # The stem projection direction is Z.
    # So the slot is along Z.
    # The slot width is along X.
    # The slot is centered at X=0, Y=0 (in the stem's cross section).
    # The sketch should be on a plane perpendicular to the slot axis (Z).
    # So the sketch should be on the XZ plane? Or YZ plane?
    # The stem is along Z. The slot is along Z.
    # So the slot is a hole along Z.
    # The sketch for the slot should be on a plane perpendicular to Z, e.g., XY plane.
    # But the slot is not a simple circle, it's an obround.
    # And it passes through the stem.
    # The stem is a solid block.
    # We need to subtract the slot.
    # The slot is defined by its profile in the XY plane (at the center Z).
    # The profile is an obround.
    # The obround has width (along X) = 2 * arc_radius.
    # The obround has length (along Z) = 4 * arc_radius.
    # But wait, the sketch is on the XY plane. So the sketch profile will be in the XY plane.
    # The slot will be extruded along Z (through all).
    # But the slot is "side-to-side" and "long axis follows the stem projection direction".
