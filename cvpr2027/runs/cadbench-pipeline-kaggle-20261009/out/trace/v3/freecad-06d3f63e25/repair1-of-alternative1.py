import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def create_document():
    """Creates a new FreeCAD document with necessary planes and axes."""
    doc = App.newDocument("Part")
    
    # Create Workplanes and Axes (FreeCAD 1.1 standard locations)
    doc.addObject("Part::Plane", "XY_Plane")
    doc.addObject("Part::Plane", "XZ_Plane")
    doc.addObject("Part::Plane", "YZ_Plane")
    
    doc.addObject("Part::Axis", "X_Axis")
    doc.addObject("Part::Axis", "Y_Axis")
    doc.addObject("Part::Axis", "Z_Axis")
    
    doc.recompute()
    return doc

def create_body_and_params(doc):
    """Creates the PartDesign Body and Parameters object."""
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create a VarSet to hold parameters
    params = body.newObject("App::VarSet", "Parameters")
    
    # --- BASE PARAMETERS ---
    params.addProperty("App::PropertyLength", "clip_base_length", "Dimensions", "Main Length")
    params.clip_base_length = 12.57
    
    params.addProperty("App::PropertyLength", "clip_base_width", "Dimensions", "Main Width")
    params.clip_base_width = 23.34
    
    params.addProperty("App::PropertyLength", "clip_base_thickness", "Dimensions", "Thickness")
    params.clip_base_thickness = 4.06
    
    # Barb notches
    params.addProperty("App::PropertyLength", "barb_cutout_base_width", "Dimensions", "Barb Width")
    params.barb_cutout_base_width = 1.01
    
    params.addProperty("App::PropertyLength", "barb_cutout_height", "Dimensions", "Barb Height")
    params.barb_cutout_height = 1.76
    
    params.addProperty("App::PropertyLength", "gap_between_barb_cutouts", "Dimensions", "Barb Gap")
    params.gap_between_barb_cutouts = 2.04
    
    params.addProperty("App::PropertyInteger", "number_of_barb_cutouts", "Dimensions", "Barb Count")
    params.number_of_barb_cutouts = 2
    
    # Lacing Slot
    params.addProperty("App::PropertyLength", "slot_top_arc_radius", "Dimensions", "Slot Arc Radius")
    params.slot_top_arc_radius = 1.1684
    
    params.addProperty("App::PropertyAngle", "slot_top_arc_central_angle_1", "Dimensions", "Slot Angle 1")
    params.slot_top_arc_central_angle_1 = 90.0
    
    params.addProperty("App::PropertyAngle", "slot_top_arc_central_angle_2", "Dimensions", "Slot Angle 2")
    params.slot_top_arc_central_angle_2 = 270.0
    
    params.addProperty("App::PropertyLength", "slot_arc_center_y_position", "Dimensions", "Slot Arc Y")
    params.slot_arc_center_y_position = 9.6393
    
    params.addProperty("App::PropertyLength", "slot_straight_length", "Dimensions", "Slot Straight")
    params.slot_straight_length = 19.3194355
    
    params.addProperty("App::PropertyLength", "slot_bottom_width", "Dimensions", "Slot Bottom W")
    params.slot_bottom_width = 1.0348006
    
    params.addProperty("App::PropertyLength", "slot_bottom_taper_height", "Dimensions", "Slot Taper H")
    params.slot_bottom_taper_height = 1.1275645
    
    params.addProperty("App::PropertyLength", "slot_overall_width", "Dimensions", "Slot Overall W")
    params.slot_overall_width = 2.3368
    
    # Trapezoidal Relief
    params.addProperty("App::PropertyLength", "trapezoid_bottom_width", "Dimensions", "Trap Bottom W")
    params.trapezoid_bottom_width = 2.04
    
    params.addProperty("App::PropertyLength", "trapezoid_top_width", "Dimensions", "Trap Top W")
    params.trapezoid_top_width = 1.0348006
    
    params.addProperty("App::PropertyLength", "trapezoid_bottom_y_position", "Dimensions", "Trap Bottom Y")
    params.trapezoid_bottom_y_position = -11.67
    
    params.addProperty("App::PropertyLength", "trapezoid_top_y_position", "Dimensions", "Trap Top Y")
    params.trapezoid_top_y_position = -10.8077
    
    # Side Slots
    params.addProperty("App::PropertyLength", "slot_width", "Dimensions", "Side Slot Width")
    params.slot_width = 0.77
    
    params.addProperty("App::PropertyLength", "slot_length", "Dimensions", "Side Slot Length")
    params.slot_length = 15.72
    
    params.addProperty("App::PropertyLength", "slot_spacing", "Dimensions", "Side Slot Spacing")
    params.slot_spacing = 11.8
    
    # --- EDIT PARAMETERS (Target) ---
    params.addProperty("App::PropertyLength", "cutout_arc_radius", "Dimensions", "Hook Arc Radius")
    params.cutout_arc_radius = 2.73
    
    params.addProperty("App::PropertyAngle", "cutout_arc_central_angle", "Dimensions", "Hook Arc Angle")
    params.cutout_arc_central_angle = 31.3008576
    
    params.addProperty("App::PropertyLength", "cutout_arc_center_y", "Dimensions", "Hook Arc Center Y")
    params.cutout_arc_center_y = 2.12
    
    params.addProperty("App::PropertyLength", "cutout_base_width", "Dimensions", "Hook Base W")
    params.cutout_base_width = 5.48
    
    params.addProperty("App::PropertyLength", "cutout_base_height", "Dimensions", "Hook Base H")
    params.cutout_base_height = 3.3
    
    params.addProperty("App::PropertyLength", "cutout_slot_width", "Dimensions", "Hook Neck W")
    params.cutout_slot_width = 1.4729302
    
    return body, params

