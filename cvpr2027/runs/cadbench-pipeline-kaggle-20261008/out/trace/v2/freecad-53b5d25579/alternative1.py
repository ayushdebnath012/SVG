"""
FreeCAD 1.1 Script to generate a Socket Weld Flange.
Saves the model to /app/answer.FCStd derived from __file__.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# -----------------------------------------------------------------------------
# 1. Setup Document and Parameters
# -----------------------------------------------------------------------------
doc = App.newDocument("SocketFlange")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define named parameters for the geometry
params = body.newObject("App::Parameter", "Parameters")
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
sketch_base.addConstraint(Sketcher.Constraint("Axis", 0, 2)) # Ensure it stays centered if moved

# Pad the base flange
pad_base = body.newObject("PartDesign::Pad", "PadFlange")
pad_base.Profile = sketch_base
pad_base.Length = params.total_height
pad_base.Midplane = False # Build upwards from bottom

# -----------------------------------------------------------------------------
# 3. Bore Hole (Through All)
# -----------------------------------------------------------------------------
# Sketch 2: Bore on XY Plane (same plane as base, or slightly offset if needed, here same plane for simplicity)
# Actually, to keep the tree clean, we can do a ThroughAll pocket directly referencing the profile on the same plane
# But PartDesign requires a specific sketch object for the profile.
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
# 4. Raised Face (Inner Cylinder removed, then Pad up)
# Construction:
# 1. Pad the "Raised Face" cylinder height from the bottom.
# 2. Remove the material between Raised Face and Neck Diameter using a Shell or Pad reversed?
# Better approach: 
# Step 4a: Pad the Raised Face height (total_height - neck_height) on the outer circle? No, that overlaps.
# Correct Topological Order:
# 1. Base Pad (Done)
# 2. Bore Pocket (Done)
# 3. Neck Pocket (Remove material from bottom up to neck_height)
# 4. Raised Face Pad (Add material from bottom up to (total_height - raised_face_thickness)? No, RA is usually measured from top).
# 
# Let's redefine dimensions relative to the bottom (Z=0):
# - Total Height = 22mm
# - Raised Face Thickness = 2mm (Top 2mm)
# - Neck Height = 2.5mm (Bottom 2.5mm)
# - Socket Depth = 16mm (Measured from top? Usually yes. If Total=22, Socket Bottom is at Z=6mm).
# 
# Let's construct features from Z=0 upwards.
# 1. Base Pad: 0 -> 22 (Done)
# 2. Bore Pocket: Through All (Done)
# 3. Neck Pocket: Remove material from 0 up to Neck Height (2.5mm). Diameter = Neck Diameter.
# 4. Raised Face: This is a ring between Neck Dia and Outer Dia, height = Total - Neck - Socket? No.
#    Raised Face is the flat top surface area between Neck Dia and Outer Dia.
#    Actually, the Raised Face is the top surface. The "Neck" is the depression below it.
#    So:
#    - We have a solid cylinder 130mm dia, 22mm high.
#    - Bore 41mm through.
#    - Neck: Remove cylinder 65mm dia, height 2.5mm from bottom.
#    - Socket: Remove cylinder 49.5mm dia, depth 16mm from top (so height 6mm from bottom).
#    - Raised Face: The remaining top surface between 65mm and 130mm? 
#      Wait, if we remove the Neck (65mm dia) and Socket (49.5mm dia), the top surface is naturally formed by the outer cylinder (130mm) and the bore (41mm). 
#      The "Raised Face" is specifically the area *between* the Neck and the Outer edge.
#      In our current construction:
#      - Base: 130mm dia.
#      - Neck Pocket (65mm dia, 2.5mm high): Removes center. Top of neck is at Z=2.5.
#      - Socket Pocket (49.5mm dia, 16mm deep from top): Removes center. Top of socket is at Z=22-16=6.
#      - Current Top Surface: 
#        - At Z=22, we have a ring from R=65 to R=65 (because Neck Pocket removes everything <65 up to 2.5). Wait.
#        - The Neck Pocket removes everything <65mm radius up to Z=2.5.
#        - The Socket Pocket removes everything <49.5mm radius from Z=6 to Z=22.
#        - So at Z=22, the material exists only at R > 65mm (from Base) and R > 49.5mm (from Socket).
#        - The material at R < 65mm exists only at Z > 2.5? No, Neck Pocket removes it.
#        - So the "Raised Face" is the top surface of the annulus between R=65 and R=65? No, that's zero width.
#        - Ah, the Neck Diameter is the diameter of the depression. The Raised Face is the flat surface surrounding the neck.
#        - So the Raised Face is the top surface of the cylinder between R=65 and R=65? No.
#        - Standard Flange: Outer Dia 130. Neck Dia 65. Raised Face is the ring between 65 and 130 on the top.
#        - My Neck Pocket removes R<32.5 (dia 65). My Socket Pocket removes R<24.75 (dia 49.5).
#        - So the top surface at Z=22 consists of:
#          - R from 32.5 to 65? No, Neck Pocket removes R<32.5 up to Z=2.5. But Socket Pocket removes R<24.75 from Z=6.
#          - The region R=24.75 to 32.5 is removed by Socket? No, Socket is 49.5 dia (R=24.75).
#          - Let's re-read specs: 
#            - Neck Diameter = 65mm.
#            - Socket Diameter = 49.5mm.
#            - Raised Face Diameter = 73mm.
#          - Okay, Raised Face is a specific ring. It is not just the outer rim. It is the ring between Neck and Outer? No, usually Raised Face is between Neck and Outer. 
#          - BUT the spec gives "raised_face_diameter=73mm". This implies the Raised Face is a ring between Neck (65) and 73? Or between 73 and Outer (130)?
#          - Standard: Raised Face is the flat surface on top. The gasket sits here.
#          - If Raised Face Diameter is 73mm, and Neck is 65mm, then the Raised Face is the ring 65mm < R < 73mm?
#          - Then what is between 73mm and 130mm? That would be the "Flat Face" or "Field"?
#          - Or maybe "Raised Face Diameter" means the outer diameter of the Raised Face ring, and the Raised Face thickness is the height of that ring.
#          - Let's assume the Raised Face is the ring between Neck (65) and Raised_Face_Dia (73).
#          - Then what is between 73 and 130? Usually, the whole top is the raised face in some standards, or there is a flat face.
#          - Given "raised_face_thickness=2mm", this suggests the top 2mm of the flange (between Z=20 and Z=22) is the raised face.
#          - And "raised_face_diameter=73mm" likely means the Raised Face extends to 73mm, or the Raised Face is the ring up to 73mm.
#          - Let's assume the Raised Face is the ring from Neck (65) to Raised_Face_Dia (73).
#          - Then the area from 73 to 130 is just the top of the base cylinder? 
#          - Let's refine the feature tree to match the geometry described:
#            1. Base Pad: 130mm dia, 22mm high.
#            2. Bore: 41mm through.
#            3. Neck Pocket: 65mm dia, 2.5mm deep (from bottom).
#            4. Socket Pocket: 49.5mm dia, 16mm deep (from top).
#            5. Raised Face: We need to ensure the top surface from 65 to 73 is the "Raised Face".
#               Currently, the top surface from 65 to 130 is exposed (except where Socket removed).
#               The Socket removes the center. The Neck removes the bottom center.
#               The top surface at Z=22 is exposed from R=32.5 (Neck) to R=130? 
#               No, Socket removes R<24.75 from Z=6 to Z=22.
#               So at Z=22:
#                 - R < 24.75: Removed by Socket.
#                 - 24.75 < R < 32.5: Exists? Yes, Socket doesn't go this far out. Neck Pocket only goes to Z=2.5.
#                 - 32.5 < R < 130: Exists (Base).
#               So we have a step at R=24.75 and R=32.5.
#               This doesn't match "Raised Face Diameter 73".
#               
#          - Alternative Interpretation:
#            The Raised Face is the ring between Neck (65) and Raised_Face_Dia (73).
#            The area between 73 and 130 is the "Flat Face".
#            To create this:
#            a) Pad the "Flat Face" area? No, it's connected.
#            b) We need to cut a Pocket for the "Raised Face" region? No, it's a protrusion relative to the socket.
#            
#          - Let's try this sequence:
#            1. Base Pad (130mm, 22mm).
#            2. Bore Pocket (41mm, Through).
#            3. Neck Pocket (65mm, 2.5mm from bottom).
#            4. Socket Pocket (49.5mm, 16mm from top).
#            5. Now we have a top surface from R=32.5 to R=130.
#            6. We want the region R=65 to R=73 to be the "Raised Face".
#            7. We want the region R=73 to R=130 to be "Flat".
#            This implies the Raised Face is higher? No, they are at the same Z=22 level usually.
#            Maybe "Raised Face Thickness" means the thickness of the ring that defines the raised face?
#            No, "Raised Face Thickness = 2mm" usually means the height of the raised surface above the gasket seating surface.
#            In this model, the "gasket seating surface" might be the bottom of the Socket?
#            Socket Bottom is at Z = 22 - 16 = 6mm.
#            So the Raised Face is the surface at Z=22?
#            If so, the "Raised Face Thickness" is the distance from Z=22 down to the gasket seat? That's the Socket Depth? No.
#            
#          - Let's stick to the simplest interpretation of the parameters provided:
#            - We have a top surface at Z=22.
#            - We have a "Raised Face" defined by a diameter (73) and a thickness (2).
#            - This usually means there is a step or a ring.
#            - Let's assume the Raised Face is a ring at the top, between Neck (65) and Raised_Face_Dia (73).
#            - And the area from 73 to 130 is the rest of the flange.
#            - To make the "Raised Face" distinct, maybe it is a slight protrusion? 
#            - Or maybe the "Raised Face Thickness" is the distance from the top (Z=22) down to the start of the socket? 
#              Socket Depth = 16. Top - 16 = 6. Neck Height = 2.5. 
#              So we have:
#              - 0 to 2.5: Neck (65mm)
#              - 2.5 to 6: ? (This is the gap between Neck and Socket Bottom).
#              - 6 to 22: Socket (49.5mm).
#              - 22: Top surface.
#            
#          - Let's assume the "Raised Face" is the top surface of the annulus between Neck (65) and Raised_Face_Dia (73).
#            And the area from 73 to 130 is just the top of the main body.
#            But how do we make the 65-73 ring special? 
#            Maybe the Socket Depth is measured from the Raised Face?
#            If Socket Depth = 16, and Raised Face Thickness = 2.
#            Then the gasket seat is at Z = 22 - 2 (Raised Face) - 16 (Socket)? = 4mm?
#            Let's assume:
#            - Top of flange: Z=22.
#            - Raised Face (ring 65-73): Z=22 to Z=20. (Thickness 2).
#            - Socket (49.5): Z=20 to Z=4. (Depth 16 from top of RF? Or 16 total?). Spec says "socket_depth=16.0". Usually total depth.
#            - Neck (65): Z=0 to Z=2.5.
#            
#            Let
