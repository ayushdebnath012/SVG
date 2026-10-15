import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration & Parameters ---
# Base Parameters
c_outer_h = 44.6
c_inner_d = 25.0
c_wall_t = 3.0
c_length = 79.0
c_end_t = 3.0

# Edit Parameters (Target)
m_plate_t = 5.0
m_plate_proj = 30.0
m_hole_d = 4.0
m_hole_offset = 2.5
m_holes = 3

# --- Document Setup ---
doc = App.newDocument("ConveyorSupport")

# Create Named Objects for Parameters
# We will store values in a dedicated VarSet for easy access in expressions
params = doc.addObject("App::VarSet", "Dimensions")
params.addProperty("App::PropertyLength", "c_outer_h", "Dimensions", "Channel Outer Height")
params.addProperty("App::PropertyLength", "c_inner_d", "Dimensions", "Channel Inner Depth")
params.addProperty("App::PropertyLength", "c_wall_t", "Dimensions", "Channel Wall Thickness")
params.addProperty("App::PropertyLength", "c_length", "Dimensions", "Channel Length")
params.addProperty("App::PropertyLength", "c_end_t", "Dimensions", "End Plate Thickness")
params.addProperty("App::PropertyLength", "m_plate_t", "Dimensions", "Mounting Plate Thickness")
params.addProperty("App::PropertyLength", "m_plate_proj", "Dimensions", "Mounting Plate Projection")
params.addProperty("App::PropertyLength", "m_hole_d", "Dimensions", "Mounting Hole Diameter")
params.addProperty("App::PropertyLength", "m_hole_offset", "Dimensions", "Mounting Hole Offset")
params.addProperty("App::PropertyInteger", "m_holes", "Dimensions", "Number of Mounting Holes")

# Set initial values
params.c_outer_h = c_outer_h
params.c_inner_d = c_inner_d
params.c_wall_t = c_wall_t
params.c_length = c_length
params.c_end_t = c_end_t
params.m_plate_t = m_plate_t
params.m_plate_proj = m_plate_proj
params.m_hole_d = m_hole_d
params.m_hole_offset = m_hole_offset
params.m_holes = m_holes

# --- Geometry Construction ---

# Helper to get plane axes
def get_plane(obj, face_idx=0):
    return (obj, [face_idx])

# 1. Base Channel Sketch (Side View)
# Defines the C-profile cross-section
sketch_profile = doc.addObject("PartDesign::Body", "Body") # This is wrong, Body is parent
# Correct approach: Create Body first
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0,0,0))

# 1.1 Sketch: Side Profile (XZ Plane)
# Origin at bottom-left corner of the channel
sketch_profile = doc.addObject("PartDesign::SketchObject", "sketch_profile")
sketch_profile.Parent = body
sketch_profile.Support = [get_plane(doc, "XY_Plane")]
sketch_profile.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_profile.Constrain = True
sketch_profile.ViewObject.Constrain = True

# Geometry: Channel Profile
# Bottom wall (width = c_inner_d)
line_bottom = Part.LineSegment(App.Vector(0, 0), App.Vector(params.c_inner_d, 0))
# Right wall (height = c_outer_h)
line_right = Part.LineSegment(App.Vector(params.c_inner_d, 0), App.Vector(params.c_inner_d, params.c_outer_h))
# Top wall (width = c_inner_d)
line_top = Part.LineSegment(App.Vector(params.c_inner_d, params.c_outer_h), App.Vector(0, params.c_outer_h))
# Left wall (height = c_outer_h)
line_left = Part.LineSegment(App.Vector(0, params.c_outer_h), App.Vector(0, 0))

sketch_profile.addGeometry(line_bottom, False)
sketch_profile.addGeometry(line_right, False)
sketch_profile.addGeometry(line_top, False)
sketch_profile.addGeometry(line_left, False)

