import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("Staircase")

# --- 1. Parameters ---
# Create a VarSet to hold editable parameters
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyInteger", "number_of_steps", "Dimensions", "Number of steps")
params.number_of_steps = 5

params.addProperty("App::PropertyLength", "step_riser", "Dimensions", "Height of each step")
params.step_riser = 170.0

params.addProperty("App::PropertyLength", "step_depth", "Dimensions", "Depth of each step")
params.step_depth = 300.0

params.addProperty("App::PropertyLength", "step_width", "Dimensions", "Width of the staircase")
params.step_width = 1200.0

# --- 2. Setup Body ---
body = doc.addObject("PartDesign::Body", "Body")
# Correct placement initialization
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- 3. Create Sketch for Stair Profile ---
# The profile needs to be in the XZ plane (X=Run, Z=Rise).
# We create a sketch attached to the global XZ_Plane.
# If the global XZ_Plane doesn't exist, we create it in the body first.

# Check if XZ_Plane exists, if not create it
xz_plane = doc.getObject("XZ_Plane")
if not xz_plane:
    xz_plane = doc.addObject("PartDesign::Plane", "XZ_Plane")
    xz_plane.Placement = App.Placement(App.Vector(0, 0, 0))
    # Ensure the plane is oriented correctly (Normal Y)
    # PartDesign::Plane uses Placement to define position and orientation.
    # By default, it aligns with the current workbench plane. 
    # To be safe, we can explicitly set the placement to align with global XZ.
    # However, in a fresh doc, the standard planes (XY, XZ, YZ) usually exist.
    # If not, the above creation might fail or default to XY.
    # Let's assume standard planes exist or create a robust one.
    # Actually, the safest way for a script is to attach to the Body's XY plane 
    # and manually orient the geometry, OR attach to a plane we create.
    # Let's try to attach to the global XZ_Plane. If it fails, we handle it.
    # But for this script, let's create a sketch on the Body's XY plane 
    # and interpret the Sketch Y as Z (Rise).
    # Then we extrude along the Body's Z axis? 
    # Prompt: "extrusion_direction = +Y".
    # This means the "Width" is along Y.
    # So the Profile MUST be in the XZ plane.
    # We will create a sketch on the Body, attach to the Body's XY plane.
    # Then we will rotate the sketch 90 degrees around X so that Sketch Y becomes Z?
    # No, PartDesign::SketchObject has a Placement.
    # We can set the sketch placement to rotate the sketch plane.
    # Let's attach to the Body's XY plane (which is at 0,0,0).
    # Then set the sketch placement to rotate 90 deg around X axis.
    # This transforms the Sketch XY plane into the Global XZ plane.
    # Sketch X -> Global X
    # Sketch Y -> Global Z
    # Sketch Z -> Global -Y (Normal)
    # This matches our needs: X is Run, Z is Rise.

    # Create a temporary plane on the body to attach to, or just use the Body's implicit plane?
    # PartDesign::SketchObject requires an AttachmentSupport.
    # We can use the Body itself? No, it needs a face/plane.
    # Let's create a Plane on the Body aligned with XY.
    xy_plane = body.newObject("PartDesign::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))

    sketch = body.newObject("Sketcher::SketchObject", "StairProfile")
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.AttachmentSupport = (xy_plane, [""])
    sketch.MapMode = "FlatFace"
    
    # Rotate the sketch 90 degrees around the X axis so that Sketch Y becomes Global Z.
    # Rotation: X axis fixed, Y -> Z, Z -> -Y.
    # App.Rotation(App.Vector(1, 0, 0), 90)
    sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(1, 0, 0), 90))

    # Generate Geometry for the Stair Profile
    # We will construct the profile using line segments.
    # Origin (0,0) in Sketch coordinates -> (0,0) in Global XZ.
    # X axis = Run, Y axis = Rise.
    
    num_steps = params.number_of_steps
    riser = params.step_riser
    depth = params.step_depth
    
    # Define points for the polyline
    # Start at (0,0)
    # Go Right (Tread) -> (depth, 0)
    # Go Up (Riser) -> (depth, riser)
    # ... repeat ...
    # Close the loop.
    
    points = []
    current_x = 0
    current_y = 0
    
    # Start point
    points.append(App.Vector(current_x, current_y, 0))
    
    # Traverse steps
    for i in range(num_steps):
        # Tread
        current_x += depth
        points.append(App.Vector(current_x, current_y, 0))
        
        # Riser
        current_y += riser
        points.append(App.Vector(current_x, current_y, 0))
        
    # Close the shape
    # Go Left to x=0
    current_x = 0
    points.append(App.Vector(current_x, current_y, 0))
    
    # Go Down to y=0
    current_y = 0
    points.append(App.Vector(current_x, current_y, 0))
    
    # Add the polyline
    polyline = Part.makePolyline(points)
    sketch.addGeometry(polyline, False)
    
    # Add constraints to ensure the sketch is valid and driven by parameters
    # We need to constrain the start point to the origin and the segments to be horizontal/vertical.
    # Since we built the geometry mathematically, the shape is closed and correct.
    # However, Sketcher requires constraints for the solver.
    # We will add constraints for the first segment to anchor it.
    
    # Line 1: Start (0,0) to (depth, 0)
    # Constraint: Start point at Origin (X=0, Y=0)
    # Constraint: Line 1 is Horizontal (Y=0)
    # Constraint: Line 1 End coincident with Line 2 Start
    
    # We need to add individual lines to add constraints easily? 
    # Or constrain the polyline? 
    # Constraining a polyline is hard. Let's add the segments as lines.
    sketch.clearGeometry()
    sketch.clearConstraints()
    
    segments = []
    # Segment 1: Tread 1
    s1_start = App.Vector(0, 0, 0)
    s1_end = App.Vector(depth, 0, 0)
    segments.append((s1_start, s1_end))
    
    # Segment 2: Riser 1
    s2_start = s1_end
    s2_end = App.Vector(depth, riser, 0)
    segments.append((s2_start, s2_end))
    
    # ... Loop for steps
    for i in range(1, num_steps):
        # Tread
        s_start = App.Vector(i*depth, (i-1)*riser, 0)
        s_end = App.Vector((i+1)*depth, (i-1)*riser, 0)
        segments.append((s_start, s_end))
        
        # Riser
        s_start = s_end
        s_end = App.Vector((i+1)*depth, i*riser, 0)
        segments.append((s_start, s_end))
        
    # Closing segments
    # Last Tread end to Top Left
    s_start = App.Vector(num_steps*depth, num_steps*riser, 0)
    s_end = App.Vector(0, num_steps*riser, 0)
    segments.append((s_start, s_end))
    
    # Top Left to Origin
    s_start = App.Vector(0, num_steps*riser, 0)
    s_end = App.Vector(0, 0, 0)
    segments.append((s_start, s_end))
    
    # Add lines
    for i, (p1, p2) in enumerate(segments):
        line = Part.LineSegment(p1, p2)
        sketch.addGeometry(line, False)
        
    # Add Constraints
    # 1. Line 1 Start at Origin (X=0, Y=0)
    sketch.addConstraint(Sketcher.Constraint("X", 1, 0, "0"))
    sketch.addConstraint(Sketcher.Constraint("Y", 1, 0, "0"))
    
    # 2. Line 1 Horizontal (Y=0 for all points)
    sketch.addConstraint(Sketcher.Constraint("Y", 1, 1, "0"))
    
    # 3. Line 1 End coincident with Line 2 Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 2, 0))
    
    # 4. Line 2 Vertical (X=const)
    sketch.addConstraint(Sketcher.Constraint("X", 2, 0, "0")) # X is fixed by coincidence with Line 1 end
    # Actually, Line 2 X is determined by Line 1 end.
    # We need to constrain Line 2 to be vertical (Y varies, X constant).
    # Constraint("Vertical", 2, 0) ? No, "Vertical" constrains the line to be vertical.
    sketch.addConstraint(Sketcher.Constraint("Vertical", 2, 0))
    
    # 5. Line 2 End coincident with Line 3 Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 1, 3, 0))
    
    # 6. Line 3 Horizontal
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 3, 0))
    
    # 7. Line 3 End coincident with Line 4 Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 1, 4, 0))
    
    # 8. Line 4 Vertical
    sketch.addConstraint(Sketcher.Constraint("Vertical", 4, 0))
    
    # 9. Line 4 End coincident with Line 5 Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 4, 1, 5, 0))
    
    # 10. Line 5 Horizontal
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 5, 0))
    
    # 11. Line 5 End coincident with Line 6 Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 5, 1, 6, 0))
    
    # 12. Line 6 Vertical
    sketch.addConstraint(Sketcher.Constraint("Vertical", 6, 0))
    
    # 13. Line 6 End coincident with Line 7 Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 6, 1, 7, 0))
    
    # 14. Line 7 Horizontal
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 7, 0))
    
    # 15. Line 7 End coincident with Line 8 Start
    sketch.addConstraint(Sketcher.Constraint("Coincident", 7, 1, 8, 0))
    
    # 16. Line 8 Vertical
    sketch.addConstraint(Sketcher.Constraint("Vertical", 8, 0))
    
    # 17. Line 8 End coincident with Line 1 Start (Close loop)
    sketch.addConstraint(Sketcher.Constraint("Coincident", 8, 1, 1, 0))

