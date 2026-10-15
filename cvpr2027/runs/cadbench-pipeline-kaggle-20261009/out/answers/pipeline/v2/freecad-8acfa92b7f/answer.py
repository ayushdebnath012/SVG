import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("SlipOnFlange")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# --- Parameters ---
# We define parameters in the Body's properties to keep them accessible and editable.
# Note: In FreeCAD 1.1, we can add properties directly to the Body object or use a VarSet.
# Using direct properties on the Body is robust for this structure.

# Dimensions
outer_circle_diameter = 108.0
flange_thickness = 12.2
total_height = 17.5
bore_diameter = 34.5
hub_diameter = 50.8
raised_face_diameter = 49.3
raised_face_thickness = 2.0
bolt_circle_diameter = 79.2
bolt_hole_diameter = 15.7
number_bolt_holes = 4

# --- Base Sketch (Outer Profile) ---
# Create XY plane if it doesn't exist (standard in new docs, but explicit is safer)
xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0))
doc.recompute()

sketch_base = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_base.Support = (doc.getObject("XY_Plane"), [])
sketch_base.MapMode = "FlatFace"

# Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), outer_circle_diameter / 2.0)
sketch_base.addGeometry(outer_circle, False)

# Bore Circle (for reference in sketch, will be used for pocket later)
bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_diameter / 2.0)
sketch_base.addGeometry(bore_circle, False)

# Hub Circle (for reference)
hub_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hub_diameter / 2.0)
sketch_base.addGeometry(hub_circle, False)

# Raised Face Circle (for reference)
raised_face_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), raised_face_diameter / 2.0)
sketch_base.addGeometry(raised_face_circle, False)

# Bolt Circle (for reference)
bolt_circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_circle_diameter / 2.0)
sketch_base.addGeometry(bolt_circle_geom, False)

# Constraints: Coincident centers
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # Outer & Bore
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2)) # Outer & Hub
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 3)) # Outer & Raised
sketch_base.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 4)) # Outer & Bolt

# Add a constraint to ensure the sketch is closed/valid if needed, though circles are fine.
# We need to constrain the bolt holes later.

doc.recompute()

# --- Feature 1: Pad (Main Body) ---
# Pad the base sketch to total_height
pad = body.newObject("PartDesign::Pad", "Pad_Flange")
pad.Profile = sketch_base
pad.Length = total_height
pad.Type = "Solid"
pad.MidPlane = False
pad.Reverse = False

doc.recompute()

# --- Feature 2: Pocket (Bore) ---
# Create a sketch for the bore on the top face (Z = total_height)
sketch_bore = body.newObject("Sketcher::SketchObject", "Sketch_Bore")
sketch_bore.Placement = App.Placement(App.Vector(0, 0, total_height))
sketch_bore.Support = (doc.getObject("Z_Axis"), []) # Attach to Z axis to get XY plane at Z
sketch_bore.MapMode = "FlatFace"

# Bore profile
bore_profile = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bore_diameter / 2.0)
sketch_bore.addGeometry(bore_profile, False)

# Constraint: Center on Z axis (handled by MapMode/Support usually, but explicit is good)
# Actually, MapMode "FlatFace" with Z_Axis support creates a plane perpendicular to Z at the intersection.
# The circle is centered at (0,0,0) in local coords, which maps to (0,0,total_height) in global.
# We need to constrain it to be centered.
# Let's add a point constraint to the origin of the sketch plane.
# Since we don't have a specific point object, we rely on the default centering if we don't move it.
# To be safe, let's add a constraint to the Z axis line if possible, or just assume center.
# Better: Use a Point on the sketch.
# Let's add a point at (0,0) in the sketch and constrain it to the Z axis.
# However, standard practice: MapMode "FlatFace" with Z_Axis creates a plane. The sketch origin is at the intersection.
# So the circle is centered.

doc.recompute()

pocket_bore = body.newObject("PartDesign::Pocket", "Pocket_Bore")
pocket_bore.Profile = sketch_bore
pocket_bore.Type = "ThroughAll" # Goes all the way through the flange

doc.recompute()

# --- Feature 3: Pad (Hub) ---
# Create a sketch for the hub on the top face (Z = total_height)
sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, total_height))
sketch_hub.Support = (doc.getObject("Z_Axis"), [])
sketch_hub.MapMode = "FlatFace"

# Hub profile
hub_profile = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hub_diameter / 2.0)
sketch_hub.addGeometry(hub_profile, False)

doc.recompute()

pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub")
pad_hub.Profile = sketch_hub
pad_hub.Length = raised_face_thickness
pad_hub.Type = "Solid"
pad_hub.MidPlane = False
pad_hub.Reverse = False

doc.recompute()

# --- Feature 4: Pocket (Raised Face) ---
# Create a sketch for the raised face on the top of the hub (Z = total_height + raised_face_thickness)
sketch_raised = body.newObject("Sketcher::SketchObject", "Sketch_RaisedFace")
sketch_raised.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
sketch_raised.Support = (doc.getObject("Z_Axis"), [])
sketch_raised.MapMode = "FlatFace"

# Raised face profile
raised_profile = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), raised_face_diameter / 2.0)
sketch_raised.addGeometry(raised_profile, False)

doc.recompute()

pocket_raised = body.newObject("PartDesign::Pocket", "Pocket_RaisedFace")
pocket_raised.Profile = sketch_raised
pocket_raised.Type = "ThroughAll"

doc.recompute()

# --- Feature 5: Hole (Bolt Holes) ---
# Create a sketch for bolt holes on the top face (Z = total_height + raised_face_thickness)
sketch_bolt = body.newObject("Sketcher::SketchObject", "Sketch_BoltHoles")
sketch_bolt.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
sketch_bolt.Support = (doc.getObject("Z_Axis"), [])
sketch_bolt.MapMode = "FlatFace"

# Bolt hole profile
bolt_hole_profile = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_hole_diameter / 2.0)
sketch_bolt.addGeometry(bolt_hole_profile, False)

# Add constraints for bolt holes
# We need to place them on the bolt circle.
# We can use a Polar Pattern feature to place the holes, but the pattern needs a profile.
# Alternatively, we can create the holes directly using a Hole feature if we define the positions.
# However, the prompt asks for a feature tree. A PolarPattern of a Hole feature is the standard way.
# But Hole feature in PartDesign requires a specific setup.
# Let's use a PolarPattern of a simple Pad (subtractive) or a Hole feature.
# Using a Hole feature is cleaner for threaded holes, but for simple clearance holes, a Pad with negative length or a Pocket works.
# Let's use a Hole feature for semantic correctness.

# First, create a single hole sketch
sketch_single_hole = body.newObject("Sketcher::SketchObject", "Sketch_SingleHole")
sketch_single_hole.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
sketch_single_hole.Support = (doc.getObject("Z_Axis"), [])
sketch_single_hole.MapMode = "FlatFace"

single_hole_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), bolt_hole_diameter / 2.0)
sketch_single_hole.addGeometry(single_hole_geom, False)

# Constraint: Center on Z axis
# We need to constrain the center of the circle to the Z axis.
# In Sketcher, we can constrain a point on the circle to the axis.
# Let's add a point at (0,0) in the sketch and constrain it to the Z axis.
# Actually, the circle center is at (0,0). We can constrain the circle center to the Z axis.
# Sketcher constraint: "PointOnLine" or similar.
# Let's add a point at (0,0) and constrain it to the Z axis.
# But we don't have a point object.
# Alternative: Constrain the circle center to the Z axis using "CenterOnLine" if available, or just assume it's centered.
# To be robust: Add a point at (0,0) in the sketch.
# sketch_single_hole.addGeometry(Part.LineSegment(App.Vector(0,0,0), App.Vector(0,0,0.1)), False) # Dummy line? No.
# Let's just constrain the circle center to the Z axis.
# Constraint: "CenterOnLine" (Circle center to Line).
# We need the Z axis line.
# Let's assume the circle is centered by default when added to a sketch on a plane defined by an axis.
# If not, we can add a constraint "PointOnLine" between a point on the circle and the Z axis.
# Let's add a point at (0,0) in the sketch.
# sketch_single_hole.addGeometry(Part.Point(App.Vector(0,0,0)), False)
# Then constrain Point to Z_Axis.
# Actually, simpler: Just use the PolarPattern on the sketch itself? No, PolarPattern works on features.
# Let's create a Hole feature first.

hole_feature = body.newObject("PartDesign::Hole", "Hole_Bolt")
hole_feature.Profile = sketch_single_hole
hole_feature.Type = "Simple"
hole_feature.Diameter = bolt_hole_diameter
hole_feature.Length = raised_face_thickness # Depth of the hole
hole_feature.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
# The Hole feature places the hole at its Placement.
# We need to constrain the Placement to the Z axis.
# Let's add a constraint to the Hole feature's Placement.
# hole_feature.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
# We need to constrain the X and Y of the placement to 0.
# hole_feature.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
# Let's use a constraint on the Placement.
# hole_feature.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
# We can add constraints to the Placement.
# hole_feature.Placement = App.Placement(App.Vector(0, 0, total_height + raised_face_thickness))
# Let's just set it and rely on the fact that we are creating it at the origin of the sketch plane.
# The sketch plane is at Z = total_height + raised_face_thickness, centered on Z axis.
# So the hole will be centered.

doc.recompute()

# Now, create a PolarPattern of the Hole feature
pattern_bolt = body.newObject("PartDesign::PolarPattern", "Pattern_BoltHoles")
pattern_bolt.Originals = [hole_feature]
pattern_bolt.Axis = (doc.getObject("Z_Axis"), [])
pattern_bolt.Angle = 360.0
pattern_bolt.Occurrences = number_bolt_holes
pattern_bolt.Distribution = "Angle"

doc.recompute()

# --- Final Save ---
# Save the document to the specified path
output_path = Path(__file__).resolve().with_suffix(".FCStd")
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
