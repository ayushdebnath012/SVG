import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def create_document(base_name):
    """Creates a new FreeCAD document with necessary planes and axes."""
    doc = App.newDocument("Part")
    
    # Create Workplanes and Axes (FreeCAD 1.1 standard locations)
    # XY_Plane (Z=0), XZ_Plane (Y=0), YZ_Plane (X=0)
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
    
    # Create a VarSet to hold parameters for easier management
    params = body.newObject("App::VarSet", "Parameters")
    
    # Add Parameters based on Base Description
    # clip_base
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
    plate_sketch.Placement = App.Placement(App.Vector(0, 0, 0)) # XZ Plane
    plate_sketch.ConstrainAuto = True
    plate_sketch.TechDrawPivot = App.Placement(App.Vector(0, 0, 0))
    
    # Rectangle: Center at (0, clip_base_thickness/2) to define thickness relative to origin if needed, 
    # but usually we sketch on XZ plane (width in X, length in Z). 
    # Let's assume X is Length, Z is Thickness.
    # Origin at center of plate.
    plate_sketch.addGeometry(
        Part.Rectangle(App.Vector(0, 0, -params.clip_base_thickness / 2), 
                       App.Vector(params.clip_base_length, 0, params.clip_base_thickness))
    )
    
    # Constraints
    plate_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center X
    plate_sketch.addConstraint(Sketcher.Constraint("Point", 0, 2, 0)) # Center Z
    plate_sketch.addConstraint(Sketcher.Constraint("Flatness", 0))
    plate_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, params.clip_base_length))
    plate_sketch.addConstraint(Sketcher.Constraint("Length", 0, 1, params.clip_base_thickness))
    plate_sketch.addConstraint(Sketcher.Constraint("Symmetry", 0, 0, 1, 1)) # Symmetric about X
    plate_sketch.addConstraint(Sketcher.Constraint("Symmetry", 1, 1, 0, 1)) # Symmetric about Z
    
    # Pad the plate to full thickness immediately to establish the solid body
    pad_plate = body.newObject("PartDesign::Pad", "Pad_Plate")
    pad_plate.Profile = plate_sketch
    pad_plate.Length = params.clip_base_thickness
    pad_plate.Type = "Solid" # Solid extrusion
    pad_plate.Reversed = False
    pad_plate.setExpression("Length", "Parameters.clip_base_thickness")
    pad_plate.update()

    # 2. Barb Notches Sketch (XZ Plane, at Y_end)
    # Barb cutouts are at Y = -clip_base_width/2
    barb_sketch = body.newObject("Sketcher::SketchObject", "Barb_Sketch")
    barb_sketch.Placement = App.Placement(App.Vector(0, -params.clip_base_width / 2, 0))
    barb_sketch.ConstrainAuto = True
    barb_sketch.TechDrawPivot = App.Placement(App.Vector(0, -params.clip_base_width / 2, 0))
    
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
    
    # The slot is centered on the plate (X=0). 
    # It has a straight vertical part, a bottom width, and a top arc.
    # Based on params: 
    # slot_straight_length (vertical part length?), slot_bottom_width, slot_top_arc_radius.
    # Let's construct the profile.
    
    # Define vertices for the keyhole
    # Bottom Width: slot_bottom_width
    # Height: slot_straight_length (approximate vertical straight part) + taper?
    # Let's simplify the geometry construction using lines and circles.
    
    # Center of the arc
    arc_center = App.Vector(0, params.slot_arc_center_y_position, 0)
    arc_radius = params.slot_top_arc_radius
    
    # The slot opens to the right and left? No, usually a single slot.
    # "centered keyhole-shaped lacing slot"
    # Let's assume it's a single slot opening to the right side or centered.
    # Given "slot_top_arc_central_angle_1" and "2", it suggests a specific arc shape.
    # Let's create a path: Vertical line, Arc, Vertical line, Horizontal bottom.
    
    # Let's try to match the visual of a lacing slot:
    # Width at bottom: slot_bottom_width
    # Width at top (arc diameter): 2 * slot_top_arc_radius
    # Height: slot_straight_length (distance from bottom of straight part to arc center?)
    
    # Let's define points:
    # P1: Left bottom corner
    # P2: Right bottom corner
    # P3: Right top corner (start of arc)
    # P4: Left top corner (end of arc)
    
    # Approximate geometry based on typical keyhole:
    # Bottom width: slot_bottom_width
    # Height of straight section: slot_straight_length
    # Radius: slot_top_arc_radius
    
    # Coordinates:
    # Bottom center: (0, -slot_straight_length - params.slot_bottom_taper_height/2, 0) ??
    # Let's place the arc center at (0, params.slot_arc_center_y_position, 0)
    # The arc radius is slot_top_arc_radius.
    # The straight parts connect to the arc.
    
    # Let's create the shape manually to ensure constraints work
    # We need a closed loop.
    
    # Bottom Line
    bottom_y = params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_bottom_taper_height
    # Actually, let's just use the provided dimensions to build a closed loop.
    # Let's assume the arc is at the top.
    
    # Let's create a simplified keyhole that fits the description:
    # Vertical straight sides, rounded top.
    
    # Center of bottom width
    bottom_y_pos = params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_bottom_taper_height
    # Wait, slot_bottom_taper_height might be the height of the tapered transition?
    # Let's assume a simple construction:
    # Arc center at (0, params.slot_arc_center_y_position, 0)
    # Radius R = params.slot_top_arc_radius
    # Bottom of arc = Arc Center Y - R
    # Let's set the bottom of the straight part to be at: Arc Center Y - R - slot_bottom_taper_height
    # Actually, let's just create the geometry and constrain it to be closed.
    
    # Create a closed loop of 4 segments:
    # 1. Left vertical
    # 2. Top Arc
    # 3. Right vertical
    # 4. Bottom horizontal
    
    # Let's calculate the bottom y position relative to the arc center.
    # If the arc is the top part, the bottom is straight.
    # Bottom Width = slot_bottom_width
    # Top Width (arc diameter) = 2 * R
    # Height = slot_straight_length
    
    # Let's place the bottom center at Y_bottom_center
    # Y_bottom_center = params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_bottom_taper_height - params.slot_straight_length
    # This seems too complex to reverse engineer perfectly without seeing the model.
    # I will construct a standard keyhole using the parameters as best as possible.
    
    # Define the closed shape
    # Bottom Width: slot_bottom_width
    # Height: slot_straight_length
    # Top Radius: slot_top_arc_radius
    # Arc Center Y: params.slot_arc_center_y_position
    
    # Let's place the Arc Center at (0, params.slot_arc_center_y_position, 0)
    # The arc goes from angle 1 to 2.
    # Let's assume the arc is at the top (negative Z in XZ plane? No, Z is thickness).
    # In XZ plane: X is horizontal, Z is vertical.
    # Arc is at the top (high Z).
    
    # Let's define the points:
    # Arc Center: (0, params.slot_arc_center_y_position, 0)
    # Radius: params.slot_top_arc_radius
    # Bottom of arc: Y_bottom_arc = Arc Center Y - R
    # Bottom of slot: Y_slot_bottom = Y_bottom_arc - slot_straight_length - params.slot_bottom_taper_height
    # Wait, slot_bottom_taper_height might be the height of the bottom straight part itself if it's tapered?
    # Let's assume slot_bottom_taper_height is the height of the straight bottom section.
    
    # Let's try:
    # Y_bottom_center = params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_bottom_taper_height - params.slot_straight_length
    # This creates a very long slot.
    
    # Alternative interpretation:
    # The slot is defined by the arc and the straight length.
    # Let's assume the straight length is the distance from the arc center to the bottom.
    
    # Let's create the geometry using Part::ShapeBuilder or manual lines.
    # To make it robust, I'll create a polygon and close it.
    
    # Let's define the vertices:
    # Bottom Left: (-slot_bottom_width/2, Y_bottom, 0)
    # Bottom Right: (slot_bottom_width/2, Y_bottom, 0)
    # Top Right (Arc Start): (R, ArcCenterY, 0)
    # Top Left (Arc End): (-R, ArcCenterY, 0)
    
    # We need to relate Y_bottom to ArcCenterY.
    # Let's assume the "straight length" is the distance from the bottom of the slot to the center of the arc.
    Y_bottom = params.slot_arc_center_y_position - params.slot_top_arc_radius - params.slot_straight_length - params.slot_bottom_taper_height
    
    # Wait, the parameters say "slot_bottom_taper_height". Maybe the bottom is tapered?
    # Let's assume it's a standard keyhole with a flat bottom.
    # Let's set Y_bottom = params.slot_arc
