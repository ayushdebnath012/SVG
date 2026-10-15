import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

def create_document():
    """Creates and configures a new FreeCAD document."""
    doc = App.newDocument("CableTieMount")
    
    # Define Named Parameters for the Base Part
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
    # "smaller square mid-layer on one side of the plate datum"
    # Interpretation: Centered on X-axis, left edge touches the plate's center line (X=0).
    # This places it in the positive X quadrant relative to the plate center.
    sk_mid = body.newObject("Sketcher::SketchObject", "Sketch_MidLayer")
    sk_mid.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_mid.Support = (doc.getObject("XY_Plane"), [])
    sk_mid.MapMode = "FlatFace"
    
    # Square: 18.03 x 18.03
    sk_mid.addGeometry(Part.makeRectangle(18.03, 18.03), False)
    sk_mid.constrain(0, "Horizontal2Point", 0, 2)
    sk_mid.constrain(1, "Vertical2Point", 0, 3)
    # Constrain bottom edge to X-axis (Y=0)
    sk_mid.constrain(0, "PointOnLine", 0, 2, "XAxis")
    # Constrain left edge to Y-axis (X=0)
    sk_mid.constrain(1, "PointOnLine", 0, 3, "YAxis")
    
    # 4. Retention Frame Sketch (Centered)
    # "centered hollow square retention frame"
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
    sk_frame.constrain(0, "PointOnLine", 0, 1, "XAxis") # Outer Center X
    sk_frame.constrain(1, "PointOnLine", 0, 2, "YAxis") # Outer Center Y
    sk_frame.constrain(2, "PointOnLine", 0, 1, "XAxis") # Inner Center X
    sk_frame.constrain(3, "PointOnLine", 0, 2, "YAxis") # Inner Center Y
    # Coincide centers
    sk_frame.constrain(0, "Coincident", 2, 1)
    sk_frame.constrain(1, "Coincident", 3, 2)
    
    # 5. Primary Slot Sketch
    # "Rectangular through-slot crosses the mount center and overlaps the center hole."
    # Width 1.52. Center offset 0.35 from mount center.
    # Orientation: Vertical (along Y), centered at X = 0.35.
    sk_slot = body.newObject("Sketcher::SketchObject", "Sketch_Slot")
    sk_slot.Placement = App.Placement(App.Vector(0.35, 0, 0))
    sk_slot.Support = (doc.getObject("XY_Plane"), [])
    sk_slot.MapMode = "FlatFace"
    
    # Rectangle: Length 5.33 (Height), Width 1.52
    sk_slot.addGeometry(Part.makeRectangle(5.33, 1.52), False)
    # Constrain dimensions
    sk_slot.constrain(0, "Vertical2Point", 0, 2)
    sk_slot.constrain(1, "Horizontal2Point", 0, 3)
    # Center Y of rect to Y-axis (Global Y=0)
    sk_slot.constrain(0, "PointOnLine", 0, 1, "XAxis")
    # The sketch placement is at (0.35, 0). The rectangle is centered at (0,0) in its own space.
    # So global center is (0.35, 0). This matches "offset 0.35".
    
    # 6. Tie Slots Sketch
    # "Four shallow tie slots are centered across the frame walls with fourfold symmetry"
    # Depth is 1.27.
    # We will create a sketch on the top face of the frame (Z = 4.76).
    sk_tie = body.newObject("Sketcher::SketchObject", "Sketch_TieSlots")
    sk_tie.Placement = App.Placement(App.Vector(0, 0, 4.76))
    sk_tie.Support = (doc.getObject("XY_Plane"), [])
    sk_tie.MapMode = "FlatFace"
    
    # Frame outer half-width: 11.18 / 2 = 5.59
    # Slot length: 5.33. Half-length: 2.665.
    # Slots are centered on the frame edges.
    # Positions:
    # Top: Y = 5.59 - 2.665 = 2.925
    # Bottom: Y = -5.59 + 2.665 = -2.925
    # Right: X = 5.59 - 2.665 = 2.925
    # Left: X = -5.59 + 2.665 = -2.925
    
    # Top Slot
    sk_tie.addGeometry(Part.makeRectangle(1.52, 5.33), False) # Width X, Height Y
    sk_tie.constrain(0, "Horizontal2Point", 0, 2)
    sk_tie.constrain(1, "Vertical2Point", 0, 3)
    sk_tie.constrain(0, "PointOnLine", 0, 1, "YAxis") # Center X
    sk_tie.constrain(1, "PointOnLine", 0, 2, "YAxis") # Center Y (relative to sketch)
    # Move sketch to Y = 2.925
    sk_tie.Placement = App.Placement(App.Vector(0, 2.925, 4.76))
    sk_tie.updatePlacement()
    
    # Bottom Slot
    sk_tie.addGeometry(Part.makeRectangle(1.52, 5.33), False)
    sk_tie.constrain(0, "Horizontal2Point", 0, 2)
    sk_tie.constrain(1, "Vertical2Point", 0, 3)
    sk_tie.constrain(0, "PointOnLine", 0, 1, "YAxis")
    sk_tie.constrain(1, "PointOnLine", 0, 2, "YAxis")
    sk_tie.Placement = App.Placement(App.Vector(0, -2.925, 4.76))
    sk_tie.updatePlacement()
    
    # Right Slot
    sk_tie.addGeometry(Part.makeRectangle(5.33, 1.52), False) # Width X, Height Y
    sk_tie.constrain(0, "Horizontal2Point", 0, 2)
    sk_tie.constrain(1, "Vertical2Point", 0, 3)
    sk_tie.constrain(0, "PointOnLine", 0, 1, "XAxis")
    sk_tie.constrain(1, "PointOnLine", 0, 2, "XAxis")
    sk_tie.Placement = App.Placement(App.Vector(2.925, 0, 4.76))
    sk_tie.updatePlacement()
    
    # Left Slot
    sk_tie.addGeometry(Part.makeRectangle(5.33, 1.52), False)
    sk_tie.constrain(0, "Horizontal2Point", 0, 2)
    sk_tie.constrain(1, "Vertical2Point", 0, 3)
    sk_tie.constrain(0, "PointOnLine", 0, 1, "XAxis")
    sk_tie.constrain(1, "PointOnLine", 0, 2, "XAxis")
    sk_tie.Placement = App.Placement(App.Vector(-2.925, 0, 4.76))
    sk_tie.updatePlacement()

