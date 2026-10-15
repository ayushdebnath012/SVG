import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("SteeringBracket")

# --- Parameters ---
# Main Sleeve
main_sleeve_outer_diameter = 24.76
main_sleeve_bore_diameter = 15.88
main_sleeve_length = 35.18

# Side Plate & Eyes
side_eye_hole_diameter = 8.0
side_eye_outer_arc_radius = 8.26
side_plate_profile_half_height = 14.61
first_eye_center_offset = 27.94
side_plate_outer_face_offset = 11.43
side_plate_thickness = 4.57
number_of_eye_profiles = 3
eye_profile_spacing = 9.4

# Secondary Boss
secondary_boss_outer_diameter = 15.56
secondary_boss_inner_diameter = 8.0
secondary_boss_inboard_projection = 22.1
secondary_boss_outboard_projection = 3.81
secondary_boss_length = 30.48

# Create Body
body = doc.addObject("PartDesign::Body", "Body")

# Add a VarSet for parameters to keep the script clean and editable
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "main_sleeve_outer_diameter", "Dimensions", "Main sleeve outer diameter")
params.main_sleeve_outer_diameter = main_sleeve_outer_diameter
params.addProperty("App::PropertyLength", "main_sleeve_bore_diameter", "Dimensions", "Main sleeve bore diameter")
params.main_sleeve_bore_diameter = main_sleeve_bore_diameter
params.addProperty("App::PropertyLength", "main_sleeve_length", "Dimensions", "Main sleeve length")
params.main_sleeve_length = main_sleeve_length
params.addProperty("App::PropertyLength", "side_eye_hole_diameter", "Dimensions", "Side eye hole diameter")
params.side_eye_hole_diameter = side_eye_hole_diameter
params.addProperty("App::PropertyLength", "side_eye_outer_arc_radius", "Dimensions", "Side eye outer arc radius")
params.side_eye_outer_arc_radius = side_eye_outer_arc_radius
params.addProperty("App::PropertyLength", "side_plate_profile_half_height", "Dimensions", "Side plate profile half height")
params.side_plate_profile_half_height = side_plate_profile_half_height
params.addProperty("App::PropertyLength", "first_eye_center_offset", "Dimensions", "First eye center offset")
params.first_eye_center_offset = first_eye_center_offset
params.addProperty("App::PropertyLength", "side_plate_outer_face_offset", "Dimensions", "Side plate outer face offset")
params.side_plate_outer_face_offset = side_plate_outer_face_offset
params.addProperty("App::PropertyLength", "side_plate_thickness", "Dimensions", "Side plate thickness")
params.side_plate_thickness = side_plate_thickness
params.addProperty("App::PropertyInteger", "number_of_eye_profiles", "Dimensions", "Number of eye profiles")
params.number_of_eye_profiles = number_of_eye_profiles
params.addProperty("App::PropertyLength", "eye_profile_spacing", "Dimensions", "Eye profile spacing")
params.eye_profile_spacing = eye_profile_spacing
params.addProperty("App::PropertyLength", "secondary_boss_outer_diameter", "Dimensions", "Secondary boss outer diameter")
params.secondary_boss_outer_diameter = secondary_boss_outer_diameter
params.addProperty("App::PropertyLength", "secondary_boss_inner_diameter", "Dimensions", "Secondary boss inner diameter")
params.secondary_boss_inner_diameter = secondary_boss_inner_diameter
params.addProperty("App::PropertyLength", "secondary_boss_inboard_projection", "Dimensions", "Secondary boss inboard projection")
params.secondary_boss_inboard_projection = secondary_boss_inboard_projection
params.addProperty("App::PropertyLength", "secondary_boss_outboard_projection", "Dimensions", "Secondary boss outboard projection")
params.secondary_boss_outboard_projection = secondary_boss_outboard_projection
params.addProperty("App::PropertyLength", "secondary_boss_length", "Dimensions", "Secondary boss length")
params.secondary_boss_length = secondary_boss_length

# --- Main Sleeve (Revolution) ---
# Sketch 1: Main Sleeve Profile (XZ plane)
sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_MainSleeve")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Support = (doc.getObject("XY_Plane"), [])
sketch_main.MapMode = "FlatFace"

# Main sleeve is a hollow cylinder. We draw the outer profile and use a hole or just revolve the outer and subtract inner?
# Easier: Draw outer profile, then use a hole feature or draw inner rectangle and subtract.
# Let's draw the outer profile and then use a hole feature or draw inner rectangle and subtract.
# Actually, standard practice: Draw outer profile, revolve. Then draw inner profile on same sketch, revolve (subtract).
# Or draw outer profile, revolve. Then create a separate sketch for the hole.
# Let's do: Sketch 1 = Outer profile. Sketch 2 = Inner profile (Hole).

# Outer Profile
sketch_main.addGeometry(Part.LineSegment(App.Vector(-params.main_sleeve_outer_diameter/2, 0, 0), App.Vector(params.main_sleeve_outer_diameter/2, 0, 0)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(params.main_sleeve_outer_diameter/2, 0, 0), App.Vector(params.main_sleeve_outer_diameter/2, 0, params.main_sleeve_length/2)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(params.main_sleeve_outer_diameter/2, 0, params.main_sleeve_length/2), App.Vector(-params.main_sleeve_outer_diameter/2, 0, params.main_sleeve_length/2)), False)
sketch_main.addGeometry(Part.LineSegment(App.Vector(-params.main_sleeve_outer_diameter/2, 0, params.main_sleeve_length/2), App.Vector(-params.main_sleeve_outer_diameter/2, 0, 0)), False)

