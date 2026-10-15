import FreeCAD as App
import Part
import PartDesign
import Sketcher
from pathlib import Path

# --- Configuration ---
# Derived from visual analysis of the drawing:
# Scale: 1.500 (Part is scaled 1.5x in the drawing relative to the 59mm dimension)
# The drawing shows "SCALE: 1.500" at the bottom left.
# The main dimension is 59mm.
# We will build the part in its actual size (real world dimensions), not the drawing size.
#
# Features identified:
# 1. Base Plate: 59mm x 39.5mm x 10mm thickness.
# 2. C-Slot (Cutout): 15.7mm wide x 17.1mm deep x 10mm wide (removing the center section).
#    (Dimensions: Total width 59. Outer flanges 24.5 + 10 + 24.5 = 59. Inner slot width 15.7 (24.5-39.5? No. 39.5-17.1? No. Let's trace).
#    Top view: Total width 59.
#    Inner slot width: The dimension 39.5 is the overall width of the C.
#    Wait, let's re-read carefully.
#    Top View:
#    - Overall Width: 59mm.
#    - Overall Height (Front View): 39.5mm.
#    - Thickness (Side View): 10mm.
#    - Center Cutout:
#      - The drawing shows a dimension 39.5 for the total width.
#      - A dimension 17.1 for the depth of the cut.
#      - A dimension 15.7 for the width of the cut.
#    - Fillet: R0.75 on the top left corner of the cutout.
#    - Side Brackets: Two vertical brackets (thickness 5mm) extending from the sides.
#      - Height: 10mm (above the base).
#      - Thickness: 5mm.
#    - Center Post: A vertical post rising from the base in the middle.
#      - Height: 25mm (above base).
#      - Width: 15.7mm (same as slot).
#      - Thickness: 6mm.
#      - Hole: 4x 3.8mm holes (drilled through the post).
#    - Base Holes: 4x 3.8mm holes (drilled through the base).
#      - Position: 22.5mm from the left edge of the base (center of hole group).
#      - Vertical spacing: 15.5mm (center to center).
#      - Horizontal spacing: 29.1mm (center to center).
#    - Keyway: A slot on the side of the C-bracket.
#      - Width: 6mm.
#      - Length: 29.16mm.
#      - Depth: 2mm (implied by the keyway shape).
#      - Location: On the inner vertical face of the C-bracket.
#
# --- Coordinate System ---
# We will use the Base Plane (XY) for the main footprint.
# Z axis points up.
# X axis points right.
# Y axis points up (in the XY plane).

