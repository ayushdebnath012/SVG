import FreeCAD as App
import Part
from pathlib import Path
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("SlotPin")
    doc.Location = App.Placement(App.Vector(0, 0, 0))
    
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
    
    # Define axes and planes for the body
    # The Body's local origin is at (0,0,0) of the part design space.
    # We will use the Body's built-in reference planes/axes.
    
    # --- Step 1: Main Cylindrical Body ---
    # Create a sketch on the XZ plane (attached to Z axis, normal to X axis? No, usually XY or XZ).
    # Let's use the XY plane for the profile (Circle).
    
    sketch_profile = body.newObject("Sketcher::SketchObject", "SketchProfile")
    sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_profile.Support = ["XY_Plane"]
    sketch_profile.MapMode = "FlatFace"
    
    # Add circle geometry: Center at (0,0,0), Radius = Diameter / 2
    radius = params.diameter / 2.0
    circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
    sketch_profile.addGeometry(circle, False)
    
    # Add constraints to ensure the circle is centered and closed
    sketch_profile.addConstraint(Sketcher.Constraint("Point", "XY_Plane", 0, 0, 0), 0, 2) # Center point
    sketch_profile.addConstraint(Sketcher.Constraint("Radius", 0, 1), 0, 1) # Radius constraint
    
    # Pad the profile along the Z axis (length)
    pad = body.newObject("PartDesign::Pad", "PadMain")
    pad.Profile = sketch_profile
    pad.Length = params.length
    pad.Type = "Solid" # Ensure solid
    pad.Join = True
    
    # --- Step 2: Slot ---
    # The slot runs along the Z axis. We need a sketch on the XZ plane (or YZ, depending on orientation).
    # Since the cylinder is on Z, let's put the slot on the XZ plane (Side view).
    # The slot will be a rectangle centered on the Z axis, extending lengthwise.
    
    # Wait, the slot depth is 0.63mm. The radius is 0.5mm. 
    # 0.63mm depth > 0.5mm radius. This means the slot goes all the way through and slightly more? 
    # Or is "depth" measured from the surface? Usually yes. 
    # If depth is 0.63 and radius is 0.5, the slot cuts completely through (depth >= diameter/2) 
    # and potentially creates two holes if it's deep enough, or just a full cut.
    # Given "slotted headless cylindrical pin", it implies a keyway or flat.
    # If depth > diameter/2, it's a through slot.
    
    sketch_slot = body.newObject("Sketcher::SketchObject", "SketchSlot")
    sketch_slot.Placement = App.Placement(App.Vector(0, 0, 0))
    # Attach to XZ plane. The normal to XZ is Y. The sketch plane is XZ.
    # We need to reference the plane correctly. 
    # In PartDesign Body, standard planes are XY, XZ, YZ.
    # Let's use XZ plane. The sketch will be in the X-Z plane.
    sketch_slot.Support = ["XZ_Plane"]
    sketch_slot.MapMode = "FlatFace"
    
    # The slot is a rectangle.
    # Width = slot_width.
    # Length = pin_length (to match the main body).
    # Position: Centered on the Z axis (the axis of the cylinder).
    # The slot is usually symmetric around the axis.
    
    half_width = params.slot_width / 2.0
    full_length = params.length
    
    # Define the rectangle points on the XZ plane.
    # Points: (x, z)
    # Top-Left: (-half_width, 0)
    # Top-Right: (half_width, 0)
    # Bottom-Right: (half_width, full_length)
    # Bottom-Left: (-half_width, full_length)
    
    p1 = App.Vector(-half_width, 0, 0)
    p2 = App.Vector(half_width, 0, 0)
    p3 = App.Vector(half_width, full_length, 0)
    p4 = App.Vector(-half_width, full_length, 0)
    
    sketch_slot.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_slot.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_slot.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_slot.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Constraints for the slot
    # Center X: Points 1 and 2 must be symmetric around X=0? Or distance between them is width.
    # Let's constrain the midpoint of the top edge to X=0.
    # Actually, simpler: Constrain the line to be horizontal (Z constant) and vertical.
    # Constrain point 1 and 2 to be on the X axis (Z=0).
    # Constrain the shape to be a rectangle.
    
    # Constraint: Point 1 and 2 on X axis (Z=0)
    sketch_slot.addConstraint(Sketcher.Constraint("Point", "XZ_Plane", 0, 0), 0, 2) # p1 Z=0
    sketch_slot.addConstraint(Sketcher.Constraint("Point", "XZ_Plane", 0, 0), 1, 2) # p2 Z=0
    
    # Constraint: Distance between p1 and p2 is slot_width
    sketch_slot.addConstraint(Sketcher.Constraint("Distance", 0, 1), 0, 1, params.slot_width)
    
    # Constraint: Distance between p1 and p4 is length (or p1 to p3)
    sketch_slot.addConstraint(Sketcher.Constraint("Distance", 0, 1), 0, 3, params.length) # Wait, 0,3 is p1 to p4? No.
    # Indices: 0=p1, 1=p2, 2=p3, 3=p4.
    # p1(0) to p4(3) is the side. Length.
    sketch_slot.addConstraint(Sketcher.Constraint("Distance", 0, 1), 0, 3, params.length)
    
    # Constraint: Right angles (Rectangle)
    # p1-p2-p3, p2-p3-p4, etc.
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 0, 1, 2), 0, 1, 2, 90)
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 1, 2, 3), 1, 2, 3, 90)
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 2, 3, 0), 2, 3, 0, 90)
    sketch_slot.addConstraint(Sketcher.Constraint("Angle", 3, 0, 1), 3, 0, 1, 90)
    
    # Pocket the slot
    # Type: "ThroughAll" is safer than specifying length to ensure it cuts all the way.
    pocket = body.newObject("PartDesign::Pocket", "PocketSlot")
    pocket.Profile = sketch_slot
    pocket.Type = "ThroughAll"
    
    # --- Step 3: Chamfers ---
    # We need chamfers on the top and bottom edges of the slot.
    # The slot edges are the lines parallel to Z at X = +/- half_width.
    # The chamfer is defined by length and angle.
    # Angle 45 deg, Length 0.08.
    # This creates a triangular cut.
    
    # FreeCAD Chamfer feature on PartDesign:
    # Base: Edge(s). Size: Distance from the edge.
    # But here we have Angle and Length.
    # Relationship: If Angle=45, Length = Distance (Size).
    # If Angle != 45, Size = Length * sin(Angle).
    # Let's calculate the Size (distance from the edge to the chamfer plane).
    # Size = chamfer_length * sin(radians(chamfer_angle))
    
    import math
    chamfer_size = params.chamfer_len * math.sin(math.radians(params.chamfer_ang))
    
    # We need to select the two edges of the slot that run along the Z axis.
    # These are the "Right" and "Left" edges of the rectangle.
    # In PartDesign, we can select edges from the sketch or the resulting faces/edges of the body?
    # Usually, for a Chamfer feature in PartDesign, we select the edges of the *body* or *sketch*?
    # If the slot is cut, the slot edges are now edges of the body.
    # However, the slot edges created by the pocket are edges of the resulting solid.
    # We can reference these edges directly.
    
    # Note: The edges might be shared with the original cylinder surface? No, the slot cuts into it.
    # So the slot walls are new edges.
    
    # How to get the edge names?
    # The pocket creates new edges.
    # Let's try to select the edges based on their description or just use a list of indices if possible?
    # In Python API, we can't easily query "the two vertical edges of the last pocket".
    # We have to name the edges or find them by position.
    # Strategy: After recompute, find the edges on the top face of the slot (or bottom) that are parallel to Z.
    
    # Alternative: Use a Fillet/Chamfer on the *sketch* before padding? No, that doesn't work for internal slots usually.
    # Alternative: Use a "Chamfer" on the "Top" and "Bottom" faces of the body? No, chamfer is on edges.
    
    # Let's rely on finding the edges after the pocket is computed.
    # We will add the chamfer feature later, after recompute, by selecting the specific edges.
    # But the script must be deterministic.
    # Let's assume the edges are named generically? No.
    # Let's try to construct the chamfer geometry using a "Groove" or "Revolution" approach?
    # A chamfer on a slot wall is effectively a small triangle cut.
    # We can model this as a small "Pad" (negative) or "Pocket" (negative) at the corners of the slot?
    # No, the chamfer runs along the length.
    
    # Actually, we can define the chamfer using the "Chamfer" feature on the *original* cylinder edges?
    # No, the slot is in the middle.
    
    # Let's try to identify the edges programmatically.
    # We'll add the Chamfer feature, but we need to specify the edges.
    # Since we can't dynamically query edge names in the initial script creation easily without recomputing,
    # and we need to save the feature tree...
    # We can add the Chamfer feature with a placeholder, then recompute, then find the edges, then update the feature?
    # That requires multiple recomputes and object modifications.
    
    # Better approach for "Headless Script":
    # Can we create the chamfer using a "Pocket" with a small angled profile?
    # Yes. Create a sketch on the side of the cylinder? No.
    # Create a sketch on the XZ plane (same as slot) but define the chamfer profile?
    # No, the chamfer is along the Z axis.
    
    # Let's go back to the Chamfer feature.
    # We can try to select the edges by their "Type" or "Position" in the selection list?
    # Or, we can create the chamfer *before* the pocket?
    # If we chamfer the edges of the rectangle in the slot sketch, and then pocket, does it work?
    # If we chamfer the sketch edges, the pocket will cut along those chamfered lines.
    # This works perfectly!
    # 1. Create Slot Sketch.
    # 2. Chamfer the two vertical edges of the rectangle in the sketch.
    # 3. Pocket the chamfered sketch.
    
    # Let's modify the plan: Add Chamfer to the SketchSlot before Pocket.
    
    # Chamfer on sketch:
    # We need to chamfer the segment from p1 to p4 (Left) and p2 to p3 (Right).
    # The chamfer is on the "outside" of the slot? No, the slot is a void.
    # The chamfer is on the corner of the slot.
    # In the sketch (XZ plane), the slot is the rectangle.
    # The chamfer is on the side edges (parallel to Z).
    # Wait, the chamfer is along the length of the pin.
    # So the chamfer is on the edges of the slot that run along Z.
    # Yes.
    # In the sketch, these are the segments (p1, p4) and (p2, p3).
    # We need to chamfer these segments.
    # But the chamfer is in 3D space (along the cylinder surface).
    # If we chamfer the sketch line, we are creating a 2D chamfer in the XZ plane.
    # When we extrude (Pocket), this 2D chamfer becomes a 3D chamfer along the Z axis.
    # This is correct.
    
    # How to chamfer a segment in the sketch?
    # Sketcher has a "Chamfer" constraint? No, usually Fillet/Chamfer is a feature, not a sketch constraint in all versions.
    # In PartDesign, Chamfer is a feature.
    # Can we apply a Chamfer feature to a sketch object? No.
    # So we cannot easily chamfer the sketch edges directly using a feature on the sketch object.
    
    # Re-evaluating:
    # We need to chamfer the edges of the *cylinder* where the slot starts?
    # No, the slot runs the full length.
    # The edges are the intersection of the slot wall and the cylinder surface?
    # No, the slot is inside. The edges are the boundaries of the slot face.
    # The chamfer is on the *corners* of the slot (Top-Left, Top-Right, Bottom-Left, Bottom-Right)?
    # No, "chamfer length" and "chamfer angle" usually refer to the bevel on the edge of the slot along the length.
    # Like a square keyway with chamfered ends? Or the whole length?
    # "A slotted headless cylindrical pin... slot width... slot depth".
    # Usually, if it says "chamfer length", it implies the edges of the slot are chamfered along the entire length?
    # Or just the corners?
    # Given "chamfer_length=0.08mm" and "pin_length=2.5mm", it's likely the corners of the slot.
    # But wait, if it's a "slot running along its length", and it has a chamfer...
    # Does it mean the edges of the slot are beveled?
    # If I take a pin and cut a slot, the edges of the slot are sharp.
    # A chamfer would be a small triangle cut at the top corners of the slot.
    # Let's assume the chamfer is at the two ends of the slot (Top and Bottom faces of the pin)?
    # No, the pin is headless.
    # Maybe the chamfer is on the *edges* of the slot itself? i.e. the intersection of the slot walls?
    # If the slot is rectangular, the edges are sharp.
    # If we chamfer the slot, we remove the sharp edge.
    # The chamfer would be a small triangular cut along the length? No, that would round the edge.
    # A "chamfer" on a long edge is usually a groove or a bevel.
    # Let's assume the standard interpretation: The slot has beveled corners at the top and bottom of the pin?
    # Or the edges of the slot are chamfered?
    # "Chamfer length" = 0.08mm. This is very small.
    # If it were at the corners of the slot (top and bottom of the pin), it would be 2 chamfers.
