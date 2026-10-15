import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# --- Configuration & Parameters ---
# Base Part Parameters
p = App.ValueVector(0, 0, 0) # Dummy vector for App.ValueVector if needed, but App.Vector is preferred
# Using a VarSet for editable parameters
param_name = "Dimensions"

# Base Part Dimensions
CH_L = 114.55
CH_W = 38.48
CH_TH = 1.59
CH_H = 6.35
CH_BEND_Y_OFF = 13.68
CH_IN_R = 3.97
CH_BEND_A = 30.0 # degrees
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
# We will store values in the Body's data dictionary to simulate properties for this script structure,
# but in FreeCAD 1.1, the recommended way inside a script without a GUI interaction is to set them directly 
# or use a VarSet. To ensure they are "named document objects" as requested, we create a VarSet.
params = body.newObject("App::VarSet", param_name)
params.setExpression("CH_L", str(CH_L))
params.setExpression("CH_W", str(CH_W))
params.setExpression("CH_TH", str(CH_TH))
params.setExpression("CH_H", str(CH_H))
params.setExpression("CH_BEND_Y_OFF", str(CH_BEND_Y_OFF))
params.setExpression("CH_IN_R", str(CH_IN_R))
params.setExpression("CH_BEND_A", str(CH_BEND_A))
params.setExpression("CH_OUT_SW", str(CH_OUT_SW))
params.setExpression("CH_IN_SW", str(CH_IN_SW))
params.setExpression("FL_L", str(FL_L))
params.setExpression("FL_W", str(FL_W))
params.setExpression("SL_L", str(SL_L))
params.setExpression("SL_W", str(SL_W))
params.setExpression("SL_CNT", str(SL_CNT))
params.setExpression("SL_SP", str(SL_SP))
params.setExpression("FL_CR", str(FL_CR))
params.setExpression("FL_X_OFF", str(FL_X_OFF))
params.setExpression("SL_X_OFF", str(SL_X_OFF))
params.setExpression("BRO_SW", str(BRO_SW))
params.setExpression("VSL_L", str(VSL_L))
params.setExpression("VSL_W", str(VSL_W))
params.setExpression("VSL_Y_OFF", str(VSL_Y_OFF))
params.setExpression("AH_Y_OFF", str(AH_Y_OFF))

# --- Construct Base Part ---

# 1. Main Channel Profile (Side View: X-Z plane logic mapped to XY sketch)
# Coordinate system: X = Width direction, Y = Height direction.
# We will sketch on XY plane.
ch_sketch = body.newObject("Sketcher::SketchObject", "ChannelProfile")
ch_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
ch_sketch.AttachmentSupport = [doc.getObject("XY_Plane")] # Assuming standard planes exist or we create them? 
# The prompt implies standard planes exist. If not, we must create them. 
# Let's assume standard XY_Plane exists in the base document or create it if missing.
# Since we are scripting, we rely on App.Placement to place sketches relative to the body if we don't have planes.
# However, the prompt says "AttachmentSupport = (doc.getObject("XY_Plane"), [""])". 
# We must ensure XY_Plane exists.
# Standard FreeCAD document creates XY_Plane, XZ_Plane, YZ_Plane automatically.

ch_sketch.MapMode = "FlatFace"
ch_sketch.ConstrainToMapAxis = True