# Constraints: Close the loop
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1))
sketch_profile.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1))
# Right angle at corners
sketch_profile.addConstraint(Sketcher.Constraint("Angle", 0, 1, 90))
sketch_profile.addConstraint(Sketcher.Constraint("Angle", 1, 2, 90))
sketch_profile.addConstraint(Sketcher.Constraint("Angle", 2, 3, 90))
sketch_profile.addConstraint(Sketcher.Constraint("Angle", 3, 0, 90))
# Lengths
sketch_profile.addConstraint(Sketcher.Constraint("Length", 0, params.c_inner_d))
sketch_profile.addConstraint(Sketcher.Constraint("Length", 2, params.c_outer_h))

# 1.2 Feature: Pad (Channel Body)
pad_channel = doc.addObject("PartDesign::Pad", "pad_channel")
pad_channel.Parent = body
pad_channel.Profile = sketch_profile
pad_channel.Length = params.c_length
pad_channel.ViewObject.ZAxis = (doc.getObject("Z_Axis"), [""])
# Ensure it's a single solid
pad_channel.SemiSolid = False

# 2. End Plate Sketch
# The end plate is on the left face (X=0).
# We need a sketch on the YZ plane.
# Origin at the intersection of the left wall and bottom wall.
sketch_endplate = doc.addObject("PartDesign::SketchObject", "sketch_endplate")
sketch_endplate.Parent = body
# Attach to the left face of the channel
face_idx = 0 # The face created by line_left
sketch_endplate.Support = [get_plane(doc, "YZ_Plane")]
# Offset Z to align with the channel bottom if the plane is not at the face
# Actually, let's attach to the face directly and adjust placement if needed.
# For PartDesign::SketchObject, Support is (Plane, Face, Placement).
# If we use YZ_Plane (0,0,0), the face is at X=0.
# We want the sketch to start at the bottom of the channel (Z=0).
# The YZ plane is at X=0. The channel width is c_inner_d.
# The sketch needs to be wide enough (c_outer_h) and deep enough (c_end_t).
# Let's create the sketch geometry.

sketch_endplate.Placement = App.Placement(App.Vector(0, 0, 0)) # On YZ plane
sketch_endplate.Constrain = True

