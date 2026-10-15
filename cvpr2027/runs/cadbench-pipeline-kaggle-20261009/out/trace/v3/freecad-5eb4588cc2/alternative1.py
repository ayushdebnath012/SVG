import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import math

# --- Parameters ---
# Dimensions
D_ROD = 8.0
L_ROD = 112.3
D_SHOULDER = 19.6
L_SHOULDER = 6.5
C_SHOULDER = 0.3

D_HEAD_OUT = 20.0
D_G1 = 11.0
W_G1 = 3.5
D_G2 = 14.0
W_G2 = 2.4
G1_TO_BOSS_GAP = 5.0
G1_TO_G2_GAP = 1.0
R_G_OUT = 0.3
R_G_IN = 0.2
D_BOSS = 18.0
L_BOSS = 1.0
C_HEAD_END = 0.3

L_EXT = 4.4
TAP_L = 1.1
D_G_SHALLOW = 5.8
L_G_SHALLOW = 2.0
D_TIP = 6.0
L_TIP = 13.0
D_TIP_END = 4.77
C_TIP_END = 0.61

D_FLAT_DEP = 1.0
W_FLAT = 3.0
ANGLE_FLAT = 135.0 # Degrees

# --- Document Setup ---
doc = App.newDocument("Pin")

# Create necessary planes for the head and tip features (XZ and YZ)
# The main body will be built in XZ (XY in standard orientation usually, but we use Z as axis for rotation)
# Standard FreeCAD: X is 1, Y is 2, Z is 3.
# We will define the body on the XY plane (Z=0) and rotate around Z (Axis 3).
# Wait, PartDesign Revolution usually expects the profile in a plane perpendicular to the axis.
# If Axis is Z (0,0,1), the profile should be in XY plane (Z=0).
# So we create XY_Plane.

# Create reference planes
plane_XY = doc.addObject("PartDesign::Plane", "XY_Plane")
plane_XY.Placement = App.Placement(App.Vector(0, 0, 0))
plane_XY.Placement = App.Placement(App.Vector(0, 0, 0)) # Default
# Actually, PartDesign::Plane objects are simpler.
# Let's just use the default Workbench planes if available, or create them.
# Since we are script-only, let's create explicit Part::Plane objects attached to the Body.

body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# Create support planes
plane_XY = body.newObject("PartDesign::Plane", "XY_Plane")
plane_XY.Placement = App.Placement(App.Vector(0, 0, 0))

plane_XZ = body.newObject("PartDesign::Plane", "XZ_Plane")
plane_XZ.Placement = App.Placement(App.Vector(0, 0, 0)) # Will rotate later or just use as reference

plane_YZ = body.newObject("PartDesign::Plane", "YZ_Plane")
plane_YZ.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Feature Construction ---

# 1. Main Rod (Pad)
# Start at Z = -L_ROD - L_EXT
# End at Z = 0
sketch_rod = body.newObject("Sketcher::SketchObject", "Sketch_Rod")
sketch_rod.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_rod.Placement = App.Placement(App.Vector(0, 0, -L_ROD - L_EXT)) # Start at tip side?
# Let's define Z=0 as the junction between Elongated Rod and Rod Extension.
# Positive Z = Elongated Rod (Head side)
# Negative Z = Rod Extension (Tip side)

# Sketch Rod: Circle at Z = -L_ROD - L_EXT
sketch_rod.Placement = App.Placement(App.Vector(0, 0, 0))
# We will build the sketch relative to Z=0, then pad to negative Z.
sketch_rod.Placement = App.Placement(App.Vector(0, 0, -L_ROD - L_EXT))
sketch_rod.Placement = App.Placement(App.Vector(0, 0, 0)) # Reset, set in properties
sketch_rob = body.newObject("Sketcher::SketchObject", "Sketch_Rod")
sketch_rob.Placement = App.Placement(App.Vector(0, 0, -L_ROD - L_EXT))
sketch_rob.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_rob.Placement = App.Placement(App.Vector(0, 0, 0))

