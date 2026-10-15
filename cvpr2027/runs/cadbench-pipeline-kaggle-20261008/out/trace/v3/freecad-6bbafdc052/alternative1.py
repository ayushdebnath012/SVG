import FreeCAD as App
import Part
from pathlib import Path
import os
import math

def create_l_shape_sketch_on_xy_plane(body, width, height, leg_width, fillet_radius):
    """Creates the L-shaped profile on the XY plane."""
    sketch_name = "BaseProfile_Sketch"
    sketch = body.newObject("Sketcher::SketchObject", sketch_name)
    
    # Attach to XY Plane
    x_plane = App.ActiveDocument.getObject("XY_Plane")
    if not x_plane:
        raise RuntimeError("XY_Plane not found in document.")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.Placement.toPlaced(sketch.Placement, sketch.Placement) # Ensure it's attached
    # Explicitly set attachment for clarity
    sketch.AttachmentSupport = [x_plane]
    sketch.Constraints = [] # Clear previous constraints if any
    sketch.Type = "PlanarSketch"
    
    # Add lines and points
    # Coordinates:
    # Bottom-Left (Origin): 0, 0
    # Bottom-Right (Outer Corner): width, 0
    # Top-Right (Inner Corner): width, height - leg_width
    # Top-Left (Inner Corner): leg_width, height - leg_width
    # Top-Left (Outer Corner): leg_width, height
    # Wait, description: "horizontal flange spans bracket_overall_width and rises by flange_thickness"
    # "centered vertical leg has leg_width and continues to bracket_overall_height"
    # "tangent inside fillet... joins the flange upper face to the leg's negative-X face"
    
    # Let's define vertices based on standard L-bracket orientation (L facing bottom-left relative to bounding box? No, L facing top-right usually).
    # Let's assume standard L-shape: 
    # Horizontal part at bottom (Y=0 to Y=flange_thickness) from X=0 to X=width.
    # Vertical part on left (X=0 to X=leg_width) from Y=0 to Y=height.
    # Intersection is top-left of horizontal, bottom-left of vertical.
    # Fillet is inside the corner (0, flange_thickness).
    
    # Let's refine based on "negative-X end" and "positive-X face" in edit instructions.
    # Edit: "Cut... from its negative-X end toward positive X". This implies the flange exists at negative X.
    # Edit: "centered vertical leg... flush with the leg's positive-X face". This implies the leg is on the positive X side of the flange start? 
    # Or the leg is a separate element.
    
    # Let's re-read carefully: "L-shaped side profile... horizontal flange spans... rises... centered vertical leg... continues... tangent inside fillet... joins flange upper face to leg's negative-X face".
    # This implies the corner is on the left side.
    # Let's place the origin at the inner corner of the fillet.
    # Flange: goes Right (Positive X) and Up (Positive Z? No, Y in global).
    # Let's use Global XY plane. X is Right, Y is Up.
    # Flange: Thickness in Y. Length in X.
    # Leg: Width in X. Height in Y.
    # If Flange is bottom, Leg is left.
    # Flange: Y from 0 to flange_thickness. X from 0 to width.
    # Leg: Y from 0 to height. X from 0 to leg_width.
    # Inner corner is at (leg_width, flange_thickness).
    # "leg's negative-X face" would be the face at X=0.
    # "flange upper face" is at Y=flange_thickness.
    # Fillet joins (0, flange_thickness) to (leg_width, 0)? No, that's outside.
    # Fillet joins (leg_width, flange_thickness) to... wait.
    
    # Alternative Interpretation (Standard Bracket):
    # Leg is vertical on the LEFT. Flange is horizontal on the BOTTOM.
    # Corner is Top-Left of the Leg / Top-Left of Flange? No.
    # Corner is Top-Right of Leg / Top-Left of Flange?
    # Let's try: Leg is vertical strip at X=0. Width leg_width. Height height.
    # Flange is horizontal strip at Y=0. Width width. Height flange_thickness.
    # They overlap in the bottom-left rectangle.
    # Inner corner is at (leg_width, flange_thickness).
    # "leg's negative-X face": The face of the leg at X=0.
    # "flange upper face": The face of the flange at Y=flange_thickness.
    # Fillet joins "flange upper face" (Y=flange_thickness) to "leg's negative-X face" (X=0)?
    # That would be the outer corner at (0, flange_thickness).
    # But the description says "tangent inside fillet".
    # Maybe the L is inverted? Leg on Right, Flange on Top?
    
    # Let's look at the Edit Instruction again for clues on orientation.
    # "Cut a rectangular opening through the horizontal flange from its negative-X end toward positive X."
    # "Cut... through the vertical leg... flush with the leg's positive-X face".
    # This implies the Leg is to the RIGHT of the Flange start?
    # If Flange is on bottom (Y=0), and extends to Positive X.
    # "negative-X end" of flange is X=0.
    # "leg's positive-X face": If Leg is to the right of X=0, its positive-X face is at X=leg_width.
    # If Leg is to the left (X=0 to leg_width), its positive-X face is X=leg_width.
    # "Cut... from negative-X end (X=0) toward positive X". This cuts into the flange from the left.
    # "Cut... flush with leg's positive-X face". This cuts into the leg from the right.
    # This implies the Leg and Flange might be separated or arranged such that the cut starts at the edge.
    
    # Let's assume a standard "L" where the corner is at the origin (0,0).
    # Leg: X in [0, leg_width], Y in [0, height].
    # Flange: X in [0, width], Y in [0, flange_thickness].
    # Overlap at [0, leg_width] x [0, flange_thickness].
    # Inner corner (concave) is at (leg_width, flange_thickness).
    # Outer corners: (0,0), (width, 0), (0, height).
    # "Flange upper face": Y = flange_thickness.
    # "Leg's negative-X face": X = 0.
    # Fillet at (0, flange_thickness)? That is an outer corner.
    # "Inside fillet" usually implies the concave corner.
    # Concave corner is at (leg_width, flange_thickness).
    # Faces meeting there: Flange Top (Y=flange_thickness, X>leg_width) and Leg Right (X=leg_width, Y>flange_thickness).
    # If the fillet is there, it joins Flange Top and Leg Right.
    # Description: "joins the flange upper face to the leg's negative-X face".
    # This contradicts the standard L at origin.
    
    # Let's try: Leg is on the RIGHT. Flange is on the TOP? No, "rises by... from bottom".
    # Let's try: Leg is on the LEFT. Flange is on the TOP.
    # Flange: Y from height-flange_thickness to height. X from 0 to width.
    # Leg: Y from 0 to height. X from 0 to leg_width.
    # Overlap top-left.
    # Inner corner at (leg_width, height-flange_thickness).
    # Flange upper face: Y = height.
    # Leg negative-X face: X = 0.
    # Fillet at (0, height)? Outer corner.
    
    # Let's reconsider "negative-X face". Maybe the Leg is shifted to the right?
    # Scenario: Flange is bottom, from X=-width/2 to X=width/2.
    # Leg is centered on Flange?
    # "centered vertical leg". Yes!
    # Flange: X from -width/2 to width/2. Y from 0 to flange_thickness.
    # Leg: X from -leg_width/2 to leg_width/2. Y from 0 to height.
    # Inner corner at (-leg_width/2, flange_thickness).
    # Flange upper face: Y=flange_thickness.
    # Leg negative-X face: X=-leg_width/2.
    # Fillet joins these two. This makes perfect sense for an "inside" fillet.
    # "Cut... from its negative-X end toward positive X". 
    # Flange negative-X end is X=-width/2. Cut goes right.
    # "Cut... through vertical leg... flush with leg's positive-X face".
    # Leg positive-X face is X=leg_width/2. Cut goes left (into the leg from the right).
    # This seems consistent.
    
    # Orientation:
    # Global XY Plane.
    # Z axis is extrusion direction (Depth).
    # Flange: Bottom (Y=0 to flange_thickness). Width X.
    # Leg: Left/Center?
    # If Leg is centered, its negative-X face is at X = -leg_width/2.
    # Flange negative-X face is at X = -width/2.
    # Edit: Cut opening in flange from "negative-X end" (X=-width/2) towards positive X.
    # Edit: Cut opening in leg "flush with leg's positive-X face" (X=leg_width/2).
    
    # Let's build the sketch centered at origin.
    # Flange thickness = flange_thickness.
    # Flange width = bracket_overall_width.
    # Leg width = leg_width.
    # Leg height = bracket_overall_height.
    # Flange is at Y=0 to Y=flange_thickness. X = -width/2 to width/2.
    # Leg is at X = -leg_width/2 to leg_width/2. Y = 0 to height.
    # Wait, if Leg is centered, the inner corner is at X = -leg_width/2, Y = flange_thickness.
    # This matches "inside fillet... joins flange upper face to leg's negative-X face".
    
    sketch = body.newObject("Sketcher::SketchObject", sketch_name)
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.Placement.toPlaced(sketch.Placement, sketch.Placement)
    sketch.Placement.Base = App.Vector(0, 0, 0) # Origin of sketch
    sketch.Placement.Rotation = App.Rotation()
    
    # We need to define lines relative to the sketch origin.
    # But the sketch origin is usually attached to the face.
    # Let's attach to XY_Plane.
    sketch.Placement = App.Placement(App.Vector(0, 0, 0)) # XY Plane is Z=0
    
    # Define points for the L-shape
    # Let's shift the sketch origin to the center of the Flange to make "negative-X end" intuitive?
    # Or just define lines explicitly.
    # Let's define the shape relative to a local coordinate system where (0,0) is the Center of the Flange.
    # Then "negative-X end" is at X = -width/2.
    
    # Points:
    # Bottom-Left (Outer): (-width/2, 0)
    # Bottom-Right (Outer): (width/2, 0)
    # Top-Right (Outer): (width/2, flange_thickness)
    # Inner Corner (Right): (leg_width/2, flange_thickness) -> Wait, Leg is centered.
    # Leg extends from -leg_width/2 to leg_width/2.
    # So Inner Corner is at (-leg_width/2, flange_thickness).
    # Top-Left (Outer): (-leg_width/2, height)
    # Top-Right (Outer): (leg_width/2, height)
    # Bottom-Left (Inner): (-leg_width/2, 0) -> This is the start of the leg.
    
    # Let's trace the perimeter counter-clockwise:
    # 1. Start at (-width/2, 0)
    # 2. Line to (width/2, 0) [Bottom of Flange]
    # 3. Line to (width/2, flange_thickness) [Right side of Flange]
    # 4. Line to (leg_width/2, flange_thickness) [Top of Flange, right of inner corner]
    # 5. Line to (leg_width/2, height) [Right side of Leg]
    # 6. Line to (-leg_width/2, height) [Top of Leg]
    # 7. Line to (-leg_width/2, flange_thickness) [Top of Leg, left of inner corner]
    # 8. Line to (-width/2, 0)? No, there is a cutout? No, base is solid.
    # 9. Line to (-width/2, 0) [Left side of Flange] -> Wait, step 1 was start.
    # 10. Line to (-width/2, 0) [Left side of Flange]
    # 11. Line to (-width/2, 0) ... wait.
    
    # Let's simplify:
    # Outer Box: (-width/2, 0) to (width/2, height).
    # Cutout: Rectangle from (leg_width/2, 0) to (width/2, height)? No.
    # Cutout: Rectangle from (-leg_width/2, flange_thickness) to (width/2, height)? No.
    
    # L Shape:
    # Start (-width/2, 0)
    # Line to (width/2, 0)
    # Line to (width/2, flange_thickness)
    # Line to (leg_width/2, flange_thickness)  <- Inner Corner X
    # Line to (leg_width/2, height)
    # Line to (-leg_width/2, height)
    # Line to (-leg_width/2, flange_thickness) <- Inner Corner X
    # Line to (-width/2, 0)? No.
    # Line to (-width/2, 0) is the left edge of flange.
    # The vertical leg goes from (-leg_width/2, 0) to (-leg_width/2, height).
    # So we need a line from (-leg_width/2, 0) to (-leg_width/2, flange_thickness) to close the loop?
    # No, the leg is part of the solid.
    # Path:
    # (-width/2, 0) -> (width/2, 0) [Bottom]
    # (width/2, 0) -> (width/2, flange_thickness) [Right Flange Edge]
    # (width/2, flange_thickness) -> (leg_width/2, flange_thickness) [Top Flange, Right Half]
    # (leg_width/2, flange_thickness) -> (leg_width/2, height) [Right Leg Edge]
    # (leg_width/2, height) -> (-leg_width/2, height) [Top Leg]
    # (-leg_width/2, height) -> (-leg_width/2, flange_thickness) [Top Leg, Left Half]
    # (-leg_width/2, flange_thickness) -> (-leg_width/2, 0) [Left Leg Edge]
    # (-leg_width/2, 0) -> (-width/2, 0) [Left Flange Edge]
    # Wait, (-leg_width/2, 0) is inside the flange?
    # Yes, if Leg is centered, the leg starts at -leg_width/2. The flange goes to -width/2.
    # So at Y=0, the solid exists from -width/2 to width/2.
    # At Y=flange_thickness, the solid exists from -leg_width/2 to leg_width/2.
    # So the path (-leg_width/2, 0) to (-width/2, 0) is valid.
    # The path (-leg_width/2, flange_thickness) to (-leg_width/2, 0) is the left edge of the leg.
    # The path (-width/2, 0) to (-width/2, flange_thickness)? No.
    # The left edge of the flange is at -width/2.
    # The left edge of the leg is at -leg_width/2.
    # Since leg_width < width, the leg is strictly inside the flange width-wise?
    # No, Leg is centered. Width is larger.
    # So at Y=0, X goes -width/2 to width/2.
    # At Y=flange_thickness, X goes -leg_width/2 to leg_width/2.
    # So the "Left Flange Edge" is at X=-width/2.
    # The "Left Leg Edge" is at X=-leg_width/2.
    # The connection between them is vertical? No.
    # The solid is continuous.
    # Perimeter:
    # 1. (-width/2, 0) to (width/2, 0)
    # 2. (width/2, 0) to (width/2, flange_thickness)
    # 3. (width/2, flange_thickness) to (leg_width/2, flange_thickness)
    # 4. (leg_width/2, flange
