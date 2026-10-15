from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

# Initialize document
doc = App.newDocument("SpokedBeltPulley")

# === 1. Create Body and Named Parameters ===
body = doc.addObject("PartDesign::Body", "Body")

params = body.newObject("App::VarSet", "Parameters")
params.width = 160.0
params.flange_len = 74.4
params.flange_thk = 1.5
params.arm_len = 47.625
params.spoke_cnt = 8
params.spoke_w = 18.36
params.spoke_r = 20.0
params.spoke_sweep = 30.0
params.spoke_cnt = 30.0  # Count
params.arm_cnt = 8.0
params.hub_od = 140.0
params.hub_id = 12.0
params.hub_thk = 10.0
params.rim_id = 18.36
params.hole_cnt = 4
params.hole_d = 12.0
params.hole_p = 38.0

# === 2. Create Reference Planes ===
# XY Plane (for top-down sketch of pulley face)
xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
doc.addObject("App::Constraint", "XY_Plane_Constraint")
xy_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
body = doc.getObject("Body")
body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
doc.recompute()

# XZ Plane (for radial arms sketch)
xz_plane = doc.addObject("PartDesign::Plane", "XZ_Plane")
xz_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(math.pi/2, 0, 0))
doc.recompute()

# === 3. Main Pulley Face Sketch (XY Plane) ===
sketch_face = body.newObject("Sketcher::SketchObject", "FaceSketch")
sketch_face.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
sketch_face.Plane = "XY_Plane"
sketch_face.Constraints = []

# Outer rim
sketch_face.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.width / 2), True)

# Inner hub OD
sketch_face.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_od / 2), True)

# Spoke outer radius (R65 from center to start of spoke base)
sketch_face.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), (params.arm_len + params.hub_thk/2 + params.rim_id/2 - params.hub_od/2) * math.cos(math.pi/4)), True) # Approximation

# Hole circle
sketch_face.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hole_p / 2), True)

# Add constraints for concentricity
sketch_face.addConstraint(Sketcher.Constraint("Equal", 0, 1, 2), True) # Concentric circles
sketch_face.addConstraint(Sketcher.Constraint("Equal", 2, 3), True) # Concentric circles
sketch_face.addConstraint(Sketcher.Constraint("Equal", 3, 4), True) # Concentric circles
sketch_face.addConstraint(Sketcher.Constraint("Equal", 4, 5), True) # Concentric circles

doc.recompute()

# === 4. Radial Arm Sketch (XZ Plane) ===
sketch_arms = body.newObject("Sketcher::SketchObject", "ArmSketch")
sketch_arms.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(math.pi/2, 0, 0))
sketch_arms.Plane = "XZ_Plane"
sketch_arms.Constraints = []

# Hub OD
sketch_arms.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_od / 2), True)

# Spoke sweep radius (R58.75 from drawing)
sketch_arms.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.spoke_r), True)

# Spoke width (18.36)
sketch_arms.addGeometry(Part.LineSegment(App.Vector(-params.spoke_w / 2, 0, 0), App.Vector(params.spoke_w / 2, 0, 0)), True)

# Hub thickness
sketch_arms.addGeometry(Part.LineSegment(App.Vector(0, params.hub_thk, 0), App.Vector(0, 0, 0)), True)

# Add constraints
sketch_arms.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.spoke_r), True)
sketch_arms.addConstraint(Sketcher.Constraint("Radius", 1, 2, params.hub_od / 2), True)
sketch_arms.addConstraint(Sketcher.Constraint("Radius", 2, 3, params.hub_od / 2), True)
sketch_arms.addConstraint(Sketcher.Constraint("Radius", 3, 4, params.spoke_w / 2), True)
sketch_arms.addConstraint(Sketcher.Constraint("Radius", 4, 5, params.spoke_w / 2), True)
sketch_arms.addConstraint(Sketcher.Constraint("Equal", 1, 2, 3, 4, 5), True) # Concentric
sketch_arms.addConstraint(Sketcher.Constraint("Angle", 0, 1, 1), True) # 90 deg

doc.recompute()

# === 5. Main Pulley Pad (Create the base body) ===
pad_main = body.newObject("PartDesign::Pad", "PadMain")
pad_main.Profile = sketch_face
pad_main.Length = params.flange_len
pad_main.Midplane = True
doc.recompute()

# === 6. Create Arm Body (for spokes) ===
arm_body = doc.addObject("PartDesign::Body", "ArmBody")

# Pad arm
pad_arm = arm_body.newObject("PartDesign::Pad", "PadArm")
pad_arm.Profile = sketch_arms
pad_arm.Length = params.hub_thk
pad_arm.Midplane = True
doc.recompute()

# === 7. Create Flange (for hub) ===
flange_body = doc.addObject("PartDesign::Body", "FlangeBody")

# Pad flange
pad_flange = flange_body.newObject("PartDesign::Pad", "PadFlange")
pad_flange.Profile = sketch_face
pad_flange.Length = params.hub_thk
pad_flange.Midplane = True
doc.recompute()

# === 8. Create Holes (Hub) ===
hole_body = doc.addObject("PartDesign::Body", "HoleBody")

# Hole sketch
hole_sketch = hole_body.newObject("Sketcher::SketchObject", "HoleSketch")
hole_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
hole_sketch.Plane = "XY_Plane"
hole_sketch.Constraints = []

