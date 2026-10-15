import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

def create_set_screw():
    # Create Document
    doc = App.newDocument("SetScrew")
    
    # Define Parameters
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "set_screw_cross_section_length", "Dimensions", "Total length of screw")
    params.set_screw_cross_section_length = 19.05
    params.addProperty("App::PropertyLength", "set_screw_cross_section_width", "Dimensions", "Diameter of screw")
    params.set_screw_cross_section_width = 2.79
    params.addProperty("App::PropertyLength", "large_diameter_section_length", "Dimensions", "Length of head section")
    params.large_diameter_section_length = 9.65
    params.addProperty("App::PropertyLength", "rounded_tip_arc_radius", "Dimensions", "Radius of rounded tip")
    params.rounded_tip_arc_radius = 1.78
    params.addProperty("App::PropertyLength", "screwdriver_slot_length", "Dimensions", "Width of screwdriver slot")
    params.screwdriver_slot_length = 1.27
    params.addProperty("App::PropertyLength", "screwdriver_slot_recess_depth", "Dimensions", "Depth of screwdriver slot")
    params.screwdriver_slot_recess_depth = 0.76
    
    # Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # Create Base Sketch (Profile for extrusion)
    # We will build the profile in two parts:
    # 1. The main cylindrical body (large diameter section + smaller section)
    # 2. The rounded tip
    
    # Step 1: Create the main body profile
    # The main body is a rectangle from x=0 to x=large_diameter_section_length + (total_length - large_diameter_section_length)
    # Actually, let's simplify:
    # The screw has a large diameter section of length L_large.
    # The remaining length is L_small = Total - L_large.
    # The rounded tip is at the end of the small section.
    
    # Let's create a sketch for the main body profile.
    # We'll create a rectangle that represents the main body up to the start of the tip.
    # Then we'll add the tip geometry.
    
    # Actually, a better approach for a single solid with a rounded tip:
    # Create a sketch that includes the main body and the tip arc in one go?
    # No, the tip is tangent to the smaller cylinder.
    # Let's create the main body as a cylinder, then add the tip as a separate feature.
    
    # Step 1: Main Body Profile Sketch
    main_sketch = body.newObject("Sketcher::SketchObject", "MainProfile")
    main_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    main_sketch.Constraints = []
    
    # Create a rectangle for the main body profile
    # The main body extends from x=0 to x=large_diameter_section_length + (total_length - large_diameter_section_length)
    # Wait, the problem says:
    # "The larger section has radius set_screw_cross_section_width and extends from the slotted end for large_diameter_section_length."
    # "The remaining smaller section has radius rounded_tip_arc_radius."
    # This implies the smaller section is a cylinder of radius rounded_tip_arc_radius.
    # And the tip is a rounded tip tangent to this smaller cylinder.
    
    # So the profile is:
    # - A rectangle from x=0 to x=large_diameter_section_length with height = set_screw_cross_section_width
    # - A rectangle from x=large_diameter_section_length to x=total_length with height = 2 * rounded_tip_arc_radius
    # - A rounded tip at the end.
    
    # Let's create the main body profile as a rectangle from x=0 to x=large_diameter_section_length
    # with height = set_screw_cross_section_width.
    
    # But wait, the smaller section has radius rounded_tip_arc_radius.
    # The set_screw_cross_section_width is 2.79, and rounded_tip_arc_radius is 1.78.
    # 2 * 1.78 = 3.56, which is larger than 2.79.
    # This means the smaller section is larger than the large section?
    # Let's re-read: "The larger section has radius set_screw_cross_section_width"
    # This is confusing. "radius" usually means the radius, but here it seems to mean diameter or the section is defined by this width.
    # Given the values: 2.79 vs 1.78, it's likely that 2.79 is the diameter of the large section, and 1.78 is the radius of the small section (so diameter 3.56).
    # This would mean the small section is larger than the large section, which is unusual for a set screw.
    # Alternatively, maybe "radius" is a typo and both are diameters?
    # Or maybe the "larger section" refers to the length, not the diameter?
    # Let's assume the values are as given:
    # Large section diameter = 2.79
    # Small section radius = 1.78 (so diameter = 3.56)
    # This would mean the small section is larger.
    
    # Let's proceed with the given values.
    
    # Create the main body profile sketch
    # We'll create a rectangle from x=0 to x=large_diameter_section_length with height = set_screw_cross_section_width
    # Then we'll create another rectangle from x=large_diameter_section_length to x=total_length with height = 2 * rounded_tip_arc_radius
    
    # Actually, let's create the entire profile in one sketch.
    # We'll create a rectangle for the large section and a rectangle for the small section.
    
    # Large section rectangle
    large_rect = Part.makeRectangle(params.large_diameter_section_length, params.set_screw_cross_section_width)
    large_rect.Placement = App.Placement(App.Vector(0, 0, 0))
    main_sketch.addGeometry(large_rect, False)
    
    # Small section rectangle
    small_length = params.set_screw_cross_section_length - params.large_diameter_section_length
    small_rect = Part.makeRectangle(small_length, 2 * params.rounded_tip_arc_radius)
    small_rect.Placement = App.Placement(App.Vector(params.large_diameter_section_length, 0, 0))
    main_sketch.addGeometry(small_rect, False)
    
    # Add constraints to align the rectangles
    # Center the large rectangle
    main_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    main_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
    main_sketch.addConstraint(Sketcher.Constraint("Vertical", 0))
    
    # Center the small rectangle
    main_sketch.addConstraint(Sketcher.Constraint("Center", 1, 0))
    main_sketch.addConstraint(Sketcher.Constraint("Horizontal", 1))
    main_sketch.addConstraint(Sketcher.Constraint("Vertical", 1))
    
    # Pad the main body
    main_pad = body.newObject("PartDesign::Pad", "MainPad")
    main_pad.Profile = main_sketch
    main_pad.Length = params.set_screw_cross_section_length
    main_pad.MidPlane = False
    main_pad.Reversed = False
    
    # Step 2: Create the rounded tip
    # The rounded tip is tangent to the smaller cylindrical side and the terminal face.
    # We need to create a sketch on the face of the main pad at the end.
    
    # Get the face of the main pad at the end
    # The face is at x = params.set_screw_cross_section_length
    
    # Create a sketch on the face
    tip_sketch = body.newObject("Sketcher::SketchObject", "TipSketch")
    tip_sketch.Placement = App.Placement(App.Vector(params.set_screw_cross_section_length, 0, 0))
    tip_sketch.Constraints = []
    
    # Create an arc for the rounded tip
    # The arc should have radius = rounded_tip_arc_radius
    # Center at (0, rounded_tip_arc_radius) relative to the sketch origin
    # Starting from (0, 0) and going to (0, 2*rounded_tip_arc_radius)
    
    arc = Part.Circle(App.Vector(0, params.rounded_tip_arc_radius, 0), App.Vector(0, 0, 1), params.rounded_tip_arc_radius)
    tip_sketch.addGeometry(arc, False)
    
    # Add constraints
    tip_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    tip_sketch.addConstraint(Sketcher.Constraint("Radius", 0, params.rounded_tip_arc_radius))
    
    # Pad the tip (additive)
    tip_pad = body.newObject("PartDesign::Pad", "TipPad")
    tip_pad.Profile = tip_sketch
    tip_pad.Length = params.rounded_tip_arc_radius
    tip_pad.MidPlane = False
    tip_pad.Reversed = False
    
    # Step 3: Create the screwdriver slot
    # The slot is a rectangular cut
    # Width = screwdriver_slot_length
    # Depth = screwdriver_slot_recess_depth
    
    # Create a sketch for the slot on the face of the main pad
    slot_sketch = body.newObject("Sketcher::SketchObject", "SlotSketch")
    slot_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    slot_sketch.Constraints = []
    
    # Create a rectangle for the slot
    # The slot is centered on the screw axis (y=0)
    # Width = screwdriver_slot_length
    # Height = very small (we'll use a thin rectangle)
    
    rect_slot = Part.makeRectangle(params.screwdriver_slot_length, 0.001)
    rect_slot.Placement = App.Placement(App.Vector(-params.screwdriver_slot_recess_depth, 0, 0))
    slot_sketch.addGeometry(rect_slot, False)
    
    # Add constraints
    slot_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    slot_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
    slot_sketch.addConstraint(Sketcher.Constraint("Vertical", 0))
    
    # Pocket the slot (subtractive)
    slot_pocket = body.newObject("PartDesign::Pocket", "SlotPocket")
    slot_pocket.Profile = slot_sketch
    slot_pocket.Type = "ThroughAll"
    slot_pocket.Clearance = 0.0
    slot_pocket.Definition = "ThroughAll"
    
    # Compute the document
    doc.recompute()
    
    # Save the document
    output_path = Path(__file__).resolve().parent / "answer.FCStd"
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    create_set_screw()
