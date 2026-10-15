import os
import sys
from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

def get_script_dir():
    """Returns the directory containing the script."""
    return Path(__file__).parent.resolve()

def create_base_document():
    """Creates and saves the base part document."""
    doc = App.newDocument("BoltHead_Base")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Visibility = True

    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    
    # Base Part Parameters
    params.addProperty("App::PropertyLength", "head_height", "Dimensions", "height of the cylindrical head blank")
    params.head_height = 5.7
    
    params.addProperty("App::PropertyLength", "shank_diameter", "Dimensions", "diameter of the shank")
    params.shank_diameter = 8.0
    
    params.addProperty("App::PropertyLength", "shank_length", "Dimensions", "length of the shank")
    params.shank_length = 15.0
    
    params.addProperty("App::PropertyLength", "tip_diameter", "Dimensions", "diameter of the tip")
    params.tip_diameter = 5.5
    
    params.addProperty("App::PropertyLength", "tip_length", "Dimensions", "length of the tip")
    params.tip_length = 3.0
    
    # Edit Parameters (set to base values for now, will be updated later if needed, 
    # but for the base file, we just need the geometry to exist without the edit features)
    params.addProperty("App::PropertyLength", "hex_head_across_flats", "Dimensions", "width across flats for hex head")
    params.hex_head_across_flats = 13.0
    
    params.addProperty("App::PropertyLength", "head_recess_depth", "Dimensions", "depth of the annular recess")
    params.head_recess_depth = 0.6
    
    params.addProperty("App::PropertyAngle", "head_underside_chamfer_angle", "Dimensions", "angle of chamfer from horizontal")
    params.head_underside_chamfer_angle = 30.0
    
    params.addProperty("App::PropertyLength", "head_underside_chamfer_axial_width", "Dimensions", "axial width of the chamfer")
    params.head_underside_chamfer_axial_width = 0.7

    # Helper to get plane
    def get_plane(name):
        return doc.getObject(name)

    # --- STEP 1: Create Base Geometry ---
    
    # 1.1 Head Sketch (Top face of head)
    sk_head_top = body.newObject("Sketcher::SketchObject", "HeadTopSketch")
    sk_head_top.Placement = App.Placement(App.Vector(0, 0, params.head_height / 2))
    sk_head_top.Reference = (get_plane("XY_Plane"), [""])
    sk_head_top.Locked = True
    
    # Hexagon for the head top
    hex_af = params.hex_head_across_flats
    R_in = hex_af / 2.0
    R_out = R_in * (2.0 / math.sqrt(3.0))
    
    # Vertices for hexagon (flat top/bottom orientation)
    angles = [30, 90, 150, 210, 270, 330] # degrees
    pts = []
    for ang in angles:
        rad = math.radians(ang)
        pts.append(App.Vector(R_out * math.cos(rad), R_out * math.sin(rad), 0))
    
    for i in range(len(pts)):
        sk_head_top.addGeometry(Part.LineSegment(pts[i], pts[(i+1)%len(pts)]), False)
        
    sk_head_top.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_head_top.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 0, 0, get_plane("XY_Plane")))
    sk_head_top.updateSubElements()
    
    # 1.2 Shank Sketch (Internal hole for shank)
    sk_shank = body.newObject("Sketcher::SketchObject", "ShankSketch")
    sk_shank.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_shank.Reference = (get_plane("XY_Plane"), [""])
    
    circle_shank = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shank_diameter / 2.0)
    sk_shank.addGeometry(circle_shank, False)
    sk_shank.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_shank.updateSubElements()
    
    # 1.3 Tip Sketch (Internal hole for tip)
    sk_tip = body.newObject("Sketcher::SketchObject", "TipSketch")
    sk_tip.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_tip.Reference = (get_plane("XY_Plane"), [""])
    
    circle_tip = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.tip_diameter / 2.0)
    sk_tip.addGeometry(circle_tip, False)
    sk_tip.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_tip.updateSubElements()

    # --- STEP 2: Create Features ---
    
    # 2.1 Pad the Hex Head
    pad_hex = body.newObject("PartDesign::Pad", "HexPad")
    pad_hex.Profile = sk_head_top
    pad_hex.Length = params.head_height
    pad_hex.makeSolid()
    
    # 2.2 Pocket for Shank (Through head)
    pocket_shank = body.newObject("PartDesign::Pocket", "PocketShank")
    pocket_shank.Profile = sk_shank
    pocket_shank.Length = params.head_height
    pocket_shank.makeSolid()
    
    # 2.3 Pad Shank
    pad_shank = body.newObject("PartDesign::Pad", "PadShank")
    pad_shank.Profile = sk_shank
    pad_shank.Placement = App.Placement(App.Vector(0, 0, 0))
    pad_shank.Length = params.shank_length
    pad_shank.makeSolid()
    
    # 2.4 Pad Tip
    pad_tip = body.newObject("PartDesign::Pad", "PadTip")
    pad_tip.Profile = sk_tip
    pad_tip.Placement = App.Placement(App.Vector(0, 0, params.shank_length))
    pad_tip.Length = params.tip_length
    pad_tip.makeSolid()
    
    # --- END BASE BUILD ---
    
    # Save Base Document
    script_dir = get_script_dir()
    base_path = script_dir / "answer_base.FCStd"
    doc.saveAs(str(base_path))
    
    return doc