def create_servo_mount():
    # Create Document
    doc = App.newDocument("ServoMount")
    doc.Label = "MG90 Servo Mount"
    
    # Create Body
    body = PartDesign.makeBody("Body")
    body.addProperty("App::PropertyPlacement", "Placement", "Placement", "Placement of the Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # Create Parameters
    params = body.newObject("App::FeaturePython", "Parameters")
    # Actually, standard PartDesign doesn't have a "Parameters" feature object that is easy to drive from scripts without the plugin or a workaround.
    # We will use expressions directly in the feature definitions where possible, or hardcode values if not critical.
    # However, the prompt asks for named document objects. We can use App::VariableSet or just use the values directly.
    # Let's stick to direct values for robustness in headless scripts, but organize them in a feature.
    
    # --- Feature 1: Base Plate ---
    # Sketch 1: Base Plate
    sk1 = body.newObject("Sketcher::SketchObject", "sk_Base")
    sk1.Placement = App.Placement(App.Vector(0, 0, 0))
    sk1.Support = [doc.getObject("XY_Plane"), [""]] # Default is XY
    sk1.Close = True
    
    # Base dimensions: 59mm (X) x 39.5mm (Y)
    sk1.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(59, 0, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(59, 0, 0), App.Vector(59, 39.5, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(59, 39.5, 0), App.Vector(0, 39.5, 0)), False)
    sk1.addGeometry(Part.LineSegment(App.Vector(0, 39.5, 0), App.Vector(0, 0, 0)), False)
    
    # Constraints
    sk1.addConstraint(Sketcher.Constraint("Equal", 0, 1, 59)) # Length 59
    sk1.addConstraint(Sketcher.Constraint("Equal", 2, 3, 39.5)) # Width 39.5
    sk1.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 2))
    sk1.addConstraint(Sketcher.Constraint("Coincident", 2, 0, 3, 1))
    sk1.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    sk1.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 2))
    sk1.addConstraint(Sketcher.Constraint("RightAngle", 0, 1, 1, 2))
    sk1.addConstraint(Sketcher.Constraint("RightAngle", 1, 2, 2, 3))
    sk1.addConstraint(Sketcher.Constraint("RightAngle", 2, 3, 3, 0))
    sk1.addConstraint(Sketcher.Constraint("RightAngle", 3, 0, 0, 1))
    sk1.addConstraint(Sketcher.Constraint("Point", 0, 2, "OriginOfPlane"))
    sk1.addConstraint(Sketcher.Constraint("Point", 2, 3, "OriginOfPlane"))

    # Pad Base
    pad1 = body.newObject("PartDesign::Pad", "pad_Base")
    pad1.Profile = sk1
    pad1.Length = 10.0
    
    # --- Feature 2: C-Slot ---
    # Sketch 2: C-Slot
    sk2 = body.newObject("Sketcher::SketchObject", "sk_CSlot")
    sk2.Placement = App.Placement(App.Vector(0, 0, 0))
    sk2.Support = [doc.getObject("XY_Plane"), [""]]
    sk2.Close = True
    
    # C-Slot dimensions:
    # Outer boundaries: X=0 to X=59, Y=10 to Y=39.5 (10mm thick base, 10mm high C)
    # Cutout: Width 15.7, Depth 17.1.
    # Position of cutout: 
    #   Left edge of cutout: X = (59 - 15.7)/2 - wait, let's look at the drawing.
    #   The drawing shows the C-shape.
    #   The total width is 59.
    #   The inner slot width is 15.7.
    #   The slot is centered horizontally? 
    #   Looking at the drawing, there are two side brackets.
    #   The dimension 15.7 is the width of the opening.
    #   The dimension 17.1 is the depth of the opening.
    #   The dimension 39.5 is the overall width? No, 39.5 is the overall height in the front view.
    #   In the top view, the dimension 39.5 is the overall width.
    #   Wait, the drawing is confusing. Let's trace lines.
    #   Top View:
    #   - Outer box: 59 wide x 39.5 high.
    #   - Inner slot: 15.7 wide x 17.1 deep.
    #   - The slot is centered?
    #   - There is a dimension 24.5 from the left edge to the center of the left bracket?
    #   - Actually, the dimension 24.5 is the distance from the left edge to the center of the keyway?
    #   - Let's assume the slot is centered.
    #   - Left edge of slot: (59 - 15.7)/2 = 21.65.
    #   - Right edge of slot: 59 - 21.65 = 37.35.
    #   - Wait, the drawing shows a dimension 24.5 from the left edge to the center of the keyway.
    #   - The keyway is on the inner face of the left bracket.
    #   - The keyway is centered on the bracket?
    #   - The keyway width is 6mm.
    #   - So the center of the keyway is 3mm from the inner edge.
    #   - If the keyway is at X=24.5, then the inner edge of the left bracket is at 24.5 - 3 = 21.5.
    #   - This matches (59 - 15.7)/2 = 21.65 roughly.
    #   - So the slot is centered.
    
    # C-Slot Sketch Geometry
    # Outer rectangle: X=0 to 59, Y=10 to 39.5.
    # Inner rectangle (cutout): X=21.65 to 37.35, Y=10 to 27.1.
    # Fillet: R0.75 at the top left corner of the cutout.
    # Coordinates of fillet:
    #   Top-Left of cutout: (21.65, 27.1).
    #   We need to fillet the inner corner.
    #   The inner corner is at (21.65, 27.1).
    #   The fillet radius is 0.75.
    #   So the arc is from (21.65 - 0.75, 27.1) to (21.65, 27.1 - 0.75).
    #   (20.9, 27.1) to (21.65, 26.35).
    
    # Add Outer Rectangle
    sk2.addGeometry(Part.LineSegment(App.Vector(0, 10, 0), App.Vector(59, 10, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(59, 10, 0), App.Vector(59, 39.5, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(59, 39.5, 0), App.Vector(0, 39.5, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(0, 39.5, 0), App.Vector(0, 10, 0)), False)
    
    # Add Cutout Rectangle
    sk2.addGeometry(Part.LineSegment(App.Vector(21.65, 10, 0), App.Vector(37.35, 10, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(37.35, 10, 0), App.Vector(37.35, 27.1, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(37.35, 27.1, 0), App.Vector(21.65, 27.1, 0)), False)
    sk2.addGeometry(Part.LineSegment(App.Vector(21.65, 27.1, 0), App.Vector(21.65, 10, 0)), False)
    
    # Fillet
    # Create a circle or use a fillet feature?
    # Sketcher doesn't have a direct fillet command for internal corners in the same way as the feature.
    # We can add a circle and use a fillet feature later, or add a fillet feature here.
    # Let's add a fillet feature on the sketch.
    sk2.addGeometry(Part.Circle(App.Vector(21.65, 27.1 - 0.75, 0), App.Vector(0, 0, 1), 0.75), False)
    sk2.addConstraint(Sketcher.Constraint("Point", 6, 2, "OriginOfPlane")) # Center point
    sk2.addConstraint(Sketcher.Constraint("Equal", 6, 1, 0.75)) # Radius
    
    # Constraints
    # Outer rectangle constraints
    sk2.addConstraint(Sketcher.Constraint("Equal", 0, 1, 59))
    sk2.addConstraint(Sketcher.Constraint("Equal", 2, 3, 39.5))
    sk2.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 2))
    sk2.addConstraint(Sketcher.Constraint("Coincident", 2, 0, 3, 1))
    sk2.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    sk2.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 2))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 0, 1, 1, 2))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 1, 2, 2, 3))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 2, 3, 3, 0))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 3, 0, 0, 1))
    sk2.addConstraint(Sketcher.Constraint("Point", 0, 2, "OriginOfPlane"))
    sk2.addConstraint(Sketcher.Constraint("Point", 2, 3, "OriginOfPlane"))
    
    # Cutout constraints
    sk2.addConstraint(Sketcher.Constraint("Equal", 4, 5, 15.7)) # Width
    sk2.addConstraint(Sketcher.Constraint("Equal", 6, 7, 17.1)) # Depth
    sk2.addConstraint(Sketcher.Constraint("Coincident", 4, 0, 5, 1)) # Bottom left
    sk2.addConstraint(Sketcher.Constraint("Coincident", 6, 0, 7, 1)) # Bottom right
    sk2.addConstraint(Sketcher.Constraint("Coincident", 4, 1, 5, 0))
    sk2.addConstraint(Sketcher.Constraint("Coincident", 6, 1, 7, 0))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 4, 5, 5, 6))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 5, 6, 6, 7))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 6, 7, 7, 4))
    sk2.addConstraint(Sketcher.Constraint("RightAngle", 7, 4, 4, 5))
    
    # Position constraints
    sk2.addConstraint(Sketcher.Constraint("Point", 4, 2, "OriginOfPlane")) # Bottom left of cutout
    sk2.addConstraint(Sketcher.Constraint("Point", 6, 3, "OriginOfPlane")) # Bottom right of cutout
    
    # Fillet constraints
    sk2.addConstraint(Sketcher.Constraint("Point", 6, 2, "OriginOfPlane")) # Center point
    sk2.addConstraint(Sketcher.Constraint("Equal", 6, 1, 0.75)) # Radius
    
    # Pocket C-Slot
    pocket1 = body.newObject("PartDesign::Pocket", "pocket_CSlot")
    pocket1.Profile = sk2
    pocket1.Type = "ThroughAll"
    
    # --- Feature 3: Side Brackets ---
    # Sketch 3: Side Brackets
    sk3 = body.newObject("Sketcher::SketchObject", "sk_SideBrackets")
    sk3.Placement = App.Placement(App.Vector(0, 0, 0))
    sk3.Support = [doc.getObject("XY_Plane"), [""]]
    sk3.Close = True
    
    # Side Brackets dimensions:
    # Left bracket: X=0 to X=5, Y=10 to Y=20.
    # Right bracket: X=54 to X=59, Y=10 to Y=20.
    # Thickness: 5mm.
    # Height: 10mm.
    
    # Add Left Bracket
    sk3.addGeometry(Part.LineSegment(App.Vector(0, 10, 0), App.Vector(5, 10, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(5, 10, 0), App.Vector(5, 20, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(5, 20, 0), App.Vector(0, 20, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(0, 20, 0), App.Vector(0, 10, 0)), False)
    
    # Add Right Bracket
    sk3.addGeometry(Part.LineSegment(App.Vector(54, 10, 0), App.Vector(59, 10, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(59, 10, 0), App.Vector(59, 20, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(59, 20, 0), App.Vector(54, 20, 0)), False)
    sk3.addGeometry(Part.LineSegment(App.Vector(54, 20, 0), App.Vector(54, 10, 0)), False)
    
    # Constraints
    # Left bracket constraints
    sk3.addConstraint(Sketcher.Constraint("Equal", 0, 1, 5)) # Width
    sk3.addConstraint(Sketcher.Constraint("Equal", 2, 3, 10)) # Height
    sk3.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 2))
    sk3.addConstraint(Sketcher.Constraint("Coincident", 2, 0, 3, 1))
    sk3.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    sk3.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 2))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 0, 1, 1, 2))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 1, 2, 2, 3))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 2, 3, 3, 0))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 3, 0, 0, 1))
    sk3.addConstraint(Sketcher.Constraint("Point", 0, 2, "OriginOfPlane"))
    sk3.addConstraint(Sketcher.Constraint("Point", 2, 3, "OriginOfPlane"))
    
    # Right bracket constraints
    sk3.addConstraint(Sketcher.Constraint("Equal", 4, 5, 5)) # Width
    sk3.addConstraint(Sketcher.Constraint("Equal", 6, 7, 10)) # Height
    sk3.addConstraint(Sketcher.Constraint("Coincident", 4, 0, 5, 1))
    sk3.addConstraint(Sketcher.Constraint("Coincident", 6, 0, 7, 1))
    sk3.addConstraint(Sketcher.Constraint("Coincident", 4, 1, 5, 0))
    sk3.addConstraint(Sketcher.Constraint("Coincident", 6, 1, 7, 0))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 4, 5, 5, 6))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 5, 6, 6, 7))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 6, 7, 7, 4))
    sk3.addConstraint(Sketcher.Constraint("RightAngle", 7, 4, 4, 5))
    sk3.addConstraint(Sketcher.Constraint("Point", 4, 2, "OriginOfPlane"))
    sk3.addConstraint(Sketcher.Constraint("Point", 6, 3, "OriginOfPlane"))
    
    # Pad Side Brackets
    pad2 = body.newObject("PartDesign::Pad", "pad_SideBrackets")
    pad2.Profile = sk3
    pad2.Length = 10.0
    
    # --- Feature 4: Center Post ---
    # Sketch 4: Center Post
    sk4 = body.newObject("Sketcher::SketchObject", "sk_CenterPost")
    sk4.Placement = App.Placement(App.Vector(0, 0, 0))
    sk4.Support = [doc.getObject("XY_Plane"), [""]]
    sk4.Close = True
    
    # Center Post dimensions:
    # Width: 15.7mm (same as slot).
    # Thickness: 6mm.
    # Height: 25mm (above base).
    # Position: Centered on the slot.
    # X position: (59 - 15.7)/2 = 21.65.
    # Y position: 10 (on top of base).
    
    # Add Center Post
    sk4.addGeometry(Part.LineSegment(App.Vector(21.65, 10, 0), App.Vector(37.35, 10, 0)), False)
    sk4.addGeometry(Part.LineSegment(App.Vector(37.35, 10, 0), App.Vector(37.35, 35, 0)), False)
    sk4.addGeometry(Part.LineSegment(App.Vector(37.35, 35, 0), App.Vector(21.65, 35, 0)), False)
    sk4.addGeometry(Part.LineSegment(App.Vector(21.65, 35, 0), App.Vector(21.65, 10, 0)), False)
    
    # Constraints
    sk4.addConstraint(Sketcher.Constraint("Equal", 0, 1, 15.7)) # Width
    sk4.addConstraint(Sketcher.Constraint("Equal", 2, 3, 25)) # Height
    sk4.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 2))
    sk4.addConstraint(Sketcher.Constraint("Coincident", 2, 0, 3, 1))
    sk4.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    sk4.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 2))
    sk4.addConstraint(Sketcher.Constraint("RightAngle", 0, 1, 1, 2))
    sk4.addConstraint(Sketcher.Constraint("RightAngle", 1, 2, 2, 3))
    sk4.addConstraint(Sketcher.Constraint("RightAngle", 2, 3, 3, 0))
    sk4.addConstraint(Sketcher.Constraint("RightAngle", 3, 0, 0, 1))
    sk4.addConstraint(Sketcher.Constraint("Point", 0, 2, "OriginOfPlane"))
    sk4.addConstraint(Sketcher.Constraint("Point", 2, 3, "OriginOfPlane"))
    
    # Pad Center Post
    pad3 = body.newObject("PartDesign::Pad", "pad_CenterPost")
    pad3.Profile = sk4
    pad3.Length = 25.0
    
    # --- Feature 5: Center Post Holes ---
    # Sketch 5: Center Post Holes
    sk5 = body.newObject("Sketcher::SketchObject", "sk_CenterPostHoles")
    sk5.Placement = App.Placement(App.Vector(0, 0, 0))
    sk5.Support = [doc.getObject("XY_Plane"), [""]]
    sk5.Close = True
    
    # Center Post Holes dimensions:
    # 4x 3.8mm holes.
    # Position: 22.5mm from the left edge of the base (center of hole group).
    # Vertical spacing: 15.5mm (center to center).
    # Horizontal spacing: 29.1mm (center to center).
    # X position: 22.5mm.
    # Y position: 10mm (on top of base).
    
    # Add Holes
    sk5.addGeometry(Part.Circle(App.Vector(22.5, 10, 0), App.Vector(0, 0, 1), 1.9), False)
    sk5.addGeometry(Part.Circle(App.Vector(22.5, 25.5, 0), App.Vector(0, 0, 1), 1.9), False)
    sk5.addGeometry(Part.Circle(App.Vector(51.6, 10, 0), App.Vector(0, 0, 1), 1.9), False)
    sk5.addGeometry(Part.Circle(App.Vector(51.6, 25.5, 0), App.Vector(0, 0, 1), 1.9), False)
    
    # Constraints
    sk5.addConstraint(Sketcher.Constraint("Equal", 0, 1, 3.8)) # Diameter
    sk5.addConstraint(Sketcher.Constraint("Equal", 2, 3, 3.8)) # Diameter
    sk5.addConstraint(Sketcher.Constraint("Equal", 4, 5, 3.8)) # Diameter
    sk5.addConstraint(Sketcher.Constraint("Equal", 6, 7, 3.8)) # Diameter
    sk5.addConstraint(Sketcher.Constraint("Point", 0, 2, "OriginOfPlane"))
    sk5.addConstraint(Sketcher.Constraint("Point", 2, 3, "OriginOfPlane"))
    sk5.addConstraint(Sketcher.Constraint("Point", 4, 2, "OriginOfPlane"))
    sk5.addConstraint(Sketcher.Constraint("Point", 6, 3, "OriginOfPlane"))
    sk5.addConstraint(Sketcher.Constraint("Equal", 0, 2, 15.5)) # Vertical spacing
    sk5.addConstraint(Sketcher.Constraint("Equal", 0, 4, 29.1)) # Horizontal spacing
    
    # Pocket Center Post Holes
    pocket2 = body.newObject("PartDesign::Pocket", "pocket_CenterPostHoles")
    pocket2.Profile = sk5
    pocket2.Type = "ThroughAll"
    
    # --- Feature 6: Base Holes ---
    # Sketch 6: Base Holes
    sk6 = body.newObject("Sketcher::SketchObject", "sk_BaseHoles")
    sk6.Placement = App.Placement(App.Vector(0, 0, 0))
    sk6.Support = [doc.getObject("XY_Plane"), [""]]
    sk6.Close = True
    
    # Base Holes dimensions:
    # 4x 3.8mm holes.
    # Position: 22.5mm from the left edge of the base (center of hole group).
    # Vertical spacing: 15.5mm (center to center).
    # Horizontal spacing: 29.1mm (center to center).
    # X position: 22.5mm.
    # Y position: 10mm (on top of base).
    
    # Add Holes
    sk6.addGeometry(Part.Circle(App.Vector(22.5, 10, 0), App.Vector(0, 0, 1), 1.9), False)
    sk6.addGeometry(Part.Circle(App.Vector(22.5, 25.5, 0), App.Vector(0, 0, 1), 1.9), False)
    sk6.addGeometry(Part.Circle(App.Vector(51.6, 10, 0), App.Vector(0, 0, 1), 1.9), False)
    sk6.addGeometry(Part.Circle(App.Vector(51.6, 25.5, 0), App.Vector(0, 0, 1), 1.9), False)
    
    # Constraints
    sk6.addConstraint(Sketcher.Constraint("Equal", 0, 1, 3.8)) # Diameter
    sk6.addConstraint(Sketcher.Constraint("Equal", 2, 3, 3.8)) # Diameter
    sk6.addConstraint(Sketcher.Constraint("Equal", 4, 5, 3.8)) # Diameter
    sk6.addConstraint(Sketcher.Constraint("Equal", 6, 7, 3.8)) # Diameter
    sk6.addConstraint(Sketcher.Constraint("Point", 0, 2, "OriginOfPlane"))
    sk6.addConstraint(Sketcher.Constraint("Point", 2, 3, "OriginOfPlane"))
    sk6.addConstraint(Sketcher.Constraint("Point", 4, 2, "OriginOfPlane"))
    sk6.addConstraint(Sketcher.Constraint("Point", 6, 3, "OriginOfPlane"))
    sk6.addConstraint(Sketcher.Constraint("Equal", 0, 2, 15.5)) # Vertical spacing
    sk6.addConstraint(Sketcher.Constraint("Equal", 0, 4, 29.1)) # Horizontal spacing
    
    # Pocket Base Holes
    pocket3 = body.newObject("PartDesign::Pocket", "pocket_BaseHoles")
    pocket3.Profile = sk6
    pocket3.Type = "ThroughAll"
    
    # --- Feature 7: Keyway ---
    # Sketch 7: Keyway
    sk7 = body.newObject("Sketcher::SketchObject", "sk_Keyway")
    sk7.Placement = App.Placement(App.Vector(0, 0, 0))
    sk7.Support = [doc.getObject("XY_Plane"), [""]]
    sk7.Close = True
    
    # Keyway dimensions:
    # Width: 6mm.
    # Length: 29.16mm.
    # Depth: 2mm (implied by the keyway shape).
    # Location: On the inner vertical face of the C-bracket.
    # X position: 21.65mm (inner edge of left bracket).
    # Y position: 10mm (on top of base).
    
    # Add Keyway
    sk7.addGeometry(Part.LineSegment(App.Vector(21.65, 10, 0), App.Vector(21.65, 39.16, 0)), False)
    sk7.addGeometry(Part.LineSegment(App.Vector(21.65, 39.16, 0), App.Vector(27.65, 39.16, 0)), False)
    sk7.addGeometry(Part.LineSegment(App.Vector(27.65, 39.16, 0), App.Vector(27.65, 10, 0)), False)
    sk7.addGeometry(Part.LineSegment(App.Vector(27.65, 10, 0), App.Vector(21.65, 10, 0)), False)
    
    # Constraints
    sk7.addConstraint(Sketcher.Constraint("Equal", 0, 1, 6)) # Width
    sk7.addConstraint(Sketcher.Constraint("Equal", 2, 3, 29.16)) # Length
    sk7.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 2))
    sk7.addConstraint(Sketcher.Constraint("Coincident", 2, 0, 3, 1))
    sk7.addConstraint(Sketcher.Constraint("Coincident", 0, 1, 1, 0))
    sk7.addConstraint(Sketcher.Constraint("Coincident", 2, 3, 3, 2))
    sk7.addConstraint(Sketcher.Constraint("RightAngle", 0, 1, 1, 2))
    sk7.addConstraint(Sketcher.Constraint("RightAngle", 1, 2, 2, 3))
    sk7.addConstraint(Sketcher.Constraint("RightAngle", 2, 3, 3, 0))
    sk7.addConstraint(Sketcher.Constraint("RightAngle", 3, 0, 0, 1))
    sk7.addConstraint(Sketcher.Constraint("Point", 0, 2, "OriginOfPlane"))
    sk7.addConstraint(Sketcher.Constraint("Point", 2, 3, "OriginOfPlane"))
    
    # Pocket Keyway
    pocket4 = body.newObject("PartDesign::Pocket", "pocket_Keyway")
    pocket4.Profile = sk7
    pocket4.Type = "ThroughAll"
    
    # --- Feature 8: Fillet ---
    # Sketch 8: Fillet
    sk8 = body.newObject("Sketcher::SketchObject", "sk_Fillet")
    sk8.Placement = App.Placement(App.Vector(0, 0, 0))
    sk8.Support = [doc.getObject("XY_Plane"), [""]]
    sk8.Close = True
    
    # Fillet dimensions:
    # Radius: 0.75mm.
    # Location: Top left corner of the cutout.
    # X position: 21.65mm.
    # Y position: 27.1mm.
    
    # Add Fillet
    sk8.addGeometry(Part.Circle(App.Vector(21.65, 27.1 - 0.75, 0), App.Vector(0,