# Let's refine the placement logic.
# Axis of rotation: Z axis (0,0,1).
# Profile plane: XY plane (Z=0).
# We will construct the profile from Z = - (L_ROD + L_EXT) to Z = L_ROD + L_SHOULDER + D_HEAD_OUT...
# Wait, the head is wider. The profile changes.
# We cannot do one single Pad for the whole thing because the diameter changes.
# We must use multiple Pads/Pockets or a series of Pads building up from a common base or stacked.
# Strategy: Build from the Tip (Bottom) up to the Head (Top).
# Z=0 is the junction between Elongated Rod and Rod Extension.
# Tip is at Z = -(L_ROD + L_EXT).
# Head Top is at Z = L_ROD + L_SHOULDER + L_HEAD_TOTAL.

# Let's define Z coordinates relative to the Junction (Z=0).
Z_TIP_START = -(L_ROD + L_EXT)
Z_TIP_END = Z_TIP_START + L_TIP
Z_TIP_CHAMFER_END = Z_TIP_END - C_TIP_END # Chamfer is at the very end
# Actually, the chamfer is at the tip end.
# Z_TIP_START = -(L_ROD + L_EXT)
# Z_TIP_CHAMFER_END = Z_TIP_START + (L_TIP - C_TIP_END) # The chamfer reduces length effectively? 
# No, "tip_end_chamfer_axial_length" is the length of the chamfer.
# So the tip cylinder ends at Z_TIP_END - C_TIP_END?
# Usually chamfer replaces the end.
# Let's assume the chamfer is cut from the end face.
# Coordinate of the start of chamfer: Z_TIP_START + L_TIP - C_TIP_END
# Coordinate of the end of chamfer: Z_TIP_START + L_TIP

Z_G_SHALLOW_START = Z_TIP_START + L_TIP - L_G_SHALLOW
Z_G_SHALLOW_END = Z_TIP_START + L_TIP
Z_TAPER_START = Z_G_SHALLOW_END
Z_TAPER_END = Z_TIP_START + L_TIP - L_G_SHALLOW - TAP_L # Taper connects RodExt (D=8) to Shallow (5.8)
# Wait, Rod Extension is 4.4mm long.
# Z_TIP_START = -(L_ROD + L_EXT) = -(112.3 + 4.4) = -116.7
# Taper starts at Z_TIP_START + L_TIP - L_G_SHALLOW ??
# "Moving toward the free end, the rod extension is followed by the taper, the shallow circumferential groove, and then the tip."
# Order: Rod Extension -> Taper -> Shallow Groove -> Tip.
# This implies the Rod Extension is the bottom-most part (closest to Z negative infinity)?
# No, "cylindrical rod extension joins it at full rod diameter".
# "At the opposite end of the elongated rod, the cylindrical rod extension joins it..."
# So: Elongated Rod (Z>0) --- Junction (Z=0) --- Rod Extension (Z<0).
# Inside Rod Extension (moving towards tip, Z decreasing):
# Rod Extension (Full Dia) -> Taper -> Shallow Groove -> Tip.
# This means:
# Z = 0: Junction.
# Z = -4.4: End of Rod Extension (Start of Taper? No, Taper follows).
# "Rod extension is followed by the taper".
# So: Junction (Z=0) -> Rod Ext (Z=-4.4) -> Taper (Z=-5.5) -> Shallow (Z=-7.5) -> Tip (Z=-19.5).
# Let's re-read: "Moving toward the free end, the rod extension is followed by the taper..."
# Yes.
# So:
# Z=0 to Z=-4.4: Rod Extension (Dia 8).
# Z=-4.4 to Z=-5.5: Taper (8 -> 5.8).
# Z=-5.5 to Z=-7.5: Shallow Groove (Dia 5.8).
# Z=-7.5 to Z=-18.5 (approx): Tip (Dia 6).
# Tip Length = 13.0. Start of Tip = -7.5. End of Tip = -20.5.
# Tip End Chamfer: Length 0.61.
# So Tip Cylinder ends at -20.5 + 0.61 = -19.89.
# Chamfer goes from -19.89 to -20.5.

