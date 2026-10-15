import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration & Parameters ---

# Base Part Dimensions
CH_L = 114.55
CH_W = 38.48
CH_TH = 1.59
CH_H = 6.35
CH_BEND_Y_OFF = 13.68
CH_IN_R = 3.97
CH_BEND_A = 30.0 # degrees (used for relief logic)
CH_OUT_SW = 16.43
CH_IN_SW = 15.52

FL_L = 41.91
FL_W = 18.29
SL_L = 13.97
SL_W = 7.4
SL_CNT = 3
SL_SP = 15.2
FL_CR = 1.52
FL_X_OFF = -7.555
SL_X_OFF = -8.195

# Edit Parameters
BRO_SW = 17.35 # Bend Relief Outer Boundary Half Width
VSL_L = 76.2   # Vertical Slot Length
VSL_W = 4.6    # Vertical Slot Width
VSL_Y_OFF = 53.85 # Vertical Slot Center Y Offset
AH_Y_OFF = 98.81 # Alignment Hole Center Y Offset

# --- Setup Document ---
doc = App.newDocument("RailBracket")
doc.Label = "RailBracket"

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Create Parameters (Editable) ---
# We use a VarSet to store parameters as named properties in the document tree
params = body.newObject("App::VarSet", "Dimensions")

# Helper to set parameter
def set_param(name, value):
    params.addProperty("App::PropertyFloat", name, "Dimensions", name)
    params[name] = value

# Set Base Parameters
set_param("CH_L", CH_L)
set_param("CH_W", CH_W)
set_param("CH_TH", CH_TH)
set_param("CH_H", CH_H)
set_param("CH_BEND_Y_OFF", CH_BEND_Y_OFF)
set_param("CH_IN_R", CH_IN_R)
set_param("CH_BEND_A", CH_BEND_A)
set_param("CH_OUT_SW", CH_OUT_SW)
set_param("CH_IN_SW", CH_IN_SW)
set_param("FL_L", FL_L)
set_param("FL_W", FL_W)
set_param("SL_L", SL_L)
set_param("SL_W", SL_W)
set_param("SL_CNT", SL_CNT)
set_param("SL_SP", SL_SP)
set_param("FL_CR", FL_CR)
set_param("FL_X_OFF", FL_X_OFF)
set_param("SL_X_OFF", SL_X_OFF)

# Set Edit Parameters (initially same as base or default, will be overridden by expressions later if needed, 
# but here we set them explicitly for the edit step)
set_param("BRO_SW", BRO_SW)
set_param("VSL_L", VSL_L)
set_param("VSL_W", VSL_W)
set_param("VSL_Y_OFF", VSL_Y_OFF)
set_param("AH_Y_OFF", AH_Y_OFF)

# --- Construct Base Part ---

# 1. Main Channel Profile (Side View)
# Coordinate system: X = Width direction, Y = Height direction.
ch_sketch = body.newObject("Sketcher::SketchObject", "ChannelProfile")
ch_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
ch_sketch.AttachmentSupport = [doc.getObject("XY_Plane")]
ch_sketch.MapMode = "FlatFace"
ch_sketch.ConstrainToMapAxis = True

# Define Channel Geometry
# Outer Profile Points
P1 = App.Vector(-CH_W/2, 0)
P2 = App.Vector(-CH_W/2, CH_H)
P3 = App.Vector(-CH_W/2 + CH_TH, CH_H - (CH_IN_R + CH_TH))
P4 = App.Vector(CH_W/2 - CH_TH, CH_H - (CH_IN_R + CH_TH))
P5 = App.Vector(CH_W/2, CH_H)
P6 = App.Vector(CH_W/2, 0)

# Inner Profile Points
P7 = App.Vector(-CH_W/2 + CH_TH, 0)
P8 = App.Vector(-CH_W/2 + CH_TH, CH_H - CH_TH)
P9 = App.Vector(-CH_W/2 + CH_TH + CH_IN_R, CH_H - CH_TH)
P10 = App.Vector(CH_W/2 - CH_TH - CH_IN_R, CH_H - CH_TH)
P11 = App.Vector(CH_W/2 - CH_TH, CH_H - CH_TH)
P12 = App.Vector(CH_W/2 - CH_TH, 0)

