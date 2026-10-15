import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("TaperPin")

# --- Create Planes (XY, XZ, YZ) ---
# We need three orthogonal planes for sketching.
xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))

xz_plane = doc.addObject("PartDesign::Plane", "XZ_Plane")
xz_plane.Placement = App.Placement(App.Vector(0, 0, 0))
xz_plane.Normal = App.Vector(0, 1, 0) # Normal points along Y

yz_plane = doc.addObject("PartDesign::Plane", "YZ_Plane")
yz_plane.Placement = App.Placement(App.Vector(0, 0, 0))
yz_plane.Normal = App.Vector(1, 0, 0) # Normal points along X

# Create Axes (Standard placement)
x_axis = doc.addObject("PartDesign::Axis", "X_Axis")
x_axis.Placement = App.Placement(App.Vector(0, 0, 0))
x_axis.XAxis = App.Vector(1, 0, 0)

y_axis = doc.addObject("PartDesign::Axis", "Y_Axis")
y_axis.Placement = App.Placement(App.Vector(0, 0, 0))
y_axis.XAxis = App.Vector(0, 1, 0)

z_axis = doc.addObject("PartDesign::Axis", "Z_Axis")
z_axis.Placement = App.Placement(App.Vector(0, 0, 0))
z_axis.XAxis = App.Vector(0, 0, 1)

# --- Define Parameters ---
# We store parameters in a specific way compatible with PartDesign variable sets or direct property binding.
# To ensure editability in the tree, we will use a PartDesign::VarSet if possible, 
# but for direct property access in scripts, we often set them on the Body or a specific feature.
# The prompt asks for named document objects driving geometry.
# We will create a VarSet to hold the main dimensions.
params = doc.addObject("PartDesign::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Small end diameter")
params.addProperty("App::PropertyLength", "length", "Dimensions", "Overall length")
params.addProperty("App::PropertyLength", "rounded_end_height", "Dimensions", "Rounded tip height")
params.addProperty("App::PropertyFloat", "taper_ratio", "Dimensions", "Taper slope per unit length")

params.diameter = 0.6
params.length = 4.0
params.rounded_end_height = 0.08
params.taper_ratio = 0.02

# --- Create the Body ---
body = doc.addObject("PartDesign::Body", "Body")

# --- Sketch 1: Main Body Profile (for the taper) ---
# We sketch on the XY plane. The profile will be the outline of the pin.
sketch_main = body.newObject("Sketcher::SketchObject", "MainProfileSketch")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.Placement.Base = App.Vector(0, 0, 0) # Center at origin
# Attach to XY plane
sketch_main.Support = (xy_plane, [""])
sketch_main.MapMode = "FlatFace"

# Calculate intermediate dimensions for the sketch
# Half width at small end
half_small_d = params.diameter / 2.0
# Total length of the straight taper section = Total Length - 2 * Rounded Height
taper_length = params.length - (2 * params.rounded_end_height)
# Radius of the rounded tip (assume semi-circle for simplicity at the very end)
tip_radius = params.rounded_end_height

# Coordinates for the profile sketch (on XY plane, Z=0)
# We define a closed loop. 
# Start at bottom center of taper start.
# x, y coordinates relative to sketch center (0,0).
# y represents the vertical dimension in the sketch (Z in 3D).

# Point 1: Center of small end (bottom of taper)
# Point 2: Corner where taper starts (x=0, y = small_d/2)
# Point 3: Corner where taper ends (x = taper_length/2, y = large_d/2)
# Point 4: Center of large end
# Point 5: Corner of large end
# Point 6: Start of large end rounded corner
# Point 7: End of large end rounded corner
# Point 8: Start of small end rounded corner
# Point 9: End of small end rounded corner

# Large end diameter calculation
large_d = params.diameter + (taper_length * params.taper_ratio * 2)
half_large_d = large_d / 2.0

# Sketch Geometry
# We construct the profile symmetrically around the X-axis (Y=0 in sketch, Z=0 in 3D).
# Wait, Sketcher sketch is on XY plane. Z is the depth.
# So the profile is in X-Y plane of the sketch.
# Let's orient the pin along the X-axis of the sketch.
# Small end at x=0, Large end at x=taper_length.

# Profile points (x, y):
p1 = App.Vector(0, -half_small_d)
p2 = App.Vector(0, half_small_d)
p3 = App.Vector(taper_length, half_large_d)
p4 = App.Vector(taper_length, -half_large_d)

# Rounded Corners
# Small End Radius
r_small = tip_radius
# Large End Radius
r_large = tip_radius

# We need to insert lines and circles.
# To keep it simple and robust in a script, we use LineSegments and Circles where possible, 
# but for a complex tapered profile, we often rely on the sketcher constraints or 
# constructing the shape directly if the constraints get messy.
# However, the requirement is "PartDesign features driven by named objects".
# We can add geometry directly.

