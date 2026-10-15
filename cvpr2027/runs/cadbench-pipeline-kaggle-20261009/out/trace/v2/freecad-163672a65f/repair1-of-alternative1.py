import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("TaperPin")

# --- Create Planes ---
# In FreeCAD 1.1 PartDesign, planes are created as PartDesign::Plane objects.
# They require a Placement and a Normal vector.
xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))

xz_plane = doc.addObject("PartDesign::Plane", "XZ_Plane")
xz_plane.Placement = App.Placement(App.Vector(0, 0, 0))
xz_plane.Normal = App.Vector(0, 1, 0)

yz_plane = doc.addObject("PartDesign::Plane", "YZ_Plane")
yz_plane.Placement = App.Placement(App.Vector(0, 0, 0))
yz_plane.Normal = App.Vector(1, 0, 0)

# Create Axes
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
# We use a PartDesign::VarSet to hold the parameters as requested.
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

# --- Sketch 1: Main Body Profile ---
# We sketch on the XY plane. The profile will be the outline of the pin.
sketch_main = body.newObject("Sketcher::SketchObject", "MainProfileSketch")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
# Attach to XY plane
sketch_main.Support = (xy_plane, [""])
sketch_main.MapMode = "FlatFace"

# Calculate intermediate dimensions for the sketch
half_small_d = params.diameter / 2.0
taper_length = params.length - (2 * params.rounded_end_height)
tip_radius = params.rounded_end_height
large_d = params.diameter + (taper_length * params.taper_ratio * 2)
half_large_d = large_d / 2.0

# We will construct the profile using LineSegments and Circles.
# To ensure robustness, we will add constraints.
# Geometry Order:
# 0: Origin Point
# 1: Small Circle
# 2: Point at Large End Center
# 3: Line Top
# 4: Line Bottom
# 5: Large Circle

# 1. Add Origin Point
origin_point = body.newObject("Sketcher::SketchPoint", "OriginPoint")
origin_point.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.addGeometry(origin_point, False)

# 2. Add Small Circle (Radius = tip_radius, Center = Origin)
circle_small = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 1, 0), tip_radius)
sketch_main.addGeometry(circle_small, False)

# 3. Add Point at Large End Center
point_large_center = body.newObject("Sketcher::SketchPoint", "PointLargeCenter")
point_large_center.Placement = App.Placement(App.Vector(taper_length, 0, 0))
sketch_main.addGeometry(point_large_center, False)

# 4. Add Line Top (Tangent to Small Circle, ends at Large Circle center height)
# Start: (0, tip_radius), End: (taper_length, half_large_d)
line_top = Part.LineSegment(App.Vector(0, tip_radius, 0), App.Vector(taper_length, half_large_d, 0))
sketch_main.addGeometry(line_top, False)

# 5. Add Line Bottom
# Start: (0, -tip_radius), End: (taper_length, -half_large_d)
line_bottom = Part.LineSegment(App.Vector(0, -tip_radius, 0), App.Vector(taper_length, -half_large_d, 0))
sketch_main.addGeometry(line_bottom, False)

# 6. Add Large Circle (Radius = tip_radius, Center = PointLargeCenter)
circle_large = Part.Circle(App.Vector(taper_length, 0, 0), App.Vector(0, 1, 0), tip_radius)
sketch_main.addGeometry(circle_large, False)

# --- Add Constraints ---
# Indices in sketch_main.Geometry:
# 0: OriginPoint
# 1: CircleSmall
# 2: PointLargeCenter
# 3: LineTop
# 4: LineBottom
# 5: CircleLarge

# 1. Coincident: Small Circle Center to Origin Point
sketch_main.addConstraint(Sketcher.Constraint("Point", 0, "Point", 1, "Center"))

# 2. Coincident: Large Circle Center to PointLargeCenter
sketch_main.addConstraint(Sketcher.Constraint("Point", 2, "Point", 5, "Center"))

# 3. Tangent: Small Circle and Line Top
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 1, 3))

# 4. Tangent: Small Circle and Line Bottom
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 1, 4))

# 5. Tangent: Large Circle and Line Top
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 5, 3))

# 6. Tangent: Large Circle and Line Bottom
sketch_main.addConstraint(Sketcher.Constraint("Tangent", 5, 4))

# 7. Horizontal: Line Top (to ensure it's straight and aligned)
# Actually, the tangent constraints and points should define it, but let's add a horizontal constraint for robustness if needed.
# However, the line is defined by two points. The tangent constraint ensures the slope matches the circle.
# Let's add a constraint to fix the Y position of the start of the line to the top of the small circle?
# The tangent constraint handles the slope. The start point is (0, tip_radius).
# We need to ensure the line starts exactly at the tangent point.
# The tangent constraint between a circle and a line segment usually implies the line is tangent to the circle.
# If the line segment starts at the tangent point, it works.
# Let's add a "Point" constraint to fix the start of LineTop to the top of SmallCircle?
# No, simpler: The geometry is defined by coordinates. The constraints just lock them.
# The coordinates (0, tip_radius) and (taper_length, half_large_d) are hardcoded.
# The tangent constraint ensures the line is tangent to the circle at the start point.
# This is sufficient.

# --- Create the Pad Feature ---
# We will pad the profile along the Z-axis (normal to XY plane).
# The pin is symmetric, so we can pad half length and mirror, or pad full length.
# Let's pad the full length.
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch_main
# The sketch is on XY plane (Z=0). We want the pin to extend along Z.
# The profile is in the XY plane of the sketch.
# We need to orient the sketch such that the "height" of the profile (Y in sketch) becomes the radius,
# and the "length" of the profile (X in sketch) becomes the length of the pin.
# The Pad will extrude along the Z-axis of the sketch (which is the normal to XY plane).
# So the pin will be along Z.
# Let's adjust the sketch orientation if necessary, but standard is:
# Sketch on XY -> Extrude along Z.
# Profile X -> Length. Profile Y -> Radius.
# This matches our setup.
pad.Length = params.length
pad.Type = "Solid"
# Ensure the pad creates a solid
pad.makeSolid = True

# --- Save the document ---
# Derive path from __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Recompute to ensure all features are updated
doc.recompute()

# Save
doc.saveAs(str(output_path))

print(f"Model saved to: {output_path}")
