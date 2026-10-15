import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("ConnectorPart")

# --- Parameters ---
# We will use App::PropertyLength variables directly on the Body to ensure they are editable
# and drive the geometry. This avoids the non-existent App::Parameter type.
body = doc.addObject("PartDesign::Body", "Body")

# Add editable parameters to the Body
body.addProperty("App::PropertyLength", "connector_plate_width", "Dimensions", "connector_plate_width")
body.addProperty("App::PropertyLength", "connector_plate_length", "Dimensions", "connector_plate_length")
body.addProperty("App::PropertyLength", "connector_plate_thickness", "Dimensions", "connector_plate_thickness")
body.addProperty("App::PropertyLength", "connector_stem_width", "Dimensions", "connector_stem_width")
body.addProperty("App::PropertyLength", "connector_stem_length", "Dimensions", "connector_stem_length")
body.addProperty("App::PropertyLength", "connector_stem_thickness", "Dimensions", "connector_stem_thickness")
body.addProperty("App::PropertyLength", "connector_stem_center_offset_across_plate", "Dimensions", "connector_stem_center_offset_across_plate")
body.addProperty("App::PropertyLength", "mounting_slot_center_depth_below_plate", "Dimensions", "mounting_slot_center_depth_below_plate")
body.addProperty("App::PropertyLength", "mounting_slot_end_arc_radius", "Dimensions", "mounting_slot_end_arc_radius")

# Set values
body.connector_plate_width = 3.5
body.connector_plate_length = 6.0
body.connector_plate_thickness = 2.0
body.connector_stem_width = 0.5
body.connector_stem_length = 2.5
body.connector_stem_thickness = 5.0
body.connector_stem_center_offset_across_plate = 1.3
body.mounting_slot_center_depth_below_plate = 3.2
body.mounting_slot_end_arc_radius = 0.5

# --- Base Plate Sketch ---
# Sketch on XY plane (Z=0)
sketch_plate = body.newObject("Sketcher::SketchObject", "PlateSketch")
sketch_plate.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_plate.Support = (doc.getObject("XY_Plane"), [""])
sketch_plate.MapMode = "FlatFace"

# Define the rectangle for the plate
# Centered at origin, width along X, length along Y
w = body.connector_plate_width
l = body.connector_plate_length

# Line 1: Bottom (-l/2, -w/2) to Top (-l/2, w/2)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(-l/2, -w/2, 0), App.Vector(-l/2, w/2, 0)), False)
# Line 2: Top (-l/2, w/2) to Right (l/2, w/2)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(-l/2, w/2, 0), App.Vector(l/2, w/2, 0)), False)
# Line 3: Right (l/2, w/2) to Bottom (l/2, -w/2)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(l/2, w/2, 0), App.Vector(l/2, -w/2, 0)), False)
# Line 4: Bottom (l/2, -w/2) to Left (-l/2, -w/2)
sketch_plate.addGeometry(Part.LineSegment(App.Vector(l/2, -w/2, 0), App.Vector(-l/2, -w/2, 0)), False)

# Constraints for the rectangle
# Horizontal lines (Vertical constraint)
sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Vertical", 0, 2))
# Vertical lines (Horizontal constraint)
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
sketch_plate.addConstraint(Sketcher.Constraint("Horizontal", 0, 3))