# Add main vertical lines for the taper height? No, let's do the outline.
# Since it's a script, we can calculate the exact points and add them.
# But Sketcher requires constraints for robustness.
# Let's try to add geometry and constraints.

# Geometry:
# Vertical line at x=0 (Small end straight part? No, it's a taper, so it's just a point if rounded)
# Actually, the profile is:
# 1. Small End Arc
# 2. Taper Line
# 3. Large End Arc

# Let's add the lines and arcs.
# Line 1: Small end top (just a point essentially, but we connect to taper)
# Let's build the shape as a closed loop of lines and circles.

# 1. Small End Arc (Centered at 0, 0)
# 2. Taper Line 1 (from Small End Top to Large End Top)
# 3. Large End Arc (Centered at taper_length, 0)
# 4. Taper Line 2 (from Large End Bottom to Small End Bottom)

# Arcs in Sketcher:
# Circle with a constrained radius and center.
# Then cut them? Or use "Arc3Point" or "ArcCenterRadius".
# Let's use Circle with a radius constraint and then constrain points.
# Actually, simpler: Add the straight lines and the arcs.

# Small End Arc
circle_small = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 1, 0), tip_radius)
sketch_main.addGeometry(circle_small, False)

# Taper Line Top
# Start: (0, tip_radius), End: (taper_length, half_large_d)
line_top = Part.LineSegment(App.Vector(0, tip_radius, 0), App.Vector(taper_length, half_large_d, 0))
sketch_main.addGeometry(line_top, False)

# Taper Line Bottom
# Start: (0, -tip_radius), End: (taper_length, -half_large_d)
line_bottom = Part.LineSegment(App.Vector(0, -tip_radius, 0), App.Vector(taper_length, -half_large_d, 0))
sketch_main.addGeometry(line_bottom, False)

# Large End Arc
circle_large = Part.Circle(App.Vector(taper_length, 0, 0), App.Vector(0, 1, 0), tip_radius)
sketch_main.addGeometry(circle_large, False)

# Constraints
# 1. Coincident: Small End Arc Center to Origin
# 2. Coincident: Large End Arc Center to (taper_length, 0)
# 3. Radius constraints
# 4. Tangent constraints between lines and arcs
# 5. Vertical lines? No, lines are tangent to arcs.

# Constraint: Small Arc Center to Origin
# LineSegment 0 (circle is 0?), Circle 1.
# In Sketcher, Circle is index 0? 
# Let's assume order: 0=CircleSmall, 1=LineTop, 2=LineBottom, 3=CircleLarge
# Constraint: Circle 0 Center to Point (0,0) -> Implicit by placement? 
# We need to constrain the circle center to the origin.
# Sketcher Constraint: "PointOnLine" or "Coincident" with a point.
# Let's add explicit points if needed, but usually, we constrain the circle center.
# We can't easily constrain circle center to a specific coordinate in basic script without adding a Point object.
# Instead, let's just constrain the circles to be tangent to the lines.

# Constraint: LineTop is tangent to CircleSmall at (0, tip_radius)
# This is the default if we place them right? No, we need to tell Sketcher.
# We will add constraints for robustness.
# Tangent between Circle 0 and Line 1 at end of Line 1 (or start).
# Tangent between Circle 0 and Line 2.
# Tangent between Circle 3 and Line 1.
# Tangent between Circle 3 and Line 2.

# Note: Sketcher constraints indices depend on the order of addition.
# Let's add the geometry again to be sure, or rely on the order above.
# Order: [CircleSmall, LineTop, LineBottom, CircleLarge]

# Constraint: Tangent Circle 0 and Line 1
# We need to specify the edge of the circle and the edge of the line.
# Sketcher.Constraint("Tangent", 0, 1, 0, 1) ? 
# Let's use the standard string format: "Tangent", <GeometryIndex>, <ConstraintType>, <GeometryIndex2>
# Actually, for circles, we often use "Radius" and "Point".
# Let's use a simpler approach: Add the shape, then constrain the tangency.
# Tangent: 0 (Circle) and 1 (Line)
# The line ends at the tangent point if the line is a segment starting from the tangent point.
# My line_top starts at (0, tip_radius). The circle ends there.
# So they are tangent by geometry if placed correctly? 
# Yes, if the line starts exactly at the tangent point of the circle.
# But Sketcher might not know they are tangent unless constrained.
# Let's add "Tangent" constraint.

# Also need to constrain the centers?
# If the lines are tangent, the distance between centers is fixed by geometry?
# Let's add "Point" constraint for the center of the small circle to (0,0).
# We need a point object.
# Let's create a helper point for the origin.
origin_point = body.newObject("Sketcher::SketchPoint", "Origin")
origin_point.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.addGeometry(Part.LineSegment(App.Vector(0,0,0), App.Vector(0,0,0)), False) # Dummy line to host point?
# Actually, Sketcher::SketchPoint is added directly.
# But wait, Sketcher::SketchPoint is a geometry itself.
# Let's replace the dummy line with a point.
# Actually, the list of geometries includes the point.
# Let's rebuild the geometry list properly.
# Remove the dummy line.

