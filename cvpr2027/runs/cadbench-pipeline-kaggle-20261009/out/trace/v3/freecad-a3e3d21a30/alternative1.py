import FreeCAD as App
import Part
from pathlib import Path
import math

# Initialize document
doc = App.newDocument("SteeringBracket")

# Create the main body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# --- Parameters ---
params = body.newObject("App::VarSet", "Parameters")

# Main Sleeve
params.addProperty("App::PropertyLength", "main_sleeve_outer_diameter", "Dimensions", "main_sleeve_outer_diameter")
params.main_sleeve_outer_diameter = 24.76
params.addProperty("App::PropertyLength", "main_sleeve_bore_diameter", "Dimensions", "main_sleeve_bore_diameter")
params.main_sleeve_bore_diameter = 15.88
params.addProperty("App::PropertyLength", "main_sleeve_length", "Dimensions", "main_sleeve_length")
params.main_sleeve_length = 35.18

# Plate & Eye Profiles
params.addProperty("App::PropertyLength", "side_eye_hole_diameter", "Dimensions", "side_eye_hole_diameter")
params.side_eye_hole_diameter = 8.0
params.addProperty("App::PropertyLength", "side_eye_outer_arc_radius", "Dimensions", "side_eye_outer_arc_radius")
params.side_eye_outer_arc_radius = 8.26
params.addProperty("App::PropertyLength", "side_plate_profile_half_height", "Dimensions", "side_plate_profile_half_height")
params.side_plate_profile_half_height = 14.61
params.addProperty("App::PropertyLength", "first_eye_center_offset", "Dimensions", "first_eye_center_offset")
params.first_eye_center_offset = 27.94
params.addProperty("App::PropertyLength", "side_plate_outer_face_offset", "Dimensions", "side_plate_outer_face_offset")
params.side_plate_outer_face_offset = 11.43
params.addProperty("App::PropertyLength", "side_plate_thickness", "Dimensions", "side_plate_thickness")
params.side_plate_thickness = 4.57
params.addProperty("App::PropertyLength", "eye_profile_spacing", "Dimensions", "eye_profile_spacing")
params.eye_profile_spacing = 9.4
params.addProperty("App::PropertyInteger", "number_of_eye_profiles", "Dimensions", "number_of_eye_profiles")
params.number_of_eye_profiles = 3

# Secondary Boss
params.addProperty("App::PropertyLength", "secondary_boss_outer_diameter", "Dimensions", "secondary_boss_outer_diameter")
params.secondary_boss_outer_diameter = 15.56
params.addProperty("App::PropertyLength", "secondary_boss_inner_diameter", "Dimensions", "secondary_boss_inner_diameter")
params.secondary_boss_inner_diameter = 8.0
params.addProperty("App::PropertyLength", "secondary_boss_inboard_projection", "Dimensions", "secondary_boss_inboard_projection")
params.secondary_boss_inboard_projection = 22.1
params.addProperty("App::PropertyLength", "secondary_boss_outboard_projection", "Dimensions", "secondary_boss_outboard_projection")
params.secondary_boss_outboard_projection = 3.81
params.addProperty("App::PropertyLength", "secondary_boss_length", "Dimensions", "secondary_boss_length")
params.secondary_boss_length = 30.48

# --- Helper to get sketch from body ---
def get_sketch(name):
    return body.getObject(name)

# --- 1. Main Sleeve ---
# Create XZ plane sketch for the main sleeve (cylinder along Z)
main_sketch = body.newObject("Sketcher::SketchObject", "MainSleeveSketch")
main_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
main_sketch.AttachmentSupport = [(doc.getObject("XY_Plane"), [""])]
main_sketch.MapMode = "FlatFace"
main_sketch.Constraints = []

# Outer circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.main_sleeve_outer_diameter / 2)
main_sketch.addGeometry(outer_circle, False)
main_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 1))

# Inner circle (bore)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.main_sleeve_bore_diameter / 2)
main_sketch.addGeometry(inner_circle, False)
main_sketch.addConstraint(Sketcher.Constraint("Axis", 0, 1))

# Pad the sleeve
sleeve_pad = body.newObject("PartDesign::Pad", "SleevePad")
sleeve_pad.Profile = main_sketch
sleeve_pad.Length = params.main_sleeve_length
sleeve_pad.Midplane = True
sleeve_pad.setExpression("Length", "Parameters.main_sleeve_length")