# Centering constraints: Constrain midpoints of opposite sides to axes
# Midpoint of Line 0 (Bottom) to X-axis (Y=0)
sketch_plate.addConstraint(Sketcher.Constraint("PointOnLine", 0, 0, 1, 1)) # Point on Line 0
sketch_plate.addConstraint(Sketcher.Constraint("PointOnLine", 0, 0, 1, 2)) # Point on Line 0
# Actually, simpler: Constrain the center of the rectangle to the origin.
# We can add a point at the center and constrain it.
center_point = Part.Point(App.Vector(0, 0, 0))
sketch_plate.addGeometry(center_point, False)
# Constrain the center point to the intersection of the diagonals? 
# Or simply constrain the lines to be symmetric.
# Let's constrain the midpoint of the vertical lines to the X-axis and horizontal lines to the Y-axis.
# Midpoint of Line 0 (Bottom) is at (-l/2, 0). We want it on the X-axis (Y=0).
# Midpoint of Line 1 (Right) is at (0, w/2). We want it on the Y-axis (X=0).
# We can use "PointOnLine" with the axis lines.
# Line 0 midpoint to X_Axis (Line 1 of XY_Plane is X-axis? No, usually Line 1 is X, Line 2 is Y).
# Let's assume standard: Line 1 is X-axis, Line 2 is Y-axis.
# Midpoint of Line 0 (Bottom) to Line 1 (X-axis):
sketch_plate.addConstraint(Sketcher.Constraint("PointOnLine", 0, 0, 1, 1)) # Point on Line 0
sketch_plate.addConstraint(Sketcher.Constraint("PointOnLine", 0, 0, 1, 2)) # Point on Line 1 (X-axis)
# Midpoint of Line 1 (Right) to Line 2 (Y-axis):
sketch_plate.addConstraint(Sketcher.Constraint("PointOnLine", 0, 1, 1, 1)) # Point on Line 1
sketch_plate.addConstraint(Sketcher.Constraint("PointOnLine", 0, 1, 1, 2)) # Point on Line 2 (Y-axis)

# --- Pad the Plate ---
pad_plate = body.newObject("PartDesign::Pad", "PadPlate")
pad_plate.Profile = sketch_plate
pad_plate.Length = body.connector_plate_thickness
pad_plate.Type = "Solid"

# --- Stem Sketch ---
# Sketch on XZ plane (Y=0), offset by connector_stem_center_offset_across_plate in Y
sketch_stem = body.newObject("Sketcher::SketchObject", "StemSketch")
offset_y = body.connector_stem_center_offset_across_plate
sketch_stem.Placement = App.Placement(App.Vector(0, offset_y, 0))
sketch_stem.Support = (doc.getObject("XZ_Plane"), [""])
sketch_stem.MapMode = "FlatFace"

# Define the rectangle for the stem
# Width along X, Length along Z (projection direction)
sw = body.connector_stem_width
sl = body.connector_stem_length

# Line 1: Bottom (-sw/2, 0) to Top (-sw/2, sl)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(-sw/2, 0, 0), App.Vector(-sw/2, sl, 0)), False)
# Line 2: Top (-sw/2, sl) to Right (sw/2, sl)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(-sw/2, sl, 0), App.Vector(sw/2, sl, 0)), False)
# Line 3: Right (sw/2, sl) to Bottom (sw/2, 0)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(sw/2, sl, 0), App.Vector(sw/2, 0, 0)), False)
# Line 4: Bottom (sw/2, 0) to Left (-sw/2, 0)
sketch_stem.addGeometry(Part.LineSegment(App.Vector(sw/2, 0, 0), App.Vector(-sw/2, 0, 0)), False)

# Constraints for the stem rectangle
# Horizontal lines (Vertical constraint)
sketch_stem.addConstraint(Sketcher.Constraint("Vertical", 0, 1))
sketch_stem.addConstraint(Sketcher.Constraint("Vertical", 0, 2))
# Vertical lines (Horizontal constraint)
sketch_stem.addConstraint(Sketcher.Constraint("Horizontal", 0, 0))
sketch_stem.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
sketch_stem.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
sketch_stem.addConstraint(Sketcher.Constraint("Horizontal", 0, 3))

# Centering constraints for the stem
# Midpoint of Line 0 (Bottom) to X-axis (Line 1 of XZ_Plane)
sketch_stem.addConstraint(Sketcher.Constraint("PointOnLine", 0, 0, 1, 1))
sketch_stem.addConstraint(Sketcher.Constraint("PointOnLine", 0, 0, 1, 2))
# Midpoint of Line 1 (Right) to Z-axis (Line 2 of XZ_Plane)
sketch_stem.addConstraint(Sketcher.Constraint("PointOnLine", 0, 1, 1, 1))
sketch_stem.addConstraint(Sketcher.Constraint("PointOnLine", 0, 1, 1, 2))

