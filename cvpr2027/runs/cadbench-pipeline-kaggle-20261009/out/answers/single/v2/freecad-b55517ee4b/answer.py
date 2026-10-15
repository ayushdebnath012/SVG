import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("BrakeDisk")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a VarSet to hold parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "disk_outer_diameter", "Dimensions", "Outer diameter of the brake disk")
params.disk_outer_diameter = 280.0
params.addProperty("App::PropertyLength", "disk_inner_diameter", "Dimensions", "Inner diameter of the brake disk")
params.disk_inner_diameter = 140.0
params.addProperty("App::PropertyLength", "disk_thickness", "Dimensions", "Thickness of the brake disk")
params.disk_thickness = 30.0
params.addProperty("App::PropertyLength", "hub_outer_diameter", "Dimensions", "Outer diameter of the central hub")
params.hub_outer_diameter = 160.0
params.addProperty("App::PropertyLength", "hub_inner_diameter", "Dimensions", "Inner diameter of the central hub")
params.hub_inner_diameter = 60.0
params.addProperty("App::PropertyLength", "hub_height", "Dimensions", "Height of the central hub")
params.hub_height = 50.0
params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "Diameter of mounting holes")
params.mounting_hole_diameter = 15.0
params.addProperty("App::PropertyLength", "mounting_hole_pcd", "Dimensions", "Pitch Circle Diameter of mounting holes")
params.mounting_hole_pcd = 100.0
params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "Number of mounting holes")
params.number_of_mounting_holes = 5
params.addProperty("App::PropertyLength", "cooling_hole_diameter", "Dimensions", "Diameter of cooling holes")
params.cooling_hole_diameter = 6.0
params.addProperty("App::PropertyLength", "cooling_hole_pcd", "Dimensions", "Pitch Circle Diameter of cooling holes")
params.cooling_hole_pcd = 210.0
params.addProperty("App::PropertyInteger", "number_of_cooling_holes", "Dimensions", "Number of cooling holes")
params.number_of_cooling_holes = 20

# --- Sketch 1: Main Disk Profile ---
sketch_disk = body.newObject("Sketcher::SketchObject", "Sketch_Disk")
sketch_disk.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_disk.Support = (doc.getObject("XY_Plane"), [])
sketch_disk.MapMode = "FlatFace"
sketch_disk.ConstrainAuto = True
sketch_disk.ConstrainToCurrent = True

# Outer Circle
outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.disk_outer_diameter / 2.0)
sketch_disk.addGeometry(outer_circle, False)

# Inner Circle (Hub Base)
inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_outer_diameter / 2.0)
sketch_disk.addGeometry(inner_circle, False)

# Add constraints to define the circles relative to each other and origin
# Coincident centers
sketch_disk.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
# Concentric
sketch_disk.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 1))
# Horizontal/Vertical alignment (optional but good for stability)
sketch_disk.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
sketch_disk.addConstraint(Sketcher.Constraint("Vertical", 0, 2))

# --- Sketch 2: Hub Profile ---
sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub")
sketch_hub.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_hub.Support = (doc.getObject("XY_Plane"), [])
sketch_hub.MapMode = "FlatFace"
sketch_hub.ConstrainAuto = True
sketch_hub.ConstrainToCurrent = True

# Hub Outer Circle
hub_outer = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_outer_diameter / 2.0)
sketch_hub.addGeometry(hub_outer, False)

# Hub Inner Circle
hub_inner = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.hub_inner_diameter / 2.0)
sketch_hub.addGeometry(hub_inner, False)

# Constraints for Hub
sketch_hub.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch_hub.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 1))
sketch_hub.addConstraint(Sketcher.Constraint("Horizontal", 0, 2))
sketch_hub.addConstraint(Sketcher.Constraint("Vertical", 0, 2))

# --- Sketch 3: Mounting Holes ---
sketch_mount = body.newObject("Sketcher::SketchObject", "Sketch_MountHoles")
sketch_mount.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_mount.Support = (doc.getObject("XY_Plane"), [])
sketch_mount.MapMode = "FlatFace"
sketch_mount.ConstrainAuto = True
sketch_mount.ConstrainToCurrent = True

# Create circles for mounting holes
mount_holes = []
for i in range(params.number_of_mounting_holes):
    angle = (i / params.number_of_mounting_holes) * 360.0 * (3.141592653589793 / 180.0)
    x = (params.mounting_hole_pcd / 2.0) * App.Vector(math.cos(angle), math.sin(angle), 0)
    circle = Part.Circle(x, App.Vector(0, 0, 1), params.mounting_hole_diameter / 2.0)
    mount_holes.append(circle)
    sketch_mount.addGeometry(circle, False)