def build_base_features(doc):
    """Creates the PartDesign features for the base part."""
    body = doc.getObject("Body")
    
    # 1. Pad Base Plate
    pad_plate = body.newObject("PartDesign::Pad", "Pad_BasePlate")
    pad_plate.Profile = body.getObject("Sketch_BasePlate")
    pad_plate.Length = doc.BasePlateThickness
    pad_plate.Type = "Blind"
    
    # 2. Pocket Hole
    pocket_hole = body.newObject("PartDesign::Pocket", "Pocket_Hole")
    pocket_hole.Profile = body.getObject("Sketch_Hole")
    pocket_hole.Type = "ThroughAll"
    
    # 3. Pad Mid Layer
    pad_mid = body.newObject("PartDesign::Pad", "Pad_MidLayer")
    pad_mid.Profile = body.getObject("Sketch_MidLayer")
    pad_mid.Length = doc.MidLayerThickness
    pad_mid.Type = "Blind"
    
    # 4. Pad Retention Frame
    pad_frame = body.newObject("PartDesign::Pad", "Pad_Frame")
    pad_frame.Profile = body.getObject("Sketch_Frame")
    pad_frame.Length = doc.RetentionFrameHeight
    pad_frame.Type = "Blind"
    
    # 5. Pocket Primary Slot
    pocket_slot = body.newObject("PartDesign::Pocket", "Pocket_Slot")
    pocket_slot.Profile = body.getObject("Sketch_Slot")
    pocket_slot.Type = "ThroughAll"
    
    # 6. Pocket Tie Slots
    pocket_tie = body.newObject("PartDesign::Pocket", "Pocket_TieSlots")
    pocket_tie.Profile = body.getObject("Sketch_TieSlots")
    pocket_tie.Type = "Blind"
    pocket_tie.Length = doc.WallTieSlotDepth