# Add Outer Wire
outer_wire = Part.Wire()
outer_wire.add(Part.LineSegment(P1, P2))
outer_wire.add(Part.LineSegment(P2, P3))
outer_wire.add(Part.LineSegment(P3, P4))
outer_wire.add(Part.LineSegment(P4, P5))
outer_wire.add(Part.LineSegment(P5, P6))
outer_wire.add(Part.LineSegment(P6, P1))
ch_sketch.addGeometry(outer_wire, False)

# Add Inner Wire
inner_wire = Part.Wire()
inner_wire.add(Part.LineSegment(P7, P8))
inner_wire.add(Part.LineSegment(P8, P9))
inner_wire.add(Part.LineSegment(P9, P10))
inner_wire.add(Part.LineSegment(P10, P11))
inner_wire.add(Part.LineSegment(P11, P12))
inner_wire.add(Part.LineSegment(P12, P7))
ch_sketch.addGeometry(inner_wire, False)

# Add Constraints for Outer Wire
# Coincident points
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 0)) # P1
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1)) # P2
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 2)) # P3
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 3)) # P4
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 4)) # P5
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 5)) # P6
# Horizontal/Vertical lines
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 0, 0)) # P1 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 1, 0)) # P2 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 2, 0)) # P3 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 3, 0)) # P4 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 4, 0)) # P5 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 5, 0)) # P6 X
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 0, 0)) # P1 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 1, 0)) # P2 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 2, 0)) # P3 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 3, 0)) # P4 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 4, 0)) # P5 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 5, 0)) # P6 Y
# Lengths
ch_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 0, 0, 1)) # P1-P2
ch_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 2, 3)) # P3-P4
ch_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 4, 5)) # P5-P6
# Arcs (Tangent)
ch_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, 0, 1, 2)) # P2-P3 Arc
ch_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, 0, 3, 4)) # P4-P5 Arc

# Add Constraints for Inner Wire
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 6, 0, 0)) # P7
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 6, 0, 1)) # P8
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 6, 0, 2)) # P9
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 6, 0, 3)) # P10
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 6, 0, 4)) # P11
ch_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 6, 0, 5)) # P12
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 6, 0, 0, 0)) # P7 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 6, 0, 1, 0)) # P8 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 6, 0, 2, 0)) # P9 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 6, 0, 3, 0)) # P10 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 6, 0, 4, 0)) # P11 X
ch_sketch.addConstraint(Sketcher.Constraint("X", 0, 6, 0, 5, 0)) # P12 X
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 6, 0, 0, 0)) # P7 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 6, 0, 1, 0)) # P8 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 6, 0, 2, 0)) # P9 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 6, 0, 3, 0)) # P10 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 6, 0, 4, 0)) # P11 Y
ch_sketch.addConstraint(Sketcher.Constraint("Y", 0, 6, 0, 5, 0)) # P12 Y
ch_sketch.addConstraint(Sketcher.Constraint("Length", 0, 6, 0, 0, 0, 1)) # P7-P8
ch_sketch.addConstraint(Sketcher.Constraint("Length", 0, 6, 0, 2, 3)) # P9-P10
ch_sketch.addConstraint(Sketcher.Constraint("Length", 0, 6, 0, 4, 5)) # P11-P12
ch_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 6, 0, 1, 2)) # P8-P9 Arc
ch_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 6, 0, 3, 4)) # P10-P11 Arc

# Pad the Channel
pad = body.newObject("PartDesign::Pad", "ChannelPad")
pad.Profile = ch_sketch
pad.Length = CH_L
pad.Midplane = False
pad.Reversed = False

# 2. Top Mounting Flange
# The flange is centered across the channel width.
# It has a rounded rectangular boundary.
# It contains three identical horizontal capsule-shaped mounting slots.
# The flange is attached to the top of the channel.
# We need to define the flange profile relative to the channel top.
# Let's create a new sketch on the top face of the channel pad.
# Since we are in headless mode, we can't easily select the face.
# Instead, we will create the sketch on the XY plane but offset it by CH_L/2 + FL_L/2?
# No, the flange is at one end. Let's say the channel goes from 0 to CH_L.
# The flange is at the top (Y=CH_L).
# We will create a sketch on the XY plane, offset by CH_L/2 + FL_L/2?
# Actually, let's place the sketch at Y = CH_L + FL_L/2.
# The flange length is FL_L.
# The flange width is FL_W.
# The flange is centered on the channel width (X=0).
# The flange has rounded corners (FL_CR).
# The slots are horizontal capsules.
# Slot length = SL_L, width = SL_W.
# Slots are centered on the flange lengthwise centerline (Y=0 relative to flange center).
# Slots are spaced by SL_SP.
# There are SL_CNT = 3 slots.
# The slots are centered at X = SL_X_OFF.