# Add constraints to align holes on a circle
# We constrain the first hole to be on the X axis
sketch_mount.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 1, 1)) # First hole center on X axis
sketch_mount.addConstraint(Sketcher.Constraint("Horizontal", 0, 2, 1, 1))

# Constrain subsequent holes to be equidistant from the first
for i in range(1, params.number_of_mounting_holes):
    idx = i + 1
    sketch_mount.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 1)) # All concentric
    sketch_mount.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 1)) # All concentric (redundant but safe)
    # Distance constraint between centers is complex in sketcher without intermediate points, 
    # so we rely on the Polar Pattern later to position them perfectly. 
    # We just ensure they are all concentric with the origin.
    sketch_mount.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 1))

# --- Sketch 4: Cooling Holes ---
sketch_cool = body.newObject("Sketcher::SketchObject", "Sketch_CoolHoles")
sketch_cool.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_cool.Support = (doc.getObject("XY_Plane"), [])
sketch_cool.MapMode = "FlatFace"
sketch_cool.ConstrainAuto = True
sketch_cool.ConstrainToCurrent = True

# Create circles for cooling holes
cool_holes = []
for i in range(params.number_of_cooling_holes):
    angle = (i / params.number_of_cooling_holes) * 360.0 * (3.141592653589793 / 180.0)
    x = (params.cooling_hole_pcd / 2.0) * App.Vector(math.cos(angle), math.sin(angle), 0)
    circle = Part.Circle(x, App.Vector(0, 0, 1), params.cooling_hole_diameter / 2.0)
    cool_holes.append(circle)
    sketch_cool.addGeometry(circle, False)

# Constrain cooling holes to be concentric
for i, circle in enumerate(cool_holes):
    if i == 0:
        sketch_cool.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, 1, 1))
        sketch_cool.addConstraint(Sketcher.Constraint("Horizontal", 0, 2, 1, 1))
    else:
        sketch_cool.addConstraint(Sketcher.Constraint("Concentric", 0, 2, 1, 1))

# --- Feature 1: Pad for the Disk ---
pad_disk = body.newObject("PartDesign::Pad", "Pad_Disk")
pad_disk.Profile = sketch_disk
pad_disk.Length = params.disk_thickness
pad_disk.Type = "Solid"
pad_disk.MidPlane = False

# --- Feature 2: Pad for the Hub (extends from disk) ---
pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub")
pad_hub.Profile = sketch_hub
pad_hub.Length = params.hub_height - params.disk_thickness
pad_hub.Type = "Solid"
pad_hub.MidPlane = False
pad_hub.Placement = App.Placement(App.Vector(0, 0, params.disk_thickness)) # Offset to sit on top of disk

# --- Feature 3: Pocket for Mounting Holes ---
pocket_mount = body.newObject("PartDesign::Pocket", "Pocket_MountHoles")
pocket_mount.Profile = sketch_mount
pocket_mount.Type = "ThroughAll"
pocket_mount.Clean = True

# --- Feature 4: Pocket for Cooling Holes ---
pocket_cool = body.newObject("PartDesign::Pocket", "Pocket_CoolHoles")
pocket_cool.Profile = sketch_cool
pocket_cool.Type = "ThroughAll"
pocket_cool.Clean = True

# --- Feature 5: Polar Pattern for Mounting Holes (Optional if sketch was fully constrained, but ensures exact spacing)
# Actually, since we used ThroughAll pockets, the sketch geometry defines the shape. 
# The sketch itself had the holes. The pocket will cut them all. 
# No need for a pattern feature if the sketch contains all holes.

# --- Feature 6: Polar Pattern for Cooling Holes (Same logic)
# No need for pattern feature if sketch contains all holes.

# --- Feature 7: Fillet for Hub Inner Edge (Optional but good for realism)
# We need to select an edge. Let's fillet the inner edge of the hub.
# This requires selecting an edge from the solid.
# Since we are building a tree, we can't easily select edges by name without recompute.
# However, we can try to fillet the inner cylindrical surface of the hub.
# Let's skip complex edge selection for now to ensure robustness in headless mode 
# unless we can reference the edge index. 
# Instead, let's just leave it smooth or add a simple chamfer if needed.
# For this script, we will skip the fillet to avoid edge selection errors in headless mode 
# without a GUI context, focusing on the parametric structure.

# --- Finalize ---
doc.recompute()

# Save the file
output_path = Path(__file__).resolve().parent / "answer.FCStd"
doc.saveAs(str(output_path))

print(f"Model saved to {output_path}")
