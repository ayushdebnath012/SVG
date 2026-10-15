"""
FreeCAD 1.1 Script to generate a Socket Weld Flange.
Saves the model to /app/answer.FCStd derived from __file__.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

# -----------------------------------------------------------------------------
# 1. Setup Document and Parameters
# -----------------------------------------------------------------------------
doc = App.newDocument("SocketFlange")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define named parameters for the geometry using App::PropertyLength
# We create a container object to hold these parameters cleanly
params_obj = body.newObject("App::Property", "Parameters")
# Note: In FreeCAD 1.1, we often just set properties directly on the Body or a VarSet.
# However, to ensure they are editable and named as requested, we use a VarSet or set them on the Body.
# The most robust way for a "Parameters" object in PartDesign is often a VarSet, 
# but for simplicity and direct access in scripts, we will set them on the Body 
# or a dedicated Property object if the API allows. 
# Given the error in the previous attempt with "App::Parameter", we will use the Body itself 
# to store the parameters or a standard App::Property object.
# Let's use a VarSet as it is the standard for named parameters in PartDesign.
params = body.newObject("App::VarSet", "Parameters")

params.addProperty("App::PropertyLength", "outer_circle_diameter", "Dimensions", "Overall outer diameter")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the main flange")
params.addProperty("App::PropertyLength", "total_height", "Dimensions", "Total height of the flange")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Center hole diameter")
params.addProperty("App::PropertyLength", "neck_diameter", "Dimensions", "Diameter of the neck (under raised face)")
params.addProperty("App::PropertyLength", "neck_height", "Dimensions", "Height of the neck")
params.addProperty("App::PropertyLength", "socket_diameter", "Dimensions", "Diameter of the socket weld recess")
params.addProperty("App::PropertyLength", "socket_depth", "Dimensions", "Depth of the socket weld recess")
params.addProperty("App::PropertyLength", "raised_face_diameter", "Dimensions", "Diameter of the raised face")
params.addProperty("App::PropertyLength", "raised_face_thickness", "Dimensions", "Thickness of the raised face")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of bolt holes")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

# Set default values as per specification
params.outer_circle_diameter = 130.0
params.flange_thickness = 17.5
params.total_height = 22.0
params.bore_diameter = 41.0
params.neck_diameter = 65.0
params.neck_height = 2.5
params.socket_diameter = 49.5
params.socket_depth = 16.0
params.raised_face_diameter = 73.0
params.raised_face_thickness = 2.0
params.bolt_circle_diameter = 98.5
params.bolt_hole_diameter = 16.0
params.number_bolt_holes = 4

# -----------------------------------------------------------------------------
# 2. Base Flange Body (Extruded Disk)
# -----------------------------------------------------------------------------
# Sketch 1: Outer Circle on XY Plane
sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [""])
sketch_base.MapMode = "FlatFace"

# Outer Circle
circle_base = sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_circle_diameter / 2.0), False)
# Center Coincident Constraint
sketch_base.addConstraint(Sketcher.Constraint("Axis", 0, 2))

# Pad the base flange
pad_base = body.newObject("PartDesign::Pad", "PadFlange")
pad_base.Profile = sketch_base
pad_base.Length = params.total_height
pad_base.Midplane = False # Build upwards from bottom

# -----------------------------------------------------------------------------
# 3. Bore Hole (Through All)
# -----------------------------------------------------------------------------
# Sketch 2: Bore on XY Plane
sketch_bore = body.newObject("Sketcher::SketchObject", "SketchBore")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bore.Support = (doc.getObject("XY_Plane"), [""])
sketch_bore.MapMode = "FlatFace"

circle_bore = sketch_bore.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0), False)
sketch_bore.addConstraint(Sketcher.Constraint("Axis", 0, 2))

pocket_bore = body.newObject("PartDesign::Pocket", "PocketBore")
pocket_bore.Profile = sketch_bore
pocket_bore.Type = "ThroughAll"

# -----------------------------------------------------------------------------
# 4. Neck Pocket (Remove material from bottom)
# -----------------------------------------------------------------------------
# Sketch 3: Neck on XY Plane
sketch_neck = body.newObject("Sketcher::SketchObject", "SketchNeck")
sketch_neck.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_neck.Support = (doc.getObject("XY_Plane"), [""])
sketch_neck.MapMode = "FlatFace"

circle_neck = sketch_neck.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.neck_diameter / 2.0), False)
sketch_neck.addConstraint(Sketcher.Constraint("Axis", 0, 2))

pocket_neck = body.newObject("PartDesign::Pocket", "PocketNeck")
pocket_neck.Profile = sketch_neck
pocket_neck.Length = params.neck_height
pocket_neck.Midplane = False

# -----------------------------------------------------------------------------
# 5. Socket Pocket (Remove material from top)
# -----------------------------------------------------------------------------
# Sketch 4: Socket on XY Plane
sketch_socket = body.newObject("Sketcher::SketchObject", "SketchSocket")
sketch_socket.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_socket.Support = (doc.getObject("XY_Plane"), [""])
sketch_socket.MapMode = "FlatFace"

circle_socket = sketch_socket.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.socket_diameter / 2.0), False)
sketch_socket.addConstraint(Sketcher.Constraint("Axis", 0, 2))

pocket_socket = body.newObject("PartDesign::Pocket", "PocketSocket")
pocket_socket.Profile = sketch_socket
pocket_socket.Length = params.socket_depth
pocket_socket.Midplane = True # Cut from both sides, but since we have a bore, it will cut through the rest.
# Actually, for a socket, we want to cut from the top down. Midplane=True cuts from both sides of the sketch plane.
# Since the sketch is on XY (Z=0), Midplane=True cuts from Z=0 upwards and downwards.
# We want to cut from the top (Z=22) downwards.
# So we should use Midplane=False and set Length to socket_depth, but we need to position the sketch at the top?
# Or use Midplane=True and ensure the pocket doesn't interfere with the bore incorrectly.
# Let's use Midplane=True. The pocket will remove material from Z=0 to Z=socket_depth and Z=-socket_depth to 0.
# Since we have a bore through the whole thing, the bottom cut is fine. The top cut creates the socket.
# Wait, if Midplane=True, it cuts from the sketch plane (Z=0) in both directions.
# So it removes Z=0 to Z=16 and Z=-16 to Z=0.
# This creates a hole from the center outwards? No, it creates a cylinder centered at Z=0.
# We want a socket at the top.
# Correct approach: Use Midplane=False, and place the sketch at the top of the flange?
# Or use Midplane=True and accept that it cuts from the center.
# Let's re-evaluate: 
# If we place the sketch at Z=0 and use Midplane=True, we get a hole from Z=-16 to Z=16.
# This is not what we want. We want a hole from Z=(22-16)=6 to Z=22.
# So we need to place the sketch at Z=6? Or use Midplane=False and Length=16, but then we need to define the start/end.
# PartDesign::Pocket with Midplane=False cuts from the sketch plane in one direction.
# If we place the sketch at Z=6 (bottom of socket) and cut upwards (Midplane=False), we get the socket.
# Let's adjust the sketch placement.

sketch_socket.Placement = App.Placement(App.Vector(0, 0, params.total_height - params.socket_depth))
pocket_socket.Midplane = False
pocket_socket.Length = params.socket_depth

# -----------------------------------------------------------------------------
# 6. Raised Face (Optional refinement based on interpretation)
# The problem description mentions "raised_face_diameter" and "raised_face_thickness".
# In a standard socket weld flange, the "Raised Face" is the flat surface on top of the flange 
# that is higher than the gasket seating surface (which is the bottom of the socket).
# In our construction:
# - Top of flange is at Z=22.
# - Bottom of socket is at Z=6.
# - The "Raised Face" is typically the surface at Z=22.
# - The "Raised Face Thickness" is the distance from Z=22 down to the gasket seat (Z=6)? That would be 16mm.
# - But the parameter says "raised_face_thickness=2mm".
# This implies there is a step.
# Interpretation: 
# The top 2mm of the flange (Z=20 to Z=22) is the "Raised Face".
# The area below that (Z=6 to Z=20) is the "Flat Face" or the socket area?
# No, the socket is the recess.
# Let's assume the geometry is:
# 1. Main body 130mm dia, 22mm high.
# 2. Socket recess 49.5mm dia, 16mm deep. (From Z=6 to Z=22).
# 3. Raised Face is the ring at the top (Z=20 to Z=22) between Neck (65) and Raised_Face_Dia (73)?
#    Or is the Raised Face the entire top surface?
# Given the parameters, let's create a specific feature for the Raised Face ring if it exists.
# If "raised_face_diameter" is 73 and "neck_diameter" is 65, there is a ring between 65 and 73.
# If "raised_face_thickness" is 2, maybe this ring is 2mm high?
# Let's assume the Raised Face is a protrusion or a specific surface.
# However, in many socket weld flanges, the "Raised Face" is simply the top surface of the flange 
# which is higher than the socket bottom.
# If the socket depth is 16, and the flange height is 22, the "Raised Face" height is 6mm.
# Why is the parameter 2mm?
# Maybe the socket depth is measured from the Raised Face?
# If Socket Depth = 16 is measured from the top of the Raised Face (Z=22), then the socket bottom is at Z=6.
# If Raised Face Thickness = 2, maybe the Raised Face is a ring at the very top (Z=20 to Z=22) 
# and the rest (Z=6 to Z=20) is the "Flat Face"?
# Let's implement a feature that creates a ring at the top (Z=20 to Z=22) with diameter 73, 
# and the rest of the top (Z=20 to Z=22) with diameter 130 is the "Flat Face"?
# No, that would make the 73mm ring higher than the 130mm ring?
# Let's assume the Raised Face is the ring between Neck (65) and Raised_Face_Dia (73) at the top level.
# And the area from 73 to 130 is the "Flat Face".
# To make the Raised Face distinct, we can pad a ring from Z=20 to Z=22 with diameter 73?
# But the base is already there.
# Let's assume the "Raised Face" is the top surface of the annulus between Neck (65) and Raised_Face_Dia (73).
# And the "Flat Face" is the top surface of the annulus between Raised_Face_Dia (73) and Outer (130).
# This implies the Raised Face is the same height as the Flat Face (Z=22).
# Then what is "raised_face_thickness=2mm"?
# Maybe it means the thickness of the material in the Raised Face region?
# Or maybe the Raised Face is a step up?
# Let's assume the Raised Face is a step up of 2mm.
# So:
# - Base: 130mm dia, 22mm high.
# - Socket: 49.5mm dia, 16mm deep (from top).
# - Neck: 65mm dia, 2.5mm high (from bottom).
# - Raised Face: A ring at the top (Z=20 to Z=22) with diameter 73?
#   If we pad a ring from Z=20 to Z=22 with diameter 73, it will sit on top of the base.
#   But the base is already 130mm high.
#   So we need to cut the base down to 20mm, then pad the Raised Face?
#   This is getting complex.
#   Let's simplify: The "Raised Face" is the top surface of the flange.
#   The "Raised Face Thickness" is the distance from the top of the flange to the bottom of the socket.
#   If Socket Depth = 16, and Raised Face Thickness = 2, then the distance from Top to Socket Bottom is 2mm?
#   That would mean Socket Depth = 2mm? No, Socket Depth is 16.
#   Maybe the Socket Depth is measured from the Raised Face?
#   If Raised Face Thickness = 2, then the Raised Face is the top 2mm.
#   The Socket is 16mm deep from the Raised Face?
#   So Socket Bottom is at Z = 22 - 2 - 16 = 4mm.
#   Let's try this:
#   1. Base: 130mm dia, 22mm high.
#   2. Bore: 41mm through.
#   3. Neck: 65mm dia, 2.5mm high (from bottom).
#   4. Socket: 49.5mm dia, 16mm deep (from the top of the Raised Face, i.e., from Z=20).
#      So Socket Bottom is at Z=4.
#   5. Raised Face: The top surface from Z=20 to Z=22.
#      This is already part of the base.
#      But we need to ensure the Socket doesn't cut into the Raised Face?
#      The Socket is 16mm deep from Z=20. So it goes from Z=20 to Z=4.
#      This leaves the Raised Face (Z=20 to Z=22) intact.
#      This matches the parameters:
#        - Raised Face Thickness = 2mm (Z=20 to Z=22).
#        - Socket Depth = 16mm (Z=20 to Z=4).
#        - Total Height = 22mm.
#        - Neck Height = 2.5mm (Z=0 to Z=2.5).
#      This seems consistent.
#      So we need to adjust the Socket Pocket to start from Z=20.

# Adjust Socket Sketch Placement
sketch_socket.Placement = App.Placement(App.Vector(0, 0, params.total_height - params.raised_face_thickness))
# Now the socket cuts from Z=20 downwards.
# We need to ensure the socket doesn't cut through the neck?
# Socket Bottom = 20 - 16 = 4mm.
# Neck Top = 2.5mm.
# So the socket bottom (Z=4) is above the neck top (Z=2.5).
# This means the socket and neck are separate features, which is good.
# But wait, the socket is 49.5mm dia, neck is 65mm dia.
# The socket is smaller than the neck.
# So the socket is inside the neck?
# No, the socket is a recess. The neck is a depression.
# If the socket is 49.5mm and neck is 65mm, the socket is narrower.
# So the socket is inside the neck?
# No, the socket is at the top, the neck is at the bottom.
# The socket is a hole in the top. The neck is a hole in the bottom.
# They are concentric.
# The socket bottom is at Z=4. The neck top is at Z=2.5.
# So there is a gap between Z=2.5 and Z=4 where the socket and neck don't overlap?
# No, the socket is a hole from Z=20 to Z=4.
# The neck is a hole from Z=0 to Z=2.5.
# So the material exists from Z=2.5 to Z=4 in the region R < 49.5/2?
# Yes, because the socket only goes down to Z=4, and the neck only goes up to Z=2.5.
# So there is a "shoulder" of material between Z=2.5 and Z=4 with diameter 49.5mm?
# No, the socket removes material from R=0 to R=24.75 from Z=20 to Z=4.
# The neck removes material from R=0 to R=32.5 from Z=0 to Z=2.5.
# So in the region R < 24.75:
#   - Z=0 to 2.5: Removed (Neck).
#   - Z=2.5 to 4: Exists (Material).
#   - Z=4 to 20: Removed (Socket).
# This creates a step at Z=4 and Z=2.5.
# This seems correct for a socket weld flange.

# -----------------------------------------------------------------------------
# 7. Bolt Holes
# -----------------------------------------------------------------------------
# Sketch 5: Bolt Holes on XY Plane
sketch_bolts = body.newObject("Sketcher::SketchObject", "SketchBolts")
sketch_bolts.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bolts.Support = (doc.getObject("XY_Plane"), [""])
sketch_bolts.MapMode = "FlatFace"

# Add bolt hole circles
for i in range(params.number_bolt_holes):
    angle = (i / params.number_bolt_holes) * 360.0
    x = (params.bolt_circle_diameter / 2.0) * math.cos(math.radians(angle))
    y = (params.bolt_circle_diameter / 2.0) * math.sin(math.radians(angle))
    circle_bolt = sketch_bolts.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0), False)

# Add constraints to keep them on the circle
for i in range(params.number_bolt_holes):
    angle = (i / params.number_bolt_holes) * 360.0
    x = (params.bolt_circle_diameter / 2.0) * math.cos(math.radians(angle))
    y = (params.bolt_circle_diameter / 2.0) * math.sin(math.radians(angle))
    # Distance constraint from center
    sketch_bolts.addConstraint(Sketcher.Constraint("DistanceXY", i, 2, 0, 0, params.bolt_circle_diameter / 2.0))
    # Coincident with center? No, we need them on the circle.
    # We can use a polar pattern instead of manual constraints.
    # Let's remove the manual constraints and use a pattern.
    # But we need to create the geometry first.
    # We can use a single circle and pattern it.
    pass

# Let's redo the bolt holes using a pattern.
# Sketch 5: Single Bolt Hole
sketch_bolts.clearGeometry()
sketch_bolts.clearConstraints()
circle_bolt_single = sketch_bolts.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0), False)
sketch_bolts.addConstraint(Sketcher.Constraint("Axis", 0, 2))

# Pattern the bolt holes
pattern_bolts = body.newObject("PartDesign::PolarPattern", "PatternBolts")
pattern_bolts.Profile = sketch_bolts
pattern_bolts.Axis = (doc.getObject("Z_Axis"), [""])
pattern_bolts.Occurrences = params.number_bolt_holes
pattern_bolts.Angle = 360.0
pattern_bolts.Distribute = False # Distribute along the circle
pattern_bolts.Reference = (sketch_bolts, [""]) # Reference the sketch

# -----------------------------------------------------------------------------
# 8. Fillets (Optional, but good for realism)
# -----------------------------------------------------------------------------
# Fillet the outer edge of the flange
# We need to select the edge.
# The outer edge of the base pad.
# We can use a Chamfer or Fillet feature.
# Let's add a small fillet to the outer edge.
# We need to find the edge.
# Since we are building parametrically, we can use a generic edge selection if possible,
# but PartDesign::Fillet requires an edge list.
# We can use the "Edge" property of the feature if we know the index, but that's fragile.
# Alternatively, we can use a Chamfer with a specific edge.
# Let's skip the fillet for now to keep the script robust, or use a simple chamfer.
# The problem description doesn't specify fillets, so we'll skip them.

# -----------------------------------------------------------------------------
# 9. Recompute and Save
# -----------------------------------------------------------------------------
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name("answer.FCStd")

doc.saveAs(str(output_path))