def create_base_sketches(body, params):
    """Creates the Base Sketches."""
    
    # 1. Main Plate Sketch (XZ Plane)
    plate_sketch = body.newObject("Sketcher::SketchObject", "Plate_Sketch")
    plate_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    plate_sketch.ConstrainAuto = True
    
    # Rectangle: Center at (0, 0) in XZ plane. X is Length, Z is Thickness.
    # Note: In XZ plane, Y is 0. The rectangle is in X and Z.
    rect = Part.Rectangle(App.Vector(0, 0, -params.clip_base_thickness / 2), 
                          App.Vector(params.clip_base_length, 0, params.clip_base_thickness))
    plate_sketch.addGeometry(rect)
    
    # Constraints
    plate_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center X
    plate_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center Z
    plate_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    plate_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.clip_base_length))
    plate_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.clip_base_thickness))
    plate_sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 1, 1)) # Symmetric about X
    plate_sketch.addConstraint(Sketcher.Constraint("Symmetry", 1, 1, 0, 1)) # Symmetric about Z
    
    # Pad the plate to full thickness
    pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
    pad_plate.Profile = plate_sketch
    pad_plate.Length = params.clip_base_thickness
    pad_plate.Type = "Solid"
    pad_plate.Reversed = False
    pad_plate.setExpression("Length", "Parameters.clip_base_thickness")
    pad_plate.update()

    # 2. Barb Notches Sketch (XZ Plane, at Y_end)
    # Barb cutouts are at Y = -clip_base_width/2
    barb_sketch = body.newObject("Sketcher::SketchObject", "Barb_Sketch")
    barb_sketch.Placement = App.Placement(App.Vector(0, -params.clip_base_width / 2, 0))
    barb_sketch.ConstrainAuto = True
    
    # Two rectangles for barbs
    # Left Barb
    barb1 = Part.Rectangle(App.Vector(-params.clip_base_length/2 + 1, 0, -params.clip_base_thickness/2),
                           App.Vector(params.barb_cutout_base_width, 0, params.barb_cutout_height))
    barb_sketch.addGeometry(barb1, False)
    
    # Right Barb
    barb2 = Part.Rectangle(App.Vector(params.clip_base_length/2 - 1, 0, -params.clip_base_thickness/2),
                           App.Vector(params.barb_cutout_base_width, 0, params.barb_cutout_height))
    barb_sketch.addGeometry(barb2, False)
    
    # Constraints
    barb_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center X
    barb_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    barb_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.barb_cutout_base_width))
    barb_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.barb_cutout_height))
    barb_sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 1, 1))
    
    # Pocket Barbs (Through All Z)
    pocket_barb = body.newObject("PartDesign::Pocket", "Pocket_Barbs")
    pocket_barb.Profile = barb_sketch
    pocket_barb.Type = "ThroughAll"
    pocket_barb.setExpression("Type", "ThroughAll")

    # 3. Lacing Slot Sketch (XZ Plane, centered on plate)
    # Keyhole shape: Rectangle + Arc
    slot_sketch = body.newObject("Sketcher::SketchObject", "Slot_Sketch")
    slot_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    slot_sketch.ConstrainAuto = True
    
    # Construct the keyhole profile
    # Arc Center: (0, params.slot_arc_center_y_position, 0)
    # Radius: params.slot_top_arc_radius
    # Bottom Width: params.slot_bottom_width
    # Straight Length: params.slot_straight_length
    # Taper Height: params.slot_bottom_taper_height
    
    # Let's define the vertices manually to ensure the shape is correct
    # We assume the arc is at the top (positive Z direction relative to the straight part)
    # Actually, looking at the coordinates, the arc center Y is positive (9.6393).
    # The plate thickness is 4.06. The center is at Z=0.
    # So the arc is near the top edge of the plate.
    
    # Let's calculate the bottom Y position of the straight part.
    # Arc Center Y = 9.6393
    # Arc Radius = 1.1684
    # Bottom of Arc = 9.6393 - 1.1684 = 8.4709
    # Straight Length = 19.3194355
    # Taper Height = 1.1275645
    
    # Let's assume the straight part goes downwards from the arc.
    # Bottom of straight part = Arc Center Y - Arc Radius - Straight Length - Taper Height
    # This seems to place the bottom way below the plate.
    # Let's re-read: "slot_straight_length" might be the length of the straight vertical part.
    # "slot_bottom_taper_height" might be the height of the tapered section at the bottom.
    
    # Let's try a different interpretation:
    # The slot is defined by the arc at the top and a straight bottom.
    # The distance from the arc center to the bottom of the straight part is:
    # Distance = Arc Radius + Straight Length + Taper Height?
    # Or maybe Straight Length is the total height?
    
    # Let's try to construct the shape using Part::ShapeBuilder to be precise.
    # We will create a closed loop.
    
    # Define points:
    # Arc Center: (0, params.slot_arc_center_y_position, 0)
    # Radius: params.slot_top_arc_radius
    # Bottom Width: params.slot_bottom_width
    # Let's assume the bottom is centered at X=0.
    
    # Let's assume the "Straight Length" is the distance from the bottom of the arc to the top of the straight part.
    # And "Taper Height" is the height of the straight part itself?
    # This is ambiguous. Let's assume a standard keyhole:
    # Top: Arc
    # Bottom: Straight line
    # Sides: Vertical lines connecting arc to bottom line.
    
    # Let's assume the bottom of the slot is at:
    # Y_bottom = params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_straight_length - params.slot_bottom_taper_height
    # This creates a very long slot.
    
    # Alternative: The slot is short.
    # Maybe "slot_straight_length" is the length of the straight part.
    # And "slot_bottom_taper_height" is the height of the tapered transition at the bottom?
    # Let's assume the bottom is at:
    # Y_bottom = params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_straight_length
    
    # Let's try to build the shape with these assumptions:
    # Arc Center: (0, 9.6393, 0)
    # Radius: 1.1684
    # Bottom Y: 9.6393 - 1.1684 - 19.3194355 = -10.8485355
    # Bottom Width: 1.0348006
    
    # Let's create the shape using Part::ShapeBuilder
    # We need to close the loop.
    # Points:
    # P1: (-slot_bottom_width/2, Y_bottom, 0)
    # P2: (slot_bottom_width/2, Y_bottom, 0)
    # P3: (slot_top_arc_radius, ArcCenterY, 0)
    # P4: (-slot_top_arc_radius, ArcCenterY, 0)
    
    # But we need to connect P2 to P3 and P1 to P4.
    # These are vertical lines.
    
    # Let's create the shape
    shape_builder = Part.ShapeBuilder()
    
    # Add lines
    # Bottom line
    shape_builder.addLine(App.Vector(-params.slot_bottom_width/2, params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_straight_length - params.slot_bottom_taper_height, 0),
                          App.Vector(params.slot_bottom_width/2, params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_straight_length - params.slot_bottom_taper_height, 0))
    
    # Right vertical line
    shape_builder.addLine(App.Vector(params.slot_bottom_width/2, params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_straight_length - params.slot_bottom_taper_height, 0),
                          App.Vector(params.slot_top_arc_radius, params.slot_arc_center_y_position, 0))
    
    # Top Arc
    shape_builder.addArc(App.Vector(0, params.slot_arc_center_y_position, 0), params.slot_top_arc_radius, 0, 180) # 0 to 180 degrees
    
    # Left vertical line
    shape_builder.addLine(App.Vector(-params.slot_top_arc_radius, params.slot_arc_center_y_position, 0),
                          App.Vector(-params.slot_bottom_width/2, params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_straight_length - params.slot_bottom_taper_height, 0))
    
    # Close the loop
    shape_builder.close()
    
    # Create the shape
    slot_shape = shape_builder.makeShape()
    slot_sketch.addGeometry(slot_shape)
    
    # Constraints
    slot_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center X
    slot_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    slot_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.slot_bottom_width))
    slot_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.slot_straight_length + params.slot_bottom_taper_height))
    slot_sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 1, 1))
    
    # Pocket Slot (Through All Z)
    pocket_slot = body.newObject("PartDesign::Pocket", "Pocket_Slot")
    pocket_slot.Profile = slot_sketch
    pocket_slot.Type = "ThroughAll"
    pocket_slot.setExpression("Type", "ThroughAll")

    # 4. Trapezoidal Relief Sketch (XZ Plane, centered on plate)
    # Trapezoid: Bottom Width, Top Width, Bottom Y, Top Y
    trap_sketch = body.newObject("Sketcher::SketchObject", "Trap_Sketch")
    trap_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    trap_sketch.ConstrainAuto = True
    
    # Trapezoid vertices
    # Bottom: ( -trap_bottom_width/2, trap_bottom_y_position, 0 ) to ( trap_bottom_width/2, trap_bottom_y_position, 0 )
    # Top: ( -trap_top_width/2, trap_top_y_position, 0 ) to ( trap_top_width/2, trap_top_y_position, 0 )
    
    # Let's create the shape
    trap_shape = Part.Trapezoid(
        App.Vector(-params.trapezoid_bottom_width/2, params.trapezoid_bottom_y_position, 0),
        App.Vector(params.trapezoid_bottom_width/2, params.trapezoid_bottom_y_position, 0),
        App.Vector(-params.trapezoid_top_width/2, params.trapezoid_top_y_position, 0),
        App.Vector(params.trapezoid_top_width/2, params.trapezoid_top_y_position, 0)
    )
    trap_sketch.addGeometry(trap_shape)
    
    # Constraints
    trap_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center X
    trap_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    trap_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.trapezoid_bottom_width))
    trap_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.trapezoid_top_width))
    trap_sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 1, 1))
    
    # Pocket Trap (Through All Z)
    pocket_trap = body.newObject("PartDesign::Pocket", "Pocket_Trap")
    pocket_trap.Profile = trap_sketch
    pocket_trap.Type = "ThroughAll"
    pocket_trap.setExpression("Type", "ThroughAll")

    # 5. Side Slots Sketch (XZ Plane, at left and right edges)
    # Two slots, one at left, one at right.
    # Start at Y = -clip_base_width/2, extend towards Y+ by slot_length.
    # Width: slot_width.
    # Spacing: slot_spacing (distance between the two slots? or from edge?)
    # "slot_spacing = 11.8 mm"
    # Plate width = 23.34. Half width = 11.67.
    # If spacing is 11.8, it's almost at the edge.
    # Let's assume the slots are centered at X = +/- (clip_base_width/2 - slot_spacing/2)?
    # Or maybe the spacing is the distance between the centers of the two slots.
    # Let's assume the slots are at X = +/- (clip_base_width/2 - slot_spacing/2)
    # But 23.34/2 = 11.67. 11.67 - 11.8/2 = 5.77.
    # Let's assume the slots are at X = +/- (clip_base_width/2 - slot_spacing/2)
    
    # Actually, "slot_spacing" might be the distance from the edge to the slot.
    # Let's assume the slots are at X = +/- (clip_base_width/2 - slot_spacing)
    # 11.67 - 11.8 = -0.13. This is inside the plate.
    # Let's assume the slots are at X = +/- (clip_base_width/2 - slot_spacing/2)
    # 11.67 - 5.9 = 5.77.
    
    # Let's create a sketch for the side slots.
    # We will create two rectangles.
    
    # Left Slot
    left_x = -params.clip_base_width/2 + params.slot_spacing/2
    right_x = params.clip_base_width/2 - params.slot_spacing/2
    
    # Slot 1 (Left)
    slot1 = Part.Rectangle(App.Vector(left_x, 0, -params.clip_base_thickness/2),
                           App.Vector(params.slot_width, 0, params.slot_length))
    slot1_sketch = body.newObject("Sketcher::SketchObject", "Slot1_Sketch")
    slot1_sketch.Placement = App.Placement(App.Vector(0, -params.clip_base_width/2, 0))
    slot1_sketch.addGeometry(slot1)
    slot1_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0))
    slot1_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    slot1_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.slot_width))
    slot1_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.slot_length))
    
    # Slot 2 (Right)
    slot2 = Part.Rectangle(App.Vector(right_x, 0, -params.clip_base_thickness/2),
                           App.Vector(params.slot_width, 0, params.slot_length))
    slot2_sketch = body.newObject("Sketcher::SketchObject", "Slot2_Sketch")
    slot2_sketch.Placement = App.Placement(App.Vector(0, -params.clip_base_width/2, 0))
    slot2_sketch.addGeometry(slot2)
    slot2_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0))
    slot2_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    slot2_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.slot_width))
    slot2_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.slot_length))
    
    # Pocket Side Slots (Through All Z)
    pocket_slot1 = body.newObject("PartDesign::Pocket", "Pocket_Slot1")
    pocket_slot1.Profile = slot1_sketch
    pocket_slot1.Type = "ThroughAll"
    pocket_slot1.setExpression("Type", "ThroughAll")
    
    pocket_slot2 = body.newObject("PartDesign::Pocket", "Pocket_Slot2")
    pocket_slot2.Profile = slot2_sketch
    pocket_slot2.Type = "ThroughAll"
    pocket_slot2.setExpression("Type", "ThroughAll")

    return plate_sketch, barb_sketch, slot_sketch, trap_sketch, slot1_sketch, slot2_sketch

