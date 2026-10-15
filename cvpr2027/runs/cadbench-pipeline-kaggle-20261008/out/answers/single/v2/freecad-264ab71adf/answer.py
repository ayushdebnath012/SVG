import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("DiscSpring")

# --- Parameters ---
# Define a VarSet to hold the parameters for easy editing
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outside_diameter", "Dimensions", "Outer diameter of the disc")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter of the hole")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height between bearing flats")
params.addProperty("App::PropertyLength", "thickness_with_bearing_flat", "Dimensions", "Thickness of the flat section")
params.addProperty("App::PropertyLength", "cone_height", "Dimensions", "Height of the conical section")

# Set values as per requirements
params.outside_diameter = 8.0
params.inner_diameter = 4.2
params.overall_height = 0.6
params.thickness_with_bearing_flat = 0.4
params.cone_height = 0.2

# --- Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Base Sketch (Outer Profile) ---
# We will create the outer profile on the XY plane.
# The profile will be a closed loop consisting of:
# 1. Outer circle
# 2. Inner circle (hole)
# 3. Two vertical lines connecting them to form the bearing flat width
# However, to make the bearing flat horizontal, we need to think about the geometry.
# The problem states: "inner edge of the upper face and the outer edge of the lower face are flattened".
# This implies a shape that looks like a trapezoid in cross-section but with flat tops/bottoms on the inner/outer radii.
# Actually, a disc spring with bearing flats usually looks like a hexagon in cross section if cut through the center,
# but here it describes a specific geometry:
# - Top face: Flat annulus from inner_radius to outer_radius.
# - Bottom face: Flat annulus from inner_radius to outer_radius.
# - Side: Conical frustum connecting the inner edge of top to inner edge of bottom? 
#   Wait, the description says "inner edge of the upper face ... flattened".
#   This means the top surface is flat. The bottom surface is flat.
#   The side walls are conical.
#   The "thickness_with_bearing_flat" is the perpendicular distance from the slanted surface to the flat surface.
#   
# Let's construct the profile on the XY plane (Radius vs Height).
# We need a closed loop.
# Points:
# 1. (OuterRadius, TopZ)
# 2. (InnerRadius, TopZ)
# 3. (InnerRadius, BottomZ)
# 4. (OuterRadius, BottomZ)
# This creates a rectangular annulus. But we need a cone.
# The cone connects the inner edge of the top flat to the inner edge of the bottom flat? 
# No, that would be a cylinder with a hole.
# 
# Re-reading: "conical disc ... inner edge of the upper face and the outer edge of the lower face are flattened".
# This is slightly ambiguous. Usually, a disc spring has a conical side.
# If the top is flat and the bottom is flat, and the side is conical, the profile is:
# - Top line: From InnerRadius to OuterRadius at Z = TopZ.
# - Bottom line: From InnerRadius to OuterRadius at Z = BottomZ.
# - Inner side: A line connecting (InnerRadius, TopZ) to (InnerRadius, BottomZ)? No, that's vertical.
# - Outer side: A line connecting (OuterRadius, TopZ) to (OuterRadius, BottomZ)? No, that's vertical.
# 
# Let's interpret "bearing flats" in the context of a disc spring.
# A standard disc spring is a truncated cone.
# If we flatten the top edge (inner radius) and the bottom edge (outer radius), we are cutting the cone.
# So the profile is:
# 1. Start at (OuterRadius, TopZ).
# 2. Go inwards to (InnerRadius, TopZ). (Top Flat)
# 3. Go down the inner slope to (InnerRadius, BottomZ). (Inner Slope)
# 4. Go outwards to (OuterRadius, BottomZ). (Bottom Flat)
# 5. Go up the outer slope to (OuterRadius, TopZ). (Outer Slope)
# 
# Let's check the dimensions:
# overall_height = 0.6 (Distance between TopZ and BottomZ).
# thickness_with_bearing_flat = 0.4 (Perpendicular distance from slanted surface to flat surface).
# cone_height = 0.2 (Nominal vertical rise of the slanted material centerline).
# 
# If the top flat is at Z=0.6 and bottom flat is at Z=0.0.
# The "slanted material centerline" rises 0.2mm.
# This implies the conical part is only 0.2mm high.
# The rest (0.4mm) is the bearing flat thickness?
# But the description says "thickness_with_bearing_flat is the perpendicular distance from the slanted disc surface to the adjacent bearing flat plane".
# This confirms the geometry:
# - There is a conical section of height 0.2mm.
# - There is a flat section of thickness 0.4mm.
# - The flat section is perpendicular to the slanted surface? 
#   "perpendicular distance ... to the adjacent bearing flat plane".
#   If the flat plane is horizontal (Z=const), and the slanted surface is at an angle, the perpendicular distance is the shortest distance between the plane and the line.
#   This matches the standard definition of a chamfer or a flat cut on a cone.
# 
# So the profile construction:
# We need to define the vertices in the XY plane (Radius, Z).
# Let's place the bottom flat at Z=0 and top flat at Z=0.6.
# 
# Geometry Logic:
# 1. Top Flat: Radius from Inner (Ri) to Outer (Ro) at Z = 0.6.
# 2. Bottom Flat: Radius from Inner (Ri) to Outer (Ro) at Z = 0.0.
# 3. Inner Slope: Connects (Ri, 0.6) to (Ri, 0.0)? 
#    If the inner edge of the top is flattened, the inner slope must start from the inner edge of the top flat.
#    But if the bottom is also flattened, the inner slope must end at the inner edge of the bottom flat.
#    This would make the inner wall vertical.
#    
#    Alternative interpretation: The "bearing flat" is the result of cutting the cone.
#    The cone has a certain angle. We cut the top and bottom to make them flat.
#    The "thickness_with_bearing_flat" is the distance from the original cone surface to the new flat surface.
#    The "cone_height" is the height of the remaining conical part.
#    
#    Let's assume the profile is defined by 4 lines:
#    A. Top Flat: Horizontal line at Z=0.6 from Ri to Ro.
#    B. Bottom Flat: Horizontal line at Z=0.0 from Ri to Ro.
#    C. Inner Wall: Connects (Ri, 0.6) to (Ri, 0.0)? -> Vertical.
#    D. Outer Wall: Connects (Ro, 0.6) to (Ro, 0.0)? -> Vertical.
#    This creates a cylinder with a hole. Not a cone.
#    
#    Let's re-read carefully: "conical disc ... inner edge of the upper face and the outer edge of the lower face are flattened".
#    This phrasing is tricky. "Inner edge of the upper face" is the circle at Ri on the top.
#    "Outer edge of the lower face" is the circle at Ro on the bottom.
#    If these are flattened, it means the top surface is flat (annulus) and the bottom surface is flat (annulus).
#    The sides are conical.
#    If the sides are conical, they connect the inner edge of the top to the inner edge of the bottom? 
#    And the outer edge of the top to the outer edge of the bottom?
#    If so, the sides are vertical cylinders.
#    
#    Maybe the "cone" refers to the shape of the spring when compressed? No, "free travel".
#    Maybe the "cone" is the main body, and the flats are cuts.
#    If the main body is a cone, the top is a point or a small circle, and the bottom is a large circle.
#    If we flatten the top edge (inner radius) and bottom edge (outer radius), we are cutting the cone.
#    This implies the profile is:
#    1. Top Flat: From Ri to Ro at Z=Top.
#    2. Inner Slope: From (Ri, Top) to (Ri, Bottom)? No.
#    3. Outer Slope: From (Ro, Top) to (Ro, Bottom)? No.
#    
#    Let's try a different interpretation which is common in disc springs:
#    The profile is a trapezoid-like shape but with flat tops/bottoms on the radii.
#    Actually, let's look at the parameters again.
#    cone_height = 0.2. overall_height = 0.6. thickness = 0.4.
#    0.2 + 0.4 = 0.6.
#    This suggests the object is composed of a conical section (height 0.2) and a flat section (thickness 0.4).
#    The flat section is perpendicular to the slanted surface?
#    "thickness_with_bearing_flat is the perpendicular distance from the slanted disc surface to the adjacent bearing flat plane".
#    This implies the flat plane is NOT horizontal if the slanted surface is not vertical?
#    But "bearing surfaces that distribute the load evenly" usually implies horizontal planes.
#    If the flat plane is horizontal, and the slanted surface is at an angle, the perpendicular distance is the shortest distance.
#    
#    Let's assume the following geometry which fits the "disc spring" description best:
#    The object is a frustum of a cone.
#    The top face is an annulus (flat).
#    The bottom face is an annulus (flat).
#    The side walls are conical.
#    BUT, the description says "inner edge of the upper face ... flattened".
#    This might mean the top face is NOT a full annulus, but the edge is flat?
#    No, "bearing flats (supporting surfaces)" implies the entire top and bottom faces are flat.
#    
#    Let's reconsider the "cone_height".
#    If the object is a frustum, the height is the vertical distance between the top and bottom faces.
#    If the top and bottom faces are horizontal, the height is simply Z_top - Z_bottom.
#    The "cone_height" parameter is described as "nominal vertical rise of the slanted material centerline".
#    This sounds like the height of the conical part only.
#    This implies the object is NOT a simple frustum.
#    It implies the object has a conical part and a flat part.
#    
#    Hypothesis:
#    The object is a frustum of a cone, but the top and bottom are cut to be flat.
#    Wait, a frustum already has flat top and bottom.
#    Maybe the "cone" is the shape of the side walls, and the "flattening" refers to the fact that the top and bottom are not the full extent of the cone?
#    No, that doesn't make sense.
#    
#    Let's try to construct the profile based on the "perpendicular distance" clue.
#    If the flat plane is horizontal (Z=const), and the slanted surface is at an angle alpha.
#    The perpendicular distance d = h * sin(alpha), where h is the vertical height of the slanted part.
#    Here d = 0.4, h_cone = 0.2.
#    sin(alpha) = 0.4 / 0.2 = 2. Impossible.
#    
#    Therefore, the "bearing flat plane" is NOT horizontal relative to the slanted surface in the way I thought.
#    OR, the "cone_height" is not the vertical height of the slanted part.
#    "cone_height is the nominal vertical rise of the slanted material centerline".
#    This is the vertical height.
#    If d = 0.4 and h = 0.2, then d > h.
#    This implies the flat surface is NOT perpendicular to the slanted surface in the way that d = h * sin(alpha).
#    Wait, "perpendicular distance from the slanted disc surface to the adjacent bearing flat plane".
#    If the flat plane is horizontal, and the slanted surface is at an angle, the perpendicular distance is indeed h * sin(alpha).
#    If d > h, then sin(alpha) > 1, which is impossible.
#    
#    Conclusion: My interpretation of the geometry is wrong.
#    Let's re-read: "thickness_with_bearing_flat is the perpendicular distance from the slanted disc surface to the adjacent bearing flat plane".
#    Maybe the "slanted disc surface" is the side wall, and the "bearing flat plane" is the top/bottom face.
#    If the top face is flat and the side wall is slanted, the distance from the side wall to the top face is 0 at the intersection.
#    Unless... the "bearing flat" is a separate feature?
#    No, "consists of a conical disc ... where the inner edge ... are flattened".
#    
#    Let's try a different geometric interpretation:
#    The object is a hexagonal prism in cross-section? No, "conical disc".
#    Maybe the "cone" is the shape of the hole? No.
#    
#    Let's look at the numbers again.
#    overall_height = 0.6.
#    thickness = 0.4.
#    cone_height = 0.2.
#    0.4 + 0.2 = 0.6.
#    This suggests the object is composed of two parts stacked vertically:
#    Part 1: A flat section of thickness 0.4.
#    Part 2: A conical section of height 0.2.
#    Total height = 0.6.
#    
#    If Part 1 is flat (horizontal), and Part 2 is conical (slanted).
#    The "bearing flat" is the top of Part 1 and the bottom of Part 1?
#    "inner edge of the upper face and the outer edge of the lower face are flattened".
#    This implies the top face (of the whole object) is flat.
#    And the bottom face (of the whole object) is flat.
#    If the object is a stack of a flat part and a conical part, the top face is flat (top of flat part).
#    The bottom face is flat (bottom of conical part)?
#    If the conical part is on top of the flat part, the bottom of the conical part is the top of the flat part (flat).
#    The bottom of the whole object is the bottom of the flat part (flat).
#    So the whole object has flat top and bottom.
#    The side walls are:
#    - Top part: Conical.
#    - Bottom part: Vertical (since it's a flat cylinder).
#    
#    Let's check the "perpendicular distance" again.
#    "thickness_with_bearing_flat is the perpendicular distance from the slanted disc surface to the adjacent bearing flat plane".
#    If the slanted surface is the side of the conical part, and the adjacent bearing flat plane is the top of the flat part (which is also the bottom of the conical part).
#    The distance from the slanted surface to the flat plane (at the junction) is 0.
#    This doesn't fit "thickness = 0.4".
#    
#    Maybe the "bearing flat" is the top of the conical part?
#    If the conical part is truncated to have a flat top.
#    Then the "slanted disc surface" is the side.
#    The "bearing flat plane" is the top.
#    The perpendicular distance from the side to the top plane is 0 at the edge.
#    
#    Let's try the reverse: The "bearing flat" is the top of the object.
#    The "slanted disc surface" is the side.
#    The "thickness" is the distance from the top edge to the bottom edge? No.
#    
#    Let's reconsider the "disc spring" shape.
#    A disc spring is a truncated cone.
#    When compressed, it flattens.
#    The "bearing flats" are the top and bottom faces.
#    The "thickness_with_bearing_flat" is the thickness of the material at the bearing flat.
#    In a standard disc spring, the thickness is constant? No, it tapers.
#    But here, we have a specific "thickness_with_bearing_flat" parameter.
#    This suggests the thickness at the bearing flat is 0.4mm.
#    And the "cone_height" is 0.2mm.
#    This implies the object is a frustum where the thickness at the top is 0.4mm and the thickness at the bottom is 0.4mm?
#    No, that would be a cylinder.
#    
#    Let's assume the following profile which is a common variation:
#    The object is a frustum of a cone.
#    The top face is an annulus.
#    The bottom face is
