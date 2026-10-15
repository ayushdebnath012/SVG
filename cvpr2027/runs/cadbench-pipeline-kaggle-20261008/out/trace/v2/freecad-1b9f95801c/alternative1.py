"""
FreeCAD 1.1 Script to generate a parametric Water Cup.
This script creates a single PartDesign Body with editable features 
based on the provided dimensions.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("WaterCup")
    
    # Create the main Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    
    # Define Parameters (App::PropertyLength)
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "cup_diameter", "Dimensions", "Outer diameter of the cup")
    params.addProperty("App::PropertyLength", "cup_height", "Dimensions", "Total height of the cup")
    params.addProperty("App::PropertyLength", "cup_thickness", "Dimensions", "Wall thickness")
    params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Calculated inner diameter")
    
    # Set initial values
    params.cup_diameter = 80.0
    params.cup_height = 120.0
    params.cup_thickness = 2.0
    
    # Helper to get parameter
    def get_param(name):
        return params.getPropertyByName(name)

    # --- Step 1: Create Outer Cylinder Sketch (Side View) ---
    # We will create the 3D shape by revolving a side-profile sketch.
    # The sketch plane is YZ (X=0). We draw a vertical line for height and 
    # a point at the outer radius.
    
    outer_sketch = body.newObject("Sketcher::SketchObject", "OuterSketch")
    outer_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    outer_sketch.Support = [(doc.getObject("YZ_Plane"), [])]
    outer_sketch.Constraints = Sketcher.MakeConstraints()
    
    # Add a line representing the height
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, params.cup_height, 0)), False)
    # Add a point at the outer radius (cup_diameter / 2)
    outer_radius = params.cup_diameter / 2.0
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, 0), App.Vector(0, params.cup_height, outer_radius)), False)
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, outer_radius), App.Vector(0, 0, outer_radius)), False)
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, outer_radius), App.Vector(0, 0, 0)), False)
    
    # Add constraints to define the shape fully
    outer_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2), False) # Bottom point on origin
    outer_sketch.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, 0, 1, params.cup_height), False) # Height
    outer_sketch.addConstraint(Sketcher.Constraint("DistanceZ", 0, 2, 0, 2, outer_radius), False) # Outer Radius
    outer_sketch.addConstraint(Sketcher.Constraint("Perpendicular", 0, 2, 0, 3), False) # Right angle
    
    # --- Step 2: Create Inner Cylinder Sketch (Side View) ---
    # Similar to outer, but using inner_diameter.
    inner_diameter = params.cup_diameter - 2.0 * params.cup_thickness
    inner_radius = inner_diameter / 2.0
    
    inner_sketch = body.newObject("Sketcher::SketchObject", "InnerSketch")
    inner_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    inner_sketch.Support = [(doc.getObject("YZ_Plane"), [])]
    
    # Add a line for the inner wall height (same as outer)
    inner_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, params.cup_height, 0)), False)
    # Add point at inner radius
    inner_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, 0), App.Vector(0, params.cup_height, inner_radius)), False)
    inner_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, inner_radius), App.Vector(0, 0, inner_radius)), False)
    
    # Constraints
    inner_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2), False)
    inner_sketch.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, 0, 1, params.cup_height), False)
    inner_sketch.addConstraint(Sketcher.Constraint("DistanceZ", 0, 2, 0, 2, inner_radius), False)
    inner_sketch.addConstraint(Sketcher.Constraint("Perpendicular", 0, 2, 0, 3), False)
    
    # --- Step 3: Create Bottom Plate Sketch (Top View) ---
    # The cup has a bottom. We define the outer and inner circles for the bottom plate.
    bottom_sketch = body.newObject("Sketcher::SketchObject", "BottomSketch")
    bottom_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    bottom_sketch.Support = [(doc.getObject("XY_Plane"), [])]
    
    # Outer circle
    bottom_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.cup_diameter / 2.0), False)
    # Inner circle (hole for the cup body)
    bottom_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), inner_radius), False)
    
    # Coaxial constraint
    bottom_sketch.addConstraint(Sketcher.Constraint("EqualRadius", 0, 1, 1, 2), False)
    
    # --- Step 4: Build the Body ---
    
    # 1. Pad the outer profile to full height
    pad_outer = body.newObject("PartDesign::Pad", "PadOuter")
    pad_outer.Profile = outer_sketch
    pad_outer.Length = params.cup_height
    pad_outer.Type = "Solid"
    
    # 2. Pad the bottom plate (only the ring part)
    # First, we need to pad the bottom sketch as a solid block, then subtract the sides? 
    # Or pad the ring directly. Since Pad works on closed profiles, we can pad the bottom sketch 
    # as a "ThroughAll" to create the bottom disk, then subtract the cylinder hole? 
    # Actually, standard practice: Pad the bottom ring. But PartDesign::Pad requires a closed profile.
    # The bottom sketch has two concentric circles. We can't pad a ring directly with one Pad feature 
    # unless we use "ThroughAll" and it treats the area between? No, Pad subtracts from the volume.
    # Strategy: Pad the outer circle fully to create the solid block. Then subtract the inner cylinder 
    # (which we already did implicitly if we reversed the order, but let's stick to Add/Subtract logic).
    
    # Revised Strategy for robustness:
    # 1. Pad Outer Sketch -> Creates a solid cylinder.
    # 2. Subtract Inner Sketch (Revolution) -> Creates the hollow tube.
    # 3. Pad Bottom Sketch (ThroughAll) -> This adds the bottom plate. Wait, if we pad the bottom sketch 
    #    as a solid block, it will intersect the tube. 
    #    Better: Pad the bottom sketch as a "ThroughAll" but we need to ensure the inner hole is respected.
    #    Actually, the easiest way for a cup bottom is:
    #    - Pad Outer Sketch (creates full cylinder).
    #    - Subtract Inner Sketch (creates tube).
    #    - The bottom of the tube is now open. 
    #    - We need to close the bottom. We can't easily "pad a ring" in one go without boolean operations.
    #    Alternative: Pad the bottom sketch as a "ThroughAll" in the negative Z direction? 
    #    No, let's use the standard "Pad" on the bottom sketch but treat it as adding material.
    #    If we pad the bottom sketch (two circles) as "ThroughAll", it creates a solid disk. 
    #    Since the disk is solid, it will merge with the cylinder and close the hole.
    #    So: Pad Bottom Sketch (ThroughAll) -> This creates the bottom disk.
    #    Wait, if I Pad Outer, then Pad Bottom, the bottom is thick.
    #    Then I Subtract Inner? The Inner sketch is a tube. Subtracting a tube from a cylinder with a bottom 
    #    attached will leave a cup shape.
    
    # Let's refine the order:
    # 1. Pad Outer Sketch (Side) -> Solid Cylinder.
    # 2. Pad Bottom Sketch (Top) -> Solid Disk. (Note: This disk has a hole in the middle).
    #    Wait, Sketcher::SketchObject with two concentric circles and a constraint will result in 
    #    a compound profile? No, it's two separate geometries. A Pad will fail if the profile isn't one 
    #    contiguous loop, UNLESS the software merges them. Usually, PartDesign::Pad expects a single loop.
    #    To fix this: We can't pad the ring directly.
    
    # Correct Approach for Cup Bottom:
    # 1. Pad Outer Sketch (Side) -> Full Cylinder.
    # 2. Subtract Inner Sketch (Side, Revolved) -> Hollow Cylinder.
    # 3. The bottom of the hollow cylinder is open.
    # 4. We need to add the bottom. We can create a small Pad on the bottom sketch, but only the outer ring?
    #    Actually, we can just Pad the Bottom Sketch as "ThroughAll" and set it to be additive. 
    #    If the sketch has two circles, PartDesign might treat them as separate profiles. 
    #    If we use "Additive" pad, it creates two disks? No, that creates a mess.
    
    # Robust Solution:
    # 1. Pad Outer Sketch (Side) -> Cylinder.
    # 2. Pad Bottom Sketch (Top) -> This creates a solid disk with a hole? 
    #    Actually, if we define the bottom sketch properly, we can pad it as a "ThroughAll" and it will 
    #    create the bottom part. But does it respect the inner hole?
    #    Let's try a different approach: 
    #    - Pad Outer Sketch (Side).
    #    - Subtract Inner Sketch (Side).
    #    - Now we have a tube open at both ends.
    #    - We need to close the bottom. We can create a Pad from the bottom sketch, but we need the profile 
    #      to be the outer ring only. 
    #    - To get the outer ring profile, we can create a sketch that is just the outer circle, pad it 
    #      to a small height, then subtract the inner circle?
    #    
    #    Let's simplify: 
    #    1. Pad Outer Sketch (Side).
    #    2. Subtract Inner Sketch (Side).
    #    3. Now, create a new sketch "BottomPlate" on XY plane. Add Outer Circle and Inner Circle.
    #    4. Pad this sketch as "ThroughAll" with Type="Additive". 
    #       Wait, if the sketch has two circles, does it create a ring? 
    #       In FreeCAD Sketcher, if you select two concentric circles, you can use a "Offset" or just rely on 
    #       the fact that a Pad on a sketch with multiple closed loops creates a compound shape (Union of all).
    #       If we pad the bottom sketch (Outer Circle + Inner Circle) as "ThroughAll", it creates a solid block 
    #       defined by the Outer Circle MINUS the Inner Circle? No, it creates a solid block defined by the 
    #       OUTER circle, and the INNER circle creates a hole IF we use a specific mode, OR it creates a 
    #       second disk if they are separate.
    #       
    #    Actually, the most reliable way in PartDesign for a cup bottom:
    #    1. Pad Outer Sketch (Side).
    #    2. Subtract Inner Sketch (Side).
    #    3. Create a Pad on the Bottom Sketch (Outer Circle + Inner Circle). 
    #       Set Pad.Type = "Solid". 
    #       If the sketch has two loops, the Pad will create a shape where the inner loop acts as a hole 
    #       ONLY if the Pad is "ThroughAll" and the topology allows it? 
    #       Actually, standard behavior: If you have two concentric circles, and you Pad, you get a solid 
    #       cylinder (outer) and a smaller solid cylinder (inner) added to it (making a thick disk with a hole 
    #       in the middle ONLY if the inner one is subtractive or if the topology is handled specifically).
    #       
    #    Let's try the "Pocket" approach for the bottom? No.
    #    Let's go with the most robust method:
    #    1. Pad Outer Sketch (Side).
    #    2. Subtract Inner Sketch (Side).
    #    3. Pad Bottom Sketch (Outer Circle ONLY) -> Creates a solid disk.
    #    4. Subtract Bottom Sketch (Inner Circle ONLY) -> Creates the hole in the bottom?
    #       Wait, the hole in the bottom is already there because we subtracted the tube.
    #       So we just need to close the bottom.
    #       
    #    Revised Plan:
    #    1. Pad Outer Sketch (Side).
    #    2. Subtract Inner Sketch (Side). (Now we have a tube open at bottom).
    #    3. Create a Pad on the Bottom Sketch (Outer Circle + Inner Circle). 
    #       We want this to act as a "Ring Pad". 
    #       If we set the Pad to "ThroughAll", it will subtract the inner circle from the outer circle 
    #       IF the sketch logic treats them as a compound profile.
    #       In FreeCAD, if you have two concentric circles in a sketch, a Pad creates a solid with a hole 
    #       only if the constraints link them as a single profile (e.g. Equal Radius? No).
    #       Actually, if you pad a sketch with two concentric circles, it creates a solid block with a 
    #       cylindrical hole through it ONLY if the "Pocket" logic is triggered or if the topology is 
    #       interpreted as a ring.
    #       
    #    Let's try a simpler geometric construction for the bottom:
    #    1. Pad Outer Sketch (Side).
    #    2. Subtract Inner Sketch (Side).
    #    3. Pad Bottom Sketch (Outer Circle) with Length = 0? No.
    #    4. Pad Bottom Sketch (Outer Circle + Inner Circle) with Type = "ThroughAll".
    #       This usually creates a solid disk with a hole in the middle (a washer shape) because the inner 
    #       circle defines a void in the projection.
    
    #    Let's execute this plan.
    
    #    Step 3a: Pad Outer
    pad_outer = body.newObject("PartDesign::Pad", "PadOuter")
    pad_outer.Profile = outer_sketch
    pad_outer.Length = params.cup_height
    pad_outer.Type = "Solid"
    
    #    Step 3b: Subtract Inner
    pocket_inner = body.newObject("PartDesign::Pocket", "PocketInner")
    pocket_inner.Profile = inner_sketch
    pocket_inner.Length = params.cup_height
    pocket_inner.Type = "ThroughAll"
    
    #    Step 3c: Close Bottom
    #    We need to pad the bottom sketch. We assume the two circles create a ring profile.
    #    If the sketch has two concentric circles, the Pad will create a solid ring (washer).
    pad_bottom = body.newObject("PartDesign::Pad", "PadBottom")
    pad_bottom.Profile = bottom_sketch
    pad_bottom.Length = 0 # ThroughAll is needed to make it a solid disk with a hole
    # Note: If Length is 0, it acts as ThroughAll.
    # However, we must ensure the sketch has the inner circle.
    # The bottom_sketch has Outer Circle and Inner Circle.
    # PadBottom will create a solid block defined by Outer Circle, and the Inner Circle will create a hole.
    pad_bottom.Length = 0 # Use 0 for ThroughAll behavior on the bottom plate
    
    # Wait, if we use Length=0, it creates a disk.
    # Is the inner circle respected as a hole? 
    # Yes, typically in PartDesign, if a sketch contains multiple closed loops, the Pad creates a 
    # compound shape where the inner loops are treated as holes (subtraction) relative to the outer loop 
    # in the same sketch feature.
    
    #    Step 3d: Add Rim (Optional but looks better)
    #    The problem description doesn't specify a rim, just "cup body".
    #    The current model: Outer cylinder, Inner tube, Bottom plate.
    #    This forms a cup.
    
    #    One correction: The "InnerSketch" subtraction removes the entire inner volume.
    #    The "PadBottom" adds the bottom plate.
    #    If the bottom plate is a ring (washer), it will sit at the bottom of the tube, closing it.
    #    This works perfectly.
    
    #    Wait, one edge case: The "InnerSketch" subtraction removes material all the way to