def create_hook_sketch(body, params):
    """Creates the Hook Sketch for the edit."""
    hook_sketch = body.newObject("Sketcher::SketchObject", "Hook_Sketch")
    hook_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    hook_sketch.ConstrainAuto = True
    
    # Hook shape:
    # Base: Rectangle (cutout_base_width x cutout_base_height)
    # Neck: Narrower rectangle (cutout_slot_width x some height)
    # Eye: Arc (cutout_arc_radius, cutout_arc_central_angle)
    
    # Let's define the vertices
    # Base: ( -cutout_base_width/2, 0 ) to ( cutout_base_width/2, cutout_base_height )
    # Neck: ( -cutout_slot_width/2, cutout_base_height ) to ( cutout_slot_width/2, cutout_base_height + neck_height )
    # Eye: Arc centered at (0, cutout_arc_center_y) with radius cutout_arc_radius
    
    # Let's assume the neck height is such that the arc is tangent to the neck.
    # Or maybe the arc is centered at cutout_arc_center_y and the neck ends at the arc.
    
    # Let's assume the arc is at the top.
    # Arc Center: (0, params.cutout_arc_center_y, 0)
    # Radius: params.cutout_arc_radius
    # Neck Top: ( -cutout_slot_width/2, params.cutout_arc_center_y - params.cutout_arc_radius ) to ( cutout_slot_width/2, params.cutout_arc_center_y - params.cutout_arc_radius )
    # Neck Bottom: ( -cutout_slot_width/2, params.cutout_base_height ) to ( cutout_slot_width/2, params.cutout_base_height )
    
    # Let's create the shape
    # Base Rectangle
    base_rect = Part.Rectangle(App.Vector(-params.cutout_base_width/2, 0, 0),
                               App.Vector(params.cutout_base_width, 0, params.cutout_base_height))
    hook_sketch.addGeometry(base_rect)
    
    # Neck Rectangle
    neck_rect = Part.Rectangle(App.Vector(-params.cutout_slot_width/2, params.cutout_base_height, 0),
                               App.Vector(params.cutout_slot_width, 0, params.cutout_arc_center_y - params.cutout_arc_radius))
    hook_sketch.addGeometry(neck_rect)
    
    # Arc
    # We need to connect the neck to the arc.
    # The arc should be tangent to the neck.
    # Let's assume the arc is centered at (0, params.cutout_arc_center_y, 0)
    # And the neck ends at (0, params.cutout_arc_center_y - params.cutout_arc_radius, 0)
    # So the arc is tangent to the neck at the bottom.
    
    # Let's create the arc
    arc = Part.Arc(App.Vector(0, params.cutout_arc_center_y, 0), params.cutout_arc_radius, 0, params.cutout_arc_central_angle)
    hook_sketch.addGeometry(arc)
    
    # Constraints
    hook_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center X
    hook_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    hook_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.cutout_base_width))
    hook_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.cutout_base_height))
    hook_sketch.addConstraint(Sketcher.Constraint("Length", 1, 0, params.cutout_slot_width))
    hook_sketch.addConstraint(Sketcher.Constraint("Length", 1, 1, params.cutout_arc_center_y - params.cutout_arc_radius - params.cutout_base_height))
    hook_sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 1, 1))
    
    # Pocket Hook (Through All Z)
    pocket_hook = body.newObject("PartDesign::Pocket", "Pocket_Hook")
    pocket_hook.Profile = hook_sketch
    pocket_hook.Type = "ThroughAll"
    pocket_hook.setExpression("Type", "ThroughAll")
    
    return hook_sketch

def save_document(doc, filename):
    """Saves the document to a file."""
    doc.saveAs(str(Path(__file__).resolve().parent / filename))

def main():
    # Create document
    doc = create_document()
    
    # Create body and params
    body, params = create_body_and_params(doc)
    
    # Create base sketches
    create_base_sketches(body, params)
    
    # Save Base
    base_filename = Path(__file__).resolve().stem + "_base.FCStd"
    save_document(doc, base_filename)
    
    # Apply Edit
    # We need to add the hook sketch and pocket
    hook_sketch = create_hook_sketch(body, params)
    
    # Recompute to update the model
    doc.recompute()
    
    # Save Edit
    edit_filename = Path(__file__).resolve().stem + "_edit.FCStd"
    save_document(doc, edit_filename)

if __name__ == "__main__":
    main()