# Hole circle
hole_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hole_d / 2), True)
# Hole center
hole_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.hole_p / 2, 0), App.Vector(0, 0, 0)), True)
# Hole center 2
hole_sketch.addGeometry(Part.LineSegment(App.Vector(0, -params.hole_p / 2, 0), App.Vector(0, 0, 0)), True)
# Hole center 3
hole_sketch.addGeometry(Part.LineSegment(App.Vector(params.hole_p / 2, 0, 0), App.Vector(0, 0, 0)), True)
# Hole center 4
hole_sketch.addGeometry(Part.LineSegment(App.Vector(-params.hole_p / 2, 0, 0), App.Vector(0, 0, 0)), True)

hole_sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1, 2, 3, 4), True) # Concentric
hole_sketch.addConstraint(Sketcher.Constraint("Distance", 0, 1, params.hole_p), True) # Distance between centers
hole_sketch.addConstraint(Sketcher.Constraint("Distance", 0, 2, params.hole_p), True) # Distance between centers
hole_sketch.addConstraint(Sketcher.Constraint("Distance", 0, 3, params.hole_p), True) # Distance between centers
hole_sketch.addConstraint(Sketcher.Constraint("Distance", 0, 4, params.hole_p), True) # Distance between centers

doc.recompute()

# Pocket holes
pocket_holes = hole_body.newObject("PartDesign::Pocket", "PocketHoles")
pocket_holes.Profile = hole_sketch
pocket_holes.Type = "ThroughAll"
doc.recompute()

# === 9. Create Spoke Body (for radial arms) ===
spoke_body = doc.addObject("PartDesign::Body", "SpokeBody")

# Spoke sketch
spoke_sketch = spoke_body.newObject("Sketcher::SketchObject", "SpokeSketch")
spoke_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(math.pi/2, 0, 0))
spoke_sketch.Plane = "XZ_Plane"
spoke_sketch.Constraints = []

# Spoke sweep radius
spoke_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.spoke_r), True)
# Spoke width
spoke_sketch.addGeometry(Part.LineSegment(App.Vector(-params.spoke_w / 2, 0, 0), App.Vector(params.spoke_w / 2, 0, 0)), True)
# Hub thickness
spoke_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.hub_thk, 0), App.Vector(0, 0, 0)), True)

spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.spoke_r), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 1, 2, params.hub_od / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 2, 3, params.hub_od / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 3, 4, params.spoke_w / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 4, 5, params.spoke_w / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Equal", 1, 2, 3, 4, 5), True) # Concentric
spoke_sketch.addConstraint(Sketcher.Constraint("Angle", 0, 1, 1), True) # 90 deg

doc.recompute()

# Pad spokes
pad_spokes = spoke_body.newObject("PartDesign::Pad", "PadSpokes")
pad_spokes.Profile = spoke_sketch
pad_spokes.Length = params.flange_len - params.hub_thk
pad_spokes.Midplane = True
doc.recompute()

# === 10. Create Flange (for hub) ===
flange_body = doc.addObject("PartDesign::Body", "FlangeBody")

# Flange sketch
flange_sketch = flange_body.newObject("Sketcher::SketchObject", "FlangeSketch")
flange_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(0, 0, 0))
flange_sketch.Plane = "XY_Plane"
flange_sketch.Constraints = []

# Flange OD
flange_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.width / 2), True)
# Flange ID
flange_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_od / 2), True)

flange_sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1), True) # Concentric

doc.recompute()

# Pad flange
pad_flange = flange_body.newObject("PartDesign::Pad", "PadFlange")
pad_flange.Profile = flange_sketch
pad_flange.Length = params.hub_thk
pad_flange.Midplane = True
doc.recompute()

# === 11. Create Spoke Body (for radial arms) ===
spoke_body = doc.addObject("PartDesign::Body", "SpokeBody")

# Spoke sketch
spoke_sketch = spoke_body.newObject("Sketcher::SketchObject", "SpokeSketch")
spoke_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(math.pi/2, 0, 0))
spoke_sketch.Plane = "XZ_Plane"
spoke_sketch.Constraints = []

# Spoke sweep radius
spoke_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.spoke_r), True)
# Spoke width
spoke_sketch.addGeometry(Part.LineSegment(App.Vector(-params.spoke_w / 2, 0, 0), App.Vector(params.spoke_w / 2, 0, 0)), True)
# Hub thickness
spoke_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.hub_thk, 0), App.Vector(0, 0, 0)), True)

spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 0, 1, params.spoke_r), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 1, 2, params.hub_od / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 2, 3, params.hub_od / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 3, 4, params.spoke_w / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Radius", 4, 5, params.spoke_w / 2), True)
spoke_sketch.addConstraint(Sketcher.Constraint("Equal", 1, 2, 3, 4, 5), True) # Concentric
spoke_sketch.addConstraint(Sketcher.Constraint("Angle", 0, 1, 1), True) # 90 deg

doc.recompute()

# Pad spokes
pad_spokes = spoke_body.newObject("PartDesign::Pad", "PadSpokes")
pad_spokes.Profile = spoke_sketch
pad_spokes.Length = params.flange_len - params.hub_thk
pad_spokes.Midplane = True
doc.recompute()

# === 12. Final Assembly ===
# Combine all bodies into one
body = doc.getObject("Body")
body = body.newObject("PartDesign::Part", "PartAssembly")
body.Part = [doc.getObject("PadMain"), doc.getObject("PadArm"), doc.getObject("PadFlange"), doc.getObject("PadSpokes")]
doc.recompute()

# Save the document
doc.saveAs(str(Path(__file__).resolve().with_suffix(".FCStd")))
