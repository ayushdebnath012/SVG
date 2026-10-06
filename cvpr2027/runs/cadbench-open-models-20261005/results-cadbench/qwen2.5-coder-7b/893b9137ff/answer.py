import FreeCAD
import Part
import PartDesign

# Set up the document
doc = FreeCAD.newDocument("LegoBrick")

# Define parameters
lego_unit_size = 8.0
lego_height = 9.6
lego_thickness = 1.6
num_studs_rows = 2
num_studs_columns = 4
studs_distance = 8.0
stud_center = (4.0, 4.0)
stud_diameter = 4.8
stud_height = 1.6
tube_center = (8.0, 8.0)
tube_outer_diameter = 6.4
tube_inner_diameter = 4.8
tube_distance = 8.0

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the main brick
brick = body.newObject("PartDesign::Box", "Brick")
brick.Length = lego_unit_size
brick.Width = lego_unit_size
brick.Height = lego_height
brick.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create the studs
for i in range(num_studs_rows):
    for j in range(num_studs_columns):
        stud = body.newObject("PartDesign::Cylinder", f"Stud_{i}_{j}")
        stud.Radius = stud_diameter / 2
        stud.Height = stud_height
        stud.Placement.Base = FreeCAD.Vector(
            stud_center[0] + (j - num_studs_columns / 2) * studs_distance,
            stud_center[1] + (i - num_studs_rows / 2) * studs_distance,
            lego_height - stud_height / 2
        )

# Create the tubes
for i in range(num_studs_rows):
    for j in range(num_studs_columns):
        tube = body.newObject("PartDesign::Cylinder", f"Tube_{i}_{j}")
        tube.Radius = tube_inner_diameter / 2
        tube.Height = tube_distance
        tube.Placement.Base = FreeCAD.Vector(
            tube_center[0] + (j - num_studs_columns / 2) * studs_distance,
            tube_center[1] + (i - num_studs_rows / 2) * studs_distance,
            lego_height - tube_distance / 2
        )
        tube.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)

# Finalize the body
body.Tip = body[-1]
body.recompute()

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