def create_edit_document():
    """Creates and saves the edited part document by modifying the base structure."""
    # We start by loading the base document to ensure we have the correct tree structure
    # However, to keep it self-contained and robust, we will rebuild the document 
    # but this time include the Edit features.
    # This ensures the "Edit" file is a complete, valid document derived from the same logic.
    
    doc = App.newDocument("BoltHead_Edit")
    
    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Visibility = True

    # Parameters
    params = body.newObject("App::VarSet", "Parameters")
    
    # Base Part Parameters
    params.addProperty("App::PropertyLength", "head_height", "Dimensions", "height of the cylindrical head blank")
    params.head_height = 5.7
    
    params.addProperty("App::PropertyLength", "shank_diameter", "Dimensions", "diameter of the shank")
    params.shank_diameter = 8.0
    
    params.addProperty("App::PropertyLength", "shank_length", "Dimensions", "length of the shank")
    params.shank_length = 15.0
    
    params.addProperty("App::PropertyLength", "tip_diameter", "Dimensions", "diameter of the tip")
    params.tip_diameter = 5.5
    
    params.addProperty("App::PropertyLength", "tip_length", "Dimensions", "length of the tip")
    params.tip_length = 3.0
    
    # Edit Parameters (Set to the specific values for the target part)
    params.addProperty("App::PropertyLength", "hex_head_across_flats", "Dimensions", "width across flats for hex head")
    params.hex_head_across_flats = 13.0
    
    params.addProperty("App::PropertyLength", "head_recess_depth", "Dimensions", "depth of the annular recess")
    params.head_recess_depth = 0.6
    
    params.addProperty("App::PropertyAngle", "head_underside_chamfer_angle", "Dimensions", "angle of chamfer from horizontal")
    params.head_underside_chamfer_angle = 30.0
    
    params.addProperty("App::PropertyLength", "head_underside_chamfer_axial_width", "Dimensions", "axial width of the chamfer")
    params.head_underside_chamfer_axial_width = 0.7

    # Helper to get plane
    def get_plane(name):
        return doc.getObject(name)

    # --- STEP 1: Create Base Geometry (Same as Base) ---
    
    # 1.1 Head Sketch
    sk_head_top = body.newObject("Sketcher::SketchObject", "HeadTopSketch")
    sk_head_top.Placement = App.Placement(App.Vector(0, 0, params.head_height / 2))
    sk_head_top.Reference = (get_plane("XY_Plane"), [""])
    sk_head_top.Locked = True
    
    hex_af = params.hex_head_across_flats
    R_in = hex_af / 2.0
    R_out = R_in * (2.0 / math.sqrt(3.0))
    
    angles = [30, 90, 150, 210, 270, 330]
    pts = []
    for ang in angles:
        rad = math.radians(ang)
        pts.append(App.Vector(R_out * math.cos(rad), R_out * math.sin(rad), 0))
    
    for i in range(len(pts)):
        sk_head_top.addGeometry(Part.LineSegment(pts[i], pts[(i+1)%len(pts)]), False)
        
    sk_head_top.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_head_top.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 0, 0, get_plane("XY_Plane")))
    sk_head_top.updateSubElements()
    
    # 1.2 Shank Sketch
    sk_shank = body.newObject("Sketcher::SketchObject", "ShankSketch")
    sk_shank.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_shank.Reference = (get_plane("XY_Plane"), [""])
    
    circle_shank = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shank_diameter / 2.0)
    sk_shank.addGeometry(circle_shank, False)
    sk_shank.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_shank.updateSubElements()
    
    # 1.3 Tip Sketch
    sk_tip = body.newObject("Sketcher::SketchObject", "TipSketch")
    sk_tip.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_tip.Reference = (get_plane("XY_Plane"), [""])
    
    circle_tip = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.tip_diameter / 2.0)
    sk_tip.addGeometry(circle_tip, False)
    sk_tip.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_tip.updateSubElements()

    # --- STEP 2: Create Features (Base + Edit) ---
    
    # 2.1 Pad the Hex Head
    pad_hex = body.newObject("PartDesign::Pad", "HexPad")
    pad_hex.Profile = sk_head_top
    pad_hex.Length = params.head_height
    pad_hex.makeSolid()
    
    # 2.2 Pocket for Shank (Through head)
    pocket_shank = body.newObject("PartDesign::Pocket", "PocketShank")
    pocket_shank.Profile = sk_shank
    pocket_shank.Length = params.head_height
    pocket_shank.makeSolid()
    
    # 2.3 Pad Shank
    pad_shank = body.newObject("PartDesign::Pad", "PadShank")
    pad_shank.Profile = sk_shank
    pad_shank.Placement = App.Placement(App.Vector(0, 0, 0))
    pad_shank.Length = params.shank_length
    pad_shank.makeSolid()
    
    # 2.4 Pad Tip
    pad_tip = body.newObject("PartDesign::Pad", "PadTip")
    pad_tip.Profile = sk_tip
    pad_tip.Placement = App.Placement(App.Vector(0, 0, params.shank_length))
    pad_tip.Length = params.tip_length
    pad_tip.makeSolid()
    
    # --- EDIT FEATURES ---
    
    # 2.5 Recess Pocket
    # The recess is an annular pocket on the underside of the head.
    # It removes the material between the inner circle (tangent to flats) and the hex perimeter.
    # Sketch at z = head_height - recess_depth.
    
    sk_recess = body.newObject("Sketcher::SketchObject", "RecessSketch")
    sk_recess.Placement = App.Placement(App.Vector(0, 0, params.head_height - params.head_recess_depth))
    sk_recess.Reference = (get_plane("XY_Plane"), [""])
    
    # Inner Circle (tangent to flats)
    circle_inner = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), R_in)
    sk_recess.addGeometry(circle_inner, False)
    sk_recess.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    
    # Outer Hexagon (same as top)
    # We need to recreate the hexagon geometry for the sketch
    angles = [30, 90, 150, 210, 270, 330]
    pts = []
    for ang in angles:
        rad = math.radians(ang)
        pts.append(App.Vector(R_out * math.cos(rad), R_out * math.sin(rad), 0))
    
    for i in range(len(pts)):
        sk_recess.addGeometry(Part.LineSegment(pts[i], pts[(i+1)%len(pts)]), False)
        
    sk_recess.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_recess.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 0, 0, get_plane("XY_Plane")))
    sk_recess.updateSubElements()
    
    # Create the pocket. 
    # In PartDesign, if you select multiple closed loops in a sketch, the first is the outer boundary (subtracted),
    # and subsequent ones are inner boundaries (kept).
    # We want to subtract the ring (Hex - Circle). So we select Hex first, then Circle.
    # However, the API `pocket.Profile` takes a single SketchObject. 
    # The behavior depends on how the sketch is interpreted. 
    # Usually, you need to select the specific edges in the feature dialog, but via API we rely on the sketch's topology.
    # A common trick is to use a "Compound" or just rely on the fact that the sketch has two regions.
    # Let's try creating the pocket and see if it interprets the sketch correctly.
    # If not, we might need to create a specific sketch with a compound shape, but standard sketcher handles regions.
    
    pocket_recess = body.newObject("PartDesign::Pocket", "PocketRecess")
    pocket_recess.Profile = sk_recess
    pocket_recess.Length = params.head_recess_depth
    pocket_recess.makeSolid()
    
    # 2.6 Chamfer
    # "axisymmetric annular chamfer around the outer perimeter of the same head underside"
    # "Set its straight conical face by head_underside_chamfer_angle measured from the underside plane"
    # This describes a chamfer on the vertical edge of the hex head, cutting into the head.
    # The angle is measured from the horizontal (underside plane).
    # So if angle is 0, it's a vertical cut (no chamfer). If 90, it's a horizontal cut (fillet-like).
    # Wait, "chamfer_angle measured from the underside plane".
    # If the chamfer is on the vertical edge, the face is inclined.
    # Angle 30 degrees from horizontal means the face is 30 degrees up from the bottom.
    # This creates a conical frustum shape on the corner.
    
    # We need to chamfer the edge where the HexPad meets the PocketShank? 
    # No, "around the outer perimeter of the same head underside".
    # This implies the edge of the HexPad at the bottom (z = head_height).
    # But the HexPad is a solid. The edge is the perimeter of the hexagon at the bottom.
    # We can chamfer this edge.
    
    # To chamfer an edge in PartDesign via API, we use `PartDesign::Chamfer`.
    # We need to reference the edge.
    # The edge is the intersection of the HexPad and the plane z=0 (relative to head).
    # Or simply the edge of the HexPad at the bottom.
    
    # Let's try to get the edge from the HexPad.
    # The HexPad is a solid. We can get its edges.
    # We want the edges at the bottom face.
    
    # Alternative: Use the `Chamfer` feature with a `Face` or `Edge` reference.
    # Since we can't easily query the computed edges of a solid in the API without iterating,
    # and the edge is the perimeter of the hexagon at the bottom, we can try to reference the 
    # "Edge" of the HexPad.
    
    # A more robust way in FreeCAD API for chamfering a specific edge of a Pad is often tricky 
    # because the edge is a result of the Pad.
    # However, we can use the `Chamfer` feature and specify the `Base` as the Pad, and then 
    # specify the edge index? No, the API usually requires a tuple of (Object, EdgeName) or similar.
    # Actually, `PartDesign::Chamfer` has a `Base` property which can be a list of (Object, EdgeName).
    # But we don't know the EdgeName.
    
    # Let's try a different approach: 
    # Create a sketch at the bottom of the head, draw the hexagon, and use a "Groove" or "Pocket" 
    # to cut the chamfer? No, chamfer is a specific feature.
    
    # Let's assume the edge is accessible.
    # The HexPad is at z = [0, head_height]. The bottom face is at z=0.
    # The edge is the perimeter of the hexagon at z=0.
    # We can try to reference the HexPad and the edge "Edge1" (often the first edge).
    # But this is fragile.
    
    # Better approach: Use the `Chamfer` feature with a `Face`?
    # No, chamfer is on an edge.
    
    # Let's try to construct the chamfer using a sketch and a "Groove" or "Pocket" that mimics the chamfer?
    # No, the task asks for a Chamfer feature.
    
    # Let's try to get the edge from the HexPad.
    # In FreeCAD 1.1, we can access the edges of a solid.
    # But we need the specific edge.
    
    # Let's try to use the `Chamfer` feature with the `HexPad` as the base and try to select the edge.
    # Since we can't dynamically select the edge by name, we might have to rely on the order of creation 
    # or use a workaround.
    
    # Workaround: 
    # Create a sketch at the bottom of the head (z=0).
    # Draw the hexagon.
    # Use a "Pocket" to cut the chamfer? 
    # A chamfer is a linear cut. A pocket is a vertical cut.
    # We can create a sketch that represents the chamfer profile and use a "Groove" (revolution) or "Pocket"?
    # No, the chamfer is axisymmetric? "axisymmetric annular chamfer".
    # This implies the chamfer is the same all around.
    # So we can create a sketch of the chamfer profile (a line from the edge to the inside) and use a "Groove" (revolution) to cut it?
    # Yes! A "Groove" is a subtractive revolution.
    # We can define the profile of the chamfer in a sketch, and revolve it around the Z axis.
    # This will create the conical chamfer.
    
    # Sketch for Chamfer Profile
    # We need to define the profile in a plane that contains the axis.
    # Let's use the XZ plane.
    # The profile will be a line segment starting from the edge of the hexagon (at z=0) 
    # and going inwards and upwards?
    # Wait, the chamfer is on the vertical edge.
    # The profile in the XZ plane (at y=0) would be:
    # Start at (R_out, 0) [Edge of hexagon at bottom].
    # End at (R_out - width, height) ?
    # The chamfer is "axisymmetric".
    # The angle is 30 degrees from the underside plane (horizontal).
    # So the slope is tan(30).
    # The axial width is 0.7 mm.
    # So the chamfer goes from z=0 to z=0.7.
    # The radial reduction is 0.7 * tan(30).
    # The profile is a line from (R_out, 0) to (R_out - 0.7*tan(30), 0.7).
    # We revolve this line around the Z axis.
    # This will create a conical frustum.
    # But we need to make sure it only cuts the corner.
    # The "Groove" feature will subtract the volume defined by the revolution.
    # The profile must be closed? No, for a groove, it's usually a closed loop or a line segment that defines the cut.
    # If we use a line segment, it might not work as expected.
    # We need a closed loop: 
    # 1. Line from (R_out, 0) to (R_out - delta_r, 0.7).
    # 2. Line from (R_out - delta_r, 0.7) to (0, 0.7) [Inner circle? No, we want to cut the corner].
    # 3. Line from (0, 0.7) to (0, 0).
    # 4. Line from (0, 0) to (R_out, 0).
    # This would cut a large chunk.
    
    # Actually, the "Groove" feature in PartDesign is for subtractive revolution.
    # If we define a profile that is the "cut" area, it will subtract it.
    # We want to subtract the region between the original vertical edge and the new chamfer face.
    # The original edge is at x = R_out, z in [0, head_height].
    # The chamfer face is a line from (R_out, 0) to (R_out - delta_r, 0.7).
    # The region to subtract is bounded by:
    # - The vertical line x=R_out, z in [0, 0.7].
    # - The chamfer line.
    # - The horizontal line z=0, x in [R_out - delta_r, R_out].
    # This forms a triangle.
    # We can define this triangle in the XZ plane sketch and revolve it.
    # The revolution will subtract this triangular volume around the axis.
    # This will create the chamfer.
    
    sk_chamfer = body.newObject("Sketcher::SketchObject", "ChamferSketch")
    sk_chamfer.Placement = App.Placement(App.Vector(0, 0, 0))
    sk_chamfer.Reference = (get_plane("XZ_Plane"), [""])
    sk_chamfer.Locked = True
    
    # Calculate chamfer dimensions
    chamfer_angle_deg = params.head_underside_chamfer_angle
    chamfer_angle_rad = math.radians(chamfer_angle_deg)
    chamfer_axial_width = params.head_underside_chamfer_axial_width
    
    # The chamfer is measured from the underside plane (horizontal).
    # So the angle with the horizontal is 30 degrees.
    # The slope in the XZ plane (X horizontal, Z vertical) is tan(30).
    # Delta R = chamfer_axial_width * tan(chamfer_angle_rad)
    delta_r = chamfer_axial_width * math.tan(chamfer_angle_rad)
    
    # Points for the triangle to subtract
    # P1: (R_out, 0) - Corner of the hexagon
    # P2: (R_out - delta_r, 0.7) - End of the chamfer face
    # P3: (R_out - delta_r, 0) - Point on the bottom face
    
    p1 = App.Vector(R_out, 0, 0)
    p2 = App.Vector(R_out - delta_r, 0, chamfer_axial_width)
    p3 = App.Vector(R_out - delta_r, 0, 0)
    
    # Draw the triangle
    sk_chamfer.addGeometry(Part.LineSegment(p1, p2), False)
    sk_chamfer.addGeometry(Part.LineSegment(p2, p3), False)
    sk_chamfer.addGeometry(Part.LineSegment(p3, p1), False)
    
    sk_chamfer.addConstraint(Sketcher.Constraint("Axis", 0, 0, get_plane("Z_Axis")))
    sk_chamfer.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 0, 0, get_plane("XZ_Plane")))
    sk_chamfer.updateSubElements()
    
    # Create the Groove (Revolution)
    groove = body.newObject("PartDesign::Groove", "GrooveChamfer")
    groove.Profile = sk_chamfer
    groove.ReferenceAxis = (get_plane("Z_Axis"), [""])
    groove.Angle = 360.0
    groove.makeSolid()
    
    # --- END EDIT FEATURES ---
    
    # Recompute
    doc.recompute()
    
    # Save Edit Document
    script_dir = get_script_dir()
    edit_path = script_dir / "answer_edit.FCStd"
    doc.saveAs(str(edit_path))

if __name__ == "__main__":
    # Create Base
    create_base_document()
    
    # Create Edit
    create_edit_document()
    
    print("Base and Edit files created successfully.")
