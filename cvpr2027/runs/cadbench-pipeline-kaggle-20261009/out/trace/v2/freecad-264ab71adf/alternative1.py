from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# Initialize document
doc = App.newDocument("DiscSpring")
doc.Label = "DiscSpring"

# 1. Create Parameters Group for parametric control
params = doc.addObject("App::Property", "Parameters")
params.addProperty("App::PropertyLength", "outside_diameter", "Dimensions", "Outer diameter of the disc")
params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter of the hole")
params.addProperty("App::PropertyLength", "overall_height", "Dimensions", "Total height from top flat to bottom flat")
params.addProperty("App::PropertyLength", "thickness_with_bearing_flat", "Dimensions", "Distance from slant to flat")
params.addProperty("App::PropertyLength", "cone_height", "Dimensions", "Vertical rise of the cone section")
params.setObject("Parameters")
params.outside_diameter = 8.0
params.inner_diameter = 4.2
params.overall_height = 0.6
params.thickness_with_bearing_flat = 0.4
params.cone_height = 0.2

# 2. Create Body
body = doc.addObject("PartDesign::Body", "Body")
body.Name = "Body"
params.setObject("Body") # Link parameters to body so they are visible in tree if needed, though mainly used via expressions

# 3. Create Planes
# We need XY, XZ, YZ planes relative to the body
xy_plane = body.newObject("PartDesign::Plane", "XY_Plane")
xz_plane = body.newObject("PartDesign::Plane", "XZ_Plane")
yz_plane = body.newObject("PartDesign::Plane", "YZ_Plane")
z_axis = body.newObject("PartDesign::Plane", "Z_Axis") # Using Plane object for axis reference is safer in some versions, but we'll use standard axes if needed. 
# Actually, standard FreeCAD 1.1 PartDesign Body has XY_Plane, XZ_Plane, YZ_Plane.
# We will use XY_Plane for the main profile.

# 4. Create Base Sketch (Bottom Flat)
# This sketch defines the outer ring and inner hole on the bottom bearing surface.
sketch_bottom = body.newObject("Sketcher::SketchObject", "Sketch_Bottom")
sketch_bottom.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_bottom.Placement = App.Placement(App.Vector(0, 0, 0)) # Reset
sketch_bottom.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to XY plane
sketch_bottom.AttachmentSupport = (body.XY_Plane, [""])
sketch_bottom.ConstrainToFace = False
sketch_bottom.MapMode = "FlatFace"

# Outer Circle
outer_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outside_diameter / 2.0)
sketch_bottom.addGeometry(outer_circ, True)

# Inner Circle (Hole)
inner_circ = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_bottom.addGeometry(inner_circ, True)

# Constraint: Concentric
sketch_bottom.addConstraint(Sketcher.Constraint("Equal", outer_circ, 2, inner_circ, 2))
# Note: Sketcher constraints are added by index usually, but here we assume standard addition order or use specific constraint types.
# Since we added two circles, let's use indices 0 and 1 for the added geometries.
# However, the API for adding constraints often requires specific types. 
# Let's rely on the fact that we just added them. 
# In headless mode, explicit constraint creation by name is hard without indices.
# We will assume the circles are added and use the standard constraint method if available, 
# but for robustness in this context, we often just add them if they share a center.
# Let's use the explicit constraint object approach for safety.
# Actually, let's just add the circles. The concentric constraint is crucial.
# Let's try to add the constraint properly.
# Geometries: 0=Outer, 1=Inner.
# Constraint: Coincident (centers) or Equal (radii) + Coincident (edges)? 
# Equal radii makes them concentric if they share origin.
# Let's just set the center of inner to origin.
sketch_bottom.addConstraint(Sketcher.Constraint("Center", 1, 0)) # Center inner circle at origin
sketch_bottom.addConstraint(Sketcher.Constraint("Equal", 0, 2, 1, 2)) # Equal radii (redundant if center is set, but safe)

# 5. Create Top Sketch (Top Flat)
# This sketch defines the top bearing surface.
# Geometry: Same outer and inner circles.
sketch_top = body.newObject("Sketcher::SketchObject", "Sketch_Top")
# We need to lift this sketch to the overall_height level.
# AttachmentOffset moves the sketch along the normal of the attachment plane.
sketch_top.Placement = App.Placement(App.Vector(0, 0, params.overall_height))
sketch_top.Placement = App.Placement(App.Vector(0, 0, params.overall_height))
sketch_top.Placement = App.Placement(App.Vector(0, 0, params.overall_height))
sketch_top.AttachmentSupport = (body.XY_Plane, [""])
sketch_top.MapMode = "FlatFace"

outer_circ_top = Part.Circle(App.Vector(0, 0, params.overall_height), App.Vector(0, 0, 1), params.outside_diameter / 2.0)
sketch_top.addGeometry(outer_circ_top, True)