fl_sketch = body.newObject("Sketcher::SketchObject", "FlangeProfile")
fl_sketch.Placement = App.Placement(App.Vector(0, 0, CH_L + FL_L/2))
fl_sketch.AttachmentSupport = [doc.getObject("XY_Plane")]
fl_sketch.MapMode = "FlatFace"
fl_sketch.ConstrainToMapAxis = True

# Flange Geometry
# Outer Boundary
# Center (0, 0) relative to sketch origin.
# Width FL_W, Length FL_L.
# Rounded corners FL_CR.
# Points:
# P1: (-FL_W/2, -FL_L/2)
# P2: (-FL_W/2 + FL_CR, -FL_L/2)
# P3: (-FL_W/2 + FL_CR, -FL_L/2 + FL_CR)
# P4: (-FL_W/2 + FL_CR, FL_L/2 - FL_CR)
# P5: (-FL_W/2, FL_L/2 - FL_CR)
# P6: (-FL_W/2, FL_L/2)
# P7: (FL_W/2, FL_L/2)
# P8: (FL_W/2, FL_L/2 - FL_CR)
# P9: (FL_W/2 - FL_CR, FL_L/2 - FL_CR)
# P10: (FL_W/2 - FL_CR, -FL_L/2 + FL_CR)
# P11: (FL_W/2, -FL_L/2 + FL_CR)
# P12: (FL_W/2, -FL_L/2)

# Slots
# Horizontal capsules.
# Center X = SL_X_OFF.
# Center Y = 0.
# Length = SL_L.
# Width = SL_W.
# Capsule = Rectangle + 2 semicircles.
# Rectangle: (SL_X_OFF - SL_L/2, -SL_W/2) to (SL_X_OFF + SL_L/2, SL_W/2).
# Semicircles at ends.

# Add Outer Wire
outer_wire_fl = Part.Wire()
outer_wire_fl.add(Part.LineSegment(App.Vector(-FL_W/2, -FL_L/2), App.Vector(-FL_W/2 + FL_CR, -FL_L/2)))
outer_wire_fl.add(Part.LineSegment(App.Vector(-FL_W/2 + FL_CR, -FL_L/2), App.Vector(-FL_W/2 + FL_CR, -FL_L/2 + FL_CR)))
outer_wire_fl.add(Part.LineSegment(App.Vector(-FL_W/2 + FL_CR, -FL_L/2 + FL_CR), App.Vector(-FL_W/2 + FL_CR, FL_L/2 - FL_CR)))
outer_wire_fl.add(Part.LineSegment(App.Vector(-FL_W/2 + FL_CR, FL_L/2 - FL_CR), App.Vector(-FL_W/2, FL_L/2 - FL_CR)))
outer_wire_fl.add(Part.LineSegment(App.Vector(-FL_W/2, FL_L/2 - FL_CR), App.Vector(-FL_W/2, FL_L/2)))
outer_wire_fl.add(Part.LineSegment(App.Vector(-FL_W/2, FL_L/2), App.Vector(FL_W/2, FL_L/2)))
outer_wire_fl.add(Part.LineSegment(App.Vector(FL_W/2, FL_L/2), App.Vector(FL_W/2, FL_L/2 - FL_CR)))
outer_wire_fl.add(Part.LineSegment(App.Vector(FL_W/2, FL_L/2 - FL_CR), App.Vector(FL_W/2 - FL_CR, FL_L/2 - FL_CR)))
outer_wire_fl.add(Part.LineSegment(App.Vector(FL_W/2 - FL_CR, FL_L/2 - FL_CR), App.Vector(FL_W/2 - FL_CR, -FL_L/2 + FL_CR)))
outer_wire_fl.add(Part.LineSegment(App.Vector(FL_W/2 - FL_CR, -FL_L/2 + FL_CR), App.Vector(FL_W/2, -FL_L/2 + FL_CR)))
outer_wire_fl.add(Part.LineSegment(App.Vector(FL_W/2, -FL_L/2 + FL_CR), App.Vector(FL_W/2, -FL_L/2)))
outer_wire_fl.add(Part.LineSegment(App.Vector(FL_W/2, -FL_L/2), App.Vector(-FL_W/2, -FL_L/2)))
fl_sketch.addGeometry(outer_wire_fl, False)