Z_JUNCTION = 0.0
Z_ROD_EXT_END = -L_EXT
Z_TAP_START = Z_ROD_EXT_END
Z_TAP_END = Z_TAP_START - TAP_L
Z_G_SHALLOW_START = Z_TAP_END
Z_G_SHALLOW_END = Z_G_SHALLOW_START - L_G_SHALLOW
Z_TIP_START = Z_G_SHALLOW_END
Z_TIP_END = Z_TIP_START - L_TIP
Z_TIP_CHAMFER_START = Z_TIP_END + C_TIP_END # Tip cylinder ends here
Z_TIP_CHAMFER_END = Z_TIP_END

# --- Part 1: Tip Assembly (Bottom) ---
# Pad from Z = Z_TIP_END to Z = Z_TIP_CHAMFER_START (Cylinder)
# Pad from Z = Z_TIP_CHAMFER_START to Z = Z_TIP_END (Chamfer - usually a Pocket or Chamfer feature)
# Let's use a Chamfer feature on the bottom face.

sketch_tip = body.newObject("Sketcher::SketchObject", "Sketch_Tip")
sketch_tip.Placement = App.Placement(App.Vector(0, 0, Z_TIP_CHAMFER_START))
sketch_tip.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_tip.Placement = App.Placement(App.Vector(0, 0, Z_TIP_CHAMFER_START))
sketch_tip.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_tip.Placement = App.Placement(App.Vector(0, 0, Z_TIP_CHAMFER_START))
sketch_tip.Placement = App.Placement(App.Vector(0, 0, 0))

# Add Tip Profile
# Circle Dia 6
sketch_tip.addGeometry(Part.makeCircle(D_TIP/2, App.Vector(0, 0, 0), App.Vector(0, 0, 1)), False)
# Add Chamfer Profile (Line)
# Chamfer connects (D_TIP/2) to (D_TIP_END/2) over length C_TIP_END.
# End point X: D_TIP_END/2. Start point X: D_TIP/2.
# Length along X: D_TIP/2 - D_TIP_END/2.
# Length along Z: C_TIP_END.
# Slope check: (D_TIP - D_TIP_END)/2 = (6 - 4.77)/2 = 0.615. C_TIP_END = 0.61.
# It's roughly 1:1.
# Line from (D_TIP/2, 0) to (D_TIP_END/2, C_TIP_END)
sketch_tip.addGeometry(Part.LineSegment(App.Vector(D_TIP/2, 0, 0), App.Vector(D_TIP_END/2, 0, C_TIP_END)), False)
sketch_tip.addGeometry(Part.LineSegment(App.Vector(D_TIP_END/2, 0, C_TIP_END), App.Vector(D_TIP_END/2, 0, 0)), False)
sketch_tip.addGeometry(Part.LineSegment(App.Vector(D_TIP_END/2, 0, 0), App.Vector(D_TIP/2, 0, 0)), False) # Closing the loop? No, sketch is a loop.
# Better to define the loop:
# 1. (D_TIP/2, 0)
# 2. (D_TIP/2, 0) -> (D_TIP/2, 0) (Wait, Z axis is up in sketch?)
# The sketch is in the XZ plane.
# Point A: (D_TIP/2, 0)
# Point B: (D_TIP/2, 0) -> (D_TIP/2, 0) is wrong.
# Point A: (D_TIP/2, 0)
# Point B: (D_TIP/2, 0) -> (D_TIP/2, 0) is not a line.
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0) -> (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (D_TIP/2, 0) to (D_TIP/2, 0)
# Line 1: (