# Geometry: End Plate
# Height = c_outer_h (matches channel wall height)
# Thickness = c_end_t (extends in X direction, so sketch width in Y is c_end_t? No.)
# The sketch is on the YZ plane.
# Y axis corresponds to the channel width (c_outer_h).
# Z axis corresponds to the channel height (c_outer_h). Wait, standard orientation:
# Channel profile sketch was in XZ (Width X, Height Z).
# Left face is at X=0. Normal is X.
# Sketch on YZ plane: Y is horizontal (channel width direction), Z is vertical.
# The plate covers the entire width (c_outer_h) and has thickness c_end_t.
# But the plate is rectangular.
# Let's define the plate sketch:
# A rectangle of height c_outer_h and width c_end_t.
# However, the plate must be flush with the inner walls.
# The channel inner walls are at Y=0 and Y=c_inner_d.
# The plate outer face is at X=c_end_t.
# The plate inner face is at X=0.
# The plate height (in Z) is c_outer_h.
# The plate width (in Y) is c_inner_d (to match the opening) + 2*c_wall_t?
# "flush with the three inner channel walls".
# Inner walls are top, bottom, back.
# So the plate inner face (X=0) should have a hole or recess? No, it's a solid plate.
# "The end plate lies at one axial end and is flush with the three inner channel walls."
# This implies the plate has a cutout? Or the plate is just the back wall?
# Description: "joined top, bottom, and closed-back walls". The base part is an open channel.
# So the end plate IS the back wall.
# It should have the same height as the channel (c_outer_h).
# It should have the same width as the channel opening (c_inner_d) + wall thicknesses on sides?
# Usually, an end plate for a channel covers the open side? No, "opposite side open".
# So the channel has 3 walls: Top, Bottom, Back.
# The End Plate is the Back wall.
# So the plate should be: Height = c_outer_h. Width (along Y) = c_inner_d + c_wall_t + c_wall_t?
# Actually, the "inner channel walls" are the ones facing the conveyor.
# If the plate is flush with them, the plate's inner surface coincides with the plane of the inner walls?
# No, the inner walls are at Y=0 and Y=c_inner_d (if bottom is Z=0).
# Wait, my profile sketch:
# Bottom: Y=0 to Y=c_inner_d.
# Left Wall: X=0.
# Right Wall: X=c_inner_d.
# Top: Y=c_inner_d.
# So the channel opening is between X=c_inner_d and X=0? No.
# My sketch:
# 0,0 -> c_inner_d, 0 (Bottom)
# c_inner_d, 0 -> c_inner_d, c_outer_h (Right Wall)
# c_inner_d, c_outer_h -> 0, c_outer_h (Top)
# 0, c_outer_h -> 0, 0 (Left Wall)
# So the channel is open on the LEFT (X=0)? No, the line segments form a closed loop.
# The "hole" in the sketch is the area.
# The area is defined by X in [0, c_inner_d] and Z in [0, c_outer_h].
# The "Left Wall" is the line from (0, c_outer_h) to (0,0).
# The "Right Wall" is the line from (c_inner_d, 0) to (c_inner_d, c_outer_h).
# The channel is open on the SIDE?
# "open channel... joined top, bottom, and closed-back walls".
# "opposite side open".
# My sketch creates a solid block of size c_inner_d x c_outer_h x c_length.
# I need to subtract the open side.
# Let's redefine the profile sketch to be the "Back Wall" shape only.
# Back wall height: c_outer_h.
# Back wall width (thickness of wall): c_wall_t.
# And it needs to connect to top and bottom?
# "joined top, bottom".
# So the back wall is a rectangle of height c_outer_h and width c_wall_t.
# Then the top and bottom walls connect to its edges.
# Top wall thickness: c_wall_t. Bottom wall thickness: c_wall_t.
# Channel length: c_length.
# So the profile sketch should be the cross section of the ENTIRE channel.
# Let's re-do Sketch Profile.
# Origin at the inner corner of the bottom-left?
# Let's place origin at the inner corner of the bottom-back corner.
# X axis: along the channel length.
# Y axis: along the channel width (across the opening).
# Sketch Plane: YZ (Y=width, Z=height).
# Back wall: From Y=0 to Y=c_wall_t, Z=0 to Z=c_outer_h.
# Top wall: From Z=c_outer_h to Z=c_outer_h + c_wall_t, Y=0 to Y=c_inner_d.
# Bottom wall: From Z=0 to Z=c_wall_t, Y=0 to Y=c_inner_d.
# This forms an inverted U shape (if Y is width, Z is height).
# Wait, "joined top, bottom, and closed-back walls".
# Back wall is at Y=0.
# Top wall connects Back Wall top to Front side?
# No, the channel is open on one side.
# Let's assume the channel runs along X (Length).
# Cross section in YZ plane.
# Back wall (Y=0): Height c_outer_h. Thickness c_wall_t (in Y).
# Top wall (Z=c_outer_h): Width c_inner_d (in Y). Thickness c_wall_t (in Z).
# Bottom wall (Z=0): Width c_inner_d (in Y). Thickness c_wall_t (in Z).
# This creates a U-channel open at the top (Y > c_wall_t)? No.
# If Back is at Y=0, Top is at Z=c_outer_h. Bottom is at Z=0.
# The opening is usually on one side.
# Let's assume the opening is towards positive Y.
# So the walls are:
# 1. Back: X=const, Z in [0, c_outer_h], Y in [0, c_wall_t].
# 2. Top: Z=c_outer_h, Y in [c_wall_t, c_wall_t+c_inner_d], X in [0, c_length].
# 3. Bottom: Z=0, Y in [c_wall_t, c_wall_t+c_inner_d], X in [0, c_length].
# This matches "joined top, bottom, closed-back". Open side is Front (Y large).
# Okay, let's build the profile sketch in YZ plane.
# Origin: Inner corner of Bottom-Back (Y=c_wall_t, Z=0)? Or Outer?
# Let's put origin at the inner corner of the Bottom-Back (Y=c_wall_t, Z=0).
# Actually, standard practice: Origin at the bottom of the back wall.
# Let's use a sketch in YZ plane at X=0.
# Points:
# A: (0, 0)  <- Back Wall Bottom Inner
# B: (c_wall_t, 0) <- Back Wall Bottom Outer
# C: (c_wall_t, c_outer_h) <- Back Wall Top Outer
# D: (c_wall_t + c_inner_d, c_outer_h) <- Top Wall Front Outer
# E: (c_wall_t + c_inner_d, c_outer_h + c_wall_t) <- Top Wall Front Top
# F: (c_wall_t + c_inner_d, c_wall_t) <- Bottom Wall Front Outer? No.
# Let's trace the perimeter of the solid cross-section.
# Start at Back-Top-Outer: (c_wall_t, c_outer_h).
# Go Up to Top-Top-Outer: (c_wall_t, c_outer_h + c_wall_t). -> Wait, thickness is in Z.
# Let's restart coordinates.
# Y: Width direction. Z: Height direction.
# Back Wall: Y in [0, c_wall_t], Z in [0, c_outer_h].
# Top Wall: Y in [c_wall_t, c_wall_t + c_inner_d], Z in [c_outer_h, c_outer_h + c_wall_t].
# Bottom Wall: Y in [c_wall_t, c_wall_t + c_inner_d], Z in [0, c_wall_t].
# This forms a U shape.
# Perimeter:
# 1. (0, c_outer_h) to (c_wall_t, c_outer_h) [Back Top Inner]
# 2. (c_wall_t, c_outer_h) to (c_wall_t, 0) [Back Wall Thickness? No, this is inside]
# Let's draw the OUTSIDE of the walls to define the solid.
# No, we need the HOLE to be the opening.
# Let's define the profile as the solid shape directly.
# Vertices:
# P1: (0, 0) [Back-Bot-Inner] -> No, let's use Outer Corner.
# Let's use (0,0) as the inner corner of the bottom-back.
# Then:
# (0,0) to (c_wall_t, 0) [Bottom thickness] -> No, Z is height.
# Let's stick to Y (width), Z (height).
# Back Wall: Y=0..c_wall_t, Z=0..c_outer_h.
# Top Wall: Y=c_wall_t..c_wall_t+c_inner_d, Z=c_outer_h..c_outer_h+c_wall_t.
# Bottom Wall: Y=c_wall_t..c_wall_t+c_inner_d, Z=0..c_wall_t.
# The solid is the union of these.
# Perimeter path (Clockwise):
# 1. (0, c_outer_h) -> (c_wall_t, c_outer_h) [Top of Back Wall]
# 2. (c_wall_t, c_outer_h) -> (c_wall_t, c_outer_h + c_wall_t) [Inner corner of Top Wall]
# 3. (c_wall_t, c_outer_h + c_wall_t) -> (c_wall_t + c_inner_d, c_outer_h + c_wall_t) [Top Front Edge]
# 4. (c_wall_t + c_inner_d, c_outer_h + c_wall_t) -> (c_wall_t + c_inner_d, c_wall_t) [Right side of Top Wall? No]
# This is getting confusing. Let's simplify.
# The channel is a U-shape in YZ.
# Walls: Back, Top, Bottom.
# Thickness: t.
# Inner Width: w.
# Inner Height: h.
# Outer Width: w + 2*t.
# Outer Height: h + t.
# Let's define the sketch points based on Outer Corners.
# Origin