# --- 4. Extrude the Profile ---
# Pad the sketch along the Global Y axis (which is the Sketch Z axis after rotation? No.)
# Recall: Sketch was rotated 90 deg around X.
# Sketch X -> Global X
# Sketch Y -> Global Z
# Sketch Z -> Global -Y
# The sketch lies in the XZ plane.
# We want to extrude along Global Y.
# In the sketch coordinate system, Global Y corresponds to the Sketch Z axis (which is the normal to the sketch plane).
# So we can simply use a Pad with Length = step_width.
# The direction will be along the sketch normal (Global -Y).
# We can reverse it if needed, or just accept the direction.
# The prompt says "extrusion_direction = +Y".
# If we pad along the normal (Global -Y), we go to negative Y.
# We can set pad.Length = -step_width to go to +Y?
# Or we can set pad.Midplane = True and pad.Reversed = True?
# Actually, let's just pad with a positive length. The direction is determined by the sketch normal.
# If the sketch normal is -Y, the pad goes to -Y.
# To go to +Y, we can set pad.Length = -step_width.
# Or we can create the sketch on the XZ plane without rotation, but then X is Run and Y is Rise?
# No, if we don't rotate, Sketch Y is Global Y. Then we can't extrude along Y (width) because Y is the profile height.
# So the rotation is necessary.
# With rotation: Sketch Y = Global Z. Sketch Z = Global -Y.
# Pad along Sketch Z (Normal) -> Global -Y.
# To get Global +Y, we set Length = -step_width.

pad = body.newObject("PartDesign::Pad", "Extrusion")
pad.Profile = sketch
pad.Length = -params.step_width # Negative to go in +Y direction (since normal is -Y)
# pad.Midplane = False
# pad.Reversed = False

# --- 5. Compute and Save ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

doc.saveAs(str(output_path))