# --- 2. Side Plate with Eyes ---
# The plate lies on one side (let's say -Z side relative to the center of the bracket, or we can orient the bracket such that the plate is in XZ plane and extends in Y).
# Let's define the bracket such that the main sleeve is along Z.
# The plate lies on the "bottom" (negative Z side) of the main sleeve, extending in the negative Y direction? 
# Wait, description says "extends laterally, perpendicular to the sleeve axis".
# Let's place the main sleeve along Z.
# Plate lies on one side (e.g., -Z face of the sleeve? No, "lies on one side... extends laterally").
# Usually, a bracket plate is a flat sheet attached to the side.
# Let's put the plate in the XZ plane, attached to the -Z face of the cylinder? No, that would be a disk.
# Let's put the plate in the XZ plane, but the cylinder is also in XZ? No, cylinder is Z.
# If cylinder is Z, a plate "lying on one side" could be in the XZ plane (vertical) or YZ plane.
# Let's assume the plate is in the XZ plane, attached to the side of the cylinder. 
# Actually, standard orientation: Cylinder along Z. Plate is a flat sheet perpendicular to Z, located at some Z.
# "Lies on one side... extends laterally". This implies the plate is a thin slab.
# Let's define the plate to be in the XZ plane (Y=0), but that would intersect the cylinder volume if the cylinder is centered at 0,0.
# Wait, "thin plate lies on one side of the sleeve". 
# Interpretation A: Plate is in YZ plane, attached to the X=Radius face of the cylinder.
# Interpretation B: Plate is in XZ plane, attached to the Z=Face of the cylinder.
# "Extends laterally, perpendicular to the sleeve axis". Sleeve axis = Z. Perpendicular = X or Y.
# So the plate normal is Z or -Z? No, the plate surface is perpendicular to Z.
# So the plate lies in the XZ or YZ plane? No, if the plate normal is Z, it's a disk.
# If the plate lies in the XZ plane, its normal is Y. It is perpendicular to the sleeve axis (Z).
# "Lies on one side": Maybe it's attached to the side of the sleeve?
# Let's assume the plate is in the XZ plane (Y=0), and the "side" refers to the location along the Z axis? 
# Or maybe the plate is in the YZ plane (X=0)?
# Let's re-read: "A thin plate lies on one side of the sleeve and extends laterally".
# If the sleeve is Z, lateral is X or Y.
# If the plate is in the XZ plane, it extends in X.
# Let's assume the plate is in the XZ plane, centered at (0,0,0), and the "sleeve" is the cylinder.
# But the cylinder is at X=0. The plate at Y=0 would be a cross-section of the cylinder?
# Ah, "lies on one side" might mean it's attached to the side surface.
# Let's assume the plate is in the XZ plane, but shifted? 
# No, "centered hollow main sleeve". "Plate lies on one side".
# Let's assume the plate is in the YZ plane (Normal X), attached to the X=+R face of the cylinder.
# "Extends laterally": Extends in Y.
# This makes sense. Plate is in YZ plane. Sleeve is along Z.
# Let's proceed with this: Plate in YZ plane. Centered at X = main_sleeve_outer_diameter/2.
# The plate has a thickness (side_plate_thickness).
# The "plate occupies the inward side of side_plate_outer_face_offset".
# This is tricky. "Inward side of offset".
# Let's define the plate geometry carefully.
# Plate center line is at X = main_sleeve_outer_diameter/2.
# Plate extends in Y.
# "Inward side" might refer to the Z position? Or the thickness direction?
# "side_plate_outer_face_offset = 11.43". This likely defines the position of the outer face relative to the eye centers.
# "The plate occupies the inward side of side_plate_outer_face_offset".
# Let's assume the eyes are arranged along the Y axis.
# Eye centers are at Y = first_eye_center_offset, Y = first + spacing, Y = first + 2*spacing?
# "Centers progress outward from the sleeve". Sleeve is at X=R. So outward means increasing Y?
# Let's assume eyes are along the Y axis.
# Eye 1 center: Y = first_eye_center_offset.
# Eye 2 center: Y = first_eye_center_offset + eye_profile_spacing.
# Eye 3 center: Y = first_eye_center_offset + 2*eye_profile_spacing.
# The plate extends laterally (Y).
# "side_plate_outer_face_offset": This sounds like the distance from the sleeve centerline (or some reference) to the outer edge of the plate?
# "The plate occupies the inward side of side_plate_outer_face_offset".
# Maybe the plate's outer face is at Y = -side_plate_outer_face_offset? And the eyes are on the positive side?
# Or maybe the plate is between Y = -side_plate_outer_face_offset and Y = +something?
# Let's assume the "outer face" is the face furthest from the sleeve center (in the negative Y direction if eyes are in positive Y).
# And the "inward side" means the plate exists for Y > -side_plate_outer_face_offset?
# Let's assume the plate starts at Y = -side_plate_outer_face_offset and goes towards the eyes.
# So Plate Y range: [-side_plate_outer_face_offset, +max_eye_y].
# The plate thickness is side_plate_thickness.
# "Inward side of side_plate_outer_face_offset" -> Maybe the plate is on the "inner" side of the offset line?
# Let's try: The plate is a slab of thickness T.
# One face is at Y = -side_plate_outer_face_offset.
# The other face is at Y = -side_plate_outer_face_offset + side_plate_thickness.
# The eyes are "on the plate".
# The eyes are "rounded eye profiles".
# "Smaller annular secondary boss is aligned with the innermost eye".
# Innermost eye is the one closest to the sleeve? 
# "Centers progress outward from the sleeve".
# If sleeve is at X=R (on the cylinder surface), and eyes are at increasing Y, then the "innermost" is the one with smallest Y (closest to X-axis? No, closest to the sleeve face?).
# Actually, if the plate is attached to the side of the sleeve, the "innermost" eye would be the one closest to the cylinder center (X=0).
# But the plate is at X=R.
# Let's assume the "innermost" eye is the one with the smallest Y coordinate (closest to the origin if the plate extends from negative Y).
# So Eye 1 is at Y = -side_plate_outer_face_offset + margin?
# No, "first_eye_center_offset = 27.94". This is likely the distance from the sleeve centerline (or some reference) to the first eye.
# Let's assume the first eye center is at Y = -side_plate_outer_face_offset + side_plate_thickness/2 + something?
# Or simply Y = -side_plate_outer_face_offset + (side_plate_thickness / 2) + ...?
# Let's assume the "innermost" eye is the one closest to the cylinder axis.
# The plate starts at Y = -side_plate_outer_face_offset.
# The thickness is side_plate_thickness.
# The inner face is at Y = -side_plate_outer_face_offset + side_plate_thickness.
# The outer face is at Y = -side_plate_outer_face_offset.
# Wait, "plate occupies the inward side of side_plate_outer_face_offset".
# This implies the plate is at Y > -side_plate_outer_face_offset.
# So Outer Face is at Y = -side_plate_outer_face_offset.
# Inner Face is at Y = -side_plate_outer_face_offset + side_plate_thickness.
# The "innermost" eye is the one closest to the cylinder (X=0). Since the plate is at X=R, the eye closest to the cylinder is the one with the smallest Y magnitude? 
# Or maybe the eyes are arranged along the Y axis, and the "innermost" is the one closest to the sleeve attachment point.
# Let's assume the eyes are arranged along the Y axis starting from the outer face moving inwards?
# Or starting from the sleeve moving outwards?
# "Centers progress outward from the sleeve".
# If the plate is attached to the side, the "sleeve" is at X=R.
# The "outward" direction along the plate is Y.
# So Eye 1 is closest to the sleeve? No, "progress outward".
# Maybe the "sleeve" is the reference point (X=0, Y=0).
# Eye 1 is at Y = first_eye_center_offset.
# Eye 2 is at Y = first + spacing.
# Eye 3 is at Y = first + 2*spacing.
# These are all positive Y.
# The plate extends from Y = -side_plate_outer_face_offset to Y = max(eye_y) + margin?
# "The plate occupies the inward side of side_plate_outer_face_offset".
# This implies the plate is at Y > -side_plate_outer_face_offset.
# So the plate starts at Y = -side_plate_outer_face_offset.
# The eyes are at positive Y.
# The "innermost" eye is the one closest to the sleeve? 
# If the plate is at Y > -11.43, and eyes are at +27.94, +37.34, +46.74.
# The closest eye to the "sleeve" (which is at X=R, Y=0) is Eye 1 (Y=27.94)?
# Wait, if the plate is attached to the side, the "innermost" might be the one closest to the cylinder center (X=0).
# But all eyes are at the same X (on the plate).
# Maybe "innermost" means the one with the smallest Y coordinate?
# Let's assume Eye 1 is the "innermost" (closest to the origin in Y).
# "Smaller annular secondary boss is aligned with the innermost eye".
# Boss Inner Dia = 8.0 (same as side eye).
# Boss Outer Dia = 15.56.
# Boss extends "beyond the inboard plate face" and "beyond the outboard plate face".
# Inboard plate face: The face closer to the cylinder? Or the face at Y = -11.43?
# If the plate is Y > -11.43, then Y = -11.43 is the "outer" face (furthest from eyes)?
# And Y = -11.43 + 4.57 is the "inner" face (closer to eyes)?
# Let's assume:
# Plate Outer Face (away from eyes) = Y = -side_plate_outer_face_offset = -11.43.
# Plate Inner Face (towards eyes) = Y = -11.43 + 4.57 = -6.86.
# Boss extends beyond Inboard (Inner) face: +22.1 mm.
# Boss extends beyond Outboard (Outer) face: +3.81 mm.
# Total Boss Length = 22.1 + 3.81 + 4.57 = 30.48. Matches secondary_boss_length.
# So Boss is centered on the Inner Face?
# Boss extends 22.1 beyond the inner face (towards eyes).
# Boss extends 3.81 beyond the outer face (away from eyes).
# So Boss spans from Y = -11.43 - 3.81 = -15.24 to Y = -6.86 + 22.1 = 15.24.
# Center of Boss = (-15.24 + 15.24) / 2 = 0? No.
# Span = 30.48. Half = 15.24.
# If it extends 3.81 beyond outer (-11.43), then bottom is -11.43 - 3.81 = -15.24.
# If it extends 22.1 beyond inner (-6.86), then top is -6.86 + 22.1 = 15.24.
# Yes, Boss is centered at Y = (-15.24 + 15.24) / 2 = 0.
# So Boss is centered at Y=0.
# Boss Inner Dia = 8.0. Boss Outer Dia = 15.56.
# "Aligned with the innermost eye