def build_edit_features(doc):
    """Creates the PartDesign features for the corner wedges (Edit Step)."""
    body = doc.getObject("Body")
    
    # Corner Wedge Width
    wedge_width = 1.02
    
    # We need to create 4 wedges.
    # Each wedge is a strip along the diagonal of the corner.
    # The wedge starts at the base plate corner and ends at the frame corner.
    # It is raised to the top of the frame.
    
    # Helper to create a wedge
    def create_wedge(sketch_obj, offset_x, offset_y, angle_deg):
        # Create a sketch for the wedge profile
        # The profile is a rectangle along the diagonal.
        # We need to define the rectangle in the sketch plane.
        
        # Calculate the length of the wedge along the diagonal.
        # Distance from plate corner to frame corner.
        # Plate corner: (offset_x, offset_y)
        # Frame corner: (offset_x + 11.18/2, offset_y + 11.18/2)
        # Wait, the frame is centered at (0,0).
        # Plate corner is at (9.525, 9.525).
        # Frame corner is at (5.59, 5.59).
        # Vector from plate to frame: (5.59 - 9.525, 5.59 - 9.525) = (-3.935, -3.935).
        # Length = sqrt(3.935^2 + 3.935^2) = 3.935 * sqrt(2) = 5.57.
        
        # Let's calculate the exact length.
        # Plate half: 19.05 / 2 = 9.525
        # Frame half: 11.18 / 2 = 5.59
        # Delta = 9.525 - 5.59 = 3.935
        # Length = 3.935 * sqrt(2)
        
        delta = 3.935
        length = delta * math.sqrt(2)
        
        # Create a rectangle of size (length, wedge_width)
        # The rectangle should be centered on the diagonal line.
        # The diagonal line goes from (9.525, 9.525) to (5.59, 5.59).
        # Midpoint of the diagonal: ((9.525+5.59)/2, (9.525+5.59)/2) = (7.5575, 7.5575)
        
        # We will create a sketch at the midpoint, rotated 45 degrees.
        # Then place a rectangle centered at (0,0) in the sketch.
        
        sk_wedge = body.newObject("Sketcher::SketchObject", f"Sketch_Wedge_{offset_x}_{offset_y}")
        sk_wedge.Placement = App.Placement(App.Vector(offset_x, offset_y, 0))
        sk_wedge.Support = (doc.getObject("XY_Plane"), [])
        sk_wedge.MapMode = "FlatFace"
        
        # Add rectangle
        sk_wedge.addGeometry(Part.makeRectangle(length, wedge_width), False)
        
        # Constrain dimensions
        sk_wedge.constrain(0, "Horizontal2Point", 0, 2)
        sk_wedge.constrain(1, "Vertical2Point", 0, 3)
        
        # Center the rectangle on the sketch origin (which is the midpoint)
        sk_wedge.constrain(0, "PointOnLine", 0, 1, "XAxis")
        sk_wedge.constrain(1, "PointOnLine", 0, 2, "YAxis")
        
        # Rotate the sketch 45 degrees to align with the diagonal
        # Rotation around Z axis
        sk_wedge.Placement = App.Placement(
            App.Vector(offset_x, offset_y, 0),
            App.Rotation(App.Vector(0, 0, 1), math.radians(45))
        )
        sk_wedge.updatePlacement()
        
        return sk_wedge

    # Create 4 sketches for the 4 corners
    # Top-Right: (9.525, 9.525)
    sk_tr = create_wedge(9.525, 9.525, 45)
    # Top-Left: (-9.525, 9.525) -> Diagonal is -135 deg
    sk_tl = create_wedge(-9.525, 9.525, -135)
    # Bottom-Right: (9.525, -9.525) -> Diagonal is -45 deg
    sk_br = create_wedge(9.525, -9.525, -45)
    # Bottom-Left: (-9.525, -9.525) -> Diagonal is 135 deg
    sk_bl = create_wedge(-9.525, -9.525, 135)
    
    # Now create the Pad features for each wedge
    # The wedge is a strip along the diagonal.
    # We need to pad it from the base plate face (Z=0) to the top of the frame (Z=4.76).
    # However, the sketch is on the base plate face.
    # We need to ensure the pad direction is correct.
    
    # Pad Top-Right
    pad_wedge_tr = body.newObject("PartDesign::Pad", "Pad_Wedge_TR")
    pad_wedge_tr.Profile = sk_tr
    pad_wedge_tr.Length = doc.RetentionFrameHeight
    pad_wedge_tr.Type = "Blind"
    # The sketch is on the top face of the plate (Z=0).
    # We need to pad in the +Z direction.
    # The sketch normal is +Z.
    # So default pad direction is correct.
    
    # Pad Top-Left
    pad_wedge_tl = body.newObject("PartDesign::Pad", "Pad_Wedge_TL")
    pad_wedge_tl.Profile = sk_tl
    pad_wedge_tl.Length = doc.RetentionFrameHeight
    pad_wedge_tl.Type = "Blind"
    
    # Pad Bottom-Right
    pad_wedge_br = body.newObject("PartDesign::Pad", "Pad_Wedge_BR")
    pad_wedge_br.Profile = sk_br
    pad_wedge_br.Length = doc.RetentionFrameHeight
    pad_wedge_br.Type = "Blind"
    
    # Pad Bottom-Left
    pad_wedge_bl = body.newObject("PartDesign::Pad", "Pad_Wedge_BL")
    pad_wedge_bl.Profile = sk_bl
    pad_wedge_bl.Length = doc.RetentionFrameHeight
    pad_wedge_bl.Type = "Blind"

def main():
    # Step 1: Create Document and Build Base
    doc = create_document()
    build_base_part(doc)
    build_base_features(doc)
    
    # Save Base
    script_path = Path(__file__).resolve()
    base_path = script_path.with_name(f"{script_path.stem}_base.FCStd")
    doc.saveAs(str(base_path))
    
    # Step 2: Apply Edit
    build_edit_features(doc)
    
    # Save Edit
    edit_path = script_path.with_name(f"{script_path.stem}_edit.FCStd")
    doc.saveAs(str(edit_path))
    
    # Recompute to ensure everything is updated
    doc.recompute()

if __name__ == "__main__":
    main()
