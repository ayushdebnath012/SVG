"""
FreeCAD 1.1 Script: Disk Brake Construction
Generates a parametric Disk Brake model using PartDesign features.
"""

import os
import FreeCAD as App
import Part
from pathlib import Path

# --- Configuration ---
# Derived from __file__ to ensure output is next to the script
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = SCRIPT_DIR / "answer.FCStd"

# Part Design Parameters (as requested)
PARAMS = {
    "disk_outer_diameter": 280.0,
    "disk_inner_diameter": 140.0,
    "disk_thickness": 30.0,
    "hub_outer_diameter": 160.0,
    "hub_inner_diameter": 60.0,
    "hub_height": 50.0,
    "mounting_hole_diameter": 15.0,
    "mounting_hole_pcd": 100.0,
    "number_of_mounting_holes": 5,
    "cooling_hole_diameter": 6.0,
    "cooling_hole_pcd": 210.0,
    "number_of_cooling_holes": 20,
}

# --- Initialization ---
doc = App.newDocument("DiskBrake")
body = doc.addObject("PartDesign::Body", "Body")

# Add a parameter container for editable variables
params = body.newObject("App::VarSet", "Parameters")
for name, value in PARAMS.items():
    params.addProperty(f"App::PropertyFloat", name, "Parameters", "Geometric Dimensions")
    setattr(params, name, value)

# --- Feature Construction ---

# 1. Main Disk Pad
# Sketch 1: Main Disk Profile (Thickness)
sketch_main = body.newObject("Sketcher::SketchObject", "Sketch_MainDisk")
sketch_main.Placement = App.Placement(App.Vector(0, 0, 0))
sketch_main.ConstrainAuto = True
sketch_main.AutoConstrain = True
sketch_main.ConstraintLabelModifier = True
sketch_main.TessellationAngle = 5

# Add outer circle
circle_outer = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["disk_outer_diameter"] / 2.0)
sketch_main.addGeometry(circle_outer, True)

# Add inner circle
circle_inner = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["disk_inner_diameter"] / 2.0)
sketch_main.addGeometry(circle_inner, True)

# Pad the disk
pad_main = body.newObject("PartDesign::Pad", "Pad_MainDisk")
pad_main.Profile = sketch_main
pad_main.Length = PARAMS["disk_thickness"]
pad_main.Midplane = False
pad_main.Reverse = False

# 2. Hub
# Sketch 2: Hub Profile
sketch_hub = body.newObject("Sketcher::SketchObject", "Sketch_Hub")
# Move sketch to the top face of the disk
offset_z = PARAMS["disk_thickness"] / 2.0
sketch_hub.Placement = App.Placement(App.Vector(0, 0, offset_z))
sketch_hub.ConstrainAuto = True
sketch_hub.AutoConstrain = True

# Hub outer circle
circle_hub_out = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["hub_outer_diameter"] / 2.0)
sketch_hub.addGeometry(circle_hub_out, True)

# Hub inner circle
circle_hub_in = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["hub_inner_diameter"] / 2.0)
sketch_hub.addGeometry(circle_hub_in, True)

# Pad the hub
pad_hub = body.newObject("PartDesign::Pad", "Pad_Hub")
pad_hub.Profile = sketch_hub
pad_hub.Length = PARAMS["hub_height"]
pad_hub.Midplane = False
pad_hub.Reverse = False

# 3. Mounting Holes
# Sketch 3: Mounting Hole Pattern
sketch_mount = body.newObject("Sketcher::SketchObject", "Sketch_MountingHoles")
sketch_mount.Placement = App.Placement(App.Vector(0, 0, PARAMS["disk_thickness"] / 2.0))
sketch_mount.ConstrainAuto = True
sketch_mount.AutoConstrain = True

# Hole circle geometry
hole_geometry = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["mounting_hole_diameter"] / 2.0)
sketch_mount.addGeometry(hole_geometry, True)

# Create the holes using a Pad with negative length (subtractive)
# We define a pattern in the PartDesign feature itself
mount_pad = body.newObject("PartDesign::Pad", "Pad_MountingHoles")
mount_pad.Profile = sketch_mount
mount_pad.Length = -PARAMS["mounting_hole_diameter"]
mount_pad.Midplane = False
mount_pad.Reverse = False

# Polar Pattern for Mounting Holes
pattern_mount = body.newObject("PartDesign::PolarPattern", "Pattern_MountingHoles")
pattern_mount.Originals = [mount_pad]
pattern_mount.Axis = (doc.getObject("Z_Axis"), [""])
pattern_mount.Angle = 360.0
pattern_mount.Occurrences = PARAMS["number_of_mounting_holes"]
pattern_mount.Distribute = True

# 4. Cooling Holes
# Sketch 4: Cooling Hole Pattern
sketch_cool = body.newObject("Sketcher::SketchObject", "Sketch_CoolingHoles")
sketch_cool.Placement = App.Placement(App.Vector(0, 0, PARAMS["disk_thickness"] / 2.0))
sketch_cool.ConstrainAuto = True
sketch_cool.AutoConstrain = True

# Hole circle geometry
cool_geometry = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), PARAMS["cooling_hole_diameter"] / 2.0)
sketch_cool.addGeometry(cool_geometry, True)

# Create the holes
cool_pad = body.newObject("PartDesign::Pad", "Pad_CoolingHoles")
cool_pad.Profile = sketch_cool
cool_pad.Length = -PARAMS["cooling_hole_diameter"]
cool_pad.Midplane = False
cool_pad.Reverse = False

# Polar Pattern for Cooling Holes
pattern_cool = body.newObject("PartDesign::PolarPattern", "Pattern_CoolingHoles")
pattern_cool.Originals = [cool_pad]
pattern_cool.Axis = (doc.getObject("Z_Axis"), [""])
pattern_cool.Angle = 360.0
pattern_cool.Occurrences = PARAMS["number_of_cooling_holes"]
pattern_cool.Distribute = True

# --- Finalization ---
doc.recompute()

# Save the file
doc.saveAs(str(OUTPUT_FILE))

print(f"Successfully generated disk brake at: {OUTPUT_FILE.resolve()}")
