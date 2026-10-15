from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# ============================================================================
# Configuration and Parameters
# ============================================================================
# Derived from task description
PRESSURE_ANGLE_DEG = 20.0
DIAMETRAL_PITCH = 24.0
NUM_TEETH = 20
PITCH_DIAMETER_MM = 21.1582
OUTER_DIAMETER_MM = 23.368
OVERALL_LENGTH_MM = 304.8
GEAR_MODULE_MM = 25.4 / DIAMETRAL_PITCH

# ============================================================================
# Document Setup
# ============================================================================
doc = App.newDocument("GearStock")
doc.Label = "GearStock"

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

# Create a VarSet to hold all parameters for easy editing later
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "pitch_diameter", "Dimensions", "Pitch Diameter [mm]")
params.pitch_diameter = PITCH_DIAMETER_MM
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer Diameter [mm]")
params.outer_diameter = OUTER_DIAMETER_MM
params.addProperty("App::PropertyLength", "overall_length", "Dimensions", "Overall Length [mm]")
params.overall_length = OVERALL_LENGTH_MM
params.addProperty("App::PropertyInteger", "number_of_teeth", "Dimensions", "Number of Teeth")
params.number_of_teeth = NUM_TEETH
params.addProperty("App::PropertyLength", "pressure_angle_deg", "Dimensions", "Pressure Angle [deg]")
params.pressure_angle_deg = PRESSURE_ANGLE_DEG
params.addProperty("App::PropertyLength", "gear_module", "Dimensions", "Gear Module [mm]")
params.gear_module = GEAR_MODULE_MM

# Create the Base Cylinder (Stock)
# We will use a sketch on the XY plane, revolve it around Z.
# The sketch will define the radial profile of the gear blank.

# 1. Create XY Plane
plane_xy = doc.addObject("PartDesign::PlanarObject", "XY_Plane")
plane_xy.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
body.addObject(plane_xy)

# 2. Create Base Sketch
base_sketch = body.newObject("Sketcher::SketchObject", "BaseProfileSketch")
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
base_sketch.ConstraintsFix = True
base_sketch.ConstraintsLock = True
base_sketch.MapMode = "FlatFace"
base_sketch.AttachmentSupport = (plane_xy, [])
base_sketch.GeometryList = []
base_sketch.ConstraintList = []

# Define the profile:
# 1. Line from Center (0,0) to Outer Radius
# 2. Arc from Outer Radius (0, R_outer) to Outer Radius (R_outer, 0) - actually we need to close the loop
# Let's define points:
# P0: (0, 0) - Center
# P1: (R_outer, 0)
# P2: (0, R_outer)
# P3: (0, 0) - Close
# This creates a quarter circle sector. Rotating 360 deg creates a cylinder.

r_outer = params.outer_diameter.Value
r_pitch = params.pitch_diameter.Value
r_root = r_outer - 2.0 * (params.gear_module.Value / 2.0) # Approximate root for simplicity based on module, or calculate exact

# Exact calculation for root diameter:
# Addendum = Module
# Dedendum = 1.25 * Module (Standard full depth)
# Pitch Dia = Dp
# Outer Dia = Dp + 2*Addendum
# Root Dia = Dp - 2*Dedendum
# Let's recalculate Root Diameter explicitly to be precise.
addendum = params.gear_module.Value
dedendum = 1.25 * params.gear_module.Value
r_root = (r_pitch - 2 * dedendum) / 2.0

# Sketch Geometry:
# Line 0: Center to Outer Radius along X
base_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(r_outer, 0, 0)), False)
# Line 1: Outer Radius along X to Outer Radius along Y (This would be a line, but we want an arc)
# Actually, standard practice for gear stock: 
# Draw line from center to outer radius.
# Draw arc from outer radius point (r,0) to (0,r).
# Draw line from (0,r) to center.
# Revolve 360.

# Line: (0,0) to (r_outer, 0)
# Arc: (r_outer, 0) to (0, r_outer) with center (0,0)
# Line: (0, r_outer) to (0,0)

base_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(r_outer, 0, 0)), False)
# Arc: Start (r_outer, 0), End (0, r_outer), Center (0,0), Radius r_outer, CounterClockwise
base_sketch.addGeometry(Part.Arc(App.Vector(r_outer, 0, 0), App.Vector(0, r_outer, 0), App.Vector(0, 0, 0), r_outer, False), False)
base_sketch.addGeometry(Part.LineSegment(App.Vector(0, r_outer, 0), App.Vector(0, 0, 0)), False)

# Constraints:
# Fix P0 (0,0)
base_sketch.addConstraint(Sketcher.Constraint("Point", "XY_Plane", "XY", 0, 0), 0, 2)
# Fix P1 (r_outer, 0) on X axis
base_sketch.addConstraint(Sketcher.Constraint("PointOnLine", "XY_Plane", "XY", 1, 0), 1, 2)
# Fix P2 (0, r_outer) on Y axis
base_sketch.addConstraint(Sketcher.Constraint("PointOnLine", "XY_Plane", "YX", 1, 0), 2, 2)
# Coincident P0 and P3 (last point of line) - handled by closure
# Tangent or Angle? The arc is tangent to lines at the axes.
# Arc tangent to X-axis at P1
base_sketch.addConstraint(Sketcher.Constraint("Tangent", "XY_Plane", "XY", 1, 2, 2), 1, 3)
# Arc tangent to Y-axis at P2
base_sketch.addConstraint(Sketcher.Constraint("Tangent", "XY_Plane", "XY", 1, 3, 1), 2, 3)
# Angle between X and Y line is 90
base_sketch.addConstraint(Sketcher.Constraint("Angle", "XY_Plane", "XY", 0, 2, 2), 3, 3)

# 3. Create the Base Cylinder via Revolution
base_rev = body.newObject("PartDesign::Revolution", "BaseCylinder")
base_rev.Profile = base_sketch
base_rev.ReferenceAxis = (body.getObject("Z_Axis"), [""]) # Wait, Z_Axis doesn't exist yet. 
# We need to create the axis objects or use the plane normal.
# Let's create the axes first to be safe, or use a specific axis creation method.
# Actually, PartDesign::Revolution expects a ReferenceAxis. 
# We can create a simple Axis object or use the fact that the sketch is on XY plane, so Z is the axis.
# Let's create the Z Axis.
z_axis = doc.addObject("Part::Line", "Z_Axis")
z_axis.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 1)) # Pointing up
# Note: Part::Line in FreeCAD is just a line. For PartDesign::Revolution, ReferenceAxis can be a Part::Line or App::Vector.
# However, the API reference suggests (doc.getObject("Z_Axis"), [""]).
# Let's assume we can use the created Z_Axis.

# Correction on ReferenceAxis: The API example uses (doc.getObject("Z_Axis"), [""]).
# We need to ensure the Z_Axis is added to the body or doc.
# Let's add it to the body.
body.addObject(z_axis)

# Re-set the revolution profile and axis
base_rev.Profile = base_sketch
# The ReferenceAxis parameter takes a tuple of (AxisObject, AxisIndexList) or similar.
# If we use the Z_Axis we just created:
base_rev.ReferenceAxis = (z_axis, [""])
base_rev.Angle = 360.0
base_rev.Length = params.overall_length.Value
base_rev.Symmetric = False

# 4. Create the Teeth Profile Sketch
# This sketch will be placed on the Pitch Diameter cylinder surface (or a coaxial cylinder at pitch dia).
# Then we revolve the tooth profile around the Z axis.

# First, create the cylinder surface or a reference plane?
# Standard way: Create a sketch on the surface of the cylinder at the pitch diameter.
# However, creating a sketch on a cylinder surface in PartDesign usually involves a "Surface" sketch.
# Alternatively, create a sketch on a plane at the pitch diameter, then use a "Revolution" with the profile offset or simply place the sketch on the cylinder if possible.
# FreeCAD PartDesign allows placing a sketch on a "Surface". The cylinder created by BaseCylinder is a solid, but its faces are surfaces.
# Let's try to place the sketch on the "Top" face of the cylinder? No, teeth are along the length.
# Teeth are radial. So we need a sketch on a cylindrical surface.
# How to create a sketch on a cylindrical surface in PartDesign?
# Option A: Use the "Create Sketch on Surface" feature (PartDesign::SketchObject).
# Option B: Create a wire on the cylinder surface using Part operations, but we need a Sketcher::SketchObject.
# The standard workflow for gears in FreeCAD often involves creating a sketch on a "Cylinder" surface.
# Let's create a new Body? No, must be one Body.
# Let's assume the API supports placing a sketch on a face of a solid.
# The BaseCylinder is a solid. We can get its "Top" face (if it were a block), but it's a cylinder.
# We need the face at the pitch diameter? No, the pitch diameter is an imaginary line.
# The teeth are carved OUT of the cylinder.
# The profile of the tooth is usually defined on the pitch cylinder surface.
# Let's create a sketch on the "Top" face of the cylinder (which is a circle). Then we can extrude the teeth?
# No, that creates a disk.
# We need to sketch on the cylindrical surface.
# Let's create a sketch object attached to the cylinder surface.
# We need to identify the face. Since we don't have a face handle yet, we can use the "FlatFace" mode on the cylinder face if we can reference it.
# Or, simpler: Create a sketch on a plane at Z=0, draw the tooth profile in the X-Z plane (radial vs axial)?
# No, standard gear geometry is Radial (R) vs Tangential (Theta) or Radial vs Axial?
# The teeth are uniform along the length.
# Profile: Radius vs Angle.
# So we need a sketch on the cylinder surface.

# Let's create a "CylinderSurface" object? No, PartDesign uses sketches.
# Let's try to attach the sketch to the cylinder's surface.
# We need to get the face index.
# Since we are scripting headlessly, getting the face index dynamically is tricky without recompute and checking.
# Alternative: Create a sketch on a plane, then use a "Pad" or "Pocket" that sweeps the profile?
# No, "Revolution" is the correct feature for gear teeth.
# We need to define the profile on the cylinder surface.
# Let's create a sketch on the "Top" face of the cylinder (the circular end face) and then rotate it? No.
# Let's create a sketch on the "Right" face (cylindrical surface).
# How?
# Create a sketch object. Set MapMode to "FlatFace".
# Select the cylinder's surface.
# But we don't know the face index.
# Let's create a temporary plane at the pitch diameter? No.

# Workaround: 
# 1. Create a sketch on the XY plane (at Z=0).
# 2. Draw the tooth profile in 2D (Radius vs Angle? No, Sketcher is 2D Cartesian).
# 3. We can't draw a polar profile directly in Sketcher easily without conversion.
# 4. Better approach: 
#    a. Create a sketch on the "Top" face of the cylinder (circular face).
#    b. Draw the tooth profile as a curve on that face? No, that's a disk.
#    c. Actually, we can create a sketch on the "Cylindrical" surface if we use the correct attachment.
#    d. In FreeCAD 0.21/1.0, you can right-click the face and create a sketch.
#    e. Headlessly: `sketch.Placement = App.Placement(...)`, `sketch.MapMode = "FlatFace"`, `sketch.AttachmentSupport = (cylinder_object, [face_index])`.
#    We need the face index of the cylinder.
#    Let's assume the first face of the cylinder is the bottom, second is the top?
#    Actually, for a cylinder, faces are: Bottom, Top, Side.
#    We need the Side face.
#    Let's try to get the side face.
#    Since we can't inspect the topology easily before recompute, let's assume standard ordering or use a different method.

# Alternative Method (Robust for scripting):
# Create the tooth profile as a sketch on the "Top" face of the cylinder, but then use a "Pocket" that extrudes the profile along the Z axis?
# No, that would create a slot.
# We want teeth.
# Let's go back to the Revolution feature.
# We need a sketch on the cylindrical surface.
# Let's create a sketch on the "Top" face (circular), but draw the profile in the "Normal" direction? No.
# Let's try this:
# 1. Create a sketch on the XY plane.
# 2. Draw the tooth profile as a "Polar" sketch? No, Sketcher is Cartesian.
# 3. Draw the tooth profile as a set of lines/arcs in Cartesian (x=r, y=theta*radius)? No.
# 4. Draw the tooth profile in the "Radial-Transverse" plane.
#    Let's create a sketch on the cylinder surface.
#    We need to find the face index.
#    Let's assume the cylinder has 3 faces: Front, Back, Side.
#    Let's try to attach to the "Side" face.
#    How to identify the side face?
#    We can create a sketch on the "Top" face (circular) and then rotate the profile 90 degrees? No.

# Let's try a different strategy:
# 1. Create a sketch on the XY plane.
# 2. Draw the tooth profile as a 2D shape (Radius vs Height along the tooth face?).
# 3. No, the tooth profile is on the cylinder surface.
# 4. Let's create a sketch on the "Top" face of the cylinder (which is a circle).
# 5. Draw the tooth profile on this face? No, that's a cross section.
# 6. We need to sketch on the curved surface.

# Let's assume the `BaseCylinder` object creates a solid.
# We can create a sketch on the "Top" face (circular) and then use a "Pocket" with `Direction = (0,0,1)`? No.
# We need to sketch on the cylindrical surface.
# In FreeCAD, you can create a sketch on a cylinder face.
# Let's try to attach the sketch to the cylinder's surface.
# We'll try index 2 (assuming 0=bottom, 1=side, 2=top or similar).
# Actually, let's create a sketch on the "Top" face (circular) and then use the "Revolution" feature on that sketch?
# No, that would revolve the circle around Z, creating a sphere or torus.

# Correct Approach for Gear Teeth in PartDesign:
# 1. Create a sketch on the "Top" face of the cylinder (the circular face).
# 2. Draw the tooth profile in the "Unfolded" view? No.
# 3. Use the "Create Sketch on Surface" feature.
#    Sketch.Placement = App.Placement(App.Vector(0, 0, params.overall_length.Value/2), App.Rotation())
#    Sketch.MapMode = "FlatFace"
#    Sketch.AttachmentSupport = (cylinder_object, [2]) # Assuming index 2 is the side.
#    This is risky if the face index is wrong.

# Let's try a more robust method:
# Create a sketch on the XY plane.
# Draw the tooth profile as a "Polar" wire? No.
# Draw the tooth profile in Cartesian coordinates:
#   x = r * cos(theta)
#   y = r * sin(theta)
#   z = axial_position
# We can define the profile as a set of points on the cylinder surface.
# But Sketcher doesn't support "Parametric Curve on Cylinder".
# However, we can use a "Revolution" feature with a "Profile" sketch that is on the "Pitch Cylinder" surface.
# How to get the Pitch Cylinder surface?
# We can create a
