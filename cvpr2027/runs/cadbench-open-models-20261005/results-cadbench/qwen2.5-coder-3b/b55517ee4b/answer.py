import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("DiskBrake")

# Create a PartDesign Body
body = PartDesign.Body(doc)

# Create the disk
disk = PartDesign.Disk(doc, "Disk")
disk.Radius1 = 140  # Inner diameter
disk.Radius2 = 280  # Outer diameter
disk.Radius3 = 30   # Thickness

# Create the hub
hub = PartDesign.Hub(doc, "Hub")
hub.Radius1 = 60   # Inner diameter
hub.Radius2 = 160  # Outer diameter
hub.Radius3 = 50   # Height

# Create mounting holes
mounting_hole_diameter = 15
mounting_hole_pcd = 100
number_of_mounting_holes = 5
for i in range(number_of_mounting_holes):
    hole = PartDesign.Hole(doc, f"MountingHole_{i+1}")
    hole.Radius = mounting_hole_diameter / 2
    hole.Pitch = mounting_hole_pcd

# Create cooling holes
cooling_hole_diameter = 6
cooling_hole_pcd = 210
number_of_cooling_holes = 20
for i in range(number_of_cooling_holes):
    hole = PartDesign.Hole(doc, f"CoolingHole_{i+1}")
    hole.Radius = cooling_hole_diameter / 2
    hole.Pitch = cooling_hole_pcd

# Add the disk and hub to the body
body.addObject(disk)
body.addObject(hub)

# Save the document
doc.saveAs("/app/answer.FCStd")