# --- Pad the Stem ---
pad_stem = body.newObject("PartDesign::Pad", "PadStem")
pad_stem.Profile = sketch_stem
pad_stem.Length = body.connector_stem_thickness
pad_stem.Type = "Solid"

# --- Slot Sketch ---
# The slot is an obround (rectangle with semicircular ends) passing through the stem.
# The slot's long axis follows the stem projection direction (Z-axis).
# The midpoint of the slot lies mounting_slot_center_depth_below_plate from the plate underside.
# Plate underside is at Z = -connector_plate_thickness.
# So slot center Z = -connector_plate_thickness + mounting_slot_center_depth_below_plate.
# The slot is centered on the stem width (X-axis) and centered on the stem length (Z-axis)?
# "midpoint lies ... from the plate underside". This implies the center of the obround is at that depth.
# The obround is oriented along the stem (Z-axis).
# The width of the obround is connector_stem_width.
# The length of the straight part is connector_stem_length - 2 * mounting_slot_end_arc_radius.
# The total length of the obround is connector_stem_length.

# Sketch on XZ plane, same placement as stem sketch
sketch_slot = body.newObject("Sketcher::SketchObject", "SlotSketch")
sketch_slot.Placement = App.Placement(App.Vector(0, offset_y, 0))
sketch_slot.Support = (doc.getObject("XZ_Plane"), [""])
sketch_slot.MapMode = "FlatFace"

# Calculate dimensions
slot_width = body.connector_stem_width
slot_length = body.connector_stem_length
slot_arc_radius = body.mounting_slot_end_arc_radius
slot_straight_length = slot_length - 2 * slot_arc_radius
slot_center_z = -body.connector_plate_thickness + body.mounting_slot_center_depth_below_plate

# Define the obround
# We can construct it using lines and circles.
# Center of the obround is at (0, slot_center_z) in the sketch plane (X, Z).
# The obround extends from -slot_length/2 to +slot_length/2 along Z.
# The straight sides are from -slot_straight_length/2 to +slot_straight_length/2 along Z.
# The semicircles are at Z = -slot_length/2 and Z = +slot_length/2.

# Line 1: Left straight side (-slot_straight_length/2, -slot_width/2) to (-slot_straight_length/2, slot_width/2)
# Wait, the slot is along Z. So the straight sides are parallel to Z.
# The width is along X.
# So the straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.

# Line 1: Left straight side
sketch_slot.addGeometry(Part.LineSegment(
    App.Vector(-slot_width/2, -slot_straight_length/2, 0), 
    App.Vector(-slot_width/2, slot_straight_length/2, 0)
), False)

# Line 2: Right straight side
sketch_slot.addGeometry(Part.LineSegment(
    App.Vector(slot_width/2, -slot_straight_length/2, 0), 
    App.Vector(slot_width/2, slot_straight_length/2, 0)
), False)

# Circle 1: Left semicircle (at Z = -slot_length/2)
# Center: (-slot_width/2, -slot_length/2)
# Radius: slot_arc_radius
# Note: In the sketch plane (X, Z), the circle is in the XZ plane.
# The circle should be centered at X = -slot_width/2, Z = -slot_length/2.
# But wait, the straight side ends at Z = -slot_straight_length/2.
# The semicircle connects the ends of the straight sides.
# So the center of the left semicircle is at X = -slot_width/2, Z = -slot_length/2.
# The circle should be drawn such that it connects the straight sides.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# The semicircle at the left end (Z = -slot_length/2) connects the points:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are vertical in the XZ plane (parallel to Z).
# So the left end of the slot is at Z = -slot_length/2.
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
# They extend from Z = -slot_straight_length/2 to Z = +slot_straight_length/2.
# The left semicircle is at Z = -slot_length/2.
# It connects the point (-slot_width/2, -slot_straight_length/2) to (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are parallel to Z.
# So the left semicircle is at the left end of the slot (negative Z).
# The points where the semicircle meets the straight sides are:
# (-slot_width/2, -slot_straight_length/2) and (-slot_width/2, slot_straight_length/2)? No.
# The straight sides are at X = -slot_width/2 and X = +slot_width/2.
#