# Redefine sketch geometry properly:
# 1. Small Circle
# 2. Line Top
# 3. Line Bottom
# 4. Large Circle
# 5. Origin Point (for constraints)

# Re-add Origin Point
# We need to remove the dummy line if added. 
# The previous addGeometry for dummy line was just a line.
# Let's just assume the origin is (0,0) and we constrain the circles to it.
# How? "PointOnLine" to a line passing through origin?
# Or "Coincident" to a point.
# Let's create a point geometry.
# We need to insert it into the sketch.
# The previous addGeometry added a line. Let's remove it conceptually.
# Since I can't remove easily in a linear script without tracking indices, 
# I will add the point first, then the lines.
# Wait, the point needs to be in the sketch.
# Let's add the point first.
# Then the circles and lines.

# Reset sketch geometry approach:
# 1. Add Point at (0,0)
# 2. Add Small Circle
# 3. Add Line Top
# 4. Add Line Bottom
# 5. Add Large Circle

# Re-implementing the sketch construction cleanly:
# We will create the sketch object and then add geometries in a specific order.

# Clear existing sketch if any? No, it's new.
# Add Origin Point
origin_geom = body.newObject("Sketcher::SketchPoint", "OriginPoint")
origin_geom.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.addGeometry(origin_geom, False) # Add point

# Add Small Circle
sketch_main.addGeometry(circle_small, False)

# Add Large Circle
sketch_main.addGeometry(circle_large, False)

# Add Line Top
sketch_main.addGeometry(line_top, False)

# Add Line Bottom
sketch_main.addGeometry(line_bottom, False)

# Now add Constraints
# Constraint list:
# 1. Point (Origin) Center to Small Circle Center? 
#    Sketcher Constraint: "Point", 0 (Point), 1 (Circle), 2 (Constraint Type: "Center")? 
#    Format: "Point", <Index1>, <Type>, <Index2>
#    Actually, for Coincident/Point: "Point", <PointIndex>, <ConstraintType>, <GeometryIndex2>
#    Let's use "PointOnLine" with a line? No.
#    Let's use "Coincident" with the center of the circle? No, circle center isn't a geometry index directly in all versions.
#    Better: Constrain the center of the small circle to the point (0,0) using "Point" constraint.
#    Index 0: OriginPoint. Index 1: CircleSmall.
#    Constraint: "Point", 0, 1, 1, 1 (Point, Point, Center, Center) -> This constrains centers.
#    Wait, syntax: "Point", <Geom1>, <Type>, <Geom2>, <ConstraintType>
#    Types: "Coincident", "Parallel", "Tangent", "Radius", "Point", "Horizontal", "Vertical", "Angle", "Equal", "Distance", "Fixed", "Lock", "Symmetric"
#    For Point on Point: "Point", 0, 1, 1, 1 (Point, Point, Center, Center) is likely wrong.
#    Let's use "Coincident" for centers? No.
#    Let's use "Point" constraint to fix the center to the origin point.
#    "Point", 0, 1, 2 (Point, Point, Center) -> This constrains the point of geom1 to the center of geom2?
#    Actually, the standard is: "Point", <PointIndex>, <ConstraintType>, <TargetIndex>, <ConstraintType2>
#    If TargetIndex is a Circle, ConstraintType2 is "Center".
#    So: "Point", 0, "Point", 1, "Center"
    
# Let's try to constrain:
# 1. Small Circle Center to Origin Point
# 2. Large Circle Center to Origin Point (shifted? No, just constrain center to a point, then move point? No)
#    We need the large circle center to be at (taper_length, 0).
#    We can constrain Large Circle Center to a Point, and that Point to be distance X from Origin?
#    Or just constrain Large Circle Center to (taper_length, 0) using "Point" and a constructed point?
#    Easier: Constrain Large Circle Center to the Line Y=0? And Distance to Origin?
#    Let's use "Point" to constrain centers to specific points.
#    We need a point at (taper_length, 0).
#    Let's add a second point.
    
# Re-add Point 2
point2_geom = body.newObject("Sketcher::SketchPoint", "Point2")
point2_geom.Placement = App.Placement(App.Vector(taper_length, 0, 0))
sketch_main.addGeometry(point2_geom, False)

# Constraints:
# 1. Small Circle Center to Origin Point
sketch_main.addConstraint(
    Sketcher.Constraint("Point", 0, "Point", 1, "Center") # 0=Origin, 1=SmallCircle
)
# 2. Large Circle Center to Point2
sketch_main.addConstraint(
    Sketcher.Constraint("Point", 2, "Point", 3, "Center") # 2=Point2, 3=LargeCircle
)

# 3. Tangent: Small Circle and Line Top
# Small Circle (4) and Line Top (5)
sketch_main.addConstraint(
    Sketcher.Constraint("Tangent", 4, 5)
)
# 4. Tangent:
