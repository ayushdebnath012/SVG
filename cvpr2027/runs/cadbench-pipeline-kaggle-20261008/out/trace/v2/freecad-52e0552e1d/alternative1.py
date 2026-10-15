import FreeCAD as App
import Part
from pathlib import Path

# Initialize document
doc = App.newDocument("Gear")

# 1. Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# 2. Define Parameters (VarSet)
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Gear Module")
params.addProperty("App::PropertyLength", "face_width", "Dimensions", "Face Width")
params.addProperty("App::PropertyLength", "hub_width", "Dimensions", "Hub Width")
params.addProperty("App::PropertyLength", "hub_diameter", "Dimensions", "Hub Diameter")
params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Shaft Diameter")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter")
params.addProperty("App::PropertyLength", "root_diameter", "Dimensions", "Root Diameter")
params.addProperty("App::PropertyLength", "addendum", "Dimensions", "Addendum")
params.addProperty("App::PropertyLength", "dedendum", "Dimensions", "Dedendum")
params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "Pressure Angle Deg")

# Set Values (ISO 21771 based)
params.gear_module = 1.0
params.face_width = 10.0
params.hub_width = 10.0
params.hub_diameter = 35.0
params.shaft_diameter = 10.0
params.pitch_diameter = 40.0
params.outer_diameter = 42.0
params.root_diameter = 37.5
params.addendum = 1.0
params.dedendum = 1.25
params.pressure_angle_deg = 20.0

# Derived: Number of teeth
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.number_of_teeth = 40

# 3. Create Sketches
# Base sketch for the gear body (Outer and Root circles + Pressure angle line)
sketch_outer = body.newObject("Sketcher::SketchObject", "Sketch_GearOuter")
sketch_outer.Plane = "XY_Plane"
sketch_outer.Close = False
# Add Outer Diameter Circle
sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0), False)
# Add Root Diameter Circle
sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.root_diameter / 2.0), False)
# Add Pressure Angle Line (tangent to base circle)
# Base Circle Diameter = Pitch Diameter * cos(Pressure Angle)
base_radius = (params.pitch_diameter / 2.0) * (App.getDocument("Base").getObject("XY_Plane").BaseVector.Length / App.getDocument("Base").getObject("Z_Axis").BaseVector.Length * App.cos(App.Radian(params.pressure_angle_deg))) # Approximation logic handled below in code
# Correct Base Radius Calculation
base_radius = (params.pitch_diameter / 2.0) * App.cos(App.Radian(params.pressure_angle_deg))
sketch_outer.addGeometry(Part.LineSegment(App.Vector(base_radius, 0, 0), App.Vector(base_radius * 1.5, 0, 0)), False)

# Define constraints for Base Circle
# Base Circle Radius = Pitch Radius * cos(Pressure Angle)
# We need to define the base circle explicitly or construct the line tangentially.
# Let's define the base circle for clarity in constraints
sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), base_radius), False)
# Coincident centers
sketch_outer.addConstraint(Sketcher.Constraint("Point", 0, "Center", 1, "Center"), False) # Center of circles
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"), False)
# Tangent constraint between pressure angle line and base circle
sketch_outer.addConstraint(Sketcher.Constraint("Distance", 2, 1, 1), False) # Simplified: Distance from origin to line start
# Better approach: Define the line start at base_radius on X axis, and ensure it's tangent to base circle.
# Actually, standard way: Line segment starts at base_radius on X, goes up. Tangent to base circle.
# Let's use explicit points and tangent constraint.
# Point 2 is (base_radius, 0). Point 3 is (base_radius, 0). No, that's a point.
# Let's define the line from (base_radius, 0) to (base_radius, 100).
# Constraint: Distance from (base_radius, 0) to origin is base_radius.
# Constraint: Line 2 (pressure line) is tangent to Circle 3 (base circle).
# Constraint: Line 2 passes through Point 2 (base_radius, 0).

# Re-building sketch logic cleanly:
sketch_outer.clearGeometry()
sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0), False)
sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.root_diameter / 2.0), False)
sketch_outer.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), base_radius), False)
sketch_outer.addGeometry(Part.LineSegment(App.Vector(base_radius, 0, 0), App.Vector(base_radius, 100, 0)), False)

sketch_outer.addConstraint(Sketcher.Constraint("Point", 0, "Center"), True)
sketch_outer.addConstraint(Sketcher.Constraint("Point", 1, "Center"), True)
sketch_outer.addConstraint(Sketcher.Constraint("Point", 2, "Center"), True)
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"), True)
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 1, "Center", 2, "Center"), True)
sketch_outer.addConstraint(Sketcher.Constraint("Tangent", 2, 3, 2, 1), True) # Line (3) tangent to Base Circle (2)
sketch_outer.addConstraint(Sketcher.Constraint("Distance", 3, 2, 1, 0), True) # Line (3) start point distance to origin? No.
# Let's use the "Distance" constraint to fix the start point of the line to the Base Circle radius.
# Actually, the line starts at (base_radius, 0).
sketch_outer.addConstraint(Sketcher.Constraint("PointOnLine", 3, 2, 0, 1, 0), True) # This might not work directly.
# Simplest robust way: Fix start point of line to be on X axis at distance base_radius.
sketch_outer.addConstraint(Sketcher.Constraint("Distance", 3, 1, 0, 2), True) # Distance between point 3 and origin is base_radius? No, point 2 is origin.
# Let's just constrain the start of the line to be on the X axis and at distance base_radius from origin.
sketch_outer.addConstraint(Sketcher.Constraint("Distance", 3, 2, 1, 0), True) # Distance between point 3 and point 2 (origin) is base_radius.
sketch_outer.addConstraint(Sketcher.Constraint("Vertical", 3, 2, 0, 1), True) # Line 3 is vertical? No, we want tangent.
# Tangent constraint is the key.
sketch_outer.addConstraint(Sketcher.Constraint("Tangent", 3, 2, 2, 1), True) # Line 3 tangent to Circle 2.
# Ensure Line 3 starts at the intersection of X-axis and Base Circle.
sketch_outer.addConstraint(Sketcher.Constraint("PointOnLine", 3, 2, 0, 1, 1), True) # Point 3 lies on Line X-Axis? No.

# Let's try a simpler parametric sketch approach for the tooth profile.
# Sketch_GearOuter:
# 1. Outer Circle
# 2. Root Circle
# 3. Base Circle
# 4. Line starting from Base Circle tangent point, going up.
# Constraints:
# - All circles concentric.
# - Line tangent to Base Circle.
# - Line start point coincident with Base Circle (at the tangent point).
# - Line start point on X axis? Not necessarily, rotation will happen later.
# Actually, for generating teeth, we usually draw a profile and revolve/pattern it.
# Here we will pattern the whole gear. So we just need the outline.

# Let's refine Sketch_GearOuter constraints:
# Entities:
# 0: Outer Circle
# 1: Root Circle
# 2: Base Circle
# 3: Line (Pressure Angle Line)
# Constraints:
# - 0, 1, 2 concentric (Point Center)
# - 3 Tangent to 2
# - 3 passes through the point on circle 2 where it is tangent? Yes, by definition of tangent.
# - We need to ensure the line doesn't rotate freely. We can constrain one end of the line to the X axis.
# Let's add a line segment on the X axis from origin to base_radius.
sketch_outer.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(base_radius, 0, 0)), False)
# Rename entities implicitly by index.
# 4: X-axis segment
sketch_outer.addConstraint(Sketcher.Constraint("Coincident", 4, "Center", 2, "Center"), True)
sketch_outer.addConstraint(Sketcher.Constraint("Distance", 4, 2, 1, 0), True) # Length is base_radius
sketch_outer.addConstraint(Sketcher.Constraint("Tangent", 3, 2, 2, 1), True) # Line 3 tangent to Circle 2
sketch_outer.addConstraint(Sketcher.Constraint("Point", 3, 4, 1, 0), True) # Line 3 starts at end of Line 4?
# This is getting complex to script perfectly without GUI.
# Alternative: Use the standard "Tangent" and "Distance" from origin.
# Let's assume the line starts at (base_radius, 0).
# We can constrain the start of Line 3 to be the same as the end of Line 4.
sketch_outer.addConstraint(Sketcher.Constraint("Point", 3, 4, 1, 0), True)
sketch_outer.addConstraint(Sketcher.Constraint("Tangent", 3, 2, 2, 1), True)
sketch_outer.addConstraint(Sketcher.Constraint("Tangent", 3, 0, 2, 1), True) # Line 3 tangent to Outer Circle? No, that's wrong.

# Let's try a different strategy for the sketch.
# Create a sketch for ONE TOOTH profile on a radial plane? No, the task asks for a spur gear body.
# Standard way: Sketch the full gear profile (outer, root, keyway if any) and pattern?
# Or sketch the tooth profile and revolve?
# Given "number_of_teeth", "gear_module", etc., the best approach for a single body is:
# 1. Sketch the full gear outline (Outer circle, Root circle).
# 2. Create a "Gear" feature using a specific PartDesign feature? No, such feature doesn't exist.
# 3. Use a "Pad" with a sketch that includes the teeth?
# To keep it editable and parametric:
# Sketch the gear body with the teeth generated by a "Pattern" feature?
# We can't pattern a 3D face easily to create teeth unless we have a tooth profile.
# Approach:
# 1. Sketch the gear body WITHOUT teeth (just the hole and the outer/inner circles).
# 2. Create a sketch of the TOOTH profile on a plane tangent to the pitch circle? No.
# 3. Create a sketch of the TOOTH profile on the XY plane, but only for one tooth?
#    Then use a "Pad" to make it 3D, then use a "PolarPattern" on the 3D object?
#    Yes, this works.

# Step 3a: Sketch the base body (Hole, Hub, Outer, Root)
sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_Base")
sketch_base.Plane = "XY_Plane"
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0), False)
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.root_diameter / 2.0), False)
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_diameter / 2.0), False)
sketch_base.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.shaft_diameter / 2.0), False)
sketch_base.addConstraint(Sketcher.Constraint("Point", 0, "Center"), True)
sketch_base.addConstraint(Sketcher.Constraint("Point", 1, "Center"), True)
sketch_base.addConstraint(Sketcher.Constraint("Point", 2, "Center"), True)
sketch_base.addConstraint(Sketcher.Constraint("Point", 3, "Center"), True)
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"), True)
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 1, "Center", 2, "Center"), True)
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 2, "Center", 3, "Center"), True)

# Step 3b: Create a sketch for ONE TOOTH profile.
# We need a plane for this. Let's create a new plane offset from XY?
# Or use the XY plane and draw the tooth profile, then rotate it?
# If we draw the tooth profile on XY, it will overlap.
# Let's create a sketch on the XY plane but only draw the tooth profile, then use a specific pattern?
# No, the cleanest way in PartDesign:
# 1. Create the base body (Pad from Sketch_Base).
# 2. Create a sketch for the TOOTH profile on a plane perpendicular to the axis (XY plane).
#    Wait, if we draw a tooth profile on XY, it's just a line.
#    We need to extrude it radially? No.
#    We need to rotate it around the center.
#    So, we create a sketch of the TOOTH profile on the XY plane.
#    The sketch consists of lines forming the tooth shape.
#    Then we use a "Revolution" feature? No, that makes a ring.
#    We use a "Pad" to make the tooth height? No.
#    Correct workflow:
#    1. Create a sketch of the TOOTH profile on the XY plane.
#    2. Use a "Pad" to extrude it? No.
#    3. Use a "Revolution" feature to create the teeth?
#       - Profile: The tooth profile (in a radial plane).
#       - Axis: Z axis.
#       - Angle: 360.
#       This creates the teeth.
#    So, we need to create a sketch of the tooth profile on a plane that contains the Z axis (e.g., XZ plane).

# Let's do this:
# 1. Create Sketch_Tooth on XZ plane.
#    - Draw the tooth profile relative to the pitch circle.
#    - The profile will be a closed loop (tooth) or open loop?
#    - Usually, we draw the tooth profile and then revolve it.
#    - The profile should be the shape of ONE tooth.
#    - We need to define the tooth boundaries.
#    - Tooth thickness at pitch circle = Pi * Module.
#    - Tooth height = Addendum + Dedendum.
#    - We need to define the involute curves? No, too complex for script.
#    - We can approximate with straight lines or use a simplified tooth profile.
#    - For a spur gear, the standard profile is involute.
#    - We can generate the involute mathematically in the sketch.

# Generating Involute in Sketch:
# Base Circle Radius = (Pitch Diameter / 2) * cos(Pressure Angle)
# Involute curve: r = BaseRadius / cos(theta), theta = integral(r/...)?
# Parametric equation for involute:
# x = BaseRadius * (cos(phi) + phi * sin(phi))
# y = BaseRadius * (sin(phi) - phi * cos(phi))
# where phi is the roll angle.

# Let's create the tooth sketch on the XZ plane.
# We need to define the tooth profile.
# The tooth is symmetric about the X axis (if we align it).
# We will draw half the tooth (from pitch circle to tip) and mirror it?
# Or draw the full tooth.
# Let's draw the full tooth profile.
# Start at the root circle?