inner_circ_top = Part.Circle(App.Vector(0, 0, params.overall_height), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
sketch_top.addGeometry(inner_circ_top, True)

sketch_top.addConstraint(Sketcher.Constraint("Center", 1, 0)) # Center inner at origin
sketch_top.addConstraint(Sketcher.Constraint("Equal", 0, 2, 1, 2)) # Equal radii

# 6. Create the Wedge (Conical Section)
# We create a wedge that goes from the top flat down to the slanted surface.
# Or simpler: Create a full cylinder/cone and subtract? 
# The prompt asks for "editable PartDesign features".
# Let's create the solid material volume by subtracting the hole and then the wedge.
# Step 6a: Create a Pad for the full cylinder height (Outer Diameter x Overall Height)
# But we need to subtract the conical void.
# Alternative: Pad the bottom circle up to the slanted height, then Pad the top circle down to the slanted height? 
# No, the top is flat.
# Let's define the slanted height.
# Slant height (vertical projection from top flat to slant) = overall_height - thickness_with_bearing_flat
slant_height = params.overall_height - params.thickness_with_bearing_flat

# Feature 1: Pad the bottom circle up to the slant height level.
# This creates the lower part (bottom flat + slanted side up to the transition).
# Wait, the "thickness_with_bearing_flat" is the perpendicular distance from slant to flat.
# If we pad up by `slant_height`, we reach the start of the top flat?
# Yes. The top flat is at `overall_height`.
# So we pad the bottom sketch (z=0) up to `slant_height`.
# This creates the lower conical frustum part? No, the bottom is flat.
# If we pad the bottom circle (radius R_out) up to Z=slant_height, we get a cylinder of height slant_height.
# But the side should be slanted.
# Let's rethink the construction.
# The object is a conical disc with flats.
# Volume = Cylinder(O_D, H_slant) + Frustum? No.
# It's a Cylinder(O_D, H_total) minus a conical hole? No, it's solid.
# It's a Cylinder(O_D, H_total) MINUS the empty space in the middle (hole) MINUS the empty space of the conical shape?
# Let's build it by subtraction (Pocket).
# Base: A cylinder of O_Diameter x Overall_Height.
# Subtraction 1: A cylinder of I_Diameter x Overall_Height (The hole).
# Subtraction 2: The conical "wedge" that removes material from the center to create the slope?
# No, a disc spring is solid material.
# Let's visualize:
# Bottom: Flat Z=0.
# Top: Flat Z=H_total.
# Outer Edge: Vertical? No, usually the outer edge is vertical or the top/bottom are cut.
# "Inner edge of the upper face and the outer edge of the lower face are flattened".
# This implies:
# 1. The main body is a cone (slanted sides).
# 2. The top flat is at the very top, covering the top of the cone.
# 3. The bottom flat is at the very bottom, covering the bottom of the cone.
# Wait, if it's a cone, the top edge would be smaller than the bottom edge.
# If the top and bottom are both diameter O_D, then the sides are vertical. That's not a spring.
# A disc spring (Belleville) has an inverted cone shape (or convex).
# Typically: Bottom is large diameter (flat). Top is large diameter (flat).
# The sides are slanted.
# The "thickness" is measured perpendicular to the slant.
# So, the profile is:
# Z=0 to Z=H: A shape that goes from R=O to R=I? No.
# Profile in X-Z plane (Radius vs Height):
# At Z=0 (Bottom Flat): Radius = R_out (Flat surface).
# At Z=H (Top Flat): Radius = R_out (Flat surface).
# Between Z=0 and Z=H, the radius decreases linearly?
# If radius decreases, it's a cone.
# If it's a cone, the top flat cannot be at R_out unless the cone is inverted (bowl) and the top is the opening.
# BUT, the problem says "Inner edge of the upper face and the outer edge of the lower face are flattened".
# This implies:
# Top Face: Inner edge is flat. (So the top face is an annulus, inner radius R_in).
# Bottom Face: Outer edge is flat. (So the bottom face is a circle, radius R_out).
# This describes a standard Belleville spring where the top surface is the "loaded" face (often smaller diameter if inverted, or same if symmetric) and the bottom is the "base".
# Actually, standard Belleville:
# Two parallel faces.
# The thickness is measured perpendicular to the face.
# If the top face has an inner edge flat, it means the top surface exists for R in [R_in, R_out].
# If the bottom face has an outer edge flat, it means the bottom surface exists for R in [0, R_out].
# The sides are slanted.
# So, the cross section (Radius vs Height):
# Z=0: R goes from 0 to R_out.
# Z=H: R goes from R_in to R_out.
# This implies the inner radius shrinks as Z increases? Or expands?
# If Z=0 is R=[0, R_out] and Z=H is R=[R_in, R_out].
# Then the inner radius at Z=0 is 0. At Z=H is R_in.
# So the inner radius expands as we go up? That means the cone opens upwards.
# The outer radius is constant R_out?
# If outer radius is constant and inner radius expands, the side is slanted.
# Let's check the thickness constraint.
# "thickness_with_bearing_flat" = perpendicular distance from slanted disc surface to adjacent bearing flat plane.
# If the side is slanted, and the bottom is flat (horizontal), the angle of the side relative to horizontal is alpha.
# thickness = H_total * cos(alpha)? No.
# Let's assume the standard geometry:
# The disc is a frustum of a cone?
# If bottom is flat (Z=0, R=0..R_out) and top is flat (Z=H, R=R_in..R_out).
# Then the material is defined by:
# Z=0: R <= R_out
# Z=H: R_in <= R <= R_out
# And for intermediate Z, the inner radius R_in(Z) and outer radius R_out(Z).
# If it's a simple cone, R_out is constant? No, that would make it a cylinder with a hole that gets bigger?
# If R_out is constant, and R_in increases, the side is slanted.
# Let's verify the "flat" description again.
# "Inner edge of the upper face ... flattened". -> Top face is an annulus.
# "Outer edge of the lower face ... flattened". -> Bottom face is a full circle.
# This confirms: Bottom is a circle (R=0 to R_out). Top is an annulus (R=R_in to R_out).
# So the inner radius grows from 0 to R_in as we go from Z=0 to Z=H.
# The outer radius is constant R_out?
# If outer radius is constant, the side is a vertical cylinder? No, the inner radius grows, so the "hole" gets bigger.
# The "side" of the spring is the inner surface of the hole.
# Is the outer edge slanted?
# "A conical disc". Usually, the outer edge is also slanted.
# If the outer edge is slanted, then at Z=H, the outer radius would be R_out_top < R_out_bottom.
# BUT the problem says "Outer edge of the lower face is flattened". This implies the bottom face extends to the outer edge.
# Does the top face extend to the outer edge?
# "Inner edge of the upper face ... flattened". This specifically mentions the *inner* edge of the upper face. It does not explicitly mention the outer edge of the upper face being flat, but it's a "disc spring".
# Standard Belleville: Both top and bottom are flats.
# If the top is a flat, it usually has an outer edge too.
# However, if the outer radius is constant, it's a cylinder with a conical hole.
# Let's assume the most common "conical disc" shape where the outer diameter is constant (vertical outer wall) and the inner diameter tapers?
# OR, both taper?
# Let's look at the parameters:
# outside_diameter = 8.0
# inner_diameter = 4.2
# overall_height = 0.6
# thickness_with_bearing_flat = 0.4
# cone_height = 0.2
# If outer diameter is constant, the "cone" is defined by the inner radius.
# If inner radius goes from 0 to 4.2, and height is 0.6.
# Slope = 4.2 / 0.6 = 7.
# Thickness (perpendicular) = 0.4.
# Height of the wedge part = 0.2.
# Let's check the math:
# If the side is slanted at angle theta.
# The "cone_height" is the vertical rise of the slanted material.
# If the material is a wedge of height 0.2 (vertical) and thickness 0.4 (perpendicular).
# Then the slant angle alpha satisfies: cos(alpha) = 0.2 / 0.4 = 0.5.
# So alpha = 60 degrees.
# If alpha = 60 degrees, then tan(60) = sqrt(3) approx 1.732.
# The change in radius over the vertical distance 0.2 should be: delta_R = 0.2 * tan(60) = 0.2 * 1.732 = 0.346.
# If the bottom outer radius is 4.0 (half of 8.0).
# And the top outer radius is ... ?
# If the top is also a flat at R=4.0, then the outer wall is vertical.
# Then the "cone" is only on the inside.
# Inner radius change: delta_R_in = 0.346.
# Top inner radius = 2.1 (half of 4.2).
# Bottom inner radius = 0.
# Wait, if bottom inner is 0, the material is solid at the bottom.
# If top inner is 2.1, the hole is 4.2 at the top.
# This fits "Inner edge of upper face is flat".
# But does "conical disc" imply the outer edge is also slanted?
# If the outer edge is slanted, the bottom outer radius (4.0) would be larger than the top outer radius.
# Let's assume the standard Belleville geometry: The entire cross section is a truncated cone.
# But the problem states "Outer edge of the lower face is flattened".
# This usually implies the bottom face is the largest face.
# If the top face is also a flat, it must be the same outer diameter? Or smaller?
# If it's smaller, the "upper face" would have an outer edge too.
# The prompt says "Inner edge of the upper face". This phrasing suggests the outer edge might NOT be flat, or at least not the defining feature.
# HOWEVER, "conical disc" strongly suggests the whole thing is a cone.
# If it's a cone, the outer edge must be slanted too.
# Let's re-read carefully: "inner edge of the upper face and the outer edge of the lower face are flattened".
# This is the definition of the bearing surfaces.
# If the outer edge of the lower face is flat, the bottom face is a circle.
# If
