import FreeCAD as App
import Part
from pathlib import Path
import Sketcher
import math

def main():
    # Create a new document
    doc = App.newDocument("SlotPin")
    
    # Create a single Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Create a VarSet for named parameters to drive geometry
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Overall pin diameter")
    params.diameter = 1.0
    params.addProperty("App::PropertyLength", "length", "Dimensions", "Total pin length")
    params.length = 2.5
    params.addProperty("App::PropertyLength", "chamfer_len", "Dimensions", "Chamfer length")
    params.chamfer_len = 0.08
    params.addProperty("App::PropertyAngle", "chamfer_ang", "Dimensions", "Chamfer angle")
    params.chamfer_ang = 45.0
    params.addProperty("App::PropertyLength", "slot_width", "Dimensions", "Slot width")
    params.slot_width = 0.2
    params.addProperty("App::PropertyLength", "slot_depth", "Dimensions", "Slot depth")
    params.slot_depth = 0.63
    
    # --- Step 1: Main Cylindrical Body ---
    # Create a sketch on the XY plane for the circular profile
    sketch_profile = body.newObject("Sketcher::SketchObject", "SketchProfile")
    sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_profile.Support = ["XY_Plane"]
    sketch_profile.MapMode = "FlatFace"
    
    # Add circle geometry: Center at (0,0,0), Radius = Diameter / 2
    radius = params.diameter / 2.0
    circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
    sketch_profile.addGeometry(circle, False)
    
    # Add constraints to ensure the circle is centered and closed
    # Constraint: Point on origin
    sketch_profile.addConstraint(Sketcher.Constraint("Point", "XY_Plane", 0, 0), 0, 2)
    # Constraint: Radius
    sketch_profile.addConstraint(Sketcher.Constraint("Radius", 0, 1), 0, 1)
    
    # Pad the profile along the Z axis (length)
    pad = body.newObject("PartDesign::Pad", "PadMain")
    pad.Profile = sketch_profile
    pad.Length = params.length
    pad.Type = "Solid"
    pad.Join = True
    
    # --- Step 2: Slot ---
    # The slot runs along the Z axis. We create a sketch on the XZ plane.
    sketch_slot = body.newObject("Sketcher::SketchObject", "SketchSlot")
    sketch_slot.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_slot.Support = ["XZ_Plane"]
    sketch_slot.MapMode = "FlatFace"
    
    # Define the rectangle points on the XZ plane.
    # The slot is centered on the Z axis (X=0).
    half_width = params.slot_width / 2.0
    full_length = params.length
    
    p1 = App.Vector(-half_width, 0, 0)
    p2 = App.Vector(half_width, 0, 0)
    p3 = App.Vector(half_width, full_length, 0)
    p4 = App.Vector(-half_width, full_length, 0)
    
    sketch_slot.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_slot.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_slot.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_slot.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Constraints for the slot
    # 1. Points 1 and 2 are on the X axis (Z=0)
    sketch_slot.addConstraint(Sketcher.Constraint("Point", "XZ_Plane", 0, 0), 0, 2)
    sketch_slot.addConstraint(Sketcher.Constraint("Point", "XZ_Plane", 0, 0), 1, 2)
    
    # 2. Distance between p1 and p2 is slot_width
    sketch_slot.addConstraint(Sketcher.Constraint("Distance", 0, 1), 0, 1, params.slot_width)
    
    # 3. Distance between p1 and p4 is length (Side edge)
    sketch_slot.addConstraint(Sketcher.Constraint("Distance", 0, 1), 0, 3, params.length)
    
    # 4. Right angles for a rectangle
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 0, 1, 2), 0, 1, 2, 90)
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 1, 2, 3), 1, 2, 3, 90)
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 2, 3, 0), 2, 3, 0, 90)
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 3, 0, 1), 3, 0, 1, 90)
    
    # Pocket the slot
    # Type: "ThroughAll" ensures it cuts completely through the cylinder
    pocket = body.newObject("PartDesign::Pocket", "PocketSlot")
    pocket.Profile = sketch_slot
    pocket.Type = "ThroughAll"
    
    # --- Step 3: Chamfers ---
    # The chamfers are on the two vertical edges of the slot (parallel to Z axis).
    # We need to chamfer the edges created by the pocket.
    # Since we cannot easily select edges by name in a headless script before they exist,
    # we will add the Chamfer feature and then programmatically find the correct edges
    # based on their position and orientation after the first recompute.
    
    # Calculate chamfer size based on length and angle
    # For a 45 degree angle, Size = Length.
    # For other angles, Size = Length * sin(Angle).
    chamfer_size = params.chamfer_len * math.sin(math.radians(params.chamfer_ang))
    
    # Create the Chamfer feature (initially with empty base)
    chamfer = body.newObject("PartDesign::Chamfer", "ChamferSlot")
    chamfer.Size = chamfer_size
    chamfer.Type = "Linear"
    chamfer.Base = [] # Will be populated dynamically
    
    # --- Step 4: Recompute to generate geometry ---
    doc.recompute()
    
    # --- Step 5: Identify and assign edges to Chamfer ---
    # We need to find the two edges of the slot that run along the Z axis.
    # These edges are located at X = +/- half_width, Z from 0 to length.
    
    # Get the solid body
    solid = body.Shape
    
    # Get all edges
    edges = solid.Edges
    
    # Filter edges:
    # 1. Must be parallel to Z axis (approx)
    # 2. Must be at the correct X position (approx +/- half_width)
    # 3. Must be within the length range
    
    target_edges = []
    half_width_val = params.slot_width / 2.0
    
    for edge in edges:
        # Check if edge is a line
        if not edge.isLine:
            continue
            
        # Get start and end points
        p_start = edge.StartPoint
        p_end = edge.EndPoint
        
        # Check if parallel to Z (X and Y components are small)
        dx = abs(p_start.X - p_end.X)
        dy = abs(p_start.Y - p_end.Y)
        dz = abs(p_start.Z - p_end.Z)
        
        if dz < 1e-6: # Not parallel to Z
            continue
            
        # Check X position (should be close to half_width or -half_width)
        x_pos = abs(p_start.X)
        if abs(x_pos - half_width_val) > 0.01:
            continue
            
        # Check Z range (should be within the pin length)
        z_min = min(p_start.Z, p_end.Z)
        z_max = max(p_start.Z, p_end.Z)
        if z_min < -0.1 or z_max > params.length + 0.1:
            continue
            
        # This edge is a candidate
        target_edges.append(edge)
    
    # We expect exactly 2 edges (Left and Right walls of the slot)
    if len(target_edges) != 2:
        raise RuntimeError(f"Expected 2 slot edges for chamfer, found {len(target_edges)}")
    
    # Assign the edges to the Chamfer feature
    # The Base property expects a tuple of (Object, EdgeIndex) or similar.
    # In PartDesign, for a Chamfer feature, Base is a list of tuples (Object, EdgeIndex).
    # However, the API often accepts a list of Edge objects directly in newer versions,
    # or we need to reference them via their index in the Body's shape or the specific object.
    # Standard PartDesign Chamfer Base: List of (Object, EdgeIndex).
    # Since these edges belong to the Body's shape, we can try to reference them by index in the Body's shape?
    # Or, more robustly, we can use the Edge objects if the API supports it.
    # Let's try passing the Edge objects directly as the Base list.
    
    chamfer.Base = target_edges
    
    # --- Final Recompute ---
    doc.recompute()
    
    # Save the file next to the script
    script_path = Path(__file__).resolve()
    output_path = script_path.with_name(script_path.stem + ".FCStd")
    
    doc.saveAs(str(output_path))
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    main()