# Define Channel Geometry
# Center X = 0. 
# Left Wall: -CH_W/2 to -CH_W/2 + CH_TH
# Right Wall: CH_W/2 - CH_TH to CH_W/2
# Top Cap: Starts at CH_H - CH_TH, curves down to CH_BEND_Y_OFF + CH_IN_R? 
# Description: "inner and outer straight wall portions meet paired concentric bends tangentially"
# Let's define the path.
# Bottom: Flat at Y=0.
# Left Side: 
#   Vertical Up to Y = CH_H - CH_TH (Top of straight part)
#   Arc: Center at (-CH_W/2, CH_H - CH_TH + CH_IN_R)? No.
#   Let's simplify based on "radial end closures maintaining uniform wall thickness".
#   This implies a U-shape with rounded corners on the inside and outside.
#   
#   Outer Profile:
#     Start (-CH_W/2, 0) -> Up to (-CH_W/2, CH_H) -> Arc to (-CH_W/2 + CH_TH, CH_H - CH_TH) -> Right to (CH_W/2 - CH_TH, CH_H - CH_TH) -> Arc to (CH_W/2, CH_H) -> Down to (CH_W/2, 0).
#   Inner Profile (for thickness):
#     Start (-CH_W/2 + CH_TH, 0) -> Up to (-CH_W/2 + CH_TH, CH_H - CH_TH) -> Arc to (-CH_W/2 + 2*CH_TH, CH_H - CH_TH)? 
#     Actually, if it's a channel, usually the inner profile is just offset by CH_TH inward.
#     
#   Let's construct the outer perimeter and inner perimeter.
#   Outer Points:
#     P1: (-CH_W/2, 0)
#     P2: (-CH_W/2, CH_H)
#     P3: (-CH_W/2 + CH_TH, CH_H - CH_TH)  <-- Top Left Inner Corner? No, Top Left Outer Corner is (-CH_W/2, CH_H).
#     Wait, if thickness is uniform, the inner corner is shifted INWARD by CH_TH.
#     
#   Let's define the shape by vertices and arcs.
#   Outer:
#     (-CH_W/2, 0)
#     (-CH_W/2, CH_H)
#     Arc to (-CH_W/2 + CH_TH, CH_H - CH_TH) ? No, tangent continuity.
#     If the bend is at the top, the outer profile goes up, then arcs to the right.
#     Center of top-left outer arc: (-CH_W/2, CH_H - CH_TH + CH_IN_R)? 
#     If the bend is "tangential", the radius is CH_IN_R? Or is CH_IN_R the inner radius?
#     "vertical_channel_inner_bend_radius = 3.97 mm".
#     So the inner corner has R = 3.97.
#     The outer corner will have R_outer = R_inner + CH_TH = 3.97 + 1.59 = 5.56.
#     
#   Let's build the sketch geometry.
#   We need to draw lines and arcs.
#   
#   Helper function to add geometry
#   We will use Part.LineSegment and Part.Circle (center, radius) but constrained.
#   Actually, for PartDesign sketches, we usually draw lines and then add constraints.
#   Or we can use Part.Shape geometry directly if we trust the math.
#   Given the complexity, let's define points and use Part.Sketcher or just Part geometry and let the solver handle it?
#   No, PartDesign::SketchObject needs Sketcher::Constraint.
#   
#   Strategy: Define a single closed polyline that approximates the shape, then add fillets?
#   "meet paired concentric bends tangentially". This implies arcs.
#   Let's create the profile using Part.BSpline or Part.Shape and convert?
#   No, better to use Sketcher primitives.
#   
#   Let's define the Outer Path and Inner Path separately? Or one continuous loop?
#   One continuous loop is harder to sketch with arcs.
#   Let's create the Outer Perimeter and Inner Perimeter.
#   Actually, we can create a single shape with two closed loops? Sketcher supports multi-wire sketches.
#   
#   Let's create the Outer Loop:
#     Start (-CH_W/2, 0)
#     Line Up to (-CH_W/2, CH_H)
#     Arc (R=5.56) to (-CH_W/2 + CH_TH, CH_H - CH_TH) -> Center (-CH_W/2 + CH_TH - CH_IN_R? No.)
#     Let's calculate centers.
#     Top Left Inner Corner Center: (-CH_W/2, CH_H - CH_TH - CH_IN_R)? No.
#     Let's assume the bend is at the top.
#     Inner profile: Up to (-CH_W/2 + CH_TH, CH_H - CH_TH). Then Arc (R=CH_IN_R) to (-CH_W/2 + CH_TH + CH_IN_R, CH_H - CH_TH + CH_IN_R)? 
#     No, the inner profile bends inward.
#     
#     Let's try a simpler interpretation:
#     The channel is a rectangle with rounded corners on the TOP.
#     Bottom is flat.
#     Top-Left Outer Corner: Radius = CH_IN_R + CH_TH.
#     Top-Left Inner Corner: Radius = CH_IN_R.
#     
#     Outer Path:
#       (-CH_W/2, 0) -> Line -> (-CH_W/2, CH_H)
#       Arc (R = CH_IN_R + CH_TH) from angle 180 to 90? No, from vertical to horizontal.
#       Start angle 90 (up), End angle 0 (right). Center: (-CH_W/2 + CH_TH, CH_H - (CH_IN_R + CH_TH)).
#       End Point: (-CH_W/2 + CH_TH, CH_H - (CH_IN_R + CH_TH)) + (CH_IN_R + CH_TH, 0) = (-CH_W/2 + 2*CH_TH, CH_H - CH_IN_R - CH_TH)?
#       Let's just use Part.makeCircle and offset.
#       
#   Alternative: Create a solid rectangle with rounded corners (Part.makeCircle + extrude) and subtract?
#   But we need the inner profile to match the thickness exactly.
#   
#   Let's construct the shape using Part.BSpline or similar and then convert to sketch?
#   No, that's not editable.
#   
#   Let's use Sketcher primitives.
#   We will create two loops: Outer and Inner.
#   
#   Outer Loop Points:
#     P1: (-CH_W/2, 0)
#     P2: (-CH_W/2, CH_H)
#     P3: (-CH_W/2 + CH_TH, CH_H - (CH_IN_R + CH_TH)) # Bottom of the outer arc
#     P4: (CH_W/2 - CH_TH, CH_H - (CH_IN_R + CH_TH))
#     P5: (CH_W/2, CH_H)
#     P6: (CH_W/2, 0)
#     
#   Wait, the arc connects P2 and P3?
#   If P2 is (-CH_W/2, CH_H) and P3 is (-CH_W/2 + CH_TH, CH_H - (CH_IN_R + CH_TH)).
#   Vector P2->P3 = (CH_TH, - (CH_IN_R + CH_TH)). Length = sqrt(CH_TH^2 + ...). Not a quarter circle.
#   
#   Correct Geometry for Rounded Top Channel:
#   Top width = CH_W - 2*CH_TH.
#   Inner height to bend start = CH_H - CH_TH - CH_IN_R.
#   Outer height to bend start = CH_H - (CH_IN_R + CH_TH).
#   
#   Let's define the sketch directly.
#   We will create a single wire.
#   
#   Let's use a trick: Create a rectangle (-CH_W/2, 0) to (CH_W/2, CH_H).
#   Then add fillets? No, we need to remove material for thickness.
#   
#   Let's define the Outer Perimeter explicitly.
#   Start: (-CH_W/2, 0)
#   Line: (-CH_W/2, 0) to (-CH_W/2, CH_H)
#   Arc: Center (-CH_W/2, CH_H - (CH_IN_R + CH_TH)), Radius (CH_IN_R + CH_TH).
#   From (-CH_W/2, CH_H) to (-CH_W/2 + CH_TH, CH_H - CH_TH).
#   Line: (-CH_W/2 + CH_TH, CH_H - CH_TH) to (CH_W/2 - CH_TH, CH_H - CH_TH)
#   Arc: Center (CH_W/2, CH_H - (CH_IN_R + CH_TH)), Radius (CH_IN_R + CH_TH).
#   From (CH_W/2 - CH_TH, CH_H - CH_TH) to (CH_W/2, CH_H).
#   Line: (CH_W/2, CH_H) to (CH_W/2, 0)
#   Line: (CH_W/2, 0) to (-CH_W/2, 0)
#   
#   Inner Perimeter (for thickness):
#   Start: (-CH_W/2 + CH_TH, 0)
#   Line: (-CH_W/2 + CH_TH, 0) to (-CH_W/2 + CH_TH, CH_H - CH_TH)
#   Arc: Center (-CH_W/2 + CH_TH, CH_H - CH_IN_R), Radius CH_IN_R.
#   From (-CH_W/2 + CH_TH, CH_H - CH_TH) to (-CH_W/2 + CH_TH + CH_IN_R, CH_H - CH_TH).
#   Line: (-CH_W/2 + CH_TH + CH_IN_R, CH_H - CH_TH) to (CH_W/2 - CH_TH - CH_IN_R, CH_H - CH_TH)
#   Arc: Center (CH_W/2 - CH_TH, CH_H - CH_IN_R), Radius CH_IN_R.
#   From (CH_W/2 - CH_TH - CH_IN_R, CH_H - CH_TH) to (CH_W/2 - CH_TH, CH_H - CH_TH).
#   Line: (CH_W/2 - CH_TH, CH_H - CH_TH) to (CH_W/2 - CH_TH, 0)
#   Line: (CH_W/2 - CH_TH, 0) to (-CH_W/2 + CH_TH, 0)
#   
#   This creates the channel.
#   
#   Implementation in Sketcher:
#   We can add LineSegments and Arcs.
#   However, adding many primitives is tedious.
#   Is there a way to make a shape and convert to sketch? No.
#   
#   Let's use the fact that we can create a Part.Shape and then extract its edges?
#   No, PartDesign requires Sketcher objects.
#   
#   Okay, I will write a helper to add geometry to the sketch.
#   Since I cannot use loops in the sketch object API easily without constraints, I'll add them manually.
#   Wait, the sketch object has `addGeometry`.
#   
#   Let's refine the "Outer" and "Inner" as two separate wires in the same sketch?
#   Sketcher supports multiple wires.
#   
#   Let's create the Outer Wire first.
#   Then the Inner Wire.
#   Then constrain them.
#   
#   Actually, to make it robust and editable, I will define the coordinates and add them as LineSegment and Circle/Arc.
#   For arcs in Sketcher, we often use Part.Circle and then constraint? No, Sketcher doesn't have an "Arc" primitive directly in the same way as Line.
#   It has `Part.Circle` which is a full circle.
#   We can use `Part.LineSegment` and `Part.Edge`? No.
#   We can use `Part.Circle` and constrain the start/end points to the lines?
#   Or use `Part.BSpline`?
#   
#   Better approach: Use `Part.makeCircle` to create the arc geometry, then add it to sketch?
#   Sketcher::SketchObject.addGeometry accepts Part.Edge.
#   A full circle is an Edge.
#   If we add a full circle, we get a closed loop.
#   We need arcs.
#   We can create a Circle, then use `Part.Wire`?
#   No, `addGeometry` takes `Part.Edge`.
#   If we add a full circle, the sketch solver sees it as a loop.
#   If we offset a rectangle, we get the channel?
#   
#   Let's try a different approach for the channel:
#   Create a rectangle (Outer) and a rectangle (Inner) and fillet them?
#   No, the bends are specific radii.
#   
#   Okay, let's use the `Part.Circle` geometry and constrain it to be an arc between two points.
#   Sketcher