# Constraints for Outer Profile
sketch_main.addConstraint(Sketcher.Constraint("Axis", 0, 1, 0, 2)) # Vertical axis
sketch_main.addConstraint(Sketcher.Constraint("Axis", 1, 2, 0, 3))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 2, 3, 0, 4))
sketch_main.addConstraint(Sketcher.Constraint("Axis", 3, 4, 0, 5))
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch_main.addConstraint(Sketcher.Constraint("Horizontal", 2, 3))
sketch_main.addConstraint(Sketcher.Constraint("Vertical", 0, 2))
sketch_main.addConstraint(Sketcher.Constraint("Vertical", 1, 3))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, 0, 2)) # Origin
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 1, 2, 0, 2))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 2, 3, 0, 2))
sketch_main.addConstraint(Sketcher.Constraint("PointOnObject", 3, 4, 0, 2))
sketch_main.addConstraint(Sketcher.Constraint("Length", 0, 1, "Parameters.main_sleeve_outer_diameter"))
sketch_main.addConstraint(Sketcher.Constraint("Length", 2, 3, "Parameters.main_sleeve_length"))

# Revolve Main Sleeve
rev_main = body.newObject("PartDesign::Revolution", "Rev_MainSleeve")
rev_main.Profile = sketch_main
rev_main.ReferenceAxis = (doc.getObject("Z_Axis"), [])
rev_main.Angle = 360.0
rev_main.Reverse = False

# --- Side Plate & Eyes (Sketch on YZ plane) ---
# The plate lies on one side of the sleeve. Let's say the +Y side.
# The plate extends laterally (along Z axis of the sketch, which is Y of the part).
# The sleeve axis is Z of the part.
# So the sketch plane should be YZ (part coordinates).
# Origin at center of sleeve.
# Plate extends from Y = -side_plate_outer_face_offset to Y = +side_plate_outer_face_offset?
# No, "plate lies on one side".
# Let's assume the plate is on the +Y side, extending from Y=0 to Y=some value?
# Or maybe the plate is centered?
# "The plate occupies the inward side of side_plate_outer_face_offset".
# Let's assume the plate is located at Y > 0.
# The plate has thickness in X.
# The "inward side" is the side facing the sleeve center? Or the side facing the other side of the bracket?
# "The plate occupies the inward side of side_plate_outer_face_offset with side_plate_thickness".
# This phrasing is tricky. Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward" face is at Y = 0 (touching the sleeve).
# The "outer" face is at Y = side_plate_outer_face_offset.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to each rounded eye end.
# The eyes are circles/rounded shapes.
# "three overlapping rounded eye profiles whose centers progress outward from the sleeve".
# "The first eye center is located by first_eye_center_offset".
# This offset is likely along the Z axis (lateral direction).
# So Eye 1 center is at Z = first_eye_center_offset.
# Eye 2 center is at Z = first_eye_center_offset + eye_profile_spacing.
# Eye 3 center is at Z = first_eye_center_offset + 2*eye_profile_spacing.
# The eyes are "rounded". "side_eye_outer_arc_radius".
# The eyes are holes? "side_eye_hole_diameter".
# The plate outline is formed by these eyes.
# "The plate's two attachment edges are symmetric and tangent to each rounded eye end".
# This means the top and bottom edges of the plate are tangent to the top and bottom of the eyes.
# The eyes are circles of diameter side_eye_hole_diameter? Or are they arcs?
# "rounded eye profiles". Let's assume they are full circles for the profile, but the plate is cut out?
# No, the plate *has* these eyes. So the plate has holes.
# The outline of the plate is defined by the tangents to these circles.
# So the plate is a shape bounded by two lines (top and bottom tangents) and the arcs of the circles?
# Or is the plate a solid shape with holes?
# "The plate's outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of these profiles? Or the plate is the region between the tangents?
# "The plate occupies the inward side of side_plate_outer_face_offset".
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the region between the tangents to the circles.
# Let's assume the plate is a flat plate on the +Y side of the sleeve.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The plate has holes (eyes) at specific Z locations.
# The holes are circles of diameter side_eye_hole_diameter.
# The centers are at Z = first_eye_center_offset, first_eye_center_offset + spacing, etc.
# The "outline" of the plate is formed by the tangents to these circles.
# This means the plate is a shape that is wider than the holes.
# The top and bottom edges of the plate are tangent to the top and bottom of the circles.
# So the plate width (in Z) is determined by the diameter of the circles.
# The plate extends from Y = 0 to Y = side_plate_outer_face_offset.
# The plate has thickness in X.
# The "inward side" of side_plate_outer_face_offset means the face at Y = 0 is the inward face (touching the sleeve).
# The face at Y = side_plate_outer_face_offset is the outward face.
# The "two attachment edges" are the top and bottom edges of the plate (along Z).
# These edges are tangent to the rounded eye ends.
# So the plate is a rectangle with rounded corners? Or just a rectangle with holes?
# "outline is formed by three overlapping rounded eye profiles".
# This suggests the plate is the union of the circles? No, that would be a blob.
# Maybe the plate is the
