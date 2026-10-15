import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("SmoothShaft")

# --- Parameters ---
# We will use App::Parameter objects to store the values and drive features via expressions.
# This ensures the geometry is editable and driven by named objects.

# 1. Create a container for parameters (optional but good practice for organization)
# However, for simplicity in a single script, we can just create the Parameter objects directly.
# We need to ensure they exist before we try to reference them in expressions.

# Define parameter names
P_SHAFT_DIAM = "smooth_shaft_diameter"
P_SHAFT_LEN = "smooth_shaft_length"
P_KEY_W = "keyway_width"
P_KEY_D = "keyway_depth"
P_KEY_H = "keyway_height"
P_NUM_KEY = "num_keyway"

# Create Parameter objects
params = []
for name in [P_SHAFT_DIAM, P_SHAFT_LEN, P_KEY_W, P_KEY_D, P_KEY_H, P_NUM_KEY]:
    p = doc.addObject("App::Parameter", name)
    p.Value = 0.0
    params.append(p)

# Set initial values
params[0].Value = 50.0  # diameter
params[1].Value = 80.0  # length
params[2].Value = 5.0   # width
params[3].Value = 3.0   # depth
params[4].Value = 20.0  # height
params[5].Value = 2     # number

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# --- Main Shaft Sketch ---
# Create a sketch on the XY plane
sketch_shaft = body.newObject("Sketcher::SketchObject", "ShaftProfile")
sketch_shaft.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_shaft.ConstrainAuto = True
sketch_shaft.TechDrawPictogramSequence = 1

# Add a circle for the shaft profile
# Center at (0,0), Radius = Diameter / 2
radius_expr = f"({params[0].Value})/2"
circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), float(radius_expr))
sketch_shaft.addGeometry(circle, False)

# Add constraints to fix the circle
# Coincident center to origin (0,0)
# We need to reference the XY plane axes. In FreeCAD 1.1 headless, we usually reference the plane object itself or axes if available.
# Since we are on XY plane, the origin is (0,0,0).
# Let's add a point constraint to the origin if possible, or just rely on the placement.
# To be robust, let's add a point at (0,0) and constrain it to the circle center.
# Actually, the simplest way in headless without explicit axis objects is to constrain the circle center to a point.
# Let's add a point geometry.
point = Part.Point(App.Vector(0, 0, 0))
sketch_shaft.addGeometry(point, False)

# Constraint: Coincident between circle center and point
# Geometry indices: 0 is circle, 1 is point.
# Circle center is index 2 (center point of circle). Point is index 0.
# Note: Sketcher constraints use geometry indices.
# Circle: 0. Point: 1.
# Circle center index: 2. Point index: 0.
sketch_shaft.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 0))

# --- Pad the Shaft ---
pad_shaft = body.newObject("PartDesign::Pad", "PadShaft")
pad_shaft.Profile = sketch_shaft
# Length driven by parameter
pad_shaft.setExpression("Length", f"{params[1].Value}")
pad_shaft.Type = "Solid"
pad_shaft.MidPlane = False

# --- Keyway Sketch ---
# Create a sketch on the XZ plane (or YZ, depending on orientation). 
# Let's assume the shaft is along Z. So keyways are cut along Z.
# We need a sketch on a plane perpendicular to the shaft axis? 
# No, keyways are usually longitudinal slots. 
# If the shaft is along Z, the keyway is a slot running along Z.
# We can create a sketch on the XZ plane (side view) and revolve it? No, that makes a hole.
# We can create a sketch on the XZ plane and use a Pad? No, Pad extrudes normal to the plane.
# If we sketch on XZ plane, normal is Y. Extruding along Y creates a slot across the diameter.
# That is a keyway!
# So: Sketch on XZ plane. Profile is a rectangle. Extrude (Pad) along Y axis.
# Wait, if we sketch on XZ, the normal is Y. The pad will extrude along Y.
# The shaft is along Z. So the pad will cut a slot across the shaft diameter.
# This is correct for a keyway.

sketch_key = body.newObject("Sketcher::SketchObject", "KeywayProfile")
sketch_key.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_key.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 90)) # Rotate to align with XZ plane?
# Actually, let's just create the sketch on the XZ plane directly.
# In FreeCAD, planes are XY, XZ, YZ.
# If we use XZ plane, the normal is Y.
# We need to attach the sketch to the XZ plane.
# The Body has access to planes via doc.getObject("XZ_Plane") etc.