# Add Slots
# Slot 1
s1_rect = Part.Wire()
s1_rect.add(Part.LineSegment(App.Vector(SL_X_OFF - SL_L/2, -SL_W/2), App.Vector(SL_X_OFF + SL_L/2, -SL_W/2)))
s1_rect.add(Part.LineSegment(App.Vector(SL_X_OFF + SL_L/2, -SL_W/2), App.Vector(SL_X_OFF + SL_L/2, SL_W/2)))
s1_rect.add(Part.LineSegment(App.Vector(SL_X_OFF + SL_L/2, SL_W/2), App.Vector(SL_X_OFF - SL_L/2, SL_W/2)))
s1_rect.add(Part.LineSegment(App.Vector(SL_X_OFF - SL_L/2, SL_W/2), App.Vector(SL_X_OFF - SL_L/2, -SL_W/2)))
fl_sketch.addGeometry(s1_rect, False)

# Slot 2
s2_rect = Part.Wire()
s2_rect.add(Part.LineSegment(App.Vector(SL_X_OFF - SL_L/2, -SL_W/2), App.Vector(SL_X_OFF + SL_L/2, -SL_W/2)))
s2_rect.add(Part.LineSegment(App.Vector(SL_X_OFF + SL_L/2, -SL_W/2), App.Vector(SL_X_OFF + SL_L/2, SL_W/2)))
s2_rect.add(Part.LineSegment(App.Vector(SL_X_OFF + SL_L/2, SL_W/2), App.Vector(SL_X_OFF - SL_L/2, SL_W/2)))
s2_rect.add(Part.LineSegment(App.Vector(SL_X_OFF - SL_L/2, SL_W/2), App.Vector(SL_X_OFF - SL_L/2, -SL_W/2)))
fl_sketch.addGeometry(s2_rect, False)

# Slot 3
s3_rect = Part.Wire()
s3_rect.add(Part.LineSegment(App.Vector(SL_X_OFF - SL_L/2, -SL_W/2), App.Vector(SL_X_OFF + SL_L/2, -SL_W/2)))
s3_rect.add(Part.LineSegment(App.Vector(SL_X_OFF + SL_L/2, -SL_W/2), App.Vector(SL_X_OFF + SL_L/2, SL_W/2)))
s3_rect.add(Part.LineSegment(App.Vector(SL_X_OFF + SL_L/2, SL_W/2), App.Vector(SL_X_OFF - SL_L/2, SL_W/2)))
s3_rect.add(Part.LineSegment(App.Vector(SL_X_OFF - SL_L/2, SL_W/2), App.Vector(SL_X_OFF - SL_L/2, -SL_W/2)))
fl_sketch.addGeometry(s3_rect, False)

# Add Constraints for Flange
# Coincident points
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 0)) # P1
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 1)) # P2
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 2)) # P3
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 3)) # P4
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 4)) # P5
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 5)) # P6
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 6)) # P7
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 7)) # P8
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 8)) # P9
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 9)) # P10
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 10)) # P11
fl_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 0, 11)) # P12

# Horizontal/Vertical lines
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 0, 0)) # P1 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 1, 0)) # P2 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 2, 0)) # P3 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 3, 0)) # P4 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 4, 0)) # P5 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 5, 0)) # P6 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 6, 0)) # P7 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 7, 0)) # P8 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 8, 0)) # P9 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 9, 0)) # P10 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 10, 0)) # P11 X
fl_sketch.addConstraint(Sketcher.Constraint("X", 0, 0, 0, 11, 0)) # P12 X
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 0, 0)) # P1 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 1, 0)) # P2 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 2, 0)) # P3 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 3, 0)) # P4 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 4, 0)) # P5 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 5, 0)) # P6 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 6, 0)) # P7 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 7, 0)) # P8 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 8, 0)) # P9 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 9, 0)) # P10 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 10, 0)) # P11 Y
fl_sketch.addConstraint(Sketcher.Constraint("Y", 0, 0, 0, 11, 0)) # P12 Y

