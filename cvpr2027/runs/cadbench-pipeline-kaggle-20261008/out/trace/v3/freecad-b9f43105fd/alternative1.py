import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def create_document():
    """Creates and configures a new FreeCAD document."""
    doc = App.newDocument("CableTieMount")
    
    # Define Named Parameters for the Base Part
    params = doc.addObject("App::Property", "Parameters")
    # We will use direct property assignment to named variables within the Body
    # to keep the tree clean, but logically they act as parameters.
    
    # Base Dimensions
    doc.BasePlateSideLength = 19.05
    doc.CenterHoleDiameter = 4.12
    doc.BasePlateThickness = 1.27
    doc.MidLayerSideLength = 18.03
    doc.MidLayerThickness = 0.79
    doc.RetentionFrameInner = 8.64
    doc.RetentionFrameOuter = 11.18
    doc.RetentionFrameHeight = 4.76
    doc.TieSlotLength = 5.33
    doc.PrimarySlotWidth = 1.52
    doc.PrimarySlotOffset = 0.35
    doc.WallTieSlotDepth = 1.27
    
    return doc

def build_base_part(doc):
    """Builds the base part geometry using PartDesign features."""
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Label = "Body"
    
    # 1. Base Plate Sketch (XY Plane)
    sk_plate = body.newObject("Sketcher::SketchObject", "Sketch_BasePlate")
    sk_plate.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_plate.Support = (doc.getObject("XY_Plane"), [])
    sk_plate.MapMode = "FlatFace"
    
    # Rectangle: 19.05 x 19.05
    sk_plate.addGeometry(Part.makeRectangle(19.05, 19.05), False)
    sk_plate.constrain(0, "Horizontal2Point", 0, 2)
    sk_plate.constrain(1, "Vertical2Point", 0, 3)
    sk_plate.constrain(0, "Coincident", 0, 2, 1, 1) # Center origin
    sk_plate.constrain(1, "Coincident", 0, 3, 1, 1)
    
    # 2. Center Hole Sketch (Same XY Plane)
    sk_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
    sk_hole.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_hole.Support = (doc.getObject("XY_Plane"), [])
    sk_hole.MapMode = "FlatFace"
    
    # Circle: 4.12 diameter
    sk_hole.addGeometry(Part.makeCircle(2.06, App.Vector(0, 0, 0), App.Vector(0, 0, 1)), False)
    sk_hole.constrain(0, "Horizontal2Point", 0, 2) # Center X
    sk_hole.constrain(1, "Vertical2Point", 0, 3)   # Center Y
    
    # 3. Mid Layer Sketch (Offset from Base)
    # The prompt says "smaller square mid-layer on one side of the plate datum".
    # Let's place it on the positive X side, centered vertically, touching the center line.
    # Actually, "datum" usually implies the center or a specific edge. 
    # Given "on one side", let's assume it sits on the positive X edge of the base plate.
    # But to be robust, let's put it centered vertically on the +X side, touching the right edge.
    
    sk_mid = body.newObject("Sketcher::SketchObject", "Sketch_MidLayer")
    sk_mid.Placement = App.Placement(App.Vector(19.05/2, 0, 0))
    sk_mid.Support = (doc.getObject("XY_Plane"), [])
    sk_mid.MapMode = "FlatFace"
    
    # Square: 18.03 x 18.03
    sk_mid.addGeometry(Part.makeRectangle(18.03, 18.03), False)
    sk_mid.constrain(0, "Horizontal2Point", 0, 2)
    sk_mid.constrain(1, "Vertical2Point", 0, 3)
    # Constrain to Base Plate Right Edge (Line 3 is top of plate, need edge geometry)
    # Sketcher constraints work on geometry indices. 
    # Let's constrain to the Center X axis to ensure symmetry, and place it relative to plate.
    # Re-evaluating "on one side of the plate datum". Let's assume datum is the center.
    # So it's centered at (0,0) but offset? Or attached to an edge?
    # "on one side of the plate datum" -> Attached to the edge defined by the datum?
    # Let's attach it to the positive X edge of the base plate.
    # We need to get the edge of the plate sketch.
    # For simplicity in script without complex object retrieval of edges:
    # We will constrain the mid-layer square to be centered on the X-axis (Y=0) and its left edge touches the plate right edge (X=9.525).
    # Wait, 18.03 width. If left edge is at 9.525, it goes to 27.555.
    # Let's assume "datum" is the center. So it is centered at X=0, Y=0 but only exists on one side? No, that's half a square.
    # Interpretation: A full square centered at (0,0) is too big (18.03 vs 19.05).
    # Interpretation: A square centered at (0,0) is too small.
    # Interpretation: A square placed on the +X side, centered vertically.
    # Let's attach the left edge of the mid-layer to the center vertical axis? No.
    # Let's attach the left edge to the right edge of the base plate.
    # To do this programmatically:
    # We need the line segment of the base plate at X=9.525.
    # Since we can't easily query the base sketch edge index without running, we will use a constraint to the base plate geometry.
    # Actually, let's just place it centered at (0,0) but offset by a parameter?
    # Let's try: Center of mid-layer is at (18.03/2, 0). Left edge touches X=0.
    # This puts it "on one side" of the center datum.
    sk_mid.addConstraint(Sketcher.Constraint("PointOnLine", 0, 1, "XAxis")) # Center Y
    # Let's constrain the bottom edge to the X-axis to fix it vertically.
    sk_mid.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, "XAxis")) 
    
    # Let's refine: "on one side of the plate datum". Let's assume the datum is the center line.
    # So the square is centered at X = 9.525 (right edge of plate)? No.
    # Let's assume it's centered at X=0, Y=0. It's 18.03mm. Plate is 19.05mm.
    # It fits inside. "On one side" might mean it's a feature that sticks out? 
    # Or maybe the "plate datum" is the edge.
    # Let's go with: The mid-layer is centered on the X-axis, and its left edge is coincident with the Base Plate's right edge? No, that would be outside.
    # Let's go with: The mid-layer is centered on the X-axis, and its left edge is coincident with the Base Plate's center line? 
    # Then it occupies X: 0 to 18.03. This is "on one side" (positive X) of the datum (center).
    sk_mid.addConstraint(Sketcher.Constraint("Coincident", 0, 1, "XAxis")) # Center Y
    sk_mid.addConstraint(Sketcher.Constraint("Distance", 0, 2, "XAxis", 0)) # Bottom on axis
    # Constrain left edge to X=0? 
    # Let's just define it centered at (9.525, 0).
    # This seems the most logical "on one side" interpretation.
    # We'll use a coordinate constraint for the center point.
    # Actually, let's just make it centered at (0,0) but the prompt says "on one side".
    # Let's assume the user means the mid-layer is centered on the X-axis, and its left edge touches the base plate's center line?
    # No, let's assume the mid-layer is centered at (0,0) and the "on one side" refers to a visual layout or it's a specific feature.
    # Let's stick to the most robust interpretation: Centered at (0,0) but maybe the prompt implies it's offset.
    # Let's try: Center at (18.03/2, 0).
    # This puts the square between X=0 and X=18.03.
    # Let's enforce this by constraining the bottom edge to Y=0 and the left edge to X=0.
    # But the sketch is relative.
    # Let's set the sketch placement at (9.525, 0) and make the rectangle symmetric around it?
    # No, simpler: Sketch at (0,0). Rectangle 18.03 wide.
    # Constrain: Bottom edge to X-axis. Left edge to Y-axis (X=0).
    # This places it in the first quadrant relative to the plate center.
    sk_mid.addConstraint(Sketcher.Constraint("PointOnLine", 0, 2, "XAxis"))
    sk_mid.addConstraint(Sketcher.Constraint("PointOnLine", 0, 3, "YAxis"))
    # Now the rectangle is from (0,0) to (18.03, 18.03).
    
    # 4. Retention Frame Sketch (Offset from Base)
    # "centered hollow square retention frame extending toward the opposite side".
    # Opposite to the mid-layer? Mid-layer was on +X (0 to 18.03).
    # So frame should be on -X side? Or centered?
    # "Centered hollow square... extending toward the opposite side".
    # This implies the frame is centered on the Y-axis, but shifted in X towards negative?
    # Or the whole frame is centered, but it extends "toward" the mid-layer?
    # Let's assume the frame is centered at (0,0) but the "extending" part is a specific feature?
    # No, "centered hollow square... extending toward the opposite side".
    # Maybe the frame is centered on the Y-axis, and its X-position is negative?
    # Let's assume the frame is centered at (-11.18/2, 0)? No.
    # Let's assume the frame is centered at (0,0) but the "extending" description is flavor text for the slot overlap?
    # "Rectangular through-slot crosses the mount center and overlaps the center hole."
    # "Four shallow tie slots are centered across the frame walls".
    # Okay, let's build the frame as a centered hollow square (inner 8.64, outer 11.18).
    # But "extending toward the opposite side".
    # Maybe the frame is NOT centered at (0,0).
    # Let's assume the frame is centered on the X-axis, but shifted to the negative side.
    # Shift amount? Let's assume the gap between MidLayer right edge and Frame left edge is symmetric?
    # MidLayer ends at 18.03. Plate ends at 19.05.
    # If Frame is centered at (0,0), it fits.
    # Let's assume the "extending" means the frame is larger than the hole and sits centrally.
    # We will build a centered hollow square for the frame.
    
    sk_frame = body.newObject("Sketcher::SketchObject", "Sketch_Frame")
    sk_frame.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_frame.Support = (doc.getObject("XY_Plane"), [])
    sk_frame.MapMode = "FlatFace"
    
    # Outer Square: 11.18 x 11.18
    sk_frame.addGeometry(Part.makeRectangle(11.18, 11.18), False)
    # Inner Square: 8.64 x 8.64
    sk_frame.addGeometry(Part.makeRectangle(8.64, 8.64), False)
    
    # Constraints for Frame:
    # Center both squares on X and Y axes.
    # Inner square constraints
    sk_frame.addConstraint(Sketcher.Constraint("PointOnLine", 1, 1, "XAxis"))
    sk_frame.addConstraint(Sketcher.Constraint("PointOnLine", 1, 2, "YAxis"))
    # Outer square constraints
    sk_frame.addConstraint(Sketcher.Constraint("PointOnLine", 2, 1, "XAxis"))
    sk_frame.addConstraint(Sketcher.Constraint("PointOnLine", 2, 2, "YAxis"))
    # Coincide centers? They share the same center (0,0) by default if placed at 0,0.
    # But to be safe, let's align them.
    sk_frame.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 2, 1))
    sk_frame.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 2))
    
    # 5. Primary Slot Sketch
    # "Rectangular through-slot crosses the mount center".
    # Width 1.52. Center offset 0.35 from mount center.
    # Orientation? "Crosses the mount center". Could be X or Y.
    # Given the "extending toward opposite side" frame, maybe the slot is perpendicular to the mid-layer direction?
    # Mid-layer was +X. Frame is centered.
    # Let's make the slot vertical (along Y), centered at X = 0.35.
    
    sk_slot = body.newObject("Sketcher::SketchObject", "Sketch_Slot")
    sk_slot.Placement = App.Placement(App.Vector(0.35, 0, 0))
    sk_slot.Support = (doc.getObject("XY_Plane"), [])
    sk_slot.MapMode = "FlatFace"
    
    # Rectangle: Length 5.33, Width 1.52
    sk_slot.addGeometry(Part.makeRectangle(5.33, 1.52), False)
    # Orientation: Vertical (along Y).
    # Constrain width to Y-axis? No, width is along Y?
    # If vertical, height is along Y (5.33), width along X (1.52).
    # Let's make height 5.33 along Y, width 1.52 along X.
    # Center at X=0, Y=0 relative to sketch placement?
    # We placed sketch at (0.35, 0).
    # Rectangle centered at (0,0) in sketch coords -> Global X = 0.35.
    # Constrain:
    # Center Y of rect to Y-axis (Global Y=0).
    # Center X of rect to ... well, the sketch placement handles X.
    # We need to constrain the rectangle dimensions.
    sk_slot.addConstraint(Sketcher.Constraint("Vertical2Point", 0, 2)) # Height vertical
    sk_slot.addConstraint(Sketcher.Constraint("Horizontal2Point", 0, 3)) # Width horizontal
    sk_slot.addConstraint(Sketcher.Constraint("PointOnLine", 0, 1, "XAxis")) # Center Y
    # The sketch placement is at (0.35, 0). The rectangle is centered at (0,0) in its own space.
    # So global center is (0.35, 0). This matches "offset 0.35".
    
    # 6. Tie Slots Sketch
    # "Four shallow tie slots are centered across the frame walls with fourfold symmetry".
    # "recess from the exposed frame face".
    # Depth is 1.27.
    # We can do this with a Pad on the frame sketch, or a separate sketch + Pocket.
    # Since they are "shallow", a Pocket on the top face of the frame (which is at Z=4.76) is best.
    # But we need to define the profile first.
    # Profile: 4 rectangles, centered on the frame edges.
    # Frame outer side length 11.18. Half = 5.59.
    # Slot length 5.33.
    # If centered on the edge, the slot extends 5.33/2 = 2.665 from the edge.
    # This overlaps the inner frame (8.64/2 = 4.32).
    # So the slot is inside the frame wall.
    
    sk_tie = body.newObject("Sketcher::SketchObject", "Sketch_TieSlots")
    sk_tie.Placement = App.Placement(App.Vector(0, 0, 4.76)) # On top of frame
    sk_tie.Support = (doc.getObject("XY_Plane"), [])
    sk_tie.MapMode = "FlatFace"
    
    # Add 4 rectangles.
    # We need to calculate positions.
    # Frame outer: +/- 5.59. Inner: +/- 4.32.