# Let's attach to XZ_Plane
sketch_key.Placement = App.Placement(App.Vector(0, 0, 0))
# We need to set the attachment support.
# In PartDesign, SketchObject has AttachmentSupport.
# We need to find the XZ plane object.
xz_plane = doc.getObject("XZ_Plane")
if xz_plane:
    sketch_key.Placement = App.Placement(App.Vector(0, 0, 0))
    # The placement of the sketch object itself defines its position relative to the attachment.
    # If AttachmentSupport is set, the sketch is placed on that face.
    sketch_key.Placement = App.Placement(App.Vector(0, 0, 0))
    # We need to explicitly set the attachment support for the sketch object
    # But in headless, we often just set the Placement and assume the plane is at origin.
    # However, to be safe and explicit:
    sketch_key.Placement = App.Placement(App.Vector(0, 0, 0))
    # Let's just draw the rectangle on the XZ plane.
    # The rectangle will be defined by width (X) and height (Z).
    # Keyway width is along X (across diameter). Keyway height is along Z (length of shaft).
    # Wait, standard keyway: width is across the shaft diameter, length is along the shaft.
    # So on XZ plane: Width = keyway_width (along X), Height = keyway_height (along Z).
    
    # Draw Rectangle
    # Bottom left corner at (0, 0) -> (width, height)
    # But we need it centered on the shaft axis (which is Z axis, passing through 0,0 in XZ plane).
    # So x goes from -w/2 to +w/2. z goes from 0 to h.
    
    w_expr = f"({params[2].Value})"
    h_expr = f"({params[4].Value})"
    
    # Line 1: Bottom
    p1 = App.Vector(-float(w_expr)/2, 0, 0)
    p2 = App.Vector(float(w_expr)/2, 0, 0)
    sketch_key.addGeometry(Part.LineSegment(p1, p2), False)
    
    # Line 2: Top
    p3 = App.Vector(-float(w_expr)/2, float(h_expr), 0)
    p4 = App.Vector(float(w_expr)/2, float(h_expr), 0)
    sketch_key.addGeometry(Part.LineSegment(p3, p4), False)
    
    # Line 3: Right
    sketch_key.addGeometry(Part.LineSegment(p2, p4), False)
    
    # Line 4: Left
    sketch_key.addGeometry(Part.LineSegment(p1, p3), False)
    
    # Constraints
    # Center X: Coincident midpoints or use symmetry.
    # Let's constrain the center of the bottom line to the origin (0,0).
    # Geometry indices: 0 (Line1), 1 (Line2), 2 (Line3), 3 (Line4).
    # Line 1 points: 0, 1. Midpoint index: 2.
    # Origin point: We need a point at (0,0).
    # Let's add a point at (0,0) and constrain it.
    origin_point = Part.Point(App.Vector(0, 0, 0))
    sketch_key.addGeometry(origin_point, False)
    
    # Coincident Line1 midpoint to origin
    sketch_key.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 4, 0)) # 0 is Line1, 2 is mid, 4 is Point, 0 is point
    
    # Vertical alignment: Bottom of rectangle on X axis (Z=0)
    # Line 1 is on Z=0. Line 3 is vertical.
    # We can constrain the bottom-left corner (p1) to be on the X axis? 
    # Or simply constrain the bottom line to the X axis.
    # X axis is a line.
    # Let's add a line for X axis.
    x_axis = Part.LineSegment(App.Vector(-100, 0, 0), App.Vector(100, 0, 0))
    sketch_key.addGeometry(x_axis, False)
    
    # Coincident Line1 (bottom) to X axis? No, Line1 is a segment.
    # Let's constrain the bottom-left point (p1) to the X axis.
    # Point index 0 of Line1 is p1.
    # Line index 4 is X axis.
    sketch_key.addConstraint(Sketcher.Constraint("PointOnLine", 0, 0, 4, 0))
    
    # Right side of keyway should be at X = w/2.
    # We can constrain the right edge to a vertical line at X=w/2.
    # Or simpler: constrain the right-bottom corner (p2) to have X = w/2.
    # But we don't have a vertical line at w/2.
    # Let's just constrain the width using a dimension constraint if possible, 
    # or rely on the geometry construction.
    # Since we constructed it with expressions, the geometry is correct.
    # We just need to fix the position.
    # We have: Center X constrained to 0. Bottom Z constrained to 0.
    # This fixes the rectangle position.
    
    # Add constraints to make it robust
    # Horizontal symmetry: Coincident midpoints of top and bottom lines?
    # Or just constrain the center of the rectangle to the origin.
    # We already constrained the bottom center to origin.
    # Now constrain the top center to the origin? No, that would force height to 0.
    # We need to constrain the vertical position of the top line? No, height is fixed by expression.
    # We need to ensure the rectangle is upright.
    # Perpendicular constraint between bottom and right lines.
    sketch_key.addConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 2, 0)) # Line1 and Line3
    
    # --- Pocket the Keyway ---
    # The sketch is on XZ plane. Normal is Y.
    # We want to cut along the Z axis (length of shaft).
    # Wait. If we sketch on XZ, the normal is Y.
    # If we use a Pad on this sketch, it extrudes along Y.
    # The shaft is along Z.
    # Extruding along Y cuts a slot across the diameter.
    # This is exactly what we want for a keyway (a slot across the diameter).
    # The length of the slot is determined by the height of the rectangle (along Z).
    # The width of the slot is determined by the width of the rectangle (along X).
    # So: Sketch on XZ -> Pad along Y.
    
    pocket_key = body.newObject("PartDesign::Pocket", "PocketKeyway")
    pocket_key.Profile = sketch_key
    pocket_key.Type = "Blind"
    pocket_key.setExpression("Length", f"{params[4].Value}") # Length along Y axis = Keyway Height (Z dimension in sketch)
    # Wait, the parameter P_KEY_H is "keyway_height". In the description:
    # "keyway_height = 20 mm". Usually keyway length is along the shaft.
    # My sketch has height along Z (shaft axis).
    # So the extrusion length (along Y) should be the width of the keyway (across diameter)?
    # No.
    # Let's re-evaluate the geometry.
    # Shaft is along Z.
    # Keyway is a slot along Z.
    # Cross section of keyway is a rectangle in the X-Y plane? No, X-Z plane?
    # If the keyway runs along Z, its cross section is in the X-Y plane.
    # So we should sketch on the X-Y plane (or Y-Z plane) and extrude along Z.
    # Let's switch strategy.
    
    # Strategy 2:
    # Sketch on X-Y plane (Top view).
    # Draw a rectangle: Width = keyway_width (along X), Length = keyway_height (along Y? No, along Z).
    # If we sketch on X-Y, we can't draw a dimension along Z directly.
    # We can draw a rectangle in X-Y with width = keyway_width and length = keyway_height?
    # No, the keyway length is along Z.
    # So in the X-Y sketch, we draw a rectangle of width = keyway_width and length = keyway_height?
    # No, the keyway length is along Z. The sketch is on X-Y.
    # So the rectangle in the sketch represents the cross-section of the keyway.
    # The rectangle dimensions are: Width (along X) = keyway_width. Depth (along Y) = keyway_depth.
    # Then we extrude (Pad) along Z for the length of the keyway (keyway_height).
    
    # Let's do this.
    # 1. Sketch on X-Y plane.
    # 2. Rectangle: Width = keyway_width, Height = keyway_depth.
    # 3. Pad along Z with Length = keyway_height.
    
    # Re-create the sketch for this strategy.
    # Delete the previous sketch_key? No, let's just overwrite the object or create a new one.
    # Let's create a new sketch object named "KeywayProfile2" and replace the old one?
    # Or just create a new one and use it.
    
    sketch_key2 = body.newObject("Sketcher::SketchObject", "KeywayProfile2")
    # Attach to XY plane
    xy_plane = doc.getObject("XY_Plane")
    sketch_key2.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # Draw Rectangle
    # Center at (0,0). Width along X, Height along Y.
    w_expr = f"({params[2].Value})"
    d_expr = f"({params[3].Value})"
    
    # Points
    p1 = App.Vector(-float(w_expr)/2, -float(d_expr)/2, 0)
    p2 = App.Vector(float(w_expr)/2, -float(d_expr)/2, 0)
    p3 = App.Vector(float(w_expr)/2, float(d_expr)/2, 0)
    p4 = App.Vector(-float(w_expr)/2, float(d_expr)/2, 0)
    
    sketch_key2.addGeometry(Part.LineSegment(p1, p2), False)
    sketch_key2.addGeometry(Part.LineSegment(p2, p3), False)
    sketch_key2.addGeometry(Part.LineSegment(p3, p4), False)
    sketch_key2.addGeometry(Part.LineSegment(p4, p1), False)
    
    # Add origin point
    origin_point2 = Part.Point(App.Vector(0, 0, 0))
    sketch_key2.addGeometry(origin_point2, False)
    
    # Constraints
    # Center X: Coincident midpoint of bottom line to origin
    sketch_key2.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 5, 0)) # 0 is Line1, 2 is mid, 5 is Point, 0 is point
    
    # Center Y: Coincident midpoint of left line to origin
    sketch_key2.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 5, 0)) # 3 is Line4, 2 is mid, 5 is Point, 0 is point
    
    # Perpendicular
    sketch_key2.addConstraint(Sketcher.Constraint("Perpendicular", 0, 1, 1, 0))
    
    # --- Pocket the Keyway (Extrude along Z) ---
    pocket_key2 = body.newObject("PartDesign::Pocket", "PocketKeyway2")
    pocket_key2.Profile = sketch_key2
    pocket_key2.Type = "Blind"
    # Extrude along Z (normal to XY plane)
    pocket_key2.setExpression("Length", f"{params[4].
