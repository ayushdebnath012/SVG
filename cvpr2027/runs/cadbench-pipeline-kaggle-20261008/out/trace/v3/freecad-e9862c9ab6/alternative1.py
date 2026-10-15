import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

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
    # This sketch will define the cross-section of the screw body
    # We'll use a rectangle that extends beyond the tip to allow for the rounded tip creation later
    
    base_sketch = body.newObject("Sketcher::SketchObject", "BaseProfileSketch")
    base_sketch.Plane = doc.addObject("Part::Plane", "XY_Plane")
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.Constraints = []
    base_sketch.AddGeometry = []
    
    # We need to create the profile geometry first
    # The profile will be a rectangle from center to the end of the large diameter section
    # Then we'll handle the rounded tip separately
    
    # Let's create a rectangle for the main body
    # The large diameter section extends from the slotted end (left) for large_diameter_section_length
    # The total length is set_screw_cross_section_length
    # So the rounded tip is at the right end
    
    # Calculate coordinates
    # Let's place the slotted end at X = 0
    # Large diameter section ends at X = large_diameter_section_length
    # Total length = set_screw_cross_section_length
    # Rounded tip is at X = set_screw_cross_section_length
    
    # The rounded tip is tangent to the smaller cylindrical side and terminal face
    # This means the arc connects the smaller cylinder to the flat end
    
    # Let's create the base profile sketch
    # We'll use a rectangle that represents the main body
    # Height = set_screw_cross_section_width
    # Width = large_diameter_section_length + some extra for the tip
    
    # Actually, let's think about this differently.
    # We need to create:
    # 1. A cylinder for the large diameter section
    # 2. A cylinder for the smaller section
    # 3. A rounded tip
    # 4. A pocket for the screwdriver slot
    
    # Let's create the base profile sketch for the main body
    # We'll create a rectangle from (0, -width/2) to (large_diameter_section_length + rounded_tip_arc_radius, width/2)
    
    base_sketch.Plane = "XY_Plane"
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create rectangle geometry
    # The rectangle will go from x=0 to x=large_diameter_section_length + rounded_tip_arc_radius
    # Height = set_screw_cross_section_width
    
    rect = Part.makeRectangle(large_diameter_section_length + params.rounded_tip_arc_radius, params.set_screw_cross_section_width)
    rect.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.addGeometry(rect, False)
    
    # Add constraints
    base_sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    base_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
    base_sketch.addConstraint(Sketcher.Constraint("Vertical", 0))
    
    # Pad the base profile
    pad = body.newObject("PartDesign::Pad", "MainPad")
    pad.Profile = base_sketch
    pad.Length = large_diameter_section_length + params.rounded_tip_arc_radius
    pad.MidPlane = False
    pad.Reversed = False
    
    # Now let's create the rounded tip
    # The rounded tip is tangent to both the smaller cylindrical side and the terminal face
    # We need to create a sketch on the face of the main pad
    
    # Get the face of the main pad
    # The face is at x = large_diameter_section_length + rounded_tip_arc_radius
    
    # Create a sketch on the face
    tip_sketch = body.newObject("Sketcher::SketchObject", "TipSketch")
    tip_sketch.Plane = "XY_Plane" # We'll reposition this later
    tip_sketch.Placement = App.Placement(App.Vector(large_diameter_section_length + params.rounded_tip_arc_radius, 0, 0))
    tip_sketch.Constraints = []
    
    # Create the arc for the rounded tip
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
    
    # Now let's create the screwdriver slot
    # The slot is a rectangular cut
    # Width = screwdriver_slot_length
    # Depth = screwdriver_slot_recess_depth
    
    # Create a sketch for the slot on the face of the main pad
    slot_sketch = body.newObject("Sketcher::SketchObject", "SlotSketch")
    slot_sketch.Plane = "XY_Plane"
    slot_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    slot_sketch.Constraints = []
    
    # Create a rectangle for the slot
    rect_slot = Part.makeRectangle(params.screwdriver_slot_length, 0.001) # Very thin rectangle
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