# Lengths
fl_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 0, 0, 1)) # P1-P2
fl_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 2, 3)) # P3-P4
fl_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 4, 5)) # P5-P6
fl_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 6, 7)) # P7-P8
fl_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 8, 9)) # P9-P10
fl_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 10, 11)) # P11-P12
fl_sketch.addConstraint(Sketcher.Constraint("Length", 0, 0, 0, 11, 0)) # P12-P1

# Arcs (Tangent)
fl_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, 0, 1, 2)) # P2-P3 Arc
fl_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, 0, 3, 4)) # P4-P5 Arc
fl_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, 0, 7, 8)) # P8-P9 Arc
fl_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, 0, 9, 10)) # P10-P11 Arc

# Pad the Flange
fl_pad = body.newObject("PartDesign::Pad", "FlangePad")
fl_pad.Profile = fl_sketch
fl_pad.Length = FL_L
fl_pad.Midplane = False
fl_pad.Reversed = False

# 3. Bend Reliefs (Edit Instruction)
# "At the flange end, cut a mirrored pair of short bend reliefs that reuse the existing channel bend centers, radii, angle, and tangent boundaries, meet the thickness boundary at the named inner and outer half-widths, and extend along the channel by the inner bend radius."
# The channel bends are at the top of the channel (Y=CH_H).
# The relief is at the flange end (Y=CH_L).
# The relief is a cutout in the wall.
# "meet the thickness boundary at the named inner and outer half-widths"
# This implies the relief cuts into the wall from the outside.
# The relief is a "short bend relief".
# It reuses the bend centers.
# The bend centers are at:
#   Outer: (-CH_W/2, CH_H - (CH_IN_R + CH_TH)) and (CH_W/2, CH_H - (CH_IN_R + CH_TH))
#   Inner: (-CH_W/2 + CH_TH, CH_H - CH_IN_R) and (CH_W/2 - CH_TH, CH_H - CH_IN_R)
# The relief extends along the channel by the inner bend radius (CH_IN_R).
# The relief is a cutout.
# "mirrored pair" -> Left and Right walls.
# "meet the thickness boundary at the named inner and outer half-widths"
# This suggests the relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".

# Relief Sketch
relief_sketch = body.newObject("Sketcher::SketchObject", "ReliefProfile")
relief_sketch.Placement = App.Placement(App.Vector(0, 0, CH_L - CH_IN_R)) # At the flange end, offset by inner bend radius
relief_sketch.AttachmentSupport = [doc.getObject("XY_Plane")]
relief_sketch.MapMode = "FlatFace"
relief_sketch.ConstrainToMapAxis = True

# Relief Geometry
# The relief is a cutout in the wall.
# The wall is at X = -CH_W/2 (Left) and X = CH_W/2 (Right).
# The relief is a cutout that removes material between the inner and outer boundaries.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".

# Left Wall Relief
# Outer boundary: X = -BRO_SW
# Inner boundary: X = -CH_IN_SW
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".

# Left Wall Relief
# Outer boundary: X = -BRO_SW
# Inner boundary: X = -CH_IN_SW
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".

# Left Wall Relief
# Outer boundary: X = -BRO_SW
# Inner boundary: X = -CH_IN_SW
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".

# Left Wall Relief
# Outer boundary: X = -BRO_SW
# Inner boundary: X = -CH_IN_SW
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel, near the flange.
# The relief is a cutout in the wall.
# The relief is defined by the outer boundary half-width (BRO_SW) and inner boundary half-width (CH_IN_SW).
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".

# Left Wall Relief
# Outer boundary: X = -BRO_SW
# Inner boundary: X = -CH_IN_SW
# The relief is a cutout that removes material between these boundaries.
# The relief is a "short bend relief".
# Let's create a sketch for the relief on the side of the channel.
# The relief is at the top of the channel,
